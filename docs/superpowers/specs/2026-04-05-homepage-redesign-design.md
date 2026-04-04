# Homepage Redesign — Design Spec

**Date:** 2026-04-05
**Branch:** `feature/ui-improvements`
**Status:** Approved

---

## Goal

Replace the current sparse homepage (hero + ticker + fun fact + 3 quick links) with a rich, personality-driven page that:

1. Immediately communicates who Ron is and what he builds
2. Funnels visitors toward Projects without requiring them to scroll
3. Shows enough breadth that a total stranger, a recruiter, and a developer peer all find something relevant

---

## Audience & Tone

- **Audience:** Recruiters, fellow developers, personal/professional network — treated equally
- **Tone:** Human warmth + clear technical identity. Not a resume, not a dev blog — a person who builds things

---

## Layout — Five Sections (top to bottom)

### ① Hero

Full-width, no sidebar. Contains:

- **Eyebrow label** — "Integration Engineer · Jamf" in accent color, small caps. Sets context before the name.
- **Name** — `Hi, I'm Ron Harifiyati` at ~2rem, bold
- **Bio** — 2 sentences max. Current: "I build systems that connect things — APIs, workflows, and teams. I care about clean interfaces, reliable backends, and code that's easy to hand off."
- **Skill badges** — Inline pill badges (Python, Swift, AWS, JavaScript, Linux, Docker) + "→ more" link to Skills page. Loaded statically (not from API — these don't change often).
- **CTA row** — `See my work` (btn-primary) + `Get in touch` (btn-outline), then a divider, then inline text links: GitHub · LinkedIn · Email. Social links pulled from the existing `/about` API response (`about.social_links`, `about.contact.email`).

**Mobile:** Skill badges wrap naturally. Social links stack below CTAs. Font size governed by CSS (no inline font-size overrides — fixes the current mobile bug where `style="font-size: 2.5rem"` ignores the responsive rule).

---

### ② Currently Learning Ticker

A single thin band immediately below the hero, separated by a border.

- Left: small uppercase label "Now learning" in muted color
- Right: the existing scrolling ticker (`currently-learning` API), inline with the label
- Pauses on hover (already implemented in CSS)
- Hidden if the API returns no items

This keeps the ticker visible but gives it a designated lane so it doesn't compete with the hero.

---

### ③ Featured Projects

A 3-column card grid (collapses to 1 column on mobile).

- Section heading "Featured Projects" + "All projects →" link (right-aligned)
- Each card: project name, 1-line description, tech tag badges
- Shows the first 3 projects returned by `/projects` (sorted by `featured` flag or creation date)
- Cards link to `#/projects/<id>`
- If fewer than 3 projects exist, grid adjusts with `auto-fill`

This replaces the current "quick links" cards (About me, Visitor map, API Docs) which don't serve portfolio visitors.

---

### ④ Testimonial + Stats

Two-column row (stacks on mobile, testimonial on top):

**Left — Testimonial pull quote:**
- One approved testimonial fetched from `/testimonials` (first result)
- Displayed with left border accent, italic body text, muted attribution
- "Read more testimonials →" link to `#/testimonials`
- Hidden entirely if no approved testimonials exist (API returns empty array or all pending)

**Right — Stats:**
- Three stat tiles (label + number): Visitors from X countries, Projects built, Courses completed
- Visitor country count from `/stats/visitors` (count unique `country` values)
- Project and course counts from `/projects` and `/courses` list lengths
- Numbers fetched in parallel with the rest of the page data

---

### ⑤ Fun Fact + Explore

Two-column row at the bottom of the page (stacks on mobile):

**Left — Fun Fact card:**
- Existing fun fact widget, verbatim
- "Another one →" button refreshes via `/fun-fact`

**Right — Explore grid:**
- 2×2 grid of quick-link buttons: Quiz, Guestbook, Visitor Map, API Docs
- Replaces the current 3 quick-link cards
- These are the "interesting for curious visitors" links, deliberately placed at the bottom so they don't compete with Projects

---

## Data Loading

All data loaded in `homePage.init()` via `Promise.all`:

```
/fun-fact
/currently-learning
/projects          → take first 3
/testimonials      → take first approved
/stats/visitors    → count unique countries
/courses           → count total
```

Social links come from `/about` (already fetched lazily if needed, or can be included in the parallel load).

Loading state: the hero renders immediately (static content). Each section below has its own loading state — spinner or skeleton — so slow API responses don't block the fold.

---

## Component Changes

### `frontend/index.html`

- Replace the entire `<!-- HOME -->` section with the new 5-section layout
- Hero `<h1>` uses a CSS class for font size (not inline `style="font-size: 2.5rem"`) so the responsive rule applies on mobile

### `frontend/assets/js/pages/home.js`

Extend `homePage()` to fetch and expose:
- `projects` — first 3 from `/projects`
- `testimonial` — first item from `/testimonials` (or null)
- `visitorCountries` — count of unique countries from `/stats/visitors`
- `projectCount` — length of `/projects` response
- `courseCount` — length of `/courses` response
- `socialLinks` — from `/about` (email, github, linkedin)

Keep existing: `funFact`, `ticker`, `loading`, `refreshFact()`

### `frontend/assets/css/main.css`

No structural changes needed. The existing `.card`, `.card-grid`, `.badge`, `.btn`, `.ticker-wrap` classes cover the new layout. Minor additions if needed for the stats tiles or testimonial left-border style.

---

## What's Removed

| Removed | Replaced by |
|---------|-------------|
| Fun fact as 3rd section | Moved to bottom (section ⑤) |
| Quick links: About me, Visitor map, API Docs | Featured Projects grid (③) + Explore grid (⑤) |
| Inline `font-size: 2.5rem` on hero h1 | CSS class |

---

## Out of Scope

- Avatar / profile photo (not available; would require image hosting decision)
- GitHub activity feed (requires GitHub API token)
- Animation redesign (covered separately in the ui-improvements branch)
- Admin/edit controls on the homepage
