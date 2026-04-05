import json
from tests.conftest import make_event


def test_get_visitor_locations_returns_list(ddb_table):
    from router import route
    resp = route(make_event("GET", "/stats/visitors"))
    assert resp["statusCode"] == 200
    assert isinstance(json.loads(resp["body"])["data"], list)


def test_get_analytics_requires_admin(ddb_table):
    from router import route
    resp = route(make_event("GET", "/stats/analytics"))
    assert resp["statusCode"] == 401


def test_get_analytics_returns_breakdown(ddb_table):
    from router import route
    from auth import make_jwt
    from models.visits import record_pageview
    record_pageview("1.2.3.4", "projects")
    record_pageview("1.2.3.4", "projects")
    record_pageview("1.2.3.4", "about")

    token = make_jwt("admin-1", "admin")
    resp = route(make_event("GET", "/stats/analytics", headers={"authorization": f"Bearer {token}"}))
    assert resp["statusCode"] == 200
    data = json.loads(resp["body"])["data"]
    assert data["total_pageviews"] == 3
    assert data["by_page"]["projects"] == 2


def test_get_pageviews_returns_counts(ddb_table):
    from router import route
    from models.visits import record_pageview
    record_pageview("1.2.3.4", "home")
    record_pageview("1.2.3.4", "about")
    record_pageview("5.6.7.8", "home")
    resp = route(make_event("GET", "/stats/pageviews"))
    assert resp["statusCode"] == 200
    data = json.loads(resp["body"])["data"]
    assert data["total"] == 3
    assert data["by_page"]["home"] == 2
    assert data["by_page"]["about"] == 1


def test_get_pageviews_empty(ddb_table):
    from router import route
    resp = route(make_event("GET", "/stats/pageviews"))
    assert resp["statusCode"] == 200
    data = json.loads(resp["body"])["data"]
    assert data["total"] == 0
    assert data["by_page"] == {}
