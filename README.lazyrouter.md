<p align="center">
  <a href="https://lazying.art">
    <img src="web/default/public/logo.png" alt="LazyingArt logo" width="140" />
  </a>
</p>

# LazyRouter

LazyRouter is a private AI API aggregator project under `/home/lachlan/ProjectsLFS/Agent/LazyRouter`.

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

## LazyRouter Additions In This Fork

- Default product name changed to `LazyRouter`.
- Runtime branding can be set with `SYSTEM_NAME`, `FOOTER_HTML`, `LOGO_URL`, and `TOP_UP_LINK`.
- Local env template: `.env.lazyrouter.example`.
- Local compose file: `docker-compose.lazyrouter.yml`.
- Provider setup and AgInTiFlow integration plan: `docs/lazyrouter/README.md`.
- Provider bootstrap tool: `scripts/bootstrap-provider-channels.py`.
- OpenAI-compatible provider setup guide: `docs/lazyrouter/provider-setup.md`.

## Local Development

```bash
cd /home/lachlan/ProjectsLFS/Agent/LazyRouter
cp .env.lazyrouter.example .env
go run . --port 3218
```

Open:

```text
http://127.0.0.1:3218
```

## Docker Development

```bash
cd /home/lachlan/ProjectsLFS/Agent/LazyRouter
SESSION_SECRET="$(openssl rand -hex 32)" \
CRYPTO_SECRET="$(openssl rand -hex 32)" \
POSTGRES_PASSWORD="$(openssl rand -hex 24)" \
REDIS_PASSWORD="$(openssl rand -hex 24)" \
docker compose -f docker-compose.lazyrouter.yml up -d --build
```

## First Provider Targets

- OpenAI: built-in OpenAI channel, base URL `https://api.openai.com`.
- OpenRouter: built-in OpenRouter channel, base URL `https://openrouter.ai/api`.
- DeepSeek: built-in DeepSeek channel, base URL `https://api.deepseek.com`.
- Venice: OpenAI-compatible channel, base URL `https://api.venice.ai/api`.
- GRSAI: native image generation is not OpenAI-compatible; only expose through a channel when a compatible base URL and model list are configured.
- claude-api.org: Claude Messages or OpenAI-compatible custom channel depending on endpoint.

Dry-run local provider bootstrap:

```bash
python3 scripts/bootstrap-provider-channels.py --fetch-models
```

See `docs/lazyrouter/provider-setup.md` for the Docker SQLite apply command and client examples.

## Next Integration With AgInTiFlow

AgInTiFlow should add a `lazyrouter` provider that reads:

```text
LAZYROUTER_API_KEY
LAZYROUTER_BASE_URL
LAZYROUTER_MODEL
```

Default local base URL:

```text
http://127.0.0.1:3218/v1
```

Do not put upstream provider keys in AgInTiFlow once LazyRouter is the account gateway. AgInTiFlow should use a LazyRouter user API token and let LazyRouter own upstream routing, usage, and credits.
