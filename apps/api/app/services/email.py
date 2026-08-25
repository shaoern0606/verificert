import logging

from app.core.config import get_settings

logger = logging.getLogger("verificert.email")


def send_email(to: str, subject: str, html: str) -> bool:
    settings = get_settings()
    if not settings.resend_api_key:
        logger.info("email_skipped reason=no_resend_api_key to=%s subject=%s", to, subject)
        return False
    try:
        import resend

        resend.api_key = settings.resend_api_key
        resend.Emails.send({"from": settings.email_from, "to": [to], "subject": subject, "html": html})
        return True
    except Exception as exc:
        logger.warning("email_send_failed to=%s subject=%s error=%s", to, subject, exc)
        return False


def certificate_issued_email(recipient_name: str, certificate_title: str, organization_name: str, verification_url: str) -> str:
    return f"""
    <div style="font-family: sans-serif; max-width: 480px; margin: auto;">
      <h2 style="color:#13795b;">Your certificate is ready</h2>
      <p>Hi {recipient_name},</p>
      <p><strong>{organization_name}</strong> has issued you a new credential: <strong>{certificate_title}</strong>.</p>
      <p><a href="{verification_url}" style="background:#13795b;color:#fff;padding:10px 16px;border-radius:6px;text-decoration:none;">View and verify your certificate</a></p>
      <p style="color:#64748b;font-size:12px;">This credential is registered on-chain and can be independently verified at any time using the link above.</p>
    </div>
    """


def certificate_revoked_email(recipient_name: str, certificate_title: str, organization_name: str, reason: str) -> str:
    return f"""
    <div style="font-family: sans-serif; max-width: 480px; margin: auto;">
      <h2 style="color:#dc2626;">A certificate has been revoked</h2>
      <p>Hi {recipient_name},</p>
      <p><strong>{organization_name}</strong> has revoked your credential: <strong>{certificate_title}</strong>.</p>
      <p><strong>Reason:</strong> {reason}</p>
      <p style="color:#64748b;font-size:12px;">If you believe this is a mistake, contact the issuing organization directly.</p>
    </div>
    """


def certificate_expiry_reminder_email(recipient_name: str, certificate_title: str, organization_name: str, expiry_date: str, verification_url: str) -> str:
    return f"""
    <div style="font-family: sans-serif; max-width: 480px; margin: auto;">
      <h2 style="color:#d97706;">Your certificate is expiring soon</h2>
      <p>Hi {recipient_name},</p>
      <p>Your credential <strong>{certificate_title}</strong> from <strong>{organization_name}</strong> expires on <strong>{expiry_date}</strong>.</p>
      <p><a href="{verification_url}" style="background:#13795b;color:#fff;padding:10px 16px;border-radius:6px;text-decoration:none;">View certificate</a></p>
    </div>
    """
