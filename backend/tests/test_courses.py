import json
from tests.conftest import make_event
from auth import make_jwt


def _admin_headers():
    return {"authorization": f"Bearer {make_jwt('admin-1', 'admin')}"}


def test_list_courses_returns_empty_list(ddb_table):
    from router import route
    resp = route(make_event("GET", "/courses"))
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"])["data"] == []


def test_create_and_get_course(ddb_table):
    from router import route
    payload = {"title": "AWS Cloud Practitioner", "platform": "AWS", "link": "https://aws.amazon.com"}
    create_resp = route(make_event("POST", "/courses", body=payload, headers=_admin_headers()))
    assert create_resp["statusCode"] == 201
    cid = json.loads(create_resp["body"])["data"]["id"]

    get_resp = route(make_event("GET", f"/courses/{cid}"))
    assert json.loads(get_resp["body"])["data"]["title"] == "AWS Cloud Practitioner"


def test_delete_course(ddb_table):
    from router import route
    cid = json.loads(
        route(make_event("POST", "/courses", body={"title": "x"}, headers=_admin_headers()))["body"]
    )["data"]["id"]
    assert route(make_event("DELETE", f"/courses/{cid}", headers=_admin_headers()))["statusCode"] == 200
    assert route(make_event("GET", f"/courses/{cid}"))["statusCode"] == 404
