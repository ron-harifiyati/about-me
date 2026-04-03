from auth import require_auth
from models import quiz as q
from utils import ok, bad_request


@require_auth
def get_questions(event, path_params, body, query, headers, user):
    questions = q.list_questions()
    # Strip answers before sending to client
    safe = [{k: v for k, v in item.items() if k not in ("answer", "PK", "SK")} for item in questions]
    return ok(safe)


@require_auth
def submit_answers(event, path_params, body, query, headers, user):
    answers = body.get("answers", {})
    if not answers:
        return bad_request("answers is required")
    questions = q.list_questions()
    score = sum(1 for item in questions if answers.get(item["question_id"]) == item["answer"])
    total = len(questions)
    attempt = q.save_score(user["sub"], score, total)
    return ok({"score": score, "total": total, "attempt_id": attempt["attempt_id"]})


@require_auth
def get_leaderboard(event, path_params, body, query, headers, user):
    return ok(q.get_leaderboard())
