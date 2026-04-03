// frontend/assets/js/themes.js

const THEMES = ["light", "dark", "coffee", "terminal", "nordic"];

function applyTheme(theme) {
  if (!THEMES.includes(theme)) theme = "light";
  document.documentElement.setAttribute("data-theme", theme === "light" ? "" : theme);
  // Keep :root clean for light — remove attribute entirely
  if (theme === "light") {
    document.documentElement.removeAttribute("data-theme");
  }
  localStorage.setItem("theme", theme);
}

function loadTheme() {
  const saved = localStorage.getItem("theme") || "light";
  applyTheme(saved);
  return saved;
}

function cycleTheme(current) {
  const idx = THEMES.indexOf(current);
  const next = THEMES[(idx + 1) % THEMES.length];
  applyTheme(next);
  return next;
}

async function syncThemeToServer(theme) {
  const token = localStorage.getItem("access_token");
  if (!token) return;
  await api.put("/auth/me", { theme });
}

async function loadThemeFromServer() {
  const token = localStorage.getItem("access_token");
  if (!token) return loadTheme();
  const resp = await api.get("/auth/me");
  if (resp.ok && resp.data?.theme) {
    applyTheme(resp.data.theme);
    return resp.data.theme;
  }
  return loadTheme();
}
