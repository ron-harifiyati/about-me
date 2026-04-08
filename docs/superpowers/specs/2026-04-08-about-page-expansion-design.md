# About Page Expansion — Design Spec

**Date:** 2026-04-08
**Status:** Approved

## Overview

Expand the About page with 4 new sections placed **after** the existing Journey timeline. The goal is to make the page more personal and complete — showing who Ron is beyond his professional bio.

## Page Layout (top to bottom)

1. Mission + Bio *(existing)*
2. Social Links *(existing)*
3. Journey Timeline *(existing, unchanged)*
4. **Languages I Speak** *(new)*
5. **Beyond Code** *(new)*
6. **Currently Learning** *(new — data exists, just not shown on About page)*
7. **How I Work** *(new)*

Each new section is separated by a horizontal divider (`.about-divider`), consistent with the existing Journey section.

## Sections Considered but Dropped

- **Fun Facts** — already works well as a random-one-at-a-time element on the home page. Showing all of them on About would kill the surprise/delight interaction.
- **What I'm Looking For / Goals** — Ron is currently in an internship at Jamf, so a "looking for work" section would send mixed signals. Can be added later.

## Data Layer

All items stored under `PK=CONTENT` in the existing DynamoDB single-table design.

### New DynamoDB Items

**`SK=LANGUAGES_SPOKEN`**
```json
{
  "languages": [
    { "name": "Ndebele", "level": "Native" },
    { "name": "Shona", "level": "Fluent" },
    { "name": "English", "level": "Fluent" },
    { "name": "German", "level": "Elementary" },
    { "name": "French", "level": "Elementary" }
  ]
}
```

**`SK=HOBBIES`**
```json
{
  "items": [
    { "icon": "🏃", "label": "Marathon Running" },
    { "icon": "🎮", "label": "Mobile & PC Gaming" },
    { "icon": "🎵", "label": "Music" },
    { "icon": "🎬", "label": "Movies" },
    { "icon": "📺", "label": "Anime & Cartoons" },
    { "icon": "📚", "label": "Comic Books" },
    { "icon": "📖", "label": "Reading & Docs" }
  ]
}
```

**`SK=VALUES`**
```json
{
  "values": [
    { "title": "Accountability", "description": "I own my work and follow through. If something breaks, I fix it." },
    { "title": "Simplicity", "description": "The best solution is the one that's easy to understand and maintain." },
    { "title": "Clear Communication", "description": "Say what you mean, document what matters, ask when unsure." },
    { "title": "Diverse Teams", "description": "The best ideas come from different perspectives working together." }
  ]
}
```

### Existing Item (no changes)

**`SK=CURRENTLY_LEARNING`** — `{ "items": ["AWS", "Cybersecurity", ...] }`

Already fetched by the home page. The About page will fetch the same endpoint.

## Backend

### New Routes

All added to `backend/routes/content.py` following the existing pattern exactly:

| Method | Path | Handler | Auth | DynamoDB Key |
|--------|------|---------|------|-------------|
| GET | `/languages` | `get_languages()` | Public | `LANGUAGES_SPOKEN` |
| PUT | `/languages` | `update_languages()` | `@require_admin` | `LANGUAGES_SPOKEN` |
| GET | `/hobbies` | `get_hobbies()` | Public | `HOBBIES` |
| PUT | `/hobbies` | `update_hobbies()` | `@require_admin` | `HOBBIES` |
| GET | `/values` | `get_values()` | Public | `VALUES` |
| PUT | `/values` | `update_values()` | `@require_admin` | `VALUES` |

Each handler is 2 lines — calls `get_content(SK)` or `update_content(SK, body)` and wraps in `ok()`. Identical to existing content routes.

### Router Registration

6 new entries in `backend/router.py` under the Content section:

```python
("GET",    "/languages",             content.get_languages),
("PUT",    "/languages",             content.update_languages),
("GET",    "/hobbies",               content.get_hobbies),
("PUT",    "/hobbies",               content.update_hobbies),
("GET",    "/values",                content.get_values),
("PUT",    "/values",                content.update_values),
```

### No Changes Needed

- `backend/models/content.py` — `get_content()` / `update_content()` are generic, work with any SK
- `backend/db.py` — no changes
- `backend/utils.py` — no changes

## Frontend

### JavaScript (`frontend/assets/js/pages/about.js`)

Expand the Alpine component to fetch 4 additional endpoints in parallel:

```javascript
function aboutPage() {
  return {
    about: null,
    timeline: [],
    languages: [],
    hobbies: [],
    learning: [],
    values: [],
    loading: true,

    async init() {
      const [aboutResp, timelineResp, langResp, hobbiesResp, learningResp, valuesResp] = await Promise.all([
        api.get("/about"),
        api.get("/timeline"),
        api.get("/languages"),
        api.get("/hobbies"),
        api.get("/currently-learning"),
        api.get("/values"),
      ]);
      this.about = aboutResp.data;
      this.timeline = timelineResp.data?.events || [];
      this.languages = langResp.data?.languages || [];
      this.hobbies = hobbiesResp.data?.items || [];
      this.learning = learningResp.data?.items || [];
      this.values = valuesResp.data?.values || [];
      this.loading = false;
      this.$nextTick(() => initScrollAnimations());
    },
  };
}
```

### HTML (`frontend/index.html`)

4 new template blocks added **after** the Journey timeline `</template>`, **before** the closing `</div>` of the about content area.

Each section follows the pattern:
```html
<template x-if="arrayName.length > 0">
  <div>
    <hr class="about-divider">
    <h2>Section Title</h2>
    <!-- section content -->
  </div>
</template>
```

#### Languages I Speak
Flex-wrap container of language badges. Each badge shows the language name and a color-coded proficiency level:
- Native → accent color
- Fluent → green
- Elementary → muted text color

#### Beyond Code
Responsive grid (`auto-fill, minmax(150px, 1fr)`) of small cards, each with an emoji icon and label.

#### Currently Learning
Flex-wrap badge list using the existing `.badge.badge-outline` classes. Same visual style as the hero skill badges.

#### How I Work
Responsive grid (`auto-fill, minmax(200px, 1fr)`) of cards, each with a title and one-line description.

### CSS (`frontend/assets/css/main.css`)

New classes added after the existing About/Timeline styles:

- `.about-lang-badge` — pill shape, `background: var(--bg-alt)`, `border: 1px solid var(--border)`, contains `.about-lang-level` span
- `.about-lang-level` — small uppercase text, color varies by level:
  - `.native` → `var(--accent)`
  - `.fluent` → a muted green that works on all backgrounds (`#66BB6A` on dark/terminal/nordic, `#388E3C` on light/coffee — use a single value that has sufficient contrast on both light and dark, e.g. `#4CAF50`)
  - `.elementary` → `var(--text-muted)`
- `.about-hobby-grid` — CSS grid, responsive auto-fill
- `.about-hobby-card` — flex row, icon + label, `background: var(--bg-alt)`, `border: 1px solid var(--border)`
- `.about-values-grid` — CSS grid, responsive auto-fill
- `.about-value-card` — card with padding, `background: var(--bg-alt)`, `border: 1px solid var(--border)`

All colors use CSS custom properties — works across all 5 themes (light, dark, coffee, terminal, nordic) with no theme-specific overrides needed.

### Mobile Responsiveness

- Language badges: flex-wrap handles narrow screens naturally
- Hobby grid: `minmax(150px, 1fr)` collapses to 2-col at 480px, 1-col if needed
- Values grid: `minmax(200px, 1fr)` collapses to 1-col at 480px
- No special media queries needed — CSS grid auto-fill handles it

## Admin Panel

### `frontend/admin.html`

3 new tabs added to the Content management section (alongside existing About, Skills, Timeline, Fun Facts, Currently Learning tabs):

- **Languages** — list editor: each row has `name` (text input) + `level` (dropdown: Native/Fluent/Elementary). Add/remove buttons.
- **Hobbies** — list editor: each row has `icon` (text input for emoji) + `label` (text input). Add/remove buttons.
- **Values** — list editor: each row has `title` (text input) + `description` (textarea). Add/remove buttons.

### `frontend/assets/js/admin-app.js`

- Fetch `/languages`, `/hobbies`, `/values` on init (add to existing `Promise.all`)
- Store in component state: `languages`, `hobbies`, `values`
- Save functions call `api.put("/languages", ...)`, `api.put("/hobbies", ...)`, `api.put("/values", ...)`
- Follow the exact same pattern as the existing Fun Facts and Currently Learning admin sections

## Testing

New tests in `backend/tests/` for the 6 new routes:

- `test_get_languages` — returns languages array
- `test_update_languages` — requires admin, stores data
- `test_get_hobbies` — returns items array
- `test_update_hobbies` — requires admin, stores data
- `test_get_values` — returns values array
- `test_update_values` — requires admin, stores data

All tests use `moto` mock DynamoDB via the existing `aws_env` fixture. Follow the pattern of existing content route tests.

## Seed Data

Initial data seeded to DynamoDB via AWS CLI with `AWS_PROFILE=portfolio-admin`:

- `LANGUAGES_SPOKEN` — 5 languages (Ndebele/Native, Shona/Fluent, English/Fluent, German/Elementary, French/Elementary)
- `HOBBIES` — 7 items (Marathon Running, Mobile & PC Gaming, Music, Movies, Anime & Cartoons, Comic Books, Reading & Docs)
- `VALUES` — 4 values (Accountability, Simplicity, Clear Communication, Diverse Teams)
