import base64
import hashlib
import secrets

import httpx
from jose import jwt as jose_jwt

from app.config import settings


def _pkce_pair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return verifier, challenge


async def get_oidc_metadata() -> dict:
    if not settings.OIDC_DISCOVERY_URL:
        raise ValueError("OIDC_DISCOVERY_URL not set")
    async with httpx.AsyncClient() as c:
        r = await c.get(settings.OIDC_DISCOVERY_URL, timeout=10)
        r.raise_for_status()
        return r.json()


async def fetch_jwks(jwks_uri: str) -> dict:
    async with httpx.AsyncClient() as c:
        r = await c.get(jwks_uri, timeout=10)
        r.raise_for_status()
        return r.json()


async def exchange_code(
    token_endpoint: str, code: str, code_verifier: str, redirect_uri: str
) -> dict:
    async with httpx.AsyncClient() as c:
        r = await c.post(
            token_endpoint,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": settings.OIDC_CLIENT_ID,
                "client_secret": settings.OIDC_CLIENT_SECRET,
                "code_verifier": code_verifier,
            },
            timeout=10,
        )
        r.raise_for_status()
        return r.json()


def decode_id_token(id_token: str, jwks: dict) -> dict:
    return jose_jwt.decode(
        id_token,
        jwks,
        algorithms=["RS256", "ES256"],
        audience=settings.OIDC_CLIENT_ID,
        options={"verify_at_hash": False},
    )
