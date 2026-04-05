import uuid
import time
import requests
from db import get_table
from boto3.dynamodb.conditions import Key


def upsert_visitor(ip: str):
    """
    Upsert a unique visitor record keyed by IP.
    Same IP always writes to the same item — natural deduplication for the map.
    Geo lookup is best-effort; silently skips on failure.
    Geo fields are only updated when the lookup returns data, preserving any
    previously stored values when a lookup fails.
    """
    try:
        geo = _lookup_ip(ip)
    except Exception:
        geo = {}

    table = get_table()
    now = int(time.time())

    update_expr = "SET last_seen = :now, first_seen = if_not_exists(first_seen, :now)"
    expr_values = {":now": now}

    if geo:
        update_expr += ", country = :country, city = :city, lat = :lat, lon = :lon"
        expr_values.update({
            ":country": geo.get("country") or "",
            ":city": geo.get("city") or "",
            ":lat": str(geo.get("lat", "")),
            ":lon": str(geo.get("lon", "")),
        })

    table.update_item(
        Key={"PK": "VISITORS", "SK": f"VISITOR#{ip}"},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=expr_values,
    )


def record_pageview(ip: str, page: str):
    """One record per page navigation — used for page view analytics."""
    table = get_table()
    ts = int(time.time())
    table.put_item(Item={
        "PK": "PAGEVIEWS",
        "SK": f"VIEW#{ts}#{str(uuid.uuid4())}",
        "page": page,
        "ip": ip,
        "created_at": ts,
    })


def _lookup_ip(ip: str) -> dict:
    if ip in ("127.0.0.1", "::1", "testclient"):
        return {}
    resp = requests.get(
        f"http://ip-api.com/json/{ip}?fields=status,country,city,lat,lon",
        timeout=3,
    )
    if resp.status_code != 200:
        return {}
    data = resp.json()
    return data if data.get("status") == "success" else {}


def get_visitor_locations() -> list:
    """Public — returns lat/lon/country/city for unique visitors only (no IP data)."""
    table = get_table()
    kwargs = {"KeyConditionExpression": Key("PK").eq("VISITORS") & Key("SK").begins_with("VISITOR#")}
    items = []
    while True:
        resp = table.query(**kwargs)
        items.extend(resp.get("Items", []))
        if "LastEvaluatedKey" not in resp:
            break
        kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
    return [
        {
            "lat": item.get("lat"),
            "lon": item.get("lon"),
            "country": item.get("country"),
            "city": item.get("city"),
        }
        for item in items
        if item.get("lat") and item.get("lon")
    ]


def get_pageviews() -> dict:
    """Public — returns page view counts by page name."""
    table = get_table()
    kwargs = {"KeyConditionExpression": Key("PK").eq("PAGEVIEWS") & Key("SK").begins_with("VIEW#")}
    counts: dict = {}
    while True:
        resp = table.query(**kwargs)
        for item in resp.get("Items", []):
            page = item.get("page", "unknown")
            counts[page] = counts.get(page, 0) + 1
        if "LastEvaluatedKey" not in resp:
            break
        kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
    return {"total": sum(counts.values()), "by_page": counts}


def get_analytics() -> dict:
    """Admin only — unique visitor count + full page view breakdown."""
    table = get_table()
    kwargs = {
        "KeyConditionExpression": Key("PK").eq("VISITORS") & Key("SK").begins_with("VISITOR#"),
        "Select": "COUNT",
    }
    unique_visitors = 0
    while True:
        resp = table.query(**kwargs)
        unique_visitors += resp.get("Count", 0)
        if "LastEvaluatedKey" not in resp:
            break
        kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
    pageviews_data = get_pageviews()
    return {
        "unique_visitors": unique_visitors,
        "total_pageviews": pageviews_data["total"],
        "by_page": pageviews_data["by_page"],
        "locations": get_visitor_locations(),
    }
