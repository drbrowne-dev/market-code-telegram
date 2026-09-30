import os
import random
import requests
from image_gen import generate_image

SCENES = [
    "a neoclassical central bank building with tall columns, a pound coin and a dollar banknote in front, a falling arrow",
    "an oil pump jack beside a storage tank, an oil barrel in front, a steep rising arrow",
    "a map of the United States with a rising zigzag arrow",
    "a euro coin and a yen coin facing each other, a pagoda and a cherry blossom branch behind, a bar chart without numbers",
    "a large metallic bitcoin coin with circuit-board lines and a candlestick bar chart without numbers, rising",
    "a bull statue facing a descending arrow, stock exchange columns behind",
    "three plain gold bars with blank unmarked surfaces, a gold coin, a flat sideways arrow",
    "a factory with smokestacks and a shopping cart in front, a falling arrow, a euro coin",
    "a map of Europe with a highlighted shape over Germany, euro coins and a downward arrow",
]

scene = os.environ.get("HERO_OBJECT", "").strip() or random.choice(SCENES)
print("Scene:", scene)

img, source = generate_image(scene)

r = requests.post(
    f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendPhoto",
    data={"chat_id": os.environ["TELEGRAM_CHAT_ID"], "caption": f"{scene}\n(image via {source})"},
    files={"photo": ("image.jpg", img, "image/jpeg")},
    timeout=60,
)
r.raise_for_status()
print("Sent to Telegram")
