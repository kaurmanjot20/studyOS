"""Symmetric encryption for secrets at rest (provider API keys).

Uses Fernet. The configured `ENCRYPTION_KEY` may be any string — we derive a valid
32-byte Fernet key from it via SHA-256, so operators don't have to generate a
Fernet-formatted key by hand. Losing/rotating the key invalidates stored ciphertexts.
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _fernet() -> Fernet:
    digest = hashlib.sha256(settings.encryption_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:  # pragma: no cover - defensive
        raise ValueError("Could not decrypt secret (wrong ENCRYPTION_KEY?)") from exc
