# Filtre "Genres du film" — Design Spec

**Date :** 2026-07-01  
**Statut :** Approuvé

## Contexte

L'application Ciné Canicule dispose de deux filtres déroulants dans la sidebar : "Cinémas" et "Film à l'affiche". Cette spec décrit l'ajout d'un troisième filtre identique pour "Genres du film".

Les séances (`sessions.json`) portent déjà un champ `genres: string[]` renseigné par le scraper AlloCiné.

## Approche retenue

Clone exact du filtre "Film à l'affiche" (pattern DSFR dropdown), avec logique de filtrage OR multi-genre.

## HTML

Nouveau bloc `<div class="filter-group">` inséré entre le filtre film et la section Options :

```html
<div class="filter-group">
  <h2>Genres du film</h2>
  <nav class="fr-nav" id="genre-nav" role="navigation" aria-label="Filtre par genre">
    <ul class="fr-nav__list">
      <li class="fr-nav__item">
        <button class="fr-nav__btn" aria-expanded="false"
                aria-controls="genre-menu-panel" id="genre-nav-btn"
                onclick="toggleGenreDropdown()">
          <span id="genre-dropdown-label">Tous les genres</span>
        </button>
        <div class="fr-collapse fr-menu" id="genre-menu-panel">
          <div style="padding:6px 6px 4px;">
            <input type="text" id="genre-filter-search"
                   placeholder="Rechercher un genre…"
                   oninput="filterGenreList(this.value)">
          </div>
          <ul class="fr-menu__list" id="genre-options"></ul>
        </div>
      </li>
    </ul>
  </nav>
</div>
```

## CSS

Étendre tous les sélecteurs groupés `#film-nav, #cinema-nav` pour inclure `#genre-nav`. Même chose pour `#film-filter-search, #cinema-filter-search` → ajouter `#genre-filter-search`. Environ 10 règles à étendre, aucune règle CSS nouvelle.

Idem pour les variantes light mode :
- `body.light #film-nav .fr-collapse, body.light #cinema-nav .fr-collapse` → ajouter `body.light #genre-nav .fr-collapse`

## JavaScript

### State

```js
let allGenres = [];
let selectedGenres = new Set();
```

### Init (`init()`)

```js
allGenres = [...new Set(DATA.sessions.flatMap(s => s.genres || []))].sort((a, b) => a.localeCompare(b, 'fr'));
selectedGenres = new Set(allGenres);
renderGenreOptions(allGenres);
```

### Filtrage (`getFilteredSessions()`)

Condition supplémentaire après les filtres cinéma et film :

```js
if (selectedGenres.size < allGenres.length) {
  const sGenres = s.genres || [];
  if (sGenres.length === 0) return false;
  if (!sGenres.some(g => selectedGenres.has(g))) return false;
}
```

Logique OR : une séance passe si au moins un de ses genres est dans `selectedGenres`. Les séances sans genres sont exclues dès qu'un filtre genre est actif.

### Fonctions

Copie fidèle du pattern film, avec renommage `Film` → `Genre` :

- `renderGenreOptions(genres)` — rendu de la liste, option "Tous les genres" en tête
- `updateGenreDropdownLabel()` — "Tous les genres" / nom unique / "N genres sélectionnés"
- `filterGenreList(query)` — filtre la liste selon la saisie
- `toggleGenre(genre)` — bascule sélection individuelle (depuis "tous" → sélection unique)
- `selectAllGenres()` — remet tout à sélectionné
- `toggleGenreDropdown()` — ouvre/ferme le panel
- Listener `click` sur `#genre-options` (délégation)
- Fermeture du panel dans le listener `document click` existant

### Reset (`resetFilters()`)

Ajouter l'appel `selectAllGenres()`.

## Comportement attendu

| Situation | Résultat |
|-----------|----------|
| Tous les genres sélectionnés (défaut) | Aucun filtrage genre appliqué |
| Un genre sélectionné (ex. "Comédie") | Seules les séances ayant "Comédie" dans leurs genres sont affichées |
| Plusieurs genres (ex. "Comédie" + "Action") | Séances ayant au moins l'un des deux genres (OR) |
| Séance sans genres (`[]`) avec filtre actif | Exclue |
| Réinitialiser les choix | Tous les genres re-sélectionnés |
