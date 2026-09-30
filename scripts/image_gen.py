import os
import random
import base64
import requests
from urllib.parse import quote

ANGLES = [
    "three-quarter view",
    "low-angle close-up",
    "top-down view",
    "side profile",
    "slightly tilted dramatic angle",
]
PAINTS = [
    "one large rough orange gouache brush-stroke smear",
    "a bold deep-orange paint swipe",
    "two overlapping orange paint strokes",
    "a wide torn orange paint stain",
]
ASHES = [
    "black charcoal ash and soot particles scattered below",
    "black ink splatter and ash dust drifting to one side",
    "dark charcoal crumbs and dust spilling out beneath",
]


def build_prompt(obj):
    return (
        f"Editorial collage illustration of {obj}, {random.choice(ANGLES)}, "
        "centered on a flat warm cream paper background. Behind the subject, "
        f"{random.choice(PAINTS)}. {random.choice(ASHES)}. "
        "Photorealistic subject, subtle paper grain, soft studio lighting, "
        "lots of empty space, clean minimal composition, no text, no logos, "
        "no letters, no numbers, no engraving or stamps on the object, no people"
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
        params={
            "width": 1344,
            "height": 768,
            "model": "flux",
            "nologo": "true",
            "seed": random.randint(1, 999999),
        },
        timeout=120,
    )
    r.raise_for_status()
    if not r.headers.get("content-type", "").startswith("image"):
        raise RuntimeError("Pollinations did not return an image")
    return r.content


def generate_image(obj):
    prompt = build_prompt(obj)
    print("Image prompt:", prompt)
    providers = (("Cloudflare", cloudflare_image), ("Pollinations", pollinations_image))
    for name, fn in providers:
        try:
            data = fn(prompt)
            print(f"Image created by {name}")
            return data, name
        except Exception as e:
            print(f"{name} failed: {e}")
    raise RuntimeError("All image providers failed")
