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


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        paths = urlparse(self.path).path.split("/")
        error = ""
        print("GET", paths, "-", self.headers.get('X-Real-IP'))

        match paths[1]:
            case "subscribe":
                self.wfile.write((config.landing).encode("utf-8"))
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
                    self.wfile.write(
                        (config.unsubscribe_success_response
                            .replace("{#EMAIL_INPUT}", email)
                            .replace("{#SECRET}", config.secret)
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
                self.wfile.write((config.landing).encode("utf-8"))


    def do_POST(self):
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
                if "secret" not in post_data or len(post_data["secret"]) != 1 or post_data["secret"][0] != config.secret:
                    email = ""
                    if "email" in post_data and len(post_data["email"]) > 0:
                        email = post_data["email"][0]
                    bad_ip.new_bad(self.headers.get('X-Real-IP') or "")
                    
                    self.wfile.write(
                        (config.subscribe_success_response.replace("{#EMAIL_INPUT}", email))
                            .encode("utf-8")
                    )
                    return

                try:
                    email = ""
                    if "email" in post_data and len(post_data["email"]) > 0:
                        email = post_data["email"][0]
                    error = subscribe(email, self.headers.get('X-Real-IP'))
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
                    self.wfile.write(
                        (config.unsubscribe_success_response
                            .replace("{#EMAIL_INPUT}", email)
                            .replace("{#SECRET}", config.secret)
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
                bad_ip.new_bad(email, self.headers.get('X-Real-IP') or "")
                self.wfile.write((config.landing).encode("utf-8"))


def subscribe(email: str, source_ip: str) -> str:
    if not isValidEmail(email):
        print("post_subscribe (invalid email) - ", email)
        return "email is invalid"

    if cursor.execute("SELECT 1 FROM subscribers WHERE email = '%s';" % email).fetchone():
        return ""
    else:
        key = str(uuid.uuid4())
        time.sleep(5)
        if bad_ip.is_bad(source_ip):
            return ""
        elif config.email_sender.send_confirmation_email(email, key):
            cursor.execute("""
                    INSERT INTO subscribers (email, key, started, source_ip, confirmed)
                    VALUES (?, ?, ?, ?, ?);
                """,
                (email, key, datetime.datetime.now().isoformat(), source_ip, False)
            )
            connection.commit()
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
    email = email_from_key(key)
    if email:
        cursor.execute("""
            UPDATE subscribers
            SET confirmed = TRUE
            WHERE email = '{0}' and key = '{1}'
        """.format("".join(email), key))
        connection.commit()
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


def unsubscribe(email: str) -> str:
    if not isValidEmail(email):
        return "email is invalid"

    if cursor.execute("SELECT 1 FROM subscribers WHERE email = '%s';" % email).fetchone():
        cursor.execute("""
            DELETE FROM subscribers
            WHERE email = '%s';
        """ % email)
        connection.commit()


def isValidEmail(email: str) -> bool:
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email)


if __name__ == "__main__":
    server_address = ("", config.port)
    httpd = HTTPServer(server_address, Handler)
    print("Server started at port " + str(config.port))
    httpd.serve_forever()
