#!/usr/bin/env python3
"""Generate an RSA-2048 key pair for JWT RS256 signing.

Prints the PEM-encoded private and public keys to stdout. Copy each value
into the corresponding environment variable (JWT_PRIVATE_KEY, JWT_PUBLIC_KEY)
in your deployment platform (e.g. Railway).

Usage:
    python scripts/generate_jwt_keys.py
"""

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

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

print("=== JWT_PRIVATE_KEY ===")
print(private_pem)
print("=== JWT_PUBLIC_KEY ===")
print(public_pem)
