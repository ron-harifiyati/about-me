import random
from auth import require_admin
from models.content import get_content, update_content
from utils import ok


def get_about(event, path_params, body, query, headers):
    return ok(get_content("ABOUT"))


@require_admin
def update_about(event, path_params, body, query, headers, user):
    return ok(update_content("ABOUT", body))


def get_skills(event, path_params, body, query, headers):
    return ok(get_content("SKILLS"))


@require_admin
def update_skills(event, path_params, body, query, headers, user):
    return ok(update_content("SKILLS", body))


def get_timeline(event, path_params, body, query, headers):
    return ok(get_content("TIMELINE"))


@require_admin
def update_timeline(event, path_params, body, query, headers, user):
    return ok(update_content("TIMELINE", body))


def get_fun_fact(event, path_params, body, query, headers):
    data = get_content("FUNFACTS")
    if not data or not data.get("facts"):
        return ok({"fact": None})
    return ok({"fact": random.choice(data["facts"])})


@require_admin
def update_fun_facts(event, path_params, body, query, headers, user):
    return ok(update_content("FUNFACTS", body))


def get_currently_learning(event, path_params, body, query, headers):
    return ok(get_content("CURRENTLY_LEARNING"))


@require_admin
def update_currently_learning(event, path_params, body, query, headers, user):
    return ok(update_content("CURRENTLY_LEARNING", body))


def get_languages(event, path_params, body, query, headers):
    return ok(get_content("LANGUAGES_SPOKEN"))


@require_admin
def update_languages(event, path_params, body, query, headers, user):
    return ok(update_content("LANGUAGES_SPOKEN", body))


def get_hobbies(event, path_params, body, query, headers):
    return ok(get_content("HOBBIES"))


@require_admin
def update_hobbies(event, path_params, body, query, headers, user):
    return ok(update_content("HOBBIES", body))


def get_values(event, path_params, body, query, headers):
    return ok(get_content("VALUES"))


@require_admin
def update_values(event, path_params, body, query, headers, user):
    return ok(update_content("VALUES", body))
