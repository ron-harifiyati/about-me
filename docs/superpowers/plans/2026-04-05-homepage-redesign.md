# Homepage Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the sparse homepage with a five-section layout — hero with skill badges and social links, learning ticker, featured projects grid, testimonial + live stats, fun fact + explore links.

**Architecture:** Pure frontend change. All required API endpoints already exist. `home.js` is extended to fetch data for all five sections in parallel. The entire `<!-- HOME -->` block in `index.html` is replaced. Two small CSS utilities are added to `main.css`.

**Tech Stack:** Alpine.js v3, CSS custom properties, existing `api.js` helper, existing REST endpoints (`/fun-fact`, `/currently-learning`, `/projects`, `/testimonials`, `/stats/visitors`, `/courses`, `/about`)

---

## File Map

| File | Change |
|------|--------|
| `frontend/assets/js/pages/home.js` | Extend state + init() to fetch projects, testimonial, stats, social links |
| `frontend/assets/css/main.css` | Add `.testimonial-quote` and `.home-two-col` utility classes |
| `frontend/index.html` | Replace `<!-- HOME -->` block (lines 112–175) with new 5-section layout |

---

## Task 1: Extend home.js data layer

**Files:**
- Modify: `frontend/assets/js/pages/home.js`

The current file fetches only `/fun-fact` and `/currently-learning`. We need to add five more parallel calls and expose new reactive properties.

Project shape from API: `{ id, title, description, tech_stack: [], avg_rating }` — matches what the projects list page already uses.
Testimonial shape: `{ testimonial_id, body, author, identity }`.
Visitors shape: array of `{ country, city, lat, lon }`.
About shape: `{ social_links: { github, linkedin }, contact: { email } }`.

- [ ] **Replace `frontend/assets/js/pages/home.js` with the extended version:**

```javascript
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

      this.loading = false;
    },

    refreshFact() {
      api.get("/fun-fact").then(r => { this.funFact = r.data?.fact || null; });
    },
  };
}
```

- [ ] **Verify the file looks correct** — open `frontend/assets/js/pages/home.js` and confirm the new state properties and parallel calls are present.

- [ ] **Commit:**

```bash
git add frontend/assets/js/pages/home.js
git commit -m "feat: extend homePage() with parallel data fetching for redesign"
```

---

## Task 2: Add CSS utilities for homepage layout

**Files:**
- Modify: `frontend/assets/css/main.css`

Two small additions needed:
1. `.testimonial-quote` — left border accent for the pull quote card
2. `.home-two-col` — responsive two-column grid used for sections ④ and ⑤ (stacks on mobile)

- [ ] **Append to the end of `frontend/assets/css/main.css`:**

```css
/* Homepage two-column sections (testimonial+stats, fun-fact+explore) */
.home-two-col {
  display: grid;
  grid-template-columns: 3fr 2fr;
  gap: 1.5rem;
  align-items: start;
}
@media (max-width: 768px) {
  .home-two-col { grid-template-columns: 1fr; }
}

/* Testimonial pull quote */
.testimonial-quote {
  border-left: 3px solid var(--accent);
  padding-left: 1rem;
}
```

- [ ] **Commit:**

```bash
git add frontend/assets/css/main.css
git commit -m "feat: add home-two-col and testimonial-quote CSS utilities"
```

---

## Task 3: Replace the HOME section in index.html

**Files:**
- Modify: `frontend/index.html` — replace lines 112–175 (the entire `<!-- HOME -->` block)

This is the main task. The new block has five sections. Replace the old `<!-- HOME -->` block (from `<!-- HOME -->` comment through the closing `</div>` at line 175) with the following.

Note: `x-cloak` is used on the social links row so it only renders after Alpine initialises (avoids a flash of empty links).

- [ ] **In `frontend/index.html`, replace the entire `<!-- HOME -->` block with:**

```html
      <!-- HOME -->
      <div x-show="currentPage === 'home'" class="page">
        <div x-data="homePage()" x-init="init()">

          <!-- ① HERO -->
          <section style="padding: 3rem 0 2rem; border-bottom: 1px solid var(--border);">
            <p style="font-size: 0.78rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--accent); margin-bottom: 0.6rem;">
              Integration Engineer · Jamf
            </p>
            <h1>Hi, I'm Ron Harifiyati</h1>
            <p style="margin-top: 0.75rem; max-width: 520px; color: var(--text-muted); line-height: 1.65;">
              I build systems that connect things — APIs, workflows, and teams.
              I care about clean interfaces, reliable backends, and code that's easy to hand off.
            </p>
            <!-- Skill badges -->
            <div style="display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 1.25rem;">
              <span class="badge badge-outline">Python</span>
              <span class="badge badge-outline">Swift</span>
              <span class="badge badge-outline">AWS</span>
              <span class="badge badge-outline">JavaScript</span>
              <span class="badge badge-outline">Linux</span>
              <span class="badge badge-outline">Docker</span>
              <a href="#/skills" style="font-size: 0.78rem; padding: 0.2rem 0.4rem; color: var(--accent);">+ more &rarr;</a>
            </div>
            <!-- CTAs + social links -->
            <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 0.75rem; margin-top: 1.4rem;">
              <a href="#/projects" class="btn btn-primary">See my work</a>
              <a href="#/contact" class="btn btn-outline">Get in touch</a>
              <template x-if="socialLinks">
                <div style="display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap;">
                  <span style="width: 1px; height: 20px; background: var(--border);"></span>
                  <template x-if="socialLinks.github">
                    <a :href="socialLinks.github" target="_blank" rel="noopener" style="font-size: 0.85rem;">GitHub</a>
                  </template>
                  <template x-if="socialLinks.linkedin">
                    <a :href="socialLinks.linkedin" target="_blank" rel="noopener" style="font-size: 0.85rem;">LinkedIn</a>
                  </template>
                  <template x-if="socialLinks.email">
                    <a :href="'mailto:' + socialLinks.email" style="font-size: 0.85rem;">Email</a>
                  </template>
                </div>
              </template>
            </div>
          </section>

          <!-- ② CURRENTLY LEARNING TICKER -->
          <template x-if="ticker.length > 0">
            <div style="display: flex; align-items: center; gap: 1rem; padding: 0.9rem 0; border-bottom: 1px solid var(--border);">
              <span style="font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); white-space: nowrap;">Now learning</span>
              <div class="ticker-wrap" style="flex: 1;">
                <span class="ticker-text" x-text="ticker.join('  ·  ')"></span>
              </div>
            </div>
          </template>

          <!-- ③ FEATURED PROJECTS -->
          <section style="padding: 2rem 0; border-bottom: 1px solid var(--border);">
            <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 1rem;">
              <h2 style="margin: 0;">Featured Projects</h2>
              <a href="#/projects" style="font-size: 0.85rem;">All projects &rarr;</a>
            </div>
            <div x-show="loading" class="loading-center"><div class="spinner"></div></div>
            <div x-show="!loading">
              <template x-if="projects.length === 0">
                <p class="subtitle">No projects yet — check back soon.</p>
              </template>
              <div class="card-grid fade-in">
                <template x-for="p in projects" :key="p.id">
                  <a :href="'#/projects/' + p.id" class="card" style="text-decoration: none; display: block;">
                    <h3 x-text="p.title"></h3>
                    <p x-text="p.description" class="subtitle" style="font-size: 0.9rem; margin: 0.5rem 0;"></p>
                    <div style="display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.75rem;">
                      <template x-for="tag in (p.tech_stack || [])" :key="tag">
                        <span class="badge badge-outline" x-text="tag"></span>
                      </template>
                    </div>
                  </a>
                </template>
              </div>
            </div>
          </section>

          <!-- ④ TESTIMONIAL + STATS -->
          <section x-show="!loading" style="padding: 2rem 0; border-bottom: 1px solid var(--border);">
            <div class="home-two-col">
              <!-- Testimonial pull quote -->
              <template x-if="testimonial">
                <div class="card testimonial-quote">
                  <p x-text="'&ldquo;' + testimonial.body + '&rdquo;'" style="font-style: italic; line-height: 1.7; margin-bottom: 0.75rem;"></p>
                  <p style="font-size: 0.82rem; color: var(--text-muted);">
                    &mdash; <span x-text="testimonial.author || 'Anonymous'"></span>
                    <template x-if="testimonial.identity">
                      <span x-text="' · ' + testimonial.identity"></span>
                    </template>
                  </p>
                  <a href="#/testimonials" style="display: inline-block; margin-top: 0.75rem; font-size: 0.82rem;">Read more testimonials &rarr;</a>
                </div>
              </template>
              <template x-if="!testimonial">
                <div class="card testimonial-quote" style="display: flex; align-items: center; justify-content: center; min-height: 100px;">
                  <a href="#/testimonials" class="subtitle" style="font-size: 0.9rem;">Leave a testimonial &rarr;</a>
                </div>
              </template>

              <!-- Stats -->
              <div style="display: flex; flex-direction: column; gap: 0.6rem;">
                <div class="card" style="display: flex; justify-content: space-between; align-items: center; padding: 0.9rem 1.1rem;">
                  <span class="subtitle" style="font-size: 0.85rem;">Visitors from</span>
                  <span style="font-size: 1.1rem; font-weight: 700;">
                    <span x-text="visitorCountries !== null ? visitorCountries + ' countries' : '—'"></span>
                  </span>
                </div>
                <div class="card" style="display: flex; justify-content: space-between; align-items: center; padding: 0.9rem 1.1rem;">
                  <span class="subtitle" style="font-size: 0.85rem;">Projects built</span>
                  <span style="font-size: 1.1rem; font-weight: 700;" x-text="projectCount !== null ? projectCount : '—'"></span>
                </div>
                <div class="card" style="display: flex; justify-content: space-between; align-items: center; padding: 0.9rem 1.1rem;">
                  <span class="subtitle" style="font-size: 0.85rem;">Courses completed</span>
                  <span style="font-size: 1.1rem; font-weight: 700;" x-text="courseCount !== null ? courseCount : '—'"></span>
                </div>
              </div>
            </div>
          </section>

          <!-- ⑤ FUN FACT + EXPLORE -->
          <section style="padding: 2rem 0;">
            <div class="home-two-col">
              <!-- Fun fact -->
              <div class="card">
                <h3>Fun Fact</h3>
                <div x-show="loading" class="loading-center" style="padding: 1rem 0;"><div class="spinner"></div></div>
                <p x-show="!loading && funFact" x-text="funFact" style="margin: 0.75rem 0; font-style: italic; color: var(--text-muted); line-height: 1.6;"></p>
                <p x-show="!loading && !funFact" class="subtitle">No fun facts yet.</p>
                <button x-show="!loading" class="btn btn-outline btn-sm" style="margin-top: 0.75rem;" @click="refreshFact()">
                  Another one
                </button>
              </div>

              <!-- Explore -->
              <div class="card">
                <h3>Explore</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem; margin-top: 0.75rem;">
                  <a href="#/quiz" class="btn btn-outline" style="text-align: center;">Quiz</a>
                  <a href="#/guestbook" class="btn btn-outline" style="text-align: center;">Guestbook</a>
                  <a href="#/stats" class="btn btn-outline" style="text-align: center;">Visitor Map</a>
                  <a href="#/developer" class="btn btn-outline" style="text-align: center;">API Docs</a>
                </div>
              </div>
            </div>
          </section>

        </div>
      </div>
```

- [ ] **Manual verification — open http://localhost:8080 and check:**
  - Hero renders: eyebrow label, name (`h1` responds to responsive CSS at narrow width), bio, skill badges, CTAs, social links appear after load
  - Ticker band shows below hero (or is absent if no items)
  - Featured projects grid shows up to 3 cards with tags
  - Testimonial + stats section shows pull quote and 3 stat tiles
  - Fun fact card shows with "Another one" button; clicking it refreshes the fact
  - Explore grid shows 4 buttons; each navigates to correct page
  - On mobile viewport (375px wide): hero stacks cleanly, `.home-two-col` sections stack to single column

- [ ] **Commit:**

```bash
git add frontend/index.html
git commit -m "feat: redesign homepage with hero, projects, testimonial, stats, explore sections"
```

---

## Self-Review Checklist

After the plan is written, verify against the spec:

| Spec requirement | Task |
|-----------------|------|
| Eyebrow label in accent color | Task 3 — hero section |
| `h1` uses CSS font-size (no inline override) | Task 3 — `<h1>Hi, I'm Ron Harifiyati</h1>` with no style attr |
| Skill badges + "more →" link | Task 3 — hero section |
| Social links from `/about` API | Task 1 (fetch) + Task 3 (render) |
| Ticker with "Now learning" label | Task 3 — section ② |
| Featured Projects 3-column grid | Task 3 — section ③ |
| "All projects →" link | Task 3 — section ③ |
| Testimonial pull quote with left border | Task 2 (CSS) + Task 3 (section ④) |
| Fallback when no testimonials | Task 3 — `x-if="!testimonial"` fallback |
| Stats tiles (countries, projects, courses) | Task 1 (fetch) + Task 3 (section ④) |
| Fun fact + refresh button | Task 3 — section ⑤ |
| Explore grid (Quiz, Guestbook, Map, API Docs) | Task 3 — section ⑤ |
| `.home-two-col` responsive stacking | Task 2 (CSS) |
| Mobile: no inline font-size on hero | Task 3 — no style attr on `<h1>` |
