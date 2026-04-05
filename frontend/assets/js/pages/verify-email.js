// frontend/assets/js/pages/verify-email.js
function verifyEmailPage() {
  return {
    status: "ready",  // ready | loading | success | error
    message: "",
    _token: null,

    init() {
      const hash = window.location.hash;
      const queryStart = hash.indexOf("?");
      const token = queryStart >= 0
        ? new URLSearchParams(hash.slice(queryStart)).get("token")
        : null;

      if (!token) {
        this.status = "error";
        this.message = "No verification token found in URL.";
        return;
      }
      this._token = token;
      // status stays "ready" — waits for user to click the button
    },

    async verify() {
      if (this.status === "loading" || this.status === "success") return;
      this.status = "loading";
      const resp = await api.post("/auth/verify-email", { token: this._token });
      if (resp.ok) {
        this.status = "success";
        this.message = resp.data?.message || "Email verified! You can now log in.";
        setTimeout(() => { window.location.hash = "#/login"; }, 3000);
      } else {
        this.status = "error";
        this.message = resp.error === "Invalid or expired token"
          ? "This link has already been used or has expired. If you verified recently, try logging in."
          : (resp.error || "Verification failed. The link may have expired.");
      }
    },
  };
}
