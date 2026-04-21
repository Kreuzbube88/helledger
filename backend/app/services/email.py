import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def _build_reset_email(lang: str, reset_url: str) -> tuple[str, str, str]:
    if lang == "de":
        subject = "Passwort zurücksetzen - HELLEDGER"
        text = f"Klicke auf diesen Link, um dein Passwort zurückzusetzen:\n\n{reset_url}\n\nDer Link ist 1 Stunde gültig."
        html = f"<p>Klicke auf diesen Link, um dein Passwort zurückzusetzen:</p><p><a href='{reset_url}'>{reset_url}</a></p><p>Der Link ist 1 Stunde gültig.</p>"
    else:
        subject = "Reset your Password - HELLEDGER"
        text = f"Click this link to reset your password:\n\n{reset_url}\n\nThe link expires in 1 hour."
        html = f"<p>Click this link to reset your password:</p><p><a href='{reset_url}'>{reset_url}</a></p><p>The link expires in 1 hour.</p>"
    return subject, text, html


def _build_invite_email(lang: str, household_name: str, invite_url: str) -> tuple[str, str, str]:
    if lang == "de":
        subject = f"Einladung zum Haushalt '{household_name}' - HELLEDGER"
        text = f"Du wurdest zum Haushalt '{household_name}' eingeladen:\n\n{invite_url}"
        html = f"<p>Du wurdest zum Haushalt '<strong>{household_name}</strong>' eingeladen:</p><p><a href='{invite_url}'>{invite_url}</a></p>"
    else:
        subject = f"Invitation to household '{household_name}' - HELLEDGER"
        text = f"You have been invited to household '{household_name}':\n\n{invite_url}"
        html = f"<p>You have been invited to household '<strong>{household_name}</strong>':</p><p><a href='{invite_url}'>{invite_url}</a></p>"
    return subject, text, html


def _send_sync(to: str, subject: str, body_text: str, body_html: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
    msg["To"] = to
    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_TLS:
            server.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(msg["From"], [to], msg.as_string())


async def send_email(to: str, subject: str, body_text: str, body_html: str) -> None:
    if not settings.SMTP_HOST:
        logger.debug("SMTP not configured, skipping email to %s", to)
        return
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _send_sync, to, subject, body_text, body_html)
