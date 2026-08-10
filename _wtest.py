import os
import sys
import tempfile

os.environ["WEBHOOK_SECRET"] = "testsecret123"
os.environ["WEB_URL"] = "http://127.0.0.1:5000"

TMP = tempfile.mkdtemp()
SHARED = os.path.join(TMP, "db.db")

sys.path.insert(0, "web")
sys.path.insert(0, ".")

import app as webapp
import db as botdb

webapp.DB_PATH = SHARED
botdb.DB_FILE = SHARED
webapp.init_db()

assert webapp.BOT_TOKEN, "token from .env"
assert webapp._dp is None, "aiogram must be lazy"

c = webapp.app.test_client()

r = c.post("/webhook/wrongsecret", json={"update_id": 1})
assert r.status_code == 403

r = c.post(
    "/webhook/testsecret123",
    json={
        "update_id": 2,
        "message": {
            "message_id": 2,
            "date": 0,
            "chat": {"id": 987654321, "type": "private", "first_name": "T"},
            "from": {"id": 987654321, "is_bot": False, "first_name": "T"},
            "text": "/start",
        },
    },
)
assert r.status_code == 200, (r.status_code, r.data)

import time

time.sleep(2)
assert webapp._aiogram_ready, "aiogram should be initialized after webhook"
user = botdb.get_user(987654321)
assert user is not None
print("LAZY WEBHOOK OK, user created:", user["name"])
