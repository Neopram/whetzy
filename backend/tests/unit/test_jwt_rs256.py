"""Tests for JWT RS256 migration (22.15).

Verifies:
- RS256 signing and verification when keys are configured
- HS256 fallback for pre-migration tokens during dual-key rotation
- HS256-only mode when no RSA keys are set (dev default)
"""

from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from jose import jwt

from app.core.security import (
    _create_token,
    _signing_config,
    _verification_keys,
    create_access_token,
    verify_token,
)


def _generate_rsa_keys() -> tuple[str, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_pem, public_pem


PRIVATE_KEY, PUBLIC_KEY = _generate_rsa_keys()


class TestHS256Default:
    """Without RSA keys, behavior is unchanged (HS256)."""

    def test_signing_config_defaults_to_hs256(self):
        _key, alg = _signing_config()
        assert alg == "HS256"

    def test_create_and_verify_hs256(self):
        user_id = uuid4()
        token = create_access_token(user_id, timedelta(minutes=5))
        payload = verify_token(token, expected_type="access")
        assert payload.sub == str(user_id)
        assert payload.type == "access"

    def test_verification_keys_only_hs256(self):
        keys = _verification_keys()
        assert len(keys) == 1
        assert keys[0][1] == ["HS256"]


class TestRS256Mode:
    """With RSA keys configured, tokens are signed RS256."""

    def _patch_settings(self):
        return patch.multiple(
            "app.core.security.settings",
            JWT_PRIVATE_KEY=PRIVATE_KEY,
            JWT_PUBLIC_KEY=PUBLIC_KEY,
        )

    def test_signing_config_uses_rs256(self):
        with self._patch_settings():
            signing_key, alg = _signing_config()
            assert alg == "RS256"
            assert "BEGIN PRIVATE KEY" in signing_key

    def test_create_and_verify_rs256(self):
        with self._patch_settings():
            user_id = uuid4()
            token = create_access_token(user_id, timedelta(minutes=5))
            header = jwt.get_unverified_header(token)
            assert header["alg"] == "RS256"

            payload = verify_token(token, expected_type="access")
            assert payload.sub == str(user_id)

    def test_rs256_token_not_verifiable_with_wrong_key(self):
        _other_priv, other_pub = _generate_rsa_keys()
        with self._patch_settings():
            token = create_access_token(uuid4(), timedelta(minutes=5))

        with patch.multiple(
            "app.core.security.settings",
            JWT_PRIVATE_KEY="",
            JWT_PUBLIC_KEY=other_pub,
            SECRET_KEY="wrong-secret",
            JWT_ALGORITHM="HS256",
        ):
            with pytest.raises(HTTPException) as exc_info:
                verify_token(token, expected_type="access")
            assert exc_info.value.status_code == 401

    def test_verification_keys_includes_both(self):
        with self._patch_settings():
            keys = _verification_keys()
            assert len(keys) == 2
            assert keys[0][1] == ["RS256"]
            assert keys[1][1] == ["HS256"]


class TestDualKeyRotation:
    """During migration, old HS256 tokens must still verify."""

    def test_old_hs256_token_accepted_after_rs256_enabled(self):
        user_id = uuid4()
        old_token = create_access_token(user_id, timedelta(minutes=5))
        header = jwt.get_unverified_header(old_token)
        assert header["alg"] == "HS256"

        with patch.multiple(
            "app.core.security.settings",
            JWT_PRIVATE_KEY=PRIVATE_KEY,
            JWT_PUBLIC_KEY=PUBLIC_KEY,
        ):
            payload = verify_token(old_token, expected_type="access")
            assert payload.sub == str(user_id)

    def test_new_rs256_and_old_hs256_coexist(self):
        user_id_old = uuid4()
        old_token = create_access_token(user_id_old, timedelta(minutes=5))

        with patch.multiple(
            "app.core.security.settings",
            JWT_PRIVATE_KEY=PRIVATE_KEY,
            JWT_PUBLIC_KEY=PUBLIC_KEY,
        ):
            user_id_new = uuid4()
            new_token = create_access_token(user_id_new, timedelta(minutes=5))

            old_payload = verify_token(old_token, expected_type="access")
            new_payload = verify_token(new_token, expected_type="access")

            assert old_payload.sub == str(user_id_old)
            assert new_payload.sub == str(user_id_new)

    def test_wrong_type_rejected_even_with_valid_signature(self):
        with patch.multiple(
            "app.core.security.settings",
            JWT_PRIVATE_KEY=PRIVATE_KEY,
            JWT_PUBLIC_KEY=PUBLIC_KEY,
        ):
            token = _create_token(uuid4(), "refresh", timedelta(minutes=5))
            with pytest.raises(HTTPException):
                verify_token(token, expected_type="access")
