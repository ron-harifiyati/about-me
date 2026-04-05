import uuid
import time
import requests
from db import get_table
from boto3.dynamodb.conditions import Key


def record_visit(ip: str, page: str, user: dict | None = None):
    """
    Called to record a visitor. Geo lookup is best-effort — silently skips on failure.
    """
    try:
        geo = _lookup_ip(ip)
    except Exception:
        geo = {}

    table = get_table()
    ts = int(time.time())
    visit_id = str(uuid.uuid4())
    item = {
        "PK": "VISITS",
        "SK": f"VISIT#{ts}#{visit_id}",
        "visit_id": visit_id,
        "ip": ip,
        "page": page,
        "country": geo.get("country"),
        "city": geo.get("city"),
        "lat": str(geo.get("lat", "")),
        "lon": str(geo.get("lon", "")),
        "created_at": ts,
    }
    if user:
        item["user_id"] = user.get("sub")
        item["identity"] = user.get("identity")
    table.put_item(Item=item)


def _lookup_ip(ip: str) -> dict:
    if ip in ("127.0.0.1", "::1", "testclient"):
        return {}
    resp = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,city,lat,lon", timeout=3)
    if resp.status_code == 200 and resp.json().get("status") == "success":
        return resp.json()
    return {}


def get_visitor_locations() -> list:
    """Public — returns lat/lon/country/city only (no IP or user data)."""
    table = get_table()
    resp = table.query(
        KeyConditionExpression=Key("PK").eq("VISITS") & Key("SK").begins_with("VISIT#"),
        Limit=500,
    )
    items = resp.get("Items", [])
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


def get_analytics() -> dict:
    """Admin only — full breakdown."""
    table = get_table()
    resp = table.query(
        KeyConditionExpression=Key("PK").eq("VISITS") & Key("SK").begins_with("VISIT#"),
    )
    items = resp.get("Items", [])

    page_counts: dict = {}
    identity_counts: dict = {}
    for item in items:
        page = item.get("page", "unknown")
        page_counts[page] = page_counts.get(page, 0) + 1
        if item.get("identity"):
            identity = item["identity"]
            identity_counts[identity] = identity_counts.get(identity, 0) + 1

    return {
        "total_visits": len(items),
        "by_page": page_counts,
        "by_identity": identity_counts,
        "locations": get_visitor_locations(),
    }
