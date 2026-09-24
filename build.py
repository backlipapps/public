#!/usr/bin/env python3
"""Generate the static GitHub Pages site for the Backlip app catalog.

    python3 build.py [BASE_URL]

BASE_URL defaults to https://backlipapps.github.io/public/ — re-run with the new
base after renaming the repository. Sources: README.md (the catalog table) and
the embedded copy below, kept at listing/evidence level per the catalog rules:
no pricing, ratings, or review counts anywhere; install links point to platform
marketplaces only. Idempotent: safe to re-run any time.
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://backlipapps.github.io/public/").rstrip("/") + "/"

CSS = """
:root{--ink:#111827;--mut:#6b7280;--line:#e5e7eb;--brand:#0a58ca}
*{box-sizing:border-box}body{margin:0;font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink);background:#fff}
.wrap{max-width:960px;margin:0 auto;padding:24px 20px 64px}
header h1{margin:0;font-size:28px}header .tag{color:var(--mut);font-size:18px;margin:4px 0 12px}
nav{display:flex;flex-wrap:wrap;gap:14px;margin:14px 0;padding:10px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
nav a{color:var(--brand);text-decoration:none}nav a:hover{text-decoration:underline}
.note{background:#f8fafc;border:1px solid var(--line);border-radius:8px;padding:10px 14px;font-size:14px;color:var(--mut)}
h2{font-size:20px;margin:28px 0 10px}
table{border-collapse:collapse;width:100%;font-size:14.5px;display:block;overflow-x:auto}
th,td{text-align:left;border-bottom:1px solid var(--line);padding:8px 10px;vertical-align:top}
thead th{font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:var(--mut)}
tbody th{font-weight:600;white-space:nowrap}
td.links a,.plist a{margin-right:8px;white-space:nowrap}
ul{padding-left:20px}li{margin:6px 0}
footer{margin-top:40px;padding-top:14px;border-top:1px solid var(--line);color:var(--mut);font-size:14px}
a{color:var(--brand)}.crumb{color:var(--mut);font-size:14px;margin:0 0 6px}
"""

NAV = [("backlip.com", "https://backlip.com"), ("Catalog", "https://backlip.com/product/"),
       ("Solutions", "https://backlip.com/solutions/"), ("Free tools", "https://backlip.com/tools/"),
       ("llms.txt", "https://backlip.com/llms.txt")]

APPS = {
 "bl-scrolling-announcement-bar": {
  "row": "BL Scrolling Announcement Bar", "expect_mkt": 5,
  "title": "BL Scrolling Announcement Bar — announcement bar app for Shopify, Wix, Ecwid, BigCommerce & Shoper",
  "meta": "Keep timely store messages visible — free-shipping thresholds, promo codes, delivery updates — without a theme-development task. Native versions for Shopify, Wix, Ecwid, BigCommerce, and the Shoper Appstore.",
  "intro": "The easiest way to keep timely store messages visible — a free-shipping threshold, a promo code, a delivery update — without a theme-development task. Native versions for Shopify, Wix, Ecwid, BigCommerce, and the Shoper Appstore (PL).",
  "capabilities": "Add multiple messages and manage them in one admin panel. Link each message to any page, category, or product. Control colours, gradient or solid backgrounds, fonts and font size, bar height, animation direction, speed, and spacing — or switch the animation off for a static bar. Live preview and pause-on-hover where the platform build supports them.",
  "boundary": "A marketplace link proves a public install destination for that platform — not identical cross-platform features. Each listing shows what that build supports.",
  "links": [("Announcement Bar Message Generator (free tool)", "https://backlip.com/tools/announcement-bar-message-generator/"),
            ("Solution hub", "https://backlip.com/solutions/scrolling-announcement-bar/"),
            ("Shopify announcement bar vs native", "https://backlip.com/solutions/shopify-announcement-bar-vs-native/"),
            ("Wix announcement bar vs native", "https://backlip.com/solutions/wix-announcement-bar-vs-native/")],
 },
 "bl-bulk-product-image-uploader": {
  "row": "BL Bulk Product Image Uploader", "expect_mkt": 4,
  "title": "BL Bulk Product Image Uploader — batch product image upload by SKU, ID, or handle",
  "meta": "Batch product photos matched to products by SKU, product ID, or handle — the native-marketplace alternative to CSV image imports. Shopify, Wix, WooCommerce, and Shopware.",
  "intro": "The native-marketplace alternative to spreadsheet-and-CSV image imports, for merchants who add products in batches. Native versions for Shopify, Wix, WooCommerce, and Shopware.",
  "capabilities": "Matches files to products by SKU, product ID, or handle — name files like TSHIRT-RED.1.jpg, review every match, then add images or carefully overwrite. Supported intake in the audited builds: JPEG, PNG, GIF, and WebP.",
  "boundary": "Treat overwrite as a controlled operation and test it on a small batch first. Platform-specific matching, overwrite, and gallery behavior varies — each listing shows what that build supports.",
  "links": [("Shopify bulk images: native CSV vs app", "https://backlip.com/solutions/shopify-bulk-images-native-csv-vs-app/")],
 },
}
import csv

APPS["bl-country-blocker"] = {
 "row": "BL Country Blocker", "expect_mkt": 2,
 "title": "BL Country Blocker — block or redirect visitors by country (Shopify & Wix)",
 "meta": "Simple storefront country rules: block some countries, redirect others to the right store, allow the rest. Native versions for Shopify and Wix.",
 "intro": "Simple country rules for storefront access: block some countries, redirect others to the right store, allow the rest. Native versions for Shopify and Wix.",
 "capabilities": "A practical access rule per country with a custom no-access message, block and redirect allowlists, and rules that are easy to review and reverse.",
 "boundary": "The visitor's country is resolved by IP. No claim of perfect accuracy, legal compliance, or bot prevention — a practical storefront rule, not legal advice or a firewall.",
 "links": [],
}
APPS["bl-external-links-button"] = {
 "row": "BL External Links Button", "expect_mkt": 1,
 "title": "BL External Links Button — external-link buttons for Shopify product pages",
 "meta": "External-link buttons for Shopify product pages: affiliate offers, dropshipping suppliers, marketplace listings, warranty pages. Fixed or per-product, with CSV bulk management.",
 "intro": "External-link buttons for Shopify product pages — for merchants who send buyers elsewhere: affiliate offers, dropshipping suppliers, marketplace listings, warranty or registration pages. Installed natively from the Shopify App Store.",
 "capabilities": "Fixed (one shared destination across the catalog) or product-specific (up to five label/URL pairs in the audited build), each opening in a new tab when configured. Bulk management through CSV import/export; setup uses the theme editor's Online Store 2.0 app blocks.",
 "boundary": "The button sends visitors to an external URL. It does not add an off-site item to Shopify's cart, process external checkout, confirm stock, or represent the external seller's pricing, delivery, return, or support policies.",
 "links": [],
}
APPS["bl-logo-showcase"] = {
 "row": "BL Logo Showcase", "expect_mkt": 2,
 "title": "BL Logo Showcase — scrolling logo carousel for Shopify & Wix",
 "meta": "A scrolling logo carousel for the storefront trust strip: client logos, partner brands, press mentions, or trust badges. Native versions for Shopify and Wix.",
 "intro": "A scrolling logo carousel for the storefront trust strip — client logos, partner brands, press mentions, or trust badges. Native versions for Shopify and Wix.",
 "capabilities": "On Shopify: layout, speed, and style controls, responsive presentation, direction left/right or none, pause-on-hover, and a standalone full-width option — up to seven logo images per section in the audited build. On Wix: continuous scrolling with adjustable speed, direction, logo size, and spacing.",
 "boundary": "A visual presentation tool. It does not verify logo ownership, approve usage rights, or create endorsements.",
 "links": [],
}

ORG_JSONLD = {"@context": "https://schema.org", "@type": "Organization", "name": "Backlip",
              "url": "https://backlip.com", "email": "backlipapps@gmail.com",
              "sameAs": ["https://github.com/backlipapps"]}

def shell(title, desc, jsonld, body, h1="Backlip", tag="Small, native ecommerce apps — one merchant job per app."):
    nav = " ".join(f'<a href="{u}">{t}</a>' for t, u in NAV)
    tagline = f'\n  <p class="tag">{html.escape(tag)}</p>' if tag else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>{html.escape(h1)}</h1>{tagline}
  <p>Install and billing always happen on your platform's own marketplace; pricing, plans, badges, and reviews live on each listing.</p>
  <nav>{nav}</nav>
</header>
<main>
{body}
</main>
<footer>
  Maintained by <a href="https://github.com/backlipapps">Backlip on GitHub</a> ·
  <a href="https://github.com/backlipapps/public">view source</a> · © 2026 Backlip
</footer>
</div>
</body>
</html>"""

def md_links(cell):
    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', html.escape(cell))

def parse_table():
    rows = []
    for line in open(os.path.join(HERE, "README.md"), encoding="utf-8"):
        if line.startswith("| BL") or line.startswith("| Default"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) == 3:
                rows.append(cells)
    return rows

def app_page(slug, meta, row, product_page):
    jsonld = {"@context": "https://schema.org", "@type": "SoftwareApplication",
              "name": meta["row"], "applicationCategory": "BusinessApplication",
              "description": meta["meta"],
              "author": {"@type": "Organization", "name": "Backlip", "url": "https://backlip.com"},
              "url": product_page}
    extra = "".join(f'\n    <li><a href="{u}">{html.escape(t)}</a></li>' for t, u in meta["links"])
    body = f"""<p class="crumb"><a href="{BASE}">Catalog</a> &#8250; {html.escape(meta["row"])}</p>
<p>{html.escape(meta["intro"])}</p>
<p>{html.escape(meta["capabilities"])}</p>
<p class="note">{html.escape(meta["boundary"])}</p>
<h2>Install</h2>
<p class="plist">{md_links(row[2])}</p>
<h2>Learn more</h2>
<ul>
    <li><a href="{product_page}">Product page</a></li>{extra}
</ul>"""
    return shell(meta["title"], meta["meta"], jsonld, body, h1=meta["row"], tag=None)

def index_body(rows, app_list):
    trs = "\n".join(f'        <tr><th scope="row">{html.escape(a)}</th><td>{html.escape(j)}</td><td class="links">{md_links(l)}</td></tr>' for a, j, l in rows)
    apps_ul = "\n".join(f'    <li><a href="apps/{s}.html">{html.escape(m["row"])}</a> — {html.escape(m["meta"])}</li>' for s, m in app_list)
    return f"""<p class="note">A marketplace link proves a public install destination for that platform — not identical cross-platform features. Each listing shows what that build supports.</p>
<h2>Catalog — 27 apps &amp; integrations, 11 platforms</h2>
<table>
<thead><tr><th>App</th><th>The one job</th><th>Install (platform marketplace)</th></tr></thead>
<tbody>
{trs}
</tbody>
</table>
<h2>App pages</h2>
<ul>
{apps_ul}
</ul>
<h2>Free tools</h2>
<p>Client-side, free to use, no account:</p>
<ul>
<li><a href="https://backlip.com/tools/announcement-bar-message-generator/">Announcement Bar Message Generator</a> — write bar copy with a live scrolling preview, presets, and per-platform install links.</li>
<li><a href="https://backlip.com/tools/size-chart-generator/">Size Chart Generator</a> — build a copy-pasteable size-chart table with live preview and cm/inch conversion.</li>
</ul>
<h2>Machine-readable</h2>
<ul>
<li><a href="apps.csv">apps.csv</a> — every product &times; platform install destination, one row each.</li>
<li><a href="llms.txt">llms.txt</a> (this site) and <a href="https://backlip.com/llms.txt">llms.txt</a> / <a href="https://backlip.com/llms-full.txt">llms-full.txt</a> for backlip.com.</li>
</ul>
<h2>Support</h2>
<p><a href="mailto:backlipapps@gmail.com">backlipapps@gmail.com</a></p>"""

def main():
    import datetime
    rows = parse_table()
    errors = []
    if len(rows) != 27:
        errors.append(f"table rows = {len(rows)}, expected 27")
    pages = {}
    with open(os.path.join(HERE, "apps.csv"), encoding="utf-8") as f:
        for r in csv.reader(f):
            if r and r[0] != "product":
                pages.setdefault(r[0], r[1])
    os.makedirs(os.path.join(HERE, "apps"), exist_ok=True)
    app_list = []
    domains = ("apps.shopify.com", "www.wix.com", "www.ecwid.com", "www.bigcommerce.com", "woocommerce.com", "store.shopware.com", "www.shoper.pl")
    for slug, meta in APPS.items():
        row = next((r for r in rows if r[0] == meta["row"]), None)
        pp = next((p for prod, p in pages.items() if prod.startswith(meta["row"])), "")
        if row is None or not pp:
            errors.append(f"{slug}: no README row or product page")
            continue
        page = app_page(slug, meta, row, pp)
        mkt = sum(page.count(d) for d in domains)
        if mkt != meta["expect_mkt"]:
            errors.append(f"{slug}: {mkt} marketplace anchors, expected {meta['expect_mkt']}")
        if page.count("<h1>") != 1 or "rel=" in page or 'href="https://backlip.com' not in page:
            errors.append(f"{slug}: structure check failed")
        open(os.path.join(HERE, "apps", slug + ".html"), "w", encoding="utf-8").write(page)
        app_list.append((slug, meta))
    desc = "Catalog of 27 Backlip apps and integrations across 11 platform marketplaces — Shopify, Wix, Ecwid, BigCommerce, WooCommerce, Shopware, Nuvemshop, Cafe24, the Shop app, Atlassian, and the Shoper Appstore. Install from your platform's marketplace."
    idx = shell("Backlip — small, native ecommerce apps, one job each", desc, ORG_JSONLD, index_body(rows, app_list))
    if "rel=" in idx or idx.count("<h1>") != 1:
        errors.append("index: structure check failed")
    open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(idx)
    today = datetime.date.today().isoformat()
    urls = [BASE] + [BASE + "apps/" + s + ".html" for s, _ in app_list]
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"<url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls) + "</urlset>\n"
    open(os.path.join(HERE, "sitemap.xml"), "w", encoding="utf-8").write(sitemap)
    open(os.path.join(HERE, "robots.txt"), "w", encoding="utf-8").write(f"User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n")
    llms = "# Backlip app catalog\n\n> Small, native ecommerce apps — one merchant job per app. Install from your platform's marketplace; pricing, plans, badges, and reviews live on each listing.\n\n"
    llms += f"- [Catalog — all 27 apps and integrations]({BASE}): the full product &times; platform table with marketplace install links.\n"
    for s, m in app_list:
        llms += f"- [{m['row']}]({BASE}apps/{s}.html): {m['meta']}\n"
    llms += f"- [apps.csv]({BASE}apps.csv): machine-readable catalog — 50 install destinations.\n\nPrimary source: https://backlip.com\n"
    open(os.path.join(HERE, "llms.txt"), "w", encoding="utf-8").write(llms)
    print(f"built: index.html ({len(idx)}B), {len(app_list)} app pages, sitemap ({len(urls)} urls), robots.txt, llms.txt · BASE={BASE}")
    if errors:
        print("ERRORS:", *errors, sep="\n  ")
        sys.exit(1)
    print("validation: PASS")

if __name__ == "__main__":
    main()
