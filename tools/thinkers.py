"""Cerca su Wikimedia Commons i ritratti dei pensatori e ne stampa licenza e autore.

Uso: python tools/thinkers.py            -> elenca candidati con licenza
     python tools/thinkers.py download   -> scarica i file scelti in CHOSEN
"""
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "img" / "thinkers"
API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "SBL-site-builder/1.0 (friedman.society@gmail.com)"}

QUERIES = {
    "smith": "Adam Smith portrait",
    "tocqueville": "Alexis de Tocqueville portrait Chassériau",
    "bastiat": "Frédéric Bastiat portrait",
    "mises": "Ludwig von Mises portrait",
    "hayek": "Friedrich Hayek portrait",
    "einaudi": "Luigi Einaudi ritratto ufficiale",
    "friedman": "Milton Friedman portrait",
    "reagan": "Official Portrait of President Reagan 1981",
    "thatcher": "Margaret Thatcher portrait",
    "popper": "Karl Popper",
}


def api(params):
    params = {**params, "format": "json"}
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def info(titles):
    if not titles:
        return []
    d = api({"action": "query", "titles": "|".join(titles), "prop": "imageinfo",
             "iiprop": "url|extmetadata|size", "iiurlwidth": 1200})
    out = []
    for p in d["query"]["pages"].values():
        if "imageinfo" not in p:
            continue
        ii = p["imageinfo"][0]
        md = ii.get("extmetadata", {})
        g = lambda k: (md.get(k, {}).get("value") or "")  # noqa: E731
        out.append({"title": p["title"], "w": ii["width"], "h": ii["height"], "thumb": ii.get("thumburl"),
                    "license": g("LicenseShortName"), "artist": g("Artist")[:120], "credit": g("Credit")[:80],
                    "page": ii.get("descriptionurl")})
    return out


def search(q):
    d = api({"action": "query", "list": "search", "srsearch": q, "srnamespace": 6, "srlimit": 8})
    return [x["title"] for x in d["query"]["search"]]


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "download":
        chosen = json.loads((ROOT / "content" / "thinkers.json").read_text(encoding="utf-8"))
        OUT.mkdir(parents=True, exist_ok=True)
        for t in chosen:
            i = info([t["file"]])[0]
            req = urllib.request.Request(i["thumb"], headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                (OUT / f"{t['id']}.jpg").write_bytes(r.read())
            t.update({"license": i["license"], "author": i["artist"], "source": i["page"]})
            print(t["id"], i["license"])
        (ROOT / "content" / "thinkers.json").write_text(json.dumps(chosen, ensure_ascii=False, indent=1), encoding="utf-8")
    else:
        for k, q in QUERIES.items():
            print(f"\n## {k}")
            for i in info(search(q)):
                if i["title"].lower().endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff")):
                    print(f"  {i['title']} | {i['w']}x{i['h']} | {i['license']} | {i['artist'][:60]}")
