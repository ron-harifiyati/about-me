import json
from tests.conftest import make_event


def test_swagger_ui_returns_html(ddb_table):
    from router import route
    resp = route(make_event("GET", "/api"))
    assert resp["statusCode"] == 200
    assert "text/html" in resp["headers"]["Content-Type"]
    assert "swagger-ui" in resp["body"]


def test_openapi_spec_returns_json(ddb_table):
    from router import route
    resp = route(make_event("GET", "/api/spec"))
    assert resp["statusCode"] == 200
    assert resp["headers"]["Content-Type"] == "application/json"
    spec = json.loads(resp["body"])
    assert spec["openapi"] == "3.0.3"
    assert "/projects" in spec["paths"]
    assert "/auth/login" in spec["paths"]
    assert "/admin/users" in spec["paths"]
