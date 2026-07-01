import json
import os
import threading
import webbrowser
from datetime import datetime

from flask import Flask, render_template, jsonify

from scraper import scrape_all
from weather import fetch_weather, get_temperature

app = Flask(__name__)
DATA_FILE = os.path.join("data", "sessions.json")

_scrape_lock = threading.Lock()
_scrape_state = {
    "running": False, "current": 0, "total": 0,
    "cinema": "", "done": False, "count": 0, "error": None
}


def load_sessions():
    if not os.path.exists(DATA_FILE):
        return {"updated_at": None, "sessions": [], "daily_temps": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_sessions(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def run_scrape(progress_callback=None):
    sessions = scrape_all(progress_callback=progress_callback)
    temps, daily_temps = fetch_weather()
    for s in sessions:
        s["temperature"] = get_temperature(temps, s["date"], s["heure"])
    data = {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "sessions": sessions,
        "daily_temps": daily_temps,
    }
    save_sessions(data)
    return len(sessions)


@app.route("/")
def index():
    return render_template("index.html")


def _run_scrape_background():
    def cb(current, total, cinema_name):
        with _scrape_lock:
            _scrape_state.update({"current": current, "total": total, "cinema": cinema_name})
    try:
        count = run_scrape(progress_callback=cb)
        with _scrape_lock:
            _scrape_state.update({"done": True, "count": count, "running": False})
    except Exception as e:
        with _scrape_lock:
            _scrape_state.update({"done": True, "error": str(e), "running": False})


@app.route("/refresh", methods=["POST"])
def refresh():
    with _scrape_lock:
        if _scrape_state["running"]:
            return jsonify({"status": "already_running"}), 409
        _scrape_state.update({
            "running": True, "current": 0, "total": 0,
            "cinema": "", "done": False, "count": 0, "error": None
        })
    threading.Thread(target=_run_scrape_background, daemon=True).start()
    return jsonify({"status": "started"})


@app.route("/progress")
def progress():
    with _scrape_lock:
        return jsonify(dict(_scrape_state))


@app.route("/sessions.json")
def sessions_data():
    return jsonify(load_sessions())


if __name__ == "__main__":
    if not os.path.exists(DATA_FILE) and os.environ.get("TESTING") != "1":
        print("Planificateur Ciné Canicule — scraping initial (~3 min)...")
        run_scrape()
    if os.environ.get("TESTING") != "1":
        threading.Timer(1.0, lambda: webbrowser.open("http://localhost:5000")).start()
    app.run(debug=False, port=5000)
