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


def _format_runtime(runtime_minutes):
    """Convert runtime in minutes to a human-readable string like '2h 46min'."""
    if not runtime_minutes:
        return ""
    try:
        mins = int(runtime_minutes)
        if mins <= 0:
            return ""
        h, m = divmod(mins, 60)
        if h > 0 and m > 0:
            return f"{h}h {m:02d}min"
        elif h > 0:
            return f"{h}h"
        else:
            return f"{m}min"
    except (ValueError, TypeError):
        return ""


def _api_to_sessions(api_result, cinema_name, date_str):
    """Convert allocineAPI response to our session dicts.

    api_result: list of {title: str, film_url: str, duration: str,
                          showtimes: [{startsAt: str, diffusionVersion: str}]}
    Returns a flat list of session dicts.
    """
    sessions = []
    for film in (api_result or []):
        title = (film.get("title") or "").strip()
        if not title:
            continue
        film_url = film.get("film_url", "")
        duration = film.get("duration", "")
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
                "film_url": film_url,
                "duration": duration,
                "date": date_str,
                "heure": heure,
                "version": version,
                "temperature": None,
            })
    return sessions


def _get_showtime_enriched(api_instance, cinema_id, date_str):
    """Fetch showtimes with enriched film data (runtime, internalId).

    Calls the same endpoint as allocineAPI.get_showtime but also extracts
    film internalId (for URL) and runtime (for duration display).
    Returns list of {title, film_url, duration, showtimes: [{startsAt, diffusionVersion}]}.
    """
    from allocineAPI.allocineAPI import URLs
    formatted_data = []
    page, total_pages = 0, 1
    while page < total_pages:
        json_data = api_instance._get_json_request(
            URLs.showtime_url(cinema_id, date_str, page + 1)
        )
        page = int(json_data["pagination"]["page"])
        total_pages = int(json_data["pagination"]["totalPages"])
        for element in json_data["results"]:
            movie = element.get("movie") or {}
            title = (movie.get("title") or "").strip()
            if not title:
                continue

            # Build AlloCiné film URL from internalId
            internal_id = movie.get("internalId")
            if internal_id:
                film_url = f"https://www.allocine.fr/film/fichefilm_gen_cfilm={internal_id}.html"
            else:
                film_url = ""

            # Runtime is in minutes in the AlloCiné API
            runtime_minutes = movie.get("runtime") or 0
            duration = _format_runtime(runtime_minutes)

            showtimes = []
            seen_ids = []
            for showtimes_key in element.get("showtimes", {}).keys():
                for showtime in element["showtimes"][showtimes_key]:
                    sid = showtime.get("internalId")
                    if sid not in seen_ids:
                        seen_ids.append(sid)
                        showtimes.append({
                            "startsAt": showtime.get("startsAt", ""),
                            "diffusionVersion": showtime.get("diffusionVersion", ""),
                        })

            formatted_data.append({
                "title": title,
                "film_url": film_url,
                "duration": duration,
                "showtimes": showtimes,
            })
    return formatted_data


def scrape_cinema_day(cinema_name, cinema_id, date_str, api=None):
    """Fetch sessions for one cinema on one date via allocineAPI.

    Returns [] on error (including when the cinema has no showtimes that day).
    """
    if api is None:
        api = allocineAPI()
    try:
        result = _get_showtime_enriched(api, cinema_id, date_str)
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
