import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.utils import formataddr


class Email():
    def __init__(self, config):
        self.email = config["address"]
        self.name = config["name"]
        self.username = config["username"]
        self.password = config["password"]
        self.to = config["to"]
        self.port = config["port"]
        self.server = config["server"]
        self.confirmation_title = config["confirmation_title"]
        self.confirmation_content = open(config["confirmation_content"], 'r').read()


    def send_confirmation_email(self, to, key) -> bool:
        return self.send_html_email(
            to,
            self.confirmation_title,
            self.confirmation_content
                .replace("{#EMAIL}", to)
                .replace("{#KEY}", key)
        )


    def send_html_email(self, to, title, content) -> bool:
        message = MIMEMultipart("alternative")
        message["Subject"] = title
        message["From"] = formataddr((self.name, self.email))
        message["To"] = to
        message.attach(MIMEText(content, "html"))
        return self.send_email(to, message)


    def new_subscription_notification(self, subscriber: str) -> bool:
        message = MIMEText("New subscriber: " + subscriber)
        message["Subject"] = "New subscriber attempt"
        message["From"] = self.email
        message["To"] = self.to
        return self.send_email(self.to, message)


    def new_confirmed_subscriber_notification(self, subscriber: str) -> bool:
        message = MIMEText("New confirmed subscriber: " + subscriber)
        message["Subject"] = "New subscriber!"
        message["From"] = self.email
        message["To"] = self.to
        return self.send_email(self.to, message)


    def send_email(self, to: str, message: MIMEBase) -> bool:
        context = ssl.create_default_context()
        if self.port == 587:
            with smtplib.SMTP(self.server, self.port) as server:
                server.starttls(context=context)
                return self.login_and_send(to, server, message)
        else:
            with smtplib.SMTP_SSL(self.server, self.port, context=context) as server:
                return self.login_and_send(to, server, message)


    def login_and_send(self, to, server, message) -> bool:
        try:
            server.login(self.username, self.password)
            server.sendmail(
                self.email, to, message.as_string()
            )
            return True
        except Exception:
            return False

