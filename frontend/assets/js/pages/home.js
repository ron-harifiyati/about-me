// frontend/assets/js/pages/home.js
function homePage() {
  return {
    // Existing
    funFact: null,
    ticker: [],
    loading: true,

    // New
    projects: [],
    testimonial: null,
    visitorCountries: null,
    projectCount: null,
    courseCount: null,
    socialLinks: null,

    async init() {
      try {
        const [
          factResp,
          tickerResp,
          projectsResp,
          testimonialsResp,
          visitorsResp,
          coursesResp,
          aboutResp,
        ] = await Promise.all([
          api.get("/fun-fact"),
          api.get("/currently-learning"),
          api.get("/projects"),
          api.get("/testimonials"),
          api.get("/stats/visitors"),
          api.get("/courses"),
          api.get("/about"),
        ]);

        this.funFact      = factResp.data?.fact || null;
        this.ticker       = tickerResp.data?.items || [];

        const allProjects  = projectsResp.data || [];
        this.projects      = allProjects.slice(0, 3);
        this.projectCount  = allProjects.length;

        const allTestimonials = testimonialsResp.data || [];
        this.testimonial   = allTestimonials[0] || null;

        const visitors     = visitorsResp.data || [];
        const countries    = new Set(visitors.map(v => v.country).filter(Boolean));
        this.visitorCountries = countries.size;

        this.courseCount   = (coursesResp.data || []).length;

        const about        = aboutResp.data;
        this.socialLinks   = {
          github:   about?.social_links?.github   || null,
          linkedin: about?.social_links?.linkedin || null,
          email:    about?.contact?.email         || null,
        };
      } finally {
        this.loading = false;
      }
    },

    refreshFact() {
      api.get("/fun-fact").then(r => { this.funFact = r.data?.fact || null; }).catch(() => {});
    },
  };
}
