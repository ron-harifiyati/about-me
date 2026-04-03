import requests
from utils import ok


def get_repos(event, path_params, body, query, headers):
    try:
        resp = requests.get(
            "https://api.github.com/users/ron-harifiyati/repos",
            params={"sort": "updated", "per_page": 6, "type": "public"},
            headers={"Accept": "application/vnd.github+json"},
            timeout=5,
        )
        repos = [
            {
                "name": r["name"],
                "description": r["description"],
                "url": r["html_url"],
                "language": r["language"],
                "stars": r["stargazers_count"],
                "updated_at": r["updated_at"],
            }
            for r in resp.json()
            if not r["fork"]
        ]
        return ok(repos)
    except Exception:
        return ok([])
