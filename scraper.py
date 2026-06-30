import time
from datetime import datetime, timedelta

from allocineAPI.allocineAPI import allocineAPI

CINEMA_IDS = {
    "Pathé Bellecour":   "P0012",
    "Lumière Terreaux":  "P0017",
    "Lumière Fourmi":    "W6903",
    "Lumière Bellecour": "P0015",
    "Le Cinéma":         "P0009",
    "Cinéma Opéra":      "P0006",
    "Le Zola":           "P0014",
    "UGC Part-Dieu":     "P0036",
    "Institut Lumière":  "P0050",
}

# Map allocineAPI diffusionVersion values to display labels
_VERSION_MAP = {
    "DUBBED": "VF",
    "ORIGINAL": "VO",
    "LOCAL": "VF",
}


def _api_to_sessions(api_result, cinema_name, date_str):
    """Convert allocineAPI response to our session dicts.

    api_result: list of {title: str, showtimes: [{startsAt: str, diffusionVersion: str}]}
    Returns a flat list of session dicts.
    """
    sessions = []
    for film in (api_result or []):
        title = (film.get("title") or "").strip()
        if not title:
            continue
        for showtime in film.get("showtimes", []):
            starts_at = showtime.get("startsAt", "")
            # startsAt is ISO format: "2026-06-30T14:00:00"
            # Extract HH:MM for the heure field
            try:
                heure = starts_at[11:16]  # "HH:MM"
            except (IndexError, TypeError):
                heure = str(starts_at).strip()

            raw_version = showtime.get("diffusionVersion", "")
            version = _VERSION_MAP.get(raw_version, raw_version)

            sessions.append({
                "cinema": cinema_name,
                "film": title,
                "date": date_str,
                "heure": heure,
                "version": version,
                "temperature": None,
            })
    return sessions


def scrape_cinema_day(cinema_name, cinema_id, date_str, api=None):
    """Fetch sessions for one cinema on one date via allocineAPI.

    Returns [] on error (including when the cinema has no showtimes that day).
    """
    if api is None:
        api = allocineAPI()
    try:
        result = api.get_showtime(cinema_id, date_str)
        return _api_to_sessions(result, cinema_name, date_str)
    except Exception:
        return []


def scrape_all(progress_callback=None):
    """Fetch sessions for all 9 cinemas over 21 days (3 weeks).

    progress_callback(current, total, cinema_name) called for each request.
    Returns flat list of session dicts without temperatures.
    """
    today = datetime.now().date()
    dates = [(today + timedelta(days=i)).isoformat() for i in range(21)]

    total = len(CINEMA_IDS) * len(dates)
    current = 0
    sessions = []
    api = allocineAPI()

    for cinema_name, cinema_id in CINEMA_IDS.items():
        for date_str in dates:
            current += 1
            if progress_callback:
                progress_callback(current, total, cinema_name)
            day_sessions = scrape_cinema_day(cinema_name, cinema_id, date_str, api=api)
            sessions.extend(day_sessions)
            time.sleep(0.5)  # polite rate limiting

    return sessions
