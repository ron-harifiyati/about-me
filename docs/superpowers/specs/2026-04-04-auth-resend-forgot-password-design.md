# Auth: Resend Verification + Forgot Password — Design Spec

**Date:** 2026-04-04
**Branch:** feature/fix-ses-email-verification
**Status:** Approved

---

## Context

`POST /auth/resend-verification` was added in the same branch to handle SES failures during registration. This spec covers wiring up that endpoint in the frontend and adding a full forgot-password flow.

---

## Features

### 1. Resend Verification Email (frontend only — backend already exists)

Two surfaces:

- **Register page success state** — after a successful registration, show a "Resend verification email" button with the email pre-filled. Clicking it calls `POST /auth/resend-verification` and shows confirmation.
- **Login page error state** — when the API returns "Please verify your email before logging in", show a "Resend verification email" button inline in the error area. Clicking it prompts for the email (pre-filled from the login form) and calls the endpoint.

### 2. Forgot Password

**Flow:**
1. User clicks "Forgot password?" link below the login submit button
2. Navigates to `#/forgot-password`
3. Enters email → `POST /auth/forgot-password`
4. Always shows: "If that address is registered, a reset link is on its way." (no enumeration)
5. User clicks link in email → `#/reset-password?token=…`
6. Enters new password + confirm → `POST /auth/reset-password`
7. On success: "Password updated!" → auto-redirect to `#/login` after 2s
8. On expired/invalid token: error with link back to `#/forgot-password`

---

## Backend

### New endpoints

#### `POST /auth/forgot-password`

- Input: `{ email }`
- Validation: email required
- Logic:
  - Look up user by email
  - If not found, or user has no `password_hash` (OAuth-only account): return `200` silently
  - Create `RESET#<token>` item in DynamoDB (TTL: 1 hour)
  - Send reset email via SES: subject "Reset your password — Ron's Portfolio", body with `{FRONTEND_URL}/#/reset-password?token={token}`
  - If SES fails: return `500` with message "Could not send reset email. Please try again later."
- Returns: `200 { message: "If that address is registered, a reset link is on its way." }`

#### `POST /auth/reset-password`

- Input: `{ token, new_password }`
- Validation: both fields required; `new_password` ≥ 8 characters
- Logic:
  - Call `consume_password_reset_token(token)` — returns `user_id` or `None`
  - If `None`: return `400 "Invalid or expired reset link"`
  - Hash new password, update `password_hash` on `USER#{user_id} / PROFILE`
- Returns: `200 { message: "Password updated. You can now log in." }`

### New model functions in `models/users.py`

```python
def create_password_reset_token(user_id: str) -> str:
    # Same pattern as create_email_verify_token
    # PK: RESET#<token>, SK: TOKEN, ttl: now + 3600

def consume_password_reset_token(token: str) -> str | None:
    # Same pattern as consume_email_verify_token
    # PK: RESET#<token>, SK: TOKEN
```

### Route registration in `router.py`

```
("POST", "/auth/forgot-password",  auth_routes.forgot_password)
("POST", "/auth/reset-password",   auth_routes.reset_password)
```

---

## Frontend

### Modified files

**`index.html`**
- Login section: add "Forgot password?" link + "Resend verification email" button in error area
- Register section: add "Resend verification email" button in success state
- Add `#/forgot-password` page section
- Add `#/reset-password` page section
- Add `<script>` tags for `forgot-password.js` and `reset-password.js`

**`assets/js/app.js`**
- Add `"forgot-password": "forgot-password"` and `"reset-password": "reset-password"` to route table

**`assets/js/pages/login.js`**
- Track `unverifiedEmail` state
- When error === "Please verify your email before logging in", set `unverifiedEmail = form.email`
- Add `resendVerification()` method: calls `POST /auth/resend-verification`, shows inline confirmation

**`assets/js/pages/register.js`**
- Before clearing `this.form` on success, save `this.submittedEmail = this.form.email`
- Add `resendVerification()` method using `this.submittedEmail`
- Show resend button + confirmation in success state

### New files

**`assets/js/pages/forgot-password.js`**
```
forgotPasswordPage() {
  form: { email: "" }
  submitting, sent, error
  submit() → POST /auth/forgot-password → set sent = true
}
```

**`assets/js/pages/reset-password.js`**
```
resetPasswordPage() {
  form: { new_password: "", confirm_password: "" }
  token (parsed from URL hash query string, same technique as verify-email.js)
  submitting, success, error
  init() → extract token; if none, set error immediately
  submit() → validate passwords match → POST /auth/reset-password
           → on success: set success = true, setTimeout 2s → navigate to #/login
           → on error: show error with link to #/forgot-password
}
```

---

## DynamoDB

New key pattern (same table `portfolio`):

| PK | SK | Attributes |
|----|-----|-----------|
| `RESET#<token>` | `TOKEN` | `user_id`, `ttl` |

TTL expiry: 1 hour. DynamoDB TTL handles cleanup (eventual, up to 48h delay is fine — `consume_password_reset_token` checks TTL manually is not needed since token is consumed on first use anyway; expired tokens just return no item).

---

## Tests

- `test_forgot_password_unknown_email_returns_200` — no enumeration
- `test_forgot_password_sends_email` — SES mock called
- `test_forgot_password_oauth_only_user_returns_200` — no password_hash, still 200
- `test_reset_password_happy_path` — token consumed, password updated, can log in
- `test_reset_password_invalid_token_returns_400`
- `test_reset_password_short_password_returns_400`

---

## Out of scope

- Rate limiting on forgot-password (can add later)
- Password strength meter in UI
- Invalidating existing sessions on password reset
