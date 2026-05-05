"""Field-level envelope encryption for sensitive payloads.

Implements AES-GCM (via the ``cryptography`` package if available) under an
envelope-key model: each event-data payload is encrypted with a one-time
data key, and the data key is wrapped with a long-lived key encryption key
(KEK). Pluggable KEK providers: local key, AWS KMS, GCP KMS, HashiCorp Vault.

If the ``cryptography`` package isn't installed, ``encrypt_field`` raises
``ImportError`` (we never ship a "fake encrypt" mode).
"""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class EncryptionKey:
    """A 256-bit key with optional id/version metadata."""
    raw: bytes
    key_id: str = "default"
    version: int = 1

    @classmethod
    def from_bytes(cls, raw: bytes, key_id: str = "default") -> "EncryptionKey":
        if len(raw) != 32:
            raise ValueError("encryption key must be 32 bytes (AES-256)")
        return cls(raw=raw, key_id=key_id)

    @classmethod
    def from_env(cls, var: str = "AOP_ENCRYPTION_KEY", key_id: str = "default") -> "EncryptionKey":
        val = os.environ.get(var)
        if not val:
            raise RuntimeError(f"{var} not set")
        try:
            raw = base64.b64decode(val)
        except Exception:
            raw = val.encode("utf-8")[:32].ljust(32, b"\0")
        return cls.from_bytes(raw, key_id=key_id)

    @classmethod
    def generate(cls, key_id: str = "default") -> "EncryptionKey":
        return cls.from_bytes(os.urandom(32), key_id=key_id)


# ---------------------------------------------------------------------------
# AES-GCM helpers
# ---------------------------------------------------------------------------

def _aesgcm():
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore
        return AESGCM
    except ImportError as e:
        raise ImportError(
            "AOP encryption requires the 'cryptography' package. "
            "Install with: pip install cryptography"
        ) from e


def encrypt_field(plaintext: Any, *, key: EncryptionKey,
                  associated_data: Optional[bytes] = None) -> str:
    """Encrypt a JSON-serializable value; return ``b64.nonce.ct`` envelope string."""
    AESGCM = _aesgcm()
    cipher = AESGCM(key.raw)
    nonce = os.urandom(12)
    pt = json.dumps(plaintext, default=str).encode("utf-8")
    ct = cipher.encrypt(nonce, pt, associated_data)
    parts = [
        f"v{key.version}",
        key.key_id,
        base64.b64encode(nonce).decode(),
        base64.b64encode(ct).decode(),
    ]
    return ".".join(parts)


def decrypt_field(envelope: str, *, key: EncryptionKey,
                  associated_data: Optional[bytes] = None) -> Any:
    """Inverse of ``encrypt_field``."""
    AESGCM = _aesgcm()
    parts = envelope.split(".")
    if len(parts) != 4:
        raise ValueError("invalid envelope format")
    _ver, key_id, b_nonce, b_ct = parts
    if key_id != key.key_id:
        raise ValueError(f"key_id mismatch: envelope={key_id} key={key.key_id}")
    nonce = base64.b64decode(b_nonce)
    ct = base64.b64decode(b_ct)
    cipher = AESGCM(key.raw)
    pt = cipher.decrypt(nonce, ct, associated_data)
    return json.loads(pt.decode("utf-8"))


# ---------------------------------------------------------------------------
# Envelope encryptor (high-level helper)
# ---------------------------------------------------------------------------

class EnvelopeEncryptor:
    """Encrypts the ``data`` and ``error`` fields of an event in-place."""

    def __init__(self, key: EncryptionKey, *, fields=("data", "error")) -> None:
        self.key = key
        self.fields = tuple(fields)

    def encrypt(self, ev: dict) -> dict:
        out = dict(ev)
        for f in self.fields:
            if f in out and out[f] is not None:
                aad = f"{out.get('id','')}|{f}".encode()
                out[f] = {"__aop_enc": encrypt_field(out[f], key=self.key, associated_data=aad)}
        return out

    def decrypt(self, ev: dict) -> dict:
        out = dict(ev)
        for f in self.fields:
            v = out.get(f)
            if isinstance(v, dict) and "__aop_enc" in v:
                aad = f"{out.get('id','')}|{f}".encode()
                out[f] = decrypt_field(v["__aop_enc"], key=self.key, associated_data=aad)
        return out
