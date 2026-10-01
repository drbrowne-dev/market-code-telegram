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


def bi(en, km, tag="span", cls=""):
    en = str(en)
    km = str(km).strip() if km else en
    extra = (" " + cls) if cls else ""
    return (
        f'<{tag} class="en{extra}" lang="en">{esc(en)}</{tag}>'
        f'<{tag} class="km{extra}" lang="km">{esc(km)}</{tag}>'
    )


UI = {
    "all_news": ("← All news", "← ព័ត៌មានទាំងអស់"),
    "takeaways": ("Key takeaways", "ចំណុចសំខាន់ៗ"),
    "source": ("Source", "ប្រភព"),
    "impact": ("XAU/USD impact", "ផលប៉ះពាល់លើ XAU/USD"),
    "footer": (
        "© E11 Lab · Educational content only. Not financial advice.",
        "© E11 Lab · មាតិកាអប់រំប៉ុណ្ណោះ មិនមែនជាដំបូន្មានហិរញ្ញវត្ថុទេ។",
    ),
    "news": ("Market News", "ព័ត៌មានទីផ្សារ"),
    "lead": (
        "Daily market news and insight for gold traders from E11 Lab.",
        "ព័ត៌មានទីផ្សារប្រចាំថ្ងៃ និងការវិភាគសម្រាប់អ្នកជួញដូរមាស ពី E11 Lab។",
    ),
}

IMPACT_LABELS = {
    "bullish": ("▲ Bullish", "▲ វិជ្ជមាន"),
    "bearish": ("▼ Bearish", "▼ អវិជ្ជមាន"),
    "mixed": ("◆ Mixed", "◆ ចម្រុះ"),
    "neutral": ("● Neutral", "● អព្យាក្រឹត"),
}

CSS = """
:root{--bg:#0a0e13;--card:#111821;--line:#1c2733;--text:#e6edf3;--muted:#8b98a5;--cyan:#22d3ee;--green:#34d399}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;line-height:1.7}
a{color:var(--cyan);text-decoration:none}
a:hover{text-decoration:underline}
html[data-lang="en"] .km{display:none}
html[data-lang="km"] .en{display:none}
.km{font-family:"Noto Sans Khmer",system-ui,sans-serif}
p.km,li.km{line-height:1.95}
header{padding:14px 20px;border-bottom:1px solid var(--line)}
.top{display:flex;justify-content:space-between;align-items:center;gap:12px}
.brand{font-weight:800;letter-spacing:.12em;font-size:14px;color:var(--text)}
.brand span{color:var(--green)}
.lang button{background:transparent;color:var(--text);border:1px solid var(--line);padding:5px 12px;border-radius:8px;cursor:pointer;font-size:14px;font-family:inherit}
html[data-lang="en"] .b-en,html[data-lang="km"] .b-km{background:var(--cyan);color:#06222a;border-color:var(--cyan)}
main{max-width:880px;margin:0 auto;padding:26px 18px 60px}
h1{font-size:30px;line-height:1.3;margin:8px 0 18px}
.meta{color:var(--muted);font-size:14px;margin:0}
.badge{display:inline-block;background:var(--card);border:1px solid var(--green);color:var(--green);padding:3px 12px;border-radius:999px;font-size:14px;margin:6px 0 12px}
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
.card h2{font-size:17px;line-height:1.35;margin:6px 0}
.card p{margin:0;color:var(--muted);font-size:14px}
footer{text-align:center;color:var(--muted);font-size:13px;padding:30px 18px}
"""

LANG_JS = """
(function(){
  var l='en';
  try{
    var p=new URLSearchParams(location.search).get('lang');
    var s=localStorage.getItem('lang');
    var n=(navigator.language||'').toLowerCase().indexOf('km')===0?'km':'en';
    l=p||s||n;
  }catch(e){}
  if(l!=='km'){l='en';}
  document.documentElement.setAttribute('data-lang',l);
  try{localStorage.setItem('lang',l);}catch(e){}
})();
function setLang(l){
  document.documentElement.setAttribute('data-lang',l);
  try{localStorage.setItem('lang',l);}catch(e){}
}
"""


def page(title, body, root, desc="", image=""):
    og = ""
    if image:
        og = (
            f'<meta property="og:image" content="{esc(image)}">'
            '<meta name="twitter:card" content="summary_large_image">'
        )
    return (
        '<!doctype html><html lang="en" data-lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{esc(title)}</title>"
        f'<meta name="description" content="{esc(desc)}">'
        f'<meta property="og:title" content="{esc(title)}">'
        f'<meta property="og:description" content="{esc(desc)}">'
        f"{og}"
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Khmer:wght@400;600;700&display=swap" rel="stylesheet">'
        f"<script>{LANG_JS}</script>"
        f"<style>{CSS}</style></head><body>"
        f'<header><div class="top"><a class="brand" href="{root}index.html">E11 LAB <span>× THE MARKET CODE</span></a>'
        '<div class="lang"><button class="b-en" onclick="setLang(\'en\')">EN</button>'
        '<button class="b-km" onclick="setLang(\'km\')">ខ្មែរ</button></div></div></header>'
        f"<main>{body}</main>"
        f"<footer>{bi(*UI['footer'])}</footer></body></html>"
    )


def render_article(a, p_en, t_en, p_km, t_km):
    paras = "".join(
        bi(p, p_km[i] if i < len(p_km) else p, "p") for i, p in enumerate(p_en)
    )
    lis = "".join(
        bi(t, t_km[i] if i < len(t_km) else t, "li") for i, t in enumerate(t_en)
    )
    impact_en, impact_km = IMPACT_LABELS.get(a.get("impact", ""), ("", ""))
    badge = ""
    if impact_en:
        badge = (
            '<p><span class="badge">'
            + bi(f"{UI['impact'][0]}: {impact_en}", f"{UI['impact'][1]}: {impact_km}")
            + "</span></p>"
        )
    src = (
        f'<a href="{esc(a["source_url"])}" rel="noopener" target="_blank">'
        f'{esc(a["source_name"])}</a>'
    )
    note = bi(
        f"Original commentary by THE MARKET CODE, based on public reporting from "
        f"{a['source_name']}. Educational only, not financial advice.",
        f"មតិវិភាគដើមដោយ THE MARKET CODE ផ្អែកលើការរាយការណ៍សាធារណៈពី "
        f"{a['source_name']}។ មាតិកាអប់រំប៉ុណ្ណោះ មិនមែនជាដំបូន្មានហិរញ្ញវត្ថុទេ។",
        "p",
        "note",
    )
    body = (
        "<article>"
        f'<p class="meta">{esc(a["date"])} · {bi(*UI["source"])}: {src}</p>'
        f'<h1>{bi(a["headline"], a.get("headline_km", ""))}</h1>'
        f"{badge}"
        f'<img class="cover" src="{esc(a["slug"])}.jpg" alt="">'
        f'{bi(a["teaser"], a.get("teaser_km", ""), "p", "lead")}'
        f"{paras}"
        f'<div class="box"><h3>{bi(*UI["takeaways"])}</h3><ul>{lis}</ul></div>'
        f"{note}"
        f'<p><a href="../index.html">{bi(*UI["all_news"])}</a></p>'
        "</article>"
    )
    image = f'{SITE_URL}/news/{a["slug"]}.jpg' if SITE_URL else ""
    return page(a["headline"] + " | E11 Lab", body, "../", a["teaser"], image)


def render_index(articles):
    cards = "".join(
        f'<a class="card" href="news/{esc(a["slug"])}.html">'
        f'<img src="news/{esc(a["slug"])}.jpg" alt="" loading="lazy">'
        f'<div class="txt"><span class="meta">{esc(a["date"])}</span>'
        f'<h2>{bi(a["headline"], a.get("headline_km", ""))}</h2>'
        f'{bi(a["teaser"], a.get("teaser_km", ""), "p")}</div></a>'
        for a in articles[:60]
    )
    body = (
        f'<h1>{bi(*UI["news"])}</h1>'
        f'{bi(*UI["lead"], "p", "lead")}'
        f'<div class="grid">{cards}</div>'
    )
    return page(
        "Market News | E11 Lab × THE MARKET CODE", body, "", "Daily market news and insight."
    )


def load_articles(docs):
    try:
        with open(os.path.join(docs, "articles.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_articles(docs, articles):
    with open(os.path.join(docs, "articles.json"), "w", encoding="utf-8") as f:
        json.dump(articles[:200], f, ensure_ascii=False, indent=2)


def write_site(docs, a, p_en, t_en, p_km, t_km, articles):
    os.makedirs(os.path.join(docs, "news"), exist_ok=True)
    with open(os.path.join(docs, "news", a["slug"] + ".html"), "w", encoding="utf-8") as f:
        f.write(render_article(a, p_en, t_en, p_km, t_km))
    with open(os.path.join(docs, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_index(articles))
    open(os.path.join(docs, ".nojekyll"), "a").close()
