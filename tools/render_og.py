"""Render the col.ad Open Graph card (1200x630) on top of og-source.png.

Run from the repo root:

    python3 tools/render_og.py

The script auto-downloads Inter (OFL) into tools/fonts/ if missing.
Requires Pillow and cairosvg:

    pip install Pillow cairosvg
"""
from __future__ import annotations

import io
import sys
import urllib.request
import zipfile
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
TOOLS = Path(__file__).resolve().parent

SRC = REPO / "assets" / "og-source.png"
LOGO_SVG = REPO / "assets" / "logo.svg"
OUT = REPO / "assets" / "og.png"

FONT_DIR = TOOLS / "fonts"
INTER_RELEASE = "https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip"
INTER_FILES = ["Inter-Regular.ttf", "Inter-SemiBold.ttf", "Inter-Bold.ttf", "Inter-ExtraBold.ttf"]

W, H = 1200, 630
ACCENT = (0, 212, 200)
ACCENT_BRIGHT = (0, 255, 204)
ACCENT_BLUE = (0, 204, 255)
WHITE = (255, 255, 255)
DIM = (210, 222, 224)


def ensure_fonts() -> None:
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    missing = [f for f in INTER_FILES if not (FONT_DIR / f).exists()]
    if not missing:
        return
    print(f"[render_og] downloading Inter (OFL) → {FONT_DIR}", file=sys.stderr)
    with urllib.request.urlopen(INTER_RELEASE) as resp:
        data = resp.read()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for name in missing:
            with zf.open(f"extras/ttf/{name}") as src, open(FONT_DIR / name, "wb") as dst:
                dst.write(src.read())


def center_crop_resize(img: Image.Image, w: int, h: int) -> Image.Image:
    src_w, src_h = img.size
    tgt_aspect = w / h
    src_aspect = src_w / src_h
    if src_aspect > tgt_aspect:
        new_w = int(src_h * tgt_aspect)
        left = (src_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, src_h))
    else:
        new_h = int(src_w / tgt_aspect)
        top = (src_h - new_h) // 2
        img = img.crop((0, top, src_w, top + new_h))
    return img.resize((w, h), Image.LANCZOS)


def horizontal_fade(w: int, h: int, side: str, start_a: int, end_a: int, frac: float) -> Image.Image:
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = overlay.load()
    cutoff = max(1, int(w * frac))
    for x in range(w):
        if side == "left":
            t = 1.0 - (x / cutoff) if x < cutoff else 0.0
        else:
            t = (x - (w - cutoff)) / cutoff if x > w - cutoff else 0.0
        t = max(0.0, min(1.0, t))
        a = int(start_a + (end_a - start_a) * (1 - t))
        for y in range(h):
            px[x, y] = (0, 0, 0, a)
    return overlay


def vertical_fade(w: int, h: int, side: str, start_a: int, end_a: int, frac: float) -> Image.Image:
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = overlay.load()
    cutoff = max(1, int(h * frac))
    for y in range(h):
        if side == "top":
            t = 1.0 - (y / cutoff) if y < cutoff else 0.0
        else:
            t = (y - (h - cutoff)) / cutoff if y > h - cutoff else 0.0
        t = max(0.0, min(1.0, t))
        a = int(start_a + (end_a - start_a) * (1 - t))
        for x in range(w):
            px[x, y] = (0, 0, 0, a)
    return overlay


def gradient_text(text: str, font: ImageFont.FreeTypeFont, c1: tuple, c2: tuple) -> Image.Image:
    probe = Image.new("L", (10, 10))
    bbox = ImageDraw.Draw(probe).textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = 20
    mw, mh = tw + pad * 2, th + pad * 2

    mask = Image.new("L", (mw, mh), 0)
    ImageDraw.Draw(mask).text((pad - bbox[0], pad - bbox[1]), text, font=font, fill=255)

    grad = Image.new("RGB", (mw, mh))
    gpx = grad.load()
    for x in range(mw):
        t = x / max(1, mw - 1)
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        for y in range(mh):
            gpx[x, y] = (r, g, b)

    out = Image.new("RGBA", (mw, mh), (0, 0, 0, 0))
    out.paste(grad, (0, 0), mask)
    return out


def load_logo(size: int) -> Image.Image:
    data = cairosvg.svg2png(url=str(LOGO_SVG), output_width=size, output_height=size)
    return Image.open(io.BytesIO(data)).convert("RGBA")


def render() -> None:
    ensure_fonts()
    f_xbold = ImageFont.truetype(str(FONT_DIR / "Inter-ExtraBold.ttf"), 96)
    f_brand = ImageFont.truetype(str(FONT_DIR / "Inter-Bold.ttf"), 36)
    f_sub = ImageFont.truetype(str(FONT_DIR / "Inter-Regular.ttf"), 34)
    f_url = ImageFont.truetype(str(FONT_DIR / "Inter-SemiBold.ttf"), 30)

    bg = Image.open(SRC).convert("RGB")
    canvas = center_crop_resize(bg, W, H).convert("RGBA")

    canvas.alpha_composite(horizontal_fade(W, H, "left", 225, 40, 0.85))
    canvas.alpha_composite(vertical_fade(W, H, "bottom", 150, 0, 0.40))
    canvas.alpha_composite(vertical_fade(W, H, "top", 110, 0, 0.22))

    pad_l, pad_t = 76, 64
    logo_size = 64
    canvas.alpha_composite(load_logo(logo_size), (pad_l, pad_t - 6))

    d = ImageDraw.Draw(canvas)
    bbb = d.textbbox((0, 0), "col.ad", font=f_brand)
    brand_h = bbb[3] - bbb[1]
    brand_y = pad_t - 6 + (logo_size - brand_h) // 2 - bbb[1]
    d.text((pad_l + logo_size + 18, brand_y), "col.ad", font=f_brand, fill=WHITE)

    title_y = 196
    line1 = "Create your AI agent"
    d.text((pad_l, title_y), line1, font=f_xbold, fill=WHITE)
    bb1 = d.textbbox((pad_l, title_y), line1, font=f_xbold)
    line2_y = bb1[3] + 8

    grad = gradient_text("on The Colony", f_xbold, ACCENT_BRIGHT, ACCENT_BLUE)
    canvas.alpha_composite(grad, (pad_l - 20, line2_y - 20))

    sub_y = line2_y + (grad.size[1] - 40) + 24
    d.text(
        (pad_l, sub_y),
        "An interactive setup wizard — pick any LLM, launch in minutes",
        font=f_sub,
        fill=DIM,
    )

    foot_y = H - 70
    d.text((pad_l, foot_y), "thecolony.cc", font=f_url, fill=ACCENT)
    arrow_x = pad_l + d.textlength("thecolony.cc", font=f_url) + 14
    d.text((arrow_x, foot_y), "→", font=f_url, fill=ACCENT)

    canvas.convert("RGB").save(OUT, "PNG", optimize=True)
    print(f"wrote {OUT}  {canvas.size}  {OUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    render()
