"""
run_pipeline.py
-----------------
Runs extract -> transform -> load in sequence for Project 4.

Run this once a day (e.g. via a scheduler/cron, or manually) to keep
repos.db up to date. Because load.py does incremental upserts, running
this repeatedly is safe and cheap — unchanged repos are simply skipped.

Usage:
    python run_pipeline.py --user torvalds
    python run_pipeline.py --offline
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
    parser.add_argument("--user", default="torvalds", help="GitHub username to track")
    parser.add_argument("--offline", action="store_true", help="Use local sample_response.json instead of the live API")
    args = parser.parse_args()

    extract_cmd = ["extract.py", "--user", args.user]
    if args.offline:
        extract_cmd.append("--offline")

    run_step(extract_cmd, "EXTRACT (GitHub API)")
    run_step(["transform.py"], "TRANSFORM")
    run_step(["load.py"], "LOAD (incremental upsert)")

    print("\n[PIPELINE] Done. Start the API with: python api.py")


if __name__ == "__main__":
    main()
