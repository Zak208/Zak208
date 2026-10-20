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
COLS          = 80          # ancho en caracteres
CHAR_W        = 6.2         # px por carácter (monospace)
CHAR_H        = 13.0        # px por línea
# Para que el SVG quede CUADRADO: filas = cols * CHAR_W / CHAR_H
# (cada char es ~2x más alto que ancho, por eso se divide)
ROWS          = int(COLS * CHAR_W / CHAR_H)   # ≈ 38 filas → aspecto cuadrado
FONT_SIZE     = 11
COLOR         = "#c9d1d9"
BG            = "#0d1117"
RAMP          = " .`:-=+*#%@"
ROW_DELAY_S   = 0.055
WIPE_DURATION = 0.30

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
    img = img.crop((left, top, left + side, top + side))  # cuadrado
    # Redimensionar a COLS × ROWS — ya corregido por aspect ratio de char
    img = img.resize((COLS, ROWS), Image.LANCZOS)
    img = img.convert("L")
    img = ImageEnhance.Contrast(img).enhance(2.4)
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    return img

def pixel_to_char(b):
    return RAMP[int(b / 255 * (len(RAMP) - 1))]

def image_to_rows(img):
    return ["".join(pixel_to_char(img.getpixel((x, y))) for x in range(img.width)) for y in range(img.height)]

def make_svg(rows):
    n_rows = len(rows)
    n_cols = max(len(r) for r in rows)
    svg_w  = math.ceil(n_cols * CHAR_W)
    svg_h  = math.ceil(n_rows * CHAR_H)
    # El SVG es cuadrado: usamos el lado mayor para ambas dimensiones
    side   = max(svg_w, svg_h)
    total  = n_rows * ROW_DELAY_S + WIPE_DURATION

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{side}" height="{side}" viewBox="0 0 {side} {side}">',
        f'  <rect width="{side}" height="{side}" fill="{BG}"/>',
        '  <style>',
        f'    text {{ font-family: "Courier New",monospace; font-size: {FONT_SIZE}px; fill: {COLOR}; white-space: pre; }}',
    ]
    for i in range(n_rows):
        s = round(i * ROW_DELAY_S / total * 100, 2)
        e = min(100.0, round((i * ROW_DELAY_S + WIPE_DURATION) / total * 100, 2))
        parts.append(f'    @keyframes r{i}{{0%,{s}%{{clip-path:inset(0 100% 0 0)}}{e}%,100%{{clip-path:inset(0 0 0 0)}}}}')
    parts.append('  </style>')
    for i, row in enumerate(rows):
        y = round((i + 1) * CHAR_H, 1)
        txt = row.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        parts.append(f'  <text x="0" y="{y}" style="animation:r{i} {round(total,2)}s linear 1 both">{txt}</text>')
    parts.append('</svg>')
    return "\n".join(parts)

img  = fetch_avatar(GITHUB_USER)
img  = preprocess(img)
rows = image_to_rows(img)
svg  = make_svg(rows)
with open(OUT_SVG, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"OK -> {OUT_SVG}  ({len(rows)} filas x {len(rows[0])} cols)")
