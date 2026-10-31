#!/usr/bin/env python3
"""First-pass validation for the Imported Bites static site."""
import os, re, html, json, sys
from html.parser import HTMLParser

ROOT = os.path.expanduser("~/workspace/importedbites")
SITE = os.path.join(ROOT, "site")
BASE = "https://importedbites.com"
errors, warnings = [], []

def check(name, ok, detail=""):
    (errors if not ok else warnings)  # placeholder to keep structure
    if not ok:
        errors.append("{}: {}".format(name, detail))

# ---------- 1. em/en dashes (site output, build script, data; not this file) ----------
dash_re = re.compile(r"[—–]")
dash_hits = []
scan_roots = [SITE,
              os.path.join(ROOT, "build.py"),
              os.path.join(ROOT, "data")]
for sr in scan_roots:
    if os.path.isdir(sr):
        walker = os.walk(sr)
    else:
        walker = [(os.path.dirname(sr), [], [os.path.basename(sr)])]
    for root, dirs, files in walker:
        for fn in files:
            if fn.endswith((".html", ".py", ".json", ".css", ".js", ".txt", ".xml")):
                fp = os.path.join(root, fn)
                with open(fp, encoding="utf-8", errors="replace") as f:
                    for i, line in enumerate(f, 1):
                        if dash_re.search(line):
                            dash_hits.append("{}:{}".format(os.path.relpath(fp, ROOT), i))
check("no em/en dashes", not dash_hits, "; ".join(dash_hits[:10]))

# ---------- 2. balanced tags ----------
VOID = {"area","base","br","col","embed","hr","img","input","link","meta","param","source","track","wbr"}
class Balancer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.problems = [], []
    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()))
    def handle_startendtag(self, tag, attrs):
        pass
    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()
        else:
            # try to find a match up the stack
            names = [t for t, _ in self.stack]
            if tag in names:
                while self.stack and self.stack[-1][0] != tag:
                    t, pos = self.stack.pop()
                    self.problems.append("unclosed <{}> opened at {}".format(t, pos))
                self.stack.pop()
            else:
                self.problems.append("stray </{}> at {}".format(tag, self.getpos()))

pages = []
for root, dirs, files in os.walk(SITE):
    for fn in files:
        if fn.endswith(".html"):
            pages.append(os.path.join(root, fn))
for fp in pages:
    with open(fp, encoding="utf-8") as f:
        c = f.read()
    b = Balancer()
    b.feed(c)
    leftover = ["<{}> at {}".format(t, pos) for t, pos in b.stack]
    probs = b.problems + (["unclosed: " + ", ".join(leftover)] if leftover else [])
    # stray text nodes directly in <head> (outside title/script/style)
    class HeadText(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.in_head = False
            self.skip_depth = 0
            self.stray = []
        def handle_starttag(self, tag, attrs):
            if tag == "head":
                self.in_head = True
            elif self.in_head and tag in ("title", "script", "style"):
                self.skip_depth += 1
        def handle_endtag(self, tag):
            if tag == "head":
                self.in_head = False
            elif self.in_head and tag in ("title", "script", "style") and self.skip_depth:
                self.skip_depth -= 1
        def handle_data(self, data):
            if self.in_head and not self.skip_depth and data.strip():
                self.stray.append(data.strip()[:60])
    ht = HeadText()
    ht.feed(c)
    if ht.stray:
        probs.append("stray text in <head>: {}".format("; ".join(ht.stray[:3])))
    check("balanced tags " + os.path.relpath(fp, SITE), not probs, "; ".join(probs[:5]))

# ---------- 3. internal links resolve ----------
def resolve(url):
    if url.startswith("#") or url.startswith("mailto:") or url.startswith("tel:"):
        return None
    if re.match(r"https?://", url):
        return None
    if url.startswith("/"):
        p = url.split("?")[0].split("#")[0]
        if p == "/":
            return os.path.join(SITE, "index.html")
        cand = os.path.join(SITE, p.lstrip("/"))
        if os.path.isdir(cand):
            cand = os.path.join(cand, "index.html")
        return cand
    return None
for fp in pages:
    with open(fp, encoding="utf-8") as f:
        c = f.read()
    for m in re.finditer(r'(?:href|src)="([^"]+)"', c):
        u = m.group(1)
        if u.startswith("data:"):
            continue
        target = resolve(u)
        if target and not os.path.exists(target):
            check("link resolves", False, "{} -> {} (from {})".format(u, os.path.relpath(target, SITE), os.path.relpath(fp, SITE)))

# ---------- 4. referenced images exist ----------
for fp in pages:
    with open(fp, encoding="utf-8") as f:
        c = f.read()
    for m in re.finditer(r'<img[^>]+src="([^"]+)"', c):
        u = m.group(1)
        target = resolve(u)
        if target and not os.path.exists(target):
            check("image exists", False, "{} (from {})".format(u, os.path.relpath(fp, SITE)))

# ---------- 5. per-page SEO requirements ----------
# Expected canonicals derived from file paths.
def expected_canonical(rel):
    if rel == "index.html":
        return BASE + "/"
    if rel.endswith("/index.html"):
        return BASE + "/" + rel[:-len("index.html")]
    return BASE + "/" + rel

titles, metas = {}, {}
for fp in pages:
    rel = os.path.relpath(fp, SITE)
    with open(fp, encoding="utf-8") as f:
        c = f.read()
    t = re.search(r"<title>([^<]*)</title>", c)
    m = re.search(r'<meta name="description" content="([^"]*)"', c)
    check("title present " + rel, bool(t and t.group(1).strip()))
    check("meta present " + rel, bool(m))
    if t:
        titles.setdefault(t.group(1), []).append(rel)
    if m:
        ml = len(html.unescape(m.group(1)))
        check("meta 130-155 " + rel, 130 <= ml <= 155, "len={}".format(ml))
        metas.setdefault(html.unescape(m.group(1)), []).append(rel)
    h1s = re.findall(r"<h1[ >]", c)
    check("one H1 " + rel, len(h1s) == 1, "found {}".format(len(h1s)))
    can = re.search(r'<link rel="canonical" href="([^"]+)"', c)
    exp = expected_canonical(rel)
    check("canonical " + rel, bool(can) and can.group(1) == exp,
          "got {} want {}".format(can.group(1) if can else None, exp))
    check("robots noindex " + rel, '<meta name="robots" content="noindex, follow">' in c)
    schemas = re.findall(r'<script type="application/ld\+json">(.*?)</script>', c, re.S)
    check("has schema " + rel, len(schemas) >= 1)
    blob = " ".join(schemas)
    if rel == "index.html":
        check("home Organization+SearchAction", '"Organization"' in blob and "SearchAction" in blob)
    if rel == "faq.html":
        check("faq FAQPage", '"FAQPage"' in blob)
    if rel not in ("index.html",):
        check("breadcrumb schema " + rel, '"BreadcrumbList"' in blob)
    if "/products/" in rel:
        check("product Offer PKR " + rel, '"priceCurrency"' in blob and '"PKR"' in blob)
    if rel in ("shop.html",) or (rel.count("/") == 1 and rel.endswith("/index.html") and not rel.startswith(("products/", "blog/"))):
        # shop + category pages carry ItemList
        check("itemlist schema " + rel, '"ItemList"' in blob)
    # alt text on every img
    for im in re.finditer(r"<img[^>]*>", c):
        check("img alt " + rel, 'alt="' in im.group(0), im.group(0)[:80])
for title, rels in titles.items():
    check("unique title", len(rels) == 1, "{} on {}".format(title[:50], rels))
for meta, rels in metas.items():
    check("unique meta", len(rels) == 1, "{} on {}".format(meta[:50], rels))

# ---------- 6. no lorem ----------
lorem_hits = []
for fp in pages:
    with open(fp, encoding="utf-8") as f:
        if "lorem" in f.read().lower():
            lorem_hits.append(os.path.relpath(fp, SITE))
check("no lorem ipsum", not lorem_hits, "; ".join(lorem_hits))

# ---------- 7. no unlisted placeholders ----------
# Real WhatsApp (0337 3698048) and hello@ email are listed in PLACEHOLDERS.md.
# Here we only flag leftover placeholder tokens and the old "(replace)" marker.
# HTML input placeholder="..." attributes are legitimate UI text, not placeholders.
suspicious = re.compile(r"0000000|\(replace\)|TODO|FIXME|example\.com", re.I)
ph_hits = []
for root, dirs, files in os.walk(SITE):
    for fn in files:
        if fn.endswith((".html", ".js")):
            fp = os.path.join(root, fn)
            with open(fp, encoding="utf-8") as f:
                content = f.read()
            content_no_attr = re.sub(r'placeholder="[^"]*"', "", content)
            for i, line in enumerate(content_no_attr.splitlines(), 1):
                if suspicious.search(line):
                    ph_hits.append("{}:{}: {}".format(os.path.relpath(fp, SITE), i, line.strip()[:100]))
check("no unlisted placeholders", not ph_hits, "; ".join(ph_hits[:10]))

print("=" * 60)
print("PAGES CHECKED:", len(pages))
if errors:
    print("ERRORS ({}):".format(len(errors)))
    for e in errors:
        print("  FAIL:", e)
    sys.exit(1)
print("ALL CHECKS PASSED")
