# Uso: python -P tools/extraer_logos.py "<BRANDBOOK-PICK-MEALS-2025.pdf>" assets/img
# Extrae del Brandbook PICK MEALS 2025 (PDF vectorial) el isologotipo vertical (p.8)
# y el isotipo (p.6) como SVG con fondo transparente. Los rellenos blancos del PDF
# (separaciones entre letras, interior de "MEALS") se convierten en máscaras.
import sys, pymupdf
PDF = sys.argv[1]; OUT = sys.argv[2]
VIOLETA = (0.388, 0.227, 0.71)
doc = pymupdf.open(PDF)

def es(c, ref): return c is not None and all(abs(a - b) < 0.01 for a, b in zip(c, ref))

def d_de(dr, ox, oy, s):
    f = lambda p: f"{(p.x-ox)*s:.2f} {(p.y-oy)*s:.2f}"
    out, ult = [], None
    for it in dr['items']:
        p0 = it[1]
        if ult is None or abs(p0.x-ult.x) > 1e-3 or abs(p0.y-ult.y) > 1e-3:
            if out: out.append('Z')
            out.append('M' + f(p0))
        if it[0] == 'l': out.append('L' + f(it[2])); ult = it[2]
        elif it[0] == 'c': out.append('C' + f(it[2]) + ' ' + f(it[3]) + ' ' + f(it[4])); ult = it[4]
        else: raise ValueError(it[0])
    out.append('Z')
    return ''.join(out).replace('.00', '')

def armar(pag, idx, nombre, s):
    drs = [doc[pag].get_drawings()[i] for i in idx]
    x0 = min(d['rect'].x0 for d in drs); y0 = min(d['rect'].y0 for d in drs)
    x1 = max(d['rect'].x1 for d in drs); y1 = max(d['rect'].y1 for d in drs)
    W, H = (x1-x0)*s, (y1-y0)*s
    # pintor: cada tramo blanco recorta todo lo violeta pintado antes
    capas, defs, n = [], [], 0
    for d in drs:
        path = d_de(d, x0, y0, s)
        if es(d['fill'], VIOLETA):
            capas.append(f'<path d="{path}"/>')
        else:
            if capas and capas[-1].startswith('<mask-pend'):
                capas[-1] += f'<path d="{path}"/>'
            else:
                capas.append('<mask-pend>' + f'<path d="{path}"/>')
    # resolver máscaras
    cuerpo = ''
    for c in capas:
        if c.startswith('<mask-pend>'):
            if not cuerpo: continue
            n += 1
            defs.append(f'<mask id="{nombre}-m{n}" maskUnits="userSpaceOnUse" x="0" y="0" width="{W:.2f}" height="{H:.2f}"><rect width="100%" height="100%" fill="#fff"/><g fill="#000">{c[len("<mask-pend>"):]}</g></mask>')
            cuerpo = f'<g mask="url(#{nombre}-m{n})">{cuerpo}</g>'
        else:
            cuerpo += c
    return W, H, (f'<defs>{"".join(defs)}</defs>' if defs else ''), cuerpo

def escribir(fn, W, H, defs, cuerpo, color, titulo):
    with open(f'{OUT}/{fn}', 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.2f} {H:.2f}" width="{W:.0f}" height="{H:.0f}" role="img" aria-label="{titulo}">'
                 f'<title>{titulo}</title>{defs}<g fill="{color}">{cuerpo}</g></svg>\n')

# Isologotipo vertical (p.8): dibujos 2..28
W, H, defs, cuerpo = armar(8, range(2, 29), 'pm', 4)
escribir('logo-pickmeals.svg', W, H, defs, cuerpo, '#633AB5', 'PICK MEALS — Somos Comida')
escribir('logo-pickmeals-blanco.svg', W, H, defs, cuerpo, '#FFFFFF', 'PICK MEALS — Somos Comida')
print('logo', W, H, 'mascaras', defs.count('<mask'))
# Isotipo (p.6, versión sobre blanco): dibujos 15..21
W, H, defs, cuerpo = armar(6, range(15, 22), 'iso', 100/170.1)
escribir('isotipo-pickmeals.svg', W, H, defs, cuerpo, '#633AB5', 'PICK MEALS')
escribir('isotipo-pickmeals-blanco.svg', W, H, defs, cuerpo, '#FFFFFF', 'PICK MEALS')
print('iso', W, H, 'mascaras', defs.count('<mask'))
