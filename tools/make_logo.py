"""Genera il logo SBL vettoriale (tre quadrati blu-rosso-blu con S B L serif bianche),
le icone del sito e l'immagine di condivisione social.

Uso: python tools/make_logo.py
"""
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "tools" / "fonts"
IMG = ROOT / "src" / "img"
BLUE = "#0D4B8C"
RED = "#AE0708"
NAVY = "#0A2240"
SQ, GAP = 100, 8


def glyph_path(font, ch, box_x, size=SQ, cap_ratio=0.66):
    gs = font.getGlyphSet()
    name = font.getBestCmap()[ord(ch)]
    g = gs[name]
    bp = BoundsPen(gs)
    g.draw(bp)
    x0, y0, x1, y1 = bp.bounds
    scale = size * cap_ratio / (y1 - y0)
    w = (x1 - x0) * scale
    tx = box_x + (size - w) / 2 - x0 * scale
    ty = size / 2 + (y1 - y0) * scale / 2 + y0 * scale
    pen = SVGPathPen(gs)
    g.draw(TransformPen(pen, (scale, 0, 0, -scale, tx, ty)))
    return pen.getCommands()


def mark_svg():
    font = TTFont(FONTS / "SourceSerif.ttf")
    parts = []
    for i, (ch, col) in enumerate(zip("SBL", (BLUE, RED, BLUE))):
        x = i * (SQ + GAP)
        parts.append(f'<rect x="{x}" y="0" width="{SQ}" height="{SQ}" fill="{col}"/>')
        parts.append(f'<path fill="#fff" d="{glyph_path(font, ch, x)}"/>')
    w = 3 * SQ + 2 * GAP
    return w, "".join(parts)


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    w, inner = mark_svg()
    (IMG / "sbl-mark.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {SQ}" role="img" aria-label="SBL">{inner}</svg>',
        encoding="utf-8")

    # favicon SVG: quadrato unico rosso con "SBL"? Meglio il marchio intero su fondo bianco, quadrato.
    pad = 14
    side = w + 2 * pad
    (IMG / "favicon.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {side} {side}">'
        f'<rect width="{side}" height="{side}" rx="40" fill="#fff"/>'
        f'<g transform="translate({pad},{(side - SQ) / 2})">{inner}</g></svg>', encoding="utf-8")

    # PNG ad alta risoluzione del marchio, renderizzato con PIL dagli stessi glifi (serve per favicon e og)
    mark = render_mark(1200)
    mark.save(IMG / "sbl-mark.png")

    # Icone quadrate (favicon.ico, apple-touch, 192, 512): marchio centrato su bianco
    for size, name in ((512, "icon-512.png"), (192, "icon-192.png"), (180, "apple-touch-icon.png")):
        square_icon(mark, size).save(IMG / name)
    square_icon(mark, 256).save(ROOT / "src" / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

    og_image(mark).save(IMG / "og-default.jpg", quality=90)
    print("ok")


def render_mark(width):
    scale = width / (3 * SQ + 2 * GAP)
    h = round(SQ * scale)
    im = Image.new("RGBA", (width, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype(str(FONTS / "SourceSerif.ttf"), size=10)
    for i, (ch, col) in enumerate(zip("SBL", (BLUE, RED, BLUE))):
        x0 = round(i * (SQ + GAP) * scale)
        x1 = round((i * (SQ + GAP) + SQ) * scale)
        d.rectangle([x0, 0, x1 - 1, h - 1], fill=col)
        # dimensiona il carattere perché l'altezza della maiuscola sia il 66% del quadrato
        target = h * 0.66
        size = 10
        f = ImageFont.truetype(str(FONTS / "SourceSerif.ttf"), size=size)
        while True:
            bb = f.getbbox(ch)
            if bb[3] - bb[1] >= target:
                break
            size += 2
            f = ImageFont.truetype(str(FONTS / "SourceSerif.ttf"), size=size)
        bb = f.getbbox(ch)
        cx = (x0 + x1) / 2 - (bb[0] + bb[2]) / 2
        cy = h / 2 - (bb[1] + bb[3]) / 2
        d.text((cx, cy), ch, font=f, fill="white")
    return im


def square_icon(mark, size):
    im = Image.new("RGBA", (size, size), "white")
    m = mark.copy()
    m.thumbnail((int(size * 0.92), size))
    im.paste(m, ((size - m.width) // 2, (size - m.height) // 2), m)
    return im


def og_image(mark):
    W, H = 1200, 630
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    d.rectangle([0, H - 18, W // 3, H], fill=BLUE)
    d.rectangle([W // 3, H - 18, 2 * W // 3, H], fill=RED)
    d.rectangle([2 * W // 3, H - 18, W, H], fill=BLUE)
    m = mark.copy()
    m.thumbnail((620, 400))
    im.paste(m, ((W - m.width) // 2, 150), m)
    f1 = ImageFont.truetype(str(FONTS / "SourceSerif.ttf"), 44)
    f2 = ImageFont.truetype(str(FONTS / "Inter.ttf"), 24)
    t1 = "Studenti Bocconiani Liberali"
    t2 = "MILTON FRIEDMAN SOCIETY  ·  DAL 2008"
    y = 150 + m.height + 48
    d.text(((W - d.textlength(t1, font=f1)) / 2, y), t1, font=f1, fill=NAVY)
    d.text(((W - d.textlength(t2, font=f2)) / 2, y + 66), t2, font=f2, fill=RED)
    return im


if __name__ == "__main__":
    main()
