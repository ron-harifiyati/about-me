from auth import require_admin
from models import visits as visit_model
from utils import ok


def get_visitor_locations(event, path_params, body, query, headers):
    return ok(visit_model.get_visitor_locations())


@require_admin
def get_analytics(event, path_params, body, query, headers, user):
    return ok(visit_model.get_analytics())
