import json
from tests.conftest import make_event


def _contact_payload():
    return {"name": "Alice", "email": "alice@example.com", "message": "Hello!"}


def test_submit_contact_returns_200(ddb_table, mocker):
    mocker.patch("routes.contact._send_contact_notification")
    from router import route
    resp = route(make_event("POST", "/contact", body=_contact_payload()))
    assert resp["statusCode"] == 200


def test_submit_contact_missing_fields_returns_400(ddb_table):
    from router import route
    resp = route(make_event("POST", "/contact", body={"name": "Alice"}))
    assert resp["statusCode"] == 400


def test_rate_limit_blocks_after_5_submissions(ddb_table, mocker):
    mocker.patch("routes.contact._send_contact_notification")
    from router import route
    for _ in range(5):
        route(make_event("POST", "/contact", body=_contact_payload(),
                         headers={"x-forwarded-for": "1.2.3.4"}))
    resp = route(make_event("POST", "/contact", body=_contact_payload(),
                            headers={"x-forwarded-for": "1.2.3.4"}))
    assert resp["statusCode"] == 429


def test_different_ips_not_rate_limited(ddb_table, mocker):
    mocker.patch("routes.contact._send_contact_notification")
    from router import route
    for _ in range(5):
        route(make_event("POST", "/contact", body=_contact_payload(),
                         headers={"x-forwarded-for": "1.2.3.4"}))
    resp = route(make_event("POST", "/contact", body=_contact_payload(),
                            headers={"x-forwarded-for": "5.6.7.8"}))
    assert resp["statusCode"] == 200
