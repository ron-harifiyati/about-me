// frontend/assets/js/pages/courses.js
function coursesPage() {
  return {
    courses: [],
    loading: true,
    async init() {
      const resp = await api.get("/courses");
      this.courses = resp.data || [];
      this.loading = false;
      this.$nextTick(() => initScrollAnimations());
    },
    starsDisplay(avg) {
      if (!avg) return "No ratings yet";
      const full = Math.round(avg);
      return "★".repeat(full) + "☆".repeat(5 - full) + ` (${avg})`;
    },
  };
}

function courseDetailPage() {
  return {
    course: null,
    comments: [],
    ratings: null,
    newComment: "",
    newRating: 0,
    hoverRating: 0,
    loading: true,
    submitting: false,
    error: null,
    success: null,

    async init() {
      const appEl = document.querySelector("[x-data]");
      const appData = appEl._x_dataStack?.[0];
      const courseId = appData?.currentParams?.id;
      if (!courseId) { this.loading = false; return; }

      const [cResp, commResp, rResp] = await Promise.all([
        api.get(`/courses/${courseId}`),
        api.get(`/courses/${courseId}/comments`),
        api.get(`/courses/${courseId}/ratings`),
      ]);
      this.course = cResp.data;
      this.comments = commResp.data || [];
      this.ratings = rResp.data;
      this.loading = false;
    },

    async submitComment() {
      if (!this.newComment.trim()) return;
      this.submitting = true;
      const resp = await api.post(`/courses/${this.course.id}/comments`, { body: this.newComment });
      if (resp.ok) {
        this.comments.push(resp.data);
        this.newComment = "";
        this.success = "Comment posted!";
      } else {
        this.error = resp.error;
      }
      this.submitting = false;
    },

    async submitRating(stars) {
      this.newRating = stars;
      const resp = await api.post(`/courses/${this.course.id}/ratings`, { stars });
      if (resp.ok) this.ratings = resp.data;
    },
  };
}
