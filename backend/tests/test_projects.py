import json
from tests.conftest import make_event
from auth import make_jwt


def _admin_headers():
    return {"authorization": f"Bearer {make_jwt('admin-1', 'admin')}"}


def test_list_projects_returns_empty_list(ddb_table):
    from router import route
    resp = route(make_event("GET", "/projects"))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["data"] == []


def test_create_and_get_project(ddb_table):
    from router import route
    payload = {
        "title": "Portfolio Site",
        "description": "My personal portfolio.",
        "tech_stack": ["Python", "AWS"],
        "links": {"github": "https://github.com/ron/portfolio"},
    }
    create_resp = route(make_event("POST", "/projects", body=payload, headers=_admin_headers()))
    assert create_resp["statusCode"] == 201
    project = json.loads(create_resp["body"])["data"]
    project_id = project["id"]

    get_resp = route(make_event("GET", f"/projects/{project_id}"))
    assert get_resp["statusCode"] == 200
    assert json.loads(get_resp["body"])["data"]["title"] == "Portfolio Site"


def test_create_project_requires_admin(ddb_table):
    from router import route
    resp = route(make_event("POST", "/projects", body={"title": "x"}))
    assert resp["statusCode"] == 401


def test_update_project(ddb_table):
    from router import route
    create_resp = route(make_event("POST", "/projects", body={"title": "Old"}, headers=_admin_headers()))
    pid = json.loads(create_resp["body"])["data"]["id"]

    update_resp = route(make_event("PUT", f"/projects/{pid}", body={"title": "New"}, headers=_admin_headers()))
    assert update_resp["statusCode"] == 200
    assert json.loads(update_resp["body"])["data"]["title"] == "New"


def test_delete_project(ddb_table):
    from router import route
    create_resp = route(make_event("POST", "/projects", body={"title": "To Delete"}, headers=_admin_headers()))
    pid = json.loads(create_resp["body"])["data"]["id"]

    del_resp = route(make_event("DELETE", f"/projects/{pid}", headers=_admin_headers()))
    assert del_resp["statusCode"] == 200

    get_resp = route(make_event("GET", f"/projects/{pid}"))
    assert get_resp["statusCode"] == 404


def test_get_nonexistent_project_returns_404(ddb_table):
    from router import route
    resp = route(make_event("GET", "/projects/does-not-exist"))
    assert resp["statusCode"] == 404
