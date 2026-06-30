# Google Agenda Button — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ajouter un bouton `📅` par séance qui ouvre Google Agenda avec l'événement pré-rempli (titre, heure début/fin, localisation = nom du cinéma).

**Architecture:** Modification 100% côté client dans `templates/index.html`. Deux nouvelles fonctions JS (`calendarUrl`, `calBtn`), un style CSS `.cal-btn`, et des modifications des fonctions de rendu existantes. Aucun changement backend.

**Tech Stack:** JavaScript vanilla, HTML/CSS dans le template Jinja2 existant.

---

## Fichiers modifiés

- Modify: `templates/index.html` — seul fichier touché

---

### Task 1 : CSS + fonctions `calendarUrl` et `calBtn`

**Files:**
- Modify: `templates/index.html`

- [ ] **Step 1 : Ajouter le style `.cal-btn` dans le bloc `<style>`**

Chercher la règle `.temp-badge` (ligne ~218). Juste après son bloc de fermeture `}`, ajouter :

```css
    /* ── Calendar button ── */
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

- [ ] **Step 2 : Ajouter `calendarUrl` et `calBtn` après le bloc Group-by-film helpers**

Chercher la fin des fonctions `buildGroupedRowCinema` (le dernier `}` du bloc Group-by-film helpers, vers la ligne 640). Juste après, ajouter :

```js
  /* ────────────────────────────────────────────
     Google Agenda helpers
  ──────────────────────────────────────────── */
  function calendarUrl(s) {
    function parseDuration(dur) {
      if (!dur) return 120;
      const h = dur.match(/(\d+)\s*h/i);
      const m = dur.match(/(\d+)\s*min/i) || dur.match(/h\s*(\d+)$/);
      const hours = h ? parseInt(h[1], 10) : 0;
      const mins  = m ? parseInt(m[1], 10) : 0;
      const total = hours * 60 + mins;
      return total > 0 ? total : 120;
    }

    function toGCalStamp(dateStr, heureStr) {
      return dateStr.replace(/-/g, '') + 'T' + heureStr.replace(':', '') + '00';
    }

    function addMinutes(dateStr, heureStr, minutes) {
      const [h, m] = heureStr.split(':').map(Number);
      const totalMin = h * 60 + m + minutes;
      const newH    = Math.floor(totalMin / 60) % 24;
      const newM    = totalMin % 60;
      const dayOver = Math.floor(totalMin / 1440);
      let endDate   = dateStr;
      if (dayOver > 0) {
        const d = new Date(dateStr + 'T12:00:00');
        d.setDate(d.getDate() + dayOver);
        endDate = d.toISOString().slice(0, 10);
      }
      return endDate.replace(/-/g, '') + 'T' + String(newH).padStart(2,'0') + String(newM).padStart(2,'0') + '00';
    }

    const durationMin = parseDuration(s.duration);
    const start  = toGCalStamp(s.date, s.heure);
    const end    = addMinutes(s.date, s.heure, durationMin);
    const title  = s.film + (s.version ? ' (' + s.version + ')' : '');
    const detail = s.film + (s.version ? ' - ' + s.version : '');

    return 'https://calendar.google.com/calendar/render?action=TEMPLATE'
      + '&text='     + encodeURIComponent(title)
      + '&dates='    + encodeURIComponent(start + '/' + end)
      + '&location=' + encodeURIComponent(s.cinema)
      + '&details='  + encodeURIComponent(detail);
  }

  function calBtn(s) {
    return `<a href="${escHtml(calendarUrl(s))}" target="_blank" rel="noopener" class="cal-btn" title="Ajouter à Google Agenda">📅</a>`;
  }
```

- [ ] **Step 3 : Vérifier dans la console navigateur**

Ouvrir les DevTools (F12 → Console) et tester :

```js
// Doit retourner une URL Google Agenda valide
calendarUrl({date:'2026-06-30', heure:'14:00', duration:'2h35', film:'Dune 2', version:'VF', cinema:'Pathé Bellecour'})
// Attendu: "https://calendar.google.com/calendar/render?action=TEMPLATE&text=Dune%202%20(VF)&dates=20260630T140000%2F20260630T163500&location=Path%C3%A9%20Bellecour&details=Dune%202%20-%20VF"

// Vérifier le fallback durée vide (+2h)
calendarUrl({date:'2026-06-30', heure:'22:30', duration:'', film:'Test', version:'VO', cinema:'Le Zola'})
// Attendu: dates=20260630T223000%2F20260701T003000 (passage à minuit : +1 jour)
```

- [ ] **Step 4 : Commit**

```bash
git add templates/index.html
git commit -m "feat: add calendarUrl and calBtn helpers with CSS"
```

---

### Task 2 : Bouton en mode non-groupé — `buildRowJour`, `buildRowCinema`, `theadHtml`

**Files:**
- Modify: `templates/index.html`

- [ ] **Step 1 : Modifier `buildRowJour` (ligne ~559)**

Remplacer :

```js
  // Vue A row: Cinema | Heure | Durée | Film | Temp
  function buildRowJour(s) {
    const cls = rowClass(s.temperature);
    return `<tr class="${cls}">
      <td>${escHtml(s.cinema)}</td>
      <td>${escHtml(s.heure)}</td>
      <td>${durationCell(s)}</td>
      <td>${filmCell(s)}</td>
      <td>${tempBadge(s.temperature)}</td>
    </tr>`;
  }
```

Par :

```js
  // Vue A row: Cinema | Heure | Durée | Film | Temp | 📅
  function buildRowJour(s) {
    const cls = rowClass(s.temperature);
    return `<tr class="${cls}">
      <td>${escHtml(s.cinema)}</td>
      <td>${escHtml(s.heure)}</td>
      <td>${durationCell(s)}</td>
      <td>${filmCell(s)}</td>
      <td>${tempBadge(s.temperature)}</td>
      <td>${calBtn(s)}</td>
    </tr>`;
  }
```

- [ ] **Step 2 : Modifier `buildRowCinema` (ligne ~571)**

Remplacer :

```js
  // Vue B row: Date | Heure | Durée | Film | Temp
  function buildRowCinema(s) {
    const cls = rowClass(s.temperature);
    const dateStr = new Date(s.date + 'T12:00:00').toLocaleDateString('fr-FR', {weekday:'short', day:'numeric', month:'short'});
    return `<tr class="${cls}">
      <td>${dateStr}</td>
      <td>${escHtml(s.heure)}</td>
      <td>${durationCell(s)}</td>
      <td>${filmCell(s)}</td>
      <td>${tempBadge(s.temperature)}</td>
    </tr>`;
  }
```

Par :

```js
  // Vue B row: Date | Heure | Durée | Film | Temp | 📅
  function buildRowCinema(s) {
    const cls = rowClass(s.temperature);
    const dateStr = new Date(s.date + 'T12:00:00').toLocaleDateString('fr-FR', {weekday:'short', day:'numeric', month:'short'});
    return `<tr class="${cls}">
      <td>${dateStr}</td>
      <td>${escHtml(s.heure)}</td>
      <td>${durationCell(s)}</td>
      <td>${filmCell(s)}</td>
      <td>${tempBadge(s.temperature)}</td>
      <td>${calBtn(s)}</td>
    </tr>`;
  }
```

- [ ] **Step 3 : Ajouter `<th></th>` dans les `theadHtml` non-groupés**

Dans `renderViewJour` (ligne ~739), remplacer la ligne non-groupée :

```js
      theadHtml = '<tr><th>Cinéma</th><th>Heure</th><th>Durée</th><th>Film</th><th>🌡️</th></tr>';
```

Par :

```js
      theadHtml = '<tr><th>Cinéma</th><th>Heure</th><th>Durée</th><th>Film</th><th>🌡️</th><th></th></tr>';
```

Dans `renderViewCinema` (ligne ~789), remplacer la ligne non-groupée :

```js
        theadHtml = '<tr><th>Date</th><th>Heure</th><th>Durée</th><th>Film</th><th>🌡️</th></tr>';
```

Par :

```js
        theadHtml = '<tr><th>Date</th><th>Heure</th><th>Durée</th><th>Film</th><th>🌡️</th><th></th></tr>';
```

- [ ] **Step 4 : Vérifier dans le navigateur — mode non-groupé**

Décocher "Regrouper par film". Dans les deux vues (Par jour et Par cinéma) :
- Chaque ligne affiche un bouton `📅` en dernière colonne
- Cliquer sur un bouton ouvre Google Agenda dans un nouvel onglet avec les champs pré-remplis
- La colonne est alignée (pas de décalage de header)

- [ ] **Step 5 : Commit**

```bash
git add templates/index.html
git commit -m "feat: add calendar button to non-grouped rows"
```

---

### Task 3 : Bouton en mode groupé — `sessionBadge`

**Files:**
- Modify: `templates/index.html`

- [ ] **Step 1 : Modifier `sessionBadge` (ligne ~597)**

Remplacer :

```js
  function sessionBadge(s) {
    const time = escHtml(s.heure);
    if (s.temperature === null || s.temperature === undefined) {
      return `<span style="white-space:nowrap;font-size:0.82rem;color:#aaa">${time}</span>`;
    }
    const color = tempColor(s.temperature);
    return `<span style="white-space:nowrap;font-size:0.82rem;">${time}&nbsp;<span class="temp-badge" style="background:${color}">${s.temperature.toFixed(1)}&nbsp;°C</span></span>`;
  }
```

Par :

```js
  function sessionBadge(s) {
    const time = escHtml(s.heure);
    let badge;
    if (s.temperature === null || s.temperature === undefined) {
      badge = `<span style="white-space:nowrap;font-size:0.82rem;color:#aaa">${time}</span>`;
    } else {
      const color = tempColor(s.temperature);
      badge = `<span style="white-space:nowrap;font-size:0.82rem;">${time}&nbsp;<span class="temp-badge" style="background:${color}">${s.temperature.toFixed(1)}&nbsp;°C</span></span>`;
    }
    return `<span style="white-space:nowrap;display:inline-flex;align-items:center;gap:3px;">${badge}${calBtn(s)}</span>`;
  }
```

- [ ] **Step 2 : Vérifier dans le navigateur — mode groupé**

Cocher "Regrouper par film". Dans les deux vues :
- Chaque badge dans la cellule Séances est suivi de son bouton `📅`
- Badge et bouton restent solidaires lors du retour à la ligne (flex-wrap)
- Cliquer sur un `📅` ouvre Google Agenda avec la bonne heure de cette séance spécifique

- [ ] **Step 3 : Vérifier les transitions**

- Basculer "Regrouper par film" coché/décoché : boutons présents dans les deux modes
- Switcher entre Vue Par jour et Vue Par cinéma : boutons présents dans les deux vues
- Pas d'erreur console

- [ ] **Step 4 : Commit final**

```bash
git add templates/index.html
git commit -m "feat: add calendar button to grouped session badges — Google Agenda complet"
```
