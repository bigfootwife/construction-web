"""Resend email helper."""
import asyncio
import logging
import resend

from .config import RESEND_API_KEY, SENDER_EMAIL, INQUIRY_NOTIFICATION_EMAIL

logger = logging.getLogger("stonebridge.mailer")
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


def _build_inquiry_email_html(inq: dict) -> str:
    return f"""
    <table style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;border:1px solid #E5E2DA;border-collapse:collapse;">
      <tr><td style="background:#A85A3F;color:#fff;padding:20px;font-size:18px;font-weight:bold;letter-spacing:2px;text-transform:uppercase;">New Inquiry · Stonebridge</td></tr>
      <tr><td style="padding:24px;">
        <p style="margin:0 0 16px;color:#1C1C1A;font-size:16px;">A new project inquiry has been received.</p>
        <table style="width:100%;border-collapse:collapse;font-size:14px;">
          <tr><td style="padding:8px 0;color:#6E6D69;width:140px;">Name</td><td style="padding:8px 0;color:#1C1C1A;font-weight:600;">{inq.get('name','')}</td></tr>
          <tr><td style="padding:8px 0;color:#6E6D69;">Email</td><td style="padding:8px 0;color:#1C1C1A;"><a href="mailto:{inq.get('email','')}" style="color:#A85A3F;">{inq.get('email','')}</a></td></tr>
          <tr><td style="padding:8px 0;color:#6E6D69;">Phone</td><td style="padding:8px 0;color:#1C1C1A;">{inq.get('phone') or '—'}</td></tr>
          <tr><td style="padding:8px 0;color:#6E6D69;">Project Type</td><td style="padding:8px 0;color:#1C1C1A;">{inq.get('project_type','')}</td></tr>
          <tr><td style="padding:8px 0;color:#6E6D69;">Budget</td><td style="padding:8px 0;color:#1C1C1A;">{inq.get('budget') or '—'}</td></tr>
        </table>
        <hr style="border:none;border-top:1px solid #E5E2DA;margin:20px 0;">
        <p style="margin:0 0 8px;color:#6E6D69;font-size:12px;text-transform:uppercase;letter-spacing:2px;">Message</p>
        <p style="margin:0;color:#1C1C1A;font-size:14px;line-height:1.6;white-space:pre-wrap;">{inq.get('message','')}</p>
      </td></tr>
      <tr><td style="background:#F5F3EF;color:#6E6D69;padding:14px 24px;font-size:12px;">Sent {inq.get('created_at','')} · Inquiry ID: {inq.get('inquiry_id','')}</td></tr>
    </table>
    """


async def send_inquiry_email(inq: dict) -> None:
    if not RESEND_API_KEY or not INQUIRY_NOTIFICATION_EMAIL:
        logger.info("Resend not configured; skipping email")
        return
    params = {
        "from": SENDER_EMAIL,
        "to": [INQUIRY_NOTIFICATION_EMAIL],
        "reply_to": inq.get("email"),
        "subject": f"New Inquiry · {inq.get('name','')} · {inq.get('project_type','')}",
        "html": _build_inquiry_email_html(inq),
    }
    try:
        result = await asyncio.to_thread(resend.Emails.send, params)
        logger.info("Inquiry email sent: %s", result.get("id"))
    except Exception as e:
        logger.error("Inquiry email send failed: %s", e)
