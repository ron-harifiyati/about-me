// frontend/assets/js/pages/home.js
function homePage() {
  return {
    funFact: null,
    ticker: [],
    loading: true,

    async init() {
      const [factResp, tickerResp] = await Promise.all([
        api.get("/fun-fact"),
        api.get("/currently-learning"),
      ]);
      this.funFact = factResp.data?.fact || null;
      this.ticker = tickerResp.data?.items || [];
      this.loading = false;
    },

    refreshFact() {
      api.get("/fun-fact").then(r => { this.funFact = r.data?.fact || null; });
    },
  };
}
