import json
import os

SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "Portfolio API",
        "version": "1.0.0",
        "description": "Personal portfolio API for Ron Harifiyati",
    },
    "servers": [{"url": "/"}],
    "components": {
        "securitySchemes": {
            "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
        }
    },
    "paths": {
        "/meta": {"get": {"summary": "Site metadata", "tags": ["Meta"], "responses": {"200": {"description": "OK"}}}},
        "/about": {
            "get": {"summary": "About section", "tags": ["Content"], "responses": {"200": {"description": "OK"}}},
            "put": {"summary": "Update about", "tags": ["Content"], "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "OK"}}},
        },
        "/skills": {
            "get": {"summary": "Skills list", "tags": ["Content"], "responses": {"200": {"description": "OK"}}},
            "put": {"summary": "Update skills", "tags": ["Content"], "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "OK"}}},
        },
        "/timeline": {
            "get": {"summary": "Timeline events", "tags": ["Content"], "responses": {"200": {"description": "OK"}}},
            "put": {"summary": "Update timeline", "tags": ["Content"], "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "OK"}}},
        },
        "/fun-fact": {
            "get": {"summary": "Fun facts", "tags": ["Content"], "responses": {"200": {"description": "OK"}}},
            "put": {"summary": "Update fun facts", "tags": ["Content"], "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "OK"}}},
        },
        "/currently-learning": {
            "get": {"summary": "Currently learning", "tags": ["Content"], "responses": {"200": {"description": "OK"}}},
            "put": {"summary": "Update currently learning", "tags": ["Content"], "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "OK"}}},
        },
        "/projects": {
            "get": {"summary": "List projects", "tags": ["Projects"], "responses": {"200": {"description": "OK"}}},
            "post": {"summary": "Create project", "tags": ["Projects"], "security": [{"bearerAuth": []}],
                     "responses": {"201": {"description": "Created"}}},
        },
        "/projects/{id}": {
            "get": {"summary": "Get project", "tags": ["Projects"], "responses": {"200": {"description": "OK"}}},
            "put": {"summary": "Update project", "tags": ["Projects"], "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "OK"}}},
            "delete": {"summary": "Delete project", "tags": ["Projects"], "security": [{"bearerAuth": []}],
                       "responses": {"200": {"description": "OK"}}},
        },
        "/projects/{id}/comments": {
            "get": {"summary": "List project comments", "tags": ["Comments"],
                    "responses": {"200": {"description": "OK"}}},
            "post": {"summary": "Add comment", "tags": ["Comments"], "security": [{"bearerAuth": []}],
                     "responses": {"201": {"description": "Created"}}},
        },
        "/projects/{id}/ratings": {
            "get": {"summary": "Get project ratings", "tags": ["Ratings"],
                    "responses": {"200": {"description": "OK"}}},
            "post": {"summary": "Submit rating", "tags": ["Ratings"], "security": [{"bearerAuth": []}],
                     "responses": {"200": {"description": "OK"}}},
        },
        "/courses": {
            "get": {"summary": "List courses", "tags": ["Courses"], "responses": {"200": {"description": "OK"}}},
            "post": {"summary": "Create course", "tags": ["Courses"], "security": [{"bearerAuth": []}],
                     "responses": {"201": {"description": "Created"}}},
        },
        "/courses/{id}": {
            "get": {"summary": "Get course", "tags": ["Courses"], "responses": {"200": {"description": "OK"}}},
            "put": {"summary": "Update course", "tags": ["Courses"], "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "OK"}}},
            "delete": {"summary": "Delete course", "tags": ["Courses"], "security": [{"bearerAuth": []}],
                       "responses": {"200": {"description": "OK"}}},
        },
        "/courses/{id}/comments": {
            "get": {"summary": "List course comments", "tags": ["Comments"],
                    "responses": {"200": {"description": "OK"}}},
            "post": {"summary": "Add comment", "tags": ["Comments"], "security": [{"bearerAuth": []}],
                     "responses": {"201": {"description": "Created"}}},
        },
        "/courses/{id}/ratings": {
            "get": {"summary": "Get course ratings", "tags": ["Ratings"],
                    "responses": {"200": {"description": "OK"}}},
            "post": {"summary": "Submit rating", "tags": ["Ratings"], "security": [{"bearerAuth": []}],
                     "responses": {"200": {"description": "OK"}}},
        },
        "/comments/{id}": {
            "delete": {"summary": "Delete comment (admin)", "tags": ["Admin"], "security": [{"bearerAuth": []}],
                       "responses": {"200": {"description": "OK"}}},
        },
        "/github/repos": {
            "get": {"summary": "GitHub repos", "tags": ["GitHub"], "responses": {"200": {"description": "OK"}}}
        },
        "/auth/register": {
            "post": {"summary": "Register", "tags": ["Auth"], "responses": {"201": {"description": "Created"}}}
        },
        "/auth/verify-email": {
            "post": {"summary": "Verify email", "tags": ["Auth"], "responses": {"200": {"description": "OK"}}}
        },
        "/auth/resend-verification": {
            "post": {"summary": "Resend verification email", "tags": ["Auth"],
                     "responses": {"200": {"description": "OK"}}}
        },
        "/auth/forgot-password": {
            "post": {"summary": "Request password reset", "tags": ["Auth"],
                     "responses": {"200": {"description": "OK"}}}
        },
        "/auth/reset-password": {
            "post": {"summary": "Reset password with token", "tags": ["Auth"],
                     "responses": {"200": {"description": "OK"}}}
        },
        "/auth/login": {
            "post": {"summary": "Login", "tags": ["Auth"], "responses": {"200": {"description": "OK"}}}
        },
        "/auth/logout": {
            "post": {"summary": "Logout", "tags": ["Auth"], "security": [{"bearerAuth": []}],
                     "responses": {"200": {"description": "OK"}}}
        },
        "/auth/refresh": {
            "post": {"summary": "Refresh token", "tags": ["Auth"], "responses": {"200": {"description": "OK"}}}
        },
        "/auth/me": {
            "get": {"summary": "Get current user", "tags": ["Auth"], "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "OK"}}},
            "put": {"summary": "Update profile", "tags": ["Auth"], "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "OK"}}},
        },
        "/auth/oauth/github": {
            "get": {"summary": "GitHub OAuth init", "tags": ["Auth"], "responses": {"302": {"description": "Redirect"}}}
        },
        "/auth/oauth/github/callback": {
            "get": {"summary": "GitHub OAuth callback", "tags": ["Auth"],
                    "responses": {"200": {"description": "OK"}}}
        },
        "/auth/oauth/google": {
            "get": {"summary": "Google OAuth init", "tags": ["Auth"], "responses": {"302": {"description": "Redirect"}}}
        },
        "/auth/oauth/google/callback": {
            "get": {"summary": "Google OAuth callback", "tags": ["Auth"],
                    "responses": {"200": {"description": "OK"}}}
        },
        "/guestbook": {
            "get": {"summary": "List guestbook entries", "tags": ["Guestbook"],
                    "responses": {"200": {"description": "OK"}}},
            "post": {"summary": "Sign guestbook", "tags": ["Guestbook"],
                     "responses": {"201": {"description": "Created"}}},
        },
        "/quiz/questions": {
            "get": {"summary": "Get quiz questions", "tags": ["Quiz"], "responses": {"200": {"description": "OK"}}}
        },
        "/quiz/submit": {
            "post": {"summary": "Submit answers", "tags": ["Quiz"], "security": [{"bearerAuth": []}],
                     "responses": {"200": {"description": "OK"}}}
        },
        "/quiz/leaderboard": {
            "get": {"summary": "Leaderboard", "tags": ["Quiz"], "responses": {"200": {"description": "OK"}}}
        },
        "/testimonials": {
            "get": {"summary": "List approved testimonials", "tags": ["Testimonials"],
                    "responses": {"200": {"description": "OK"}}},
            "post": {"summary": "Submit testimonial", "tags": ["Testimonials"],
                     "responses": {"201": {"description": "Created"}}},
        },
        "/visits": {
            "post": {"summary": "Record page visit", "tags": ["Stats"],
                     "requestBody": {"required": True, "content": {"application/json": {"schema": {
                         "type": "object", "required": ["page"],
                         "properties": {"page": {"type": "string", "example": "home"}}
                     }}}},
                     "responses": {"200": {"description": "OK"}}}
        },
        "/stats/visitors": {
            "get": {"summary": "Unique visitor locations", "tags": ["Stats"],
                    "responses": {"200": {"description": "OK"}}}
        },
        "/stats/pageviews": {
            "get": {"summary": "Page view counts", "tags": ["Stats"], "responses": {"200": {"description": "OK"}}}
        },
        "/stats/analytics": {
            "get": {"summary": "Analytics breakdown (admin)", "tags": ["Stats"],
                    "security": [{"bearerAuth": []}], "responses": {"200": {"description": "OK"}}}
        },
        "/contact": {
            "post": {"summary": "Submit contact form", "tags": ["Contact"],
                     "responses": {"201": {"description": "Created"}}}
        },
        "/admin/users": {
            "get": {"summary": "List users (admin)", "tags": ["Admin"], "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "OK"}}}
        },
        "/admin/users/{id}": {
            "put": {"summary": "Update user status (admin)", "tags": ["Admin"], "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "OK"}}},
            "delete": {"summary": "Delete user (admin)", "tags": ["Admin"], "security": [{"bearerAuth": []}],
                       "responses": {"200": {"description": "OK"}}},
        },
        "/admin/contacts": {
            "get": {"summary": "List contacts (admin)", "tags": ["Admin"], "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "OK"}}}
        },
        "/admin/testimonials/pending": {
            "get": {"summary": "List pending testimonials (admin)", "tags": ["Admin"],
                    "security": [{"bearerAuth": []}], "responses": {"200": {"description": "OK"}}}
        },
        "/admin/testimonials/{id}": {
            "put": {"summary": "Approve/reject testimonial (admin)", "tags": ["Admin"],
                    "security": [{"bearerAuth": []}], "responses": {"200": {"description": "OK"}}}
        },
        "/admin/quiz/questions": {
            "get": {"summary": "List all quiz questions (admin)", "tags": ["Admin"],
                    "security": [{"bearerAuth": []}], "responses": {"200": {"description": "OK"}}},
            "post": {"summary": "Create quiz question (admin)", "tags": ["Admin"],
                     "security": [{"bearerAuth": []}], "responses": {"201": {"description": "Created"}}},
        },
        "/admin/quiz/questions/{id}": {
            "put": {"summary": "Update quiz question (admin)", "tags": ["Admin"],
                    "security": [{"bearerAuth": []}], "responses": {"200": {"description": "OK"}}},
            "delete": {"summary": "Delete quiz question (admin)", "tags": ["Admin"],
                       "security": [{"bearerAuth": []}], "responses": {"200": {"description": "OK"}}},
        },
    },
}

_CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
}

_API_BASE = os.environ.get("API_BASE_URL", "")

_SWAGGER_HTML = """<!DOCTYPE html>
<html>
<head>
  <title>Portfolio API Docs</title>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
<div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>
  SwaggerUIBundle({
    url: "{api_base}/api/spec",
    dom_id: '#swagger-ui',
    presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
    layout: "BaseLayout"
  })
</script>
</body>
</html>"""


def swagger_ui(event, path_params, body, query, headers):
    api_base = os.environ.get("API_BASE_URL", "")
    html = _SWAGGER_HTML.replace("{api_base}", api_base)
    return {
        "statusCode": 200,
        "headers": {**_CORS, "Content-Type": "text/html"},
        "body": html,
    }


def openapi_spec(event, path_params, body, query, headers):
    return {
        "statusCode": 200,
        "headers": {**_CORS, "Content-Type": "application/json"},
        "body": json.dumps(SPEC),
    }
