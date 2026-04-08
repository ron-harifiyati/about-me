import json
import re
from utils import cors_response, not_found


def _parse_body(event: dict) -> dict:
    body = event.get("body") or ""
    if not body:
        return {}
    try:
        return json.loads(body)
    except (ValueError, TypeError):
        return {}


def route(event: dict) -> dict:
    ctx = event.get("requestContext", {}).get("http", {})
    method = ctx.get("method", "GET").upper()
    path = event.get("rawPath", "/").rstrip("/") or "/"
    body = _parse_body(event)
    query = event.get("queryStringParameters") or {}
    headers = event.get("headers") or {}

    if method == "OPTIONS":
        return cors_response(200, {})

    # Record visit (best-effort)
    ip = ctx.get("sourceIp", "")
    if ip:
        try:
            from models.visits import record_visit
            record_visit(ip, path)
        except Exception:
            pass

    # Import route handlers here to keep imports lazy
    from routes import (
        meta, content, projects, courses, github,
        auth_routes, comments, ratings, guestbook,
        quiz, testimonials, stats, contact, admin, docs, visits,
    )

    # (method, pattern, handler)  — exact strings matched first, regex second
    ROUTES = [
        # Meta & docs
        ("GET",    "/meta",                           meta.get_meta),
        ("GET",    "/api",                            docs.swagger_ui),
        ("GET",    "/api/spec",                       docs.openapi_spec),
        # Content
        ("GET",    "/about",                          content.get_about),
        ("PUT",    "/about",                          content.update_about),
        ("GET",    "/skills",                         content.get_skills),
        ("PUT",    "/skills",                         content.update_skills),
        ("GET",    "/timeline",                       content.get_timeline),
        ("PUT",    "/timeline",                       content.update_timeline),
        ("GET",    "/fun-fact",                       content.get_fun_fact),
        ("GET",    "/fun-facts",                      content.get_all_fun_facts),
        ("PUT",    "/fun-fact",                       content.update_fun_facts),
        ("GET",    "/currently-learning",             content.get_currently_learning),
        ("PUT",    "/currently-learning",             content.update_currently_learning),
        ("GET",    "/languages",                      content.get_languages),
        ("PUT",    "/languages",                      content.update_languages),
        ("GET",    "/hobbies",                        content.get_hobbies),
        ("PUT",    "/hobbies",                        content.update_hobbies),
        ("GET",    "/values",                         content.get_values),
        ("PUT",    "/values",                         content.update_values),
        # Projects
        ("GET",    "/projects",                       projects.list_projects),
        ("POST",   "/projects",                       projects.create_project),
        ("GET",    r"/projects/(?P<id>[^/]+)$",       projects.get_project),
        ("PUT",    r"/projects/(?P<id>[^/]+)$",       projects.update_project),
        ("DELETE", r"/projects/(?P<id>[^/]+)$",       projects.delete_project),
        ("GET",    r"/projects/(?P<id>[^/]+)/comments$",  comments.list_comments),
        ("POST",   r"/projects/(?P<id>[^/]+)/comments$",  comments.create_comment),
        ("GET",    r"/projects/(?P<id>[^/]+)/ratings$",   ratings.get_ratings),
        ("POST",   r"/projects/(?P<id>[^/]+)/ratings$",   ratings.submit_rating),
        # Courses
        ("GET",    "/courses",                        courses.list_courses),
        ("POST",   "/courses",                        courses.create_course),
        ("GET",    r"/courses/(?P<id>[^/]+)$",        courses.get_course),
        ("PUT",    r"/courses/(?P<id>[^/]+)$",        courses.update_course),
        ("DELETE", r"/courses/(?P<id>[^/]+)$",        courses.delete_course),
        ("GET",    r"/courses/(?P<id>[^/]+)/comments$",   comments.list_comments),
        ("POST",   r"/courses/(?P<id>[^/]+)/comments$",   comments.create_comment),
        ("GET",    r"/courses/(?P<id>[^/]+)/ratings$",    ratings.get_ratings),
        ("POST",   r"/courses/(?P<id>[^/]+)/ratings$",    ratings.submit_rating),
        # Comments (admin delete)
        ("DELETE", r"/comments/(?P<id>[^/]+)$",       comments.delete_comment),
        # GitHub
        ("GET",    "/github/repos",                   github.get_repos),
        # Auth
        ("POST",   "/auth/register",                  auth_routes.register),
        ("POST",   "/auth/verify-email",              auth_routes.verify_email),
        ("POST",   "/auth/resend-verification",       auth_routes.resend_verification),
        ("POST",   "/auth/forgot-password",           auth_routes.forgot_password),
        ("POST",   "/auth/reset-password",            auth_routes.reset_password),
        ("POST",   "/auth/login",                     auth_routes.login),
        ("POST",   "/auth/logout",                    auth_routes.logout),
        ("POST",   "/auth/refresh",                   auth_routes.refresh),
        ("GET",    "/auth/me",                        auth_routes.get_me),
        ("PUT",    "/auth/me",                        auth_routes.update_me),
        ("GET",    "/auth/oauth/github",              auth_routes.oauth_github_init),
        ("GET",    "/auth/oauth/github/callback",     auth_routes.oauth_github_callback),
        ("GET",    "/auth/oauth/google",              auth_routes.oauth_google_init),
        ("GET",    "/auth/oauth/google/callback",     auth_routes.oauth_google_callback),
        # Guestbook
        ("GET",    "/guestbook",                      guestbook.list_entries),
        ("POST",   "/guestbook",                      guestbook.create_entry),
        ("DELETE", r"/guestbook/(?P<id>[^/]+)$",      guestbook.delete_entry),
        # Quiz
        ("GET",    "/quiz/questions",                 quiz.get_questions),
        ("POST",   "/quiz/submit",                    quiz.submit_answers),
        ("GET",    "/quiz/leaderboard",               quiz.get_leaderboard),
        # Testimonials
        ("GET",    "/testimonials",                   testimonials.list_testimonials),
        ("POST",   "/testimonials",                   testimonials.submit_testimonial),
        # Stats
        ("GET",    "/stats/visitors",                 stats.get_visitor_locations),
        ("GET",    "/stats/pageviews",                stats.get_pageviews),
        ("GET",    "/stats/analytics",                stats.get_analytics),
        # Visits
        ("POST",   "/visits",                         visits.record_visit),
        # Contact
        ("POST",   "/contact",                        contact.submit_contact),
        # Admin
        ("GET",    "/admin/users",                    admin.list_users),
        ("PUT",    r"/admin/users/(?P<id>[^/]+)$",    admin.update_user),
        ("DELETE", r"/admin/users/(?P<id>[^/]+)$",    admin.delete_user),
        ("GET",    "/admin/contacts",                 admin.list_contacts),
        ("DELETE", r"/admin/contacts/(?P<id>[^/]+)$", admin.delete_contact),
        ("GET",    "/admin/testimonials/pending",      admin.list_pending_testimonials),
        ("GET",    "/admin/testimonials/approved",     admin.list_approved_testimonials),
        ("DELETE", r"/admin/testimonials/(?P<id>[^/]+)$", admin.delete_testimonial_handler),
        ("PUT",    r"/admin/testimonials/(?P<id>[^/]+)$", admin.update_testimonial),
        ("GET",    "/admin/quiz/questions",           admin.list_quiz_questions),
        ("POST",   "/admin/quiz/questions",           admin.create_quiz_question),
        ("PUT",    r"/admin/quiz/questions/(?P<id>[^/]+)$", admin.update_quiz_question),
        ("DELETE", r"/admin/quiz/questions/(?P<id>[^/]+)$", admin.delete_quiz_question),
    ]

    for route_method, pattern, handler_fn in ROUTES:
        if method != route_method:
            continue
        if pattern == path:
            return handler_fn(event, {}, body, query, headers)
        m = re.fullmatch(pattern, path)
        if m:
            return handler_fn(event, m.groupdict(), body, query, headers)

    return not_found("Route not found")
