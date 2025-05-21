import json
from lib.email import Email


class Config():
    def __init__(self):
        config = json.load(open("config.json", "r"))
        self.secret = config["secret"]
        self.email_sender = Email(config["email"])
        page_template = open(config["template"], "r").read()
        self.landing = open(config["landing"], "r").read()
        self.subscribe_success_response = page_template.replace("{#CONTENT}", open(config["subscribe"]["success_template"], "r").read())
        self.subscribe_error_response = page_template.replace("{#CONTENT}", open(config["subscribe"]["error_template"], "r").read())
        self.confirm_success_response = page_template.replace("{#CONTENT}", open(config["confirm"]["success_template"], "r").read())
        self.confirm_error_response = page_template.replace("{#CONTENT}", open(config["confirm"]["error_template"], "r").read())
        self.unsubscribe_success_response = page_template.replace("{#CONTENT}", open(config["unsubscribe"]["success_template"], "r").read())
        self.unsubscribe_error_response = page_template.replace("{#CONTENT}", open(config["unsubscribe"]["error_template"], "r").read())

        self.db_name = "subscription.db"
        if "db_name" in config:
            self.db_name = config["db_name"]

        self.port = 8000
        if "port" in config:
            self.port = config["port"]
