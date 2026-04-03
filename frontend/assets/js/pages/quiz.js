// frontend/assets/js/pages/quiz.js
function quizPage() {
  return {
    // States: "loading" | "start" | "playing" | "result" | "leaderboard"
    state: "loading",
    questions: [],
    answers: {},        // { question_id: selected_option }
    current: 0,
    result: null,
    leaderboard: [],
    loadingLeaderboard: false,
    submitting: false,
    error: null,

    async init() {
      const resp = await api.get("/quiz/questions");
      if (!resp.ok) {
        this.error = resp.error || "Could not load questions.";
        this.state = "start";
        return;
      }
      this.questions = resp.data || [];
      this.state = "start";
    },

    startQuiz() {
      this.answers = {};
      this.current = 0;
      this.result = null;
      this.error = null;
      this.state = "playing";
    },

    selectAnswer(questionId, option) {
      this.answers[questionId] = option;
    },

    isAnswered(questionId) {
      return questionId in this.answers;
    },

    get allAnswered() {
      return this.questions.every(q => this.isAnswered(q.question_id));
    },

    get progress() {
      return Math.round((Object.keys(this.answers).length / this.questions.length) * 100);
    },

    async submitQuiz() {
      if (!this.allAnswered) {
        this.error = "Please answer all questions before submitting.";
        return;
      }
      this.submitting = true;
      const resp = await api.post("/quiz/submit", { answers: this.answers });
      if (resp.ok) {
        this.result = resp.data;
        this.state = "result";
      } else {
        this.error = resp.error;
      }
      this.submitting = false;
    },

    async showLeaderboard() {
      this.state = "leaderboard";
      this.loadingLeaderboard = true;
      const resp = await api.get("/quiz/leaderboard");
      this.leaderboard = resp.data || [];
      this.loadingLeaderboard = false;
    },

    get scorePercent() {
      if (!this.result) return 0;
      return Math.round((this.result.score / this.result.total) * 100);
    },

    scoreMessage() {
      const p = this.scorePercent;
      if (p === 100) return "Perfect score!";
      if (p >= 80)  return "Great work!";
      if (p >= 60)  return "Not bad!";
      if (p >= 40)  return "Keep practicing!";
      return "Better luck next time!";
    },
  };
}
