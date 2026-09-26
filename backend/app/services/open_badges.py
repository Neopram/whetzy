"""Open Badges 3.0 / W3C Verifiable Credentials service (29.10, ADR-37).

Builds and signs JSON-LD credentials for track certificates. The signing key
lives in env (OB_SIGNING_PRIVATE_KEY), never in the repo. When the key is
absent the service still builds the unsigned assertion — useful for dev and
for the verification page (the proof block is simply absent).

QR codes encode the public verification URL for embedding in PDF certificates.
"""

from __future__ import annotations

import base64
import io
from datetime import UTC, datetime
from typing import Any

import cryptography.exceptions
import qrcode  # type: ignore[import-untyped]
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
    load_pem_private_key,
)

from app.core.config import settings

_OB3_CONTEXT = [
    "https://www.w3.org/ns/credentials/v2",
    "https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.3.json",
]

_ISSUER_ID = f"{settings.FRONTEND_BASE_URL}/issuer"
_VERIFY_BASE = f"{settings.FRONTEND_BASE_URL}/verify"


def _load_private_key() -> Ed25519PrivateKey | None:
    pem = settings.OB_SIGNING_PRIVATE_KEY.strip()
    if not pem:
        return None
    key = load_pem_private_key(pem.encode(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise TypeError("OB_SIGNING_PRIVATE_KEY must be Ed25519")
    return key


def _public_key_multibase(pub: Ed25519PublicKey) -> str:
    raw = pub.public_bytes(Encoding.Raw, PublicFormat.Raw)
    # Multicodec ed25519-pub prefix 0xed01 + raw 32 bytes, then base58btc with 'z' prefix
    mc = b"\xed\x01" + raw
    alphabet = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    n = int.from_bytes(mc, "big")
    result = bytearray()
    while n > 0:
        n, r = divmod(n, 58)
        result.append(alphabet[r])
    for byte in mc:
        if byte == 0:
            result.append(alphabet[0])
        else:
            break
    return "z" + result[::-1].decode()


def build_credential(
    *,
    code: str,
    username: str,
    track_id: str,
    track_name_en: str,
    track_name_es: str,
    score_pct: float,
    questions: int,
    issued_at: datetime,
    revoked: bool,
    is_certification: bool,
) -> dict[str, Any]:
    """Build an Open Badges 3.0 / VC JSON-LD document for a certificate."""
    credential_id = f"{_VERIFY_BASE}/{code}"

    achievement_type = "Certification" if is_certification else "Completion"

    credential: dict[str, Any] = {
        "@context": _OB3_CONTEXT,
        "id": credential_id,
        "type": ["VerifiableCredential", "OpenBadgeCredential"],
        "issuer": {
            "id": _ISSUER_ID,
            "type": ["Profile"],
            "name": "Whetzy",
            "url": settings.FRONTEND_BASE_URL,
        },
        "validFrom": issued_at.astimezone(UTC).isoformat(),
        "name": f"Whetzy {achievement_type}: {track_name_en}",
        "credentialSubject": {
            "type": ["AchievementSubject"],
            "achievement": {
                "id": f"{settings.FRONTEND_BASE_URL}/tracks/{track_id}",
                "type": ["Achievement"],
                "name": {"en": track_name_en, "es": track_name_es},
                "description": {
                    "en": f"Passed the {track_name_en} track on Whetzy with {score_pct:.0f}% ({questions} questions)",
                    "es": f"Aprobó el track {track_name_es} en Whetzy con {score_pct:.0f}% ({questions} preguntas)",
                },
                "criteria": {
                    "narrative": f"Score at least 70% on the track final exam ({questions} questions)"
                },
                "achievementType": achievement_type,
            },
        },
    }

    if revoked:
        credential["credentialStatus"] = {
            "id": f"{credential_id}#status",
            "type": "StatusList2021Entry",
            "statusPurpose": "revocation",
            "statusListIndex": "0",
            "statusListCredential": f"{_ISSUER_ID}/status",
        }

    return credential


def sign_credential(credential: dict[str, Any]) -> dict[str, Any]:
    """Add a DataIntegrityProof (Ed25519) to the credential if a key is configured."""
    private_key = _load_private_key()
    if private_key is None:
        return credential

    import copy
    import json

    signed = copy.deepcopy(credential)

    canonical = json.dumps(credential, sort_keys=True, ensure_ascii=False).encode()
    signature = private_key.sign(canonical)

    pub = private_key.public_key()
    vm_id = f"{_ISSUER_ID}#key-1"

    signed["proof"] = {
        "type": "DataIntegrityProof",
        "cryptosuite": "eddsa-jcs-2022",
        "created": datetime.now(UTC).isoformat(),
        "verificationMethod": vm_id,
        "proofPurpose": "assertionMethod",
        "proofValue": "z" + base64.b64encode(signature).decode(),
    }

    signed["issuer"]["verificationMethod"] = [{
        "id": vm_id,
        "type": "Multikey",
        "controller": _ISSUER_ID,
        "publicKeyMultibase": _public_key_multibase(pub),
    }]

    return signed


def verify_proof(credential: dict[str, Any]) -> bool:
    """Verify the DataIntegrityProof on a credential. Returns False if no proof or invalid."""
    proof = credential.get("proof")
    if not proof or proof.get("type") != "DataIntegrityProof":
        return False

    vm_list = credential.get("issuer", {}).get("verificationMethod", [])
    if not vm_list:
        return False

    pub_multibase = vm_list[0].get("publicKeyMultibase", "")
    if not pub_multibase.startswith("z"):
        return False

    # Decode base58btc
    alphabet = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    encoded = pub_multibase[1:].encode()
    n = 0
    for char in encoded:
        n = n * 58 + alphabet.index(char)
    mc_bytes = n.to_bytes((n.bit_length() + 7) // 8, "big")

    if mc_bytes[:2] != b"\xed\x01":
        return False
    raw_pub = mc_bytes[2:]
    if len(raw_pub) != 32:
        return False

    pub = Ed25519PublicKey.from_public_bytes(raw_pub)

    sig_b64 = proof.get("proofValue", "")
    if not sig_b64.startswith("z"):
        return False
    signature = base64.b64decode(sig_b64[1:])

    import copy
    import json

    unsigned = copy.deepcopy(credential)
    unsigned.pop("proof", None)
    if "verificationMethod" in unsigned.get("issuer", {}):
        del unsigned["issuer"]["verificationMethod"]

    canonical = json.dumps(unsigned, sort_keys=True, ensure_ascii=False).encode()

    try:
        pub.verify(signature, canonical)
        return True
    except (ValueError, TypeError, cryptography.exceptions.InvalidSignature):
        return False


def qr_data_uri(code: str) -> str:
    """Generate a QR code as a data:image/png;base64 URI for the verification URL."""
    url = f"{_VERIFY_BASE}/{code}"
    img = qrcode.make(url, box_size=6, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def qr_png_bytes(code: str) -> bytes:
    """Generate a QR code as raw PNG bytes."""
    url = f"{_VERIFY_BASE}/{code}"
    img = qrcode.make(url, box_size=8, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
