import threading
import smtplib
from email.mime.text import MIMEText

class EmailService:
    def __init__(self, sender, password, recipient):
        self.sender = sender
        self.password = password
        self.recipient = recipient

    def send_alert_async(self, subject: str, body: str):
        threading.Thread(target=self._send, args=(subject, body), daemon=True).start()

    def _send(self, subject, body):
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = self.recipient

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(self.sender, self.password)
            server.sendmail(self.sender, self.recipient, msg.as_string())
