from auth import require_admin
from models import projects as project_model
from utils import ok, created, not_found, bad_request


def list_projects(event, path_params, body, query, headers):
    return ok(project_model.list_projects())


def get_project(event, path_params, body, query, headers):
    project = project_model.get_project(path_params["id"])
    return ok(project) if project else not_found("Project not found")


@require_admin
def create_project(event, path_params, body, query, headers, user):
    if not body.get("title"):
        return bad_request("title is required")
    return created(project_model.create_project(body))


@require_admin
def update_project(event, path_params, body, query, headers, user):
    result = project_model.update_project(path_params["id"], body)
    return ok(result) if result else not_found("Project not found")


@require_admin
def delete_project(event, path_params, body, query, headers, user):
    success = project_model.delete_project(path_params["id"])
    return ok({"deleted": True}) if success else not_found("Project not found")
