# Auth: Resend Verification + Forgot Password — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add resend-verification button to login/register pages and implement a full forgot/reset password flow.

**Architecture:** Two new backend endpoints (`/auth/forgot-password`, `/auth/reset-password`) mirror the existing verify-email pattern. Frontend gets two new pages (`#/forgot-password`, `#/reset-password`) and inline resend buttons on login and register.

**Tech Stack:** Python/boto3 (SES + DynamoDB), Alpine.js, no build step.

---

### Task 1: Backend model functions

**Files:**
- Modify: `backend/models/users.py`
- Test: `backend/tests/test_auth_routes.py`

- [ ] **Write failing tests**

Add to `backend/tests/test_auth_routes.py`:

```python
def test_reset_password_happy_path(ddb_table, mocker):
    mocker.patch("routes.auth_routes._send_verification_email")
    mocker.patch("routes.auth_routes._send_reset_email")
    from router import route
    from models.users import mark_email_verified, get_user_by_email, create_password_reset_token
    route(make_event("POST", "/auth/register", body={
        "email": "ron@example.com", "password": "Secure123!", "name": "Ron", "identity": "Jamf",
    }))
    user = get_user_by_email("ron@example.com")
    mark_email_verified(user["user_id"])
    token = create_password_reset_token(user["user_id"])

    resp = route(make_event("POST", "/auth/reset-password", body={
        "token": token, "new_password": "NewPass123!",
    }))
    assert resp["statusCode"] == 200

    login = route(make_event("POST", "/auth/login", body={
        "email": "ron@example.com", "password": "NewPass123!",
    }))
    assert login["statusCode"] == 200


def test_reset_password_invalid_token_returns_400(ddb_table, mocker):
    mocker.patch("routes.auth_routes._send_verification_email")
    from router import route
    resp = route(make_event("POST", "/auth/reset-password", body={
        "token": "badtoken", "new_password": "NewPass123!",
    }))
    assert resp["statusCode"] == 400


def test_reset_password_short_password_returns_400(ddb_table, mocker):
    mocker.patch("routes.auth_routes._send_verification_email")
    from router import route
    resp = route(make_event("POST", "/auth/reset-password", body={
        "token": "anytoken", "new_password": "short",
    }))
    assert resp["statusCode"] == 400


def test_forgot_password_unknown_email_returns_200(ddb_table, mocker):
    mock_send = mocker.patch("routes.auth_routes._send_reset_email")
    from router import route
    resp = route(make_event("POST", "/auth/forgot-password", body={"email": "ghost@example.com"}))
    assert resp["statusCode"] == 200
    mock_send.assert_not_called()


def test_forgot_password_sends_email(ddb_table, mocker):
    mocker.patch("routes.auth_routes._send_verification_email")
    mock_send = mocker.patch("routes.auth_routes._send_reset_email")
    from router import route
    route(make_event("POST", "/auth/register", body={
        "email": "ron@example.com", "password": "Secure123!", "name": "Ron", "identity": "Jamf",
    }))
    resp = route(make_event("POST", "/auth/forgot-password", body={"email": "ron@example.com"}))
    assert resp["statusCode"] == 200
    mock_send.assert_called_once()


def test_forgot_password_oauth_only_user_returns_200(ddb_table, mocker):
    mock_send = mocker.patch("routes.auth_routes._send_reset_email")
    from router import route
    from models.users import create_user
    create_user("oauth@example.com", "OAuth User", "Other")  # no password
    resp = route(make_event("POST", "/auth/forgot-password", body={"email": "oauth@example.com"}))
    assert resp["statusCode"] == 200
    mock_send.assert_not_called()
```

- [ ] **Run — expect failures**
```bash
cd backend && pytest tests/test_auth_routes.py -k "forgot or reset_password" -v
```
Expected: ImportError or AttributeError on missing functions.

- [ ] **Implement model functions** — append to `backend/models/users.py`:

```python
def create_password_reset_token(user_id: str) -> str:
    table = get_table()
    token = secrets.token_urlsafe(32)
    ttl = int(time.time()) + 3600
    table.put_item(Item={
        "PK": f"RESET#{token}",
        "SK": "TOKEN",
        "user_id": user_id,
        "ttl": ttl,
    })
    return token


def consume_password_reset_token(token: str) -> str | None:
    table = get_table()
    resp = table.get_item(Key={"PK": f"RESET#{token}", "SK": "TOKEN"})
    item = resp.get("Item")
    if not item:
        return None
    table.delete_item(Key={"PK": f"RESET#{token}", "SK": "TOKEN"})
    return item["user_id"]


def update_user_password(user_id: str, new_password: str):
    table = get_table()
    table.update_item(
        Key={"PK": f"USER#{user_id}", "SK": "PROFILE"},
        UpdateExpression="SET password_hash = :h",
        ExpressionAttributeValues={":h": _hash_password(new_password)},
    )
```

- [ ] **Commit**
```bash
git add backend/models/users.py
git commit -m "feat: add password reset token model functions"
```

---

### Task 2: Backend route handlers

**Files:**
- Modify: `backend/routes/auth_routes.py`

- [ ] **Add `_send_reset_email`, `forgot_password`, `reset_password`** to `auth_routes.py`

Update the import at the top:
```python
from models.users import (
    get_user_by_id, get_user_by_email, create_user, verify_user_password,
    mark_email_verified, update_user_profile, create_email_verify_token,
    consume_email_verify_token, create_refresh_token, consume_refresh_token,
    delete_refresh_token, get_or_create_oauth_user,
    create_password_reset_token, consume_password_reset_token, update_user_password,
)
```

Add after `_send_verification_email`:
```python
def _send_reset_email(email: str, token: str):
    import boto3
    ses = boto3.client("ses", region_name="us-east-1")
    sender = os.environ["SES_SENDER_EMAIL"]
    base_url = os.environ.get("FRONTEND_URL", "https://dkdwnfmhg75yf.cloudfront.net")
    reset_url = f"{base_url}/#/reset-password?token={token}"
    ses.send_email(
        Source=sender,
        Destination={"ToAddresses": [email]},
        Message={
            "Subject": {"Data": "Reset your password — Ron's Portfolio"},
            "Body": {"Text": {"Data": f"Click to reset your password: {reset_url}\n\nThis link expires in 1 hour."}},
        },
    )
```

Add before `login`:
```python
def forgot_password(event, path_params, body, query, headers):
    email = (body.get("email") or "").strip().lower()
    if not email:
        return bad_request("email is required")
    safe_msg = "If that address is registered, a reset link is on its way."
    user = get_user_by_email(email)
    if not user or not user.get("password_hash"):
        return ok({"message": safe_msg})
    token = create_password_reset_token(user["user_id"])
    try:
        _send_reset_email(email, token)
    except Exception:
        return server_error("Could not send reset email. Please try again later.")
    return ok({"message": safe_msg})


def reset_password(event, path_params, body, query, headers):
    token = (body.get("token") or "").strip()
    new_password = body.get("new_password", "")
    if not token or not new_password:
        return bad_request("token and new_password are required")
    if len(new_password) < 8:
        return bad_request("password must be at least 8 characters")
    user_id = consume_password_reset_token(token)
    if not user_id:
        return bad_request("Invalid or expired reset link")
    update_user_password(user_id, new_password)
    return ok({"message": "Password updated. You can now log in."})
```

- [ ] **Run tests — expect all to pass**
```bash
cd backend && pytest tests/test_auth_routes.py -v
```
Expected: 17 passed.

- [ ] **Commit**
```bash
git add backend/routes/auth_routes.py
git commit -m "feat: add forgot-password and reset-password route handlers"
```

---

### Task 3: Register routes + full test run

**Files:**
- Modify: `backend/router.py`

- [ ] **Add routes** after `/auth/resend-verification`:
```python
("POST",   "/auth/forgot-password",        auth_routes.forgot_password),
("POST",   "/auth/reset-password",         auth_routes.reset_password),
```

- [ ] **Run full suite**
```bash
cd backend && pytest tests/ -v
```
Expected: 85 passed.

- [ ] **Commit**
```bash
git add backend/router.py
git commit -m "feat: register forgot-password and reset-password routes"
```

---

### Task 4: Update login.js

**Files:**
- Modify: `frontend/assets/js/pages/login.js`

- [ ] **Replace entire file contents:**

```javascript
// frontend/assets/js/pages/login.js
function loginPage() {
  return {
    form: { email: "", password: "", remember_me: false },
    submitting: false,
    error: null,
    unverifiedEmail: null,
    resendSending: false,
    resendSent: false,

    async init() {
      const token = localStorage.getItem("access_token");
      if (token) window.location.hash = "#/";
    },

    async submit() {
      this.error = null;
      this.unverifiedEmail = null;
      this.resendSent = false;
      if (!this.form.email || !this.form.password) {
        this.error = "Email and password are required.";
        return;
      }
      this.submitting = true;
      const app = document.querySelector("[x-data]")._x_dataStack?.[0];
      const result = app
        ? await app.login(this.form.email, this.form.password, this.form.remember_me)
        : await api.post("/auth/login", { email: this.form.email, password: this.form.password, remember_me: this.form.remember_me });

      if (result?.ok || result?.data?.access_token) {
        const returnTo = sessionStorage.getItem("returnTo") || "#/";
        sessionStorage.removeItem("returnTo");
        window.location.hash = returnTo.replace(/^#/, "");
      } else {
        this.error = result?.error || "Invalid email or password.";
        if (this.error === "Please verify your email before logging in") {
          this.unverifiedEmail = this.form.email;
        }
      }
      this.submitting = false;
    },

    async resendVerification() {
      this.resendSending = true;
      this.resendSent = false;
      await api.post("/auth/resend-verification", { email: this.unverifiedEmail });
      this.resendSent = true;
      this.resendSending = false;
    },

    loginWithGithub() {
      window.location.href = `${API_BASE}/auth/oauth/github`;
    },

    loginWithGoogle() {
      window.location.href = `${API_BASE}/auth/oauth/google`;
    },
  };
}
```

- [ ] **Commit**
```bash
git add frontend/assets/js/pages/login.js
git commit -m "feat: add resend-verification and forgot-password support to login page"
```

---

### Task 5: Update register.js

**Files:**
- Modify: `frontend/assets/js/pages/register.js`

- [ ] **Replace entire file contents:**

```javascript
// frontend/assets/js/pages/register.js
function registerPage() {
  return {
    form: { name: "", email: "", password: "", identity: "Other" },
    identities: ["Jamf", "MCRI", "Friend", "Family", "Other"],
    submitting: false,
    error: null,
    success: null,
    submittedEmail: null,
    resendSending: false,
    resendSent: false,
    resendError: null,

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
        this.submittedEmail = this.form.email;
        this.success = "Account created! Check your email to verify your account.";
        this.form = { name: "", email: "", password: "", identity: "Other" };
      } else {
        this.error = resp.error;
      }
      this.submitting = false;
    },

    async resendVerification() {
      this.resendSending = true;
      this.resendSent = false;
      this.resendError = null;
      const resp = await api.post("/auth/resend-verification", { email: this.submittedEmail });
      if (resp.ok) {
        this.resendSent = true;
      } else {
        this.resendError = resp.error || "Could not resend. Please try again.";
      }
      this.resendSending = false;
    },
  };
}
```

- [ ] **Commit**
```bash
git add frontend/assets/js/pages/register.js
git commit -m "feat: add resend-verification button to register success state"
```

---

### Task 6: Create forgot-password.js

**Files:**
- Create: `frontend/assets/js/pages/forgot-password.js`

- [ ] **Write file:**

```javascript
// frontend/assets/js/pages/forgot-password.js
function forgotPasswordPage() {
  return {
    form: { email: "" },
    submitting: false,
    sent: false,
    error: null,

    async submit() {
      this.error = null;
      if (!this.form.email) {
        this.error = "Email is required.";
        return;
      }
      this.submitting = true;
      const resp = await api.post("/auth/forgot-password", { email: this.form.email });
      if (resp.ok) {
        this.sent = true;
      } else {
        this.error = resp.error || "Something went wrong. Please try again.";
      }
      this.submitting = false;
    },
  };
}
```

- [ ] **Commit**
```bash
git add frontend/assets/js/pages/forgot-password.js
git commit -m "feat: add forgot-password page component"
```

---

### Task 7: Create reset-password.js

**Files:**
- Create: `frontend/assets/js/pages/reset-password.js`

- [ ] **Write file:**

```javascript
// frontend/assets/js/pages/reset-password.js
function resetPasswordPage() {
  return {
    form: { new_password: "", confirm_password: "" },
    token: null,
    submitting: false,
    success: false,
    error: null,

    init() {
      const hash = window.location.hash;
      const queryStart = hash.indexOf("?");
      this.token = queryStart >= 0
        ? new URLSearchParams(hash.slice(queryStart)).get("token")
        : null;
      if (!this.token) {
        this.error = "No reset token found. Please request a new password reset link.";
      }
    },

    async submit() {
      this.error = null;
      if (!this.form.new_password || !this.form.confirm_password) {
        this.error = "Both fields are required.";
        return;
      }
      if (this.form.new_password !== this.form.confirm_password) {
        this.error = "Passwords do not match.";
        return;
      }
      if (this.form.new_password.length < 8) {
        this.error = "Password must be at least 8 characters.";
        return;
      }
      this.submitting = true;
      const resp = await api.post("/auth/reset-password", {
        token: this.token,
        new_password: this.form.new_password,
      });
      if (resp.ok) {
        this.success = true;
        setTimeout(() => { window.location.hash = "#/login"; }, 2000);
      } else {
        this.error = resp.error || "Something went wrong. Please try again.";
      }
      this.submitting = false;
    },
  };
}
```

- [ ] **Commit**
```bash
git add frontend/assets/js/pages/reset-password.js
git commit -m "feat: add reset-password page component"
```

---

### Task 8: Update app.js routing

**Files:**
- Modify: `frontend/assets/js/app.js`

- [ ] **Add two entries to the routes object** (after `"verify-email": "verify-email"`):

```javascript
"forgot-password": "forgot-password",
"reset-password":  "reset-password",
```

- [ ] **Commit**
```bash
git add frontend/assets/js/app.js
git commit -m "feat: add forgot-password and reset-password routes to app router"
```

---

### Task 9: Update index.html

**Files:**
- Modify: `frontend/index.html`

- [ ] **Login error block** — replace the current error div (around line 776):

Old:
```html
            <div x-show="error" class="alert alert-error" style="margin-top: 1rem;" x-text="error"></div>
```
New:
```html
            <div x-show="error" class="alert alert-error" style="margin-top: 1rem;">
              <span x-text="error"></span>
              <template x-if="unverifiedEmail">
                <div style="margin-top: 0.75rem;">
                  <button class="btn btn-outline btn-sm" @click="resendVerification()" :disabled="resendSending">
                    <span x-text="resendSending ? 'Sending...' : 'Resend verification email'"></span>
                  </button>
                  <span x-show="resendSent" style="margin-left: 0.5rem; font-size: 0.85rem; color: green;">Email sent!</span>
                </div>
              </template>
            </div>
```

- [ ] **Login footer links** — replace the current sign-up paragraph (around line 815):

Old:
```html
            <p style="text-align: center; margin-top: 1rem; font-size: 0.9rem; color: var(--text-muted);">
              Don't have an account? <a href="#/register">Sign up</a>
            </p>
```
New:
```html
            <p style="text-align: center; margin-top: 1rem; font-size: 0.9rem; color: var(--text-muted);">
              <a href="#/forgot-password">Forgot password?</a>
              &nbsp;&middot;&nbsp;
              Don't have an account? <a href="#/register">Sign up</a>
            </p>
```

- [ ] **Register success block** — replace the current success div (around line 830):

Old:
```html
            <div x-show="success" class="alert alert-success" style="margin-top: 1rem;" x-text="success"></div>
```
New:
```html
            <div x-show="success" class="alert alert-success" style="margin-top: 1rem;">
              <span x-text="success"></span>
              <div style="margin-top: 0.75rem;">
                <p style="font-size: 0.85rem; margin-bottom: 0.4rem;">Didn't receive it?</p>
                <button class="btn btn-outline btn-sm" @click="resendVerification()" :disabled="resendSending">
                  <span x-text="resendSending ? 'Sending...' : 'Resend verification email'"></span>
                </button>
                <span x-show="resendSent" style="display: block; margin-top: 0.4rem; font-size: 0.85rem; color: green;">New email sent!</span>
                <span x-show="resendError" x-text="resendError" style="display: block; margin-top: 0.4rem; font-size: 0.85rem; color: red;"></span>
              </div>
            </div>
```

- [ ] **Add forgot-password page** — insert before `<!-- 404 -->`:

```html
      <!-- FORGOT PASSWORD -->
      <div x-show="currentPage === 'forgot-password'" class="page">
        <div x-data="forgotPasswordPage()">
          <div style="max-width: 400px; margin: 3rem auto;">
            <h1>Forgot password?</h1>
            <p class="subtitle">Enter your email and we'll send you a reset link. Valid for 1 hour.</p>
            <div x-show="error" class="alert alert-error" style="margin-top: 1rem;" x-text="error"></div>
            <div x-show="sent" class="alert alert-success" style="margin-top: 1rem;">
              If that address is registered, a reset link is on its way. Check your inbox.
            </div>
            <form @submit.prevent="submit()" style="margin-top: 1.5rem;" x-show="!sent">
              <div class="form-group">
                <label>Email</label>
                <input x-model="form.email" type="email" class="form-input" placeholder="you@example.com" required>
              </div>
              <button type="submit" class="btn btn-primary" style="width: 100%;" :disabled="submitting">
                <span x-text="submitting ? 'Sending...' : 'Send reset link'"></span>
              </button>
            </form>
            <p style="text-align: center; margin-top: 1rem; font-size: 0.9rem; color: var(--text-muted);">
              <a href="#/login">&larr; Back to login</a>
            </p>
          </div>
        </div>
      </div>

      <!-- RESET PASSWORD -->
      <div x-show="currentPage === 'reset-password'" class="page">
        <div x-data="resetPasswordPage()" x-init="init()">
          <div style="max-width: 400px; margin: 3rem auto;">
            <h1>Set a new password</h1>
            <div x-show="error" class="alert alert-error" style="margin-top: 1rem;">
              <span x-text="error"></span>
              <a href="#/forgot-password" style="display: block; margin-top: 0.5rem; font-size: 0.85rem;">Request a new link &rarr;</a>
            </div>
            <div x-show="success" class="alert alert-success" style="margin-top: 1rem;">
              Password updated! Redirecting to login...
            </div>
            <form @submit.prevent="submit()" style="margin-top: 1.5rem;" x-show="!success && token">
              <div class="form-group">
                <label>New password</label>
                <input x-model="form.new_password" type="password" class="form-input" placeholder="Min. 8 characters" required>
              </div>
              <div class="form-group">
                <label>Confirm password</label>
                <input x-model="form.confirm_password" type="password" class="form-input" placeholder="Repeat password" required>
              </div>
              <button type="submit" class="btn btn-primary" style="width: 100%;" :disabled="submitting">
                <span x-text="submitting ? 'Updating...' : 'Reset password'"></span>
              </button>
            </form>
          </div>
        </div>
      </div>

```

- [ ] **Add script tags** — insert before the Alpine.js script tag:

```html
  <script src="/assets/js/pages/forgot-password.js"></script>
  <script src="/assets/js/pages/reset-password.js"></script>
```

- [ ] **Commit**
```bash
git add frontend/index.html
git commit -m "feat: add forgot/reset password pages and resend verification buttons to HTML"
```

---

### Task 10: Commit version bump + final verification

- [ ] **Commit version.txt**
```bash
git add version.txt
git commit -m "chore: bump version to 1.1"
```

- [ ] **Run full backend test suite one last time**
```bash
cd backend && pytest tests/ -v
```
Expected: 85 passed.

- [ ] **Done** — branch `feature/fix-ses-email-verification` is ready to merge to `dev`.
