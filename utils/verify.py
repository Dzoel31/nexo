import hashlib
import hmac

from fastapi import HTTPException

from config.settings import settings


def verify_signature(payload: bytes, secret_header: str) -> None:
    github_secret = settings.GITHUB_SECRET.strip()
    if not github_secret:
        raise HTTPException(
            status_code=500,
            detail="GITHUB_SECRET is not configured on the server",
        )

    if not secret_header:
        raise HTTPException(
            status_code=401, detail="Missing X-Hub-Signature-256 header"
        )

    secret_bytes = github_secret.encode("utf-8")
    signature = hmac.new(secret_bytes, payload, hashlib.sha256)
    expected = "sha256=" + signature.hexdigest()

    if not hmac.compare_digest(expected, secret_header):
        raise HTTPException(status_code=401, detail="Invalid signature")
