# Visitor Analytics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace per-API-call visit recording with frontend-driven page navigation tracking, deduplicating visitors by IP on the map while tracking full page view counts in a separate analytics section.

**Architecture:** The frontend fires `POST /visits` once per `handleRoute()` call with the page name. The backend upserts a unique visitor record (keyed by IP, for the map) and writes a separate page view record (one per navigation, for analytics). The stats page fetches both and displays unique visitor dots on the map plus a page breakdown table underneath.

**Tech Stack:** Python (backend), DynamoDB single-table, Alpine.js + Leaflet (frontend)

---

## File Map

| File | Change |
|------|--------|
| `backend/models/visits.py` | Replace `record_visit` with `upsert_visitor` + `record_pageview` + `get_pageviews`; update `get_visitor_locations` + `get_analytics` |
| `backend/routes/visits.py` | **Create** — `POST /visits` handler |
| `backend/routes/stats.py` | Add public `GET /stats/pageviews` handler |
| `backend/router.py` | Remove old `record_visit` middleware block; add `POST /visits` + `GET /stats/pageviews` routes |
| `backend/tests/test_visits.py` | **Create** — tests for new model functions + POST /visits route |
| `backend/tests/test_stats.py` | Update analytics test to use new model functions |
| `frontend/assets/js/app.js` | Fire `POST /visits` in `handleRoute()` |
| `frontend/assets/js/pages/stats.js` | Fetch pageviews, expose `sortedPageviews` array |
| `frontend/index.html` | Add page view breakdown section under map |
| `frontend/assets/css/main.css` | Add `.analytics-table` styles |

---

## DynamoDB Key Patterns

| Partition | SK pattern | Purpose |
|-----------|-----------|---------|
| `VISITORS` | `VISITOR#{ip}` | One item per unique IP; upserted on each visit |
| `PAGEVIEWS` | `VIEW#{timestamp}#{uuid}` | One item per page navigation |

---

## Task 1: New model functions

**Files:**
- Modify: `backend/models/visits.py`
- Create: `backend/tests/test_visits.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_visits.py`:

```python
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
    assert len(locs) == 1  # still one unique visitor


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
```

- [ ] **Step 2: Run to confirm they fail**

```bash
cd backend && pytest tests/test_visits.py -v
```
Expected: `ImportError` or `AttributeError` — `upsert_visitor`, `record_pageview`, `get_pageviews` don't exist yet.

- [ ] **Step 3: Implement new model functions**

Replace the entire contents of `backend/models/visits.py`:

```python
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd backend && pytest tests/test_visits.py -v
```
Expected: all 5 tests pass.

- [ ] **Step 5: Update the analytics test in test_stats.py**

Replace `test_get_analytics_returns_breakdown` in `backend/tests/test_stats.py`:

```python
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
```

- [ ] **Step 6: Run full test suite**

```bash
cd backend && pytest tests/ -v
```
Expected: all tests pass (test_stats.py::test_get_analytics_returns_breakdown now uses `record_pageview`).

- [ ] **Step 7: Commit**

```bash
git add backend/models/visits.py backend/tests/test_visits.py backend/tests/test_stats.py
git commit -m "feat: replace record_visit with upsert_visitor + record_pageview + get_pageviews"
```

---

## Task 2: POST /visits route

**Files:**
- Create: `backend/routes/visits.py`
- Modify: `backend/router.py`
- Modify: `backend/tests/test_visits.py`

- [ ] **Step 1: Write failing tests**

Add to `backend/tests/test_visits.py`:

```python
def test_post_visits_records_visitor_and_pageview(ddb_table, monkeypatch):
    monkeypatch.setattr("models.visits._lookup_ip", lambda ip: {})
    from router import route
    from models.visits import get_pageviews
    event = make_event("POST", "/visits", body={"page": "home"})
    event["requestContext"]["http"]["sourceIp"] = "1.2.3.4"
    resp = route(event)
    assert resp["statusCode"] == 200
    assert get_pageviews()["total"] == 1
    assert get_pageviews()["by_page"]["home"] == 1


def test_post_visits_requires_page(ddb_table):
    from router import route
    event = make_event("POST", "/visits", body={})
    event["requestContext"]["http"]["sourceIp"] = "1.2.3.4"
    resp = route(event)
    assert resp["statusCode"] == 400


def test_post_visits_requires_source_ip(ddb_table):
    from router import route
    resp = route(make_event("POST", "/visits", body={"page": "home"}))
    assert resp["statusCode"] == 400
```

- [ ] **Step 2: Run to confirm they fail**

```bash
cd backend && pytest tests/test_visits.py::test_post_visits_records_visitor_and_pageview tests/test_visits.py::test_post_visits_requires_page tests/test_visits.py::test_post_visits_requires_source_ip -v
```
Expected: FAIL — route returns 404.

- [ ] **Step 3: Create the route handler**

Create `backend/routes/visits.py`:

```python
from models import visits as visit_model
from utils import ok, bad_request


def record_visit(event, path_params, body, query, headers):
    ip = event.get("requestContext", {}).get("http", {}).get("sourceIp", "")
    page = body.get("page", "")
    if not ip:
        return bad_request("Missing source IP")
    if not page:
        return bad_request("Missing page")
    visit_model.upsert_visitor(ip, page)
    visit_model.record_pageview(ip, page)
    return ok(None)
```

- [ ] **Step 4: Register the route and remove old middleware**

In `backend/router.py`, replace:

```python
    if method == "OPTIONS":
        return cors_response(200, {})

    # Record visit (best-effort)
    ip = ctx.get("sourceIp", "")
    if ip:
        try:
            from models.visits import record_visit
            record_visit(ip, path)
        except Exception:
            pass

    # Import route handlers here to keep imports lazy
    from routes import (
        meta, content, projects, courses, github,
        auth_routes, comments, ratings, guestbook,
        quiz, testimonials, stats, contact, admin, docs,
    )
```

With:

```python
    if method == "OPTIONS":
        return cors_response(200, {})

    # Import route handlers here to keep imports lazy
    from routes import (
        meta, content, projects, courses, github,
        auth_routes, comments, ratings, guestbook,
        quiz, testimonials, stats, contact, admin, docs, visits,
    )
```

Then add the route entry after the Stats block in the ROUTES list:

```python
        # Visits
        ("POST",   "/visits",                            visits.record_visit),
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
cd backend && pytest tests/test_visits.py -v
```
Expected: all 8 tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/routes/visits.py backend/router.py backend/tests/test_visits.py
git commit -m "feat: POST /visits — records unique visitor and page view"
```

---

## Task 3: GET /stats/pageviews route

**Files:**
- Modify: `backend/routes/stats.py`
- Modify: `backend/router.py`
- Modify: `backend/tests/test_stats.py`

- [ ] **Step 1: Write failing test**

Add to `backend/tests/test_stats.py`:

```python
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
```

- [ ] **Step 2: Run to confirm they fail**

```bash
cd backend && pytest tests/test_stats.py::test_get_pageviews_returns_counts tests/test_stats.py::test_get_pageviews_empty -v
```
Expected: FAIL — 404.

- [ ] **Step 3: Add handler to stats route**

In `backend/routes/stats.py`, add:

```python
from auth import require_admin
from models import visits as visit_model
from utils import ok


def get_visitor_locations(event, path_params, body, query, headers):
    return ok(visit_model.get_visitor_locations())


def get_pageviews(event, path_params, body, query, headers):
    return ok(visit_model.get_pageviews())


@require_admin
def get_analytics(event, path_params, body, query, headers, user):
    return ok(visit_model.get_analytics())
```

- [ ] **Step 4: Register the route**

In `backend/router.py`, add to the Stats block in ROUTES:

```python
        # Stats
        ("GET",    "/stats/visitors",                 stats.get_visitor_locations),
        ("GET",    "/stats/pageviews",                stats.get_pageviews),
        ("GET",    "/stats/analytics",                stats.get_analytics),
```

- [ ] **Step 5: Run full test suite**

```bash
cd backend && pytest tests/ -v
```
Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/routes/stats.py backend/router.py backend/tests/test_stats.py
git commit -m "feat: GET /stats/pageviews — public page view counts endpoint"
```

---

## Task 4: Frontend — fire POST /visits on navigation

**Files:**
- Modify: `frontend/assets/js/app.js`

- [ ] **Step 1: Add the visit call to handleRoute**

In `frontend/assets/js/app.js`, add one line after `this.currentPage` is set (line 89):

```js
    handleRoute(hash) {
      const path = hash.replace(/^#/, "") || "/";
      const [rawBase, ...rest] = path.split("/").filter(Boolean);
      const base = (rawBase || "").split("?")[0];

      // Route table
      const routes = {
        "":             "home",
        "home":         "home",
        "about":        "about",
        "projects":     rest.length ? "project-detail" : "projects",
        "courses":      rest.length ? "course-detail"  : "courses",
        "skills":       "skills",
        "stats":        "stats",
        "contact":      "contact",
        "guestbook":    "guestbook",
        "testimonials": "testimonials",
        "developer":    "developer",
        "quiz":         "quiz",
        "login":        "login",
        "register":     "register",
        "verify-email": "verify-email",
        "forgot-password": "forgot-password",
        "reset-password":  "reset-password",
      };

      this.currentPage = routes[base ?? ""] || "not-found";
      this.currentParams = { id: rest[0] };

      // Record page visit (fire-and-forget)
      api.post("/visits", { page: this.currentPage }).catch(() => {});

      // Scroll to top on navigation
      window.scrollTo(0, 0);

      // Re-attach scroll observers after page change and restart page animation
      this.$nextTick(() => {
        initScrollAnimations();
        // Force page enter animation to replay on each navigation
        const page = document.querySelector(".page");
        if (page) {
          page.style.animation = "none";
          page.offsetHeight; // reflow
          page.style.animation = "";
        }
      });
    },
```

- [ ] **Step 2: Verify manually**

Open `frontend/index.html` via local static server, navigate between pages, then check DynamoDB:

```bash
AWS_PROFILE=portfolio-admin aws dynamodb query \
  --table-name portfolio \
  --key-condition-expression "PK = :pk AND begins_with(SK, :sk)" \
  --expression-attribute-values '{":pk":{"S":"PAGEVIEWS"},":sk":{"S":"VIEW#"}}' \
  --select COUNT \
  --region us-east-1
```

Expected: Count increments by 1 per navigation (not 9).

- [ ] **Step 3: Commit**

```bash
git add frontend/assets/js/app.js
git commit -m "feat: fire POST /visits on each page navigation"
```

---

## Task 5: Frontend — stats page analytics section

**Files:**
- Modify: `frontend/assets/js/pages/stats.js`
- Modify: `frontend/index.html`
- Modify: `frontend/assets/css/main.css`

- [ ] **Step 1: Update stats.js to fetch pageviews**

Replace the full contents of `frontend/assets/js/pages/stats.js`:

```js
// frontend/assets/js/pages/stats.js
function statsPage() {
  return {
    locations: [],
    total: 0,
    pageviews: null,
    sortedPageviews: [],
    loading: true,
    map: null,

    async init() {
      const [visitorsResp, pageviewsResp] = await Promise.all([
        api.get("/stats/visitors"),
        api.get("/stats/pageviews"),
      ]);
      this.locations = visitorsResp.data || [];
      this.total = this.locations.length;
      this.pageviews = pageviewsResp.data || { by_page: {}, total: 0 };
      this.sortedPageviews = Object.entries(this.pageviews.by_page)
        .sort((a, b) => b[1] - a[1]);
      this.loading = false;
      await this.loadLeaflet();
      await this.$nextTick();
      this.initMap();
      this._themeHandler = () => this.initMap();
      window.addEventListener("themechange", this._themeHandler);
    },

    async loadLeaflet() {
      if (window.L) return;
      await new Promise((resolve, reject) => {
        const link = document.createElement("link");
        link.rel = "stylesheet";
        link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
        document.head.appendChild(link);
        const script = document.createElement("script");
        script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
      });
    },

    initMap() {
      if (this.map) { this.map.remove(); this.map = null; }
      const el = document.getElementById("visitor-map");
      if (!el || typeof L === "undefined") return;

      this.map = L.map("visitor-map", { zoomControl: true }).setView([20, 0], 2);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 18,
      }).addTo(this.map);

      this.locations.forEach(loc => {
        if (loc.lat && loc.lon) {
          L.circleMarker([parseFloat(loc.lat), parseFloat(loc.lon)], {
            radius: 5,
            fillColor: "#e53e3e",
            color: "transparent",
            fillOpacity: 0.7,
          })
          .addTo(this.map)
          .bindPopup(`${loc.city || ""}${loc.city ? ", " : ""}${loc.country || "Unknown"}`);
        }
      });
    },

    destroy() {
      if (this.map) { this.map.remove(); this.map = null; }
      if (this._themeHandler) window.removeEventListener("themechange", this._themeHandler);
    },
  };
}
```

- [ ] **Step 2: Update the stats section in index.html**

Replace the stats section (lines 535–548):

```html
      <!-- STATS -->
      <template x-if="currentPage === 'stats'">
        <div class="page" x-data="statsPage()">
          <h1>Visitor Map</h1>
          <p class="subtitle">People who've visited from around the world.</p>
          <div x-show="loading" class="loading-center"><div class="spinner"></div></div>
          <template x-if="!loading">
            <div>
              <p class="subtitle" style="margin: 0.75rem 0;" x-text="`${total} unique visitor${total !== 1 ? 's' : ''}`"></p>
              <div id="visitor-map" class="visitor-map"></div>
              <template x-if="pageviews && pageviews.total > 0">
                <div style="margin-top: 2rem;">
                  <h2>Page Views</h2>
                  <p class="subtitle" style="margin: 0.5rem 0 1rem;" x-text="`${pageviews.total} total views`"></p>
                  <table class="analytics-table">
                    <thead>
                      <tr><th>Page</th><th>Views</th></tr>
                    </thead>
                    <tbody>
                      <template x-for="[page, count] in sortedPageviews" :key="page">
                        <tr>
                          <td x-text="page"></td>
                          <td x-text="count"></td>
                        </tr>
                      </template>
                    </tbody>
                  </table>
                </div>
              </template>
            </div>
          </template>
        </div>
      </template>
```

- [ ] **Step 3: Add analytics-table CSS**

In `frontend/assets/css/main.css`, after the `.visitor-map` block, add:

```css
/* Analytics table */
.analytics-table { width: 100%; border-collapse: collapse; margin-top: 0.5rem; }
.analytics-table th, .analytics-table td { padding: 0.5rem 0.75rem; text-align: left; border-bottom: 1px solid var(--border); }
.analytics-table th { font-weight: 600; color: var(--text-muted); font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; }
.analytics-table tr:last-child td { border-bottom: none; }
```

- [ ] **Step 4: Commit**

```bash
git add frontend/assets/js/pages/stats.js frontend/index.html frontend/assets/css/main.css
git commit -m "feat: stats page shows page view analytics under visitor map"
```

---

## Task 6: PR and deploy

- [ ] **Step 1: Run full backend test suite one last time**

```bash
cd backend && pytest tests/ -v
```
Expected: all tests pass.

- [ ] **Step 2: Push and open PR**

```bash
git push
gh pr create --base dev --title "feat: visitor analytics — unique visitor map + page view tracking"
```

- [ ] **Step 3: After merge to dev, verify in DynamoDB**

```bash
# Check unique visitors
AWS_PROFILE=portfolio-admin aws dynamodb query \
  --table-name portfolio \
  --key-condition-expression "PK = :pk AND begins_with(SK, :sk)" \
  --expression-attribute-values '{":pk":{"S":"VISITORS"},":sk":{"S":"VISITOR#"}}' \
  --select COUNT --region us-east-1

# Check page views
AWS_PROFILE=portfolio-admin aws dynamodb query \
  --table-name portfolio \
  --key-condition-expression "PK = :pk AND begins_with(SK, :sk)" \
  --expression-attribute-values '{":pk":{"S":"PAGEVIEWS"},":sk":{"S":"VIEW#"}}' \
  --select COUNT --region us-east-1
```

Navigate between pages — PAGEVIEWS count should increment by 1 per navigation. VISITORS count should stay at 1 for the same IP across multiple navigations.
