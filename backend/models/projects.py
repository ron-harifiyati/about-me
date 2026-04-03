import uuid
import time
from db import get_table
from boto3.dynamodb.conditions import Attr


def list_projects() -> list:
    table = get_table()
    resp = table.scan(
        FilterExpression=Attr("PK").begins_with("PROJECT#") & Attr("SK").eq("META")
    )
    items = resp.get("Items", [])
    for item in items:
        item.pop("PK", None)
        item.pop("SK", None)
    return items


def get_project(project_id: str) -> dict | None:
    table = get_table()
    resp = table.get_item(Key={"PK": f"PROJECT#{project_id}", "SK": "META"})
    item = resp.get("Item")
    if item:
        item.pop("PK", None)
        item.pop("SK", None)
    return item


def create_project(fields: dict) -> dict:
    table = get_table()
    project_id = str(uuid.uuid4())
    item = {
        "PK": f"PROJECT#{project_id}",
        "SK": "META",
        "id": project_id,
        "created_at": int(time.time()),
        **fields,
    }
    table.put_item(Item=item)
    result = dict(item)
    result.pop("PK", None)
    result.pop("SK", None)
    return result


def update_project(project_id: str, fields: dict) -> dict | None:
    existing = get_project(project_id)
    if not existing:
        return None
    table = get_table()
    updated = {**existing, **fields, "id": project_id}
    table.put_item(Item={"PK": f"PROJECT#{project_id}", "SK": "META", **updated})
    return updated


def delete_project(project_id: str) -> bool:
    existing = get_project(project_id)
    if not existing:
        return False
    table = get_table()
    table.delete_item(Key={"PK": f"PROJECT#{project_id}", "SK": "META"})
    return True
