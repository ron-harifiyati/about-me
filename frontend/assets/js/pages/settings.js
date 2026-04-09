// frontend/assets/js/pages/settings.js
function settingsPage() {
  return {
    activeSection: "profile",
    sections: ["profile", "appearance", "connections", "activity", "account"],

    // Profile
    profileForm: { name: "", identity: "Other" },
    profileDirty: false,
    profileSaving: false,
    profileMessage: null,

    // Appearance
    themes: ["light", "dark", "coffee", "terminal", "nordic"],

    // Connections
    connections: [],
    connectionsLoading: true,
    hasPassword: false,

    // Activity
    activityTab: "comments",
    activityData: { comments: [], ratings: [], quiz: [], guestbook: [], testimonials: [] },
    activityCounts: { comments: 0, ratings: 0, quiz: 0, guestbook: 0, testimonials: 0 },
    activityLoading: true,

    // Account
    deleteConfirmation: "",
    deleteError: null,
    deleting: false,

    async init() {
      const app = this.getApp();
      if (!app || !app.user) {
        window.location.hash = "#/login";
        return;
      }
      this.profileForm.name = app.user.name || "";
      this.profileForm.identity = app.user.identity || "Other";
      this.hasPassword = app.user.has_password || false;

      this.setupScrollSpy();
      await Promise.all([this.loadConnections(), this.loadActivity()]);
    },

    getApp() {
      const el = document.querySelector("[x-data]");
      return el?._x_dataStack?.[0];
    },

    setupScrollSpy() {
      const observer = new IntersectionObserver(
        (entries) => {
          for (const entry of entries) {
            if (entry.isIntersecting) {
              this.activeSection = entry.target.id.replace("settings-", "");
            }
          }
        },
        { rootMargin: "-20% 0px -70% 0px" }
      );
      this.$nextTick(() => {
        this.sections.forEach((s) => {
          const el = document.getElementById("settings-" + s);
          if (el) observer.observe(el);
        });
      });
    },

    scrollTo(section) {
      const el = document.getElementById("settings-" + section);
      if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    },

    onProfileChange() {
      const app = this.getApp();
      this.profileDirty =
        this.profileForm.name !== (app?.user?.name || "") ||
        this.profileForm.identity !== (app?.user?.identity || "Other");
    },

    async saveProfile() {
      this.profileSaving = true;
      this.profileMessage = null;
      const resp = await api.put("/auth/me", this.profileForm);
      if (resp.ok) {
        this.profileMessage = { type: "success", text: "Profile updated!" };
        const app = this.getApp();
        if (app) app.user = resp.data;
        this.profileDirty = false;
      } else {
        this.profileMessage = { type: "error", text: resp.error || "Failed to save" };
      }
      this.profileSaving = false;
    },

    async selectTheme(theme) {
      const app = this.getApp();
      if (app) {
        app.theme = theme;
        applyTheme(theme);
        await syncThemeToServer(theme);
      }
    },

    async loadConnections() {
      this.connectionsLoading = true;
      const resp = await api.get("/auth/me/connections");
      if (resp.ok) {
        this.connections = resp.data.providers || [];
      }
      this.connectionsLoading = false;
    },

    isConnected(provider) {
      return this.connections.some((c) => c.provider === provider);
    },

    getProviderUsername(provider) {
      const conn = this.connections.find((c) => c.provider === provider);
      return conn?.provider_username || "";
    },

    connectProvider(provider) {
      const token = localStorage.getItem("access_token");
      window.location.href = API_BASE + "/auth/oauth/" + provider + "?link=true&token=" + token;
    },

    async disconnectProvider(provider) {
      if (!confirm("Disconnect " + provider + "?")) return;
      const resp = await api.delete("/auth/me/oauth/" + provider);
      if (resp.ok) {
        this.connections = this.connections.filter((c) => c.provider !== provider);
      } else {
        alert(resp.error || "Failed to disconnect");
      }
    },

    async loadActivity() {
      this.activityLoading = true;
      const [comments, ratings, quiz, guestbook, testimonials] = await Promise.all([
        api.get("/auth/me/comments"),
        api.get("/auth/me/ratings"),
        api.get("/auth/me/quiz-scores"),
        api.get("/auth/me/guestbook-entries"),
        api.get("/auth/me/testimonials"),
      ]);
      this.activityData.comments = comments.ok ? comments.data : [];
      this.activityData.ratings = ratings.ok ? ratings.data : [];
      this.activityData.quiz = quiz.ok ? quiz.data : [];
      this.activityData.guestbook = guestbook.ok ? guestbook.data : [];
      this.activityData.testimonials = testimonials.ok ? testimonials.data : [];
      this.activityCounts = {
        comments: this.activityData.comments.length,
        ratings: this.activityData.ratings.length,
        quiz: this.activityData.quiz.length,
        guestbook: this.activityData.guestbook.length,
        testimonials: this.activityData.testimonials.length,
      };
      this.activityLoading = false;
    },

    async deleteComment(commentId) {
      if (!confirm("Delete this comment?")) return;
      const resp = await api.delete("/auth/me/comments/" + commentId);
      if (resp.ok) {
        this.activityData.comments = this.activityData.comments.filter((c) => c.comment_id !== commentId);
        this.activityCounts.comments--;
      }
    },

    async deleteGuestbookEntry(entryId) {
      if (!confirm("Delete this guestbook entry?")) return;
      const resp = await api.delete("/auth/me/guestbook-entries/" + entryId);
      if (resp.ok) {
        this.activityData.guestbook = this.activityData.guestbook.filter((e) => e.entry_id !== entryId);
        this.activityCounts.guestbook--;
      }
    },

    timeAgo(ts) {
      const diff = Math.floor(Date.now() / 1000) - ts;
      if (diff < 60) return "just now";
      if (diff < 3600) return Math.floor(diff / 60) + "m ago";
      if (diff < 86400) return Math.floor(diff / 3600) + "h ago";
      if (diff < 604800) return Math.floor(diff / 86400) + "d ago";
      return new Date(ts * 1000).toLocaleDateString();
    },

    async deleteAccount() {
      this.deleteError = null;
      if (this.deleteConfirmation !== "DELETE") {
        this.deleteError = "Type DELETE to confirm";
        return;
      }
      this.deleting = true;
      const resp = await apiFetch("/auth/me", { method: "DELETE", body: { confirmation: "DELETE" } });
      if (resp.ok) {
        const app = this.getApp();
        if (app) await app.logout();
      } else {
        this.deleteError = resp.error || "Failed to delete account";
        this.deleting = false;
      }
    },
  };
}
