#!/usr/bin/env python3
"""Build the Imported Bites static site from data + shared templates.

Catalog: data/products.json holds the confirmed 20-product list (owner edits
prices there; re-run to regenerate). Categories, product pages, shop filters,
blog and schema are all generated from that single source of truth.
Store policy: free delivery across Karachi on orders of Rs 3,000+.
"""
import json, os, re, html, sys

ROOT = os.path.expanduser("~/workspace/importedbites")
SITE = os.path.join(ROOT, "site")
DATA = os.path.join(ROOT, "data", "products.json")
IMG_DIR = os.path.join(SITE, "assets", "img")
BASE = "https://importedbites.com"

sys.path.insert(0, DATA.replace("products.json", ""))
from content import CAT_META, CAT_COPY, BLOGS

# Real business WhatsApp (owner supplied 2026-10-31). Display format and wa.me format.
WA_DISPLAY = "0337 3698048"
WA_NUMBER = "923373698048"

with open(DATA, encoding="utf-8") as f:
    CATALOG = json.load(f)
PRODUCTS = CATALOG.get("products", [])
BY_SLUG = {p["slug"]: p for p in PRODUCTS}

# Category tiles on the home page and full category pages (7 categories).
TILE_CATS = [
    ("cat-dry-food", "Cat Dry Food", "🐱", "products/whiskas-adult-chicken-1-9kg.jpg"),
    ("cat-wet-food", "Cat Wet Food", "🥫", "products/whiskas-pouch-beef-poultry-85g.png"),
    ("cat-treats", "Cat Treats", "🦴", "products/whiskas-temptations-chicken-45g.webp"),
    ("cat-litter", "Cat Litter", "🧹", "products/klumpy-cat-litter-5l.jpg"),
    ("coffee", "Coffee", "☕", "products/nescafe-gold.png"),
    ("stevia-sweeteners", "Stevia and Sweeteners", "🌿", "products/stevia-powder.png"),
    ("jellies-candy", "Jellies and Candy", "🍬", "products/haribo-goldbears-200g.jpg"),
]
CAT_NAME = {c[0]: c[1] for c in TILE_CATS}

CAT_LEAD = {
    "cat-dry-food": "Me-O and Whiskas dry food with Thailand origin authenticity, life-stage formulas and honest price per kg math.",
    "cat-wet-food": "Whiskas pouches in jelly and gravy, single serves and a 12 pack variety box for hydration and happy cats.",
    "cat-treats": "Crunchy Temptations and lickable creamy purees for training, bonding and winning over fussy cats.",
    "cat-litter": "Clumping bentonite litter in lavender, coffee and unscented options, in 5L trial and 10L value bags.",
    "coffee": "Imported instant coffee for a proper cup at home, with genuine sealed jars and printed expiry dates.",
    "stevia-sweeteners": "Plant derived stevia sweetener for cutting sugar, with honest guidance and no medical claims.",
    "jellies-candy": "Genuine imported gummies and candy with full ingredient transparency and resealable freshness.",
}

def img_exists(name):
    return os.path.exists(os.path.join(IMG_DIR, name))

def price(p):
    return "PKR {:,}".format(p["price"])

def esc(s):
    return html.escape(s, quote=True)

# ---------------- shared fragments ----------------

NAV = [
    ("Home", "/"),
    ("Shop", "/shop.html"),
    ("Blog", "/blog/"),
    ("FAQ", "/faq.html"),
    ("About", "/about.html"),
    ("Contact", "/contact.html"),
]

def header(active):
    links = "".join(
        '<a href="{}"{}>{}</a>'.format(url, ' class="active"' if name == active else "", name)
        for name, url in NAV)
    return """
<div class="announce"><a class="announce-sticker wa" href="https://wa.me/{wn}" target="_blank" rel="noopener">WhatsApp: {wa}</a><span class="announce-sticker">🚚 Cash on Delivery Nationwide</span><span class="announce-sticker alt">🎉 Free Delivery in Karachi on Orders Over Rs 3,000</span></div>
<header class="site">
  <div class="wrap header-inner">
    <a class="logo" href="/"><svg class="logo-mark" viewBox="0 0 64 64" aria-hidden="true"><polygon points="20,22 15,6 30,14" fill="#EA580C"/><polygon points="44,22 49,6 34,14" fill="#EA580C"/><path d="M16 24 h32 l-3.5 30 a5 5 0 0 1 -5 4.5 h-15 a5 5 0 0 1 -5 -4.5 z" fill="#EA580C"/><path d="M25 24 v-3 a7 7 0 0 1 14 0 v3" fill="none" stroke="#7C2D12" stroke-width="4" stroke-linecap="round"/><ellipse cx="29" cy="43" rx="8" ry="5" fill="#FFF7ED"/><polygon points="37,43 44,38 44,48" fill="#FFF7ED"/><circle cx="26" cy="42" r="1.3" fill="#7C2D12"/></svg><span class="logo-text">Imported<span>Bites</span><small>Cat Food and Imported Groceries</small></span></a>
    <form class="header-search" id="header-search" role="search" action="/shop.html" method="get">
      <input id="header-search-input" type="search" name="q" placeholder="Search imported products..." aria-label="Search products">
      <button type="submit">Search</button>
    </form>
    <button class="hamburger" id="hamburger" type="button" aria-label="Open menu">☰</button>
    <nav class="main-nav" id="main-nav" aria-label="Main navigation">{links}</nav>
    <button class="cart-btn" type="button" data-cart-open aria-label="Open cart">Cart<span class="cart-count" id="cart-count">0</span></button>
  </div>
</header>
""".format(links=links, wa=WA_DISPLAY, wn=WA_NUMBER)

def cart_drawer():
    return """
<div class="cart-overlay" id="cart-overlay"></div>
<aside class="cart-drawer" id="cart-drawer" aria-label="Shopping cart">
  <div class="cart-head">
    <h2>Your Cart</h2>
    <button class="cart-close" id="cart-close" type="button" aria-label="Close cart">×</button>
  </div>
  <div class="cart-scroll">
    <div class="cart-items" id="cart-items"></div>
    <div class="cart-foot" id="cart-foot">
    <div class="free-delivery-hint" id="free-delivery-hint" aria-live="polite"></div>
    <div class="cart-total"><span>Total</span><span id="cart-total">PKR 0</span></div>
    <button class="btn btn-cart" id="checkout-toggle" type="button">Checkout with Cash on Delivery</button>
    <form class="checkout-form" id="checkout-form" onsubmit="return false;">
      <label for="co-name">Full Name</label>
      <input id="co-name" type="text" autocomplete="name" placeholder="Your full name">
      <label for="co-phone">Phone Number</label>
      <input id="co-phone" type="tel" autocomplete="tel" placeholder="03xx xxxxxxx">
      <label for="co-address">Delivery Address</label>
      <textarea id="co-address" rows="2" autocomplete="street-address" placeholder="House, street, area"></textarea>
      <label for="co-city">City</label>
      <input id="co-city" type="text" autocomplete="address-level2" placeholder="City">
      <div class="cod-note">🎉 Free delivery across Karachi on orders of Rs 3,000 and above. Other cities: delivery fee confirmed on WhatsApp before dispatch.</div>
      <div class="cod-note">Payment method: Cash on Delivery. You pay in cash when your order arrives.</div>
      <button class="btn btn-wa" id="place-order-btn" type="button" style="margin-top:12px;">Place Order on WhatsApp</button>
    </form>
    </div>
  </div>
</aside>
"""

def footer():
    cats = "".join('      <a href="/{s}/">{n}</a>\n'.format(s=s, n=n) for s, n, e, i in TILE_CATS)
    return """
<footer class="site">
  <div class="wrap footer-inner">
    <div class="f-brand">
      <a class="f-logo" href="/" aria-label="Imported Bites home"><svg class="logo-mark" viewBox="0 0 64 64" aria-hidden="true"><polygon points="20,22 15,6 30,14" fill="#EA580C"/><polygon points="44,22 49,6 34,14" fill="#EA580C"/><path d="M16 24 h32 l-3.5 30 a5 5 0 0 1 -5 4.5 h-15 a5 5 0 0 1 -5 -4.5 z" fill="#EA580C"/><path d="M25 24 v-3 a7 7 0 0 1 14 0 v3" fill="none" stroke="#7C2D12" stroke-width="4" stroke-linecap="round"/><ellipse cx="29" cy="43" rx="8" ry="5" fill="#FFF7ED"/><polygon points="37,43 44,38 44,48" fill="#FFF7ED"/><circle cx="26" cy="42" r="1.3" fill="#7C2D12"/></svg><span class="logo-text">Imported<span>Bites</span><small>Cat Food and Imported Groceries</small></span></a>
      <p>Pakistan's online store for 100% genuine imported food: cat food, coffee, sweeteners, jellies and more, with cash on delivery nationwide.</p>
      <a class="f-wa" href="https://wa.me/{wn}" target="_blank" rel="noopener"><span class="f-wa-label">Order on WhatsApp</span><span class="f-wa-num">{wa}</span></a>
    </div>
    <div class="f-shop">
      <h4>Shop</h4>
      <div class="f-shop-links">
      <a href="/shop.html">All Products</a>
{cats}      </div>
    </div>
    <div class="f-col">
      <h4>Company</h4>
      <a href="/about.html">About Us</a>
      <a href="/contact.html">Contact</a>
      <a href="/blog/">Blog</a>
    </div>
    <div class="f-col">
      <h4>Support</h4>
      <a href="/faq.html">FAQ</a>
      <a href="/shipping-delivery.html">Shipping and Delivery</a>
      <a href="/returns-refunds.html">Returns and Refunds</a>
      <a href="/privacy.html">Privacy Policy</a>
      <a href="/terms.html">Terms of Service</a>
    </div>
  </div>
  <div class="wrap footer-trust" aria-label="Why shop with us">
    <span class="f-trust"><span aria-hidden="true">&#9989;</span>100% Genuine Imports</span>
    <span class="f-trust"><span aria-hidden="true">&#128181;</span>Cash on Delivery Nationwide</span>
    <span class="f-trust"><span aria-hidden="true">&#128666;</span>Free Karachi Delivery Over Rs 3,000</span>
  </div>
  <div class="copy">&copy; 2026 Imported Bites. All rights reserved. Prices in Pakistani Rupees.<button class="to-top" id="to-top" type="button" aria-label="Back to top">&#8593;</button></div>
</footer>
{drawer}
<script src="/assets/js/app.js"></script>
""".format(drawer=cart_drawer(), wa=WA_DISPLAY, wn=WA_NUMBER, cats=cats)

def breadcrumbs(items):
    parts = ['<a href="/">Home</a>']
    for name, url in items:
        if url:
            parts.append('<a href="{}">{}</a>'.format(url, esc(name)))
        else:
            parts.append('<span>{}</span>'.format(esc(name)))
    crumbs = " / ".join(parts)
    trail = [{"@type": "ListItem", "position": i + 1, "name": n,
              **({"item": BASE + u} if u else {})} for i, (n, u) in enumerate([("Home", "/")] + items)]
    schema = {"@context": "https://schema.org", "@type": "BreadcrumbList",
              "itemListElement": trail}
    return ('<nav class="breadcrumbs" aria-label="Breadcrumb">{}</nav>'.format(crumbs),
            '<script type="application/ld+json">{}</script>'.format(json.dumps(schema)))

def page(title, meta, canonical, body, schemas=None, nav="Home"):
    schema_html = "\n".join(schemas) if schemas else ""
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{meta}">
<meta name="robots" content="noindex, follow">
<link rel="canonical" href="{canonical}">
<link rel="stylesheet" href="/assets/css/style.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><polygon points='20,22 15,6 30,14' fill='%23EA580C'/><polygon points='44,22 49,6 34,14' fill='%23EA580C'/><path d='M16 24 h32 l-3.5 30 a5 5 0 0 1 -5 4.5 h-15 a5 5 0 0 1 -5 -4.5 z' fill='%23EA580C'/><ellipse cx='29' cy='43' rx='8' ry='5' fill='%23FFF7ED'/><polygon points='37,43 44,38 44,48' fill='%23FFF7ED'/></svg>">
{schema}
</head>
<body>
{header}
<main class="wrap">
{body}
</main>
{footer}
</body>
</html>""".format(title=esc(title), meta=esc(meta), canonical=canonical,
                 schema=schema_html, header=header(nav), body=body, footer=footer())

def write(path, content):
    full = os.path.join(SITE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    return full

# ---------------- schema builders (reusable; product/category pages use them later) ----------------

def org_website_schema():
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "Organization", "name": "Imported Bites", "url": BASE + "/",
             "description": "Pakistan online store for 100% genuine imported food with cash on delivery nationwide.",
             "sameAs": []},
            {"@type": "WebSite", "name": "Imported Bites", "url": BASE + "/",
             "potentialAction": {"@type": "SearchAction",
                                 "target": BASE + "/shop.html?q={search_term_string}",
                                 "query-input": "required name=search_term_string"}}
        ]}
    return '<script type="application/ld+json">{}</script>'.format(json.dumps(data))

def itemlist_schema(items, list_name):
    els = []
    for i, p in enumerate(items, 1):
        els.append({"@type": "ListItem", "position": i,
                    "item": {"@type": "Product", "name": p["name"], "url": BASE + "/products/" + p["slug"] + "/"}})
    data = {"@context": "https://schema.org", "@type": "ItemList", "name": list_name,
            "itemListElement": els}
    return '<script type="application/ld+json">{}</script>'.format(json.dumps(data))

def product_schema(p):
    avail = "https://schema.org/OutOfStock" if p.get("stock", 0) == 0 else "https://schema.org/InStock"
    data = {"@context": "https://schema.org", "@type": "Product",
            "name": p["name"], "description": p.get("desc", p["name"])[:300],
            "category": p.get("category", ""),
            "url": BASE + "/products/" + p["slug"] + "/",
            "offers": {"@type": "Offer", "priceCurrency": "PKR", "price": p["price"],
                       "availability": avail, "url": BASE + "/products/" + p["slug"] + "/"}}
    return '<script type="application/ld+json">{}</script>'.format(json.dumps(data))

def faq_schema(faqs):
    data = {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}
    return '<script type="application/ld+json">{}</script>'.format(json.dumps(data))

def product_card(p):
    badges = []
    if p.get("stock", 0) == 0:
        badges.append('<span class="mini-badge">Out of Stock</span>')
    elif p.get("stock", 0) <= 9:
        badges.append('<span class="mini-badge orange">Low Stock</span>')
    if p.get("badge") and p.get("stock", 0) > 0:
        badges.append('<span class="mini-badge green">{}</span>'.format(esc(p["badge"])))
    if p.get("stock", 0) == 0:
        actions = ('<button class="btn btn-cart" type="button" disabled>Add to Cart</button>'
                   '<button class="btn btn-wa" type="button" data-wa-order="{}">Pre-order on WhatsApp</button>').format(p["slug"])
    else:
        actions = ('<button class="btn btn-cart" type="button" data-add-cart="{}">Add to Cart</button>'
                   '<button class="btn btn-wa" type="button" data-wa-order="{}">Order on WhatsApp</button>').format(p["slug"], p["slug"])
    if p.get("image"):
        card_img = ('<div class="card-img"><img src="/assets/img/products/{}" alt="{}" loading="lazy"></div>'
                    .format(esc(p["image"]), esc(p["name"])))
    else:
        card_img = '<div class="card-img" aria-hidden="true">{}</div>'.format(esc(p.get("emoji", "📦")))
    return """
<article class="card" data-category="{cat}" data-name="{name}">
  {card_img}
  <div class="card-body">
    <div class="badge-row">{badges}</div>
    <h3><a href="/products/{slug}/">{name}</a></h3>
    <p class="variant">Imported</p>
    <p class="price">{price}</p>
    {actions}
  </div>
</article>""".format(cat=esc(p.get("category", "")), name=esc(p["name"]), card_img=card_img,
                     badges="".join(badges), slug=p["slug"], price=price(p), actions=actions)

# ---------------- FAQ data (sentence case questions) ----------------

FAQS = [
    ("Is your cat food really imported from Thailand?",
     "Yes. Our cat food range focuses on the Thai manufactured brands Pakistani cat owners trust most, including Me-O and Whiskas. "
     "Every pack arrives sealed with readable batch codes and printed expiry dates, and we verify the stock before it lists on the site. "
     "If you ever want to confirm a batch, message us on WhatsApp with a photo of the pack and we will check it for you."),
    ("How do I know the products are original and not fake?",
     "We source through licensed import channels, so each product arrives with a sharp readable batch code, a printed expiry date, and an intact factory seal. "
     "Counterfeit packs usually fail on at least one of these: smudged printing, missing batch codes, or resealed packing. "
     "When our full catalog launches, every product page will carry a genuine check guide for that item, and you can always ask us to photograph the actual pack before you order."),
    ("Do you offer cash on delivery in Pakistan?",
     "Yes, cash on delivery is available on every order, anywhere in Pakistan. "
     "You pay in cash when the courier hands you your parcel, and the total is the PKR price on the site plus the delivery fee stated at checkout. "
     "There are no card details, advance payments or hidden charges involved."),
    ("How long does delivery take to Karachi, Lahore and Islamabad?",
     "Orders to Karachi, Lahore and Islamabad are delivered in 2 to 4 working days after dispatch. "
     "Smaller cities and towns usually take 3 to 6 working days depending on the courier route. "
     "You will get a tracking update on WhatsApp once your parcel leaves our packing station."),
    ("What is the expiry date on the products?",
     "We only ship stock with several months of shelf life remaining, and the printed expiry date is confirmed per batch before dispatch. "
     "Every pack carries the manufacturer's printed expiry, never a sticker pasted over it. "
     "If you ever receive an item close to expiry, contact us within 48 hours and we will make it right."),
    ("Can I return cat food if my cat does not eat it?",
     "Because of food safety rules, opened cat food cannot be resold, so a change of taste alone does not qualify for a return. "
     "To be safe, we recommend starting with a small pack when trying a new flavour with your cat. "
     "If your order arrives damaged, wrong or past its printed expiry, send us a photo within 48 hours and we will replace it or refund you."),
    ("Is stevia a good sugar alternative?",
     "Stevia is a plant derived sweetener that many people use to reduce their sugar intake, and it tastes noticeably sweeter than sugar per spoon. "
     "We make no medical or health claims about our products, and sweetness preference is personal, so we suggest trying a small pack first. "
     "If you have a medical condition such as diabetes, please consult your doctor before changing your diet."),
    ("Do you deliver to smaller cities and towns?",
     "Yes, we deliver nationwide through courier partners that cover smaller cities and towns across Pakistan. "
     "Delivery to remote areas takes a few days longer than the 2 to 4 day window for major cities. "
     "Cash on delivery is available everywhere we ship, with no advance payment needed."),
    ("Are the prices on the site final, or are there extra charges?",
     "The PKR price you see is the product price, and the only addition is the delivery fee, which is stated clearly before you confirm your order on WhatsApp. "
     "There are no taxes, handling charges or surprises added at your doorstep. "
     "What you agree on WhatsApp is exactly what you pay the courier in cash."),
    ("How should I store cat food and coffee?",
     "Keep dry cat food in its original bag, rolled shut or in an airtight container, in a cool dry place away from sunlight; use it within a month of opening for the best nutrition. "
     "Keep coffee sealed tight with a dry spoon, away from the stove and moisture, because humidity clumps it fast. "
     "Wet cat food pouches should be refrigerated after opening and used within two days."),
    ("Do you offer bulk or multi-pack deals?",
     "Multi-pack pricing for cat food is available on request, which suits multi-cat households and regular buyers. "
     "Message us on WhatsApp with the brand and quantity you need and we will quote you a bundled price with a single delivery fee. "
     "When our full catalog launches, popular items will carry standing multi-pack options on their product pages."),
    ("What payment methods do you accept?",
     "We accept cash on delivery only. "
     "You pay in cash when the courier delivers your parcel, and there are no card payments, bank transfers or advance payments involved. "
     "This keeps every order simple and risk free for you."),
]

def faq_html(faqs):
    items = []
    for q, a in faqs:
        items.append('<details><summary>{}</summary><div class="answer"><p>{}</p></div></details>'.format(esc(q), esc(a)))
    return '<div class="faq-list">\n' + "\n".join(items) + "\n</div>"

# ---------------- page builders ----------------

# ---------------- hero slider ----------------

SLIDES = [
    {"sticker": "100% Authentic Imported", "tag": "h1",
     "title": "Imported Cat Food, Coffee and More, Delivered in Pakistan",
     "text": "Shop genuine Thailand-origin cat food, imported coffee, stevia and jellies. Pay cash on delivery, shipped to your doorstep anywhere in Pakistan.",
     "cta": "Shop Cat Food", "href": "/cat-dry-food/"},
    {"sticker": "For Your Kitchen", "tag": "h2",
     "title": "Imported Coffee, Stevia and Jellies",
     "text": "Real imported coffee, natural stevia sweetener and fun jelly packs. Every item sealed, dated and genuine.",
     "cta": "Shop Groceries", "href": "/coffee/"},
    {"sticker": "Karachi Offer", "tag": "h2",
     "title": "Free Delivery in Karachi on Orders Over Rs 3,000",
     "text": "Stock up on cat food and groceries. Cross Rs 3,000 and Karachi delivery is on us, with cash on delivery.",
     "cta": "Start Shopping", "href": "/shop.html"},
]

# Transparent product cutouts for the continuous hero marquee (uniform height, one line).
MARQUEE_IMGS = [
    "cutouts/cutout-meo-tuna.webp",
    "cutouts/cutout-meo-persian.webp",
    "cutouts/cutout-meo-kitten.webp",
    "cutouts/cutout-whiskas-adult.webp",
    "cutouts/cutout-temptations.webp",
    "cutouts/cutout-stevia.webp",
    "cutouts/cutout-nescafe.webp",
    "cutouts/cutout-haribo.webp",
]

def hero_slider():
    slides = []
    for n, s in enumerate(SLIDES):
        active = " active" if n == 0 else ""
        slides.append(
            '<div class="slide{act}" role="group" aria-roledescription="slide" aria-label="Slide {num} of 3">'
            '<span class="sticker">{sticker}</span>'
            '<{tag}>{title}</{tag}>'
            '<p>{text}</p>'
            '<a class="hero-cta" href="{href}">{cta}</a>'
            '</div>'.format(act=active, num=n + 1, sticker=esc(s["sticker"]), tag=s["tag"],
                            title=esc(s["title"]), text=esc(s["text"]),
                            cta=esc(s["cta"]), href=s["href"]))
    dots = "".join(
        '<button class="slide-dot{act}" type="button" data-slide="{n}" aria-label="Go to slide {num}"></button>'.format(
            act=" active" if n == 0 else "", n=n, num=n + 1)
        for n in range(len(SLIDES)))
    group = "".join(
        '<img src="/assets/img/{f}" alt="" loading="lazy" draggable="false">'.format(f=f)
        for f in MARQUEE_IMGS)
    return """
<section class="hero hero-slider" aria-label="Featured offers">
  <div class="hero-inner hero-split">
    <div class="hero-text">
      <div class="hero-slides" id="hero-slides">
{slides}
      </div>
      <div class="slider-controls">
        <button class="slide-arrow prev" type="button" data-slide-prev aria-label="Previous slide">&#8249; Prev</button>
        <div class="slide-dots">{dots}</div>
        <button class="slide-arrow next" type="button" data-slide-next aria-label="Next slide">Next &#8250;</button>
      </div>
    </div>
    <div class="hero-marquee" aria-hidden="true">
      <div class="marquee-track">
        <div class="marquee-group">{group}</div>
        <div class="marquee-group">{group}</div>
      </div>
    </div>
  </div>
  <svg class="hero-wave" viewBox="0 0 1440 48" preserveAspectRatio="none" aria-hidden="true" focusable="false"><path d="M0,48 L0,30 C240,6 480,6 720,26 C960,46 1200,46 1440,22 L1440,48 Z" fill="#FFF7ED"/></svg>
</section>""".format(slides="\n".join(slides), dots=dots, group=group)

def build_home():
    tiles = []
    for slug, name, emoji, img in TILE_CATS:
        if img and img_exists(img):
            visual = '<img src="/assets/img/{}" alt="{} online in Pakistan" loading="lazy">'.format(img, esc(name))
        else:
            visual = '<span class="emoji" aria-hidden="true">{}</span>'.format(emoji)
        tiles.append('<a class="cat" href="/{s}/">{v}<span>{n}</span></a>'.format(s=slug, v=visual, n=esc(name)))

    FEATURED = ["me-o-adult-tuna-1-1kg", "whiskas-adult-chicken-1-9kg",
                "whiskas-pouch-beef-poultry-85g", "whiskas-temptations-chicken-45g",
                "klumpy-bentonite-litter-5l-lavender", "nescafe-gold-200g",
                "stevia-sweetener", "haribo-goldbears-200g"]
    ARRIVALS = ["me-o-kitten-1-1kg", "me-o-creamy-treats-tuna",
                "temptations-creamy-puree-salmon-4pack", "whiskas-pouches-12x85g-jelly-variety"]

    featured_section = ""
    if PRODUCTS:
        featured = [BY_SLUG[s] for s in FEATURED if s in BY_SLUG]
        featured_section = """
<p class="eyebrow">Our Picks</p>
<h2 class="section-title">Featured <span class="hl">Products</span></h2>
<p class="section-sub">Bestsellers, restocked fresh this week.</p>
<section class="products" aria-label="Featured products">
{cards}
</section>
""".format(cards="\n".join(product_card(p) for p in featured))
    arrivals_section = ""
    if len(PRODUCTS) >= 4:
        arrivals = [BY_SLUG[s] for s in ARRIVALS if s in BY_SLUG]
        arrivals_section = """
<p class="eyebrow">Fresh Stock</p>
<h2 class="section-title">New <span class="hl">Arrivals</span></h2>
<p class="section-sub">Latest additions, including new price estimates.</p>
<section class="products" aria-label="New arrivals">
{cards}
</section>
""".format(cards="\n".join(product_card(p) for p in arrivals))

    body = """
{hero_slider}

<p class="eyebrow">Browse</p>
<h2 class="section-title">Shop by <span class="hl">Category</span></h2>
<p class="section-sub">Pick your need, we handle the importing.</p>
<section class="cats" aria-label="Categories">
{tiles}
</section>

<p class="eyebrow">Why Us</p>
<h2 class="section-title">Why Shop <span class="hl">With Us</span></h2>
<p class="section-sub">Built for Pakistani shoppers, from sourcing to payment.</p>
<div class="why-grid">
  <div class="why-card"><span class="emoji">🐱</span><h3>Thailand-Origin Cat Food</h3><p>We stock the Thai manufactured cat food brands Pakistani cat owners trust, including Me-O and Whiskas, sourced through licensed import channels.</p></div>
  <div class="why-card"><span class="emoji">📦</span><h3>Sealed Packs, Readable Batch Codes</h3><p>Every product arrives factory sealed with sharp, readable batch codes. No repacked goods, no smudged printing, no guessing.</p></div>
  <div class="why-card"><span class="emoji">📅</span><h3>Printed Expiry Dates</h3><p>We ship only stock with months of shelf life remaining, and every pack carries the manufacturer's printed expiry date.</p></div>
  <div class="why-card"><span class="emoji">💵</span><h3>Cash on Delivery Nationwide</h3><p>Pay in cash when your order arrives, anywhere in Pakistan. No advance payments, no card details, no surprises.</p></div>
  <div class="why-card"><span class="emoji">🚚</span><h3>2 to 4 Day Delivery</h3><p>Orders reach Karachi, Lahore and Islamabad in 2 to 4 working days, with nationwide courier coverage for smaller cities and towns.</p></div>
  <div class="why-card"><span class="emoji">💬</span><h3>WhatsApp Support</h3><p>Questions about ingredients, expiry dates or bulk cat food orders get fast, honest answers on WhatsApp before you spend a rupee.</p></div>
</div>

{featured}
{arrivals}

<p class="eyebrow">Good to Know</p>
<h2 class="section-title">Common <span class="hl">Questions</span></h2>
<p class="section-sub">Quick answers before you order.</p>
{faqs}
<p style="text-align:center;margin-top:16px;"><a class="btn btn-cart" style="display:inline-block;width:auto;padding:12px 32px;" href="/faq.html">Read All FAQs</a></p>

<section class="trust" aria-label="Trust badges">
  <div class="trust-item"><span class="emoji">✅</span>100% Authentic Imported<small>Genuine products, licensed imports</small></div>
  <div class="trust-item"><span class="emoji">💵</span>Cash on Delivery<small>Pay when your order arrives</small></div>
  <div class="trust-item"><span class="emoji">🚚</span>Nationwide Shipping<small>2 to 4 days to major cities</small></div>
</section>
<section class="wa-band" aria-label="Order on WhatsApp">
  <h2>Prefer to Order Directly?</h2>
  <p>Send us your shopping list on WhatsApp and we will confirm your order, delivery fee and timing within minutes.</p>
  <a class="wa-big" href="https://wa.me/{wn}?text=Hi%20Imported%20Bites!%20I%20want%20to%20place%20an%20order." target="_blank" rel="noopener">WhatsApp: {wa}</a>
</section>
""".format(hero_slider=hero_slider(), tiles="\n".join(tiles),
           featured=featured_section, arrivals=arrivals_section,
           faqs=faq_html(FAQS[:4]), wa=WA_DISPLAY, wn=WA_NUMBER)
    return page("Imported Bites: Imported Cat Food, Coffee and More in Pakistan",
                "Shop 100% genuine imported cat food, coffee, stevia and jellies in Pakistan. PKR prices, cash on delivery, 2 to 4 day delivery nationwide.",
                BASE + "/", body, schemas=[org_website_schema()], nav="Home")

def build_shop():
    if PRODUCTS:
        btns = ['<button class="filter-btn active" type="button" data-cat="all">All</button>']
        present = set(p.get("category", "") for p in PRODUCTS)
        for slug, name, e, i in TILE_CATS:
            if slug in present:
                btns.append('<button class="filter-btn" type="button" data-cat="{s}">{n}</button>'.format(s=slug, n=esc(name)))
        filters = """
<div class="filters" role="group" aria-label="Filter products">
  {btns}
  <div class="shop-search">
    <input id="shop-search-input" type="search" placeholder="Search products..." aria-label="Search products">
    <button type="button" onclick="applyShopFilters()">Go</button>
  </div>
</div>""".format(btns="\n".join(btns))
        grid = '<section class="products" id="product-grid" aria-label="All products">\n{cards}\n</section>\n<p id="no-results" class="callout" style="display:none;">No products match your search. Try a different word.</p>'.format(
            cards="\n".join(product_card(p) for p in PRODUCTS))
        schemas_extra = [itemlist_schema(PRODUCTS, "All Imported Products")]
    else:
        filters = ""
        grid = """
<div class="callout">
<strong>Our full product catalog is launching soon.</strong>
We are finalising imported cat food (Me-O and Whiskas, Thailand origin), coffee, stevia sweetener, jellies and more, with PKR prices.
Want to pre-order or get notified at launch? WhatsApp us at <strong>{wa}</strong> and we will reserve your items with cash on delivery, no advance payment.
</div>""".format(wa=WA_DISPLAY)
        schemas_extra = []
    body = """
{c}
<div class="page-hero">
  <h1>Shop Imported Products</h1>
  <p class="lead">Genuine imported cat food, coffee, stevia and jellies with prices in PKR. Filter by category or search by name. Cash on delivery on every order, nationwide.</p>
</div>
{filters}
{grid}
""".format(c=breadcrumbs([("Shop", None)])[0], filters=filters, grid=grid)
    crumb_schema = breadcrumbs([("Shop", None)])[1]
    return page("Shop Imported Cat Food, Coffee and More in Pakistan",
                "Browse genuine imported cat food, coffee, stevia and jellies with prices in PKR. Cash on delivery across Pakistan on every single order.",
                BASE + "/shop.html", body,
                schemas=[crumb_schema] + schemas_extra, nav="Shop")

INFO_PAGES = {
"about": ("About Imported Bites: Imported Food Store in Pakistan",
    "Imported Bites is a Pakistan online store for 100% genuine imported food. Licensed imports, PKR prices, COD and nationwide delivery.",
    "About Imported Bites",
    """
<p class="lead">Pakistan's online store for 100% genuine imported food and pet food, built on authenticity, fair PKR pricing and cash on delivery.</p>
<h2>Why We Started</h2>
<p>Imported Bites began with a simple frustration: buying imported cat food and groceries in Pakistan meant either paying inflated mall prices or gambling on anonymous sellers with no guarantees. We built the store we wished existed, one where every product is sourced through licensed import channels, every price is stated in PKR with no hidden charges, and every order can be paid in cash on delivery.</p>
<h2>What We Sell</h2>
<p>Our focus is the imported essentials Pakistani households actually reorder: Thailand-origin cat food from trusted brands like Me-O and Whiskas, imported coffee, stevia sweetener, jellies and candy, and similar quality imports. Our full catalog with PKR prices is launching soon, and every product page will carry verification guidance so you can check batch codes, expiry dates and seals yourself.</p>
<h2>How We Operate</h2>
<p>Our authenticity promise rests on four practices: licensed imports with readable batch codes, printed expiry dates with months of shelf life, careful protective packing for every parcel, and a 48 hour photo proof replacement policy for anything damaged or wrong. Orders dispatch within 24 hours and reach Karachi, Lahore and Islamabad in 2 to 4 working days, with nationwide courier coverage and cash on delivery everywhere.</p>
<h2>Talk to Us</h2>
<p>We are a small team and we answer our own WhatsApp at {wa}. Questions about ingredients, expiry dates, bulk cat food orders or pre-orders are all welcome. If you are unsure about a product label, message us and we will photograph the actual pack from our shelf.</p>
""".format(wa=WA_DISPLAY)),
"contact": ("Contact Imported Bites Pakistan",
    "Reach Imported Bites for order help, bulk queries and product questions. WhatsApp and email support with fast nationwide service in Pakistan.",
    "Contact Imported Bites",
    """
<p class="lead">Order help, product questions and bulk queries, we reply fast.</p>
<h2>WhatsApp Us</h2>
<p>The fastest way to reach us is WhatsApp at <strong>{wa}</strong>. Send your order, a product question, or a photo of an ingredient label you want us to check, and we will reply during working hours.</p>
<div class="callout">Ordering on WhatsApp is simple: tell us the product names and quantities, share your name, phone, address and city, and we confirm your total with cash on delivery. No advance payment, ever.</div>
<h2>Email</h2>
<p>For detailed queries, bulk orders and business partnerships, email us at <strong>hello@importedbites.com</strong>. We respond within one working day.</p>
<h2>Delivery Coverage</h2>
<p>We deliver to Karachi, Lahore, Islamabad and nationwide across Pakistan in 2 to 4 working days for major cities. See our <a href="/shipping-delivery.html">shipping and delivery page</a> for full details, and our <a href="/faq.html">FAQ page</a> for quick answers.</p>
""".format(wa=WA_DISPLAY)),
"shipping-delivery": ("Shipping and Delivery Across Pakistan",
    "Imported Bites delivers in 2 to 4 days to Karachi, Lahore, Islamabad and nationwide. Cash on delivery and heat-safe food packing nationwide.",
    "Shipping and Delivery",
    """
<p class="lead">2 to 4 working days to major cities, cash on delivery everywhere, and careful packing for every parcel.</p>
<div class="free-delivery-banner"><span class="sticker">🎉 Free Karachi Delivery</span><p><strong>Orders of Rs 3,000 and above get FREE delivery across Karachi.</strong> No code needed: if your cart subtotal reaches Rs 3,000, the delivery fee is on us. Cash on delivery is still available on every order.</p></div>
<h2>Delivery Timeframes</h2>
<p>Orders dispatch within 24 hours of confirmation. Karachi, Lahore and Islamabad receive orders in 2 to 4 working days. Smaller cities and towns typically take 3 to 6 working days depending on the courier route. You receive a tracking update on WhatsApp once your parcel leaves our packing station.</p>
<h2>Cash on Delivery</h2>
<p>Every order is cash on delivery, nationwide. You pay the courier in cash when your parcel arrives. The total is the PKR price on the site plus the delivery fee stated when you confirm your order on WhatsApp. There are no advance payments and no card details involved.</p>
<h2>Careful Packing</h2>
<p>Every parcel is packed to protect its contents: cat food bags are sealed against moisture, jars and delicate items are cushioned, and boxes are taped and labelled for careful handling. If anything arrives damaged or leaking, a photo within 48 hours gets you a replacement under our <a href="/returns-refunds.html">returns policy</a>.</p>
<h2>Delivery Fee</h2>
<p>Karachi orders of Rs 3,000 and above: <strong>delivery is FREE</strong>. For orders below Rs 3,000 and for cities outside Karachi, a flat delivery fee applies per order and is confirmed on WhatsApp before dispatch, so you always know the full total before you commit. The fee depends on your city and parcel weight, and it is the only addition to the product prices on the site.</p>
"""),
"returns-refunds": ("Returns and Refunds at Imported Bites",
    "Damaged or wrong items are replaced or refunded with photo proof within 48 hours. Food and pet food safety rules apply, see the full policy.",
    "Returns and Refunds",
    """
<p class="lead">Damaged or wrong items are replaced or refunded with photo proof within 48 hours. Food safety comes first.</p>
<h2>48 Hour Photo Proof Policy</h2>
<p>If your order arrives damaged, wrong or past its printed expiry date, send us a photo on WhatsApp within 48 hours of delivery. We will replace the item in your next dispatch or adjust the amount on your next order, your choice. No forms, no arguments, no return shipping needed for damaged goods.</p>
<h2>Food and Pet Food Safety Rules</h2>
<p>Because of food safety, opened food and opened pet food cannot be resold, so taste preference, including a cat refusing a new flavour, does not qualify for a return. We state this plainly so expectations are clear, and we recommend starting with a small pack when trying something new with your pet. Items that arrive sealed but are not what you ordered are replaced regardless.</p>
<h2>Unopened Returns</h2>
<p>Unopened items in their original sealed packing can be returned within 7 days of delivery for a refund or exchange. Contact us on WhatsApp first to confirm, and return shipping is arranged at the buyer's cost. Refunds for unopened returns are processed within 5 working days of us receiving the item.</p>
<h2>How to Report a Problem</h2>
<p>Message us on WhatsApp at {wa} with your order name, a photo of the issue, and whether you prefer a replacement or refund. Most cases are resolved the same day.</p>
""".format(wa=WA_DISPLAY)),
"privacy": ("Privacy Policy: Imported Bites Pakistan",
    "How Imported Bites collects, uses and protects your personal data for orders, delivery and support in Pakistan. Read the full policy.",
    "Privacy Policy",
    """
<p class="lead">What we collect, why we collect it, and how we protect it.</p>
<h2>Information We Collect</h2>
<p>When you order, we collect your name, phone number, delivery address and city so the courier can deliver your parcel. When you contact us on WhatsApp or email, we keep the conversation so we can help with your order and improve our service. Our site does not require accounts, so we do not store passwords or payment details; all payments are cash on delivery.</p>
<h2>How We Use It</h2>
<p>Your details are used only to process, pack, ship and support your order. We may message you about your delivery status or about products you asked us to reserve. We do not sell, rent or share your personal information with third parties for marketing. Courier partners receive only the name, phone, address and city needed for delivery.</p>
<h2>Data Storage and Your Rights</h2>
<p>Order records are kept for our accounts and for handling returns within the policy period. You can ask us at any time on WhatsApp or at hello@importedbites.com to see, correct or delete your personal information, and we will comply promptly. If you prefer not to share details beyond what delivery needs, tell us and we will keep it minimal.</p>
"""),
"terms": ("Terms of Service: Imported Bites Pakistan",
    "The terms that govern shopping at Imported Bites, including orders, payments, delivery, returns and food product safety in Pakistan.",
    "Terms of Service",
    """
<p class="lead">The simple rules that govern shopping with us.</p>
<h2>Orders and Prices</h2>
<p>All prices are in Pakistani Rupees (PKR) and are confirmed on WhatsApp before dispatch. An order is confirmed when we acknowledge it and you share your delivery details. We reserve the right to cancel an order if an item is out of stock or a price was listed in error, in which case you pay nothing.</p>
<h2>Payment and Delivery</h2>
<p>Payment is cash on delivery only. You pay the courier in cash when your parcel arrives. Delivery timeframes are 2 to 4 working days for Karachi, Lahore and Islamabad and 3 to 6 working days for other areas; these are estimates and courier delays beyond our control do not qualify for compensation, though we will always help track your parcel.</p>
<h2>Product Safety</h2>
<p>All products are imported food or pet food items with printed expiry dates. Check the expiry on arrival and store products as directed on the product pages and packaging. Products containing common allergens are labelled as such; if you have allergies, read the ingredient information we provide and ask us before ordering.</p>
<h2>Returns</h2>
<p>Returns and refunds follow our <a href="/returns-refunds.html">returns and refunds policy</a>: 48 hour photo proof for damaged or wrong items, and 7 day returns for unopened sealed products. By ordering from Imported Bites you accept these terms.</p>
"""),
"faq": ("FAQs: Buying Imported Food Online in Pakistan",
    "Answers on authenticity, cash on delivery, delivery time, expiry dates and returns for imported cat food and groceries in Pakistan.",
    "Frequently Asked Questions",
    None),
}

def build_category(slug):
    name = CAT_NAME[slug]
    title, meta = CAT_META[slug]
    items = [p for p in PRODUCTS if p["category"] == slug]
    img = [i for s, n, e, i in TILE_CATS if s == slug][0]
    hero_visual = ('<img class="inline" src="/assets/img/{}" alt="{} online in Pakistan" loading="lazy">'.format(img, esc(name))
                   if img and img_exists(img) else "")
    grid = ('<section class="products" aria-label="{n} products">\n{cards}\n</section>'.format(
                n=esc(name), cards="\n".join(product_card(p) for p in items))
            if items else '<div class="callout"><strong>Stock arriving soon.</strong> WhatsApp us at {wa} to pre-order.</div>'.format(wa=WA_DISPLAY))
    body = """
{c}
<div class="page-hero">
  <h1>{n} in Pakistan</h1>
  <p class="lead">{lead}</p>
</div>
<div class="prose">
  {hv}
  {copy}
</div>
{grid}
""".format(c=breadcrumbs([("Shop", "/shop.html"), (name, None)])[0], n=esc(name),
           lead=esc(CAT_LEAD[slug]), hv=hero_visual, copy=CAT_COPY[slug], grid=grid)
    crumb_schema = breadcrumbs([("Shop", "/shop.html"), (name, None)])[1]
    schemas = [crumb_schema]
    if items:
        schemas.append(itemlist_schema(items, name + " in Pakistan"))
    return page(title, meta, BASE + "/" + slug + "/", body, schemas=schemas, nav="Shop")

def build_product(p):
    if p.get("stock", 0) == 0:
        stock = '<p class="stock-line out">Out of Stock: WhatsApp us to pre-order at this price.</p>'
        actions = ('<button class="btn btn-cart" type="button" disabled>Add to Cart</button>'
                   '<button class="btn btn-wa" type="button" data-wa-order="{s}">Pre-order on WhatsApp</button>').format(s=p["slug"])
    elif p.get("stock", 0) <= 9:
        stock = '<p class="stock-line low">Low Stock: only {n} left, order soon.</p>'.format(n=p["stock"])
        actions = ('<button class="btn btn-cart" type="button" data-add-cart="{s}">Add to Cart</button>'
                   '<button class="btn btn-wa" type="button" data-wa-order="{s}">Order on WhatsApp</button>').format(s=p["slug"])
    else:
        stock = '<p class="stock-line in">In Stock: ready to dispatch in 24 hours.</p>'
        actions = ('<button class="btn btn-cart" type="button" data-add-cart="{s}">Add to Cart</button>'
                   '<button class="btn btn-wa" type="button" data-wa-order="{s}">Order on WhatsApp</button>').format(s=p["slug"])
    estimate = ('<p class="callout"><strong>Price note:</strong> this price is an estimate and will be confirmed by the owner before dispatch.</p>'
                if p.get("price_estimate") else "")
    brand_note = ('<p class="callout"><strong>Brand:</strong> the brand for this stevia listing is being finalised; quality and sealing standards are unchanged.</p>'
                  if p["slug"] == "stevia-sweetener" else "")
    related = [BY_SLUG[s] for s in p["related"]]
    genuine = "".join("<li>{}</li>".format(esc(g)) for g in p["genuine"])
    stock_n = p.get("stock", 0)
    sticky_atc = ('<div class="sticky-atc" id="sticky-atc">'
                  '<div class="sa-info"><strong>{name}</strong><span>{price}</span></div>'
                  '<button class="btn btn-cart" type="button" data-add-cart="{s}">Add to Cart</button>'
                  '</div>').format(name=esc(p["name"]), price=price(p), s=p["slug"]) if stock_n > 0 else ""
    badges = []
    if p.get("stock", 0) == 0:
        badges.append('<span class="mini-badge">Out of Stock</span>')
    elif p.get("stock", 0) <= 9:
        badges.append('<span class="mini-badge orange">Low Stock</span>')
    if p.get("badge") and p.get("stock", 0) > 0:
        badges.append('<span class="mini-badge green">{}</span>'.format(esc(p["badge"])))
    if p.get("price_estimate"):
        badges.append('<span class="mini-badge orange">Price TBC</span>')
    if p.get("image"):
        media = ('<div class="product-media"><img src="/assets/img/products/{}" alt="{}"></div>'
                 .format(esc(p["image"]), esc(p["name"])))
    else:
        media = ('<div class="product-media" role="img" aria-label="{}">{}</div>'
                 .format(esc(p["name"]), esc(p.get("emoji", "📦"))))
    body = """
{c}
<article class="product-detail">
  {media}
  <div class="product-info">
    <div class="badge-row">{badges}</div>
    <h1>{name}</h1>
    <p class="variant">{cat}, Imported</p>
    <p class="price-lg">{price}</p>
    {estimate}
    {brand_note}
    {stock}
    <div class="product-actions">{actions}</div>
    <p><strong>Payment:</strong> Cash on Delivery nationwide. <strong>Delivery:</strong> 2 to 4 working days to Karachi, Lahore and Islamabad. Free Karachi delivery on orders over Rs 3,000.</p>
    <div class="genuine-box">
      <h2>How to Check It Is Genuine</h2>
      <ul>{genuine}</ul>
    </div>
  </div>
</article>
{sticky_atc}
<div class="prose">
  <h2>About This Product</h2>
  <p>{desc}</p>
</div>
<h2 class="section-title">Related <span class="hl">Products</span></h2>
<section class="products" aria-label="Related products">
{related}
</section>
""".format(c=breadcrumbs([("Shop", "/shop.html"), (CAT_NAME[p["category"]], "/" + p["category"] + "/"), (p["name"], None)])[0],
           name=esc(p["name"]), media=media, badges="".join(badges),
           cat=esc(CAT_NAME[p["category"]]), price=price(p), estimate=estimate, brand_note=brand_note,
           stock=stock, actions=actions, genuine=genuine, desc=esc(p["desc"]),
           related="\n".join(product_card(r) for r in related), sticky_atc=sticky_atc)
    crumb_schema = breadcrumbs([("Shop", "/shop.html"), (CAT_NAME[p["category"]], "/" + p["category"] + "/"), (p["name"], None)])[1]
    return page(p["name"] + " Price in Pakistan", p["meta"], BASE + "/products/" + p["slug"] + "/",
                body, schemas=[crumb_schema, product_schema(p)], nav="Shop")

def build_blog_index():
    cards = []
    for b in BLOGS:
        visual = ('<img src="/assets/img/{img}" alt="{t}" loading="lazy">'.format(img=b["img"], t=esc(b["title"]))
                  if b.get("img") and img_exists(b["img"])
                  else '<div class="blog-emoji-tile" aria-hidden="true">{e}</div>'.format(e=b["emoji"]))
        cards.append(
            '<a class="blog-card" href="/blog/{slug}/">{v}<div class="blog-body"><h3>{t}</h3><p>{x}</p></div></a>'
            .format(slug=b["slug"], v=visual, t=esc(b["title"]), x=esc(b["excerpt"])))
    body = """
{c}
<div class="page-hero">
  <h1>Imported Bites Blog</h1>
  <p class="lead">Guides for Pakistani cat owners and smart imported grocery shopping: spotting fakes, choosing litter, and comparing brands.</p>
</div>
<div class="blog-grid">
{cards}
</div>
""".format(c=breadcrumbs([("Blog", None)])[0], cards="\n".join(cards))
    crumb_schema = breadcrumbs([("Blog", None)])[1]
    return page("Imported Bites Blog: Cat Food Guides for Pakistan",
                "Guides for Pakistani cat owners: how to spot fake Me-O and Whiskas, best cat litter comparison, plus the Me-O vs Whiskas buying guide.",
                BASE + "/blog/", body, schemas=[crumb_schema], nav="Blog")

def build_blog_post(b):
    visual = ('<img class="inline" src="/assets/img/{img}" alt="{t}" loading="lazy">'.format(img=b["img"], t=esc(b["title"]))
              if b.get("img") and img_exists(b["img"]) else "")
    others = [x for x in BLOGS if x["slug"] != b["slug"]]
    rel = "".join(
        '<a class="blog-card" href="/blog/{s}/"><div class="blog-emoji-tile" aria-hidden="true">{e}</div>'
        '<div class="blog-body"><h3>{t}</h3><p>{x}</p></div></a>'
        .format(s=x["slug"], e=x["emoji"], t=esc(x["title"]), x=esc(x["excerpt"])) for x in others)
    body = """
{c}
<article class="prose">
  <h1 style="font-size:30px;font-weight:900;margin-bottom:12px;">{t}</h1>
  {v}
  {body}
</article>
<h2 class="section-title">Keep <span class="hl">Reading</span></h2>
<div class="blog-grid">
{rel}
</div>
""".format(c=breadcrumbs([("Blog", "/blog/"), (b["title"], None)])[0],
           t=esc(b["title"]), v=visual, body=b["body"], rel=rel)
    crumb_schema = breadcrumbs([("Blog", "/blog/"), (b["title"], None)])[1]
    return page(b["title"] + " | Imported Bites Blog", b["meta"], BASE + "/blog/" + b["slug"] + "/",
                body, schemas=[crumb_schema], nav="Blog")

def build_info(slug):
    title, meta, h1, copy = INFO_PAGES[slug]
    content = ('<p class="lead">Honest answers about authenticity, delivery, expiry dates and returns.</p>' + faq_html(FAQS)) if slug == "faq" else copy
    body = """
{c}
<div class="page-hero">
  <h1>{h1}</h1>
</div>
<div class="prose">
{content}
</div>
""".format(c=breadcrumbs([(h1, None)])[0], h1=h1, content=content)
    crumb_schema = breadcrumbs([(h1, None)])[1]
    schemas = [crumb_schema]
    if slug == "faq":
        schemas.append(faq_schema(FAQS))
    nav = {"faq": "FAQ", "about": "About", "contact": "Contact"}.get(slug, "Home")
    return page(title, meta, BASE + "/" + slug + ".html", body, schemas=schemas, nav=nav)

def build_404():
    body = """
<div class="page-hero error-box">
  <div class="big">404</div>
  <h1>Page Not Found</h1>
  <p class="lead">The page you are looking for does not exist. Try one of these instead.</p>
  <p style="margin-top:18px;"><a class="btn btn-cart" style="display:inline-block;width:auto;padding:12px 32px;" href="/">Back to Home</a>
  <a class="btn btn-wa" style="display:inline-block;width:auto;padding:12px 32px;margin-left:10px;" href="/shop.html">Shop All</a></p>
</div>
"""
    return page("Page Not Found | Imported Bites",
                "The page you are looking for does not exist. Browse imported cat food, coffee and more at Imported Bites Pakistan with cash on delivery.",
                BASE + "/404.html", body, schemas=[breadcrumbs([("Page Not Found", None)])[1]], nav="Home")

# ---------------- sitemap / robots / llms ----------------

def build_sitemap(urls):
    items = "\n".join('  <url><loc>{}</loc></url>'.format(u) for u in urls)
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{}</urlset>\n'.format(items)

def build_robots():
    return "User-agent: *\nAllow: /\nSitemap: {}/sitemap.xml\n".format(BASE)

def build_llms():
    cats = "\n".join("- {}: {}{}/".format(n, BASE, s) for s, n, e, i in TILE_CATS)
    prods = "\n".join("- {} ({}): {}products/{}/".format(p["name"], price(p), BASE, p["slug"]) for p in PRODUCTS)
    blogs = "\n".join("- {}: {}blog/{}/".format(b["title"], BASE, b["slug"]) for b in BLOGS)
    return """# Imported Bites

Imported Bites (importedbites.com) is a Pakistan online store for 100% genuine imported food and pet food: Thailand-origin cat food (Me-O, Whiskas), imported coffee, stevia sweetener, jellies and candy. Prices in PKR, cash on delivery nationwide, 2 to 4 day delivery to Karachi, Lahore and Islamabad. Free delivery across Karachi on orders of Rs 3,000 and above.

Note: the site is in pre-launch and all pages carry noindex directives until launch.

## Categories
{cats}

## Products ({n} items, prices in PKR)
{prods}

## Blog
{blogs}

## Key pages
- Shop all: {base}/shop.html
- Shipping and delivery: {base}/shipping-delivery.html
- Returns and refunds: {base}/returns-refunds.html
- FAQ: {base}/faq.html
- Contact: WhatsApp {wa} (https://wa.me/{wn})

## Ordering
Customers order via the cart checkout or WhatsApp order buttons, which open a WhatsApp chat with a pre-filled cash-on-delivery order summary.
""".format(base=BASE, wa=WA_DISPLAY, wn=WA_NUMBER, cats=cats, prods=prods, blogs=blogs, n=len(PRODUCTS))

# ---------------- app.js catalog + WhatsApp sync ----------------

def sync_app_js():
    path = os.path.join(SITE, "assets", "js", "app.js")
    with open(path, encoding="utf-8") as f:
        js = f.read()
    marker = "/*__PRODUCTS__*/"
    assert marker in js, "PRODUCTS marker missing in app.js"
    mirror = {}
    for p in PRODUCTS:
        mirror[p["slug"]] = {"name": p["name"], "price": p["price"],
                             "emoji": p.get("emoji", "📦"), "stock": p.get("stock", 0),
                             "img": ("/assets/img/products/" + p["image"]) if p.get("image") else ""}
    js = re.sub(r'/\*__PRODUCTS__\*/ .*?;',
                lambda m: marker + " " + json.dumps(mirror, ensure_ascii=False) + ";",
                js, count=1)
    js = re.sub(r'var WHATSAPP_NUMBER = "[0-9]+";',
                'var WHATSAPP_NUMBER = "' + WA_NUMBER + '";', js, count=1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(js)
    print("app.js synced: {} products, WHATSAPP_NUMBER={}".format(len(mirror), WA_NUMBER))

# ---------------- main ----------------

def main():
    os.makedirs(SITE, exist_ok=True)
    sitemap_urls = []
    def add(path, html_content):
        write(path, html_content)
        sitemap_urls.append(BASE + "/" + path.replace("index.html", ""))

    add("index.html", build_home())
    add("shop.html", build_shop())
    for slug, name, e, i in TILE_CATS:
        add(slug + "/index.html", build_category(slug))
    for p in PRODUCTS:
        add("products/" + p["slug"] + "/index.html", build_product(p))
    for slug in INFO_PAGES:
        add(slug + ".html", build_info(slug))
    add("blog/index.html", build_blog_index())
    for b in BLOGS:
        add("blog/" + b["slug"] + "/index.html", build_blog_post(b))
    write("404.html", build_404())
    write("sitemap.xml", build_sitemap(sorted(set(sitemap_urls))))
    write("robots.txt", build_robots())
    write("llms.txt", build_llms())
    sync_app_js()

    print("pages written, checking meta lengths...")
    bad = []
    for root, dirs, files in os.walk(SITE):
        for fn in files:
            if fn.endswith(".html"):
                fp = os.path.join(root, fn)
                with open(fp, encoding="utf-8") as f:
                    c = f.read()
                m = re.search(r'<meta name="description" content="([^"]*)"', c)
                t = re.search(r'<title>([^<]*)</title>', c)
                rel = os.path.relpath(fp, SITE)
                if not m:
                    bad.append((rel, "missing meta"))
                elif not (130 <= len(html.unescape(m.group(1))) <= 155):
                    bad.append((rel, "meta len %d" % len(html.unescape(m.group(1)))))
                if not t or not t.group(1).strip():
                    bad.append((rel, "missing title"))
    for rel, issue in bad:
        print("META ISSUE:", rel, issue)
    if not bad:
        print("all metas 130-155 chars, all titles present")
    print("done.")

if __name__ == "__main__":
    main()
