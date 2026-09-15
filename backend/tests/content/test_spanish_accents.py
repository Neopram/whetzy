"""Catches Spanish content shipped without its accents (red line 3).

There is already a guard for content that arrives *double-encoded*
(`test_no_double_encoded_text`, added in 17.1b after eight lessons shipped with
`mÃ¡s` in them). This is the other half of the same problem, and it is the one
that is easy to miss because the text stays perfectly valid UTF-8, valid JSON
and perfectly readable: it is just not Spanish.

It keeps happening for a mechanical reason. Content is authored through Python
scripts and agents, accents are the first thing to fall off when a string is
retyped rather than copied, and nothing downstream complains — every assertion
about ids, sources, bilingual presence and executed output passes on
`la operacion mide cuanto apuntan dos vectores`. Red line 3 says the Spanish is
written natively, and unaccented Spanish is not native Spanish; it is what a
tourist writes. A learner paying for this notices immediately.

The word list is deliberately narrow: every entry is a string that is **not a
Spanish word at all** without its accent, so a hit is a defect rather than a
style opinion. Words whose unaccented form is a different, legitimate word
(`mas`/`más`, `el`/`él`, `si`/`sí`, `como`/`cómo`, `que`/`qué`) are left out on
purpose - flagging those would produce false positives on correct text, and a
guard that cries wolf gets deleted.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from app.services.content_loader import _content_root

# Unaccented form -> what it should be. Every key is meaningless in Spanish.
MISSING_ACCENT = {
    "asi": "así",
    "aqui": "aquí",
    "ahi": "ahí",
    "segun": "según",
    "tambien": "también",
    "ademas": "además",
    "despues": "después",
    "aun": None,  # placeholder removed below - see NOTE
    "numero": "número",
    "numeros": "números",
    "codigo": "código",
    "funcion": "función",
    "funciones": "funciones",  # correct unaccented; removed below
    "division": "división",
    "operacion": "operación",
    "informacion": "información",
    "definicion": "definición",
    "posicion": "posición",
    "direccion": "dirección",
    "comparacion": "comparación",
    "aplicacion": "aplicación",
    "ejecucion": "ejecución",
    "expresion": "expresión",
    "version": "versión",
    "parametro": "parámetro",
    "parametros": "parámetros",
    "metodo": "método",
    "metodos": "métodos",
    "modulo": "módulo",
    "modulos": "módulos",
    "practica": None,  # "practica" is a valid verb form - removed below
    "rapido": "rápido",
    "facil": "fácil",
    "dificil": "difícil",
    "ultimo": "último",
    "unico": "único",
    "minimo": "mínimo",
    "maximo": "máximo",
    "indice": "índice",
    "linea": "línea",
    "logica": "lógica",
    "automatico": "automático",
    "estatico": "estático",
    "dinamico": "dinámico",
    "generico": "genérico",
    "basico": "básico",
    "grafico": "gráfico",
    "analisis": "análisis",
    "sintaxis": None,  # correct without an accent - removed below
    "habito": "hábito",
    "deberia": "debería",
    "podria": "podría",
    "tendria": "tendría",
    "seria": None,  # "seria" is a valid adjective - removed below
    "mas": None,  # "mas" is a valid (if literary) conjunction - removed below
}
# NOTE: entries whose unaccented spelling is itself a real Spanish word are
# dropped here rather than never written, so the reason they are excluded stays
# visible next to them instead of living in a commit message.
MISSING_ACCENT = {k: v for k, v in MISSING_ACCENT.items() if v is not None and k != v}

SPANISH_FIELDS = ("question_es", "explanation_es", "correct_answer_es")
LESSON_FIELDS = ("title_es", "body_es")

# Code is not prose: `print(len(x))` and a variable called `codigo` are not
# Spanish that lost an accent. Fenced blocks and inline spans are stripped
# before the check.
FENCE_RE = re.compile(r"```[\s\S]*?```")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
# Not every author marks code with backticks. Several lessons write it in
# straight quotes ("'import modulo' importa el modulo completo"), where `modulo`
# is the statement being quoted and not Spanish that lost an accent. Quoted
# spans are skipped too: under-detecting is the right way to be wrong here,
# because a guard with false positives gets switched off.
QUOTED_RE = re.compile(r"'[^'\n]{1,60}'|\"[^\"\n]{1,60}\"")


def _prose_only(text: str) -> str:
    return QUOTED_RE.sub(" ", INLINE_CODE_RE.sub(" ", FENCE_RE.sub(" ", text)))


def _offences(text: str) -> list[str]:
    prose = _prose_only(text).lower()
    words = set(re.findall(r"[a-záéíóúñü]+", prose))
    return sorted(w for w in words if w in MISSING_ACCENT)


def _spanish_strings() -> list[tuple[str, str, str]]:
    """(source id, field, text) for every Spanish string in the content bank."""
    root = _content_root()
    out: list[tuple[str, str, str]] = []

    for qfile in sorted((root / "questions").rglob("*.json")):
        payload = json.loads(qfile.read_text(encoding="utf-8"))
        items = payload if isinstance(payload, list) else payload.get("questions", [])
        for q in items:
            for field in SPANISH_FIELDS:
                value = q.get(field)
                if isinstance(value, str) and value.strip():
                    out.append((q.get("id", qfile.name), field, value))

    for lfile in sorted((root / "lessons").rglob("*.json")):
        lesson = json.loads(lfile.read_text(encoding="utf-8"))
        for field in LESSON_FIELDS:
            value = lesson.get(field)
            if isinstance(value, str) and value.strip():
                out.append((lesson.get("id", lfile.name), field, value))

    return out


def test_the_guard_recognises_unaccented_spanish() -> None:
    """The guard's own teeth, checked here rather than assumed.

    Without this, a typo in the word list would leave the corpus test passing
    over an empty rule set and nobody would know.
    """
    assert _offences("la operacion mide cuanto apuntan") == ["operacion"]
    assert _offences("un numero y un codigo") == ["codigo", "numero"]
    # Correct Spanish is left alone.
    assert _offences("la operación mide cuánto apuntan dos vectores") == []
    # Code is not prose: a variable named `codigo` must not trip it.
    assert _offences("usa `codigo` para el valor") == []
    assert _offences("```python\ncodigo = 1\n```\nTexto correcto.") == []
    assert _offences("la forma 'import modulo' carga el módulo entero") == []


# Content that already shipped without its accents, as (id, field) pairs.
#
# Turning this guard on found the problem is far wider than the eight questions
# that prompted it: whole lessons in track08 and track09 mix correct Spanish with
# unaccented Spanish inside one paragraph, which is what happens when text is
# generated in two passes and only one of them was careful.
#
# Fixing them is authoring work, not a mechanical replace - `practica` is a verb
# as often as it is a noun, and a bulk substitution would corrupt the correct
# half. So the debt is written down instead of hidden: this list may only ever
# SHRINK. New content fails the moment it is added, which is the point; the
# backlog carries the job of emptying it.
DEBT_PATH = Path(__file__).parent / "spanish_accent_debt.json"
KNOWN_UNACCENTED: set[tuple[str, str]] = {
    (entry["id"], entry["field"])
    for entry in json.loads(DEBT_PATH.read_text(encoding="utf-8"))["known"]
}


def test_the_debt_list_only_covers_real_offences() -> None:
    """An entry that no longer offends must be removed, or the list never shrinks.

    Without this, fixing a string would leave its id sitting in the allowlist
    for ever and the ratchet would quietly stop being one.
    """
    still_offending = {
        (source_id, field)
        for source_id, field, text in _spanish_strings()
        if _offences(text)
    }
    stale = sorted(KNOWN_UNACCENTED - still_offending)
    assert not stale, (
        f"{len(stale)} entries in spanish_accent_debt.json no longer contain "
        f"unaccented Spanish and must be deleted from it: {stale[:10]}"
    )


@pytest.mark.parametrize("source_id,field,text", _spanish_strings())
def test_spanish_text_keeps_its_accents(source_id: str, field: str, text: str) -> None:
    if (source_id, field) in KNOWN_UNACCENTED:
        pytest.xfail("known unaccented content, tracked in spanish_accent_debt.json")
    offences = _offences(text)
    assert not offences, (
        f"{source_id}.{field} contains unaccented Spanish: "
        + ", ".join(f"{w!r} should be {MISSING_ACCENT[w]!r}" for w in offences)
        + ". Red line 3 says the Spanish is written natively; unaccented Spanish "
        "is not. Fix the text rather than the word list."
    )
