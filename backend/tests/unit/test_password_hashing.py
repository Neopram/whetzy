"""Hash de contraseñas con bcrypt directo (sin passlib).

passlib 1.7.4 no arranca con bcrypt 5 y el despliegue de `master` del
2026-10-02 (be9bb1a) entró en bucle de caídas. Lo que no puede romperse al
quitarlo: los hashes que ya hay en producción. Los dos de abajo se generaron con
passlib 1.7.4 + bcrypt 4.0.1, la pareja que corría en producción.
"""

from __future__ import annotations

import pytest

from app.core.security import _DUMMY_HASH, get_password_hash, verify_password

SHORT = "Passw0rd!long"
SHORT_LEGACY = "$2b$12$PHGptyYAS.ANMYoP5s.NKeFDIhgtfVy8ZpAyuHSEZ5l6Id.CV/lfC"
# 80 caracteres, 110 bytes en UTF-8: passlib truncaba en silencio a 72 bytes.
LONG = "ñ" * 40 + "X" * 30
LONG_LEGACY = "$2b$12$KTDdhf.BEgweKYHYf0yW0OJ4uzAm0CMUK.X.yvynct04gNciwOmhS"


@pytest.mark.parametrize(("password", "legacy"), [(SHORT, SHORT_LEGACY), (LONG, LONG_LEGACY)])
def test_hashes_made_by_passlib_still_verify(password: str, legacy: str) -> None:
    assert verify_password(password, legacy)
    assert not verify_password(password + "x" if len(password.encode()) < 72 else "otra", legacy)


def test_new_hashes_keep_the_same_format_and_work_past_72_bytes() -> None:
    for password in (SHORT, LONG):
        h = get_password_hash(password)
        assert h.startswith("$2b$12$")
        assert verify_password(password, h)
        assert not verify_password("wrong-password", h)


def test_a_malformed_hash_is_a_mismatch_not_a_crash() -> None:
    assert verify_password(SHORT, "not-a-bcrypt-hash") is False
    assert verify_password(SHORT, "") is False


def test_the_timing_dummy_hash_is_a_real_bcrypt_hash() -> None:
    assert _DUMMY_HASH.startswith("$2b$12$")
    assert verify_password("dummy-password-for-timing-safety", _DUMMY_HASH)
