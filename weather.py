import requests

LYON_LAT = 45.75
LYON_LON = 4.85


def fetch_temperatures():
    """Retourne {datetime_str: temperature} pour les 16 prochains jours."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LYON_LAT,
        "longitude": LYON_LON,
        "hourly": "temperature_2m",
        "timezone": "Europe/Paris",
        "forecast_days": 16,
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    times = data["hourly"]["time"]
    temps = data["hourly"]["temperature_2m"]
    return dict(zip(times, temps))


def get_temperature(temps_dict, date_str, heure_str):
    """Retourne la température pour une date et une heure AlloCiné ('14h30').
    Arrondit à l'heure inférieure. Retourne None si hors période de prévision."""
    hour = heure_str.split("h")[0].zfill(2)
    key = f"{date_str}T{hour}:00"
    return temps_dict.get(key)
