import uuid
import time
from db import get_table
from boto3.dynamodb.conditions import Key


def create_testimonial(body_text: str, author: str, identity: str, anonymous: bool, user_id: str | None = None) -> dict:
    table = get_table()
    tid = str(uuid.uuid4())
    ts = int(time.time())
    display_author = "Anonymous" if anonymous else author
    item = {
        "PK": "TESTIMONIALS",
        "SK": f"TESTIMONIAL#{tid}",
        "GSI2PK": "STATUS#pending",
        "GSI2SK": f"TESTIMONIAL#{ts}",
        "testimonial_id": tid,
        "body": body_text,
        "author": display_author,
        "identity": identity,
        "status": "pending",
        "created_at": ts,
    }
    if user_id:
        item["user_id"] = user_id
    table.put_item(Item=item)
    result = dict(item)
    result.pop("PK", None)
    result.pop("SK", None)
    return result


def list_approved(identity_filter: str | None = None) -> list:
    table = get_table()
    resp = table.query(
        IndexName="GSI2",
        KeyConditionExpression=Key("GSI2PK").eq("STATUS#approved"),
        ScanIndexForward=False,
    )
    items = resp.get("Items", [])
    if identity_filter:
        items = [i for i in items if i.get("identity") == identity_filter]
    for item in items:
        item.pop("PK", None)
        item.pop("GSI2PK", None)
        item.pop("GSI2SK", None)
    return items


def delete_testimonial(testimonial_id: str):
    table = get_table()
    table.delete_item(Key={"PK": "TESTIMONIALS", "SK": f"TESTIMONIAL#{testimonial_id}"})


def list_pending() -> list:
    table = get_table()
    resp = table.query(
        IndexName="GSI2",
        KeyConditionExpression=Key("GSI2PK").eq("STATUS#pending"),
    )
    items = resp.get("Items", [])
    for item in items:
        item.pop("PK", None)
        item.pop("SK", None)
    return items


def approve_testimonial(testimonial_id: str) -> bool:
    return _set_status(testimonial_id, "approved")


def reject_testimonial(testimonial_id: str) -> bool:
    return _set_status(testimonial_id, "rejected")


def _set_status(testimonial_id: str, status: str) -> bool:
    table = get_table()
    ts = int(time.time())
    try:
        table.update_item(
            Key={"PK": "TESTIMONIALS", "SK": f"TESTIMONIAL#{testimonial_id}"},
            UpdateExpression="SET #s = :s, GSI2PK = :gpk, GSI2SK = :gsk",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":s": status,
                ":gpk": f"STATUS#{status}",
                ":gsk": f"TESTIMONIAL#{ts}",
            },
        )
        return True
    except Exception:
        return False
