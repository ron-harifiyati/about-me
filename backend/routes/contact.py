import os
import boto3
from models import contacts as c
from utils import ok, bad_request, rate_limited


def _get_ip(event: dict) -> str:
    headers = event.get("headers") or {}
    forwarded = headers.get("x-forwarded-for") or headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return event.get("requestContext", {}).get("http", {}).get("sourceIp", "unknown")


def _send_contact_notification(name: str, email: str, message: str):
    ses = boto3.client("ses", region_name="us-east-1")
    sender = os.environ["SES_SENDER_EMAIL"]
    ses.send_email(
        Source=sender,
        Destination={"ToAddresses": [sender]},
        Message={
            "Subject": {"Data": f"Portfolio contact from {name}"},
            "Body": {"Text": {"Data": f"From: {name} <{email}>\n\n{message}"}},
        },
    )


def submit_contact(event, path_params, body, query, headers):
    name = (body.get("name") or "").strip()
    email = (body.get("email") or "").strip()
    message = (body.get("message") or "").strip()
    if not name or not email or not message:
        return bad_request("name, email, and message are required")

    ip = _get_ip(event)
    if c.is_rate_limited(ip):
        return rate_limited("You have sent too many messages. Please try again in an hour.")

    c.increment_rate_limit(ip)
    c.save_contact(name, email, message)
    _send_contact_notification(name, email, message)
    return ok({"message": "Message sent. I'll get back to you soon!"})
