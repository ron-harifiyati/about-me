import boto3
import pytest
from moto import mock_aws


@pytest.fixture(autouse=True)
def aws_env(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("DYNAMODB_TABLE_NAME", "portfolio")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-32-chars-long-padding!")
    monkeypatch.setenv("SES_SENDER_EMAIL", "test@example.com")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("GIT_SHA", "abc123")
    monkeypatch.setenv("DEPLOY_TIMESTAMP", "2026-04-02T00:00:00Z")
    monkeypatch.setenv("VERSION", "0.1.0")
    monkeypatch.setenv("GITHUB_OAUTH_CLIENT_ID", "gh-client-id")
    monkeypatch.setenv("GITHUB_OAUTH_CLIENT_SECRET", "gh-client-secret")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "goog-client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "goog-client-secret")


@pytest.fixture
def ddb_table(aws_env):
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.create_table(
            TableName="portfolio",
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
                {"AttributeName": "GSI1PK", "AttributeType": "S"},
                {"AttributeName": "GSI1SK", "AttributeType": "S"},
                {"AttributeName": "GSI2PK", "AttributeType": "S"},
                {"AttributeName": "GSI2SK", "AttributeType": "S"},
                {"AttributeName": "GSI3PK", "AttributeType": "S"},
                {"AttributeName": "GSI3SK", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "GSI1",
                    "KeySchema": [
                        {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                        {"AttributeName": "GSI1SK", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
                {
                    "IndexName": "GSI2",
                    "KeySchema": [
                        {"AttributeName": "GSI2PK", "KeyType": "HASH"},
                        {"AttributeName": "GSI2SK", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
                {
                    "IndexName": "GSI3",
                    "KeySchema": [
                        {"AttributeName": "GSI3PK", "KeyType": "HASH"},
                        {"AttributeName": "GSI3SK", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        yield table


def make_event(method="GET", path="/", body=None, headers=None, query=None):
    """Helper to build a Lambda Function URL event dict."""
    return {
        "requestContext": {"http": {"method": method, "path": path}},
        "rawPath": path,
        "headers": headers or {},
        "queryStringParameters": query or {},
        "body": __import__("json").dumps(body) if body else None,
    }


@pytest.fixture(autouse=True)
def reset_db_singleton():
    import db
    db.reset_table()
    yield
    db.reset_table()
