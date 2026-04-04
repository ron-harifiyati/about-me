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
