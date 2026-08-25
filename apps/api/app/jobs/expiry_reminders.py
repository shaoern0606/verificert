"""Send a one-time reminder email for certificates expiring soon.

Not wired to a scheduler — this project has no task-queue/cron infrastructure yet, so run it
externally on a schedule, e.g. a daily cron entry:

    0 8 * * * cd /path/to/apps/api && .venv/bin/python -m app.jobs.expiry_reminders
"""

from datetime import datetime, timedelta

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.domain import Certificate, CertificateStatus
from app.services.email import certificate_expiry_reminder_email, send_email


def run() -> int:
    settings = get_settings()
    window_end = datetime.utcnow() + timedelta(days=settings.certificate_expiry_reminder_days)
    db = SessionLocal()
    sent = 0
    try:
        certificates = db.scalars(
            select(Certificate).where(
                Certificate.status == CertificateStatus.ACTIVE,
                Certificate.expiry_date.is_not(None),
                Certificate.expiry_date <= window_end,
                Certificate.expiry_date >= datetime.utcnow(),
                Certificate.expiry_reminder_sent_at.is_(None),
            )
        ).all()
        for cert in certificates:
            ok = send_email(
                cert.recipient.email,
                f"Your certificate is expiring soon: {cert.title}",
                certificate_expiry_reminder_email(cert.recipient.name, cert.title, cert.organization.name, cert.expiry_date.date().isoformat(), cert.verification_url),
            )
            if ok:
                cert.expiry_reminder_sent_at = datetime.utcnow()
                sent += 1
        db.commit()
        print(f"Sent {sent} expiry reminder(s) out of {len(certificates)} certificate(s) expiring within {settings.certificate_expiry_reminder_days} days.")
        return sent
    finally:
        db.close()


if __name__ == "__main__":
    run()
