"""El contenido no publica direcciones de correo reales (39.30).

Una lección de track26 (`l260101`, 18.10) enseñaba `git config user.email`
con el correo personal del dueño, y el mismo fallo reapareció el 2026-09-26
cuando un agente redactor copió el nombre y el correo que tenía en su
contexto. Los ejemplos usan dominios reservados (example.com, RFC 2606) o
dominios inventados; un buzón de un proveedor de correo real es casi siempre
el de una persona.
"""

from __future__ import annotations

import re

from app.services.content_loader import _content_root

PERSONAL_PROVIDERS = (
    "gmail.com",
    "googlemail.com",
    "hotmail.com",
    "outlook.com",
    "live.com",
    "yahoo.com",
    "icloud.com",
    "me.com",
    "protonmail.com",
    "proton.me",
)
EMAIL = re.compile(r"([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")


def personal_emails() -> list[str]:
    hits = []
    for path in sorted(_content_root().rglob("*.json")):
        if "_quarantine" in path.parts:
            continue
        for local, domain in EMAIL.findall(path.read_text(encoding="utf-8")):
            # `%@gmail.com` es un patrón LIKE de SQL, no un buzón.
            if domain.lower() in PERSONAL_PROVIDERS and re.search(
                r"[A-Za-z0-9]", local
            ):
                hits.append(f"{path.name}: {local}@{domain}")
    return hits


def test_content_has_no_real_mailbox() -> None:
    hits = personal_emails()
    assert not hits, (
        f"{len(hits)} correos de buzones reales en el contenido: {hits[:5]}"
    )
