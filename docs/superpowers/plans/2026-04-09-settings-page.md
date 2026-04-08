# Settings Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a user settings page with profile editing, theme picker, OAuth connection management, activity history, and account deletion with anonymization.

**Architecture:** New `#/settings` route in the main SPA with Alpine.js component. Backend gets ~12 new endpoints under `/auth/me/*` for activity retrieval, OAuth management, and account deletion. Nav bar updated: logged-in users see their identicon linking to settings (replacing theme toggle + logout); logged-out users keep the theme toggle.

**Tech Stack:** Python/Lambda backend, Alpine.js frontend, DynamoDB single-table, jdenticon for identicon generation.

**Spec:** `docs/superpowers/specs/2026-04-09-settings-page-design.md`

---

## File Structure

### New files

| File | Responsibility |
|------|---------------|
| `backend/routes/settings_routes.py` | HTTP handlers for all `/auth/me/*` settings endpoints |
| `backend/models/settings.py` | DynamoDB queries for user activity, OAuth links, account deletion |
| `backend/tests/test_settings.py` | Tests for all settings endpoints |
| `frontend/assets/js/pages/settings.js` | Settings page Alpine.js component |
| `frontend/assets/js/identicon.js` | Identicon generation utility (canvas-based) |

### Modified files

| File | Changes |
|------|---------|
| `backend/router.py` | Register ~12 new routes under `/auth/me/*` |
| `backend/routes/auth_routes.py` | Modify `get_me` to include `has_password`; modify OAuth init/callback for link mode |
| `backend/models/users.py` | Add `get_user_raw` (with password_hash check); add `has_password` helper |
| `backend/routes/guestbook.py` | Store `user_id` on authenticated guestbook entries |
| `backend/models/guestbook.py` | Accept optional `user_id` in `create_entry` |
| `backend/routes/testimonials.py` | Store `user_id` on testimonial submissions |
| `backend/models/testimonials.py` | Accept optional `user_id` in `create_testimonial` |
| `backend/routes/docs.py` | Add new endpoints to OpenAPI spec |
| `frontend/index.html` | Add `#/settings` route template; update nav bar (identicon for logged-in, theme toggle for logged-out) |
| `frontend/assets/js/app.js` | Add `settings` to route table; keep `toggleTheme` for logged-out nav |
| `frontend/assets/js/themes.js` | No changes needed (already works standalone) |
| `frontend/assets/css/main.css` | Settings page styles, identicon styles |
| `version.txt` | Bump from 2.8 to 2.9 |

---

## Task 1: Create feature branch

**Files:** None (git only)

- [ ] **Step 1: Create and switch to feature branch**

```bash
git checkout -b feature/settings-page
```

- [ ] **Step 2: Verify branch**

```bash
git branch --show-current
```

Expected: `feature/settings-page`

---

## Task 2: Store `user_id` on guestbook entries and testimonials

Guestbook entries and testimonials don't currently store `user_id`, which blocks the activity queries. Fix this first.

**Files:**
- Modify: `backend/models/guestbook.py:23-41`
- Modify: `backend/routes/guestbook.py:20-35`
- Modify: `backend/models/testimonials.py:7-28`
- Modify: `backend/routes/testimonials.py`
- Test: `backend/tests/test_settings.py` (new file)

- [ ] **Step 1: Write failing test for guestbook user_id storage**

Create `backend/tests/test_settings.py`:

```python
import json
from tests.conftest import make_event
from auth import make_jwt


def _register_and_verify(ddb_table, mocker):
    """Helper: register a user, verify email, return (user_id, jwt_token)."""
    mocker.patch("routes.auth_routes._send_verification_email")
    from router import route
    from models.users import get_user_by_email, mark_email_verified
    route(make_event("POST", "/auth/register", body={
        "email": "test@example.com", "password": "Secure123!",
        "name": "Test User", "identity": "Other",
    }))
    user = get_user_by_email("test@example.com")
    mark_email_verified(user["user_id"])
    token = make_jwt(user["user_id"], "user")
    return user["user_id"], token


def test_guestbook_entry_stores_user_id(ddb_table, mocker):
    user_id, token = _register_and_verify(ddb_table, mocker)
    from router import route
    resp = route(make_event("POST", "/guestbook",
        body={"name": "Test", "message": "Hello!"},
        headers={"authorization": f"Bearer {token}"}))
    assert resp["statusCode"] == 201
    body = json.loads(resp["body"])
    assert body["data"].get("user_id") == user_id
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/test_settings.py::test_guestbook_entry_stores_user_id -v
```

Expected: FAIL — `user_id` not in guestbook entry response.

- [ ] **Step 3: Update guestbook model to accept user_id**

In `backend/models/guestbook.py`, change `create_entry` signature and body:

```python
def create_entry(name: str, message: str, is_authenticated: bool, identity: str | None = None, user_id: str | None = None) -> dict:
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
    if user_id:
        item["user_id"] = user_id
    table.put_item(Item=item)
    result = dict(item)
    result.pop("PK", None)
    return result
```

- [ ] **Step 4: Update guestbook route to pass user_id**

In `backend/routes/guestbook.py`, update `create_entry`:

```python
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
        entry = g.create_entry(display_name, message, True, identity, user_id=user["sub"])
    else:
        entry = g.create_entry(f"{name} (guest)", message, False)

    return created(entry)
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd backend && pytest tests/test_settings.py::test_guestbook_entry_stores_user_id -v
```

Expected: PASS

- [ ] **Step 6: Write failing test for testimonial user_id storage**

Add to `backend/tests/test_settings.py`:

```python
def test_testimonial_stores_user_id(ddb_table, mocker):
    user_id, token = _register_and_verify(ddb_table, mocker)
    from router import route
    resp = route(make_event("POST", "/testimonials",
        body={"body": "Great portfolio!", "author": "Test", "identity": "Other", "anonymous": False},
        headers={"authorization": f"Bearer {token}"}))
    assert resp["statusCode"] == 201
    body = json.loads(resp["body"])
    assert body["data"].get("user_id") == user_id
```

- [ ] **Step 7: Run test to verify it fails**

```bash
cd backend && pytest tests/test_settings.py::test_testimonial_stores_user_id -v
```

Expected: FAIL

- [ ] **Step 8: Update testimonial model to accept user_id**

In `backend/models/testimonials.py`, update `create_testimonial`:

```python
def create_testimonial(body_text: str, author: str, identity: str, anonymous: bool, user_id: str | None = None) -> dict:
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
    if user_id:
        item["user_id"] = user_id
    table.put_item(Item=item)
    result = dict(item)
    result.pop("PK", None)
    result.pop("SK", None)
    return result
```

- [ ] **Step 9: Update testimonial route to pass user_id**

Read `backend/routes/testimonials.py` and update `submit_testimonial` to extract user from headers and pass `user_id`:

```python
from auth import get_current_user

def submit_testimonial(event, path_params, body, query, headers):
    text = (body.get("body") or "").strip()
    author = (body.get("author") or "").strip()
    identity = body.get("identity", "Other")
    anonymous = bool(body.get("anonymous", False))
    if not text or not author:
        return bad_request("body and author are required")

    user = get_current_user(headers)
    uid = user["sub"] if user else None
    testimonial = t.create_testimonial(text, author, identity, anonymous, user_id=uid)
    return created(testimonial)
```

- [ ] **Step 10: Run all tests**

```bash
cd backend && pytest tests/test_settings.py -v
```

Expected: Both tests PASS

- [ ] **Step 11: Run full test suite to check no regressions**

```bash
cd backend && pytest tests/ -v
```

Expected: All existing tests still pass.

- [ ] **Step 12: Commit**

```bash
git add backend/models/guestbook.py backend/routes/guestbook.py backend/models/testimonials.py backend/routes/testimonials.py backend/tests/test_settings.py
git commit -m "feat: store user_id on guestbook entries and testimonials"
```

---

## Task 3: Add `has_password` to GET /auth/me and user model helpers

**Files:**
- Modify: `backend/models/users.py`
- Modify: `backend/routes/auth_routes.py:182-185`
- Test: `backend/tests/test_settings.py`

- [ ] **Step 1: Write failing test**

Add to `backend/tests/test_settings.py`:

```python
def test_get_me_includes_has_password(ddb_table, mocker):
    user_id, token = _register_and_verify(ddb_table, mocker)
    from router import route
    resp = route(make_event("GET", "/auth/me",
        headers={"authorization": f"Bearer {token}"}))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["data"]["has_password"] is True


def test_get_me_has_password_false_for_oauth_user(ddb_table, mocker):
    from models.users import create_user, mark_email_verified
    user = create_user("oauth@example.com", "OAuth User", "Other")  # no password
    mark_email_verified(user["user_id"])
    token = make_jwt(user["user_id"], "user")
    from router import route
    resp = route(make_event("GET", "/auth/me",
        headers={"authorization": f"Bearer {token}"}))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["data"]["has_password"] is False
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && pytest tests/test_settings.py::test_get_me_includes_has_password tests/test_settings.py::test_get_me_has_password_false_for_oauth_user -v
```

Expected: FAIL — `has_password` key not in response.

- [ ] **Step 3: Add has_password helper to users model**

In `backend/models/users.py`, add a function to check if user has a password, and modify `get_user_by_id` to include it:

```python
def user_has_password(user_id: str) -> bool:
    """Check if user has a password set (without exposing the hash)."""
    table = get_table()
    resp = table.get_item(Key={"PK": f"USER#{user_id}", "SK": "PROFILE"})
    item = resp.get("Item")
    if not item:
        return False
    return bool(item.get("password_hash"))
```

- [ ] **Step 4: Update get_me to include has_password**

In `backend/routes/auth_routes.py`, update `get_me`:

```python
@require_auth
def get_me(event, path_params, body, query, headers, user):
    from models.users import user_has_password
    profile = get_user_by_id(user["sub"])
    if profile:
        profile["has_password"] = user_has_password(user["sub"])
    return ok(profile)
```

- [ ] **Step 5: Run tests**

```bash
cd backend && pytest tests/test_settings.py::test_get_me_includes_has_password tests/test_settings.py::test_get_me_has_password_false_for_oauth_user -v
```

Expected: PASS

- [ ] **Step 6: Run full test suite**

```bash
cd backend && pytest tests/ -v
```

Expected: All pass.

- [ ] **Step 7: Commit**

```bash
git add backend/models/users.py backend/routes/auth_routes.py backend/tests/test_settings.py
git commit -m "feat: add has_password field to GET /auth/me response"
```

---

## Task 4: Activity endpoints — list user's comments, ratings, quiz scores, guestbook, testimonials

**Files:**
- Create: `backend/models/settings.py`
- Create: `backend/routes/settings_routes.py`
- Modify: `backend/router.py`
- Test: `backend/tests/test_settings.py`

- [ ] **Step 1: Write failing tests for activity endpoints**

Add to `backend/tests/test_settings.py`:

```python
def test_get_my_comments(ddb_table, mocker):
    user_id, token = _register_and_verify(ddb_table, mocker)
    from router import route
    # Create a project first (need admin)
    admin_token = make_jwt(user_id, "admin")
    route(make_event("POST", "/projects",
        body={"title": "Test Project", "description": "desc", "tech_stack": ["Python"]},
        headers={"authorization": f"Bearer {admin_token}"}))
    # Get project id
    projects = json.loads(route(make_event("GET", "/projects"))["body"])["data"]
    pid = projects[0]["project_id"]
    # Post a comment
    route(make_event("POST", f"/projects/{pid}/comments",
        body={"body": "Great project!"},
        headers={"authorization": f"Bearer {token}"}))

    resp = route(make_event("GET", "/auth/me/comments",
        headers={"authorization": f"Bearer {token}"}))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert len(body["data"]) == 1
    assert body["data"][0]["body"] == "Great project!"


def test_get_my_ratings(ddb_table, mocker):
    user_id, token = _register_and_verify(ddb_table, mocker)
    from router import route
    admin_token = make_jwt(user_id, "admin")
    route(make_event("POST", "/projects",
        body={"title": "Test Project", "description": "desc", "tech_stack": ["Python"]},
        headers={"authorization": f"Bearer {admin_token}"}))
    projects = json.loads(route(make_event("GET", "/projects"))["body"])["data"]
    pid = projects[0]["project_id"]
    route(make_event("POST", f"/projects/{pid}/ratings",
        body={"stars": 5},
        headers={"authorization": f"Bearer {token}"}))

    resp = route(make_event("GET", "/auth/me/ratings",
        headers={"authorization": f"Bearer {token}"}))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert len(body["data"]) == 1
    assert body["data"][0]["stars"] == 5


def test_get_my_quiz_scores(ddb_table, mocker):
    user_id, token = _register_and_verify(ddb_table, mocker)
    from models.quiz import save_score
    save_score(user_id, 8, 10)
    save_score(user_id, 6, 10)
    from router import route
    resp = route(make_event("GET", "/auth/me/quiz-scores",
        headers={"authorization": f"Bearer {token}"}))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert len(body["data"]) == 2


def test_get_my_guestbook_entries(ddb_table, mocker):
    user_id, token = _register_and_verify(ddb_table, mocker)
    from router import route
    route(make_event("POST", "/guestbook",
        body={"name": "Test", "message": "Hello!"},
        headers={"authorization": f"Bearer {token}"}))
    route(make_event("POST", "/guestbook",
        body={"name": "Test", "message": "Second entry!"},
        headers={"authorization": f"Bearer {token}"}))

    resp = route(make_event("GET", "/auth/me/guestbook-entries",
        headers={"authorization": f"Bearer {token}"}))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert len(body["data"]) == 2


def test_get_my_testimonials(ddb_table, mocker):
    user_id, token = _register_and_verify(ddb_table, mocker)
    from router import route
    route(make_event("POST", "/testimonials",
        body={"body": "Awesome!", "author": "Test", "identity": "Other", "anonymous": False},
        headers={"authorization": f"Bearer {token}"}))

    resp = route(make_event("GET", "/auth/me/testimonials",
        headers={"authorization": f"Bearer {token}"}))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert len(body["data"]) == 1


def test_activity_requires_auth(ddb_table):
    from router import route
    for path in ["/auth/me/comments", "/auth/me/ratings", "/auth/me/quiz-scores",
                 "/auth/me/guestbook-entries", "/auth/me/testimonials"]:
        resp = route(make_event("GET", path))
        assert resp["statusCode"] == 401, f"{path} should require auth"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && pytest tests/test_settings.py::test_get_my_comments -v
```

Expected: FAIL — route not found (404).

- [ ] **Step 3: Create settings model**

Create `backend/models/settings.py`:

```python
from db import get_table
from boto3.dynamodb.conditions import Key, Attr


def get_user_comments(user_id: str) -> list:
    """Scan all comments by this user across all entities."""
    table = get_table()
    resp = table.scan(
        FilterExpression=Attr("SK").begins_with("COMMENT#") & Attr("user_id").eq(user_id),
    )
    items = resp.get("Items", [])
    for item in items:
        item.pop("PK", None)
    return sorted(items, key=lambda x: x.get("created_at", 0), reverse=True)


def get_user_ratings(user_id: str) -> list:
    """Scan all ratings by this user."""
    table = get_table()
    resp = table.scan(
        FilterExpression=Attr("SK").begins_with("RATING#") & Attr("user_id").eq(user_id),
    )
    items = resp.get("Items", [])
    for item in items:
        item.pop("PK", None)
    return sorted(items, key=lambda x: x.get("created_at", 0), reverse=True)


def get_user_quiz_scores(user_id: str) -> list:
    """Query quiz scores for a user (keyed by PK=USER#{user_id})."""
    table = get_table()
    resp = table.query(
        KeyConditionExpression=Key("PK").eq(f"USER#{user_id}") & Key("SK").begins_with("QUIZ_SCORE#"),
    )
    items = resp.get("Items", [])
    for item in items:
        item.pop("PK", None)
        item.pop("SK", None)
        item.pop("GSI3PK", None)
        item.pop("GSI3SK", None)
    return sorted(items, key=lambda x: x.get("created_at", 0), reverse=True)


def get_user_guestbook_entries(user_id: str) -> list:
    """Scan guestbook entries by this user."""
    table = get_table()
    resp = table.scan(
        FilterExpression=Attr("PK").eq("GUESTBOOK") & Attr("user_id").eq(user_id),
    )
    items = resp.get("Items", [])
    for item in items:
        item.pop("PK", None)
    return sorted(items, key=lambda x: x.get("created_at", 0), reverse=True)


def get_user_testimonials(user_id: str) -> list:
    """Scan testimonials by this user."""
    table = get_table()
    resp = table.scan(
        FilterExpression=Attr("PK").eq("TESTIMONIALS") & Attr("user_id").eq(user_id),
    )
    items = resp.get("Items", [])
    for item in items:
        item.pop("PK", None)
        item.pop("SK", None)
        item.pop("GSI2PK", None)
        item.pop("GSI2SK", None)
    return sorted(items, key=lambda x: x.get("created_at", 0), reverse=True)
```

- [ ] **Step 4: Create settings routes (activity handlers)**

Create `backend/routes/settings_routes.py`:

```python
from auth import require_auth
from models import settings as s
from utils import ok


@require_auth
def get_my_comments(event, path_params, body, query, headers, user):
    return ok(s.get_user_comments(user["sub"]))


@require_auth
def get_my_ratings(event, path_params, body, query, headers, user):
    return ok(s.get_user_ratings(user["sub"]))


@require_auth
def get_my_quiz_scores(event, path_params, body, query, headers, user):
    return ok(s.get_user_quiz_scores(user["sub"]))


@require_auth
def get_my_guestbook_entries(event, path_params, body, query, headers, user):
    return ok(s.get_user_guestbook_entries(user["sub"]))


@require_auth
def get_my_testimonials(event, path_params, body, query, headers, user):
    return ok(s.get_user_testimonials(user["sub"]))
```

- [ ] **Step 5: Register routes in router.py**

In `backend/router.py`, add the import and routes. In the imports section, add `settings_routes` to the import block:

```python
from routes import (
    meta, content, projects, courses, github,
    auth_routes, comments, ratings, guestbook,
    quiz, testimonials, stats, contact, admin, docs, visits,
    settings_routes,
)
```

Add these routes in the ROUTES list after the existing `/auth/me` PUT route:

```python
        # Settings — activity
        ("GET",    "/auth/me/comments",               settings_routes.get_my_comments),
        ("GET",    "/auth/me/ratings",                 settings_routes.get_my_ratings),
        ("GET",    "/auth/me/quiz-scores",             settings_routes.get_my_quiz_scores),
        ("GET",    "/auth/me/guestbook-entries",       settings_routes.get_my_guestbook_entries),
        ("GET",    "/auth/me/testimonials",            settings_routes.get_my_testimonials),
```

**Important:** These must come BEFORE the `("GET", "/auth/me", ...)` route because `/auth/me/comments` is more specific. Move the existing `/auth/me` GET and PUT routes after the settings routes, or use regex. Since the router matches exact strings first and then regex, and these are all exact strings, just make sure the more-specific `/auth/me/*` routes appear first in the list.

- [ ] **Step 6: Run activity tests**

```bash
cd backend && pytest tests/test_settings.py -v
```

Expected: All activity tests PASS.

- [ ] **Step 7: Run full test suite**

```bash
cd backend && pytest tests/ -v
```

Expected: All pass.

- [ ] **Step 8: Commit**

```bash
git add backend/models/settings.py backend/routes/settings_routes.py backend/router.py backend/tests/test_settings.py
git commit -m "feat: add activity endpoints for user comments, ratings, quiz scores, guestbook, testimonials"
```

---

## Task 5: Delete own comment and guestbook entry endpoints

**Files:**
- Modify: `backend/models/settings.py`
- Modify: `backend/routes/settings_routes.py`
- Modify: `backend/router.py`
- Test: `backend/tests/test_settings.py`

- [ ] **Step 1: Write failing tests**

Add to `backend/tests/test_settings.py`:

```python
def test_delete_own_comment(ddb_table, mocker):
    user_id, token = _register_and_verify(ddb_table, mocker)
    from router import route
    admin_token = make_jwt(user_id, "admin")
    route(make_event("POST", "/projects",
        body={"title": "Test", "description": "desc", "tech_stack": ["Python"]},
        headers={"authorization": f"Bearer {admin_token}"}))
    projects = json.loads(route(make_event("GET", "/projects"))["body"])["data"]
    pid = projects[0]["project_id"]
    route(make_event("POST", f"/projects/{pid}/comments",
        body={"body": "My comment"},
        headers={"authorization": f"Bearer {token}"}))

    comments = json.loads(route(make_event("GET", "/auth/me/comments",
        headers={"authorization": f"Bearer {token}"}))["body"])["data"]
    comment_id = comments[0]["comment_id"]

    resp = route(make_event("DELETE", f"/auth/me/comments/{comment_id}",
        headers={"authorization": f"Bearer {token}"}))
    assert resp["statusCode"] == 200

    # Verify deleted
    remaining = json.loads(route(make_event("GET", "/auth/me/comments",
        headers={"authorization": f"Bearer {token}"}))["body"])["data"]
    assert len(remaining) == 0


def test_delete_own_guestbook_entry(ddb_table, mocker):
    user_id, token = _register_and_verify(ddb_table, mocker)
    from router import route
    route(make_event("POST", "/guestbook",
        body={"name": "Test", "message": "Hello!"},
        headers={"authorization": f"Bearer {token}"}))

    entries = json.loads(route(make_event("GET", "/auth/me/guestbook-entries",
        headers={"authorization": f"Bearer {token}"}))["body"])["data"]
    entry_id = entries[0]["entry_id"]

    resp = route(make_event("DELETE", f"/auth/me/guestbook-entries/{entry_id}",
        headers={"authorization": f"Bearer {token}"}))
    assert resp["statusCode"] == 200

    remaining = json.loads(route(make_event("GET", "/auth/me/guestbook-entries",
        headers={"authorization": f"Bearer {token}"}))["body"])["data"]
    assert len(remaining) == 0


def test_cannot_delete_other_users_comment(ddb_table, mocker):
    user_id, token = _register_and_verify(ddb_table, mocker)
    # Create another user
    mocker.patch("routes.auth_routes._send_verification_email")
    from router import route
    from models.users import get_user_by_email, mark_email_verified, create_user
    user2 = create_user("other@example.com", "Other User", "Other", "Secure123!")
    mark_email_verified(user2["user_id"])
    token2 = make_jwt(user2["user_id"], "user")

    # user1 creates a project and comment
    admin_token = make_jwt(user_id, "admin")
    route(make_event("POST", "/projects",
        body={"title": "Test", "description": "desc", "tech_stack": ["Python"]},
        headers={"authorization": f"Bearer {admin_token}"}))
    projects = json.loads(route(make_event("GET", "/projects"))["body"])["data"]
    pid = projects[0]["project_id"]
    route(make_event("POST", f"/projects/{pid}/comments",
        body={"body": "User1 comment"},
        headers={"authorization": f"Bearer {token}"}))

    comments = json.loads(route(make_event("GET", "/auth/me/comments",
        headers={"authorization": f"Bearer {token}"}))["body"])["data"]
    comment_id = comments[0]["comment_id"]

    # user2 tries to delete user1's comment
    resp = route(make_event("DELETE", f"/auth/me/comments/{comment_id}",
        headers={"authorization": f"Bearer {token2}"}))
    assert resp["statusCode"] == 404
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && pytest tests/test_settings.py::test_delete_own_comment -v
```

Expected: FAIL — route not found.

- [ ] **Step 3: Add delete functions to settings model**

Add to `backend/models/settings.py`:

```python
def delete_user_comment(user_id: str, comment_id: str) -> bool:
    """Find and delete a comment owned by this user. Returns True if found and deleted."""
    table = get_table()
    resp = table.scan(
        FilterExpression=Attr("SK").begins_with("COMMENT#") & Attr("comment_id").eq(comment_id) & Attr("user_id").eq(user_id),
    )
    items = resp.get("Items", [])
    if not items:
        return False
    item = items[0]
    table.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})
    return True


def delete_user_guestbook_entry(user_id: str, entry_id: str) -> bool:
    """Find and delete a guestbook entry owned by this user."""
    table = get_table()
    resp = table.scan(
        FilterExpression=Attr("PK").eq("GUESTBOOK") & Attr("entry_id").eq(entry_id) & Attr("user_id").eq(user_id),
    )
    items = resp.get("Items", [])
    if not items:
        return False
    item = items[0]
    table.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})
    return True
```

- [ ] **Step 4: Add route handlers**

Add to `backend/routes/settings_routes.py`:

```python
from utils import ok, not_found


@require_auth
def delete_my_comment(event, path_params, body, query, headers, user):
    comment_id = path_params["id"]
    if s.delete_user_comment(user["sub"], comment_id):
        return ok({"deleted": True})
    return not_found("Comment not found")


@require_auth
def delete_my_guestbook_entry(event, path_params, body, query, headers, user):
    entry_id = path_params["id"]
    if s.delete_user_guestbook_entry(user["sub"], entry_id):
        return ok({"deleted": True})
    return not_found("Guestbook entry not found")
```

Update the imports at the top of `settings_routes.py` to include `not_found`:

```python
from utils import ok, not_found
```

- [ ] **Step 5: Register delete routes in router.py**

Add to the settings routes section in `backend/router.py`:

```python
        ("DELETE", r"/auth/me/comments/(?P<id>[^/]+)$",          settings_routes.delete_my_comment),
        ("DELETE", r"/auth/me/guestbook-entries/(?P<id>[^/]+)$",  settings_routes.delete_my_guestbook_entry),
```

- [ ] **Step 6: Run tests**

```bash
cd backend && pytest tests/test_settings.py::test_delete_own_comment tests/test_settings.py::test_delete_own_guestbook_entry tests/test_settings.py::test_cannot_delete_other_users_comment -v
```

Expected: All PASS.

- [ ] **Step 7: Run full test suite**

```bash
cd backend && pytest tests/ -v
```

Expected: All pass.

- [ ] **Step 8: Commit**

```bash
git add backend/models/settings.py backend/routes/settings_routes.py backend/router.py backend/tests/test_settings.py
git commit -m "feat: add delete own comment and guestbook entry endpoints"
```

---

## Task 6: OAuth connections — list, disconnect, connect (link mode)

**Files:**
- Modify: `backend/models/settings.py`
- Modify: `backend/routes/settings_routes.py`
- Modify: `backend/routes/auth_routes.py`
- Modify: `backend/models/users.py`
- Modify: `backend/router.py`
- Test: `backend/tests/test_settings.py`

- [ ] **Step 1: Write failing tests**

Add to `backend/tests/test_settings.py`:

```python
def test_get_connections_empty(ddb_table, mocker):
    user_id, token = _register_and_verify(ddb_table, mocker)
    from router import route
    resp = route(make_event("GET", "/auth/me/connections",
        headers={"authorization": f"Bearer {token}"}))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["data"]["providers"] == []


def test_get_connections_with_oauth(ddb_table, mocker):
    user_id, token = _register_and_verify(ddb_table, mocker)
    # Manually insert an OAuth link
    from db import get_table
    table = get_table()
    table.put_item(Item={
        "PK": "OAUTH#github#12345",
        "SK": "LINK",
        "user_id": user_id,
        "provider": "github",
        "provider_id": "12345",
        "provider_username": "testuser",
    })
    from router import route
    resp = route(make_event("GET", "/auth/me/connections",
        headers={"authorization": f"Bearer {token}"}))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert len(body["data"]["providers"]) == 1
    assert body["data"]["providers"][0]["provider"] == "github"


def test_disconnect_oauth_provider(ddb_table, mocker):
    user_id, token = _register_and_verify(ddb_table, mocker)
    from db import get_table
    table = get_table()
    table.put_item(Item={
        "PK": "OAUTH#github#12345",
        "SK": "LINK",
        "user_id": user_id,
        "provider": "github",
        "provider_id": "12345",
    })
    from router import route
    resp = route(make_event("DELETE", "/auth/me/oauth/github",
        headers={"authorization": f"Bearer {token}"}))
    assert resp["statusCode"] == 200
    # Verify it's gone
    conns = json.loads(route(make_event("GET", "/auth/me/connections",
        headers={"authorization": f"Bearer {token}"}))["body"])["data"]
    assert len(conns["providers"]) == 0


def test_disconnect_last_auth_method_rejected(ddb_table, mocker):
    """OAuth-only user cannot disconnect their only provider."""
    from models.users import create_user, mark_email_verified
    user = create_user("oauth@example.com", "OAuth User", "Other")  # no password
    mark_email_verified(user["user_id"])
    token = make_jwt(user["user_id"], "user")
    from db import get_table
    table = get_table()
    table.put_item(Item={
        "PK": "OAUTH#github#12345",
        "SK": "LINK",
        "user_id": user["user_id"],
        "provider": "github",
        "provider_id": "12345",
    })
    from router import route
    resp = route(make_event("DELETE", "/auth/me/oauth/github",
        headers={"authorization": f"Bearer {token}"}))
    assert resp["statusCode"] == 400
    body = json.loads(resp["body"])
    assert "last" in body["error"].lower() or "sign-in" in body["error"].lower()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && pytest tests/test_settings.py::test_get_connections_empty -v
```

Expected: FAIL — route not found.

- [ ] **Step 3: Add OAuth link model functions**

Add to `backend/models/settings.py`:

```python
def get_user_oauth_links(user_id: str) -> list:
    """Scan for all OAuth links belonging to this user."""
    table = get_table()
    resp = table.scan(
        FilterExpression=Attr("SK").eq("LINK") & Attr("user_id").eq(user_id),
    )
    items = resp.get("Items", [])
    return [
        {
            "provider": item.get("provider"),
            "provider_id": item.get("provider_id"),
            "provider_username": item.get("provider_username"),
        }
        for item in items
    ]


def delete_oauth_link(user_id: str, provider: str) -> bool:
    """Delete OAuth link for a specific provider. Returns True if found and deleted."""
    table = get_table()
    resp = table.scan(
        FilterExpression=Attr("SK").eq("LINK") & Attr("user_id").eq(user_id) & Attr("provider").eq(provider),
    )
    items = resp.get("Items", [])
    if not items:
        return False
    table.delete_item(Key={"PK": items[0]["PK"], "SK": items[0]["SK"]})
    return True
```

- [ ] **Step 4: Add connection route handlers**

Add to `backend/routes/settings_routes.py`:

```python
from utils import ok, not_found, bad_request
from models.users import user_has_password


@require_auth
def get_connections(event, path_params, body, query, headers, user):
    providers = s.get_user_oauth_links(user["sub"])
    return ok({"providers": providers})


@require_auth
def disconnect_oauth(event, path_params, body, query, headers, user):
    provider = path_params["provider"]
    if provider not in ("github", "google"):
        return bad_request("Invalid provider")

    # Check if this would leave user with no auth method
    has_pw = user_has_password(user["sub"])
    links = s.get_user_oauth_links(user["sub"])
    other_links = [l for l in links if l["provider"] != provider]
    if not has_pw and len(other_links) == 0:
        return bad_request("Cannot disconnect your last sign-in method. Set a password or connect another provider first.")

    if s.delete_oauth_link(user["sub"], provider):
        return ok({"disconnected": True})
    return not_found("Provider not connected")
```

- [ ] **Step 5: Register routes in router.py**

Add to settings routes in `backend/router.py`:

```python
        ("GET",    "/auth/me/connections",                        settings_routes.get_connections),
        ("DELETE", r"/auth/me/oauth/(?P<provider>[^/]+)$",        settings_routes.disconnect_oauth),
```

- [ ] **Step 6: Run OAuth tests**

```bash
cd backend && pytest tests/test_settings.py::test_get_connections_empty tests/test_settings.py::test_get_connections_with_oauth tests/test_settings.py::test_disconnect_oauth_provider tests/test_settings.py::test_disconnect_last_auth_method_rejected -v
```

Expected: All PASS.

- [ ] **Step 7: Modify OAuth init and callback for link mode**

In `backend/routes/auth_routes.py`, update `oauth_github_init` to accept link mode:

```python
def oauth_github_init(event, path_params, body, query, headers):
    client_id = os.environ["GITHUB_OAUTH_CLIENT_ID"]
    link_mode = query.get("link") == "true"
    state_data = {"csrf": os.urandom(16).hex()}
    if link_mode:
        # Token comes as query param (browser redirect, not AJAX)
        token_str = query.get("token", "")
        from auth import decode_jwt
        user = decode_jwt(token_str) if token_str else None
        if user:
            state_data["link_user_id"] = user["sub"]
    state = json.dumps(state_data)
    import base64
    state_b64 = base64.urlsafe_b64encode(state.encode()).decode()
    url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={client_id}&scope=user:email&state={state_b64}"
    )
    return {
        "statusCode": 302,
        "headers": {"Location": url, "Access-Control-Allow-Origin": "*"},
        "body": "",
    }
```

Update `oauth_github_callback` to handle link mode:

```python
def oauth_github_callback(event, path_params, body, query, headers):
    code = query.get("code", "")
    if not code:
        return _oauth_error_redirect("GitHub login failed")

    # Decode state for link mode
    link_user_id = None
    state_raw = query.get("state", "")
    if state_raw:
        try:
            import base64
            state_data = json.loads(base64.urlsafe_b64decode(state_raw + "==").decode())
            link_user_id = state_data.get("link_user_id")
        except Exception:
            pass

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
        return _oauth_error_redirect("GitHub login failed")

    user_resp = http.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {gh_token}", "Accept": "application/vnd.github+json"},
        timeout=10,
    )
    gh_user = user_resp.json()

    email = gh_user.get("email")
    if not email:
        emails_resp = http.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {gh_token}", "Accept": "application/vnd.github+json"},
            timeout=10,
        )
        primary = next((e for e in emails_resp.json() if e.get("primary")), None)
        email = primary["email"] if primary else f"{gh_user['login']}@github.noemail"

    if link_user_id:
        # Link mode: connect this provider to existing user
        from db import get_table
        table = get_table()
        table.put_item(Item={
            "PK": f"OAUTH#github#{gh_user['id']}",
            "SK": "LINK",
            "user_id": link_user_id,
            "provider": "github",
            "provider_id": str(gh_user["id"]),
            "provider_username": gh_user.get("login", ""),
        })
        user = get_user_by_id(link_user_id)
    else:
        user = get_or_create_oauth_user("github", str(gh_user["id"]), email, gh_user.get("name") or gh_user["login"])

    access_token = make_jwt(user["user_id"], user["role"])
    refresh_token = create_refresh_token(user["user_id"], user["role"])
    return _oauth_redirect(access_token, refresh_token)
```

Apply the same pattern to `oauth_google_init` and `oauth_google_callback`:

In `oauth_google_init`:

```python
def oauth_google_init(event, path_params, body, query, headers):
    client_id = os.environ["GOOGLE_OAUTH_CLIENT_ID"]
    redirect_uri = _google_redirect_uri(event)
    link_mode = query.get("link") == "true"
    state_data = {}
    if link_mode:
        token_str = query.get("token", "")
        from auth import decode_jwt
        user = decode_jwt(token_str) if token_str else None
        if user:
            state_data["link_user_id"] = user["sub"]
    import base64
    state_b64 = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode() if state_data else ""
    state_param = f"&state={state_b64}" if state_b64 else ""
    url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
        f"{state_param}"
    )
    return {
        "statusCode": 302,
        "headers": {"Location": url, "Access-Control-Allow-Origin": "*"},
        "body": "",
    }
```

In `oauth_google_callback`, add link mode handling after getting `google_id`, `email`, `name`:

```python
    link_user_id = None
    state_raw = query.get("state", "")
    if state_raw:
        try:
            import base64
            state_data = json.loads(base64.urlsafe_b64decode(state_raw + "==").decode())
            link_user_id = state_data.get("link_user_id")
        except Exception:
            pass

    if link_user_id:
        from db import get_table
        table = get_table()
        table.put_item(Item={
            "PK": f"OAUTH#google#{google_id}",
            "SK": "LINK",
            "user_id": link_user_id,
            "provider": "google",
            "provider_id": google_id,
            "provider_username": email,
        })
        user = get_user_by_id(link_user_id)
    else:
        user = get_or_create_oauth_user("google", google_id, email, name)
```

- [ ] **Step 8: Run full test suite**

```bash
cd backend && pytest tests/ -v
```

Expected: All pass.

- [ ] **Step 9: Commit**

```bash
git add backend/models/settings.py backend/routes/settings_routes.py backend/routes/auth_routes.py backend/router.py backend/tests/test_settings.py
git commit -m "feat: add OAuth connection management — list, disconnect, link mode"
```

---

## Task 7: Account deletion with anonymization

**Files:**
- Modify: `backend/models/settings.py`
- Modify: `backend/routes/settings_routes.py`
- Modify: `backend/router.py`
- Test: `backend/tests/test_settings.py`

- [ ] **Step 1: Write failing tests**

Add to `backend/tests/test_settings.py`:

```python
def test_delete_account_anonymizes_comments(ddb_table, mocker):
    user_id, token = _register_and_verify(ddb_table, mocker)
    from router import route
    admin_token = make_jwt(user_id, "admin")
    route(make_event("POST", "/projects",
        body={"title": "Test", "description": "desc", "tech_stack": ["Python"]},
        headers={"authorization": f"Bearer {admin_token}"}))
    projects = json.loads(route(make_event("GET", "/projects"))["body"])["data"]
    pid = projects[0]["project_id"]
    route(make_event("POST", f"/projects/{pid}/comments",
        body={"body": "My comment"},
        headers={"authorization": f"Bearer {token}"}))

    # Delete account
    resp = route(make_event("DELETE", "/auth/me",
        body={"confirmation": "DELETE"},
        headers={"authorization": f"Bearer {token}"}))
    assert resp["statusCode"] == 200

    # Comment should still exist but anonymized
    comments = json.loads(route(make_event("GET", f"/projects/{pid}/comments"))["body"])["data"]
    assert len(comments) == 1
    assert comments[0]["name"] == "Deleted User"
    assert comments[0].get("user_id") is None


def test_delete_account_removes_user_profile(ddb_table, mocker):
    user_id, token = _register_and_verify(ddb_table, mocker)
    from router import route
    resp = route(make_event("DELETE", "/auth/me",
        body={"confirmation": "DELETE"},
        headers={"authorization": f"Bearer {token}"}))
    assert resp["statusCode"] == 200
    # User should no longer exist
    from models.users import get_user_by_id
    assert get_user_by_id(user_id) is None


def test_delete_account_requires_confirmation(ddb_table, mocker):
    user_id, token = _register_and_verify(ddb_table, mocker)
    from router import route
    resp = route(make_event("DELETE", "/auth/me",
        body={},
        headers={"authorization": f"Bearer {token}"}))
    assert resp["statusCode"] == 400


def test_delete_account_wrong_confirmation(ddb_table, mocker):
    user_id, token = _register_and_verify(ddb_table, mocker)
    from router import route
    resp = route(make_event("DELETE", "/auth/me",
        body={"confirmation": "WRONG"},
        headers={"authorization": f"Bearer {token}"}))
    assert resp["statusCode"] == 400
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && pytest tests/test_settings.py::test_delete_account_anonymizes_comments -v
```

Expected: FAIL — route not found.

- [ ] **Step 3: Add anonymize and delete functions to settings model**

Add to `backend/models/settings.py`:

```python
def anonymize_user_content(user_id: str):
    """Anonymize all content by this user: comments, guestbook, testimonials, ratings, quiz scores."""
    table = get_table()

    # Anonymize comments
    comments = table.scan(
        FilterExpression=Attr("SK").begins_with("COMMENT#") & Attr("user_id").eq(user_id),
    ).get("Items", [])
    for item in comments:
        table.update_item(
            Key={"PK": item["PK"], "SK": item["SK"]},
            UpdateExpression="SET #n = :n, #i = :i REMOVE user_id",
            ExpressionAttributeNames={"#n": "name", "#i": "identity"},
            ExpressionAttributeValues={":n": "Deleted User", ":i": None},
        )

    # Anonymize guestbook entries
    guestbook = table.scan(
        FilterExpression=Attr("PK").eq("GUESTBOOK") & Attr("user_id").eq(user_id),
    ).get("Items", [])
    for item in guestbook:
        table.update_item(
            Key={"PK": item["PK"], "SK": item["SK"]},
            UpdateExpression="SET #n = :n REMOVE identity, user_id",
            ExpressionAttributeNames={"#n": "name"},
            ExpressionAttributeValues={":n": "Deleted User"},
        )

    # Anonymize testimonials
    testimonials = table.scan(
        FilterExpression=Attr("PK").eq("TESTIMONIALS") & Attr("user_id").eq(user_id),
    ).get("Items", [])
    for item in testimonials:
        table.update_item(
            Key={"PK": item["PK"], "SK": item["SK"]},
            UpdateExpression="SET author = :a REMOVE user_id",
            ExpressionAttributeValues={":a": "Deleted User"},
        )

    # Anonymize ratings (keep data, clear user_id)
    ratings = table.scan(
        FilterExpression=Attr("SK").begins_with("RATING#") & Attr("user_id").eq(user_id),
    ).get("Items", [])
    for item in ratings:
        table.update_item(
            Key={"PK": item["PK"], "SK": item["SK"]},
            UpdateExpression="SET user_id = :d",
            ExpressionAttributeValues={":d": "DELETED"},
        )

    # Anonymize quiz scores (keep scores, clear user_id)
    scores = table.query(
        KeyConditionExpression=Key("PK").eq(f"USER#{user_id}") & Key("SK").begins_with("QUIZ_SCORE#"),
    ).get("Items", [])
    for item in scores:
        table.update_item(
            Key={"PK": item["PK"], "SK": item["SK"]},
            UpdateExpression="SET user_id = :d",
            ExpressionAttributeValues={":d": "DELETED"},
        )


def delete_user_oauth_links(user_id: str):
    """Delete all OAuth link records for this user."""
    table = get_table()
    links = table.scan(
        FilterExpression=Attr("SK").eq("LINK") & Attr("user_id").eq(user_id),
    ).get("Items", [])
    for item in links:
        table.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})


def delete_user_sessions(user_id: str):
    """Delete all refresh tokens for this user."""
    table = get_table()
    sessions = table.scan(
        FilterExpression=Attr("SK").eq("SESSION") & Attr("user_id").eq(user_id),
    ).get("Items", [])
    for item in sessions:
        table.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})
```

- [ ] **Step 4: Add delete account route handler**

Add to `backend/routes/settings_routes.py`:

```python
from models.users import delete_user


@require_auth
def delete_account(event, path_params, body, query, headers, user):
    confirmation = body.get("confirmation", "")
    if confirmation != "DELETE":
        return bad_request("Type DELETE to confirm account deletion")
    user_id = user["sub"]
    s.anonymize_user_content(user_id)
    s.delete_user_oauth_links(user_id)
    s.delete_user_sessions(user_id)
    delete_user(user_id)
    return ok({"message": "Account deleted"})
```

- [ ] **Step 5: Register route in router.py**

Add to settings routes in `backend/router.py`:

```python
        ("DELETE", "/auth/me",                                    settings_routes.delete_account),
```

**Important:** This exact-string `/auth/me` DELETE route must be listed in the ROUTES list. Since the router checks exact strings before regex, and the existing GET/PUT `/auth/me` are also exact strings, just add the DELETE alongside them.

- [ ] **Step 6: Run tests**

```bash
cd backend && pytest tests/test_settings.py::test_delete_account_anonymizes_comments tests/test_settings.py::test_delete_account_removes_user_profile tests/test_settings.py::test_delete_account_requires_confirmation tests/test_settings.py::test_delete_account_wrong_confirmation -v
```

Expected: All PASS.

- [ ] **Step 7: Run full test suite**

```bash
cd backend && pytest tests/ -v
```

Expected: All pass.

- [ ] **Step 8: Commit**

```bash
git add backend/models/settings.py backend/routes/settings_routes.py backend/router.py backend/tests/test_settings.py
git commit -m "feat: add account deletion with content anonymization"
```

---

## Task 8: Update OpenAPI/Swagger spec

**Files:**
- Modify: `backend/routes/docs.py`

- [ ] **Step 1: Add new endpoints to the SPEC dict**

In `backend/routes/docs.py`, add these entries to the `"paths"` dict inside `SPEC`:

```python
        "/auth/me/connections": {
            "get": {"summary": "List linked OAuth providers", "tags": ["Settings"],
                    "security": [{"bearerAuth": []}], "responses": {"200": {"description": "OK"}}},
        },
        "/auth/me/oauth/{provider}": {
            "delete": {"summary": "Disconnect OAuth provider", "tags": ["Settings"],
                       "security": [{"bearerAuth": []}],
                       "parameters": [{"name": "provider", "in": "path", "required": True,
                                       "schema": {"type": "string", "enum": ["github", "google"]}}],
                       "responses": {"200": {"description": "OK"}, "400": {"description": "Last auth method"}}},
        },
        "/auth/me/comments": {
            "get": {"summary": "List my comments", "tags": ["Settings"],
                    "security": [{"bearerAuth": []}], "responses": {"200": {"description": "OK"}}},
        },
        "/auth/me/comments/{id}": {
            "delete": {"summary": "Delete my comment", "tags": ["Settings"],
                       "security": [{"bearerAuth": []}], "responses": {"200": {"description": "OK"}}},
        },
        "/auth/me/ratings": {
            "get": {"summary": "List my ratings", "tags": ["Settings"],
                    "security": [{"bearerAuth": []}], "responses": {"200": {"description": "OK"}}},
        },
        "/auth/me/quiz-scores": {
            "get": {"summary": "List my quiz scores", "tags": ["Settings"],
                    "security": [{"bearerAuth": []}], "responses": {"200": {"description": "OK"}}},
        },
        "/auth/me/guestbook-entries": {
            "get": {"summary": "List my guestbook entries", "tags": ["Settings"],
                    "security": [{"bearerAuth": []}], "responses": {"200": {"description": "OK"}}},
        },
        "/auth/me/guestbook-entries/{id}": {
            "delete": {"summary": "Delete my guestbook entry", "tags": ["Settings"],
                       "security": [{"bearerAuth": []}], "responses": {"200": {"description": "OK"}}},
        },
        "/auth/me/testimonials": {
            "get": {"summary": "List my testimonials", "tags": ["Settings"],
                    "security": [{"bearerAuth": []}], "responses": {"200": {"description": "OK"}}},
        },
```

Also update the existing `/auth/me` entry to include the DELETE method:

```python
        "/auth/me": {
            "get": {"summary": "Get current user", "tags": ["Auth"], "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "OK"}}},
            "put": {"summary": "Update profile", "tags": ["Auth"], "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "OK"}}},
            "delete": {"summary": "Delete account (anonymize + remove)", "tags": ["Settings"],
                       "security": [{"bearerAuth": []}],
                       "requestBody": {"required": True, "content": {"application/json": {"schema": {
                           "type": "object", "required": ["confirmation"],
                           "properties": {"confirmation": {"type": "string", "example": "DELETE"}}
                       }}}},
                       "responses": {"200": {"description": "OK"}, "400": {"description": "Missing confirmation"}}},
        },
```

- [ ] **Step 2: Run docs test**

```bash
cd backend && pytest tests/test_docs.py -v
```

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add backend/routes/docs.py
git commit -m "docs: add settings endpoints to OpenAPI spec"
```

---

## Task 9: Frontend — identicon utility

**Files:**
- Create: `frontend/assets/js/identicon.js`

- [ ] **Step 1: Create identicon generator**

Create `frontend/assets/js/identicon.js`. This is a self-contained canvas-based identicon generator — no external libraries:

```javascript
// frontend/assets/js/identicon.js
// Generates GitHub-style geometric identicons from a string hash.

function generateIdenticon(value, size) {
  size = size || 64;
  const hash = hashCode(value || "default");
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");

  // Background
  ctx.fillStyle = "#e1e4e8";
  ctx.fillRect(0, 0, size, size);

  // Derive color from hash
  const hue = Math.abs(hash) % 360;
  const color = `hsl(${hue}, 65%, 50%)`;
  ctx.fillStyle = color;

  // 5x5 grid, mirrored horizontally (only compute left 3 columns)
  const cellSize = size / 5;
  for (let row = 0; row < 5; row++) {
    for (let col = 0; col < 3; col++) {
      // Use different bits of hash for each cell
      const bit = (hash >> (row * 3 + col)) & 1;
      if (bit) {
        ctx.fillRect(col * cellSize, row * cellSize, cellSize, cellSize);
        // Mirror
        if (col < 2) {
          ctx.fillRect((4 - col) * cellSize, row * cellSize, cellSize, cellSize);
        }
      }
    }
  }

  return canvas.toDataURL("image/png");
}

function hashCode(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash |= 0; // Convert to 32-bit int
  }
  return hash;
}

// Helper: create an <img> element with identicon
function identiconImg(value, size, cssClass) {
  const src = generateIdenticon(value, size || 32);
  const img = document.createElement("img");
  img.src = src;
  img.width = size || 32;
  img.height = size || 32;
  img.style.borderRadius = "50%";
  if (cssClass) img.className = cssClass;
  img.alt = "User avatar";
  return img;
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/assets/js/identicon.js
git commit -m "feat: add client-side identicon generator"
```

---

## Task 10: Frontend — settings page component

**Files:**
- Create: `frontend/assets/js/pages/settings.js`

- [ ] **Step 1: Create settings page Alpine component**

Create `frontend/assets/js/pages/settings.js`:

```javascript
// frontend/assets/js/pages/settings.js
function settingsPage() {
  return {
    // Section state
    activeSection: "profile",
    sections: ["profile", "appearance", "connections", "activity", "account"],

    // Profile
    profileForm: { name: "", identity: "Other" },
    profileDirty: false,
    profileSaving: false,
    profileMessage: null,

    // Appearance
    themes: ["light", "dark", "coffee", "terminal", "nordic"],

    // Connections
    connections: [],
    connectionsLoading: true,
    hasPassword: false,

    // Activity
    activityTab: "comments",
    activityData: { comments: [], ratings: [], quiz: [], guestbook: [], testimonials: [] },
    activityCounts: { comments: 0, ratings: 0, quiz: 0, guestbook: 0, testimonials: 0 },
    activityLoading: true,

    // Account
    deleteConfirmation: "",
    deleteError: null,
    deleting: false,

    async init() {
      const app = this.getApp();
      if (!app || !app.user) {
        window.location.hash = "#/login";
        return;
      }
      this.profileForm.name = app.user.name || "";
      this.profileForm.identity = app.user.identity || "Other";
      this.hasPassword = app.user.has_password || false;

      this.setupScrollSpy();
      await Promise.all([this.loadConnections(), this.loadActivity()]);
    },

    getApp() {
      const el = document.querySelector("[x-data]");
      return el?._x_dataStack?.[0];
    },

    // --- Scroll spy ---
    setupScrollSpy() {
      const observer = new IntersectionObserver(
        (entries) => {
          for (const entry of entries) {
            if (entry.isIntersecting) {
              this.activeSection = entry.target.id.replace("settings-", "");
            }
          }
        },
        { rootMargin: "-20% 0px -70% 0px" }
      );
      this.$nextTick(() => {
        this.sections.forEach((s) => {
          const el = document.getElementById(`settings-${s}`);
          if (el) observer.observe(el);
        });
      });
    },

    scrollTo(section) {
      const el = document.getElementById(`settings-${section}`);
      if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    },

    // --- Profile ---
    onProfileChange() {
      const app = this.getApp();
      this.profileDirty =
        this.profileForm.name !== (app?.user?.name || "") ||
        this.profileForm.identity !== (app?.user?.identity || "Other");
    },

    async saveProfile() {
      this.profileSaving = true;
      this.profileMessage = null;
      const resp = await api.put("/auth/me", this.profileForm);
      if (resp.ok) {
        this.profileMessage = { type: "success", text: "Profile updated!" };
        const app = this.getApp();
        if (app) app.user = resp.data;
        this.profileDirty = false;
      } else {
        this.profileMessage = { type: "error", text: resp.error || "Failed to save" };
      }
      this.profileSaving = false;
    },

    // --- Appearance ---
    async selectTheme(theme) {
      const app = this.getApp();
      if (app) {
        app.theme = theme;
        applyTheme(theme);
        await syncThemeToServer(theme);
      }
    },

    // --- Connections ---
    async loadConnections() {
      this.connectionsLoading = true;
      const resp = await api.get("/auth/me/connections");
      if (resp.ok) {
        this.connections = resp.data.providers || [];
      }
      this.connectionsLoading = false;
    },

    isConnected(provider) {
      return this.connections.some((c) => c.provider === provider);
    },

    getProviderUsername(provider) {
      const conn = this.connections.find((c) => c.provider === provider);
      return conn?.provider_username || "";
    },

    connectProvider(provider) {
      const token = localStorage.getItem("access_token");
      window.location.href = `${API_BASE}/auth/oauth/${provider}?link=true&token=${token}`;
    },

    async disconnectProvider(provider) {
      if (!confirm(`Disconnect ${provider}?`)) return;
      const resp = await api.delete(`/auth/me/oauth/${provider}`);
      if (resp.ok) {
        this.connections = this.connections.filter((c) => c.provider !== provider);
      } else {
        alert(resp.error || "Failed to disconnect");
      }
    },

    // --- Activity ---
    async loadActivity() {
      this.activityLoading = true;
      const [comments, ratings, quiz, guestbook, testimonials] = await Promise.all([
        api.get("/auth/me/comments"),
        api.get("/auth/me/ratings"),
        api.get("/auth/me/quiz-scores"),
        api.get("/auth/me/guestbook-entries"),
        api.get("/auth/me/testimonials"),
      ]);
      this.activityData.comments = comments.ok ? comments.data : [];
      this.activityData.ratings = ratings.ok ? ratings.data : [];
      this.activityData.quiz = quiz.ok ? quiz.data : [];
      this.activityData.guestbook = guestbook.ok ? guestbook.data : [];
      this.activityData.testimonials = testimonials.ok ? testimonials.data : [];
      this.activityCounts = {
        comments: this.activityData.comments.length,
        ratings: this.activityData.ratings.length,
        quiz: this.activityData.quiz.length,
        guestbook: this.activityData.guestbook.length,
        testimonials: this.activityData.testimonials.length,
      };
      this.activityLoading = false;
    },

    async deleteComment(commentId) {
      if (!confirm("Delete this comment?")) return;
      const resp = await api.delete(`/auth/me/comments/${commentId}`);
      if (resp.ok) {
        this.activityData.comments = this.activityData.comments.filter((c) => c.comment_id !== commentId);
        this.activityCounts.comments--;
      }
    },

    async deleteGuestbookEntry(entryId) {
      if (!confirm("Delete this guestbook entry?")) return;
      const resp = await api.delete(`/auth/me/guestbook-entries/${entryId}`);
      if (resp.ok) {
        this.activityData.guestbook = this.activityData.guestbook.filter((e) => e.entry_id !== entryId);
        this.activityCounts.guestbook--;
      }
    },

    timeAgo(ts) {
      const diff = Math.floor(Date.now() / 1000) - ts;
      if (diff < 60) return "just now";
      if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
      if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
      if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
      return new Date(ts * 1000).toLocaleDateString();
    },

    // --- Account ---
    async deleteAccount() {
      this.deleteError = null;
      if (this.deleteConfirmation !== "DELETE") {
        this.deleteError = "Type DELETE to confirm";
        return;
      }
      this.deleting = true;
      const resp = await api.delete("/auth/me");
      if (resp.ok) {
        const app = this.getApp();
        if (app) await app.logout();
      } else {
        this.deleteError = resp.error || "Failed to delete account";
        this.deleting = false;
      }
    },
  };
}
```

Note: `api.delete` currently doesn't send a body. We need the DELETE /auth/me to receive `{ confirmation: "DELETE" }`. Update the `api.delete` call in `deleteAccount` to use `apiFetch` directly:

Replace the `deleteAccount` method body with:

```javascript
    async deleteAccount() {
      this.deleteError = null;
      if (this.deleteConfirmation !== "DELETE") {
        this.deleteError = "Type DELETE to confirm";
        return;
      }
      this.deleting = true;
      const resp = await apiFetch("/auth/me", { method: "DELETE", body: { confirmation: "DELETE" } });
      if (resp.ok) {
        const app = this.getApp();
        if (app) await app.logout();
      } else {
        this.deleteError = resp.error || "Failed to delete account";
        this.deleting = false;
      }
    },
```

- [ ] **Step 2: Commit**

```bash
git add frontend/assets/js/pages/settings.js
git commit -m "feat: add settings page Alpine.js component"
```

---

## Task 11: Frontend — update index.html (nav bar, route, settings template)

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/assets/js/app.js`
- Modify: `frontend/assets/css/main.css`

- [ ] **Step 1: Update app.js route table**

In `frontend/assets/js/app.js`, add `settings` to the route table inside `handleRoute`:

```javascript
        "settings":    "settings",
```

Add it after the `"quiz"` line.

- [ ] **Step 2: Update nav bar in index.html**

In `frontend/index.html`, replace the theme toggle button and logout button section. Find this block (approximately lines 76-88):

```html
            <template x-if="!isAuthenticated">
              <a href="#/login" class="btn btn-primary btn-sm">Login</a>
            </template>
            <template x-if="isAuthenticated">
              <button @click="logout()" class="btn btn-outline btn-sm">Logout</button>
            </template>
          </div>

          <button class="theme-toggle" @click="toggleTheme()"
                  :title="`Switch theme (current: ${theme})`"
                  aria-label="Toggle theme">
            <span x-text="{ light: '☀️', dark: '🌙', coffee: '☕', terminal: '>_', nordic: '❄️' }[theme] || '☀️'"></span>
          </button>
```

Replace with:

```html
            <template x-if="!isAuthenticated">
              <a href="#/login" class="btn btn-primary btn-sm">Login</a>
            </template>
            <template x-if="isAuthenticated">
              <a href="#/settings" class="nav-identicon" :title="`Settings (${user.name})`">
                <canvas x-ref="navIdenticon" width="32" height="32" style="border-radius:50%;width:32px;height:32px;"></canvas>
              </a>
            </template>
          </div>

          <template x-if="!isAuthenticated">
            <button class="theme-toggle" @click="toggleTheme()"
                    :title="`Switch theme (current: ${theme})`"
                    aria-label="Toggle theme">
              <span x-text="{ light: '☀️', dark: '🌙', coffee: '☕', terminal: '>_', nordic: '❄️' }[theme] || '☀️'"></span>
            </button>
          </template>
```

Then update the `init()` method in `app.js` to render the identicon after auth is restored. Add at the end of the `if (resp.ok && resp.data)` block:

```javascript
          this.$nextTick(() => {
            const canvas = this.$refs?.navIdenticon;
            if (canvas) this.renderIdenticon(canvas, this.user.user_id, 32);
          });
```

Add a `renderIdenticon` method to `portfolioApp()`:

```javascript
    renderIdenticon(canvas, value, size) {
      const src = generateIdenticon(value, size);
      const img = new Image();
      img.onload = () => {
        const ctx = canvas.getContext("2d");
        ctx.clearRect(0, 0, size, size);
        ctx.drawImage(img, 0, 0, size, size);
      };
      img.src = src;
    },
```

- [ ] **Step 3: Add settings page template to index.html**

In `frontend/index.html`, add the settings page template in the PAGE ROUTER section (after the last existing template, before the closing `</main>`):

```html
      <!-- SETTINGS -->
      <template x-if="currentPage === 'settings'">
        <div class="page" x-data="settingsPage()" x-init="init()">
          <div class="settings-layout">
            <!-- Sidebar / pills -->
            <div class="settings-sidebar">
              <div class="settings-sidebar-title">Settings</div>
              <template x-for="s in sections" :key="s">
                <a class="settings-nav-link"
                   :class="{ active: activeSection === s, danger: s === 'account' }"
                   @click.prevent="scrollTo(s)"
                   :href="'#settings-' + s"
                   x-text="s[0].toUpperCase() + s.slice(1)"></a>
              </template>
            </div>

            <div class="settings-content">
              <!-- PROFILE -->
              <section id="settings-profile" class="settings-section">
                <h2>Profile</h2>
                <p class="subtitle">Manage your personal information</p>

                <div class="settings-profile-header">
                  <canvas x-ref="profileIdenticon" width="52" height="52"
                          x-init="$nextTick(() => { const app = getApp(); if (app?.user) { const src = generateIdenticon(app.user.user_id, 52); const img = new Image(); img.onload = () => { $refs.profileIdenticon.getContext('2d').drawImage(img, 0, 0, 52, 52); }; img.src = src; } })"
                          style="border-radius: 50%; width: 52px; height: 52px;"></canvas>
                  <div>
                    <strong x-text="getApp()?.user?.name || ''"></strong>
                    <div class="text-muted" style="font-size: 0.8rem;">
                      <span x-text="getApp()?.user?.email || ''"></span>
                      <template x-if="getApp()?.user?.created_at">
                        <span> · Member since <span x-text="new Date(getApp().user.created_at * 1000).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })"></span></span>
                      </template>
                    </div>
                  </div>
                </div>

                <div class="settings-form-grid">
                  <div>
                    <label>Display Name</label>
                    <input type="text" x-model="profileForm.name" @input="onProfileChange()" maxlength="100">
                  </div>
                  <div>
                    <label>Identity</label>
                    <select x-model="profileForm.identity" @change="onProfileChange()">
                      <option>Jamf</option><option>MCRI</option><option>Friend</option><option>Family</option><option>Other</option>
                    </select>
                  </div>
                </div>
                <div style="margin-bottom: 1rem;">
                  <label>Email</label>
                  <div class="text-muted" style="font-size: 0.85rem;">
                    <span x-text="getApp()?.user?.email"></span>
                    <span class="badge">read-only</span>
                  </div>
                </div>
                <template x-if="profileMessage">
                  <div class="settings-toast" :class="profileMessage.type" x-text="profileMessage.text"></div>
                </template>
                <button class="btn btn-primary" @click="saveProfile()" :disabled="!profileDirty || profileSaving"
                        x-text="profileSaving ? 'Saving...' : 'Save Changes'"></button>
              </section>

              <hr class="settings-divider">

              <!-- APPEARANCE -->
              <section id="settings-appearance" class="settings-section">
                <h2>Appearance</h2>
                <p class="subtitle">Choose your theme — synced across devices</p>
                <div class="theme-grid">
                  <template x-for="t in themes" :key="t">
                    <div class="theme-card" :class="{ active: getApp()?.theme === t }" @click="selectTheme(t)">
                      <div class="theme-preview" :data-theme-preview="t"></div>
                      <div class="theme-name" x-text="t[0].toUpperCase() + t.slice(1)"></div>
                      <div class="theme-check" x-show="getApp()?.theme === t">✓</div>
                    </div>
                  </template>
                </div>
              </section>

              <hr class="settings-divider">

              <!-- CONNECTIONS -->
              <section id="settings-connections" class="settings-section">
                <h2>Connections</h2>
                <p class="subtitle">Manage sign-in methods — must keep at least one active</p>

                <div x-show="connectionsLoading" class="text-muted">Loading...</div>
                <div x-show="!connectionsLoading">
                  <!-- GitHub -->
                  <div class="connection-card">
                    <div class="connection-info">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
                      <div>
                        <strong>GitHub</strong>
                        <div class="text-muted" x-text="isConnected('github') ? 'Connected as ' + getProviderUsername('github') : 'Not connected'" style="font-size: 0.78rem;"></div>
                      </div>
                    </div>
                    <button x-show="isConnected('github')" class="btn btn-outline btn-sm btn-danger" @click="disconnectProvider('github')">Disconnect</button>
                    <button x-show="!isConnected('github')" class="btn btn-primary btn-sm" @click="connectProvider('github')">Connect</button>
                  </div>

                  <!-- Google -->
                  <div class="connection-card">
                    <div class="connection-info">
                      <svg width="20" height="20" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
                      <div>
                        <strong>Google</strong>
                        <div class="text-muted" x-text="isConnected('google') ? 'Connected as ' + getProviderUsername('google') : 'Not connected'" style="font-size: 0.78rem;"></div>
                      </div>
                    </div>
                    <button x-show="isConnected('google')" class="btn btn-outline btn-sm btn-danger" @click="disconnectProvider('google')">Disconnect</button>
                    <button x-show="!isConnected('google')" class="btn btn-primary btn-sm" @click="connectProvider('google')">Connect</button>
                  </div>

                  <!-- Password -->
                  <div class="connection-card">
                    <div class="connection-info">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
                      <div>
                        <strong>Password</strong>
                        <div class="text-muted" style="font-size: 0.78rem;">
                          <template x-if="hasPassword"><span>Set · <a href="#/forgot-password">Reset via email</a></span></template>
                          <template x-if="!hasPassword"><span>Not set · <a href="#/forgot-password">Set via email</a></span></template>
                        </div>
                      </div>
                    </div>
                    <span x-show="hasPassword" class="text-success" style="font-size: 0.78rem; font-weight: 500;">✓ Active</span>
                  </div>
                </div>
              </section>

              <hr class="settings-divider">

              <!-- ACTIVITY -->
              <section id="settings-activity" class="settings-section">
                <h2>Activity</h2>
                <p class="subtitle">Your contributions across the site</p>

                <div class="activity-tabs">
                  <template x-for="tab in ['comments','ratings','quiz','guestbook','testimonials']" :key="tab">
                    <button class="activity-tab" :class="{ active: activityTab === tab }" @click="activityTab = tab">
                      <span x-text="tab[0].toUpperCase() + tab.slice(1)"></span>
                      <span class="activity-count" x-text="activityCounts[tab]"></span>
                    </button>
                  </template>
                </div>

                <div x-show="activityLoading" class="text-muted">Loading...</div>

                <!-- Comments -->
                <div x-show="activityTab === 'comments' && !activityLoading">
                  <template x-if="activityData.comments.length === 0"><p class="text-muted">No comments yet.</p></template>
                  <template x-for="c in activityData.comments" :key="c.comment_id">
                    <div class="activity-item">
                      <div>
                        <div class="activity-meta">On <strong x-text="c.SK?.split('#')[0] || 'item'"></strong> · <span x-text="timeAgo(c.created_at)"></span></div>
                        <div x-text="c.body"></div>
                      </div>
                      <button class="btn btn-outline btn-sm btn-danger" @click="deleteComment(c.comment_id)">Delete</button>
                    </div>
                  </template>
                </div>

                <!-- Ratings -->
                <div x-show="activityTab === 'ratings' && !activityLoading">
                  <template x-if="activityData.ratings.length === 0"><p class="text-muted">No ratings yet.</p></template>
                  <template x-for="r in activityData.ratings" :key="r.SK">
                    <div class="activity-item">
                      <div>
                        <div class="activity-meta"><span x-text="timeAgo(r.created_at)"></span></div>
                        <div><span x-text="'★'.repeat(r.stars) + '☆'.repeat(5 - r.stars)"></span></div>
                      </div>
                    </div>
                  </template>
                </div>

                <!-- Quiz -->
                <div x-show="activityTab === 'quiz' && !activityLoading">
                  <template x-if="activityData.quiz.length === 0"><p class="text-muted">No quiz attempts yet.</p></template>
                  <template x-for="q in activityData.quiz" :key="q.attempt_id">
                    <div class="activity-item">
                      <div>
                        <div class="activity-meta"><span x-text="timeAgo(q.created_at)"></span></div>
                        <div>Score: <strong x-text="q.score"></strong> / <span x-text="q.total"></span></div>
                      </div>
                    </div>
                  </template>
                </div>

                <!-- Guestbook -->
                <div x-show="activityTab === 'guestbook' && !activityLoading">
                  <template x-if="activityData.guestbook.length === 0"><p class="text-muted">No guestbook entries yet.</p></template>
                  <template x-for="g in activityData.guestbook" :key="g.entry_id">
                    <div class="activity-item">
                      <div>
                        <div class="activity-meta"><span x-text="timeAgo(g.created_at)"></span></div>
                        <div x-text="g.message"></div>
                      </div>
                      <button class="btn btn-outline btn-sm btn-danger" @click="deleteGuestbookEntry(g.entry_id)">Delete</button>
                    </div>
                  </template>
                </div>

                <!-- Testimonials -->
                <div x-show="activityTab === 'testimonials' && !activityLoading">
                  <template x-if="activityData.testimonials.length === 0"><p class="text-muted">No testimonials yet.</p></template>
                  <template x-for="t in activityData.testimonials" :key="t.testimonial_id">
                    <div class="activity-item">
                      <div>
                        <div class="activity-meta">
                          <span class="badge" :class="t.status" x-text="t.status"></span>
                          · <span x-text="timeAgo(t.created_at)"></span>
                        </div>
                        <div x-text="t.body"></div>
                      </div>
                    </div>
                  </template>
                </div>
              </section>

              <hr class="settings-divider">

              <!-- ACCOUNT -->
              <section id="settings-account" class="settings-section">
                <h2>Account</h2>
                <p class="subtitle">Session and account management</p>

                <div class="connection-card" style="margin-bottom: 1.5rem;">
                  <div>
                    <strong>Sign out</strong>
                    <div class="text-muted" style="font-size: 0.78rem;">Sign out of this device</div>
                  </div>
                  <button class="btn btn-primary btn-sm" @click="getApp()?.logout()">Log out</button>
                </div>

                <div class="danger-zone">
                  <h3 style="color: var(--danger);">Danger Zone</h3>
                  <p class="text-muted" style="margin-bottom: 1rem;">Permanently delete your account. Contributions are anonymized to "Deleted User". This cannot be undone.</p>
                  <input type="text" x-model="deleteConfirmation" placeholder='Type "DELETE" to confirm'
                         style="margin-bottom: 0.5rem; max-width: 300px;">
                  <template x-if="deleteError"><div class="settings-toast error" x-text="deleteError"></div></template>
                  <button class="btn btn-danger" @click="deleteAccount()" :disabled="deleting"
                          x-text="deleting ? 'Deleting...' : 'Delete My Account'"></button>
                </div>
              </section>
            </div>
          </div>
        </div>
      </template>
```

- [ ] **Step 4: Add script tags for new JS files in index.html**

In `frontend/index.html`, add the new script tags before the Alpine.js `<script defer>` tag, after the existing page script tags:

```html
  <script src="/assets/js/identicon.js"></script>
  <script src="/assets/js/pages/settings.js"></script>
```

- [ ] **Step 5: Add CSS styles for settings page**

Append to `frontend/assets/css/main.css`:

```css
/* Settings page */
.settings-layout { display: flex; gap: 0; min-height: calc(100vh - 200px); }
.settings-sidebar {
  width: 170px; flex-shrink: 0; padding: 1.25rem 0.75rem;
  position: sticky; top: 80px; align-self: flex-start; height: fit-content;
}
.settings-sidebar-title {
  font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em;
  color: var(--text-muted); margin-bottom: 0.75rem; font-weight: 600;
}
.settings-nav-link {
  display: block; padding: 0.35rem 0.6rem; border-radius: 5px;
  font-size: 0.85rem; margin-bottom: 0.2rem; color: var(--text-muted); cursor: pointer;
}
.settings-nav-link:hover { background: var(--bg-alt); text-decoration: none; }
.settings-nav-link.active { background: var(--accent); color: #fff; }
.settings-nav-link.danger { color: var(--danger, #e74c3c); }
.settings-nav-link.danger.active { background: var(--danger, #e74c3c); color: #fff; }
.settings-content { flex: 1; padding: 1.25rem 0 1.25rem 1.5rem; min-width: 0; }
.settings-section { scroll-margin-top: 100px; }
.settings-section h2 { font-size: 1.1rem; margin-bottom: 0.1rem; }
.settings-divider { border: none; border-top: 1px solid var(--border); margin: 2rem 0; }
.settings-profile-header {
  display: flex; align-items: center; gap: 1rem; margin: 1rem 0 1.25rem;
  padding: 0.85rem; background: var(--bg-alt); border-radius: 8px;
}
.settings-form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.85rem; margin-bottom: 0.85rem; }
.settings-form-grid label, .settings-section > label { font-size: 0.8rem; font-weight: 500; display: block; margin-bottom: 0.2rem; }
.settings-form-grid input, .settings-form-grid select {
  width: 100%; padding: 0.45rem 0.5rem; border: 1px solid var(--border);
  border-radius: 6px; font-size: 0.85rem; background: var(--bg); color: var(--text);
}
.settings-toast { font-size: 0.82rem; padding: 0.4rem 0.6rem; border-radius: 5px; margin-bottom: 0.75rem; }
.settings-toast.success { background: rgba(39,174,96,0.1); color: #27ae60; }
.settings-toast.error { background: rgba(231,76,60,0.1); color: #e74c3c; }
.badge { font-size: 0.68rem; background: var(--bg-alt); padding: 0.1rem 0.35rem; border-radius: 4px; }
.badge.approved { background: rgba(39,174,96,0.1); color: #27ae60; }
.badge.pending { background: rgba(241,196,15,0.1); color: #f1c40f; }
.badge.rejected { background: rgba(231,76,60,0.1); color: #e74c3c; }

/* Theme picker */
.theme-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 0.6rem; }
.theme-card {
  border: 2px solid var(--border); border-radius: 8px; padding: 0.45rem;
  text-align: center; cursor: pointer; transition: border-color 0.15s;
}
.theme-card.active { border-color: var(--accent); }
.theme-card:hover { border-color: var(--accent); }
.theme-preview { height: 40px; border-radius: 4px; margin-bottom: 0.3rem; }
.theme-preview[data-theme-preview="light"] { background: #fff; border: 1px solid #ddd; }
.theme-preview[data-theme-preview="dark"] { background: #1a1a2e; border: 1px solid #333; }
.theme-preview[data-theme-preview="coffee"] { background: #2c1810; border: 1px solid #4a2c1a; }
.theme-preview[data-theme-preview="terminal"] { background: #0a0a0a; border: 1px solid #222; }
.theme-preview[data-theme-preview="nordic"] { background: #2e3440; border: 1px solid #3b4252; }
.theme-name { font-size: 0.72rem; font-weight: 600; }
.theme-check { font-size: 0.6rem; color: var(--accent); }

/* Connections */
.connection-card {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.75rem 0.85rem; border: 1px solid var(--border); border-radius: 8px; margin-bottom: 0.5rem;
}
.connection-info { display: flex; align-items: center; gap: 0.65rem; }

/* Activity */
.activity-tabs { display: flex; gap: 0.15rem; margin-bottom: 1rem; border-bottom: 1px solid var(--border); }
.activity-tab {
  padding: 0.35rem 0.65rem; font-size: 0.8rem; background: none; border: none;
  border-bottom: 2px solid transparent; color: var(--text-muted); cursor: pointer;
}
.activity-tab.active { border-bottom-color: var(--accent); color: var(--accent); font-weight: 600; }
.activity-count { font-size: 0.68rem; background: var(--bg-alt); padding: 0.05rem 0.35rem; border-radius: 10px; margin-left: 0.25rem; }
.activity-item {
  display: flex; justify-content: space-between; align-items: start;
  padding: 0.65rem 0.85rem; border: 1px solid var(--border); border-radius: 7px; margin-bottom: 0.4rem;
}
.activity-meta { font-size: 0.72rem; color: var(--text-muted); margin-bottom: 0.2rem; }

/* Danger zone */
.danger-zone {
  border: 1px solid rgba(231,76,60,0.25); border-radius: 8px; padding: 1rem;
  background: rgba(231,76,60,0.02);
}
.btn-danger { background: var(--danger, #e74c3c); color: #fff; border-color: var(--danger, #e74c3c); }
.btn-danger:hover { opacity: 0.9; }
.text-success { color: #27ae60; }

/* Nav identicon */
.nav-identicon { display: flex; align-items: center; }

/* Mobile settings */
@media (max-width: 768px) {
  .settings-layout { flex-direction: column; }
  .settings-sidebar {
    width: 100%; position: sticky; top: 64px; z-index: 10;
    display: flex; gap: 0.35rem; padding: 0.6rem 0.5rem;
    overflow-x: auto; background: var(--bg); border-bottom: 1px solid var(--border);
  }
  .settings-sidebar-title { display: none; }
  .settings-nav-link {
    padding: 0.3rem 0.65rem; border-radius: 20px; white-space: nowrap; flex-shrink: 0;
    font-size: 0.75rem; background: var(--bg-alt);
  }
  .settings-content { padding: 1rem 0; }
  .settings-form-grid { grid-template-columns: 1fr; }
  .theme-grid { grid-template-columns: repeat(3, 1fr); }
  .activity-tabs { overflow-x: auto; }
  .connection-card { flex-direction: column; align-items: stretch; gap: 0.5rem; }
  .connection-card button { width: 100%; }
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/index.html frontend/assets/js/app.js frontend/assets/js/identicon.js frontend/assets/js/pages/settings.js frontend/assets/css/main.css
git commit -m "feat: add settings page frontend — layout, nav identicon, all sections"
```

---

## Task 12: Run full linter and test suite

**Files:** None (verification only)

- [ ] **Step 1: Run backend linter**

```bash
cd backend && flake8 . --max-line-length=120 --exclude=tests/,package/
```

Expected: No errors (fix any that appear).

- [ ] **Step 2: Run full backend test suite**

```bash
cd backend && pytest tests/ -v
```

Expected: All pass.

- [ ] **Step 3: Fix any issues and commit**

If there are linter or test failures, fix them and commit:

```bash
git add -A && git commit -m "fix: address linter/test issues"
```

---

## Task 13: Bump version and final commit

**Files:**
- Modify: `version.txt`

- [ ] **Step 1: Update version**

Write `2.9` to `version.txt`.

- [ ] **Step 2: Commit version bump**

```bash
git add version.txt
git commit -m "chore: bump version to 2.9"
```

- [ ] **Step 3: Verify final state**

```bash
cd backend && pytest tests/ -v && flake8 . --max-line-length=120 --exclude=tests/,package/
```

Expected: All tests pass, no linter errors.

```bash
git log --oneline feature/settings-page --not dev | head -15
```

Expected: All commits from this feature branch listed.

---

## Task 14: Merge feature branch to dev

- [ ] **Step 1: Merge to dev**

```bash
git checkout dev
git merge feature/settings-page
```

- [ ] **Step 2: Verify merge**

```bash
git log --oneline -5
```

Expected: Feature commits visible on dev.
