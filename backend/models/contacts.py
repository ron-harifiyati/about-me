import uuid
import time
from db import get_table
from boto3.dynamodb.conditions import Key

RATE_LIMIT = 5  # submissions per hour per IP


def is_rate_limited(ip: str) -> bool:
    table = get_table()
    resp = table.get_item(Key={"PK": f"RATELIMIT#{ip}", "SK": "CONTACT"})
    item = resp.get("Item")
    if not item:
        return False
    return int(item.get("count", 0)) >= RATE_LIMIT


def increment_rate_limit(ip: str):
    table = get_table()
    ttl = int(time.time()) + 3600  # 1 hour TTL
    table.update_item(
        Key={"PK": f"RATELIMIT#{ip}", "SK": "CONTACT"},
        UpdateExpression="SET #c = if_not_exists(#c, :zero) + :one, #t = :ttl",
        ExpressionAttributeNames={"#c": "count", "#t": "ttl"},
        ExpressionAttributeValues={":zero": 0, ":one": 1, ":ttl": ttl},
    )


def save_contact(name: str, email: str, message: str) -> dict:
    table = get_table()
    cid = str(uuid.uuid4())
    ts = int(time.time())
    item = {
        "PK": "CONTACTS",
        "SK": f"CONTACT#{ts}#{cid}",
        "contact_id": cid,
        "name": name,
        "email": email,
        "message": message,
        "created_at": ts,
    }
    table.put_item(Item=item)
    result = dict(item)
    result.pop("PK", None)
    result.pop("SK", None)
    return result


def list_contacts() -> list:
    table = get_table()
    resp = table.query(
        KeyConditionExpression=Key("PK").eq("CONTACTS") & Key("SK").begins_with("CONTACT#"),
    )
    items = resp.get("Items", [])
    for item in items:
        item.pop("PK", None)
    return sorted(items, key=lambda x: x.get("created_at", 0), reverse=True)


def delete_contact_by_sk(sk: str):
    table = get_table()
    table.delete_item(Key={"PK": "CONTACTS", "SK": sk})
