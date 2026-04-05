from models import visits as visit_model
from utils import ok, bad_request


def record_visit(event, path_params, body, query, headers):
    ip = event.get("requestContext", {}).get("http", {}).get("sourceIp", "")
    page = body.get("page", "")
    if not ip:
        return bad_request("Missing source IP")
    if not page:
        return bad_request("Missing page")
    visit_model.upsert_visitor(ip)
    visit_model.record_pageview(ip, page)
    return ok(None)
