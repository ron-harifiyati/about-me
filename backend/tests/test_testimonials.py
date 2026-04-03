import json
from tests.conftest import make_event
from auth import make_jwt


def test_submit_testimonial_as_guest(ddb_table):
    from router import route
    resp = route(make_event("POST", "/testimonials", body={
        "body": "Ron is great!",
        "anonymous": True,
    }))
    assert resp["statusCode"] == 201
    data = json.loads(resp["body"])["data"]
    assert data["author"] == "Anonymous"
    assert data["status"] == "pending"


def test_list_testimonials_only_shows_approved(ddb_table):
    from router import route
    from models.testimonials import create_testimonial, approve_testimonial
    t = create_testimonial("Great!", "Alice", "MCRI", False)
    approve_testimonial(t["testimonial_id"])

    # Also create a pending one
    create_testimonial("Also great!", "Bob", "Friend", False)

    resp = route(make_event("GET", "/testimonials"))
    assert resp["statusCode"] == 200
    items = json.loads(resp["body"])["data"]
    assert all(t["status"] == "approved" for t in items)
    assert len(items) == 1


def test_filter_testimonials_by_identity(ddb_table):
    from router import route
    from models.testimonials import create_testimonial, approve_testimonial
    t1 = create_testimonial("From Jamf!", "Alice", "Jamf", False)
    t2 = create_testimonial("From MCRI!", "Bob", "MCRI", False)
    approve_testimonial(t1["testimonial_id"])
    approve_testimonial(t2["testimonial_id"])

    resp = route(make_event("GET", "/testimonials", query={"identity": "Jamf"}))
    items = json.loads(resp["body"])["data"]
    assert all(t["identity"] == "Jamf" for t in items)
