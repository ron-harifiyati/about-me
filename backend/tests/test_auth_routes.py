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
    assert body["data"]["user_id"]


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
    from models.users import mark_email_verified, get_user_by_email
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
