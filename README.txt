accordion.sg — static site
==========================

Flat by design: every page is a .html file in this folder, every picture is in
images/, and there is nothing to build or install. Copy the contents of this
folder into the repo root, commit, and it is live. Opening index.html from disk
works too.

What is here
------------
  *.html                57 pages + 404.html, all in the root
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
Every URL inside the HTML is relative — navigation, images, CSS and JS, the
canonical tag, the hreflang alternates, the og:image social card and the
schema.org data. The site therefore renders correctly from any host, from any
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
Twelve, all inside each HTML file: en, es, fr, de, it, pt, ru, zh, ja, ko, ms, ta.
Add ?lang=xx to any URL to force one; the header picker remembers the choice.
All 50 journal articles are translated into all twelve.

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
Only if you want to change the source rather than the output. The generator is
in the separate source package: build_flat.py plus body/, body-<lang>/,
content/, content-<lang>/, i18n/ and assets/. Run `python3 build_flat.py` and it
rewrites this folder, sitemap.xml, robots.txt and llms.txt included.
