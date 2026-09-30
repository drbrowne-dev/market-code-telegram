import os
import requests
from image_gen import generate_image

obj = os.environ.get("HERO_OBJECT", "three gold bars")
img, source = generate_image(obj)

r = requests.post(
    f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendPhoto",
    data={"chat_id": os.environ["TELEGRAM_CHAT_ID"], "caption": f"Test image via {source}"},
    files={"photo": ("image.jpg", img, "image/jpeg")},
    timeout=60,
)
r.raise_for_status()
print("Sent to Telegram")
