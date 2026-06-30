import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

import requests
from allocineAPI.allocineAPI import allocineAPI

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Referer": "https://www.allocine.fr/",
}


class _AllocineAPIWithHeaders(allocineAPI):
    def _get_json_request(self, path, url_params=None):
        import json
        req = requests.get(path, params=url_params, headers=_HEADERS)
        if req.status_code != 200:
            raise Exception("Error " + str(req.status_code))
        return json.loads(req.content.decode("utf-8"))


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
    "Le Comoedia":       "P0003",
}

# Map allocineAPI diffusionVersion values to display labels
_VERSION_MAP = {
    "DUBBED": "VF",
    "ORIGINAL": "VO",
    "LOCAL": "VF",
}



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
        poster_url = film.get("poster_url", "")
        synopsis = film.get("synopsis", "")
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
                "poster_url": poster_url,
                "synopsis": synopsis,
                "date": date_str,
                "heure": heure,
                "version": version,
                "temperature": None,
            })
    return sessions


# Global rate limiter: max 1 request every 0.2 s across all threads
_rate_lock   = threading.Lock()
_last_req_at = [0.0]
_MIN_INTERVAL = 0.2


def _rate_limited_request(api_instance, url, retries=4):
    """Throttle + retry with exponential backoff on 429."""
    for attempt in range(retries):
        with _rate_lock:
            gap = _MIN_INTERVAL - (time.time() - _last_req_at[0])
            if gap > 0:
                time.sleep(gap)
            _last_req_at[0] = time.time()
        try:
            return api_instance._get_json_request(url)
        except Exception as e:
            if "429" in str(e) and attempt < retries - 1:
                time.sleep(2.0 * (2 ** attempt))
            else:
                raise


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
        json_data = _rate_limited_request(
            api_instance, URLs.showtime_url(cinema_id, date_str, page + 1)
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

            # Runtime is already a formatted string in the AlloCiné API (e.g. "1h 29min")
            duration = movie.get("runtime") or ""

            poster = movie.get("poster") or {}
            poster_url = poster.get("url") or ""
            raw_synopsis = movie.get("synopsisFull") or ""
            synopsis = re.sub(r"<[^>]+>", " ", raw_synopsis).strip()

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
                "poster_url": poster_url,
                "synopsis": synopsis,
                "showtimes": showtimes,
            })
    return formatted_data


def scrape_cinema_day(cinema_name, cinema_id, date_str, api=None):
    """Fetch sessions for one cinema on one date via allocineAPI.

    Returns [] on error (including when the cinema has no showtimes that day).
    """
    if api is None:
        api = _AllocineAPIWithHeaders()
    try:
        result = _get_showtime_enriched(api, cinema_id, date_str)
        return _api_to_sessions(result, cinema_name, date_str)
    except Exception:
        return []


def scrape_all(progress_callback=None):
    """Fetch sessions for all 9 cinemas over 21 days (3 weeks).

    5 cinemas scraped in parallel; each cinema's 21 days run sequentially
    with a 0.2s delay. Reduces total time from ~3 min to ~35-45 seconds.

    progress_callback(current, total, cinema_name) called for each request.
    Returns flat list of session dicts without temperatures.
    """
    today = datetime.now().date()
    dates = [(today + timedelta(days=i)).isoformat() for i in range(21)]

    total = len(CINEMA_IDS) * len(dates)
    lock = threading.Lock()
    counter = [0]
    all_sessions = []

    def fetch_cinema(cinema_name, cinema_id):
        api = _AllocineAPIWithHeaders()
        cinema_sessions = []
        for date_str in dates:
            day_sessions = scrape_cinema_day(cinema_name, cinema_id, date_str, api=api)
            cinema_sessions.extend(day_sessions)
            with lock:
                counter[0] += 1
                if progress_callback:
                    progress_callback(counter[0], total, cinema_name)
        return cinema_sessions

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(fetch_cinema, name, cid): name
            for name, cid in CINEMA_IDS.items()
        }
        for future in as_completed(futures):
            all_sessions.extend(future.result())

    return all_sessions
