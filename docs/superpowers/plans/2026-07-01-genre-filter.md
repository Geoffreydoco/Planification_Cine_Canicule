# Filtre "Genres du film" — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ajouter un troisième filtre déroulant "Genres du film" dans la sidebar, identique au pattern "Cinémas" / "Film à l'affiche", avec filtrage OR multi-genre.

**Architecture:** Modification d'un unique fichier `templates/index.html` en trois zones : CSS (extension des sélecteurs groupés), HTML (nouveau bloc filter-group), JS (state, init, filtrage, fonctions). Pas de backend modifié — les genres sont déjà présents dans `sessions.json` via `s.genres: string[]`.

**Tech Stack:** HTML/CSS/JS vanilla, Flask (non modifié), pattern DSFR dropdown existant.

> **Note TDD :** Il n'existe pas d'infrastructure de test frontend dans ce projet. Les tasks JS sont vérifiées par test manuel dans le navigateur (Task 8).

---

### Task 1 : CSS — Étendre les sélecteurs pour `#genre-nav`

**Files:**
- Modify: `templates/index.html` (section `<style>`, lignes ~147–243)

- [ ] **Étape 1 : Étendre le sélecteur `position: relative`**

Remplacer :
```css
#film-nav, #cinema-nav { position: relative; }
```
Par :
```css
#film-nav, #cinema-nav, #genre-nav { position: relative; }
```

- [ ] **Étape 2 : Étendre `.fr-nav__list`**

Remplacer :
```css
    #film-nav .fr-nav__list, #cinema-nav .fr-nav__list { list-style: none; margin: 0; padding: 0; }
```
Par :
```css
    #film-nav .fr-nav__list, #cinema-nav .fr-nav__list, #genre-nav .fr-nav__list { list-style: none; margin: 0; padding: 0; }
```

- [ ] **Étape 3 : Étendre `.fr-nav__item`**

Remplacer :
```css
    #film-nav .fr-nav__item, #cinema-nav .fr-nav__item { position: relative; }
```
Par :
```css
    #film-nav .fr-nav__item, #cinema-nav .fr-nav__item, #genre-nav .fr-nav__item { position: relative; }
```

- [ ] **Étape 4 : Étendre `.fr-nav__btn` (bloc multi-lignes)**

Remplacer :
```css
    #film-nav .fr-nav__btn, #cinema-nav .fr-nav__btn {
```
Par :
```css
    #film-nav .fr-nav__btn, #cinema-nav .fr-nav__btn, #genre-nav .fr-nav__btn {
```

- [ ] **Étape 5 : Étendre `.fr-nav__btn::after`**

Remplacer :
```css
    #film-nav .fr-nav__btn::after, #cinema-nav .fr-nav__btn::after {
```
Par :
```css
    #film-nav .fr-nav__btn::after, #cinema-nav .fr-nav__btn::after, #genre-nav .fr-nav__btn::after {
```

- [ ] **Étape 6 : Étendre `.fr-nav__btn[aria-expanded="true"]::after`**

Remplacer :
```css
    #film-nav .fr-nav__btn[aria-expanded="true"]::after,
    #cinema-nav .fr-nav__btn[aria-expanded="true"]::after { transform: rotate(180deg); }
```
Par :
```css
    #film-nav .fr-nav__btn[aria-expanded="true"]::after,
    #cinema-nav .fr-nav__btn[aria-expanded="true"]::after,
    #genre-nav .fr-nav__btn[aria-expanded="true"]::after { transform: rotate(180deg); }
```

- [ ] **Étape 7 : Étendre `.fr-nav__btn:hover`**

Remplacer :
```css
    #film-nav .fr-nav__btn:hover, #cinema-nav .fr-nav__btn:hover { border-color: var(--accent); }
```
Par :
```css
    #film-nav .fr-nav__btn:hover, #cinema-nav .fr-nav__btn:hover, #genre-nav .fr-nav__btn:hover { border-color: var(--accent); }
```

- [ ] **Étape 8 : Étendre `.fr-collapse`**

Remplacer :
```css
    #film-nav .fr-collapse, #cinema-nav .fr-collapse {
```
Par :
```css
    #film-nav .fr-collapse, #cinema-nav .fr-collapse, #genre-nav .fr-collapse {
```

- [ ] **Étape 9 : Étendre `.fr-collapse--expanded`**

Remplacer :
```css
    #film-nav .fr-collapse--expanded, #cinema-nav .fr-collapse--expanded { display: block; }
```
Par :
```css
    #film-nav .fr-collapse--expanded, #cinema-nav .fr-collapse--expanded, #genre-nav .fr-collapse--expanded { display: block; }
```

- [ ] **Étape 10 : Étendre l'input de recherche**

Remplacer :
```css
    #film-filter-search, #cinema-filter-search {
```
Par :
```css
    #film-filter-search, #cinema-filter-search, #genre-filter-search {
```

- [ ] **Étape 11 : Étendre `::placeholder`**

Remplacer :
```css
    #film-filter-search::placeholder, #cinema-filter-search::placeholder { color: var(--muted); }
```
Par :
```css
    #film-filter-search::placeholder, #cinema-filter-search::placeholder, #genre-filter-search::placeholder { color: var(--muted); }
```

- [ ] **Étape 12 : Étendre `:focus`**

Remplacer :
```css
    #film-filter-search:focus, #cinema-filter-search:focus { outline: none; border-color: var(--accent); }
```
Par :
```css
    #film-filter-search:focus, #cinema-filter-search:focus, #genre-filter-search:focus { outline: none; border-color: var(--accent); }
```

- [ ] **Étape 13 : Étendre `.fr-menu__list`**

Remplacer :
```css
    #film-nav .fr-menu__list, #cinema-nav .fr-menu__list {
```
Par :
```css
    #film-nav .fr-menu__list, #cinema-nav .fr-menu__list, #genre-nav .fr-menu__list {
```

- [ ] **Étape 14 : Étendre `.fr-nav__link`**

Remplacer :
```css
    #film-nav .fr-nav__link, #cinema-nav .fr-nav__link {
```
Par :
```css
    #film-nav .fr-nav__link, #cinema-nav .fr-nav__link, #genre-nav .fr-nav__link {
```

- [ ] **Étape 15 : Étendre `.fr-nav__link:hover`**

Remplacer :
```css
    #film-nav .fr-nav__link:hover, #cinema-nav .fr-nav__link:hover {
```
Par :
```css
    #film-nav .fr-nav__link:hover, #cinema-nav .fr-nav__link:hover, #genre-nav .fr-nav__link:hover {
```

- [ ] **Étape 16 : Étendre `.fr-nav__link--active`**

Remplacer :
```css
    #film-nav .fr-nav__link--active, #cinema-nav .fr-nav__link--active {
```
Par :
```css
    #film-nav .fr-nav__link--active, #cinema-nav .fr-nav__link--active, #genre-nav .fr-nav__link--active {
```

- [ ] **Étape 17 : Étendre `li:first-child .fr-nav__link`**

Remplacer :
```css
    #film-nav li:first-child .fr-nav__link, #cinema-nav li:first-child .fr-nav__link {
```
Par :
```css
    #film-nav li:first-child .fr-nav__link, #cinema-nav li:first-child .fr-nav__link, #genre-nav li:first-child .fr-nav__link {
```

- [ ] **Étape 18 : Étendre le sélecteur light mode `.fr-collapse`**

Remplacer :
```css
    body.light #film-nav .fr-collapse,
    body.light #cinema-nav .fr-collapse { background:#fff; border-color:#c0ccd8; }
```
Par :
```css
    body.light #film-nav .fr-collapse,
    body.light #cinema-nav .fr-collapse,
    body.light #genre-nav .fr-collapse { background:#fff; border-color:#c0ccd8; }
```

- [ ] **Étape 19 : Commit CSS**

```bash
git add templates/index.html
git commit -m "feat: étendre sélecteurs CSS pour #genre-nav"
```

---

### Task 2 : HTML — Bloc filtre genres

**Files:**
- Modify: `templates/index.html` (section `<aside>`, après le bloc `<!-- Film filter -->`)

- [ ] **Étape 1 : Insérer le bloc HTML genre**

Après la `</div>` fermante du bloc `<!-- Film filter -->` (ligne ~757), insérer :

```html

    <!-- Genre filter -->
    <div class="filter-group">
      <h2>Genres du film</h2>
      <nav class="fr-nav" id="genre-nav" role="navigation" aria-label="Filtre par genre">
        <ul class="fr-nav__list">
          <li class="fr-nav__item">
            <button class="fr-nav__btn" aria-expanded="false" aria-controls="genre-menu-panel" id="genre-nav-btn" onclick="toggleGenreDropdown()">
              <span id="genre-dropdown-label">Tous les genres</span>
            </button>
            <div class="fr-collapse fr-menu" id="genre-menu-panel">
              <div style="padding:6px 6px 4px;">
                <input type="text" id="genre-filter-search" placeholder="Rechercher un genre…" oninput="filterGenreList(this.value)">
              </div>
              <ul class="fr-menu__list" id="genre-options"></ul>
            </div>
          </li>
        </ul>
      </nav>
    </div>
```

Le bloc doit être inséré exactement entre la `</div>` du filter-group film et la `<!-- Group by film toggle + advanced info -->`.

Vérifier que la structure dans `<aside>` est dans cet ordre :
1. `<!-- View switch -->`
2. `<!-- Cinema filter -->`
3. `<!-- Film filter -->`
4. `<!-- Genre filter -->` ← nouveau
5. `<!-- Group by film toggle + advanced info -->`

- [ ] **Étape 2 : Commit HTML**

```bash
git add templates/index.html
git commit -m "feat: ajouter bloc HTML filtre genres"
```

---

### Task 3 : JS — Variables d'état genre

**Files:**
- Modify: `templates/index.html` (bloc `State` en JS, lignes ~804–812)

- [ ] **Étape 1 : Ajouter les variables genre dans le bloc State**

Localiser le commentaire `/* State */` et la liste de variables. Ajouter deux lignes après `let allFilms = [];` :

Remplacer :
```js
  let selectedFilms = new Set();
  let allFilms = [];
```
Par :
```js
  let selectedFilms = new Set();
  let allFilms = [];
  let selectedGenres = new Set();
  let allGenres = [];
```

- [ ] **Étape 2 : Commit state**

```bash
git add templates/index.html
git commit -m "feat: ajouter variables état selectedGenres/allGenres"
```

---

### Task 4 : JS — Filtrage genre dans `getFilteredSessions()`

**Files:**
- Modify: `templates/index.html` (fonction `getFilteredSessions`, lignes ~853–861)

- [ ] **Étape 1 : Ajouter la condition genre**

Remplacer la fonction entière :
```js
  function getFilteredSessions() {
    if (!DATA) return [];
    return DATA.sessions.filter(s => {
      if (!selectedCinemas.has(s.cinema)) return false;
      if (selectedFilms.size < allFilms.length && !selectedFilms.has(s.film)) return false;
      if (onlyAllAges && s.certificate !== 'Tout public' && s.certificate !== 'Tous publics') return false;
      return true;
    });
  }
```
Par :
```js
  function getFilteredSessions() {
    if (!DATA) return [];
    return DATA.sessions.filter(s => {
      if (!selectedCinemas.has(s.cinema)) return false;
      if (selectedFilms.size < allFilms.length && !selectedFilms.has(s.film)) return false;
      if (selectedGenres.size < allGenres.length) {
        const sGenres = s.genres || [];
        if (sGenres.length === 0) return false;
        if (!sGenres.some(g => selectedGenres.has(g))) return false;
      }
      if (onlyAllAges && s.certificate !== 'Tout public' && s.certificate !== 'Tous publics') return false;
      return true;
    });
  }
```

- [ ] **Étape 2 : Commit filtrage**

```bash
git add templates/index.html
git commit -m "feat: filtrage OR par genre dans getFilteredSessions"
```

---

### Task 5 : JS — Fonctions genre

**Files:**
- Modify: `templates/index.html` (après les fonctions film, avant `resetFilters`)

- [ ] **Étape 1 : Ajouter toutes les fonctions genre**

Après le bloc `document.getElementById('film-options').addEventListener(...)` (vers la fin du script, avant `document.addEventListener('click', ...)`), insérer :

```js

  function renderGenreOptions(genres) {
    const container = document.getElementById('genre-options');
    const allSelected = selectedGenres.size === allGenres.length;
    const allCls = 'fr-nav__link' + (allSelected ? ' fr-nav__link--active' : '');
    let html = `<li><button class="${allCls}" data-action="all-genres">Tous les genres</button></li>`;
    html += genres.map(g => {
      const isActive = !allSelected && selectedGenres.has(g);
      const cls = 'fr-nav__link' + (isActive ? ' fr-nav__link--active' : '');
      return `<li><button class="${cls}" data-genre="${escHtml(g)}">${escHtml(g)}</button></li>`;
    }).join('');
    container.innerHTML = html;
  }

  function updateGenreDropdownLabel() {
    const label = document.getElementById('genre-dropdown-label');
    if (selectedGenres.size === allGenres.length) {
      label.textContent = 'Tous les genres';
    } else if (selectedGenres.size === 1) {
      label.textContent = [...selectedGenres][0];
    } else {
      label.textContent = `${selectedGenres.size} genres sélectionnés`;
    }
  }

  function filterGenreList(query) {
    const q = query.trim().toLowerCase();
    const filtered = q ? allGenres.filter(g => g.toLowerCase().includes(q)) : allGenres;
    renderGenreOptions(filtered);
  }

  function toggleGenre(genre) {
    if (selectedGenres.size === allGenres.length) {
      selectedGenres = new Set([genre]);
    } else if (selectedGenres.has(genre)) {
      selectedGenres.delete(genre);
      if (selectedGenres.size === 0) selectedGenres = new Set(allGenres);
    } else {
      selectedGenres.add(genre);
    }
    renderGenreOptions(allGenres);
    updateGenreDropdownLabel();
    applyFilters();
  }

  function selectAllGenres() {
    selectedGenres = new Set(allGenres);
    renderGenreOptions(allGenres);
    updateGenreDropdownLabel();
    applyFilters();
  }

  function toggleGenreDropdown() {
    const btn = document.getElementById('genre-nav-btn');
    const panel = document.getElementById('genre-menu-panel');
    const expanded = btn.getAttribute('aria-expanded') === 'true';
    btn.setAttribute('aria-expanded', String(!expanded));
    panel.classList.toggle('fr-collapse--expanded', !expanded);
  }

  document.getElementById('genre-options').addEventListener('click', e => {
    const opt = e.target.closest('button[data-genre], button[data-action]');
    if (!opt) return;
    e.stopPropagation();
    if (opt.dataset.action === 'all-genres') selectAllGenres();
    else toggleGenre(opt.dataset.genre);
  });
```

- [ ] **Étape 2 : Commit fonctions**

```bash
git add templates/index.html
git commit -m "feat: fonctions JS filtre genre (render, toggle, dropdown)"
```

---

### Task 6 : JS — Init, reset et fermeture au clic extérieur

**Files:**
- Modify: `templates/index.html` (fonctions `init`, `resetFilters`, listener `document click`)

- [ ] **Étape 1 : Ajouter l'init genres dans `init()`**

Remplacer :
```js
    // Build film dropdown
    allFilms = [...new Set(DATA.sessions.map(s => s.film))].sort((a, b) => a.localeCompare(b, 'fr'));
    selectedFilms = new Set(allFilms);
    renderFilmOptions(allFilms);

    // Initial render
    applyFilters();
```
Par :
```js
    // Build film dropdown
    allFilms = [...new Set(DATA.sessions.map(s => s.film))].sort((a, b) => a.localeCompare(b, 'fr'));
    selectedFilms = new Set(allFilms);
    renderFilmOptions(allFilms);

    // Build genre dropdown
    allGenres = [...new Set(DATA.sessions.flatMap(s => s.genres || []))].sort((a, b) => a.localeCompare(b, 'fr'));
    selectedGenres = new Set(allGenres);
    renderGenreOptions(allGenres);

    // Initial render
    applyFilters();
```

- [ ] **Étape 2 : Ajouter `selectAllGenres()` dans `resetFilters()`**

Remplacer :
```js
  function resetFilters() {
    selectAllCinemas();
    selectAllFilms();
```
Par :
```js
  function resetFilters() {
    selectAllCinemas();
    selectAllFilms();
    selectAllGenres();
```

- [ ] **Étape 3 : Ajouter la fermeture du dropdown genre dans le listener clic extérieur**

Remplacer :
```js
  document.addEventListener('click', e => {
    const filmNav = document.getElementById('film-nav');
    if (filmNav && !filmNav.contains(e.target)) {
      document.getElementById('film-nav-btn').setAttribute('aria-expanded', 'false');
      document.getElementById('film-menu-panel').classList.remove('fr-collapse--expanded');
    }
    const cinemaNav = document.getElementById('cinema-nav');
    if (cinemaNav && !cinemaNav.contains(e.target)) {
      document.getElementById('cinema-nav-btn').setAttribute('aria-expanded', 'false');
      document.getElementById('cinema-menu-panel').classList.remove('fr-collapse--expanded');
    }
  });
```
Par :
```js
  document.addEventListener('click', e => {
    const filmNav = document.getElementById('film-nav');
    if (filmNav && !filmNav.contains(e.target)) {
      document.getElementById('film-nav-btn').setAttribute('aria-expanded', 'false');
      document.getElementById('film-menu-panel').classList.remove('fr-collapse--expanded');
    }
    const cinemaNav = document.getElementById('cinema-nav');
    if (cinemaNav && !cinemaNav.contains(e.target)) {
      document.getElementById('cinema-nav-btn').setAttribute('aria-expanded', 'false');
      document.getElementById('cinema-menu-panel').classList.remove('fr-collapse--expanded');
    }
    const genreNav = document.getElementById('genre-nav');
    if (genreNav && !genreNav.contains(e.target)) {
      document.getElementById('genre-nav-btn').setAttribute('aria-expanded', 'false');
      document.getElementById('genre-menu-panel').classList.remove('fr-collapse--expanded');
    }
  });
```

- [ ] **Étape 4 : Commit final**

```bash
git add templates/index.html
git commit -m "feat: init/reset/close filtre genres — filtre genres complet"
```

---

### Task 7 : Vérification manuelle

**Files:** aucun

- [ ] **Étape 1 : Lancer l'application**

```bash
python app.py
```
Ouvrir `http://localhost:5000` dans le navigateur.

- [ ] **Étape 2 : Vérifier l'affichage**

- [ ] Le nouveau bloc "Genres du film" apparaît dans la sidebar entre "Film à l'affiche" et "Options"
- [ ] Le dropdown s'ouvre et affiche la liste des genres (ex. "Action", "Comédie", "Drame"…)
- [ ] Le champ de recherche filtre la liste en temps réel
- [ ] Le label affiche "Tous les genres" par défaut

- [ ] **Étape 3 : Vérifier le filtrage**

- [ ] Sélectionner un seul genre (ex. "Comédie") → le label passe à "Comédie", seules les séances avec ce genre s'affichent
- [ ] Sélectionner un deuxième genre (ex. "Drame") → label "2 genres sélectionnés", séances avec Comédie OU Drame visibles
- [ ] Cliquer "Tous les genres" dans le dropdown → retour à l'état initial, toutes les séances affichées
- [ ] Cliquer "Réinitialiser les choix" → le filtre genre revient à "Tous les genres"

- [ ] **Étape 4 : Vérifier le mode clair**

Activer le mode clair (toggle en haut à droite) : le dropdown genre a le même style blanc que les deux autres dropdowns.

- [ ] **Étape 5 : Vérifier la fermeture au clic extérieur**

Ouvrir le dropdown genre, cliquer ailleurs sur la page → le panel se ferme.
