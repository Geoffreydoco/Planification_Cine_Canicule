import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

import requests
from allocineAPI.allocineAPI import allocineAPI, URLs

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
        req = requests.get(path, params=url_params, headers=_HEADERS)
        if req.status_code != 200:
            raise Exception("Error " + str(req.status_code))
        return json.loads(req.content.decode("utf-8"))


# Fallback hardcoded in case the discovery call fails
_FALLBACK_CINEMA_IDS = {
    "Pathé Lyon - Bellecour":        "P0012",
    "Cinéma Lumière Terreaux":       "P0017",
    "Cinéma Lumière La Fourmi":      "W6903",
    "Cinéma Lumière Bellecour":      "P0015",
    "Le Cinéma":                     "P0009",
    "Le Cinéma Opéra":               "P0006",
    "Le Zola":                       "P0014",
    "UGC Ciné Cité Lyon Part-Dieu":  "P0036",
    "Institut Lumière":              "P0050",
    "Cinéma Comoedia":               "P3757",
}


def _fetch_cinema_ids():
    """Discover all cinemas in Lyon and Villeurbanne from AlloCiné.

    Combines the Lyon city list with Villeurbanne cinemas from the Rhône
    department page (filtered by ZIP 69100). Falls back to the hardcoded
    list on any error.
    """
    try:
        api = _AllocineAPIWithHeaders()
        result = {}

        # All Lyon cinemas via city ID
        for c in api.get_cinema("ville-113315"):
            result[c["name"]] = c["id"]

        # Villeurbanne cinemas (ZIP 69100) via Rhône department
        for c in api.get_cinema("departement-83196"):
            address = c.get("address", "")
            zip_code = next((w for w in address.split() if w.isdigit() and len(w) == 5), "")
            if zip_code == "69100" and c["id"] not in result.values():
                result[c["name"]] = c["id"]

        if result:
            return result
    except Exception:
        pass
    return _FALLBACK_CINEMA_IDS

def _extract_booking_url(showtime):
    """Pull a ticketing URL out of a raw showtime's data.ticketing list.

    Prefers the "default" provider (falls back to any provider with a URL);
    returns None when the theater has no online ticketing partner.
    """
    ticketing = ((showtime.get("data") or {}).get("ticketing")) or []
    fallback = None
    for entry in ticketing:
        urls = entry.get("urls") or []
        if not urls:
            continue
        if entry.get("provider") == "default":
            return urls[0]
        if fallback is None:
            fallback = urls[0]
    return fallback


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
        director = film.get("director", "")
        user_rating = film.get("user_rating")
        press_rating = film.get("press_rating")
        genres = film.get("genres", [])
        actors = film.get("actors", [])
        certificate = film.get("certificate")
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
                "director": director,
                "user_rating": user_rating,
                "press_rating": press_rating,
                "genres": genres,
                "actors": actors,
                "certificate": certificate,
                "date": date_str,
                "heure": heure,
                "version": version,
                "temperature": None,
                "booking_url": showtime.get("booking_url"),
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
            now = time.time()
            wait_until = _last_req_at[0] + _MIN_INTERVAL
            gap = wait_until - now
            _last_req_at[0] = max(now, wait_until)  # réserver le slot avant de relâcher
        if gap > 0:
            time.sleep(gap)  # dormir EN DEHORS du verrou
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

            # Director(s)
            director_parts = []
            for credit in (movie.get("credits") or []):
                pos = (credit.get("position") or {}).get("name", "")
                if pos in ("DIRECTOR", "CO_DIRECTOR"):
                    person = credit.get("person") or {}
                    name = f"{person.get('firstName', '')} {person.get('lastName', '')}".strip()
                    if name:
                        director_parts.append(name)
            director = ", ".join(director_parts)

            # Ratings
            stats = movie.get("stats") or {}
            user_rating = (stats.get("userRating") or {}).get("score")
            press_rating = (stats.get("pressReview") or {}).get("score")

            # Genres
            genres = [g["translate"] for g in (movie.get("genres") or []) if g.get("translate")]

            # Age certificate (classification CNC)
            releases = movie.get("releases") or []
            certificate = None
            if releases:
                cert = (releases[0].get("certificate") or {})
                certificate = cert.get("label") or cert.get("code") or None

            # Main cast (first 4)
            cast_edges = (movie.get("cast") or {}).get("edges") or []
            actors = []
            for edge in cast_edges[:4]:
                node = edge.get("node") or {}
                person = node.get("actor") or node.get("voiceActor") or node.get("originalVoiceActor")
                if person:
                    name = f"{person.get('firstName', '')} {person.get('lastName', '')}".strip()
                    if name:
                        actors.append(name)

            showtimes = []
            seen_ids = set()
            for showtimes_key in element.get("showtimes", {}).keys():
                for showtime in element["showtimes"][showtimes_key]:
                    sid = showtime.get("internalId")
                    if sid not in seen_ids:
                        seen_ids.add(sid)
                        showtimes.append({
                            "startsAt": showtime.get("startsAt", ""),
                            "diffusionVersion": showtime.get("diffusionVersion", ""),
                            "booking_url": _extract_booking_url(showtime),
                        })

            formatted_data.append({
                "title": title,
                "film_url": film_url,
                "duration": duration,
                "poster_url": poster_url,
                "synopsis": synopsis,
                "director": director,
                "user_rating": user_rating,
                "press_rating": press_rating,
                "genres": genres,
                "actors": actors,
                "certificate": certificate,
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
        sessions = _api_to_sessions(result, cinema_name, date_str)
        cinema_url = f"https://www.allocine.fr/salle/cinema/{cinema_id}/"
        for s in sessions:
            s["cinema_url"] = cinema_url
        return sessions
    except Exception:
        return []


def scrape_all(progress_callback=None):
    """Fetch sessions for all cinemas in Lyon and Villeurbanne over 15 days.

    Cinema list is discovered dynamically from AlloCiné at call time.
    5 cinemas scraped in parallel; each cinema's 15 days run sequentially
    with a 0.2s delay.

    progress_callback(current, total, cinema_name) called for each request.
    Returns flat list of session dicts without temperatures.
    """
    cinema_ids = _fetch_cinema_ids()

    today = datetime.now().date()
    dates = [(today + timedelta(days=i)).isoformat() for i in range(15)]

    total = len(cinema_ids) * len(dates)
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
            for name, cid in cinema_ids.items()
        }
        for future in as_completed(futures):
            all_sessions.extend(future.result())

    return all_sessions
