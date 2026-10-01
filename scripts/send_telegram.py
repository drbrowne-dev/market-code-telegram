import os
import json
import html
import requests

with open("last_post.json", encoding="utf-8") as f:
    post = json.load(f)

url = html.escape(post["url"], quote=True)

caption = (
    f"<b>{html.escape(post['headline'])}</b>\n\n"
    f"{html.escape(post['teaser'])}\n\n"
    f'<a href="{url}">Read More👈</a>'
)

with open(post["image_path"], "rb") as img:
    r = requests.post(
        f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendPhoto",
        data={
            "chat_id": os.environ["TELEGRAM_CHAT_ID"],
            "caption": caption,
            "parse_mode": "HTML",
        },
        files={"photo": ("image.jpg", img, "image/jpeg")},
        timeout=60,
    )
r.raise_for_status()
print("Sent to Telegram:", post["url"])
