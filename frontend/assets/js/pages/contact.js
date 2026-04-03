// frontend/assets/js/pages/contact.js
function contactPage() {
  return {
    about: null,
    form: { name: "", email: "", message: "" },
    submitting: false,
    error: null,
    success: null,

    async init() {
      const resp = await api.get("/about");
      this.about = resp.data;
    },

    async submitForm() {
      this.error = null;
      this.success = null;
      if (!this.form.name || !this.form.email || !this.form.message) {
        this.error = "All fields are required.";
        return;
      }
      this.submitting = true;
      const resp = await api.post("/contact", this.form);
      if (resp.ok) {
        this.success = resp.data?.message || "Message sent!";
        this.form = { name: "", email: "", message: "" };
      } else {
        this.error = resp.error || "Something went wrong. Please try again.";
      }
      this.submitting = false;
    },
  };
}
