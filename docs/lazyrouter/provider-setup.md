# LazyRouter Provider Setup

This document describes the supported upstream provider presets and the client-facing API contract for LazyRouter.

LazyRouter is an OpenAI-compatible gateway for client applications. Users should call LazyRouter with a LazyRouter-issued API token. Upstream provider keys stay on the server side as admin-managed channels.

## Client Contract

Local development endpoint:

```text
http://127.0.0.1:3218/v1
```

Production target:

```text
https://router.lazying.art/v1
```

Python example:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:3218/v1",
    api_key="YOUR_LAZYROUTER_USER_TOKEN",
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Say hello from LazyRouter."}],
)

print(response.choices[0].message.content)
```

Curl example:

```bash
curl http://127.0.0.1:3218/v1/chat/completions \
  -H "Authorization: Bearer $LAZYROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "Give one sentence about routing."}]
  }'
```

## Provider Presets

| Provider | Channel type | Upstream base URL | Key variable | Model variable | Notes |
| --- | --- | --- | --- | --- | --- |
| OpenAI | Built-in OpenAI | `https://api.openai.com` | `OPENAI_API_KEY` | `OPENAI_MODELS` | Supports chat, embeddings, image/audio routes when the upstream model and route are enabled. |
| OpenRouter | Built-in OpenRouter | `https://openrouter.ai/api` | `OPENROUTER_API_KEY` | `OPENROUTER_MODELS` | Adds LazyRouter referer/title headers. Use `openrouter/auto` or provider-specific model ids. |
| DeepSeek | Built-in DeepSeek | `https://api.deepseek.com` | `DEEPSEEK_API_KEY` | `DEEPSEEK_MODELS` | Defaults to `deepseek-chat` and `deepseek-reasoner`. |
| Venice | OpenAI-compatible channel | `https://api.venice.ai/api` | `VENICE_API_KEY` | `VENICE_MODELS` | Configure text/chat models explicitly or use `--fetch-models`. Do not include `/v1` in `VENICE_BASE_URL` for this codebase. |
| GRSAI | Optional OpenAI-compatible channel | set `GRSAI_OPENAI_BASE_URL` or `GRSAI_BASE_URL` | `GRSAI_API_KEY` or `GRSAI` | `GRSAI_MODELS` | Native GRS AI Nano Banana image calls are not OpenAI-compatible. Only add this preset when you have a compatible base URL/model list. |

Important base URL rule: New API appends paths like `/v1/chat/completions` to channel `base_url`. For OpenAI-compatible providers, the base URL should usually omit the final `/v1`.

## Bootstrap Channels From Environment

Dry-run first:

```bash
cd /home/lachlan/ProjectsLFS/Agent/LazyRouter
python3 scripts/bootstrap-provider-channels.py --fetch-models
```

Apply to the local Docker SQLite database:

```bash
docker run --rm \
  -e OPENAI_API_KEY \
  -e OPENROUTER_API_KEY \
  -e DEEPSEEK_API_KEY \
  -e VENICE_API_KEY \
  -e GRSAI_API_KEY \
  -e GRSAI \
  -e VENICE_MODELS \
  -e GRSAI_OPENAI_BASE_URL \
  -e GRSAI_BASE_URL \
  -e GRSAI_MODELS \
  -v /tmp/lazy-router-dev-data:/data \
  -v "$PWD":/src \
  -w /src \
  python:3.12-alpine \
  python scripts/bootstrap-provider-channels.py \
    --db /data/lazyrouter.sqlite \
    --fetch-models \
    --allow-root-unpriced-models \
    --apply
```

Then restart LazyRouter so the running process reloads the channel cache:

```bash
docker restart lazy-router-dev
```

The script prints only whether keys are present. It never prints raw key values.

`--allow-root-unpriced-models` is a local/development convenience. It lets root/admin users test newly fetched provider models before model pricing is configured. For production, configure model prices or model ratios for every public model instead of relying on unpriced access.

## Environment Template

Copy `.env.lazyrouter.example` to `.env` for local development. Keep real provider keys out of git.

Common variables:

```text
OPENAI_API_KEY=
OPENAI_MODELS=gpt-4o-mini,gpt-4o,gpt-4.1-mini,gpt-4.1,o4-mini

OPENROUTER_API_KEY=
OPENROUTER_MODELS=openrouter/auto,anthropic/claude-sonnet-4.5,openai/gpt-5.1

DEEPSEEK_API_KEY=
DEEPSEEK_MODELS=deepseek-chat,deepseek-reasoner

VENICE_API_KEY=
VENICE_BASE_URL=https://api.venice.ai/api
VENICE_MODELS=

GRSAI_API_KEY=
GRSAI_OPENAI_BASE_URL=
GRSAI_MODELS=
```

## Admin Checklist

1. Create the root admin user through the setup screen.
2. Add or bootstrap upstream channels.
3. Fetch/test each channel in the admin UI.
4. Create model aliases only after the raw provider models work.
5. Configure model prices or model ratios for every public model.
6. Create a user API token.
7. Test `/v1/models` and `/v1/chat/completions` with that user token.
8. Disable public registration until abuse, payment, quota, and legal policy are ready.

## Scope Caveat

LazyRouter can provide an OpenRouter-like API surface for configured providers, user keys, quotas, logs, and routing. It is not yet a full public marketplace until payments, public model catalog policy, provider terms review, abuse controls, and production observability are completed.
