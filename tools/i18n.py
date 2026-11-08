#!/usr/bin/env python3
"""accordion.sg multilingual build (standard library only).

The English pages in the repo root are the source and the template for every language. Each
language is published as real static pages in its own folder (/es/about.html, /zh-hans/, /ar/ ...)
with its own <html lang>, self-canonical, a full hreflang cluster, translated title, description,
Open Graph text and JSON-LD, and the header language picker linking the versions together.

Every translatable piece of English is a *segment*, keyed by a short hash of its text:
  - the chrome dictionary (window.ACCSG_I18N.en: nav, footer, labels, WhatsApp drafts)
  - the page body inside <div class="lx" data-l="en"> (text runs, alt/title/aria-label, data-wa drafts)
  - <title>, meta description, og:/twitter: text
  - JSON-LD text (headline, description, FAQ questions/answers, breadcrumb names ...)
Translations live in i18n/<code>.json ({id: text}; an "id@/page.html" key overrides one page).
i18n/source.json holds the English, i18n/pages.json which ids each page needs.

Commands
  python3 tools/i18n.py import-legacy          import the old in-page translations (12 languages in every
                                               file, ?lang=xx) into the translation memory; build runs it
                                               automatically while legacy blocks are still in the pages
  python3 tools/i18n.py extract                refresh i18n/source.json + i18n/pages.json
  python3 tools/i18n.py todo <code> [page ...] print untranslated segments as  id<TAB>English
  python3 tools/i18n.py merge <code> <file>    merge  id<TAB>translation  lines (placeholders checked)
  python3 tools/i18n.py build [--prune]        English pages (normalised), every language page whose
                                               content is 100% translated, hreflang, picker, sitemaps
  python3 tools/i18n.py status                 coverage per language

Inline markup inside a segment appears as <g1>…</g1> (paired tags) and <x1/> (void tags or labels the
site fills in itself); keep every one of them. A page is published in a language when all of its content
segments (body, chrome, title, description) are translated. Structured-data-only strings and image alt
text in the head fall back to English until translated (they are still listed by `todo`).
"""
import hashlib, html, json, os, re, sys, glob
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://accordion.sg"
I18N = os.path.join(ROOT, "i18n")
TODAY = "2026-11-08"

# code, folder, hreflang + <html lang>, og:locale, native name, runtime key (legacy ?lang= value), extra font
LANGS = [
    ("en", "", "en", "en_SG", "English", "en", None),
    ("es", "es", "es", "es_ES", "Español", "es", None),
    ("fr", "fr", "fr", "fr_FR", "Français", "fr", None),
    ("de", "de", "de", "de_DE", "Deutsch", "de", None),
    ("it", "it", "it", "it_IT", "Italiano", "it", None),
    ("pt", "pt", "pt", "pt_PT", "Português", "pt", None),
    ("ru", "ru", "ru", "ru_RU", "Русский", "ru", None),
    ("zh-hans", "zh-hans", "zh-Hans", "zh_CN", "简体中文", "zh", None),
    ("zh-hant", "zh-hant", "zh-Hant", "zh_TW", "繁體中文", "zh-hant", "Noto+Sans+TC:wght@400;700"),
    ("ja", "ja", "ja", "ja_JP", "日本語", "ja", None),
    ("ko", "ko", "ko", "ko_KR", "한국어", "ko", None),
    ("th", "th", "th", "th_TH", "ไทย", "th", "Noto+Sans+Thai:wght@400;600;700"),
    ("vi", "vi", "vi", "vi_VN", "Tiếng Việt", "vi", None),
    ("id", "id", "id", "id_ID", "Bahasa Indonesia", "id", None),
    ("ms", "ms", "ms", "ms_MY", "Bahasa Melayu", "ms", None),
    ("ta", "ta", "ta", "ta_IN", "தமிழ்", "ta", None),
    ("hi", "hi", "hi", "hi_IN", "हिन्दी", "hi", "Noto+Sans+Devanagari:wght@400;600;700"),
    ("fil", "fil", "fil", "tl_PH", "Filipino", "fil", None),
    ("ar", "ar", "ar", "ar_AR", "العربية", "ar", "Noto+Sans+Arabic:wght@400;600;700"),
]
L = {l[0]: dict(code=l[0], dir=l[1], tag=l[2], og=l[3], name=l[4], key=l[5], font=l[6]) for l in LANGS}
CODES = [l[0] for l in LANGS]
BY_KEY = {L[c]["key"]: c for c in CODES}            # runtime/legacy key -> code ("zh" -> "zh-hans")
LEGACY = ["es", "fr", "de", "it", "pt", "ru", "zh-hans", "ja", "ko", "ms", "ta"]
NOT_TRANSLATED = {"404.html", "thank-you.html"}     # English-only utility pages

INLINE = {"a", "abbr", "b", "br", "code", "em", "i", "mark", "q", "s", "small", "span", "strong", "sub", "sup",
          "time", "u", "wbr", "img", "cite", "dfn", "kbd", "var", "bdi", "bdo"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr", "param"}
SKIP = {"script", "style", "svg", "noscript", "template", "select"}
ATTRS = ("alt", "title", "aria-label", "placeholder", "data-wa")
META_NAMES = {"description", "twitter:title", "twitter:description", "twitter:image:alt"}
META_PROPS = {"og:title", "og:description", "og:image:alt"}
SOFT_META = {"twitter:image:alt", "og:image:alt"}
LD_TEXT_KEYS = {"name", "headline", "alternativeHeadline", "description", "text", "articleSection", "caption"}
# JSON-LD entities (people, the academy, products and their offers) stay exactly as authored in every language
LD_SKIP_TYPES = {"Organization", "WebSite", "Person", "MusicGroup", "MusicSchool", "LocalBusiness", "Brand",
                 "CollegeOrUniversity", "EducationalOrganization", "Product", "Offer", "AggregateOffer",
                 "OfferShippingDetails", "MonetaryAmount", "DefinedRegion", "PostalAddress", "Occupation",
                 "OrganizationRole", "Role", "Service"}
KEEP_RE = re.compile(r"^(?:accordion\.sg|A&G Academy|Trio de Tango|WhatsApp|YouTube|Instagram|SGD|"
                     r"[\d\s.,:;+×x–\-−%°~<>/()·#$S]*)$")
PH_RE = re.compile(r"</?g\d+>|<x\d+/>")


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def write(p, s):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)


def sid(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]


def norm(s):
    return re.sub(r"[ \t\n\r\f\v]+", " ", s).strip(" \t\n\r\f\v")


def translatable(t):
    return bool(t) and bool(re.search(r"[^\W\d_]", t)) and not KEEP_RE.match(t)


# ---------------------------------------------------------------- parsing
class Tok:
    __slots__ = ("kind", "tag", "attrs", "start", "end", "raw", "el")

    def __init__(self, kind, tag, attrs, start):
        self.kind, self.tag, self.attrs, self.start, self.end, self.raw, self.el = kind, tag, attrs, start, None, None, None


class El:
    __slots__ = ("tag", "attrs", "open", "close", "children", "parent")

    def __init__(self, tag, attrs, open_i, parent):
        self.tag, self.attrs, self.open, self.close, self.children, self.parent = tag, dict(attrs), open_i, None, [], parent


class Parser(HTMLParser):
    def __init__(self, doc):
        super().__init__(convert_charrefs=False)
        self.lines = [0]
        for m in re.finditer("\n", doc):
            self.lines.append(m.end())
        self.toks = []

    def off(self):
        ln, col = self.getpos()
        return self.lines[ln - 1] + col

    def add(self, kind, tag=None, attrs=()):
        self.toks.append(Tok(kind, tag, attrs, self.off()))

    def handle_starttag(self, tag, attrs): self.add("start", tag, attrs)
    def handle_startendtag(self, tag, attrs): self.add("startend", tag, attrs)
    def handle_endtag(self, tag): self.add("end", tag)
    def handle_data(self, d): self.add("data")
    def handle_entityref(self, n): self.add("data")
    def handle_charref(self, n): self.add("data")
    def handle_comment(self, d): self.add("other")
    def handle_decl(self, d): self.add("other")
    def handle_pi(self, d): self.add("other")
    def unknown_decl(self, d): self.add("other")


def parse(doc):
    p = Parser(doc)
    p.feed(doc)
    p.close()
    toks = p.toks
    # merge adjacent data tokens (entities split text into several tokens)
    merged = []
    for t in toks:
        if t.kind == "data" and merged and merged[-1].kind == "data":
            continue
        merged.append(t)
    toks = merged
    for i, t in enumerate(toks):
        t.end = toks[i + 1].start if i + 1 < len(toks) else len(doc)
        t.raw = doc[t.start:t.end]
    root = El("#root", (), -1, None)
    cur = root
    for i, t in enumerate(toks):
        if t.kind in ("start", "startend"):
            el = El(t.tag, t.attrs, i, cur)
            t.el = el
            cur.children.append(("el", el))
            if t.kind == "start" and t.tag not in VOID:
                cur = el
            else:
                el.close = i
        elif t.kind == "end":
            x = cur
            while x is not root and x.tag != t.tag:
                x = x.parent
            if x is not root:
                x.close = i
                cur = x.parent
        elif t.kind == "data":
            cur.children.append(("tok", i))
    return toks, root


def is_lx(el):
    return el.tag == "div" and "lx" in (el.attrs.get("class") or "").split() and el.attrs.get("data-l")


# ---------------------------------------------------------------- segmentation
class Seg:
    __slots__ = ("kind", "text", "id", "a", "b", "tags", "lead", "trail", "tok", "attr", "soft")


def direct_text(toks, el):
    return any(k == "tok" and toks[x].raw.strip() for k, x in el.children)


def text_of_children(toks, children, tagmap):
    out = []

    def ser(kind, x):
        if kind == "tok":
            out.append(html.unescape(toks[x].raw))
            return
        n = len(tagmap) + 1
        if x.attrs.get("data-t") is not None and x.close is not None and x.close != x.open:
            tagmap.append(("xe", x.open, x.close))      # label filled from the chrome dictionary
            out.append("<x%d/>" % n)
        elif x.close is None or x.close == x.open or x.tag in VOID:
            tagmap.append(("x", x.open, None))
            out.append("<x%d/>" % n)
        else:
            tagmap.append(("g", x.open, x.close))
            out.append("<g%d>" % n)
            for c in x.children:
                ser(*c)
            out.append("</g%d>" % n)
    for c in children:
        ser(*c)
    return "".join(out)


def container(toks, el):
    """Inline element with no text of its own that wraps elements (card links): treat as a block."""
    if el.tag not in INLINE or el.tag in VOID or el.attrs.get("data-t") is not None:
        return False
    if el.close is None or el.close == el.open or direct_text(toks, el):
        return False
    return any(k == "el" for k, c in el.children)


def segments(doc):
    """Segments of an English page: <head> text, the English .lx blocks; chrome comes from the dictionary."""
    toks, root = parse(doc)
    segs = []
    active = [False] * len(toks)

    def mark(el, on):
        if el.open >= 0:
            end = el.close if el.close is not None else el.open
            for i in range(el.open, end + 1):
                active[i] = on

    def walk_regions(el, inside):
        for k, x in el.children:
            if k != "el":
                continue
            if x.tag == "head":
                mark(x, True)
                walk_regions(x, True)
            elif is_lx(x):
                mark(x, x.attrs.get("data-l") == "en")
                if x.attrs.get("data-l") == "en":
                    walk_regions(x, True)
            elif x.tag in SKIP or x.attrs.get("data-t") is not None:
                mark(x, False)
            else:
                walk_regions(x, inside)
    walk_regions(root, False)

    def visit(el, inside):
        if el.tag in SKIP or el.attrs.get("translate") == "no" or el.attrs.get("data-t") is not None:
            return
        if is_lx(el):
            if el.attrs.get("data-l") != "en":
                return
            inside = True
        if el.tag == "head":
            inside = True
        if not inside:
            for k, x in el.children:
                if k == "el":
                    visit(x, False)
            return
        runs, run = [], []
        for c in el.children:
            inl = c[0] == "tok" or (c[1].tag in INLINE and c[1].tag not in SKIP and not container(toks, c[1]))
            if inl:
                run.append(c)
            else:
                if run:
                    runs.append(("run", run)); run = []
                runs.append(("blk", c))
        if run:
            runs.append(("run", run))
        for kind, r in runs:
            if kind == "blk":
                if r[0] == "el":
                    visit(r[1], True)
                continue
            if any(k == "tok" and toks[x].raw.strip() for k, x in r):
                make_run_seg(r)
            else:
                for k, x in r:
                    if k == "el":
                        visit(x, True)

    def first_tok(c):
        return c[1] if c[0] == "tok" else c[1].open

    def last_tok(c):
        return c[1] if c[0] == "tok" else (c[1].close if c[1].close is not None else c[1].open)

    def make_run_seg(r):
        while r and r[0][0] == "tok" and not toks[r[0][1]].raw.strip():
            r = r[1:]
        while r and r[-1][0] == "tok" and not toks[r[-1][1]].raw.strip():
            r = r[:-1]
        if not r:
            return
        tagmap = []
        raw_text = text_of_children(toks, r, tagmap)
        a, b = toks[first_tok(r[0])].start, toks[last_tok(r[-1])].end
        s = Seg()
        s.kind, s.a, s.b, s.tags, s.tok, s.attr, s.soft = "run", a, b, tagmap, None, None, False
        s.lead = re.match(r"\s*", doc[a:b]).group(0)
        s.trail = re.search(r"\s*$", doc[a:b]).group(0)
        s.text = norm(raw_text)
        s.id = sid(s.text) if translatable(PH_RE.sub("", s.text)) else None
        segs.append(s)

    visit(root, False)
    for i, t in enumerate(toks):
        if t.kind not in ("start", "startend") or not active[i]:
            continue
        at = dict(t.attrs)
        names = [a for a in ATTRS if at.get(a)]
        if t.tag == "meta" and at.get("content") and (at.get("name") in META_NAMES or at.get("property") in META_PROPS):
            names.append("content")
        for a in names:
            val = norm(html.unescape(at[a]) if a == "content" else at[a])
            s = Seg()
            s.kind, s.tok, s.attr, s.tags, s.lead, s.trail, s.a, s.b = "attr", i, a, [], "", "", None, None
            s.soft = a == "content" and (at.get("name") in SOFT_META or at.get("property") in SOFT_META)
            s.text = val
            s.id = sid(val) if translatable(val) else None
            segs.append(s)
    for i, t in enumerate(toks):
        if t.kind == "start" and t.tag == "script" and dict(t.attrs).get("type") == "application/ld+json":
            for val in ld_texts(json.loads(toks[i + 1].raw)):
                s = Seg()
                s.kind, s.tok, s.attr, s.tags, s.lead, s.trail, s.a, s.b, s.soft = "ld", i + 1, None, [], "", "", None, None, True
                s.text = val
                s.id = sid(val) if translatable(val) else None
                segs.append(s)
    return toks, segs


def ld_skip(d):
    t = d.get("@type")
    t = t if isinstance(t, list) else [t]
    return any(x in LD_SKIP_TYPES for x in t)


def ld_texts(d, skip=False):
    out = []
    if isinstance(d, dict):
        skip = skip or ld_skip(d)
        for k, v in d.items():
            if isinstance(v, str):
                if not skip and k in LD_TEXT_KEYS:
                    out.append(norm(v))
            else:
                out += ld_texts(v, skip)
    elif isinstance(d, list):
        for v in d:
            out += ld_texts(v, skip)
    return out


# ---------------------------------------------------------------- page model
def en_pages():
    return sorted((os.path.basename(p) for p in glob.glob(os.path.join(ROOT, "*.html"))
                   if os.path.basename(p) not in NOT_TRANSLATED), key=lambda p: (p != "index.html", p))


def lang_url(code, page):
    d = L[code]["dir"]
    tail = "" if page == "index.html" else page
    return "/" + (d + "/" if d else "") + tail


def lang_file(code, page):
    d = L[code]["dir"]
    return os.path.join(ROOT, d, page) if d else os.path.join(ROOT, page)


DICT_RE = re.compile(r'<script>\s*window\.ACCSG_I18N=(\{.*?\});\s*window\.ACCSG_META=(\{.*?\});\s*'
                     r'window\.ACCSG_LANGS=(\[.*?\]);(.*?)</script>', re.S)


def page_data(doc):
    m = DICT_RE.search(doc)
    if not m:
        raise RuntimeError("no ACCSG_I18N block")
    return json.loads(m.group(1)), json.loads(m.group(2)), m


def lx_elements(toks, root):
    out = []

    def walk(el):
        for k, x in el.children:
            if k == "el":
                if is_lx(x):
                    out.append(x)
                else:
                    walk(x)
    walk(root)
    return out


def normalise_en(doc):
    """English source view of a root page: only the English blocks, English dictionary, empty picker."""
    toks, root = parse(doc)
    cuts = []
    for el in lx_elements(toks, root):
        if el.attrs.get("data-l") != "en":
            a, b = toks[el.open].start, toks[el.close].end
            if doc[b:b + 1] == "\n":
                b += 1
            cuts.append((a, b))
    for a, b in sorted(cuts, reverse=True):
        doc = doc[:a] + doc[b:]
    D, M, m = page_data(doc)
    keep = (m.group(4) or "")
    keep = re.sub(r"window\.ACCSG_PAGE=.*$", "", keep, flags=re.S).strip()
    new = '<script>\nwindow.ACCSG_I18N=%s;window.ACCSG_META=%s;window.ACCSG_LANGS=[["en", "en", "English"]];%s\n</script>' % (
        json.dumps({"en": D["en"]}, ensure_ascii=False),
        json.dumps({"title": {"en": M["title"]["en"]}, "desc": {"en": M["desc"]["en"]}}, ensure_ascii=False),
        ("\n" + keep) if keep else "")
    doc = doc[:m.start()] + new + doc[m.end():]
    doc = re.sub(r'<select id="langsel">.*?</select>', '<select id="langsel"></select>', doc, count=1, flags=re.S)
    return doc


def has_legacy(doc):
    return re.search(r'<div class="lx" data-l="(?!en")[^"]+"', doc) is not None


# ---------------------------------------------------------------- translation memory
def load_tm(code):
    p = os.path.join(I18N, code + ".json")
    return json.loads(read(p)) if os.path.exists(p) else {}


def save_tm(code, tm):
    write(os.path.join(I18N, code + ".json"), json.dumps(dict(sorted(tm.items())), ensure_ascii=False, indent=0) + "\n")


def lookup(tm, i, scope, occ=None):
    """Translation of segment i on page scope: occurrence override, page override, then the shared entry."""
    if occ is not None:
        v = tm.get("%s@%s#%s" % (i, scope, occ))
        if v is not None:
            return v
    v = tm.get(i + "@" + scope)
    return v if v is not None else tm.get(i)


def occurrences(doc, toks, segs):
    """n-th occurrence of each id among body (.lx) run/attr segments, in document order."""
    m = re.search(r'<div class="lx" data-l="', doc)
    start = m.start() if m else len(doc)
    seen, occ = {}, {}
    items = []
    for s in segs:
        if s.kind not in ("run", "attr") or s.id is None:
            continue
        pos = s.a if s.kind == "run" else toks[s.tok].start
        if pos >= start:
            items.append((pos, 0 if s.kind == "run" else 1, s))
    for pos, _, s in sorted(items, key=lambda x: (x[0], x[1])):
        k = (s.kind, s.id)
        occ[id(s)] = "%s%d" % (s.kind[0], seen.get(k, 0))
        seen[k] = seen.get(k, 0) + 1
    for s in segs:      # head: <title> and the title/description meta tags
        if s.id is None or id(s) in occ:
            continue
        if s.kind == "run" and s.a < start:
            occ[id(s)] = "title"
        elif s.kind == "attr":
            at = dict(toks[s.tok].attrs)
            nm = at.get("name") or at.get("property") or ""
            if nm in ("description", "og:description", "twitter:description"):
                occ[id(s)] = "desc"
            elif nm in ("og:title", "twitter:title"):
                occ[id(s)] = "title"
    return occ


# ---------------------------------------------------------------- legacy import
def tag_key(tok):
    a = dict(tok.attrs)
    return (tok.tag, a.get("href"), a.get("src"), a.get("class"), a.get("data-t"), a.get("id"))


def segs_of_block(html_block):
    """Segment a single .lx block as if it were the English one."""
    fake = re.sub(r'^<div class="lx" data-l="[^"]+"(?: hidden)?>', '<div class="lx" data-l="en">', html_block, count=1)
    toks, segs = segments(fake)
    return toks, [s for s in segs if s.kind in ("run", "attr")]


def renumber(en_seg, en_toks, tr_seg, tr_toks):
    """Rewrite the placeholders of a legacy translation so that gN/xN refer to the matching English tags."""
    en_keys = [tag_key(en_toks[o]) for _, o, _ in en_seg.tags]
    used = set()
    mapping = {}
    for j, (_, o, _) in enumerate(tr_seg.tags):
        k = tag_key(tr_toks[o])
        hit = None
        for n, ek in enumerate(en_keys):
            if n not in used and ek == k:
                hit = n; break
        if hit is None:
            for n, ek in enumerate(en_keys):
                if n not in used and ek[0] == k[0]:
                    hit = n; break
        if hit is None:
            return None
        used.add(hit)
        mapping[j + 1] = hit + 1
    return re.sub(r"<(/?)([gx])(\d+)(/?)>", lambda m: "<%s%s%d%s>" % (m.group(1), m.group(2), mapping[int(m.group(3))], m.group(4)),
                  tr_seg.text)


def cmd_import_legacy(pages=None, quiet=False):
    """Align every legacy language block with the English block and store the pairs in the TM."""
    tms = {c: load_tm(c) for c in LEGACY}
    stats = {c: [0, 0, 0] for c in LEGACY}   # pairs, new, page-scoped overrides
    problems = []

    def put(c, i, scope, val, occ=None):
        tm = tms[c]
        stats[c][0] += 1
        if lookup(tm, i, scope, occ) == val:
            return
        if i not in tm:
            tm[i] = val; stats[c][1] += 1
        else:   # same English, different translation here: keep it for this one place only
            tm["%s@%s#%s" % (i, scope, occ)] = val; stats[c][2] += 1

    for page in (pages or en_pages()):
        doc = read(os.path.join(ROOT, page))
        if not has_legacy(doc):
            continue
        D, M, _ = page_data(doc)
        for c in LEGACY:
            k = L[c]["key"]
            for key, en in D["en"].items():
                if D.get(k, {}).get(key) and translatable(en):
                    put(c, sid(norm(en)), "dict", norm(D[k][key]), key)
            for f in ("title", "desc"):
                en = norm(html.unescape(M[f]["en"]))
                if M[f].get(k) and translatable(en):
                    put(c, sid(en), "/" + page, norm(html.unescape(M[f][k])), f)
        toks, root = parse(doc)
        blocks = {}
        for el in lx_elements(toks, root):
            blocks.setdefault(el.attrs["data-l"], []).append(doc[toks[el.open].start:toks[el.close].end])
        en_blocks = [segs_of_block(b) for b in blocks["en"]]
        # occurrence numbers in document order (same rule as render(): runs before attributes at one position)
        en_occ, seen = [], {}
        for et, es in en_blocks:
            items = sorted(((s.a if s.kind == "run" else et[s.tok].start, 0 if s.kind == "run" else 1, n)
                            for n, s in enumerate(es) if s.id), key=lambda x: (x[0], x[1]))
            occ = {}
            for _, _, n in items:
                k = (es[n].kind, es[n].id)
                occ[n] = "%s%d" % (k[0][0], seen.get(k, 0)); seen[k] = seen.get(k, 0) + 1
            en_occ.append(occ)
        for c in LEGACY:
            k = L[c]["key"]
            lb = blocks.get(k, [])
            if len(lb) != len(en_blocks):
                problems.append("%s %s: %d blocks vs %d" % (c, page, len(lb), len(en_blocks))); continue
            for (et, es), occ, b in zip(en_blocks, en_occ, lb):
                tt, ts = segs_of_block(b)
                if len(ts) != len(es):
                    problems.append("%s %s: %d segments vs %d" % (c, page, len(ts), len(es))); continue
                for n, (s1, s2) in enumerate(zip(es, ts)):
                    if s1.id is None or s1.kind != s2.kind or s1.attr != s2.attr:
                        continue
                    if s1.kind == "run":
                        if not s2.text:
                            continue
                        v = renumber(s1, et, s2, tt)
                        if v is None or not check_ph(s1.text, v):
                            problems.append("%s %s: tag mismatch in %s" % (c, page, s1.text[:50])); continue
                    else:
                        v = s2.text
                    if v:
                        put(c, s1.id, "/" + page, v, occ.get(n))
    for c in LEGACY:
        save_tm(c, tms[c])
    if not quiet:
        for c in LEGACY:
            print("%-8s %6d aligned pairs, %5d new, %4d page-specific" % (c, *stats[c]))
        for p in problems[:20]:
            print("  !", p)
        print("%d alignment problems" % len(problems))
    return problems


# ---------------------------------------------------------------- extraction
def page_segments(page):
    doc = normalise_en(read(os.path.join(ROOT, page)))
    D, M, _ = page_data(doc)
    toks, segs = segments(doc)
    return doc, D, toks, segs


def cmd_extract(quiet=False):
    src, pages = {}, {}
    dict_ids = []
    for page in en_pages():
        doc, D, toks, segs = page_segments(page)
        for key, v in D["en"].items():
            v = norm(v)
            if translatable(v):
                src[sid(v)] = v
                if sid(v) not in dict_ids:
                    dict_ids.append(sid(v))
        hard, soft = [], []
        for s in segs:
            if s.id:
                src[s.id] = s.text
                (soft if s.soft else hard).append(s.id)
        hard = list(dict.fromkeys(hard))
        soft = [i for i in dict.fromkeys(soft) if i not in hard]
        pages["/" + page] = {"hard": hard, "soft": soft}
    pages = {"dict": {"hard": dict_ids, "soft": []}, **pages}
    write(os.path.join(I18N, "source.json"), json.dumps(dict(sorted(src.items())), ensure_ascii=False, indent=0) + "\n")
    write(os.path.join(I18N, "pages.json"), json.dumps(pages, ensure_ascii=False, indent=0) + "\n")
    if not quiet:
        words = sum(len(v.split()) for v in src.values())
        print("%d pages, %d unique segments, %d words" % (len(pages) - 1, len(src), words))
    return src, pages


def missing_ids(tm, pages, scope):
    ent = pages[scope]
    sc = "dict" if scope == "dict" else scope
    hard = [i for i in ent["hard"] if lookup(tm, i, sc) is None]
    soft = [i for i in ent["soft"] if lookup(tm, i, sc) is None]
    return hard, soft


def availability(code, pages, tm):
    if code == "en":
        return set(p[1:] for p in pages if p != "dict")
    if missing_ids(tm, pages, "dict")[0]:
        return set()
    av = set(p[1:] for p in pages if p != "dict" and not missing_ids(tm, pages, p)[0])
    return av if "index.html" in av else set()


# ---------------------------------------------------------------- rendering
def esc_text(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\xa0", "&nbsp;")


def rebuild_tag(tok, new_attrs):
    raw = tok.raw
    for name, val in new_attrs.items():
        pat = re.compile(r'(\s%s=")([^"]*)(")' % re.escape(name))
        raw, n = pat.subn(lambda m: m.group(1) + val + m.group(3), raw, count=1)
        if not n:
            raw = re.sub(r"(/?>)$", lambda m: ' %s="%s"%s' % (name, val, m.group(1)), raw, count=1)
    return raw


def map_href(v, code, avail):
    """Root-relative-to-file href in an English page -> href valid from /<dir>/ for language code."""
    if code == "en" or re.match(r"^(?:[a-z][a-z0-9+.-]*:|//|#)", v) or v == "":
        return v
    m = re.match(r"^([^?#]*)(.*)$", v)
    path, rest = m.group(1), m.group(2)
    if path.startswith("/"):
        return v
    path = re.sub(r"^\./", "", path)
    if path.endswith(".html") and "/" not in path and path in avail:
        return path + rest
    return "../" + path + rest


def map_abs(url, code, avail):
    if code == "en" or not url.startswith(SITE + "/"):
        return url
    rest = url[len(SITE):]
    path, _, frag = rest.partition("#")
    if frag:
        return url
    page = "index.html" if path == "/" else path[1:]
    if page in avail and "/" not in page:
        return SITE + lang_url(code, page)
    return url


def ld_transform(d, tr_ld, code, avail, skip=False, site_tags=None):
    if isinstance(d, dict):
        skip2 = skip or ld_skip(d)
        o = {}
        for k, v in d.items():
            if k == "inLanguage" and d.get("@type") == "WebSite" and site_tags:
                o[k] = site_tags if len(site_tags) > 1 else site_tags[0]
            elif isinstance(v, str):
                if k == "inLanguage":
                    o[k] = L[code]["tag"]
                elif not skip2 and k in LD_TEXT_KEYS:
                    t = tr_ld(norm(v))
                    o[k] = v if t == norm(v) else t
                elif not skip2 and k != "@id" and v.startswith(SITE):
                    o[k] = map_abs(v, code, avail)
                else:
                    o[k] = v
            elif k == "inLanguage":
                o[k] = L[code]["tag"]
            else:
                o[k] = ld_transform(v, tr_ld, code, avail, skip2, site_tags)
        return o
    if isinstance(d, list):
        return [ld_transform(v, tr_ld, code, avail, skip, site_tags) for v in d]
    return d


def ld_dump(d):
    return json.dumps(d, ensure_ascii=False)


def render(doc, page, code, tm, avail, clusters):
    """Render English source doc (normalised) of page in language code. Returns (html, missing_hard_ids)."""
    toks, segs = segments(doc)
    D, M, _ = page_data(doc)
    scope = "/" + page
    missing = set()

    occ = occurrences(doc, toks, segs)

    def tr(i, text, soft=False, sc=None, seg=None):
        if i is None or code == "en":
            return text
        v = lookup(tm, i, sc or scope, occ.get(id(seg)) if seg is not None else None)
        if v is None:
            if not soft:
                missing.add(i)
            return text
        return v

    newtag = {}
    attr_tr = {}
    for s in segs:
        if s.kind == "attr":
            attr_tr.setdefault(s.tok, {})[s.attr] = tr(s.id, s.text, s.soft, seg=s)
    for i, t in enumerate(toks):
        if t.kind not in ("start", "startend"):
            continue
        at = dict(t.attrs)
        repl = {}
        if code != "en":
            for a, v in attr_tr.get(i, {}).items():
                repl[a] = html.escape(v, quote=True)
            for a in ("href", "src"):
                v = at.get(a)
                if v is None or (t.tag == "link" and at.get("rel") in ("canonical", "alternate")):
                    continue
                nv = map_href(v, code, avail)
                if nv != v:
                    repl[a] = html.escape(nv, quote=True)
        newtag[i] = rebuild_tag(t, repl) if repl else t.raw

    edits, covered = [], []
    for s in segs:
        if s.kind != "run" or code == "en":
            continue
        txt = tr(s.id, s.text, seg=s)
        pieces, pos = [], 0
        for m in PH_RE.finditer(txt):
            pieces.append(esc_text(txt[pos:m.start()]))
            ph = m.group(0)
            n = int(re.search(r"\d+", ph).group(0)) - 1
            kind, o, c = s.tags[n]
            if kind == "xe":
                pieces.append(newtag.get(o, toks[o].raw) + "".join(toks[j].raw for j in range(o + 1, c)) + toks[c].raw)
            elif ph.startswith("</"):
                pieces.append(toks[c].raw)
            else:
                pieces.append(newtag.get(o, toks[o].raw))
            pos = m.end()
        pieces.append(esc_text(txt[pos:]))
        edits.append((s.a, s.b, s.lead + "".join(pieces) + s.trail))
        covered.append((s.a, s.b))
    for i, t in enumerate(toks):
        if t.kind in ("start", "startend") and newtag[i] != t.raw:
            if not any(a <= t.start < b for a, b in covered):
                edits.append((t.start, t.end, newtag[i]))
    ld_ids = {s.text: s.id for s in segs if s.kind == "ld"}
    for i, t in enumerate(toks):
        if t.kind == "start" and t.tag == "script" and dict(t.attrs).get("type") == "application/ld+json":
            d = json.loads(toks[i + 1].raw)
            # English: text and URLs stay byte for byte; only inLanguage is set (page language; the
            # WebSite node lists every live language)
            d = ld_transform(d, (lambda v: v) if code == "en" else (lambda v: tr(ld_ids.get(v), v, True)),
                             code, avail if code != "en" else set(), site_tags=[L[c]["tag"] for c in clusters.get("index.html", ["en"])])
            new = ld_dump(d)
            if new != toks[i + 1].raw:
                edits.append((toks[i + 1].start, toks[i + 1].end, new))
    edits.sort(key=lambda e: e[0])
    res, pos = [], 0
    for a, b, txt in edits:
        if a < pos:
            raise RuntimeError("overlapping edits in %s" % page)
        res.append(doc[pos:a]); res.append(txt); pos = b
    res.append(doc[pos:])
    out = "".join(res)

    # chrome dictionary for this language
    key = L[code]["key"]
    dct = {}
    for k, v in D["en"].items():
        if code == "en" or not translatable(norm(v)):
            dct[k] = v
            continue
        t = lookup(tm, sid(norm(v)), "dict", k)
        if t is None:
            missing.add(sid(norm(v)))
        dct[k] = v if t is None else t
    if code != "en":
        def fill(m):
            k = m.group(3)
            return m.group(1) + esc_text(dct[k]) + m.group(5) if k in dct else m.group(0)
        out = re.sub(r'(<(\w+)\b[^>]*\sdata-t="([^"]+)"[^>]*>)([^<]*)(</\2>)', fill, out)
        out = out.replace('<div class="lx" data-l="en">', '<div class="lx" data-l="%s">' % key)
    title = re.search(r"<title>(.*?)</title>", out, re.S).group(1)
    desc = re.search(r'<meta name="description" content="([^"]*)"', out).group(1)
    shipped = clusters.get("index.html", ["en"])
    have = clusters.get(page, ["en"])
    alt = {}
    for c in shipped:
        tgt = page if c in have else "index.html"
        alt[L[c]["key"]] = rel_from(code, c, tgt)
    page_js = {"lang": key, "root": "../" if code != "en" else "", "alt": alt}
    i18n = {"en": D["en"]} if code == "en" else {"en": D["en"], key: dct}
    meta = {"title": {key: title}, "desc": {key: desc}}
    langs = [[L[c]["key"], L[c]["tag"], L[c]["name"]] for c in shipped]
    m = DICT_RE.search(out)
    extra = (m.group(4) or "").strip()
    script = ('<script>\nwindow.ACCSG_I18N=%s;window.ACCSG_META=%s;window.ACCSG_LANGS=%s;\n%s%s\n</script>'
              % (json.dumps(i18n, ensure_ascii=False), json.dumps(meta, ensure_ascii=False), json.dumps(langs, ensure_ascii=False),
                 (extra + "\n") if extra else "", "window.ACCSG_PAGE=%s;%s" % (json.dumps(page_js, ensure_ascii=False), REDIRECT_JS if code == "en" else "")))
    out = out[:m.start()] + script + out[m.end():]
    # the page's language is fixed now (the Score Library widget reads it)
    out = re.sub(r'\(function\(\)\{var q=new URLSearchParams\(location\.search\)\.get\("lang"\);.*?window\.ACCSG_LANG=q\|\|s\|\|"en";\}\)\(\);',
                 'window.ACCSG_LANG="%s";' % key, out, flags=re.S)
    out = re.sub(r'window\.ACCSG_LANG="[^"]*";', 'window.ACCSG_LANG="%s";' % key, out)
    if code != "en":
        out = out.replace('window.ACCSG_PDFBASE="accordion_pdfs/"', 'window.ACCSG_PDFBASE="../accordion_pdfs/"')
    opts = "".join('<option value="%s" lang="%s"%s>%s</option>' % (L[c]["key"], L[c]["tag"], " selected" if c == code else "", L[c]["name"])
                   for c in shipped)
    out = out.replace('<select id="langsel"></select>', '<select id="langsel">%s</select>' % opts, 1)
    out = head_fixups(out, code, page, have)
    return out, missing


# Root (English) pages: an old ?lang=xx link, a remembered choice or (first visit) the browser language
# sends the visitor to the static page in that language.
REDIRECT_JS = ('(function(){var P=window.ACCSG_PAGE,A=P.alt,t=null,q=null,s=null;'
               'try{q=new URLSearchParams(location.search).get("lang");}catch(e){}'
               'try{s=localStorage.getItem("accsg.lang");}catch(e){}'
               'function k(v){v=String(v||"").toLowerCase();if(A[v])return v;'
               'if(/^zh-(hant|tw|hk|mo)/.test(v))return A["zh-hant"]?"zh-hant":null;'
               'if(/^zh/.test(v))return A.zh?"zh":null;if(v==="tl")return A.fil?"fil":null;'
               'v=v.split("-")[0];return A[v]?v:null;}'
               'if(q){t=k(q);if(t){try{localStorage.setItem("accsg.lang",t);}catch(e){}}}'
               'else if(s){t=k(s);}'
               'else{var n=navigator.languages||[navigator.language||"en"];for(var i=0;i<n.length;i++){t=k(n[i]);if(t)break;}}'
               'if(t&&t!=="en"){var u=new URL(A[t],location.href);var p=new URLSearchParams(location.search);p.delete("lang");'
               'var r=p.toString();location.replace(u.pathname+(r?"?"+r:"")+location.hash);}})();')


def rel_from(code_from, code_to, page):
    """Relative href from a page of language code_from to page in language code_to."""
    up = "../" if L[code_from]["dir"] else ""
    d = L[code_to]["dir"]
    if not d:
        return up + page
    if code_to == code_from:
        return page
    return up + d + "/" + page


def head_fixups(doc, code, page, cluster):
    lg = L[code]
    url = SITE + lang_url(code, page)
    attrs = 'lang="%s"' % lg["tag"] + (' dir="rtl"' if code == "ar" else "")
    doc = re.sub(r'<html lang="[^"]*"(?: dir="rtl")?>', "<html %s>" % attrs, doc, count=1)
    doc = re.sub(r'<link rel="canonical" href="[^"]*">', '<link rel="canonical" href="%s">' % url, doc, count=1)
    alts = "\n".join('<link rel="alternate" hreflang="%s" href="%s%s">' % (L[c]["tag"], SITE, lang_url(c, page)) for c in cluster)
    alts += '\n<link rel="alternate" hreflang="x-default" href="%s%s">' % (SITE, lang_url("en", page))
    doc = re.sub(r'(?:<link rel="alternate" hreflang="[^"]*" href="[^"]*">\n?)+', alts + "\n", doc, count=1)
    doc = re.sub(r'<meta property="og:url" content="[^"]*">', '<meta property="og:url" content="%s">' % url, doc, count=1)
    doc = re.sub(r'<meta property="og:locale(?::alternate)?" content="[^"]*">\n?', "", doc)
    loc = '<meta property="og:locale" content="%s">\n' % lg["og"] + "".join(
        '<meta property="og:locale:alternate" content="%s">\n' % L[c]["og"] for c in cluster if c != code)
    doc = doc.replace('<meta name="twitter:card"', loc + '<meta name="twitter:card"', 1)
    doc = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com/css2\?family=Noto[^"]*" data-i18n-font>\n?', "", doc)
    if lg["font"]:
        doc = re.sub(r'(<link rel="stylesheet" href="(?:\.\./)?style\.css">)',
                     lambda m: '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=%s&amp;display=swap" data-i18n-font>\n%s'
                     % (lg["font"], m.group(1)), doc, count=1)
    return doc


# ---------------------------------------------------------------- commands
def cmd_todo(code, which, out=None):
    src, pages = cmd_extract(quiet=True)
    tm = load_tm(code)
    seen, lines = set(), []
    sel = ["dict"] + ["/" + p for p in en_pages()] if not which else ["dict"] + ["/" + w.lstrip("/") for w in which]
    for scope in sel:
        hard, soft = missing_ids(tm, pages, scope)
        for i in hard + soft:
            if i not in seen:
                seen.add(i)
                lines.append("%s\t%s" % (i, src[i]))
    if out:
        write(out, "\n".join(lines) + ("\n" if lines else ""))
    else:
        for ln in lines:
            print(ln)
    return lines


def check_ph(en, tr):
    return sorted(PH_RE.findall(en)) == sorted(PH_RE.findall(tr))


def cmd_merge(code, f):
    src = json.loads(read(os.path.join(I18N, "source.json")))
    tm = load_tm(code)
    bad, n = 0, 0
    for ln in read(f).splitlines():
        if not ln.strip() or "\t" not in ln:
            continue
        i, t = ln.split("\t", 1)
        i, t = i.strip(), t.strip()
        if i not in src:
            print("unknown id", i); bad += 1; continue
        if not t:
            print("empty", i); bad += 1; continue
        if not check_ph(src[i], t):
            print("placeholder mismatch", i, src[i][:60], "||", t[:60]); bad += 1; continue
        tm[i] = t; n += 1
    save_tm(code, tm)
    print("merged %d, rejected %d -> i18n/%s.json (%d entries)" % (n, bad, code, len(tm)))
    return bad


def cmd_status():
    src, pages = cmd_extract(quiet=True)
    for code in CODES[1:]:
        tm = load_tm(code)
        av = availability(code, pages, tm)
        need = set(i for k, e in pages.items() for i in e["hard"] + e["soft"])
        hard = set(i for k, e in pages.items() for i in e["hard"])
        done = set(i for i in need if i in tm)
        words = sum(len(src[i].split()) for i in need - done)
        print("%-8s %5d/%5d segments (%5d/%5d content)  %2d/%2d pages live  %6d words to go"
              % (code, len(done), len(need), len(hard & done), len(hard), len(av), len(pages) - 1, words))


def lastmod_meta():
    """Per-page sitemap data, captured once from the original sitemap.xml."""
    p = os.path.join(I18N, "sitemap-meta.json")
    if os.path.exists(p):
        return json.loads(read(p))
    s = read(os.path.join(ROOT, "sitemap.xml"))
    meta = {}
    for u in re.findall(r"<url>.*?</url>", s, re.S):
        loc = re.search(r"<loc>([^<]+)</loc>", u).group(1)
        page = "index.html" if loc == SITE + "/" else loc[len(SITE) + 1:]
        g = lambda t: (re.search(r"<%s>([^<]*)</%s>" % (t, t), u) or [None, None])[1]
        meta[page] = {"lastmod": g("lastmod"), "changefreq": g("changefreq"), "priority": g("priority"),
                      "image": g("image:loc"), "image_title": html.unescape(g("image:title") or "")}
    write(p, json.dumps(meta, ensure_ascii=False, indent=1) + "\n")
    return meta


def cmd_build():
    pages_all = en_pages()
    smeta = lastmod_meta()
    # 1) old in-page translations are moved into the TM before the English pages are normalised
    legacy_pages = [p for p in pages_all if has_legacy(read(os.path.join(ROOT, p)))]
    if legacy_pages:
        probs = cmd_import_legacy(legacy_pages, quiet=True)
        if probs:
            sys.exit("legacy import problems, refusing to strip: %s" % probs[:3])
    src, pages = cmd_extract(quiet=True)
    tms = {c: load_tm(c) for c in CODES[1:]}
    avail = {c: availability(c, pages, tms.get(c, {})) for c in CODES}
    if legacy_pages:
        lost = [c for c in LEGACY if set(legacy_pages) - avail[c]]
        if lost:
            sys.exit("refusing to strip legacy blocks: languages %s would lose pages %s"
                     % (lost, sorted(set(legacy_pages) - avail[lost[0]])[:5]))
    clusters = {p: [c for c in CODES if p in avail[c]] for p in pages_all}
    written = []
    for page in pages_all:
        base = normalise_en(read(os.path.join(ROOT, page)))
        for c in CODES:
            if page not in avail[c]:
                continue
            out, missing = render(base, page, c, tms.get(c, {}), avail[c], clusters)
            if missing:
                raise RuntimeError("%s %s missing %d" % (c, page, len(missing)))
            write(lang_file(c, page), out)
            written.append(lang_file(c, page))
    stale = []
    for c in CODES[1:]:
        for f in glob.glob(os.path.join(ROOT, L[c]["dir"], "*.html")):
            if f not in written:
                if "--prune" in sys.argv:
                    os.remove(f)
                else:
                    stale.append(os.path.relpath(f, ROOT))
    if stale:
        sys.exit("refusing to drop %d existing language pages (missing translations?): %s — translate them or rerun with --prune"
                 % (len(stale), ", ".join(stale[:5])))
    write_sitemaps(pages_all, avail, clusters, smeta)
    write_robots(avail)
    write_llms(avail)
    print("built %d pages; languages live: %s" % (len(written), ", ".join("%s(%d)" % (c, len(avail[c])) for c in CODES if avail[c])))


def page_title(code, page):
    h = read(lang_file(code, page))
    return html.unescape(re.search(r"<title>(.*?)</title>", h, re.S).group(1))


def write_sitemaps(pages_all, avail, clusters, smeta):
    files = []
    for c in CODES:
        if not avail[c]:
            continue
        rows = []
        for page in pages_all:
            if page not in avail[c]:
                continue
            sm = smeta.get(page, {})
            loc = SITE + lang_url(c, page)
            alts = "".join('<xhtml:link rel="alternate" hreflang="%s" href="%s%s"/>' % (L[x]["tag"], SITE, lang_url(x, page)) for x in clusters[page])
            alts += '<xhtml:link rel="alternate" hreflang="x-default" href="%s%s"/>' % (SITE, lang_url("en", page))
            img = ""
            if sm.get("image"):
                it = sm.get("image_title") if c == "en" else page_title(c, page)
                img = "<image:image><image:loc>%s</image:loc><image:title>%s</image:title></image:image>" % (sm["image"], html.escape(it, quote=False))
            rows.append("<url><loc>%s</loc>%s%s<lastmod>%s</lastmod><changefreq>%s</changefreq><priority>%s</priority></url>"
                        % (loc, alts, img, sm.get("lastmod") or TODAY, sm.get("changefreq") or "monthly", sm.get("priority") or "0.6"))
        name = "sitemap-%s.xml" % c
        write(os.path.join(ROOT, name), '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
              'xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'
              + "\n".join(rows) + "\n</urlset>\n")
        files.append(name)
    for f in glob.glob(os.path.join(ROOT, "sitemap-*.xml")):
        if os.path.basename(f) not in files:
            os.remove(f)
    idx = '<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(
        "<sitemap><loc>%s/%s</loc><lastmod>%s</lastmod></sitemap>" % (SITE, f, TODAY) for f in files) + "\n</sitemapindex>\n"
    write(os.path.join(ROOT, "sitemap.xml"), idx)


def write_robots(avail):
    p = os.path.join(ROOT, "robots.txt")
    t = read(p)
    lines = ["Sitemap: %s/sitemap.xml" % SITE] + ["Sitemap: %s/sitemap-%s.xml" % (SITE, c) for c in CODES if avail[c]]
    t = re.sub(r"(?:^Sitemap: .*\n)+", "\n".join(lines) + "\n", t, count=1, flags=re.M)
    write(p, t)


def write_llms(avail):
    live = [c for c in CODES if avail[c]]
    line = ("Languages: English at the root URLs; every translated page is a static page in its own folder — "
            + ", ".join("%s %s%s" % (L[c]["name"], SITE, lang_url(c, "index.html")) for c in live[1:])
            + ". Same file names in every folder (e.g. /es/about.html). Old ?lang=xx links redirect to these pages.")
    for name in ("llms.txt", "llms-full.txt"):
        p = os.path.join(ROOT, name)
        if os.path.exists(p):
            t = read(p)
            t2 = re.sub(r"^Languages: .*$", line, t, count=1, flags=re.M)
            if t2 != t:
                write(p, t2)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(0)
    if a[0] == "import-legacy":
        cmd_import_legacy()
    elif a[0] == "extract":
        cmd_extract()
    elif a[0] == "todo":
        cmd_todo(a[1], a[2:])
    elif a[0] == "merge":
        sys.exit(1 if cmd_merge(a[1], a[2]) else 0)
    elif a[0] == "status":
        cmd_status()
    elif a[0] == "build":
        cmd_build()
    else:
        print(__doc__)
