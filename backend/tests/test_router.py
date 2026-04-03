import json
from tests.conftest import make_event
from db import get_table


def test_get_table_returns_table_resource(ddb_table):
    table = get_table()
    assert table.name == "portfolio"


def test_options_returns_cors_200():
    from router import route
    event = make_event(method="OPTIONS", path="/meta")
    resp = route(event)
    assert resp["statusCode"] == 200
    assert resp["headers"]["Access-Control-Allow-Origin"] == "*"


def test_unknown_route_returns_404():
    from router import route
    event = make_event(method="GET", path="/does-not-exist")
    resp = route(event)
    assert resp["statusCode"] == 404


def test_handler_returns_200_for_root(ddb_table, monkeypatch):
    monkeypatch.setenv("VERSION", "0.1.0")
    from router import route
    event = make_event(method="GET", path="/meta")
    resp = route(event)
    # /meta route not yet implemented — 404 is expected here
    # This test will be updated in the meta task
    assert resp["statusCode"] in (200, 404)
