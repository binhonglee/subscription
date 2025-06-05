from lib.config import Config
import json
import sqlite3
from lib.bad_ip import BadIP


config = Config()
connection = sqlite3.connect(config.db_name)
cursor = connection.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS subscribers (
        email TEXT UNIQUE PRIMARY KEY,
        key TEXT UNIQUE,
        started TEXT,
        source_ip TEXT,
        confirmed BOOLEAN
    );
""")
connection.commit()
bad_ip = BadIP()
emails = cursor.execute("SELECT email, key, source_ip FROM subscribers WHERE confirmed = TRUE;")
new_content_config = json.load(open("new_content.json", "r"))
new_content_body = open(new_content_config["content_html"], "r").read()
for row in emails:
    if row[2] is not None and bad_ip.is_bad("", row[2]):
        print("Email sending skipped for " + row[0])
    else:
        # config.email_sender.send_html_email(
        #     row[0],
        #     new_content_config["title"],
        #     new_content_body.replace("{#KEY}", row[1]),
        # )
        print("Email sent to " + row[0])
