# Portfolio Build Phases

Quick-reference breakdown of all 3 implementation plans.

**Execution order:** Plan 1 → Plan 2 → Plan 3
Plans 2 and 3 can run in parallel once Plan 1 is complete.

---

## Plan 1 — Infrastructure & CI/CD
**File:** `2026-04-02-portfolio-infra.md`
**Goal:** AWS resources live, CI/CD auto-deploys on push to `dev`/`prod`

| Task | What gets built |
|------|----------------|
| 1 — Repo structure | `version.txt`, hello-world `handler.py`, placeholder `index.html`, `dev` branch pushed |
| 2 — DynamoDB | `portfolio` table with GSI1/GSI2/GSI3 + TTL enabled |
| 3 — IAM | `portfolio-lambda-role` with DynamoDB, SES, CloudWatch permissions |
| 4 — Lambda | `portfolio-dev` + `portfolio-prod` functions with Function URLs |
| 5 — S3 | Two buckets (dev + prod), public access blocked |
| 6 — CloudFront | Two distributions with OAC, SPA 404→index.html fallback |
| 7 — SES | Sender email verified |
| 8 — GitHub Secrets | AWS keys, Lambda names, CF IDs, JWT secret, OAuth credentials |
| 9 — Backend CI | `deploy-backend.yml` — test → lint → package → deploy Lambda |
| 10 — Frontend CI | `deploy-frontend.yml` — sync S3 → invalidate CloudFront |
| 11 — Smoke test | Push to `dev`, both workflows green, Lambda URL + CF domain respond |

---

## Plan 2 — Backend API
**File:** `2026-04-02-portfolio-backend.md`
**Goal:** All 40+ API endpoints tested and deployed

| Branch | Tasks | What gets built |
|--------|-------|----------------|
| `feature/backend-foundation` | 1–4 | `conftest.py` (moto fixtures), `utils.py` (response helpers), `db.py` (DynamoDB singleton), `auth.py` (JWT + decorators), `handler.py`, `router.py` (full route dispatch table) |
| `feature/content-routes` | 5–7 | `/meta`, site content CRUD (admin), projects CRUD, courses CRUD, GitHub repos proxy |
| `feature/auth-routes` | 8–9 | User model (register/verify/login/OAuth account linking), email/password auth, GitHub + Google OAuth, JWT refresh rotation |
| `feature/interaction-routes` | 10–13 | Comments, ratings, guestbook, quiz (with leaderboard), testimonials (with approval flow) |
| `feature/stats-contact` | 14–15 | Visitor tracking + IP geolocation, analytics, contact form with rate limiting + SES email |
| `feature/admin-routes` | 16 | All `@require_admin` routes — user management, contact list, testimonial moderation, quiz CRUD |
| `feature/api-docs` | 17 | Swagger UI + full OpenAPI 3.0 spec |

---

## Plan 3 — Frontend SPA
**File:** `2026-04-02-portfolio-frontend.md`
**Goal:** Complete Alpine.js SPA deployed to S3/CloudFront

| Branch | Tasks | What gets built |
|--------|-------|----------------|
| `feature/frontend-foundation` | 1–5 | `theme.css` (5 themes + WCAG fixes), `main.css`, `api.js` (fetch wrapper), `themes.js`, `app.js` (hash router + auth state), `index.html` skeleton |
| `feature/public-pages` | 6–10 | Home (fun fact ticker), About (bio + timeline), Projects list + detail (comments + ratings), Courses list + detail, Skills |
| `feature/interactive-pages` | 11–14 | Stats (Leaflet visitor map, lazy loaded), Contact form, Guestbook, Testimonials |
| `feature/auth-flow` | 15–17 | Login (email + GitHub/Google OAuth), Register (identity picker), Verify email |
| `feature/authenticated-pages` | 18 | Quiz (start → play → result → leaderboard flow) |
| `feature/admin-panel` | 19–20 | `admin.html` sidebar dashboard (users, contacts, testimonials, quiz CRUD), Developer page |
| `feature/polish` | 21–24 | Favicon SVG, Open Graph meta tags, console Easter egg, scroll animations, Lighthouse audit + fixes |
