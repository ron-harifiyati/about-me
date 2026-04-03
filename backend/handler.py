from router import route
from utils import server_error


def handler(event, context):
    try:
        return route(event)
    except Exception as exc:
        print(f"Unhandled error: {exc}")
        return server_error()
