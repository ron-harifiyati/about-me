// frontend/assets/js/pages/developer.js
function developerPage() {
  return {
    apiUrl: null,
    meta: null,

    async init() {
      this.apiUrl = API_BASE;
      const resp = await api.get("/meta");
      this.meta = resp.data;
    },
  };
}
