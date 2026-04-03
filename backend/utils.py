import json


def cors_response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        },
        "body": json.dumps(body, default=str),
    }


def ok(data) -> dict:
    return cors_response(200, {"data": data, "error": None})


def created(data) -> dict:
    return cors_response(201, {"data": data, "error": None})


def bad_request(message: str) -> dict:
    return cors_response(400, {"data": None, "error": message})


def unauthorized(message: str = "Authentication required") -> dict:
    return cors_response(401, {"data": None, "error": message})


def forbidden(message: str = "Forbidden") -> dict:
    return cors_response(403, {"data": None, "error": message})


def not_found(message: str = "Not found") -> dict:
    return cors_response(404, {"data": None, "error": message})


def conflict(message: str) -> dict:
    return cors_response(409, {"data": None, "error": message})


def rate_limited(message: str = "Rate limit exceeded. Try again later.") -> dict:
    return cors_response(429, {"data": None, "error": message})


def server_error(message: str = "Internal server error") -> dict:
    return cors_response(500, {"data": None, "error": message})
