// frontend/assets/js/pages/verify-email.js
function verifyEmailPage() {
  return {
    status: "loading",  // loading | success | error
    message: "",

    async init() {
      // Token comes from URL query string: /verify-email?token=xxx
      // With hash routing it arrives as: #/verify-email?token=xxx
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

      const resp = await api.post("/auth/verify-email", { token });
      if (resp.ok) {
        this.status = "success";
        this.message = resp.data?.message || "Email verified! You can now log in.";
        // Auto-redirect to login after 3s
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
