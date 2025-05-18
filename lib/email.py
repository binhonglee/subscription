import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class Email():
    def __init__(self, config):
        self.email = config["address"]
        self.username = config["username"]
        self.password = config["password"]
        self.port = config["port"]
        self.server = config["server"]
        self.confirmation_title = config["confirmation_title"]
        self.confirmation_content = open(config["confirmation_content"], 'r').read()


    def send_confirmation_email(self, to, key) -> bool:
        return self.send_email(
            to,
            self.confirmation_title,
            self.confirmation_content
                .replace("{#EMAIL}", to)
                .replace("{#KEY}", key)
        )


    def send_email(self, to, title, content) -> bool:
        message = MIMEMultipart("alternative")
        message["Subject"] = title
        message["From"] = self.email
        message["To"] = to
        message.attach(MIMEText(content, "html"))

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

