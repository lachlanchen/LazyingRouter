# LLM Gateway and Shadow API Market Research

Date: 2026-05-31

Purpose: document the current LLM gateway, proxy, router, and shadow-API landscape for LazyRouter product design. This note is a product and security reference, not legal advice.

## Executive Summary

The market has three distinct categories that are often mixed together:

1. Legitimate hosted gateways: OpenRouter, Vercel AI Gateway, Portkey Cloud, Requesty, Cloudflare AI Gateway, and Helicone Gateway. These usually sell routing, billing normalization, fallback, observability, team controls, and model coverage.
2. Self-hosted control planes: LiteLLM, Portkey Gateway self-hosted, New API, and similar projects. These let the operator keep policy, keys, routing, logs, and usage controls inside their own infrastructure.
3. Grey-market or shadow APIs: opaque "OpenAI/Claude proxy", "Claude transfer station", account-pooling, reverse-proxy, or ultra-cheap relay services. These often obscure who owns upstream credentials, what model actually answered, and whether prompts or outputs are retained.

Recommended defaults:

- Fastest hosted aggregator for testing: OpenRouter.
- Best self-hosted proxy/control plane: LiteLLM.
- Best enterprise governance product: Portkey.
- Best base for LazyRouter right now: New API plus LazyRouter-specific trust policy, account credits, usage metering, and provider-class metadata.
- Avoid for sensitive workloads: grey-market/shadow APIs, including claude-api.org, unless the task is explicitly low-risk and disposable.

## Practical Ranking

| Rank | Provider | Best For | Main Reason |
| --- | --- | --- | --- |
| 1 | OpenRouter | Fast testing and broad model access | One OpenAI-compatible API, broad model catalog, provider routing, usable privacy controls. |
| 2 | LiteLLM | Serious self-hosted infrastructure | Broad provider support, virtual keys, budgets, fallback routing, OpenTelemetry, and local control. |
| 3 | Portkey | Enterprise governance | Gateway plus guardrails, audit logs, retention controls, hybrid/self-host/air-gapped options. |
| 4 | Vercel AI Gateway | Vercel and AI SDK apps | Strong developer experience for web apps with unified gateway billing and routing. |
| 5 | Requesty | Hosted startup/team gateway | Anthropic/OpenAI-compatible routing, failover, and governance, but requires careful privacy review. |
| 6 | Cloudflare AI Gateway | Cloudflare-centric infra | Strong edge/security integration, logging, DLP, rate limits, and unified billing. |
| 7 | Helicone Gateway | Observability-first teams | Good logs, traces, provider routing, and self-host option. |
| Avoid | claude-api.org and similar relays | Low-risk experiments only | Third-party relay, not official Anthropic/OpenAI/Google access; opaque upstream channels and weak trust posture. |

## What Differentiates a Serious Gateway

A serious gateway should do more than forward requests:

- Normalize OpenAI-compatible and provider-native API shapes.
- Centralize user keys, virtual keys, model aliases, and spending limits.
- Route across official upstream providers with explicit fallback rules.
- Track usage, cost, latency, failures, and provider health.
- Make prompt/body logging configurable and disabled by default for sensitive deployments.
- Separate operational metadata from full prompt/output retention.
- Expose auditable policy: who can use which model, which provider class is allowed, and under what data-sensitivity level.
- Preserve model identity and upstream response metadata so downstream apps can verify what actually answered.

For LazyRouter, the durable application contract should be internal model aliases such as `lazying/auto`, `lazying/fast`, `lazying/main`, `lazying/reasoning`, or `lazying/writer`. Provider-specific names should live behind router configuration.

## Provider Comparison

| Provider | Hosted or Self-hosted | Auth Model | Routing and Fallback | Privacy and Logging | LazyRouter Use |
| --- | --- | --- | --- | --- | --- |
| OpenRouter | Hosted | OpenRouter API key and OpenRouter credits | Provider routing, fallback, load balancing, provider filters | Prompts pass through OpenRouter and upstream provider; private logging controls and provider privacy filters exist | Good upstream fallback or prototype provider. Do not make it the only long-term control plane. |
| LiteLLM | Self-hosted or hosted enterprise | Proxy master/virtual keys; upstream keys usually controlled by operator | Broad routing, fallbacks, health checks, budgets, tag routing | Self-hosting avoids adding an extra hosted intermediary beyond chosen upstream provider | Strong option behind LazyRouter or as a reference implementation for routing policy. |
| Vercel AI Gateway | Hosted | Vercel gateway key or OIDC; BYOK available | Dynamic provider choice, fallbacks, provider ordering | Good Vercel ecosystem defaults, but still adds Vercel in path | Useful for Vercel products, less ideal as general CLI/research control plane. |
| Portkey | Hosted, self-hosted, hybrid, air-gapped | Portkey gateway keys and centrally managed upstream keys | Retries, load balancing, canary routing, caching | Strong audit/logging/retention story, especially enterprise deployments | Best governance reference for admin UI and policy design. |
| Requesty | Hosted | Requesty API key | Smart routing, failover, caching, compatible endpoints | Privacy behavior is product/mode dependent; verify EU/zero-retention claims before relying on them | Interesting hosted competitor; useful feature benchmark. |
| Cloudflare AI Gateway | Hosted | Cloudflare token, unified billing, BYOK, or provider headers | Retries, fallbacks, caching, rate limits, DLP | Payload logging must be configured deliberately; Cloudflare is in request path | Good benchmark for logging, rate limits, and DLP. |
| Helicone Gateway | Hosted and self-hosted | Helicone API key, credits, optional BYOK | Cheapest-provider routing, failover, load balancing | Observability is central, so hosted logging must be reviewed carefully | Good benchmark for trace UI and usage analytics. |
| claude-api.org | Hosted third-party relay | Site-issued key; appears operator-managed upstream channels, not true BYOK | OpenAI/Anthropic-compatible relay behavior, but upstream routing details are opaque | Third-party relay sees traffic; public ownership and trust anchors are weak | Treat as high-risk. Do not use for production, secrets, private code, manuscripts, regulated data, or customer data. |

## claude-api.org Assessment

claude-api.org is not an official Anthropic endpoint. It presents itself as an AI API relay or aggregation gateway for Claude, GPT, Gemini, and related clients, but public materials do not show first-party commercial affiliation with Anthropic, OpenAI, or Google.

Confident assessment:

- It is a third-party proxy/relay, not official Anthropic access.
- It appears to use site-managed upstream channels or credentials rather than requiring the user to bring official provider keys.
- User prompts and outputs necessarily pass through the relay and then through upstream providers.
- Public ownership, audit, compliance, and vendor-risk materials are not strong enough for production trust.
- It may be easy to point Claude Code or OpenAI-compatible tools at it, but ease of use is not evidence of safety.

Not proven from public evidence alone:

- That it specifically uses stolen credentials.
- That it specifically substitutes cheaper models.
- That it specifically resells logs.

Practical policy:

- Do not route sensitive LazyRouter traffic through claude-api.org.
- If a user insists on configuring it, mark the channel as `high_risk_shadow_api`.
- Disable it by default for code, manuscripts, private research, private business data, secrets, or any regulated data.
- Require explicit admin acknowledgement before enabling it.
- Never present it in the UI as equivalent to official Anthropic, OpenAI, Google, OpenRouter, LiteLLM, Portkey, or Cloudflare channels.

## Security Reports and Risk Themes

The research record since 2024 points to the same core risks:

- Fraudulent-account proxy networks can industrialize access to frontier models.
- Grey-market "transfer stations" can be subsidized by account abuse, stolen cards, stolen credentials, or unexplained upstream channels.
- Shadow APIs can misrepresent which model served a request.
- Malicious intermediary routers can inject payloads or exfiltrate secrets from agent workflows.
- Stolen API-key resale and LLMjacking are already practical attack patterns.
- Self-hosted gateways still need supply-chain hygiene, version pinning, credential rotation, and restricted outbound access.

Product implications for LazyRouter:

- Treat the router as a high-value credential concentrator.
- Do not log full prompts by default.
- Make sensitive-data mode incompatible with high-risk channels.
- Preserve upstream provider metadata in every response and usage event.
- Add a visible provider trust level to the admin UI and API.
- Make user-facing model aliases stable while upstream routing stays configurable.

## Recommended LazyRouter Architecture

Preferred deployment path:

```text
AgInTiFlow / AAPS / apps
  -> LazyRouter OpenAI-compatible API
    -> official provider keys
    -> self-hosted LiteLLM or official provider gateways
    -> OpenRouter as optional hosted breadth/fallback
    -> high-risk relays disabled by default
```

Key design rules:

- LazyRouter should own users, credits, quotas, usage records, provider policy, model aliases, and channel risk levels.
- Provider adapters should not define LazyRouter semantics.
- Every upstream channel should have an explicit `provider_class`.
- Every model alias should have an explicit routing policy.
- Every high-risk provider should require an opt-in policy waiver.
- Full prompt/output retention should be opt-in, time-limited, and visible.

Suggested provider classes:

```yaml
provider_classes:
  official_provider:
    examples: [openai, anthropic, google, deepseek, mistral, groq]
    default_sensitive_allowed: true
  hosted_gateway:
    examples: [openrouter, vercel_ai_gateway, requesty, cloudflare_ai_gateway, helicone_hosted, portkey_hosted]
    default_sensitive_allowed: review_required
  self_hosted_gateway:
    examples: [litellm_self_hosted, portkey_self_hosted, lazyrouter_internal]
    default_sensitive_allowed: true
  shadow_api:
    examples: [claude-api.org, transfer_station, pooled_account_proxy]
    default_sensitive_allowed: false
```

Suggested model aliases:

```yaml
models:
  lazying/fast:
    purpose: low-cost simple chat, routing, summaries
    preferred: deepseek/deepseek-chat or openai/gpt-4.1-mini equivalent
  lazying/main:
    purpose: ordinary coding, writing, research
    preferred: official strong general model
  lazying/reasoning:
    purpose: high-stakes design, debugging, multi-step analysis
    preferred: official reasoning model
  lazying/writer:
    purpose: long-form writing with minimal agent/system context
    preferred: writing-optimized model route
  lazying/auto:
    purpose: route by task complexity and sensitivity
    preferred: policy router
```

## Migration Pattern for Apps

Apps should depend on an OpenAI-compatible configuration boundary:

```bash
export LLM_BASE_URL="https://router.lazying.art/v1"
export LLM_API_KEY="lzyr-user-or-service-key"
export LLM_MODEL="lazying/auto"
```

Minimal Python client:

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url=os.environ["LLM_BASE_URL"],
    api_key=os.environ["LLM_API_KEY"],
)

response = client.chat.completions.create(
    model=os.getenv("LLM_MODEL", "lazying/auto"),
    messages=[
        {"role": "system", "content": "You are a concise research assistant."},
        {"role": "user", "content": "Give three tradeoffs of using an LLM gateway."},
    ],
    temperature=0.2,
)

print(response.choices[0].message.content)
```

Hosted pilot examples:

```bash
# OpenRouter
export LLM_BASE_URL="https://openrouter.ai/api/v1"
export LLM_MODEL="anthropic/claude-sonnet-4.5"

# Requesty
export LLM_BASE_URL="https://router.requesty.ai/v1"
export LLM_MODEL="anthropic/claude-sonnet-4.5"

# LazyRouter
export LLM_BASE_URL="https://router.lazying.art/v1"
export LLM_MODEL="lazying/auto"
```

Self-hosted LiteLLM-style backend example:

```yaml
model_list:
  - model_name: primary-chat
    litellm_params:
      model: openai/gpt-4.1
      api_key: os.environ/OPENAI_API_KEY

  - model_name: primary-chat
    litellm_params:
      model: anthropic/claude-sonnet-4.5
      api_key: os.environ/ANTHROPIC_API_KEY

router_settings:
  routing_strategy: simple-shuffle
  fallbacks:
    - primary-chat:
        - openai/gpt-4.1
        - anthropic/claude-sonnet-4.5

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
```

This keeps application code stable while router policy changes behind the base URL and model alias.

## LazyRouter Engineering Backlog From This Research

1. Add `provider_class`, `trust_level`, `sensitive_allowed`, and `requires_admin_ack` fields for channels.
2. Add admin UI warnings for hosted gateways and hard warnings for shadow APIs.
3. Add a per-request sensitivity flag, with safe defaults for code, manuscripts, secrets, private research, and customer data.
4. Add a policy layer that blocks high-risk channels for sensitive requests unless explicitly overridden.
5. Add stable model aliases and routing profiles: `lazying/fast`, `lazying/main`, `lazying/reasoning`, `lazying/writer`, and `lazying/auto`.
6. Add an AgInTiFlow provider adapter for LazyRouter using the OpenAI-compatible endpoint and usage/credits API.
7. Add usage and credit APIs that AgInTiFlow can query after login.
8. Add retention controls: operational metadata retention, prompt/output retention, and audit-log retention should be configured separately.
9. Add upstream response metadata preservation so callers can see the actual provider/channel/model used.
10. Add a security reference page explaining why grey-market APIs are not treated as normal providers.

## Source Links

Official and product documentation:

- New API: https://github.com/QuantumNous/new-api
- New API docs: https://docs.newapi.pro/
- OpenRouter quickstart: https://openrouter.ai/docs/quickstart
- OpenRouter provider routing: https://openrouter.ai/docs/features/provider-routing
- OpenRouter privacy and logging: https://openrouter.ai/docs/features/privacy-and-logging
- LiteLLM docs: https://docs.litellm.ai/docs/
- LiteLLM proxy docs: https://docs.litellm.ai/docs/proxy/quick_start
- LiteLLM virtual keys: https://docs.litellm.ai/docs/proxy/virtual_keys
- LiteLLM reliability and fallbacks: https://docs.litellm.ai/docs/proxy/reliability
- Vercel AI Gateway: https://vercel.com/docs/ai-gateway
- Portkey docs: https://portkey.ai/docs
- Portkey open-source gateway: https://github.com/Portkey-AI/gateway
- Requesty docs: https://docs.requesty.ai/
- Cloudflare AI Gateway: https://developers.cloudflare.com/ai-gateway/
- Helicone docs: https://docs.helicone.ai/
- Helicone GitHub: https://github.com/Helicone/helicone
- Anthropic docs: https://docs.anthropic.com/
- claude-api.org: https://claude-api.org/

Security and market-risk references to verify before quoting in public marketing:

- Anthropic threat intelligence and transparency reports: https://www.anthropic.com/news
- Microsoft Digital Defense reports: https://www.microsoft.com/en-us/security/security-insider/intelligence-reports/
- Sysdig threat research on LLMjacking: https://sysdig.com/blog/
- CISPA publications: https://cispa.de/en/research/publications
- ChinaTalk coverage of Chinese AI transfer stations: https://www.chinatalk.media/
- Tom's Hardware AI and security coverage: https://www.tomshardware.com/

## Bottom Line

LazyRouter should not present itself as just another proxy. The valuable product is a trusted control plane: user accounts, credits, model aliases, routing policy, provider trust metadata, usage accounting, and safe defaults. OpenRouter is the best hosted benchmark for breadth, LiteLLM is the best self-hosted benchmark for control, and Portkey is the best governance benchmark. Shadow APIs should be explicitly classified and blocked for sensitive work by default.
