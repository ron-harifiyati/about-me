from auth import require_auth
from models import settings as s
from utils import ok, not_found, bad_request
from models.users import user_has_password, delete_user


@require_auth
def get_my_comments(event, path_params, body, query, headers, user):
    return ok(s.get_user_comments(user["sub"]))


@require_auth
def get_my_ratings(event, path_params, body, query, headers, user):
    return ok(s.get_user_ratings(user["sub"]))


@require_auth
def get_my_quiz_scores(event, path_params, body, query, headers, user):
    return ok(s.get_user_quiz_scores(user["sub"]))


@require_auth
def get_my_guestbook_entries(event, path_params, body, query, headers, user):
    return ok(s.get_user_guestbook_entries(user["sub"]))


@require_auth
def get_my_testimonials(event, path_params, body, query, headers, user):
    return ok(s.get_user_testimonials(user["sub"]))


@require_auth
def delete_my_comment(event, path_params, body, query, headers, user):
    comment_id = path_params["id"]
    if s.delete_user_comment(user["sub"], comment_id):
        return ok({"deleted": True})
    return not_found("Comment not found")


@require_auth
def delete_my_guestbook_entry(event, path_params, body, query, headers, user):
    entry_id = path_params["id"]
    if s.delete_user_guestbook_entry(user["sub"], entry_id):
        return ok({"deleted": True})
    return not_found("Guestbook entry not found")


@require_auth
def get_connections(event, path_params, body, query, headers, user):
    providers = s.get_user_oauth_links(user["sub"])
    return ok({"providers": providers})


@require_auth
def delete_account(event, path_params, body, query, headers, user):
    confirmation = body.get("confirmation", "")
    if confirmation != "DELETE":
        return bad_request("Type DELETE to confirm account deletion")
    user_id = user["sub"]
    s.anonymize_user_content(user_id)
    s.delete_user_oauth_links(user_id)
    s.delete_user_sessions(user_id)
    delete_user(user_id)
    return ok({"message": "Account deleted"})


@require_auth
def disconnect_oauth(event, path_params, body, query, headers, user):
    provider = path_params["provider"]
    if provider not in ("github", "google"):
        return bad_request("Invalid provider")
    has_pw = user_has_password(user["sub"])
    links = s.get_user_oauth_links(user["sub"])
    other_links = [lnk for lnk in links if lnk["provider"] != provider]
    if not has_pw and len(other_links) == 0:
        return bad_request(
            "Cannot disconnect your last sign-in method. Set a password or connect another provider first."
        )
    if s.delete_oauth_link(user["sub"], provider):
        return ok({"disconnected": True})
    return not_found("Provider not connected")
