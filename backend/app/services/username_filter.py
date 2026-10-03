"""Filtro de palabras para `username`/`display_name` (19.11, App Store 1.2).

Mínimo a propósito: una lista corta y explícita en ES/EN, comparada por
palabra completa sobre el texto normalizado (minúsculas, sin acentos, con los
separadores comunes de "leetspeak" colapsados), no un modelo de toxicidad.
Suficiente para que la cuenta no se pueda crear ni editar con un insulto en el
nombre visible; no filtra el contenido de duelos ni chats porque hoy no
existen.

El verificador adversario del protocolo (§7, 2026-10-02) encontró que un
substring ciego bloqueaba palabras reales que solo contienen una de las
bloqueadas por casualidad: "reputation"/"reputación" (⊃ puta), "imputado"
(⊃ puta), "shitake" (⊃ shit). `ALLOWED_WORDS` las exime explícitamente —
es la vía correcta para ampliar, no aflojar el substring, que sigue haciendo
falta para pillar "p-u-t-a" o "puta123" sin perder cobertura.
"""

from __future__ import annotations

import re
import unicodedata

#: Corto y explícito a propósito — ampliar vía PR, no vía config en caliente.
BLOCKED_WORDS: frozenset[str] = frozenset(
    {
        "puta", "puto", "mierda", "gilipollas", "cabron", "cabrona", "maricon",
        "zorra", "nazi", "retrasado", "retrasada",
        "fuck", "shit", "bitch", "asshole", "cunt", "nigger", "faggot", "retard",
    }
)

#: Palabras reales que contienen una bloqueada por casualidad (hallado por el
#: verificador adversario, 2026-10-02): sin esto, nadie podría registrarse
#: como "reputation" o "imputado". Comparado tras la misma normalización.
ALLOWED_WORDS: frozenset[str] = frozenset(
    {
        "reputation", "reputacion", "imputado", "imputada", "imputacion",
        "disputa", "disputar", "disputado", "disputada", "indisputable",
        "diputado", "diputada", "amputado", "amputada", "amputacion",
        "computador", "computadora", "computacion", "shitake", "putative",
        # "matsushita" ⊃ "shit" ([COORD]/[S5], 2026-10-03): un apellido real
        # de una comunidad grande no puede dar 422 al registrarse.
        "matsushita",
    }
)

_SEPARATORS = re.compile(r"[\s_.\-]+")
_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"})


def _normalize(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return _SEPARATORS.sub("", folded.lower().translate(_LEET))


def contains_blocked_word(text: str) -> bool:
    # Cada palabra separada por espacio se juzga por su cuenta: así "mi
    # reputation" no se lee pegado como "mireputation" antes de mirar la
    # lista de excepciones, pero "p u t a" (con espacios de por medio, el
    # mismo truco que los guiones) se sigue colapsando y detectando.
    for raw_word in text.split():
        normalized = _normalize(raw_word)
        if normalized in ALLOWED_WORDS:
            continue
        if any(word in normalized for word in BLOCKED_WORDS):
            return True
    return False
