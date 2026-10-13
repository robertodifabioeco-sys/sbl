"""Verifica che ogni link e risorsa interna di dist/ esista."""
import re, sys
from pathlib import Path
from urllib.parse import unquote, urlparse
D = Path(__file__).resolve().parent.parent / "dist"
bad = {}
n = 0
for f in D.rglob("*.html"):
    h = f.read_text(encoding="utf-8")
    for m in re.findall(r'(?:href|src)="(/[^"#?]*)', h):
        n += 1
        p = D / unquote(m).lstrip("/")
        if m.endswith("/") or p.is_dir():
            p = p / "index.html"
        if not p.exists():
            bad.setdefault(m, set()).add(str(f.relative_to(D)))
print(f"{n} link interni controllati, {len(bad)} rotti")
for k, v in list(bad.items())[:30]:
    print(k, "<-", list(v)[:2])
sys.exit(1 if bad else 0)
