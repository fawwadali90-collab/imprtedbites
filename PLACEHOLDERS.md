# PLACEHOLDERS — Imported Bites

Everything on this list is waiting on the store owner. Nothing else on the
site is a placeholder. WhatsApp is NOT a placeholder: the real number
0337 3698048 (wa.me/923373698048) is live in the header, footer, contact
page, cart drawer checkout and all order links.

## 1. Business address / city — PENDING
No street address is shown anywhere on the site. The footer (every page,
`site/assets` footer block in `build.py` `footer()`) says "Serving all of
Pakistan" instead of an address. Add the real address/city when supplied.

## 2. Email address — PENDING (currently hello@importedbites.com)
Shown in:
- `build.py` `footer()` (renders on every page, e.g. `site/index.html`,
  `site/shop.html`, all category/product/blog pages)
- `build.py` INFO_PAGES["contact"] (renders `site/contact.html`)
- `build.py` INFO_PAGES["privacy"] (renders `site/privacy.html`)
- `build.py` `build_llms()` (renders `site/llms.txt`)
Replace with the real business email when supplied.

## 3. Stevia Sweetener — brand TBD, price is an ESTIMATE
- `data/products.json` product `stevia-sweetener`: price 950 PKR flagged
  `"price_estimate": true`; brand not yet chosen.
- `site/products/stevia-sweetener/index.html`: shows a "Price TBC" badge, a
  price-estimate callout, and a brand-TBD callout. Product description notes
  the brand is being finalised.

## 4. Estimate prices awaiting owner confirmation ("Price TBC" badge + callout on each product page)
- Me-O Kitten 1.1kg — PKR 2100 (`data/products.json` line ~62,
  `site/products/me-o-kitten-1-1kg/index.html`)
- Me-O Creamy Treats Tuna Pack — PKR 650 (`data/products.json` line ~257,
  `site/products/me-o-creamy-treats-tuna/index.html`)
- Temptations Creamy Puree Salmon 4 Pack — PKR 1200
  (`data/products.json` line ~280,
  `site/products/temptations-creamy-puree-salmon-4pack/index.html`)
All prices are wired through `data/products.json`; the owner edits prices
there (or later in the dashboard) and re-runs `build.py`.

## 5. Product images — pending real photos
All product cards and product pages currently use styled emoji tiles.
Category tiles use the generated images where they exist (hero-flatlay.png on
the home hero; cat-cat-food.png, cat-coffee.png, cat-sweeteners.png and
cat-jellies-candy.png on the home category tiles and their category pages;
blog-delivery-parcel.png on the cat litter blog post), with emoji-tile
fallback elsewhere. about-pantry.png exists but is intentionally unreferenced
for now. Expected image files, referenced only if present at build time:
- `site/assets/img/hero-flatlay.png` (home hero)
- `site/assets/img/cat-cat-food.png` (Cat Dry Food tile)
- `site/assets/img/cat-coffee.png` (Coffee tile)
- `site/assets/img/cat-sweeteners.png` (Stevia and Sweeteners tile)
- `site/assets/img/cat-jellies-candy.png` (Jellies and Candy tile)
- `site/assets/img/about-pantry.png` (about page, not currently referenced)
- `site/assets/img/blog-delivery-parcel.png` (litter blog post)
`build.py` `img_exists()` falls back to emoji tiles when a file is missing,
so dropping real photos into `site/assets/img/` and re-running `build.py`
wires them in automatically.

## 6. Delivery fees outside the free-Karachi policy — confirmed per order
Free delivery across Karachi on orders of Rs 3,000+ is live (announcement
bar, cart drawer progress hint, checkout note, WhatsApp summary line,
shipping page banner). Delivery fees for Karachi orders under Rs 3,000 and
for other cities are NOT invented; the site states they are confirmed on
WhatsApp before dispatch.
