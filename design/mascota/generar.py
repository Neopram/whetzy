"""Genera las tres láminas de dirección de la mascota (46.8, ADR-67 D2).

Son BOCETOS PARA UN ILUSTRADOR, no la mascota final: los ha escrito una IA
(Claude, 2026-10-19) y, como anota `design/iconos/PROCEDENCIA.md`, lo que hace
una IA no es exclusivo ni registrable como marca. Cada SVG lo dice en su
`<metadata>`. Uso: `python design/mascota/generar.py` (escribe junto a este
fichero `direccion-{a,b,c}.svg`).
"""

from __future__ import annotations

from pathlib import Path

BG = "#0A0E1A"
CARD = "#111A2C"
INK = "#E6EDF7"
MUTED = "#8A97AD"
CYAN = "#00BFFF"
VIOLET = "#7B68EE"
MAGENTA = "#C71585"
PINK = "#FF1493"
STONE = "#1B2438"

POSES = [("neutral", "Neutral"), ("acierto", "Acierto"), ("fallo", "Fallo"), ("celebra", "Celebración")]
CELL = 180
W = CELL * 4 + 40
H = 260

METADATA = (
    "<metadata>Boceto de dirección generado por IA (Claude, Anthropic) el 2026-10-19 para la fila 46.8 "
    "(ADR-67 D2). No es la mascota final ni es registrable como marca: es material para el brief de un "
    "ilustrador humano (design/mascota/BRIEF.md).</metadata>"
)

DEFS = f"""<defs>
  <linearGradient id="marca" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{CYAN}"/><stop offset="0.4" stop-color="{VIOLET}"/>
    <stop offset="0.75" stop-color="{MAGENTA}"/><stop offset="1" stop-color="{PINK}"/>
  </linearGradient>
</defs>"""


def eyes(pose: str, cx: float, cy: float, gap: float, color: str) -> str:
    """Ojos tranquilos: puntos (neutral), arcos (acierto), rayas (fallo), estrellas pequeñas no: arcos (celebra)."""
    lx, rx = cx - gap, cx + gap
    if pose == "neutral":
        return f'<circle cx="{lx}" cy="{cy}" r="4" fill="{color}"/><circle cx="{rx}" cy="{cy}" r="4" fill="{color}"/>'
    if pose in ("acierto", "celebra"):
        return "".join(
            f'<path d="M{x - 6} {cy + 2} Q{x} {cy - 6} {x + 6} {cy + 2}" fill="none" stroke="{color}" '
            f'stroke-width="3" stroke-linecap="round"/>'
            for x in (lx, rx)
        )
    # fallo: pensativo, no triste: rayas y una ceja levantada
    return (
        f'<line x1="{lx - 5}" y1="{cy}" x2="{lx + 5}" y2="{cy}" stroke="{color}" stroke-width="3" stroke-linecap="round"/>'
        f'<line x1="{rx - 5}" y1="{cy}" x2="{rx + 5}" y2="{cy}" stroke="{color}" stroke-width="3" stroke-linecap="round"/>'
        f'<line x1="{rx - 6}" y1="{cy - 10}" x2="{rx + 5}" y2="{cy - 13}" stroke="{color}" stroke-width="2.5" stroke-linecap="round"/>'
    )


def sparks(cx: float, cy: float, r: float, n: int, color: str) -> str:
    import math

    out = []
    for i in range(n):
        a = -math.pi / 2 + (i - (n - 1) / 2) * 0.5
        x1, y1 = cx + math.cos(a) * r, cy + math.sin(a) * r
        x2, y2 = cx + math.cos(a) * (r + 12), cy + math.sin(a) * (r + 12)
        out.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" '
            f'stroke-width="3" stroke-linecap="round"/>'
        )
    return "".join(out)


# ── A · «Piedra»: una piedra de afilar con el filo de luz cian ─────────────
def piedra(pose: str, cx: float, cy: float) -> str:
    tilt = {"neutral": 0, "acierto": -4, "fallo": 6, "celebra": -8}[pose]
    body = (
        f'<g transform="rotate({tilt} {cx} {cy})">'
        f'<rect x="{cx - 46}" y="{cy - 26}" width="92" height="56" rx="14" fill="{STONE}" stroke="{CYAN}" stroke-width="3"/>'
        f'<rect x="{cx - 40}" y="{cy - 20}" width="80" height="8" rx="4" fill="{CYAN}" opacity="0.35"/>'
        f'{eyes(pose, cx, cy + 6, 16, INK)}'
        "</g>"
    )
    extra = ""
    if pose == "acierto":
        extra = sparks(cx, cy - 30, 10, 3, CYAN)
    elif pose == "celebra":
        extra = sparks(cx, cy - 30, 10, 5, "url(#marca)")
    return body + extra


# ── B · «Chispa»: una chispa de cuatro puntas con el degradado del logo ────
def chispa(pose: str, cx: float, cy: float) -> str:
    s = {"neutral": 1.0, "acierto": 1.08, "fallo": 0.92, "celebra": 1.15}[pose]
    rot = {"neutral": 0, "acierto": 0, "fallo": -10, "celebra": 12}[pose]
    r_out, r_in = 56 * s, 24 * s
    pts = []
    import math

    for i in range(8):
        a = -math.pi / 2 + i * math.pi / 4
        r = r_out if i % 2 == 0 else r_in
        pts.append(f"{cx + math.cos(a) * r:.1f},{cy + math.sin(a) * r:.1f}")
    star = (
        f'<g transform="rotate({rot} {cx} {cy})">'
        f'<polygon points="{" ".join(pts)}" fill="url(#marca)" stroke="{BG}" stroke-width="2" stroke-linejoin="round"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{21 * s:.1f}" fill="{BG}"/>'
        f"{eyes(pose, cx, cy, 9 * s, INK)}"
        "</g>"
    )
    extra = sparks(cx, cy - 40, 18, 5, CYAN) if pose == "celebra" else ""
    return star + extra


# ── C · «Cursor»: el cursor de una terminal, que parpadea cuando piensa ────
def cursor(pose: str, cx: float, cy: float) -> str:
    tilt = {"neutral": 0, "acierto": 0, "fallo": 8, "celebra": -6}[pose]
    block = (
        f'<g transform="rotate({tilt} {cx} {cy})">'
        f'<rect x="{cx - 26}" y="{cy - 40}" width="52" height="80" rx="6" fill="{CYAN}"/>'
        f"{eyes(pose, cx, cy - 8, 11, BG)}"
        "</g>"
        f'<text x="{cx - 56}" y="{cy + 8}" fill="{MUTED}" font-family="monospace" font-size="22">&gt;</text>'
    )
    extra = ""
    if pose == "acierto":
        extra = (
            f'<path d="M{cx + 36} {cy - 2} l8 8 l16 -18" fill="none" stroke="{CYAN}" stroke-width="4" '
            'stroke-linecap="round" stroke-linejoin="round"/>'
        )
    elif pose == "fallo":
        extra = f'<text x="{cx + 34}" y="{cy - 22}" fill="{MUTED}" font-family="monospace" font-size="22">?</text>'
    elif pose == "celebra":
        extra = sparks(cx, cy - 46, 10, 5, "url(#marca)")
    return block + extra


DIRECTIONS = [
    ("a", "A · Piedra", "Una piedra de afilar (whet = afilar). Tranquila, sólida; el filo de luz cian es la marca.", piedra),
    ("b", "B · Chispa", "La chispa que sale al afilar, con el degradado del logo. Más expresiva, sigue siendo geométrica.", chispa),
    ("c", "C · Cursor", "El cursor de una terminal: técnico y sobrio; piensa parpadeando.", cursor),
]


def sheet(title: str, note: str, draw) -> str:
    cells = []
    for i, (pose, label) in enumerate(POSES):
        x0 = 20 + i * CELL
        cx, cy = x0 + CELL / 2, 120
        cells.append(
            f'<rect x="{x0 + 6}" y="50" width="{CELL - 12}" height="160" rx="16" fill="{CARD}"/>'
            f"{draw(pose, cx, cy)}"
            f'<text x="{cx}" y="236" fill="{MUTED}" font-family="Inter, sans-serif" font-size="14" '
            f'text-anchor="middle">{label}</text>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
        f"{METADATA}{DEFS}"
        f'<rect width="{W}" height="{H}" fill="{BG}"/>'
        f'<text x="26" y="32" fill="{INK}" font-family="Inter, sans-serif" font-size="18" font-weight="700">{title}</text>'
        f'<text x="{W - 20}" y="32" fill="{MUTED}" font-family="Inter, sans-serif" font-size="12" '
        f'text-anchor="end">boceto IA para ilustrador · no final</text>'
        f'<title>{title}: {note}</title>'
        + "".join(cells)
        + "</svg>\n"
    )


def main() -> None:
    here = Path(__file__).resolve().parent
    for key, title, note, draw in DIRECTIONS:
        (here / f"direccion-{key}.svg").write_text(sheet(title, note, draw), encoding="utf-8")


if __name__ == "__main__":
    main()
