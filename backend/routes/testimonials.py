from auth import get_current_user
from models import testimonials as t
from models.users import get_user_by_id
from utils import ok, created, bad_request


def list_testimonials(event, path_params, body, query, headers):
    identity = query.get("identity")
    return ok(t.list_approved(identity))


def submit_testimonial(event, path_params, body, query, headers):
    text = (body.get("body") or "").strip()
    if not text:
        return bad_request("body is required")

    anonymous = bool(body.get("anonymous", False))
    user = get_current_user(headers)
    if user:
        profile = get_user_by_id(user["sub"]) or {}
        author = profile.get("name", "Anonymous")
        identity = profile.get("identity", "Other")
    else:
        author = (body.get("author") or "Anonymous").strip()
        identity = body.get("identity", "Other")
        anonymous = True  # guests are always anonymous

    uid = user["sub"] if user else None
    testimonial = t.create_testimonial(text, author, identity, anonymous, user_id=uid)
    return created(testimonial)
