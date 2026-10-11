"""Tests for Open Badges 3.0 credential building, signing, and verification (29.10)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
)


@pytest.fixture()
def _ob_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Generate an ephemeral Ed25519 key and inject it into settings."""
    key = Ed25519PrivateKey.generate()
    pem = key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()).decode()
    monkeypatch.setattr("app.core.config.settings.OB_SIGNING_PRIVATE_KEY", pem)


CERT_KWARGS = {
    "code": "abc123deadbeef",
    "username": "alice",
    "track_id": "track01",
    "track_name_en": "Python Fundamentals",
    "track_name_es": "Fundamentos de Python",
    "score_pct": 85.0,
    "questions": 40,
    "issued_at": datetime(2026, 9, 26, 12, 0, 0, tzinfo=UTC),
    "revoked": False,
    "is_certification": False,
}


def test_build_credential_structure():
    from app.services.open_badges import build_credential

    cred = build_credential(**CERT_KWARGS)

    assert cred["@context"][0] == "https://www.w3.org/ns/credentials/v2"
    assert "VerifiableCredential" in cred["type"]
    assert "OpenBadgeCredential" in cred["type"]
    assert cred["issuer"]["name"] == "Whetzy"
    assert "validFrom" in cred
    assert "AchievementSubject" in cred["credentialSubject"]["type"]
    assert cred["credentialSubject"]["achievement"]["name"]["en"] == "Python Fundamentals"
    assert "proof" not in cred


def test_build_credential_revoked():
    from app.services.open_badges import build_credential

    cred = build_credential(**{**CERT_KWARGS, "revoked": True})
    assert "credentialStatus" in cred
    assert cred["credentialStatus"]["statusPurpose"] == "revocation"


def test_build_credential_certification():
    from app.services.open_badges import build_credential

    cred = build_credential(**{**CERT_KWARGS, "is_certification": True})
    # El nombre del badge no puede leerse como la certificación del vendor.
    assert "Certification" not in cred["name"]
    assert cred["name"] == "Whetzy Exam preparation: Python Fundamentals"
    achievement = cred["credentialSubject"]["achievement"]
    assert achievement["achievementType"] == "Assessment"
    for lang in ("en", "es"):
        assert "Whetzy" in achievement["description"][lang]
    assert "Not an official certification" in achievement["description"]["en"]
    assert "No es una certificación oficial" in achievement["description"]["es"]


@pytest.mark.usefixtures("_ob_key")
def test_sign_and_verify():
    from app.services.open_badges import build_credential, sign_credential, verify_proof

    cred = build_credential(**CERT_KWARGS)
    signed = sign_credential(cred)

    assert "proof" in signed
    assert signed["proof"]["type"] == "DataIntegrityProof"
    assert signed["proof"]["cryptosuite"] == "eddsa-jcs-2022"
    assert signed["proof"]["proofValue"].startswith("z")
    assert "verificationMethod" in signed["issuer"]

    assert verify_proof(signed) is True


@pytest.mark.usefixtures("_ob_key")
def test_tampered_credential_fails_verification():
    from app.services.open_badges import build_credential, sign_credential, verify_proof

    cred = build_credential(**CERT_KWARGS)
    signed = sign_credential(cred)

    signed["name"] = "TAMPERED"
    assert verify_proof(signed) is False


def test_unsigned_credential_verify_returns_false():
    from app.services.open_badges import build_credential, verify_proof

    cred = build_credential(**CERT_KWARGS)
    assert verify_proof(cred) is False


def test_qr_data_uri():
    from app.services.open_badges import qr_data_uri

    uri = qr_data_uri("abc123")
    assert uri.startswith("data:image/png;base64,")
    assert len(uri) > 100


def test_qr_png_bytes():
    from app.services.open_badges import qr_png_bytes

    png = qr_png_bytes("abc123")
    assert png[:4] == b"\x89PNG"
    assert len(png) > 100
