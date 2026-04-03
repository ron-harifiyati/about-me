# Frontend Runbook

## Overview

Alpine.js SPA served from S3/CloudFront. No build step required — plain HTML/CSS/JS.

**Entry points:**
- `frontend/index.html` — main SPA (all public + auth pages)
- `frontend/admin.html` — admin panel (separate page, guards on load)

**Deploy target:**
- Dev: S3 `portfolio-frontend-dev-993249606359` → CloudFront `d3sw9ggppgh9as.cloudfront.net`
- Prod: S3 `portfolio-frontend-prod-993249606359` → CloudFront `dkdwnfmhg75yf.cloudfront.net`

---

## Running Locally

```bash
cd frontend
python3 -m http.server 8080
# Open http://localhost:8080
```

No build step, no npm, no bundler.

---

## Architecture

### File Structure

```
frontend/
├── index.html                  # SPA entry point
├── admin.html                  # Admin panel
└── assets/
    ├── css/
    │   ├── theme.css           # 5 theme CSS custom properties
    │   └── main.css            # Global styles, layout, components
    ├── js/
    │   ├── api.js              # fetch() wrapper — base URL, JWT, error handling
    │   ├── themes.js           # Theme management (localStorage + server sync)
    │   ├── app.js              # Alpine.js app state, router, auth
    │   ├── admin-app.js        # Admin panel Alpine.js state
    │   └── pages/              # Per-page Alpine.js components
    └── images/
        └── favicon.svg
```

### Script Load Order

Scripts must load in this exact order (they're global):
1. `api.js` — defines `api`, `API_BASE`, `apiFetch`
2. `themes.js` — defines `applyTheme`, `loadTheme`, `cycleTheme`, `syncThemeToServer`
3. `app.js` — defines `portfolioApp()`, `initScrollAnimations()`
4. `pages/*.js` — define page component functions
5. Alpine.js (`defer`) — runs last, initializes components

---

## Routing

Hash-based: `#/page-name` or `#/collection/id`

| Hash | Page |
|------|------|
| `#/` or `#/home` | Home |
| `#/about` | About |
| `#/projects` | Projects list |
| `#/projects/:id` | Project detail |
| `#/courses` | Courses list |
| `#/courses/:id` | Course detail |
| `#/skills` | Skills |
| `#/stats` | Visitor map |
| `#/contact` | Contact form |
| `#/guestbook` | Guestbook |
| `#/testimonials` | Testimonials |
| `#/developer` | API docs / deploy info |
| `#/quiz` | Quiz (auth required) |
| `#/login` | Login |
| `#/register` | Register |
| `#/verify-email?token=xxx` | Email verification |

CloudFront is configured with a custom error rule to return `index.html` for all 404s, enabling direct URL access.

---

## Theme System

5 themes defined in `theme.css` via CSS custom properties on `:root` and `[data-theme="..."]`.

| Theme | Selector |
|-------|----------|
| Light (default) | `:root` (no attribute) |
| Dark | `[data-theme="dark"]` |
| Coffee | `[data-theme="coffee"]` |
| Terminal | `[data-theme="terminal"]` |
| Nordic | `[data-theme="nordic"]` |

**Theme persistence:**
- Guests: `localStorage["theme"]`
- Authenticated users: synced to server via `PUT /auth/me` → `{ theme }`

**WCAG AA fixes:** Dark, Coffee, Terminal, Nordic themes override `.btn-primary` text color for contrast compliance.

---

## API Client (`api.js`)

```javascript
// All requests go through:
api.get("/path")
api.post("/path", body)
api.put("/path", body)
api.delete("/path")

// Returns: { ok, status, data, error }
```

`API_BASE` auto-detects environment by hostname:
- `dkdwnfmhg75yf.cloudfront.net` → prod API Gateway (`o4o1xcb3wc`)
- anything else → dev API Gateway (`ly0fxfdai9`)

JWT token is read from `localStorage["access_token"]` and injected as `Authorization: Bearer <token>`.

---

## Auth Flow

1. **Register:** `POST /auth/register` → success message, check email
2. **Verify email:** link in email → `#/verify-email?token=xxx` → `POST /auth/verify-email`
3. **Login:** `POST /auth/login` → `{ access_token, refresh_token, user }`
4. **Session restore:** on app init, reads `access_token` from localStorage → `GET /auth/me`
5. **Logout:** `POST /auth/logout` → clears localStorage
6. **OAuth:** redirects to `${API_BASE}/auth/oauth/github` or `/auth/oauth/google`

Auth state lives in `portfolioApp()`:
- `user` — user object or `null`
- `isAuthenticated` — computed getter
- `isAdmin` — `user.role === "admin"`

---

## Admin Panel

`/admin.html` — separate page, checks `GET /auth/me` on load. Redirects to login if not admin.

Sections:
- **Dashboard** — stat counts (users, contacts, pending testimonials)
- **Content** — edit About bio/mission, Skills JSON, Fun Facts, Currently Learning
- **Users** — list all users, suspend/reinstate/delete
- **Contacts** — view all contact form submissions
- **Testimonials** — approve/reject pending submissions
- **Quiz** — add/edit/delete quiz questions

---

## Visitor Map (Stats page)

Uses Leaflet.js, loaded **lazily** when the stats page is visited (not in `<head>`). The `statsPage.loadLeaflet()` method injects the script and CSS tags dynamically.

Markers use `--accent` CSS variable color to match the current theme.

---

## Console Easter Egg

Open DevTools on the site → console shows:
- Styled greeting to developers
- Sample API fetch command
- Link to `#/developer` page

---

## Deployment

Dev pushes happen automatically on merge to `dev` branch via GitHub Actions.
Prod pushes happen automatically on merge to `prod` branch.

**Manual deploy to prod:**
```bash
git checkout prod
git merge dev
git push origin prod
```

**Invalidate CloudFront cache after deploy:**
```bash
# Dev
aws cloudfront create-invalidation --distribution-id E3GFM00HUAVU15 --paths "/*"
# Prod
aws cloudfront create-invalidation --distribution-id E1P7C158XTW7UF --paths "/*"
```
