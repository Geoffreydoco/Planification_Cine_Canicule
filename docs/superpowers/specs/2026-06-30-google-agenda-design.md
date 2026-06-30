# Design — Bouton Google Agenda par séance

**Date :** 2026-06-30  
**Statut :** Approuvé

---

## Objectif

Ajouter un bouton `📅` sur chaque séance individuelle qui ouvre Google Agenda dans un nouvel onglet avec l'événement pré-rempli (titre = film, heure de début et de fin, localisation = nom du cinéma). Aucune authentification requise.

---

## Intégration Google Agenda

Méthode : URL directe `https://calendar.google.com/calendar/render?action=TEMPLATE` — pas d'API, pas d'OAuth.

Paramètres :
- `text` : `<film> (<version>)` — ex : `Dune 2 (VF)`
- `dates` : `YYYYMMDDTHHmmss/YYYYMMDDTHHmmss` en heure locale (pas de suffixe Z — Google utilise le fuseau de l'utilisateur)
- `location` : nom du cinéma (ex : `Pathé Bellecour`)
- `details` : `<film> - <version>`

Exemple complet :
```
https://calendar.google.com/calendar/render?action=TEMPLATE
  &text=Dune+2+(VF)
  &dates=20260630T140000/20260630T163500
  &location=Path%C3%A9+Bellecour
  &details=Dune+2+-+VF
```

---

## Calcul de l'heure de fin

À partir de `s.heure` (format `HH:MM`) et `s.duration` (format `"2h35"`, `"1h30"`, `"45min"` ou `""`).

Algorithme :
1. Parser `s.duration` : chercher `(\d+)h` pour les heures et `(\d+)(?:min)?$` pour les minutes
2. Calculer les minutes totales → ajouter à `s.heure`
3. Gérer le passage à minuit (ex : séance à 22h30 de 2h → 00h30 le lendemain, date +1)
4. **Fallback** : si duration absente ou non parseable → heure de fin = heure de début + 2h

---

## Fonction `calendarUrl(s)`

Entrée : un objet session `{ date, heure, duration, film, version, cinema }`.

Retourne l'URL Google Agenda complète en encodant tous les paramètres via `encodeURIComponent`.

---

## Fonction `calBtn(s)`

Retourne le HTML du bouton :
```html
<a href="<calendarUrl(s)>" target="_blank" rel="noopener"
   class="cal-btn" title="Ajouter à Google Agenda">📅</a>
```

Utilise `<a>` plutôt que `<button>` pour éviter d'intercepter les événements du formulaire et permettre le Ctrl+clic (ouvrir dans un autre onglet).

---

## Placement des boutons

### Mode non-groupé (`buildRowJour`, `buildRowCinema`)

Colonne supplémentaire ajoutée en fin de tableau :

| Avant | Après |
|---|---|
| `Cinéma \| Heure \| Durée \| Film \| 🌡️` | `Cinéma \| Heure \| Durée \| Film \| 🌡️ \| ` (vide) |

- `<th></th>` ajouté dans `theadHtml` de la branche non-groupée des deux vues
- `<td>${calBtn(s)}</td>` ajouté dans `buildRowJour` et `buildRowCinema`

### Mode groupé (`sessionBadge`)

Le bouton est inséré inline, côte à côte avec le badge heure+temp :

```
[14:00 ●36°C] [📅]   [17:30 ●37°C] [📅]
```

`sessionBadge(s)` retourne `<badge heure+temp> + <calBtn(s)>` enveloppés dans un span `white-space:nowrap` pour garder badge et bouton solidaires lors du retour à la ligne (flex-wrap).

---

## Style `.cal-btn`

```css
.cal-btn {
  display: inline-flex;
  align-items: center;
  background: transparent;
  border: 1px solid #3a3a5a;
  color: #888;
  border-radius: 4px;
  padding: 1px 5px;
  font-size: 0.72rem;
  cursor: pointer;
  text-decoration: none;
  line-height: 1.4;
  transition: border-color .15s, color .15s;
}
.cal-btn:hover {
  border-color: #e94560;
  color: #e94560;
}
```

---

## Fichiers modifiés

- `templates/index.html` uniquement — 100% côté client, aucun changement backend.

---

## Modèle de données

Aucun changement — `calendarUrl` utilise les champs déjà présents dans chaque session : `date`, `heure`, `duration`, `film`, `version`, `cinema`.
