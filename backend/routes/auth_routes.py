import os
import json
from urllib.parse import urlencode
import requests as http
from auth import make_jwt, require_auth
from models.users import (
    get_user_by_id, get_user_by_email, create_user, verify_user_password,
    mark_email_verified, update_user_profile, create_email_verify_token,
    consume_email_verify_token, create_refresh_token, consume_refresh_token,
    delete_refresh_token, get_or_create_oauth_user,
    create_password_reset_token, consume_password_reset_token, update_user_password,
)
from utils import ok, created, bad_request, unauthorized, conflict, server_error


def _send_verification_email(email: str, token: str, name: str = ""):
    import boto3
    from routes.email_templates import verification_email
    ses = boto3.client("ses", region_name="us-east-1")
    sender = os.environ["SES_SENDER_EMAIL"]
    base_url = os.environ.get("FRONTEND_URL", "https://dkdwnfmhg75yf.cloudfront.net")
    verify_url = f"{base_url}/#/verify-email?token={token}"
    greeting = f"Hi {name}," if name else "Hi,"
    html, text = verification_email(greeting, verify_url, base_url)
    ses.send_email(
        Source=sender,
        Destination={"ToAddresses": [email]},
        Message={
            "Subject": {"Data": "Verify your email \u2014 Ron's Portfolio"},
            "Body": {"Html": {"Data": html}, "Text": {"Data": text}},
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
    try:
        _send_verification_email(email, token, name)
    except Exception:
        return server_error(
            "Account created but we couldn't send the verification email. "
            "Please use 'Resend verification email' to try again."
        )
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


def resend_verification(event, path_params, body, query, headers):
    email = (body.get("email") or "").strip().lower()
    if not email:
        return bad_request("email is required")
    user = get_user_by_email(email)
    if user and user.get("email_verified"):
        return ok({"message": "This email is already verified. You can log in now."})
    # Return the same vague message whether not found or unverified to avoid leaking registration status
    if not user:
        return ok({"message": "If that address is registered and unverified, a new email is on its way."})
    token = create_email_verify_token(user["user_id"])
    try:
        _send_verification_email(email, token)
    except Exception:
        return server_error("Could not send verification email. Please try again later.")
    return ok({"message": "If that address is registered and unverified, a new email is on its way."})


def _send_reset_email(email: str, token: str, name: str = ""):
    import boto3
    from routes.email_templates import reset_email
    ses = boto3.client("ses", region_name="us-east-1")
    sender = os.environ["SES_SENDER_EMAIL"]
    base_url = os.environ.get("FRONTEND_URL", "https://dkdwnfmhg75yf.cloudfront.net")
    reset_url = f"{base_url}/#/reset-password?token={token}"
    greeting = f"Hi {name}," if name else "Hi,"
    html, text = reset_email(greeting, reset_url, base_url)
    ses.send_email(
        Source=sender,
        Destination={"ToAddresses": [email]},
        Message={
            "Subject": {"Data": "Reset your password \u2014 Ron's Portfolio"},
            "Body": {"Html": {"Data": html}, "Text": {"Data": text}},
        },
    )


def forgot_password(event, path_params, body, query, headers):
    email = (body.get("email") or "").strip().lower()
    if not email:
        return bad_request("email is required")
    safe_msg = "If that address is registered, a reset link is on its way."
    user = get_user_by_email(email)
    if not user or not user.get("password_hash"):
        return ok({"message": safe_msg})
    token = create_password_reset_token(user["user_id"])
    try:
        _send_reset_email(email, token, user.get("name", ""))
    except Exception:
        return server_error("Could not send reset email. Please try again later.")
    return ok({"message": safe_msg})


def reset_password(event, path_params, body, query, headers):
    token = (body.get("token") or "").strip()
    new_password = body.get("new_password", "")
    if not token or not new_password:
        return bad_request("token and new_password are required")
    if len(new_password) < 8:
        return bad_request("password must be at least 8 characters")
    user_id = consume_password_reset_token(token)
    if not user_id:
        return bad_request("Invalid or expired reset link")
    update_user_password(user_id, new_password)
    return ok({"message": "Password updated. You can now log in."})


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

def _oauth_redirect(access_token, refresh_token):
    frontend_url = os.environ.get("FRONTEND_URL", "https://dkdwnfmhg75yf.cloudfront.net")
    params = urlencode({"access_token": access_token, "refresh_token": refresh_token})
    return {
        "statusCode": 302,
        "headers": {"Location": f"{frontend_url}/#/oauth-callback?{params}"},
        "body": "",
    }


def _oauth_error_redirect(message):
    frontend_url = os.environ.get("FRONTEND_URL", "https://dkdwnfmhg75yf.cloudfront.net")
    params = urlencode({"error": message})
    return {
        "statusCode": 302,
        "headers": {"Location": f"{frontend_url}/#/login?{params}"},
        "body": "",
    }


def oauth_github_init(event, path_params, body, query, headers):
    client_id = os.environ["GITHUB_OAUTH_CLIENT_ID"]
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
        return _oauth_error_redirect("GitHub login failed")

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

    user = get_or_create_oauth_user("github", str(gh_user["id"]), email, gh_user.get("name") or gh_user["login"])
    access_token = make_jwt(user["user_id"], user["role"])
    refresh_token = create_refresh_token(user["user_id"], user["role"])
    return _oauth_redirect(access_token, refresh_token)


def _google_redirect_uri(event):
    uri = os.environ.get("GOOGLE_REDIRECT_URI", "")
    if not uri:
        domain = event.get("requestContext", {}).get("domainName", "")
        if domain:
            uri = f"https://{domain}/auth/oauth/google/callback"
    return uri


def oauth_google_init(event, path_params, body, query, headers):
    client_id = os.environ["GOOGLE_OAUTH_CLIENT_ID"]
    redirect_uri = _google_redirect_uri(event)
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
        return _oauth_error_redirect("Google login failed")

    redirect_uri = _google_redirect_uri(event)
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
        return _oauth_error_redirect("Google login failed")

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
    return _oauth_redirect(access_token, refresh_token)
