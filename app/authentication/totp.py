import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote


def generate_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def code_at(secret: str, timestamp: float | None = None, interval: int = 30) -> str:
    current_time = time.time() if timestamp is None else timestamp
    counter = int(current_time // interval)
    padding = "=" * ((8 - len(secret) % 8) % 8)
    key = base64.b32decode(secret + padding, casefold=True)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return f"{value % 1_000_000:06d}"


def verify_code(secret: str, candidate: str, timestamp: float | None = None) -> bool:
    current_time = time.time() if timestamp is None else timestamp
    normalized = candidate.replace(" ", "").strip()
    return any(
        hmac.compare_digest(code_at(secret, current_time + offset), normalized)
        for offset in (-30, 0, 30)
    )


def provisioning_uri(secret: str, email: str) -> str:
    label = quote(f"Vaulta:{email}")
    issuer = quote("Vaulta")
    return f"otpauth://totp/{label}?secret={secret}&issuer={issuer}&digits=6&period=30"
