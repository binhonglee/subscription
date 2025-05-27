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
ips = cursor.execute("SELECT source_ip FROM subscribers;")
to_remove = []
for ip in ips:
    to_remove.append(ip[0])
for row in to_remove:
    if row is not None and bad_ip.is_bad("", row):
        emails = cursor.execute("SELECT email FROM subscribers WHERE source_ip = '%s';" % row)
        for email in emails:
            print(email[0])
            bad_ip.new_bad_email(email[0])
        cursor.execute("DELETE FROM subscribers WHERE source_ip = '%s' AND confirmed = FALSE;" % row)

connection.commit()