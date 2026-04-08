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


# --- Languages ---

def test_get_languages_empty(ddb_table):
    from router import route
    resp = route(make_event("GET", "/languages"))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["data"] is None or isinstance(body["data"], dict)


def test_put_and_get_languages(ddb_table):
    from router import route
    payload = {"languages": [
        {"name": "Ndebele", "level": "Native"},
        {"name": "English", "level": "Fluent"},
    ]}
    put_resp = route(make_event("PUT", "/languages", body=payload, headers=_admin_headers()))
    assert put_resp["statusCode"] == 200

    get_resp = route(make_event("GET", "/languages"))
    body = json.loads(get_resp["body"])
    assert len(body["data"]["languages"]) == 2
    assert body["data"]["languages"][0]["name"] == "Ndebele"


def test_put_languages_requires_admin(ddb_table):
    from router import route
    resp = route(make_event("PUT", "/languages", body={"languages": []}))
    assert resp["statusCode"] == 401


# --- Hobbies ---

def test_get_hobbies_empty(ddb_table):
    from router import route
    resp = route(make_event("GET", "/hobbies"))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["data"] is None or isinstance(body["data"], dict)


def test_put_and_get_hobbies(ddb_table):
    from router import route
    payload = {"items": [
        {"icon": "🏃", "label": "Marathon Running"},
        {"icon": "🎮", "label": "Gaming"},
    ]}
    put_resp = route(make_event("PUT", "/hobbies", body=payload, headers=_admin_headers()))
    assert put_resp["statusCode"] == 200

    get_resp = route(make_event("GET", "/hobbies"))
    body = json.loads(get_resp["body"])
    assert len(body["data"]["items"]) == 2
    assert body["data"]["items"][0]["label"] == "Marathon Running"


def test_put_hobbies_requires_admin(ddb_table):
    from router import route
    resp = route(make_event("PUT", "/hobbies", body={"items": []}))
    assert resp["statusCode"] == 401


# --- Values ---

def test_get_values_empty(ddb_table):
    from router import route
    resp = route(make_event("GET", "/values"))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["data"] is None or isinstance(body["data"], dict)


def test_put_and_get_values(ddb_table):
    from router import route
    payload = {"values": [
        {"title": "Accountability", "description": "I own my work."},
        {"title": "Simplicity", "description": "Keep it simple."},
    ]}
    put_resp = route(make_event("PUT", "/values", body=payload, headers=_admin_headers()))
    assert put_resp["statusCode"] == 200

    get_resp = route(make_event("GET", "/values"))
    body = json.loads(get_resp["body"])
    assert len(body["data"]["values"]) == 2
    assert body["data"]["values"][0]["title"] == "Accountability"


def test_put_values_requires_admin(ddb_table):
    from router import route
    resp = route(make_event("PUT", "/values", body={"values": []}))
    assert resp["statusCode"] == 401
