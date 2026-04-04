// frontend/assets/js/pages/login.js
function loginPage() {
  return {
    form: { email: "", password: "", remember_me: false },
    submitting: false,
    error: null,
    unverifiedEmail: null,
    resendSending: false,
    resendSent: false,
    resendError: null,

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
      this.resendError = null;
      const resp = await api.post("/auth/resend-verification", { email: this.unverifiedEmail });
      if (resp.ok) {
        this.resendSent = true;
      } else {
        this.resendError = resp.error || "Could not resend. Please try again.";
      }
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
