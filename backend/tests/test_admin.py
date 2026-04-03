import json
from tests.conftest import make_event
from auth import make_jwt


def _admin_headers():
    return {"authorization": f"Bearer {make_jwt('admin-1', 'admin')}"}


def _user_headers():
    return {"authorization": f"Bearer {make_jwt('user-1', 'user')}"}


# --- Users ---

def test_list_users_requires_admin(ddb_table):
    from router import route
    assert route(make_event("GET", "/admin/users"))["statusCode"] == 401
    assert route(make_event("GET", "/admin/users", headers=_user_headers()))["statusCode"] == 403


def test_list_users_returns_list(ddb_table):
    from router import route
    from models.users import create_user
    create_user("a@example.com", "Alice", "Jamf")
    create_user("b@example.com", "Bob", "MCRI")

    resp = route(make_event("GET", "/admin/users", headers=_admin_headers()))
    assert resp["statusCode"] == 200
    users = json.loads(resp["body"])["data"]
    assert len(users) == 2
    assert all("password_hash" not in u for u in users)


def test_suspend_user(ddb_table):
    from router import route
    from models.users import create_user
    user = create_user("a@example.com", "Alice", "Jamf")
    uid = user["user_id"]

    resp = route(make_event("PUT", f"/admin/users/{uid}",
        body={"status": "suspended"},
        headers=_admin_headers(),
    ))
    assert resp["statusCode"] == 200

    from models.users import get_user_by_id
    updated = get_user_by_id(uid)
    assert updated["status"] == "suspended"


def test_delete_user(ddb_table):
    from router import route
    from models.users import create_user, get_user_by_id
    user = create_user("a@example.com", "Alice", "Jamf")
    uid = user["user_id"]

    resp = route(make_event("DELETE", f"/admin/users/{uid}", headers=_admin_headers()))
    assert resp["statusCode"] == 200
    assert get_user_by_id(uid) is None


# --- Contacts ---

def test_list_contacts(ddb_table):
    from router import route
    from models.contacts import save_contact
    save_contact("Alice", "alice@example.com", "Hello!")

    resp = route(make_event("GET", "/admin/contacts", headers=_admin_headers()))
    assert resp["statusCode"] == 200
    items = json.loads(resp["body"])["data"]
    assert len(items) == 1


# --- Testimonials ---

def test_list_pending_testimonials(ddb_table):
    from router import route
    from models.testimonials import create_testimonial
    create_testimonial("Great!", "Alice", "Jamf", False)

    resp = route(make_event("GET", "/admin/testimonials/pending", headers=_admin_headers()))
    assert resp["statusCode"] == 200
    items = json.loads(resp["body"])["data"]
    assert len(items) == 1


def test_approve_testimonial(ddb_table):
    from router import route
    from models.testimonials import create_testimonial, list_approved
    t = create_testimonial("Awesome!", "Bob", "MCRI", False)
    tid = t["testimonial_id"]

    resp = route(make_event("PUT", f"/admin/testimonials/{tid}",
        body={"action": "approve"},
        headers=_admin_headers(),
    ))
    assert resp["statusCode"] == 200
    assert len(list_approved()) == 1


def test_reject_testimonial(ddb_table):
    from router import route
    from models.testimonials import create_testimonial, list_pending
    t = create_testimonial("Bad!", "Eve", "Other", False)
    tid = t["testimonial_id"]

    route(make_event("PUT", f"/admin/testimonials/{tid}",
        body={"action": "reject"},
        headers=_admin_headers(),
    ))
    assert len(list_pending()) == 0


# --- Quiz management ---

def test_admin_can_add_quiz_question(ddb_table):
    from router import route
    resp = route(make_event("POST", "/admin/quiz/questions",
        body={"question": "What is 2+2?", "options": ["1", "2", "3", "4"], "answer": "4", "topic": "math"},
        headers=_admin_headers(),
    ))
    assert resp["statusCode"] == 201


def test_admin_can_delete_quiz_question(ddb_table):
    from router import route
    from models.quiz import create_question, list_questions
    q = create_question({"question": "Q?", "options": ["A"], "answer": "A", "topic": "t"})
    qid = q["question_id"]

    resp = route(make_event("DELETE", f"/admin/quiz/questions/{qid}", headers=_admin_headers()))
    assert resp["statusCode"] == 200
    assert list_questions() == []
