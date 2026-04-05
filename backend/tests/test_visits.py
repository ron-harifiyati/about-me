import json
import pytest
from tests.conftest import make_event


def test_upsert_visitor_creates_record(ddb_table, monkeypatch):
    monkeypatch.setattr("models.visits._lookup_ip", lambda ip: {
        "country": "US", "city": "New York", "lat": 40.7, "lon": -74.0
    })
    from models.visits import upsert_visitor, get_visitor_locations
    upsert_visitor("1.2.3.4", "home")
    locs = get_visitor_locations()
    assert len(locs) == 1
    assert locs[0]["country"] == "US"
    assert locs[0]["city"] == "New York"


def test_upsert_visitor_deduplicates_by_ip(ddb_table, monkeypatch):
    monkeypatch.setattr("models.visits._lookup_ip", lambda ip: {
        "country": "US", "city": "New York", "lat": 40.7, "lon": -74.0
    })
    from models.visits import upsert_visitor, get_visitor_locations
    upsert_visitor("1.2.3.4", "home")
    upsert_visitor("1.2.3.4", "projects")
    upsert_visitor("1.2.3.4", "about")
    locs = get_visitor_locations()
    assert len(locs) == 1


def test_upsert_visitor_different_ips(ddb_table, monkeypatch):
    monkeypatch.setattr("models.visits._lookup_ip", lambda ip: {
        "country": "US", "city": "NYC", "lat": 40.7, "lon": -74.0
    })
    from models.visits import upsert_visitor, get_visitor_locations
    upsert_visitor("1.2.3.4", "home")
    upsert_visitor("5.6.7.8", "home")
    locs = get_visitor_locations()
    assert len(locs) == 2


def test_record_pageview_and_get_pageviews(ddb_table):
    from models.visits import record_pageview, get_pageviews
    record_pageview("1.2.3.4", "home")
    record_pageview("1.2.3.4", "projects")
    record_pageview("5.6.7.8", "home")
    data = get_pageviews()
    assert data["total"] == 3
    assert data["by_page"]["home"] == 2
    assert data["by_page"]["projects"] == 1


def test_get_pageviews_empty(ddb_table):
    from models.visits import get_pageviews
    data = get_pageviews()
    assert data["total"] == 0
    assert data["by_page"] == {}
