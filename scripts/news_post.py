import os
import json
import datetime
import requests
import feedparser
from image_gen import generate_image

FEEDS = [
    "https://www.federalreserve.gov/feeds/press_all.xml",
    "http://feeds.bbci.co.uk/news/business/rss.xml",
    "https://www.cnbc.com/id/10000664/device/rss/rss.html",
    "https://www.ecb.europa.eu/rss/press.html",
]
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
LANG = os.environ.get("POST_LANGUAGE", "English")
HISTORY_FILE = "history.json"


def load_history():
    try:
        with open(HISTORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_history(history, entry):
    history.append(entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history[-40:], f, ensure_ascii=False, indent=2)


def get_headlines():
    items = []
    for url in FEEDS:
        feed = feedparser.parse(url)
        print(f"{url} -> {len(feed.entries)} items")
        for e in feed.entries[:6]:
            title = e.get("title", "").strip()
            if title:
                items.append(f"- {title} ({url.split('/')[2]})")
    if not items:
        raise RuntimeError("No headlines found from any feed")
    return items


def ask_gemini(headlines, history):
    recent = "\n".join(
        f"- {h['headline']} | image: {h['image_subject']}" for h in history[-10:]
    ) or "- (none yet)"
    prompt = (
        "You are the editor of THE MARKET CODE, an educational trading-psychology "
        "and market-insight Telegram channel.\n"
        "Below are today's headlines from public news feeds.\n"
        "Pick the ONE story most relevant to traders (gold, forex, indices, oil, "
        "crypto, interest rates) that is NOT similar to the recently posted ones. "
        "Write a short original post about it in " + LANG + ".\n"
        "Rules for the post: do not copy headline wording; 3 to 5 short lines; "
        "explain what happened and what traders should watch; never give buy or "
        "sell signals or price targets; calm, professional tone.\n"
        "Rules for image_subject: write ONE scene description (max 35 words) for "
        "a collage illustration that visually tells THIS specific story using 3 "
        "kinds of elements: (1) the main subject tied to the story, such as the "
        "country's central bank or government building, a recognizable national "
        "landmark, the relevant country map, an oil pump jack or tanker, gold "
        "bars, a bitcoin coin, a bull or bear statue, or a factory or shopping "
        "cart for economic data; (2) the currencies or assets involved, shown as "
        "coins or banknotes; (3) the direction of the story as an orange arrow "
        "or bar chart without numbers: rising if bullish, falling if bearish, "
        "flat if neutral. Choose elements that look clearly different from the "
        "recent images listed below. No text, numbers or people in the scene.\n"
        "Return ONLY JSON with keys: headline (max 8 words), body, image_subject.\n\n"
        "RECENTLY POSTED (avoid repeating):\n" + recent + "\n\n"
        "TODAY'S HEADLINES:\n" + "\n".join(headlines)
    )
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    r = requests.post(
        url,
        headers={
            "x-goog-api-key": os.environ["GEMINI_API_KEY"],
            "Content-Type": "application/json",
        },
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"},
        },
        timeout=90,
    )
    r.raise_for_status()
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)


def main():
    history = load_history()
    headlines = get_headlines()
    post = ask_gemini(headlines, history)
    print("Gemini chose:", post["headline"], "|", post["image_subject"])

    img, source = generate_image(post["image_subject"])

    caption = (
        f"📰 {post['headline'].upper()}\n\n"
        f"{post['body']}\n\n"
        "⚠️ Educational only. Not financial advice.\n"
        "━━━━━━━━━━\n"
        "THE MARKET CODE"
    )[:1000]

    r = requests.post(
        f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendPhoto",
        data={"chat_id": os.environ["TELEGRAM_CHAT_ID"], "caption": caption},
        files={"photo": ("image.jpg", img, "image/jpeg")},
        timeout=60,
    )
    r.raise_for_status()
    print(f"Posted (image via {source})")

    save_history(
        history,
        {
            "date": datetime.date.today().isoformat(),
            "headline": post["headline"],
            "image_subject": post["image_subject"],
        },
    )


main()
