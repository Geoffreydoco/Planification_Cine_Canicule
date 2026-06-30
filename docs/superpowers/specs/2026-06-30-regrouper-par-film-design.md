# Design — Regrouper par film

**Date :** 2026-06-30  
**Statut :** Approuvé

---

## Objectif

Ajouter un toggle "Regrouper par film" (coché par défaut) qui fusionne les séances du même film dans les deux vues. Quand il est actif, chaque ligne représente un couple (cinéma × film) ou (film × date), avec les heures et températures affichées sous forme de badges dans une colonne "Séances". Quand il est décoché, le tableau reste identique à l'actuel.

---

## Toggle

- **Emplacement :** sidebar, sous le filtre Film
- **Label :** "Regrouper par film"
- **État par défaut :** coché
- **Variable JS :** `groupByFilm` (booléen)
- **Comportement :** tout changement appelle `applyFilters()` pour re-rendre immédiatement

---

## Vue Par jour — groupement actif

### Colonnes

| Avant | Après |
|---|---|
| Cinéma \| Heure \| Durée \| Film \| 🌡️ | Cinéma \| Film \| Durée \| Séances |

### Logique de regroupement

- Clé de groupe : `(cinema, film, version)` — VF et VO restent sur des lignes séparées
- Tri des lignes : par `cinema` puis par `film` alphabétique, puis par `version`
- Tri des badges dans la cellule Séances : par `heure` chronologique

### Cellule Séances

Liste horizontale (flex-wrap) de badges `HH:MM — badge_temp`. Chaque badge est rendu comme :

```
14:00 — ●36°C   17:30 — ●37°C   20:00 — —
```

- Si `temperature !== null` : badge coloré via `tempBadge()`
- Si `temperature === null` : affiche juste `HH:MM`

### Couleur de ligne

Basée sur la **température maximale** non-null du groupe. Si toutes les températures sont null : `row-none`.

### Durée

Identique pour toutes les séances d'un même film — affiche la valeur commune. En cas d'incohérence (rare), affiche la première valeur trouvée.

### Lien film et tooltip

Le nom du film reste cliquable (lien AlloCiné) et le tooltip reste actif, comme dans le mode non-groupé. Les données poster/synopsis proviennent de la première séance du groupe. La version (VF/VO) est affichée en petit à côté du titre, comme actuellement.

---

## Vue Par cinéma — groupement actif

### Colonnes

| Avant | Après |
|---|---|
| Date \| Heure \| Durée \| Film \| 🌡️ | Date \| Film \| Durée \| Séances |

### Logique de regroupement

- Clé de groupe : `(film, date, version)` au sein d'un cinéma — VF et VO restent séparés
- Tri des lignes : par `date` puis par `film` alphabétique, puis par `version`
- Tri des badges dans la cellule Séances : par `heure` chronologique

### Cellule Séances

Même format que Vue Par jour.

### Couleur de ligne

Même logique (max température non-null du groupe).

---

## Groupement désactivé

Aucun changement par rapport au comportement actuel. Les en-têtes, les lignes et la logique de rendu reviennent exactement à leur forme d'origine (`buildRowJour` / `buildRowCinema`).

---

## Fichiers modifiés

- `templates/index.html` uniquement — logique 100% côté client JS + HTML

---

## Modèle de données

Aucun changement au modèle de données (`sessions.json`). Le regroupement est purement côté affichage.
