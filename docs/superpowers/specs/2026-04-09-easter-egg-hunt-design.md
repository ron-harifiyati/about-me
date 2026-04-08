# Easter Egg Hunt — Design Spec

## Overview

A developer-oriented scavenger hunt with 12 linear easter eggs hidden across the frontend. Each egg gives a clue to find the next. Finding all 12 unlocks two rewards: **terminal mode** (a full CLI-style interface to the site) and a **hacker badge** (shield with circuit pattern displayed next to the user's name).

## Easter Eggs — Linear Sequence

Each egg is discovered through a different developer technique. The clue for the next egg is revealed upon finding the current one.

| # | ID | Name | Discovery Method | Clue to Next |
|---|-----|------|-----------------|--------------|
| 1 | `console-greeting` | The Greeting | Open the browser console — the existing dev greeting is the entry point. The about page hunt section tells users to start here. | Type `ron()` in the console |
| 2 | `ron-function` | ron() | Type `ron()` in the console — a hidden global function | "Nice find! I hid something in the page source — look near the top." |
| 3 | `view-source` | View Source | View page source — ASCII art in an HTML comment near the top of `index.html` | "Now inspect the footer — not everything is visible." |
| 4 | `hidden-element` | The Inspector | Inspect the footer — a `display: none` element with a `data-egg` attribute and message | "Check localStorage — I left you something." |
| 5 | `localstorage` | The Breadcrumb | Check localStorage — a key called `hint` set on first visit with a base64-encoded value | Decodes to: "Select all the text on the about page." |
| 6 | `ghost-text` | Ghost Text | On the about page, hidden same-color-as-background text that becomes visible when selected/highlighted | "You see the invisible! Try the Konami code." |
| 7 | `konami` | Konami | ↑ ↑ ↓ ↓ ← → ← → B A | Matrix rain effect + message: "Classic! Click my name in the header 7 times." |
| 8 | `rage-click` | Rage Click | Click the site name/logo in the header 7 times rapidly | Glitch animation + message: "Try navigating to #/root" |
| 9 | `secret-route` | Secret Route | Navigate to `#/root` — a terminal-styled hidden page | "Some styles hide secrets — inspect the hero section's ::after" |
| 10 | `phantom-css` | Phantom CSS | Inspect the hero section's `::after` pseudo-element — it has a `content` value hidden with `font-size: 0` | "Resize your browser to exactly 1337px wide." |
| 11 | `leet-width` | 1337 | Resize the viewport to exactly 1337px wide — a hidden element appears via `@media (width: 1337px)` | "Last one — cycle all 3 themes within 2 seconds." |
| 12 | `speed-themer` | Speed Themer | Cycle through all 3 themes in under 2 seconds | Unlocks terminal mode + hacker badge |

## Tracking System

### Registered Users (API)

- New field on user profile: `eggs_found: ["console-greeting", "ron-function", ...]`
- Endpoint: `POST /easter-eggs/found` with body `{ "egg_id": "..." }`
  - Validates the egg ID is the next in sequence (prevents skipping)
  - Appends to `eggs_found` and returns updated list
- Endpoint: `GET /easter-eggs` — returns the user's found eggs list
- On egg #12 completion: also sets `hacker_badge: true` on the user profile

### Unregistered Users (localStorage)

- `localStorage` key: `eggs_found` — JSON array of found egg IDs
- Same sequential validation on the frontend (must find them in order)
- On login/register: sync localStorage progress to API automatically
  - Frontend calls `POST /easter-eggs/sync` with the localStorage array
  - API validates sequence and updates the user profile

### Response Envelope

All easter egg endpoints follow the standard response envelope:
```json
{ "data": { "eggs_found": [...], "total": 12 }, "error": null }
```

## About Page — Hunt Section

A card at the bottom of the about page serves as the "home base" for the hunt.

### Content

- **Title:** "Developer Easter Egg Hunt"
- **Description:** "There are 12 hidden easter eggs scattered around this site. Each one leads to the next. Find them all to unlock something special."
- **Progress:** `3/12 found` with visual indicators (checkmarks for found, locked icons for remaining — no spoilers)
- **Active hint:** Always shows the clue for the next unfound egg
  - If none found: "Open your browser's developer console to get started."
  - If all found: congratulations message + link to terminal mode
- **Reward teaser:** For registered users: "Find all 12 to unlock Terminal Mode and earn the Hacker Badge." For guests: "Log in to save your progress and earn the reward."

## Reward: Terminal Mode

### Access

- Unlocked after finding all 12 eggs (registered users only)
- Accessible at `#/terminal` — only users with `eggs_found` length 12 can access; others are redirected
- Also accessible via future settings page toggle
- Preference persisted: if the user chooses terminal mode, it stays on across visits until they switch back
- Stored on user profile: `terminal_mode: true/false`

### Interface

- **Fullscreen** — no nav bar, no footer, pure terminal immersion
- **Aesthetic:** Green-on-black (#00ff00 on #0a0a0a), monospace font, blinking cursor, subtle scanline CSS overlay for CRT feel
- **Typing animation:** ~5ms per character for output, fast enough to feel like a real terminal. Skip animation by pressing any key mid-output.
- **First visit hint:** On first activation, display: "Type `help` to see available commands."

### Commands

| Command | Description |
|---------|-------------|
| `help` | List all available commands |
| `ls` | List available sections (projects, courses, about, skills, etc.) |
| `cd <section>` | Navigate to a section (e.g., `cd projects`) |
| `cat <item>` | View details of an item (e.g., `cat portfolio-site`) |
| `ls` (within a section) | List items in the current section |
| `cd ..` | Go back to root |
| `whoami` | Show logged-in user info |
| `clear` | Clear the terminal screen |
| `theme` | Cycle terminal color scheme (green, amber, blue, white) |
| `exit` | Return to normal site mode (sets `terminal_mode: false`) |
| `pwd` | Show current "path" |

### Data

All content is pulled live from the existing API endpoints and displayed in terminal-formatted text:
- `ls` in projects → calls `GET /projects`, displays as a file listing
- `cat project-name` → calls `GET /projects/{id}`, displays formatted text
- `cd about` + `cat` → calls `GET /about`, displays as text block
- Same pattern for courses, skills, timeline, etc.

### Routing

- Terminal mode is a full page at `#/terminal`
- Internal navigation happens via commands, not URL hash changes
- The terminal maintains its own path state (e.g., `/projects/portfolio-site`)

## Reward: Hacker Badge

### Visual

- Small SVG icon — a shield with a circuit board pattern
- Sits next to the username wherever it appears
- Subtle, clean, developer-themed

### Display Locations (Current)

- **Guestbook entries** — next to the author's name
- **Comments** — next to the commenter's name

### Display Locations (Future)

- Profile/settings page (when built)
- Chat feature (when built)

### Data

- Stored on user profile: `hacker_badge: true`
- API returns it as part of the user object
- Frontend checks `user.hacker_badge` and renders the SVG icon when true
- Badge also visible on other users' public content (guestbook, comments) — any user with the badge gets the icon next to their name

## DynamoDB Changes

No new table needed. Changes to existing user profile item:

- `eggs_found` — list of string egg IDs (e.g., `["console-greeting", "ron-function", ...]`)
- `hacker_badge` — boolean, set to `true` on completing all 12
- `terminal_mode` — boolean, user preference for terminal mode as default

## New API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/easter-eggs` | `@require_auth` | Get user's found eggs |
| `POST` | `/easter-eggs/found` | `@require_auth` | Mark an egg as found (validates sequence) |
| `POST` | `/easter-eggs/sync` | `@require_auth` | Sync localStorage progress on login |

## Frontend Files (New)

- `frontend/assets/js/eggs.js` — easter egg discovery logic, tracking, clue display
- `frontend/assets/js/pages/terminal.js` — terminal mode page component
- `frontend/assets/css/terminal.css` — terminal mode styles (CRT aesthetic, scanlines, cursor)
- `frontend/assets/js/pages/root.js` — secret `#/root` page (egg #9)

## Frontend Files (Modified)

- `index.html` — add hunt section to about page, add hidden elements (eggs #3, #4, #10, #11), add `#/terminal` and `#/root` templates, add script includes
- `app.js` — add `terminal` and `root` routes, add Konami code listener, add logo click counter, add theme speed detection
- `themes.js` — track theme cycle speed for egg #12
- `about.js` — add ghost text (egg #6), add hunt section logic
- `main.css` — add ghost text styles, 1337px media query, hidden element styles
