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
