import uuid
import time
import requests
from db import get_table
from boto3.dynamodb.conditions import Key


def upsert_visitor(ip: str, page: str):
    """
    Upsert a unique visitor record keyed by IP.
    Same IP always writes to the same item — natural deduplication for the map.
    Geo lookup is best-effort; silently skips on failure.
    """
    try:
        geo = _lookup_ip(ip)
    except Exception:
        geo = {}

    table = get_table()
    now = int(time.time())
    table.update_item(
        Key={"PK": "VISITORS", "SK": f"VISITOR#{ip}"},
        UpdateExpression=(
            "SET last_seen = :now, country = :country, city = :city, "
            "lat = :lat, lon = :lon, "
            "first_seen = if_not_exists(first_seen, :now)"
        ),
        ExpressionAttributeValues={
            ":now": now,
            ":country": geo.get("country") or "",
            ":city": geo.get("city") or "",
            ":lat": str(geo.get("lat", "")),
            ":lon": str(geo.get("lon", "")),
        },
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
    if resp.status_code == 200 and resp.json().get("status") == "success":
        return resp.json()
    return {}


def get_visitor_locations() -> list:
    """Public — returns lat/lon/country/city for unique visitors only (no IP data)."""
    table = get_table()
    resp = table.query(
        KeyConditionExpression=Key("PK").eq("VISITORS") & Key("SK").begins_with("VISITOR#"),
    )
    return [
        {
            "lat": item.get("lat"),
            "lon": item.get("lon"),
            "country": item.get("country"),
            "city": item.get("city"),
        }
        for item in resp.get("Items", [])
        if item.get("lat") and item.get("lon")
    ]


def get_pageviews() -> dict:
    """Public — returns page view counts by page name."""
    table = get_table()
    resp = table.query(
        KeyConditionExpression=Key("PK").eq("PAGEVIEWS") & Key("SK").begins_with("VIEW#"),
    )
    counts: dict = {}
    for item in resp.get("Items", []):
        page = item.get("page", "unknown")
        counts[page] = counts.get(page, 0) + 1
    return {"total": sum(counts.values()), "by_page": counts}


def get_analytics() -> dict:
    """Admin only — unique visitor count + full page view breakdown."""
    table = get_table()
    visitors_resp = table.query(
        KeyConditionExpression=Key("PK").eq("VISITORS") & Key("SK").begins_with("VISITOR#"),
        Select="COUNT",
    )
    pageviews_data = get_pageviews()
    return {
        "unique_visitors": visitors_resp.get("Count", 0),
        "total_pageviews": pageviews_data["total"],
        "by_page": pageviews_data["by_page"],
        "locations": get_visitor_locations(),
    }
