import re
import requests

LYON_LAT = 45.75
LYON_LON = 4.85


def fetch_weather():
    """Retourne (hourly_temps, daily_minmax) en un seul appel Open-Meteo.

    hourly_temps: {"2026-06-30T14:00": 36.5, ...}
    daily_minmax: {"2026-06-30": {"min": 28.0, "max": 38.5}, ...}
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LYON_LAT,
        "longitude": LYON_LON,
        "hourly": "temperature_2m",
        "daily": "temperature_2m_min,temperature_2m_max",
        "timezone": "Europe/Paris",
        "forecast_days": 16,
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    hourly = dict(zip(data["hourly"]["time"], data["hourly"]["temperature_2m"]))
    daily = {
        d: {"min": mn, "max": mx}
        for d, mn, mx in zip(
            data["daily"]["time"],
            data["daily"]["temperature_2m_min"],
            data["daily"]["temperature_2m_max"],
        )
    }
    return hourly, daily


def get_temperature(temps_dict, date_str, heure_str):
    """Retourne la température pour une date et une heure AlloCiné.
    Gère '14h30' et '14:30'. Arrondit à l'heure inférieure. None si hors prévision."""
    match = re.match(r'(\d{1,2})[h:]', heure_str)
    hour = match.group(1).zfill(2) if match else "00"
    return temps_dict.get(f"{date_str}T{hour}:00")
