import smtplib
from email.mime.text import MIMEText
from typing import List

from app.config import settings


class EmailService:
    @classmethod
    def send_email(cls, subject: str, body: str, recipients: List[str]):
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = settings.email_service.username
        msg['To'] = ', '.join(recipients)
        smtp_server = smtplib.SMTP_SSL(settings.email_service.smtp_host, settings.email_service.smtp_port)
        smtp_server.login(settings.email_service.username, settings.email_service.password)
        smtp_server.sendmail(settings.email_service.username, recipients, msg.as_string())
        smtp_server.quit()

