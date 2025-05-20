from lib.config import Config
import json
import sqlite3


config = Config()
connection = sqlite3.connect(config.db_name)
cursor = connection.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS subscribers (
        email TEXT UNIQUE PRIMARY KEY,
        key TEXT UNIQUE,
        started TEXT,
        confirmed BOOLEAN
    );
""")
connection.commit()


emails = cursor.execute("SELECT email, key FROM subscribers WHERE confirmed = TRUE;")
new_content_config = json.load(open("new_content.json", "r"))
new_content_body = open(new_content_config["content_html"], "r").read()
for row in emails:
    config.email_sender.send_email(
        row[0],
        new_content_config["title"],
        new_content_body.replace("{#KEY}", row[1]),
    )
    print("Email sent to " + row[0])
