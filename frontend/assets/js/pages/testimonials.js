// frontend/assets/js/pages/testimonials.js
function testimonialsPage() {
  return {
    testimonials: [],
    filtered: [],
    activeFilter: "all",
    identities: ["all"],
    form: { body: "", author: "", identity: "Other", anonymous: false },
    loading: true,
    submitting: false,
    showModal: false,
    error: null,
    success: null,

    async init() {
      const resp = await api.get("/testimonials");
      this.testimonials = resp.data || [];
      this.filtered = this.testimonials;
      // Build identity filter list from actual data
      const seen = new Set(this.testimonials.map(t => t.identity).filter(Boolean));
      this.identities = ["all", ...Array.from(seen)];
      this.loading = false;
      this.$nextTick(() => initScrollAnimations());
    },

    setFilter(identity) {
      this.activeFilter = identity;
      this.filtered = identity === "all"
        ? this.testimonials
        : this.testimonials.filter(t => t.identity === identity);
    },

    async submit() {
      this.error = null;
      this.success = null;
      if (!this.form.body.trim()) {
        this.error = "Please write your testimonial.";
        return;
      }
      this.submitting = true;
      const resp = await api.post("/testimonials", this.form);
      if (resp.ok) {
        this.success = "Thank you! Your testimonial is pending approval.";
        this.form = { body: "", author: "", identity: "Other", anonymous: false };
        setTimeout(() => { this.showModal = false; this.success = null; }, 2000);
      } else {
        this.error = resp.error;
      }
      this.submitting = false;
    },
  };
}
