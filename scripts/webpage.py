import os
import re
import json
import html

SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")


def esc(s):
    return html.escape(str(s), quote=True)


def slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:70].strip("-") or "story"


CSS = """
:root{--bg:#0a0e13;--card:#111821;--line:#1c2733;--text:#e6edf3;--muted:#8b98a5;--cyan:#22d3ee;--green:#34d399}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;line-height:1.7}
a{color:var(--cyan);text-decoration:none}
a:hover{text-decoration:underline}
header{padding:16px 20px;border-bottom:1px solid var(--line)}
.brand{font-weight:800;letter-spacing:.12em;font-size:14px;color:var(--text)}
.brand span{color:var(--green)}
main{max-width:880px;margin:0 auto;padding:26px 18px 60px}
h1{font-size:30px;line-height:1.25;margin:8px 0 18px}
.meta{color:var(--muted);font-size:14px;margin:0}
.cover{width:100%;border-radius:12px;border:1px solid var(--line);margin:8px 0 20px}
.lead{font-size:19px;color:#cfe9ee;border-left:3px solid var(--green);padding-left:14px}
.box{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:6px 20px 10px;margin:26px 0}
.box h3{color:var(--green);margin:14px 0 6px}
.note{color:var(--muted);font-size:13px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:18px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;color:var(--text)}
.card:hover{border-color:var(--cyan);text-decoration:none}
.card img{width:100%;display:block;aspect-ratio:16/10;object-fit:cover}
.card .txt{padding:12px 14px 16px}
.card h2{font-size:17px;line-height:1.3;margin:6px 0}
.card p{margin:0;color:var(--muted);font-size:14px}
footer{text-align:center;color:var(--muted);font-size:13px;padding:30px 18px}
"""


def page(title, body, root, desc="", image=""):
    og = ""
    if image:
        og = (
            f'<meta property="og:image" content="{esc(image)}">'
            '<meta name="twitter:card" content="summary_large_image">'
        )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{esc(title)}</title>"
        f'<meta name="description" content="{esc(desc)}">'
        f'<meta property="og:title" content="{esc(title)}">'
        f'<meta property="og:description" content="{esc(desc)}">'
        f"{og}<style>{CSS}</style></head><body>"
        f'<header><a class="brand" href="{root}index.html">E11 LAB <span>× THE MARKET CODE</span></a></header>'
        f"<main>{body}</main>"
        "<footer>© E11 Lab · Educational content only. Not financial advice.</footer>"
        "</body></html>"
    )


def render_article(a, paragraphs, takeaways):
    paras = "".join(f"<p>{esc(p)}</p>" for p in paragraphs)
    lis = "".join(f"<li>{esc(t)}</li>" for t in takeaways)
    body = (
        "<article>"
        f'<p class="meta">{esc(a["date"])} · Source: '
        f'<a href="{esc(a["source_url"])}" rel="noopener" target="_blank">{esc(a["source_name"])}</a></p>'
        f'<h1>{esc(a["headline"])}</h1>'
        f'<img class="cover" src="{esc(a["slug"])}.jpg" alt="">'
        f'<p class="lead">{esc(a["teaser"])}</p>'
        f"{paras}"
        f'<div class="box"><h3>Key takeaways</h3><ul>{lis}</ul></div>'
        f'<p class="note">Original commentary by THE MARKET CODE, based on public reporting from '
        f'{esc(a["source_name"])}. Educational only, not financial advice.</p>'
        '<p><a href="../index.html">← All news</a></p>'
        "</article>"
    )
    image = f'{SITE_URL}/news/{a["slug"]}.jpg' if SITE_URL else ""
    return page(a["headline"] + " | E11 Lab", body, "../", a["teaser"], image)


def render_index(articles):
    cards = "".join(
        f'<a class="card" href="news/{esc(a["slug"])}.html">'
        f'<img src="news/{esc(a["slug"])}.jpg" alt="" loading="lazy">'
        f'<div class="txt"><span class="meta">{esc(a["date"])}</span>'
        f'<h2>{esc(a["headline"])}</h2><p>{esc(a["teaser"])}</p></div></a>'
        for a in articles[:60]
    )
    body = (
        "<h1>Market News</h1>"
        '<p class="lead">Daily market stories and trading-psychology insight from E11 Lab.</p>'
        f'<div class="grid">{cards}</div>'
    )
    return page("Market News | E11 Lab × THE MARKET CODE", body, "", "Daily market news and insight.")


def load_articles(docs):
    try:
        with open(os.path.join(docs, "articles.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_articles(docs, articles):
    with open(os.path.join(docs, "articles.json"), "w", encoding="utf-8") as f:
        json.dump(articles[:200], f, ensure_ascii=False, indent=2)


def write_site(docs, a, paragraphs, takeaways, articles):
    os.makedirs(os.path.join(docs, "news"), exist_ok=True)
    with open(os.path.join(docs, "news", a["slug"] + ".html"), "w", encoding="utf-8") as f:
        f.write(render_article(a, paragraphs, takeaways))
    with open(os.path.join(docs, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_index(articles))
    open(os.path.join(docs, ".nojekyll"), "a").close()
