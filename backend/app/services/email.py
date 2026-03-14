import smtplib
from email.message import EmailMessage

from app.core.config import settings


def send_email(subject: str, body: str, recipient: str) -> bool:
    if not settings.smtp_host:
        print("[email] SMTP not configured. Skipping email send.")
        print(f"[email] To: {recipient}\nSubject: {subject}\n\n{body}")
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from
    message["To"] = recipient
    message.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(message)
    return True


def send_invite_email(recipient: str, property_name: str) -> bool:
    subject = f"You're invited to {property_name} Hotel Cash"
    body = (
        f"You have been invited to access {property_name} Hotel Cash Management.\n\n"
        f"Login: {settings.frontend_url}/login\n"
        f"Email: {recipient}\n\n"
        "Enter your email to receive a one-time verification code."
    )
    return send_email(subject, body, recipient)


def send_mfa_code(recipient: str, code: str) -> bool:
    subject = "Your Hotel Cash verification code"
    body = (
        f"Your verification code is: {code}\n\n"
        f"This code expires in {settings.mfa_code_expire_minutes} minutes."
    )
    return send_email(subject, body, recipient)
