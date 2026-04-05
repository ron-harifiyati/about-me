// frontend/assets/js/pages/verify-email.js
let _verifyInitCallCount = 0;

function verifyEmailPage() {
  return {
    status: "loading",  // loading | success | error
    message: "",

    async init() {
      _verifyInitCallCount++;
      const callN = _verifyInitCallCount;
      const hash = window.location.hash;
      const queryStart = hash.indexOf("?");
      const token = queryStart >= 0
        ? new URLSearchParams(hash.slice(queryStart)).get("token")
        : null;

      console.group("[verify-email] init() call #" + callN);
      console.log("hash:", hash);
      console.log("token extracted:", token ? token.slice(0, 12) + "..." : null);
      console.log("localStorage access_token present:", !!localStorage.getItem("access_token"));

      if (!token) {
        this.status = "error";
        this.message = "No verification token found in URL.";
        console.log("→ No token. Setting status=error");
        console.groupEnd();
        return;
      }

      const resp = await api.post("/auth/verify-email", { token });
      console.log("API response:", { ok: resp.ok, status: resp.status, error: resp.error, data: resp.data });

      if (resp.ok) {
        this.status = "success";
        this.message = resp.data?.message || "Email verified! You can now log in.";
        console.log("→ status=SUCCESS");
        setTimeout(() => { window.location.hash = "#/login"; }, 3000);
      } else {
        this.status = "error";
        this.message = resp.error === "Invalid or expired token"
          ? "This link has already been used or has expired. If you verified recently, try logging in."
          : (resp.error || "Verification failed. The link may have expired.");
        console.log("→ status=ERROR, message:", this.message);
      }
      console.groupEnd();
    },
  };
}
