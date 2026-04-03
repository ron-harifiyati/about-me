// frontend/assets/js/pages/guestbook.js
function guestbookPage() {
  return {
    entries: [],
    form: { name: "", message: "" },
    loading: true,
    submitting: false,
    error: null,
    success: null,

    async init() {
      const resp = await api.get("/guestbook");
      this.entries = resp.data || [];
      this.loading = false;
    },

    async submit() {
      this.error = null;
      this.success = null;
      if (!this.form.name || !this.form.message) {
        this.error = "Name and message are required.";
        return;
      }
      this.submitting = true;
      const resp = await api.post("/guestbook", this.form);
      if (resp.ok) {
        this.entries.unshift(resp.data);
        this.form = { name: "", message: "" };
        this.success = "Entry added!";
      } else {
        this.error = resp.error;
      }
      this.submitting = false;
    },

    formatDate(ts) {
      return ts ? new Date(ts * 1000).toLocaleDateString() : "";
    },
  };
}
