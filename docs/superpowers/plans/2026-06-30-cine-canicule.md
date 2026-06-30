# Ciné Canicule — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Serveur Flask local générant une page HTML listant les séances de 9 cinémas lyonnais sur 3 semaines, enrichies de la température prévue à l'heure de chaque séance.

**Architecture:** `lancer.bat` démarre Flask et ouvre le navigateur. `scraper.py` récupère les séances depuis AlloCiné (9 cinémas × 21 jours = 189 requêtes). `weather.py` appelle Open-Meteo pour enrichir chaque séance en température. Le résultat est mis en cache dans `data/sessions.json`. Le bouton "Actualiser" de la page appelle `POST /refresh` qui relance le scraping (~3 min).

**Tech Stack:** Python 3.8+, Flask, requests, BeautifulSoup4, Open-Meteo API (gratuit, sans clé), pytest, unittest.mock

---

## Structure des fichiers

```
projet-cine-canicule/
├── lancer.bat
├── requirements.txt
├── app.py
├── scraper.py
├── weather.py
├── data/                    # créé automatiquement
│   └── sessions.json
├── templates/
│   └── index.html
└── tests/
    ├── test_weather.py
    ├── test_scraper.py
    └── test_app.py
```

---

### Task 1 : Setup du projet

**Files:**
- Create: `requirements.txt`
- Create: `lancer.bat`
- Create: `tests/__init__.py`

- [ ] **Étape 1 : Créer `requirements.txt`**

```
flask>=2.0
requests>=2.28
beautifulsoup4>=4.11
pytest>=7.0
```

- [ ] **Étape 2 : Créer `lancer.bat`**

```batch
@echo off
chcp 65001 >nul
echo === Ciné Canicule ===

python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR : Python n'est pas installe ou n'est pas dans le PATH.
    echo Installez Python depuis https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Installation des dependances...
pip install -r requirements.txt --quiet

echo Demarrage du serveur sur http://localhost:5000 ...
python app.py
```

- [ ] **Étape 3 : Créer `tests/__init__.py` vide**

Créer le fichier `tests/__init__.py` avec un contenu vide (nécessaire pour que pytest le trouve).

- [ ] **Étape 4 : Vérifier que pytest fonctionne**

Commande : `pytest tests/ -v`  
Attendu : `no tests ran` (pas d'erreur)

- [ ] **Étape 5 : Commit**

```bash
git init
git add requirements.txt lancer.bat tests/__init__.py
git commit -m "chore: project setup"
```

---

### Task 2 : Trouver les IDs AlloCiné des 9 cinémas

**Files:**
- Create: `scraper.py` (uniquement la constante `CINEMA_IDS`)

Les pages AlloCiné utilisent des IDs numériques dans les URLs, exemple :  
`https://www.allocine.fr/seances/salle_gen_csalle=C0013.html`

- [ ] **Étape 1 : Trouver les IDs en visitant AlloCiné**

Ouvrir un navigateur et rechercher chaque cinéma sur `https://www.allocine.fr`.  
Cliquer sur "Séances" pour chaque cinéma et noter l'ID `CXXXXX` dans l'URL.

Cinémas à rechercher :
- Pathé Bellecour
- Cinémas Lumière - Les Terreaux
- Cinémas Lumière - La Fourmi
- Cinémas Lumière - Bellecour
- Le Cinéma (Lyon)
- Cinéma Opéra (Lyon)
- Le Zola (Villeurbanne)
- UGC Ciné Cité Part-Dieu
- Institut Lumière

- [ ] **Étape 2 : Créer `scraper.py` avec les IDs trouvés**

Remplacer les `C????` par les vrais IDs trouvés à l'étape précédente :

```python
import requests
from bs4 import BeautifulSoup
import time
import json
import os
from datetime import datetime, timedelta

CINEMA_IDS = {
    "Pathé Bellecour":        "C????",
    "Lumière Terreaux":       "C????",
    "Lumière Fourmi":         "C????",
    "Lumière Bellecour":      "C????",
    "Le Cinéma":              "C????",
    "Cinéma Opéra":           "C????",
    "Le Zola":                "C????",
    "UGC Part-Dieu":          "C????",
    "Institut Lumière":       "C????",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}
```

- [ ] **Étape 3 : Vérifier qu'une URL fonctionne manuellement**

Dans un terminal Python :
```python
import requests
HEADERS = {"User-Agent": "Mozilla/5.0 ..."}  # copier depuis scraper.py
r = requests.get("https://www.allocine.fr/seances/salle_gen_csalle=C????.html", headers=HEADERS)
print(r.status_code)  # Doit afficher 200
print(len(r.text))    # Doit afficher > 10000
```

- [ ] **Étape 4 : Inspecter la structure HTML**

Dans le même terminal :
```python
from bs4 import BeautifulSoup
soup = BeautifulSoup(r.text, "html.parser")
# Chercher les cartes de films
cards = soup.select(".card.entity-card")
print(f"{len(cards)} cartes trouvées")
if cards:
    print(cards[0].prettify()[:2000])
```

Noter les sélecteurs CSS réels pour le titre du film et les horaires. Ils seront utilisés dans Task 4.

- [ ] **Étape 5 : Commit**

```bash
git add scraper.py
git commit -m "chore: add AlloCiné cinema IDs"
```

---

### Task 3 : `weather.py` — températures Open-Meteo

**Files:**
- Create: `weather.py`
- Create: `tests/test_weather.py`

- [ ] **Étape 1 : Écrire les tests**

```python
# tests/test_weather.py
from unittest.mock import patch, Mock
import weather

FAKE_RESPONSE = {
    "hourly": {
        "time": [
            "2026-06-30T13:00",
            "2026-06-30T14:00",
            "2026-06-30T15:00",
        ],
        "temperature_2m": [34.1, 36.5, 37.2]
    }
}

def test_fetch_temperatures_returns_dict():
    mock_resp = Mock()
    mock_resp.json.return_value = FAKE_RESPONSE
    mock_resp.raise_for_status = Mock()

    with patch("weather.requests.get", return_value=mock_resp):
        result = weather.fetch_temperatures()

    assert result == {
        "2026-06-30T13:00": 34.1,
        "2026-06-30T14:00": 36.5,
        "2026-06-30T15:00": 37.2,
    }

def test_get_temperature_exact_match():
    temps = {"2026-06-30T14:00": 36.5}
    assert weather.get_temperature(temps, "2026-06-30", "14h00") == 36.5

def test_get_temperature_rounds_down_minutes():
    temps = {"2026-06-30T14:00": 36.5}
    # 14h30 -> cherche 14:00
    assert weather.get_temperature(temps, "2026-06-30", "14h30") == 36.5

def test_get_temperature_returns_none_when_missing():
    temps = {"2026-06-30T14:00": 36.5}
    assert weather.get_temperature(temps, "2026-07-20", "14h00") is None
```

- [ ] **Étape 2 : Lancer les tests — vérifier qu'ils échouent**

Commande : `pytest tests/test_weather.py -v`  
Attendu : `ModuleNotFoundError: No module named 'weather'`

- [ ] **Étape 3 : Créer `weather.py`**

```python
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
```

- [ ] **Étape 4 : Lancer les tests — vérifier qu'ils passent**

Commande : `pytest tests/test_weather.py -v`  
Attendu :
```
test_weather.py::test_fetch_temperatures_returns_dict PASSED
test_weather.py::test_get_temperature_exact_match PASSED
test_weather.py::test_get_temperature_rounds_down_minutes PASSED
test_weather.py::test_get_temperature_returns_none_when_missing PASSED
4 passed
```

- [ ] **Étape 5 : Commit**

```bash
git add weather.py tests/test_weather.py
git commit -m "feat: weather module with Open-Meteo integration"
```

---

### Task 4 : `scraper.py` — parser une page (un cinéma, un jour)

**Files:**
- Modify: `scraper.py` (ajouter `scrape_cinema_day`)
- Create: `tests/test_scraper.py`

> **Note :** Les sélecteurs CSS ci-dessous correspondent à la structure AlloCiné observée en Task 2. Si la structure diffère, adapter les sélecteurs dans `scrape_cinema_day` avant de valider les tests.

- [ ] **Étape 1 : Construire un fichier HTML de test depuis la vraie page AlloCiné**

Dans un terminal Python, sauvegarder le HTML d'une vraie page pour les tests :

```python
import requests
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)..."}
r = requests.get("https://www.allocine.fr/seances/salle_gen_csalle=C????.html", headers=HEADERS)
with open("tests/sample_allocine.html", "w", encoding="utf-8") as f:
    f.write(r.text)
print("HTML sauvegardé")
```

Remplacer `C????` par l'ID du Pathé Bellecour trouvé en Task 2.

- [ ] **Étape 2 : Identifier les vrais sélecteurs CSS**

```python
from bs4 import BeautifulSoup
with open("tests/sample_allocine.html", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

# Chercher les films
cards = soup.select(".card.entity-card")
print(f"{len(cards)} films")

if cards:
    # Titre
    title = cards[0].select_one(".meta-title-link") or cards[0].select_one("a.meta-title")
    print("Titre :", title.text.strip() if title else "NON TROUVÉ")
    
    # Horaires
    hours = cards[0].select(".showtimes-hour-item-value")
    print("Horaires :", [h.text.strip() for h in hours])
```

Si les sélecteurs ne retournent rien, inspecter `cards[0].prettify()` et adapter les sélecteurs dans les étapes suivantes.

- [ ] **Étape 3 : Écrire les tests avec un HTML minimal**

Construire un mini-HTML qui reproduit la structure réelle trouvée à l'étape précédente. Exemple (à adapter selon les vrais sélecteurs) :

```python
# tests/test_scraper.py
from unittest.mock import patch, Mock
import scraper

SAMPLE_HTML = """
<html><body>
<div class="card entity-card">
  <a class="meta-title-link" href="/film/fichefilm_gen_cfilm=123.html">Dune : Partie 2</a>
  <div class="showtimes-hour-item">
    <span class="showtimes-hour-item-value">14h00</span>
    <span class="showtimes-hour-item-tag">VF</span>
  </div>
  <div class="showtimes-hour-item">
    <span class="showtimes-hour-item-value">17h30</span>
    <span class="showtimes-hour-item-tag">VOST</span>
  </div>
</div>
<div class="card entity-card">
  <a class="meta-title-link" href="/film/fichefilm_gen_cfilm=456.html">Le Comte de Monte-Cristo</a>
  <div class="showtimes-hour-item">
    <span class="showtimes-hour-item-value">20h00</span>
    <span class="showtimes-hour-item-tag">VF</span>
  </div>
</div>
</body></html>
"""


def make_mock_response(html):
    mock = Mock()
    mock.text = html
    mock.raise_for_status = Mock()
    return mock


def test_scrape_cinema_day_returns_sessions():
    with patch("scraper.requests.get", return_value=make_mock_response(SAMPLE_HTML)):
        sessions = scraper.scrape_cinema_day("Pathé Bellecour", "C0013", "2026-06-30")

    assert len(sessions) == 3

def test_scrape_cinema_day_session_fields():
    with patch("scraper.requests.get", return_value=make_mock_response(SAMPLE_HTML)):
        sessions = scraper.scrape_cinema_day("Pathé Bellecour", "C0013", "2026-06-30")

    first = sessions[0]
    assert first["cinema"] == "Pathé Bellecour"
    assert first["film"] == "Dune : Partie 2"
    assert first["date"] == "2026-06-30"
    assert first["heure"] == "14h00"
    assert first["version"] == "VF"
    assert first["temperature"] is None

def test_scrape_cinema_day_empty_on_http_error():
    mock = Mock()
    mock.raise_for_status.side_effect = Exception("HTTP 403")
    with patch("scraper.requests.get", return_value=mock):
        sessions = scraper.scrape_cinema_day("Pathé Bellecour", "C0013", "2026-06-30")
    assert sessions == []
```

- [ ] **Étape 4 : Lancer les tests — vérifier qu'ils échouent**

Commande : `pytest tests/test_scraper.py -v`  
Attendu : `AttributeError` ou `ImportError` — `scrape_cinema_day` n'existe pas encore.

- [ ] **Étape 5 : Implémenter `scrape_cinema_day` dans `scraper.py`**

Ajouter après les constantes existantes (adapter les sélecteurs si besoin selon Task 4 étape 2) :

```python
def scrape_cinema_day(cinema_name, cinema_id, date_str):
    """Scrape les séances d'un cinéma pour une date donnée.
    Retourne une liste de dicts, [] en cas d'erreur."""
    url = (
        f"https://www.allocine.fr/seances/"
        f"salle_gen_csalle={cinema_id}-d_date={date_str}.html"
    )
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    sessions = []

    for card in soup.select(".card.entity-card"):
        title_tag = card.select_one(".meta-title-link")
        if not title_tag:
            continue
        film_title = title_tag.text.strip()

        for showtime in card.select(".showtimes-hour-item"):
            heure_tag = showtime.select_one(".showtimes-hour-item-value")
            if not heure_tag:
                continue
            heure = heure_tag.text.strip()

            version_tag = showtime.select_one(".showtimes-hour-item-tag")
            version = version_tag.text.strip() if version_tag else "VF"

            sessions.append({
                "cinema": cinema_name,
                "film": film_title,
                "date": date_str,
                "heure": heure,
                "version": version,
                "temperature": None,
            })

    return sessions
```

- [ ] **Étape 6 : Lancer les tests — vérifier qu'ils passent**

Commande : `pytest tests/test_scraper.py -v`  
Attendu : `3 passed`

Si les sélecteurs CSS sont mauvais (0 sessions retournées en production mais tests OK avec le HTML de test), ouvrir `tests/sample_allocine.html` dans un navigateur et inspecter avec F12 pour trouver les vrais sélecteurs.

- [ ] **Étape 7 : Commit**

```bash
git add scraper.py tests/test_scraper.py tests/sample_allocine.html
git commit -m "feat: AlloCiné single-page scraper"
```

---

### Task 5 : `scraper.py` — scraping complet (tous cinémas × toutes dates)

**Files:**
- Modify: `scraper.py` (ajouter `scrape_all`)
- Modify: `tests/test_scraper.py` (ajouter test de `scrape_all`)

- [ ] **Étape 1 : Écrire le test de `scrape_all`**

Ajouter à `tests/test_scraper.py` :

```python
def test_scrape_all_calls_scrape_cinema_day_for_each_combo():
    """Vérifie que scrape_all appelle scrape_cinema_day pour chaque cinéma × chaque date."""
    with patch("scraper.scrape_cinema_day", return_value=[]) as mock_scrape, \
         patch("scraper.time.sleep"):  # supprimer les délais dans les tests
        result = scraper.scrape_all()

    # 9 cinémas × 21 jours = 189 appels
    assert mock_scrape.call_count == 189
    assert result == []

def test_scrape_all_aggregates_sessions():
    fake_session = {
        "cinema": "Pathé Bellecour", "film": "Film X",
        "date": "2026-06-30", "heure": "14h00",
        "version": "VF", "temperature": None
    }
    with patch("scraper.scrape_cinema_day", return_value=[fake_session]), \
         patch("scraper.time.sleep"):
        result = scraper.scrape_all()

    assert len(result) == 189  # 1 session par appel × 189 appels
```

- [ ] **Étape 2 : Lancer les tests — vérifier qu'ils échouent**

Commande : `pytest tests/test_scraper.py::test_scrape_all_calls_scrape_cinema_day_for_each_combo -v`  
Attendu : `AttributeError: module 'scraper' has no attribute 'scrape_all'`

- [ ] **Étape 3 : Implémenter `scrape_all` dans `scraper.py`**

Ajouter en bas de `scraper.py` (avant les imports utilisés, `datetime` et `timedelta` doivent déjà être importés) :

```python
def scrape_all(progress_callback=None):
    """Scrape toutes les séances pour les 9 cinémas sur 21 jours.
    
    progress_callback(current, total, cinema_name) appelé à chaque requête.
    Retourne une liste plate de séances (sans températures).
    """
    from datetime import datetime, timedelta
    today = datetime.now().date()
    dates = [(today + timedelta(days=i)).isoformat() for i in range(21)]

    total = len(CINEMA_IDS) * len(dates)
    current = 0
    sessions = []

    for cinema_name, cinema_id in CINEMA_IDS.items():
        for date_str in dates:
            current += 1
            if progress_callback:
                progress_callback(current, total, cinema_name)
            day_sessions = scrape_cinema_day(cinema_name, cinema_id, date_str)
            sessions.extend(day_sessions)
            time.sleep(1)

    return sessions
```

- [ ] **Étape 4 : Lancer tous les tests scraper**

Commande : `pytest tests/test_scraper.py -v`  
Attendu : `5 passed`

- [ ] **Étape 5 : Commit**

```bash
git add scraper.py tests/test_scraper.py
git commit -m "feat: full scrape across all cinemas and dates"
```

---

### Task 6 : `app.py` — serveur Flask

**Files:**
- Create: `app.py`
- Create: `tests/test_app.py`

- [ ] **Étape 1 : Écrire les tests Flask**

```python
# tests/test_app.py
import json
import os
from unittest.mock import patch, Mock
import pytest

os.environ["TESTING"] = "1"
import app as flask_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(flask_app, "DATA_FILE", str(tmp_path / "sessions.json"))
    flask_app.app.config["TESTING"] = True
    with flask_app.app.test_client() as c:
        yield c


def test_index_returns_200(client):
    resp = client.get("/")
    assert resp.status_code == 200

def test_index_contains_sessions_json(client, tmp_path, monkeypatch):
    data = {"updated_at": "2026-06-30T10:00:00", "sessions": [
        {"cinema": "Pathé Bellecour", "film": "Dune 2",
         "date": "2026-06-30", "heure": "14h00", "version": "VF", "temperature": 36.0}
    ]}
    monkeypatch.setattr(flask_app, "DATA_FILE", str(tmp_path / "sessions.json"))
    (tmp_path / "sessions.json").write_text(json.dumps(data), encoding="utf-8")

    resp = client.get("/")
    assert b"Dune 2" in resp.data

def test_refresh_calls_scrape(client, monkeypatch, tmp_path):
    monkeypatch.setattr(flask_app, "DATA_FILE", str(tmp_path / "sessions.json"))

    with patch("app.run_scrape", return_value=42) as mock_scrape:
        resp = client.post("/refresh")

    assert resp.status_code == 200
    body = json.loads(resp.data)
    assert body["status"] == "ok"
    assert body["count"] == 42
    mock_scrape.assert_called_once()
```

- [ ] **Étape 2 : Lancer les tests — vérifier qu'ils échouent**

Commande : `pytest tests/test_app.py -v`  
Attendu : `ModuleNotFoundError: No module named 'app'`

- [ ] **Étape 3 : Créer `app.py`**

```python
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
```

- [ ] **Étape 4 : Créer le dossier `templates/` et un `index.html` minimal**

Créer `templates/index.html` avec ce contenu temporaire (il sera remplacé en Task 7) :

```html
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>Ciné Canicule</title></head>
<body>
<h1>Ciné Canicule</h1>
<script>const DATA = {{ sessions_json | safe }};</script>
</body>
</html>
```

- [ ] **Étape 5 : Lancer les tests Flask**

Commande : `pytest tests/test_app.py -v`  
Attendu : `3 passed`

- [ ] **Étape 6 : Commit**

```bash
git add app.py templates/index.html tests/test_app.py
git commit -m "feat: Flask server with scrape orchestration"
```

---

### Task 7 : `index.html` — structure, données et switch A/B

**Files:**
- Modify: `templates/index.html` (remplacement complet)

- [ ] **Étape 1 : Remplacer `templates/index.html` par la version complète**

```html
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ciné Canicule — Lyon</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, sans-serif; background: #1a1a2e; color: #e0e0e0; min-height: 100vh; }
    header { background: #16213e; padding: 16px 24px; display: flex; align-items: center; gap: 16px; flex-wrap: wrap; border-bottom: 2px solid #0f3460; }
    header h1 { font-size: 1.4rem; color: #e94560; }
    .meta { font-size: 0.8rem; color: #888; margin-left: auto; }

    /* Switch A/B */
    .view-switch { display: flex; gap: 8px; }
    .view-btn { padding: 6px 16px; border: 1px solid #0f3460; background: transparent; color: #aaa; border-radius: 20px; cursor: pointer; font-size: 0.85rem; transition: all 0.2s; }
    .view-btn.active { background: #0f3460; color: #fff; border-color: #e94560; }

    /* Filters */
    .filters { background: #16213e; padding: 12px 24px; display: flex; gap: 20px; flex-wrap: wrap; align-items: center; border-bottom: 1px solid #0f3460; }
    .filter-group { display: flex; flex-direction: column; gap: 4px; }
    .filter-group label.title { font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 0.05em; }
    .cinema-checks { display: flex; gap: 8px; flex-wrap: wrap; }
    .cinema-checks label { font-size: 0.82rem; display: flex; align-items: center; gap: 4px; cursor: pointer; }
    input[type="text"] { background: #0f3460; border: 1px solid #2a4a7f; color: #e0e0e0; padding: 5px 10px; border-radius: 4px; font-size: 0.85rem; }
    input[type="range"] { accent-color: #e94560; }
    .temp-slider-label { font-size: 0.82rem; color: #ccc; }
    .reset-btn { padding: 5px 12px; background: transparent; border: 1px solid #555; color: #aaa; border-radius: 4px; cursor: pointer; font-size: 0.82rem; }
    .reset-btn:hover { border-color: #e94560; color: #e94560; }

    /* Refresh */
    .refresh-btn { padding: 7px 18px; background: #e94560; border: none; color: #fff; border-radius: 4px; cursor: pointer; font-size: 0.85rem; font-weight: bold; }
    .refresh-btn:disabled { opacity: 0.5; cursor: not-allowed; }
    .spinner { display: none; width: 16px; height: 16px; border: 2px solid #fff; border-top-color: transparent; border-radius: 50%; animation: spin 0.8s linear infinite; }
    @keyframes spin { to { transform: rotate(360deg); } }

    /* Main content */
    main { padding: 20px 24px; }
    .empty-msg { text-align: center; color: #888; padding: 60px; font-size: 1.1rem; }

    /* Vue A — Par jour */
    .day-group { margin-bottom: 28px; }
    .day-header { font-size: 1rem; font-weight: bold; color: #e94560; padding: 8px 0 6px; border-bottom: 1px solid #2a4a7f; margin-bottom: 8px; }
    
    /* Vue B — Par cinéma */
    .cinema-group { margin-bottom: 28px; }
    .cinema-header { font-size: 1rem; font-weight: bold; color: #4fc3f7; padding: 8px 0 6px; border-bottom: 1px solid #2a4a7f; margin-bottom: 8px; }

    /* Table */
    table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
    th { text-align: left; padding: 7px 10px; color: #888; font-weight: normal; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; }
    td { padding: 7px 10px; border-bottom: 1px solid #1e1e3a; }
    tr:last-child td { border-bottom: none; }
    .temp-badge { display: inline-block; padding: 2px 9px; border-radius: 12px; font-size: 0.8rem; font-weight: bold; color: #fff; }
    .no-temp { color: #555; }
    .tag { font-size: 0.75rem; background: #2a2a4a; color: #aaa; padding: 1px 6px; border-radius: 3px; }
  </style>
</head>
<body>

<header>
  <h1>🎬 Ciné Canicule — Lyon</h1>
  <div class="view-switch">
    <button class="view-btn active" onclick="setView('jour')" id="btn-jour">Par jour</button>
    <button class="view-btn" onclick="setView('cinema')" id="btn-cinema">Par cinéma</button>
  </div>
  <div style="display:flex;align-items:center;gap:10px;">
    <div class="spinner" id="spinner"></div>
    <button class="refresh-btn" id="refresh-btn" onclick="doRefresh()">Actualiser</button>
  </div>
  <div class="meta" id="meta-info"></div>
</header>

<div class="filters">
  <div class="filter-group">
    <span class="title">Cinémas</span>
    <div class="cinema-checks" id="cinema-checks"></div>
  </div>
  <div class="filter-group">
    <span class="title">Film</span>
    <input type="text" id="film-filter" placeholder="Rechercher un film..." oninput="renderView()">
  </div>
  <div class="filter-group">
    <span class="title">Temp. min : <span id="temp-val">0°C</span></span>
    <input type="range" id="temp-filter" min="0" max="45" value="0"
           oninput="document.getElementById('temp-val').textContent=this.value+'°C';renderView()">
  </div>
  <button class="reset-btn" onclick="resetFilters()">Réinitialiser</button>
</div>

<main id="main-content">
  <div class="empty-msg">Chargement...</div>
</main>

<script>
const DATA = {{ sessions_json | safe }};
let currentView = 'jour';
const CINEMAS = [...new Set((DATA.sessions || []).map(s => s.cinema))].sort();

// Init meta
(function() {
  const el = document.getElementById('meta-info');
  if (DATA.updated_at) {
    const d = new Date(DATA.updated_at);
    el.textContent = `Mis à jour : ${d.toLocaleString('fr-FR')} — ${DATA.sessions.length} séances`;
  } else {
    el.textContent = 'Aucune donnée — cliquez sur Actualiser';
  }
})();

// Init cinema checkboxes
(function() {
  const container = document.getElementById('cinema-checks');
  CINEMAS.forEach(c => {
    const lbl = document.createElement('label');
    const cb = document.createElement('input');
    cb.type = 'checkbox'; cb.checked = true; cb.value = c;
    cb.onchange = renderView;
    lbl.appendChild(cb);
    lbl.appendChild(document.createTextNode(' ' + c));
    container.appendChild(lbl);
  });
})();

function getTempStyle(temp) {
  if (temp === null || temp === undefined) return null;
  if (temp < 25) return { badge: '#3498db', bg: 'rgba(52,152,219,0.1)', border: '#3498db' };
  if (temp < 30) return { badge: '#2ecc71', bg: 'rgba(46,204,113,0.1)', border: '#2ecc71' };
  if (temp < 35) return { badge: '#f39c12', bg: 'rgba(243,156,18,0.12)', border: '#f39c12' };
  if (temp < 39) return { badge: '#e67e22', bg: 'rgba(230,126,34,0.15)', border: '#e67e22' };
  return { badge: '#e74c3c', bg: 'rgba(231,76,60,0.18)', border: '#e74c3c' };
}

function getFilteredSessions() {
  const checkedCinemas = [...document.querySelectorAll('#cinema-checks input:checked')].map(cb => cb.value);
  const filmQuery = document.getElementById('film-filter').value.toLowerCase();
  const tempMin = parseFloat(document.getElementById('temp-filter').value);

  return (DATA.sessions || []).filter(s => {
    if (!checkedCinemas.includes(s.cinema)) return false;
    if (filmQuery && !s.film.toLowerCase().includes(filmQuery)) return false;
    if (s.temperature !== null && s.temperature !== undefined && s.temperature < tempMin) return false;
    if (s.temperature === null && tempMin > 0) return false;
    return true;
  });
}

function renderSessionRow(s, showCinema = true) {
  const style = getTempStyle(s.temperature);
  const rowBg = style ? `background:${style.bg};border-left:3px solid ${style.border};` : '';
  const badge = s.temperature !== null && s.temperature !== undefined
    ? `<span class="temp-badge" style="background:${style.badge}">${Math.round(s.temperature)}°C</span>`
    : `<span class="no-temp">—</span>`;
  const cinemaCell = showCinema ? `<td>${s.cinema}</td>` : '';
  return `<tr style="${rowBg}">
    ${cinemaCell}
    <td>${s.heure}</td>
    <td>${s.film} <span class="tag">${s.version}</span></td>
    <td>${badge}</td>
  </tr>`;
}

function renderViewJour(sessions) {
  const byDate = {};
  sessions.forEach(s => { (byDate[s.date] = byDate[s.date] || []).push(s); });
  const dates = Object.keys(byDate).sort();
  if (!dates.length) return '<div class="empty-msg">Aucune séance pour ces filtres.</div>';

  return dates.map(date => {
    const d = new Date(date + 'T12:00:00');
    const label = d.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });
    const rows = byDate[date]
      .sort((a, b) => a.heure.localeCompare(b.heure))
      .map(s => renderSessionRow(s, true))
      .join('');
    return `<div class="day-group">
      <div class="day-header">${label.charAt(0).toUpperCase() + label.slice(1)}</div>
      <table>
        <thead><tr><th>Cinéma</th><th>Heure</th><th>Film</th><th>🌡️</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
  }).join('');
}

function renderViewCinema(sessions) {
  const byCinema = {};
  sessions.forEach(s => { (byCinema[s.cinema] = byCinema[s.cinema] || []).push(s); });
  const cinemas = Object.keys(byCinema).sort();
  if (!cinemas.length) return '<div class="empty-msg">Aucune séance pour ces filtres.</div>';

  return cinemas.map(cinema => {
    const rows = byCinema[cinema]
      .sort((a, b) => a.date.localeCompare(b.date) || a.heure.localeCompare(b.heure))
      .map(s => renderSessionRow(s, false))
      .join('');
    return `<div class="cinema-group">
      <div class="cinema-header">🎬 ${cinema}</div>
      <table>
        <thead><tr><th>Date</th><th>Heure</th><th>Film</th><th>🌡️</th></tr></thead>
        <tbody>${rows.replace(/<td>/g, (m, i, str) => {
          // Injecter la date dans la première colonne manquante
          return m;
        })}</tbody>
      </table>
    </div>`;
  }).join('');
}

function renderView() {
  const sessions = getFilteredSessions();
  const content = currentView === 'jour'
    ? renderViewJour(sessions)
    : renderViewCinema(sessions);
  document.getElementById('main-content').innerHTML = content;
}

function setView(view) {
  currentView = view;
  document.getElementById('btn-jour').classList.toggle('active', view === 'jour');
  document.getElementById('btn-cinema').classList.toggle('active', view === 'cinema');
  renderView();
}

function resetFilters() {
  document.querySelectorAll('#cinema-checks input').forEach(cb => cb.checked = true);
  document.getElementById('film-filter').value = '';
  document.getElementById('temp-filter').value = 0;
  document.getElementById('temp-val').textContent = '0°C';
  renderView();
}

async function doRefresh() {
  const btn = document.getElementById('refresh-btn');
  const spinner = document.getElementById('spinner');
  btn.disabled = true;
  btn.textContent = 'Actualisation (~3 min)...';
  spinner.style.display = 'inline-block';

  try {
    const resp = await fetch('/refresh', { method: 'POST' });
    const data = await resp.json();
    const d = new Date(data.updated_at);
    document.getElementById('meta-info').textContent =
      `Mis à jour : ${d.toLocaleString('fr-FR')} — ${data.count} séances`;
    // Recharger la page pour intégrer les nouvelles données
    window.location.reload();
  } catch (e) {
    alert('Erreur lors de l\'actualisation : ' + e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Actualiser';
    spinner.style.display = 'none';
  }
}

// Render initial view
if (!DATA.sessions || DATA.sessions.length === 0) {
  document.getElementById('main-content').innerHTML =
    '<div class="empty-msg">Aucune donnée — cliquez sur <strong>Actualiser</strong> pour scraper les séances.</div>';
} else {
  renderView();
}
</script>
</body>
</html>
```

- [ ] **Étape 2 : Corriger `renderViewCinema` — la date dans les lignes**

La fonction `renderViewCinema` doit passer `false` à `renderSessionRow` (pas de colonne cinéma) mais afficher la date à la place. Remplacer la fonction `renderViewCinema` par cette version corrigée dans `index.html` :

```javascript
function renderViewCinema(sessions) {
  const byCinema = {};
  sessions.forEach(s => { (byCinema[s.cinema] = byCinema[s.cinema] || []).push(s); });
  const cinemas = Object.keys(byCinema).sort();
  if (!cinemas.length) return '<div class="empty-msg">Aucune séance pour ces filtres.</div>';

  return cinemas.map(cinema => {
    const rows = byCinema[cinema]
      .sort((a, b) => a.date.localeCompare(b.date) || a.heure.localeCompare(b.heure))
      .map(s => {
        const style = getTempStyle(s.temperature);
        const rowBg = style ? `background:${style.bg};border-left:3px solid ${style.border};` : '';
        const badge = s.temperature !== null && s.temperature !== undefined
          ? `<span class="temp-badge" style="background:${style.badge}">${Math.round(s.temperature)}°C</span>`
          : `<span class="no-temp">—</span>`;
        const d = new Date(s.date + 'T12:00:00');
        const dateLabel = d.toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric', month: 'short' });
        return `<tr style="${rowBg}">
          <td>${dateLabel}</td>
          <td>${s.heure}</td>
          <td>${s.film} <span class="tag">${s.version}</span></td>
          <td>${badge}</td>
        </tr>`;
      }).join('');
    return `<div class="cinema-group">
      <div class="cinema-header">🎬 ${cinema}</div>
      <table>
        <thead><tr><th>Date</th><th>Heure</th><th>Film</th><th>🌡️</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
  }).join('');
}
```

> Remplacer la version incorrecte de `renderViewCinema` dans le fichier. Garder le reste intact.

- [ ] **Étape 3 : Tester manuellement**

Lancer `python app.py` et ouvrir `http://localhost:5000`.

Vérifier :
- La page s'affiche sans erreur JavaScript (F12 > Console)
- Le switch "Par jour" / "Par cinéma" fonctionne
- Les filtres cinéma, film et température filtrent en temps réel
- Le bouton "Réinitialiser" remet tout à zéro

Si `sessions.json` n'existe pas encore, le message "Aucune donnée" s'affiche — c'est attendu.

- [ ] **Étape 4 : Commit**

```bash
git add templates/index.html
git commit -m "feat: complete HTML interface with A/B switch, filters, and refresh"
```

---

### Task 8 : Test end-to-end complet

**Files:**
- Aucun fichier modifié — test manuel uniquement

- [ ] **Étape 1 : Lancer `lancer.bat`**

Double-cliquer sur `lancer.bat`. Vérifier :
- Le navigateur s'ouvre sur `http://localhost:5000`
- La page affiche "Aucune donnée — cliquez sur Actualiser"

- [ ] **Étape 2 : Lancer le scraping via le bouton**

Cliquer sur "Actualiser". Observer :
- Le bouton devient "Actualisation (~3 min)..." et est désactivé
- Le spinner tourne
- Après ~3 minutes, la page se recharge avec les séances

- [ ] **Étape 3 : Vérifier les données**

- Les 9 cinémas apparaissent dans les filtres
- Les températures s'affichent avec la bonne couleur (badge + fond de ligne)
- Les séances J+16 à J+20 affichent "—" pour la température
- Le switch "Par jour" / "Par cinéma" fonctionne correctement
- Les filtres cinéma, film et température fonctionnent

- [ ] **Étape 4 : Vérifier `data/sessions.json`**

Ouvrir `data/sessions.json` et vérifier :
- Champ `updated_at` renseigné
- Champ `sessions` contient des centaines d'entrées
- Les entrées ont les champs `cinema`, `film`, `date`, `heure`, `version`, `temperature`

- [ ] **Étape 5 : Commit final**

```bash
git add data/.gitkeep
git commit -m "chore: add data directory placeholder"
```

(Ne pas commiter `sessions.json` — ajouter `data/sessions.json` dans `.gitignore` si nécessaire)

---

## Résumé des tâches

| Task | Description | Tests |
|------|-------------|-------|
| 1 | Setup (requirements, lancer.bat) | Manuel |
| 2 | IDs AlloCiné (recherche manuelle) | Manuel |
| 3 | `weather.py` | `pytest tests/test_weather.py` |
| 4 | `scraper.py` — page unique | `pytest tests/test_scraper.py` |
| 5 | `scraper.py` — scraping complet | `pytest tests/test_scraper.py` |
| 6 | `app.py` — Flask | `pytest tests/test_app.py` |
| 7 | `index.html` — UI complète | Manuel |
| 8 | End-to-end | Manuel |

Commande pour lancer tous les tests unitaires : `pytest tests/ -v`
