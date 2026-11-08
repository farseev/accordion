accordion.sg — static site
==========================

Flat by design: every page is a .html file in this folder, every picture is in
images/, and there is nothing to build or install. Copy the contents of this
folder into the repo root, commit, and it is live. Opening index.html from disk
works too.

What is here
------------
  *.html                57 English pages + 404.html + thank-you.html, in the root
  <lang>/*.html         the same 57 pages per language (generated, see Languages)
  i18n/  tools/         translation memory; i18n.py (build) and check_site.py
  images/               photos, favicons, social cards, images/products/
  style.css script.js   site styles and behaviour
  scores.css scores.js scores-data.js    the 743-score library widget
  sitemap.xml robots.txt llms.txt llms-full.txt site.webmanifest
  _redirects vercel.json                 host redirect rules

There are no per-page folders. /shop-piano/ still works because _redirects
handles Netlify, vercel.json handles Vercel, and 404.html rewrites the URL on
GitHub Pages, so old indexed links keep resolving either way.

Links and hosting
-----------------
Navigation, images, CSS and JS are relative URLs; the canonical tag, the
hreflang alternates, the og:image social card and the schema.org data are
absolute (https://accordion.sg/...). The site therefore renders correctly from any host, from any
sub-folder, and from a file:// path, with nothing to configure.

Two files must carry the domain, because their specs require absolute URLs:
sitemap.xml and robots.txt. llms.txt does too, since an AI citing the site
needs a resolvable address. If you move the site, change SITE on line 8 of
build_flat.py and rebuild, or edit those three files by hand.

Social previews
---------------
Every page and every article declares og:image and twitter:image, chosen from
the cards already in images/: og-home, og-about, og-trio, og-shop, og-lessons,
og-library, og-blog. Articles use the card that matches their subject — tango
articles get og-trio, theory gets og-library, buying guides get og-shop, double
bass gets og-about, accordion gets og-home. Each page also carries its own meta
description and meta keywords, and the sitemap repeats the card with a caption.

Your score PDFs
---------------
Leave accordion_pdfs/ in the repo exactly as it is — this package deliberately
does not contain it, so it cannot overwrite your files. The library reads from
accordion_pdfs/ next to index.html, using the filenames in scores-data.js.

Languages
---------
English pages live in the root and are the source. Every other language is a
real static page with the same file name in its own folder:

  /es/ /fr/ /de/ /it/ /pt/ /ru/ /zh-hans/ /ja/ /ko/ /ms/ /ta/        live (all 57 pages)
  /zh-hant/ /th/ /vi/ /id/ /hi/ /fil/ /ar/                           appear as soon as
                                                                    they are translated

Each language page has its own <html lang> (dir="rtl" for Arabic), a
self-canonical, the full hreflang cluster + x-default, translated title,
description, Open Graph text and JSON-LD (products, prices and people are
never changed), and per-language sitemaps (sitemap.xml is the index). The
header picker links the versions together and remembers the choice; it sends
the GA4 event language_switch. Old ?lang=xx links on English URLs redirect to
the static page (?lang=zh still means Simplified Chinese).

Translations are kept in i18n/<code>.json (translation memory, one entry per
English sentence/paragraph, keyed by a hash). The 11 languages that used to be
embedded in every page were imported from those pages, so nothing was
re-translated. tools/i18n.py does the rest (standard-library Python):

  python3 tools/i18n.py status                 coverage per language
  python3 tools/i18n.py todo th > th.tsv       untranslated text:  id<TAB>English
  python3 tools/i18n.py merge th th.out.tsv    add translations (id<TAB>translation)
  python3 tools/i18n.py build                  rebuild English + every language page
  python3 tools/check_site.py                  must end with "0 errors"

Keep the <g1>…</g1> and <x1/> placeholders in translations. A page goes live
in a language only when its whole text is translated; until then that
language links to the English page.

After editing an English page (text inside <div class="lx" data-l="en">,
the title/description, or the ACCSG_I18N dictionary), run build: changed
sentences show up in `todo` for every language, and pages whose new text is
not yet translated are kept back (build refuses to delete an existing
language page unless you add --prune).

The one file to edit
--------------------
script.js, top of file:
  SITE.whatsapp   the number every enquiry button uses (+65 9122 7009)
  SITE.email      the contact address
  STRIPE_LINKS    one live Stripe payment link per accordion model
  CATALOGUE       the 14 instruments: photo, name, tier, specs, prices
Change a price in CATALOGUE and the card updates; change a Stripe link and the
ORDER button follows it. ASK FIRST always opens WhatsApp.

Analytics
---------
Google Analytics G-MDTZJXNQ59 on every page, including 404.html, which also
fires a page_not_found event carrying the bad URL.

Rebuilding (optional)
---------------------
The English pages in this folder are now the source: edit them directly and
run `python3 tools/i18n.py build` to regenerate the language folders,
sitemaps, robots.txt Sitemap lines and the Languages line in llms.txt. The
old generator (build_flat.py with body-<lang>/ and content-<lang>/) is no
longer needed; its translations are in i18n/<code>.json.
