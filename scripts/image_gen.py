import os
import random
import base64
import requests
from urllib.parse import quote

STYLE = (
    "Editorial mixed-media collage illustration for a financial news article, "
    "{bg}. Desaturated black-and-white photographic cutouts of the scene "
    "elements, combined with bold flat graphic shapes in vivid cyan (turquoise) "
    "and emerald green. Limited palette: black, charcoal grey, white, vivid "
    "cyan, emerald green. Any rising arrow or chart is emerald green, any "
    "falling arrow or chart is cyan. Scene: {scene}. {layout}. {extras}. "
    "Torn paper edges, subtle paper grain, clean flat composition, no orange, "
    "no red, no readable text, no letters, no numbers, no logos, no watermark, "
    "no people"
)

BACKGROUNDS = [
    "on a cream off-white paper background",
    "on a cream off-white paper background",
    "on a cream off-white paper background",
    "on a deep charcoal-black paper background with faint thin grid lines",
]

LAYOUTS = [
    "A large vivid cyan circle behind the main subject and a smaller emerald green circle at the edge",
    "Main subject on the left, secondary elements overlapping in the center, a big cyan brush-stroke shape on the right",
    "Main subject centered over a wide emerald green paint smear with black ink splatter below",
    "Two overlapping torn paper layers with a block of cyan behind and green ink drips",
    "Main subject in the lower half with a huge cyan sun-like disc rising behind it",
    "Symmetrical composition with the subject in the middle and cyan and green shapes on both sides",
]

EXTRAS = [
    "A cyan halftone dot pattern in one corner",
    "Thin green radiating lines fanning out from behind the subject",
    "Cyan and green ink splatter dots scattered around",
    "A faint grid of thin lines in the background with a thin green line chart curve",
    "Small torn cyan and green paper strips along one edge",
]


def build_prompt(scene):
    scene = scene.replace("orange ", "").replace("Orange ", "")
    return STYLE.format(
        bg=random.choice(BACKGROUNDS),
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
