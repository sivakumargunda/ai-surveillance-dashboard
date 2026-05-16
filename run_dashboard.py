#!/usr/bin/env python3
"""
run_dashboard.py
Script to run both the FastAPI server and React dashboard.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

def run_api_server(port: int | None = None):
    """Run the FastAPI server."""
    if port is None:
        port = _find_open_port(8000, 8100)
    print("Starting FastAPI server...")
    api_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "api:app",
        "--host", "0.0.0.0",
        "--port", str(port),
        "--reload"
    ], cwd=Path(__file__).parent)
    return api_process, port

def _find_open_port(start_port: int = 3000, max_port: int = 3100) -> int:
    import socket

    port = start_port
    while port <= max_port:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(("127.0.0.1", port))
            if result != 0:
                return port
            port += 1
    raise RuntimeError("No available port found for React dashboard")


def run_react_dashboard(api_port: int = 8000):
    """Run the React dashboard."""
    print("Starting React dashboard...")
    frontend_dir = Path(__file__).parent / "frontend"
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"

    # Install dependencies if node_modules doesn't exist
    if not (frontend_dir / "node_modules").exists():
        print("Installing React dependencies...")
        subprocess.run([npm_cmd, "install"], cwd=frontend_dir, check=True)

    port = _find_open_port(3000)
    env = os.environ.copy()
    env["PORT"] = str(port)
    env["REACT_APP_API_BASE_URL"] = f"http://localhost:{api_port}"

    # Start the React development server on the chosen port
    react_process = subprocess.Popen([
        npm_cmd, "start"
    ], cwd=frontend_dir, env=env)
    return react_process, port

def main():
    print("Starting Surveillance Dashboard")
    print("=" * 50)

    # Start API server
    api_process, api_port = run_api_server()
    time.sleep(2)  # Give API server time to start

    # Start React dashboard
    react_process, dashboard_port = run_react_dashboard(api_port)

    print("\nDashboard URLs:")
    print(f"  API: http://localhost:{api_port}")
    print(f"  Dashboard: http://localhost:{dashboard_port}")
    print(f"  API Docs: http://localhost:{api_port}/docs")
    print("\nPress Ctrl+C to stop all services")

    try:
        # Wait for both processes
        api_process.wait()
        react_process.wait()
    except KeyboardInterrupt:
        print("\nStopping services...")
        api_process.terminate()
        react_process.terminate()
        api_process.wait()
        react_process.wait()
        print("All services stopped")

if __name__ == "__main__":
    main()
