from auth import require_admin
from models import courses as course_model
from utils import ok, created, not_found, bad_request


def list_courses(event, path_params, body, query, headers):
    return ok(course_model.list_courses())


def get_course(event, path_params, body, query, headers):
    course = course_model.get_course(path_params["id"])
    return ok(course) if course else not_found("Course not found")


@require_admin
def create_course(event, path_params, body, query, headers, user):
    if not body.get("title"):
        return bad_request("title is required")
    return created(course_model.create_course(body))


@require_admin
def update_course(event, path_params, body, query, headers, user):
    result = course_model.update_course(path_params["id"], body)
    return ok(result) if result else not_found("Course not found")


@require_admin
def delete_course(event, path_params, body, query, headers, user):
    success = course_model.delete_course(path_params["id"])
    return ok({"deleted": True}) if success else not_found("Course not found")
