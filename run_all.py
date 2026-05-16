#!/usr/bin/env python3
"""run_all.py
Start the surveillance pipeline together with the FastAPI server and React dashboard.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

from run_dashboard import run_api_server, run_react_dashboard


def run_pipeline(api_port: int = 8000):
    print("Starting surveillance pipeline...")
    env = os.environ.copy()
    env["API_BASE_URL"] = f"http://localhost:{api_port}"
    pipeline_process = subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=Path(__file__).parent,
        env=env,
    )
    return pipeline_process


def main():
    print("Starting Full Surveillance Stack")
    print("=" * 50)

    api_process, api_port = run_api_server()
    time.sleep(2)

    react_process, dashboard_port = run_react_dashboard(api_port)
    pipeline_process = run_pipeline(api_port)

    print("\nServices:")
    print(f"  API: http://localhost:{api_port}")
    print(f"  Dashboard: http://localhost:{dashboard_port}")
    print("  Pipeline: running main.py for camera input")
    print("\nPress Ctrl+C to stop all services")

    try:
        while True:
            time.sleep(1)
            if any(proc.poll() is not None for proc in (api_process, react_process, pipeline_process)):
                break
    except KeyboardInterrupt:
        print("\nStopping all services...")
    finally:
        for proc in (pipeline_process, api_process, react_process):
            if proc and proc.poll() is None:
                proc.terminate()
        for proc in (pipeline_process, api_process, react_process):
            if proc:
                proc.wait()
        print("All services stopped")


if __name__ == "__main__":
    main()
