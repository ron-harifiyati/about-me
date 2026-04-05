// frontend/assets/js/pages/about.js
function aboutPage() {
  return {
    about: null,
    timeline: [],
    loading: true,

    async init() {
      const [aboutResp, timelineResp] = await Promise.all([
        api.get("/about"),
        api.get("/timeline"),
      ]);
      this.about = aboutResp.data;
      this.timeline = timelineResp.data?.events || [];
      this.loading = false;
      this.$nextTick(() => initScrollAnimations());
    },
  };
}
