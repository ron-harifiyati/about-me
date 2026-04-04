// frontend/assets/js/app.js

function portfolioApp() {
  return {
    // Auth state
    user: null,
    accessToken: null,

    // Router state
    currentPage: "home",
    currentParams: {},

    // UI state
    theme: "light",
    navOpen: false,

    async init() {
      // Easter egg
      console.log(
        "%c👋 Hey there, fellow developer!",
        "font-size: 16px; font-weight: bold; color: #007BFF;"
      );
      console.log(
        "%cYou found the console. Since you're here, the API is open — try:\n\n" +
        `  fetch('${DEV_API_URL}/meta').then(r=>r.json()).then(console.log)\n\n` +
        "Or visit #/developer for the full API docs.",
        "font-size: 13px; color: #6C757D;"
      );
      console.log(
        "%c— Ron",
        "font-style: italic; color: #6C757D;"
      );

      // Load theme
      this.theme = loadTheme();

      // Restore auth session
      const token = localStorage.getItem("access_token");
      if (token) {
        this.accessToken = token;
        const resp = await api.get("/auth/me");
        if (resp.ok) {
          this.user = resp.data;
          // Sync server theme
          if (resp.data.theme) {
            this.theme = resp.data.theme;
            applyTheme(resp.data.theme);
          }
        } else {
          // Token expired or invalid — clear it
          this.logout(false);
        }
      }

      // Initial route
      this.handleRoute(window.location.hash || "#/");
      window.addEventListener("hashchange", () => {
        this.handleRoute(window.location.hash);
        this.navOpen = false;
      });
    },

    handleRoute(hash) {
      const path = hash.replace(/^#/, "") || "/";
      const [base, ...rest] = path.split("/").filter(Boolean);

      // Route table
      const routes = {
        "":             "home",
        "home":         "home",
        "about":        "about",
        "projects":     rest.length ? "project-detail" : "projects",
        "courses":      rest.length ? "course-detail"  : "courses",
        "skills":       "skills",
        "stats":        "stats",
        "contact":      "contact",
        "guestbook":    "guestbook",
        "testimonials": "testimonials",
        "developer":    "developer",
        "quiz":         "quiz",
        "login":        "login",
        "register":     "register",
        "verify-email": "verify-email",
        "forgot-password": "forgot-password",
        "reset-password":  "reset-password",
      };

      this.currentPage = routes[base ?? ""] || "not-found";
      this.currentParams = { id: rest[0] };

      // Scroll to top on navigation
      window.scrollTo(0, 0);

      // Re-attach scroll observers after page change and restart page animation
      this.$nextTick(() => {
        initScrollAnimations();
        // Force page enter animation to replay on each navigation
        const page = document.querySelector(".page");
        if (page) {
          page.style.animation = "none";
          page.offsetHeight; // reflow
          page.style.animation = "";
        }
      });
    },

    navigate(page) {
      window.location.hash = `#/${page}`;
    },

    async toggleTheme() {
      this.theme = cycleTheme(this.theme);
      await syncThemeToServer(this.theme);
    },

    async login(email, password, rememberMe) {
      const resp = await api.post("/auth/login", { email, password, remember_me: rememberMe });
      if (resp.ok) {
        this.accessToken = resp.data.access_token;
        this.user = resp.data.user;
        localStorage.setItem("access_token", resp.data.access_token);
        localStorage.setItem("refresh_token", resp.data.refresh_token);
        return { ok: true };
      }
      return { ok: false, error: resp.error };
    },

    async logout(redirect = true) {
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) await api.post("/auth/logout", { refresh_token: refresh });
      this.user = null;
      this.accessToken = null;
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      if (redirect) this.navigate("home");
    },

    get isAuthenticated() { return !!this.user; },
    get isAdmin() { return this.user?.role === "admin"; },
    get greeting() {
      if (!this.user) return null;
      return `Welcome back, ${this.user.name}`;
    },
  };
}

// Scroll fade-in observer — attach to elements with class .fade-in
let _scrollObserver = null;

function initScrollAnimations() {
  // Disconnect previous observer so they don't stack across route changes
  if (_scrollObserver) {
    _scrollObserver.disconnect();
  }

  _scrollObserver = new IntersectionObserver(
    entries => entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        _scrollObserver.unobserve(entry.target);
      }
    }),
    { threshold: 0.05 }
  );

  // Only observe elements that are currently in a visible container
  // (offsetParent === null means an ancestor has display:none — skip those)
  document.querySelectorAll(".fade-in:not(.visible)").forEach(el => {
    if (el.offsetParent !== null) {
      _scrollObserver.observe(el);
    }
  });
}
