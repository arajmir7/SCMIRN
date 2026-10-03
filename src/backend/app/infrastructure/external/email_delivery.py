"""
Outbound email delivery helpers for enterprise executive briefings.

Supported providers:
 - SendGrid (REST API)
 - AWS SES (boto3 send_raw_email)
"""

from __future__ import annotations

import base64
import http.client
import json
import ssl
from email.message import EmailMessage
from typing import Any, Dict


class EmailDeliveryError(Exception):
    """Raised when outbound email delivery fails."""


def resolve_email_provider(config: Dict[str, Any]) -> str:
    provider = str(config.get("EMAIL_PROVIDER", "auto")).strip().lower()
    if provider in {"sendgrid", "ses", "none"}:
        return provider

    sendgrid_key = str(config.get("SENDGRID_API_KEY", "")).strip()
    if sendgrid_key:
        return "sendgrid"

    ses_from = str(config.get("SES_FROM_EMAIL", "")).strip() or str(config.get("EMAIL_FROM", "")).strip()
    if ses_from:
        return "ses"

    return "none"


def send_briefing_email(
    *,
    config: Dict[str, Any],
    recipient: str,
    subject: str,
    body_text: str,
    attachment_bytes: bytes | None = None,
    attachment_filename: str | None = None,
) -> Dict[str, Any]:
    provider = resolve_email_provider(config)
    try:
        if provider == "none":
            raise EmailDeliveryError("No outbound email provider configured (set EMAIL_PROVIDER or provider credentials).")

        if provider == "sendgrid":
            from_email = str(config.get("SENDGRID_FROM_EMAIL") or config.get("EMAIL_FROM") or "").strip()
            api_key = str(config.get("SENDGRID_API_KEY") or "").strip()
            if not api_key:
                raise EmailDeliveryError("SENDGRID_API_KEY is missing.")
            if not from_email:
                raise EmailDeliveryError("SENDGRID_FROM_EMAIL or EMAIL_FROM is required for SendGrid.")
            message_id = _send_via_sendgrid(
                api_key=api_key,
                from_email=from_email,
                recipient=recipient,
                subject=subject,
                body_text=body_text,
                attachment_bytes=attachment_bytes,
                attachment_filename=attachment_filename,
            )
            return {"status": "SENT", "provider": "sendgrid", "message_id": message_id}

        if provider == "ses":
            from_email = str(config.get("SES_FROM_EMAIL") or config.get("EMAIL_FROM") or "").strip()
            if not from_email:
                raise EmailDeliveryError("SES_FROM_EMAIL or EMAIL_FROM is required for SES.")
            region = str(config.get("AWS_REGION") or config.get("AWS_DEFAULT_REGION") or "us-east-1")
            message_id = _send_via_ses(
                region=region,
                from_email=from_email,
                recipient=recipient,
                subject=subject,
                body_text=body_text,
                attachment_bytes=attachment_bytes,
                attachment_filename=attachment_filename,
            )
            return {"status": "SENT", "provider": "ses", "message_id": message_id}

        raise EmailDeliveryError(f"Unsupported email provider: {provider}")
    except Exception as exc:
        return {"status": "FAILED", "provider": provider, "error": str(exc)}


def _send_via_sendgrid(
    *,
    api_key: str,
    from_email: str,
    recipient: str,
    subject: str,
    body_text: str,
    attachment_bytes: bytes | None,
    attachment_filename: str | None,
) -> str:
    payload: Dict[str, Any] = {
        "personalizations": [{"to": [{"email": recipient}]}],
        "from": {"email": from_email},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body_text}],
    }
    if attachment_bytes and attachment_filename:
        payload["attachments"] = [
            {
                "content": base64.b64encode(attachment_bytes).decode("ascii"),
                "type": "application/pdf",
                "filename": attachment_filename,
                "disposition": "attachment",
            }
        ]

    request_data = json.dumps(payload).encode("utf-8")
    # Fixed host/path, no redirects, and an explicit default TLS context; the
    # Semgrep HTTPSConnection warning is therefore not an unverified TLS use.
    connection = http.client.HTTPSConnection(  # nosemgrep: python.lang.security.audit.httpsconnection-detected.httpsconnection-detected
        "api.sendgrid.com", timeout=20, context=ssl.create_default_context()
    )
    try:
        connection.request(
            "POST",
            "/v3/mail/send",
            body=request_data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        response = connection.getresponse()
        if response.status not in {200, 202}:
            raise EmailDeliveryError(f"SendGrid rejected email with status {response.status}.")
        return str(response.getheader("X-Message-Id") or "sendgrid-accepted")
    except (OSError, http.client.HTTPException) as exc:
        raise EmailDeliveryError("SendGrid connectivity error.") from exc
    finally:
        connection.close()


def _send_via_ses(
    *,
    region: str,
    from_email: str,
    recipient: str,
    subject: str,
    body_text: str,
    attachment_bytes: bytes | None,
    attachment_filename: str | None,
) -> str:
    try:
        import boto3
    except ImportError as exc:
        raise EmailDeliveryError("boto3 is required for SES delivery. Install boto3 in backend dependencies.") from exc

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_email
    message["To"] = recipient
    message.set_content(body_text)

    if attachment_bytes and attachment_filename:
        message.add_attachment(
            attachment_bytes,
            maintype="application",
            subtype="pdf",
            filename=attachment_filename,
        )

    try:
        ses_client = boto3.client("ses", region_name=region)
        response = ses_client.send_raw_email(
            Source=from_email,
            Destinations=[recipient],
            RawMessage={"Data": message.as_bytes()},
        )
        return str(response.get("MessageId") or "ses-accepted")
    except Exception as exc:
        raise EmailDeliveryError(f"SES delivery failed: {exc}") from exc
