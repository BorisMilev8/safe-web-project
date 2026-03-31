import csv
import json
import sys
import time
import unittest
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import DefaultDict, Dict, List, Optional, Tuple

import psutil
from playwright.sync_api import sync_playwright


@dataclass
class BrowserConfig:
    key: str
    name: str
    playwright_name: str


BROWSERS: Dict[str, BrowserConfig] = {
    "chrome": BrowserConfig(
        key="chrome",
        name="Google Chrome",
        playwright_name="chromium",
    ),
    "firefox": BrowserConfig(
        key="firefox",
        name="Firefox",
        playwright_name="firefox",
    ),
    "safari": BrowserConfig(
        key="safari",
        name="Safari",
        playwright_name="webkit",
    ),
}

DEFAULT_BROWSER_ORDER = ["chrome", "firefox", "safari"]
TRIALS_PER_BROWSER = 3
URLS_TO_TEST = [
    "https://youtube.com",
    "https://www.wikipedia.org",
    "https://www.cnn.com",
]


def resolve_base_dir() -> Path:
    if "__file__" in globals():
        return Path(__file__).resolve().parent
    return Path.cwd().resolve()


BASE_DIR = resolve_base_dir()
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

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


def measure_process_tree(pid: int, duration: float = 8.0, interval: float = 0.25) -> Dict[str, float]:
    cpu_samples: List[float] = []
    memory_samples: List[float] = []

    try:
        parent = psutil.Process(pid)
        processes = [parent] + parent.children(recursive=True)

        for proc in processes:
            try:
                proc.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        time.sleep(0.1)
        start = time.time()

        while time.time() - start < duration:
            total_cpu = 0.0
            total_memory = 0.0

            processes = [parent]
            try:
                processes += parent.children(recursive=True)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

            for proc in processes:
                try:
                    total_cpu += proc.cpu_percent(interval=None)
                    total_memory += proc.memory_info().rss / (1024 * 1024)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            cpu_samples.append(total_cpu / max(psutil.cpu_count(), 1))
            memory_samples.append(total_memory)
            time.sleep(interval)

        return {
            "avg_cpu_percent": round(sum(cpu_samples) / len(cpu_samples), 2) if cpu_samples else 0.0,
            "peak_cpu_percent": round(max(cpu_samples), 2) if cpu_samples else 0.0,
            "avg_rss_mb": round(sum(memory_samples) / len(memory_samples), 2) if memory_samples else 0.0,
            "peak_rss_mb": round(max(memory_samples), 2) if memory_samples else 0.0,
        }
    except Exception as exc:
        print(f"Measurement error for pid {pid}: {exc}")
        return {
            "avg_cpu_percent": 0.0,
            "peak_cpu_percent": 0.0,
            "avg_rss_mb": 0.0,
            "peak_rss_mb": 0.0,
        }


def run_real_trial(playwright, browser_config: BrowserConfig, url: str) -> Dict[str, object]:
    browser_type = getattr(playwright, browser_config.playwright_name)
    browser = browser_type.launch(headless=False)

    try:
        browser_pid = browser.process.pid if getattr(browser, "process", None) else None

        context = browser.new_context()
        page = context.new_page()

        start = time.perf_counter()
        page.goto(url, wait_until="load", timeout=60000)
        load_time_sec = round(time.perf_counter() - start, 2)

        page.wait_for_timeout(5000)

        metrics = measure_process_tree(browser_pid, duration=8.0, interval=0.25) if browser_pid else {
            "avg_cpu_percent": 0.0,
            "peak_cpu_percent": 0.0,
            "avg_rss_mb": 0.0,
            "peak_rss_mb": 0.0,
        }

        context.close()
        return {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "browser": browser_config.playwright_name,
            "url": url,
            "load_time_sec": load_time_sec,
            **metrics,
        }
    finally:
        browser.close()


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
            "browsers": [BROWSERS[key].playwright_name for key in DEFAULT_BROWSER_ORDER],
            "trials_per_browser": TRIALS_PER_BROWSER,
            "urls_tested": URLS_TO_TEST,
        },
        "summary": build_summary(rows),
        "results": rows,
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

    print(f"Exported JSON -> {output_file}")
    return output_file


def main() -> None:
    if RESULTS_FILE.exists():
        RESULTS_FILE.unlink()

    write_csv_header_if_needed()

    with sync_playwright() as playwright:
        for key in DEFAULT_BROWSER_ORDER:
            browser_config = BROWSERS[key]
            for url in URLS_TO_TEST:
                for trial in range(1, TRIALS_PER_BROWSER + 1):
                    print(f"Running {browser_config.name} | {url} | trial {trial}")
                    row = run_real_trial(playwright, browser_config, url)
                    append_result(row)

    export_dashboard_json()
    print("Run complete!")


class SafeWebMvpTests(unittest.TestCase):
    def test_resolve_base_dir_without___file__(self) -> None:
        original_file = globals().pop("__file__", None)
        try:
            self.assertEqual(resolve_base_dir(), Path.cwd().resolve())
        finally:
            if original_file is not None:
                globals()["__file__"] = original_file

    def test_build_summary(self) -> None:
        rows = [
            {
                "timestamp": "2026-01-01T10:00:00",
                "browser": "chromium",
                "url": "https://example.com",
                "load_time_sec": 1.2,
                "avg_cpu_percent": 10.0,
                "peak_cpu_percent": 20.0,
                "avg_rss_mb": 200.0,
                "peak_rss_mb": 250.0,
            },
            {
                "timestamp": "2026-01-01T10:01:00",
                "browser": "chromium",
                "url": "https://example.com",
                "load_time_sec": 1.4,
                "avg_cpu_percent": 12.0,
                "peak_cpu_percent": 22.0,
                "avg_rss_mb": 220.0,
                "peak_rss_mb": 270.0,
            },
        ]
        summary = build_summary(rows)
        self.assertEqual(summary[0]["browser"], "chromium")
        self.assertEqual(summary[0]["runs"], 2)
        self.assertEqual(summary[0]["avg_load_time_sec"], 1.3)


if __name__ == "__main__":
    main()
