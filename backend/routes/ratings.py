from auth import require_auth
from models import interactions as m
from models.projects import get_project
from models.courses import get_course
from utils import ok, not_found, bad_request


def _entity_pk(path: str, entity_id: str) -> str | None:
    if "projects" in path:
        return f"PROJECT#{entity_id}" if get_project(entity_id) else None
    if "courses" in path:
        return f"COURSE#{entity_id}" if get_course(entity_id) else None
    return None


def get_ratings(event, path_params, body, query, headers):
    pk = _entity_pk(event.get("rawPath", ""), path_params["id"])
    if pk is None:
        return not_found("Entity not found")
    return ok(m.get_ratings_summary(pk))


@require_auth
def submit_rating(event, path_params, body, query, headers, user):
    stars = body.get("stars")
    if stars not in (1, 2, 3, 4, 5):
        return bad_request("stars must be an integer 1-5")
    pk = _entity_pk(event.get("rawPath", ""), path_params["id"])
    if pk is None:
        return not_found("Entity not found")
    return ok(m.submit_rating(pk, user["sub"], int(stars)))
