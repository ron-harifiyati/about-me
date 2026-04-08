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


def delete_user_comment(user_id: str, comment_id: str) -> bool:
    """Find and delete a comment owned by this user. Returns True if found and deleted."""
    table = get_table()
    filt = Attr("SK").begins_with("COMMENT#") & Attr("comment_id").eq(comment_id) & Attr("user_id").eq(user_id)
    resp = table.scan(FilterExpression=filt)
    items = resp.get("Items", [])
    if not items:
        return False
    item = items[0]
    table.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})
    return True


def get_user_oauth_links(user_id: str) -> list:
    """Scan for all OAuth links belonging to this user."""
    table = get_table()
    resp = table.scan(
        FilterExpression=Attr("SK").eq("LINK") & Attr("user_id").eq(user_id),
    )
    items = resp.get("Items", [])
    return [
        {
            "provider": item.get("provider"),
            "provider_id": item.get("provider_id"),
            "provider_username": item.get("provider_username"),
        }
        for item in items
    ]


def delete_oauth_link(user_id: str, provider: str) -> bool:
    """Delete OAuth link for a specific provider. Returns True if found and deleted."""
    table = get_table()
    resp = table.scan(
        FilterExpression=Attr("SK").eq("LINK") & Attr("user_id").eq(user_id) & Attr("provider").eq(provider),
    )
    items = resp.get("Items", [])
    if not items:
        return False
    table.delete_item(Key={"PK": items[0]["PK"], "SK": items[0]["SK"]})
    return True


def anonymize_user_content(user_id: str):
    """Anonymize all content by this user: comments, guestbook, testimonials, ratings, quiz scores."""
    table = get_table()

    # Anonymize comments
    comments = table.scan(
        FilterExpression=Attr("SK").begins_with("COMMENT#") & Attr("user_id").eq(user_id),
    ).get("Items", [])
    for item in comments:
        table.update_item(
            Key={"PK": item["PK"], "SK": item["SK"]},
            UpdateExpression="SET #n = :n, #i = :i REMOVE user_id",
            ExpressionAttributeNames={"#n": "name", "#i": "identity"},
            ExpressionAttributeValues={":n": "Deleted User", ":i": None},
        )

    # Anonymize guestbook entries
    guestbook = table.scan(
        FilterExpression=Attr("PK").eq("GUESTBOOK") & Attr("user_id").eq(user_id),
    ).get("Items", [])
    for item in guestbook:
        table.update_item(
            Key={"PK": item["PK"], "SK": item["SK"]},
            UpdateExpression="SET #n = :n REMOVE identity, user_id",
            ExpressionAttributeNames={"#n": "name"},
            ExpressionAttributeValues={":n": "Deleted User"},
        )

    # Anonymize testimonials
    testimonials = table.scan(
        FilterExpression=Attr("PK").eq("TESTIMONIALS") & Attr("user_id").eq(user_id),
    ).get("Items", [])
    for item in testimonials:
        table.update_item(
            Key={"PK": item["PK"], "SK": item["SK"]},
            UpdateExpression="SET author = :a REMOVE user_id",
            ExpressionAttributeValues={":a": "Deleted User"},
        )

    # Anonymize ratings (keep data, clear user_id)
    ratings = table.scan(
        FilterExpression=Attr("SK").begins_with("RATING#") & Attr("user_id").eq(user_id),
    ).get("Items", [])
    for item in ratings:
        table.update_item(
            Key={"PK": item["PK"], "SK": item["SK"]},
            UpdateExpression="SET user_id = :d",
            ExpressionAttributeValues={":d": "DELETED"},
        )

    # Anonymize quiz scores (keep scores, clear user_id)
    scores = table.query(
        KeyConditionExpression=Key("PK").eq(f"USER#{user_id}") & Key("SK").begins_with("QUIZ_SCORE#"),
    ).get("Items", [])
    for item in scores:
        table.update_item(
            Key={"PK": item["PK"], "SK": item["SK"]},
            UpdateExpression="SET user_id = :d",
            ExpressionAttributeValues={":d": "DELETED"},
        )


def delete_user_oauth_links(user_id: str):
    """Delete all OAuth link records for this user."""
    table = get_table()
    links = table.scan(
        FilterExpression=Attr("SK").eq("LINK") & Attr("user_id").eq(user_id),
    ).get("Items", [])
    for item in links:
        table.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})


def delete_user_sessions(user_id: str):
    """Delete all refresh tokens for this user."""
    table = get_table()
    sessions = table.scan(
        FilterExpression=Attr("SK").eq("SESSION") & Attr("user_id").eq(user_id),
    ).get("Items", [])
    for item in sessions:
        table.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})


def delete_user_guestbook_entry(user_id: str, entry_id: str) -> bool:
    """Find and delete a guestbook entry owned by this user."""
    table = get_table()
    resp = table.scan(
        FilterExpression=Attr("PK").eq("GUESTBOOK") & Attr("entry_id").eq(entry_id) & Attr("user_id").eq(user_id),
    )
    items = resp.get("Items", [])
    if not items:
        return False
    item = items[0]
    table.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})
    return True
