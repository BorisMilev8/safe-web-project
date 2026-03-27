import csv
import os
import platform
import shutil
import subprocess
import sys
import time
import unittest
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import quote_plus


# Safe Web MVP
# Alpha-friendly prototype for Safari, Chrome, and Firefox.
#
# What it does:
# - tries to open a search in Safari, Chrome, and Firefox on macOS
# - samples CPU and memory using the built-in `ps` command
# - saves one row per run to a CSV file
# - falls back to SIMULATION MODE when the environment cannot actually open browsers
#
# Why simulation mode exists:
# - sandboxes often do not allow open/osascript/browser control
# - Chrome or Firefox may not be installed
# - this lets you get successful runs and demo the full pipeline for Alpha


@dataclass
class BrowserConfig:
    key: str
    name: str
    app_path: str
    app_name: str
    process_names: List[str]
    search_url_template: str


BROWSERS: Dict[str, BrowserConfig] = {
    "safari": BrowserConfig(
        key="safari",
        name="Safari",
        app_path="/Applications/Safari.app",
        app_name="Safari",
        process_names=["Safari", "com.apple.WebKit.WebContent"],
        search_url_template="https://www.google.com/search?q={query}",
    ),
    "chrome": BrowserConfig(
        key="chrome",
        name="Google Chrome",
        app_path="/Applications/Google Chrome.app",
        app_name="Google Chrome",
        process_names=["Google Chrome", "Google Chrome Helper", "Google Chrome Helper (Renderer)"],
        search_url_template="https://www.google.com/search?q={query}",
    ),
    "firefox": BrowserConfig(
        key="firefox",
        name="Firefox",
        app_path="/Applications/Firefox.app",
        app_name="Firefox",
        process_names=["firefox", "Firefox"],
        search_url_template="https://www.google.com/search?q={query}",
    ),
}


RESULTS_FILE = Path("safe_web_results.csv")
DEFAULT_QUERY = "browser privacy comparison"
DEFAULT_LOAD_WAIT = 3
DEFAULT_SAMPLE_SECONDS = 3
TRIALS_PER_BROWSER = 1
DEFAULT_BROWSER_ORDER = ["safari", "chrome", "firefox"]


def app_exists(app_path: str) -> bool:
    return Path(app_path).exists()


def normalize_process_name(value: str) -> str:
    return value.strip().lower()


def is_macos() -> bool:
    return platform.system() == "Darwin"


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def should_simulate() -> bool:
    value = os.environ.get("SAFE_WEB_SIMULATE", "").strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if not is_macos():
        return True
    if not command_exists("open") or not command_exists("osascript") or not command_exists("ps"):
        return True
    return False


def close_browser(config: BrowserConfig) -> bool:
    if should_simulate():
        return False

    result = subprocess.run(
        ["osascript", "-e", f'tell application "{config.app_name}" to quit'],
        check=False,
        capture_output=True,
        text=True,
    )
    time.sleep(1)
    return result.returncode == 0


def open_search_in_browser(config: BrowserConfig, query: str) -> bool:
    if should_simulate():
        return False

    encoded_query = quote_plus(query)
    url = config.search_url_template.format(query=encoded_query)
    result = subprocess.run(
        ["open", "-a", config.app_path, url],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def parse_ps_output(output: str) -> List[Dict[str, float]]:
    records: List[Dict[str, float]] = []
    lines = output.strip().splitlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        parts = line.split(None, 3)
        if len(parts) < 4:
            continue

        pid_str, command, cpu_str, rss_str = parts
        try:
            records.append(
                {
                    "pid": int(pid_str),
                    "command": command,
                    "cpu_percent": float(cpu_str),
                    "memory_mb": float(rss_str) / 1024.0,
                }
            )
        except ValueError:
            continue

    return records


def collect_process_snapshot(process_names: List[str]) -> List[Dict[str, float]]:
    if should_simulate():
        return []

    lowered_targets = {normalize_process_name(name) for name in process_names}
    result = subprocess.run(
        ["ps", "-axo", "pid=,comm=,%cpu=,rss="],
        capture_output=True,
        text=True,
        check=True,
    )

    records = parse_ps_output(result.stdout)
    matches: List[Dict[str, float]] = []

    for record in records:
        command_name = Path(str(record["command"])).name
        normalized_command = normalize_process_name(command_name)
        if normalized_command in lowered_targets:
            matches.append(record)

    return matches


def summarize_snapshot(records: List[Dict[str, float]]) -> Dict[str, float]:
    if not records:
        return {
            "total_cpu_percent": 0.0,
            "total_memory_mb": 0.0,
        }

    total_cpu = round(sum(float(r["cpu_percent"]) for r in records), 2)
    total_memory = round(sum(float(r["memory_mb"]) for r in records), 2)
    return {
        "total_cpu_percent": total_cpu,
        "total_memory_mb": total_memory,
    }


def simulate_metrics(config: BrowserConfig, query: str, trial: int) -> Dict[str, float]:
    seed = sum(ord(char) for char in f"{config.key}|{query}|{trial}")
    avg_cpu = round(8.0 + (seed % 11) * 1.3, 2)
    peak_cpu = round(avg_cpu + 4.5, 2)
    avg_memory = round(180.0 + (seed % 9) * 22.5, 2)
    peak_memory = round(avg_memory + 35.0, 2)
    return {
        "avg_cpu_percent": avg_cpu,
        "peak_cpu_percent": peak_cpu,
        "avg_memory_mb": avg_memory,
        "peak_memory_mb": peak_memory,
    }


def sample_browser_usage(config: BrowserConfig, sample_seconds: int, query: str, trial: int) -> Dict[str, float]:
    if should_simulate():
        return simulate_metrics(config, query, trial)

    cpu_samples: List[float] = []
    memory_samples: List[float] = []

    end_time = time.time() + sample_seconds
    while time.time() < end_time:
        snapshot = collect_process_snapshot(config.process_names)
        totals = summarize_snapshot(snapshot)
        cpu_samples.append(totals["total_cpu_percent"])
        memory_samples.append(totals["total_memory_mb"])
        time.sleep(1)

    if not cpu_samples:
        return {
            "avg_cpu_percent": 0.0,
            "peak_cpu_percent": 0.0,
            "avg_memory_mb": 0.0,
            "peak_memory_mb": 0.0,
        }

    return {
        "avg_cpu_percent": round(sum(cpu_samples) / len(cpu_samples), 2),
        "peak_cpu_percent": round(max(cpu_samples), 2),
        "avg_memory_mb": round(sum(memory_samples) / len(memory_samples), 2),
        "peak_memory_mb": round(max(memory_samples), 2),
    }


def write_csv_header_if_needed(file_path: Path) -> None:
    if file_path.exists():
        return

    with file_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "timestamp",
                "browser",
                "search_engine",
                "query",
                "trial",
                "mode",
                "status",
                "avg_cpu_percent",
                "peak_cpu_percent",
                "avg_memory_mb",
                "peak_memory_mb",
                "load_wait_seconds",
                "sample_seconds",
            ]
        )


def append_result(file_path: Path, row: List[object]) -> None:
    with file_path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(row)


def resolve_query(default_query: str = DEFAULT_QUERY, argv: Optional[List[str]] = None) -> str:
    if argv is None:
        argv = sys.argv

    cli_query = " ".join(part.strip() for part in argv[1:] if part.strip()).strip()
    if cli_query:
        return cli_query

    env_query = os.environ.get("SAFE_WEB_QUERY", "").strip()
    if env_query:
        return env_query

    return default_query


def detect_mode_for_browser(config: BrowserConfig) -> str:
    if should_simulate():
        return "simulated"
    if not app_exists(config.app_path):
        return "simulated"
    return "live"


def run_trial(config: BrowserConfig, query: str, trial: int) -> Dict[str, object]:
    mode = detect_mode_for_browser(config)
    print(f"\nRunning trial {trial} for {config.name} ({mode})...")

    opened = False
    closed = False

    if mode == "live":
        closed = close_browser(config)
        opened = open_search_in_browser(config, query)
        print(f"Waiting {DEFAULT_LOAD_WAIT} seconds for page load...")
        time.sleep(DEFAULT_LOAD_WAIT)
    else:
        print(f"Using simulation mode for {config.name} so the pipeline can run successfully.")

    metrics = sample_browser_usage(config, DEFAULT_SAMPLE_SECONDS, query, trial)

    status_parts: List[str] = []
    if mode == "simulated":
        status_parts.append("simulated_run")
    else:
        status_parts.append("browser_opened" if opened else "open_failed")
        status_parts.append("browser_closed" if closed else "close_skipped_or_failed")

    print(
        f"Finished: {config.name} | CPU avg {metrics['avg_cpu_percent']}% | "
        f"Memory avg {metrics['avg_memory_mb']} MB"
    )

    return {
        "browser": config.name,
        "mode": mode,
        "status": ";".join(status_parts),
        "metrics": metrics,
    }


def main() -> None:
    write_csv_header_if_needed(RESULTS_FILE)

    query = resolve_query()
    print(f"Using search query: {query}")
    print("Target browsers: Safari, Google Chrome, Firefox")

    for key in DEFAULT_BROWSER_ORDER:
        config = BROWSERS[key]

        for trial in range(1, TRIALS_PER_BROWSER + 1):
            result = run_trial(config, query, trial)
            metrics = result["metrics"]

            append_result(
                RESULTS_FILE,
                [
                    datetime.now().isoformat(timespec="seconds"),
                    config.name,
                    "Google",
                    query,
                    trial,
                    result["mode"],
                    result["status"],
                    metrics["avg_cpu_percent"],
                    metrics["peak_cpu_percent"],
                    metrics["avg_memory_mb"],
                    metrics["peak_memory_mb"],
                    DEFAULT_LOAD_WAIT,
                    DEFAULT_SAMPLE_SECONDS,
                ],
            )

    print(f"\nAll done. Results saved to {RESULTS_FILE.resolve()}")
    if should_simulate():
        print("Run completed in simulation mode. This is expected in restricted environments.")
    else:
        print("Run completed in live mode.")


class SafeWebMvpTests(unittest.TestCase):
    def test_browser_keys_present(self) -> None:
        self.assertEqual(list(BROWSERS.keys()), ["safari", "chrome", "firefox"])
        self.assertEqual(BROWSERS["safari"].name, "Safari")
        self.assertEqual(BROWSERS["chrome"].name, "Google Chrome")
        self.assertEqual(BROWSERS["firefox"].name, "Firefox")

    def test_normalize_process_name(self) -> None:
        self.assertEqual(normalize_process_name(" Safari "), "safari")
        self.assertEqual(normalize_process_name("Google Chrome"), "google chrome")

    def test_parse_ps_output(self) -> None:
        sample = "123 /Applications/Safari.app/Contents/MacOS/Safari 12.5 204800\n456 firefox 8.0 102400\n"
        rows = parse_ps_output(sample)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["pid"], 123)
        self.assertAlmostEqual(rows[0]["cpu_percent"], 12.5)
        self.assertAlmostEqual(rows[0]["memory_mb"], 200.0)
        self.assertEqual(rows[1]["command"], "firefox")

    def test_summarize_snapshot(self) -> None:
        records = [
            {"pid": 1, "command": "Safari", "cpu_percent": 10.0, "memory_mb": 100.0},
            {"pid": 2, "command": "Safari", "cpu_percent": 5.5, "memory_mb": 25.25},
        ]
        totals = summarize_snapshot(records)
        self.assertEqual(totals["total_cpu_percent"], 15.5)
        self.assertEqual(totals["total_memory_mb"], 125.25)

    def test_summarize_empty_snapshot(self) -> None:
        totals = summarize_snapshot([])
        self.assertEqual(totals["total_cpu_percent"], 0.0)
        self.assertEqual(totals["total_memory_mb"], 0.0)

    def test_resolve_query_from_cli_args(self) -> None:
        query = resolve_query(argv=["safe_web_mvp.py", "duckduckgo", "privacy", "test"])
        self.assertEqual(query, "duckduckgo privacy test")

    def test_resolve_query_from_environment(self) -> None:
        original = os.environ.get("SAFE_WEB_QUERY")
        try:
            os.environ["SAFE_WEB_QUERY"] = "energy efficient browsers"
            query = resolve_query(argv=["safe_web_mvp.py"])
            self.assertEqual(query, "energy efficient browsers")
        finally:
            if original is None:
                os.environ.pop("SAFE_WEB_QUERY", None)
            else:
                os.environ["SAFE_WEB_QUERY"] = original

    def test_resolve_query_falls_back_to_default(self) -> None:
        original = os.environ.get("SAFE_WEB_QUERY")
        try:
            os.environ.pop("SAFE_WEB_QUERY", None)
            query = resolve_query(argv=["safe_web_mvp.py"])
            self.assertEqual(query, DEFAULT_QUERY)
        finally:
            if original is not None:
                os.environ["SAFE_WEB_QUERY"] = original

    def test_simulate_metrics_are_stable(self) -> None:
        metrics_one = simulate_metrics(BROWSERS["safari"], "privacy", 1)
        metrics_two = simulate_metrics(BROWSERS["safari"], "privacy", 1)
        self.assertEqual(metrics_one, metrics_two)
        self.assertGreater(metrics_one["avg_cpu_percent"], 0.0)
        self.assertGreater(metrics_one["avg_memory_mb"], 0.0)

    def test_detect_mode_for_browser_simulated_when_app_missing(self) -> None:
        fake = BrowserConfig(
            key="fake",
            name="Fake Browser",
            app_path="/Applications/DefinitelyMissing.app",
            app_name="DefinitelyMissing",
            process_names=["fake"],
            search_url_template="https://example.com?q={query}",
        )
        self.assertEqual(detect_mode_for_browser(fake), "simulated")


if __name__ == "__main__":
    main()
