<p align="center">
  <a href="https://lazying.art">
    <img src="../../web/default/public/logo.png" alt="LazyingArt logo" width="140" />
  </a>
</p>

# LazyingRouter Adaptation Plan

LazyingRouter is a private AI API aggregator built on top of the mature open-source New API gateway. The goal is to provide OpenRouter-like account, key, quota, and routing behavior while preserving upstream mergeability.

## Base Project

Selected base: `QuantumNous/new-api`.

Why this base is appropriate:

- Built-in web UI, password registration, OAuth options, passkeys, user roles, API tokens, quota, recharge/accounting, usage logs, and admin dashboards.
- Supports OpenAI-compatible, Claude Messages, Gemini, OpenRouter, DeepSeek, Qwen, xAI, custom provider channels, weighted routing, retry, and model mapping.
- Supports OpenAI-compatible to Claude/Gemini format conversion, which is the main bridge AgInTiFlow needs.
- Actively maintained Go backend with embedded web frontends and Docker deployment.

Keep upstream attribution and AGPL obligations intact. Do not remove license notices.

## LazyingRouter Product Contract

LazyingRouter owns:

- User registration and login.
- User credits and quotas.
- User-issued API keys.
- Model list exposed to clients.
- Model-to-upstream routing.
- Upstream channel keys for OpenRouter, Venice, GRSAI, claude-api.org, and future providers.
- Usage accounting, logs, and admin controls.

Upstream providers own:

- Actual model inference.
- Provider-specific content rules.
- Provider-side billing and rate limits.
- Provider-specific model availability.

AgInTiFlow should treat LazyingRouter as a first-class provider with one account/API key, then consume usage and credit state from LazyingRouter instead of directly handling every upstream account.

## First Local Run

```bash
cd /home/lachlan/ProjectsLFS/Agent/LazyingRouter
cp .env.lazyingrouter.example .env
go run . --port 3218
```

Open:

```text
http://127.0.0.1:3218
```

For container deployment:

```bash
cd /home/lachlan/ProjectsLFS/Agent/LazyingRouter
SESSION_SECRET="$(openssl rand -hex 32)" \
CRYPTO_SECRET="$(openssl rand -hex 32)" \
POSTGRES_PASSWORD="$(openssl rand -hex 24)" \
REDIS_PASSWORD="$(openssl rand -hex 24)" \
docker compose -f docker-compose.lazyingrouter.yml up -d --build
```

## Provider Channel Mapping

### OpenRouter

Use the built-in OpenRouter channel when available.

- Upstream base URL: `https://openrouter.ai/api/v1`
- Auth: Bearer upstream key.
- Exposed route to clients: OpenAI-compatible `/v1/chat/completions` and model list.
- Default visible model can be `openrouter/auto`.
- Optional upstream headers: `HTTP-Referer` and `X-OpenRouter-Title` if supported by channel settings.

### Venice

Use a custom OpenAI-compatible channel unless a dedicated Venice channel is added later.

- Upstream base URL: `https://api.venice.ai/api/v1`
- Auth: Bearer upstream key.
- Exposed models should be curated, not blindly all upstream models.
- Start with text models and add image models only after billing and output accounting are verified.

### GRSAI

Use a custom channel for image-generation calls until a dedicated adaptor is implemented.

- Treat this as an image provider first, not a generic text LLM provider.
- Add model names under an image category and test request/response shape before exposing to users.
- If an endpoint cannot return SVG, return PNG and record `requested_format` and `actual_format`.

### claude-api.org

Use either Anthropic-compatible or OpenAI-compatible channel mode depending on the exact endpoint exposed by the upstream account.

- If the upstream exposes Claude Messages, use Claude/Anthropic mode.
- If the upstream exposes OpenAI-compatible or Responses-compatible endpoints, use Custom/OpenAI-compatible mode.
- Do not assume a third-party Claude reseller has the same safety, billing, or rate semantics as Anthropic.

## Required Admin Setup

1. Create the root admin user during first setup.
2. Disable public registration until email verification, abuse controls, and payment policy are configured.
3. Add upstream provider channels one by one.
4. Test each channel with a low-cost model before exposing it to normal users.
5. Define model aliases that AgInTiFlow will use, for example:
   - `lazying/auto`
   - `lazying/writing`
   - `lazying/coding`
   - `lazying/vision`
   - `lazying/image`
6. Assign user groups and quotas.
7. Create one user API token and verify OpenAI-compatible calls through LazyingRouter.

## AgInTiFlow Integration Target

AgInTiFlow should later add:

- `LAZYINGROUTER_API_KEY`
- `LAZYINGROUTER_BASE_URL`, defaulting to `http://127.0.0.1:3218/v1` for local testing.
- `LAZYINGROUTER_MODEL`, defaulting to `lazying/auto`.
- `/auth lazyingrouter` and `aginti keys set lazyingrouter`.
- Web settings provider option: `LazyingRouter`.
- Usage endpoint integration for credits and remaining quota.

Minimal client config:

```text
provider=lazyingrouter
baseURL=http://127.0.0.1:3218/v1
model=lazying/auto
apiKey=<user-issued LazyingRouter API key>
```

## Non-Negotiable Security Rules

- Never commit upstream provider keys.
- Never expose admin upstream keys to users.
- Public service operation requires legal/compliance review for API resale, tax, content safety, user identity, logs, and upstream terms.
- Keep provider failures visible; do not hide missing upstream quota or authentication errors as model failures.
- Apply per-user and per-model rate limits before enabling public registration.
