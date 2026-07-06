from flask import Flask, request
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import os
import sqlite3

app = Flask(__name__)

CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")

handler = WebhookHandler(CHANNEL_SECRET)

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)

# DB 생성
conn = sqlite3.connect("counter.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id TEXT PRIMARY KEY,
    count INTEGER
)
""")

conn.commit()


@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature")

    body = request.get_data(as_text=True)

    handler.handle(body, signature)

    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):

    user_id = event.source.user_id
    text = event.message.text

    cursor.execute("SELECT count FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()

    if result:
        cursor.execute(
            "UPDATE users SET count=count+1 WHERE user_id=?",
            (user_id,)
        )
    else:
        cursor.execute(
            "INSERT INTO users(user_id,count) VALUES(?,1)",
            (user_id,)
        )

    conn.commit()

    if text == "!내기록":

        cursor.execute(
            "SELECT count FROM users WHERE user_id=?",
            (user_id,)
        )

        count = cursor.fetchone()[0]

        with ApiClient(configuration) as api_client:
            MessagingApi(api_client).reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(
                            text=f"현재 채팅 횟수 : {count}회"
                        )
                    ]
                )
            )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
