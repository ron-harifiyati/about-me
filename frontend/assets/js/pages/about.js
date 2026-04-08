// frontend/assets/js/pages/about.js
function aboutPage() {
  return {
    about: null,
    timeline: [],
    languages: [],
    hobbies: [],
    learning: [],
    values: [],
    loading: true,

    async init() {
      const [aboutResp, timelineResp, langResp, hobbiesResp, learningResp, valuesResp] = await Promise.all([
        api.get("/about"),
        api.get("/timeline"),
        api.get("/languages"),
        api.get("/hobbies"),
        api.get("/currently-learning"),
        api.get("/values"),
      ]);
      this.about = aboutResp.data;
      this.timeline = timelineResp.data?.events || [];
      this.languages = langResp.data?.languages || [];
      this.hobbies = hobbiesResp.data?.items || [];
      this.learning = learningResp.data?.items || [];
      this.values = valuesResp.data?.values || [];
      this.loading = false;
      this.$nextTick(() => initScrollAnimations());
    },
  };
}
