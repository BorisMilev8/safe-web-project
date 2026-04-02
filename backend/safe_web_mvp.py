import csv
import json
import os
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import DefaultDict, Dict, List, Optional, Set

import psutil
from playwright.sync_api import sync_playwright


@dataclass
class BrowserConfig:
    key: str
    name: str
    playwright_name: str
    process_name_keywords: List[str]
    launch_channel: Optional[str] = None


BROWSERS: Dict[str, BrowserConfig] = {
    "chrome": BrowserConfig(
        key="chrome",
        name="Google Chrome",
        playwright_name="chromium",
        process_name_keywords=["chrome", "chromium"],
        launch_channel="chrome",
    ),
    "firefox": BrowserConfig(
        key="firefox",
        name="Firefox",
        playwright_name="firefox",
        process_name_keywords=["firefox"],
        launch_channel=None,
    ),
}

DEFAULT_BROWSER_ORDER = ["chrome", "firefox"]
TRIALS_PER_BROWSER = 1

URLS_TO_TEST = [
    "https://www.wikipedia.org",
    "https://www.youtube.com",
    "https://www.cnn.com",
]

NAVIGATION_TIMEOUT_MS = 60000
SETTLE_AFTER_LOAD_MS = 3000
SAMPLE_INTERVAL_SEC = 0.25
EXTRA_OBSERVE_SEC = 2.0


def resolve_base_dir() -> Path:
    return Path(__file__).resolve().parent


BASE_DIR = resolve_base_dir()
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

RESULTS_FILE = DATA_DIR / "safe_web_results.csv"
FRONTEND_OUTPUT = BASE_DIR.parent / "frontend" / "public" / "safe_web_results_real.json"

CSV_HEADERS = [
    "timestamp",
    "browser",
    "url",
    "load_time_sec",
    "avg_cpu_percent",
    "peak_cpu_percent",
    "avg_rss_mb",
    "peak_rss_mb",
]


def write_csv_header_if_needed(results_file: Path = RESULTS_FILE) -> None:
    results_file.parent.mkdir(parents=True, exist_ok=True)
    if not results_file.exists():
        with results_file.open("w", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerow(CSV_HEADERS)


def append_result(row: Dict[str, object], results_file: Path = RESULTS_FILE) -> None:
    with results_file.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            row["timestamp"],
            row["browser"],
            row["url"],
            row["load_time_sec"],
            row["avg_cpu_percent"],
            row["peak_cpu_percent"],
            row["avg_rss_mb"],
            row["peak_rss_mb"],
        ])


def get_headless_mode() -> bool:
    # Local Windows/Mac: False so browser windows pop up and CPU is more realistic.
    # CI/Linux without X server: True.
    return os.getenv("CI", "false").lower() == "true"


def safe_lower(value: Optional[str]) -> str:
    return (value or "").lower()


def snapshot_matching_processes(keywords: List[str]) -> Dict[int, Dict[str, object]]:
    matches: Dict[int, Dict[str, object]] = {}
    for proc in psutil.process_iter(["pid", "name", "create_time", "cmdline"]):
        try:
            name = safe_lower(proc.info.get("name"))
            cmdline = " ".join(proc.info.get("cmdline") or []).lower()
            if any(keyword in name or keyword in cmdline for keyword in keywords):
                matches[proc.info["pid"]] = {
                    "pid": proc.info["pid"],
                    "name": proc.info.get("name") or "",
                    "create_time": float(proc.info.get("create_time") or 0.0),
                    "cmdline": proc.info.get("cmdline") or [],
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return matches


def find_new_browser_root_pid(
    keywords: List[str],
    before: Dict[int, Dict[str, object]],
    timeout: float = 10.0,
) -> Optional[int]:
    deadline = time.time() + timeout
    newest_pid: Optional[int] = None
    newest_ctime = -1.0

    while time.time() < deadline:
        after = snapshot_matching_processes(keywords)
        for pid, info in after.items():
            if pid in before:
                continue
            ctime = float(info.get("create_time") or 0.0)
            if ctime > newest_ctime:
                newest_ctime = ctime
                newest_pid = pid

        if newest_pid is not None:
            return newest_pid

        time.sleep(0.2)

    return None


def collect_descendant_pids(root_pid: int) -> Set[int]:
    try:
        root = psutil.Process(root_pid)
        pids = {root.pid}
        try:
            for child in root.children(recursive=True):
                pids.add(child.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
        return pids
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return set()


def collect_dynamic_browser_pids(
    root_pid: Optional[int],
    browser_keywords: List[str],
    launch_time: float,
) -> Set[int]:
    pids: Set[int] = set()

    if root_pid is not None:
        pids |= collect_descendant_pids(root_pid)

    for proc in psutil.process_iter(["pid", "name", "create_time", "cmdline"]):
        try:
            pid = proc.info["pid"]
            name = safe_lower(proc.info.get("name"))
            cmdline = " ".join(proc.info.get("cmdline") or []).lower()
            ctime = float(proc.info.get("create_time") or 0.0)

            if ctime + 0.001 < launch_time:
                continue

            if any(keyword in name or keyword in cmdline for keyword in browser_keywords):
                pids.add(pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    return pids


class BrowserMetricsSampler:
    def __init__(
        self,
        root_pid: Optional[int],
        browser_keywords: List[str],
        launch_time: float,
        interval: float = SAMPLE_INTERVAL_SEC,
    ) -> None:
        self.root_pid = root_pid
        self.browser_keywords = browser_keywords
        self.launch_time = launch_time
        self.interval = interval

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        self.cpu_samples: List[float] = []
        self.memory_samples: List[float] = []
        self.seen_pids: Set[int] = set()

        self._last_wall_time: Optional[float] = None
        self._last_total_cpu_time: Optional[float] = None

    def _get_current_processes(self) -> List[psutil.Process]:
        current_pids = collect_dynamic_browser_pids(
            root_pid=self.root_pid,
            browser_keywords=self.browser_keywords,
            launch_time=self.launch_time,
        )

        self.seen_pids |= current_pids

        processes: List[psutil.Process] = []
        for pid in current_pids:
            try:
                processes.append(psutil.Process(pid))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return processes

    def _sample_once(self) -> None:
        processes = self._get_current_processes()
        now = time.time()

        if not processes:
            self.cpu_samples.append(0.0)
            self.memory_samples.append(0.0)
            self._last_wall_time = now
            self._last_total_cpu_time = 0.0
            return

        total_cpu_time = 0.0
        total_memory_mb = 0.0

        for proc in processes:
            try:
                cpu_times = proc.cpu_times()
                total_cpu_time += cpu_times.user + cpu_times.system
                total_memory_mb += proc.memory_info().rss / (1024 * 1024)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        if self._last_wall_time is None or self._last_total_cpu_time is None:
            cpu_percent = 0.0
        else:
            wall_delta = now - self._last_wall_time
            cpu_delta = total_cpu_time - self._last_total_cpu_time

            if wall_delta > 0:
                # 100 = one full core saturated
                cpu_percent = max(0.0, (cpu_delta / wall_delta) * 100.0)
            else:
                cpu_percent = 0.0

        self.cpu_samples.append(round(cpu_percent, 2))
        self.memory_samples.append(round(total_memory_mb, 2))

        self._last_wall_time = now
        self._last_total_cpu_time = total_cpu_time

    def _run(self) -> None:
        self._sample_once()
        time.sleep(self.interval)

        while not self._stop_event.is_set():
            self._sample_once()
            time.sleep(self.interval)

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self, extra_observe_sec: float = EXTRA_OBSERVE_SEC) -> Dict[str, float]:
        deadline = time.time() + max(extra_observe_sec, 0.0)
        while time.time() < deadline:
            self._sample_once()
            time.sleep(self.interval)

        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)

        return {
            "avg_cpu_percent": round(sum(self.cpu_samples) / len(self.cpu_samples), 2) if self.cpu_samples else 0.0,
            "peak_cpu_percent": round(max(self.cpu_samples), 2) if self.cpu_samples else 0.0,
            "avg_rss_mb": round(sum(self.memory_samples) / len(self.memory_samples), 2) if self.memory_samples else 0.0,
            "peak_rss_mb": round(max(self.memory_samples), 2) if self.memory_samples else 0.0,
        }


def launch_browser(playwright, browser_config: BrowserConfig, headless_mode: bool):
    browser_type = getattr(playwright, browser_config.playwright_name)
    launch_kwargs = {"headless": headless_mode}

    if browser_config.playwright_name == "chromium" and browser_config.launch_channel:
        launch_kwargs["channel"] = browser_config.launch_channel

    return browser_type.launch(**launch_kwargs)


def run_real_trial(playwright, browser_config: BrowserConfig, url: str) -> Dict[str, object]:
    headless_mode = get_headless_mode()

    print(f"\nLaunching {browser_config.name} | headless={headless_mode} | url={url}")
    before = snapshot_matching_processes(browser_config.process_name_keywords)
    browser = launch_browser(playwright, browser_config, headless_mode)
    launch_time = time.time()

    try:
        context = browser.new_context()
        page = context.new_page()

        root_pid = find_new_browser_root_pid(
            browser_config.process_name_keywords,
            before,
            timeout=10.0,
        )
        print(f"Detected root/browser pid for {browser_config.name}: {root_pid}")

        sampler = BrowserMetricsSampler(
            root_pid=root_pid,
            browser_keywords=browser_config.process_name_keywords,
            launch_time=launch_time,
            interval=SAMPLE_INTERVAL_SEC,
        )
        sampler.start()

        start = time.perf_counter()
        try:
            page.goto(url, wait_until="load", timeout=NAVIGATION_TIMEOUT_MS)
        except Exception as exc:
            print(f"Navigation warning for {browser_config.name} on {url}: {exc}")

        load_time_sec = round(time.perf_counter() - start, 2)

        try:
            page.wait_for_timeout(SETTLE_AFTER_LOAD_MS)
        except Exception:
            pass

        metrics = sampler.stop(extra_observe_sec=EXTRA_OBSERVE_SEC)
        print(f"Metrics for {browser_config.name} on {url}: {metrics}")
        print(f"Observed PIDs: {sorted(sampler.seen_pids)}")

        try:
            context.close()
        except Exception:
            pass

        return {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "browser": browser_config.name,
            "url": url,
            "load_time_sec": load_time_sec,
            **metrics,
        }

    finally:
        try:
            browser.close()
        except Exception:
            pass


def load_results(results_file: Path = RESULTS_FILE) -> List[Dict[str, object]]:
    if not results_file.exists():
        return []

    rows: List[Dict[str, object]] = []
    with results_file.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append({
                "timestamp": row["timestamp"],
                "browser": row["browser"],
                "url": row["url"],
                "load_time_sec": float(row["load_time_sec"]),
                "avg_cpu_percent": float(row["avg_cpu_percent"]),
                "peak_cpu_percent": float(row["peak_cpu_percent"]),
                "avg_rss_mb": float(row["avg_rss_mb"]),
                "peak_rss_mb": float(row["peak_rss_mb"]),
            })
    return rows


def build_summary(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    grouped: DefaultDict[str, List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["browser"])].append(row)

    summary: List[Dict[str, object]] = []
    for browser, items in grouped.items():
        summary.append({
            "browser": browser,
            "runs": len(items),
            "avg_load_time_sec": round(sum(i["load_time_sec"] for i in items) / len(items), 2),
            "avg_cpu_percent": round(sum(i["avg_cpu_percent"] for i in items) / len(items), 2),
            "peak_cpu_percent": round(max(i["peak_cpu_percent"] for i in items), 2),
            "avg_rss_mb": round(sum(i["avg_rss_mb"] for i in items) / len(items), 2),
            "peak_rss_mb": round(max(i["peak_rss_mb"] for i in items), 2),
        })

    return sorted(summary, key=lambda x: str(x["browser"]))


def export_dashboard_json(results_file: Path = RESULTS_FILE, output_file: Path = FRONTEND_OUTPUT) -> Path:
    rows = load_results(results_file)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "config": {
            "browsers": [BROWSERS[key].name for key in DEFAULT_BROWSER_ORDER],
            "trials_per_browser": TRIALS_PER_BROWSER,
            "urls_tested": URLS_TO_TEST,
            "headless": get_headless_mode(),
        },
        "summary": build_summary(rows),
        "results": rows,
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

    print(f"Exported dashboard JSON -> {output_file}")
    return output_file


def main() -> None:
    print("Starting Safe Web metrics run...")
    print(f"Base dir: {BASE_DIR}")
    print(f"Results CSV: {RESULTS_FILE}")
    print(f"Frontend JSON: {FRONTEND_OUTPUT}")
    print(f"Headless mode: {get_headless_mode()}")

    if RESULTS_FILE.exists():
        RESULTS_FILE.unlink()

    write_csv_header_if_needed()

    with sync_playwright() as playwright:
        for key in DEFAULT_BROWSER_ORDER:
            browser_config = BROWSERS[key]

            for url in URLS_TO_TEST:
                for trial in range(1, TRIALS_PER_BROWSER + 1):
                    print(f"\nRunning {browser_config.name} | {url} | trial {trial}")
                    row = run_real_trial(playwright, browser_config, url)
                    append_result(row)
    }
if __name__ == "__main__":
    main()
    def run_all_tests_live():
    if RESULTS_FILE.exists():
        RESULTS_FILE.unlink()

    write_csv_header_if_needed()

    with sync_playwright() as playwright:
        for key in DEFAULT_BROWSER_ORDER:
            browser_config = BROWSERS[key]

            for url in URLS_TO_TEST:
                for trial in range(1, TRIALS_PER_BROWSER + 1):
                    print(f"\nRunning {browser_config.name} | {url} | trial {trial}")
                    row = run_real_trial(playwright, browser_config, url)
                    append_result(row)

    rows = load_results()

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "config": {
            "browsers": [BROWSERS[key].name for key in DEFAULT_BROWSER_ORDER],
            "trials_per_browser": TRIALS_PER_BROWSER,
            "urls_tested": URLS_TO_TEST,
            "headless": get_headless_mode(),
        },
        "summary": build_summary(rows),
        "results": rows,
    }

    return payload
