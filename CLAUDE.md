# CLAUDE.md — Portfolio Site

This file tells Claude how to work in this repository.

## Project

Personal portfolio site for Ron Harifiyati. API-first architecture: Python Lambda backend behind API Gateway HTTP API + Alpine.js frontend on S3/CloudFront. See `docs/superpowers/specs/2026-04-02-portfolio-design.md` for the full design spec.

## Key Conventions

### Branch strategy
- `prod` → auto-deploys to production
- `dev` → auto-deploys to dev environment
- `feature/*` → tests only, no deploy
- Always branch from `dev`, merge back to `dev`

### Commits
- Commit after every completed task
- Use conventional commits: `feat:`, `fix:`, `chore:`, `ci:`, `docs:`

### Response envelope
Every API response must use:
```json
{ "data": ..., "error": null }
{ "data": null, "error": "message" }
```
Use helpers from `backend/utils.py`: `ok()`, `created()`, `bad_request()`, `unauthorized()`, `not_found()`, etc.

### Route handler signature
All route functions take exactly these parameters (no exceptions):
```python
def my_route(event, path_params, body, query, headers):
    ...
```
Authenticated routes use `@require_auth` or `@require_admin` decorators from `auth.py`, which inject a `user` kwarg.

### DynamoDB
Single-table design. Table name from `os.environ["DYNAMODB_TABLE_NAME"]` (always `"portfolio"`).
Key patterns are defined in `docs/superpowers/plans/2026-04-02-portfolio-backend.md` — always check before adding new access patterns.
GSI attribute names: `GSI1PK`, `GSI1SK`, `GSI2PK`, `GSI2SK`, `GSI3PK`, `GSI3SK`.

### Models vs Routes
- `models/` — pure DynamoDB read/write, no HTTP logic
- `routes/` — HTTP handling only, call models for data

### Import pattern (avoid name shadowing)
When route function names match model function names, import models with alias:
```python
from models import projects as project_model
```

## Running Tests

```bash
cd backend
pytest tests/ -v
```

Tests use `moto` to mock DynamoDB — no real AWS calls needed. The `aws_env` fixture in `conftest.py` sets all required env vars and runs `autouse=True`.

## Running Linter

```bash
cd backend
flake8 . --max-line-length=120 --exclude=tests/,package/
```

## Frontend

- No build step. Open `frontend/` with any static server.
- `api.js` must be loaded before `themes.js` and `app.js`
- Alpine.js is loaded last with `defer`
- Theme system: CSS custom properties in `theme.css`, managed by `themes.js`
- Hash-based routing in `app.js` — `#/page-name`

## AWS Environments

| Resource | Dev | Prod |
|----------|-----|------|
| API Gateway | `portfolio-dev` (`ly0fxfdai9`) | `portfolio-prod` (`o4o1xcb3wc`) |
| Lambda | `portfolio-dev` | `portfolio-prod` |
| S3 | `portfolio-frontend-dev-993249606359` | `portfolio-frontend-prod-993249606359` |
| CloudFront | `E3GFM00HUAVU15` (`d3sw9ggppgh9as.cloudfront.net`) | `E1P7C158XTW7UF` (`dkdwnfmhg75yf.cloudfront.net`) |
| DynamoDB | `portfolio` (shared) | `portfolio` (shared) |

## Implementation Plans

Execute plans in this order:
1. `docs/superpowers/plans/2026-04-02-portfolio-infra.md` — AWS setup + CI/CD
2. `docs/superpowers/plans/2026-04-02-portfolio-backend.md` — Python API
3. `docs/superpowers/plans/2026-04-02-portfolio-frontend.md` — Alpine.js SPA

Use `superpowers:executing-plans` or `superpowers:subagent-driven-development` to execute them.
