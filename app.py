"""Run the local web application: python app.py [--open]."""
import argparse
import json
import threading
import time
import urllib.request
import webbrowser

from app import create_app

app = create_app()


def open_when_ready(url):
    for _ in range(60):
        try:
            with urllib.request.urlopen(url + "/api/health", timeout=0.5) as response:
                health = json.load(response)
                if health.get("status") == "ok" and health.get("service") == "Assignment Statement DFA Validator":
                    webbrowser.open(url)
                    return
        except (OSError, ValueError):
            time.sleep(0.25)


def main():
    parser = argparse.ArgumentParser(description="Assignment Statement DFA Validator")
    parser.add_argument("--open", action="store_true", help="Open the browser after localhost is ready")
    args = parser.parse_args()
    url = "http://127.0.0.1:5000"
    print(f"Assignment Statement DFA Validator: {url}\nPress Ctrl+C to stop.", flush=True)
    if args.open:
        threading.Thread(target=open_when_ready, args=(url,), daemon=True).start()
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
