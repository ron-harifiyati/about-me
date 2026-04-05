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

    get passwordStrength() {
      const p = this.form.password;
      if (!p) return 0;
      let score = 0;
      if (p.length >= 8)  score++;
      if (p.length >= 12) score++;
      if (/[A-Z]/.test(p)) score++;
      if (/[0-9]/.test(p)) score++;
      if (/[^A-Za-z0-9]/.test(p)) score++;
      return score; // 0–5
    },

    get passwordStrengthLabel() {
      const s = this.passwordStrength;
      if (s <= 1) return "Weak";
      if (s <= 3) return "Fair";
      if (s === 4) return "Good";
      return "Strong";
    },

    get passwordStrengthColor() {
      const s = this.passwordStrength;
      if (s <= 1) return "#DC3545";
      if (s <= 3) return "#FFC107";
      if (s === 4) return "#20C997";
      return "#28A745";
    },

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
