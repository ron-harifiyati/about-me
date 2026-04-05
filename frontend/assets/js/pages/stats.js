// frontend/assets/js/pages/stats.js
function statsPage() {
  return {
    locations: [],
    total: 0,
    pageviews: null,
    sortedPageviews: [],
    loading: true,
    map: null,

    async init() {
      try {
        const [visitorsResp, pageviewsResp] = await Promise.all([
          api.get("/stats/visitors"),
          api.get("/stats/pageviews"),
        ]);
        this.locations = visitorsResp.data || [];
        this.total = this.locations.length;
        this.pageviews = pageviewsResp.data || { by_page: {}, total: 0 };
        this.sortedPageviews = Object.entries(this.pageviews.by_page)
          .sort((a, b) => b[1] - a[1]);
      } finally {
        this.loading = false;
      }
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
      if (this._outsideClick) document.removeEventListener("click", this._outsideClick);
      const el = document.getElementById("visitor-map");
      if (!el || typeof L === "undefined") return;

      this.map = L.map("visitor-map", {
        zoomControl: true,
        minZoom: 2,
        maxZoom: 18,
        scrollWheelZoom: false,
      }).setView([20, 0], 2);

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 18,
      }).addTo(this.map);

      this.locations.forEach(loc => {
        if (loc.lat && loc.lon) {
          L.circleMarker([parseFloat(loc.lat), parseFloat(loc.lon)], {
            radius: 5,
            fillColor: "#e53e3e",
            color: "transparent",
            fillOpacity: 0.7,
          })
          .addTo(this.map)
          .bindPopup(`${loc.city || ""}${loc.city ? ", " : ""}${loc.country || "Unknown"}`);
        }
      });

      // Click-to-activate scroll zoom with hint overlay
      const hint = document.createElement("div");
      hint.className = "map-hint";
      hint.innerHTML = "<span>Click to interact</span>";
      this.map.getContainer().appendChild(hint);

      this.map.on("click", () => {
        hint.style.display = "none";
        this.map.scrollWheelZoom.enable();
      });

      this._outsideClick = (e) => {
        if (!this.map.getContainer().contains(e.target)) {
          hint.style.display = "";
          this.map.scrollWheelZoom.disable();
        }
      };
      document.addEventListener("click", this._outsideClick);
    },

    destroy() {
      if (this.map) { this.map.remove(); this.map = null; }
      if (this._themeHandler) window.removeEventListener("themechange", this._themeHandler);
      if (this._outsideClick) document.removeEventListener("click", this._outsideClick);
    },
  };
}
