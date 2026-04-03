import json
from tests.conftest import make_event
from auth import make_jwt
from models.projects import create_project


def _auth_headers(user_id="user-1"):
    return {"authorization": f"Bearer {make_jwt(user_id, 'user')}"}


def test_get_ratings_empty(ddb_table):
    from router import route
    p = create_project({"title": "P1"})
    resp = route(make_event("GET", f"/projects/{p['id']}/ratings"))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])["data"]
    assert body["count"] == 0
    assert body["average"] is None


def test_submit_rating(ddb_table):
    from router import route
    p = create_project({"title": "P1"})
    resp = route(make_event("POST", f"/projects/{p['id']}/ratings",
        body={"stars": 5},
        headers=_auth_headers(),
    ))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])["data"]
    assert body["average"] == 5.0
    assert body["count"] == 1


def test_rating_requires_auth(ddb_table):
    from router import route
    p = create_project({"title": "P1"})
    resp = route(make_event("POST", f"/projects/{p['id']}/ratings", body={"stars": 3}))
    assert resp["statusCode"] == 401


def test_resubmit_rating_updates(ddb_table):
    from router import route
    p = create_project({"title": "P1"})
    route(make_event("POST", f"/projects/{p['id']}/ratings", body={"stars": 2}, headers=_auth_headers()))
    route(make_event("POST", f"/projects/{p['id']}/ratings", body={"stars": 4}, headers=_auth_headers()))
    resp = route(make_event("GET", f"/projects/{p['id']}/ratings"))
    body = json.loads(resp["body"])["data"]
    assert body["count"] == 1  # same user, only one rating
    assert body["average"] == 4.0
