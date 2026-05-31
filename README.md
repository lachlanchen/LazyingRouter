<p align="center">
  <a href="https://lazying.art">
    <img src="web/default/public/logo.png" alt="LazyingArt logo" width="140" />
  </a>
</p>

<h1 align="center">LazyingRouter</h1>

<p align="center">
  <strong>A private AI API gateway for accounts, user keys, credits, model routing, and upstream provider aggregation.</strong>
</p>

<p align="center">
  <a href="https://router.lazying.art">router.lazying.art</a>
  ·
  <a href="docs/lazyingrouter/README.md">Operator guide</a>
  ·
  <a href="docs/lazyingrouter/provider-setup.md">Provider setup</a>
  ·
  <a href="README.en.md">Upstream New API docs</a>
</p>

<p align="center">
  English |
  <a href="docs/lazyingrouter/i18n/README.zh-Hans.md">简体中文</a> |
  <a href="docs/lazyingrouter/i18n/README.zh-Hant.md">繁體中文</a> |
  <a href="docs/lazyingrouter/i18n/README.ja.md">日本語</a> |
  <a href="docs/lazyingrouter/i18n/README.fr.md">Français</a> |
  <a href="docs/lazyingrouter/i18n/README.de.md">Deutsch</a> |
  <a href="docs/lazyingrouter/i18n/README.es.md">Español</a> |
  <a href="docs/lazyingrouter/i18n/README.ko.md">한국어</a> |
  <a href="docs/lazyingrouter/i18n/README.ru.md">Русский</a> |
  <a href="docs/lazyingrouter/i18n/README.pt.md">Português</a> |
  <a href="docs/lazyingrouter/i18n/README.ar.md">العربية</a>
</p>

---

## What It Is

LazyingRouter is a self-hosted AI API aggregator built from the mature open-source New API gateway. It lets an operator issue user API keys, assign credits and quotas, route model requests to authorized upstream providers, and inspect usage from a web dashboard.

The immediate goal is to make AgInTiFlow and other LazyingArt tools login through one LazyingRouter account/API key, while LazyingRouter owns upstream routing, quota accounting, and provider credentials.

## Why This Exists

Directly wiring every application to OpenRouter, Venice, GRSAI, Claude-compatible providers, and future model providers becomes hard to audit and hard to bill. LazyingRouter centralizes that layer:

- One account and one API key per user or app.
- One admin panel for upstream provider keys.
- One usage ledger for text, image, and future multimodal requests.
- One model namespace for AgInTiFlow and sibling tools.
- Clear separation between user-facing keys and operator-owned upstream keys.

## Core Capabilities

- User registration and login.
- Admin setup flow.
- User roles and API token management.
- Credit/quota accounting.
- Usage logs and dashboards.
- OpenAI-compatible API relay.
- Claude Messages relay.
- Gemini-compatible relay.
- Built-in and custom provider channels.
- Weighted routing, retry, and model mapping.
- Docker deployment with PostgreSQL and Redis.

## Target Upstream Providers

| Provider | First Integration Path | Notes |
| --- | --- | --- |
| OpenAI | Built-in OpenAI channel | Use `https://api.openai.com`; supports standard OpenAI-compatible routes. |
| OpenRouter | Built-in OpenRouter channel | Use `https://openrouter.ai/api`; optional headers include `HTTP-Referer` and `X-OpenRouter-Title`. |
| DeepSeek | Built-in DeepSeek channel | Use `https://api.deepseek.com`; defaults to `deepseek-chat` and `deepseek-reasoner`. |
| Venice | OpenAI-compatible channel | Use `https://api.venice.ai/api`; do not add trailing `/v1` because this codebase appends `/v1/...`. |
| GRSAI | Image-generation channel/custom adaptor | Treat as image-first; only expose through an OpenAI-compatible channel when a compatible base URL and models are configured. |
| claude-api.org | Claude Messages or OpenAI-compatible custom channel | Pick channel mode from the actual endpoint contract; do not assume Anthropic semantics. |

See `docs/lazyingrouter/provider-setup.md` for the safe bootstrap command, environment variables, and client examples.

## Local Development

```bash
cd /home/lachlan/ProjectsLFS/Agent/LazyingRouter
cp .env.lazyingrouter.example .env
go run . --port 3218
```

Open:

```text
http://127.0.0.1:3218
```

If Go is not installed locally, use Docker:

```bash
cd /home/lachlan/ProjectsLFS/Agent/LazyingRouter
SESSION_SECRET="$(openssl rand -hex 32)" \
CRYPTO_SECRET="$(openssl rand -hex 32)" \
POSTGRES_PASSWORD="$(openssl rand -hex 24)" \
REDIS_PASSWORD="$(openssl rand -hex 24)" \
docker compose -f docker-compose.lazyingrouter.yml up -d --build
```

## Verified Development Image

The current fork has been verified with:

```bash
docker build -t lazying-router:dev .
docker run -d --name lazying-router-dev -p 3218:3000 \
  -e SYSTEM_NAME=LazyingRouter \
  -e FOOTER_HTML="LazyingRouter local dev gateway" \
  -e SQLITE_PATH=/data/lazyingrouter.sqlite \
  -e MEMORY_CACHE_ENABLED=true \
  -v /tmp/lazying-router-dev-data:/data \
  lazying-router:dev
curl -fsS http://127.0.0.1:3218/api/status
```

Expected status includes:

```json
{
  "success": true,
  "data": {
    "system_name": "LazyingRouter"
  }
}
```

## AgInTiFlow Integration Target

AgInTiFlow should later add a `lazyingrouter` provider:

```text
LAZYINGROUTER_API_KEY=<user-issued LazyingRouter API key>
LAZYINGROUTER_BASE_URL=https://router.lazying.art/v1
LAZYINGROUTER_MODEL=lazying/auto
```

Local development defaults:

```text
LAZYINGROUTER_BASE_URL=http://127.0.0.1:3218/v1
LAZYINGROUTER_MODEL=lazying/auto
```

Planned AgInTiFlow commands:

```bash
aginti auth lazyingrouter
aginti keys set lazyingrouter
aginti --provider lazyingrouter
```

## Security Rules

- Never commit upstream provider keys.
- Never expose upstream provider keys to users.
- Keep user-issued LazyingRouter API keys separate from operator upstream keys.
- Disable public registration until email verification, abuse limits, payment policy, and legal/compliance requirements are configured.
- Add upstream channels one by one and test each channel with low-cost requests before exposing it broadly.
- Keep provider errors visible; do not hide missing quota, missing auth, or upstream rate limits as generic model errors.

## Upstream Attribution

LazyingRouter is based on the open-source New API project:

- Upstream repository: <https://github.com/QuantumNous/new-api>
- Upstream documentation: <https://docs.newapi.pro>
- Original One API lineage: <https://github.com/songquanpeng/one-api>

This repository keeps the upstream license and third-party notices. Review `LICENSE`, `NOTICE`, and `THIRD-PARTY-LICENSES.md` before any public service launch.

## Public Endpoint

Production URL target:

```text
https://router.lazying.art
```

DNS, TLS, payment, and public registration policy should be configured before this is opened beyond trusted users.
