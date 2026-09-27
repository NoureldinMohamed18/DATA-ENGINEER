"""
run_pipeline.py
-----------------
Runs the full E-T-L pipeline in order: extract -> transform -> load.

This mirrors the "pipeline as a graph of dependent tasks" idea from the
Data Pipelines material: each step only makes sense after the previous
one has completed, so we run them strictly in sequence and stop if any
step fails.

Usage:
    python run_pipeline.py               # scrapes the live site
    python run_pipeline.py --offline     # uses the local HTML fixture (no internet needed)
"""
import argparse
import subprocess
import sys

def run_step(command: list[str], step_name: str) -> None:
    print(f"\n{'=' * 60}\nSTEP: {step_name}\n{'=' * 60}")
    result = subprocess.run([sys.executable] + command)
    if result.returncode != 0:
        print(f"[PIPELINE] Step '{step_name}' failed. Stopping pipeline.")
        sys.exit(1)
        
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="Use local HTML fixture instead of live scraping")
    parser.add_argument("--pages", type=int, default=5, help="Number of pages to scrape (live mode only)")
    args = parser.parse_args()

    extract_cmd = ["extract.py"]
    if args.offline:
        extract_cmd.append("--offline")
    else:
        extract_cmd += ["--pages", str(args.pages)]

    run_step(extract_cmd, "EXTRACT")
    run_step(["transform.py"], "TRANSFORM")
    run_step(["load.py"], "LOAD")

    print("\n[PIPELINE] Completed successfully. Data is ready in books.db")


if __name__ == "__main__":
    main()
    