import os
import random
import requests
from image_gen import generate_image

SUBJECTS = [
    "a stack of three smooth plain gold bars with blank unmarked surfaces",
    "a wooden oil barrel with a drop of black crude oil",
    "a fan of US dollar banknotes",
    "a single large metallic bitcoin coin standing on its edge",
    "a gavel resting on stacked coins",
    "a bull figurine made of dark metal",
    "a shopping basket filled with coins",
    "a brass balance scale holding coins",
    "a cracked piggy bank with coins spilling out",
    "a metal padlock on a pile of coins",
]

obj = os.environ.get("HERO_OBJECT", "").strip() or random.choice(SUBJECTS)
print("Subject:", obj)

img, source = generate_image(obj)

r = requests.post(
    f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendPhoto",
    data={"chat_id": os.environ["TELEGRAM_CHAT_ID"], "caption": f"{obj}\n(image via {source})"},
    files={"photo": ("image.jpg", img, "image/jpeg")},
    timeout=60,
)
r.raise_for_status()
print("Sent to Telegram")
