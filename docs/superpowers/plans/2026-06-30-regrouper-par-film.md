# Regrouper par film — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ajouter un toggle "Regrouper par film" (coché par défaut) qui fusionne les séances du même film (par cinema × film × version pour Vue A, et film × date × version pour Vue B) en une seule ligne avec une cellule "Séances" listant les badges heure+température.

**Architecture:** Modification 100% côté client dans `templates/index.html`. Ajout de helpers JS, branchement dans `renderViewJour` et `renderViewCinema`. Aucun changement backend ni modèle de données.

**Tech Stack:** JavaScript vanilla, HTML/CSS dans le template Jinja2 existant.

---

## Fichiers modifiés

- Modify: `templates/index.html` — seul fichier touché

---

### Task 1 : État + toggle sidebar

**Files:**
- Modify: `templates/index.html`

- [ ] **Step 1 : Ajouter la variable d'état `groupByFilm`**

Dans le bloc State (ligne ~372), après `let selectedDay = null;`, ajouter :

```js
let groupByFilm = true;
```

Résultat attendu dans le bloc State :
```js
let currentView = 'jour';
let selectedCinemas = new Set();
let allCinemas = [];
let selectedDay = null;  // null = auto-select first available day
let groupByFilm = true;
```

- [ ] **Step 2 : Ajouter le toggle dans la sidebar**

Dans la sidebar HTML (ligne ~350), après le bloc `filter-group` du champ Film (qui se termine par `</div>` après l'`<input id="film-search">`), ajouter un nouveau `filter-group` :

```html
    <!-- Group by film toggle -->
    <div class="filter-group">
      <h2>Options</h2>
      <label style="display:flex;align-items:center;gap:.45rem;font-size:0.82rem;color:var(--text);cursor:pointer;">
        <input type="checkbox" id="group-by-film" checked
               onchange="groupByFilm=this.checked;applyFilters()"
               style="accent-color:var(--accent);width:14px;height:14px;flex-shrink:0;">
        Regrouper par film
      </label>
    </div>
```

- [ ] **Step 3 : Vérifier visuellement dans le navigateur**

Ouvrir `http://localhost:5000`. La checkbox "Regrouper par film" doit apparaître dans la sidebar sous le champ Film, cochée par défaut. La décocher ne doit (pour l'instant) rien changer au tableau — c'est normal, les fonctions de rendu ne branchent pas encore sur `groupByFilm`.

- [ ] **Step 4 : Commit**

```bash
git add templates/index.html
git commit -m "feat: add groupByFilm state and sidebar toggle"
```

---

### Task 2 : Fonctions helper de groupement

**Files:**
- Modify: `templates/index.html`

- [ ] **Step 1 : Ajouter les helpers après `escHtml`**

Après la fonction `escHtml` (ligne ~571), ajouter les quatre fonctions suivantes dans l'ordre :

```js
  /* ────────────────────────────────────────────
     Group-by-film helpers
  ──────────────────────────────────────────── */
  function maxTemp(sessions) {
    const temps = sessions.map(s => s.temperature).filter(t => t !== null && t !== undefined);
    return temps.length ? Math.max(...temps) : null;
  }

  function sessionBadge(s) {
    const time = escHtml(s.heure);
    if (s.temperature === null || s.temperature === undefined) {
      return `<span style="white-space:nowrap;font-size:0.82rem;color:#aaa">${time}</span>`;
    }
    const color = tempColor(s.temperature);
    return `<span style="white-space:nowrap;font-size:0.82rem;">${time}&nbsp;<span class="temp-badge" style="background:${color}">${s.temperature.toFixed(1)}&nbsp;°C</span></span>`;
  }

  function seancesCell(sessions) {
    const sorted = sessions.slice().sort((a, b) => a.heure.localeCompare(b.heure));
    return `<div style="display:flex;flex-wrap:wrap;gap:6px 10px;">${sorted.map(sessionBadge).join('')}</div>`;
  }

  function buildGroupedRowJour(group) {
    const t = maxTemp(group.sessions);
    const cls = rowClass(t);
    const rep = group.sessions[0];
    return `<tr class="${cls}">
      <td>${escHtml(group.cinema)}</td>
      <td>${filmCell(rep)}</td>
      <td>${durationCell(rep)}</td>
      <td>${seancesCell(group.sessions)}</td>
    </tr>`;
  }

  function buildGroupedRowCinema(group) {
    const t = maxTemp(group.sessions);
    const cls = rowClass(t);
    const rep = group.sessions[0];
    const dateStr = new Date(group.date + 'T12:00:00').toLocaleDateString('fr-FR', {weekday:'short', day:'numeric', month:'short'});
    return `<tr class="${cls}">
      <td>${dateStr}</td>
      <td>${filmCell(rep)}</td>
      <td>${durationCell(rep)}</td>
      <td>${seancesCell(group.sessions)}</td>
    </tr>`;
  }
```

- [ ] **Step 2 : Vérifier dans la console navigateur**

Ouvrir les DevTools (F12 → Console) et tester manuellement :

```js
// Doit retourner null
maxTemp([{temperature: null}, {temperature: undefined}])

// Doit retourner 37
maxTemp([{temperature: 34}, {temperature: 37}, {temperature: 29}])

// Doit afficher un badge coloré
sessionBadge({heure: '14:00', temperature: 36.2})

// Doit afficher l'heure sans badge
sessionBadge({heure: '14:00', temperature: null})
```

Pas d'erreurs attendues dans la console.

- [ ] **Step 3 : Commit**

```bash
git add templates/index.html
git commit -m "feat: add grouping helper functions (maxTemp, sessionBadge, seancesCell, buildGroupedRow*)"
```

---

### Task 3 : Brancher Vue Par jour

**Files:**
- Modify: `templates/index.html` — fonction `renderViewJour` (ligne ~628)

- [ ] **Step 1 : Remplacer le bloc de construction des lignes et des en-têtes dans `renderViewJour`**

Localiser ce bloc (lignes ~662-679) :

```js
    // Show only selected day's sessions
    const daySessions = (groups[selectedDay] || []).slice().sort(
      (a, b) => a.cinema.localeCompare(b.cinema) || a.heure.localeCompare(b.heure)
    );
    const rowsHtml = daySessions.map(buildRowJour).join('');

    const d = new Date(selectedDay + 'T12:00:00');
    const fullLabel = d.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });
    const capitalized = fullLabel.charAt(0).toUpperCase() + fullLabel.slice(1);

    return `<div id="day-nav">${navHtml}</div>
      <div class="group">
        <div class="group-header">${capitalized}</div>
        <table>
          <thead><tr>
            <th>Cinéma</th><th>Heure</th><th>Durée</th><th>Film</th><th>🌡️</th>
          </tr></thead>
          <tbody>${rowsHtml}</tbody>
        </table>
      </div>`;
```

Le remplacer par :

```js
    // Show only selected day's sessions
    const rawDay = (groups[selectedDay] || []);
    let rowsHtml, theadHtml;

    if (groupByFilm) {
      const grouped = new Map();
      rawDay.forEach(s => {
        const key = `${s.cinema}|||${s.film}|||${s.version}`;
        if (!grouped.has(key)) grouped.set(key, { cinema: s.cinema, film: s.film, version: s.version, sessions: [] });
        grouped.get(key).sessions.push(s);
      });
      const groupList = [...grouped.values()].sort((a, b) =>
        a.cinema.localeCompare(b.cinema) || a.film.localeCompare(b.film) || a.version.localeCompare(b.version)
      );
      rowsHtml  = groupList.map(buildGroupedRowJour).join('');
      theadHtml = '<tr><th>Cinéma</th><th>Film</th><th>Durée</th><th>Séances</th></tr>';
    } else {
      const sorted = rawDay.slice().sort((a, b) => a.cinema.localeCompare(b.cinema) || a.heure.localeCompare(b.heure));
      rowsHtml  = sorted.map(buildRowJour).join('');
      theadHtml = '<tr><th>Cinéma</th><th>Heure</th><th>Durée</th><th>Film</th><th>🌡️</th></tr>';
    }

    const d = new Date(selectedDay + 'T12:00:00');
    const fullLabel = d.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });
    const capitalized = fullLabel.charAt(0).toUpperCase() + fullLabel.slice(1);

    return `<div id="day-nav">${navHtml}</div>
      <div class="group">
        <div class="group-header">${capitalized}</div>
        <table>
          <thead>${theadHtml}</thead>
          <tbody>${rowsHtml}</tbody>
        </table>
      </div>`;
```

- [ ] **Step 2 : Vérifier dans le navigateur — groupement activé (Vue Par jour)**

- La Vue "Par jour" doit afficher `Cinéma | Film | Durée | Séances`
- Chaque film apparaît une seule fois par cinéma pour le jour sélectionné
- La cellule Séances liste les heures avec leurs badges température colorés
- La couleur de fond de la ligne reflète la température la plus haute du groupe

- [ ] **Step 3 : Vérifier dans le navigateur — groupement désactivé (Vue Par jour)**

Décocher "Regrouper par film" :
- Les colonnes reviennent à `Cinéma | Heure | Durée | Film | 🌡️`
- Chaque séance est sur sa propre ligne, comportement identique à avant

- [ ] **Step 4 : Commit**

```bash
git add templates/index.html
git commit -m "feat: branch renderViewJour on groupByFilm"
```

---

### Task 4 : Brancher Vue Par cinéma

**Files:**
- Modify: `templates/index.html` — fonction `renderViewCinema` (ligne ~686)

- [ ] **Step 1 : Remplacer le corps de `renderViewCinema`**

Localiser ce bloc (lignes ~696-711) :

```js
    return cinemas.map(cinema => {
      const rows = groups[cinema].slice().sort((a,b) => {
        const d = a.date.localeCompare(b.date);
        return d !== 0 ? d : a.heure.localeCompare(b.heure);
      });
      const rowsHtml = rows.map(buildRowCinema).join('');
      return `<div class="group">
        <div class="group-header">${escHtml(cinema)}</div>
        <table>
          <thead><tr>
            <th>Date</th><th>Heure</th><th>Durée</th><th>Film</th><th>🌡️</th>
          </tr></thead>
          <tbody>${rowsHtml}</tbody>
        </table>
      </div>`;
    }).join('');
```

Le remplacer par :

```js
    return cinemas.map(cinema => {
      let rowsHtml, theadHtml;
      if (groupByFilm) {
        const grouped = new Map();
        groups[cinema].forEach(s => {
          const key = `${s.film}|||${s.date}|||${s.version}`;
          if (!grouped.has(key)) grouped.set(key, { film: s.film, date: s.date, version: s.version, sessions: [] });
          grouped.get(key).sessions.push(s);
        });
        const groupList = [...grouped.values()].sort((a, b) =>
          a.date.localeCompare(b.date) || a.film.localeCompare(b.film) || a.version.localeCompare(b.version)
        );
        rowsHtml  = groupList.map(buildGroupedRowCinema).join('');
        theadHtml = '<tr><th>Date</th><th>Film</th><th>Durée</th><th>Séances</th></tr>';
      } else {
        const sorted = groups[cinema].slice().sort((a, b) => {
          const d = a.date.localeCompare(b.date);
          return d !== 0 ? d : a.heure.localeCompare(b.heure);
        });
        rowsHtml  = sorted.map(buildRowCinema).join('');
        theadHtml = '<tr><th>Date</th><th>Heure</th><th>Durée</th><th>Film</th><th>🌡️</th></tr>';
      }
      return `<div class="group">
        <div class="group-header">${escHtml(cinema)}</div>
        <table>
          <thead>${theadHtml}</thead>
          <tbody>${rowsHtml}</tbody>
        </table>
      </div>`;
    }).join('');
```

- [ ] **Step 2 : Vérifier dans le navigateur — groupement activé (Vue Par cinéma)**

Passer sur la Vue "Par cinéma" :
- Les colonnes affichent `Date | Film | Durée | Séances`
- Chaque film apparaît une seule fois par (date × version) dans chaque section cinéma
- La cellule Séances liste les heures avec leurs badges température
- VF et VO sont sur des lignes séparées si le film est diffusé dans les deux versions

- [ ] **Step 3 : Vérifier dans le navigateur — groupement désactivé (Vue Par cinéma)**

Décocher "Regrouper par film" :
- Les colonnes reviennent à `Date | Heure | Durée | Film | 🌡️`
- Comportement identique à avant

- [ ] **Step 4 : Vérifier les transitions de vue**

- Basculer entre Par jour et Par cinéma avec le toggle coché et décoché : pas d'erreur console, re-render correct à chaque fois
- Filtrer par cinéma avec le toggle actif : les cinémas décochés disparaissent normalement
- Rechercher un film avec le toggle actif : seules les lignes correspondantes s'affichent

- [ ] **Step 5 : Commit final**

```bash
git add templates/index.html
git commit -m "feat: branch renderViewCinema on groupByFilm — regrouper par film complet"
```
