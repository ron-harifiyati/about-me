import uuid
import time
from db import get_table
from boto3.dynamodb.conditions import Key


def list_comments(entity_pk: str) -> list:
    """entity_pk: 'PROJECT#<id>' or 'COURSE#<id>'"""
    table = get_table()
    resp = table.query(
        KeyConditionExpression=Key("PK").eq(entity_pk) & Key("SK").begins_with("COMMENT#"),
    )
    items = resp.get("Items", [])
    for item in items:
        item.pop("PK", None)
    return sorted(items, key=lambda x: x.get("created_at", 0))


def create_comment(entity_pk: str, user_id: str, name: str, identity: str, body_text: str) -> dict:
    table = get_table()
    comment_id = str(uuid.uuid4())
    ts = int(time.time())
    item = {
        "PK": entity_pk,
        "SK": f"COMMENT#{ts}#{comment_id}",
        "comment_id": comment_id,
        "user_id": user_id,
        "name": name,
        "identity": identity,
        "body": body_text,
        "created_at": ts,
    }
    table.put_item(Item=item)
    result = dict(item)
    result.pop("PK", None)
    return result


def delete_comment_by_sk(entity_pk: str, sk: str):
    table = get_table()
    table.delete_item(Key={"PK": entity_pk, "SK": sk})


def find_comment_pk_sk(comment_id: str, entity_pk: str) -> tuple:
    """Scan for comment_id within an entity — used by admin delete."""
    table = get_table()
    resp = table.query(
        KeyConditionExpression=Key("PK").eq(entity_pk) & Key("SK").begins_with("COMMENT#"),
        FilterExpression="comment_id = :cid",
        ExpressionAttributeValues={":cid": comment_id},
    )
    items = resp.get("Items", [])
    if items:
        return entity_pk, items[0]["SK"]
    return None, None


def get_ratings_summary(entity_pk: str) -> dict:
    table = get_table()
    resp = table.query(
        KeyConditionExpression=Key("PK").eq(entity_pk) & Key("SK").begins_with("RATING#"),
    )
    items = resp.get("Items", [])
    if not items:
        return {"average": None, "count": 0}
    stars = [float(item["stars"]) for item in items]
    return {"average": round(sum(stars) / len(stars), 1), "count": len(stars)}


def submit_rating(entity_pk: str, user_id: str, stars: int) -> dict:
    table = get_table()
    table.put_item(Item={
        "PK": entity_pk,
        "SK": f"RATING#{user_id}",
        "user_id": user_id,
        "stars": stars,
        "created_at": int(time.time()),
    })
    return get_ratings_summary(entity_pk)
