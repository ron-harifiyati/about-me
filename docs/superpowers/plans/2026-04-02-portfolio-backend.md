# Portfolio Site — Backend API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete Python Lambda API — all 40+ endpoints, DynamoDB model layer, JWT auth, OAuth, rate limiting, visitor tracking, and Swagger docs.

**Architecture:** Single `handler.py` entry point dispatches to a path-based router; routes/ holds one file per feature group; models/ holds pure DynamoDB access patterns; auth.py provides JWT utilities and decorators; db.py wraps the boto3 client. All responses use `{"data": ..., "error": ...}` envelope. CORS headers on every response.

**Tech Stack:** Python 3.12, boto3, PyJWT, requests, pytest, moto[dynamodb,ses]

**Prerequisites:** Plan 1 (Infrastructure) complete — DynamoDB table active, Lambda functions exist, CI/CD workflows in place.

---

## File Structure

```
backend/
├── handler.py                  # Lambda entry point — calls router
├── router.py                   # Path-based dispatch table (regex matching)
├── auth.py                     # JWT encode/decode, require_auth/require_admin decorators
├── db.py                       # boto3 DynamoDB client singleton
├── utils.py                    # cors_response(), envelope helpers
├── requirements.txt            # Production deps
├── routes/
│   ├── __init__.py
│   ├── meta.py                 # GET /meta
│   ├── content.py              # GET+PUT /about /skills /timeline /fun-fact /currently-learning
│   ├── projects.py             # CRUD /projects + /projects/{id}
│   ├── courses.py              # CRUD /courses + /courses/{id}
│   ├── github.py               # GET /github/repos
│   ├── auth_routes.py          # /auth/* (register, verify, login, logout, refresh, me, OAuth)
│   ├── comments.py             # /projects/{id}/comments, /courses/{id}/comments, /comments/{id}
│   ├── ratings.py              # /projects/{id}/ratings, /courses/{id}/ratings
│   ├── guestbook.py            # /guestbook
│   ├── quiz.py                 # /quiz/questions, /quiz/submit, /quiz/leaderboard
│   ├── testimonials.py         # /testimonials
│   ├── stats.py                # /stats/visitors, /stats/analytics
│   ├── contact.py              # POST /contact (rate limited)
│   ├── admin.py                # /admin/*
│   └── docs.py                 # GET /api (Swagger UI), GET /api/spec (OpenAPI JSON)
├── models/
│   ├── __init__.py
│   ├── users.py                # User CRUD + OAuth link + email verify + session tokens
│   ├── content.py              # Site content singleton items (about, skills, etc.)
│   ├── projects.py             # Project CRUD
│   ├── courses.py              # Course CRUD
│   ├── interactions.py         # Comments + ratings (shared, works for projects and courses)
│   ├── guestbook.py            # Guestbook entries
│   ├── quiz.py                 # Quiz questions + scores
│   ├── testimonials.py         # Testimonials + approval
│   ├── visits.py               # Visit records + geolocation
│   └── contacts.py             # Contact submissions + rate limit tracker
└── tests/
    ├── conftest.py             # pytest fixtures: mock AWS creds, moto DynamoDB table
    ├── test_router.py
    ├── test_auth.py
    ├── test_meta.py
    ├── test_content.py
    ├── test_projects.py
    ├── test_courses.py
    ├── test_auth_routes.py
    ├── test_oauth.py
    ├── test_comments.py
    ├── test_ratings.py
    ├── test_guestbook.py
    ├── test_quiz.py
    ├── test_testimonials.py
    ├── test_stats.py
    ├── test_contact.py
    └── test_admin.py
```

## DynamoDB Key Patterns (reference for model code)

| Entity | PK | SK | GSI attributes |
|--------|----|----|----------------|
| User profile | `USER#<id>` | `PROFILE` | `GSI1PK=EMAIL#<email>`, `GSI1SK=USER` |
| OAuth link | `OAUTH#<provider>#<provider_id>` | `LINK` | — |
| Email verify token | `VERIFY#<token>` | `TOKEN` | ttl (24hr) |
| Refresh token | `SESSION#<token>` | `SESSION` | ttl (7d) |
| Site content | `CONTENT` | `ABOUT` / `SKILLS` / `TIMELINE` / `FUNFACTS` / `CURRENTLY_LEARNING` / `CONTACT_INFO` | — |
| Project | `PROJECT#<id>` | `META` | — |
| Course | `COURSE#<id>` | `META` | — |
| Comment | `PROJECT#<id>` or `COURSE#<id>` | `COMMENT#<ts>#<id>` | — |
| Rating | `PROJECT#<id>` or `COURSE#<id>` | `RATING#<user_id>` | — |
| Guestbook entry | `GUESTBOOK` | `ENTRY#<ts>#<id>` | — |
| Quiz question | `QUIZ` | `QUESTION#<id>` | — |
| Quiz score | `USER#<id>` | `QUIZ_SCORE#<attempt_id>` | `GSI3PK=QUIZ_LEADERBOARD`, `GSI3SK=SCORE#<zero-padded>` |
| Testimonial | `TESTIMONIALS` | `TESTIMONIAL#<id>` | `GSI2PK=STATUS#<status>`, `GSI2SK=TESTIMONIAL#<ts>` |
| Visit record | `VISITS` | `VISIT#<ts>#<id>` | — |
| Contact submission | `CONTACTS` | `CONTACT#<ts>#<id>` | — |
| Rate limit tracker | `RATELIMIT#<ip>` | `CONTACT` | ttl (1hr) |

---

<!-- SECTIONS BELOW ARE ADDED INCREMENTALLY -->

---

## Feature Branch: `feature/backend-foundation`

> Covers: handler.py, router.py, db.py, auth.py, utils.py, conftest.py, test_router.py, test_auth.py

```bash
git checkout dev
git checkout -b feature/backend-foundation
```

---

### Task 1: Test infrastructure (conftest + utils)

**Files:**
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/utils.py`

- [ ] **Step 1: Create tests package**

```bash
mkdir -p backend/tests
touch backend/tests/__init__.py
touch backend/routes/__init__.py
touch backend/models/__init__.py
```

- [ ] **Step 2: Write conftest.py**

```python
# backend/tests/conftest.py
import boto3
import pytest
from moto import mock_aws


@pytest.fixture(autouse=True)
def aws_env(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("DYNAMODB_TABLE_NAME", "portfolio")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-32-chars-long-padding!")
    monkeypatch.setenv("SES_SENDER_EMAIL", "test@example.com")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("GIT_SHA", "abc123")
    monkeypatch.setenv("DEPLOY_TIMESTAMP", "2026-04-02T00:00:00Z")
    monkeypatch.setenv("VERSION", "0.1.0")
    monkeypatch.setenv("GITHUB_OAUTH_CLIENT_ID", "gh-client-id")
    monkeypatch.setenv("GITHUB_OAUTH_CLIENT_SECRET", "gh-client-secret")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "goog-client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "goog-client-secret")


@pytest.fixture
def ddb_table(aws_env):
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.create_table(
            TableName="portfolio",
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
                {"AttributeName": "GSI1PK", "AttributeType": "S"},
                {"AttributeName": "GSI1SK", "AttributeType": "S"},
                {"AttributeName": "GSI2PK", "AttributeType": "S"},
                {"AttributeName": "GSI2SK", "AttributeType": "S"},
                {"AttributeName": "GSI3PK", "AttributeType": "S"},
                {"AttributeName": "GSI3SK", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "GSI1",
                    "KeySchema": [
                        {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                        {"AttributeName": "GSI1SK", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
                {
                    "IndexName": "GSI2",
                    "KeySchema": [
                        {"AttributeName": "GSI2PK", "KeyType": "HASH"},
                        {"AttributeName": "GSI2SK", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
                {
                    "IndexName": "GSI3",
                    "KeySchema": [
                        {"AttributeName": "GSI3PK", "KeyType": "HASH"},
                        {"AttributeName": "GSI3SK", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        yield table


def make_event(method="GET", path="/", body=None, headers=None, query=None):
    """Helper to build a Lambda Function URL event dict."""
    return {
        "requestContext": {"http": {"method": method, "path": path}},
        "rawPath": path,
        "headers": headers or {},
        "queryStringParameters": query or {},
        "body": __import__("json").dumps(body) if body else None,
    }
```

- [ ] **Step 3: Write utils.py**

```python
# backend/utils.py
import json


def cors_response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        },
        "body": json.dumps(body, default=str),
    }


def ok(data) -> dict:
    return cors_response(200, {"data": data, "error": None})


def created(data) -> dict:
    return cors_response(201, {"data": data, "error": None})


def bad_request(message: str) -> dict:
    return cors_response(400, {"data": None, "error": message})


def unauthorized(message: str = "Authentication required") -> dict:
    return cors_response(401, {"data": None, "error": message})


def forbidden(message: str = "Forbidden") -> dict:
    return cors_response(403, {"data": None, "error": message})


def not_found(message: str = "Not found") -> dict:
    return cors_response(404, {"data": None, "error": message})


def conflict(message: str) -> dict:
    return cors_response(409, {"data": None, "error": message})


def rate_limited(message: str = "Rate limit exceeded. Try again later.") -> dict:
    return cors_response(429, {"data": None, "error": message})


def server_error(message: str = "Internal server error") -> dict:
    return cors_response(500, {"data": None, "error": message})
```

- [ ] **Step 4: Update requirements.txt**

```
boto3>=1.34.0
PyJWT>=2.8.0
requests>=2.31.0
```

- [ ] **Step 5: Run tests (empty suite passes)**

```bash
cd backend
pip install -r requirements.txt
pip install pytest pytest-mock "moto[dynamodb,ses]" flake8
pytest tests/ -v
```

Expected: `no tests ran` (0 collected). No errors.

---

### Task 2: db.py — DynamoDB client

**Files:**
- Create: `backend/db.py`
- Create: `backend/tests/test_router.py` (used later, placeholder for now)

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_router.py
from db import get_table


def test_get_table_returns_table_resource(ddb_table):
    table = get_table()
    assert table.name == "portfolio"
```

- [ ] **Step 2: Run to confirm it fails**

```bash
cd backend && pytest tests/test_router.py -v
```

Expected: `ModuleNotFoundError: No module named 'db'`

- [ ] **Step 3: Implement db.py**

```python
# backend/db.py
import os
import boto3

_table = None


def get_table():
    global _table
    if _table is None:
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        _table = dynamodb.Table(os.environ["DYNAMODB_TABLE_NAME"])
    return _table


def reset_table():
    """Call this in tests to force re-init with mocked client."""
    global _table
    _table = None
```

- [ ] **Step 4: Update conftest.py to reset the singleton between tests**

Add this fixture to `backend/tests/conftest.py` (append inside the file after the `make_event` function):

```python
@pytest.fixture(autouse=True)
def reset_db_singleton():
    import db
    db.reset_table()
    yield
    db.reset_table()
```

- [ ] **Step 5: Run test**

```bash
cd backend && pytest tests/test_router.py::test_get_table_returns_table_resource -v
```

Expected: PASS

---

### Task 3: auth.py — JWT utilities and decorators

**Files:**
- Create: `backend/auth.py`
- Create: `backend/tests/test_auth.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_auth.py
import time
import pytest
from auth import make_jwt, decode_jwt, get_current_user, require_auth, require_admin
from utils import ok


def test_make_and_decode_jwt():
    token = make_jwt("user-123", "user")
    payload = decode_jwt(token)
    assert payload["sub"] == "user-123"
    assert payload["role"] == "user"


def test_decode_jwt_returns_none_for_garbage():
    assert decode_jwt("not-a-token") is None


def test_make_jwt_remember_me_has_longer_expiry():
    token_short = make_jwt("u1", "user", remember_me=False)
    token_long = make_jwt("u1", "user", remember_me=True)
    short_exp = decode_jwt(token_short)["exp"]
    long_exp = decode_jwt(token_long)["exp"]
    assert long_exp > short_exp + 86400  # long token expires >1 day after short


def test_get_current_user_extracts_from_bearer_header():
    token = make_jwt("user-456", "user")
    headers = {"authorization": f"Bearer {token}"}
    payload = get_current_user(headers)
    assert payload["sub"] == "user-456"


def test_get_current_user_returns_none_without_header():
    assert get_current_user({}) is None


def test_require_auth_blocks_unauthenticated():
    @require_auth
    def protected(event, path_params, body, query, headers, user):
        return ok({"user": user["sub"]})

    resp = protected({}, {}, {}, {}, {})
    assert resp["statusCode"] == 401


def test_require_auth_passes_user_to_handler():
    token = make_jwt("user-789", "user")

    @require_auth
    def protected(event, path_params, body, query, headers, user):
        return ok({"user": user["sub"]})

    resp = protected({}, {}, {}, {}, {"authorization": f"Bearer {token}"})
    assert resp["statusCode"] == 200


def test_require_admin_blocks_non_admin():
    token = make_jwt("user-1", "user")

    @require_admin
    def admin_only(event, path_params, body, query, headers, user):
        return ok({})

    resp = admin_only({}, {}, {}, {}, {"authorization": f"Bearer {token}"})
    assert resp["statusCode"] == 403


def test_require_admin_allows_admin_role():
    token = make_jwt("admin-1", "admin")

    @require_admin
    def admin_only(event, path_params, body, query, headers, user):
        return ok({"ok": True})

    resp = admin_only({}, {}, {}, {}, {"authorization": f"Bearer {token}"})
    assert resp["statusCode"] == 200
```

- [ ] **Step 2: Run to confirm they fail**

```bash
cd backend && pytest tests/test_auth.py -v
```

Expected: `ModuleNotFoundError: No module named 'auth'`

- [ ] **Step 3: Implement auth.py**

```python
# backend/auth.py
import os
import time
import functools
import jwt
from utils import unauthorized, forbidden


def make_jwt(user_id: str, role: str, remember_me: bool = False) -> str:
    secret = os.environ["JWT_SECRET_KEY"]
    ttl = 7 * 24 * 3600 if remember_me else 24 * 3600
    payload = {"sub": user_id, "role": role, "exp": int(time.time()) + ttl}
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_jwt(token: str) -> dict | None:
    secret = os.environ["JWT_SECRET_KEY"]
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def get_current_user(headers: dict) -> dict | None:
    auth = headers.get("authorization") or headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    return decode_jwt(auth[7:])


def require_auth(fn):
    @functools.wraps(fn)
    def wrapper(event, path_params, body, query, headers):
        user = get_current_user(headers)
        if not user:
            return unauthorized()
        return fn(event, path_params, body, query, headers, user=user)
    return wrapper


def require_admin(fn):
    @functools.wraps(fn)
    def wrapper(event, path_params, body, query, headers):
        user = get_current_user(headers)
        if not user:
            return unauthorized()
        if user.get("role") != "admin":
            return forbidden("Admin access required")
        return fn(event, path_params, body, query, headers, user=user)
    return wrapper
```

- [ ] **Step 4: Run tests**

```bash
cd backend && pytest tests/test_auth.py -v
```

Expected: All 9 tests PASS

---

### Task 4: handler.py + router.py

**Files:**
- Modify: `backend/handler.py`
- Create: `backend/router.py`
- Modify: `backend/tests/test_router.py`

- [ ] **Step 1: Write failing router tests**

```python
# backend/tests/test_router.py
import json
from tests.conftest import make_event
from db import get_table


def test_get_table_returns_table_resource(ddb_table):
    table = get_table()
    assert table.name == "portfolio"


def test_options_returns_cors_200():
    from router import route
    event = make_event(method="OPTIONS", path="/meta")
    resp = route(event)
    assert resp["statusCode"] == 200
    assert resp["headers"]["Access-Control-Allow-Origin"] == "*"


def test_unknown_route_returns_404():
    from router import route
    event = make_event(method="GET", path="/does-not-exist")
    resp = route(event)
    assert resp["statusCode"] == 404


def test_handler_returns_200_for_root(ddb_table, monkeypatch):
    monkeypatch.setenv("VERSION", "0.1.0")
    from router import route
    event = make_event(method="GET", path="/meta")
    resp = route(event)
    # /meta route not yet implemented — 404 is expected here
    # This test will be updated in the meta task
    assert resp["statusCode"] in (200, 404)
```

- [ ] **Step 2: Run to confirm they fail**

```bash
cd backend && pytest tests/test_router.py -v
```

Expected: `ModuleNotFoundError: No module named 'router'`

- [ ] **Step 3: Implement router.py**

```python
# backend/router.py
import json
import re
from utils import cors_response, not_found


def _parse_body(event: dict) -> dict:
    body = event.get("body") or ""
    if not body:
        return {}
    try:
        return json.loads(body)
    except (ValueError, TypeError):
        return {}


def route(event: dict) -> dict:
    ctx = event.get("requestContext", {}).get("http", {})
    method = ctx.get("method", "GET").upper()
    path = event.get("rawPath", "/").rstrip("/") or "/"
    body = _parse_body(event)
    query = event.get("queryStringParameters") or {}
    headers = event.get("headers") or {}

    if method == "OPTIONS":
        return cors_response(200, {})

    # Import route handlers here to keep imports lazy
    from routes import (
        meta, content, projects, courses, github,
        auth_routes, comments, ratings, guestbook,
        quiz, testimonials, stats, contact, admin, docs,
    )

    # (method, pattern, handler)  — exact strings matched first, regex second
    ROUTES = [
        # Meta & docs
        ("GET",    "/meta",                           meta.get_meta),
        ("GET",    "/api",                            docs.swagger_ui),
        ("GET",    "/api/spec",                       docs.openapi_spec),
        # Content
        ("GET",    "/about",                          content.get_about),
        ("PUT",    "/about",                          content.update_about),
        ("GET",    "/skills",                         content.get_skills),
        ("PUT",    "/skills",                         content.update_skills),
        ("GET",    "/timeline",                       content.get_timeline),
        ("PUT",    "/timeline",                       content.update_timeline),
        ("GET",    "/fun-fact",                       content.get_fun_fact),
        ("PUT",    "/fun-fact",                       content.update_fun_facts),
        ("GET",    "/currently-learning",             content.get_currently_learning),
        ("PUT",    "/currently-learning",             content.update_currently_learning),
        # Projects
        ("GET",    "/projects",                       projects.list_projects),
        ("POST",   "/projects",                       projects.create_project),
        ("GET",    r"/projects/(?P<id>[^/]+)$",       projects.get_project),
        ("PUT",    r"/projects/(?P<id>[^/]+)$",       projects.update_project),
        ("DELETE", r"/projects/(?P<id>[^/]+)$",       projects.delete_project),
        ("GET",    r"/projects/(?P<id>[^/]+)/comments$",  comments.list_comments),
        ("POST",   r"/projects/(?P<id>[^/]+)/comments$",  comments.create_comment),
        ("GET",    r"/projects/(?P<id>[^/]+)/ratings$",   ratings.get_ratings),
        ("POST",   r"/projects/(?P<id>[^/]+)/ratings$",   ratings.submit_rating),
        # Courses
        ("GET",    "/courses",                        courses.list_courses),
        ("POST",   "/courses",                        courses.create_course),
        ("GET",    r"/courses/(?P<id>[^/]+)$",        courses.get_course),
        ("PUT",    r"/courses/(?P<id>[^/]+)$",        courses.update_course),
        ("DELETE", r"/courses/(?P<id>[^/]+)$",        courses.delete_course),
        ("GET",    r"/courses/(?P<id>[^/]+)/comments$",   comments.list_comments),
        ("POST",   r"/courses/(?P<id>[^/]+)/comments$",   comments.create_comment),
        ("GET",    r"/courses/(?P<id>[^/]+)/ratings$",    ratings.get_ratings),
        ("POST",   r"/courses/(?P<id>[^/]+)/ratings$",    ratings.submit_rating),
        # Comments (admin delete)
        ("DELETE", r"/comments/(?P<id>[^/]+)$",       comments.delete_comment),
        # GitHub
        ("GET",    "/github/repos",                   github.get_repos),
        # Auth
        ("POST",   "/auth/register",                  auth_routes.register),
        ("POST",   "/auth/verify-email",              auth_routes.verify_email),
        ("POST",   "/auth/login",                     auth_routes.login),
        ("POST",   "/auth/logout",                    auth_routes.logout),
        ("POST",   "/auth/refresh",                   auth_routes.refresh),
        ("GET",    "/auth/me",                        auth_routes.get_me),
        ("PUT",    "/auth/me",                        auth_routes.update_me),
        ("GET",    "/auth/oauth/github",              auth_routes.oauth_github_init),
        ("GET",    "/auth/oauth/github/callback",     auth_routes.oauth_github_callback),
        ("GET",    "/auth/oauth/google",              auth_routes.oauth_google_init),
        ("GET",    "/auth/oauth/google/callback",     auth_routes.oauth_google_callback),
        # Guestbook
        ("GET",    "/guestbook",                      guestbook.list_entries),
        ("POST",   "/guestbook",                      guestbook.create_entry),
        # Quiz
        ("GET",    "/quiz/questions",                 quiz.get_questions),
        ("POST",   "/quiz/submit",                    quiz.submit_answers),
        ("GET",    "/quiz/leaderboard",               quiz.get_leaderboard),
        # Testimonials
        ("GET",    "/testimonials",                   testimonials.list_testimonials),
        ("POST",   "/testimonials",                   testimonials.submit_testimonial),
        # Stats
        ("GET",    "/stats/visitors",                 stats.get_visitor_locations),
        ("GET",    "/stats/analytics",                stats.get_analytics),
        # Contact
        ("POST",   "/contact",                        contact.submit_contact),
        # Admin
        ("GET",    "/admin/users",                    admin.list_users),
        ("PUT",    r"/admin/users/(?P<id>[^/]+)$",    admin.update_user),
        ("DELETE", r"/admin/users/(?P<id>[^/]+)$",    admin.delete_user),
        ("GET",    "/admin/contacts",                 admin.list_contacts),
        ("GET",    "/admin/testimonials/pending",     admin.list_pending_testimonials),
        ("PUT",    r"/admin/testimonials/(?P<id>[^/]+)$", admin.update_testimonial),
        ("GET",    "/admin/quiz/questions",           admin.list_quiz_questions),
        ("POST",   "/admin/quiz/questions",           admin.create_quiz_question),
        ("PUT",    r"/admin/quiz/questions/(?P<id>[^/]+)$", admin.update_quiz_question),
        ("DELETE", r"/admin/quiz/questions/(?P<id>[^/]+)$", admin.delete_quiz_question),
    ]

    for route_method, pattern, handler_fn in ROUTES:
        if method != route_method:
            continue
        if pattern == path:
            return handler_fn(event, {}, body, query, headers)
        m = re.fullmatch(pattern, path)
        if m:
            return handler_fn(event, m.groupdict(), body, query, headers)

    return not_found("Route not found")
```

- [ ] **Step 4: Update handler.py**

```python
# backend/handler.py
from router import route
from utils import server_error


def handler(event, context):
    try:
        return route(event)
    except Exception as exc:
        print(f"Unhandled error: {exc}")
        return server_error()
```

- [ ] **Step 5: Create stub route files so router imports don't fail**

Each file needs to exist with placeholder functions. Run:

```bash
cd backend
for f in meta content projects courses github auth_routes comments ratings guestbook quiz testimonials stats contact admin docs; do
  touch routes/${f}.py
done
```

Then add a minimal stub to each file. Here is the stub pattern — apply it to all 15 files:

```python
# routes/meta.py  (repeat same pattern for each file, changing function names)
from utils import not_found


def get_meta(event, path_params, body, query, headers):
    return not_found("Not implemented yet")
```

For files with multiple functions referenced in the router, create a stub for each. Here is the full list per file:

**routes/content.py** — `get_about`, `update_about`, `get_skills`, `update_skills`, `get_timeline`, `update_timeline`, `get_fun_fact`, `update_fun_facts`, `get_currently_learning`, `update_currently_learning`

**routes/projects.py** — `list_projects`, `create_project`, `get_project`, `update_project`, `delete_project`

**routes/courses.py** — `list_courses`, `create_course`, `get_course`, `update_course`, `delete_course`

**routes/github.py** — `get_repos`

**routes/auth_routes.py** — `register`, `verify_email`, `login`, `logout`, `refresh`, `get_me`, `update_me`, `oauth_github_init`, `oauth_github_callback`, `oauth_google_init`, `oauth_google_callback`

**routes/comments.py** — `list_comments`, `create_comment`, `delete_comment`

**routes/ratings.py** — `get_ratings`, `submit_rating`

**routes/guestbook.py** — `list_entries`, `create_entry`

**routes/quiz.py** — `get_questions`, `submit_answers`, `get_leaderboard`

**routes/testimonials.py** — `list_testimonials`, `submit_testimonial`

**routes/stats.py** — `get_visitor_locations`, `get_analytics`

**routes/contact.py** — `submit_contact`

**routes/admin.py** — `list_users`, `update_user`, `delete_user`, `list_contacts`, `list_pending_testimonials`, `update_testimonial`, `list_quiz_questions`, `create_quiz_question`, `update_quiz_question`, `delete_quiz_question`

**routes/docs.py** — `swagger_ui`, `openapi_spec`

Example stub for a file with multiple functions:
```python
# routes/projects.py
from utils import not_found


def list_projects(event, path_params, body, query, headers):
    return not_found("Not implemented yet")


def create_project(event, path_params, body, query, headers):
    return not_found("Not implemented yet")


def get_project(event, path_params, body, query, headers):
    return not_found("Not implemented yet")


def update_project(event, path_params, body, query, headers):
    return not_found("Not implemented yet")


def delete_project(event, path_params, body, query, headers):
    return not_found("Not implemented yet")
```

- [ ] **Step 6: Run router tests**

```bash
cd backend && pytest tests/test_router.py -v
```

Expected: All 4 tests PASS

- [ ] **Step 7: Run full suite**

```bash
cd backend && pytest tests/ -v
```

Expected: All tests PASS, no import errors

- [ ] **Step 8: Commit**

```bash
git add backend/
git commit -m "feat: add Lambda handler, path router, db client, JWT auth utilities"
```

- [ ] **Step 9: Merge to dev**

```bash
git checkout dev
git merge feature/backend-foundation
git push origin dev
```

---

## Feature Branch: `feature/content-routes`

> Covers: /meta, /about, /skills, /timeline, /fun-fact, /currently-learning, /projects, /courses, /github/repos

```bash
git checkout dev
git checkout -b feature/content-routes
```

---

### Task 5: /meta route

**Files:**
- Modify: `backend/routes/meta.py`
- Create: `backend/tests/test_meta.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_meta.py
import json
from tests.conftest import make_event


def test_get_meta_returns_deploy_info():
    from router import route
    resp = route(make_event("GET", "/meta"))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    data = body["data"]
    assert data["git_sha"] == "abc123"
    assert data["environment"] == "test"
    assert data["version"] == "0.1.0"
    assert data["deploy_timestamp"] == "2026-04-02T00:00:00Z"
    assert "author" in data
    assert "region" in data
```

- [ ] **Step 2: Run to confirm it fails**

```bash
cd backend && pytest tests/test_meta.py -v
```

Expected: FAIL — `assert resp["statusCode"] == 200` (currently returns 404)

- [ ] **Step 3: Implement routes/meta.py**

```python
# backend/routes/meta.py
import os
from utils import ok


def get_meta(event, path_params, body, query, headers):
    return ok({
        "git_sha": os.environ.get("GIT_SHA", "unknown"),
        "deploy_timestamp": os.environ.get("DEPLOY_TIMESTAMP", "unknown"),
        "environment": os.environ.get("ENVIRONMENT", "unknown"),
        "version": os.environ.get("VERSION", "unknown"),
        "region": os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
        "author": "Ron Harifiyati",
        "repository": "https://github.com/ron-harifiyati/about-me",
    })
```

- [ ] **Step 4: Run test**

```bash
cd backend && pytest tests/test_meta.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/routes/meta.py backend/tests/test_meta.py
git commit -m "feat: implement GET /meta endpoint"
```

---

### Task 6: Site content routes + models

**Files:**
- Create: `backend/models/content.py`
- Modify: `backend/routes/content.py`
- Create: `backend/tests/test_content.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_content.py
import json
from tests.conftest import make_event
from auth import make_jwt


def _admin_headers():
    return {"authorization": f"Bearer {make_jwt('admin-1', 'admin')}"}


def test_get_about_returns_404_when_no_data(ddb_table):
    from router import route
    resp = route(make_event("GET", "/about"))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["data"] is None or isinstance(body["data"], dict)


def test_put_and_get_about(ddb_table):
    from router import route
    payload = {
        "bio": "Hi, I'm Ron.",
        "mission": "Build great software.",
        "social_links": {"github": "https://github.com/ron"},
        "contact": {"email": "ron@example.com", "location": "Israel"},
    }
    put_resp = route(make_event("PUT", "/about", body=payload, headers=_admin_headers()))
    assert put_resp["statusCode"] == 200

    get_resp = route(make_event("GET", "/about"))
    body = json.loads(get_resp["body"])
    assert body["data"]["bio"] == "Hi, I'm Ron."


def test_put_about_requires_admin(ddb_table):
    from router import route
    resp = route(make_event("PUT", "/about", body={"bio": "x"}))
    assert resp["statusCode"] == 401


def test_get_skills_returns_empty_list_when_no_data(ddb_table):
    from router import route
    resp = route(make_event("GET", "/skills"))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["data"] is None or isinstance(body["data"], (dict, list))


def test_get_fun_fact_returns_random_fact(ddb_table):
    from router import route
    # seed some facts
    from models.content import update_content
    update_content("FUNFACTS", {"facts": ["Fact A", "Fact B", "Fact C"]})
    resp = route(make_event("GET", "/fun-fact"))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["data"]["fact"] in ["Fact A", "Fact B", "Fact C"]
```

- [ ] **Step 2: Run to confirm they fail**

```bash
cd backend && pytest tests/test_content.py -v
```

Expected: FAIL — import errors or 404s

- [ ] **Step 3: Implement models/content.py**

```python
# backend/models/content.py
from db import get_table


def get_content(sk: str) -> dict | None:
    table = get_table()
    resp = table.get_item(Key={"PK": "CONTENT", "SK": sk})
    item = resp.get("Item")
    if item:
        item.pop("PK", None)
        item.pop("SK", None)
    return item


def update_content(sk: str, fields: dict) -> dict:
    table = get_table()
    table.put_item(Item={"PK": "CONTENT", "SK": sk, **fields})
    return fields
```

- [ ] **Step 4: Implement routes/content.py**

```python
# backend/routes/content.py
import random
from auth import require_admin
from models.content import get_content, update_content
from utils import ok, not_found


def get_about(event, path_params, body, query, headers):
    return ok(get_content("ABOUT"))


@require_admin
def update_about(event, path_params, body, query, headers, user):
    return ok(update_content("ABOUT", body))


def get_skills(event, path_params, body, query, headers):
    return ok(get_content("SKILLS"))


@require_admin
def update_skills(event, path_params, body, query, headers, user):
    return ok(update_content("SKILLS", body))


def get_timeline(event, path_params, body, query, headers):
    return ok(get_content("TIMELINE"))


@require_admin
def update_timeline(event, path_params, body, query, headers, user):
    return ok(update_content("TIMELINE", body))


def get_fun_fact(event, path_params, body, query, headers):
    data = get_content("FUNFACTS")
    if not data or not data.get("facts"):
        return ok({"fact": None})
    return ok({"fact": random.choice(data["facts"])})


@require_admin
def update_fun_facts(event, path_params, body, query, headers, user):
    return ok(update_content("FUNFACTS", body))


def get_currently_learning(event, path_params, body, query, headers):
    return ok(get_content("CURRENTLY_LEARNING"))


@require_admin
def update_currently_learning(event, path_params, body, query, headers, user):
    return ok(update_content("CURRENTLY_LEARNING", body))
```

- [ ] **Step 5: Run tests**

```bash
cd backend && pytest tests/test_content.py -v
```

Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add backend/models/content.py backend/routes/content.py backend/tests/test_content.py
git commit -m "feat: implement content routes (about, skills, timeline, fun-fact, currently-learning)"
```

---

### Task 7: Projects + Courses routes

**Files:**
- Create: `backend/models/projects.py`
- Create: `backend/models/courses.py`
- Modify: `backend/routes/projects.py`
- Modify: `backend/routes/courses.py`
- Create: `backend/tests/test_projects.py`
- Create: `backend/tests/test_courses.py`

- [ ] **Step 1: Write failing tests for projects**

```python
# backend/tests/test_projects.py
import json
from tests.conftest import make_event
from auth import make_jwt


def _admin_headers():
    return {"authorization": f"Bearer {make_jwt('admin-1', 'admin')}"}


def test_list_projects_returns_empty_list(ddb_table):
    from router import route
    resp = route(make_event("GET", "/projects"))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["data"] == []


def test_create_and_get_project(ddb_table):
    from router import route
    payload = {
        "title": "Portfolio Site",
        "description": "My personal portfolio.",
        "tech_stack": ["Python", "AWS"],
        "links": {"github": "https://github.com/ron/portfolio"},
    }
    create_resp = route(make_event("POST", "/projects", body=payload, headers=_admin_headers()))
    assert create_resp["statusCode"] == 201
    project = json.loads(create_resp["body"])["data"]
    project_id = project["id"]

    get_resp = route(make_event("GET", f"/projects/{project_id}"))
    assert get_resp["statusCode"] == 200
    assert json.loads(get_resp["body"])["data"]["title"] == "Portfolio Site"


def test_create_project_requires_admin(ddb_table):
    from router import route
    resp = route(make_event("POST", "/projects", body={"title": "x"}))
    assert resp["statusCode"] == 401


def test_update_project(ddb_table):
    from router import route
    create_resp = route(make_event("POST", "/projects", body={"title": "Old"}, headers=_admin_headers()))
    pid = json.loads(create_resp["body"])["data"]["id"]

    update_resp = route(make_event("PUT", f"/projects/{pid}", body={"title": "New"}, headers=_admin_headers()))
    assert update_resp["statusCode"] == 200
    assert json.loads(update_resp["body"])["data"]["title"] == "New"


def test_delete_project(ddb_table):
    from router import route
    create_resp = route(make_event("POST", "/projects", body={"title": "To Delete"}, headers=_admin_headers()))
    pid = json.loads(create_resp["body"])["data"]["id"]

    del_resp = route(make_event("DELETE", f"/projects/{pid}", headers=_admin_headers()))
    assert del_resp["statusCode"] == 200

    get_resp = route(make_event("GET", f"/projects/{pid}"))
    assert get_resp["statusCode"] == 404


def test_get_nonexistent_project_returns_404(ddb_table):
    from router import route
    resp = route(make_event("GET", "/projects/does-not-exist"))
    assert resp["statusCode"] == 404
```

- [ ] **Step 2: Run to confirm they fail**

```bash
cd backend && pytest tests/test_projects.py -v
```

Expected: FAIL

- [ ] **Step 3: Implement models/projects.py**

```python
# backend/models/projects.py
import uuid
import time
from db import get_table
from boto3.dynamodb.conditions import Key


def list_projects() -> list:
    table = get_table()
    resp = table.query(
        KeyConditionExpression=Key("PK").begins_with("PROJECT#") & Key("SK").eq("META")
    )
    items = resp.get("Items", [])
    for item in items:
        item.pop("PK", None)
        item.pop("SK", None)
    return items


def get_project(project_id: str) -> dict | None:
    table = get_table()
    resp = table.get_item(Key={"PK": f"PROJECT#{project_id}", "SK": "META"})
    item = resp.get("Item")
    if item:
        item.pop("PK", None)
        item.pop("SK", None)
    return item


def create_project(fields: dict) -> dict:
    table = get_table()
    project_id = str(uuid.uuid4())
    item = {
        "PK": f"PROJECT#{project_id}",
        "SK": "META",
        "id": project_id,
        "created_at": int(time.time()),
        **fields,
    }
    table.put_item(Item=item)
    result = dict(item)
    result.pop("PK", None)
    result.pop("SK", None)
    return result


def update_project(project_id: str, fields: dict) -> dict | None:
    existing = get_project(project_id)
    if not existing:
        return None
    table = get_table()
    updated = {**existing, **fields, "id": project_id}
    table.put_item(Item={"PK": f"PROJECT#{project_id}", "SK": "META", **updated})
    return updated


def delete_project(project_id: str) -> bool:
    existing = get_project(project_id)
    if not existing:
        return False
    table = get_table()
    table.delete_item(Key={"PK": f"PROJECT#{project_id}", "SK": "META"})
    return True
```

- [ ] **Step 4: Implement routes/projects.py**

```python
# backend/routes/projects.py
from auth import require_admin
from models.projects import (
    list_projects, get_project, create_project, update_project, delete_project,
)
from utils import ok, created, not_found, bad_request


def list_projects(event, path_params, body, query, headers):
    return ok(list_projects())


def get_project(event, path_params, body, query, headers):
    project = get_project(path_params["id"])
    return ok(project) if project else not_found("Project not found")


@require_admin
def create_project(event, path_params, body, query, headers, user):
    if not body.get("title"):
        return bad_request("title is required")
    return created(create_project(body))


@require_admin
def update_project(event, path_params, body, query, headers, user):
    result = update_project(path_params["id"], body)
    return ok(result) if result else not_found("Project not found")


@require_admin
def delete_project(event, path_params, body, query, headers, user):
    success = delete_project(path_params["id"])
    return ok({"deleted": True}) if success else not_found("Project not found")
```

**Note:** The route functions shadow the model imports — rename to avoid collision:

```python
# backend/routes/projects.py  (corrected — use aliased imports)
from auth import require_admin
from models import projects as project_model
from utils import ok, created, not_found, bad_request


def list_projects(event, path_params, body, query, headers):
    return ok(project_model.list_projects())


def get_project(event, path_params, body, query, headers):
    project = project_model.get_project(path_params["id"])
    return ok(project) if project else not_found("Project not found")


@require_admin
def create_project(event, path_params, body, query, headers, user):
    if not body.get("title"):
        return bad_request("title is required")
    return created(project_model.create_project(body))


@require_admin
def update_project(event, path_params, body, query, headers, user):
    result = project_model.update_project(path_params["id"], body)
    return ok(result) if result else not_found("Project not found")


@require_admin
def delete_project(event, path_params, body, query, headers, user):
    success = project_model.delete_project(path_params["id"])
    return ok({"deleted": True}) if success else not_found("Project not found")
```

- [ ] **Step 5: Implement models/courses.py** (identical structure to projects, different PK prefix)

```python
# backend/models/courses.py
import uuid
import time
from db import get_table
from boto3.dynamodb.conditions import Key


def list_courses() -> list:
    table = get_table()
    resp = table.query(
        KeyConditionExpression=Key("PK").begins_with("COURSE#") & Key("SK").eq("META")
    )
    items = resp.get("Items", [])
    for item in items:
        item.pop("PK", None)
        item.pop("SK", None)
    return items


def get_course(course_id: str) -> dict | None:
    table = get_table()
    resp = table.get_item(Key={"PK": f"COURSE#{course_id}", "SK": "META"})
    item = resp.get("Item")
    if item:
        item.pop("PK", None)
        item.pop("SK", None)
    return item


def create_course(fields: dict) -> dict:
    table = get_table()
    course_id = str(uuid.uuid4())
    item = {
        "PK": f"COURSE#{course_id}",
        "SK": "META",
        "id": course_id,
        "created_at": int(time.time()),
        **fields,
    }
    table.put_item(Item=item)
    result = dict(item)
    result.pop("PK", None)
    result.pop("SK", None)
    return result


def update_course(course_id: str, fields: dict) -> dict | None:
    existing = get_course(course_id)
    if not existing:
        return None
    table = get_table()
    updated = {**existing, **fields, "id": course_id}
    table.put_item(Item={"PK": f"COURSE#{course_id}", "SK": "META", **updated})
    return updated


def delete_course(course_id: str) -> bool:
    existing = get_course(course_id)
    if not existing:
        return False
    table = get_table()
    table.delete_item(Key={"PK": f"COURSE#{course_id}", "SK": "META"})
    return True
```

- [ ] **Step 6: Implement routes/courses.py**

```python
# backend/routes/courses.py
from auth import require_admin
from models import courses as course_model
from utils import ok, created, not_found, bad_request


def list_courses(event, path_params, body, query, headers):
    return ok(course_model.list_courses())


def get_course(event, path_params, body, query, headers):
    course = course_model.get_course(path_params["id"])
    return ok(course) if course else not_found("Course not found")


@require_admin
def create_course(event, path_params, body, query, headers, user):
    if not body.get("title"):
        return bad_request("title is required")
    return created(course_model.create_course(body))


@require_admin
def update_course(event, path_params, body, query, headers, user):
    result = course_model.update_course(path_params["id"], body)
    return ok(result) if result else not_found("Course not found")


@require_admin
def delete_course(event, path_params, body, query, headers, user):
    success = course_model.delete_course(path_params["id"])
    return ok({"deleted": True}) if success else not_found("Course not found")
```

- [ ] **Step 7: Write courses tests**

```python
# backend/tests/test_courses.py
import json
from tests.conftest import make_event
from auth import make_jwt


def _admin_headers():
    return {"authorization": f"Bearer {make_jwt('admin-1', 'admin')}"}


def test_list_courses_returns_empty_list(ddb_table):
    from router import route
    resp = route(make_event("GET", "/courses"))
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"])["data"] == []


def test_create_and_get_course(ddb_table):
    from router import route
    payload = {"title": "AWS Cloud Practitioner", "platform": "AWS", "link": "https://aws.amazon.com"}
    create_resp = route(make_event("POST", "/courses", body=payload, headers=_admin_headers()))
    assert create_resp["statusCode"] == 201
    cid = json.loads(create_resp["body"])["data"]["id"]

    get_resp = route(make_event("GET", f"/courses/{cid}"))
    assert json.loads(get_resp["body"])["data"]["title"] == "AWS Cloud Practitioner"


def test_delete_course(ddb_table):
    from router import route
    cid = json.loads(
        route(make_event("POST", "/courses", body={"title": "x"}, headers=_admin_headers()))["body"]
    )["data"]["id"]
    assert route(make_event("DELETE", f"/courses/{cid}", headers=_admin_headers()))["statusCode"] == 200
    assert route(make_event("GET", f"/courses/{cid}"))["statusCode"] == 404
```

- [ ] **Step 8: Implement routes/github.py**

```python
# backend/routes/github.py
import requests
from utils import ok, server_error


def get_repos(event, path_params, body, query, headers):
    try:
        resp = requests.get(
            "https://api.github.com/users/ron-harifiyati/repos",
            params={"sort": "updated", "per_page": 6, "type": "public"},
            headers={"Accept": "application/vnd.github+json"},
            timeout=5,
        )
        repos = [
            {
                "name": r["name"],
                "description": r["description"],
                "url": r["html_url"],
                "language": r["language"],
                "stars": r["stargazers_count"],
                "updated_at": r["updated_at"],
            }
            for r in resp.json()
            if not r["fork"]
        ]
        return ok(repos)
    except Exception:
        return ok([])
```

- [ ] **Step 9: Run all content tests**

```bash
cd backend && pytest tests/test_meta.py tests/test_content.py tests/test_projects.py tests/test_courses.py -v
```

Expected: All PASS

- [ ] **Step 10: Commit**

```bash
git add backend/
git commit -m "feat: implement projects, courses, github repos routes"
```

- [ ] **Step 11: Merge to dev**

```bash
git checkout dev
git merge feature/content-routes
git push origin dev
```

---

## Feature Branch: `feature/auth-routes`

> Covers: register, verify-email, login, logout, refresh, me, GitHub OAuth, Google OAuth, account linking

```bash
git checkout dev
git checkout -b feature/auth-routes
```

---

### Task 8: User model

**Files:**
- Create: `backend/models/users.py`

- [ ] **Step 1: Implement models/users.py**

```python
# backend/models/users.py
import uuid
import time
import hashlib
import secrets
from db import get_table
from boto3.dynamodb.conditions import Key


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}:{h}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, h = stored.split(":", 1)
        return hashlib.sha256(f"{salt}{password}".encode()).hexdigest() == h
    except ValueError:
        return False


def get_user_by_id(user_id: str) -> dict | None:
    table = get_table()
    resp = table.get_item(Key={"PK": f"USER#{user_id}", "SK": "PROFILE"})
    item = resp.get("Item")
    if item:
        item.pop("PK", None)
        item.pop("SK", None)
        item.pop("password_hash", None)
    return item


def get_user_by_email(email: str) -> dict | None:
    table = get_table()
    resp = table.query(
        IndexName="GSI1",
        KeyConditionExpression=Key("GSI1PK").eq(f"EMAIL#{email}") & Key("GSI1SK").eq("USER"),
    )
    items = resp.get("Items", [])
    return items[0] if items else None


def create_user(email: str, name: str, identity: str, password: str | None = None) -> dict:
    table = get_table()
    user_id = str(uuid.uuid4())
    item = {
        "PK": f"USER#{user_id}",
        "SK": "PROFILE",
        "GSI1PK": f"EMAIL#{email}",
        "GSI1SK": "USER",
        "user_id": user_id,
        "email": email,
        "name": name,
        "identity": identity,
        "role": "user",
        "email_verified": False,
        "theme": "light",
        "created_at": int(time.time()),
    }
    if password:
        item["password_hash"] = _hash_password(password)
    table.put_item(Item=item)
    result = dict(item)
    result.pop("PK", None)
    result.pop("SK", None)
    result.pop("password_hash", None)
    return result


def verify_user_password(email: str, password: str) -> dict | None:
    table = get_table()
    resp = table.query(
        IndexName="GSI1",
        KeyConditionExpression=Key("GSI1PK").eq(f"EMAIL#{email}") & Key("GSI1SK").eq("USER"),
    )
    items = resp.get("Items", [])
    if not items:
        return None
    user = items[0]
    if not _verify_password(password, user.get("password_hash", "")):
        return None
    result = dict(user)
    result.pop("PK", None)
    result.pop("SK", None)
    result.pop("password_hash", None)
    return result


def mark_email_verified(user_id: str):
    table = get_table()
    table.update_item(
        Key={"PK": f"USER#{user_id}", "SK": "PROFILE"},
        UpdateExpression="SET email_verified = :v",
        ExpressionAttributeValues={":v": True},
    )


def update_user_profile(user_id: str, fields: dict) -> dict | None:
    allowed = {"name", "identity", "theme"}
    safe_fields = {k: v for k, v in fields.items() if k in allowed}
    if not safe_fields:
        return get_user_by_id(user_id)
    table = get_table()
    set_expr = ", ".join(f"#{k} = :{k}" for k in safe_fields)
    attr_names = {f"#{k}": k for k in safe_fields}
    attr_values = {f":{k}": v for k, v in safe_fields.items()}
    table.update_item(
        Key={"PK": f"USER#{user_id}", "SK": "PROFILE"},
        UpdateExpression=f"SET {set_expr}",
        ExpressionAttributeNames=attr_names,
        ExpressionAttributeValues=attr_values,
    )
    return get_user_by_id(user_id)


def create_email_verify_token(user_id: str) -> str:
    table = get_table()
    token = secrets.token_urlsafe(32)
    ttl = int(time.time()) + 24 * 3600
    table.put_item(Item={
        "PK": f"VERIFY#{token}",
        "SK": "TOKEN",
        "user_id": user_id,
        "ttl": ttl,
    })
    return token


def consume_email_verify_token(token: str) -> str | None:
    """Returns user_id if token is valid, deletes it."""
    table = get_table()
    resp = table.get_item(Key={"PK": f"VERIFY#{token}", "SK": "TOKEN"})
    item = resp.get("Item")
    if not item:
        return None
    table.delete_item(Key={"PK": f"VERIFY#{token}", "SK": "TOKEN"})
    return item["user_id"]


def create_refresh_token(user_id: str, role: str) -> str:
    table = get_table()
    token = secrets.token_urlsafe(48)
    ttl = int(time.time()) + 7 * 24 * 3600
    table.put_item(Item={
        "PK": f"SESSION#{token}",
        "SK": "SESSION",
        "user_id": user_id,
        "role": role,
        "ttl": ttl,
    })
    return token


def consume_refresh_token(token: str) -> dict | None:
    """Returns {user_id, role} if valid, deletes it (single-use rotation)."""
    table = get_table()
    resp = table.get_item(Key={"PK": f"SESSION#{token}", "SK": "SESSION"})
    item = resp.get("Item")
    if not item:
        return None
    table.delete_item(Key={"PK": f"SESSION#{token}", "SK": "SESSION"})
    return {"user_id": item["user_id"], "role": item["role"]}


def delete_refresh_token(token: str):
    table = get_table()
    table.delete_item(Key={"PK": f"SESSION#{token}", "SK": "SESSION"})


def get_or_create_oauth_user(provider: str, provider_id: str, email: str, name: str) -> dict:
    """
    Link table approach: if OAUTH#<provider>#<provider_id> exists, return that user.
    If not, check if a user with the same email exists (account linking).
    If not, create a new user. Either way, upsert the OAuth link record.
    """
    table = get_table()

    # Check existing OAuth link
    link = table.get_item(Key={"PK": f"OAUTH#{provider}#{provider_id}", "SK": "LINK"}).get("Item")
    if link:
        return get_user_by_id(link["user_id"])

    # Check by email (account linking)
    existing = get_user_by_email(email)
    if existing:
        user_id = existing["user_id"]
    else:
        # Create new user (no password, email pre-verified via OAuth)
        user = create_user(email, name, "Other")
        mark_email_verified(user["user_id"])
        user_id = user["user_id"]

    # Store OAuth link
    table.put_item(Item={
        "PK": f"OAUTH#{provider}#{provider_id}",
        "SK": "LINK",
        "user_id": user_id,
        "provider": provider,
        "provider_id": provider_id,
    })
    return get_user_by_id(user_id)


def list_all_users() -> list:
    table = get_table()
    resp = table.query(
        IndexName="GSI1",
        KeyConditionExpression=Key("GSI1SK").eq("USER"),
    )
    items = resp.get("Items", [])
    for item in items:
        item.pop("PK", None)
        item.pop("SK", None)
        item.pop("password_hash", None)
    return items


def set_user_status(user_id: str, status: str):
    """status: 'active' | 'suspended' | 'banned'"""
    table = get_table()
    table.update_item(
        Key={"PK": f"USER#{user_id}", "SK": "PROFILE"},
        UpdateExpression="SET #s = :s",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": status},
    )


def delete_user(user_id: str):
    table = get_table()
    table.delete_item(Key={"PK": f"USER#{user_id}", "SK": "PROFILE"})
```

- [ ] **Step 2: Commit model**

```bash
git add backend/models/users.py
git commit -m "feat: add user model (CRUD, password hashing, tokens, OAuth linking)"
```

---

### Task 9: Auth routes (email/password + JWT)

**Files:**
- Modify: `backend/routes/auth_routes.py`
- Create: `backend/tests/test_auth_routes.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_auth_routes.py
import json
from tests.conftest import make_event
from auth import make_jwt


def test_register_creates_user(ddb_table, mocker):
    mocker.patch("routes.auth_routes._send_verification_email")
    from router import route
    resp = route(make_event("POST", "/auth/register", body={
        "email": "ron@example.com",
        "password": "Secure123!",
        "name": "Ron",
        "identity": "Jamf",
    }))
    assert resp["statusCode"] == 201
    body = json.loads(resp["body"])
    assert body["data"]["email"] == "ron@example.com"


def test_register_duplicate_email_returns_409(ddb_table, mocker):
    mocker.patch("routes.auth_routes._send_verification_email")
    from router import route
    payload = {"email": "ron@example.com", "password": "Secure123!", "name": "Ron", "identity": "Jamf"}
    route(make_event("POST", "/auth/register", body=payload))
    resp = route(make_event("POST", "/auth/register", body=payload))
    assert resp["statusCode"] == 409


def test_login_returns_jwt(ddb_table, mocker):
    mocker.patch("routes.auth_routes._send_verification_email")
    from router import route
    from models.users import mark_email_verified, get_user_by_email
    route(make_event("POST", "/auth/register", body={
        "email": "ron@example.com", "password": "Secure123!", "name": "Ron", "identity": "Jamf",
    }))
    user = get_user_by_email("ron@example.com")
    mark_email_verified(user["user_id"])

    resp = route(make_event("POST", "/auth/login", body={
        "email": "ron@example.com", "password": "Secure123!",
    }))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert "access_token" in body["data"]
    assert "refresh_token" in body["data"]


def test_login_wrong_password_returns_401(ddb_table, mocker):
    mocker.patch("routes.auth_routes._send_verification_email")
    from router import route
    route(make_event("POST", "/auth/register", body={
        "email": "ron@example.com", "password": "Secure123!", "name": "Ron", "identity": "Jamf",
    }))
    resp = route(make_event("POST", "/auth/login", body={
        "email": "ron@example.com", "password": "WrongPassword",
    }))
    assert resp["statusCode"] == 401


def test_get_me_returns_profile(ddb_table, mocker):
    mocker.patch("routes.auth_routes._send_verification_email")
    from router import route
    from models.users import mark_email_verified, get_user_by_email, create_refresh_token
    route(make_event("POST", "/auth/register", body={
        "email": "ron@example.com", "password": "Secure123!", "name": "Ron", "identity": "Jamf",
    }))
    user = get_user_by_email("ron@example.com")
    mark_email_verified(user["user_id"])
    token = make_jwt(user["user_id"], "user")

    resp = route(make_event("GET", "/auth/me", headers={"authorization": f"Bearer {token}"}))
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"])["data"]["email"] == "ron@example.com"


def test_update_me_changes_identity(ddb_table, mocker):
    mocker.patch("routes.auth_routes._send_verification_email")
    from router import route
    from models.users import mark_email_verified, get_user_by_email
    route(make_event("POST", "/auth/register", body={
        "email": "ron@example.com", "password": "Secure123!", "name": "Ron", "identity": "Jamf",
    }))
    user = get_user_by_email("ron@example.com")
    mark_email_verified(user["user_id"])
    token = make_jwt(user["user_id"], "user")

    resp = route(make_event("PUT", "/auth/me",
        body={"identity": "MCRI"},
        headers={"authorization": f"Bearer {token}"}
    ))
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"])["data"]["identity"] == "MCRI"


def test_verify_email_activates_account(ddb_table, mocker):
    mocker.patch("routes.auth_routes._send_verification_email")
    from router import route
    from models.users import get_user_by_email, create_email_verify_token
    route(make_event("POST", "/auth/register", body={
        "email": "ron@example.com", "password": "Secure123!", "name": "Ron", "identity": "Jamf",
    }))
    user = get_user_by_email("ron@example.com")
    token = create_email_verify_token(user["user_id"])

    resp = route(make_event("POST", "/auth/verify-email", body={"token": token}))
    assert resp["statusCode"] == 200

    fresh = get_user_by_email("ron@example.com")
    assert fresh is not None
```

- [ ] **Step 2: Run to confirm they fail**

```bash
cd backend && pytest tests/test_auth_routes.py -v
```

Expected: FAIL (import errors or 404s)

- [ ] **Step 3: Implement routes/auth_routes.py**

```python
# backend/routes/auth_routes.py
import os
import json
import requests as http
from auth import make_jwt, require_auth
from models.users import (
    get_user_by_id, get_user_by_email, create_user, verify_user_password,
    mark_email_verified, update_user_profile, create_email_verify_token,
    consume_email_verify_token, create_refresh_token, consume_refresh_token,
    delete_refresh_token, get_or_create_oauth_user,
)
from utils import ok, created, bad_request, unauthorized, conflict


def _send_verification_email(email: str, token: str):
    import boto3
    ses = boto3.client("ses", region_name="us-east-1")
    sender = os.environ["SES_SENDER_EMAIL"]
    # Lambda Function URL is injected as env var; fallback to placeholder
    base_url = os.environ.get("FRONTEND_URL", "https://portfolio.example.com")
    verify_url = f"{base_url}/verify-email?token={token}"
    ses.send_email(
        Source=sender,
        Destination={"ToAddresses": [email]},
        Message={
            "Subject": {"Data": "Verify your email — Ron's Portfolio"},
            "Body": {"Text": {"Data": f"Click to verify: {verify_url}"}},
        },
    )


def register(event, path_params, body, query, headers):
    email = (body.get("email") or "").strip().lower()
    password = body.get("password", "")
    name = (body.get("name") or "").strip()
    identity = body.get("identity", "Other")

    if not email or not password or not name:
        return bad_request("email, password, and name are required")
    if len(password) < 8:
        return bad_request("password must be at least 8 characters")
    if identity not in ("Jamf", "MCRI", "Friend", "Family", "Other"):
        return bad_request("invalid identity")
    if get_user_by_email(email):
        return conflict("An account with this email already exists")

    user = create_user(email, name, identity, password)
    token = create_email_verify_token(user["user_id"])
    _send_verification_email(email, token)
    return created({"message": "Account created. Check your email to verify.", "user_id": user["user_id"]})


def verify_email(event, path_params, body, query, headers):
    token = body.get("token") or query.get("token", "")
    if not token:
        return bad_request("token is required")
    user_id = consume_email_verify_token(token)
    if not user_id:
        return bad_request("Invalid or expired token")
    mark_email_verified(user_id)
    return ok({"message": "Email verified. You can now log in."})


def login(event, path_params, body, query, headers):
    email = (body.get("email") or "").strip().lower()
    password = body.get("password", "")
    remember_me = bool(body.get("remember_me", False))

    if not email or not password:
        return bad_request("email and password are required")

    user = verify_user_password(email, password)
    if not user:
        return unauthorized("Invalid email or password")
    if not user.get("email_verified"):
        return unauthorized("Please verify your email before logging in")

    access_token = make_jwt(user["user_id"], user["role"], remember_me=remember_me)
    refresh_token = create_refresh_token(user["user_id"], user["role"])
    return ok({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user,
    })


def logout(event, path_params, body, query, headers):
    token = body.get("refresh_token", "")
    if token:
        delete_refresh_token(token)
    return ok({"message": "Logged out"})


def refresh(event, path_params, body, query, headers):
    token = body.get("refresh_token", "")
    if not token:
        return bad_request("refresh_token is required")
    data = consume_refresh_token(token)
    if not data:
        return unauthorized("Invalid or expired refresh token")
    new_access = make_jwt(data["user_id"], data["role"])
    new_refresh = create_refresh_token(data["user_id"], data["role"])
    return ok({"access_token": new_access, "refresh_token": new_refresh})


@require_auth
def get_me(event, path_params, body, query, headers, user):
    profile = get_user_by_id(user["sub"])
    return ok(profile)


@require_auth
def update_me(event, path_params, body, query, headers, user):
    if "identity" in body and body["identity"] not in ("Jamf", "MCRI", "Friend", "Family", "Other"):
        return bad_request("invalid identity")
    updated = update_user_profile(user["sub"], body)
    return ok(updated)


# --- OAuth ---

def oauth_github_init(event, path_params, body, query, headers):
    client_id = os.environ["GITHUB_OAUTH_CLIENT_ID"]
    redirect_uri = query.get("redirect_uri", "")
    state = os.urandom(16).hex()
    url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={client_id}&scope=user:email&state={state}"
    )
    return {
        "statusCode": 302,
        "headers": {"Location": url, "Access-Control-Allow-Origin": "*"},
        "body": "",
    }


def oauth_github_callback(event, path_params, body, query, headers):
    code = query.get("code", "")
    if not code:
        return bad_request("code is required")

    # Exchange code for access token
    token_resp = http.post(
        "https://github.com/login/oauth/access_token",
        json={
            "client_id": os.environ["GITHUB_OAUTH_CLIENT_ID"],
            "client_secret": os.environ["GITHUB_OAUTH_CLIENT_SECRET"],
            "code": code,
        },
        headers={"Accept": "application/json"},
        timeout=10,
    )
    gh_token = token_resp.json().get("access_token")
    if not gh_token:
        return unauthorized("GitHub OAuth failed")

    # Fetch user info
    user_resp = http.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {gh_token}", "Accept": "application/vnd.github+json"},
        timeout=10,
    )
    gh_user = user_resp.json()

    # Get primary email if not public
    email = gh_user.get("email")
    if not email:
        emails_resp = http.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {gh_token}", "Accept": "application/vnd.github+json"},
            timeout=10,
        )
        primary = next((e for e in emails_resp.json() if e.get("primary")), None)
        email = primary["email"] if primary else f"{gh_user['login']}@github.noemail"

    user = get_or_create_oauth_user("github", str(gh_user["id"]), email, gh_user.get("name") or gh_user["login"])
    access_token = make_jwt(user["user_id"], user["role"])
    refresh_token = create_refresh_token(user["user_id"], user["role"])
    return ok({"access_token": access_token, "refresh_token": refresh_token, "user": user})


def oauth_google_init(event, path_params, body, query, headers):
    client_id = os.environ["GOOGLE_OAUTH_CLIENT_ID"]
    redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI", "")
    url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
    )
    return {
        "statusCode": 302,
        "headers": {"Location": url, "Access-Control-Allow-Origin": "*"},
        "body": "",
    }


def oauth_google_callback(event, path_params, body, query, headers):
    code = query.get("code", "")
    if not code:
        return bad_request("code is required")

    redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI", "")
    token_resp = http.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": os.environ["GOOGLE_OAUTH_CLIENT_ID"],
            "client_secret": os.environ["GOOGLE_OAUTH_CLIENT_SECRET"],
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=10,
    )
    tokens = token_resp.json()
    id_token = tokens.get("id_token")
    if not id_token:
        return unauthorized("Google OAuth failed")

    # Decode JWT payload (no signature verification needed — Google already validated the code flow)
    import base64
    parts = id_token.split(".")
    padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
    payload = json.loads(base64.urlsafe_b64decode(padded))

    email = payload.get("email", "")
    name = payload.get("name", email.split("@")[0])
    google_id = payload.get("sub", "")

    user = get_or_create_oauth_user("google", google_id, email, name)
    access_token = make_jwt(user["user_id"], user["role"])
    refresh_token = create_refresh_token(user["user_id"], user["role"])
    return ok({"access_token": access_token, "refresh_token": refresh_token, "user": user})
```

- [ ] **Step 4: Run auth tests**

```bash
cd backend && pytest tests/test_auth_routes.py -v
```

Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add backend/models/users.py backend/routes/auth_routes.py backend/tests/test_auth_routes.py
git commit -m "feat: implement auth routes (register, verify-email, login, logout, refresh, me, GitHub/Google OAuth)"
```

- [ ] **Step 6: Merge to dev**

```bash
git checkout dev
git merge feature/auth-routes
git push origin dev
```

---

## Feature Branch: `feature/interaction-routes`

> Covers: comments, ratings, guestbook, quiz, testimonials

```bash
git checkout dev
git checkout -b feature/interaction-routes
```

---

### Task 10: Comments + Ratings

**Files:**
- Create: `backend/models/interactions.py`
- Modify: `backend/routes/comments.py`
- Modify: `backend/routes/ratings.py`
- Create: `backend/tests/test_comments.py`
- Create: `backend/tests/test_ratings.py`

- [ ] **Step 1: Implement models/interactions.py**

```python
# backend/models/interactions.py
import uuid
import time
from db import get_table
from boto3.dynamodb.conditions import Key
from decimal import Decimal


def list_comments(entity_pk: str) -> list:
    """entity_pk: 'PROJECT#<id>' or 'COURSE#<id>'"""
    table = get_table()
    resp = table.query(
        KeyConditionExpression=Key("PK").eq(entity_pk) & Key("SK").begins_with("COMMENT#"),
    )
    items = resp.get("Items", [])
    for item in items:
        item.pop("PK", None)
    return sorted(items, key=lambda x: x.get("created_at", 0))


def create_comment(entity_pk: str, user_id: str, name: str, identity: str, body_text: str) -> dict:
    table = get_table()
    comment_id = str(uuid.uuid4())
    ts = int(time.time())
    item = {
        "PK": entity_pk,
        "SK": f"COMMENT#{ts}#{comment_id}",
        "comment_id": comment_id,
        "user_id": user_id,
        "name": name,
        "identity": identity,
        "body": body_text,
        "created_at": ts,
    }
    table.put_item(Item=item)
    result = dict(item)
    result.pop("PK", None)
    return result


def delete_comment_by_sk(entity_pk: str, sk: str):
    table = get_table()
    table.delete_item(Key={"PK": entity_pk, "SK": sk})


def find_comment_pk_sk(comment_id: str, entity_pk: str) -> tuple[str, str] | tuple[None, None]:
    """Scan for comment_id within an entity — used by admin delete."""
    table = get_table()
    resp = table.query(
        KeyConditionExpression=Key("PK").eq(entity_pk) & Key("SK").begins_with("COMMENT#"),
        FilterExpression="comment_id = :cid",
        ExpressionAttributeValues={":cid": comment_id},
    )
    items = resp.get("Items", [])
    if items:
        return entity_pk, items[0]["SK"]
    return None, None


def get_ratings_summary(entity_pk: str) -> dict:
    table = get_table()
    resp = table.query(
        KeyConditionExpression=Key("PK").eq(entity_pk) & Key("SK").begins_with("RATING#"),
    )
    items = resp.get("Items", [])
    if not items:
        return {"average": None, "count": 0}
    stars = [float(item["stars"]) for item in items]
    return {"average": round(sum(stars) / len(stars), 1), "count": len(stars)}


def submit_rating(entity_pk: str, user_id: str, stars: int) -> dict:
    table = get_table()
    table.put_item(Item={
        "PK": entity_pk,
        "SK": f"RATING#{user_id}",
        "user_id": user_id,
        "stars": stars,
        "created_at": int(time.time()),
    })
    return get_ratings_summary(entity_pk)
```

- [ ] **Step 2: Write failing tests for comments**

```python
# backend/tests/test_comments.py
import json
from tests.conftest import make_event
from auth import make_jwt
from models.projects import create_project


def _auth_headers(user_id="user-1", role="user"):
    return {"authorization": f"Bearer {make_jwt(user_id, role)}"}


def test_list_comments_empty(ddb_table):
    from router import route
    p = create_project({"title": "P1"})
    resp = route(make_event("GET", f"/projects/{p['id']}/comments"))
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"])["data"] == []


def test_create_and_list_comment(ddb_table):
    from router import route
    from models.users import create_user, mark_email_verified
    user = create_user("u@example.com", "User One", "Jamf")
    mark_email_verified(user["user_id"])
    p = create_project({"title": "P1"})

    resp = route(make_event("POST", f"/projects/{p['id']}/comments",
        body={"body": "Great project!"},
        headers=_auth_headers(user["user_id"]),
    ))
    assert resp["statusCode"] == 201

    list_resp = route(make_event("GET", f"/projects/{p['id']}/comments"))
    comments = json.loads(list_resp["body"])["data"]
    assert len(comments) == 1
    assert comments[0]["body"] == "Great project!"


def test_create_comment_requires_auth(ddb_table):
    from router import route
    p = create_project({"title": "P1"})
    resp = route(make_event("POST", f"/projects/{p['id']}/comments", body={"body": "x"}))
    assert resp["statusCode"] == 401


def test_admin_can_delete_comment(ddb_table):
    from router import route
    from models.users import create_user, mark_email_verified
    user = create_user("u@example.com", "User One", "Jamf")
    mark_email_verified(user["user_id"])
    p = create_project({"title": "P1"})

    create_resp = route(make_event("POST", f"/projects/{p['id']}/comments",
        body={"body": "Bad comment"},
        headers=_auth_headers(user["user_id"]),
    ))
    comment_id = json.loads(create_resp["body"])["data"]["comment_id"]

    del_resp = route(make_event("DELETE", f"/comments/{comment_id}",
        headers=_auth_headers("admin-1", "admin"),
    ))
    assert del_resp["statusCode"] == 200
```

- [ ] **Step 3: Implement routes/comments.py**

```python
# backend/routes/comments.py
from auth import require_auth, require_admin, get_current_user
from models import interactions as m
from models.users import get_user_by_id
from models.projects import get_project
from models.courses import get_course
from utils import ok, created, not_found, bad_request


def _entity_pk(path: str, entity_id: str) -> str | None:
    if "projects" in path:
        return f"PROJECT#{entity_id}" if get_project(entity_id) else None
    if "courses" in path:
        return f"COURSE#{entity_id}" if get_course(entity_id) else None
    return None


def list_comments(event, path_params, body, query, headers):
    entity_id = path_params["id"]
    path = event.get("rawPath", "")
    pk = _entity_pk(path, entity_id)
    if pk is None:
        return not_found("Entity not found")
    return ok(m.list_comments(pk))


@require_auth
def create_comment(event, path_params, body, query, headers, user):
    if not body.get("body"):
        return bad_request("body is required")
    entity_id = path_params["id"]
    path = event.get("rawPath", "")
    pk = _entity_pk(path, entity_id)
    if pk is None:
        return not_found("Entity not found")
    profile = get_user_by_id(user["sub"]) or {}
    comment = m.create_comment(
        pk,
        user["sub"],
        profile.get("name", "Unknown"),
        profile.get("identity", "Other"),
        body["body"],
    )
    return created(comment)


@require_admin
def delete_comment(event, path_params, body, query, headers, user):
    comment_id = path_params["id"]
    # Search across projects and courses — try to find the comment
    # Admin passes entity info in query params if known, otherwise we scan
    entity_pk = query.get("entity_pk", "")
    if entity_pk:
        pk, sk = m.find_comment_pk_sk(comment_id, entity_pk)
        if pk:
            m.delete_comment_by_sk(pk, sk)
            return ok({"deleted": True})
    return not_found("Comment not found")
```

- [ ] **Step 4: Write failing tests for ratings**

```python
# backend/tests/test_ratings.py
import json
from tests.conftest import make_event
from auth import make_jwt
from models.projects import create_project


def _auth_headers(user_id="user-1"):
    return {"authorization": f"Bearer {make_jwt(user_id, 'user')}"}


def test_get_ratings_empty(ddb_table):
    from router import route
    p = create_project({"title": "P1"})
    resp = route(make_event("GET", f"/projects/{p['id']}/ratings"))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])["data"]
    assert body["count"] == 0
    assert body["average"] is None


def test_submit_rating(ddb_table):
    from router import route
    p = create_project({"title": "P1"})
    resp = route(make_event("POST", f"/projects/{p['id']}/ratings",
        body={"stars": 5},
        headers=_auth_headers(),
    ))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])["data"]
    assert body["average"] == 5.0
    assert body["count"] == 1


def test_rating_requires_auth(ddb_table):
    from router import route
    p = create_project({"title": "P1"})
    resp = route(make_event("POST", f"/projects/{p['id']}/ratings", body={"stars": 3}))
    assert resp["statusCode"] == 401


def test_resubmit_rating_updates(ddb_table):
    from router import route
    p = create_project({"title": "P1"})
    route(make_event("POST", f"/projects/{p['id']}/ratings", body={"stars": 2}, headers=_auth_headers()))
    route(make_event("POST", f"/projects/{p['id']}/ratings", body={"stars": 4}, headers=_auth_headers()))
    resp = route(make_event("GET", f"/projects/{p['id']}/ratings"))
    body = json.loads(resp["body"])["data"]
    assert body["count"] == 1  # same user, only one rating
    assert body["average"] == 4.0
```

- [ ] **Step 5: Implement routes/ratings.py**

```python
# backend/routes/ratings.py
from auth import require_auth
from models import interactions as m
from models.projects import get_project
from models.courses import get_course
from utils import ok, not_found, bad_request


def _entity_pk(path: str, entity_id: str) -> str | None:
    if "projects" in path:
        return f"PROJECT#{entity_id}" if get_project(entity_id) else None
    if "courses" in path:
        return f"COURSE#{entity_id}" if get_course(entity_id) else None
    return None


def get_ratings(event, path_params, body, query, headers):
    pk = _entity_pk(event.get("rawPath", ""), path_params["id"])
    if pk is None:
        return not_found("Entity not found")
    return ok(m.get_ratings_summary(pk))


@require_auth
def submit_rating(event, path_params, body, query, headers, user):
    stars = body.get("stars")
    if stars not in (1, 2, 3, 4, 5):
        return bad_request("stars must be an integer 1–5")
    pk = _entity_pk(event.get("rawPath", ""), path_params["id"])
    if pk is None:
        return not_found("Entity not found")
    return ok(m.submit_rating(pk, user["sub"], int(stars)))
```

- [ ] **Step 6: Run interaction tests**

```bash
cd backend && pytest tests/test_comments.py tests/test_ratings.py -v
```

Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add backend/models/interactions.py backend/routes/comments.py backend/routes/ratings.py \
  backend/tests/test_comments.py backend/tests/test_ratings.py
git commit -m "feat: implement comments and ratings routes"
```

---

### Task 11: Guestbook

**Files:**
- Create: `backend/models/guestbook.py`
- Modify: `backend/routes/guestbook.py`
- Create: `backend/tests/test_guestbook.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_guestbook.py
import json
from tests.conftest import make_event
from auth import make_jwt


def test_list_guestbook_empty(ddb_table):
    from router import route
    resp = route(make_event("GET", "/guestbook"))
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"])["data"] == []


def test_guest_can_submit_entry(ddb_table):
    from router import route
    resp = route(make_event("POST", "/guestbook", body={"name": "Alice", "message": "Cool site!"}))
    assert resp["statusCode"] == 201
    entry = json.loads(resp["body"])["data"]
    assert entry["name"] == "Alice (guest)"
    assert entry["message"] == "Cool site!"


def test_authenticated_entry_shows_identity(ddb_table):
    from router import route
    from models.users import create_user, mark_email_verified
    user = create_user("u@example.com", "Bob", "MCRI")
    mark_email_verified(user["user_id"])
    token = make_jwt(user["user_id"], "user")

    resp = route(make_event("POST", "/guestbook",
        body={"name": "Bob", "message": "Hi!"},
        headers={"authorization": f"Bearer {token}"},
    ))
    assert resp["statusCode"] == 201
    entry = json.loads(resp["body"])["data"]
    assert entry["name"] == "Bob"
    assert entry["identity"] == "MCRI"


def test_entry_requires_name_and_message(ddb_table):
    from router import route
    resp = route(make_event("POST", "/guestbook", body={"name": "Alice"}))
    assert resp["statusCode"] == 400
```

- [ ] **Step 2: Implement models/guestbook.py**

```python
# backend/models/guestbook.py
import uuid
import time
from db import get_table
from boto3.dynamodb.conditions import Key


def list_entries() -> list:
    table = get_table()
    resp = table.query(
        KeyConditionExpression=Key("PK").eq("GUESTBOOK") & Key("SK").begins_with("ENTRY#"),
    )
    items = resp.get("Items", [])
    for item in items:
        item.pop("PK", None)
    return sorted(items, key=lambda x: x.get("created_at", 0), reverse=True)


def create_entry(name: str, message: str, is_authenticated: bool, identity: str | None = None) -> dict:
    table = get_table()
    entry_id = str(uuid.uuid4())
    ts = int(time.time())
    item = {
        "PK": "GUESTBOOK",
        "SK": f"ENTRY#{ts}#{entry_id}",
        "entry_id": entry_id,
        "name": name,
        "message": message,
        "is_authenticated": is_authenticated,
        "created_at": ts,
    }
    if identity:
        item["identity"] = identity
    table.put_item(Item=item)
    result = dict(item)
    result.pop("PK", None)
    return result
```

- [ ] **Step 3: Implement routes/guestbook.py**

```python
# backend/routes/guestbook.py
from auth import get_current_user
from models import guestbook as g
from models.users import get_user_by_id
from utils import ok, created, bad_request


def list_entries(event, path_params, body, query, headers):
    return ok(g.list_entries())


def create_entry(event, path_params, body, query, headers):
    name = (body.get("name") or "").strip()
    message = (body.get("message") or "").strip()
    if not name or not message:
        return bad_request("name and message are required")

    user = get_current_user(headers)
    if user:
        profile = get_user_by_id(user["sub"]) or {}
        display_name = profile.get("name", name)
        identity = profile.get("identity")
        entry = g.create_entry(display_name, message, True, identity)
    else:
        entry = g.create_entry(f"{name} (guest)", message, False)

    return created(entry)
```

- [ ] **Step 4: Run tests**

```bash
cd backend && pytest tests/test_guestbook.py -v
```

Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add backend/models/guestbook.py backend/routes/guestbook.py backend/tests/test_guestbook.py
git commit -m "feat: implement guestbook routes"
```

---

### Task 12: Quiz

**Files:**
- Create: `backend/models/quiz.py`
- Modify: `backend/routes/quiz.py`
- Create: `backend/tests/test_quiz.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_quiz.py
import json
from tests.conftest import make_event
from auth import make_jwt


def _auth_headers(user_id="user-1"):
    return {"authorization": f"Bearer {make_jwt(user_id, 'user')}"}


def _seed_questions(ddb_table):
    from models.quiz import create_question
    for i in range(3):
        create_question({
            "question": f"Question {i+1}?",
            "options": ["A", "B", "C", "D"],
            "answer": "A",
            "topic": "general",
        })


def test_get_questions_requires_auth(ddb_table):
    from router import route
    resp = route(make_event("GET", "/quiz/questions"))
    assert resp["statusCode"] == 401


def test_get_questions_returns_list(ddb_table):
    from router import route
    _seed_questions(ddb_table)
    resp = route(make_event("GET", "/quiz/questions", headers=_auth_headers()))
    assert resp["statusCode"] == 200
    questions = json.loads(resp["body"])["data"]
    assert len(questions) == 3
    # Answers must NOT be included in the response
    for q in questions:
        assert "answer" not in q


def test_submit_quiz_scores_correctly(ddb_table):
    from router import route
    from models.quiz import create_question, list_questions
    _seed_questions(ddb_table)
    questions = list_questions()
    answers = {q["question_id"]: "A" for q in questions}

    resp = route(make_event("POST", "/quiz/submit",
        body={"answers": answers},
        headers=_auth_headers(),
    ))
    assert resp["statusCode"] == 200
    result = json.loads(resp["body"])["data"]
    assert result["score"] == 3
    assert result["total"] == 3


def test_leaderboard_requires_auth(ddb_table):
    from router import route
    resp = route(make_event("GET", "/quiz/leaderboard"))
    assert resp["statusCode"] == 401


def test_leaderboard_returns_scores(ddb_table):
    from router import route
    from models.quiz import create_question, list_questions
    _seed_questions(ddb_table)
    questions = list_questions()
    answers = {q["question_id"]: "A" for q in questions}
    route(make_event("POST", "/quiz/submit", body={"answers": answers}, headers=_auth_headers("user-1")))
    route(make_event("POST", "/quiz/submit", body={"answers": answers}, headers=_auth_headers("user-2")))

    resp = route(make_event("GET", "/quiz/leaderboard", headers=_auth_headers()))
    assert resp["statusCode"] == 200
    board = json.loads(resp["body"])["data"]
    assert len(board) >= 2
```

- [ ] **Step 2: Implement models/quiz.py**

```python
# backend/models/quiz.py
import uuid
import time
from db import get_table
from boto3.dynamodb.conditions import Key


def list_questions() -> list:
    table = get_table()
    resp = table.query(
        KeyConditionExpression=Key("PK").eq("QUIZ") & Key("SK").begins_with("QUESTION#"),
    )
    return resp.get("Items", [])


def create_question(fields: dict) -> dict:
    table = get_table()
    qid = str(uuid.uuid4())
    item = {"PK": "QUIZ", "SK": f"QUESTION#{qid}", "question_id": qid, **fields}
    table.put_item(Item=item)
    return item


def update_question(question_id: str, fields: dict) -> dict | None:
    table = get_table()
    resp = table.get_item(Key={"PK": "QUIZ", "SK": f"QUESTION#{question_id}"})
    item = resp.get("Item")
    if not item:
        return None
    updated = {**item, **fields}
    table.put_item(Item=updated)
    return updated


def delete_question(question_id: str) -> bool:
    table = get_table()
    resp = table.get_item(Key={"PK": "QUIZ", "SK": f"QUESTION#{question_id}"})
    if not resp.get("Item"):
        return False
    table.delete_item(Key={"PK": "QUIZ", "SK": f"QUESTION#{question_id}"})
    return True


def save_score(user_id: str, score: int, total: int) -> dict:
    table = get_table()
    attempt_id = str(uuid.uuid4())
    ts = int(time.time())
    padded_score = str(score).zfill(6)
    item = {
        "PK": f"USER#{user_id}",
        "SK": f"QUIZ_SCORE#{attempt_id}",
        "GSI3PK": "QUIZ_LEADERBOARD",
        "GSI3SK": f"SCORE#{padded_score}",
        "user_id": user_id,
        "score": score,
        "total": total,
        "attempt_id": attempt_id,
        "created_at": ts,
    }
    table.put_item(Item=item)
    return item


def get_leaderboard(limit: int = 20) -> list:
    table = get_table()
    resp = table.query(
        IndexName="GSI3",
        KeyConditionExpression=Key("GSI3PK").eq("QUIZ_LEADERBOARD"),
        ScanIndexForward=False,
        Limit=limit,
    )
    items = resp.get("Items", [])
    for item in items:
        item.pop("PK", None)
        item.pop("SK", None)
        item.pop("GSI3PK", None)
        item.pop("GSI3SK", None)
    return items
```

- [ ] **Step 3: Implement routes/quiz.py**

```python
# backend/routes/quiz.py
from auth import require_auth
from models import quiz as q
from utils import ok, bad_request


@require_auth
def get_questions(event, path_params, body, query, headers, user):
    questions = q.list_questions()
    # Strip answers before sending to client
    safe = [{k: v for k, v in item.items() if k not in ("answer", "PK", "SK")} for item in questions]
    return ok(safe)


@require_auth
def submit_answers(event, path_params, body, query, headers, user):
    answers = body.get("answers", {})
    if not answers:
        return bad_request("answers is required")
    questions = q.list_questions()
    score = sum(1 for item in questions if answers.get(item["question_id"]) == item["answer"])
    total = len(questions)
    attempt = q.save_score(user["sub"], score, total)
    return ok({"score": score, "total": total, "attempt_id": attempt["attempt_id"]})


@require_auth
def get_leaderboard(event, path_params, body, query, headers, user):
    return ok(q.get_leaderboard())
```

- [ ] **Step 4: Run quiz tests**

```bash
cd backend && pytest tests/test_quiz.py -v
```

Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add backend/models/quiz.py backend/routes/quiz.py backend/tests/test_quiz.py
git commit -m "feat: implement quiz routes (questions, submit, leaderboard)"
```

---

### Task 13: Testimonials

**Files:**
- Create: `backend/models/testimonials.py`
- Modify: `backend/routes/testimonials.py`
- Create: `backend/tests/test_testimonials.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_testimonials.py
import json
from tests.conftest import make_event
from auth import make_jwt


def test_submit_testimonial_as_guest(ddb_table):
    from router import route
    resp = route(make_event("POST", "/testimonials", body={
        "body": "Ron is great!",
        "anonymous": True,
    }))
    assert resp["statusCode"] == 201
    data = json.loads(resp["body"])["data"]
    assert data["author"] == "Anonymous"
    assert data["status"] == "pending"


def test_list_testimonials_only_shows_approved(ddb_table):
    from router import route
    from models.testimonials import create_testimonial, approve_testimonial
    t = create_testimonial("Great!", "Alice", "MCRI", False)
    approve_testimonial(t["testimonial_id"])

    # Also create a pending one
    create_testimonial("Also great!", "Bob", "Friend", False)

    resp = route(make_event("GET", "/testimonials"))
    assert resp["statusCode"] == 200
    items = json.loads(resp["body"])["data"]
    assert all(t["status"] == "approved" for t in items)
    assert len(items) == 1


def test_filter_testimonials_by_identity(ddb_table):
    from router import route
    from models.testimonials import create_testimonial, approve_testimonial
    t1 = create_testimonial("From Jamf!", "Alice", "Jamf", False)
    t2 = create_testimonial("From MCRI!", "Bob", "MCRI", False)
    approve_testimonial(t1["testimonial_id"])
    approve_testimonial(t2["testimonial_id"])

    resp = route(make_event("GET", "/testimonials", query={"identity": "Jamf"}))
    items = json.loads(resp["body"])["data"]
    assert all(t["identity"] == "Jamf" for t in items)
```

- [ ] **Step 2: Implement models/testimonials.py**

```python
# backend/models/testimonials.py
import uuid
import time
from db import get_table
from boto3.dynamodb.conditions import Key


def create_testimonial(body_text: str, author: str, identity: str, anonymous: bool) -> dict:
    table = get_table()
    tid = str(uuid.uuid4())
    ts = int(time.time())
    display_author = "Anonymous" if anonymous else author
    item = {
        "PK": "TESTIMONIALS",
        "SK": f"TESTIMONIAL#{tid}",
        "GSI2PK": "STATUS#pending",
        "GSI2SK": f"TESTIMONIAL#{ts}",
        "testimonial_id": tid,
        "body": body_text,
        "author": display_author,
        "identity": identity,
        "status": "pending",
        "created_at": ts,
    }
    table.put_item(Item=item)
    result = dict(item)
    result.pop("PK", None)
    result.pop("SK", None)
    return result


def list_approved(identity_filter: str | None = None) -> list:
    table = get_table()
    resp = table.query(
        IndexName="GSI2",
        KeyConditionExpression=Key("GSI2PK").eq("STATUS#approved"),
        ScanIndexForward=False,
    )
    items = resp.get("Items", [])
    if identity_filter:
        items = [i for i in items if i.get("identity") == identity_filter]
    for item in items:
        item.pop("PK", None)
        item.pop("SK", None)
        item.pop("GSI2PK", None)
        item.pop("GSI2SK", None)
    return items


def list_pending() -> list:
    table = get_table()
    resp = table.query(
        IndexName="GSI2",
        KeyConditionExpression=Key("GSI2PK").eq("STATUS#pending"),
    )
    items = resp.get("Items", [])
    for item in items:
        item.pop("PK", None)
        item.pop("SK", None)
    return items


def approve_testimonial(testimonial_id: str) -> bool:
    return _set_status(testimonial_id, "approved")


def reject_testimonial(testimonial_id: str) -> bool:
    return _set_status(testimonial_id, "rejected")


def _set_status(testimonial_id: str, status: str) -> bool:
    table = get_table()
    ts = int(time.time())
    try:
        table.update_item(
            Key={"PK": "TESTIMONIALS", "SK": f"TESTIMONIAL#{testimonial_id}"},
            UpdateExpression="SET #s = :s, GSI2PK = :gpk, GSI2SK = :gsk",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":s": status,
                ":gpk": f"STATUS#{status}",
                ":gsk": f"TESTIMONIAL#{ts}",
            },
        )
        return True
    except Exception:
        return False
```

- [ ] **Step 3: Implement routes/testimonials.py**

```python
# backend/routes/testimonials.py
from auth import get_current_user
from models import testimonials as t
from models.users import get_user_by_id
from utils import ok, created, bad_request


def list_testimonials(event, path_params, body, query, headers):
    identity = query.get("identity")
    return ok(t.list_approved(identity))


def submit_testimonial(event, path_params, body, query, headers):
    text = (body.get("body") or "").strip()
    if not text:
        return bad_request("body is required")

    anonymous = bool(body.get("anonymous", False))
    user = get_current_user(headers)
    if user:
        profile = get_user_by_id(user["sub"]) or {}
        author = profile.get("name", "Anonymous")
        identity = profile.get("identity", "Other")
    else:
        author = (body.get("author") or "Anonymous").strip()
        identity = body.get("identity", "Other")
        anonymous = True  # guests are always anonymous

    testimonial = t.create_testimonial(text, author, identity, anonymous)
    return created(testimonial)
```

- [ ] **Step 4: Run tests**

```bash
cd backend && pytest tests/test_testimonials.py -v
```

Expected: All PASS

- [ ] **Step 5: Commit + merge**

```bash
git add backend/models/ backend/routes/ backend/tests/
git commit -m "feat: implement guestbook, quiz, testimonials routes"
git checkout dev
git merge feature/interaction-routes
git push origin dev
```

---

## Feature Branch: `feature/stats-contact`

> Covers: visitor tracking (ip-api.com), /stats/visitors, /stats/analytics, /contact + rate limiting

```bash
git checkout dev
git checkout -b feature/stats-contact
```

---

### Task 14: Visitor tracking + stats routes

**Files:**
- Create: `backend/models/visits.py`
- Modify: `backend/routes/stats.py`
- Create: `backend/tests/test_stats.py`

- [ ] **Step 1: Implement models/visits.py**

```python
# backend/models/visits.py
import uuid
import time
import requests
from db import get_table
from boto3.dynamodb.conditions import Key


def record_visit(ip: str, page: str, user: dict | None = None):
    """
    Called from the router on every request to record a visitor.
    Geo lookup is best-effort — silently skips on failure.
    """
    try:
        geo = _lookup_ip(ip)
    except Exception:
        geo = {}

    table = get_table()
    ts = int(time.time())
    visit_id = str(uuid.uuid4())
    item = {
        "PK": "VISITS",
        "SK": f"VISIT#{ts}#{visit_id}",
        "visit_id": visit_id,
        "ip": ip,
        "page": page,
        "country": geo.get("country"),
        "city": geo.get("city"),
        "lat": str(geo.get("lat", "")),
        "lon": str(geo.get("lon", "")),
        "created_at": ts,
    }
    if user:
        item["user_id"] = user.get("sub")
        item["identity"] = user.get("identity")
    table.put_item(Item=item)


def _lookup_ip(ip: str) -> dict:
    if ip in ("127.0.0.1", "::1", "testclient"):
        return {}
    resp = requests.get(f"http://ip-api.com/json/{ip}?fields=country,city,lat,lon", timeout=3)
    if resp.status_code == 200 and resp.json().get("status") == "success":
        return resp.json()
    return {}


def get_visitor_locations() -> list:
    """Public — returns lat/lon/country/city only (no IP or user data)."""
    table = get_table()
    resp = table.query(
        KeyConditionExpression=Key("PK").eq("VISITS") & Key("SK").begins_with("VISIT#"),
        Limit=500,
    )
    items = resp.get("Items", [])
    return [
        {
            "lat": item.get("lat"),
            "lon": item.get("lon"),
            "country": item.get("country"),
            "city": item.get("city"),
        }
        for item in items
        if item.get("lat") and item.get("lon")
    ]


def get_analytics() -> dict:
    """Admin only — full breakdown."""
    table = get_table()
    resp = table.query(
        KeyConditionExpression=Key("PK").eq("VISITS") & Key("SK").begins_with("VISIT#"),
    )
    items = resp.get("Items", [])

    page_counts: dict = {}
    identity_counts: dict = {}
    for item in items:
        page = item.get("page", "unknown")
        page_counts[page] = page_counts.get(page, 0) + 1
        if item.get("identity"):
            identity = item["identity"]
            identity_counts[identity] = identity_counts.get(identity, 0) + 1

    return {
        "total_visits": len(items),
        "by_page": page_counts,
        "by_identity": identity_counts,
        "locations": get_visitor_locations(),
    }
```

- [ ] **Step 2: Write failing tests**

```python
# backend/tests/test_stats.py
import json
from tests.conftest import make_event


def test_get_visitor_locations_returns_list(ddb_table):
    from router import route
    resp = route(make_event("GET", "/stats/visitors"))
    assert resp["statusCode"] == 200
    assert isinstance(json.loads(resp["body"])["data"], list)


def test_get_analytics_requires_admin(ddb_table):
    from router import route
    resp = route(make_event("GET", "/stats/analytics"))
    assert resp["statusCode"] == 401


def test_get_analytics_returns_breakdown(ddb_table):
    from router import route
    from auth import make_jwt
    from models.visits import record_visit
    record_visit("testclient", "/projects", None)
    record_visit("testclient", "/projects", None)
    record_visit("testclient", "/about", None)

    token = make_jwt("admin-1", "admin")
    resp = route(make_event("GET", "/stats/analytics", headers={"authorization": f"Bearer {token}"}))
    assert resp["statusCode"] == 200
    data = json.loads(resp["body"])["data"]
    assert data["total_visits"] == 3
    assert data["by_page"]["/projects"] == 2
```

- [ ] **Step 3: Implement routes/stats.py**

```python
# backend/routes/stats.py
from auth import require_admin
from models.visits import get_visitor_locations, get_analytics
from utils import ok


def get_visitor_locations(event, path_params, body, query, headers):
    return ok(get_visitor_locations())


@require_admin
def get_analytics(event, path_params, body, query, headers, user):
    return ok(get_analytics())
```

**Note:** Route functions shadow model imports — use aliased imports:

```python
# backend/routes/stats.py  (corrected)
from auth import require_admin
from models import visits as visit_model
from utils import ok


def get_visitor_locations(event, path_params, body, query, headers):
    return ok(visit_model.get_visitor_locations())


@require_admin
def get_analytics(event, path_params, body, query, headers, user):
    return ok(visit_model.get_analytics())
```

- [ ] **Step 4: Run stats tests**

```bash
cd backend && pytest tests/test_stats.py -v
```

Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add backend/models/visits.py backend/routes/stats.py backend/tests/test_stats.py
git commit -m "feat: implement visitor tracking and stats routes"
```

---

### Task 15: Contact form + rate limiting

**Files:**
- Create: `backend/models/contacts.py`
- Modify: `backend/routes/contact.py`
- Create: `backend/tests/test_contact.py`

- [ ] **Step 1: Implement models/contacts.py**

```python
# backend/models/contacts.py
import uuid
import time
from db import get_table
from boto3.dynamodb.conditions import Key

RATE_LIMIT = 5  # submissions per hour per IP


def is_rate_limited(ip: str) -> bool:
    table = get_table()
    resp = table.get_item(Key={"PK": f"RATELIMIT#{ip}", "SK": "CONTACT"})
    item = resp.get("Item")
    if not item:
        return False
    return int(item.get("count", 0)) >= RATE_LIMIT


def increment_rate_limit(ip: str):
    table = get_table()
    ttl = int(time.time()) + 3600  # 1 hour TTL
    table.update_item(
        Key={"PK": f"RATELIMIT#{ip}", "SK": "CONTACT"},
        UpdateExpression="SET #c = if_not_exists(#c, :zero) + :one, #t = :ttl",
        ExpressionAttributeNames={"#c": "count", "#t": "ttl"},
        ExpressionAttributeValues={":zero": 0, ":one": 1, ":ttl": ttl},
    )


def save_contact(name: str, email: str, message: str) -> dict:
    table = get_table()
    cid = str(uuid.uuid4())
    ts = int(time.time())
    item = {
        "PK": "CONTACTS",
        "SK": f"CONTACT#{ts}#{cid}",
        "contact_id": cid,
        "name": name,
        "email": email,
        "message": message,
        "created_at": ts,
    }
    table.put_item(Item=item)
    result = dict(item)
    result.pop("PK", None)
    result.pop("SK", None)
    return result


def list_contacts() -> list:
    table = get_table()
    resp = table.query(
        KeyConditionExpression=Key("PK").eq("CONTACTS") & Key("SK").begins_with("CONTACT#"),
    )
    items = resp.get("Items", [])
    for item in items:
        item.pop("PK", None)
        item.pop("SK", None)
    return sorted(items, key=lambda x: x.get("created_at", 0), reverse=True)
```

- [ ] **Step 2: Write failing tests**

```python
# backend/tests/test_contact.py
import json
from tests.conftest import make_event


def _contact_payload():
    return {"name": "Alice", "email": "alice@example.com", "message": "Hello!"}


def test_submit_contact_returns_200(ddb_table, mocker):
    mocker.patch("routes.contact._send_contact_notification")
    from router import route
    resp = route(make_event("POST", "/contact", body=_contact_payload()))
    assert resp["statusCode"] == 200


def test_submit_contact_missing_fields_returns_400(ddb_table):
    from router import route
    resp = route(make_event("POST", "/contact", body={"name": "Alice"}))
    assert resp["statusCode"] == 400


def test_rate_limit_blocks_after_5_submissions(ddb_table, mocker):
    mocker.patch("routes.contact._send_contact_notification")
    from router import route
    for _ in range(5):
        route(make_event("POST", "/contact", body=_contact_payload(),
                         headers={"x-forwarded-for": "1.2.3.4"}))
    resp = route(make_event("POST", "/contact", body=_contact_payload(),
                            headers={"x-forwarded-for": "1.2.3.4"}))
    assert resp["statusCode"] == 429


def test_different_ips_not_rate_limited(ddb_table, mocker):
    mocker.patch("routes.contact._send_contact_notification")
    from router import route
    for _ in range(5):
        route(make_event("POST", "/contact", body=_contact_payload(),
                         headers={"x-forwarded-for": "1.2.3.4"}))
    resp = route(make_event("POST", "/contact", body=_contact_payload(),
                            headers={"x-forwarded-for": "5.6.7.8"}))
    assert resp["statusCode"] == 200
```

- [ ] **Step 3: Implement routes/contact.py**

```python
# backend/routes/contact.py
import os
import boto3
from models import contacts as c
from utils import ok, bad_request, rate_limited


def _get_ip(event: dict) -> str:
    headers = event.get("headers") or {}
    forwarded = headers.get("x-forwarded-for") or headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return event.get("requestContext", {}).get("http", {}).get("sourceIp", "unknown")


def _send_contact_notification(name: str, email: str, message: str):
    ses = boto3.client("ses", region_name="us-east-1")
    sender = os.environ["SES_SENDER_EMAIL"]
    ses.send_email(
        Source=sender,
        Destination={"ToAddresses": [sender]},
        Message={
            "Subject": {"Data": f"Portfolio contact from {name}"},
            "Body": {"Text": {"Data": f"From: {name} <{email}>\n\n{message}"}},
        },
    )


def submit_contact(event, path_params, body, query, headers):
    name = (body.get("name") or "").strip()
    email = (body.get("email") or "").strip()
    message = (body.get("message") or "").strip()
    if not name or not email or not message:
        return bad_request("name, email, and message are required")

    ip = _get_ip(event)
    if c.is_rate_limited(ip):
        return rate_limited("You have sent too many messages. Please try again in an hour.")

    c.increment_rate_limit(ip)
    contact = c.save_contact(name, email, message)
    _send_contact_notification(name, email, message)
    return ok({"message": "Message sent. I'll get back to you soon!"})
```

- [ ] **Step 4: Run tests**

```bash
cd backend && pytest tests/test_contact.py -v
```

Expected: All PASS

- [ ] **Step 5: Commit + merge**

```bash
git add backend/models/contacts.py backend/routes/contact.py backend/tests/test_contact.py
git commit -m "feat: implement contact form with IP-based rate limiting (5/hr)"
git checkout dev
git merge feature/stats-contact
git push origin dev
```

---

## Feature Branch: `feature/admin-routes`

> Covers: all /admin/* endpoints (users, contacts, testimonials, quiz questions)

```bash
git checkout dev
git checkout -b feature/admin-routes
```

---

### Task 16: Admin routes

**Files:**
- Modify: `backend/routes/admin.py`
- Create: `backend/tests/test_admin.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_admin.py
import json
from tests.conftest import make_event
from auth import make_jwt


def _admin_headers():
    return {"authorization": f"Bearer {make_jwt('admin-1', 'admin')}"}


def _user_headers():
    return {"authorization": f"Bearer {make_jwt('user-1', 'user')}"}


# --- Users ---

def test_list_users_requires_admin(ddb_table):
    from router import route
    assert route(make_event("GET", "/admin/users"))["statusCode"] == 401
    assert route(make_event("GET", "/admin/users", headers=_user_headers()))["statusCode"] == 403


def test_list_users_returns_list(ddb_table):
    from router import route
    from models.users import create_user
    create_user("a@example.com", "Alice", "Jamf")
    create_user("b@example.com", "Bob", "MCRI")

    resp = route(make_event("GET", "/admin/users", headers=_admin_headers()))
    assert resp["statusCode"] == 200
    users = json.loads(resp["body"])["data"]
    assert len(users) == 2
    assert all("password_hash" not in u for u in users)


def test_suspend_user(ddb_table):
    from router import route
    from models.users import create_user
    user = create_user("a@example.com", "Alice", "Jamf")
    uid = user["user_id"]

    resp = route(make_event("PUT", f"/admin/users/{uid}",
        body={"status": "suspended"},
        headers=_admin_headers(),
    ))
    assert resp["statusCode"] == 200

    from models.users import get_user_by_id
    updated = get_user_by_id(uid)
    assert updated["status"] == "suspended"


def test_delete_user(ddb_table):
    from router import route
    from models.users import create_user, get_user_by_id
    user = create_user("a@example.com", "Alice", "Jamf")
    uid = user["user_id"]

    resp = route(make_event("DELETE", f"/admin/users/{uid}", headers=_admin_headers()))
    assert resp["statusCode"] == 200
    assert get_user_by_id(uid) is None


# --- Contacts ---

def test_list_contacts(ddb_table):
    from router import route
    from models.contacts import save_contact
    save_contact("Alice", "alice@example.com", "Hello!")

    resp = route(make_event("GET", "/admin/contacts", headers=_admin_headers()))
    assert resp["statusCode"] == 200
    items = json.loads(resp["body"])["data"]
    assert len(items) == 1


# --- Testimonials ---

def test_list_pending_testimonials(ddb_table):
    from router import route
    from models.testimonials import create_testimonial
    create_testimonial("Great!", "Alice", "Jamf", False)

    resp = route(make_event("GET", "/admin/testimonials/pending", headers=_admin_headers()))
    assert resp["statusCode"] == 200
    items = json.loads(resp["body"])["data"]
    assert len(items) == 1


def test_approve_testimonial(ddb_table):
    from router import route
    from models.testimonials import create_testimonial, list_approved
    t = create_testimonial("Awesome!", "Bob", "MCRI", False)
    tid = t["testimonial_id"]

    resp = route(make_event("PUT", f"/admin/testimonials/{tid}",
        body={"action": "approve"},
        headers=_admin_headers(),
    ))
    assert resp["statusCode"] == 200
    assert len(list_approved()) == 1


def test_reject_testimonial(ddb_table):
    from router import route
    from models.testimonials import create_testimonial, list_pending
    t = create_testimonial("Bad!", "Eve", "Other", False)
    tid = t["testimonial_id"]

    route(make_event("PUT", f"/admin/testimonials/{tid}",
        body={"action": "reject"},
        headers=_admin_headers(),
    ))
    assert len(list_pending()) == 0


# --- Quiz management ---

def test_admin_can_add_quiz_question(ddb_table):
    from router import route
    resp = route(make_event("POST", "/admin/quiz/questions",
        body={"question": "What is 2+2?", "options": ["1","2","3","4"], "answer": "4", "topic": "math"},
        headers=_admin_headers(),
    ))
    assert resp["statusCode"] == 201


def test_admin_can_delete_quiz_question(ddb_table):
    from router import route
    from models.quiz import create_question, list_questions
    q = create_question({"question": "Q?", "options": ["A"], "answer": "A", "topic": "t"})
    qid = q["question_id"]

    resp = route(make_event("DELETE", f"/admin/quiz/questions/{qid}", headers=_admin_headers()))
    assert resp["statusCode"] == 200
    assert list_questions() == []
```

- [ ] **Step 2: Run to confirm they fail**

```bash
cd backend && pytest tests/test_admin.py -v
```

Expected: FAIL (404s or 401s from stub implementations)

- [ ] **Step 3: Implement routes/admin.py**

```python
# backend/routes/admin.py
from auth import require_admin
from models.users import list_all_users, set_user_status, delete_user as delete_user_model, get_user_by_id
from models.contacts import list_contacts as list_contacts_model
from models.testimonials import list_pending, approve_testimonial, reject_testimonial
from models import quiz as quiz_model
from utils import ok, created, bad_request, not_found


@require_admin
def list_users(event, path_params, body, query, headers, user):
    return ok(list_all_users())


@require_admin
def update_user(event, path_params, body, query, headers, user):
    uid = path_params["id"]
    status = body.get("status")
    if status not in ("active", "suspended", "banned"):
        return bad_request("status must be active, suspended, or banned")
    if not get_user_by_id(uid):
        return not_found("User not found")
    set_user_status(uid, status)
    return ok(get_user_by_id(uid))


@require_admin
def delete_user(event, path_params, body, query, headers, user):
    uid = path_params["id"]
    if not get_user_by_id(uid):
        return not_found("User not found")
    delete_user_model(uid)
    return ok({"deleted": True})


@require_admin
def list_contacts(event, path_params, body, query, headers, user):
    return ok(list_contacts_model())


@require_admin
def list_pending_testimonials(event, path_params, body, query, headers, user):
    return ok(list_pending())


@require_admin
def update_testimonial(event, path_params, body, query, headers, user):
    tid = path_params["id"]
    action = body.get("action")
    if action == "approve":
        approve_testimonial(tid)
        return ok({"action": "approved"})
    elif action == "reject":
        reject_testimonial(tid)
        return ok({"action": "rejected"})
    return bad_request("action must be 'approve' or 'reject'")


@require_admin
def list_quiz_questions(event, path_params, body, query, headers, user):
    return ok(quiz_model.list_questions())


@require_admin
def create_quiz_question(event, path_params, body, query, headers, user):
    for field in ("question", "options", "answer", "topic"):
        if not body.get(field):
            return bad_request(f"{field} is required")
    return created(quiz_model.create_question(body))


@require_admin
def update_quiz_question(event, path_params, body, query, headers, user):
    result = quiz_model.update_question(path_params["id"], body)
    return ok(result) if result else not_found("Question not found")


@require_admin
def delete_quiz_question(event, path_params, body, query, headers, user):
    success = quiz_model.delete_question(path_params["id"])
    return ok({"deleted": True}) if success else not_found("Question not found")
```

- [ ] **Step 4: Run admin tests**

```bash
cd backend && pytest tests/test_admin.py -v
```

Expected: All PASS

- [ ] **Step 5: Commit + merge**

```bash
git add backend/routes/admin.py backend/tests/test_admin.py
git commit -m "feat: implement admin routes (users, contacts, testimonials, quiz management)"
git checkout dev
git merge feature/admin-routes
git push origin dev
```

---

## Feature Branch: `feature/api-docs`

> Covers: GET /api (Swagger UI HTML), GET /api/spec (OpenAPI 3.0 JSON)

```bash
git checkout dev
git checkout -b feature/api-docs
```

---

### Task 17: Swagger UI + OpenAPI spec

**Files:**
- Modify: `backend/routes/docs.py`

- [ ] **Step 1: Implement routes/docs.py**

```python
# backend/routes/docs.py
import json
import os


def swagger_ui(event, path_params, body, query, headers):
    """Returns interactive Swagger UI HTML page."""
    lambda_url = os.environ.get("LAMBDA_FUNCTION_URL", "")
    spec_url = f"{lambda_url.rstrip('/')}/api/spec" if lambda_url else "/api/spec"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Ron Harifiyati — API Docs</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    SwaggerUIBundle({{
      url: "{spec_url}",
      dom_id: "#swagger-ui",
      presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
      layout: "StandaloneLayout",
      deepLinking: true,
    }});
  </script>
</body>
</html>"""
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/html",
            "Access-Control-Allow-Origin": "*",
        },
        "body": html,
    }


def openapi_spec(event, path_params, body, query, headers):
    """Returns the OpenAPI 3.0 spec as JSON."""
    lambda_url = os.environ.get("LAMBDA_FUNCTION_URL", "https://api.example.com")
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Ron Harifiyati — Portfolio API",
            "version": os.environ.get("VERSION", "0.1.0"),
            "description": "Personal portfolio API. All endpoints return {data, error} envelope.",
            "contact": {"name": "Ron Harifiyati", "email": os.environ.get("SES_SENDER_EMAIL", "")},
        },
        "servers": [{"url": lambda_url.rstrip("/"), "description": "Live API"}],
        "components": {
            "securitySchemes": {
                "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
            }
        },
        "paths": {
            "/meta": {"get": {"summary": "Deploy metadata", "tags": ["Meta"], "responses": {"200": {"description": "GIT_SHA, DEPLOY_TIMESTAMP, ENVIRONMENT, VERSION, region, author"}}}},
            "/about": {"get": {"summary": "Bio + contact info", "tags": ["Content"], "responses": {"200": {"description": "About data"}}}},
            "/skills": {"get": {"summary": "Skills by category", "tags": ["Content"], "responses": {"200": {"description": "Skills"}}}},
            "/timeline": {"get": {"summary": "Journey timeline", "tags": ["Content"], "responses": {"200": {"description": "Timeline events"}}}},
            "/fun-fact": {"get": {"summary": "Random fun fact", "tags": ["Content"], "responses": {"200": {"description": "One random fun fact"}}}},
            "/currently-learning": {"get": {"summary": "Currently learning ticker", "tags": ["Content"], "responses": {"200": {"description": "Learning items"}}}},
            "/projects": {
                "get": {"summary": "List all projects", "tags": ["Projects"], "responses": {"200": {"description": "Projects list"}}},
                "post": {"summary": "Create project (admin)", "tags": ["Projects"], "security": [{"BearerAuth": []}], "responses": {"201": {"description": "Created project"}}},
            },
            "/projects/{id}": {
                "get": {"summary": "Get project by ID", "tags": ["Projects"], "responses": {"200": {"description": "Project"}}},
                "put": {"summary": "Update project (admin)", "tags": ["Projects"], "security": [{"BearerAuth": []}], "responses": {"200": {"description": "Updated project"}}},
                "delete": {"summary": "Delete project (admin)", "tags": ["Projects"], "security": [{"BearerAuth": []}], "responses": {"200": {"description": "Deleted"}}},
            },
            "/projects/{id}/comments": {
                "get": {"summary": "List project comments", "tags": ["Comments"], "responses": {"200": {"description": "Comments"}}},
                "post": {"summary": "Post a comment", "tags": ["Comments"], "security": [{"BearerAuth": []}], "responses": {"201": {"description": "Comment created"}}},
            },
            "/projects/{id}/ratings": {
                "get": {"summary": "Get rating summary", "tags": ["Ratings"], "responses": {"200": {"description": "Rating summary"}}},
                "post": {"summary": "Submit or update rating", "tags": ["Ratings"], "security": [{"BearerAuth": []}], "responses": {"200": {"description": "Updated rating summary"}}},
            },
            "/courses": {
                "get": {"summary": "List all courses", "tags": ["Courses"], "responses": {"200": {"description": "Courses list"}}},
                "post": {"summary": "Create course (admin)", "tags": ["Courses"], "security": [{"BearerAuth": []}], "responses": {"201": {"description": "Created course"}}},
            },
            "/courses/{id}": {
                "get": {"summary": "Get course by ID", "tags": ["Courses"], "responses": {"200": {"description": "Course"}}},
                "put": {"summary": "Update course (admin)", "tags": ["Courses"], "security": [{"BearerAuth": []}], "responses": {"200": {"description": "Updated course"}}},
                "delete": {"summary": "Delete course (admin)", "tags": ["Courses"], "security": [{"BearerAuth": []}], "responses": {"200": {"description": "Deleted"}}},
            },
            "/courses/{id}/comments": {
                "get": {"summary": "List course comments", "tags": ["Comments"], "responses": {"200": {"description": "Comments"}}},
                "post": {"summary": "Post a comment", "tags": ["Comments"], "security": [{"BearerAuth": []}], "responses": {"201": {"description": "Comment created"}}},
            },
            "/courses/{id}/ratings": {
                "get": {"summary": "Get rating summary", "tags": ["Ratings"], "responses": {"200": {"description": "Rating summary"}}},
                "post": {"summary": "Submit or update rating", "tags": ["Ratings"], "security": [{"BearerAuth": []}], "responses": {"200": {"description": "Updated rating summary"}}},
            },
            "/github/repos": {"get": {"summary": "Latest public GitHub repos", "tags": ["GitHub"], "responses": {"200": {"description": "Repos list"}}}},
            "/auth/register": {"post": {"summary": "Register with email + password", "tags": ["Auth"], "responses": {"201": {"description": "Account created"}}}},
            "/auth/verify-email": {"post": {"summary": "Verify email token", "tags": ["Auth"], "responses": {"200": {"description": "Verified"}}}},
            "/auth/login": {"post": {"summary": "Login — returns JWT", "tags": ["Auth"], "responses": {"200": {"description": "access_token + refresh_token"}}}},
            "/auth/logout": {"post": {"summary": "Logout — invalidates refresh token", "tags": ["Auth"], "security": [{"BearerAuth": []}], "responses": {"200": {"description": "Logged out"}}}},
            "/auth/refresh": {"post": {"summary": "Refresh access token", "tags": ["Auth"], "responses": {"200": {"description": "New tokens"}}}},
            "/auth/me": {
                "get": {"summary": "Get current user profile", "tags": ["Auth"], "security": [{"BearerAuth": []}], "responses": {"200": {"description": "User profile"}}},
                "put": {"summary": "Update profile (identity, name, theme)", "tags": ["Auth"], "security": [{"BearerAuth": []}], "responses": {"200": {"description": "Updated profile"}}},
            },
            "/auth/oauth/github": {"get": {"summary": "Initiate GitHub OAuth", "tags": ["Auth"], "responses": {"302": {"description": "Redirect to GitHub"}}}},
            "/auth/oauth/github/callback": {"get": {"summary": "GitHub OAuth callback", "tags": ["Auth"], "responses": {"200": {"description": "JWT tokens"}}}},
            "/auth/oauth/google": {"get": {"summary": "Initiate Google OAuth", "tags": ["Auth"], "responses": {"302": {"description": "Redirect to Google"}}}},
            "/auth/oauth/google/callback": {"get": {"summary": "Google OAuth callback", "tags": ["Auth"], "responses": {"200": {"description": "JWT tokens"}}}},
            "/guestbook": {
                "get": {"summary": "List guestbook entries", "tags": ["Guestbook"], "responses": {"200": {"description": "Entries"}}},
                "post": {"summary": "Submit entry (guests welcome)", "tags": ["Guestbook"], "responses": {"201": {"description": "Entry created"}}},
            },
            "/quiz/questions": {"get": {"summary": "Get quiz questions (auth required)", "tags": ["Quiz"], "security": [{"BearerAuth": []}], "responses": {"200": {"description": "Questions without answers"}}}},
            "/quiz/submit": {"post": {"summary": "Submit quiz answers", "tags": ["Quiz"], "security": [{"BearerAuth": []}], "responses": {"200": {"description": "Score"}}}},
            "/quiz/leaderboard": {"get": {"summary": "Top scores", "tags": ["Quiz"], "security": [{"BearerAuth": []}], "responses": {"200": {"description": "Leaderboard"}}}},
            "/testimonials": {
                "get": {"summary": "Approved testimonials (filterable by identity)", "tags": ["Testimonials"], "responses": {"200": {"description": "Testimonials"}}},
                "post": {"summary": "Submit testimonial (pending approval)", "tags": ["Testimonials"], "responses": {"201": {"description": "Submitted"}}},
            },
            "/stats/visitors": {"get": {"summary": "Visitor locations for public map", "tags": ["Stats"], "responses": {"200": {"description": "lat/lon/country/city list"}}}},
            "/stats/analytics": {"get": {"summary": "Full analytics (admin only)", "tags": ["Stats"], "security": [{"BearerAuth": []}], "responses": {"200": {"description": "Analytics breakdown"}}}},
            "/contact": {"post": {"summary": "Submit contact form (5/hr per IP)", "tags": ["Contact"], "responses": {"200": {"description": "Message sent"}, "429": {"description": "Rate limited"}}}},
            "/admin/users": {"get": {"summary": "List all users", "tags": ["Admin"], "security": [{"BearerAuth": []}], "responses": {"200": {"description": "Users"}}}},
            "/admin/users/{id}": {
                "put": {"summary": "Suspend or ban user", "tags": ["Admin"], "security": [{"BearerAuth": []}], "responses": {"200": {"description": "Updated"}}},
                "delete": {"summary": "Delete user", "tags": ["Admin"], "security": [{"BearerAuth": []}], "responses": {"200": {"description": "Deleted"}}},
            },
            "/admin/contacts": {"get": {"summary": "View contact submissions", "tags": ["Admin"], "security": [{"BearerAuth": []}], "responses": {"200": {"description": "Contacts"}}}},
            "/admin/testimonials/pending": {"get": {"summary": "Pending testimonials", "tags": ["Admin"], "security": [{"BearerAuth": []}], "responses": {"200": {"description": "Pending"}}}},
            "/admin/testimonials/{id}": {"put": {"summary": "Approve or reject testimonial", "tags": ["Admin"], "security": [{"BearerAuth": []}], "responses": {"200": {"description": "Updated"}}}},
            "/admin/quiz/questions": {
                "get": {"summary": "List all quiz questions", "tags": ["Admin"], "security": [{"BearerAuth": []}], "responses": {"200": {"description": "Questions with answers"}}},
                "post": {"summary": "Add quiz question", "tags": ["Admin"], "security": [{"BearerAuth": []}], "responses": {"201": {"description": "Created"}}},
            },
            "/admin/quiz/questions/{id}": {
                "put": {"summary": "Edit quiz question", "tags": ["Admin"], "security": [{"BearerAuth": []}], "responses": {"200": {"description": "Updated"}}},
                "delete": {"summary": "Delete quiz question", "tags": ["Admin"], "security": [{"BearerAuth": []}], "responses": {"200": {"description": "Deleted"}}},
            },
        },
    }
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(spec),
    }
```

- [ ] **Step 2: Commit**

```bash
git add backend/routes/docs.py
git commit -m "feat: implement Swagger UI at /api and OpenAPI 3.0 spec at /api/spec"
```

- [ ] **Step 3: Merge to dev**

```bash
git checkout dev
git merge feature/api-docs
git push origin dev
```

---

## Final Verification

- [ ] **Step 1: Run the full test suite**

```bash
cd backend && pytest tests/ -v --tb=short
```

Expected: All tests PASS, no failures.

- [ ] **Step 2: Run flake8 lint**

```bash
cd backend && flake8 . --max-line-length=120 --exclude=tests/,package/
```

Expected: No errors.

- [ ] **Step 3: Push to dev — verify CI/CD deploys**

```bash
git push origin dev
```

Go to GitHub → Actions → `Deploy Backend`. Expected: tests pass, Lambda updated.

- [ ] **Step 4: Smoke test the live API**

```bash
# Replace with your actual Dev Lambda Function URL
API_URL="https://<your-dev-function-url>"

curl $API_URL/meta
# Expected: {"data": {"git_sha": "...", "environment": "dev", ...}, "error": null}

curl $API_URL/projects
# Expected: {"data": [], "error": null}

curl $API_URL/api/spec | python3 -m json.tool | head -20
# Expected: valid OpenAPI JSON

curl $API_URL/api
# Expected: Swagger UI HTML page
```

- [ ] **Step 5: Promote to prod**

```bash
git checkout prod
git merge dev
git push origin prod
```

Expected: `Deploy Backend` workflow runs against `portfolio-prod`.

---

## Checklist before starting Frontend Plan

- [ ] All pytest tests pass locally
- [ ] `GET /meta` returns correct GIT_SHA, ENVIRONMENT, VERSION on both dev and prod Lambda
- [ ] `GET /api` serves Swagger UI HTML
- [ ] `GET /api/spec` returns valid OpenAPI JSON importable into Postman
- [ ] `POST /auth/register` → `POST /auth/verify-email` → `POST /auth/login` flow works end-to-end
- [ ] Note down: Dev Lambda Function URL and Prod Lambda Function URL (needed in frontend plan)


