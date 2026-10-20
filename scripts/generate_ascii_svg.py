import sys
import urllib.request
import io
import math

try:
    from PIL import Image, ImageEnhance
except ImportError:
    sys.exit("Instala Pillow: pip install pillow")

GITHUB_USER   = "Zak208"
OUT_SVG       = "avi-ascii.svg"

# ── CANVAS TARGET ──────────────────────────────────────────────────────────
# Queremos que el SVG final sea visualmente cuadrado.
# Courier New en SVG: cada char ~6.5px ancho, ~12px alto (line-height real ~1.2em).
# Para cuadrado: ROWS/COLS = CHAR_W/CHAR_H
COLS          = 60
CHAR_W        = 6.5          # ancho real de un char monospace en px
CHAR_H        = 12.0         # line-height real en SVG
ROWS          = int(COLS * CHAR_W / CHAR_H)   # 60 * 6.5/12 = 32 filas
FONT_SIZE     = 10.5

COLOR         = "#c9d1d9"
BG            = "#0d1117"
RAMP          = " .`:-=+*#%@"
ROW_DELAY_S   = 0.06
WIPE_DURATION = 0.30
# ───────────────────────────────────────────────────────────────────────────

def fetch_avatar(user):
    url = f"https://github.com/{user}.png?size=400"
    print(f"Descargando {url}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as r:
        data = r.read()
    return Image.open(io.BytesIO(data)).convert("RGB")

def preprocess(img):
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top  = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))
    img = img.resize((COLS, ROWS), Image.LANCZOS)
    img = img.convert("L")
    img = ImageEnhance.Contrast(img).enhance(2.5)
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    return img

def pixel_to_char(b):
    return RAMP[int(b / 255 * (len(RAMP) - 1))]

def image_to_rows(img):
    return [
        "".join(pixel_to_char(img.getpixel((x, y))) for x in range(img.width))
        for y in range(img.height)
    ]

def make_svg(rows):
    n_rows = len(rows)
    n_cols = max(len(r) for r in rows)

    # Dimensiones exactas del contenido de texto
    content_w = math.ceil(n_cols * CHAR_W)
    content_h = math.ceil(n_rows * CHAR_H)

    # Canvas CUADRADO: lado = el mayor de los dos
    canvas = max(content_w, content_h)

    # Centrar el contenido en el canvas cuadrado
    offset_x = (canvas - content_w) // 2
    offset_y = (canvas - content_h) // 2

    total = n_rows * ROW_DELAY_S + WIPE_DURATION

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg"'
        f' width="{canvas}" height="{canvas}"'
        f' viewBox="0 0 {canvas} {canvas}"'
        f' preserveAspectRatio="xMidYMid meet">',
        f'  <rect width="{canvas}" height="{canvas}" fill="{BG}"/>',
        '  <style>',
        f'    text {{ font-family: "Courier New",Courier,monospace;'
        f' font-size: {FONT_SIZE}px; fill: {COLOR}; white-space: pre; }}',
    ]

    for i in range(n_rows):
        s = round(i * ROW_DELAY_S / total * 100, 2)
        e = min(100.0, round((i * ROW_DELAY_S + WIPE_DURATION) / total * 100, 2))
        parts.append(
            f'    @keyframes r{i}{{'
            f'0%,{s}%{{clip-path:inset(0 100% 0 0)}}'
            f'{e}%,100%{{clip-path:inset(0 0 0 0)}}}}'
        )
    parts.append('  </style>')

    for i, row in enumerate(rows):
        y = round(offset_y + (i + 1) * CHAR_H, 1)
        x = offset_x
        txt = row.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        dur = round(total, 2)
        parts.append(
            f'  <text x="{x}" y="{y}"'
            f' style="animation:r{i} {dur}s linear 1 both">{txt}</text>'
        )

    parts.append('</svg>')
    return "\n".join(parts)

if __name__ == "__main__":
    img  = fetch_avatar(GITHUB_USER)
    img  = preprocess(img)
    rows = image_to_rows(img)
    svg  = make_svg(rows)

    with open(OUT_SVG, "w", encoding="utf-8") as f:
        f.write(svg)

    n_rows = len(rows)
    n_cols = len(rows[0])
    content_w = math.ceil(n_cols * CHAR_W)
    content_h = math.ceil(n_rows * CHAR_H)
    canvas    = max(content_w, content_h)
    print(f"OK -> {OUT_SVG}")
    print(f"  Chars: {n_rows} filas x {n_cols} cols")
    print(f"  Contenido: {content_w}x{content_h}px  |  Canvas: {canvas}x{canvas}px (cuadrado)")
