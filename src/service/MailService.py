import asyncio
import smtplib
import ssl
import os
from datetime import datetime
from email.message import EmailMessage
from http.client import HTTPException

from src.config.scheduler import scheduler
from src.service.Logger import logger


class MailService:
    def __init__(self):
        self.password = os.environ.get('MAIL_PASSWORD')
        self.port = 465
        self.email = os.environ.get('MAIL_EMAIL')
        self.smtp_server = "smtp.zoho.com"

    def _send_email(self, receiver: str, subject: str, content: str):
        context = ssl.create_default_context()
        msg = EmailMessage()
        msg.set_content(content, subtype='html')
        msg['Subject'] = subject
        msg['From'] = self.email
        msg['To'] = receiver
        logger.info(f"Sending email from {self.email} to {receiver} with subject {subject}")
        self._send_email_sync(msg, context)

    async def _send_email_with_file(self, receiver: str, subject: str, content: str, file, filename):
        context = ssl.create_default_context()
        msg = EmailMessage()
        msg.set_content(content, subtype='html')
        msg['Subject'] = subject
        msg['From'] = self.email
        msg['To'] = receiver
        msg.add_attachment(file, maintype='application', subtype='octet-stream', filename=filename)
        await asyncio.to_thread(self._send_email_sync, msg, context)

    def _send_email_sync(self, msg, context):
        with smtplib.SMTP_SSL(self.smtp_server, self.port, context=context) as server:
            server.login(self.email, self.password)
            server.send_message(msg)

    def _send_emails(self, receivers: list[str], subject: str, message: str):
        for to in receivers:
            self._send_email(to, subject, message)

    def _schedule_email(self, receiver: str, subject: str, content: str, date: datetime):
        try:
            scheduler.add_job(
                self._send_email,
                'date',
                run_date=date,
                args=[receiver, subject, content],
                id=f"email_{datetime.now().strftime('%d_%m_%Y-%H:%M:%S:%MS')}",
                replace_existing=True
            )
            return {"message": "Notification scheduled successfully!"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

