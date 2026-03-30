import csv
import json
import sys
import unittest
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import DefaultDict, Dict, List, Optional, Tuple


# Safe Web MVP + DASHBOARD


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


DEFAULT_QUERY = "browser privacy comparison"
DEFAULT_BROWSER_ORDER = ["safari", "chrome", "firefox"]
CURRENT_HEADERS = ["timestamp", "browser", "cpu", "memory"]
CPU_HEADER_CANDIDATES = ["cpu", "avg_cpu_percent"]
MEMORY_HEADER_CANDIDATES = ["memory", "avg_memory_mb"]


def resolve_base_dir() -> Path:
    """Return a stable base directory in both script and sandbox environments."""
    if "__file__" in globals():
        return Path(__file__).resolve().parent
    return Path.cwd().resolve()


# Backend storage
BASE_DIR = resolve_base_dir()
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
RESULTS_FILE = DATA_DIR / "safe_web_results.csv"


def simulate_metrics(config: BrowserConfig, query: str, trial: int) -> Dict[str, float]:
    seed = sum(ord(char) for char in f"{config.key}|{query}|{trial}")
    return {
        "avg_cpu_percent": round(10 + (seed % 10), 2),
        "avg_memory_mb": round(200 + (seed % 50), 2),
    }


def resolve_query(argv: Optional[List[str]] = None) -> str:
    args = sys.argv if argv is None else argv
    return " ".join(args[1:]) if len(args) > 1 else DEFAULT_QUERY


def write_csv_header_if_needed(results_file: Path = RESULTS_FILE) -> None:
    results_file.parent.mkdir(parents=True, exist_ok=True)
    if not results_file.exists():
        with results_file.open("w", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerow(CURRENT_HEADERS)


def append_result(browser: str, metrics: Dict[str, float], results_file: Path = RESULTS_FILE) -> None:
    results_file.parent.mkdir(parents=True, exist_ok=True)
    with results_file.open("a", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerow(
            [
                datetime.now().isoformat(timespec="seconds"),
                browser,
                metrics["avg_cpu_percent"],
                metrics["avg_memory_mb"],
            ]
        )


def detect_metric_headers(fieldnames: Optional[List[str]]) -> Tuple[str, str]:
    if not fieldnames:
        raise ValueError("CSV header row is missing.")

    cpu_header = next((name for name in CPU_HEADER_CANDIDATES if name in fieldnames), None)
    memory_header = next((name for name in MEMORY_HEADER_CANDIDATES if name in fieldnames), None)

    if not cpu_header or not memory_header:
        raise ValueError("Missing CPU or Memory columns")

    return cpu_header, memory_header


def load_dashboard_data(results_file: Path = RESULTS_FILE) -> DefaultDict[str, List[Dict[str, float]]]:
    data: DefaultDict[str, List[Dict[str, float]]] = defaultdict(list)

    if not results_file.exists():
        return data

    with results_file.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        cpu_header, memory_header = detect_metric_headers(reader.fieldnames)
        for row in reader:
            browser_name = row.get("browser", "").strip()
            if not browser_name:
                continue
            data[browser_name].append(
                {
                    "cpu": float(row[cpu_header]),
                    "memory": float(row[memory_header]),
                }
            )
    return data


def export_dashboard_json(
    results_file: Path = RESULTS_FILE,
    frontend_data_dir: Optional[Path] = None,
) -> Path:
    data = load_dashboard_data(results_file)
    rows: List[Dict[str, float | str]] = []

    for browser, values in data.items():
        for value in values:
            rows.append(
                {
                    "browser": browser,
                    "cpu": value["cpu"],
                    "memory": value["memory"],
                }
            )

    output_dir = frontend_data_dir or (BASE_DIR.parent / "frontend" / "src" / "data")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "backendResults.json"

    with output_file.open("w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2)

    print(f"Exported JSON → {output_file}")
    return output_file


def generate_dashboard(results_file: Path = RESULTS_FILE) -> None:
    print("\n📊 DASHBOARD RESULTS")
    print("=" * 40)

    data = load_dashboard_data(results_file)
    if not data:
        print("No data available")
        return

    for browser, values in data.items():
        avg_cpu = sum(value["cpu"] for value in values) / len(values)
        avg_mem = sum(value["memory"] for value in values) / len(values)
        print(f"\n{browser}")
        print(f"  Avg CPU: {avg_cpu:.2f}%")
        print(f"  Avg Memory: {avg_mem:.2f} MB")


def main() -> None:
    write_csv_header_if_needed()
    query = resolve_query()

    for key in DEFAULT_BROWSER_ORDER:
        config = BROWSERS[key]
        metrics = simulate_metrics(config, query, 1)
        append_result(config.name, metrics)

    print("\nRun complete!")
    export_dashboard_json()
    generate_dashboard()


class SafeWebMvpTests(unittest.TestCase):
    def test_resolve_base_dir_without___file__(self) -> None:
        original_file = globals().pop("__file__", None)
        try:
            self.assertEqual(resolve_base_dir(), Path.cwd().resolve())
        finally:
            if original_file is not None:
                globals()["__file__"] = original_file

    def test_resolve_query_uses_default(self) -> None:
        self.assertEqual(resolve_query(["safe_web_mvp.py"]), DEFAULT_QUERY)

    def test_resolve_query_uses_cli_args(self) -> None:
        self.assertEqual(
            resolve_query(["safe_web_mvp.py", "private", "search"]),
            "private search",
        )

    def test_detect_metric_headers_current(self) -> None:
        self.assertEqual(
            detect_metric_headers(["timestamp", "browser", "cpu", "memory"]),
            ("cpu", "memory"),
        )

    def test_detect_metric_headers_legacy(self) -> None:
        self.assertEqual(
            detect_metric_headers(["timestamp", "browser", "avg_cpu_percent", "avg_memory_mb"]),
            ("avg_cpu_percent", "avg_memory_mb"),
        )

    def test_export_dashboard_json_creates_output(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            results_file = temp_path / "data" / "safe_web_results.csv"
            frontend_data_dir = temp_path / "frontend" / "src" / "data"

            write_csv_header_if_needed(results_file)
            append_result("Safari", {"avg_cpu_percent": 12.5, "avg_memory_mb": 220.0}, results_file)
            append_result("Firefox", {"avg_cpu_percent": 14.0, "avg_memory_mb": 230.0}, results_file)

            output_file = export_dashboard_json(results_file, frontend_data_dir)
            self.assertTrue(output_file.exists())

            with output_file.open("r", encoding="utf-8") as handle:
                rows = json.load(handle)

            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["browser"], "Safari")
            self.assertIn("cpu", rows[0])
            self.assertIn("memory", rows[0])


if __name__ == "__main__":
    main()


