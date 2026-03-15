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

:::note Other Public Providers
The token-validation pattern on this page is not unique to Entra ID. The same JWKS-based verification model also shows up with other public identity providers such as Auth0, Firebase Authentication, and Amazon Cognito. This guide keeps the concrete example on Entra ID because that is the Azure-native enterprise SSO path for this repo.
:::

## How it works

```
User → Entra ID login (MFA, Conditional Access)
     ← RS256-signed JWT with "roles" claim
     → Your FastAPI app with Bearer token
Your app → Fetch JWKS from Entra ID
         ← Public keys
Your app verifies token signature locally (fast, no Entra round-trip per request)
```

If you swap Entra ID for another OpenID Connect or OAuth provider, the moving parts stay broadly the same: the client sends a bearer token, your API reads `iss` and `kid` from the JWT, fetches the provider's JWKS metadata, selects the matching signing key, and verifies the token locally.

## Register your app

1. Azure Portal → **Microsoft Entra ID** → **App registrations** → New registration
2. Name it (e.g. `fastapi-books-api`), select your supported account type
3. Note the **Application (client) ID** and **Directory (tenant) ID**
4. Go to **Expose an API** → Add a scope: `Books.Read` and `Books.Write`
5. Go to **App roles** → Add roles: `Books.Admin`, `Books.Reader`

## Install dependencies

```bash
uv add "pyjwt[crypto]" pyjwt-key-fetcher
```

## Validation implementation

```python
import os
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import OAuth2AuthorizationCodeBearer, SecurityScopes
from pydantic import BaseModel
from pyjwt_key_fetcher import AsyncKeyFetcher
from pyjwt_key_fetcher.errors import JWTKeyFetcherError

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

# ── JWKS key fetching (cache + rotation handling) ─────────────────────
key_fetcher = AsyncKeyFetcher(
    valid_issuers=[ISSUER],
    static_issuer_config={
        ISSUER: {
            "jwks_uri": JWKS_URI,
        }
    },
)

async def verify_entra_token(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(entra_oauth2)],
) -> EntraClaims:
    try:
        key_entry = await key_fetcher.get_key(token)
        payload = jwt.decode(
            jwt=token,
            audience=CLIENT_ID,
            issuer=ISSUER,
            options={"require": ["exp", "iss", "sub"]},
            **key_entry,
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
    except (jwt.InvalidTokenError, JWTKeyFetcherError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid token: {exc}") from exc

    claims = EntraClaims(**payload)

    if security_scopes.scopes:
        token_scopes = set(claims.scp.split()) if claims.scp else set()
        missing_scopes = [scope for scope in security_scopes.scopes if scope not in token_scopes]
        if missing_scopes:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Missing scopes: {', '.join(missing_scopes)}",
            )

    return claims

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

Prefer `AsyncKeyFetcher` over a hand-rolled module-global TTL cache. It keeps issuer configuration and keys cached per issuer, defaults to a 1-hour TTL for up to 32 issuers, and forces a JWKS refresh when it encounters a new `kid` after the library's built-in 5-minute minimum refresh window.

```python
key_fetcher = AsyncKeyFetcher(
    valid_issuers=[ISSUER],
    static_issuer_config={
        ISSUER: {
            "jwks_uri": JWKS_URI,
        }
    },
    cache_ttl=3600,
)

key_entry = await key_fetcher.get_key(token)
payload = jwt.decode(jwt=token, audience=CLIENT_ID, issuer=ISSUER, **key_entry)
```

Use `static_issuer_config` when you already know the issuer and its JWKS URL. It skips OpenID discovery on the hot path while still preserving key caching and rotation handling.
