import os
import random
import base64
import requests
from urllib.parse import quote

STYLE = (
    "Editorial mixed-media collage illustration for a financial news article, "
    "on a cream off-white paper background. Desaturated black-and-white "
    "photographic cutouts of the scene elements, combined with bold flat "
    "graphic shapes in vivid orange and solid black. Limited palette: cream, "
    "black, charcoal grey, vivid orange. Scene: {scene}. {layout}. {extras}. "
    "Torn paper edges, subtle paper grain, clean flat composition, "
    "no readable text, no letters, no numbers, no logos, no watermark, no people"
)

LAYOUTS = [
    "A large vivid orange circle behind the main subject and a smaller black circle at the edge",
    "Main subject on the left, secondary elements overlapping in the center, a big orange brush-stroke shape on the right",
    "Main subject centered over a wide orange paint smear with black ink splatter below",
    "Two overlapping torn paper layers with a block of orange behind and black ink drips",
    "Main subject in the lower half with a huge orange sun-like disc rising behind it",
    "Symmetrical composition with the subject in the middle and orange and black shapes on both sides",
]
EXTRAS = [
    "An orange halftone dot pattern in one corner",
    "Thin black radiating lines fanning out from behind the subject",
    "Orange and black ink splatter dots scattered around",
    "A faint grid of thin lines in the background",
    "Small torn orange paper strips along one edge",
]


def build_prompt(scene):
    return STYLE.format(
        scene=scene,
        layout=random.choice(LAYOUTS),
        extras=random.choice(EXTRAS),
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


def generate_image(scene):
    prompt = build_prompt(scene)
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
