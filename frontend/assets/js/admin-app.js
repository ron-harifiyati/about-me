// frontend/assets/js/admin-app.js

function adminApp() {
  return {
    user: null,
    loading: true,
    section: "dashboard",
    stats: {},

    async init() {
      loadTheme();
      const token = localStorage.getItem("access_token");
      if (!token) { this.loading = false; return; }
      const resp = await api.get("/auth/me");
      if (resp.ok && resp.data?.role === "admin") {
        this.user = resp.data;
        await this.loadStats();
      }
      this.loading = false;
    },

    get isAdmin() { return this.user?.role === "admin"; },

    async loadStats() {
      const [users, contacts, testimonials] = await Promise.all([
        api.get("/admin/users"),
        api.get("/admin/contacts"),
        api.get("/admin/testimonials/pending"),
      ]);
      this.stats = {
        users: users.data?.length || 0,
        contacts: contacts.data?.length || 0,
        pending_testimonials: testimonials.data?.length || 0,
      };
    },
  };
}

// ── Section components ────────────────────────────────────────────────────

function adminContent() {
  return {
    activeTab: "about",
    about: {},
    skills: {},
    funFacts: { facts: [] },
    currentlyLearning: { items: [] },
    saving: false,
    success: null,

    async init() {
      const [a, s, f, c] = await Promise.all([
        api.get("/about"), api.get("/skills"), api.get("/fun-fact"), api.get("/currently-learning"),
      ]);
      this.about = a.data || {};
      this.skills = s.data || {};
      this.funFacts = { facts: [] };
      this.currentlyLearning = c.data || { items: [] };
    },

    async save(section, data) {
      this.saving = true; this.success = null;
      const resp = await api.put(`/${section}`, data);
      if (resp.ok) this.success = `${section} saved!`;
      this.saving = false;
    },
  };
}

function adminUsers() {
  return {
    users: [],
    loading: true,

    async init() {
      const resp = await api.get("/admin/users");
      this.users = resp.data || [];
      this.loading = false;
    },

    async setStatus(userId, status) {
      await api.put(`/admin/users/${userId}`, { status });
      const u = this.users.find(u => u.user_id === userId);
      if (u) u.status = status;
    },

    async deleteUser(userId) {
      if (!confirm("Delete this user? This cannot be undone.")) return;
      await api.delete(`/admin/users/${userId}`);
      this.users = this.users.filter(u => u.user_id !== userId);
    },
  };
}

function adminContacts() {
  return {
    contacts: [],
    loading: true,
    async init() {
      const resp = await api.get("/admin/contacts");
      this.contacts = resp.data || [];
      this.loading = false;
    },
    formatDate(ts) { return ts ? new Date(ts * 1000).toLocaleString() : ""; },
  };
}

function adminTestimonials() {
  return {
    pending: [],
    loading: true,

    async init() {
      const resp = await api.get("/admin/testimonials/pending");
      this.pending = resp.data || [];
      this.loading = false;
    },

    async action(id, action) {
      await api.put(`/admin/testimonials/${id}`, { action });
      this.pending = this.pending.filter(t => t.testimonial_id !== id);
    },
  };
}

function adminProjects() {
  return {
    projects: [],
    loading: true,
    saving: false,
    error: null,
    success: null,
    showModal: false,
    editing: null,
    form: { title: "", description: "", tech_stack: "", github: "", live: "" },

    async init() {
      const resp = await api.get("/projects");
      this.projects = resp.data || [];
      this.loading = false;
    },

    openCreate() {
      this.editing = null;
      this.form = { title: "", description: "", tech_stack: "", github: "", live: "" };
      this.error = null;
      this.showModal = true;
    },

    openEdit(p) {
      this.editing = p.id;
      this.form = {
        title: p.title || "",
        description: p.description || "",
        tech_stack: (p.tech_stack || []).join(", "),
        github: p.links?.github || "",
        live: p.links?.live || "",
      };
      this.error = null;
      this.showModal = true;
    },

    closeModal() {
      this.showModal = false;
      this.editing = null;
      this.error = null;
    },

    async save() {
      this.error = null;
      if (!this.form.title.trim()) { this.error = "Title is required."; return; }
      this.saving = true;
      const payload = {
        title: this.form.title.trim(),
        description: this.form.description.trim(),
        tech_stack: this.form.tech_stack.split(",").map(s => s.trim()).filter(Boolean),
        links: {
          github: this.form.github.trim() || null,
          live: this.form.live.trim() || null,
        },
      };
      const resp = this.editing
        ? await api.put(`/projects/${this.editing}`, payload)
        : await api.post("/projects", payload);
      if (resp.ok) {
        const r = await api.get("/projects");
        this.projects = r.data || [];
        this.success = this.editing ? "Project updated." : "Project created.";
        this.closeModal();
        setTimeout(() => { this.success = null; }, 3000);
      } else {
        this.error = resp.error;
      }
      this.saving = false;
    },

    async deleteProject(id) {
      if (!confirm("Delete this project? This cannot be undone.")) return;
      await api.delete(`/projects/${id}`);
      this.projects = this.projects.filter(p => p.id !== id);
    },
  };
}

function adminCourses() {
  return {
    courses: [],
    loading: true,
    saving: false,
    error: null,
    success: null,
    showModal: false,
    editing: null,
    form: { title: "", description: "", platform: "", link: "" },

    async init() {
      const resp = await api.get("/courses");
      this.courses = resp.data || [];
      this.loading = false;
    },

    openCreate() {
      this.editing = null;
      this.form = { title: "", description: "", platform: "", link: "" };
      this.error = null;
      this.showModal = true;
    },

    openEdit(c) {
      this.editing = c.id;
      this.form = {
        title: c.title || "",
        description: c.description || "",
        platform: c.platform || "",
        link: c.link || "",
      };
      this.error = null;
      this.showModal = true;
    },

    closeModal() {
      this.showModal = false;
      this.editing = null;
      this.error = null;
    },

    async save() {
      this.error = null;
      if (!this.form.title.trim()) { this.error = "Title is required."; return; }
      this.saving = true;
      const payload = {
        title: this.form.title.trim(),
        description: this.form.description.trim(),
        platform: this.form.platform.trim(),
        link: this.form.link.trim() || null,
      };
      const resp = this.editing
        ? await api.put(`/courses/${this.editing}`, payload)
        : await api.post("/courses", payload);
      if (resp.ok) {
        const r = await api.get("/courses");
        this.courses = r.data || [];
        this.success = this.editing ? "Course updated." : "Course created.";
        this.closeModal();
        setTimeout(() => { this.success = null; }, 3000);
      } else {
        this.error = resp.error;
      }
      this.saving = false;
    },

    async deleteCourse(id) {
      if (!confirm("Delete this course? This cannot be undone.")) return;
      await api.delete(`/courses/${id}`);
      this.courses = this.courses.filter(c => c.id !== id);
    },
  };
}

function adminQuiz() {
  return {
    questions: [],
    loading: true,
    form: { question: "", options: ["", "", "", ""], answer: "", topic: "general" },
    editing: null,
    saving: false,
    error: null,

    async init() {
      const resp = await api.get("/admin/quiz/questions");
      this.questions = resp.data || [];
      this.loading = false;
    },

    async save() {
      this.error = null;
      if (!this.form.question || !this.form.answer) {
        this.error = "Question and answer are required."; return;
      }
      this.saving = true;
      const resp = this.editing
        ? await api.put(`/admin/quiz/questions/${this.editing}`, this.form)
        : await api.post("/admin/quiz/questions", this.form);
      if (resp.ok) {
        const resp2 = await api.get("/admin/quiz/questions");
        this.questions = resp2.data || [];
        this.resetForm();
      } else {
        this.error = resp.error;
      }
      this.saving = false;
    },

    editQuestion(q) {
      this.editing = q.question_id;
      this.form = { question: q.question, options: [...q.options], answer: q.answer, topic: q.topic };
    },

    async deleteQuestion(id) {
      if (!confirm("Delete this question?")) return;
      await api.delete(`/admin/quiz/questions/${id}`);
      this.questions = this.questions.filter(q => q.question_id !== id);
    },

    resetForm() {
      this.editing = null;
      this.form = { question: "", options: ["", "", "", ""], answer: "", topic: "general" };
    },
  };
}
