from auth import require_auth
from models import settings as s
from utils import ok


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
