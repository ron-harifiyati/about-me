# Portfolio Site — Design Specification
**Date:** 2026-04-02
**Author:** Ron Harifiyati
**Status:** Approved

---

## Overview

A live, interactive, API-first personal portfolio website running on AWS. The backend is a standalone Python API (usable via Postman/curl or browser), the frontend is an Alpine.js SPA served from S3/CloudFront. Anyone can browse the site as a guest; visitors can create accounts and unlock interactive features; the site owner has full admin control.

---

## Section 1 — Architecture

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                                   BROWSER                                      │
│  Alpine.js frontend (HTML/CSS/JS) — fetches all data from Lambda via fetch()   │
└────────────────────┬───────────────────────────────────┬───────────────────────┘
                     │ static assets                      │ API calls (JSON)
                     ▼                                    ▼
        ┌────────────────────────┐       ┌────────────────────────────────────┐
        │   CloudFront CDN       │       │   Lambda Function URL              │
        │   + S3 Bucket          │       │   (Python 3.12, single handler)    │
        │                        │       │                                    │
        │   index.html           │       │   routes:                          │
        │   admin.html           │       │   /meta  /about  /projects         │
        │   CSS, JS, assets      │       │   /courses  /skills  /timeline     │
        └────────────────────────┘       │   /fun-fact  /currently-learning   │
                                         │   /contact  /guestbook  /stats/*   │
                                         │   /testimonials  /github/repos     │
                                         │   /auth/*  /quiz/*                 │
                                         │   /comments/*  /ratings/*          │
                                         │   /admin/*  /api  /api/spec        │
                                         └────────────────┬───────────────────┘
                                                          │
                              ┌───────────────────────────┼───────────────────────┐
                              │                           │                       │
                              ▼                           ▼                       ▼
                   ┌──────────────────┐        ┌──────────────┐       ┌──────────────────┐
                   │   DynamoDB       │        │   AWS SES    │       │   ip-api.com     │
                   │  (single table)  │        │   (email)    │       │  (geolocation)   │
                   └──────────────────┘        └──────────────┘       └──────────────────┘
```

**Key decisions:**
- Single Lambda with Python path-based router — one deployment unit, simple to reason about
- S3 + CloudFront for frontend — CDN-cached, globally fast, enables Lighthouse 90+ score
- CORS headers returned by Lambda for all API responses
- Frontend and API are fully decoupled — API works standalone via Postman/curl
- No custom domain initially — CloudFront provides HTTPS on `*.cloudfront.net`

**Repository structure:**
```
about-me/
├── frontend/                        # Static files → S3
│   ├── index.html
│   ├── admin.html
│   └── assets/
├── backend/                         # Python Lambda
│   ├── handler.py                   # Entry point + router
│   ├── routes/                      # One file per route group
│   ├── models/                      # DynamoDB access patterns
│   └── requirements.txt
├── .github/
│   └── workflows/
│       ├── deploy-frontend.yml      # Triggers on frontend/** changes
│       └── deploy-backend.yml       # Triggers on backend/** changes
├── docs/
│   └── superpowers/specs/
└── version.txt                      # Bumped manually on release
```

---

## Section 2 — Features

### Guest (no account)
- View all public content: bio, projects, courses, skills, timeline, mission statement
- Currently learning ticker
- Fun fact widget (hits `/fun-fact` API)
- Visitor map (public — shows visit locations worldwide)
- Leave a guestbook entry (name required, displays as `name (guest)`)
- Submit contact form (rate limited: 5/hr per IP, friendly message when blocked)
- View testimonials (filterable by identity: Jamf · MCRI · Friend · Family · Other)
- View project and course ratings (read-only)
- View GitHub feed (latest public repos)
- Browse `/api` Swagger documentation

### Authenticated User
- Everything guests can do, plus:
- Personalised greeting by name on return visits
- Identity badge on all contributions (Jamf / MCRI / Friend / Family / Other)
- Rate projects and courses (1–5 stars)
- Comment on individual projects and courses
- Take the quiz (20 questions, scored and saved, leaderboard)
- Submit a testimonial (anonymous or named — pending admin approval)
- Change identity tag after registration
- Account linking: GitHub, Google, and email/password merge under one account by email

### Admin (site owner)
- Everything above, plus `/admin` protected route with:
  - Edit all content fields individually (bio, projects, courses, fun facts, skills, currently learning, contact details)
  - View and manage contact form submissions
  - Approve or reject testimonials
  - Delete inappropriate comments
  - Suspend or ban users
  - Full analytics: visit counts, identity breakdown, per-page views, visitor map with location data
  - Manage quiz questions (add, edit, delete)

### Identity System
- Categories: **Jamf · MCRI · Friend · Family · Other**
- One identity per account, changeable after registration
- Display + personal analytics only (no access gating)
- Personalised welcome: `"Welcome back, [name]"` (no identity in greeting text)
- Identity badge shown on comments, ratings, testimonials, guestbook entries
- Identity-filtered testimonials view
- Connections count per identity category
- Admin sees identity breakdown in analytics

### Auth System
- Email registration → SES verification email → account active on confirm
- GitHub OAuth (primary), Google OAuth (secondary)
- Custom JWT: 24hr default, 7-day with "remember me" checkbox
- Same email across providers → accounts merge automatically
- Secrets stored in Lambda environment variables

### Visitor Map
- Public to all visitors
- Lambda calls `ip-api.com` on each visit to get `lat/lon/country/city`
- Stored in DynamoDB visit records
- `GET /stats/visitors` returns location data for map rendering
- Admin sees identity overlay, per-page data, and time of visit

---

## Section 3 — API Design

All responses use a consistent envelope:
```json
{ "data": { ... }, "error": null }
{ "data": null, "error": "message here" }
```

### Meta & Docs
| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| GET | `/meta` | None | Version, deploy timestamp, commit SHA, environment, region, author, repository |
| GET | `/api` | None | Interactive Swagger UI (HTML) |
| GET | `/api/spec` | None | Raw OpenAPI 3.0 JSON spec |

### Content (public reads, admin writes)
| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| GET | `/about` | None | Bio, mission statement, contact details, social links |
| GET | `/skills` | None | Skills list by category |
| GET | `/timeline` | None | Journey timeline |
| GET | `/fun-fact` | None | Random fun fact |
| GET | `/currently-learning` | None | Currently learning ticker items |
| GET | `/projects` | None | All projects |
| GET | `/projects/{id}` | None | Single project |
| POST | `/projects` | Admin | Create project |
| PUT | `/projects/{id}` | Admin | Update individual fields |
| DELETE | `/projects/{id}` | Admin | Delete project |
| GET | `/courses` | None | All courses |
| GET | `/courses/{id}` | None | Single course |
| POST | `/courses` | Admin | Create course |
| PUT | `/courses/{id}` | Admin | Update individual fields |
| DELETE | `/courses/{id}` | Admin | Delete course |
| GET | `/github/repos` | None | Latest public GitHub repos |

### Auth
| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| POST | `/auth/register` | None | Email + password registration, triggers SES verification |
| POST | `/auth/verify-email` | None | Confirm email with token |
| POST | `/auth/login` | None | Email + password login, returns JWT |
| POST | `/auth/logout` | User | Invalidate session |
| POST | `/auth/refresh` | User | Exchange refresh token for new JWT |
| GET | `/auth/me` | User | Current user profile |
| PUT | `/auth/me` | User | Update profile (identity tag, display name, theme preference) |
| GET | `/auth/oauth/github` | None | Initiate GitHub OAuth flow |
| GET | `/auth/oauth/github/callback` | None | GitHub OAuth callback, returns JWT |
| GET | `/auth/oauth/google` | None | Initiate Google OAuth flow |
| GET | `/auth/oauth/google/callback` | None | Google OAuth callback, returns JWT |

### Interactions
| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| GET | `/projects/{id}/comments` | None | Comments for a project |
| POST | `/projects/{id}/comments` | User | Post a comment |
| GET | `/courses/{id}/comments` | None | Comments for a course |
| POST | `/courses/{id}/comments` | User | Post a comment |
| DELETE | `/comments/{id}` | Admin | Delete a comment |
| GET | `/projects/{id}/ratings` | None | Rating summary for a project |
| POST | `/projects/{id}/ratings` | User | Submit or update a rating (1–5 stars) |
| GET | `/courses/{id}/ratings` | None | Rating summary for a course |
| POST | `/courses/{id}/ratings` | User | Submit or update a rating (1–5 stars) |
| GET | `/guestbook` | None | All guestbook entries |
| POST | `/guestbook` | None | Submit entry (name required, shows as `name (guest)` if not logged in) |
| GET | `/quiz/questions` | User | Fetch quiz questions |
| POST | `/quiz/submit` | User | Submit answers, receive score |
| GET | `/quiz/leaderboard` | User | Top scores |
| GET | `/testimonials` | None | Approved testimonials (filterable by identity) |
| POST | `/testimonials` | None | Submit testimonial (anonymous or named, pending approval) |

### Stats
| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| GET | `/stats/visitors` | None | Visit locations for public map |
| GET | `/stats/analytics` | Admin | Full breakdown: identity, per-page, time, region |

### Admin
| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| GET | `/admin/users` | Admin | List all users |
| PUT | `/admin/users/{id}` | Admin | Suspend or ban a user |
| DELETE | `/admin/users/{id}` | Admin | Delete a user |
| GET | `/admin/contacts` | Admin | View contact form submissions |
| GET | `/admin/testimonials/pending` | Admin | Testimonials awaiting approval |
| PUT | `/admin/testimonials/{id}` | Admin | Approve or reject a testimonial |
| GET | `/admin/quiz/questions` | Admin | List all quiz questions |
| POST | `/admin/quiz/questions` | Admin | Add a quiz question |
| PUT | `/admin/quiz/questions/{id}` | Admin | Edit a quiz question |
| DELETE | `/admin/quiz/questions/{id}` | Admin | Delete a quiz question |

### Contact
| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| POST | `/contact` | None | Submit contact form (rate limited 5/hr per IP) |

---

## Section 4 — Data & Storage

**Table name:** `portfolio`
**Billing:** On-demand (pay per request)
**Primary key:** `PK` (partition key) + `SK` (sort key), both strings

| Entity | PK | SK | Notes |
|--------|----|----|-------|
| User profile | `USER#<id>` | `PROFILE` | name, email, identity, role, created_at |
| OAuth link | `OAUTH#<provider>#<provider_id>` | `LINK` | maps provider ID → user ID |
| Email verify token | `VERIFY#<token>` | `TOKEN` | TTL: 24hrs |
| Refresh token | `SESSION#<token>` | `SESSION` | TTL: 7 days |
| Site content | `CONTENT` | `ABOUT` / `SKILLS` / `TIMELINE` / `FUNFACTS` / `CURRENTLY_LEARNING` / `CONTACT_INFO` | Singleton items, field-level updates |
| Project | `PROJECT#<id>` | `META` | title, description, links, tech stack |
| Course | `COURSE#<id>` | `META` | title, description, platform, link |
| Comment on project | `PROJECT#<id>` | `COMMENT#<timestamp>#<id>` | user_id, body, identity tag |
| Comment on course | `COURSE#<id>` | `COMMENT#<timestamp>#<id>` | same structure |
| Rating on project | `PROJECT#<id>` | `RATING#<user_id>` | stars 1–5, one per user per project |
| Rating on course | `COURSE#<id>` | `RATING#<user_id>` | same structure |
| Guestbook entry | `GUESTBOOK` | `ENTRY#<timestamp>#<id>` | name, body, is_authenticated |
| Quiz question | `QUIZ` | `QUESTION#<id>` | question, options, answer, topic |
| Quiz score | `USER#<id>` | `QUIZ_SCORE#<attempt_id>` | score, answers, timestamp |
| Testimonial | `TESTIMONIALS` | `TESTIMONIAL#<id>` | body, author (or "Anonymous"), identity, status |
| Visit record | `VISITS` | `VISIT#<timestamp>#<id>` | ip, country, city, lat, lon, page, identity |
| Contact submission | `CONTACTS` | `CONTACT#<timestamp>#<id>` | name, email, message |
| Rate limit tracker | `RATELIMIT#<ip>` | `CONTACT` | count, TTL: 1hr |

**Global Secondary Indexes:**

| GSI | GSI PK | GSI SK | Used for |
|-----|--------|--------|----------|
| GSI1 | `EMAIL#<email>` | `USER` | User lookup by email (login + account linking) |
| GSI2 | `STATUS#<pending/approved>` | `TESTIMONIAL#<timestamp>` | Admin fetches pending testimonials |
| GSI3 | `QUIZ_LEADERBOARD` | `SCORE#<zero-padded>` | Leaderboard sorted by score |

**TTL fields:** `verify_token` (24hrs), `refresh_token` (7 days), `rate_limit` (1hr) — auto-deleted by DynamoDB.

**Why single-table:** One query instead of multiple round-trips, lower cost, fewer AWS resources to manage. All access patterns designed upfront in the schema above.

---

## Section 5 — CI/CD & Branch Strategy

**Branches:**
```
prod       →  auto-deploys to production (live site)
dev        →  auto-deploys to dev environment
feature/*  →  runs tests only, no deploy
```

**Path-based triggers — only redeploys what changed:**
- Changes in `backend/**` → `deploy-backend.yml` runs
- Changes in `frontend/**` → `deploy-frontend.yml` runs
- Both can trigger independently on the same push

**deploy-backend.yml steps:**
1. Run `pytest` — stops deploy on failure
2. Run `flake8` lint
3. `pip install -r requirements.txt -t package/`
4. Zip into `lambda.zip`
5. `aws lambda update-function-code`
6. Stamp env vars: `GIT_SHA`, `DEPLOY_TIMESTAMP`, `ENVIRONMENT` injected into Lambda config
7. Send deploy notification (Discord webhook)

**deploy-frontend.yml steps:**
1. Validate HTML
2. `aws s3 sync frontend/ s3://<bucket> --delete`
3. `aws cloudfront create-invalidation` (clears CDN cache)
4. Send deploy notification

**Environments:**

| Resource | Dev | Prod |
|----------|-----|------|
| Lambda | `portfolio-dev` | `portfolio-prod` |
| S3 bucket | `portfolio-frontend-dev` | `portfolio-frontend-prod` |
| CloudFront | Separate distribution | Separate distribution |
| DynamoDB | Shared `portfolio` table | Shared `portfolio` table |

**GitHub Secrets required:**
```
AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_REGION
PROD_LAMBDA_FUNCTION_NAME / DEV_LAMBDA_FUNCTION_NAME
PROD_S3_BUCKET / DEV_S3_BUCKET
PROD_CLOUDFRONT_ID / DEV_CLOUDFRONT_ID
SES_SENDER_EMAIL
JWT_SECRET_KEY
GITHUB_OAUTH_CLIENT_ID / GITHUB_OAUTH_CLIENT_SECRET
GOOGLE_OAUTH_CLIENT_ID / GOOGLE_OAUTH_CLIENT_SECRET
```

---

## Section 6 — Frontend Design

**Stack:** Alpine.js (15KB, no build step) + vanilla HTML/CSS → S3/CloudFront

**Themes (5 total, default: Light):**

| Theme | Background | Text | Accent |
|-------|-----------|------|--------|
| Light (default) | `#FFFFFF` | `#212529` | `#007BFF` |
| Dark | `#121212` | `#E0E0E0` | `#4FC3F7` |
| Coffee | `#FAF3E0` | `#5D4037` | `#A1887F` |
| Terminal | `#000000` | `#00FF41` | `#008F11` |
| Nordic | `#2E3440` | `#D8DEE9` | `#88C0D0` |

- Theme stored in `localStorage` for guests, DynamoDB profile for authenticated users
- Updated via `PUT /auth/me` — synced across devices on login
- WCAG AA contrast ratio enforced for all themes before implementation

**Site map & navigation:**

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                         GLOBAL NAVIGATION BAR                                  │
│  Home · About · Projects · Courses · Skills · Stats · Contact                  │
│  Guestbook · Testimonials · Developer                          (all users)     │
│  + Quiz                                                    (authenticated+)    │
│  + Admin                                                      (admin only)     │
└────────────────────────────────────────────────────────────────────────────────┘

── Public Pages ──────────────────────────────────────────────────────────────────

┌──────────────────────────────────────┐  ┌──────────────────────────────────────┐
│  / (Home)                            │  │  /about                              │
│──────────────────────────────────────│  │──────────────────────────────────────│
│  · Hero + mission statement          │  │  · Full bio told as a story          │
│  · Currently learning ticker         │  │  · Journey timeline                  │
│  · Fun fact widget                   │  │  · Personal quote                    │
│  · Visitor map teaser                │  │  · Social + contact links            │
└──────────────────────────────────────┘  └──────────────────────────────────────┘

┌──────────────────────────────────────┐  ┌──────────────────────────────────────┐
│  /projects                           │  │  /courses                            │
│──────────────────────────────────────│  │──────────────────────────────────────│
│  · Project cards + descriptions      │  │  · Course cards + descriptions       │
│  · Tech stack tags                   │  │  · Tech stack tags                   │
│  · Star rating display               │  │  · Star rating display               │
│  · Comment count                     │  │  · Comment count                     │
└──────────────────────┬───────────────┘  └──────────────────────┬───────────────┘
                       │                                         │
                       ▼                                         ▼
┌──────────────────────────────────────┐  ┌──────────────────────────────────────┐
│  /projects/:id                       │  │  /courses/:id                        │
│──────────────────────────────────────│  │──────────────────────────────────────│
│  · Full description                  │  │  · Full description                  │
│  · Star rating (auth to rate)        │  │  · Star rating (auth to rate)        │
│  · Comments section                  │  │  · Comments section                  │
└──────────────────────────────────────┘  └──────────────────────────────────────┘

┌──────────────────────────────────────┐  ┌──────────────────────────────────────┐
│  /skills                             │  │  /stats                              │
│──────────────────────────────────────│  │──────────────────────────────────────│
│  · Skills grouped by category        │  │  · World visitor map                 │
│  · Languages · Tools · Platforms     │  │  · Visit counts                      │
│  · Soft skills                       │  │  · Identity breakdown                │
│                                      │  │  · (admin sees richer analytics)     │
└──────────────────────────────────────┘  └──────────────────────────────────────┘

┌──────────────────────────────────────┐  ┌──────────────────────────────────────┐
│  /contact                            │  │  /guestbook                          │
│──────────────────────────────────────│  │──────────────────────────────────────│
│  · Contact details (email, GitHub,   │  │  · All entries (name + message)      │
│    LinkedIn, location)               │  │  · Submit form (guests welcome)      │
│  · Contact form (rate limited        │  │  · Shows as "name (guest)" if not    │
│    5/hr per IP)                      │  │    logged in                         │
└──────────────────────────────────────┘  └──────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────────┐
│  /testimonials                                                                 │
│────────────────────────────────────────────────────────────────────────────────│
│  · Approved testimonials with identity badges                                  │
│  · Filterable by: Jamf · MCRI · Friend · Family · Other                        │
│  · Submit form (anonymous allowed — pending admin approval before going live)  │
└────────────────────────────────────────────────────────────────────────────────┘

── Auth Flow ─────────────────────────────────────────────────────────────────────

┌──────────────────────────┐  ┌──────────────────────────┐  ┌──────────────────────────┐
│  /login                  │─▶│  /register               │─▶│  /verify-email           │
│──────────────────────────│  │──────────────────────────│  │──────────────────────────│
│  · Email + password      │  │  · Name + email          │  │  · Token sent via SES    │
│  · GitHub OAuth          │  │  · Password              │  │  · Confirms account      │
│  · Google OAuth          │  │  · Identity tag          │  │  · Redirects to home     │
│  · Remember me (7d JWT)  │  │  · Same-email → linked   │  │                          │
└──────────────────────────┘  └──────────────────────────┘  └──────────────────────────┘
  │ on success → redirect to previous page or Home

── Authenticated Only ────────────────────────────────────────────────────────────

┌────────────────────────────────────────────────────────────────────────────────┐
│  /quiz  (authenticated users only)                                             │
│────────────────────────────────────────────────────────────────────────────────│
│  · 20 questions · scored and saved per user · results shown on submit          │
│  · Leaderboard · filterable by topic (scalable)                                │
└────────────────────────────────────────────────────────────────────────────────┘

── Admin (/admin/*) ──────────────────────────────────────────────────────────────

┌────────────────────────────────────────────────────────────────────────────────┐
│  /admin  — Dashboard overview (stats summary, quick actions)                   │
└────────────────────────────────────────────────────────────────────────────────┘
                                         │
     ┌──────────────────┬────────────────┼────────────────┬──────────────────┐
     │                  │                │                │                  │
     ▼                  ▼                ▼                ▼                  ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ /content     │ │ /users       │ │ /contacts    │ │ /testimony   │ │ /quiz        │
│──────────────│ │──────────────│ │──────────────│ │──────────────│ │──────────────│
│ Edit bio     │ │ View all     │ │ View all     │ │ Pending      │ │ Add/edit     │
│ Projects     │ │ Suspend      │ │ submissions  │ │ queue        │ │ delete       │
│ Courses      │ │ Ban          │ │              │ │ Approve /    │ │ questions    │
│ Fun facts    │ │ Delete       │ │              │ │ Reject       │ │              │
│ Skills       │ │              │ │              │ │              │ │              │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘

── Developer ─────────────────────────────────────────────────────────────────────

┌────────────────────────────────────────────────────────────────────────────────┐
│  /api  — Interactive Swagger UI (accessible to all, linked in nav as Developer)│
│────────────────────────────────────────────────────────────────────────────────│
│  · Try all endpoints live from the browser                                     │
│  · /api/spec → raw OpenAPI 3.0 JSON (importable into Postman)                  │
└────────────────────────────────────────────────────────────────────────────────┘
```

**Small touches:**
- Custom favicon
- Loading animation while Alpine.js fetches API data
- Scroll interactions
- Easter egg hidden in browser console logs
- Open Graph meta tags for social sharing
- Theme toggle accessible from nav on every page

---

## Section 7 — Hosting & Deployment

### AWS Resources

| Resource | Name | Config |
|----------|------|--------|
| S3 bucket (prod) | `portfolio-frontend-prod` | Public read blocked, CloudFront-only access |
| S3 bucket (dev) | `portfolio-frontend-dev` | Same config |
| CloudFront (prod) | — | Origin = prod S3, default root = `index.html`, HTTPS via `*.cloudfront.net` |
| CloudFront (dev) | — | Origin = dev S3 |
| Lambda (prod) | `portfolio-prod` | Python 3.12, 512MB, 30s timeout, Function URL enabled |
| Lambda (dev) | `portfolio-dev` | Same config |
| DynamoDB | `portfolio` | On-demand billing, shared by dev and prod |
| SES | — | Single verified sender email address |
| IAM role | `portfolio-lambda-role` | Least-privilege: DynamoDB read/write, SES send, CloudWatch logs |

### Lambda Environment Variables
```
GIT_SHA              ← injected by GitHub Actions (${{ github.sha }})
DEPLOY_TIMESTAMP     ← injected by GitHub Actions (ISO 8601)
ENVIRONMENT          ← prod or dev
VERSION              ← read from version.txt in repo
JWT_SECRET_KEY       ← GitHub Secret
SES_SENDER_EMAIL     ← GitHub Secret
GITHUB_OAUTH_CLIENT_ID / GITHUB_OAUTH_CLIENT_SECRET  ← GitHub Secrets
GOOGLE_OAUTH_CLIENT_ID / GOOGLE_OAUTH_CLIENT_SECRET  ← GitHub Secrets
DYNAMODB_TABLE_NAME  ← portfolio
```

### IAM Policy (least-privilege)
- `dynamodb:GetItem`, `PutItem`, `UpdateItem`, `DeleteItem`, `Query` on `portfolio` table + GSIs
- `ses:SendEmail` from verified sender address only
- `logs:CreateLogGroup`, `PutLogEvents` for CloudWatch

### CloudFront Behaviour
- All unmatched routes (e.g. `/about`, `/quiz`) serve `index.html` — Alpine.js handles client-side routing
- `/api/*` routes hit Lambda Function URL directly, not via CloudFront
- HTTPS provided automatically by CloudFront default certificate

### /meta Stamping
At deploy time, GitHub Actions runs:
```bash
aws lambda update-function-configuration \
  --function-name $LAMBDA_NAME \
  --environment Variables="{GIT_SHA=${{ github.sha }},DEPLOY_TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ),ENVIRONMENT=prod,...}"
```
The `/meta` endpoint reads these from `os.environ` — always accurate, never manually updated.
