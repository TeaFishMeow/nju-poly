from email.message import EmailMessage
import smtplib

from app.core.config import settings


class EmailDelivery:
    SMTP = "smtp"
    LOCAL_DEV = "local_dev"


def send_verification_email(*, email: str, code: str) -> str:
    if not settings.smtp_enabled:
        return EmailDelivery.LOCAL_DEV

    message = EmailMessage()
    message["Subject"] = "南哪竞猜 NJUPoly 验证码"
    message["From"] = settings.smtp_from
    message["To"] = email
    message.set_content(f"你的南哪竞猜验证码是 {code}，{settings.verification_code_ttl_minutes} 分钟内有效。")

    smtp_class = smtplib.SMTP_SSL if settings.smtp_use_ssl else smtplib.SMTP
    with smtp_class(settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout_seconds) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_username and settings.smtp_password:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)

    return EmailDelivery.SMTP
