// frontend/assets/js/pages/projects.js
function projectsPage() {
  return {
    projects: [],
    loading: true,
    async init() {
      const resp = await api.get("/projects");
      this.projects = resp.data || [];
      this.loading = false;
    },
    starsDisplay(avg) {
      if (!avg) return "No ratings yet";
      const full = Math.round(avg);
      return "★".repeat(full) + "☆".repeat(5 - full) + ` (${avg})`;
    },
  };
}

function projectDetailPage() {
  return {
    project: null,
    comments: [],
    ratings: null,
    newComment: "",
    newRating: 0,
    loading: true,
    submitting: false,
    error: null,
    success: null,

    async init() {
      const appEl = document.querySelector("body");
      const appData = appEl._x_dataStack?.[0];
      const projectId = appData?.currentParams?.id;
      if (!projectId) { this.loading = false; return; }

      const [pResp, cResp, rResp] = await Promise.all([
        api.get(`/projects/${projectId}`),
        api.get(`/projects/${projectId}/comments`),
        api.get(`/projects/${projectId}/ratings`),
      ]);
      this.project = pResp.data;
      this.comments = cResp.data || [];
      this.ratings = rResp.data;
      this.loading = false;
    },

    async submitComment() {
      if (!this.newComment.trim()) return;
      this.submitting = true;
      const id = this.project?.id;
      const resp = await api.post(`/projects/${id}/comments`, { body: this.newComment });
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
      const id = this.project?.id;
      const resp = await api.post(`/projects/${id}/ratings`, { stars });
      if (resp.ok) this.ratings = resp.data;
    },
  };
}
