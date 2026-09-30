import secrets

from fastapi import Header, HTTPException

from app.config import settings


# Blocks any request without the right X-API-Key header.
# If no key is configured, everything is blocked (safe by default).
def require_api_key(x_api_key: str = Header(default="")):
    expected = settings.service_api_key
    sent = x_api_key.encode()
    if not expected or not secrets.compare_digest(sent, expected.encode()):
        raise HTTPException(status_code=401, detail="Invalid API key")
