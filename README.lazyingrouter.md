# LazyingRouter

LazyingRouter is a private AI API aggregator project under `/home/lachlan/ProjectsLFS/Agent/LazyingRouter`.

It is based on the mature open-source New API gateway and keeps upstream attribution and license files intact. The fork is intended to route user-issued API keys and account credits to authorized upstream providers such as OpenRouter, Venice, GRSAI, and claude-api.org-compatible endpoints.

## What Works From The Base

- Website with login/register logic.
- Admin setup flow.
- User roles.
- User API tokens.
- Quota and credit accounting.
- Usage logs.
- Provider/channel routing.
- OpenAI-compatible API relay.
- Claude Messages relay.
- Custom provider channels.
- Weighted routing and retry.
- Docker deployment.

## LazyingRouter Additions In This Fork

- Default product name changed to `LazyingRouter`.
- Runtime branding can be set with `SYSTEM_NAME`, `FOOTER_HTML`, `LOGO_URL`, and `TOP_UP_LINK`.
- Local env template: `.env.lazyingrouter.example`.
- Local compose file: `docker-compose.lazyingrouter.yml`.
- Provider setup and AgInTiFlow integration plan: `docs/lazyingrouter/README.md`.

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

## Docker Development

```bash
cd /home/lachlan/ProjectsLFS/Agent/LazyingRouter
SESSION_SECRET="$(openssl rand -hex 32)" \
CRYPTO_SECRET="$(openssl rand -hex 32)" \
POSTGRES_PASSWORD="$(openssl rand -hex 24)" \
REDIS_PASSWORD="$(openssl rand -hex 24)" \
docker compose -f docker-compose.lazyingrouter.yml up -d --build
```

## First Provider Targets

- OpenRouter: built-in OpenRouter channel, base URL `https://openrouter.ai/api/v1`.
- Venice: custom OpenAI-compatible channel, base URL `https://api.venice.ai/api/v1`.
- GRSAI: image-generation channel/custom adaptor; verify request/response shape before exposing.
- claude-api.org: Claude Messages or OpenAI-compatible custom channel depending on endpoint.

## Next Integration With AgInTiFlow

AgInTiFlow should add a `lazyingrouter` provider that reads:

```text
LAZYINGROUTER_API_KEY
LAZYINGROUTER_BASE_URL
LAZYINGROUTER_MODEL
```

Default local base URL:

```text
http://127.0.0.1:3218/v1
```

Do not put upstream provider keys in AgInTiFlow once LazyingRouter is the account gateway. AgInTiFlow should use a LazyingRouter user API token and let LazyingRouter own upstream routing, usage, and credits.
