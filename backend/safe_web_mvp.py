import csv
import json
import statistics
import time
from datetime import datetime
from pathlib import Path

import psutil
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


URLS_TO_TEST = [
    "https://example.com",
    "https://www.wikipedia.org",
    "https://news.ycombinator.com",
]

TRIALS_PER_BROWSER = 3
SAMPLE_SECONDS = 5
SAMPLE_INTERVAL = 0.5

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

CSV_PATH = DATA_DIR / "safe_web_results.csv"
JSON_PATH = DATA_DIR / "safe_web_results_real.json"

BROWSERS = ["chromium", "firefox", "webkit"]


def get_browser_type(playwright_obj, browser_name):
    mapping = {
        "chromium": playwright_obj.chromium,
        "firefox": playwright_obj.firefox,
        "webkit": playwright_obj.webkit,
    }
    return mapping[browser_name]


def collect_process_tree_metrics(root_pid, sample_seconds=5, interval=0.5):
    try:
        root = psutil.Process(root_pid)
    except psutil.NoSuchProcess:
        return {
            "avg_cpu_percent": 0.0,
            "peak_cpu_percent": 0.0,
            "avg_rss_mb": 0.0,
            "peak_rss_mb": 0.0,
        }

    processes = [root] + root.children(recursive=True)
    for proc in processes:
        try:
            proc.cpu_percent(interval=None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    cpu_samples = []
    rss_samples = []

    end_time = time.time() + sample_seconds
    while time.time() < end_time:
        total_cpu = 0.0
        total_rss = 0

        try:
            current_processes = [root] + root.children(recursive=True)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            current_processes = []

        for proc in current_processes:
            try:
                total_cpu += proc.cpu_percent(interval=None)
                total_rss += proc.memory_info().rss
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        cpu_samples.append(total_cpu)
        rss_samples.append(total_rss / (1024 * 1024))
        time.sleep(interval)

    return {
        "avg_cpu_percent": round(statistics.mean(cpu_samples), 2) if cpu_samples else 0.0,
        "peak_cpu_percent": round(max(cpu_samples), 2) if cpu_samples else 0.0,
        "avg_rss_mb": round(statistics.mean(rss_samples), 2) if rss_samples else 0.0,
        "peak_rss_mb": round(max(rss_samples), 2) if rss_samples else 0.0,
    }


def run_trial(playwright_obj, browser_name, url, trial_num):
    browser_type = get_browser_type(playwright_obj, browser_name)

    browser = None
    context = None
    page = None

    started_at = datetime.now().isoformat()

    try:
        browser = browser_type.launch(headless=True)
        browser_pid = None

        context = browser.new_context()
        page = context.new_page()

        nav_start = time.perf_counter()
        page.goto(url, wait_until="load", timeout=30000)
        page.wait_for_timeout(2000)
        load_time_sec = round(time.perf_counter() - nav_start, 3)

        metrics = (
    collect_process_tree_metrics(browser_pid, SAMPLE_SECONDS, SAMPLE_INTERVAL)
    if browser_pid
    else {
        "avg_cpu_percent": 0.0,
        "peak_cpu_percent": 0.0,
        "avg_rss_mb": 0.0,
        "peak_rss_mb": 0.0,
    }
)

        result = {
            "timestamp": started_at,
            "browser": browser_name,
            "url": url,
            "trial": trial_num,
            "success": True,
            "load_time_sec": load_time_sec,
            "avg_cpu_percent": metrics["avg_cpu_percent"],
            "peak_cpu_percent": metrics["peak_cpu_percent"],
            "avg_rss_mb": metrics["avg_rss_mb"],
            "peak_rss_mb": metrics["peak_rss_mb"],
            "error": "",
        }

    except PlaywrightTimeoutError:
        result = {
            "timestamp": started_at,
            "browser": browser_name,
            "url": url,
            "trial": trial_num,
            "success": False,
            "load_time_sec": None,
            "avg_cpu_percent": None,
            "peak_cpu_percent": None,
            "avg_rss_mb": None,
            "peak_rss_mb": None,
            "error": "Navigation timeout",
        }
    except Exception as e:
        result = {
            "timestamp": started_at,
            "browser": browser_name,
            "url": url,
            "trial": trial_num,
            "success": False,
            "load_time_sec": None,
            "avg_cpu_percent": None,
            "peak_cpu_percent": None,
            "avg_rss_mb": None,
            "peak_rss_mb": None,
            "error": str(e),
        }
    finally:
        try:
            if page:
                page.close()
        except Exception:
            pass
        try:
            if context:
                context.close()
        except Exception:
            pass
        try:
            if browser:
                browser.close()
        except Exception:
            pass

    print(
        f"[{browser_name}] Trial {trial_num} | URL={url} | "
        f"success={result['success']} | error={result['error'] or 'none'}"
    )
    return result


def summarize_results(results):
    summary = []

    for browser_name in BROWSERS:
        browser_results = [
            row for row in results
            if row["browser"] == browser_name and row["success"]
        ]

        if not browser_results:
            summary.append({
                "browser": browser_name,
                "runs": 0,
                "avg_load_time_sec": None,
                "avg_cpu_percent": None,
                "peak_cpu_percent": None,
                "avg_rss_mb": None,
                "peak_rss_mb": None,
            })
            continue

        avg_load_times = [row["load_time_sec"] for row in browser_results if row["load_time_sec"] is not None]
        avg_cpu_vals = [row["avg_cpu_percent"] for row in browser_results if row["avg_cpu_percent"] is not None]
        peak_cpu_vals = [row["peak_cpu_percent"] for row in browser_results if row["peak_cpu_percent"] is not None]
        avg_rss_vals = [row["avg_rss_mb"] for row in browser_results if row["avg_rss_mb"] is not None]
        peak_rss_vals = [row["peak_rss_mb"] for row in browser_results if row["peak_rss_mb"] is not None]

        summary.append({
            "browser": browser_name,
            "runs": len(browser_results),
            "avg_load_time_sec": round(statistics.mean(avg_load_times), 2) if avg_load_times else None,
            "avg_cpu_percent": round(statistics.mean(avg_cpu_vals), 2) if avg_cpu_vals else None,
            "peak_cpu_percent": round(max(peak_cpu_vals), 2) if peak_cpu_vals else None,
            "avg_rss_mb": round(statistics.mean(avg_rss_vals), 2) if avg_rss_vals else None,
            "peak_rss_mb": round(max(peak_rss_vals), 2) if peak_rss_vals else None,
        })

    return summary


def save_csv(results):
    fieldnames = [
        "timestamp",
        "browser",
        "url",
        "trial",
        "success",
        "load_time_sec",
        "avg_cpu_percent",
        "peak_cpu_percent",
        "avg_rss_mb",
        "peak_rss_mb",
        "error",
    ]

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def save_json(results, summary):
    payload = {
        "generated_at": datetime.now().isoformat(),
        "config": {
            "urls_tested": URLS_TO_TEST,
            "trials_per_browser": TRIALS_PER_BROWSER,
            "sample_seconds": SAMPLE_SECONDS,
            "sample_interval": SAMPLE_INTERVAL,
            "browsers": BROWSERS,
        },
        "summary": summary,
        "results": results,
    }

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def main():
    all_results = []

    with sync_playwright() as p:
        for browser_name in BROWSERS:
            for url in URLS_TO_TEST:
                for trial in range(1, TRIALS_PER_BROWSER + 1):
                    result = run_trial(p, browser_name, url, trial)
                    all_results.append(result)

    summary = summarize_results(all_results)
    save_csv(all_results)
    save_json(all_results, summary)

    print(f"\nSaved CSV to: {CSV_PATH}")
    print(f"Saved JSON to: {JSON_PATH}")


if __name__ == "__main__":
    main()
