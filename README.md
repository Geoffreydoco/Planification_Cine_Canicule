# Ciné Canicule

Quand il fait chaud à Lyon, les cinémas climatisés deviennent des havres. Ciné Canicule affiche les programmations des salles lyonnaises avec la température prévue à l'heure de chaque séance, pour choisir son film selon la météo.

## Ce que ça fait

- Récupère les séances de ~10 cinémas lyonnais et villeurbannais via AlloCiné
- Récupère les températures horaires et min/max journalières via Open-Meteo (sans clé API)
- 3 vues : par jour, par cinéma, par film (affiches, synopsis, notes, casting)
- Filtres : cinéma, film, version VO/VF, films tout public uniquement
- Mode clair/sombre, carte au survol des cinémas

## Architecture

```
app.py                    Serveur Flask dev — interface + API /sessions.json + refresh
scraper.py                Scrape AlloCiné (découverte dynamique, ~10 cinémas × 21 jours, 5 threads)
weather.py                Températures Open-Meteo (1 appel HTTP combiné horaire + journalier)
templates/index.html      Frontend unique partagé entre Flask et build statique
scripts/build_static.py   Génère _site/ pour GitHub Pages
scripts/update_data.py    Met à jour sessions.json seul (sans regénérer le HTML)
data/sessions.json        Cache local des séances + températures
```

## Installation

```bash
pip install -r requirements.txt
```

## Lancer en mode développement

```bash
python app.py
```

Ou double-cliquer `lancer.bat` sous Windows.

Ouvre automatiquement http://localhost:5000. Le bouton **Actualiser** déclenche un nouveau scraping (~45 s) et rafraîchit la page.

## Déploiement GitHub Pages

```bash
python scripts/build_static.py
```

Génère `_site/index.html` et `_site/sessions.json`. Configurer GitHub Pages sur le dossier `_site/` de la branche `main`.

## Mise à jour automatique des données (cron / GitHub Actions)

```bash
python scripts/update_data.py
```

Écrit `sessions.json` à la racine. À utiliser dans un workflow GitHub Actions pour rafraîchir les données sans reconstruire le site complet.

## Tests

```bash
pytest
pytest -v tests/test_scraper.py   # scraper uniquement
```

## Sources de données

| Source | Usage |
|--------|-------|
| [AlloCiné](https://www.allocine.fr/) via [allocineAPI](https://pypi.org/project/allocineAPI/) | Séances, affiches, synopsis, notes, casting |
| [Open-Meteo](https://open-meteo.com/) | Températures horaires et min/max (gratuit, sans clé) |
| [Nominatim / OpenStreetMap](https://nominatim.org/) | Géocodage des cinémas pour la carte au survol |
