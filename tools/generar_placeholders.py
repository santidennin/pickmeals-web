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

VIOLET = (99, 58, 181)       # #633AB5 — violeta oficial del Brandbook PICK MEALS 2025 (p.21)
VIOLET_DEEP = (56, 34, 100)  # #382264 — equivale a --violet-900 de styles.css
MIST = (246, 243, 251)
MIST_2 = (230, 222, 250)
INK_2 = (74, 66, 88)
WHITE = (255, 255, 255)

# Isotipo oficial (mano "pick" formando una C) — mismas coordenadas que .pm-iso en styles.css/HTML,
# en un espacio de 100x100. Reutilizado acá para los placeholders y la imagen og-pickmeals.webp.
ISO_RING = dict(center=(40.9, 57.8), r_outer=23.1, stroke=15.0, gap_from=-15.0, gap_to=65.0)
# (translate, rotate_deg, [P0, C1, C2, P3(punta), C4, C5, de vuelta a P0]) — dos curvas cúbicas (pétalo cerrado)
ISO_PETALS = [
    ((21.0, 46.3), -35, (0, 2), (-7, -3), (-7.3, -10), (0, -16.5), (7.3, -10), (7, -3)),
    ((29.4, 37.9), -10, (0, 2), (-8.5, -4.5), (-9, -17), (0, -27.5), (9, -17), (8.5, -4.5)),
    ((40.9, 34.8), 22, (0, 2), (-8.5, -4.5), (-8.5, -16), (0, -26), (9.5, -16), (9, -4.5)),
]


def _cubic_bezier_points(p0, c1, c2, p3, steps=14):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        mt = 1 - t
        x = mt**3 * p0[0] + 3 * mt**2 * t * c1[0] + 3 * mt * t**2 * c2[0] + t**3 * p3[0]
        y = mt**3 * p0[1] + 3 * mt**2 * t * c1[1] + 3 * mt * t**2 * c2[1] + t**3 * p3[1]
        pts.append((x, y))
    return pts


def petal_polygon(translate, rotate_deg, p0, c1, c2, tip, c4, c5):
    """Puntos (sin transformar) de un pétalo: dos curvas cúbicas que forman una forma cerrada."""
    import math
    pts = _cubic_bezier_points(p0, c1, c2, tip) + _cubic_bezier_points(tip, c4, c5, p0)[1:]
    a = math.radians(rotate_deg)
    ca, sa = math.cos(a), math.sin(a)
    tx, ty = translate
    # mismo sentido que SVG transform="translate(tx ty) rotate(deg)": rota primero, luego traslada
    return [(tx + x * ca - y * sa, ty + x * sa + y * ca) for x, y in pts]


def draw_isotipo(draw, img, cx, cy, scale, color, bg_for_gap=None):
    """Dibuja el isotipo (anillo + 3 pétalos) centrado en (cx,cy), en el espacio local 100x100
    escalado por `scale` px/unidad. Si bg_for_gap se da, se usa para 'abrir' el anillo (recorte real
    sobre el fondo); si no, el anillo se dibuja como arco grueso con los extremos redondeados."""
    import math

    def tp(x, y):
        # el icono fuente tiene su masa visual centrada en (~39,45) dentro del lienzo 0-100
        return (cx + (x - 39) * scale, cy + (y - 45) * scale)

    ring = ISO_RING
    rcx, rcy = ring["center"]
    r_out = ring["r_outer"] * scale
    sw = ring["stroke"] * scale
    r_c = r_out - sw / 2
    cx2, cy2 = tp(rcx, rcy)
    steps = 72
    a0, a1 = math.radians(ring["gap_to"]), math.radians(ring["gap_from"] + 360)
    pts = []
    for i in range(steps + 1):
        a = a0 + (a1 - a0) * i / steps
        pts.append((cx2 + r_c * math.cos(a), cy2 + r_c * math.sin(a)))
    draw.line(pts, fill=color, width=round(sw), joint="curve")
    # tapas redondeadas en las puntas del anillo
    r_cap = sw / 2
    for px, py in (pts[0], pts[-1]):
        draw.ellipse([px - r_cap, py - r_cap, px + r_cap, py + r_cap], fill=color)

    for translate, rot, p0, c1, c2, tip, c4, c5 in ISO_PETALS:
        poly = petal_polygon(translate, rot, p0, c1, c2, tip, c4, c5)
        poly = [tp(x, y) for x, y in poly]
        draw.polygon(poly, fill=color)

# nombre, ancho, alto, ratio legible, descripción breve del slot
# Catálogo: 4 productos en total — 2 reales (jamón y queso, pollo y puerro, ya con foto) +
# 2 demo (vianda-03/04, pendientes). Formato vertical 4:5 para combinar con las fotos reales
# del cliente (tray + etiqueta, tomadas en vertical).
SLOTS = [
    ("hero-vianda", 1600, 2000, "4:5 · vertical", "Portada"),
    ("vianda-03", 1200, 1500, "4:5 · vertical", "Producto 3 (demo)"),
    ("vianda-04", 1200, 1500, "4:5 · vertical", "Producto 4 (demo)"),
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

    # isotipo + wordmark a la derecha (versión sobre fondo violeta: todo en blanco, MEALS en contorno)
    cx, cy, R = W * 0.78, H * 0.38, H * 0.30
    draw_isotipo(d, img, cx, cy, scale=R * 0.0115, color=WHITE)

    fw = font(["seguibl.ttf", "segoeuib.ttf", "arialbd.ttf"], round(R * 0.30))
    wy = cy + R * 0.42
    pick_w = d.textlength("PICK", font=fw)
    d.text((cx - pick_w / 2, wy), "PICK", font=fw, fill=WHITE)
    meals_w = d.textlength("MEALS", font=fw)
    sw = max(2, round(R * 0.018))
    d.text((cx - meals_w / 2, wy + R * 0.34), "MEALS", font=fw, fill=VIOLET, stroke_width=sw, stroke_fill=WHITE)

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
