// frontend/assets/js/pages/stats.js
function statsPage() {
  return {
    locations: [],
    total: 0,
    loading: true,
    map: null,

    async init() {
      const resp = await api.get("/stats/visitors");
      this.locations = resp.data || [];
      this.total = this.locations.length;
      this.loading = false;
      await this.loadLeaflet();
      await this.$nextTick();
      this.initMap();
      this._themeHandler = () => this.initMap();
      window.addEventListener("themechange", this._themeHandler);
    },

    async loadLeaflet() {
      if (window.L) return;
      await new Promise((resolve, reject) => {
        const link = document.createElement("link");
        link.rel = "stylesheet";
        link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
        document.head.appendChild(link);
        const script = document.createElement("script");
        script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
      });
    },

    initMap() {
      if (this.map) { this.map.remove(); this.map = null; }
      const el = document.getElementById("visitor-map");
      if (!el || typeof L === "undefined") return;

      this.map = L.map("visitor-map", { zoomControl: true }).setView([20, 0], 2);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 18,
      }).addTo(this.map);

      this.locations.forEach(loc => {
        if (loc.lat && loc.lon) {
          L.circleMarker([parseFloat(loc.lat), parseFloat(loc.lon)], {
            radius: 5,
            fillColor: getComputedStyle(document.documentElement).getPropertyValue("--accent").trim() || "#007BFF",
            color: "transparent",
            fillOpacity: 0.7,
          })
          .addTo(this.map)
          .bindPopup(`${loc.city || ""}${loc.city ? ", " : ""}${loc.country || "Unknown"}`);
        }
      });
    },

    destroy() {
      if (this.map) { this.map.remove(); this.map = null; }
      if (this._themeHandler) window.removeEventListener("themechange", this._themeHandler);
    },
  };
}
