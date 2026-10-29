import os
import sys
import ssl
import urllib.request
import io
import math

try:
    from PIL import Image, ImageEnhance
except ImportError:
    sys.exit("Instala Pillow: pip install pillow")

SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR   = os.path.dirname(SCRIPT_DIR)
GITHUB_USER   = "Zak208"
OUT_SVG       = os.path.join(PROJECT_DIR, "avi-ascii.svg")

# ── CANVAS TARGET ──────────────────────────────────────────────────────────
# Queremos que el SVG final sea visualmente cuadrado y con caracteres más definidos.
# Con COLS=84 y FONT_SIZE=7.5px conseguimos mayor resolución y nitidez en el avatar.
COLS          = 84
CHAR_W        = round(390.0 / COLS, 2)       # ~4.64px ancho por char
CHAR_H        = round(CHAR_W * (12.0 / 6.5), 2)  # ~8.57px alto por línea
ROWS          = int(COLS * CHAR_W / CHAR_H)  # 45 filas
FONT_SIZE     = round(CHAR_W * (10.5 / 6.5), 1)  # 7.5px

COLOR         = "#c9d1d9"
BG            = "#0d1117"
RAMP          = " .`:-=+*#%@"
ROW_DELAY_S   = 0.045
WIPE_DURATION = 0.28
# ───────────────────────────────────────────────────────────────────────────

def fetch_avatar(user):
    local_temp = os.path.join(PROJECT_DIR, "temp_avatar.png")
    if os.path.exists(local_temp):
        return Image.open(local_temp).convert("RGB")
    url = f"https://github.com/{user}.png?size=400"
    print(f"Descargando {url}...")
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ctx) as r:
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
    img = ImageEnhance.Contrast(img).enhance(2.4)
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    return img

def pixel_to_char(b, ramp):
    return ramp[int(b / 255 * (len(ramp) - 1))]

def image_to_rows(img, ramp):
    return [
        "".join(pixel_to_char(img.getpixel((x, y)), ramp) for x in range(img.width))
        for y in range(img.height)
    ]

def make_svg(rows, bg, color):
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
        f'  <rect width="{canvas}" height="{canvas}" fill="{bg}"/>',
        '  <style>',
        f'    text {{ font-family: "Courier New",Courier,monospace;'
        f' font-size: {FONT_SIZE}px; fill: {color}; white-space: pre; }}',
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
    img = fetch_avatar(GITHUB_USER)
    img = preprocess(img)

    # 1. Versión Dark (avi-ascii.svg)
    ramp_dark = " .`:-=+*#%@"
    rows_dark = image_to_rows(img, ramp_dark)
    svg_dark  = make_svg(rows_dark, bg="#0d1117", color="#c9d1d9")
    with open(OUT_SVG, "w", encoding="utf-8") as f:
        f.write(svg_dark)
    print(f"OK Dark  -> {OUT_SVG}")

    # 2. Versión Light (avi-ascii-light.svg)
    out_svg_light = os.path.join(PROJECT_DIR, "avi-ascii-light.svg")
    ramp_light = "@%#*+=-:. "
    rows_light = image_to_rows(img, ramp_light)
    svg_light  = make_svg(rows_light, bg="#ffffff", color="#1f2328")
    with open(out_svg_light, "w", encoding="utf-8") as f:
        f.write(svg_light)
    print(f"OK Light -> {out_svg_light}")
