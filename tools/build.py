"""Genera il sito statico in dist/.

Uso: python tools/build.py
Anteprima: python -m http.server 8000 --directory dist
"""
import datetime as dt
import html
import json
import math
import re
import shutil
import unicodedata
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
DIST = ROOT / "dist"
import sys as _sys
PREVIEW = "--preview" in _sys.argv
PREVIEW_URL = "https://robertodifabioeco-sys.github.io/sbl"
ROOT_PATH = "/sbl/" if PREVIEW else "/"
if PREVIEW:
    DIST = ROOT / "dist-preview"
_ABS = re.compile(r'((?:href|src|action)=")/(?!/)')


def prefix_paths(html_text):
    """Con l'anteprima in sottocartella, i percorsi assoluti /x diventano /sbl/x."""
    if ROOT_PATH == "/":
        return html_text
    html_text = _ABS.sub(lambda m: m.group(1) + ROOT_PATH, html_text)
    return html_text.replace("url=/", "url=" + ROOT_PATH)
CONTENT = ROOT / "content"
FONTS = ROOT / "tools" / "fonts"
LANGS = ("it", "en")
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
BLUE, RED, NAVY = "#0D4B8C", "#AE0708", "#0A2240"

site = json.loads((CONTENT / "site.json").read_text(encoding="utf-8"))
PATHS = site["paths"]


def ascii_slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s


def text_of(h):
    return html.unescape(re.sub(r"<[^>]+>", " ", h or ""))


def excerpt(blocks, limit=230):
    """Attacco dell'articolo: le prime frasi del primo paragrafo vero, parole dell'autore."""
    for b in blocks:
        if b["type"] != "p":
            continue
        txt = re.sub(r"\s+", " ", text_of(b["html"])).strip()
        if len(txt) < 90 or txt.endswith(":"):
            continue
        if len(txt) <= limit:
            return txt
        sents = re.split(r"(?<=[.!?»”])\s+", txt)
        out = ""
        for snt in sents:
            if len(out) + len(snt) + 1 > limit:
                break
            out = (out + " " + snt).strip()
        if len(out) >= 80:
            return out
        cut = txt[:limit].rsplit(" ", 1)[0].rstrip(",;:–-")
        return cut + "…"
    return ""


def date_h(d, lang):
    return f"{d.day} {MESI[d.month - 1]} {d.year}" if lang == "it" else f"{d.day} {MONTHS[d.month - 1]} {d.year}"


# ——— immagini ———

def out_img(rel):
    p = DIST / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def fresh(src, dst):
    return dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime


def save_resized(src, rel, max_w, fmt="WEBP", quality=80):
    dst = out_img(rel)
    if fresh(src, dst):
        with Image.open(dst) as im:
            return im.size
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)
        if getattr(im, "is_animated", False):
            im.seek(0)
        has_alpha = im.mode in ("RGBA", "LA", "P")
        im = im.convert("RGBA" if has_alpha and fmt == "WEBP" else "RGB")
        if im.width > max_w:
            im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
        im.save(dst, fmt, quality=quality, method=6) if fmt == "WEBP" else im.save(dst, fmt, quality=quality, optimize=True, progressive=True)
        return im.size


def save_crop(src, rel, size, fmt="JPEG", quality=84):
    dst = out_img(rel)
    if fresh(src, dst):
        return
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        im = ImageOps.fit(im, size, Image.LANCZOS, centering=(0.5, 0.4))
        im.save(dst, fmt, quality=quality, optimize=True) if fmt == "JPEG" else im.save(dst, fmt, quality=quality, method=6)


def wrap_text(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def make_cover(title, cat_label, seed, dst):
    """Copertina grafica per gli articoli senza immagine: fondo blu/navy, motivo a quadrati SBL, titolo serif."""
    W, H = 1600, 1000
    rnd = sum(map(ord, seed))
    bg = [NAVY, BLUE][rnd % 2]
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im, "RGBA")
    # motivo: griglia di quadrati, alcuni pieni (rosso/bianco/blu), nella fascia destra
    cell, gap = 54, 10
    cols, rows = 9, 15
    x0 = W - cols * (cell + gap) + gap - 40
    for r in range(rows):
        for c in range(cols):
            k = (rnd * 31 + r * 17 + c * 13 + r * c * 7) % 23
            x = x0 + c * (cell + gap)
            y = -20 + r * (cell + gap)
            if k in (0, 5):
                col = (174, 7, 8, 235)
            elif k in (3, 11):
                col = (255, 255, 255, 220)
            elif k in (7, 14, 19):
                col = (13, 75, 140, 255) if bg == NAVY else (10, 34, 64, 255)
            else:
                col = (255, 255, 255, 18)
            d.rectangle([x, y, x + cell, y + cell], fill=col)
    # velatura a sinistra per leggibilità
    grad = Image.new("L", (W, 1))
    for x in range(W):
        grad.putpixel((x, 0), int(255 * max(0, min(1, (x - 700) / 600))))
    veil = Image.new("RGB", (W, H), bg)
    im = Image.composite(im, veil, grad.resize((W, H)))
    d = ImageDraw.Draw(im, "RGBA")
    # etichetta categoria
    fk = ImageFont.truetype(str(FONTS / "InterBold.ttf"), 26)
    label = cat_label.upper()
    lw = d.textlength(label, font=fk) + 44
    d.rectangle([90, 110, 90 + lw, 162], fill=RED)
    d.text((112, 121), label, font=fk, fill="white")
    # titolo
    size = 92
    while True:
        ft = ImageFont.truetype(str(FONTS / "SourceSerif.ttf"), size)
        lines = wrap_text(d, title, ft, 900)
        if len(lines) <= 5 or size <= 54:
            break
        size -= 6
    y = 230
    for ln in lines[:6]:
        d.text((90, y), ln, font=ft, fill="white")
        y += int(size * 1.16)
    # firma
    fs = ImageFont.truetype(str(FONTS / "Inter.ttf"), 24)
    d.rectangle([90, H - 118, 90 + 3 * 22 + 8, H - 96], fill=None)
    for i, col in enumerate((BLUE if bg == NAVY else NAVY, RED, "white")):
        d.rectangle([90 + i * 26, H - 120, 90 + i * 26 + 20, H - 100], fill=col)
    d.text((180, H - 124), "STUDENTI BOCCONIANI LIBERALI · MILTON FRIEDMAN SOCIETY", font=fs, fill=(255, 255, 255, 200))
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, "PNG")


# ——— contenuti ———

def load_articles():
    raw = json.loads((CONTENT / "articles_raw.json").read_text(encoding="utf-8"))
    overrides = json.loads((CONTENT / "overrides.json").read_text(encoding="utf-8")) if (CONTENT / "overrides.json").exists() else {}
    out = []
    missing = []
    for p in raw:
        trf = CONTENT / "tr" / f"{p['slug']}.json"
        if not trf.exists():
            missing.append(p["slug"])
            continue
        tr = json.loads(trf.read_text(encoding="utf-8"))
        ov = overrides.get(p["slug"], {})
        slug = ascii_slug(p["slug"])
        d = dt.datetime.fromisoformat(p["published"].replace("Z", "+00:00"))
        orig, other = tr["orig_lang"], ("en" if tr["orig_lang"] == "it" else "it")
        drop = set(tr.get("drop_blocks", [])) | set(ov.get("drop", []))
        cat = ov.get("category", tr["category"])
        a = {"slug": slug, "old_slug": p["slug"], "author": ov.get("author", tr.get("author", "")), "category": cat,
             "orig_lang": orig, "date": d, "date_iso": d.date().isoformat(),
             "date_h": {l: date_h(d, l) for l in LANGS}, "v": {}}
        # immagine principale
        hero_src = None
        if p.get("hero_local") and not ov.get("cover"):
            hero_src = SRC / p["hero_local"]
        words = 0
        for lang in LANGS:
            blocks = []
            for i, b in enumerate(p["blocks"]):
                if i in drop:
                    continue
                if lang == orig:
                    nb = dict(b)
                else:
                    t = tr["blocks_tr"][i]
                    nb = dict(b)
                    if b["type"] == "image":
                        nb["caption"] = t or ""
                    elif b["type"] in ("ul", "ol"):
                        nb["items"] = t
                    else:
                        nb["html"] = t
                if nb["type"] == "image":
                    src = SRC / b["local"]
                    rel = f"img/a/{slug}/{Path(b['local']).stem}.webp"
                    w, h = save_resized(src, rel, 1440)
                    nb.update(local=rel, w=w, h=h)
                    # salta un'immagine identica alla copertina in testa al corpo
                    if hero_src and src == hero_src and not blocks:
                        continue
                blocks.append(nb)
            for nb in blocks:
                if nb["type"] == "p":
                    first = text_of(nb["html"]).lstrip()[:1]
                    nb["dropcap"] = first.isalpha() and len(text_of(nb["html"])) > 180
                    break
            title = p["title"] if lang == orig else tr["title_tr"]
            title = ov.get("title", {}).get(lang, title)
            title = re.sub(r"\s+", " ", title).strip().rstrip(".").strip()
            if lang == orig:
                words = sum(len(text_of(b.get("html", "") or " ".join(b.get("items", []) or [])).split()) for b in blocks)
            a["v"][lang] = {"title": title.strip(), "dek": ov.get("dek", {}).get(lang) or excerpt(blocks) or tr["dek"][lang].strip(), "blocks": blocks,
                            "path": f"{PATHS['articles'][lang]}{slug}/"}
        a["minutes"] = max(1, math.ceil(words / 220))
        cats = site["categories"]
        for lang in LANGS:
            v = a["v"][lang]
            if hero_src:
                v["image"] = f"img/a/{slug}/hero.webp"
                save_resized(hero_src, v["image"], 1600)
                v["thumb"] = f"img/a/{slug}/thumb.webp"
                save_crop(hero_src, v["thumb"], (800, 500), fmt="WEBP", quality=78)
                v["og"] = f"img/a/{slug}/og.jpg"
                save_crop(hero_src, v["og"], (1200, 630))
            else:
                cover = ROOT / "build-cache" / "covers" / f"{slug}-{lang}.png"
                key = json.dumps([v["title"], cats[cat][lang]], ensure_ascii=False)
                keyf = cover.with_suffix(".key")
                if not cover.exists() or not keyf.exists() or keyf.read_text(encoding="utf-8") != key:
                    make_cover(v["title"], cats[cat][lang], slug, cover)
                    keyf.write_text(key, encoding="utf-8")
                v["image"] = f"img/a/{slug}/cover-{lang}.webp"
                save_resized(cover, v["image"], 1600, quality=86)
                v["thumb"] = f"img/a/{slug}/cover-{lang}-thumb.webp"
                save_crop(cover, v["thumb"], (800, 500), fmt="WEBP", quality=82)
                v["og"] = f"img/a/{slug}/cover-{lang}-og.jpg"
                save_crop(cover, v["og"], (1200, 630))
        out.append(a)
    out.sort(key=lambda a: a["date"], reverse=True)
    return out, missing


def icon_factory():
    cache = {}

    def icon(name):
        if name not in cache:
            s = (ROOT / "tools" / "icons" / f"{name}.svg").read_text(encoding="utf-8")
            s = re.sub(r"<title>.*?</title>", "", s)
            s = s.replace("<svg ", '<svg aria-hidden="true" focusable="false" ', 1)
            cache[name] = Markup(s)
        return cache[name]
    return icon


def clean_author(a):
    a = re.sub(r"<[^>]+>", "", a or "")
    a = html.unescape(a).strip()
    return a


def main():
    if DIST.exists():
        for p in DIST.iterdir():
            if p.name == "img":
                continue  # le immagini elaborate restano in cache
            shutil.rmtree(p) if p.is_dir() else p.unlink()
    DIST.mkdir(exist_ok=True)
    if PREVIEW and not (DIST / "img").exists() and (ROOT / "dist" / "img").exists():
        shutil.copytree(ROOT / "dist" / "img", DIST / "img")  # riusa le immagini gia' elaborate
    for sub in ("css", "js", "fonts"):
        shutil.copytree(SRC / sub, DIST / sub, dirs_exist_ok=True)
    for f in ("sbl-mark.svg", "sbl-mark.png", "favicon.svg", "icon-192.png", "icon-512.png", "apple-touch-icon.png", "og-default.jpg"):
        shutil.copy2(SRC / "img" / f, out_img(f"img/{f}"))
    shutil.copy2(SRC / "favicon.ico", DIST / "favicon.ico")
    for f in (SRC / "img" / "thinkers").glob("*.jpg"):
        save_resized(f, f"img/thinkers/{f.name}", 900, fmt="JPEG", quality=82)
    for f in (SRC / "img" / "events").glob("*.jpg"):
        save_resized(f, f"img/events/{f.name}", 1400, fmt="JPEG", quality=82)
    for f in (SRC / "img" / "site").glob("*.jpg"):
        save_resized(f, f"img/site/{f.name}", 1600, fmt="JPEG", quality=82)

    articles, missing = load_articles()
    if missing:
        print(f"ATTENZIONE: {len(missing)} articoli senza traduzione, esclusi: {missing}")
    thinkers = json.loads((CONTENT / "thinkers.json").read_text(encoding="utf-8"))
    for th in thinkers:
        th["author_clean"] = clean_author(th.get("author", ""))
    events = json.loads((CONTENT / "events.json").read_text(encoding="utf-8"))
    quotes = json.loads((CONTENT / "quotes.json").read_text(encoding="utf-8"))
    books = json.loads((CONTENT / "books.json").read_text(encoding="utf-8"))
    by_cat = {c: [a for a in articles if a["category"] == c] for c in site["categories"]}
    top = {id(a) for a in articles[:4]}
    by_cat_home = {c: [a for a in v if id(a) not in top] for c, v in by_cat.items()}
    version = dt.datetime.now().strftime("%Y%m%d%H%M")
    year = dt.date.today().year
    base = PREVIEW_URL if PREVIEW else site["base_url"].rstrip("/")

    env = Environment(loader=FileSystemLoader(ROOT / "tools" / "templates"), autoescape=True, trim_blocks=True, lstrip_blocks=True)
    env.globals.update(root=ROOT_PATH, abs=lambda p: f"{base}/{p}", icon=icon_factory(), site=site, paths=PATHS, cats=site["categories"],
                       version=version, year=year)
    sitemap = []

    def render(tpl, path, lang, alternates, **ctx):
        t = site["t"][lang]
        org = {"@context": "https://schema.org", "@type": "Organization", "name": "Studenti Bocconiani Liberali – Milton Friedman Society",
               "alternateName": ["SBL", "Milton Friedman Society", "Friedman Society"], "url": f"{base}/",
               "logo": f"{base}/img/icon-512.png", "email": site["email"], "foundingDate": str(site["founded"]),
               "sameAs": list(site["social"].values())}
        ctx.setdefault("jsonld", [org])
        ctx.setdefault("page_desc", t["site_desc"])
        out = env.get_template(tpl).render(lang=lang, t=t, path=path, alternates=alternates, **ctx)
        f = DIST / path / "index.html" if (path == "" or path.endswith("/")) else DIST / path
        f.parent.mkdir(parents=True, exist_ok=True)
        if PREVIEW:
            out = out.replace('<meta name="viewport"', '<meta name="robots" content="noindex, nofollow">\n<meta name="viewport"', 1)
        f.write_text(prefix_paths(out), encoding="utf-8")
        if tpl != "404.html":
            sitemap.append((path, alternates))

    def suffix(lang):
        return "SBL – Milton Friedman Society"

    pages = [("home", "home.html"), ("articles", "articles.html"), ("events", "events.html"), ("thinkers", "thinkers.html"),
             ("about", "about.html"), ("contact", "contact.html"), ("credits", "credits.html"),
             ("compass", "compass.html"), ("privacy", "privacy.html")]
    compass = json.loads((CONTENT / "compass.json").read_text(encoding="utf-8"))
    th_by_id = {th["id"]: th for th in thinkers}

    def compass_js(lang):
        t = site["t"][lang]
        def tx(v):
            return v[lang] if isinstance(v, dict) else v
        return {
            "lang": lang,
            "questions": [{"axis": q["axis"], "sign": q["sign"], "text": q[lang]} for q in compass["questions"]],
            "profiles": {k: {"name": v["name"][lang], "text": v["text"][lang],
                             "books": [{"t": tx(b["t"]), "a": tx(b["a"])} for b in v["books"]],
                             "thinker": {"name": th_by_id[v["thinker"]]["name"], "img": f"{ROOT_PATH}img/thinkers/{v['thinker']}.jpg",
                                         "quote": th_by_id[v["thinker"]]["quote"][lang],
                                         "url": f"{ROOT_PATH}{PATHS['thinkers'][lang]}#{v['thinker']}"}}
                         for k, v in compass["profiles"].items()},
            "form": site["compass_form"],
            "share_text": t["compass_share_text"],
            "share_url": f"{base}/{PATHS['compass'][lang]}",
            "q_open": "«" if lang == "it" else "“", "q_close": "»" if lang == "it" else "”",
        }
    friedman = next(th for th in thinkers if th["id"] == "friedman")
    for lang in LANGS:
        t = site["t"][lang]
        alts = {k: {l: PATHS[k][l] for l in LANGS} for k, _ in pages}
        for key, tpl in pages:
            label = {"credits": t["credits_title"], "privacy": t["privacy_title"], "compass": t["compass_title"]}.get(key) or t.get("nav_" + key, "")
            title = f"{t['site_name']} – {t['site_sub']}" if key == "home" else f"{label} | {suffix(lang)}"
            desc = {"articles": t["articles_intro"], "events": t["events_page_intro"], "thinkers": t["thinkers_page_intro"],
                    "about": t["about_lead"], "contact": t["contact_intro"], "compass": t["compass_intro"]}.get(key, t["site_desc"])
            render(tpl, PATHS[key][lang], lang, alts[key], page_title=title, page_desc=desc, section=key,
                   articles=articles, featured=articles[0], latest=articles[1:4], by_cat=by_cat_home, thinkers=thinkers,
                   events=events, n_articles=len(articles), friedman=friedman, quotes=quotes, compass=compass, compass_js=compass_js(lang), books=books)
        for i, a in enumerate(articles):
            v = a["v"][lang]
            same = [r for r in by_cat[a["category"]] if r is not a]
            idx = by_cat[a["category"]].index(a)
            related = (same[idx:idx + 3] + same[:3])[:3] if same else articles[:3]
            ld = {"@context": "https://schema.org", "@type": "Article", "headline": v["title"][:110], "description": v["dek"],
                  "image": [f"{base}/{v['og']}"], "datePublished": a["date"].isoformat(), "inLanguage": lang,
                  "author": [{"@type": "Person", "name": n.strip()} for n in re.split(r",| e | and ", a["author"]) if n.strip()] or {"@type": "Organization", "name": "SBL – Milton Friedman Society"},
                  "publisher": {"@type": "Organization", "name": "Studenti Bocconiani Liberali – Milton Friedman Society", "logo": {"@type": "ImageObject", "url": f"{base}/img/icon-512.png"}},
                  "mainEntityOfPage": f"{base}/{v['path']}"}
            if a["orig_lang"] != lang:
                ld["translationOfWork"] = {"@id": f"{base}/{a['v'][a['orig_lang']]['path']}"}
            crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{base}/{PATHS['home'][lang]}"},
                {"@type": "ListItem", "position": 2, "name": t["nav_articles"], "item": f"{base}/{PATHS['articles'][lang]}"},
                {"@type": "ListItem", "position": 3, "name": v["title"]}]}
            render("article.html", v["path"], lang, {l: a["v"][l]["path"] for l in LANGS}, page_title=f"{v['title']} | {suffix(lang)}",
                   page_desc=v["dek"], og_type="article", og_title=v["title"], og_image=v["og"], section="articles", a=a,
                   related=related, jsonld=[ld, crumbs], quote=quotes[i % len(quotes)])
    # 404 (GitHub Pages usa /404.html)
    render("404.html", "404.html", "it", {"it": "", "en": "en/"}, page_title=f"404 | {suffix('it')}", section="")

    # Reindirizzamenti dai vecchi indirizzi Wix
    redirects = {"articles": "articoli/", "events": "eventi/", "about-us": "chi-siamo/", "contact": "contatti/", "servicesnumbered": ""}
    for c in site["categories"]:
        redirects[f"articles/categories/{c}"] = f"articoli/#{c}"
    for a in articles:
        redirects[f"post/{a['old_slug']}"] = a["v"][a["orig_lang"]]["path"]
        if ascii_slug(a["old_slug"]) != a["old_slug"]:
            redirects[f"post/{ascii_slug(a['old_slug'])}"] = a["v"][a["orig_lang"]]["path"]
    for old, new in redirects.items():
        f = DIST / old / "index.html"
        f.parent.mkdir(parents=True, exist_ok=True)
        url = f"{base}/{new}"
        f.write_text(prefix_paths(f'<!doctype html><html lang="it"><head><meta charset="utf-8"><title>SBL – Milton Friedman Society</title>'
                     f'<link rel="canonical" href="{url}"><meta name="robots" content="noindex">'
                     f'<meta http-equiv="refresh" content="0; url=/{new}"></head>'
                     f'<body><a href="/{new}">{url}</a></body></html>'), encoding="utf-8")

    # sitemap, robots, manifest, CNAME
    today = dt.date.today().isoformat()
    xs = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for path, alts in sitemap:
        xs.append(f"<url><loc>{base}/{path}</loc><lastmod>{today}</lastmod>")
        for l, p in alts.items():
            xs.append(f'<xhtml:link rel="alternate" hreflang="{l}" href="{base}/{p}"/>')
        xs.append("</url>")
    xs.append("</urlset>")
    (DIST / "sitemap.xml").write_text("\n".join(xs), encoding="utf-8")
    (DIST / "robots.txt").write_text("User-agent: *\nDisallow: /\n" if PREVIEW else f"User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n", encoding="utf-8")
    (DIST / "site.webmanifest").write_text(json.dumps({
        "name": "SBL – Milton Friedman Society", "short_name": "SBL", "start_url": ROOT_PATH, "display": "standalone",
        "background_color": "#ffffff", "theme_color": "#0a2240",
        "icons": [{"src": f"{ROOT_PATH}img/icon-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": f"{ROOT_PATH}img/icon-512.png", "sizes": "512x512", "type": "image/png"}]}, indent=1), encoding="utf-8")
    if PREVIEW:
        (DIST / "CNAME").unlink(missing_ok=True)
    else:
        (DIST / "CNAME").write_text("friedmansociety.com\n", encoding="utf-8")
    (DIST / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Sito generato: {len(articles)} articoli, {len(sitemap)} pagine in sitemap, {len(redirects)} redirect")


if __name__ == "__main__":
    main()
