import json
from tests.conftest import make_event
from auth import make_jwt


def _auth_headers(user_id="user-1"):
    return {"authorization": f"Bearer {make_jwt(user_id, 'user')}"}


def _seed_questions(ddb_table):
    from models.quiz import create_question
    for i in range(3):
        create_question({
            "question": f"Question {i+1}?",
            "options": ["A", "B", "C", "D"],
            "answer": "A",
            "topic": "general",
        })


def test_get_questions_requires_auth(ddb_table):
    from router import route
    resp = route(make_event("GET", "/quiz/questions"))
    assert resp["statusCode"] == 401


def test_get_questions_returns_list(ddb_table):
    from router import route
    _seed_questions(ddb_table)
    resp = route(make_event("GET", "/quiz/questions", headers=_auth_headers()))
    assert resp["statusCode"] == 200
    questions = json.loads(resp["body"])["data"]
    assert len(questions) == 3
    # Answers must NOT be included in the response
    for q in questions:
        assert "answer" not in q


def test_submit_quiz_scores_correctly(ddb_table):
    from router import route
    from models.quiz import create_question, list_questions
    _seed_questions(ddb_table)
    questions = list_questions()
    answers = {q["question_id"]: "A" for q in questions}

    resp = route(make_event("POST", "/quiz/submit",
        body={"answers": answers},
        headers=_auth_headers(),
    ))
    assert resp["statusCode"] == 200
    result = json.loads(resp["body"])["data"]
    assert result["score"] == 3
    assert result["total"] == 3


def test_leaderboard_requires_auth(ddb_table):
    from router import route
    resp = route(make_event("GET", "/quiz/leaderboard"))
    assert resp["statusCode"] == 401


def test_leaderboard_returns_scores(ddb_table):
    from router import route
    from models.quiz import create_question, list_questions
    _seed_questions(ddb_table)
    questions = list_questions()
    answers = {q["question_id"]: "A" for q in questions}
    route(make_event("POST", "/quiz/submit", body={"answers": answers}, headers=_auth_headers("user-1")))
    route(make_event("POST", "/quiz/submit", body={"answers": answers}, headers=_auth_headers("user-2")))

    resp = route(make_event("GET", "/quiz/leaderboard", headers=_auth_headers()))
    assert resp["statusCode"] == 200
    board = json.loads(resp["body"])["data"]
    assert len(board) >= 2
