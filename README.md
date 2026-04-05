# Ron Harifiyati — Personal Portfolio

A live, interactive, API-first personal portfolio running on AWS. The backend is a standalone Python API (usable via Postman/curl), the frontend is an Alpine.js SPA served from S3/CloudFront.

---

## Architecture

```
Browser (Alpine.js SPA)
    │
    ├── Static assets ──▶ CloudFront + S3
    │
    └── API calls ──▶ API Gateway HTTP API → Lambda (Python 3.12)
                            │
                ┌───────────┼──────────────┐
                ▼           ▼              ▼
           DynamoDB       AWS SES      ip-api.com
         (single table)  (email)     (geolocation)
```

## Repository Structure

```
about-me/
├── frontend/                        # Static SPA → S3/CloudFront
│   ├── index.html                   # Main app (all public pages)
│   ├── admin.html                   # Admin panel
│   └── assets/
│       ├── css/                     # theme.css (5 themes) + main.css
│       └── js/                      # api.js, themes.js, app.js, pages/
├── backend/                         # Python Lambda
│   ├── handler.py                   # Entry point
│   ├── router.py                    # Path-based dispatch
│   ├── auth.py                      # JWT utilities + decorators
│   ├── db.py                        # DynamoDB client
│   ├── utils.py                     # Response helpers
│   ├── routes/                      # One file per route group
│   ├── models/                      # DynamoDB access patterns
│   ├── requirements.txt
│   └── tests/                       # pytest + moto
├── .github/
│   └── workflows/
│       ├── deploy-backend.yml       # Triggers on backend/** changes
│       └── deploy-frontend.yml      # Triggers on frontend/** changes
├── infra/
│   └── iam-policy.json              # Lambda IAM permissions policy
├── docs/
│   └── superpowers/
│       ├── specs/                   # Design specifications
│       └── plans/                   # Implementation plans
└── version.txt                      # Bumped manually on release
```

## Branch Strategy

| Branch | Behaviour |
|--------|-----------|
| `prod` | Auto-deploys to production AWS resources |
| `dev` | Auto-deploys to dev AWS resources |
| `feature/*` | Runs tests only, no deploy |

## Getting Started

### Backend

The backend runs as a Lambda function — there is no local server. The dev Lambda is already deployed and accessible at:

- **Dev API:** `https://ly0fxfdai9.execute-api.us-east-1.amazonaws.com`
- **Prod API:** `https://o4o1xcb3wc.execute-api.us-east-1.amazonaws.com`

`frontend/assets/js/api.js` auto-detects the environment and points to the correct URL.

For tests and linting:

```bash
cd backend
pip install -r requirements.txt
pip install pytest pytest-mock "moto[dynamodb,ses]" flake8

# Run tests (moto mocks DynamoDB — no AWS calls)
pytest tests/ -v

# Lint
flake8 . --max-line-length=120 --exclude=tests/,package/
```

### Frontend (local)

```bash
cd frontend
python3 -m http.server 8080
# Open http://localhost:8080
```

The frontend automatically calls the dev Lambda. No configuration needed.

## Docs

- **Design spec:** [`docs/superpowers/specs/2026-04-02-portfolio-design.md`](docs/superpowers/specs/2026-04-02-portfolio-design.md)
- **Infrastructure plan:** [`docs/superpowers/plans/2026-04-02-portfolio-infra.md`](docs/superpowers/plans/2026-04-02-portfolio-infra.md)
- **Backend plan:** [`docs/superpowers/plans/2026-04-02-portfolio-backend.md`](docs/superpowers/plans/2026-04-02-portfolio-backend.md)
- **Frontend plan:** [`docs/superpowers/plans/2026-04-02-portfolio-frontend.md`](docs/superpowers/plans/2026-04-02-portfolio-frontend.md)
- **Visitor analytics plan:** [`docs/superpowers/plans/2026-04-05-visitor-analytics.md`](docs/superpowers/plans/2026-04-05-visitor-analytics.md)

## API

The API is publicly accessible and documented interactively.

- **Swagger UI (dev):** `https://ly0fxfdai9.execute-api.us-east-1.amazonaws.com/api`
- **OpenAPI spec (dev):** `https://ly0fxfdai9.execute-api.us-east-1.amazonaws.com/api/spec`
- **Deploy info:** `https://ly0fxfdai9.execute-api.us-east-1.amazonaws.com/meta`

All responses use the envelope: `{"data": ..., "error": ...}`

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, boto3, PyJWT, requests |
| Database | DynamoDB single-table (on-demand billing) |
| Auth | Custom JWT + GitHub OAuth + Google OAuth |
| Frontend | Alpine.js 3.x, vanilla CSS, Leaflet.js |
| Hosting | API Gateway HTTP API, Lambda, S3, CloudFront |
| Email | AWS SES |
| CI/CD | GitHub Actions (path-based triggers) |
| Tests | pytest, moto |
