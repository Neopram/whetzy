"""Recorta una hoja de iconos generada con IA en celdas y vectoriza cada una a SVG.

Uso: python hoja_a_svg.py HOJA COLUMNAS FILAS SALIDA nombre1,nombre2,...
     --media-id=MAH... --generada=AAAA-MM-DD --copia="de dónde sale el fichero"
(design/iconos/PROCEDENCIA.md). Necesita `vtracer` (MIT) y Pillow.

Cada SVG lleva en <metadata> su procedencia (herramienta, id de Canva, fecha,
términos aplicables y hoja de origen), porque los términos de Canva prohíben
quitar los metadatos de procedencia del contenido generado con IA y el SVG no
puede conservar los del original. Una celda con nombre "-" se salta.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

import vtracer
from PIL import Image

FONDO = (0x0A, 0x0E, 0x1A)
TOLERANCIA = 40  # distancia por canal para considerar un píxel «fondo»
TERMINOS = "Canva AI Product Terms, effective 26 June 2026 (https://www.canva.com/policies/ai-product-terms/)"


def _sin_fondo(img: Image.Image) -> Image.Image:
    """Borra solo el fondo conectado con el borde de la celda (relleno por
    inundación): el contorno oscuro del icono se parece al fondo y, quitado por
    color, desaparecía."""
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size

    def es_fondo(x: int, y: int) -> bool:
        r, g, b, a = px[x, y]
        return a > 0 and all(abs(c - f) <= TOLERANCIA for c, f in zip((r, g, b), FONDO))

    pila = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    while pila:
        x, y = pila.pop()
        if 0 <= x < w and 0 <= y < h and es_fondo(x, y):
            px[x, y] = (0, 0, 0, 0)
            pila.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    bbox = img.getbbox()
    return img.crop(bbox) if bbox else img


def _con_procedencia(svg: str, meta: dict[str, str]) -> str:
    # viewBox para que escale con CSS; vtracer solo pone width/height.
    m = re.search(r'<svg[^>]*\swidth="(\d+)"\s+height="(\d+)"', svg)
    if m and "viewBox" not in svg[: svg.index(">", svg.index("<svg"))]:
        svg = svg.replace("<svg ", f'<svg viewBox="0 0 {m.group(1)} {m.group(2)}" ', 1)
    texto = escape(json.dumps(meta, ensure_ascii=False))
    bloque = f"<metadata>{texto}</metadata>"
    i = svg.index(">", svg.index("<svg")) + 1
    return svg[:i] + bloque + svg[i:]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("hoja", type=Path)
    ap.add_argument("columnas", type=int)
    ap.add_argument("filas", type=int)
    ap.add_argument("salida", type=Path)
    ap.add_argument("nombres")
    ap.add_argument("--media-id", required=True)
    ap.add_argument("--generada", required=True)
    ap.add_argument("--copia", required=True, help="qué fichero se procesó y cómo llegó")
    args = ap.parse_args()

    nombres = args.nombres.split(",")
    assert len(nombres) == args.columnas * args.filas, "un nombre por celda"
    hoja = Image.open(args.hoja)
    sha = hashlib.sha256(args.hoja.read_bytes()).hexdigest()
    cw, ch = hoja.width / args.columnas, hoja.height / args.filas
    args.salida.mkdir(parents=True, exist_ok=True)
    manifiesto = []
    for k, nombre in enumerate(nombres):
        if nombre == "-":
            continue
        c, f = k % args.columnas, k // args.columnas
        celda = hoja.crop((round(c * cw), round(f * ch), round((c + 1) * cw), round((f + 1) * ch)))
        png = args.salida / f".{nombre}.png"
        _sin_fondo(celda).save(png)
        svg = vtracer.convert_raw_image_to_svg(
            # Polígonos y trazado simplificado: 2-5 KB por icono en vez de
            # hasta 95 KB, sin diferencia visible a 32 px (comparado a ojo).
            png.read_bytes(), img_format="png", colormode="color", filter_speckle=10,
            color_precision=4, layer_difference=32, mode="polygon", path_precision=1,
        )
        png.unlink()
        meta = {
            "generado_con_ia": "Sí — Canva AI (generate-image)",
            "canva_media_id": args.media_id,
            "fecha_generacion": args.generada,
            "terminos": TERMINOS,
            "copia_procesada": args.copia,
            "hoja_origen_sha256": sha,
            "celda": f"columna {c + 1}, fila {f + 1}",
            "vectorizado_con": f"vtracer {importlib.metadata.version('vtracer')} (MIT)",
        }
        (args.salida / f"{nombre}.svg").write_text(_con_procedencia(svg, meta), encoding="utf-8")
        manifiesto.append({"icono": f"{nombre}.svg", **meta})
    (args.salida / f"procedencia-{args.media_id}.json").write_text(
        json.dumps(manifiesto, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"{len(manifiesto)} SVG en {args.salida}")


if __name__ == "__main__":
    main()
