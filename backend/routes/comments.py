from auth import require_auth, require_admin, get_current_user
from models import interactions as m
from models.users import get_user_by_id
from models.projects import get_project
from models.courses import get_course
from utils import ok, created, not_found, bad_request


def _entity_pk(path: str, entity_id: str) -> str | None:
    if "projects" in path:
        return f"PROJECT#{entity_id}" if get_project(entity_id) else None
    if "courses" in path:
        return f"COURSE#{entity_id}" if get_course(entity_id) else None
    return None


def list_comments(event, path_params, body, query, headers):
    entity_id = path_params["id"]
    path = event.get("rawPath", "")
    pk = _entity_pk(path, entity_id)
    if pk is None:
        return not_found("Entity not found")
    return ok(m.list_comments(pk))


@require_auth
def create_comment(event, path_params, body, query, headers, user):
    if not body.get("body"):
        return bad_request("body is required")
    entity_id = path_params["id"]
    path = event.get("rawPath", "")
    pk = _entity_pk(path, entity_id)
    if pk is None:
        return not_found("Entity not found")
    profile = get_user_by_id(user["sub"]) or {}
    comment = m.create_comment(
        pk,
        user["sub"],
        profile.get("name", "Unknown"),
        profile.get("identity", "Other"),
        body["body"],
    )
    return created(comment)


@require_admin
def delete_comment(event, path_params, body, query, headers, user):
    comment_id = path_params["id"]
    entity_pk = query.get("entity_pk", "")
    if entity_pk:
        pk, sk = m.find_comment_pk_sk(comment_id, entity_pk)
        if pk:
            m.delete_comment_by_sk(pk, sk)
            return ok({"deleted": True})
    return not_found("Comment not found")
