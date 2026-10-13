import json, glob, re, os
raw = {p['slug']: p for p in json.load(open('content/articles_raw.json', encoding='utf-8'))}
IT = set('il lo la gli le di che non per una sono del della nel con anche come più questo'.split())
EN = set('the of and to is that for with are this was which have from not by'.split())
def lang(s):
    w = re.findall(r"[a-zàèéìòù']+", re.sub(r'<[^>]+>', ' ', s).lower())
    i = sum(x in IT for x in w); e = sum(x in EN for x in w)
    return 'it' if i > e else 'en'
for f in glob.glob('content/tr/*.json'):
    t = json.load(open(f, encoding='utf-8'))
    s = os.path.basename(f)[:-5]
    p = raw[s]
    if t['slug'] != s: print('SLUG', s, t['slug'])
    o = ' '.join(b.get('html', '') for i, b in enumerate(p['blocks']) if b['type'] in ('p','h','quote') and i not in t['drop_blocks'])
    tr = ' '.join(x for i, x in enumerate(t['blocks_tr']) if isinstance(x, str) and p['blocks'][i]['type'] in ('p','h','quote'))
    lo, lt = lang(o), lang(tr)
    ratio = len(tr) / max(1, len(o))
    if lo != t['orig_lang'] or lt == lo or not 0.75 < ratio < 1.45:
        print(f'{s[:60]:60} orig={t["orig_lang"]} det={lo}->{lt} ratio={ratio:.2f}')
print('audit finito')
