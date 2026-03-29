import csv
import sys
import unittest
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Safe Web MVP + DASHBOARD
# Alpha-friendly prototype for Safari, Chrome, and Firefox.
#
# This version uses simulation mode for reliable demo runs and includes
# a terminal dashboard that summarizes CSV results.
#
# Important compatibility note:
# Older CSV files may have different header names. The dashboard now
# supports both the current compact headers and older metric headers.


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
        process_names=["Google Chrome", "Google Chrome Helper"],
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


# Store results inside backend/data for clean project structure
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
RESULTS_FILE = DATA_DIR / "safe_web_results.csv"
DEFAULT_QUERY = "browser privacy comparison"
DEFAULT_LOAD_WAIT = 2
DEFAULT_SAMPLE_SECONDS = 2
TRIALS_PER_BROWSER = 1
DEFAULT_BROWSER_ORDER = ["safari", "chrome", "firefox"]
CURRENT_HEADERS = ["timestamp", "browser", "cpu", "memory"]
CPU_HEADER_CANDIDATES = ["cpu", "avg_cpu_percent"]
MEMORY_HEADER_CANDIDATES = ["memory", "avg_memory_mb"]


def should_simulate() -> bool:
    return True


def simulate_metrics(config: BrowserConfig, query: str, trial: int) -> Dict[str, float]:
    seed = sum(ord(char) for char in f"{config.key}|{query}|{trial}")
    return {
        "avg_cpu_percent": round(10 + (seed % 10), 2),
        "peak_cpu_percent": round(15 + (seed % 10), 2),
        "avg_memory_mb": round(200 + (seed % 50), 2),
        "peak_memory_mb": round(250 + (seed % 50), 2),
    }


def resolve_query() -> str:
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:])
    return DEFAULT_QUERY


def write_csv_header_if_needed(file_path: Path = RESULTS_FILE) -> None:
    if file_path.exists():
        return

    with file_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(CURRENT_HEADERS)


def append_result(browser: str, metrics: Dict[str, float], file_path: Path = RESULTS_FILE) -> None:
    with file_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                datetime.now().isoformat(timespec="seconds"),
                browser,
                metrics["avg_cpu_percent"],
                metrics["avg_memory_mb"],
            ]
        )


def detect_metric_headers(fieldnames: Optional[List[str]]) -> Tuple[str, str]:
    if not fieldnames:
        raise ValueError("CSV file is missing a header row.")

    cpu_header = next((name for name in CPU_HEADER_CANDIDATES if name in fieldnames), None)
    memory_header = next((name for name in MEMORY_HEADER_CANDIDATES if name in fieldnames), None)

    if cpu_header is None or memory_header is None:
        raise ValueError(
            "CSV file is missing required metric columns. Expected one of "
            f"{CPU_HEADER_CANDIDATES} for CPU and one of {MEMORY_HEADER_CANDIDATES} for memory. "
            f"Found columns: {fieldnames}"
        )

    return cpu_header, memory_header


def load_dashboard_data(file_path: Path = RESULTS_FILE) -> Dict[str, List[Dict[str, float]]]:
    data: Dict[str, List[Dict[str, float]]] = defaultdict(list)

    with file_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        cpu_header, memory_header = detect_metric_headers(reader.fieldnames)

        for row in reader:
            browser_name = (row.get("browser") or "Unknown Browser").strip() or "Unknown Browser"
            cpu_value = row.get(cpu_header, "")
            memory_value = row.get(memory_header, "")

            if cpu_value in (None, "") or memory_value in (None, ""):
                continue

            data[browser_name].append(
                {
                    "cpu": float(cpu_value),
                    "memory": float(memory_value),
                }
            )

    return data


def generate_dashboard(file_path: Path = RESULTS_FILE) -> None:
    print("\n📊 DASHBOARD RESULTS")
    print("=" * 40)

    if not file_path.exists():
        print("No data available")
        return

    data = load_dashboard_data(file_path)
    if not data:
        print("No usable rows found in the CSV file")
        return

    for browser, values in data.items():
        avg_cpu = sum(item["cpu"] for item in values) / len(values)
        avg_memory = sum(item["memory"] for item in values) / len(values)

        print(f"\n{browser}")
        print(f"  Avg CPU: {avg_cpu:.2f}%")
        print(f"  Avg Memory: {avg_memory:.2f} MB")


def run_trial(config: BrowserConfig, query: str, trial: int) -> Dict[str, float]:
    print(f"Running {config.name}...")
    return simulate_metrics(config, query, trial)


def main() -> None:
    write_csv_header_if_needed()

    query = resolve_query()
    print(f"Query: {query}")

    for key in DEFAULT_BROWSER_ORDER:
        config = BROWSERS[key]
        metrics = run_trial(config, query, 1)
        append_result(config.name, metrics)

    print("\nRun complete!")
    generate_dashboard()


class TestDashboard(unittest.TestCase):
    def setUp(self) -> None:
        self.test_file = Path("test_safe_web_results.csv")
        if self.test_file.exists():
            self.test_file.unlink()

    def tearDown(self) -> None:
        if self.test_file.exists():
            self.test_file.unlink()

    def test_simulation_returns_values(self) -> None:
        metrics = simulate_metrics(BROWSERS["safari"], "test", 1)
        self.assertTrue(metrics["avg_cpu_percent"] > 0)
        self.assertTrue(metrics["avg_memory_mb"] > 0)

    def test_write_header_and_append_current_format(self) -> None:
        write_csv_header_if_needed(self.test_file)
        append_result("Safari", simulate_metrics(BROWSERS["safari"], "test", 1), self.test_file)

        loaded = load_dashboard_data(self.test_file)
        self.assertIn("Safari", loaded)
        self.assertEqual(len(loaded["Safari"]), 1)

    def test_load_dashboard_data_supports_legacy_headers(self) -> None:
        with self.test_file.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["timestamp", "browser", "avg_cpu_percent", "avg_memory_mb"])
            writer.writerow(["2026-03-29T12:00:00", "Firefox", "12.5", "220.0"])

        loaded = load_dashboard_data(self.test_file)
        self.assertEqual(loaded["Firefox"][0]["cpu"], 12.5)
        self.assertEqual(loaded["Firefox"][0]["memory"], 220.0)

    def test_detect_metric_headers_current(self) -> None:
        cpu_header, memory_header = detect_metric_headers(["timestamp", "browser", "cpu", "memory"])
        self.assertEqual(cpu_header, "cpu")
        self.assertEqual(memory_header, "memory")

    def test_detect_metric_headers_legacy(self) -> None:
        cpu_header, memory_header = detect_metric_headers(["timestamp", "browser", "avg_cpu_percent", "avg_memory_mb"])
        self.assertEqual(cpu_header, "avg_cpu_percent")
        self.assertEqual(memory_header, "avg_memory_mb")

    def test_detect_metric_headers_raises_for_missing_columns(self) -> None:
        with self.assertRaises(ValueError):
            detect_metric_headers(["timestamp", "browser", "peak_cpu_percent"])


if __name__ == "__main__":
    main()

