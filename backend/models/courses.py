import uuid
import time
from db import get_table
from boto3.dynamodb.conditions import Attr


def list_courses() -> list:
    table = get_table()
    resp = table.scan(
        FilterExpression=Attr("PK").begins_with("COURSE#") & Attr("SK").eq("META")
    )
    items = resp.get("Items", [])
    for item in items:
        item.pop("PK", None)
        item.pop("SK", None)
    return items


def get_course(course_id: str) -> dict | None:
    table = get_table()
    resp = table.get_item(Key={"PK": f"COURSE#{course_id}", "SK": "META"})
    item = resp.get("Item")
    if item:
        item.pop("PK", None)
        item.pop("SK", None)
    return item


def create_course(fields: dict) -> dict:
    table = get_table()
    course_id = str(uuid.uuid4())
    item = {
        "PK": f"COURSE#{course_id}",
        "SK": "META",
        "id": course_id,
        "created_at": int(time.time()),
        **fields,
    }
    table.put_item(Item=item)
    result = dict(item)
    result.pop("PK", None)
    result.pop("SK", None)
    return result


def update_course(course_id: str, fields: dict) -> dict | None:
    existing = get_course(course_id)
    if not existing:
        return None
    table = get_table()
    updated = {**existing, **fields, "id": course_id}
    table.put_item(Item={"PK": f"COURSE#{course_id}", "SK": "META", **updated})
    return updated


def delete_course(course_id: str) -> bool:
    existing = get_course(course_id)
    if not existing:
        return False
    table = get_table()
    table.delete_item(Key={"PK": f"COURSE#{course_id}", "SK": "META"})
    return True
