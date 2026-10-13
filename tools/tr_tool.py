"""Strumenti per i traduttori.

python tools/tr_tool.py list <gruppo>      -> slug del gruppo (0-9)
python tools/tr_tool.py show <slug>        -> articolo in forma compatta, blocchi numerati
python tools/tr_tool.py check <slug>       -> valida content/tr/<slug>.json
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")


def load():
    return {p["slug"]: p for p in json.loads((ROOT / "content" / "articles_raw.json").read_text(encoding="utf-8"))}


def tags(html):
    return sorted(re.findall(r"</?(?:strong|em|u|a|sup|sub|br)\b", html or ""))


def main():
    cmd, arg = sys.argv[1], sys.argv[2]
    if cmd == "list":
        print("\n".join(json.loads((ROOT / "content" / "tr_groups.json").read_text(encoding="utf-8"))[int(arg)]))
    elif cmd == "show":
        p = load()[arg]
        print(f"TITLE: {p['title']}\nCATEGORIES: {p['categories']}\nPUBLISHED: {p['published']}\nN_BLOCKS: {len(p['blocks'])}\n")
        for i, b in enumerate(p["blocks"]):
            if b["type"] == "image":
                print(f"[{i}] image caption={b.get('caption')!r}")
            elif b["type"] in ("ul", "ol"):
                print(f"[{i}] {b['type']} items={json.dumps(b['items'], ensure_ascii=False)}")
            elif b["type"] == "h":
                print(f"[{i}] h{b['level']} {b['html']}")
            else:
                print(f"[{i}] {b['type']} {b['html']}")
    elif cmd == "check":
        p = load()[arg]
        f = ROOT / "content" / "tr" / f"{arg}.json"
        t = json.loads(f.read_text(encoding="utf-8"))
        errs = []
        for k in ("slug", "orig_lang", "author", "drop_blocks", "category", "dek", "title_tr", "blocks_tr"):
            if k not in t:
                errs.append(f"manca {k}")
        if t.get("orig_lang") not in ("it", "en"):
            errs.append("orig_lang deve essere it o en")
        if t.get("category") not in ("politics", "economics-finance", "world"):
            errs.append("category non valida")
        if not (isinstance(t.get("dek"), dict) and t["dek"].get("it") and t["dek"].get("en")):
            errs.append("dek.it e dek.en obbligatori")
        bt = t.get("blocks_tr", [])
        if len(bt) != len(p["blocks"]):
            errs.append(f"blocks_tr ha {len(bt)} elementi, servono {len(p['blocks'])}")
        else:
            for i, (o, tr) in enumerate(zip(p["blocks"], bt)):
                if i in t.get("drop_blocks", []):
                    continue
                if o["type"] == "image":
                    if tr is not None and not isinstance(tr, str):
                        errs.append(f"[{i}] immagine: serve null o stringa didascalia")
                elif o["type"] in ("ul", "ol"):
                    if not isinstance(tr, list) or len(tr) != len(o["items"]):
                        errs.append(f"[{i}] lista: servono {len(o['items'])} voci")
                else:
                    if not isinstance(tr, str) or not tr.strip():
                        errs.append(f"[{i}] testo mancante")
                    elif tags(tr) != tags(o["html"]):
                        errs.append(f"[{i}] tag inline diversi dall'originale: {tags(o['html'])} vs {tags(tr)}")
        print("OK" if not errs else "ERRORI:\n" + "\n".join(errs))


if __name__ == "__main__":
    main()
