import json
from tests.conftest import make_event
from auth import make_jwt
from models.projects import create_project


def _auth_headers(user_id="user-1", role="user"):
    return {"authorization": f"Bearer {make_jwt(user_id, role)}"}


def test_list_comments_empty(ddb_table):
    from router import route
    p = create_project({"title": "P1"})
    resp = route(make_event("GET", f"/projects/{p['id']}/comments"))
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"])["data"] == []


def test_create_and_list_comment(ddb_table):
    from router import route
    from models.users import create_user, mark_email_verified
    user = create_user("u@example.com", "User One", "Jamf")
    mark_email_verified(user["user_id"])
    p = create_project({"title": "P1"})

    resp = route(make_event("POST", f"/projects/{p['id']}/comments",
        body={"body": "Great project!"},
        headers=_auth_headers(user["user_id"]),
    ))
    assert resp["statusCode"] == 201

    list_resp = route(make_event("GET", f"/projects/{p['id']}/comments"))
    comments = json.loads(list_resp["body"])["data"]
    assert len(comments) == 1
    assert comments[0]["body"] == "Great project!"


def test_create_comment_requires_auth(ddb_table):
    from router import route
    p = create_project({"title": "P1"})
    resp = route(make_event("POST", f"/projects/{p['id']}/comments", body={"body": "x"}))
    assert resp["statusCode"] == 401


def test_admin_can_delete_comment(ddb_table):
    from router import route
    from models.users import create_user, mark_email_verified
    user = create_user("u@example.com", "User One", "Jamf")
    mark_email_verified(user["user_id"])
    p = create_project({"title": "P1"})

    create_resp = route(make_event("POST", f"/projects/{p['id']}/comments",
        body={"body": "Bad comment"},
        headers=_auth_headers(user["user_id"]),
    ))
    comment_id = json.loads(create_resp["body"])["data"]["comment_id"]

    del_resp = route(make_event("DELETE", f"/comments/{comment_id}",
        headers=_auth_headers("admin-1", "admin"),
        query={"entity_pk": f"PROJECT#{p['id']}"},
    ))
    assert del_resp["statusCode"] == 200
