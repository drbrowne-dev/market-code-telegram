import webpage

DOCS = "../docs"

if not webpage.SITE_URL:
    raise RuntimeError("SITE_URL is not set")

articles = webpage.load_articles(DOCS)
webpage.write_static(DOCS, articles)
print("Rebuilt the site with", len(articles), "articles")
