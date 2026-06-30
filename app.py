import json
import os
import threading
import webbrowser
from datetime import datetime

from flask import Flask, render_template, jsonify

from scraper import scrape_all
from weather import fetch_temperatures, get_temperature

app = Flask(__name__)
DATA_FILE = os.path.join("data", "sessions.json")


def load_sessions():
    if not os.path.exists(DATA_FILE):
        return {"updated_at": None, "sessions": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_sessions(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def run_scrape(progress_callback=None):
    sessions = scrape_all(progress_callback=progress_callback)
    temps = fetch_temperatures()
    for s in sessions:
        s["temperature"] = get_temperature(temps, s["date"], s["heure"])
    data = {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "sessions": sessions,
    }
    save_sessions(data)
    return len(sessions)


@app.route("/")
def index():
    data = load_sessions()
    return render_template(
        "index.html",
        sessions_json=json.dumps(data, ensure_ascii=False),
    )


@app.route("/refresh", methods=["POST"])
def refresh():
    count = run_scrape()
    data = load_sessions()
    return jsonify({"status": "ok", "count": count, "updated_at": data["updated_at"]})


if __name__ == "__main__":
    if not os.path.exists(DATA_FILE) and os.environ.get("TESTING") != "1":
        print("Premier lancement — scraping initial (~3 min)...")
        run_scrape()
    if os.environ.get("TESTING") != "1":
        threading.Timer(1.0, lambda: webbrowser.open("http://localhost:5000")).start()
    app.run(debug=False, port=5000)
