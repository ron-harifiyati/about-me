# About Page Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 4 new sections to the About page (Languages, Beyond Code, Currently Learning, How I Work) with backend routes, frontend rendering, admin management, tests, and DynamoDB seed data.

**Architecture:** Each section follows the existing content pattern — DynamoDB item under `PK=CONTENT`, generic model layer, thin route handlers, Alpine.js rendering. No new abstractions needed.

**Tech Stack:** Python 3 (Lambda), DynamoDB, Alpine.js, vanilla CSS, pytest + moto

**Spec:** `docs/superpowers/specs/2026-04-08-about-page-expansion-design.md`

---

## File Map

| Action | File | Responsibility |
|--------|------|---------------|
| Modify | `backend/routes/content.py` | 6 new route handlers (GET/PUT for languages, hobbies, values) |
| Modify | `backend/router.py` | Register 6 new routes |
| Modify | `backend/tests/test_content.py` | Tests for all 6 new routes |
| Modify | `frontend/assets/js/pages/about.js` | Fetch and expose new data |
| Modify | `frontend/index.html` | 4 new HTML sections on About page |
| Modify | `frontend/assets/css/main.css` | Styles for new sections |
| Modify | `frontend/admin.html` | 3 new admin tabs (Languages, Hobbies, Values) |
| Modify | `frontend/assets/js/admin-app.js` | Fetch/save logic for new content |

---

### Task 1: Backend routes for Languages, Hobbies, Values

**Files:**
- Modify: `backend/routes/content.py`
- Modify: `backend/router.py`

- [ ] **Step 1: Add 6 route handlers to `backend/routes/content.py`**

Add at the end of the file:

```python
def get_languages(event, path_params, body, query, headers):
    return ok(get_content("LANGUAGES_SPOKEN"))


@require_admin
def update_languages(event, path_params, body, query, headers, user):
    return ok(update_content("LANGUAGES_SPOKEN", body))


def get_hobbies(event, path_params, body, query, headers):
    return ok(get_content("HOBBIES"))


@require_admin
def update_hobbies(event, path_params, body, query, headers, user):
    return ok(update_content("HOBBIES", body))


def get_values(event, path_params, body, query, headers):
    return ok(get_content("VALUES"))


@require_admin
def update_values(event, path_params, body, query, headers, user):
    return ok(update_content("VALUES", body))
```

- [ ] **Step 2: Register routes in `backend/router.py`**

Add these 6 entries in the `ROUTES` list, right after the existing `("/currently-learning", ...)` entries (around line 50):

```python
        ("GET",    "/languages",                     content.get_languages),
        ("PUT",    "/languages",                     content.update_languages),
        ("GET",    "/hobbies",                       content.get_hobbies),
        ("PUT",    "/hobbies",                       content.update_hobbies),
        ("GET",    "/values",                        content.get_values),
        ("PUT",    "/values",                        content.update_values),
```

- [ ] **Step 3: Run linter**

Run: `cd backend && flake8 . --max-line-length=120 --exclude=tests/,package/`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add backend/routes/content.py backend/router.py
git commit -m "feat: add backend routes for languages, hobbies, and values"
```

---

### Task 2: Backend tests

**Files:**
- Modify: `backend/tests/test_content.py`

- [ ] **Step 1: Add tests for all 6 new routes**

Append to `backend/tests/test_content.py`:

```python
# --- Languages ---

def test_get_languages_empty(ddb_table):
    from router import route
    resp = route(make_event("GET", "/languages"))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["data"] is None or isinstance(body["data"], dict)


def test_put_and_get_languages(ddb_table):
    from router import route
    payload = {"languages": [
        {"name": "Ndebele", "level": "Native"},
        {"name": "English", "level": "Fluent"},
    ]}
    put_resp = route(make_event("PUT", "/languages", body=payload, headers=_admin_headers()))
    assert put_resp["statusCode"] == 200

    get_resp = route(make_event("GET", "/languages"))
    body = json.loads(get_resp["body"])
    assert len(body["data"]["languages"]) == 2
    assert body["data"]["languages"][0]["name"] == "Ndebele"


def test_put_languages_requires_admin(ddb_table):
    from router import route
    resp = route(make_event("PUT", "/languages", body={"languages": []}))
    assert resp["statusCode"] == 401


# --- Hobbies ---

def test_get_hobbies_empty(ddb_table):
    from router import route
    resp = route(make_event("GET", "/hobbies"))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["data"] is None or isinstance(body["data"], dict)


def test_put_and_get_hobbies(ddb_table):
    from router import route
    payload = {"items": [
        {"icon": "🏃", "label": "Marathon Running"},
        {"icon": "🎮", "label": "Gaming"},
    ]}
    put_resp = route(make_event("PUT", "/hobbies", body=payload, headers=_admin_headers()))
    assert put_resp["statusCode"] == 200

    get_resp = route(make_event("GET", "/hobbies"))
    body = json.loads(get_resp["body"])
    assert len(body["data"]["items"]) == 2
    assert body["data"]["items"][0]["label"] == "Marathon Running"


def test_put_hobbies_requires_admin(ddb_table):
    from router import route
    resp = route(make_event("PUT", "/hobbies", body={"items": []}))
    assert resp["statusCode"] == 401


# --- Values ---

def test_get_values_empty(ddb_table):
    from router import route
    resp = route(make_event("GET", "/values"))
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["data"] is None or isinstance(body["data"], dict)


def test_put_and_get_values(ddb_table):
    from router import route
    payload = {"values": [
        {"title": "Accountability", "description": "I own my work."},
        {"title": "Simplicity", "description": "Keep it simple."},
    ]}
    put_resp = route(make_event("PUT", "/values", body=payload, headers=_admin_headers()))
    assert put_resp["statusCode"] == 200

    get_resp = route(make_event("GET", "/values"))
    body = json.loads(get_resp["body"])
    assert len(body["data"]["values"]) == 2
    assert body["data"]["values"][0]["title"] == "Accountability"


def test_put_values_requires_admin(ddb_table):
    from router import route
    resp = route(make_event("PUT", "/values", body={"values": []}))
    assert resp["statusCode"] == 401
```

- [ ] **Step 2: Run tests**

Run: `cd backend && pytest tests/test_content.py -v`
Expected: All tests pass (existing + 9 new)

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_content.py
git commit -m "test: add tests for languages, hobbies, and values routes"
```

---

### Task 3: Seed DynamoDB with initial data

- [ ] **Step 1: Seed LANGUAGES_SPOKEN**

```bash
AWS_PROFILE=portfolio-admin aws dynamodb put-item \
  --table-name portfolio \
  --item '{
    "PK": {"S": "CONTENT"},
    "SK": {"S": "LANGUAGES_SPOKEN"},
    "languages": {"L": [
      {"M": {"name": {"S": "Ndebele"}, "level": {"S": "Native"}}},
      {"M": {"name": {"S": "Shona"}, "level": {"S": "Fluent"}}},
      {"M": {"name": {"S": "English"}, "level": {"S": "Fluent"}}},
      {"M": {"name": {"S": "German"}, "level": {"S": "Elementary"}}},
      {"M": {"name": {"S": "French"}, "level": {"S": "Elementary"}}}
    ]}
  }'
```

- [ ] **Step 2: Seed HOBBIES**

```bash
AWS_PROFILE=portfolio-admin aws dynamodb put-item \
  --table-name portfolio \
  --item '{
    "PK": {"S": "CONTENT"},
    "SK": {"S": "HOBBIES"},
    "items": {"L": [
      {"M": {"icon": {"S": "🏃"}, "label": {"S": "Marathon Running"}}},
      {"M": {"icon": {"S": "🎮"}, "label": {"S": "Mobile & PC Gaming"}}},
      {"M": {"icon": {"S": "🎵"}, "label": {"S": "Music"}}},
      {"M": {"icon": {"S": "🎬"}, "label": {"S": "Movies"}}},
      {"M": {"icon": {"S": "📺"}, "label": {"S": "Anime & Cartoons"}}},
      {"M": {"icon": {"S": "📚"}, "label": {"S": "Comic Books"}}},
      {"M": {"icon": {"S": "📖"}, "label": {"S": "Reading & Docs"}}}
    ]}
  }'
```

- [ ] **Step 3: Seed VALUES**

```bash
AWS_PROFILE=portfolio-admin aws dynamodb put-item \
  --table-name portfolio \
  --item '{
    "PK": {"S": "CONTENT"},
    "SK": {"S": "VALUES"},
    "values": {"L": [
      {"M": {"title": {"S": "Accountability"}, "description": {"S": "I own my work and follow through. If something breaks, I fix it."}}},
      {"M": {"title": {"S": "Simplicity"}, "description": {"S": "The best solution is the one that\u0027s easy to understand and maintain."}}},
      {"M": {"title": {"S": "Clear Communication"}, "description": {"S": "Say what you mean, document what matters, ask when unsure."}}},
      {"M": {"title": {"S": "Diverse Teams"}, "description": {"S": "The best ideas come from different perspectives working together."}}}
    ]}
  }'
```

- [ ] **Step 4: Verify all 3 items exist**

```bash
AWS_PROFILE=portfolio-admin aws dynamodb get-item --table-name portfolio --key '{"PK":{"S":"CONTENT"},"SK":{"S":"LANGUAGES_SPOKEN"}}' --query 'Item.languages.L[0].M.name.S' --output text
AWS_PROFILE=portfolio-admin aws dynamodb get-item --table-name portfolio --key '{"PK":{"S":"CONTENT"},"SK":{"S":"HOBBIES"}}' --query 'Item.items.L[0].M.label.S' --output text
AWS_PROFILE=portfolio-admin aws dynamodb get-item --table-name portfolio --key '{"PK":{"S":"CONTENT"},"SK":{"S":"VALUES"}}' --query 'Item.values.L[0].M.title.S' --output text
```

Expected output:
```
Ndebele
Marathon Running
Accountability
```

---

### Task 4: Frontend CSS for new sections

**Files:**
- Modify: `frontend/assets/css/main.css`

- [ ] **Step 1: Add styles after the existing Timeline styles (after line 497)**

Insert after the `.timeline-desc` rule in `main.css`:

```css
/* About — Languages */
.about-lang-badges { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.about-lang-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
  background: var(--bg-alt);
  border: 1px solid var(--border);
  color: var(--text);
}
.about-lang-level {
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.about-lang-level.native { color: var(--accent); }
.about-lang-level.fluent { color: #4CAF50; }
.about-lang-level.elementary { color: var(--text-muted); }

/* About — Hobbies */
.about-hobby-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 0.6rem;
}
.about-hobby-card {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.7rem 0.9rem;
  background: var(--bg-alt);
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 0.85rem;
  color: var(--text);
}
.about-hobby-icon { font-size: 1.2rem; flex-shrink: 0; }

/* About — Values */
.about-values-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.75rem;
}
.about-value-card {
  padding: 1rem;
  background: var(--bg-alt);
  border: 1px solid var(--border);
  border-radius: 8px;
}
.about-value-card h3 { font-size: 0.9rem; margin-bottom: 0.3rem; }
.about-value-card p { font-size: 0.8rem; color: var(--text-muted); line-height: 1.5; }
```

- [ ] **Step 2: Commit**

```bash
git add frontend/assets/css/main.css
git commit -m "feat: add CSS for about page languages, hobbies, and values sections"
```

---

### Task 5: Frontend JS — expand aboutPage() to fetch new data

**Files:**
- Modify: `frontend/assets/js/pages/about.js`

- [ ] **Step 1: Replace the entire `about.js` file**

```javascript
// frontend/assets/js/pages/about.js
function aboutPage() {
  return {
    about: null,
    timeline: [],
    languages: [],
    hobbies: [],
    learning: [],
    values: [],
    loading: true,

    async init() {
      const [aboutResp, timelineResp, langResp, hobbiesResp, learningResp, valuesResp] = await Promise.all([
        api.get("/about"),
        api.get("/timeline"),
        api.get("/languages"),
        api.get("/hobbies"),
        api.get("/currently-learning"),
        api.get("/values"),
      ]);
      this.about = aboutResp.data;
      this.timeline = timelineResp.data?.events || [];
      this.languages = langResp.data?.languages || [];
      this.hobbies = hobbiesResp.data?.items || [];
      this.learning = learningResp.data?.items || [];
      this.values = valuesResp.data?.values || [];
      this.loading = false;
      this.$nextTick(() => initScrollAnimations());
    },
  };
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/assets/js/pages/about.js
git commit -m "feat: fetch languages, hobbies, learning, and values in about page"
```

---

### Task 6: Frontend HTML — add 4 new sections to About page

**Files:**
- Modify: `frontend/index.html`

- [ ] **Step 1: Add 4 sections after the Journey timeline**

In `frontend/index.html`, find the closing `</template>` of the Journey timeline section (line 295: `</template>` after the timeline `</div>`). Insert the following **after** that `</template>` and **before** the closing `</div>` on line 296:

```html
              <!-- Languages -->
              <template x-if="languages.length > 0">
                <div>
                  <hr class="about-divider">
                  <h2>Languages I Speak</h2>
                  <div class="about-lang-badges">
                    <template x-for="lang in languages" :key="lang.name">
                      <span class="about-lang-badge">
                        <span x-text="lang.name"></span>
                        <span class="about-lang-level"
                              :class="lang.level.toLowerCase()"
                              x-text="lang.level"></span>
                      </span>
                    </template>
                  </div>
                </div>
              </template>

              <!-- Beyond Code -->
              <template x-if="hobbies.length > 0">
                <div>
                  <hr class="about-divider">
                  <h2>Beyond Code</h2>
                  <div class="about-hobby-grid">
                    <template x-for="hobby in hobbies" :key="hobby.label">
                      <div class="about-hobby-card fade-in">
                        <span class="about-hobby-icon" x-text="hobby.icon"></span>
                        <span x-text="hobby.label"></span>
                      </div>
                    </template>
                  </div>
                </div>
              </template>

              <!-- Currently Learning -->
              <template x-if="learning.length > 0">
                <div>
                  <hr class="about-divider">
                  <h2>Currently Learning</h2>
                  <div style="display: flex; flex-wrap: wrap; gap: 0.4rem;">
                    <template x-for="item in learning" :key="item">
                      <span class="badge badge-outline" x-text="item"></span>
                    </template>
                  </div>
                </div>
              </template>

              <!-- How I Work -->
              <template x-if="values.length > 0">
                <div>
                  <hr class="about-divider">
                  <h2>How I Work</h2>
                  <div class="about-values-grid">
                    <template x-for="val in values" :key="val.title">
                      <div class="about-value-card fade-in">
                        <h3 x-text="val.title"></h3>
                        <p x-text="val.description"></p>
                      </div>
                    </template>
                  </div>
                </div>
              </template>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/index.html
git commit -m "feat: add languages, hobbies, learning, and values sections to about page"
```

---

### Task 7: Admin panel — add tabs for Languages, Hobbies, Values

**Files:**
- Modify: `frontend/admin.html`
- Modify: `frontend/assets/js/admin-app.js`

- [ ] **Step 1: Add 3 new tab buttons in `frontend/admin.html`**

Find the tab buttons container (line 287-292). After the "Currently Learning" button (line 291), add:

```html
              <button class="btn btn-sm" :class="activeTab==='languages'?'btn-primary':'btn-outline'" @click="activeTab='languages'">Languages</button>
              <button class="btn btn-sm" :class="activeTab==='hobbies'?'btn-primary':'btn-outline'" @click="activeTab='hobbies'">Hobbies</button>
              <button class="btn btn-sm" :class="activeTab==='values'?'btn-primary':'btn-outline'" @click="activeTab='values'">Values</button>
```

- [ ] **Step 2: Add 3 new tab content panels in `frontend/admin.html`**

After the Currently Learning tab `</div>` (line 335), before the closing `</div>` of the content editor section (line 336), add:

```html
            <!-- Languages tab -->
            <div x-show="activeTab === 'languages'" class="card">
              <p class="subtitle" style="margin-bottom: 0.75rem;">Edit as JSON. Format: {"languages": [{"name": "English", "level": "Fluent"}]}</p>
              <textarea class="form-input" rows="10"
                        :value="JSON.stringify(languagesData, null, 2)"
                        @input="try { languagesData = JSON.parse($event.target.value) } catch(e) {}"></textarea>
              <button class="btn btn-primary" style="margin-top: 0.75rem;" @click="save('languages', languagesData)" :disabled="saving">
                <span x-text="saving ? 'Saving...' : 'Save'"></span>
              </button>
            </div>

            <!-- Hobbies tab -->
            <div x-show="activeTab === 'hobbies'" class="card">
              <p class="subtitle" style="margin-bottom: 0.75rem;">Edit as JSON. Format: {"items": [{"icon": "🏃", "label": "Running"}]}</p>
              <textarea class="form-input" rows="10"
                        :value="JSON.stringify(hobbiesData, null, 2)"
                        @input="try { hobbiesData = JSON.parse($event.target.value) } catch(e) {}"></textarea>
              <button class="btn btn-primary" style="margin-top: 0.75rem;" @click="save('hobbies', hobbiesData)" :disabled="saving">
                <span x-text="saving ? 'Saving...' : 'Save'"></span>
              </button>
            </div>

            <!-- Values tab -->
            <div x-show="activeTab === 'values'" class="card">
              <p class="subtitle" style="margin-bottom: 0.75rem;">Edit as JSON. Format: {"values": [{"title": "...", "description": "..."}]}</p>
              <textarea class="form-input" rows="10"
                        :value="JSON.stringify(valuesData, null, 2)"
                        @input="try { valuesData = JSON.parse($event.target.value) } catch(e) {}"></textarea>
              <button class="btn btn-primary" style="margin-top: 0.75rem;" @click="save('values', valuesData)" :disabled="saving">
                <span x-text="saving ? 'Saving...' : 'Save'"></span>
              </button>
            </div>
```

- [ ] **Step 3: Update `adminContent()` in `frontend/assets/js/admin-app.js`**

Add 3 new state properties after `currentlyLearning`:

```javascript
    languagesData: { languages: [] },
    hobbiesData: { items: [] },
    valuesData: { values: [] },
```

Update the `init()` method to fetch the 3 new endpoints. Replace the existing init:

```javascript
    async init() {
      const [a, s, f, c, l, h, v] = await Promise.all([
        api.get("/about"), api.get("/skills"), api.get("/fun-fact"), api.get("/currently-learning"),
        api.get("/languages"), api.get("/hobbies"), api.get("/values"),
      ]);
      this.about = a.data || {};
      this.skills = s.data || {};
      this.funFacts = { facts: [] };
      this.currentlyLearning = c.data || { items: [] };
      this.languagesData = l.data || { languages: [] };
      this.hobbiesData = h.data || { items: [] };
      this.valuesData = v.data || { values: [] };
    },
```

- [ ] **Step 4: Commit**

```bash
git add frontend/admin.html frontend/assets/js/admin-app.js
git commit -m "feat: add admin tabs for languages, hobbies, and values content"
```

---

### Task 8: Final verification

- [ ] **Step 1: Run backend linter**

Run: `cd backend && flake8 . --max-line-length=120 --exclude=tests/,package/`
Expected: No errors

- [ ] **Step 2: Run all backend tests**

Run: `cd backend && pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 3: Verify the dev API returns new data**

After the Lambda deploys (push to `dev` branch triggers CI/CD), verify:

```bash
curl -s https://ly0fxfdai9.execute-api.us-east-1.amazonaws.com/languages | python3 -m json.tool
curl -s https://ly0fxfdai9.execute-api.us-east-1.amazonaws.com/hobbies | python3 -m json.tool
curl -s https://ly0fxfdai9.execute-api.us-east-1.amazonaws.com/values | python3 -m json.tool
```

Expected: Each returns `{"data": {...}, "error": null}` with the seeded content.

- [ ] **Step 4: Visual check**

Open the dev frontend and navigate to `#/about`. Verify:
- Languages section shows 5 badges with colored proficiency levels
- Beyond Code shows 7 icon cards in a responsive grid
- Currently Learning shows badge list
- How I Work shows 4 value cards
- All sections appear after Journey timeline
- Switch between all 5 themes — colors should adapt
- Check at 768px and 480px widths — grids should collapse gracefully
