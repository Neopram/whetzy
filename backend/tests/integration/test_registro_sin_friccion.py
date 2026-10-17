"""43.2 (ADR-65 D10): el registro no se atasca por mayúsculas, espacios o un
filtro de palabras demasiado ancho, y sus errores dicen qué campo falla.

Antes de este cambio:
- `Maria@Gmail.COM` se guardaba tal cual, así que quien entraba con `maria@gmail.com`
  recibía «Incorrect email or password».
- Un 409 decía «A user with that email or username already exists» sin decir cuál
  de los dos.
- `computo` daba 422 porque contiene «puto».
- `" ana_b "` (con espacios, lo que deja el autocompletado del móvil) daba 422 por
  el patrón del usuario.
"""

from __future__ import annotations

import itertools

from sqlalchemy import select

from app.models.user import User
from app.services.username_filter import contains_blocked_word

AUTH = "/api/v1/auth"
_ip = itertools.count(1)


def _h() -> dict:
    return {"X-Forwarded-For": f"198.51.100.{next(_ip) % 255 or 255}"}


def _payload(**over: object) -> dict:
    base = {
        "email": "maria@example.com",
        "username": "maria_43",
        "password": "Str0ng!Pass",
        "display_name": "María",
        "language": "es",
        "age_confirmed": True,
    }
    base.update(over)
    return base


async def test_email_con_mayusculas_se_guarda_en_minusculas_y_entra_con_cualquier_caja(client, db_session):
    r = await client.post(f"{AUTH}/register", json=_payload(email="Maria@Example.COM"), headers=_h())
    assert r.status_code == 201, r.text
    user = (await db_session.execute(select(User).where(User.username == "maria_43"))).scalar_one()
    assert user.email == "maria@example.com"

    login = await client.post(
        f"{AUTH}/login", data={"username": "MARIA@example.com", "password": "Str0ng!Pass"}, headers=_h()
    )
    assert login.status_code == 200, login.text


async def test_cuenta_vieja_con_mayusculas_entra_con_minusculas(client, db_session):
    # Cuentas creadas antes de normalizar: el email sigue con su caja original en
    # la base y el login tiene que encontrarlas igual.
    from app.core.security import get_password_hash

    db_session.add(
        User(
            email="Legacy@Example.com",
            username="legacy_43",
            hashed_password=get_password_hash("Str0ng!Pass"),
            display_name="Legacy",
            language="es",
            age_confirmed=True,
        )
    )
    await db_session.commit()

    login = await client.post(
        f"{AUTH}/login", data={"username": "legacy@example.com", "password": "Str0ng!Pass"}, headers=_h()
    )
    assert login.status_code == 200, login.text


async def test_409_dice_si_es_el_email_o_el_usuario(client):
    assert (await client.post(f"{AUTH}/register", json=_payload(), headers=_h())).status_code == 201

    same_email = await client.post(
        f"{AUTH}/register", json=_payload(email="MARIA@example.com", username="otro_43"), headers=_h()
    )
    assert same_email.status_code == 409
    assert same_email.json()["detail"]["code"] == "email_taken"

    same_user = await client.post(
        f"{AUTH}/register", json=_payload(email="otra@example.com"), headers=_h()
    )
    assert same_user.status_code == 409
    assert same_user.json()["detail"]["code"] == "username_taken"


async def test_usuario_con_espacios_alrededor_se_recorta(client, db_session):
    r = await client.post(f"{AUTH}/register", json=_payload(username="  ana_b  "), headers=_h())
    assert r.status_code == 201, r.text
    assert (await db_session.execute(select(User).where(User.username == "ana_b"))).scalar_one()


def test_filtro_por_palabra_completa_en_los_terminos_cortos():
    # Palabras reales que contienen un término corto por casualidad.
    for ok in ("computo", "Computo", "disputa", "matsushita", "nazionale"):
        assert not contains_blocked_word(ok), ok
    # Los términos cortos solos, con separadores o con números pegados, siguen bloqueados.
    for bad in ("puta", "p-u-t-a", "puta123", "PUTO", "f.u.c.k", "nazi", "shit"):
        assert contains_blocked_word(bad), bad
    # Los largos siguen buscándose dentro de la palabra.
    for bad in ("gilipollas99", "xmaricon", "assholes"):
        assert contains_blocked_word(bad), bad
