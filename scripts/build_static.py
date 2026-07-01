"""
Build script for GitHub Pages static deployment.
Runs the scraper, fetches temperatures, and outputs:
  _site/sessions.json  — data file loaded by index.html
  _site/index.html     — static HTML page
"""
import json
import os
import shutil
import sys
from datetime import datetime

# Allow importing scraper/weather from the repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import scrape_all
from weather import fetch_weather, get_temperature

OUT_DIR = "_site"


def main():
    print("Scraping cinemas...")
    sessions = scrape_all()

    print("Fetching temperatures...")
    temps, daily_temps = fetch_weather()
    for s in sessions:
        s["temperature"] = get_temperature(temps, s["date"], s["heure"])

    data = {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "sessions": sessions,
        "daily_temps": daily_temps,
    }

    os.makedirs(OUT_DIR, exist_ok=True)

    json_path = os.path.join(OUT_DIR, "sessions.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    print(f"Saved {len(sessions)} sessions → {json_path}")

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    html_src = os.path.join(repo_root, "templates", "index.html")
    html_dst = os.path.join(OUT_DIR, "index.html")
    shutil.copy2(html_src, html_dst)
    print(f"Copied index.html → {html_dst}")

    print(f"Build complete. {OUT_DIR}/ ready for deployment.")


if __name__ == "__main__":
    main()
