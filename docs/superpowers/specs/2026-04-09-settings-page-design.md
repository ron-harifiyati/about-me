# Settings Page Design Spec

**Date:** 2026-04-09
**Status:** Approved
**Goal:** Add a user settings page where authenticated users can manage their profile, appearance, OAuth connections, activity history, and account (including deletion with anonymization).

---

## Overview

A new `#/settings` route in the main SPA, accessible only to authenticated users. The page uses a sidebar-with-scrollable-content layout: a sticky left sidebar with anchor links that smooth-scroll to sections on the right. On mobile, the sidebar collapses to horizontally scrollable pills pinned to the top.

## Nav Bar Changes

**Logged in:**
- Replace the theme toggle button and logout button with the user's hash-based identicon (32px circle). Clicking it navigates to `#/settings`.
- Theme selection moves to the Appearance section in settings.

**Logged out:**
- No identicon shown. Login button stays as-is.
- Theme toggle remains in the nav bar so guests can still switch themes.

## Identicons

Deterministic geometric avatars generated client-side from a hash of the user's `user_id`. No server storage needed.

- **Generation:** Canvas-based or SVG, using a small library (e.g., jdenticon) or a custom implementation that hashes the user ID into a symmetric geometric pattern with distinct colors.
- **Sizes:** 32px in nav bar, 52px in settings profile header, 24px inline next to comments/guestbook entries.
- **Unregistered users:** Show a generic grey placeholder identicon (not personalized) next to their guestbook entries/comments.

## Page Layout

### Desktop (>768px)
- Sticky sidebar (170px wide) on the left with section anchor links.
- Scrollable content area on the right with all sections stacked vertically, separated by dividers.
- Sidebar highlights the current section based on scroll position (Intersection Observer).

### Mobile (≤768px)
- Sidebar collapses to a row of horizontally scrollable pills, sticky at the top.
- Active pill highlights based on scroll position.
- All form fields stack single-column.
- Action buttons go full-width.

## Sections

### 1. Profile

Editable user profile fields.

**Fields:**
- **Identicon + name header** — read-only display of the user's identicon, name, email, and "Member since" date.
- **Display Name** — text input, required, max 100 chars.
- **Identity** — dropdown select: Jamf, MCRI, Friend, Family, Other.
- **Email** — displayed read-only with a "read-only" badge. Cannot be changed.
- **Save Changes** button — calls `PUT /auth/me` with `{ name, identity }`.

**Behavior:**
- On load, pre-fill from `GET /auth/me` response (already available in app state).
- Show success/error toast on save.
- Button disabled until a field changes (dirty check).

### 2. Appearance

Theme selector with visual preview swatches.

**Layout:**
- 5 theme cards in a row (desktop) or 3-column grid wrapping to 2 rows (mobile).
- Each card shows a miniature color preview of that theme's background, accent, and text colors.
- Active theme has a highlighted border and checkmark.
- Clicking a card applies the theme immediately (live preview) and saves to server via `PUT /auth/me { theme }`.

**Themes:** light, dark, coffee, terminal, nordic.

**Behavior:**
- Theme applies instantly on click — no save button needed.
- Synced to server so it persists across devices.

### 3. Connections

Manage OAuth providers and password status.

**Cards (one per provider + password):**

**GitHub:**
- If connected: show "Connected as {username}", Disconnect button.
- If not connected: show "Not connected", Connect button.

**Google:**
- Same pattern as GitHub.

**Password:**
- If set: show "Set" with green checkmark, "Reset via email" link (navigates to `#/forgot-password`).
- If not set (OAuth-only user): show "Not set", "Set password via email" link.

**Connect flow:** Clicking "Connect" redirects to the OAuth init endpoint with a `link=true` query param: `GET /auth/oauth/{provider}?link=true`. The init endpoint encodes `link=true` plus the user's `user_id` into the OAuth `state` parameter. On callback, the backend checks the state: if `link=true`, it links the provider to the existing user instead of creating a new account or logging in as a different user. The frontend passes the access token as a `token` query param so the init endpoint can extract the user ID.

**Disconnect flow:** Clicking "Disconnect" calls `DELETE /auth/me/oauth/{provider}`. The backend rejects the request if it would leave the user with no sign-in method (no password and no other OAuth provider linked).

**New backend work required:**
- `GET /auth/me/connections` — returns list of linked providers with provider username/email.
- `DELETE /auth/me/oauth/{provider}` — unlink an OAuth provider.
- Modify OAuth init endpoints to accept `link=true&token=JWT` and pass through state.
- Modify OAuth callback to check state for link mode and link to existing user.
- `GET /auth/me` response should include a `has_password` boolean field.

### 4. Activity

Read-only view of user contributions with delete capability for comments and guestbook entries.

**Sub-tabs:** Comments, Ratings, Quiz, Guestbook, Testimonials — each with a count badge.

**Comments tab:**
- List of user's comments across projects and courses.
- Each shows: entity name (project/course title), relative timestamp, comment text, Delete button.
- Delete calls `DELETE /auth/me/comments/{id}` (backend looks up the comment, verifies ownership, deletes).

**Ratings tab:**
- List of user's ratings across projects and courses.
- Each shows: entity name, star rating (1-5), timestamp.
- Read-only — no delete.

**Quiz tab:**
- List of user's quiz attempts.
- Each shows: score, number correct, timestamp.
- Read-only — no delete.

**Guestbook tab:**
- List of user's guestbook entries.
- Each shows: message text, timestamp, Delete button.
- Delete calls `DELETE /auth/me/guestbook-entries/{id}` (backend verifies ownership, deletes).

**Testimonials tab:**
- List of user's submitted testimonials.
- Each shows: message text, status (pending/approved/rejected), timestamp.
- Read-only — no delete.

**New backend work required:**
- `GET /auth/me/comments` — list comments by the current user across all entities.
- `GET /auth/me/ratings` — list ratings by the current user.
- `GET /auth/me/quiz-scores` — list quiz attempts by the current user.
- `GET /auth/me/guestbook-entries` — list guestbook entries by the current user.
- `GET /auth/me/testimonials` — list testimonials submitted by the current user.
- `DELETE /auth/me/comments/{id}` — delete own comment.
- `DELETE /auth/me/guestbook-entries/{id}` — delete own guestbook entry.

**DynamoDB consideration:** Comments and guestbook entries are not currently indexed by user. Fetching a user's activity requires scanning. Options:
- **Scan with filter** — simplest, acceptable at current scale (small user base).
- **GSI on user_id** — more efficient but adds a GSI. Can be added later if scale demands it.

Start with scan + filter. Add a GSI if performance becomes an issue.

### 5. Account

Session management and account deletion.

**Sign out:**
- "Log out" button — calls existing `POST /auth/logout`, clears tokens, redirects to home.

**Danger Zone (red bordered section):**
- Explanation text: "Permanently delete your account. Your contributions (comments, ratings, etc.) will be anonymized — they'll show 'Deleted User' instead of your name. This action cannot be undone."
- "Delete My Account" button (red).
- On click: opens a confirmation modal requiring the user to type `DELETE` to confirm.
- On confirm: calls new endpoint `DELETE /auth/me`.

**Account deletion flow (`DELETE /auth/me`):**
1. Verify JWT authentication.
2. Anonymize all user content:
   - Update all comments by this user: set `user_name` to "Deleted User", `user_identity` to null, `user_id` to null.
   - Update all guestbook entries by this user: set `name` to "Deleted User", `identity` to null.
   - Update all testimonials by this user: set `name` to "Deleted User".
   - Ratings and quiz scores: set `user_id` to `DELETED`, keep the data (ratings still count, scores still on leaderboard as anonymous).
3. Delete all OAuth link records (`OAUTH#{provider}#{id}`).
4. Delete all session/refresh tokens.
5. Delete the user profile record (`USER#{id}, PROFILE`).
6. Return 200 with success message.
7. Frontend clears tokens, redirects to home.

**New backend work required:**
- `DELETE /auth/me` — account deletion with anonymization.

## API Summary

### New Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/auth/me/connections` | @auth | List linked OAuth providers |
| DELETE | `/auth/me/oauth/{provider}` | @auth | Unlink OAuth provider |
| GET | `/auth/me/comments` | @auth | List user's comments |
| GET | `/auth/me/ratings` | @auth | List user's ratings |
| GET | `/auth/me/quiz-scores` | @auth | List user's quiz attempts |
| GET | `/auth/me/guestbook-entries` | @auth | List user's guestbook entries |
| GET | `/auth/me/testimonials` | @auth | List user's testimonials |
| DELETE | `/auth/me/comments/{id}` | @auth | Delete own comment |
| DELETE | `/auth/me/guestbook-entries/{id}` | @auth | Delete own guestbook entry |
| DELETE | `/auth/me` | @auth | Delete account (anonymize + remove) |

### Modified Endpoints

| Method | Path | Change |
|--------|------|--------|
| GET | `/auth/me` | Add `has_password` boolean to response |
| GET/POST | `/auth/oauth/{provider}/callback` | Support linking to existing authenticated user |

### New Frontend Files

| File | Purpose |
|------|---------|
| `frontend/assets/js/pages/settings.js` | Settings page Alpine component |
| `frontend/assets/js/identicon.js` | Identicon generation utility |

### Modified Frontend Files

| File | Change |
|------|--------|
| `frontend/index.html` | Add `#/settings` route, replace theme toggle + logout with identicon |
| `frontend/assets/js/app.js` | Add settings route handler, remove theme toggle logic from nav |
| `frontend/assets/js/themes.js` | Keep theme application logic, remove nav toggle cycling |
| `frontend/assets/css/main.css` | Add settings page styles, identicon styles |

## Out of Scope

- Profile photo uploads (dropped — identicons only).
- In-app password change (uses existing email reset flow).
- Email change.
- Admin settings (admin panel is separate).
