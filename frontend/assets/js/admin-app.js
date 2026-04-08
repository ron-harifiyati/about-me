// frontend/assets/js/admin-app.js

function adminApp() {
  return {
    user: null,
    loading: true,
    section: "dashboard",
    sidebarOpen: false,
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
      const [users, contacts, testimonials, guestbook, analytics] = await Promise.all([
        api.get("/admin/users"),
        api.get("/admin/contacts"),
        api.get("/admin/testimonials/pending"),
        api.get("/guestbook"),
        api.get("/stats/analytics"),
      ]);
      const byPage = analytics.data?.by_page || {};
      const topPages = Object.entries(byPage)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3);
      const maxCount = topPages[0]?.[1] || 1;
      this.stats = {
        users: users.data?.length || 0,
        contacts: contacts.data?.length || 0,
        pending_testimonials: testimonials.data?.length || 0,
        guestbook: guestbook.data?.length || 0,
        unique_visitors: analytics.data?.unique_visitors || 0,
        total_pageviews: analytics.data?.total_pageviews || 0,
        top_pages: topPages,
        max_page_count: maxCount,
        recent_contacts: (contacts.data || []).slice(0, 3),
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
    languagesData: { languages: [] },
    hobbiesData: { items: [] },
    valuesData: { values: [] },
    saving: false,
    success: null,

    async init() {
      const [a, s, f, c, l, h, v] = await Promise.all([
        api.get("/about"), api.get("/skills"), api.get("/fun-fact"), api.get("/currently-learning"),
        api.get("/languages"), api.get("/hobbies"), api.get("/values"),
      ]);
      this.about = a.data || {};
      this.skills = s.data || {};
      this.funFacts = f.data || { facts: [] };
      this.currentlyLearning = c.data || { items: [] };
      this.languagesData = l.data || { languages: [] };
      this.hobbiesData = h.data || { items: [] };
      this.valuesData = v.data || { values: [] };
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

    async deleteContact(contact) {
      if (!confirm("Delete this contact submission?")) return;
      const resp = await api.delete(`/admin/contacts/${contact.contact_id}?sk=${encodeURIComponent(contact.SK)}`);
      if (resp.ok) this.contacts = this.contacts.filter(c => c.contact_id !== contact.contact_id);
    },

    formatDate(ts) { return ts ? new Date(ts * 1000).toLocaleString() : ""; },
  };
}

function adminTestimonials() {
  return {
    tab: "pending",
    pending: [],
    approved: [],
    loading: true,

    async init() {
      this.loading = true;
      const [p, a] = await Promise.all([
        api.get("/admin/testimonials/pending"),
        api.get("/admin/testimonials/approved"),
      ]);
      this.pending = p.data || [];
      this.approved = a.data || [];
      this.loading = false;
    },

    async action(id, action) {
      await api.put(`/admin/testimonials/${id}`, { action });
      this.pending = this.pending.filter(t => t.testimonial_id !== id);
    },

    async deleteApproved(t) {
      if (!confirm("Remove this approved testimonial?")) return;
      const resp = await api.delete(`/admin/testimonials/${t.testimonial_id}`);
      if (resp.ok) this.approved = this.approved.filter(a => a.testimonial_id !== t.testimonial_id);
    },
  };
}

function adminAnalytics() {
  return {
    data: null,
    loading: true,

    async init() {
      const resp = await api.get("/stats/analytics");
      this.data = resp.data || null;
      this.loading = false;
    },

    get pageRows() {
      if (!this.data?.by_page) return [];
      return Object.entries(this.data.by_page)
        .map(([page, count]) => ({ page, count }))
        .sort((a, b) => b.count - a.count);
    },

    pct(count) {
      const total = this.data?.total_pageviews || 1;
      return Math.round((count / total) * 100);
    },
  };
}

function adminGuestbook() {
  return {
    entries: [],
    loading: true,

    async init() {
      const resp = await api.get("/guestbook");
      this.entries = resp.data || [];
      this.loading = false;
    },

    async deleteEntry(entry) {
      if (!confirm("Delete this guestbook entry?")) return;
      const resp = await api.delete(`/guestbook/${entry.entry_id}?sk=${encodeURIComponent(entry.SK)}`);
      if (resp.ok) this.entries = this.entries.filter(e => e.entry_id !== entry.entry_id);
    },

    formatDate(ts) { return ts ? new Date(ts * 1000).toLocaleString() : ""; },
  };
}

function adminComments() {
  return {
    tab: "projects",
    projectGroups: [],
    courseGroups: [],
    loading: true,

    async init() {
      const [pResp, cResp] = await Promise.all([
        api.get("/projects"),
        api.get("/courses"),
      ]);
      const projects = pResp.data || [];
      const courses = cResp.data || [];

      const pFetches = projects.map(p => ({ label: p.title, entityPk: `PROJECT#${p.id}`, path: `/projects/${p.id}/comments` }));
      const cFetches = courses.map(c => ({ label: c.title, entityPk: `COURSE#${c.id}`, path: `/courses/${c.id}/comments` }));

      const [pResults, cResults] = await Promise.all([
        Promise.all(pFetches.map(f => api.get(f.path))),
        Promise.all(cFetches.map(f => api.get(f.path))),
      ]);

      this.projectGroups = pFetches
        .map((f, i) => ({ label: f.label, entityPk: f.entityPk, comments: pResults[i].data || [] }))
        .filter(g => g.comments.length > 0);

      this.courseGroups = cFetches
        .map((f, i) => ({ label: f.label, entityPk: f.entityPk, comments: cResults[i].data || [] }))
        .filter(g => g.comments.length > 0);

      this.loading = false;
    },

    get activeGroups() {
      return this.tab === "projects" ? this.projectGroups : this.courseGroups;
    },

    async deleteComment(commentId, entityPk) {
      if (!confirm("Delete this comment?")) return;
      const resp = await api.delete(`/comments/${commentId}?entity_pk=${encodeURIComponent(entityPk)}`);
      if (resp.ok) {
        const groups = this.tab === "projects" ? this.projectGroups : this.courseGroups;
        for (const g of groups) {
          const idx = g.comments.findIndex(c => c.comment_id === commentId);
          if (idx !== -1) { g.comments.splice(idx, 1); break; }
        }
      }
    },

    formatDate(ts) { return ts ? new Date(ts * 1000).toLocaleString() : ""; },
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
    showModal: false,
    form: { question: "", options: ["", "", "", ""], answer: "", topic: "general" },
    editing: null,
    saving: false,
    error: null,

    async init() {
      const resp = await api.get("/admin/quiz/questions");
      this.questions = resp.data || [];
      this.loading = false;
    },

    openCreate() {
      this.editing = null;
      this.form = { question: "", options: ["", "", "", ""], answer: "", topic: "general" };
      this.error = null;
      this.showModal = true;
    },

    openEdit(q) {
      this.editing = q.question_id;
      this.form = { question: q.question, options: [...q.options], answer: q.answer, topic: q.topic };
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
        this.closeModal();
      } else {
        this.error = resp.error;
      }
      this.saving = false;
    },

    async deleteQuestion(id) {
      if (!confirm("Delete this question?")) return;
      await api.delete(`/admin/quiz/questions/${id}`);
      this.questions = this.questions.filter(q => q.question_id !== id);
    },
  };
}
