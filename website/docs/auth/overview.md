---
sidebar_position: 1
description: Decision guide for JWT bearer auth, managed identity, and Microsoft Entra ID in a FastAPI application.
keywords:
  - authentication
  - jwt
  - managed identity
  - entra id
---

# Auth Overview — The Big Picture

This page answers the question developers always ask first: **"Which auth pattern do I use, and when?"**

A production FastAPI app on Azure typically uses **all three patterns simultaneously** — they solve different problems.

## The three patterns at a glance

```
┌─────────────────────────────────────────────────────────────────────┐
│                        YOUR FASTAPI APP                             │
│                                                                     │
│  Inbound (who calls you)          Outbound (what you call)          │
│  ─────────────────────────        ──────────────────────────        │
│  Pattern 1: JWT Bearer            Pattern 2: Managed Identity       │
│  → Generic internet users         → Azure SQL, Key Vault,           │
│                                     Storage, Service Bus            │
│  Pattern 3: Microsoft Entra ID                                      │
│  → Corporate users / MFA / SSO                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Pattern 1 — JWT Bearer (user-facing)

**Answer to:** "I have internet users hitting my API."

Your app issues a signed JWT after verifying credentials. Every subsequent request attaches the token in `Authorization: Bearer <token>`. The server verifies the signature cryptographically — **no database round-trip per request**.

```python
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends

oauth2 = OAuth2PasswordBearer(tokenUrl="/token")

@app.get("/api/v1/books")
async def list_books(token: str = Depends(oauth2)):
    claims = verify_token(token)   # pure crypto — fast
    ...
```

**Use when:** mobile apps, SPAs, public REST APIs, any scenario where you control the token issuance.

→ [Full JWT guide](./jwt-bearer.md)

---

## Pattern 2 — Azure Managed Identity (outbound)

**Answer to:** "My app needs credentials to talk to Azure SQL, Key Vault, or Storage."

Managed Identity gives your app an Azure-managed certificate. It exchanges that certificate for a short-lived access token from IMDS (the Instance Metadata Service running on the VM/container host). **No passwords, no secrets, no rotation scripts.**

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()   # picks up MI automatically in Azure
client = SecretClient("https://myvault.vault.azure.net/", credential)
jwt_secret = client.get_secret("jwt-signing-key").value
```

**Use when:** your app reads secrets from Key Vault, connects to Azure SQL with token auth, pushes to Service Bus, reads blobs — anything Azure-service-to-Azure-service.

→ [Full Managed Identity guide](./managed-identity.md)

---

## Pattern 3 — Microsoft Entra ID (enterprise SSO)

**Answer to:** "My users are corporate employees — they should log in with their Microsoft account."

Your app validates tokens issued by Microsoft Entra ID (formerly Azure AD). You don't touch passwords at all. Entra handles MFA, conditional access, and app roles. Tokens are RS256-signed; your app fetches the JWKS endpoint to verify them.

```python
from fastapi.security import OAuth2AuthorizationCodeBearer

entra_oauth2 = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize",
    tokenUrl=f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token",
)

@app.get("/api/v1/admin")
async def admin_only(token: str = Depends(entra_oauth2)):
    claims = verify_entra_token(token)
    require_role(claims, "Books.Admin")
    ...
```

**Use when:** internal tools, Teams integrations, Microsoft 365 connected apps, anything that needs corporate SSO with MFA.

→ [Full Entra ID guide](./entra-id.md)

---

## Decision matrix

| Scenario                       | Pattern                      |
| ------------------------------ | ---------------------------- |
| Public-facing REST API         | Pattern 1 (JWT)              |
| Mobile or SPA frontend         | Pattern 1 (JWT)              |
| App reads from Azure SQL       | Pattern 2 (Managed Identity) |
| App fetches secrets at startup | Pattern 2 (Managed Identity) |
| Corporate internal tool        | Pattern 3 (Entra ID)         |
| Teams / M365 integration       | Pattern 3 (Entra ID)         |
| App needs DB **and** user auth | Patterns 2 + 1 or 2 + 3      |

## Security invariants (always true)

- Never store passwords in plain text — use `pwdlib[argon2]` (argon2id)
- Always use `secrets.compare_digest()` for timing-safe comparisons
- JWT expiry ≤ 15 minutes for access tokens; use refresh tokens for longevity
- Never put `SECRET_KEY` or Azure client secrets in source code — use Key Vault or environment variables injected by the platform
- Return `401 Unauthorized` for expired/invalid tokens; `403 Forbidden` for valid token but insufficient permissions
