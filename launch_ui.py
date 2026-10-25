"""
Mission Control UI Launcher
Starts the interactive executive web interface and automatically opens it in the default browser.
"""

import webbrowser
import time
import threading
from web_dashboard.app import app, ensure_testbench

PORT = 5000


def open_browser():
    time.sleep(1.2)
    webbrowser.open(f"http://127.0.0.1:{PORT}")


if __name__ == "__main__":
    ensure_testbench()
    threading.Thread(target=open_browser, daemon=True).start()
    print(f"\n========================================================")
    print(f"🚀 Mission Control Dashboard running on: http://127.0.0.1:{PORT}")
    print(f"========================================================\n")
    app.run(host="127.0.0.1", port=PORT, debug=False)
