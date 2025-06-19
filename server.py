from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import datetime
import json
import re
import sqlite3
import sys
import time
import traceback
import uuid
from lib.config import Config
from lib.bad_ip import BadIP
from lib.secret import Secret


config = Config()
connection = sqlite3.connect(config.db_name)
cursor = connection.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS subscribers (
        email TEXT UNIQUE PRIMARY KEY,
        key TEXT,
        started TEXT,
        source_ip TEXT,
        confirmed BOOLEAN
    );
""")
connection.commit()
bad_ip = BadIP()
secret = Secret()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        secret.new_secret()
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        # self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        paths = urlparse(self.path).path.split("/")
        error = ""
        print("GET", paths, "-", self.headers.get('X-Real-IP'))

        match paths[1]:
            case "secret":
                self.wfile.write(secret.get_secret().encode("utf-8"))
            case "subscribe":
                self.wfile.write((config.landing.replace("{#SECRET}", secret.get_secret())).encode("utf-8"))
            case "confirm":
                try:
                    key = paths[2]
                    email = email_from_key(key)
                    if not email:
                        error = "invalid key"
                    else:
                        error = confirm(key)
                except Exception as e:
                    print("get_confirm - ", e)
                    error = "something went wrong"

                if not error:
                    self.wfile.write(
                        (config.confirm_success_response.replace("{#EMAIL_INPUT}", email))
                            .encode("utf-8")
                    )
                else:
                    self.wfile.write(
                        (config.confirm_error_response
                            .replace("{#EMAIL_INPUT}", email)
                            .replace("{#ERROR_MESSAGE}", error)
                        ).encode("utf-8")
                    )
            case "unsubscribe":
                try:
                    key = paths[2]
                    email = email_from_key(key)
                    if not email:
                        error = "invalid key"
                    else:
                        error = unsubscribe_key(key)
                except Exception as e:
                    print("get_unsubscribe - ", e)
                    error = "something went wrong"

                if not error:
                    print('\033[91m' + "Unsubscribed: " + email + '\033[0m')
                    self.wfile.write(
                        (config.unsubscribe_success_response
                            .replace("{#EMAIL_INPUT}", email)
                            .replace("{#SECRET}", secret.get_secret())
                        ).encode("utf-8")
                    )
                else:
                    self.wfile.write(
                        (config.unsubscribe_error_response
                            .replace("{#EMAIL_INPUT}", email)
                            .replace("{#ERROR_MESSAGE}", error)
                        ).encode("utf-8")
                    )
            case _:
                self.wfile.write((config.landing.replace("{#SECRET}", secret.get_secret())).encode("utf-8"))


    def do_POST(self):
        secret.new_secret()
        content_length = int(self.headers["Content-Length"])
        post_data = parse_qs(self.rfile.read(content_length).decode("utf-8"))
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        path = urlparse(self.path).path
        error = ""
        print("POST", path, "-", self.headers.get('X-Real-IP'), "-", post_data)

        match path:
            case "/subscribe":
                if "secret" not in post_data or len(post_data["secret"]) != 1:
                    email = ""
                    if "email" in post_data and len(post_data["email"]) > 0:
                        email = post_data["email"][0]
                    new_bad_ip(self.headers.get('X-Real-IP') or "")
                    
                    self.wfile.write(
                        (config.subscribe_success_response.replace("{#EMAIL_INPUT}", email))
                            .encode("utf-8")
                    )
                    return

                if not secret.is_valid(post_data["secret"][0]):
                    email = ""
                    if "email" in post_data and len(post_data["email"]) > 0:
                        email = post_data["email"][0]
                    self.wfile.write(
                        (config.subscribe_success_response.replace("{#EMAIL_INPUT}", email))
                            .encode("utf-8")
                    )
                    return

                try:
                    email = ""
                    if "email" in post_data and len(post_data["email"]) > 0:
                        email = post_data["email"][0]
                    error = subscribe(email, self.headers.get('X-Real-IP') or "")
                except Exception as e:
                    print("post_subscribe - ", e, email)
                    error = "something went wrong"

                self.wfile.write(
                    (config.subscribe_success_response.replace("{#EMAIL_INPUT}", email))
                        .encode("utf-8")
                )
            case "/confirm":
                try:
                    email = ""
                    if "email" in post_data and len(post_data["email"]) > 0:
                        email = post_data["email"][0]
                    key = ""
                    if "key" in post_data and len(post_data["key"]) > 0:
                        key = post_data["key"][0]
                    error = confirm(key)
                except Exception as e:
                    print("post_confirm - ", e)
                    error = "something went wrong"

                if not error:
                    self.wfile.write(
                        (config.confirm_success_response.replace("{#EMAIL_INPUT}", email))
                            .encode("utf-8")
                    )
                else:
                    self.wfile.write(
                        (config.confirm_error_response
                            .replace("{#EMAIL_INPUT}", email)
                            .replace("{#ERROR_MESSAGE}", error)
                        ).encode("utf-8")
                    )
            case "/unsubscribe":
                try:
                    email = ""
                    if "email" in post_data and len(post_data["email"]) > 0:
                        email = post_data["email"][0]
                    key = ""
                    if "key" in post_data and len(post_data["key"]) > 0:
                        key = post_data["key"][0]
                    error = unsubscribe(email)
                except Exception as e:
                    print("post_unsubscribe - ", e)
                    error = "something went wrong"

                if not error:
                    print('\033[91m' + "Unsubscribed: " + email + '\033[0m')
                    self.wfile.write(
                        (config.unsubscribe_success_response
                            .replace("{#EMAIL_INPUT}", email)
                            .replace("{#SECRET}", secret.get_secret())
                        ).encode("utf-8")
                    )
                else:
                    self.wfile.write(
                        (config.unsubscribe_error_response
                            .replace("{#EMAIL_INPUT}", email)
                            .replace("{#ERROR_MESSAGE}", error)
                        ).encode("utf-8")
                    )
            case _:
                new_bad_ip(self.headers.get('X-Real-IP') or "")
                self.wfile.write((config.landing.replace("{#SECRET}", secret.get_secret())).encode("utf-8"))


def subscribe(email: str, source_ip: str) -> str:
    if not is_valid_email(email):
        print("post_subscribe (invalid email) - ", email)
        return "email is invalid"

    if cursor.execute("SELECT 1 FROM subscribers WHERE email = '%s';" % email).fetchone():
        print("post subscribe (email exist) - ", email)
        return ""
    else:
        key = str(uuid.uuid4())
        time.sleep(5)
        if bad_ip.is_bad(email, source_ip):
            print("post subscribe (bad_ip) - ", email)
            return ""
        elif config.email_sender.send_confirmation_email(email, key):
            cursor.execute("""
                    INSERT INTO subscribers (email, key, started, source_ip, confirmed)
                    VALUES (?, ?, ?, ?, ?);
                """,
                (email, key, datetime.datetime.now().isoformat(), source_ip, False)
            )
            connection.commit()
            config.email_sender.new_subscription_notification(email)
            return ""
        else:
            print("post_subscribe (failed to send) - ", email)
            return "failed to send email"


def email_from_key(key: str) -> str:
    email = cursor.execute("SELECT email FROM subscribers WHERE key = '%s';" % key).fetchone()
    if email:
        return "".join(email)
    else:
        return ""


def confirm(key: str) -> str:
    email = cursor.execute("SELECT email FROM subscribers WHERE key = '%s' AND confirmed = FALSE;" % key).fetchone()
    if email:
        email = "".join(email)
        cursor.execute("""
            UPDATE subscribers
            SET confirmed = TRUE
            WHERE email = '{0}' and key = '{1}'
        """.format("".join(email), key))
        connection.commit()
        config.email_sender.new_confirmed_subscriber_notification(email)
        print('\033[92m' + "New subscriber confirmed: " + email + '\033[0m')
        return ""
    else:
        return "invalid key"


def unsubscribe_key(key: str) -> str:
    email = email_from_key(key)
    if email:
        cursor.execute("""
            DELETE FROM subscribers
            WHERE email = '%s';
        """ % email)
        connection.commit()
        return ''
    else:
        return "invalid key"


def unsubscribe(email: str) -> str | None:
    if not is_valid_email(email):
        return "email is invalid"

    if cursor.execute("SELECT 1 FROM subscribers WHERE email = '%s';" % email).fetchone():
        cursor.execute("""
            DELETE FROM subscribers
            WHERE email = '%s';
        """ % email)
        connection.commit()


def new_bad_ip(ip: str):
    bad_ip.new_bad(ip)
    emails = cursor.execute("SELECT email FROM subscribers WHERE source_ip = '%s';" % ip)
    for row in emails:
        bad_ip.new_bad_email(row[0])
    cursor.execute("""
        DELETE FROM subscribers
        WHERE source_ip = '%s';
    """ % ip)
    connection.commit()


def is_valid_email(email: str) -> bool:
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None


if __name__ == "__main__":
    server_address = ("", config.port)
    httpd = HTTPServer(server_address, Handler)
    print("Server started at port " + str(config.port))
    httpd.serve_forever()
