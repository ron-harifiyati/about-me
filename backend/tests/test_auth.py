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
