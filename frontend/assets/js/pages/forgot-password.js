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
