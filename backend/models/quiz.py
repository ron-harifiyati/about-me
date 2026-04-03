import uuid
import time
from db import get_table
from boto3.dynamodb.conditions import Key


def list_questions() -> list:
    table = get_table()
    resp = table.query(
        KeyConditionExpression=Key("PK").eq("QUIZ") & Key("SK").begins_with("QUESTION#"),
    )
    return resp.get("Items", [])


def create_question(fields: dict) -> dict:
    table = get_table()
    qid = str(uuid.uuid4())
    item = {"PK": "QUIZ", "SK": f"QUESTION#{qid}", "question_id": qid, **fields}
    table.put_item(Item=item)
    return item


def update_question(question_id: str, fields: dict) -> dict | None:
    table = get_table()
    resp = table.get_item(Key={"PK": "QUIZ", "SK": f"QUESTION#{question_id}"})
    item = resp.get("Item")
    if not item:
        return None
    updated = {**item, **fields}
    table.put_item(Item=updated)
    return updated


def delete_question(question_id: str) -> bool:
    table = get_table()
    resp = table.get_item(Key={"PK": "QUIZ", "SK": f"QUESTION#{question_id}"})
    if not resp.get("Item"):
        return False
    table.delete_item(Key={"PK": "QUIZ", "SK": f"QUESTION#{question_id}"})
    return True


def save_score(user_id: str, score: int, total: int) -> dict:
    table = get_table()
    attempt_id = str(uuid.uuid4())
    ts = int(time.time())
    padded_score = str(score).zfill(6)
    item = {
        "PK": f"USER#{user_id}",
        "SK": f"QUIZ_SCORE#{attempt_id}",
        "GSI3PK": "QUIZ_LEADERBOARD",
        "GSI3SK": f"SCORE#{padded_score}",
        "user_id": user_id,
        "score": score,
        "total": total,
        "attempt_id": attempt_id,
        "created_at": ts,
    }
    table.put_item(Item=item)
    return item


def get_leaderboard(limit: int = 20) -> list:
    table = get_table()
    resp = table.query(
        IndexName="GSI3",
        KeyConditionExpression=Key("GSI3PK").eq("QUIZ_LEADERBOARD"),
        ScanIndexForward=False,
        Limit=limit,
    )
    items = resp.get("Items", [])
    for item in items:
        item.pop("PK", None)
        item.pop("SK", None)
        item.pop("GSI3PK", None)
        item.pop("GSI3SK", None)
    return items
