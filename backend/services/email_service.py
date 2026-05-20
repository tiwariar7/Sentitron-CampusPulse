"""
Async email service using aiosmtplib.
Handles escalation alerts, notification digests, and system alerts.
All send attempts are audit-logged via EmailAuditLog.
"""
import asyncio
import logging
import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional

import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from services.email_templates import (
    render_escalation_alert,
    render_notification_digest,
    render_system_alert,
)

logger = logging.getLogger(__name__)

# ── Config from environment ─────────────────────────────────────
SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
SMTP_TLS      = os.getenv("SMTP_TLS", "true").lower() == "true"
SMTP_USER     = os.getenv("SMTP_USER", "tiwariar279@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM    = os.getenv("ALERT_EMAIL_FROM", "tiwariar279@gmail.com")
EMAIL_TO      = os.getenv("ALERT_EMAIL_TO", "tiwariar279@gmail.com")
MAX_RETRIES   = int(os.getenv("EMAIL_MAX_RETRIES", "3"))
BASE_DELAY    = float(os.getenv("EMAIL_RETRY_BASE_DELAY", "2"))


class EmailService:
    """
    Async SMTP email service with exponential-backoff retry.
    Circuit-breaker aware — caller should wrap with circuit_breaker utility.
    """

    async def _send_raw(self, to: str, subject: str, html_body: str) -> None:
        """Low-level: build MIME message and hand off to aiosmtplib."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = EMAIL_FROM
        msg["To"]      = to
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            start_tls=SMTP_TLS,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            timeout=10,
        )

    async def send_with_retry(
        self,
        to: str,
        subject: str,
        html_body: str,
        template_name: str = "generic",
        complaint_id: Optional[str] = None,
        db=None,
    ) -> dict:
        """
        Send email with exponential-backoff retry (2s → 4s → 8s).
        Writes an EmailAuditLog entry on each attempt.
        Returns: {"status": "sent"|"failed", "attempts": int, "error": str|None}
        """
        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                await self._send_raw(to, subject, html_body)
                logger.info(f"Email sent to {to} | subject={subject!r} | attempt={attempt}")
                if db:
                    await self._write_audit(
                        db, to, subject, template_name, "sent", attempt, None, complaint_id
                    )
                return {"status": "sent", "attempts": attempt, "error": None}
            except Exception as exc:
                last_error = str(exc)
                logger.warning(
                    f"Email attempt {attempt}/{MAX_RETRIES} failed to {to}: {exc}"
                )
                if attempt < MAX_RETRIES:
                    delay = BASE_DELAY * (2 ** (attempt - 1))  # 2, 4, 8
                    await asyncio.sleep(delay)

        # All retries exhausted
        logger.error(f"Email permanently failed to {to} after {MAX_RETRIES} attempts: {last_error}")
        if db:
            await self._write_audit(
                db, to, subject, template_name, "failed", MAX_RETRIES, last_error, complaint_id
            )
        return {"status": "failed", "attempts": MAX_RETRIES, "error": last_error}

    async def send_escalation_alert(
        self,
        complaint_id: str,
        department: str,
        severity: str,
        description: str,
        db=None,
    ) -> dict:
        subject   = f"[CampusPulse ESCALATION] {severity} — {department}"
        html_body = render_escalation_alert(complaint_id, department, severity, description)
        return await self.send_with_retry(
            to=EMAIL_TO,
            subject=subject,
            html_body=html_body,
            template_name="escalation_alert",
            complaint_id=complaint_id,
            db=db,
        )

    async def send_notification_digest(
        self,
        recipient: str,
        notifications: list,
        db=None,
    ) -> dict:
        subject   = "[CampusPulse] Notification Digest"
        html_body = render_notification_digest(notifications)
        return await self.send_with_retry(
            to=recipient,
            subject=subject,
            html_body=html_body,
            template_name="notification_digest",
            db=db,
        )

    async def send_system_alert(
        self,
        alert_name: str,
        severity: str,
        description: str,
        db=None,
    ) -> dict:
        subject   = f"[CampusPulse SYSTEM] {alert_name}"
        html_body = render_system_alert(alert_name, severity, description)
        return await self.send_with_retry(
            to=EMAIL_TO,
            subject=subject,
            html_body=html_body,
            template_name="system_alert",
            db=db,
        )

    @staticmethod
    async def _write_audit(db, to, subject, template_name, status, attempts, error, complaint_id):
        """Write EmailAuditLog record (fire-and-forget safe)."""
        try:
            from services.db import EmailAuditLog
            record = EmailAuditLog(
                to_address=to,
                subject=subject,
                template_name=template_name,
                status=status,
                attempt_count=attempts,
                last_error=error,
                complaint_id=complaint_id,
                sent_at=datetime.utcnow() if status == "sent" else None,
            )
            db.add(record)
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to write email audit log: {e}")


# Singleton instance
email_service = EmailService()
