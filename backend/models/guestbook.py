import uuid
import time
from db import get_table
from boto3.dynamodb.conditions import Key


def list_entries() -> list:
    table = get_table()
    resp = table.query(
        KeyConditionExpression=Key("PK").eq("GUESTBOOK") & Key("SK").begins_with("ENTRY#"),
    )
    items = resp.get("Items", [])
    for item in items:
        item.pop("PK", None)
    return sorted(items, key=lambda x: x.get("created_at", 0), reverse=True)


def delete_entry_by_sk(sk: str):
    table = get_table()
    table.delete_item(Key={"PK": "GUESTBOOK", "SK": sk})


def create_entry(name: str, message: str, is_authenticated: bool,
                 identity: str | None = None, user_id: str | None = None) -> dict:
    table = get_table()
    entry_id = str(uuid.uuid4())
    ts = int(time.time())
    item = {
        "PK": "GUESTBOOK",
        "SK": f"ENTRY#{ts}#{entry_id}",
        "entry_id": entry_id,
        "name": name,
        "message": message,
        "is_authenticated": is_authenticated,
        "created_at": ts,
    }
    if identity:
        item["identity"] = identity
    if user_id:
        item["user_id"] = user_id
    table.put_item(Item=item)
    result = dict(item)
    result.pop("PK", None)
    return result
