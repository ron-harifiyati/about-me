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
