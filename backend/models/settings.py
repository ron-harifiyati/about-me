from db import get_table
from boto3.dynamodb.conditions import Key, Attr


def get_user_comments(user_id: str) -> list:
    """Scan all comments by this user across all entities."""
    table = get_table()
    resp = table.scan(
        FilterExpression=Attr("SK").begins_with("COMMENT#") & Attr("user_id").eq(user_id),
    )
    items = resp.get("Items", [])
    for item in items:
        item.pop("PK", None)
    return sorted(items, key=lambda x: x.get("created_at", 0), reverse=True)


def get_user_ratings(user_id: str) -> list:
    """Scan all ratings by this user."""
    table = get_table()
    resp = table.scan(
        FilterExpression=Attr("SK").begins_with("RATING#") & Attr("user_id").eq(user_id),
    )
    items = resp.get("Items", [])
    for item in items:
        item.pop("PK", None)
        if "stars" in item:
            item["stars"] = int(item["stars"])
    return sorted(items, key=lambda x: x.get("created_at", 0), reverse=True)


def get_user_quiz_scores(user_id: str) -> list:
    """Query quiz scores for a user (keyed by PK=USER#{user_id})."""
    table = get_table()
    resp = table.query(
        KeyConditionExpression=Key("PK").eq(f"USER#{user_id}") & Key("SK").begins_with("QUIZ_SCORE#"),
    )
    items = resp.get("Items", [])
    for item in items:
        item.pop("PK", None)
        item.pop("SK", None)
        item.pop("GSI3PK", None)
        item.pop("GSI3SK", None)
    return sorted(items, key=lambda x: x.get("created_at", 0), reverse=True)


def get_user_guestbook_entries(user_id: str) -> list:
    """Scan guestbook entries by this user."""
    table = get_table()
    resp = table.scan(
        FilterExpression=Attr("PK").eq("GUESTBOOK") & Attr("user_id").eq(user_id),
    )
    items = resp.get("Items", [])
    for item in items:
        item.pop("PK", None)
    return sorted(items, key=lambda x: x.get("created_at", 0), reverse=True)


def get_user_testimonials(user_id: str) -> list:
    """Scan testimonials by this user."""
    table = get_table()
    resp = table.scan(
        FilterExpression=Attr("PK").eq("TESTIMONIALS") & Attr("user_id").eq(user_id),
    )
    items = resp.get("Items", [])
    for item in items:
        item.pop("PK", None)
        item.pop("SK", None)
        item.pop("GSI2PK", None)
        item.pop("GSI2SK", None)
    return sorted(items, key=lambda x: x.get("created_at", 0), reverse=True)
