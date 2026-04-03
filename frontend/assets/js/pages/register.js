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
