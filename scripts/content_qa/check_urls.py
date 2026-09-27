#!/usr/bin/env python3
"""Comprueba que cada URL de `source` responde 200 (con redirecciones).

Uso: python scripts/content_qa/check_urls.py DIR
El 26-09, 5 de 20 URLs escritas por un agente para track27 daban 404. Usa curl con
User-Agent de navegador porque algunos sitios devuelven 500 a peticiones sin él.
Un 403 no cuenta como fallo sino como «revisar a mano»: framework.scaledagile.com
responde 403 a curl y la página existe (leída con WebFetch el 26-09).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

URL = re.compile(r"https?://[^\s)\"]+")


def status(url: str) -> str:
    proc = subprocess.run(
        [
            "curl",
            "-s",
            "-o",
            "/dev/null",
            "-L",
            "-A",
            "Mozilla/5.0",
            "-w",
            "%{http_code}",
            "--max-time",
            "20",
            url,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout.strip() or "000"


def main(argv: list[str]) -> int:
    urls = set()
    for path in Path(argv[0]).rglob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else data.get("questions", [data])
        for item in items:
            urls.update(URL.findall(str(item.get("source", ""))))
    bad = manual = 0
    for url in sorted(urls):
        code = status(url)
        manual += code == "403"
        bad += code not in ("200", "403")
        print(code, url, "(revisar a mano: bloqueo de bots)" if code == "403" else "")
    if manual:
        print(f"REVISAR A MANO: {manual}")
    print("OK" if not bad else f"FALLOS: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
