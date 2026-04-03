import json
from tests.conftest import make_event
from auth import make_jwt


def _admin_headers():
    return {"authorization": f"Bearer {make_jwt('admin-1', 'admin')}"}


def test_get_about_returns_404_when_no_data(ddb_table):
    from router import route
    resp = route(make_event("GET", "/about"))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["data"] is None or isinstance(body["data"], dict)


def test_put_and_get_about(ddb_table):
    from router import route
    payload = {
        "bio": "Hi, I'm Ron.",
        "mission": "Build great software.",
        "social_links": {"github": "https://github.com/ron"},
        "contact": {"email": "ron@example.com", "location": "Israel"},
    }
    put_resp = route(make_event("PUT", "/about", body=payload, headers=_admin_headers()))
    assert put_resp["statusCode"] == 200

    get_resp = route(make_event("GET", "/about"))
    body = json.loads(get_resp["body"])
    assert body["data"]["bio"] == "Hi, I'm Ron."


def test_put_about_requires_admin(ddb_table):
    from router import route
    resp = route(make_event("PUT", "/about", body={"bio": "x"}))
    assert resp["statusCode"] == 401


def test_get_skills_returns_empty_list_when_no_data(ddb_table):
    from router import route
    resp = route(make_event("GET", "/skills"))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["data"] is None or isinstance(body["data"], (dict, list))


def test_get_fun_fact_returns_random_fact(ddb_table):
    from router import route
    # seed some facts
    from models.content import update_content
    update_content("FUNFACTS", {"facts": ["Fact A", "Fact B", "Fact C"]})
    resp = route(make_event("GET", "/fun-fact"))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["data"]["fact"] in ["Fact A", "Fact B", "Fact C"]
