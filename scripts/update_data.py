"""
Data-only update script for the cron job.
Runs the scraper, fetches temperatures, and writes sessions.json to the repo root.
No HTML generation or Pages deployment — just the data file.
"""
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import scrape_all
from weather import fetch_weather, get_temperature

OUT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sessions.json")


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

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    print(f"Saved {len(sessions)} sessions → {OUT_PATH}")


if __name__ == "__main__":
    main()
