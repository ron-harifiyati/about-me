import os
from utils import ok


def get_meta(event, path_params, body, query, headers):
    return ok({
        "git_sha": os.environ.get("GIT_SHA", "unknown"),
        "deploy_timestamp": os.environ.get("DEPLOY_TIMESTAMP", "unknown"),
        "environment": os.environ.get("ENVIRONMENT", "unknown"),
        "version": os.environ.get("VERSION", "unknown"),
        "region": os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
        "author": "Ron Harifiyati",
        "repository": "https://github.com/ron-harifiyati/about-me",
    })
