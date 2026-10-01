import os
import re
import json
import html
import time
import calendar
import datetime
import requests
import feedparser
from image_gen import generate_image
import webpage

FEEDS = [
    # Official sources
    "https://www.federalreserve.gov/feeds/press_monetary.xml",
    "https://www.federalreserve.gov/feeds/press_all.xml",
    "https://www.federalreserve.gov/feeds/speeches.xml",
    "https://www.bls.gov/feed/bls_latest.rss",
    "https://www.ecb.europa.eu/rss/press.html",
    # Markets and economy
    "http://feeds.bbci.co.uk/news/business/rss.xml",
    "https://www.cnbc.com/id/10000664/device/rss/rss.html",
    "https://www.cnbc.com/id/20910258/device/rss/rss.html",
    "https://feeds.content.dowjones.io/public/rss/mw_topstories",
    "https://feeds.content.dowjones.io/public/rss/mw_marketpulse",
    "https://finance.yahoo.com/news/rssindex",
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=GC=F&region=US&lang=en-US",
]
MODELS = [
    os.environ.get("GEMINI_MODEL", "gemini-3.8-flash"),
    "gemini-3.7-flash",
    "gemini-3.5-flash-lite",
]
LANG = os.environ.get("POST_LANGUAGE", "English")
MIN_IMPACT = int(os.environ.get("MIN_IMPACT", "6"))
MAX_POSTS = int(os.environ.get("MAX_POSTS_PER_DAY", "8"))
MAX_AGE_HOURS = 36
USER_AGENT = "Mozilla/5.0 (compatible; MarketCodeBot/1.0)"
HISTORY_FILE = "history.json"
DOCS = "../docs"

KEYWORDS = {
    "gold": 5, "xau": 5, "bullion": 4, "safe haven": 3, "safe-haven": 3,
    "fed": 3, "fomc": 4, "powell": 3, "federal reserve": 3,
    "rate cut": 3, "rate hike": 3, "interest rate": 2, "monetary policy": 2,
    "inflation": 3, "cpi": 4, "pce": 4, "ppi": 3,
    "payroll": 4, "nonfarm": 4, "jobs report": 4, "unemployment": 2, "jobless": 2,
    "treasury": 2, "yield": 2, "dollar": 2, "dxy": 3,
    "central bank": 2, "ecb": 2, "boj": 2, "pboc": 3, "bank of england": 2,
    "tariff": 2, "sanction": 2, "war": 2, "ceasefire": 2, "iran": 2,
    "hormuz": 3, "israel": 1, "ukraine": 1, "russia": 1, "china": 1,
    "oil": 1, "recession": 2, "gdp": 2, "debt ceiling": 2, "shutdown": 2,
}


def clean(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def as_list(v):
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    return [p.strip() for p in str(v).split("\n") if p.strip()]


def set_output(posted):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"posted={'true' if posted else 'false'}\n")


def load_history():
    try:
        with open(HISTORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_history(history, entry):
    history.append(entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history[-80:], f, ensure_ascii=False, indent=2)


def score(text):
    t = text.lower()
    total = 0
    for word, weight in KEYWORDS.items():
        if re.search(r"\b" + re.escape(word) + r"s?\b", t):
            total += weight
    return total


def is_fresh(entry):
    t = entry.get("published_parsed") or entry.get("updated_parsed")
    if not t:
        return True
    return (time.time() - calendar.timegm(t)) < MAX_AGE_HOURS * 3600


def get_items(history):
    posted = {h.get("link") for h in history if h.get("link")}
    items = []
    seen = set()
    for url in FEEDS:
        try:
            feed = feedparser.parse(url, agent=USER_AGENT)
        except Exception as e:
            print(f"{url} -> failed: {e}")
            continue
        print(f"{url} -> {len(feed.entries)} items")
        source = clean(feed.feed.get("title", "")) or url.split("/")[2]
        for e in feed.entries[:15]:
            title = clean(e.get("title"))
            link = e.get("link", "")
            if not title or title.lower() in seen or link in posted or not is_fresh(e):
                continue
            seen.add(title.lower())
            summary = clean(e.get("summary"))[:500]
            items.append(
                {
                    "title": title,
                    "summary": summary,
                    "link": link,
                    "source": source,
                    "score": score(title + " " + summary),
                }
            )
    items = [i for i in items if i["score"] > 0]
    items.sort(key=lambda i: i["score"], reverse=True)
    return items[:25]


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

    recent = "\n".join(
        f"- {h['headline']} | image: {h['image_subject']}" for h in history[-12:]
    ) or "- (none yet)"
    listing = "\n".join(
        f"[{i}] (relevance {it['score']}) {it['title']} -- {it['summary']} ({it['source']})"
        for i, it in enumerate(items)
    )
    prompt = (
        "You are the editor of THE MARKET CODE by E11 Lab. Your audience is "
        "gold traders who trade XAU/USD. Your job is to make them better "
        "informed, not to give signals.\n"
        "Below are fresh news items from public feeds, each with an index, a "
        "keyword relevance score, a title and a short summary.\n"
        "Pick the ONE item with the biggest likely impact on gold (XAU/USD) "
        "right now. Strong drivers are: US economic data and Fed policy, "
        "inflation, the US dollar and Treasury yields, other central bank policy "
        "and central bank gold buying, geopolitical or safe-haven events, and "
        "gold-specific news. Ignore items with little link to gold. It must NOT "
        "be similar to the recently posted ones. If nothing matters for gold, "
        "set impact_score to 1.\n"
        "Write ORIGINAL commentary in " + LANG + ". Use ONLY facts found in the "
        "chosen item's title and summary. Do not invent numbers, quotes, dates, "
        "events or price levels. Never copy sentences from the source.\n"
        "The article must cover: (1) what happened, facts only; (2) the "
        "transmission channel to gold, such as the US dollar, real yields and "
        "rate expectations, safe-haven demand, inflation hedging or central bank "
        "demand; (3) a balanced if/then view of what would typically support "
        "gold and what would pressure it; (4) what traders should watch next. "
        "Educational only: never say buy or sell, never give entries, stops or "
        "price targets, and never present a prediction as certain. Calm, "
        "professional tone.\n"
        "Return ONLY JSON with these keys:\n"
        "headline: max 10 words, news style;\n"
        "teaser: 2 short sentences, max 260 characters; the second sentence "
        "says why it matters for gold;\n"
        "article: a list of 4 to 6 paragraphs (about 250 to 400 words in total);\n"
        "takeaways: a list of exactly 3 short bullet points;\n"
        "gold_impact: one of bullish, bearish, mixed, neutral (the likely effect "
        "on gold);\n"
        "impact_score: integer from 1 to 10 (how strongly this is likely to "
        "move gold);\n"
        "image_subject: ONE scene description (max 35 words) for a collage "
        "illustration with these elements: plain gold bars with blank unmarked "
        "surfaces, the main subject of the story (for example the Federal "
        "Reserve building, a country map, an oil rig, dollar banknotes, a "
        "factory), and ONE arrow showing the likely effect on gold: pointing up "
        "if bullish, down if bearish, sideways if mixed or neutral. Do not "
        "mention colours. Make the main subject look clearly different from the "
        "recent images listed below. No text, numbers or people;\n"
        "source_index: the integer index of the chosen item.\n\n"
        "RECENTLY POSTED (avoid repeating):\n" + recent + "\n\n"
        "FRESH ITEMS:\n" + listing
    )
    data = call_gemini(key, prompt)
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)


def main():
    if not webpage.SITE_URL:
        raise RuntimeError("SITE_URL is not set")

    history = load_history()
    today = datetime.date.today().isoformat()

    posts_today = sum(1 for h in history if h.get("date") == today)
    if posts_today >= MAX_POSTS:
        print(f"Daily limit reached ({posts_today}/{MAX_POSTS}). Skipping.")
        set_output(False)
        return

    items = get_items(history)
    if not items:
        print("No fresh gold-relevant items found. Skipping.")
        set_output(False)
        return

    post = ask_gemini(items, history)

    try:
        impact_score = int(post.get("impact_score", 0))
    except Exception:
        impact_score = 0
    if impact_score < MIN_IMPACT:
        print(
            f"Skipped: impact score {impact_score} is below {MIN_IMPACT} "
            f"({post.get('headline')})"
        )
        set_output(False)
        return

    try:
        idx = int(post.get("source_index", 0))
    except Exception:
        idx = 0
    if not 0 <= idx < len(items):
        idx = 0
    src = items[idx]

    impact = str(post.get("gold_impact", "mixed")).strip().lower()
    if impact not in ("bullish", "bearish", "mixed", "neutral"):
        impact = "mixed"

    print("Gemini chose:", post["headline"], "| source:", src["source"])
    print("Gold impact:", impact, "| score:", impact_score)
    print("Scene:", post["image_subject"])

    img, provider = generate_image(post["image_subject"])

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
        "impact": impact,
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
            "link": src["link"],
        },
    )
    set_output(True)
    print(f"Article built (image via {provider}):", last["url"])


main()
