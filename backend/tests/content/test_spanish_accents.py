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
    # Added in 18.13, after extending the scan to `tracks.json`. Every one of
    # these was sitting in a track, module or skill name that the curriculum
    # screen renders verbatim - `Python Basico` was the display name of the
    # flagship track - and the guard could not see the file at all. They follow
    # the same rule as the rest: none is a Spanish word without its accent.
    "algebra": "álgebra",
    "algoritmica": "algorítmica",
    "anomalias": "anomalías",
    "arboles": "árboles",
    "asimetrico": "asimétrico",
    "asincrona": "asíncrona",
    "autenticacion": "autenticación",
    "autorizacion": "autorización",
    "basica": "básica",
    "basicos": "básicos",
    "calculo": None,  # "calculo" is a valid verb form - removed below
    "categorias": "categorías",
    "clasico": "clásico",
    "clasificacion": "clasificación",
    "codigos": "códigos",
    "computo": None,  # "computo" is a valid verb form - removed below
    "concienciacion": "concienciación",
    "contencion": "contención",
    "contrasenas": "contraseñas",
    "conversion": "conversión",
    "criptografia": "criptografía",
    "decision": "decisión",
    "deteccion": "detección",
    "dinamica": "dinámica",
    "diseno": "diseño",
    "documentacion": "documentación",
    "economia": "economía",
    "encapsulacion": "encapsulación",
    "erradicacion": "erradicación",
    "estadistica": "estadística",
    "estandar": "estándar",
    "estatica": "estática",
    "etica": "ética",
    "evaluacion": "evaluación",
    "facturacion": "facturación",
    "federacion": "federación",
    "fisico": "físico",
    "fisicos": "físicos",
    "generacion": "generación",
    "gestion": "gestión",
    "hibrida": "híbrida",
    "identificacion": "identificación",
    "inalambrica": "inalámbrica",
    "indices": "índices",
    "ingenieria": "ingeniería",
    "integracion": "integración",
    "invalidacion": "invalidación",
    "inyeccion": "inyección",
    "iteracion": "iteración",
    "jerarquico": "jerárquico",
    "leccion": "lección",
    "libreria": "librería",
    "logicos": "lógicos",
    "logistica": "logística",
    "matematicas": "matemáticas",
    "metricas": "métricas",
    "migracion": "migración",
    "numericos": "numéricos",
    "optimizacion": "optimización",
    "orquestacion": "orquestación",
    "parametrizacion": "parametrización",
    "patron": "patrón",
    "politicas": "políticas",
    "produccion": "producción",
    "programacion": "programación",
    "recuperacion": "recuperación",
    "recursion": "recursión",
    "reduccion": "reducción",
    "refactorizacion": "refactorización",
    "regresion": "regresión",
    "replicacion": "replicación",
    "resolucion": "resolución",
    "sanitizacion": "sanitización",
    "segmentacion": "segmentación",
    "separacion": "separación",
    "serializacion": "serialización",
    "simetrico": "simétrico",
    "sincronizacion": "sincronización",
    "tecnicas": "técnicas",
    "tecnicos": "técnicos",
    "tecnologia": "tecnología",
    "tokenizacion": "tokenización",
    "triada": "tríada",
    "tunel": "túnel",
    "validacion": "validación",
    "verificacion": "verificación",
    "visualizacion": "visualización",
    "volumenes": "volúmenes",
    # Added in 37.16 (2026-09-25), when the scan reached the answer options: the
    # distractor rewrite of track05 shipped `ningun`, `demas`, `jamas`, and 280
    # options across the bank had lost accents the guard never looked at. Plurals
    # in -ciones are correct without an accent and stay out on purpose.
    "demas": "demás",
    "logico": "lógico",
    "actualizacion": "actualización",
    "administracion": "administración",
    "atomica": "atómica",
    "atomico": "atómico",
    "atomicos": "atómicos",
    "automaticamente": "automáticamente",
    "compresion": "compresión",
    "comunicacion": "comunicación",
    "condicion": "condición",
    "conexion": "conexión",
    "configuracion": "configuración",
    "creacion": "creación",
    "eliminacion": "eliminación",
    "excepcion": "excepción",
    "facilmente": "fácilmente",
    "imagenes": "imágenes",
    "implementacion": "implementación",
    "jamas": "jamás",
    "ningun": "ningún",
    "organizacion": "organización",
    "particion": "partición",
    "peticion": "petición",
    "prevencion": "prevención",
    "proposito": "propósito",
    "propositos": "propósitos",
    "proteccion": "protección",
    "rapidamente": "rápidamente",
    "revocacion": "revocación",
    "sesion": "sesión",
    "transaccion": "transacción",
    "unicamente": "únicamente",
}
# NOTE: entries whose unaccented spelling is itself a real Spanish word are
# dropped here rather than never written, so the reason they are excluded stays
# visible next to them instead of living in a commit message.
MISSING_ACCENT = {k: v for k, v in MISSING_ACCENT.items() if v is not None and k != v}

SPANISH_FIELDS = ("question_es", "explanation_es", "correct_answer_es")
LESSON_FIELDS = ("title_es", "body_es")
# `tracks.json` is the highest-visibility Spanish in the product and was the
# last file this guard could not see: every one of these strings is rendered
# verbatim on the curriculum screen, the track card and the module header.
CURRICULUM_FIELDS = ("name_es", "description_es")
GLOSSARY_FIELDS = ("term_es", "definition_es")

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
# Code written inline with no marker at all, which several lessons do:
# `nombre_modulo.funcion()`, `reduce(funcion, iterable)`, `dis.dis(funcion)`.
# The words inside are identifiers, not Spanish that lost an accent, and
# flagging them sends an author to "fix" a code sample.
# NO whitespace before the paren, deliberately. Allowing `\s*` made this match
# ordinary Spanish parentheticals — `CloudWatch Logs (que registro la aplicacion
# o el sistema)` and `la replica (elegida por un hash ... no por su direccion
# IP)` both parse as "call" — and stripping those HID TWO REAL DEFECTS. A guard
# that suppresses findings is worse than no guard, so the cost of being wrong
# here falls on the false-positive side: `DVC (Data Version Control)` stays
# flagged and lives in the exception list with its reason, which is the
# harmless way to be wrong.
CALL_RE = re.compile(r"\b[A-Za-z_]\w*\([^)\n]{0,100}\)")
DOTTED_RE = re.compile(r"\b[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+")
SNAKE_RE = re.compile(r"\b[A-Za-z]\w*_\w+\b")


def _prose_only(text: str) -> str:
    for pattern in (FENCE_RE, INLINE_CODE_RE, QUOTED_RE, CALL_RE, DOTTED_RE, SNAKE_RE):
        text = pattern.sub(" ", text)
    return text


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
            # The options are what the learner reads to answer, and until 37.16
            # nobody checked them: 280 had lost their accents.
            for i, option in enumerate(q.get("options_es") or []):
                if isinstance(option, str) and option.strip():
                    out.append((q.get("id", qfile.name), f"options_es[{i}]", option))

    for lfile in sorted((root / "lessons").rglob("*.json")):
        lesson = json.loads(lfile.read_text(encoding="utf-8"))
        for field in LESSON_FIELDS:
            value = lesson.get(field)
            if isinstance(value, str) and value.strip():
                out.append((lesson.get("id", lfile.name), field, value))

    payload = json.loads(
        (root / "curriculum" / "tracks.json").read_text(encoding="utf-8")
    )
    for track in payload["tracks"]:
        for node in _curriculum_nodes(track):
            for field in CURRICULUM_FIELDS:
                value = node.get(field)
                if isinstance(value, str) and value.strip():
                    out.append((node["id"], field, value))

    for gfile in sorted((root / "glossary").rglob("*.json")):
        payload = json.loads(gfile.read_text(encoding="utf-8"))
        terms = payload if isinstance(payload, list) else payload.get("terms", [])
        for term in terms:
            for field in GLOSSARY_FIELDS:
                value = term.get(field)
                if isinstance(value, str) and value.strip():
                    out.append((term.get("id", gfile.name), field, value))

    return out


def _curriculum_nodes(track: dict) -> list[dict]:
    """The track itself, its modules and its skills - each one a named node."""
    nodes = [track]
    for module in track.get("modules", []):
        nodes.append(module)
        nodes.extend(module.get("skills", []))
    return nodes


def test_the_guard_recognises_unaccented_spanish() -> None:
    """The guard's own teeth, checked here rather than assumed.

    Without this, a typo in the word list would leave the corpus test passing
    over an empty rule set and nobody would know.
    """
    assert _offences("la operacion mide cuanto apuntan") == ["operacion"]
    assert _offences("un numero y un codigo") == ["codigo", "numero"]
    assert _offences("sin ningun limite y los demas") == ["demas", "ningun"]
    # Correct Spanish is left alone.
    assert _offences("la operación mide cuánto apuntan dos vectores") == []
    # Code is not prose: a variable named `codigo` must not trip it.
    assert _offences("usa `codigo` para el valor") == []
    assert _offences("```python\ncodigo = 1\n```\nTexto correcto.") == []
    assert _offences("la forma 'import modulo' carga el módulo entero") == []
    # Code written inline with no marker at all, straight from real lessons.
    assert _offences("escribes nombre_modulo.funcion() para llamarla") == []
    assert _offences("reduce(funcion, iterable) aplica la función acumulando") == []
    assert _offences("dis.dis(funcion) imprime cada instrucción") == []
    # ...but stripping code must not swallow the prose around it.
    assert _offences("dis.dis(funcion) imprime la operacion") == ["operacion"]
    # And a Spanish parenthetical is prose, not a call. Both of these are real
    # sentences from the bank that an earlier version of CALL_RE swallowed,
    # hiding the defect they contain.
    assert _offences("CloudWatch Logs (que registro la aplicacion o el sistema)") == [
        "aplicacion"
    ]
    assert _offences("la replica (elegida por un hash, no por su direccion IP)") == [
        "direccion"
    ]


# Strings this guard flags that are NOT defects, each with its reason.
#
# This file started life as a debt list of 315 strings: turning the guard on
# showed the problem was far wider than the eight questions that prompted it,
# with whole lessons mixing correct and unaccented Spanish inside one paragraph.
# Paying that debt off left only these, so the file was renamed rather than left
# claiming to hold debt it no longer holds.
#
# What is left is three kinds of thing the checker cannot tell from prose: code
# written without backticks (`for linea in f:`), English proper nouns (`Data
# Version Control`), and `correct_answer_es` fields that are a program's
# expected stdout - accenting those would break the test that compares them
# against what CPython actually printed.
#
# Every entry needs a written reason. Without that rule this file becomes the
# place where anything tedious to fix quietly goes to live.
EXCEPTIONS_PATH = Path(__file__).parent / "spanish_accent_exceptions.json"
_EXCEPTIONS = json.loads(EXCEPTIONS_PATH.read_text(encoding="utf-8"))["known"]
KNOWN_UNACCENTED: set[tuple[str, str]] = {(e["id"], e["field"]) for e in _EXCEPTIONS}


def test_every_exception_carries_a_reason() -> None:
    """An exception without a reason is a defect someone got tired of."""
    missing = [
        f"{e['id']}.{e['field']}" for e in _EXCEPTIONS if not (e.get("reason") or "").strip()
    ]
    assert not missing, (
        f"{len(missing)} entries in spanish_accent_exceptions.json have no reason: {missing}"
    )


def test_the_exception_list_only_covers_strings_that_still_flag() -> None:
    """An entry that no longer flags must be removed, or the list never shrinks.

    Without this, fixing a string would leave its id sitting in the list for
    ever and the ratchet would quietly stop being one.
    """
    still_offending = {
        (source_id, field)
        for source_id, field, text in _spanish_strings()
        if _offences(text)
    }
    stale = sorted(KNOWN_UNACCENTED - still_offending)
    assert not stale, (
        f"{len(stale)} entries in spanish_accent_exceptions.json no longer flag and "
        f"must be deleted from it: {stale[:10]}"
    )


# NOTE (18.13): an accent-*density* guard was written here and then deleted,
# because the data refuted it. The idea was that a word list only catches words
# somebody thought to list, so instead require any Spanish text of 40+ words to
# carry at least one accent. The bank's distribution looked like it supported
# that - median 8,8 %, p1 1,3 %, then a cliff to 29 texts at exactly 0,00 % -
# but reading those 29 showed almost all were correct Spanish that simply never
# needs an accent: «Mantener el build verde es un pilar de la CI: un build roto
# en la rama principal bloquea a todo el equipo...» is 50 words, flawless, and
# unaccented. The premise was wrong, so the guard was a false-positive machine,
# and this file's own doctrine is that a guard that cries wolf gets deleted.
# What actually caught the half-unaccented lesson bodies was the word list, once
# it was rich enough. Widening that list is the lever; density is not.


def test_the_scan_reaches_every_content_file() -> None:
    """A guard that scans nothing passes, which is how this one missed a file.

    Until 18.13 `_spanish_strings` walked only `questions/` and `lessons/`, so
    `tracks.json` - the most visible Spanish in the product, rendered verbatim
    on every track card - was never looked at once. It held 160 unaccented
    strings, `Python Basico` (the flagship track's display name) among them,
    while this file sat green. The lesson from 17.3 and 17.8 applies exactly:
    *a check that has never failed is not the same as a check that passes.*
    So assert the sources are non-empty rather than trusting the walk.
    """
    seen = {field for _, field, _ in _spanish_strings()}
    for group, fields in (
        ("questions", SPANISH_FIELDS),
        ("lessons", LESSON_FIELDS),
        ("curriculum", CURRICULUM_FIELDS),
        ("glossary", GLOSSARY_FIELDS),
    ):
        assert seen & set(fields), (
            f"the scan returned no {group} strings at all, so that whole source "
            f"is unguarded. Expected at least one of {fields}."
        )


@pytest.mark.parametrize("source_id,field,text", _spanish_strings())
def test_spanish_text_keeps_its_accents(source_id: str, field: str, text: str) -> None:
    if (source_id, field) in KNOWN_UNACCENTED:
        pytest.xfail("known false positive, with its reason in spanish_accent_exceptions.json")
    offences = _offences(text)
    assert not offences, (
        f"{source_id}.{field} contains unaccented Spanish: "
        + ", ".join(f"{w!r} should be {MISSING_ACCENT[w]!r}" for w in offences)
        + ". Red line 3 says the Spanish is written natively; unaccented Spanish "
        "is not. Fix the text rather than the word list."
    )
