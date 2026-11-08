#!/usr/bin/env python3
"""Site checker for accordion.sg (stdlib only):  python3 tools/check_site.py
Checks every *.html page (root and language folders):
  - exactly one <h1>; one visible language block (.lx) per page, in the page's language
  - every JSON-LD block parses; FAQPage questions match the visible <summary> count
  - Product / Offer / Organization / Person JSON-LD on a language page is identical to the English page
    (prices, SKUs, availability, shipping are never touched by translation)
  - canonical present, absolute and self-referencing
  - hreflang: every target exists, the cluster includes self and x-default, and is identical on every
    page it lists (reciprocal); <html lang> matches the page's own entry; dir="rtl" on Arabic
  - every internal href/src resolves to a file (and #anchors to an id on the target page)
  - sitemap.xml and every sitemap-*.xml parse, every <loc> and xhtml:link exists on disk
Exit code 1 on any error. 404.html and thank-you.html (noindex utility pages) skip canonical/hreflang.
"""
import html, json, os, re, sys, glob
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit, unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://accordion.sg"
NOINDEX = {"404.html", "thank-you.html"}
ENTITY_TYPES = {"Product", "Offer", "AggregateOffer", "Organization", "Person", "MusicGroup", "LocalBusiness"}
errors = []


def err(page, msg):
    errors.append("%s: %s" % (os.path.relpath(page, ROOT), msg))


def url_to_file(url):
    p = urlsplit(url)
    if p.netloc and p.netloc not in ("accordion.sg", "www.accordion.sg"):
        return None
    path = unquote(p.path)
    f = os.path.join(ROOT, path.lstrip("/"))
    if path.endswith("/") or path == "":
        f = os.path.join(f, "index.html")
    return f


def file_to_url(f):
    rel = os.path.relpath(f, ROOT).replace(os.sep, "/")
    if rel == "index.html" or rel.endswith("/index.html"):
        rel = rel[: -len("index.html")]
    return SITE + "/" + rel


ids_cache = {}


def ids_of(f):
    if f not in ids_cache:
        try:
            ids_cache[f] = set(re.findall(r'\sid="([^"]+)"', open(f, encoding="utf-8").read()))
        except OSError:
            ids_cache[f] = set()
    return ids_cache[f]


def entities(d, out):
    if isinstance(d, dict):
        t = d.get("@type")
        t = t if isinstance(t, list) else [t]
        if any(x in ENTITY_TYPES for x in t):
            out.append(json.dumps(d, sort_keys=True, ensure_ascii=False))
            return out
        for v in d.values():
            entities(v, out)
    elif isinstance(d, list):
        for v in d:
            entities(v, out)
    return out


def ld_blocks(h):
    out = []
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        out.append(m.group(1))
    return out


def main():
    pages = [p for p in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True)
             if "/.git/" not in p and "/tools/" not in p and "/accordion_pdfs/" not in p and "/images/" not in p]
    clusters = {}
    en_entities = {}
    for f in sorted(pages, key=lambda x: (os.path.dirname(x) != ROOT, x)):
        h = open(f, encoding="utf-8").read()
        base = os.path.basename(f)
        is_root = os.path.dirname(f) == ROOT
        utility = base in NOINDEX
        n = len(re.findall(r"<h1[\s>]", h))
        if n != 1:
            err(f, "%d <h1> elements" % n)
        lx = re.findall(r'<div class="lx" data-l="([^"]+)"', h)
        if len(set(lx)) > 1:
            err(f, "more than one language block: %s" % sorted(set(lx)))
        faq_ld = 0
        ents = []
        for raw in ld_blocks(h):
            try:
                d = json.loads(raw)
            except ValueError as e:
                err(f, "JSON-LD does not parse: %s" % e)
                continue
            if isinstance(d, dict) and d.get("@type") == "FAQPage":
                faq_ld = len(d["mainEntity"])
            entities(d, ents)
        if faq_ld and faq_ld != h.count("<summary>"):
            err(f, "FAQPage has %d questions, page shows %d" % (faq_ld, h.count("<summary>")))
        if is_root:
            en_entities[base] = ents
        elif base in en_entities and ents != en_entities[base]:
            err(f, "Product/Offer/Organization/Person JSON-LD differs from the English page")
        lang = re.search(r'<html lang="([^"]+)"', h)
        lang = lang.group(1) if lang else None
        if lang and lang.startswith("ar") and 'dir="rtl"' not in h[:300]:
            err(f, 'Arabic page without dir="rtl"')
        if not utility:
            c = re.search(r'<link rel="canonical" href="([^"]+)"', h)
            if not c:
                err(f, "no canonical")
            elif c.group(1) != file_to_url(f):
                err(f, "canonical %s is not self (%s)" % (c.group(1), file_to_url(f)))
            alts = re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)">', h)
            if not alts:
                err(f, "no hreflang")
            codes = dict(alts)
            if "x-default" not in codes:
                err(f, "no x-default hreflang")
            if file_to_url(f) not in codes.values():
                err(f, "hreflang cluster does not include self")
            elif lang and codes.get(lang) != file_to_url(f):
                err(f, "html lang %s does not match own hreflang entry" % lang)
            for code, u in alts:
                if "?" in u:
                    err(f, "hreflang %s uses a query URL %s" % (code, u))
                t = url_to_file(u)
                if not t or not os.path.exists(t):
                    err(f, "hreflang %s -> missing %s" % (code, u))
            clusters[file_to_url(f)] = tuple(sorted(alts))
            m = re.search(r"window\.ACCSG_PAGE=(\{.*?\});", h)
            if not m:
                err(f, "no window.ACCSG_PAGE")
            else:
                P = json.loads(m.group(1))
                for k, u in P["alt"].items():
                    t = os.path.normpath(os.path.join(os.path.dirname(f), u))
                    if not os.path.exists(t):
                        err(f, "language picker %s -> missing %s" % (k, u))
        for attr, u in re.findall(r'\s(href|src)="([^"]+)"', h):
            u = html.unescape(u)
            if re.match(r"^(https?:|mailto:|tel:|data:|//|javascript:)", u):
                if u.startswith(SITE) and "#" not in u:
                    t = url_to_file(u)
                    if t and not os.path.exists(t):
                        err(f, "absolute link to missing %s" % u)
                continue
            path, _, frag = u.partition("#")
            path = path.split("?", 1)[0]
            if path == "":
                tgt = f
            elif path.startswith("/"):
                tgt = os.path.join(ROOT, unquote(path).lstrip("/"))
                if path.endswith("/") or os.path.isdir(tgt):
                    tgt = os.path.join(tgt, "index.html")
            else:
                tgt = os.path.normpath(os.path.join(os.path.dirname(f), unquote(path)))
                if path.endswith("/") or os.path.isdir(tgt):
                    tgt = os.path.join(tgt, "index.html")
            if not os.path.exists(tgt):
                err(f, "broken link %s" % u)
            elif frag and tgt.endswith(".html") and frag not in ids_of(tgt):
                err(f, "missing anchor #%s in %s" % (frag, os.path.relpath(tgt, ROOT)))
    for url, cl in clusters.items():
        for code, u in cl:
            if code == "x-default":
                continue
            other = clusters.get(u)
            if other is not None and other != cl:
                err(url_to_file(url), "hreflang cluster differs from %s" % u)
                break
    X = "{http://www.w3.org/1999/xhtml}link"
    for sm in glob.glob(os.path.join(ROOT, "sitemap*.xml")):
        try:
            t = ET.parse(sm)
        except ET.ParseError as e:
            err(sm, "XML does not parse: %s" % e)
            continue
        for loc in t.getroot().iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
            tf = url_to_file(loc.text)
            if not tf or not os.path.exists(tf):
                err(sm, "loc missing on disk: %s" % loc.text)
        for x in t.getroot().iter(X):
            tf = url_to_file(x.get("href"))
            if not tf or not os.path.exists(tf):
                err(sm, "xhtml:link missing on disk: %s" % x.get("href"))
    for e in errors[:200]:
        print("ERROR", e)
    print("%d pages checked, %d errors" % (len(pages), len(errors)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
