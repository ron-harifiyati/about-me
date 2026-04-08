import uuid
import time
import hashlib
import secrets
from db import get_table
from boto3.dynamodb.conditions import Key, Attr


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}:{h}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, h = stored.split(":", 1)
        return hashlib.sha256(f"{salt}{password}".encode()).hexdigest() == h
    except ValueError:
        return False


_INTERNAL_KEYS = ("PK", "SK", "GSI1PK", "GSI1SK", "GSI2PK", "GSI2SK", "GSI3PK", "GSI3SK", "password_hash")


def _strip_internal(item: dict) -> dict:
    for key in _INTERNAL_KEYS:
        item.pop(key, None)
    return item


def get_user_by_id(user_id: str) -> dict | None:
    table = get_table()
    resp = table.get_item(Key={"PK": f"USER#{user_id}", "SK": "PROFILE"})
    item = resp.get("Item")
    if item:
        _strip_internal(item)
    return item


def get_user_by_email(email: str) -> dict | None:
    table = get_table()
    resp = table.query(
        IndexName="GSI1",
        KeyConditionExpression=Key("GSI1PK").eq(f"EMAIL#{email}") & Key("GSI1SK").eq("USER"),
    )
    items = resp.get("Items", [])
    return items[0] if items else None


def user_has_password(user_id: str) -> bool:
    """Check if user has a password set (without exposing the hash)."""
    table = get_table()
    resp = table.get_item(Key={"PK": f"USER#{user_id}", "SK": "PROFILE"})
    item = resp.get("Item")
    if not item:
        return False
    return bool(item.get("password_hash"))


def create_user(email: str, name: str, identity: str, password: str | None = None) -> dict:
    table = get_table()
    user_id = str(uuid.uuid4())
    item = {
        "PK": f"USER#{user_id}",
        "SK": "PROFILE",
        "GSI1PK": f"EMAIL#{email}",
        "GSI1SK": "USER",
        "user_id": user_id,
        "email": email,
        "name": name,
        "identity": identity,
        "role": "user",
        "email_verified": False,
        "theme": "light",
        "created_at": int(time.time()),
    }
    if password:
        item["password_hash"] = _hash_password(password)
    table.put_item(Item=item)
    result = dict(item)
    _strip_internal(result)
    return result


def verify_user_password(email: str, password: str) -> dict | None:
    table = get_table()
    resp = table.query(
        IndexName="GSI1",
        KeyConditionExpression=Key("GSI1PK").eq(f"EMAIL#{email}") & Key("GSI1SK").eq("USER"),
    )
    items = resp.get("Items", [])
    if not items:
        return None
    user = items[0]
    if not _verify_password(password, user.get("password_hash", "")):
        return None
    result = dict(user)
    _strip_internal(result)
    return result


def mark_email_verified(user_id: str):
    table = get_table()
    table.update_item(
        Key={"PK": f"USER#{user_id}", "SK": "PROFILE"},
        UpdateExpression="SET email_verified = :v",
        ExpressionAttributeValues={":v": True},
    )


def update_user_profile(user_id: str, fields: dict) -> dict | None:
    allowed = {"name", "identity", "theme"}
    safe_fields = {k: v for k, v in fields.items() if k in allowed}
    if not safe_fields:
        return get_user_by_id(user_id)
    table = get_table()
    set_expr = ", ".join(f"#{k} = :{k}" for k in safe_fields)
    attr_names = {f"#{k}": k for k in safe_fields}
    attr_values = {f":{k}": v for k, v in safe_fields.items()}
    table.update_item(
        Key={"PK": f"USER#{user_id}", "SK": "PROFILE"},
        UpdateExpression=f"SET {set_expr}",
        ExpressionAttributeNames=attr_names,
        ExpressionAttributeValues=attr_values,
    )
    return get_user_by_id(user_id)


def create_email_verify_token(user_id: str) -> str:
    table = get_table()
    token = secrets.token_urlsafe(32)
    ttl = int(time.time()) + 24 * 3600
    table.put_item(Item={
        "PK": f"VERIFY#{token}",
        "SK": "TOKEN",
        "user_id": user_id,
        "ttl": ttl,
    })
    return token


def consume_email_verify_token(token: str) -> str | None:
    """Returns user_id if token is valid, deletes it."""
    table = get_table()
    resp = table.get_item(Key={"PK": f"VERIFY#{token}", "SK": "TOKEN"})
    item = resp.get("Item")
    if not item:
        return None
    table.delete_item(Key={"PK": f"VERIFY#{token}", "SK": "TOKEN"})
    return item["user_id"]


def create_refresh_token(user_id: str, role: str) -> str:
    table = get_table()
    token = secrets.token_urlsafe(48)
    ttl = int(time.time()) + 7 * 24 * 3600
    table.put_item(Item={
        "PK": f"SESSION#{token}",
        "SK": "SESSION",
        "user_id": user_id,
        "role": role,
        "ttl": ttl,
    })
    return token


def consume_refresh_token(token: str) -> dict | None:
    """Returns {user_id, role} if valid, deletes it (single-use rotation)."""
    table = get_table()
    resp = table.get_item(Key={"PK": f"SESSION#{token}", "SK": "SESSION"})
    item = resp.get("Item")
    if not item:
        return None
    table.delete_item(Key={"PK": f"SESSION#{token}", "SK": "SESSION"})
    return {"user_id": item["user_id"], "role": item["role"]}


def delete_refresh_token(token: str):
    table = get_table()
    table.delete_item(Key={"PK": f"SESSION#{token}", "SK": "SESSION"})


def get_or_create_oauth_user(provider: str, provider_id: str, email: str, name: str) -> dict:
    """
    Link table approach: if OAUTH#<provider>#<provider_id> exists, return that user.
    If not, check if a user with the same email exists (account linking).
    If not, create a new user. Either way, upsert the OAuth link record.
    """
    table = get_table()

    # Check existing OAuth link
    link = table.get_item(Key={"PK": f"OAUTH#{provider}#{provider_id}", "SK": "LINK"}).get("Item")
    if link:
        return get_user_by_id(link["user_id"])

    # Check by email (account linking)
    existing = get_user_by_email(email)
    if existing:
        user_id = existing["user_id"]
    else:
        # Create new user (no password, email pre-verified via OAuth)
        user = create_user(email, name, "Other")
        mark_email_verified(user["user_id"])
        user_id = user["user_id"]

    # Store OAuth link
    table.put_item(Item={
        "PK": f"OAUTH#{provider}#{provider_id}",
        "SK": "LINK",
        "user_id": user_id,
        "provider": provider,
        "provider_id": provider_id,
    })
    return get_user_by_id(user_id)


def list_all_users() -> list:
    table = get_table()
    resp = table.scan(
        FilterExpression=Attr("SK").eq("PROFILE") & Attr("PK").begins_with("USER#")
    )
    items = resp.get("Items", [])
    for item in items:
        _strip_internal(item)
    return items


def set_user_status(user_id: str, status: str):
    """status: 'active' | 'suspended' | 'banned'"""
    table = get_table()
    table.update_item(
        Key={"PK": f"USER#{user_id}", "SK": "PROFILE"},
        UpdateExpression="SET #s = :s",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": status},
    )


def delete_user(user_id: str):
    table = get_table()
    table.delete_item(Key={"PK": f"USER#{user_id}", "SK": "PROFILE"})


def create_password_reset_token(user_id: str) -> str:
    table = get_table()
    token = secrets.token_urlsafe(32)
    ttl = int(time.time()) + 3600
    table.put_item(Item={
        "PK": f"RESET#{token}",
        "SK": "TOKEN",
        "user_id": user_id,
        "ttl": ttl,
    })
    return token


def consume_password_reset_token(token: str) -> str | None:
    """Returns user_id if token is valid, deletes it (single-use)."""
    table = get_table()
    resp = table.get_item(Key={"PK": f"RESET#{token}", "SK": "TOKEN"})
    item = resp.get("Item")
    if not item:
        return None
    table.delete_item(Key={"PK": f"RESET#{token}", "SK": "TOKEN"})
    return item["user_id"]


def update_user_password(user_id: str, new_password: str):
    table = get_table()
    table.update_item(
        Key={"PK": f"USER#{user_id}", "SK": "PROFILE"},
        UpdateExpression="SET password_hash = :h",
        ExpressionAttributeValues={":h": _hash_password(new_password)},
    )
