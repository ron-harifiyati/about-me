import json
from tests.conftest import make_event
from auth import make_jwt


def test_list_guestbook_empty(ddb_table):
    from router import route
    resp = route(make_event("GET", "/guestbook"))
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"])["data"] == []


def test_guest_can_submit_entry(ddb_table):
    from router import route
    resp = route(make_event("POST", "/guestbook", body={"name": "Alice", "message": "Cool site!"}))
    assert resp["statusCode"] == 201
    entry = json.loads(resp["body"])["data"]
    assert entry["name"] == "Alice (guest)"
    assert entry["message"] == "Cool site!"


def test_authenticated_entry_shows_identity(ddb_table):
    from router import route
    from models.users import create_user, mark_email_verified
    user = create_user("u@example.com", "Bob", "MCRI")
    mark_email_verified(user["user_id"])
    token = make_jwt(user["user_id"], "user")

    resp = route(make_event("POST", "/guestbook",
        body={"name": "Bob", "message": "Hi!"},
        headers={"authorization": f"Bearer {token}"},
    ))
    assert resp["statusCode"] == 201
    entry = json.loads(resp["body"])["data"]
    assert entry["name"] == "Bob"
    assert entry["identity"] == "MCRI"


def test_entry_requires_name_and_message(ddb_table):
    from router import route
    resp = route(make_event("POST", "/guestbook", body={"name": "Alice"}))
    assert resp["statusCode"] == 400
