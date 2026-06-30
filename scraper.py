import requests
from bs4 import BeautifulSoup
import time
import json
import os
from datetime import datetime, timedelta

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

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def scrape_cinema_day(cinema_name, cinema_id, date_str):
    """Scrape les séances d'un cinéma pour une date donnée.

    LIMITATION AlloCiné : les URLs paramétrées par date (d_date=YYYY-MM-DD)
    renvoient systématiquement 404, et le paramètre ?shwt_date= est ignoré par
    le serveur. La navigation par date du site est entièrement côté client (JS).
    En conséquence, l'URL sans date renvoie toujours les séances du jour courant,
    quelle que soit la valeur de date_str passée en argument.

    Cette fonction accepte toujours date_str pour maintenir une interface
    cohérente, mais elle scrape uniquement les séances du jour courant.
    Appeler cette fonction avec une date future ne produira pas les séances de
    cette date future.

    Retourne une liste de dicts avec les clés :
        cinema, film, date, heure, version, temperature (None)
    Retourne [] en cas d'erreur HTTP ou d'absence de données.
    """
    # AlloCiné date-parameterized URLs always return 404; the undated URL is
    # the only working endpoint but always serves today's sessions.
    url = (
        f"https://www.allocine.fr/seance/"
        f"salle_gen_csalle={cinema_id}.html"
    )

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    sessions = []

    # Each film card has class "card entity-card"
    for card in soup.select(".card.entity-card"):
        # Film title is in h2 (also carries .meta-title on a nested element)
        title_tag = card.select_one("h2")
        if not title_tag:
            continue
        film_title = title_tag.text.strip()

        # Each version block groups showtimes for one version (VF, VOST, …)
        for version_block in card.select(".showtimes-version"):
            # Version label lives in the "text" div: "30 juin 2026 - En VF"
            text_div = version_block.select_one("div.text")
            if text_div:
                raw = text_div.text.strip()
                # Text is "30 juin 2026 -\n                En VF" (newline after dash)
                # Split on " -" to isolate the version part.
                if " -" in raw:
                    version_label = raw.split(" -", 1)[1].strip()
                else:
                    version_label = raw.strip()
                # Normalise to short form: "VF", "VOST", "VO", …
                version = version_label.replace("En ", "").strip() if version_label.startswith("En ") else version_label
            else:
                version = "VF"

            # Hour values are in .showtimes-hour-item-value spans
            for hour_tag in version_block.select(".showtimes-hour-item-value"):
                heure = hour_tag.text.strip()
                if not heure:
                    continue
                sessions.append({
                    "cinema": cinema_name,
                    "film": film_title,
                    "date": date_str,
                    "heure": heure,
                    "version": version,
                    "temperature": None,
                })

    return sessions


def scrape_all():
    """Scrape les séances du jour pour tous les cinémas.

    LIMITATION : AlloCiné ne fournit que les séances du jour courant via
    scraping HTML statique. La navigation multi-dates est JavaScript uniquement.
    Cette fonction scrape donc uniquement aujourd'hui pour chaque cinéma.

    Retourne une liste de dicts de séances avec les clés :
        cinema, film, date, heure, version, temperature (None)
    """
    today = datetime.now().strftime("%Y-%m-%d")
    all_sessions = []
    for cinema_name, cinema_id in CINEMA_IDS.items():
        sessions = scrape_cinema_day(cinema_name, cinema_id, today)
        all_sessions.extend(sessions)
        time.sleep(1)  # politesse envers le serveur
    return all_sessions
