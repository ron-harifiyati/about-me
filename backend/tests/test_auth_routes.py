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


def test_register_ses_failure_returns_500(ddb_table, mocker):
    mocker.patch("routes.auth_routes._send_verification_email", side_effect=Exception("SES sandbox"))
    from router import route
    resp = route(make_event("POST", "/auth/register", body={
        "email": "ron@example.com",
        "password": "Secure123!",
        "name": "Ron",
        "identity": "Jamf",
    }))
    assert resp["statusCode"] == 500
    body = json.loads(resp["body"])
    assert "Resend" in body["error"] or "resend" in body["error"]


def test_resend_verification_sends_email(ddb_table, mocker):
    mock_send = mocker.patch("routes.auth_routes._send_verification_email")
    from router import route
    route(make_event("POST", "/auth/register", body={
        "email": "ron@example.com", "password": "Secure123!", "name": "Ron", "identity": "Jamf",
    }))
    mock_send.reset_mock()

    resp = route(make_event("POST", "/auth/resend-verification", body={"email": "ron@example.com"}))
    assert resp["statusCode"] == 200
    mock_send.assert_called_once()


def test_resend_verification_unknown_email_returns_200(ddb_table, mocker):
    mocker.patch("routes.auth_routes._send_verification_email")
    from router import route
    resp = route(make_event("POST", "/auth/resend-verification", body={"email": "ghost@example.com"}))
    assert resp["statusCode"] == 200


def test_resend_verification_already_verified_returns_200(ddb_table, mocker):
    mock_send = mocker.patch("routes.auth_routes._send_verification_email")
    from router import route
    from models.users import mark_email_verified, get_user_by_email
    route(make_event("POST", "/auth/register", body={
        "email": "ron@example.com", "password": "Secure123!", "name": "Ron", "identity": "Jamf",
    }))
    user = get_user_by_email("ron@example.com")
    mark_email_verified(user["user_id"])
    mock_send.reset_mock()

    resp = route(make_event("POST", "/auth/resend-verification", body={"email": "ron@example.com"}))
    assert resp["statusCode"] == 200
    mock_send.assert_not_called()


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
    # Critical: assert email_verified flag is actually set
    assert fresh["email_verified"] is True, "email_verified should be True after successful verification"


def test_verify_email_second_call_returns_400(ddb_table, mocker):
    """Simulate the double-call race condition: clicking the email link twice."""
    mocker.patch("routes.auth_routes._send_verification_email")
    from router import route
    from models.users import get_user_by_email, create_email_verify_token
    route(make_event("POST", "/auth/register", body={
        "email": "ron@example.com", "password": "Secure123!", "name": "Ron", "identity": "Jamf",
    }))
    user = get_user_by_email("ron@example.com")
    token = create_email_verify_token(user["user_id"])

    # First call — must succeed
    resp1 = route(make_event("POST", "/auth/verify-email", body={"token": token}))
    assert resp1["statusCode"] == 200, f"First verify call should return 200, got {resp1['statusCode']}"
    body1 = json.loads(resp1["body"])
    assert body1["data"] is not None, "First verify call should return success data"
    assert body1["error"] is None, "First verify call should have no error"

    # Second call with same token — must fail (token consumed)
    resp2 = route(make_event("POST", "/auth/verify-email", body={"token": token}))
    assert resp2["statusCode"] == 400, f"Second verify call should return 400, got {resp2['statusCode']}"
    body2 = json.loads(resp2["body"])
    assert body2["error"] == "Invalid or expired token", \
        f"Expected 'Invalid or expired token', got '{body2['error']}'"

    # Account should still be verified after the second call
    fresh = get_user_by_email("ron@example.com")
    assert fresh["email_verified"] is True, "email_verified should remain True after second (failed) call"


def test_verify_email_full_happy_path(ddb_table, mocker):
    """End-to-end: register → capture token from register call → verify → login."""
    captured = {}

    def capture_send(email, token, name=""):
        captured["token"] = token

    mocker.patch("routes.auth_routes._send_verification_email", side_effect=capture_send)
    from router import route
    from models.users import get_user_by_email

    # Register — captures the verification token sent via email
    reg_resp = route(make_event("POST", "/auth/register", body={
        "email": "ron@example.com", "password": "Secure123!", "name": "Ron", "identity": "Jamf",
    }))
    assert reg_resp["statusCode"] == 201
    assert "token" in captured, "Verification email should have been sent with a token"

    token = captured["token"]

    # User should NOT be verified yet
    user = get_user_by_email("ron@example.com")
    assert not user.get("email_verified"), "User should not be verified before clicking the link"

    # Click the verification link (frontend posts the token)
    verify_resp = route(make_event("POST", "/auth/verify-email", body={"token": token}))
    assert verify_resp["statusCode"] == 200, \
        f"Verify should return 200. Got {verify_resp['statusCode']}: {json.loads(verify_resp['body'])}"

    # User should now be verified
    user = get_user_by_email("ron@example.com")
    assert user["email_verified"] is True

    # Login should succeed
    login_resp = route(make_event("POST", "/auth/login", body={
        "email": "ron@example.com", "password": "Secure123!",
    }))
    assert login_resp["statusCode"] == 200, \
        f"Login should succeed after verification. Got {login_resp['statusCode']}: {json.loads(login_resp['body'])}"
    login_body = json.loads(login_resp["body"])
    assert "access_token" in login_body["data"]


def test_resend_verification_already_verified_message(ddb_table, mocker):
    """Resend for already-verified account must return the actionable message, not the vague one."""
    mock_send = mocker.patch("routes.auth_routes._send_verification_email")
    from router import route
    from models.users import mark_email_verified, get_user_by_email
    route(make_event("POST", "/auth/register", body={
        "email": "ron@example.com", "password": "Secure123!", "name": "Ron", "identity": "Jamf",
    }))
    user = get_user_by_email("ron@example.com")
    mark_email_verified(user["user_id"])
    mock_send.reset_mock()

    resp = route(make_event("POST", "/auth/resend-verification", body={"email": "ron@example.com"}))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert "already verified" in body["data"]["message"].lower(), \
        f"Expected 'already verified' in message, got: '{body['data']['message']}'"
    mock_send.assert_not_called()


def test_reset_password_happy_path(ddb_table, mocker):
    mocker.patch("routes.auth_routes._send_verification_email")
    mocker.patch("routes.auth_routes._send_reset_email")
    from router import route
    from models.users import mark_email_verified, get_user_by_email, create_password_reset_token
    route(make_event("POST", "/auth/register", body={
        "email": "ron@example.com", "password": "Secure123!", "name": "Ron", "identity": "Jamf",
    }))
    user = get_user_by_email("ron@example.com")
    mark_email_verified(user["user_id"])
    token = create_password_reset_token(user["user_id"])

    resp = route(make_event("POST", "/auth/reset-password", body={
        "token": token, "new_password": "NewPass123!",
    }))
    assert resp["statusCode"] == 200

    login = route(make_event("POST", "/auth/login", body={
        "email": "ron@example.com", "password": "NewPass123!",
    }))
    assert login["statusCode"] == 200


def test_reset_password_invalid_token_returns_400(ddb_table, mocker):
    mocker.patch("routes.auth_routes._send_verification_email")
    from router import route
    resp = route(make_event("POST", "/auth/reset-password", body={
        "token": "badtoken", "new_password": "NewPass123!",
    }))
    assert resp["statusCode"] == 400


def test_reset_password_short_password_returns_400(ddb_table, mocker):
    mocker.patch("routes.auth_routes._send_verification_email")
    from router import route
    resp = route(make_event("POST", "/auth/reset-password", body={
        "token": "anytoken", "new_password": "short",
    }))
    assert resp["statusCode"] == 400


def test_forgot_password_unknown_email_returns_200(ddb_table, mocker):
    mock_send = mocker.patch("routes.auth_routes._send_reset_email")
    from router import route
    resp = route(make_event("POST", "/auth/forgot-password", body={"email": "ghost@example.com"}))
    assert resp["statusCode"] == 200
    mock_send.assert_not_called()


def test_forgot_password_sends_email(ddb_table, mocker):
    mocker.patch("routes.auth_routes._send_verification_email")
    mock_send = mocker.patch("routes.auth_routes._send_reset_email")
    from router import route
    route(make_event("POST", "/auth/register", body={
        "email": "ron@example.com", "password": "Secure123!", "name": "Ron", "identity": "Jamf",
    }))
    resp = route(make_event("POST", "/auth/forgot-password", body={"email": "ron@example.com"}))
    assert resp["statusCode"] == 200
    mock_send.assert_called_once()


def test_forgot_password_oauth_only_user_returns_200(ddb_table, mocker):
    mock_send = mocker.patch("routes.auth_routes._send_reset_email")
    from router import route
    from models.users import create_user
    create_user("oauth@example.com", "OAuth User", "Other")  # no password
    resp = route(make_event("POST", "/auth/forgot-password", body={"email": "oauth@example.com"}))
    assert resp["statusCode"] == 200
    mock_send.assert_not_called()
