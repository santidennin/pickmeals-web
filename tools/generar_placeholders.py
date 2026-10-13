#!/usr/bin/env python3
"""
Genera los placeholders de fotos (WebP) con los nombres EXACTOS de cada slot,
más la imagen para compartir en redes (og-pickmeals.webp).

Herramienta de desarrollo — NO se publica. Uso:
    python tools/generar_placeholders.py

Cuando lleguen las fotos reales del cliente:
    1. Copiarlas a assets/photos/source/ con el mismo nombre (hero-vianda.jpg, vianda-01.jpg, ...).
    2. Correr el conversor de la skill:
       python <skill>/scripts/webp_convert.py --src assets/photos/source --dst assets/img
    3. Pisa cada placeholder con la foto real. El HTML no se toca.
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "img"

VIOLET = (91, 43, 196)
VIOLET_DEEP = (43, 21, 102)
MIST = (244, 242, 250)
MIST_2 = (230, 222, 250)
INK_2 = (74, 66, 88)
WHITE = (255, 255, 255)

# nombre, ancho, alto, ratio legible, descripción breve del slot
SLOTS = [
    ("hero-vianda", 1600, 2000, "4:5 · vertical", "Portada"),
    ("vianda-01", 1200, 900, "4:3 · horizontal", "Producto 1"),
    ("vianda-02", 1200, 900, "4:3 · horizontal", "Producto 2"),
    ("vianda-03", 1200, 900, "4:3 · horizontal", "Producto 3"),
    ("vianda-04", 1200, 900, "4:3 · horizontal", "Producto 4"),
    ("vianda-05", 1200, 900, "4:3 · horizontal", "Producto 5"),
    ("vianda-06", 1200, 900, "4:3 · horizontal", "Producto 6"),
    ("punto-de-venta", 1200, 1500, "4:5 · vertical", "Pick Meals en un comercio"),
    ("nosotros-cocina", 1500, 1000, "3:2 · horizontal", "Somos Pick Meals"),
]

FONT_DIR = Path("C:/Windows/Fonts")


def font(names, size):
    for n in names:
        p = FONT_DIR / n
        if p.exists():
            return ImageFont.truetype(str(p), size)
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()


def text_spaced(draw, center_x, y, text, fnt, fill, spacing):
    """Texto centrado con tracking manual."""
    widths = [draw.textlength(ch, font=fnt) for ch in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x = center_x - total / 2
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += w + spacing


def vertical_gradient(w, h, top, bottom):
    img = Image.new("RGB", (w, h), top)
    px = ImageDraw.Draw(img)
    for yy in range(h):
        t = yy / max(1, h - 1)
        c = tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        px.line([(0, yy), (w, yy)], fill=c)
    return img


def draw_tray_icon(draw, cx, cy, s, color, stroke):
    """Ícono lineal de vianda: bandeja con tapa y vapor."""
    w, h = s * 1.5, s * 0.78
    x0, y0 = cx - w / 2, cy - h / 2 + s * 0.18
    # bandeja
    draw.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=s * 0.16, outline=color, width=stroke)
    # tapa
    draw.line([(x0 - s * 0.08, y0 + s * 0.2), (x0 + w + s * 0.08, y0 + s * 0.2)], fill=color, width=stroke)
    # divisiones de la bandeja
    draw.line([(cx + s * 0.12, y0 + s * 0.2), (cx + s * 0.12, y0 + h)], fill=color, width=max(2, stroke // 2))
    # vapor (tres ondas)
    for i, dx in enumerate((-0.38, 0.0, 0.38)):
        bx = cx + dx * s
        top = y0 - s * 0.62
        pts = []
        for k in range(0, 41):
            t = k / 40
            yy = top + t * s * 0.46
            xx = bx + (s * 0.07) * __import__("math").sin(t * 6.283 + i)
            pts.append((xx, yy))
        draw.line(pts, fill=color, width=max(2, stroke // 2), joint="curve")


def placeholder(name, w, h, ratio, label):
    ss = 2  # supersampling para bordes suaves
    W, H = w * ss, h * ss
    img = vertical_gradient(W, H, MIST, MIST_2)
    d = ImageDraw.Draw(img, "RGBA")

    # textura de puntos muy sutil
    step = 34 * ss
    for yy in range(step // 2, H, step):
        for xx in range(step // 2, W, step):
            r = 2 * ss
            d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=VIOLET + (22,))

    # marco interior
    m = round(min(W, H) * 0.045)
    d.rounded_rectangle([m, m, W - m, H - m], radius=m * 1.2, outline=VIOLET + (60,), width=2 * ss)

    # círculo suave detrás del ícono
    cx, cy = W / 2, H * 0.44
    R = min(W, H) * 0.2
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=WHITE + (170,))

    draw_tray_icon(d, cx, cy, R * 0.62, VIOLET + (255,), max(3, round(R * 0.045)))

    # texto — sólo "FOTO PENDIENTE" (sin nombre de archivo ni medidas: ver tools/generar_placeholders.py)
    base = min(W, H)
    f1 = font(["seguisb.ttf", "segoeuib.ttf", "arialbd.ttf"], round(base * 0.046))
    ty = cy + R + base * 0.09
    text_spaced(d, W / 2, ty, "FOTO PENDIENTE", f1, VIOLET, round(base * 0.009))

    img = img.resize((w, h), Image.LANCZOS)
    img.save(OUT / (name + ".webp"), "WEBP", quality=82, method=6)


def wave_points(W, H, y_mid, amp, phase, period):
    import math
    return [(x, y_mid + amp * math.sin((x / period) * 6.2832 + phase)) for x in range(0, W + 1, 4)]


def og_image():
    ss = 2
    w, h = 1200, 630
    W, H = w * ss, h * ss
    img = Image.new("RGB", (W, H), VIOLET)
    d = ImageDraw.Draw(img, "RGBA")

    # ondas inferiores (la "atmósfera")
    for (y_mid, amp, phase, alpha) in ((H * 0.80, 26 * ss, 0.0, 60), (H * 0.86, 22 * ss, 1.6, 110)):
        pts = wave_points(W, H, y_mid, amp, phase, W / 1.6)
        d.polygon(pts + [(W, H), (0, H)], fill=(255, 255, 255, alpha))

    # sello circular a la derecha
    cx, cy, R = W * 0.80, H * 0.40, H * 0.26
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(255, 255, 255, 200), width=3 * ss)
    d.ellipse([cx - R * 0.74, cy - R * 0.74, cx + R * 0.74, cy + R * 0.74], outline=(255, 255, 255, 120), width=2 * ss)
    fs = font(["segoeuib.ttf", "arialbd.ttf"], round(R * 0.14))
    import math
    track = R * 0.025
    # (texto, ángulo central en pantalla, sentido, radio): arriba se lee en sentido horario, abajo antihorario
    for text, mid, direction, rr in (("ATMÓSFERA CONTROLADA", 270, 1, R * 0.87), ("SIN CONSERVANTES", 90, -1, R * 0.87)):
        widths = [d.textlength(ch, font=fs) for ch in text]
        total = sum(widths) + track * (len(text) - 1)
        start = math.radians(mid) - direction * (total / rr) / 2
        cum = 0.0
        for ch, gw in zip(text, widths):
            a = start + direction * (cum + gw / 2) / rr
            cum += gw + track
            if ch == " ":
                continue
            x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
            box = round(R * 0.32)
            glyph = Image.new("RGBA", (box, box), (0, 0, 0, 0))
            gd = ImageDraw.Draw(glyph)
            _, t, _, b = gd.textbbox((0, 0), "H", font=fs)  # misma línea base para todas las letras
            gd.text((box / 2 - gw / 2, box / 2 - (t + b) / 2), ch, font=fs, fill=WHITE)
            deg = math.degrees(a)
            rot = (270 - deg) if direction == 1 else (90 - deg)
            glyph = glyph.rotate(rot, resample=Image.BICUBIC)
            img.paste(glyph, (round(x - box / 2), round(y - box / 2)), glyph)
    d = ImageDraw.Draw(img, "RGBA")
    fw = font(["seguibl.ttf", "segoeuib.ttf", "arialbd.ttf"], round(R * 0.26))
    t = "PICK·MEALS"
    d.text((cx - d.textlength(t, font=fw) / 2, cy - R * 0.2), t, font=fw, fill=WHITE)

    # textos a la izquierda
    fx = W * 0.07
    f_kick = font(["segoeuib.ttf", "arialbd.ttf"], 30 * ss)
    f_h = font(["seguibl.ttf", "segoeuib.ttf", "arialbd.ttf"], 58 * ss)
    f_s = font(["segoescb.ttf", "segoesc.ttf", "Inkfree.ttf", "segoeui.ttf"], 40 * ss)
    f_url = font(["seguisb.ttf", "segoeui.ttf"], 26 * ss)
    kick, sp = "PICK MEALS", 6 * ss
    kw = sum(d.textlength(c, font=f_kick) for c in kick) + sp * (len(kick) - 1)
    text_spaced(d, fx + kw / 2, H * 0.13, kick, f_kick, (255, 255, 255, 230), sp)
    y = H * 0.24
    for line in ("Comida rica, práctica", "y lista para tu", "punto de venta."):
        d.text((fx, y), line, font=f_h, fill=WHITE)
        y += 70 * ss
    d.text((fx, y + 14 * ss), "Somos comida", font=f_s, fill=(237, 231, 251))
    d.text((fx, H * 0.90), "pickmeals.com.ar", font=f_url, fill=VIOLET_DEEP)

    img = img.resize((w, h), Image.LANCZOS)
    img.save(OUT / "og-pickmeals.webp", "WEBP", quality=86, method=6)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for slot in SLOTS:
        placeholder(*slot)
        print("  placeholder", slot[0] + ".webp", f"{slot[1]}x{slot[2]}")
    og_image()
    print("  og-pickmeals.webp 1200x630")


if __name__ == "__main__":
    sys.exit(main())
