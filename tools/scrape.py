"""Scarica tutti gli articoli dal vecchio sito Wix in content/articles_raw.json
e le immagini in src/img/articles/<slug>/.

Uso: python tools/scrape.py
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

BASE = "https://www.friedmansociety.com"
ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "content" / "articles_raw.json"
IMG_DIR = ROOT / "src" / "img" / "articles"
UA = {"User-Agent": "Mozilla/5.0 (SBL site migration)"}

ALLOWED_INLINE = {"strong": "strong", "b": "strong", "em": "em", "i": "em", "u": "u", "a": "a", "br": "br", "sup": "sup", "sub": "sub"}


def get(url, binary=False):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            return data if binary else data.decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            if attempt == 3:
                raise
            time.sleep(2 + attempt * 2)


def original_wix_image(src):
    """Da un URL Wix ridimensionato ricava l'originale."""
    m = re.search(r"static\.wixstatic\.com/media/([^/]+)", src or "")
    if not m:
        return None
    return f"https://static.wixstatic.com/media/{m.group(1)}"


def inline_html(node):
    """Converte i figli di un nodo in HTML inline ripulito."""
    out = []
    for ch in node.children:
        if isinstance(ch, NavigableString):
            out.append(escape(str(ch)))
        elif isinstance(ch, Tag):
            name = ch.name.lower()
            # Wix usa span con font-weight/style per grassetto e corsivo
            style = (ch.get("style") or "").replace(" ", "")
            inner = inline_html(ch)
            if name == "br":
                out.append("<br>")
            elif name == "a" and ch.get("href"):
                href = ch["href"]
                out.append(f'<a href="{escape(href)}">{inner}</a>')
            elif name in ALLOWED_INLINE and name != "a":
                tag = ALLOWED_INLINE[name]
                out.append(f"<{tag}>{inner}</{tag}>")
            elif "font-weight:bold" in style or "font-weight:700" in style:
                out.append(f"<strong>{inner}</strong>")
            elif "font-style:italic" in style:
                out.append(f"<em>{inner}</em>")
            else:
                out.append(inner)
    html = "".join(out)
    html = re.sub(r"<(strong|em|u)>\s*</\1>", "", html)
    return html


def escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def text_of(html):
    return re.sub(r"<[^>]+>", "", html).replace("&nbsp;", " ").strip()


BLOCK_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "blockquote", "pre", "figure"]


def parse_content(cv):
    """Contenuto Wix (content-viewer) -> lista di blocchi nostri, in ordine."""
    res = []
    for el in cv.find_all(BLOCK_TAGS):
        # salta gli elementi annidati dentro un altro blocco (p dentro li, img dentro figure...)
        anc = []
        for par in el.parents:
            if par is cv:
                break
            anc.append(par.name)
        if any(a in BLOCK_TAGS for a in anc):
            continue
        name = el.name
        if name == "figure":
            img = el.find("img")
            src = original_wix_image(img.get("src") if img else "")
            cap = el.find("figcaption")
            if src:
                res.append({"type": "image", "src": src, "caption": text_of(inline_html(cap)) if cap else ""})
        elif name in ("ul", "ol"):
            items = [inline_html(li).strip() for li in el.find_all("li", recursive=False)]
            items = [i for i in items if text_of(i)]
            if items:
                res.append({"type": name, "items": items})
        elif name == "blockquote":
            html = inline_html(el).strip()
            if text_of(html):
                res.append({"type": "quote", "html": html})
        elif name.startswith("h"):
            html = inline_html(el).strip()
            if text_of(html):
                res.append({"type": "h", "level": int(name[1]), "html": html})
        else:
            html = inline_html(el).strip()
            html = re.sub(r"^(<br>)+|(<br>)+$", "", html)
            if text_of(html):
                res.append({"type": "p", "html": html})
    return res


def scrape_post(url):
    html = get(url)
    soup = BeautifulSoup(html, "html.parser")
    meta = {m.get("property"): m.get("content") for m in soup.find_all("meta") if m.get("property")}
    art = soup.find("article")
    title_el = art.find(attrs={"data-hook": "post-title"}) if art else None
    title = title_el.get_text(" ", strip=True) if title_el else meta.get("og:title", "")
    cv = art.find(attrs={"data-id": "content-viewer"}) if art else None
    blocks = parse_content(cv) if cv is not None else []
    # categorie dai link presenti nella pagina del post
    cats = sorted({a["href"].rsplit("/", 1)[-1] for a in soup.find_all("a", href=True) if "/articles/categories/" in a["href"]})
    ttr = art.find(attrs={"data-hook": "time-to-read"}) if art else None
    hero = meta.get("og:image")
    return {
        "slug": urllib.parse.unquote(url.rsplit("/post/", 1)[1]),
        "url": url,
        "title": title,
        "published": meta.get("article:published_time"),
        "modified": meta.get("article:modified_time"),
        "description": meta.get("og:description", ""),
        "hero": original_wix_image(hero) if hero else None,
        "read_time": ttr.get_text(strip=True) if ttr else "",
        "categories_on_page": cats,
        "blocks": blocks,
    }


def category_map():
    """slug categoria -> set di slug post, leggendo le pagine categoria (con paginazione)."""
    m = {}
    for cat in ("politics", "economics-finance", "world"):
        posts = set()
        page = 1
        while True:
            url = f"{BASE}/articles/categories/{cat}" + (f"/page/{page}" if page > 1 else "")
            try:
                h = get(url)
            except Exception:  # noqa: BLE001
                break
            found = {urllib.parse.unquote(x) for x in re.findall(r'/post/([^"\'?#<\s]+)', h)}
            new = found - posts
            if not new:
                break
            posts |= found
            page += 1
            if page > 20:
                break
        m[cat] = posts
    return m


def download_images(post):
    d = IMG_DIR / post["slug"]
    srcs = []
    if post["hero"]:
        srcs.append(post["hero"])
    srcs += [b["src"] for b in post["blocks"] if b["type"] == "image"]
    local = {}
    for i, src in enumerate(dict.fromkeys(srcs)):
        ext = Path(urllib.parse.urlparse(src).path).suffix.lower() or ".jpg"
        if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
            ext = ".jpg"
        name = f"{i:02d}{ext}"
        p = d / name
        if not p.exists():
            d.mkdir(parents=True, exist_ok=True)
            p.write_bytes(get(src, binary=True))
        local[src] = f"img/articles/{post['slug']}/{name}"
    if post["hero"]:
        post["hero_local"] = local[post["hero"]]
    for b in post["blocks"]:
        if b["type"] == "image":
            b["local"] = local[b["src"]]


def main():
    sm = get(f"{BASE}/blog-posts-sitemap.xml")
    urls = re.findall(r"<loc>([^<]+)</loc>", sm)
    print(f"{len(urls)} articoli nella sitemap", flush=True)
    cmap = category_map()
    posts = []
    for i, u in enumerate(urls, 1):
        u = urllib.parse.quote(u, safe=":/")
        try:
            p = scrape_post(u)
            p["categories"] = sorted(c for c, s in cmap.items() if p["slug"] in s)
            download_images(p)
            posts.append(p)
            print(f"[{i}/{len(urls)}] {p['slug']}: {len(p['blocks'])} blocchi, hero={'si' if p['hero'] else 'NO'}, cat={p['categories']}", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"[{i}/{len(urls)}] ERRORE {u}: {e}", file=sys.stderr, flush=True)
    posts.sort(key=lambda p: p["published"] or "", reverse=True)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(posts, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Salvati {len(posts)} articoli in {OUT_JSON}")


if __name__ == "__main__":
    main()
