# Portfolio Site — Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete Alpine.js SPA — all public pages, auth flow, quiz, admin panel, 5 themes, and polish — served from S3/CloudFront with a Lighthouse score of 90+.

**Architecture:** Single `index.html` entry point; Alpine.js handles client-side routing via `window.location.hash`; all data fetched from the Lambda Function URL via a shared `api.js` fetch wrapper; CSS custom properties power the 5 themes; no build step required.

**Tech Stack:** Alpine.js 3.x (CDN), Leaflet.js (CDN, for visitor map), vanilla HTML/CSS, S3/CloudFront

**Prerequisites:** Plan 2 (Backend) complete — Lambda Function URL available for dev and prod environments.

---

## File Structure

```
frontend/
├── index.html                  # Main SPA — all public + auth + quiz pages
├── admin.html                  # Admin panel (separate page, guards on load)
└── assets/
    ├── css/
    │   ├── theme.css           # CSS custom properties for all 5 themes
    │   └── main.css            # Global styles, layout, components
    ├── js/
    │   ├── api.js              # fetch() wrapper — base URL, JWT headers, error handling
    │   ├── themes.js           # Theme load/save (localStorage for guests, API for auth users)
    │   └── app.js              # Alpine.js app state, router, auth state
    └── images/
        └── favicon.ico         # Custom favicon
```

**Routing strategy:** Hash-based (`#/about`, `#/projects/123`). Alpine.js listens to `hashchange` and renders the correct section. CloudFront serves `index.html` for all paths, so deep links also work without hashes.

**Theme tokens (CSS custom properties):**

| Theme | `--bg` | `--text` | `--accent` |
|-------|--------|----------|------------|
| Light (default) | `#FFFFFF` | `#212529` | `#007BFF` |
| Dark | `#121212` | `#E0E0E0` | `#4FC3F7` |
| Coffee | `#FAF3E0` | `#5D4037` | `#A1887F` |
| Terminal | `#000000` | `#00FF41` | `#008F11` |
| Nordic | `#2E3440` | `#D8DEE9` | `#88C0D0` |

---

<!-- SECTIONS BELOW ARE ADDED INCREMENTALLY -->

---

## Feature Branch: `feature/frontend-foundation`

> Covers: theme CSS, API client, app.js (router + auth state), index.html skeleton, global nav

```bash
git checkout dev
git checkout -b feature/frontend-foundation
```

---

### Task 1: Theme CSS

**Files:**
- Create: `frontend/assets/css/theme.css`
- Create: `frontend/assets/css/main.css`

- [ ] **Step 1: Create theme.css**

```css
/* frontend/assets/css/theme.css */

/* Default: Light */
:root {
  --bg:        #FFFFFF;
  --bg-alt:    #F8F9FA;
  --text:      #212529;
  --text-muted:#6C757D;
  --accent:    #007BFF;
  --accent-hover: #0056b3;
  --border:    #DEE2E6;
  --card-bg:   #FFFFFF;
  --shadow:    0 2px 8px rgba(0,0,0,0.08);
}

[data-theme="dark"] {
  --bg:        #121212;
  --bg-alt:    #1E1E1E;
  --text:      #E0E0E0;
  --text-muted:#9E9E9E;
  --accent:    #4FC3F7;
  --accent-hover: #81D4FA;
  --border:    #333333;
  --card-bg:   #1E1E1E;
  --shadow:    0 2px 8px rgba(0,0,0,0.4);
}

[data-theme="coffee"] {
  --bg:        #FAF3E0;
  --bg-alt:    #F0E6C8;
  --text:      #5D4037;
  --text-muted:#8D6E63;
  --accent:    #A1887F;
  --accent-hover: #795548;
  --border:    #D7CCC8;
  --card-bg:   #FDF6E3;
  --shadow:    0 2px 8px rgba(93,64,55,0.12);
}

[data-theme="terminal"] {
  --bg:        #000000;
  --bg-alt:    #0A0A0A;
  --text:      #00FF41;
  --text-muted:#008F11;
  --accent:    #008F11;
  --accent-hover: #00CC33;
  --border:    #003300;
  --card-bg:   #050505;
  --shadow:    0 2px 8px rgba(0,255,65,0.1);
}

[data-theme="nordic"] {
  --bg:        #2E3440;
  --bg-alt:    #3B4252;
  --text:      #D8DEE9;
  --text-muted:#B0BAD0;
  --accent:    #88C0D0;
  --accent-hover: #81A1C1;
  --border:    #4C566A;
  --card-bg:   #3B4252;
  --shadow:    0 2px 8px rgba(0,0,0,0.3);
}
```

- [ ] **Step 2: Create main.css**

```css
/* frontend/assets/css/main.css */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background-color: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-size: 16px;
  line-height: 1.6;
  transition: background-color 0.2s, color 0.2s;
}

a { color: var(--accent); text-decoration: none; }
a:hover { color: var(--accent-hover); text-decoration: underline; }

/* Layout */
.container { max-width: 900px; margin: 0 auto; padding: 0 1.5rem; }
.page { padding: 2rem 0; min-height: calc(100vh - 64px - 60px); }

/* Nav */
nav {
  background: var(--bg-alt);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
  height: 64px;
}
.nav-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
}
.nav-brand { font-weight: 700; font-size: 1.1rem; color: var(--text); }
.nav-links { display: flex; gap: 1.25rem; align-items: center; flex-wrap: wrap; }
.nav-links a {
  color: var(--text-muted);
  font-size: 0.9rem;
  transition: color 0.15s;
}
.nav-links a:hover, .nav-links a.active { color: var(--accent); text-decoration: none; }

/* Theme toggle button */
.theme-toggle {
  background: var(--bg-alt);
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: 6px;
  padding: 0.3rem 0.75rem;
  cursor: pointer;
  font-size: 0.85rem;
}
.theme-toggle:hover { border-color: var(--accent); }

/* Cards */
.card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.5rem;
  box-shadow: var(--shadow);
  transition: box-shadow 0.2s;
}
.card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.12); }

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.25rem;
  margin-top: 1.5rem;
}

/* Star rating */
.stars { color: #F5A623; letter-spacing: 2px; }
.stars-muted { color: var(--border); }

/* Badges */
.badge {
  display: inline-block;
  padding: 0.2rem 0.6rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  background: var(--accent);
  color: var(--bg);
}
.badge-outline {
  background: transparent;
  border: 1px solid var(--accent);
  color: var(--accent);
}

/* Forms */
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; margin-bottom: 0.3rem; font-size: 0.9rem; color: var(--text-muted); }
.form-input {
  width: 100%;
  padding: 0.6rem 0.9rem;
  background: var(--bg-alt);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text);
  font-size: 0.95rem;
  transition: border-color 0.15s;
}
.form-input:focus { outline: none; border-color: var(--accent); }

/* Buttons */
.btn {
  display: inline-block;
  padding: 0.55rem 1.25rem;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 500;
  transition: background 0.15s, opacity 0.15s;
}
.btn-primary { background: var(--accent); color: #fff; }
.btn-primary:hover { background: var(--accent-hover); }
.btn-outline {
  background: transparent;
  border: 1px solid var(--accent);
  color: var(--accent);
}
.btn-outline:hover { background: var(--accent); color: #fff; }
.btn-danger { background: #DC3545; color: #fff; }
.btn-sm { padding: 0.35rem 0.8rem; font-size: 0.85rem; }

/* Loading spinner */
.spinner {
  display: inline-block;
  width: 24px; height: 24px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.loading-center { display: flex; justify-content: center; padding: 3rem 0; }

/* Section headings */
h1 { font-size: 2rem; margin-bottom: 0.5rem; }
h2 { font-size: 1.4rem; margin-bottom: 1rem; }
h3 { font-size: 1.1rem; margin-bottom: 0.5rem; }
.subtitle { color: var(--text-muted); font-size: 1rem; }

/* Alert */
.alert {
  padding: 0.75rem 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}
.alert-error { background: #fde8e8; color: #c0392b; border: 1px solid #f5c6cb; }
.alert-success { background: #e8f5e9; color: #2e7d32; border: 1px solid #c3e6cb; }

/* Ticker */
.ticker-wrap {
  overflow: hidden;
  white-space: nowrap;
  background: var(--bg-alt);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 0.5rem 0;
}
.ticker-text {
  display: inline-block;
  animation: ticker 20s linear infinite;
}
@keyframes ticker { from { transform: translateX(100%); } to { transform: translateX(-100%); } }

/* Footer */
footer {
  background: var(--bg-alt);
  border-top: 1px solid var(--border);
  text-align: center;
  padding: 1rem;
  font-size: 0.85rem;
  color: var(--text-muted);
}

/* Responsive */
@media (max-width: 640px) {
  .nav-links { gap: 0.75rem; }
  .nav-links a { font-size: 0.8rem; }
  h1 { font-size: 1.5rem; }
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/assets/css/
git commit -m "feat: add theme CSS (5 themes) and global styles"
```

---

### Task 2: api.js — fetch wrapper

**Files:**
- Create: `frontend/assets/js/api.js`

- [ ] **Step 1: Create api.js**

```javascript
// frontend/assets/js/api.js

// Set this to your Lambda Function URL.
// For production, swap DEV_API_URL for PROD_API_URL.
const DEV_API_URL  = "https://REPLACE_WITH_DEV_LAMBDA_URL";
const PROD_API_URL = "https://REPLACE_WITH_PROD_LAMBDA_URL";

// Detect environment: if served from prod CloudFront domain, use prod API.
const API_BASE = (() => {
  const host = window.location.hostname;
  // Update this check once you have your prod CloudFront domain
  return (host.endsWith(".cloudfront.net") && !host.includes("dev"))
    ? PROD_API_URL
    : DEV_API_URL;
})();

function getAuthHeaders() {
  const token = localStorage.getItem("access_token");
  return token ? { "Authorization": `Bearer ${token}` } : {};
}

async function apiFetch(path, options = {}) {
  const url = `${API_BASE.replace(/\/$/, "")}${path}`;
  const headers = {
    "Content-Type": "application/json",
    ...getAuthHeaders(),
    ...(options.headers || {}),
  };
  const config = { ...options, headers };
  if (config.body && typeof config.body !== "string") {
    config.body = JSON.stringify(config.body);
  }
  try {
    const resp = await fetch(url, config);
    const json = await resp.json();
    return { ok: resp.ok, status: resp.status, data: json.data, error: json.error };
  } catch (err) {
    return { ok: false, status: 0, data: null, error: "Network error" };
  }
}

const api = {
  get:    (path)         => apiFetch(path, { method: "GET" }),
  post:   (path, body)   => apiFetch(path, { method: "POST",   body }),
  put:    (path, body)   => apiFetch(path, { method: "PUT",    body }),
  delete: (path)         => apiFetch(path, { method: "DELETE" }),
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/assets/js/api.js
git commit -m "feat: add API fetch wrapper"
```

---

### Task 3: themes.js — theme management

**Files:**
- Create: `frontend/assets/js/themes.js`

- [ ] **Step 1: Create themes.js**

```javascript
// frontend/assets/js/themes.js

const THEMES = ["light", "dark", "coffee", "terminal", "nordic"];

function applyTheme(theme) {
  if (!THEMES.includes(theme)) theme = "light";
  document.documentElement.setAttribute("data-theme", theme === "light" ? "" : theme);
  // Keep :root clean for light — remove attribute entirely
  if (theme === "light") {
    document.documentElement.removeAttribute("data-theme");
  }
  localStorage.setItem("theme", theme);
}

function loadTheme() {
  const saved = localStorage.getItem("theme") || "light";
  applyTheme(saved);
  return saved;
}

function cycleTheme(current) {
  const idx = THEMES.indexOf(current);
  const next = THEMES[(idx + 1) % THEMES.length];
  applyTheme(next);
  return next;
}

async function syncThemeToServer(theme) {
  const token = localStorage.getItem("access_token");
  if (!token) return;
  await api.put("/auth/me", { theme });
}

async function loadThemeFromServer() {
  const token = localStorage.getItem("access_token");
  if (!token) return loadTheme();
  const resp = await api.get("/auth/me");
  if (resp.ok && resp.data?.theme) {
    applyTheme(resp.data.theme);
    return resp.data.theme;
  }
  return loadTheme();
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/assets/js/themes.js
git commit -m "feat: add theme management (localStorage + server sync)"
```

---

### Task 4: app.js — Alpine.js app + router

**Files:**
- Create: `frontend/assets/js/app.js`

- [ ] **Step 1: Create app.js**

```javascript
// frontend/assets/js/app.js

function portfolioApp() {
  return {
    // Auth state
    user: null,
    accessToken: null,

    // Router state
    currentPage: "home",
    currentParams: {},

    // UI state
    theme: "light",
    navOpen: false,

    async init() {
      // Load theme
      this.theme = loadTheme();

      // Restore auth session
      const token = localStorage.getItem("access_token");
      if (token) {
        this.accessToken = token;
        const resp = await api.get("/auth/me");
        if (resp.ok) {
          this.user = resp.data;
          // Sync server theme
          if (resp.data.theme) {
            this.theme = resp.data.theme;
            applyTheme(resp.data.theme);
          }
        } else {
          // Token expired or invalid — clear it
          this.logout(false);
        }
      }

      // Initial route
      this.handleRoute(window.location.hash || "#/");
      window.addEventListener("hashchange", () => {
        this.handleRoute(window.location.hash);
        this.navOpen = false;
      });
    },

    handleRoute(hash) {
      const path = hash.replace(/^#/, "") || "/";
      const [base, ...rest] = path.split("/").filter(Boolean);

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
      };

      this.currentPage = routes[base] || "not-found";
      this.currentParams = { id: rest[0] };

      // Scroll to top on navigation
      window.scrollTo(0, 0);
    },

    navigate(page) {
      window.location.hash = `#/${page}`;
    },

    async toggleTheme() {
      this.theme = cycleTheme(this.theme);
      await syncThemeToServer(this.theme);
    },

    async login(email, password, rememberMe) {
      const resp = await api.post("/auth/login", { email, password, remember_me: rememberMe });
      if (resp.ok) {
        this.accessToken = resp.data.access_token;
        this.user = resp.data.user;
        localStorage.setItem("access_token", resp.data.access_token);
        localStorage.setItem("refresh_token", resp.data.refresh_token);
        return { ok: true };
      }
      return { ok: false, error: resp.error };
    },

    async logout(redirect = true) {
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) await api.post("/auth/logout", { refresh_token: refresh });
      this.user = null;
      this.accessToken = null;
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      if (redirect) this.navigate("home");
    },

    get isAuthenticated() { return !!this.user; },
    get isAdmin() { return this.user?.role === "admin"; },
    get greeting() {
      if (!this.user) return null;
      return `Welcome back, ${this.user.name}`;
    },
  };
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/assets/js/app.js
git commit -m "feat: add Alpine.js app state and hash-based router"
```

---

### Task 5: index.html skeleton + global nav

**Files:**
- Modify: `frontend/index.html`

- [ ] **Step 1: Replace index.html with full SPA skeleton**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ron Harifiyati</title>

  <!-- Open Graph (populated in polish section) -->
  <meta property="og:title" content="Ron Harifiyati — Portfolio">
  <meta property="og:description" content="Integration Engineer, builder, and learner.">
  <meta name="theme-color" content="#007BFF">

  <!-- Styles -->
  <link rel="stylesheet" href="/assets/css/theme.css">
  <link rel="stylesheet" href="/assets/css/main.css">
  <link rel="icon" href="/assets/images/favicon.ico">
</head>
<body>
  <div x-data="portfolioApp()" x-init="init()">

    <!-- GLOBAL NAV -->
    <nav>
      <div class="container nav-inner">
        <a href="#/" class="nav-brand">Ron Harifiyati</a>

        <div class="nav-links">
          <a href="#/about" :class="{ active: currentPage === 'about' }">About</a>
          <a href="#/projects" :class="{ active: currentPage === 'projects' }">Projects</a>
          <a href="#/courses" :class="{ active: currentPage === 'courses' }">Courses</a>
          <a href="#/skills" :class="{ active: currentPage === 'skills' }">Skills</a>
          <a href="#/stats" :class="{ active: currentPage === 'stats' }">Stats</a>
          <a href="#/contact" :class="{ active: currentPage === 'contact' }">Contact</a>
          <a href="#/guestbook" :class="{ active: currentPage === 'guestbook' }">Guestbook</a>
          <a href="#/testimonials" :class="{ active: currentPage === 'testimonials' }">Testimonials</a>
          <a href="#/developer" :class="{ active: currentPage === 'developer' }">Developer</a>
          <template x-if="isAuthenticated">
            <a href="#/quiz" :class="{ active: currentPage === 'quiz' }">Quiz</a>
          </template>
          <template x-if="isAdmin">
            <a href="/admin.html" style="color: var(--accent); font-weight: 600;">Admin</a>
          </template>
          <template x-if="!isAuthenticated">
            <a href="#/login" class="btn btn-primary btn-sm">Login</a>
          </template>
          <template x-if="isAuthenticated">
            <button @click="logout()" class="btn btn-outline btn-sm">Logout</button>
          </template>
          <button class="theme-toggle" @click="toggleTheme()"
                  :title="`Switch theme (current: ${theme})`">
            <span x-text="{ light: '☀️', dark: '🌙', coffee: '☕', terminal: '>_', nordic: '❄️' }[theme] || '☀️'"></span>
          </button>
        </div>
      </div>
    </nav>

    <!-- PERSONALISED GREETING (authenticated users) -->
    <template x-if="isAuthenticated && greeting">
      <div style="background: var(--bg-alt); border-bottom: 1px solid var(--border); padding: 0.4rem 0; text-align: center; font-size: 0.85rem; color: var(--text-muted);">
        <span x-text="greeting"></span>
      </div>
    </template>

    <!-- PAGE ROUTER -->
    <main class="container">

      <!-- HOME -->
      <div x-show="currentPage === 'home'" class="page">
        <div x-data="homePage()" x-init="init()">
          <!-- populated in Task: Home page -->
          <p class="subtitle">Loading...</p>
        </div>
      </div>

      <!-- ABOUT -->
      <div x-show="currentPage === 'about'" class="page">
        <div x-data="aboutPage()" x-init="init()">
          <p class="subtitle">Loading...</p>
        </div>
      </div>

      <!-- PROJECTS LIST -->
      <div x-show="currentPage === 'projects'" class="page">
        <div x-data="projectsPage()" x-init="init()">
          <p class="subtitle">Loading...</p>
        </div>
      </div>

      <!-- PROJECT DETAIL -->
      <div x-show="currentPage === 'project-detail'" class="page">
        <div x-data="projectDetailPage()" x-init="init()">
          <p class="subtitle">Loading...</p>
        </div>
      </div>

      <!-- COURSES LIST -->
      <div x-show="currentPage === 'courses'" class="page">
        <div x-data="coursesPage()" x-init="init()">
          <p class="subtitle">Loading...</p>
        </div>
      </div>

      <!-- COURSE DETAIL -->
      <div x-show="currentPage === 'course-detail'" class="page">
        <div x-data="courseDetailPage()" x-init="init()">
          <p class="subtitle">Loading...</p>
        </div>
      </div>

      <!-- SKILLS -->
      <div x-show="currentPage === 'skills'" class="page">
        <div x-data="skillsPage()" x-init="init()">
          <p class="subtitle">Loading...</p>
        </div>
      </div>

      <!-- STATS -->
      <div x-show="currentPage === 'stats'" class="page">
        <div x-data="statsPage()" x-init="init()">
          <p class="subtitle">Loading...</p>
        </div>
      </div>

      <!-- CONTACT -->
      <div x-show="currentPage === 'contact'" class="page">
        <div x-data="contactPage()" x-init="init()">
          <p class="subtitle">Loading...</p>
        </div>
      </div>

      <!-- GUESTBOOK -->
      <div x-show="currentPage === 'guestbook'" class="page">
        <div x-data="guestbookPage()" x-init="init()">
          <p class="subtitle">Loading...</p>
        </div>
      </div>

      <!-- TESTIMONIALS -->
      <div x-show="currentPage === 'testimonials'" class="page">
        <div x-data="testimonialsPage()" x-init="init()">
          <p class="subtitle">Loading...</p>
        </div>
      </div>

      <!-- DEVELOPER -->
      <div x-show="currentPage === 'developer'" class="page">
        <div x-data="developerPage()" x-init="init()">
          <p class="subtitle">Loading...</p>
        </div>
      </div>

      <!-- QUIZ (auth required) -->
      <div x-show="currentPage === 'quiz'" class="page">
        <template x-if="!isAuthenticated">
          <div>
            <h1>Quiz</h1>
            <p>Please <a href="#/login">log in</a> to take the quiz.</p>
          </div>
        </template>
        <template x-if="isAuthenticated">
          <div x-data="quizPage()" x-init="init()">
            <p class="subtitle">Loading...</p>
          </div>
        </template>
      </div>

      <!-- LOGIN -->
      <div x-show="currentPage === 'login'" class="page">
        <div x-data="loginPage()" x-init="init()">
          <p class="subtitle">Loading...</p>
        </div>
      </div>

      <!-- REGISTER -->
      <div x-show="currentPage === 'register'" class="page">
        <div x-data="registerPage()" x-init="init()">
          <p class="subtitle">Loading...</p>
        </div>
      </div>

      <!-- VERIFY EMAIL -->
      <div x-show="currentPage === 'verify-email'" class="page">
        <div x-data="verifyEmailPage()" x-init="init()">
          <p class="subtitle">Loading...</p>
        </div>
      </div>

      <!-- 404 -->
      <div x-show="currentPage === 'not-found'" class="page">
        <h1>404</h1>
        <p>Page not found. <a href="#/">Go home.</a></p>
      </div>

    </main>

    <!-- FOOTER -->
    <footer>
      <p>Built by Ron Harifiyati &mdash; <span x-text="new Date().getFullYear()"></span></p>
    </footer>

  </div>

  <!-- Scripts — load order matters -->
  <script src="/assets/js/api.js"></script>
  <script src="/assets/js/themes.js"></script>
  <script src="/assets/js/app.js"></script>

  <!-- Page components (added in subsequent tasks) -->
  <script src="/assets/js/pages/home.js"></script>
  <script src="/assets/js/pages/about.js"></script>
  <script src="/assets/js/pages/projects.js"></script>
  <script src="/assets/js/pages/courses.js"></script>
  <script src="/assets/js/pages/skills.js"></script>
  <script src="/assets/js/pages/stats.js"></script>
  <script src="/assets/js/pages/contact.js"></script>
  <script src="/assets/js/pages/guestbook.js"></script>
  <script src="/assets/js/pages/testimonials.js"></script>
  <script src="/assets/js/pages/developer.js"></script>
  <script src="/assets/js/pages/quiz.js"></script>
  <script src="/assets/js/pages/login.js"></script>
  <script src="/assets/js/pages/register.js"></script>
  <script src="/assets/js/pages/verify-email.js"></script>

  <!-- Alpine.js (loaded last) -->
  <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
</body>
</html>
```

- [ ] **Step 2: Create the pages directory and stub all page JS files**

```bash
mkdir -p frontend/assets/js/pages
for page in home about projects courses skills stats contact guestbook testimonials developer quiz login register verify-email; do
  cat > frontend/assets/js/pages/${page}.js << EOF
// ${page}.js — implemented in later tasks
function ${page//-/_}Page() {
  return { async init() {} };
}
EOF
done
```

Rename any functions with hyphens — JavaScript functions can't have hyphens in names:
- `verify-email.js` → function name is `verifyEmailPage`
- `project-detail` and `course-detail` are handled inside projects.js and courses.js

- [ ] **Step 3: Open in browser and verify the skeleton loads**

```bash
# Serve locally (Python built-in server)
cd frontend && python3 -m http.server 8080
```

Open `http://localhost:8080`. Expected:
- Nav bar appears with all links
- Theme toggle cycles through themes (check by pressing it — background changes)
- No JavaScript errors in browser console
- "Loading..." placeholders show on each page section

- [ ] **Step 4: Commit**

```bash
git add frontend/
git commit -m "feat: add index.html SPA skeleton with nav, router, and all page stubs"
```

- [ ] **Step 5: Merge to dev**

```bash
git checkout dev
git merge feature/frontend-foundation
git push origin dev
```

---

## Feature Branch: `feature/public-pages`

> Covers: Home, About, Projects list + detail, Courses list + detail, Skills

```bash
git checkout dev
git checkout -b feature/public-pages
```

---

### Task 6: Home page

**Files:**
- Modify: `frontend/assets/js/pages/home.js`
- Modify: `frontend/index.html` (replace Home page section placeholder)

- [ ] **Step 1: Replace home.js**

```javascript
// frontend/assets/js/pages/home.js
function homePage() {
  return {
    funFact: null,
    ticker: [],
    loading: true,

    async init() {
      const [factResp, tickerResp] = await Promise.all([
        api.get("/fun-fact"),
        api.get("/currently-learning"),
      ]);
      this.funFact = factResp.data?.fact || null;
      this.ticker = tickerResp.data?.items || [];
      this.loading = false;
    },

    refreshFact() {
      api.get("/fun-fact").then(r => { this.funFact = r.data?.fact || null; });
    },
  };
}
```

- [ ] **Step 2: Replace Home page section in index.html**

Find and replace:
```html
      <!-- HOME -->
      <div x-show="currentPage === 'home'" class="page">
        <div x-data="homePage()" x-init="init()">
          <!-- populated in Task: Home page -->
          <p class="subtitle">Loading...</p>
        </div>
      </div>
```

With:
```html
      <!-- HOME -->
      <div x-show="currentPage === 'home'" class="page">
        <div x-data="homePage()" x-init="init()">
          <!-- Hero -->
          <section style="padding: 3rem 0 2rem;">
            <h1 style="font-size: 2.5rem;">Hi, I'm Ron Harifiyati</h1>
            <p class="subtitle" style="font-size: 1.15rem; margin-top: 0.5rem;">
              Integration Engineer · Builder · Learner
            </p>
            <p style="margin-top: 1rem; max-width: 600px; color: var(--text-muted);">
              I build systems that connect things — APIs, workflows, and teams.
              Currently an Integration Engineering intern at Jamf.
            </p>
            <div style="margin-top: 1.5rem; display: flex; gap: 1rem;">
              <a href="#/projects" class="btn btn-primary">See my work</a>
              <a href="#/contact" class="btn btn-outline">Get in touch</a>
            </div>
          </section>

          <!-- Currently Learning Ticker -->
          <template x-if="ticker.length > 0">
            <section style="margin: 1.5rem 0;">
              <p class="subtitle" style="font-size: 0.85rem; margin-bottom: 0.4rem;">Currently learning</p>
              <div class="ticker-wrap">
                <span class="ticker-text" x-text="ticker.join('  ·  ')"></span>
              </div>
            </section>
          </template>

          <!-- Fun Fact Widget -->
          <section style="margin-top: 2rem;">
            <div class="card" style="max-width: 500px;">
              <h3>Fun Fact</h3>
              <div x-show="loading" class="loading-center" style="padding: 1rem 0;"><div class="spinner"></div></div>
              <p x-show="!loading && funFact" x-text="funFact" style="margin: 0.75rem 0; font-style: italic;"></p>
              <p x-show="!loading && !funFact" class="subtitle">No fun facts yet.</p>
              <button x-show="!loading" class="btn btn-outline btn-sm" style="margin-top: 0.75rem;" @click="refreshFact()">
                Another one
              </button>
            </div>
          </section>

          <!-- Quick links -->
          <section style="margin-top: 2.5rem;">
            <div class="card-grid" style="grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));">
              <a href="#/about" class="card" style="text-decoration: none; text-align: center;">
                <div style="font-size: 1.5rem;">👤</div>
                <h3 style="margin-top: 0.5rem;">About me</h3>
                <p class="subtitle" style="font-size: 0.85rem;">Bio &amp; timeline</p>
              </a>
              <a href="#/stats" class="card" style="text-decoration: none; text-align: center;">
                <div style="font-size: 1.5rem;">🌍</div>
                <h3 style="margin-top: 0.5rem;">Visitor map</h3>
                <p class="subtitle" style="font-size: 0.85rem;">See who's visited</p>
              </a>
              <a href="#/developer" class="card" style="text-decoration: none; text-align: center;">
                <div style="font-size: 1.5rem;">📡</div>
                <h3 style="margin-top: 0.5rem;">API Docs</h3>
                <p class="subtitle" style="font-size: 0.85rem;">Try the API live</p>
              </a>
            </div>
          </section>
        </div>
      </div>
```

- [ ] **Step 3: Open browser, navigate to Home — verify fun fact loads and ticker scrolls**

- [ ] **Step 4: Commit**

```bash
git add frontend/assets/js/pages/home.js frontend/index.html
git commit -m "feat: implement Home page (hero, ticker, fun fact, quick links)"
```

---

### Task 7: About page

**Files:**
- Modify: `frontend/assets/js/pages/about.js`
- Modify: `frontend/index.html` (About section)

- [ ] **Step 1: Replace about.js**

```javascript
// frontend/assets/js/pages/about.js
function aboutPage() {
  return {
    about: null,
    timeline: [],
    loading: true,

    async init() {
      const [aboutResp, timelineResp] = await Promise.all([
        api.get("/about"),
        api.get("/timeline"),
      ]);
      this.about = aboutResp.data;
      this.timeline = timelineResp.data?.events || [];
      this.loading = false;
    },
  };
}
```

- [ ] **Step 2: Replace About section in index.html**

```html
      <!-- ABOUT -->
      <div x-show="currentPage === 'about'" class="page">
        <div x-data="aboutPage()" x-init="init()">
          <div x-show="loading" class="loading-center"><div class="spinner"></div></div>
          <template x-if="!loading && about">
            <div>
              <h1>About me</h1>
              <p class="subtitle" style="margin-bottom: 1.5rem;" x-text="about.mission"></p>
              <p x-text="about.bio" style="margin-bottom: 2rem; line-height: 1.8;"></p>

              <!-- Social links -->
              <div style="display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 2.5rem;">
                <template x-if="about.contact?.email">
                  <a :href="'mailto:' + about.contact.email" class="btn btn-outline btn-sm">Email</a>
                </template>
                <template x-if="about.social_links?.github">
                  <a :href="about.social_links.github" target="_blank" class="btn btn-outline btn-sm">GitHub</a>
                </template>
                <template x-if="about.social_links?.linkedin">
                  <a :href="about.social_links.linkedin" target="_blank" class="btn btn-outline btn-sm">LinkedIn</a>
                </template>
              </div>

              <!-- Timeline -->
              <template x-if="timeline.length > 0">
                <div>
                  <h2>Journey</h2>
                  <div style="border-left: 2px solid var(--accent); padding-left: 1.5rem; margin-top: 1rem;">
                    <template x-for="event in timeline" :key="event.date">
                      <div style="margin-bottom: 1.5rem; position: relative;">
                        <div style="position: absolute; left: -1.85rem; top: 0.2rem; width: 12px; height: 12px; background: var(--accent); border-radius: 50%;"></div>
                        <p style="font-size: 0.8rem; color: var(--text-muted);" x-text="event.date"></p>
                        <h3 x-text="event.title" style="margin: 0.2rem 0;"></h3>
                        <p x-text="event.description" style="color: var(--text-muted); font-size: 0.9rem;"></p>
                      </div>
                    </template>
                  </div>
                </div>
              </template>
            </div>
          </template>
          <template x-if="!loading && !about">
            <p class="subtitle">About content coming soon.</p>
          </template>
        </div>
      </div>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/assets/js/pages/about.js frontend/index.html
git commit -m "feat: implement About page (bio, mission, social links, timeline)"
```

---

### Task 8: Projects list + detail

**Files:**
- Modify: `frontend/assets/js/pages/projects.js`
- Modify: `frontend/index.html` (Projects list + Project detail sections)

- [ ] **Step 1: Replace projects.js**

```javascript
// frontend/assets/js/pages/projects.js
function projectsPage() {
  return {
    projects: [],
    loading: true,
    async init() {
      const resp = await api.get("/projects");
      this.projects = resp.data || [];
      this.loading = false;
    },
    starsDisplay(avg) {
      if (!avg) return "No ratings yet";
      const full = Math.round(avg);
      return "★".repeat(full) + "☆".repeat(5 - full) + ` (${avg})`;
    },
  };
}

function projectDetailPage() {
  return {
    project: null,
    comments: [],
    ratings: null,
    newComment: "",
    newRating: 0,
    loading: true,
    submitting: false,
    error: null,
    success: null,

    async init() {
      const id = Alpine.store ? null : document.querySelector("[x-data]")?._x_dataStack?.[0]?.currentParams?.id;
      // Get ID from parent app's currentParams
      const appEl = document.querySelector("[x-data='portfolioApp()']") || document.body;
      const appData = appEl._x_dataStack?.[0];
      const projectId = appData?.currentParams?.id;
      if (!projectId) { this.loading = false; return; }

      const [pResp, cResp, rResp] = await Promise.all([
        api.get(`/projects/${projectId}`),
        api.get(`/projects/${projectId}/comments`),
        api.get(`/projects/${projectId}/ratings`),
      ]);
      this.project = pResp.data;
      this.comments = cResp.data || [];
      this.ratings = rResp.data;
      this.loading = false;
    },

    async submitComment() {
      if (!this.newComment.trim()) return;
      this.submitting = true;
      const id = this.project?.id;
      const resp = await api.post(`/projects/${id}/comments`, { body: this.newComment });
      if (resp.ok) {
        this.comments.push(resp.data);
        this.newComment = "";
        this.success = "Comment posted!";
      } else {
        this.error = resp.error;
      }
      this.submitting = false;
    },

    async submitRating(stars) {
      this.newRating = stars;
      const id = this.project?.id;
      const resp = await api.post(`/projects/${id}/ratings`, { stars });
      if (resp.ok) this.ratings = resp.data;
    },
  };
}
```

- [ ] **Step 2: Replace Projects list section in index.html**

```html
      <!-- PROJECTS LIST -->
      <div x-show="currentPage === 'projects'" class="page">
        <div x-data="projectsPage()" x-init="init()">
          <h1>Projects</h1>
          <p class="subtitle">Things I've built.</p>
          <div x-show="loading" class="loading-center"><div class="spinner"></div></div>
          <div x-show="!loading">
            <template x-if="projects.length === 0">
              <p class="subtitle" style="margin-top: 2rem;">No projects yet.</p>
            </template>
            <div class="card-grid">
              <template x-for="p in projects" :key="p.id">
                <a :href="'#/projects/' + p.id" class="card" style="text-decoration: none; display: block;">
                  <h3 x-text="p.title"></h3>
                  <p x-text="p.description" class="subtitle" style="font-size: 0.9rem; margin: 0.5rem 0;"></p>
                  <div style="display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0.75rem 0;">
                    <template x-for="tag in (p.tech_stack || [])" :key="tag">
                      <span class="badge badge-outline" x-text="tag"></span>
                    </template>
                  </div>
                  <p class="stars" style="font-size: 0.85rem;" x-text="starsDisplay(p.avg_rating)"></p>
                </a>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- PROJECT DETAIL -->
      <div x-show="currentPage === 'project-detail'" class="page">
        <div x-data="projectDetailPage()" x-init="init()">
          <div x-show="loading" class="loading-center"><div class="spinner"></div></div>
          <template x-if="!loading && project">
            <div>
              <a href="#/projects" style="font-size: 0.9rem; color: var(--text-muted);">&larr; Back to Projects</a>
              <h1 x-text="project.title" style="margin-top: 1rem;"></h1>
              <p x-text="project.description" style="margin: 1rem 0; line-height: 1.8;"></p>

              <!-- Tech stack -->
              <div style="display: flex; gap: 0.4rem; flex-wrap: wrap; margin-bottom: 1.5rem;">
                <template x-for="tag in (project.tech_stack || [])" :key="tag">
                  <span class="badge" x-text="tag"></span>
                </template>
              </div>

              <!-- Links -->
              <div style="display: flex; gap: 1rem; margin-bottom: 2rem;">
                <template x-if="project.links?.github">
                  <a :href="project.links.github" target="_blank" class="btn btn-outline btn-sm">GitHub</a>
                </template>
                <template x-if="project.links?.live">
                  <a :href="project.links.live" target="_blank" class="btn btn-primary btn-sm">Live Demo</a>
                </template>
              </div>

              <!-- Ratings -->
              <div class="card" style="max-width: 320px; margin-bottom: 2rem;">
                <h3>Rating</h3>
                <template x-if="ratings">
                  <p x-text="ratings.count > 0 ? `${ratings.average} / 5 from ${ratings.count} ratings` : 'No ratings yet'"></p>
                </template>
                <template x-if="$store?.auth?.isAuthenticated || window.portfolioAuth?.isAuthenticated">
                  <div style="margin-top: 0.75rem;">
                    <p style="font-size: 0.85rem; color: var(--text-muted);">Your rating:</p>
                    <div style="display: flex; gap: 0.5rem; font-size: 1.5rem; cursor: pointer;">
                      <template x-for="n in [1,2,3,4,5]" :key="n">
                        <span @click="submitRating(n)"
                              :style="n <= newRating ? 'color: #F5A623;' : 'color: var(--border);'">★</span>
                      </template>
                    </div>
                  </div>
                </template>
              </div>

              <!-- Comments -->
              <h2>Comments (<span x-text="comments.length"></span>)</h2>
              <template x-if="comments.length === 0">
                <p class="subtitle">No comments yet. Be the first!</p>
              </template>
              <div style="margin-top: 1rem;">
                <template x-for="c in comments" :key="c.comment_id">
                  <div class="card" style="margin-bottom: 0.75rem;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
                      <strong x-text="c.name"></strong>
                      <span class="badge badge-outline" x-text="c.identity" x-show="c.identity"></span>
                    </div>
                    <p x-text="c.body"></p>
                  </div>
                </template>
              </div>

              <!-- Add comment (auth required) -->
              <div style="margin-top: 1.5rem;">
                <div x-show="error" class="alert alert-error" x-text="error"></div>
                <div x-show="success" class="alert alert-success" x-text="success"></div>
                <textarea x-model="newComment" class="form-input" rows="3"
                          placeholder="Leave a comment..."></textarea>
                <button class="btn btn-primary" style="margin-top: 0.5rem;"
                        @click="submitComment()" :disabled="submitting">
                  <span x-text="submitting ? 'Posting...' : 'Post comment'"></span>
                </button>
              </div>
            </div>
          </template>
        </div>
      </div>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/assets/js/pages/projects.js frontend/index.html
git commit -m "feat: implement Projects list and project detail pages"
```

---

### Task 9: Courses list + detail

**Files:**
- Modify: `frontend/assets/js/pages/courses.js`
- Modify: `frontend/index.html` (Courses sections)

- [ ] **Step 1: Replace courses.js** (identical structure to projects.js, different entity)

```javascript
// frontend/assets/js/pages/courses.js
function coursesPage() {
  return {
    courses: [],
    loading: true,
    async init() {
      const resp = await api.get("/courses");
      this.courses = resp.data || [];
      this.loading = false;
    },
    starsDisplay(avg) {
      if (!avg) return "No ratings yet";
      const full = Math.round(avg);
      return "★".repeat(full) + "☆".repeat(5 - full) + ` (${avg})`;
    },
  };
}

function courseDetailPage() {
  return {
    course: null,
    comments: [],
    ratings: null,
    newComment: "",
    newRating: 0,
    loading: true,
    submitting: false,
    error: null,
    success: null,

    async init() {
      const appEl = document.querySelector("body");
      const appData = appEl._x_dataStack?.[0];
      const courseId = appData?.currentParams?.id;
      if (!courseId) { this.loading = false; return; }

      const [cResp, commResp, rResp] = await Promise.all([
        api.get(`/courses/${courseId}`),
        api.get(`/courses/${courseId}/comments`),
        api.get(`/courses/${courseId}/ratings`),
      ]);
      this.course = cResp.data;
      this.comments = commResp.data || [];
      this.ratings = rResp.data;
      this.loading = false;
    },

    async submitComment() {
      if (!this.newComment.trim()) return;
      this.submitting = true;
      const resp = await api.post(`/courses/${this.course.id}/comments`, { body: this.newComment });
      if (resp.ok) {
        this.comments.push(resp.data);
        this.newComment = "";
        this.success = "Comment posted!";
      } else {
        this.error = resp.error;
      }
      this.submitting = false;
    },

    async submitRating(stars) {
      this.newRating = stars;
      const resp = await api.post(`/courses/${this.course.id}/ratings`, { stars });
      if (resp.ok) this.ratings = resp.data;
    },
  };
}
```

- [ ] **Step 2: Replace Courses sections in index.html**

```html
      <!-- COURSES LIST -->
      <div x-show="currentPage === 'courses'" class="page">
        <div x-data="coursesPage()" x-init="init()">
          <h1>Courses</h1>
          <p class="subtitle">Things I've studied.</p>
          <div x-show="loading" class="loading-center"><div class="spinner"></div></div>
          <div x-show="!loading">
            <template x-if="courses.length === 0">
              <p class="subtitle" style="margin-top: 2rem;">No courses yet.</p>
            </template>
            <div class="card-grid">
              <template x-for="c in courses" :key="c.id">
                <a :href="'#/courses/' + c.id" class="card" style="text-decoration: none; display: block;">
                  <h3 x-text="c.title"></h3>
                  <p x-text="c.platform" class="subtitle" style="font-size: 0.85rem; margin: 0.3rem 0;"></p>
                  <p x-text="c.description" class="subtitle" style="font-size: 0.9rem; margin: 0.5rem 0;"></p>
                  <p class="stars" style="font-size: 0.85rem;" x-text="starsDisplay(c.avg_rating)"></p>
                </a>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- COURSE DETAIL -->
      <div x-show="currentPage === 'course-detail'" class="page">
        <div x-data="courseDetailPage()" x-init="init()">
          <div x-show="loading" class="loading-center"><div class="spinner"></div></div>
          <template x-if="!loading && course">
            <div>
              <a href="#/courses" style="font-size: 0.9rem; color: var(--text-muted);">&larr; Back to Courses</a>
              <h1 x-text="course.title" style="margin-top: 1rem;"></h1>
              <p class="subtitle" x-text="course.platform"></p>
              <p x-text="course.description" style="margin: 1rem 0; line-height: 1.8;"></p>
              <template x-if="course.link">
                <a :href="course.link" target="_blank" class="btn btn-outline btn-sm" style="margin-bottom: 2rem;">
                  View course
                </a>
              </template>

              <!-- Ratings (same pattern as project detail) -->
              <div class="card" style="max-width: 320px; margin-bottom: 2rem;">
                <h3>Rating</h3>
                <template x-if="ratings">
                  <p x-text="ratings.count > 0 ? `${ratings.average} / 5 from ${ratings.count} ratings` : 'No ratings yet'"></p>
                </template>
                <div style="margin-top: 0.75rem;">
                  <p style="font-size: 0.85rem; color: var(--text-muted);">Your rating:</p>
                  <div style="display: flex; gap: 0.5rem; font-size: 1.5rem; cursor: pointer;">
                    <template x-for="n in [1,2,3,4,5]" :key="n">
                      <span @click="submitRating(n)"
                            :style="n <= newRating ? 'color: #F5A623;' : 'color: var(--border);'">★</span>
                    </template>
                  </div>
                </div>
              </div>

              <!-- Comments -->
              <h2>Comments (<span x-text="comments.length"></span>)</h2>
              <div style="margin-top: 1rem;">
                <template x-for="c in comments" :key="c.comment_id">
                  <div class="card" style="margin-bottom: 0.75rem;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
                      <strong x-text="c.name"></strong>
                      <span class="badge badge-outline" x-text="c.identity" x-show="c.identity"></span>
                    </div>
                    <p x-text="c.body"></p>
                  </div>
                </template>
              </div>
              <div style="margin-top: 1.5rem;">
                <div x-show="error" class="alert alert-error" x-text="error"></div>
                <div x-show="success" class="alert alert-success" x-text="success"></div>
                <textarea x-model="newComment" class="form-input" rows="3" placeholder="Leave a comment..."></textarea>
                <button class="btn btn-primary" style="margin-top: 0.5rem;" @click="submitComment()" :disabled="submitting">
                  <span x-text="submitting ? 'Posting...' : 'Post comment'"></span>
                </button>
              </div>
            </div>
          </template>
        </div>
      </div>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/assets/js/pages/courses.js frontend/index.html
git commit -m "feat: implement Courses list and course detail pages"
```

---

### Task 10: Skills page

**Files:**
- Modify: `frontend/assets/js/pages/skills.js`
- Modify: `frontend/index.html` (Skills section)

- [ ] **Step 1: Replace skills.js**

```javascript
// frontend/assets/js/pages/skills.js
function skillsPage() {
  return {
    skills: null,
    loading: true,
    async init() {
      const resp = await api.get("/skills");
      this.skills = resp.data;
      this.loading = false;
    },
    categories() {
      if (!this.skills) return [];
      return Object.keys(this.skills).filter(k => Array.isArray(this.skills[k]));
    },
  };
}
```

- [ ] **Step 2: Replace Skills section in index.html**

```html
      <!-- SKILLS -->
      <div x-show="currentPage === 'skills'" class="page">
        <div x-data="skillsPage()" x-init="init()">
          <h1>Skills</h1>
          <p class="subtitle">My technical toolkit.</p>
          <div x-show="loading" class="loading-center"><div class="spinner"></div></div>
          <template x-if="!loading && skills">
            <div style="margin-top: 2rem;">
              <template x-for="cat in categories()" :key="cat">
                <div style="margin-bottom: 2rem;">
                  <h2 style="text-transform: capitalize;" x-text="cat.replace('_', ' ')"></h2>
                  <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.75rem;">
                    <template x-for="skill in skills[cat]" :key="skill">
                      <span class="badge" x-text="skill"></span>
                    </template>
                  </div>
                </div>
              </template>
            </div>
          </template>
          <template x-if="!loading && !skills">
            <p class="subtitle" style="margin-top: 2rem;">Skills coming soon.</p>
          </template>
        </div>
      </div>
```

- [ ] **Step 3: Commit + merge to dev**

```bash
git add frontend/assets/js/pages/skills.js frontend/index.html
git commit -m "feat: implement Skills page"
git checkout dev
git merge feature/public-pages
git push origin dev
```

---

## Feature Branch: `feature/interactive-pages`

> Covers: Stats (Leaflet.js visitor map), Contact, Guestbook, Testimonials

```bash
git checkout dev
git checkout -b feature/interactive-pages
```

---

### Task 11: Stats page (visitor map)

**Files:**
- Modify: `frontend/assets/js/pages/stats.js`
- Modify: `frontend/index.html` (Stats section + Leaflet CDN link)

- [ ] **Step 1: Add Leaflet.js to index.html head**

Add inside `<head>` after the favicon line:
```html
  <!-- Leaflet.js (visitor map) — loaded only when needed -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
```

- [ ] **Step 2: Replace stats.js**

```javascript
// frontend/assets/js/pages/stats.js
function statsPage() {
  return {
    locations: [],
    total: 0,
    loading: true,
    map: null,

    async init() {
      const resp = await api.get("/stats/visitors");
      this.locations = resp.data || [];
      this.total = this.locations.length;
      this.loading = false;
      // Wait for DOM to render the map container
      await this.$nextTick();
      this.initMap();
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
            fillColor: getComputedStyle(document.documentElement).getPropertyValue("--accent").trim() || "#007BFF",
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
    },
  };
}
```

- [ ] **Step 3: Replace Stats section in index.html**

```html
      <!-- STATS -->
      <div x-show="currentPage === 'stats'" class="page" x-data="statsPage()"
           x-init="init()" @hashchange.window="destroy()">
        <h1>Visitor Map</h1>
        <p class="subtitle">People who've visited from around the world.</p>
        <div x-show="loading" class="loading-center"><div class="spinner"></div></div>
        <template x-if="!loading">
          <div>
            <p style="margin: 0.75rem 0; color: var(--text-muted);" x-text="`${total} visit locations recorded`"></p>
            <div id="visitor-map" style="height: 420px; border-radius: 10px; border: 1px solid var(--border); margin-top: 1rem;"></div>
          </div>
        </template>
      </div>
```

- [ ] **Step 4: Verify map loads**

Open `http://localhost:8080` → navigate to Stats. Map should render with OpenStreetMap tiles. No JS errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/assets/js/pages/stats.js frontend/index.html
git commit -m "feat: implement Stats page with Leaflet.js visitor map"
```

---

### Task 12: Contact page

**Files:**
- Modify: `frontend/assets/js/pages/contact.js`
- Modify: `frontend/index.html` (Contact section)

- [ ] **Step 1: Replace contact.js**

```javascript
// frontend/assets/js/pages/contact.js
function contactPage() {
  return {
    about: null,
    form: { name: "", email: "", message: "" },
    submitting: false,
    error: null,
    success: null,

    async init() {
      const resp = await api.get("/about");
      this.about = resp.data;
    },

    async submitForm() {
      this.error = null;
      this.success = null;
      if (!this.form.name || !this.form.email || !this.form.message) {
        this.error = "All fields are required.";
        return;
      }
      this.submitting = true;
      const resp = await api.post("/contact", this.form);
      if (resp.ok) {
        this.success = resp.data?.message || "Message sent!";
        this.form = { name: "", email: "", message: "" };
      } else {
        this.error = resp.error || "Something went wrong. Please try again.";
      }
      this.submitting = false;
    },
  };
}
```

- [ ] **Step 2: Replace Contact section in index.html**

```html
      <!-- CONTACT -->
      <div x-show="currentPage === 'contact'" class="page">
        <div x-data="contactPage()" x-init="init()">
          <h1>Contact</h1>
          <p class="subtitle">Get in touch.</p>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-top: 2rem;">
            <!-- Contact details -->
            <div>
              <h2>Details</h2>
              <template x-if="about?.contact">
                <div style="margin-top: 1rem;">
                  <template x-if="about.contact.email">
                    <p style="margin-bottom: 0.75rem;">
                      <strong>Email:</strong>
                      <a :href="'mailto:' + about.contact.email" x-text="about.contact.email"></a>
                    </p>
                  </template>
                  <template x-if="about.contact.location">
                    <p style="margin-bottom: 0.75rem;">
                      <strong>Location:</strong> <span x-text="about.contact.location"></span>
                    </p>
                  </template>
                </div>
              </template>
              <template x-if="about?.social_links">
                <div style="margin-top: 1rem; display: flex; gap: 0.75rem; flex-wrap: wrap;">
                  <template x-if="about.social_links.github">
                    <a :href="about.social_links.github" target="_blank" class="btn btn-outline btn-sm">GitHub</a>
                  </template>
                  <template x-if="about.social_links.linkedin">
                    <a :href="about.social_links.linkedin" target="_blank" class="btn btn-outline btn-sm">LinkedIn</a>
                  </template>
                </div>
              </template>
            </div>

            <!-- Contact form -->
            <div>
              <h2>Send a message</h2>
              <div x-show="error" class="alert alert-error" x-text="error"></div>
              <div x-show="success" class="alert alert-success" x-text="success"></div>
              <form @submit.prevent="submitForm()" style="margin-top: 1rem;">
                <div class="form-group">
                  <label>Name</label>
                  <input x-model="form.name" class="form-input" type="text" placeholder="Your name" required>
                </div>
                <div class="form-group">
                  <label>Email</label>
                  <input x-model="form.email" class="form-input" type="email" placeholder="your@email.com" required>
                </div>
                <div class="form-group">
                  <label>Message</label>
                  <textarea x-model="form.message" class="form-input" rows="5" placeholder="Your message..." required></textarea>
                </div>
                <button type="submit" class="btn btn-primary" :disabled="submitting">
                  <span x-text="submitting ? 'Sending...' : 'Send message'"></span>
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/assets/js/pages/contact.js frontend/index.html
git commit -m "feat: implement Contact page (contact details + rate-limited form)"
```

---

### Task 13: Guestbook page

**Files:**
- Modify: `frontend/assets/js/pages/guestbook.js`
- Modify: `frontend/index.html` (Guestbook section)

- [ ] **Step 1: Replace guestbook.js**

```javascript
// frontend/assets/js/pages/guestbook.js
function guestbookPage() {
  return {
    entries: [],
    form: { name: "", message: "" },
    loading: true,
    submitting: false,
    error: null,
    success: null,

    async init() {
      const resp = await api.get("/guestbook");
      this.entries = resp.data || [];
      this.loading = false;
    },

    async submit() {
      this.error = null;
      this.success = null;
      if (!this.form.name || !this.form.message) {
        this.error = "Name and message are required.";
        return;
      }
      this.submitting = true;
      const resp = await api.post("/guestbook", this.form);
      if (resp.ok) {
        this.entries.unshift(resp.data);
        this.form = { name: "", message: "" };
        this.success = "Entry added!";
      } else {
        this.error = resp.error;
      }
      this.submitting = false;
    },

    formatDate(ts) {
      return ts ? new Date(ts * 1000).toLocaleDateString() : "";
    },
  };
}
```

- [ ] **Step 2: Replace Guestbook section in index.html**

```html
      <!-- GUESTBOOK -->
      <div x-show="currentPage === 'guestbook'" class="page">
        <div x-data="guestbookPage()" x-init="init()">
          <h1>Guestbook</h1>
          <p class="subtitle">Say hello — everyone's welcome.</p>

          <!-- Submit form -->
          <div class="card" style="max-width: 500px; margin-top: 1.5rem;">
            <h3>Leave a message</h3>
            <div x-show="error" class="alert alert-error" x-text="error" style="margin-top: 0.75rem;"></div>
            <div x-show="success" class="alert alert-success" x-text="success" style="margin-top: 0.75rem;"></div>
            <div class="form-group" style="margin-top: 0.75rem;">
              <label>Name</label>
              <input x-model="form.name" class="form-input" placeholder="Your name">
            </div>
            <div class="form-group">
              <label>Message</label>
              <textarea x-model="form.message" class="form-input" rows="3" placeholder="What's on your mind?"></textarea>
            </div>
            <button class="btn btn-primary" @click="submit()" :disabled="submitting">
              <span x-text="submitting ? 'Posting...' : 'Post'"></span>
            </button>
          </div>

          <!-- Entries list -->
          <div x-show="loading" class="loading-center" style="margin-top: 2rem;"><div class="spinner"></div></div>
          <div x-show="!loading" style="margin-top: 2rem;">
            <template x-if="entries.length === 0">
              <p class="subtitle">No entries yet. Be the first!</p>
            </template>
            <template x-for="entry in entries" :key="entry.entry_id">
              <div class="card" style="margin-bottom: 0.75rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                  <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <strong x-text="entry.name"></strong>
                    <span class="badge badge-outline" x-text="entry.identity" x-show="entry.identity"></span>
                  </div>
                  <span style="font-size: 0.8rem; color: var(--text-muted);" x-text="formatDate(entry.created_at)"></span>
                </div>
                <p x-text="entry.message"></p>
              </div>
            </template>
          </div>
        </div>
      </div>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/assets/js/pages/guestbook.js frontend/index.html
git commit -m "feat: implement Guestbook page"
```

---

### Task 14: Testimonials page

**Files:**
- Modify: `frontend/assets/js/pages/testimonials.js`
- Modify: `frontend/index.html` (Testimonials section)

- [ ] **Step 1: Replace testimonials.js**

```javascript
// frontend/assets/js/pages/testimonials.js
function testimonialsPage() {
  return {
    testimonials: [],
    filtered: [],
    activeFilter: "all",
    identities: ["all", "Jamf", "MCRI", "Friend", "Family", "Other"],
    form: { body: "", author: "", identity: "Other", anonymous: false },
    loading: true,
    submitting: false,
    error: null,
    success: null,

    async init() {
      const resp = await api.get("/testimonials");
      this.testimonials = resp.data || [];
      this.filtered = this.testimonials;
      this.loading = false;
    },

    setFilter(identity) {
      this.activeFilter = identity;
      this.filtered = identity === "all"
        ? this.testimonials
        : this.testimonials.filter(t => t.identity === identity);
    },

    async submit() {
      this.error = null;
      this.success = null;
      if (!this.form.body.trim()) {
        this.error = "Please write your testimonial.";
        return;
      }
      this.submitting = true;
      const resp = await api.post("/testimonials", this.form);
      if (resp.ok) {
        this.success = "Thank you! Your testimonial is pending approval.";
        this.form = { body: "", author: "", identity: "Other", anonymous: false };
      } else {
        this.error = resp.error;
      }
      this.submitting = false;
    },
  };
}
```

- [ ] **Step 2: Replace Testimonials section in index.html**

```html
      <!-- TESTIMONIALS -->
      <div x-show="currentPage === 'testimonials'" class="page">
        <div x-data="testimonialsPage()" x-init="init()">
          <h1>Testimonials</h1>
          <p class="subtitle">What people say.</p>

          <!-- Identity filter -->
          <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 1.5rem;">
            <template x-for="identity in identities" :key="identity">
              <button class="btn btn-sm"
                      :class="activeFilter === identity ? 'btn-primary' : 'btn-outline'"
                      @click="setFilter(identity)"
                      x-text="identity === 'all' ? 'All' : identity">
              </button>
            </template>
          </div>

          <!-- Testimonials list -->
          <div x-show="loading" class="loading-center"><div class="spinner"></div></div>
          <div x-show="!loading" style="margin-top: 1.5rem;">
            <template x-if="filtered.length === 0">
              <p class="subtitle">No testimonials yet.</p>
            </template>
            <div class="card-grid">
              <template x-for="t in filtered" :key="t.testimonial_id">
                <div class="card">
                  <p x-text="'&ldquo;' + t.body + '&rdquo;'" style="font-style: italic; margin-bottom: 1rem;"></p>
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong x-text="t.author"></strong>
                    <span class="badge badge-outline" x-text="t.identity" x-show="t.identity"></span>
                  </div>
                </div>
              </template>
            </div>
          </div>

          <!-- Submit form -->
          <div class="card" style="max-width: 500px; margin-top: 2.5rem;">
            <h3>Submit a testimonial</h3>
            <p class="subtitle" style="font-size: 0.85rem; margin-bottom: 1rem;">Pending admin approval before going live.</p>
            <div x-show="error" class="alert alert-error" x-text="error"></div>
            <div x-show="success" class="alert alert-success" x-text="success"></div>
            <div class="form-group">
              <label>Your testimonial</label>
              <textarea x-model="form.body" class="form-input" rows="4" placeholder="What would you like to say?"></textarea>
            </div>
            <div class="form-group" x-show="!form.anonymous">
              <label>Your name (optional)</label>
              <input x-model="form.author" class="form-input" placeholder="Leave blank to be anonymous">
            </div>
            <div class="form-group">
              <label>Identity</label>
              <select x-model="form.identity" class="form-input">
                <option>Jamf</option>
                <option>MCRI</option>
                <option>Friend</option>
                <option>Family</option>
                <option selected>Other</option>
              </select>
            </div>
            <div class="form-group" style="display: flex; align-items: center; gap: 0.5rem;">
              <input type="checkbox" x-model="form.anonymous" id="anon">
              <label for="anon" style="margin: 0; cursor: pointer;">Submit anonymously</label>
            </div>
            <button class="btn btn-primary" @click="submit()" :disabled="submitting">
              <span x-text="submitting ? 'Submitting...' : 'Submit'"></span>
            </button>
          </div>
        </div>
      </div>
```

- [ ] **Step 3: Commit + merge**

```bash
git add frontend/assets/js/pages/testimonials.js frontend/index.html
git commit -m "feat: implement Testimonials page (filter by identity + submit form)"
git checkout dev
git merge feature/interactive-pages
git push origin dev
```

---

## Feature Branch: `feature/auth-flow`

> Covers: Login (email + OAuth buttons + remember me), Register (identity picker), Verify Email, auth state

```bash
git checkout dev
git checkout -b feature/auth-flow
```

---

### Task 15: Login page

**Files:**
- Modify: `frontend/assets/js/pages/login.js`
- Modify: `frontend/index.html` (Login section)

- [ ] **Step 1: Replace login.js**

```javascript
// frontend/assets/js/pages/login.js
function loginPage() {
  return {
    form: { email: "", password: "", remember_me: false },
    submitting: false,
    error: null,

    async init() {
      // Redirect if already logged in
      const token = localStorage.getItem("access_token");
      if (token) window.location.hash = "#/";
    },

    async submit() {
      this.error = null;
      if (!this.form.email || !this.form.password) {
        this.error = "Email and password are required.";
        return;
      }
      this.submitting = true;
      // Call the parent app's login method
      const app = document.querySelector("[x-data]")._x_dataStack?.[0];
      const result = app
        ? await app.login(this.form.email, this.form.password, this.form.remember_me)
        : await api.post("/auth/login", { email: this.form.email, password: this.form.password, remember_me: this.form.remember_me });

      if (result?.ok || result?.data?.access_token) {
        // Redirect to previous page or home
        const returnTo = sessionStorage.getItem("returnTo") || "#/";
        sessionStorage.removeItem("returnTo");
        window.location.hash = returnTo.replace(/^#/, "");
      } else {
        this.error = result?.error || "Invalid email or password.";
      }
      this.submitting = false;
    },

    loginWithGithub() {
      // Redirect to Lambda OAuth init endpoint
      window.location.href = `${API_BASE}/auth/oauth/github`;
    },

    loginWithGoogle() {
      window.location.href = `${API_BASE}/auth/oauth/google`;
    },
  };
}
```

- [ ] **Step 2: Replace Login section in index.html**

```html
      <!-- LOGIN -->
      <div x-show="currentPage === 'login'" class="page">
        <div x-data="loginPage()" x-init="init()">
          <div style="max-width: 400px; margin: 3rem auto;">
            <h1>Login</h1>
            <p class="subtitle">Welcome back.</p>

            <div x-show="error" class="alert alert-error" style="margin-top: 1rem;" x-text="error"></div>

            <!-- OAuth buttons -->
            <div style="margin-top: 1.5rem; display: flex; flex-direction: column; gap: 0.75rem;">
              <button class="btn btn-outline" @click="loginWithGithub()" style="display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
                Continue with GitHub
              </button>
              <button class="btn btn-outline" @click="loginWithGoogle()" style="display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                <svg width="16" height="16" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
                Continue with Google
              </button>
            </div>

            <div style="display: flex; align-items: center; gap: 1rem; margin: 1.25rem 0; color: var(--text-muted);">
              <div style="flex: 1; height: 1px; background: var(--border);"></div>
              <span style="font-size: 0.85rem;">or</span>
              <div style="flex: 1; height: 1px; background: var(--border);"></div>
            </div>

            <!-- Email/password form -->
            <form @submit.prevent="submit()">
              <div class="form-group">
                <label>Email</label>
                <input x-model="form.email" type="email" class="form-input" placeholder="you@example.com" required>
              </div>
              <div class="form-group">
                <label>Password</label>
                <input x-model="form.password" type="password" class="form-input" placeholder="••••••••" required>
              </div>
              <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
                <input type="checkbox" x-model="form.remember_me" id="remember">
                <label for="remember" style="margin: 0; cursor: pointer; font-size: 0.9rem;">Remember me (7 days)</label>
              </div>
              <button type="submit" class="btn btn-primary" style="width: 100%;" :disabled="submitting">
                <span x-text="submitting ? 'Logging in...' : 'Log in'"></span>
              </button>
            </form>

            <p style="text-align: center; margin-top: 1rem; font-size: 0.9rem; color: var(--text-muted);">
              Don't have an account? <a href="#/register">Sign up</a>
            </p>
          </div>
        </div>
      </div>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/assets/js/pages/login.js frontend/index.html
git commit -m "feat: implement Login page (email/password + GitHub/Google OAuth + remember me)"
```

---

### Task 16: Register page

**Files:**
- Modify: `frontend/assets/js/pages/register.js`
- Modify: `frontend/index.html` (Register section)

- [ ] **Step 1: Replace register.js**

```javascript
// frontend/assets/js/pages/register.js
function registerPage() {
  return {
    form: { name: "", email: "", password: "", identity: "Other" },
    identities: ["Jamf", "MCRI", "Friend", "Family", "Other"],
    submitting: false,
    error: null,
    success: null,

    async init() {
      const token = localStorage.getItem("access_token");
      if (token) window.location.hash = "#/";
    },

    async submit() {
      this.error = null;
      this.success = null;
      if (!this.form.name || !this.form.email || !this.form.password) {
        this.error = "All fields are required.";
        return;
      }
      if (this.form.password.length < 8) {
        this.error = "Password must be at least 8 characters.";
        return;
      }
      this.submitting = true;
      const resp = await api.post("/auth/register", this.form);
      if (resp.ok) {
        this.success = "Account created! Check your email to verify your account.";
        this.form = { name: "", email: "", password: "", identity: "Other" };
      } else {
        this.error = resp.error;
      }
      this.submitting = false;
    },
  };
}
```

- [ ] **Step 2: Replace Register section in index.html**

```html
      <!-- REGISTER -->
      <div x-show="currentPage === 'register'" class="page">
        <div x-data="registerPage()" x-init="init()">
          <div style="max-width: 420px; margin: 3rem auto;">
            <h1>Create account</h1>
            <p class="subtitle">Join and unlock interactive features.</p>

            <div x-show="error" class="alert alert-error" style="margin-top: 1rem;" x-text="error"></div>
            <div x-show="success" class="alert alert-success" style="margin-top: 1rem;" x-text="success"></div>

            <form @submit.prevent="submit()" style="margin-top: 1.5rem;" x-show="!success">
              <div class="form-group">
                <label>Name</label>
                <input x-model="form.name" class="form-input" placeholder="Your name" required>
              </div>
              <div class="form-group">
                <label>Email</label>
                <input x-model="form.email" type="email" class="form-input" placeholder="you@example.com" required>
              </div>
              <div class="form-group">
                <label>Password</label>
                <input x-model="form.password" type="password" class="form-input" placeholder="Min. 8 characters" required>
              </div>

              <!-- Identity picker -->
              <div class="form-group">
                <label>How do you know me?</label>
                <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.4rem;">
                  <template x-for="id in identities" :key="id">
                    <button type="button"
                            class="btn btn-sm"
                            :class="form.identity === id ? 'btn-primary' : 'btn-outline'"
                            @click="form.identity = id"
                            x-text="id">
                    </button>
                  </template>
                </div>
              </div>

              <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 0.5rem;" :disabled="submitting">
                <span x-text="submitting ? 'Creating account...' : 'Create account'"></span>
              </button>
            </form>

            <p style="text-align: center; margin-top: 1rem; font-size: 0.9rem; color: var(--text-muted);">
              Already have an account? <a href="#/login">Log in</a>
            </p>
          </div>
        </div>
      </div>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/assets/js/pages/register.js frontend/index.html
git commit -m "feat: implement Register page (identity picker + email registration)"
```

---

### Task 17: Verify Email page

**Files:**
- Modify: `frontend/assets/js/pages/verify-email.js`
- Modify: `frontend/index.html` (Verify Email section)

- [ ] **Step 1: Replace verify-email.js**

```javascript
// frontend/assets/js/pages/verify-email.js
function verifyEmailPage() {
  return {
    status: "loading",  // loading | success | error
    message: "",

    async init() {
      // Token comes from URL query string: /verify-email?token=xxx
      // With hash routing it arrives as: #/verify-email?token=xxx
      const hash = window.location.hash;
      const queryStart = hash.indexOf("?");
      const token = queryStart >= 0
        ? new URLSearchParams(hash.slice(queryStart)).get("token")
        : null;

      if (!token) {
        this.status = "error";
        this.message = "No verification token found in URL.";
        return;
      }

      const resp = await api.post("/auth/verify-email", { token });
      if (resp.ok) {
        this.status = "success";
        this.message = resp.data?.message || "Email verified! You can now log in.";
        // Auto-redirect to login after 3s
        setTimeout(() => { window.location.hash = "#/login"; }, 3000);
      } else {
        this.status = "error";
        this.message = resp.error || "Verification failed. The link may have expired.";
      }
    },
  };
}
```

- [ ] **Step 2: Replace Verify Email section in index.html**

```html
      <!-- VERIFY EMAIL -->
      <div x-show="currentPage === 'verify-email'" class="page">
        <div x-data="verifyEmailPage()" x-init="init()">
          <div style="max-width: 400px; margin: 4rem auto; text-align: center;">
            <div x-show="status === 'loading'" class="loading-center"><div class="spinner"></div></div>
            <div x-show="status === 'success'">
              <div style="font-size: 3rem;">✓</div>
              <h1 style="margin-top: 1rem;">Email verified!</h1>
              <p class="subtitle" x-text="message"></p>
              <p style="margin-top: 0.5rem; font-size: 0.85rem; color: var(--text-muted);">Redirecting to login...</p>
            </div>
            <div x-show="status === 'error'">
              <div style="font-size: 3rem;">✗</div>
              <h1 style="margin-top: 1rem;">Verification failed</h1>
              <p class="subtitle" x-text="message"></p>
              <a href="#/register" class="btn btn-primary" style="margin-top: 1rem; display: inline-block;">Register again</a>
            </div>
          </div>
        </div>
      </div>
```

- [ ] **Step 3: Commit + merge**

```bash
git add frontend/assets/js/pages/verify-email.js frontend/assets/js/pages/register.js frontend/index.html
git commit -m "feat: implement Verify Email page (token from URL, auto-redirect on success)"
git checkout dev
git merge feature/auth-flow
git push origin dev
```

---

## Feature Branch: `feature/authenticated-pages`

> Covers: Quiz (20 questions, scoring, leaderboard) — visible only when logged in

```bash
git checkout dev
git checkout -b feature/authenticated-pages
```

---

### Task 18: Quiz page

**Files:**
- Modify: `frontend/assets/js/pages/quiz.js`
- Modify: `frontend/index.html` (Quiz section)

- [ ] **Step 1: Replace quiz.js**

```javascript
// frontend/assets/js/pages/quiz.js
function quizPage() {
  return {
    // States: "loading" | "start" | "playing" | "result" | "leaderboard"
    state: "loading",
    questions: [],
    answers: {},        // { question_id: selected_option }
    current: 0,
    result: null,
    leaderboard: [],
    loadingLeaderboard: false,
    submitting: false,
    error: null,

    async init() {
      const resp = await api.get("/quiz/questions");
      if (!resp.ok) {
        this.error = resp.error || "Could not load questions.";
        this.state = "start";
        return;
      }
      this.questions = resp.data || [];
      this.state = "start";
    },

    startQuiz() {
      this.answers = {};
      this.current = 0;
      this.result = null;
      this.error = null;
      this.state = "playing";
    },

    selectAnswer(questionId, option) {
      this.answers[questionId] = option;
    },

    isAnswered(questionId) {
      return questionId in this.answers;
    },

    get allAnswered() {
      return this.questions.every(q => this.isAnswered(q.question_id));
    },

    get progress() {
      return Math.round((Object.keys(this.answers).length / this.questions.length) * 100);
    },

    async submitQuiz() {
      if (!this.allAnswered) {
        this.error = "Please answer all questions before submitting.";
        return;
      }
      this.submitting = true;
      const resp = await api.post("/quiz/submit", { answers: this.answers });
      if (resp.ok) {
        this.result = resp.data;
        this.state = "result";
      } else {
        this.error = resp.error;
      }
      this.submitting = false;
    },

    async showLeaderboard() {
      this.state = "leaderboard";
      this.loadingLeaderboard = true;
      const resp = await api.get("/quiz/leaderboard");
      this.leaderboard = resp.data || [];
      this.loadingLeaderboard = false;
    },

    get scorePercent() {
      if (!this.result) return 0;
      return Math.round((this.result.score / this.result.total) * 100);
    },

    scoreMessage() {
      const p = this.scorePercent;
      if (p === 100) return "Perfect score!";
      if (p >= 80)  return "Great work!";
      if (p >= 60)  return "Not bad!";
      if (p >= 40)  return "Keep practicing!";
      return "Better luck next time!";
    },
  };
}
```

- [ ] **Step 2: Replace Quiz section in index.html**

```html
      <!-- QUIZ (auth required) -->
      <div x-show="currentPage === 'quiz'" class="page">
        <template x-if="!isAuthenticated">
          <div style="text-align: center; padding: 4rem 0;">
            <h1>Quiz</h1>
            <p class="subtitle">Log in to take the quiz and compete on the leaderboard.</p>
            <a href="#/login" class="btn btn-primary" style="margin-top: 1.5rem; display: inline-block;">Log in</a>
          </div>
        </template>
        <template x-if="isAuthenticated">
          <div x-data="quizPage()" x-init="init()">

            <!-- Loading -->
            <div x-show="state === 'loading'" class="loading-center"><div class="spinner"></div></div>

            <!-- Start screen -->
            <div x-show="state === 'start'" style="text-align: center; padding: 3rem 0;">
              <h1>Quiz</h1>
              <p class="subtitle" x-text="`${questions.length} questions · Test your knowledge`"></p>
              <div x-show="error" class="alert alert-error" style="max-width: 400px; margin: 1rem auto;" x-text="error"></div>
              <button class="btn btn-primary" style="margin-top: 1.5rem;" @click="startQuiz()" x-show="questions.length > 0">
                Start Quiz
              </button>
              <button class="btn btn-outline" style="margin-top: 1rem; display: block; margin-left: auto; margin-right: auto;" @click="showLeaderboard()">
                View Leaderboard
              </button>
            </div>

            <!-- Playing -->
            <div x-show="state === 'playing'">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h1>Quiz</h1>
                <span class="subtitle" x-text="`${Object.keys(answers).length} / ${questions.length} answered`"></span>
              </div>

              <!-- Progress bar -->
              <div style="height: 6px; background: var(--border); border-radius: 3px; margin-bottom: 2rem;">
                <div :style="`width: ${progress}%; background: var(--accent); height: 100%; border-radius: 3px; transition: width 0.3s;`"></div>
              </div>

              <div x-show="error" class="alert alert-error" x-text="error"></div>

              <!-- Questions -->
              <div style="display: flex; flex-direction: column; gap: 1.5rem;">
                <template x-for="(q, idx) in questions" :key="q.question_id">
                  <div class="card">
                    <p style="font-weight: 600; margin-bottom: 1rem;">
                      <span x-text="idx + 1 + '. '"></span>
                      <span x-text="q.question"></span>
                    </p>
                    <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                      <template x-for="option in q.options" :key="option">
                        <button class="btn"
                                :class="answers[q.question_id] === option ? 'btn-primary' : 'btn-outline'"
                                style="text-align: left; justify-content: flex-start;"
                                @click="selectAnswer(q.question_id, option)"
                                x-text="option">
                        </button>
                      </template>
                    </div>
                  </div>
                </template>
              </div>

              <div style="margin-top: 2rem; display: flex; justify-content: flex-end;">
                <button class="btn btn-primary"
                        @click="submitQuiz()"
                        :disabled="!allAnswered || submitting">
                  <span x-text="submitting ? 'Submitting...' : 'Submit Quiz'"></span>
                </button>
              </div>
            </div>

            <!-- Result -->
            <div x-show="state === 'result'" style="text-align: center; padding: 3rem 0;">
              <div style="font-size: 3rem;" x-text="scorePercent === 100 ? '🏆' : scorePercent >= 80 ? '🎉' : '📝'"></div>
              <h1 x-text="scoreMessage()" style="margin-top: 1rem;"></h1>
              <template x-if="result">
                <div>
                  <p class="subtitle" style="font-size: 1.2rem; margin-top: 0.5rem;">
                    <span x-text="result.score"></span> / <span x-text="result.total"></span>
                    (<span x-text="scorePercent"></span>%)
                  </p>
                  <div style="height: 12px; background: var(--border); border-radius: 6px; max-width: 300px; margin: 1.5rem auto;">
                    <div :style="`width: ${scorePercent}%; background: var(--accent); height: 100%; border-radius: 6px; transition: width 1s;`"></div>
                  </div>
                </div>
              </template>
              <div style="display: flex; gap: 1rem; justify-content: center; margin-top: 1.5rem;">
                <button class="btn btn-outline" @click="startQuiz()">Try again</button>
                <button class="btn btn-primary" @click="showLeaderboard()">Leaderboard</button>
              </div>
            </div>

            <!-- Leaderboard -->
            <div x-show="state === 'leaderboard'">
              <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem;">
                <h1>Leaderboard</h1>
                <button class="btn btn-outline btn-sm" @click="state = 'start'">&larr; Back</button>
              </div>
              <div x-show="loadingLeaderboard" class="loading-center"><div class="spinner"></div></div>
              <template x-if="!loadingLeaderboard">
                <div>
                  <template x-if="leaderboard.length === 0">
                    <p class="subtitle">No scores yet. Be the first!</p>
                  </template>
                  <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                    <template x-for="(entry, idx) in leaderboard" :key="entry.attempt_id">
                      <div class="card" style="display: flex; align-items: center; justify-content: space-between;">
                        <div style="display: flex; align-items: center; gap: 1rem;">
                          <span style="font-size: 1.2rem; width: 2rem; text-align: center;"
                                x-text="idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : (idx + 1) + '.'">
                          </span>
                          <span x-text="entry.user_id"></span>
                        </div>
                        <span style="font-weight: 700; color: var(--accent);"
                              x-text="`${entry.score} / ${entry.total}`">
                        </span>
                      </div>
                    </template>
                  </div>
                </div>
              </template>
            </div>

          </div>
        </template>
      </div>
```

- [ ] **Step 3: Commit + merge**

```bash
git add frontend/assets/js/pages/quiz.js frontend/index.html
git commit -m "feat: implement Quiz page (20 questions, scoring, progress bar, leaderboard)"
git checkout dev
git merge feature/authenticated-pages
git push origin dev
```

---

## Feature Branch: `feature/admin-panel`

> Covers: admin.html — Content editor, Users, Contacts, Testimonials queue, Quiz manager, Developer page

```bash
git checkout dev
git checkout -b feature/admin-panel
```

---

### Task 19: admin.html + navigation

**Files:**
- Create: `frontend/admin.html`

- [ ] **Step 1: Create admin.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Admin — Ron Harifiyati</title>
  <link rel="stylesheet" href="/assets/css/theme.css">
  <link rel="stylesheet" href="/assets/css/main.css">
  <link rel="icon" href="/assets/images/favicon.ico">
  <style>
    .admin-layout { display: flex; min-height: 100vh; }
    .admin-sidebar {
      width: 220px; flex-shrink: 0;
      background: var(--bg-alt);
      border-right: 1px solid var(--border);
      padding: 1.5rem 1rem;
    }
    .admin-sidebar h2 { font-size: 1rem; margin-bottom: 1.5rem; color: var(--text-muted); }
    .admin-sidebar a {
      display: block; padding: 0.5rem 0.75rem;
      border-radius: 6px; margin-bottom: 0.25rem;
      color: var(--text-muted); font-size: 0.9rem;
    }
    .admin-sidebar a:hover, .admin-sidebar a.active {
      background: var(--accent); color: #fff; text-decoration: none;
    }
    .admin-content { flex: 1; padding: 2rem; overflow-y: auto; }
  </style>
</head>
<body>
  <div x-data="adminApp()" x-init="init()">

    <!-- Auth guard -->
    <template x-if="!isAdmin && !loading">
      <div style="text-align: center; padding: 4rem;">
        <h1>Access denied</h1>
        <p class="subtitle">Admin access required.</p>
        <a href="/index.html#/login" class="btn btn-primary" style="display: inline-block; margin-top: 1rem;">Log in</a>
      </div>
    </template>

    <div x-show="loading" class="loading-center" style="height: 100vh;"><div class="spinner"></div></div>

    <template x-if="isAdmin">
      <div class="admin-layout">

        <!-- Sidebar -->
        <aside class="admin-sidebar">
          <h2>Admin Panel</h2>
          <a href="#/dashboard"   :class="{ active: section === 'dashboard' }"   @click.prevent="section='dashboard'">Dashboard</a>
          <a href="#/content"     :class="{ active: section === 'content' }"     @click.prevent="section='content'">Content</a>
          <a href="#/users"       :class="{ active: section === 'users' }"       @click.prevent="section='users'">Users</a>
          <a href="#/contacts"    :class="{ active: section === 'contacts' }"    @click.prevent="section='contacts'">Contacts</a>
          <a href="#/testimonials":class="{ active: section === 'testimonials' }" @click.prevent="section='testimonials'">Testimonials</a>
          <a href="#/quiz"        :class="{ active: section === 'quiz' }"        @click.prevent="section='quiz'">Quiz</a>
          <hr style="border: none; border-top: 1px solid var(--border); margin: 1rem 0;">
          <a href="/index.html" style="color: var(--text-muted);">&larr; Back to site</a>
        </aside>

        <!-- Main content area -->
        <main class="admin-content">

          <!-- Dashboard -->
          <div x-show="section === 'dashboard'">
            <h1>Dashboard</h1>
            <p class="subtitle">Welcome back, <span x-text="user?.name"></span>.</p>
            <div class="card-grid" style="margin-top: 1.5rem; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));">
              <div class="card" style="text-align: center; cursor: pointer;" @click="section='users'">
                <div style="font-size: 2rem;" x-text="stats.users || '—'"></div>
                <p class="subtitle">Users</p>
              </div>
              <div class="card" style="text-align: center; cursor: pointer;" @click="section='contacts'">
                <div style="font-size: 2rem;" x-text="stats.contacts || '—'"></div>
                <p class="subtitle">Contacts</p>
              </div>
              <div class="card" style="text-align: center; cursor: pointer;" @click="section='testimonials'">
                <div style="font-size: 2rem;" x-text="stats.pending_testimonials || '—'"></div>
                <p class="subtitle">Pending testimonials</p>
              </div>
            </div>
          </div>

          <!-- Content editor (see Task 20) -->
          <div x-show="section === 'content'" x-data="adminContent()" x-init="init()">
            <!-- populated in Task 20 -->
            <h1>Content</h1>
            <div class="loading-center"><div class="spinner"></div></div>
          </div>

          <!-- Users (see Task 21) -->
          <div x-show="section === 'users'" x-data="adminUsers()" x-init="init()">
            <h1>Users</h1>
            <div class="loading-center"><div class="spinner"></div></div>
          </div>

          <!-- Contacts (see Task 22) -->
          <div x-show="section === 'contacts'" x-data="adminContacts()" x-init="init()">
            <h1>Contacts</h1>
            <div class="loading-center"><div class="spinner"></div></div>
          </div>

          <!-- Testimonials (see Task 23) -->
          <div x-show="section === 'testimonials'" x-data="adminTestimonials()" x-init="init()">
            <h1>Testimonials</h1>
            <div class="loading-center"><div class="spinner"></div></div>
          </div>

          <!-- Quiz (see Task 24) -->
          <div x-show="section === 'quiz'" x-data="adminQuiz()" x-init="init()">
            <h1>Quiz Questions</h1>
            <div class="loading-center"><div class="spinner"></div></div>
          </div>

        </main>
      </div>
    </template>
  </div>

  <script src="/assets/js/api.js"></script>
  <script src="/assets/js/themes.js"></script>
  <script src="/assets/js/admin-app.js"></script>
  <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
</body>
</html>
```

- [ ] **Step 2: Create frontend/assets/js/admin-app.js**

```javascript
// frontend/assets/js/admin-app.js

function adminApp() {
  return {
    user: null,
    loading: true,
    section: "dashboard",
    stats: {},

    async init() {
      loadTheme();
      const token = localStorage.getItem("access_token");
      if (!token) { this.loading = false; return; }
      const resp = await api.get("/auth/me");
      if (resp.ok && resp.data?.role === "admin") {
        this.user = resp.data;
        await this.loadStats();
      }
      this.loading = false;
    },

    get isAdmin() { return this.user?.role === "admin"; },

    async loadStats() {
      const [users, contacts, testimonials] = await Promise.all([
        api.get("/admin/users"),
        api.get("/admin/contacts"),
        api.get("/admin/testimonials/pending"),
      ]);
      this.stats = {
        users: users.data?.length || 0,
        contacts: contacts.data?.length || 0,
        pending_testimonials: testimonials.data?.length || 0,
      };
    },
  };
}

// ── Section components ────────────────────────────────────────────────────

function adminContent() {
  return {
    activeTab: "about",
    about: {},
    skills: {},
    funFacts: { facts: [] },
    currentlyLearning: { items: [] },
    saving: false,
    success: null,

    async init() {
      const [a, s, f, c] = await Promise.all([
        api.get("/about"), api.get("/skills"), api.get("/fun-fact"), api.get("/currently-learning"),
      ]);
      this.about = a.data || {};
      this.skills = s.data || {};
      this.funFacts = { facts: [] };
      this.currentlyLearning = c.data || { items: [] };
    },

    async save(section, data) {
      this.saving = true; this.success = null;
      const resp = await api.put(`/${section}`, data);
      if (resp.ok) this.success = `${section} saved!`;
      this.saving = false;
    },
  };
}

function adminUsers() {
  return {
    users: [],
    loading: true,

    async init() {
      const resp = await api.get("/admin/users");
      this.users = resp.data || [];
      this.loading = false;
    },

    async setStatus(userId, status) {
      await api.put(`/admin/users/${userId}`, { status });
      const u = this.users.find(u => u.user_id === userId);
      if (u) u.status = status;
    },

    async deleteUser(userId) {
      if (!confirm("Delete this user? This cannot be undone.")) return;
      await api.delete(`/admin/users/${userId}`);
      this.users = this.users.filter(u => u.user_id !== userId);
    },
  };
}

function adminContacts() {
  return {
    contacts: [],
    loading: true,
    async init() {
      const resp = await api.get("/admin/contacts");
      this.contacts = resp.data || [];
      this.loading = false;
    },
    formatDate(ts) { return ts ? new Date(ts * 1000).toLocaleString() : ""; },
  };
}

function adminTestimonials() {
  return {
    pending: [],
    loading: true,

    async init() {
      const resp = await api.get("/admin/testimonials/pending");
      this.pending = resp.data || [];
      this.loading = false;
    },

    async action(id, action) {
      await api.put(`/admin/testimonials/${id}`, { action });
      this.pending = this.pending.filter(t => t.testimonial_id !== id);
    },
  };
}

function adminQuiz() {
  return {
    questions: [],
    loading: true,
    form: { question: "", options: ["", "", "", ""], answer: "", topic: "general" },
    editing: null,
    saving: false,
    error: null,

    async init() {
      const resp = await api.get("/admin/quiz/questions");
      this.questions = resp.data || [];
      this.loading = false;
    },

    async save() {
      this.error = null;
      if (!this.form.question || !this.form.answer) {
        this.error = "Question and answer are required."; return;
      }
      this.saving = true;
      const resp = this.editing
        ? await api.put(`/admin/quiz/questions/${this.editing}`, this.form)
        : await api.post("/admin/quiz/questions", this.form);
      if (resp.ok) {
        const resp2 = await api.get("/admin/quiz/questions");
        this.questions = resp2.data || [];
        this.resetForm();
      } else {
        this.error = resp.error;
      }
      this.saving = false;
    },

    editQuestion(q) {
      this.editing = q.question_id;
      this.form = { question: q.question, options: [...q.options], answer: q.answer, topic: q.topic };
    },

    async deleteQuestion(id) {
      if (!confirm("Delete this question?")) return;
      await api.delete(`/admin/quiz/questions/${id}`);
      this.questions = this.questions.filter(q => q.question_id !== id);
    },

    resetForm() {
      this.editing = null;
      this.form = { question: "", options: ["", "", "", ""], answer: "", topic: "general" };
    },
  };
}
```

- [ ] **Step 3: Replace section placeholders in admin.html with actual UI**

Replace the Content section placeholder:
```html
          <!-- Content editor -->
          <div x-show="section === 'content'" x-data="adminContent()" x-init="init()">
            <h1>Content</h1>
            <div style="display: flex; gap: 0.5rem; margin: 1rem 0; flex-wrap: wrap;">
              <button class="btn btn-sm" :class="activeTab==='about'?'btn-primary':'btn-outline'" @click="activeTab='about'">About</button>
              <button class="btn btn-sm" :class="activeTab==='skills'?'btn-primary':'btn-outline'" @click="activeTab='skills'">Skills (JSON)</button>
              <button class="btn btn-sm" :class="activeTab==='fun-facts'?'btn-primary':'btn-outline'" @click="activeTab='fun-facts'">Fun Facts</button>
              <button class="btn btn-sm" :class="activeTab==='learning'?'btn-primary':'btn-outline'" @click="activeTab='learning'">Currently Learning</button>
            </div>
            <div x-show="success" class="alert alert-success" x-text="success"></div>

            <!-- About tab -->
            <div x-show="activeTab === 'about'" class="card">
              <div class="form-group"><label>Bio</label><textarea x-model="about.bio" class="form-input" rows="5"></textarea></div>
              <div class="form-group"><label>Mission</label><input x-model="about.mission" class="form-input"></div>
              <button class="btn btn-primary" @click="save('about', about)" :disabled="saving">
                <span x-text="saving ? 'Saving...' : 'Save'"></span>
              </button>
            </div>

            <!-- Skills tab -->
            <div x-show="activeTab === 'skills'" class="card">
              <p class="subtitle" style="margin-bottom: 0.75rem;">Edit as JSON. Format: {"languages": ["Python", "JS"], "tools": ["AWS", "Docker"]}</p>
              <textarea x-model="skillsJson" class="form-input" rows="10"
                        :value="JSON.stringify(skills, null, 2)"
                        @input="try { skills = JSON.parse($event.target.value) } catch(e) {}"></textarea>
              <button class="btn btn-primary" style="margin-top: 0.75rem;" @click="save('skills', skills)" :disabled="saving">
                <span x-text="saving ? 'Saving...' : 'Save'"></span>
              </button>
            </div>

            <!-- Fun facts tab -->
            <div x-show="activeTab === 'fun-facts'" class="card">
              <p class="subtitle" style="margin-bottom: 0.75rem;">One fact per line.</p>
              <textarea class="form-input" rows="8"
                        :value="funFacts.facts.join('\n')"
                        @input="funFacts.facts = $event.target.value.split('\n').filter(Boolean)"></textarea>
              <button class="btn btn-primary" style="margin-top: 0.75rem;" @click="save('fun-fact', funFacts)" :disabled="saving">
                <span x-text="saving ? 'Saving...' : 'Save'"></span>
              </button>
            </div>

            <!-- Currently learning tab -->
            <div x-show="activeTab === 'learning'" class="card">
              <p class="subtitle" style="margin-bottom: 0.75rem;">Items shown in the ticker. One per line.</p>
              <textarea class="form-input" rows="6"
                        :value="(currentlyLearning.items || []).join('\n')"
                        @input="currentlyLearning.items = $event.target.value.split('\n').filter(Boolean)"></textarea>
              <button class="btn btn-primary" style="margin-top: 0.75rem;" @click="save('currently-learning', currentlyLearning)" :disabled="saving">
                <span x-text="saving ? 'Saving...' : 'Save'"></span>
              </button>
            </div>
          </div>
```

Replace Users section placeholder:
```html
          <!-- Users -->
          <div x-show="section === 'users'" x-data="adminUsers()" x-init="init()">
            <h1>Users</h1>
            <div x-show="loading" class="loading-center"><div class="spinner"></div></div>
            <template x-if="!loading">
              <div style="margin-top: 1rem;">
                <template x-if="users.length === 0"><p class="subtitle">No users yet.</p></template>
                <template x-for="u in users" :key="u.user_id">
                  <div class="card" style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem; flex-wrap: wrap; gap: 0.5rem;">
                    <div>
                      <strong x-text="u.name"></strong>
                      <span class="subtitle" style="margin-left: 0.5rem;" x-text="u.email"></span>
                      <span class="badge badge-outline" style="margin-left: 0.5rem;" x-text="u.identity"></span>
                      <span class="badge" style="margin-left: 0.25rem;" x-show="u.status && u.status !== 'active'"
                            :style="u.status === 'banned' ? 'background:#DC3545' : 'background:#FFC107; color:#212529'"
                            x-text="u.status"></span>
                    </div>
                    <div style="display: flex; gap: 0.5rem;">
                      <button class="btn btn-outline btn-sm" @click="setStatus(u.user_id, 'suspended')"
                              x-show="u.status !== 'suspended'">Suspend</button>
                      <button class="btn btn-outline btn-sm" @click="setStatus(u.user_id, 'active')"
                              x-show="u.status === 'suspended'">Reinstate</button>
                      <button class="btn btn-danger btn-sm" @click="deleteUser(u.user_id)">Delete</button>
                    </div>
                  </div>
                </template>
              </div>
            </template>
          </div>
```

Replace Contacts section placeholder:
```html
          <!-- Contacts -->
          <div x-show="section === 'contacts'" x-data="adminContacts()" x-init="init()">
            <h1>Contact Submissions</h1>
            <div x-show="loading" class="loading-center"><div class="spinner"></div></div>
            <template x-if="!loading">
              <div style="margin-top: 1rem;">
                <template x-if="contacts.length === 0"><p class="subtitle">No contact submissions.</p></template>
                <template x-for="c in contacts" :key="c.contact_id">
                  <div class="card" style="margin-bottom: 0.75rem;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
                      <strong x-text="c.name + ' &lt;' + c.email + '&gt;'"></strong>
                      <span class="subtitle" style="font-size: 0.8rem;" x-text="formatDate(c.created_at)"></span>
                    </div>
                    <p x-text="c.message"></p>
                  </div>
                </template>
              </div>
            </template>
          </div>
```

Replace Testimonials section placeholder:
```html
          <!-- Testimonials -->
          <div x-show="section === 'testimonials'" x-data="adminTestimonials()" x-init="init()">
            <h1>Pending Testimonials</h1>
            <div x-show="loading" class="loading-center"><div class="spinner"></div></div>
            <template x-if="!loading">
              <div style="margin-top: 1rem;">
                <template x-if="pending.length === 0"><p class="subtitle">No pending testimonials.</p></template>
                <template x-for="t in pending" :key="t.testimonial_id">
                  <div class="card" style="margin-bottom: 0.75rem;">
                    <p style="font-style: italic; margin-bottom: 0.75rem;" x-text="'&ldquo;' + t.body + '&rdquo;'"></p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                      <div>
                        <strong x-text="t.author"></strong>
                        <span class="badge badge-outline" style="margin-left: 0.5rem;" x-text="t.identity"></span>
                      </div>
                      <div style="display: flex; gap: 0.5rem;">
                        <button class="btn btn-primary btn-sm" @click="action(t.testimonial_id, 'approve')">Approve</button>
                        <button class="btn btn-danger btn-sm" @click="action(t.testimonial_id, 'reject')">Reject</button>
                      </div>
                    </div>
                  </div>
                </template>
              </div>
            </template>
          </div>
```

Replace Quiz section placeholder:
```html
          <!-- Quiz -->
          <div x-show="section === 'quiz'" x-data="adminQuiz()" x-init="init()">
            <h1>Quiz Questions</h1>
            <div x-show="error" class="alert alert-error" x-text="error"></div>

            <!-- Add/Edit form -->
            <div class="card" style="margin-bottom: 1.5rem;">
              <h3 x-text="editing ? 'Edit Question' : 'Add Question'"></h3>
              <div class="form-group"><label>Question</label>
                <input x-model="form.question" class="form-input" placeholder="What is...?"></div>
              <div class="form-group"><label>Options (4 choices)</label>
                <template x-for="(opt, idx) in form.options" :key="idx">
                  <input :x-model="`form.options[${idx}]`" class="form-input" style="margin-bottom: 0.4rem;"
                         :placeholder="`Option ${idx + 1}`">
                </template>
              </div>
              <div class="form-group"><label>Correct answer (must match one option exactly)</label>
                <input x-model="form.answer" class="form-input" placeholder="Exact text of correct option"></div>
              <div class="form-group"><label>Topic</label>
                <input x-model="form.topic" class="form-input" placeholder="general"></div>
              <div style="display: flex; gap: 0.75rem;">
                <button class="btn btn-primary" @click="save()" :disabled="saving">
                  <span x-text="saving ? 'Saving...' : editing ? 'Update' : 'Add'"></span>
                </button>
                <button class="btn btn-outline" x-show="editing" @click="resetForm()">Cancel</button>
              </div>
            </div>

            <!-- Questions list -->
            <div x-show="loading" class="loading-center"><div class="spinner"></div></div>
            <template x-if="!loading">
              <div>
                <template x-if="questions.length === 0"><p class="subtitle">No questions yet.</p></template>
                <template x-for="q in questions" :key="q.question_id">
                  <div class="card" style="margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem;">
                    <div>
                      <p x-text="q.question" style="font-weight: 500;"></p>
                      <p class="subtitle" style="font-size: 0.8rem; margin-top: 0.3rem;" x-text="'Answer: ' + q.answer"></p>
                    </div>
                    <div style="display: flex; gap: 0.5rem; flex-shrink: 0;">
                      <button class="btn btn-outline btn-sm" @click="editQuestion(q)">Edit</button>
                      <button class="btn btn-danger btn-sm" @click="deleteQuestion(q.question_id)">Delete</button>
                    </div>
                  </div>
                </template>
              </div>
            </template>
          </div>
```

- [ ] **Step 4: Commit**

```bash
git add frontend/admin.html frontend/assets/js/admin-app.js
git commit -m "feat: implement admin panel (content, users, contacts, testimonials, quiz)"
```

---

### Task 20: Developer page (Swagger link)

**Files:**
- Modify: `frontend/assets/js/pages/developer.js`
- Modify: `frontend/index.html` (Developer section)

- [ ] **Step 1: Replace developer.js**

```javascript
// frontend/assets/js/pages/developer.js
function developerPage() {
  return {
    apiUrl: null,
    meta: null,

    async init() {
      this.apiUrl = API_BASE;
      const resp = await api.get("/meta");
      this.meta = resp.data;
    },
  };
}
```

- [ ] **Step 2: Replace Developer section in index.html**

```html
      <!-- DEVELOPER -->
      <div x-show="currentPage === 'developer'" class="page">
        <div x-data="developerPage()" x-init="init()">
          <h1>Developer</h1>
          <p class="subtitle">Explore the API that powers this portfolio.</p>

          <div style="margin-top: 2rem; display: flex; flex-direction: column; gap: 1rem; max-width: 600px;">
            <div class="card">
              <h3>Interactive API docs</h3>
              <p style="margin: 0.5rem 0; color: var(--text-muted); font-size: 0.9rem;">
                Try every endpoint live in your browser.
              </p>
              <a :href="apiUrl + '/api'" target="_blank" class="btn btn-primary" style="display: inline-block; margin-top: 0.75rem;">
                Open Swagger UI
              </a>
            </div>

            <div class="card">
              <h3>OpenAPI spec</h3>
              <p style="margin: 0.5rem 0; color: var(--text-muted); font-size: 0.9rem;">
                Import into Postman or any OpenAPI-compatible tool.
              </p>
              <a :href="apiUrl + '/api/spec'" target="_blank" class="btn btn-outline" style="display: inline-block; margin-top: 0.75rem;">
                Download spec (JSON)
              </a>
            </div>

            <template x-if="meta">
              <div class="card">
                <h3>Deploy info</h3>
                <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
                  <tr><td style="padding: 0.3rem 0; color: var(--text-muted);">Version</td>
                      <td x-text="meta.version"></td></tr>
                  <tr><td style="padding: 0.3rem 0; color: var(--text-muted);">Environment</td>
                      <td x-text="meta.environment"></td></tr>
                  <tr><td style="padding: 0.3rem 0; color: var(--text-muted);">Git SHA</td>
                      <td><code x-text="meta.git_sha?.slice(0, 8)"></code></td></tr>
                  <tr><td style="padding: 0.3rem 0; color: var(--text-muted);">Deployed</td>
                      <td x-text="meta.deploy_timestamp"></td></tr>
                </table>
              </div>
            </template>
          </div>
        </div>
      </div>
```

- [ ] **Step 3: Commit + merge**

```bash
git add frontend/assets/js/pages/developer.js frontend/index.html
git commit -m "feat: implement Developer page (Swagger link, spec download, deploy info)"
git checkout dev
git merge feature/admin-panel
git push origin dev
```

---

## Feature Branch: `feature/polish`

> Covers: favicon, Open Graph tags, console Easter egg, loading animations, scroll animations, Lighthouse 90+

```bash
git checkout dev
git checkout -b feature/polish
```

---

### Task 21: Favicon + Open Graph meta tags

**Files:**
- Create: `frontend/assets/images/favicon.ico`
- Modify: `frontend/index.html` (head section)

- [ ] **Step 1: Generate a favicon**

Option A — use an emoji-based favicon generator:
```bash
# Create a simple SVG favicon using initials "RH"
cat > frontend/assets/images/favicon.svg << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="6" fill="#007BFF"/>
  <text x="16" y="22" font-family="Arial" font-weight="bold" font-size="14"
        fill="white" text-anchor="middle">RH</text>
</svg>
EOF
```

Option B — use a real favicon generator: go to favicon.io, generate from text "RH", download and place `favicon.ico` in `frontend/assets/images/`.

Update the favicon link in `index.html` head:
```html
  <link rel="icon" href="/assets/images/favicon.svg" type="image/svg+xml">
  <link rel="alternate icon" href="/assets/images/favicon.ico">
```

- [ ] **Step 2: Update Open Graph tags in index.html head**

Replace the existing OG meta block:
```html
  <!-- Open Graph / Social sharing -->
  <meta property="og:type" content="website">
  <meta property="og:title" content="Ron Harifiyati — Portfolio">
  <meta property="og:description" content="Integration Engineer at Jamf. Builder of APIs, automation, and systems.">
  <meta property="og:image" content="/assets/images/og-image.png">
  <meta property="og:url" content="https://YOUR_PROD_CLOUDFRONT_DOMAIN">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Ron Harifiyati — Portfolio">
  <meta name="twitter:description" content="Integration Engineer at Jamf. Builder of APIs, automation, and systems.">
  <meta name="description" content="Ron Harifiyati — Integration Engineer, builder, and learner. Projects, courses, and more.">
```

- [ ] **Step 3: Create a simple OG image**

Create `frontend/assets/images/og-image.png` — a 1200×630 image. Easiest option: use Canva or a similar tool to create a simple branded image with your name and title.

- [ ] **Step 4: Commit**

```bash
git add frontend/assets/images/ frontend/index.html
git commit -m "feat: add favicon, Open Graph and Twitter card meta tags"
```

---

### Task 22: Console Easter egg

**Files:**
- Modify: `frontend/assets/js/app.js`

- [ ] **Step 1: Add Easter egg to app.js init()**

Add at the top of the `init()` method in `portfolioApp()`:

```javascript
    async init() {
      // Easter egg
      console.log(
        "%c👋 Hey there, fellow developer!",
        "font-size: 16px; font-weight: bold; color: #007BFF;"
      );
      console.log(
        "%cYou found the console. Since you're here, the API is open — try:\n\n" +
        `  fetch('${DEV_API_URL}/meta').then(r=>r.json()).then(console.log)\n\n` +
        "Or visit #/developer for the full API docs.",
        "font-size: 13px; color: #6C757D;"
      );
      console.log(
        "%c— Ron",
        "font-style: italic; color: #6C757D;"
      );

      // ... rest of init
```

- [ ] **Step 2: Verify in browser**

Open DevTools → Console on the portfolio site. Expected: styled console messages appear.

- [ ] **Step 3: Commit**

```bash
git add frontend/assets/js/app.js
git commit -m "feat: add console Easter egg for developers"
```

---

### Task 23: Loading animations + scroll animations

**Files:**
- Modify: `frontend/assets/css/main.css`
- Modify: `frontend/assets/js/app.js`

- [ ] **Step 1: Add fade-in animation to main.css**

Append to `frontend/assets/css/main.css`:

```css
/* Fade-in on scroll */
.fade-in {
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 0.5s ease, transform 0.5s ease;
}
.fade-in.visible {
  opacity: 1;
  transform: translateY(0);
}

/* Page transition */
.page {
  animation: pageEnter 0.2s ease;
}
@keyframes pageEnter {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
```

- [ ] **Step 2: Add IntersectionObserver to app.js**

Add this function at the bottom of `app.js` (outside the `portfolioApp()` function):

```javascript
// Scroll fade-in observer — attach to elements with class .fade-in
function initScrollAnimations() {
  const observer = new IntersectionObserver(
    entries => entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        observer.unobserve(entry.target);
      }
    }),
    { threshold: 0.1 }
  );
  document.querySelectorAll(".fade-in").forEach(el => observer.observe(el));
}
```

- [ ] **Step 3: Call initScrollAnimations after page renders**

In the `handleRoute` method of `portfolioApp()`, add at the end:

```javascript
    handleRoute(hash) {
      // ... existing route logic ...
      // Re-attach scroll observers after page change
      this.$nextTick(() => initScrollAnimations());
    },
```

- [ ] **Step 4: Add `fade-in` class to card-grid items**

In `index.html`, add `class="fade-in"` to the outer `<div>` of key sections. Example for Projects list:
```html
<div class="card-grid fade-in">
```

Apply to: project cards, course cards, skills section, about bio, testimonials grid.

- [ ] **Step 5: Commit**

```bash
git add frontend/assets/css/main.css frontend/assets/js/app.js frontend/index.html
git commit -m "feat: add page transition and scroll fade-in animations"
```

---

### Task 24: Lighthouse audit + performance fixes

- [ ] **Step 1: Serve frontend locally and run Lighthouse**

```bash
cd frontend && python3 -m http.server 8080
```

In Chrome: DevTools → Lighthouse → run audit on `http://localhost:8080`.

Target: **Performance 90+, Accessibility 90+, Best Practices 90+, SEO 90+**

- [ ] **Step 2: Common fixes if score is below 90**

**Images not sized:** Add `width` and `height` attributes to any `<img>` tags.

**Render-blocking resources:** Alpine.js already has `defer`. Ensure all `<script>` tags use `defer` or are at end of `<body>`.

**Missing alt text:** Add `alt` attributes to all images.

**Contrast issues:** Verify CSS custom properties meet WCAG AA (4.5:1 for normal text, 3:1 for large text). Use https://webaim.org/resources/contrastchecker/ for each theme combination.

**Missing lang attribute:** Already in `<html lang="en">`.

**Missing meta description:** Already added in Task 21.

**Leaflet.js loading on every page:** Move the Leaflet `<script>` and `<link>` tags to load lazily only when the stats page is visited. Replace the CDN tags in `<head>` with dynamic loading in `stats.js`:

```javascript
// In stats.js, before initMap():
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

async init() {
  const resp = await api.get("/stats/visitors");
  this.locations = resp.data || [];
  this.total = this.locations.length;
  this.loading = false;
  await this.loadLeaflet();          // load Leaflet on demand
  await this.$nextTick();
  this.initMap();
},
```

Remove the Leaflet CDN `<link>` and `<script>` tags from `index.html` head.

- [ ] **Step 3: Re-run Lighthouse until score ≥ 90**

```bash
# Open http://localhost:8080 in Chrome
# DevTools → Lighthouse → Mobile → Analyze page load
```

Expected: All four categories ≥ 90.

- [ ] **Step 4: Verify all 5 themes pass WCAG AA contrast**

For each theme, check these pairs at https://webaim.org/resources/contrastchecker/:
- `--text` on `--bg` (body text): target 4.5:1
- `--text-muted` on `--bg` (secondary text): target 4.5:1
- white on `--accent` (button text): target 4.5:1

| Theme | text/bg | muted/bg | white/accent |
|-------|---------|----------|--------------|
| Light | `#212529`/`#FFFFFF` = 16.1:1 ✓ | `#6C757D`/`#FFFFFF` = 4.6:1 ✓ | `#FFF`/`#007BFF` = 4.6:1 ✓ |
| Dark | `#E0E0E0`/`#121212` = 12.6:1 ✓ | `#9E9E9E`/`#121212` = 5.7:1 ✓ | `#FFF`/`#4FC3F7` = 1.7:1 ✗ — fix: use dark text on accent button |
| Coffee | `#5D4037`/`#FAF3E0` = 7.1:1 ✓ | `#8D6E63`/`#FAF3E0` = 4.6:1 ✓ | `#FFF`/`#A1887F` = 2.3:1 ✗ — fix: use `#5D4037` text on accent buttons |
| Terminal | `#00FF41`/`#000000` = 15.3:1 ✓ | `#008F11`/`#000000` = 3.2:1 ✓ | `#000`/`#008F11` = 3.2:1 — use black text on green buttons |
| Nordic | `#D8DEE9`/`#2E3440` = 9.4:1 ✓ | `#B0BAD0`/`#2E3440` = 5.3:1 ✓ | `#FFF`/`#88C0D0` = 2.8:1 ✗ — fix: use `#2E3440` text on accent buttons |

Fix failing themes by adding per-theme button text overrides in `theme.css`:

```css
/* Dark theme — accent buttons need dark text */
[data-theme="dark"] .btn-primary { color: #121212; }

/* Coffee theme — accent buttons need dark brown text */
[data-theme="coffee"] .btn-primary { color: #5D4037; }

/* Terminal theme — green buttons use black text */
[data-theme="terminal"] .btn-primary { color: #000000; }

/* Nordic theme — accent buttons need dark text */
[data-theme="nordic"] .btn-primary { color: #2E3440; }
```

- [ ] **Step 5: Final commit + merge to dev**

```bash
git add frontend/
git commit -m "feat: polish — WCAG AA contrast fixes, lazy Leaflet, Lighthouse 90+"
git checkout dev
git merge feature/polish
git push origin dev
```

- [ ] **Step 6: Promote to prod**

```bash
git checkout prod
git merge dev
git push origin prod
```

Expected: `Deploy Frontend` workflow deploys to S3/CloudFront prod. Visit the prod CloudFront URL — full site should be live.

---

## Final Checklist

- [ ] All 5 themes apply correctly via theme toggle
- [ ] Theme persists on page refresh (localStorage)
- [ ] Authenticated users' theme syncs to server and restores on next login
- [ ] Hash-based routing works for all pages (no 404 on direct URL access — CloudFront custom error config serves index.html)
- [ ] Login → register → verify email → login flow works end-to-end
- [ ] GitHub OAuth and Google OAuth redirect and create sessions
- [ ] Quiz requires auth, shows leaderboard correctly
- [ ] Admin panel only accessible with admin JWT
- [ ] Visitor map renders on `/stats`
- [ ] Contact form shows rate limit message after 5 submissions
- [ ] Testimonials show only approved entries; filter by identity works
- [ ] Guestbook shows `name (guest)` for unauthenticated entries
- [ ] Developer page links to live Swagger UI
- [ ] Console Easter egg appears in browser DevTools
- [ ] Lighthouse score ≥ 90 on mobile and desktop
- [ ] All 5 themes pass WCAG AA contrast check
- [ ] OG tags render correctly when URL is pasted into Slack/Twitter

