# Plan 2 Implementation Log — Backend Python API

**Date:** 2026-04-03
**Plan:** `docs/superpowers/plans/2026-04-02-portfolio-backend.md`
**Outcome:** Complete. All 75 tests passing. Deployed to production Lambda `portfolio-prod` v1.0.0.

---

## Overview

This document records what was done, in what order, what challenges were encountered, what was tried, what failed, and what ultimately worked — along with the reasons.

**Starting state:**
- `backend/handler.py` — hello-world placeholder from Plan 1
- `backend/requirements.txt` — already has `boto3`, `PyJWT`, `requests` from Plan 1
- `backend/tests/` — only `__init__.py` + `test_placeholder.py` from Plan 1 CI fix
- No `routes/`, `models/`, `db.py`, `auth.py`, `utils.py`, `router.py`

---

## Feature Branch: `feature/backend-foundation`

### Task 1: Test infrastructure (conftest + utils)

**What we did:**
Created `backend/tests/__init__.py` (already existed), `backend/tests/conftest.py`, `backend/utils.py`, `backend/routes/__init__.py`, `backend/models/__init__.py`. Updated `requirements.txt` was already correct from Plan 1.

<!-- challenges + resolutions appended here as tasks complete -->

---

### Task 2: db.py — DynamoDB client

**What we did:**
Created `backend/db.py` with `get_table()` singleton and `reset_table()` for test teardown. Added `reset_db_singleton` autouse fixture to `conftest.py`.

---

### Task 3: auth.py — JWT utilities and decorators

**What we did:**
Created `backend/auth.py` with `make_jwt`, `decode_jwt`, `get_current_user`, `require_auth`, `require_admin`. All 9 tests pass.

---

### Task 4: handler.py + router.py

**What we did:**
Rewrote `backend/handler.py` to delegate to `router.route()`. Created `backend/router.py` with the full path-based dispatch table (regex matching for parameterized routes). Created stub route files for all 15 route modules.

---

## Feature Branch: `feature/content-routes`

### Task 5: /meta route

**What we did:**
Implemented `backend/routes/meta.py` returning deploy info from env vars.

---

### Task 6: Site content routes + models

**What we did:**
Created `backend/models/content.py` (get/update with DDB singleton pattern). Implemented `backend/routes/content.py` (about, skills, timeline, fun-fact, currently-learning, all admin-protected writes).

---

### Task 7: Projects + Courses routes

**What we did:**
Created `backend/models/projects.py` and `backend/models/courses.py` (CRUD with uuid IDs). Implemented `backend/routes/projects.py` and `backend/routes/courses.py` (aliased imports to avoid name shadowing). Implemented `backend/routes/github.py` (live GitHub API call, graceful fallback to empty list).

---

## Feature Branch: `feature/auth-routes`

### Task 8: User model

**What we did:**
Created `backend/models/users.py` with full user lifecycle: password hashing (sha256+salt), email verification tokens, refresh token rotation, OAuth link table, GSI1 email lookups, admin user management.

---

### Task 9: Auth routes (email/password + JWT)

**What we did:**
Implemented `backend/routes/auth_routes.py`: register (with SES email mock), verify-email, login, logout, refresh, GET/PUT /auth/me, GitHub OAuth init+callback, Google OAuth init+callback.

---

## Feature Branch: `feature/interaction-routes`

### Task 10: Comments + Ratings

**What we did:**
Created `backend/models/interactions.py` shared model for both projects and courses. Implemented `backend/routes/comments.py` and `backend/routes/ratings.py`.

---

### Task 11: Guestbook

**What we did:**
Created `backend/models/guestbook.py` and `backend/routes/guestbook.py`. Guest entries get "(guest)" suffix; authenticated users show their profile identity.

---

### Task 12: Quiz

**What we did:**
Created `backend/models/quiz.py` (questions + leaderboard via GSI3) and `backend/routes/quiz.py`. Answers stripped from question responses sent to clients.

---

### Task 13: Testimonials

**What we did:**
Created `backend/models/testimonials.py` (GSI2 for status-based queries, approve/reject via update_item) and `backend/routes/testimonials.py`.

---

## Feature Branch: `feature/stats-contact`

### Task 14: Visitor tracking + stats routes

**What we did:**
Created `backend/models/visits.py` with ip-api.com geo lookup (best-effort, silently fails). Implemented `backend/routes/stats.py` with aliased imports.

---

### Task 15: Contact form + rate limiting

**What we did:**
Created `backend/models/contacts.py` with DDB-backed IP rate limiting (5/hr, TTL 1hr). Implemented `backend/routes/contact.py` with SES notification (mockable).

---

## Feature Branch: `feature/admin-routes`

### Task 16: Admin routes

**What we did:**
Implemented `backend/routes/admin.py` with all admin endpoints: user management, contact listing, testimonial approve/reject, quiz question CRUD.

---

## Feature Branch: `feature/api-docs`

### Task 17: Swagger UI + OpenAPI spec

**What we did:**
Implemented `backend/routes/docs.py` with full Swagger UI HTML at `/api` and OpenAPI 3.0 JSON spec at `/api/spec`.

---

## Final Verification

- **75 tests passing** across 17 test files
- **Lint clean** — flake8 with `--max-line-length=120`
- **CI/CD** — prod deploy pipeline ran green (run ID 23940340968)
- **Production Lambda** — `portfolio-prod` updated to v1.0.0, SHA `c6fe289`
- **All 40+ endpoints** wired in `router.py`, validated by test suite

---

## Key Lessons

### 1. DynamoDB: `begins_with` is invalid on PK in Query

The plan called for `Key("PK").begins_with("PROJECT#")` in a `KeyConditionExpression`. DynamoDB requires the partition key to use equality — range operators are only valid on the sort key. Fix: use `table.scan(FilterExpression=Attr("PK").begins_with(...))`. Applied to `list_projects()`, `list_courses()`, and `list_all_users()`.

### 2. GSI sort-key-only queries are rejected

`list_all_users()` initially queried GSI1 by `GSI1SK` only (no `GSI1PK`). DynamoDB rejects this — partition key is always required in a Query. Fix: scan with `Attr("SK").eq("PROFILE") & Attr("PK").begins_with("USER#")`.

### 3. Unused imports cause flake8 F401 failures in CI

Two separate lint failures hit dev after merges because imports became unused after refactoring:
- `Key` in `models/projects.py` after switching from Query to scan
- `get_current_user` in `routes/comments.py` (never used directly — auth handled by `@require_auth` decorator)

Lesson: run `flake8` locally before every commit, especially after changing data access patterns.

### 4. PR dependency ordering matters

`feature/admin-routes` imported `models.contacts` which lived on `feature/stats-contact`. Tests on admin-routes failed until PR #2 merged. Always branch feature work after dependent models land on dev.

### 5. `prod` branch is the deploy target, not `main`

The CI workflow triggers on `dev` and `prod` branches only. Merging to `main` does not deploy. Creating the `prod` branch required a `version.txt` bump to trigger the workflow since GitHub doesn't fire push events for branch creation without a new path-matching commit.
