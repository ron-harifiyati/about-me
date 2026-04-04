import os
import json
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
    ses = boto3.client("ses", region_name="us-east-1")
    sender = os.environ["SES_SENDER_EMAIL"]
    base_url = os.environ.get("FRONTEND_URL", "https://dkdwnfmhg75yf.cloudfront.net")
    verify_url = f"{base_url}/#/verify-email?token={token}"
    greeting = f"Hi {name}," if name else "Hi,"
    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:40px 20px;background:#f0f2f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <div style="max-width:560px;margin:0 auto;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
    <div style="background:#0f172a;padding:32px 40px;text-align:center;">
      <span style="font-size:22px;font-weight:700;color:#ffffff;letter-spacing:-0.5px;">Ron<span style="color:#6366f1;">.</span>dev</span>
    </div>
    <div style="padding:40px 40px 32px;">
      <h1 style="font-size:22px;font-weight:700;color:#0f172a;margin:0 0 12px;">Verify your email address</h1>
      <p style="font-size:15px;color:#475569;line-height:1.6;margin:0 0 16px;">{greeting}</p>
      <p style="font-size:15px;color:#475569;line-height:1.6;margin:0 0 16px;">Thanks for signing up! Click the button below to verify your email address and activate your account.</p>
      <div style="text-align:center;margin:32px 0;">
        <a href="{verify_url}" style="display:inline-block;background:#6366f1;color:#ffffff;text-decoration:none;font-size:15px;font-weight:600;padding:14px 36px;border-radius:8px;">Verify my email</a>
      </div>
      <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px 16px;font-size:13px;color:#64748b;">
        <strong style="color:#0f172a;">This link expires in 24 hours.</strong> If you didn't create an account, you can safely ignore this email.
      </div>
      <p style="margin-top:24px;font-size:13px;color:#94a3b8;">Button not working? Copy and paste this link into your browser:<br>
        <a href="{verify_url}" style="color:#6366f1;word-break:break-all;">{verify_url}</a>
      </p>
    </div>
    <div style="background:#f8fafc;border-top:1px solid #e2e8f0;padding:24px 40px;text-align:center;font-size:12px;color:#94a3b8;line-height:1.6;">
      You're receiving this because you signed up at <a href="{base_url}" style="color:#6366f1;text-decoration:none;">Ron's Portfolio</a>.<br>
      &copy; 2026 Ron Harifiyati
    </div>
  </div>
</body>
</html>"""
    text = f"{greeting}\n\nThanks for signing up! Verify your email address by visiting:\n{verify_url}\n\nThis link expires in 24 hours. If you didn't create an account, ignore this email.\n\n\u00a9 2026 Ron Harifiyati"  # noqa: E501
    ses.send_email(
        Source=sender,
        Destination={"ToAddresses": [email]},
        Message={
            "Subject": {"Data": "Verify your email \u2014 Ron's Portfolio"},
            "Body": {
                "Html": {"Data": html},
                "Text": {"Data": text},
            },
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
    # Always return 200 to avoid leaking whether an email is registered
    if not user or user.get("email_verified"):
        return ok({"message": "If that address is registered and unverified, a new email is on its way."})
    token = create_email_verify_token(user["user_id"])
    try:
        _send_verification_email(email, token)
    except Exception:
        return server_error("Could not send verification email. Please try again later.")
    return ok({"message": "If that address is registered and unverified, a new email is on its way."})


def _send_reset_email(email: str, token: str, name: str = ""):
    import boto3
    ses = boto3.client("ses", region_name="us-east-1")
    sender = os.environ["SES_SENDER_EMAIL"]
    base_url = os.environ.get("FRONTEND_URL", "https://dkdwnfmhg75yf.cloudfront.net")
    reset_url = f"{base_url}/#/reset-password?token={token}"
    greeting = f"Hi {name}," if name else "Hi,"
    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:40px 20px;background:#f0f2f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <div style="max-width:560px;margin:0 auto;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
    <div style="background:#0f172a;padding:32px 40px;text-align:center;">
      <span style="font-size:22px;font-weight:700;color:#ffffff;letter-spacing:-0.5px;">Ron<span style="color:#6366f1;">.</span>dev</span>
    </div>
    <div style="padding:40px 40px 32px;">
      <h1 style="font-size:22px;font-weight:700;color:#0f172a;margin:0 0 12px;">Reset your password</h1>
      <p style="font-size:15px;color:#475569;line-height:1.6;margin:0 0 16px;">{greeting}</p>
      <p style="font-size:15px;color:#475569;line-height:1.6;margin:0 0 16px;">We received a request to reset your password. Click the button below to choose a new one.</p>
      <div style="text-align:center;margin:32px 0;">
        <a href="{reset_url}" style="display:inline-block;background:#6366f1;color:#ffffff;text-decoration:none;font-size:15px;font-weight:600;padding:14px 36px;border-radius:8px;">Reset my password</a>
      </div>
      <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px 16px;font-size:13px;color:#64748b;">
        <strong style="color:#0f172a;">This link expires in 1 hour.</strong> If you didn't request a password reset, you can safely ignore this email &mdash; your password won't change.
      </div>
      <p style="margin-top:24px;font-size:13px;color:#94a3b8;">Button not working? Copy and paste this link into your browser:<br>
        <a href="{reset_url}" style="color:#6366f1;word-break:break-all;">{reset_url}</a>
      </p>
    </div>
    <div style="background:#f8fafc;border-top:1px solid #e2e8f0;padding:24px 40px;text-align:center;font-size:12px;color:#94a3b8;line-height:1.6;">
      You're receiving this because a password reset was requested for your account at <a href="{base_url}" style="color:#6366f1;text-decoration:none;">Ron's Portfolio</a>.<br>
      &copy; 2026 Ron Harifiyati
    </div>
  </div>
</body>
</html>"""
    text = f"{greeting}\n\nWe received a request to reset your password. Visit this link to choose a new one:\n{reset_url}\n\nThis link expires in 1 hour. If you didn't request this, ignore this email.\n\n\u00a9 2026 Ron Harifiyati"  # noqa: E501
    ses.send_email(
        Source=sender,
        Destination={"ToAddresses": [email]},
        Message={
            "Subject": {"Data": "Reset your password \u2014 Ron's Portfolio"},
            "Body": {
                "Html": {"Data": html},
                "Text": {"Data": text},
            },
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
        return bad_request("code is required")

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
