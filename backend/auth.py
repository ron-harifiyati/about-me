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
