---
sidebar_position: 4
---

# Microsoft Entra ID

Pattern 3 — enterprise SSO with MFA, conditional access, and app roles managed in the Azure portal.

## When to use

- Internal tools accessed by employees
- Microsoft Teams or Microsoft 365 integrations
- Any API that needs corporate SSO — no custom password system to build or maintain
- When you need MFA and conditional access policies enforced by IT (not by you)

## How it works

```
User → Entra ID login (MFA, Conditional Access)
     ← RS256-signed JWT with "roles" claim
     → Your FastAPI app with Bearer token
Your app → Fetch JWKS from Entra ID
         ← Public keys
Your app verifies token signature locally (fast, no Entra round-trip per request)
```

## Register your app

1. Azure Portal → **Microsoft Entra ID** → **App registrations** → New registration
2. Name it (e.g. `fastapi-books-api`), select your supported account type
3. Note the **Application (client) ID** and **Directory (tenant) ID**
4. Go to **Expose an API** → Add a scope: `Books.Read` and `Books.Write`
5. Go to **App roles** → Add roles: `Books.Admin`, `Books.Reader`

## Install dependencies

```bash
uv add "pyjwt[crypto]" httpx
```

## Validation implementation

```python
import os
from typing import Annotated

import httpx
import jwt
from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from pydantic import BaseModel

TENANT_ID = os.environ["ENTRA_TENANT_ID"]
CLIENT_ID = os.environ["ENTRA_CLIENT_ID"]

JWKS_URI = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"
ISSUER = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"

entra_oauth2 = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize",
    tokenUrl=f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token",
    scopes={
        f"api://{CLIENT_ID}/Books.Read": "Read books",
        f"api://{CLIENT_ID}/Books.Write": "Write books",
    },
)

class EntraClaims(BaseModel):
    sub: str
    name: str | None = None
    preferred_username: str | None = None
    roles: list[str] = []
    scp: str = ""   # delegated scopes

# ── JWKS key fetching (cache in production with TTL) ──────────────────
def _fetch_jwks() -> dict:
    response = httpx.get(JWKS_URI, timeout=10)
    response.raise_for_status()
    return response.json()

def verify_entra_token(token: str) -> EntraClaims:
    jwks = _fetch_jwks()   # cache this with a TTL in production
    try:
        header = jwt.get_unverified_header(token)
        # Find the matching key from the JWKS
        key = next(
            (k for k in jwks["keys"] if k["kid"] == header["kid"]),
            None,
        )
        if not key:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unknown signing key")
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=CLIENT_ID,
            issuer=ISSUER,
        )
        return EntraClaims(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid token: {exc}")

def require_role(role: str):
    """Dependency factory — enforces a specific app role."""
    def _check(claims: Annotated[EntraClaims, Depends(verify_entra_token)]) -> EntraClaims:
        if role not in claims.roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Role '{role}' required")
        return claims
    return _check

# ── Endpoints ─────────────────────────────────────────────────────────
app = FastAPI()

@app.get("/api/v1/books")
async def list_books(
    claims: Annotated[EntraClaims, Security(verify_entra_token, scopes=["Books.Read"])]
) -> dict:
    return {"books": [], "user": claims.preferred_username}

@app.delete("/api/v1/books/{book_id}")
async def delete_book(
    book_id: str,
    claims: Annotated[EntraClaims, Depends(require_role("Books.Admin"))],
) -> dict:
    return {"deleted": book_id, "by": claims.preferred_username}
```

## `Security()` vs `Depends()`

Use `Security()` (not `Depends()`) when you need to declare OAuth2 scopes — this is what makes them appear in the Swagger UI's **Authorize** dialog, so developers can test with the right permissions.

```python
# ✅ Correct — scopes surfaced in Swagger UI
Security(verify_token, scopes=["Books.Read"])

# ⚠️  Works but scopes not declared in OpenAPI schema
Depends(verify_token)
```

## Grant app roles in Azure Portal

1. Entra ID → **Enterprise applications** → find your app
2. **Users and groups** → Add assignment → select user → select role (`Books.Admin`)

The `roles` claim in the token is populated automatically by Entra ID.

## JWKS caching

In production, cache the JWKS response with a TTL (e.g. 1 hour) to avoid fetching it on every request:

```python
import time

_jwks_cache: dict = {}
_jwks_fetched_at: float = 0.0
JWKS_TTL = 3600  # seconds

def _fetch_jwks_cached() -> dict:
    global _jwks_cache, _jwks_fetched_at
    if time.monotonic() - _jwks_fetched_at > JWKS_TTL:
        _jwks_cache = httpx.get(JWKS_URI, timeout=10).raise_for_status().json()
        _jwks_fetched_at = time.monotonic()
    return _jwks_cache
```
