import os
import boto3

_table = None


def get_table():
    global _table
    if _table is None:
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        _table = dynamodb.Table(os.environ["DYNAMODB_TABLE_NAME"])
    return _table


def reset_table():
    """Call this in tests to force re-init with mocked client."""
    global _table
    _table = None
