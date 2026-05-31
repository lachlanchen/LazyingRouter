# AgInTiFlow Account Login Design For LazyingRouter

Date: 2026-05-31

Purpose: define how LazyingRouter should let a paid user authorize AgInTiFlow without exposing upstream provider keys, while keeping LazyingRouter's existing token, quota, model routing, and billing logic consistent.

## Product Goal

A normal user should be able to:

1. Install AgInTiFlow.
2. Run `aginti login lazyingrouter` or click "Login with LazyingRouter".
3. Sign in or register on LazyingRouter.
4. Pay or top up in LazyingRouter.
5. Use AgInTiFlow immediately through `https://router.lazying.art/v1`.

The user should not paste OpenAI, DeepSeek, Venice, OpenRouter, GRS AI, Claude, or other upstream provider keys into AgInTiFlow. LazyingRouter should be the account, billing, quota, and provider-routing authority.

## Current LazyingRouter State

Relevant source files:

- `router/api-router.go`: user, token, usage, subscription, payment, model, channel, and admin API routes.
- `router/dashboard.go`: OpenAI-compatible billing endpoints protected by token auth.
- `router/relay-router.go`: OpenAI, Anthropic, Gemini, and other relay routes protected by token auth.
- `controller/user.go`: user register/login/session, self APIs, top-up/payment, and access-token helper.
- `controller/token.go`: user token CRUD, token key retrieval, token status, and token usage.
- `middleware/auth.go`: session auth, token auth, read-only token auth, and authorization header normalization.
- `model/token.go`: token model and `ValidateUserToken()`.
- `service/quota.go`: pre-consume and post-consume quota behavior.

The existing foundation is close to what AgInTiFlow needs:

- Users already register and log in through LazyingRouter.
- Users already own API tokens.
- Tokens already have status, expiration, model limits, group, used quota, remaining quota, and unlimited quota flags.
- Relay routes already accept `Authorization: Bearer sk-...`.
- `ValidateUserToken()` rejects invalid, expired, exhausted, and zero-quota non-unlimited tokens.
- Usage status already exists under `/api/usage/token/` with read-only token auth.
- OpenAI-compatible billing status exists under `/dashboard/billing/*` and `/v1/dashboard/billing/*`.

The missing product piece is a trusted app authorization flow that creates or rotates a normal LazyingRouter token for AgInTiFlow without forcing the user to manually create, reveal, and paste a key.

## Current Token Behavior

Current token API:

```text
GET    /api/token/
POST   /api/token/
GET    /api/token/:id
POST   /api/token/:id/key
PUT    /api/token/
DELETE /api/token/:id
POST   /api/token/batch
POST   /api/token/batch/keys
GET    /api/usage/token/
```

The normal token creation endpoint creates a key internally, but does not return the raw key in the creation response. The raw key can be fetched later through `POST /api/token/:id/key`.

This is appropriate for the dashboard, but not ideal for a CLI app login flow. AgInTiFlow needs a one-time token delivery response after user approval.

Important middleware detail:

- `TokenAuth()` trims `Bearer `, trims `sk-`, then splits the remaining key on `-` and uses the first segment.
- This means app-issued token keys should use the normal `common.GenerateKey()` shape and avoid embedding metadata with hyphens inside the actual key material.

## Proposed Minimal Design

Add a device/app authorization layer on top of existing users and tokens.

Do not build a full OAuth provider first. The minimal design is:

- LazyingRouter session login remains the user login source.
- AgInTiFlow receives one normal LazyingRouter API token after the user approves the device.
- That token is visible in the user's token list, revocable, model-limited, and usage-tracked.
- LazyingRouter enforces user balance and token validity on every `/v1` request.

The implicit AgInTiFlow token should behave like a normal user API token, not like an upstream provider key.

## Device Authorization Flow

### 1. Start

AgInTiFlow calls:

```http
POST /api/app-auth/device/start
Content-Type: application/json

{
  "app": "agintiflow",
  "device_name": "hostname/project",
  "scopes": ["chat", "models", "usage", "artifacts"],
  "client_nonce": "random",
  "preferred_model": "lazying/auto"
}
```

LazyingRouter creates a pending authorization record and returns:

```json
{
  "success": true,
  "data": {
    "login_url": "https://router.lazying.art/app-auth/authorize?device_code=...",
    "device_code": "opaque",
    "user_code": "ABCD-EFGH",
    "expires_at": 1790000000,
    "poll_interval_seconds": 3
  }
}
```

### 2. User Approves In Browser

Browser URL:

```text
/app-auth/authorize?device_code=...
```

If the user is not logged in, LazyingRouter shows normal login/register first. After login, the page shows:

- App: AgInTiFlow.
- Device name.
- Requested scopes.
- Default model route: `lazying/auto`.
- Current balance and top-up prompt if balance is insufficient.
- Buttons: Authorize, Cancel.

### 3. Token Creation

On approval, LazyingRouter creates or rotates a token:

```text
Name: AgInTiFlow - <device_name>
UserId: current user id
Group: user's selected/default group
ModelLimitsEnabled: true
ModelLimits: curated LazyingRouter model aliases and allowed direct model names
ExpiredTime: recommended 90 days to 1 year, or -1 for no expiry if policy allows
Status: enabled
```

The token key should be delivered once to the polling client and never shown again except through existing explicit "show key" dashboard behavior.

### 4. Poll

AgInTiFlow calls:

```http
POST /api/app-auth/device/poll
Content-Type: application/json

{
  "device_code": "opaque",
  "client_nonce": "same-random"
}
```

Pending response:

```json
{
  "success": true,
  "data": {
    "status": "pending",
    "poll_interval_seconds": 3
  }
}
```

Approved response:

```json
{
  "success": true,
  "data": {
    "status": "approved",
    "api_base": "https://router.lazying.art/v1",
    "api_key": "sk-...",
    "model": "lazying/auto",
    "token_id": 123,
    "user_id": 456,
    "display_name": "Lachlan",
    "quota": {
      "available": 123456,
      "used": 789,
      "display": "$12.34",
      "topup_url": "https://router.lazying.art/topup"
    }
  }
}
```

Denied, expired, or cancelled responses should be explicit and should not create a token.

## Quota And Funding Semantics

This is the most important implementation decision.

Current token validation rejects a non-unlimited token when `RemainQuota <= 0`. Current quota code also checks user quota and token quota in several paths. Therefore, an AgInTiFlow app token must not accidentally bypass payment.

Recommended durable design:

- Add an app-token funding mode that is backed by the user's wallet or subscription.
- A token can be an `app_token` for `agintiflow`.
- It can be `UnlimitedQuota` only if the billing/session code still debits user wallet or subscription and cannot bypass money.
- If wallet-backed app tokens are not implemented yet, allocate token quota from the user's balance on approval and provide an automatic refresh/reallocation path after top-up.

Do not simply create default unlimited app tokens unless tests prove that every paid request still consumes user balance or subscription and stops when the user has no money.

Suggested normalized status response:

```json
{
  "success": true,
  "data": {
    "user": {
      "id": 456,
      "display_name": "Lachlan",
      "group": "default"
    },
    "token": {
      "id": 123,
      "name": "AgInTiFlow - MacBook",
      "status": "enabled",
      "expires_at": 1790000000
    },
    "quota": {
      "available": 123456,
      "used": 789,
      "unlimited_token": false,
      "billing_source": "wallet",
      "display": "$12.34",
      "topup_url": "https://router.lazying.art/topup"
    },
    "models": {
      "default": "lazying/auto",
      "allowed": ["lazying/auto", "lazying/fast", "lazying/main", "lazying/writer"]
    }
  }
}
```

AgInTiFlow can call this before runs, but LazyingRouter must still enforce quota during every relay request.

## Endpoints To Add

Recommended v1 endpoints:

```text
POST /api/app-auth/device/start
GET  /app-auth/authorize
POST /api/app-auth/device/approve
POST /api/app-auth/device/poll
GET  /api/app-auth/status
POST /api/app-auth/token/revoke
```

Auth policy:

- `device/start`: public, rate-limited, no session required.
- `authorize`: browser page, session login required before approval.
- `device/approve`: session auth required.
- `device/poll`: public but requires valid device code and nonce; rate-limited.
- `status`: token auth read-only.
- `token/revoke`: token auth for self-revoke or session auth for dashboard revoke.

Suggested database table:

```sql
app_device_authorizations (
  id,
  app_id,
  device_name,
  device_code_hash,
  user_code_hash,
  client_nonce_hash,
  status,
  user_id,
  token_id,
  scopes_json,
  expires_at,
  approved_at,
  delivered_at,
  created_at,
  updated_at,
  ip_hash,
  user_agent_hash
)
```

The raw device code should not be stored.

## Token UI Requirements

In the LazyingRouter dashboard, an AgInTiFlow token should be understandable:

- Label: `AgInTiFlow`.
- Device: hostname/project label.
- Last used.
- Current status.
- Model limits.
- Quota funding source.
- Revoke button.
- Rotate/re-login button.

This prevents hidden "magic" tokens while avoiding manual key copy/paste.

## Model Alias Contract

Expose stable LazyingRouter aliases to AgInTiFlow:

```text
lazying/auto
lazying/fast
lazying/main
lazying/reasoning
lazying/writer
lazying/coder
```

Provider-specific upstream model names should stay behind LazyingRouter channel and routing configuration. This lets AgInTiFlow keep stable defaults while LazyingRouter changes provider mix, fallback, pricing, or risk policy.

## Security Rules

- Never send upstream provider keys to AgInTiFlow.
- App auth token delivery is one-time.
- Pending device codes expire quickly, for example 10 minutes.
- Polling is rate-limited.
- Approvals are bound to a client nonce or code challenge.
- Raw device codes are stored only as hashes.
- App tokens are normal revocable user tokens.
- Every issue, rotate, revoke, and failed poll event should be auditable.
- Token status and usage endpoints must redact raw keys.
- Quota failure should return a stable machine-readable error and top-up URL.

## AgInTiFlow Client Expectations

AgInTiFlow will store:

```env
LAZYINGROUTER_API_KEY=sk-...
LAZYINGROUTER_BASE_URL=https://router.lazying.art/v1
LAZYINGROUTER_MODEL=lazying/auto
LAZYINGROUTER_ACCOUNT_URL=https://router.lazying.art
LAZYINGROUTER_TOKEN_ID=123
LAZYINGROUTER_USER_ID=456
```

AgInTiFlow will call:

```http
GET /api/app-auth/status
Authorization: Bearer sk-...
```

or, if v1 status is not ready:

```http
GET /api/usage/token/
Authorization: Bearer sk-...
```

Then it will use:

```http
POST /v1/chat/completions
Authorization: Bearer sk-...
```

with model `lazying/auto` by default.

## Acceptance Tests

Minimum LazyingRouter TDV tests:

1. Fresh user can register, top up, and authorize AgInTiFlow without seeing upstream keys.
2. Device flow returns a token only after browser approval.
3. The issued token appears in the user's token list and can be revoked.
4. `GET /api/app-auth/status` returns quota, token, user, model defaults, and top-up URL.
5. `POST /v1/chat/completions` with the app token works while quota is available.
6. A user with no money receives a stable quota error and cannot continue paid relay calls.
7. Revoked token fails immediately.
8. Expired device code cannot be used.
9. Raw token is not logged by server, web UI, or AgInTiFlow event logs.
10. Model limits prevent the app token from using disallowed models.

## Implementation Order

1. Add design tests around current token quota behavior so app tokens cannot bypass payment.
2. Add the `app_device_authorizations` model and migration.
3. Add `device/start`, `authorize`, `approve`, and `poll`.
4. Create app-token issuance through a service function instead of direct controller duplication.
5. Add normalized status and revoke endpoints.
6. Add dashboard UI for AgInTiFlow devices.
7. Add AgInTiFlow client support after the server flow is stable.

## Non-Goals For V1

- Do not implement a complete third-party OAuth platform unless another app needs it.
- Do not expose upstream provider keys.
- Do not make AgInTiFlow know LazyingRouter channel internals.
- Do not make users manually copy token keys for the normal path.
- Do not merge app tokens with external OAuth access tokens; keep them as user API tokens with app metadata.

