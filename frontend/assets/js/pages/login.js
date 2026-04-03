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
      window.location.href = `${API_BASE}/auth/oauth/github`;
    },

    loginWithGoogle() {
      window.location.href = `${API_BASE}/auth/oauth/google`;
    },
  };
}
