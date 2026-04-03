from auth import get_current_user
from models import guestbook as g
from models.users import get_user_by_id
from utils import ok, created, bad_request


def list_entries(event, path_params, body, query, headers):
    return ok(g.list_entries())


def create_entry(event, path_params, body, query, headers):
    name = (body.get("name") or "").strip()
    message = (body.get("message") or "").strip()
    if not name or not message:
        return bad_request("name and message are required")

    user = get_current_user(headers)
    if user:
        profile = get_user_by_id(user["sub"]) or {}
        display_name = profile.get("name", name)
        identity = profile.get("identity")
        entry = g.create_entry(display_name, message, True, identity)
    else:
        entry = g.create_entry(f"{name} (guest)", message, False)

    return created(entry)
