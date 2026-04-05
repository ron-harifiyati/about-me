// frontend/assets/js/pages/skills.js
function skillsPage() {
  return {
    skills: null,
    loading: true,
    async init() {
      const resp = await api.get("/skills");
      this.skills = resp.data;
      this.loading = false;
      this.$nextTick(() => initScrollAnimations());
    },
    categories() {
      if (!this.skills) return [];
      return Object.keys(this.skills).filter(k => Array.isArray(this.skills[k]));
    },
  };
}
