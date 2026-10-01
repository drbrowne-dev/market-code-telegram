import os
import re
import json
import html
import time
import datetime
import requests
import feedparser
from image_gen import generate_image
import webpage

FEEDS = [
    "https://www.federalreserve.gov/feeds/press_all.xml",
    "http://feeds.bbci.co.uk/news/business/rss.xml",
    "https://www.cnbc.com/id/10000664/device/rss/rss.html",
    "https://www.ecb.europa.eu/rss/press.html",
]
MODELS = [
    os.environ.get("GEMINI_MODEL", "gemini-3.8-flash"),
    "gemini-3.7-flash",
    "gemini-3.5-flash-lite",
]
LANG = os.environ.get("POST_LANGUAGE", "English")
HISTORY_FILE = "history.json"
DOCS = "../docs"


def clean(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def as_list(v):
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    return [p.strip() for p in str(v).split("\n") if p.strip()]


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


def get_items():
    items = []
    for url in FEEDS:
        feed = feedparser.parse(url)
        print(f"{url} -> {len(feed.entries)} items")
        source = clean(feed.feed.get("title", "")) or url.split("/")[2]
        for e in feed.entries[:6]:
            title = clean(e.get("title"))
            if title:
                items.append(
                    {
                        "title": title,
                        "summary": clean(e.get("summary"))[:400],
                        "link": e.get("link", ""),
                        "source": source,
                    }
                )
    if not items:
        raise RuntimeError("No items found from any feed")
    return items


def call_gemini(key, prompt):
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    headers = {"x-goog-api-key": key, "Content-Type": "application/json"}
    last = "no attempt made"
    for model in MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        for attempt in range(1, 4):
            try:
                r = requests.post(url, headers=headers, json=body, timeout=120)
            except requests.RequestException as e:
                last = f"{model}: {e}"
                print(f"Gemini network error ({model}, try {attempt}):", e)
                time.sleep(10 * attempt)
                continue
            if r.status_code == 200:
                print("Gemini model used:", model)
                return r.json()
            last = f"{model}: {r.status_code}"
            print(f"Gemini error ({model}, try {attempt}):", r.status_code, r.text[:300])
            if r.status_code in (400, 403, 404):
                break
            time.sleep(15 * attempt)
    raise RuntimeError("All Gemini models failed. Last: " + last)


def ask_gemini(items, history):
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GEMINI_API_KEY secret is empty or missing")
    print("Gemini key length:", len(key))

    recent = "\n".join(
        f"- {h['headline']} | image: {h['image_subject']}" for h in history[-10:]
    ) or "- (none yet)"
    listing = "\n".join(
        f"[{i}] {it['title']} -- {it['summary']} ({it['source']})"
        for i, it in enumerate(items)
    )
    prompt = (
        "You are the editor of THE MARKET CODE by E11 Lab, an educational "
        "trading-psychology and market-insight publication.\n"
        "Below are today's news items from public feeds, each with an index, "
        "title and short summary.\n"
        "Pick the ONE item most relevant to traders (gold, forex, indices, oil, "
        "crypto, interest rates) that is NOT similar to the recently posted ones. "
        "Write ORIGINAL commentary about it in " + LANG + ".\n"
        "Use ONLY facts found in the chosen item's title and summary. Do not "
        "invent numbers, quotes, dates or events. If details are thin, keep the "
        "facts brief and explain the concept and context for traders (for "
        "example how rate decisions or oil prices can affect a currency). Never "
        "copy sentences from the source. Never give buy or sell signals or price "
        "targets. Calm, professional tone.\n"
        "Return ONLY JSON with these keys:\n"
        "headline: max 10 words, news style;\n"
        "teaser: 2 short sentences, max 260 characters, for the Telegram post "
        "and the website card;\n"
        "article: a list of 4 to 6 paragraphs (about 250 to 400 words in total) "
        "explaining what happened, why it matters, and what traders should watch;\n"
        "takeaways: a list of exactly 3 short bullet points;\n"
        "image_subject: ONE scene description (max 35 words) for a collage "
        "illustration that visually tells THIS specific story using 3 kinds of "
        "elements: (1) the main subject tied to the story, such as the country's "
        "central bank or government building, a recognizable national landmark, "
        "the relevant country map, an oil pump jack or tanker, gold bars, a "
        "bitcoin coin, a bull or bear statue, or a factory or shopping cart for "
        "economic data; (2) the currencies or assets involved, shown as coins or "
        "banknotes; (3) the direction of the story as a single clear arrow or "
        "bar chart without numbers: pointing up if bullish, pointing down if "
        "bearish, pointing sideways if neutral. Do not mention colours. Choose "
        "elements that look clearly different from the recent images listed "
        "below. No text, numbers or people in the scene;\n"
        "source_index: the integer index of the chosen item.\n\n"
        "RECENTLY POSTED (avoid repeating):\n" + recent + "\n\n"
        "TODAY'S ITEMS:\n" + listing
    )
    data = call_gemini(key, prompt)
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)


def main():
    if not webpage.SITE_URL:
        raise RuntimeError("SITE_URL is not set")

    history = load_history()
    items = get_items()
    post = ask_gemini(items, history)

    try:
        idx = int(post.get("source_index", 0))
    except Exception:
        idx = 0
    if not 0 <= idx < len(items):
        idx = 0
    src = items[idx]
    print("Gemini chose:", post["headline"], "| source:", src["source"])
    print("Scene:", post["image_subject"])

    img, provider = generate_image(post["image_subject"])

    today = datetime.date.today().isoformat()
    slug = f"{today}-{webpage.slugify(post['headline'])}"
    os.makedirs(os.path.join(DOCS, "news"), exist_ok=True)
    with open(os.path.join(DOCS, "news", slug + ".jpg"), "wb") as f:
        f.write(img)

    article = {
        "slug": slug,
        "date": today,
        "headline": post["headline"].strip(),
        "teaser": post["teaser"].strip(),
        "source_name": src["source"],
        "source_url": src["link"] or "#",
    }
    articles = webpage.load_articles(DOCS)
    articles.insert(0, article)
    webpage.save_articles(DOCS, articles)
    webpage.write_site(
        DOCS, article, as_list(post["article"]), as_list(post["takeaways"]), articles
    )

    last = {
        "headline": article["headline"],
        "teaser": article["teaser"],
        "url": f"{webpage.SITE_URL}/news/{slug}.html",
        "image_path": f"{DOCS}/news/{slug}.jpg",
    }
    with open("last_post.json", "w", encoding="utf-8") as f:
        json.dump(last, f, ensure_ascii=False, indent=2)

    save_history(
        history,
        {
            "date": today,
            "headline": article["headline"],
            "image_subject": post["image_subject"],
        },
    )
    print(f"Article built (image via {provider}):", last["url"])


main()
