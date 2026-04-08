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


def test_testimonial_stores_user_id(ddb_table, mocker):
    user_id, token = _register_and_verify(ddb_table, mocker)
    from router import route
    resp = route(make_event("POST", "/testimonials",
        body={"body": "Great portfolio!", "author": "Test", "identity": "Other", "anonymous": False},
        headers={"authorization": f"Bearer {token}"}))
    assert resp["statusCode"] == 201
    body = json.loads(resp["body"])
    assert body["data"].get("user_id") == user_id


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


def test_get_my_comments(ddb_table, mocker):
    user_id, token = _register_and_verify(ddb_table, mocker)
    from router import route
    admin_token = make_jwt(user_id, "admin")
    route(make_event("POST", "/projects",
        body={"title": "Test Project", "description": "desc", "tech_stack": ["Python"]},
        headers={"authorization": f"Bearer {admin_token}"}))
    projects = json.loads(route(make_event("GET", "/projects"))["body"])["data"]
    pid = projects[0]["id"]
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
    pid = projects[0]["id"]
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


def test_delete_own_comment(ddb_table, mocker):
    user_id, token = _register_and_verify(ddb_table, mocker)
    from router import route
    admin_token = make_jwt(user_id, "admin")
    route(make_event("POST", "/projects",
        body={"title": "Test", "description": "desc", "tech_stack": ["Python"]},
        headers={"authorization": f"Bearer {admin_token}"}))
    projects = json.loads(route(make_event("GET", "/projects"))["body"])["data"]
    pid = projects[0]["id"]
    route(make_event("POST", f"/projects/{pid}/comments",
        body={"body": "My comment"},
        headers={"authorization": f"Bearer {token}"}))

    comments = json.loads(route(make_event("GET", "/auth/me/comments",
        headers={"authorization": f"Bearer {token}"}))["body"])["data"]
    comment_id = comments[0]["comment_id"]

    resp = route(make_event("DELETE", f"/auth/me/comments/{comment_id}",
        headers={"authorization": f"Bearer {token}"}))
    assert resp["statusCode"] == 200

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
    mocker.patch("routes.auth_routes._send_verification_email")
    from router import route
    from models.users import mark_email_verified, create_user
    user2 = create_user("other@example.com", "Other User", "Other", "Secure123!")
    mark_email_verified(user2["user_id"])
    token2 = make_jwt(user2["user_id"], "user")

    admin_token = make_jwt(user_id, "admin")
    route(make_event("POST", "/projects",
        body={"title": "Test", "description": "desc", "tech_stack": ["Python"]},
        headers={"authorization": f"Bearer {admin_token}"}))
    projects = json.loads(route(make_event("GET", "/projects"))["body"])["data"]
    pid = projects[0]["id"]
    route(make_event("POST", f"/projects/{pid}/comments",
        body={"body": "User1 comment"},
        headers={"authorization": f"Bearer {token}"}))

    comments = json.loads(route(make_event("GET", "/auth/me/comments",
        headers={"authorization": f"Bearer {token}"}))["body"])["data"]
    comment_id = comments[0]["comment_id"]

    resp = route(make_event("DELETE", f"/auth/me/comments/{comment_id}",
        headers={"authorization": f"Bearer {token2}"}))
    assert resp["statusCode"] == 404
