---
sidebar_position: 2
---

# JWT Bearer Authentication

Pattern 1 — stateless, self-contained tokens for user-facing APIs.

## How it works

1. User `POST /token` with credentials
2. Server verifies password with `argon2id`, creates a signed JWT
3. Client stores the token and sends `Authorization: Bearer <token>` on every request
4. Server verifies the cryptographic signature — no DB lookup needed

## Install dependencies

```bash
uv add "pyjwt[crypto]" "pwdlib[argon2]"
```

## Complete example

```python
import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from pwdlib import PasswordHash

# ── Config ────────────────────────────────────────────────────────────
SECRET_KEY = os.environ["JWT_SECRET_KEY"]   # never hardcode this
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

hasher = PasswordHash.recommended()         # argon2id by default
oauth2 = OAuth2PasswordBearer(tokenUrl="/token")
app = FastAPI()

# ── Models ────────────────────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenClaims(BaseModel):
    sub: str
    roles: list[str] = []

# ── Fake user store (replace with DB) ─────────────────────────────────
USERS = {
    "alice": {
        "hashed_password": hasher.hash("s3cr3t"),
        "roles": ["Books.Read", "Books.Write"],
    }
}

# ── Helpers ───────────────────────────────────────────────────────────
def create_access_token(subject: str, roles: list[str]) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "roles": roles, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> TokenClaims:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenClaims(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

# ── Endpoints ─────────────────────────────────────────────────────────
@app.post("/token", response_model=Token)
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    user = USERS.get(form.username)
    # Dummy hash prevents timing attacks even when user doesn't exist
    dummy = hasher.hash("dummy")
    stored_hash = user["hashed_password"] if user else dummy
    if not user or not hasher.verify(form.password, stored_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect credentials")
    token = create_access_token(form.username, user["roles"])
    return Token(access_token=token, expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60)

@app.get("/api/v1/books")
async def list_books(claims: Annotated[TokenClaims, Depends(verify_token)]) -> dict:
    if "Books.Read" not in claims.roles:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient scope")
    return {"books": [], "user": claims.sub}
```

## Security checklist

| Item                                     | Why                                                  |
| ---------------------------------------- | ---------------------------------------------------- |
| `argon2id` via `pwdlib`                  | Memory-hard, GPU-resistant password hashing          |
| Dummy hash on unknown user               | Prevents user enumeration via timing                 |
| `SECRET_KEY` from environment            | Never commit secrets to source control               |
| 15-minute expiry                         | Limits blast radius of stolen tokens                 |
| `401` for bad token, `403` for bad scope | Correct RFC 6750 semantics                           |
| RS256 instead of HS256 for multi-service | Asymmetric — services verify without the signing key |

## Key Vault integration

Combine with Managed Identity to store `JWT_SECRET_KEY` in Azure Key Vault:

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

async def load_jwt_secret() -> str:
    credential = DefaultAzureCredential()
    client = SecretClient("https://myvault.vault.azure.net/", credential)
    return client.get_secret("jwt-signing-key").value

# In your FastAPI lifespan:
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.jwt_secret = await load_jwt_secret()
    yield
```

→ See [Managed Identity](./managed-identity.md) for the full pattern.
