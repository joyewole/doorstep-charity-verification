import os
import json
import hmac
import hashlib
import base64
from typing import Dict, Any

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)

def sign_payload(payload: Dict[str, Any]) -> str:
    """
    Token format:
      base64url(payload_json) . base64url(HMAC_SHA256(payload_b64, TOKEN_SIGNING_KEY))
    """
    key = os.getenv("TOKEN_SIGNING_KEY", "dev-signing-key").encode("utf-8")

    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = _b64url_encode(payload_json).encode("utf-8")

    sig = hmac.new(key, payload_b64, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(sig)

    return payload_b64.decode("utf-8") + "." + sig_b64

def verify_token(token: str) -> Dict[str, Any]:
    key = os.getenv("TOKEN_SIGNING_KEY", "dev-signing-key").encode("utf-8")

    try:
        payload_b64, sig_b64 = token.split(".", 1)
    except ValueError:
        raise ValueError("Malformed token")

    expected_sig = hmac.new(key, payload_b64.encode("utf-8"), hashlib.sha256).digest()
    expected_sig_b64 = _b64url_encode(expected_sig)

    if not hmac.compare_digest(expected_sig_b64, sig_b64):
        raise ValueError("Invalid signature")

    payload_json = _b64url_decode(payload_b64)
    return json.loads(payload_json.decode("utf-8"))

def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

