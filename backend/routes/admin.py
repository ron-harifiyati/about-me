from auth import require_admin
from models.users import list_all_users, set_user_status, delete_user as delete_user_model, get_user_by_id
from models.contacts import list_contacts as list_contacts_model, delete_contact_by_sk
from models.testimonials import list_pending, list_approved, approve_testimonial, reject_testimonial, delete_testimonial
from models import quiz as quiz_model
from utils import ok, created, bad_request, not_found


@require_admin
def list_users(event, path_params, body, query, headers, user):
    return ok(list_all_users())


@require_admin
def update_user(event, path_params, body, query, headers, user):
    uid = path_params["id"]
    status = body.get("status")
    if status not in ("active", "suspended", "banned"):
        return bad_request("status must be active, suspended, or banned")
    if not get_user_by_id(uid):
        return not_found("User not found")
    set_user_status(uid, status)
    return ok(get_user_by_id(uid))


@require_admin
def delete_user(event, path_params, body, query, headers, user):
    uid = path_params["id"]
    if not get_user_by_id(uid):
        return not_found("User not found")
    delete_user_model(uid)
    return ok({"deleted": True})


@require_admin
def list_contacts(event, path_params, body, query, headers, user):
    return ok(list_contacts_model())


@require_admin
def delete_contact(event, path_params, body, query, headers, user):
    sk = query.get("sk", "")
    if not sk:
        return bad_request("sk is required")
    delete_contact_by_sk(sk)
    return ok({"deleted": True})


@require_admin
def list_pending_testimonials(event, path_params, body, query, headers, user):
    return ok(list_pending())


@require_admin
def list_approved_testimonials(event, path_params, body, query, headers, user):
    return ok(list_approved())


@require_admin
def delete_testimonial_handler(event, path_params, body, query, headers, user):
    delete_testimonial(path_params["id"])
    return ok({"deleted": True})


@require_admin
def update_testimonial(event, path_params, body, query, headers, user):
    tid = path_params["id"]
    action = body.get("action")
    if action == "approve":
        approve_testimonial(tid)
        return ok({"action": "approved"})
    elif action == "reject":
        reject_testimonial(tid)
        return ok({"action": "rejected"})
    return bad_request("action must be 'approve' or 'reject'")


@require_admin
def list_quiz_questions(event, path_params, body, query, headers, user):
    return ok(quiz_model.list_questions())


@require_admin
def create_quiz_question(event, path_params, body, query, headers, user):
    for field in ("question", "options", "answer", "topic"):
        if not body.get(field):
            return bad_request(f"{field} is required")
    return created(quiz_model.create_question(body))


@require_admin
def update_quiz_question(event, path_params, body, query, headers, user):
    result = quiz_model.update_question(path_params["id"], body)
    return ok(result) if result else not_found("Question not found")


@require_admin
def delete_quiz_question(event, path_params, body, query, headers, user):
    success = quiz_model.delete_question(path_params["id"])
    return ok({"deleted": True}) if success else not_found("Question not found")
