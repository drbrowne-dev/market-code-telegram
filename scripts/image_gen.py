import os
import base64
import requests
from urllib.parse import quote

STYLE = (
    "Editorial collage illustration, {obj} as the hero subject, centered, "
    "on a warm cream paper background. Bold orange gouache paint smear behind "
    "the subject, black charcoal ash dust scattered below, subtle paper grain, "
    "soft studio lighting, minimalist, no text, no logos, no letters"
)


def cloudflare_image(prompt):
    account = os.environ["CF_ACCOUNT_ID"]
    token = os.environ["CF_API_TOKEN"]
    url = (
        f"https://api.cloudflare.com/client/v4/accounts/{account}"
        "/ai/run/@cf/black-forest-labs/flux-1-schnell"
    )
    r = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}"},
        json={"prompt": prompt, "steps": 6},
        timeout=90,
    )
    r.raise_for_status()
    return base64.b64decode(r.json()["result"]["image"])


def pollinations_image(prompt):
    url = "https://image.pollinations.ai/prompt/" + quote(prompt)
    r = requests.get(
        url,
        params={"width": 1344, "height": 768, "model": "flux", "nologo": "true"},
        timeout=120,
    )
    r.raise_for_status()
    if not r.headers.get("content-type", "").startswith("image"):
        raise RuntimeError("Pollinations did not return an image")
    return r.content


def generate_image(obj):
    prompt = STYLE.format(obj=obj)
    providers = (("Cloudflare", cloudflare_image), ("Pollinations", pollinations_image))
    for name, fn in providers:
        try:
            data = fn(prompt)
            print(f"Image created by {name}")
            return data, name
        except Exception as e:
            print(f"{name} failed: {e}")
    raise RuntimeError("All image providers failed")
