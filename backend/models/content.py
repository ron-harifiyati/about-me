from db import get_table


def get_content(sk: str) -> dict | None:
    table = get_table()
    resp = table.get_item(Key={"PK": "CONTENT", "SK": sk})
    item = resp.get("Item")
    if item:
        item.pop("PK", None)
        item.pop("SK", None)
    return item


def update_content(sk: str, fields: dict) -> dict:
    table = get_table()
    table.put_item(Item={"PK": "CONTENT", "SK": sk, **fields})
    return fields
