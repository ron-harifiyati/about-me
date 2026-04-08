// frontend/assets/js/pages/oauth-callback.js
function oauthCallbackPage() {
  return {
    error: null,

    async init() {
      // Tokens are in the hash: #/oauth-callback?access_token=...&refresh_token=...
      const hash = window.location.hash;
      const qIndex = hash.indexOf("?");
      if (qIndex === -1) {
        this.error = "Login failed. Please try again.";
        return;
      }
      const params = new URLSearchParams(hash.substring(qIndex));
      const accessToken = params.get("access_token");
      const refreshToken = params.get("refresh_token");

      if (!accessToken || !refreshToken) {
        this.error = "Login failed. Please try again.";
        return;
      }

      localStorage.setItem("access_token", accessToken);
      localStorage.setItem("refresh_token", refreshToken);

      // Let the root app pick up the new token and load the user profile
      const app = document.querySelector("[x-data]")?._x_dataStack?.[0];
      if (app) {
        app.accessToken = accessToken;
        const resp = await api.get("/auth/me");
        if (resp.ok && resp.data) {
          app.user = resp.data;
          if (resp.data.theme) {
            app.theme = resp.data.theme;
            applyTheme(resp.data.theme);
          }
        }
      }

      const returnTo = sessionStorage.getItem("returnTo") || "#/";
      sessionStorage.removeItem("returnTo");
      window.location.hash = returnTo.replace(/^#/, "");
    },
  };
}
