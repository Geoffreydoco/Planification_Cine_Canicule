# Design — Ciné Canicule (Lyon)

**Date :** 2026-06-30  
**Statut :** Approuvé

---

## Objectif

Générer une page HTML locale listant les séances de cinéma dans 9 cinémas lyonnais sur 3 semaines, enrichies de la température prévue à l'heure de chaque séance. L'utilisateur double-clique sur `lancer.bat` pour démarrer, puis clique "Actualiser" dans le navigateur pour mettre à jour les données.

---

## Cinémas couverts

| Nom affiché | ID AlloCiné (à rechercher) |
|---|---|
| Pathé Bellecour | `C????` |
| Lumière Terreaux | `C????` |
| Lumière Fourmi | `C????` |
| Lumière Bellecour | `C????` |
| Le Cinéma | `C????` |
| Cinéma Opéra | `C????` |
| Le Zola (Villeurbanne) | `C????` |
| UGC Part-Dieu | `C????` |
| Institut Lumière | `C????` |

Les IDs numériques AlloCiné (format `CXXXXX`) seront récupérés lors de la première étape d'implémentation en cherchant chaque cinéma sur AlloCiné et en notant l'ID dans l'URL. Ils seront hardcodés dans `scraper.py`.

---

## Architecture

```
projet-cine-canicule/
├── lancer.bat              # Point d'entrée : installe les deps, lance Flask, ouvre le navigateur
├── app.py                  # Serveur Flask
├── scraper.py              # Scraping AlloCiné
├── weather.py              # Températures horaires Open-Meteo
├── data/
│   └── sessions.json       # Cache : liste de séances enrichies
└── templates/
    └── index.html          # Interface utilisateur
```

---

## Composants

### `lancer.bat`

1. Vérifie que Python est installé
2. Installe les dépendances si absentes : `pip install flask requests beautifulsoup4`
3. Lance `python app.py`
4. Ouvre `http://localhost:5000` dans le navigateur par défaut

### `scraper.py`

- Scrape les pages de séances AlloCiné pour chacun des 9 cinémas
- URL cible : `https://www.allocine.fr/seances/salle_gen_csalle=CXXXXX-d_date=YYYY-MM-DD.html` (par cinéma ET par date)
- Période : J+0 à J+20 → **21 dates × 9 cinémas = 189 requêtes** au total
- Headers HTTP avec un User-Agent réaliste pour éviter les blocages basiques
- Délai de 1 seconde entre chaque requête → durée totale du scraping : ~3 minutes
- Un message de progression est affiché sur la page pendant le scraping
- Pour chaque séance extraite : `{film, cinema, date, heure, version (VF/VO/3D)}`
- Résultat : liste brute de séances, sans météo

### `weather.py`

- API : Open-Meteo (`https://api.open-meteo.com/v1/forecast`)
- Paramètres : latitude=45.75, longitude=4.85 (Lyon), `hourly=temperature_2m`, `forecast_days=16`
- Pour chaque séance, trouve la température à l'heure la plus proche (arrondie à l'heure)
- Jours J+16 à J+20 : champ `temperature` laissé à `null`, affiché "—" dans l'interface
- Résultat : enrichit chaque séance avec `{temperature: float | null}`

### `app.py`

Routes Flask :
- `GET /` → sert `index.html` (lit `data/sessions.json`)
- `POST /refresh` → appelle `scraper.py` + `weather.py`, écrit `sessions.json`, répond `{status: "ok", count: N, updated_at: "..."}`
- Ouvre automatiquement le navigateur au démarrage si `sessions.json` existe, sinon déclenche un premier scraping

### `templates/index.html`

**Switch de vue :**
- Vue A "Par jour" : regroupement par date, chaque groupe liste les séances du jour (heure, film, cinéma, température)
- Vue B "Par cinéma" : regroupement par cinéma, chaque section liste les séances du cinéma sur 3 semaines

**Filtres (appliqués côté client en JavaScript) :**
- Checkboxes cinémas (9 cases, toutes cochées par défaut)
- Champ texte film (filtre sur le titre, insensible à la casse)
- Slider température minimale (0°C → 45°C, par défaut 0°C) — n'affiche que les séances avec `temperature >= valeur`
- Bouton "Réinitialiser les filtres"

**Bouton "Actualiser" :**
- Lance `POST /refresh`, affiche un spinner pendant le scraping
- Affiche la date/heure de la dernière mise à jour et le nombre de séances récupérées

**Codage couleur température :**
- `< 25°C` → bleu `#3498db`
- `25–29°C` → vert `#2ecc71`
- `30–34°C` → jaune/orange `#f39c12`
- `35–38°C` → orange foncé `#e67e22`
- `≥ 39°C` → rouge `#e74c3c`
- Appliqué sur : badge coloré sur la cellule température + légère teinte de fond sur la ligne

---

## Modèle de données (`sessions.json`)

```json
{
  "updated_at": "2026-06-30T10:00:00",
  "sessions": [
    {
      "cinema": "Pathé Bellecour",
      "film": "Dune 2",
      "date": "2026-06-30",
      "heure": "14:00",
      "version": "VF",
      "temperature": 36.2
    }
  ]
}
```

---

## Gestion des erreurs

- Si AlloCiné bloque une requête (429 / structure HTML inattendue) : le cinéma concerné est ignoré, un avertissement est affiché sur la page
- Si `sessions.json` n'existe pas au démarrage : Flask déclenche automatiquement un premier scraping
- Si Open-Meteo est inaccessible : toutes les températures restent `null`
- Délai max de 10 secondes par requête, timeout propre affiché à l'utilisateur

---

## Contraintes

- Python 3.8+ requis
- Dépendances : `flask`, `requests`, `beautifulsoup4` (installées automatiquement par `lancer.bat`)
- Fonctionne sans connexion après le premier scraping (données en cache)
- Open-Meteo : prévisions disponibles sur 16 jours max — les séances J+16 à J+20 n'ont pas de température
