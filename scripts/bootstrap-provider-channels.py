#!/usr/bin/env python3
"""Bootstrap LazyRouter provider channels from local environment variables.

This script intentionally never prints API keys. It can be run on the host for
dry-run checks, or inside a container/root context when the SQLite file is owned
by the LazyRouter Docker container.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


CHANNEL_TYPE_OPENAI = 1
CHANNEL_TYPE_OPENROUTER = 20
CHANNEL_TYPE_DEEPSEEK = 43


PROVIDERS = [
    {
        "id": "openai",
        "name": "LazyRouter / OpenAI",
        "type": CHANNEL_TYPE_OPENAI,
        "key_env": ["OPENAI_API_KEY"],
        "base_url_env": ["OPENAI_BASE_URL"],
        "default_base_url": "https://api.openai.com",
        "models_env": "OPENAI_MODELS",
        "default_models": [
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-4.1-mini",
            "gpt-4.1",
            "o4-mini",
            "gpt-image-1",
            "dall-e-3",
            "text-embedding-3-small",
            "text-embedding-3-large",
        ],
        "test_model": "gpt-4o-mini",
        "priority": 50,
        "weight": 100,
    },
    {
        "id": "openrouter",
        "name": "LazyRouter / OpenRouter",
        "type": CHANNEL_TYPE_OPENROUTER,
        "key_env": ["OPENROUTER_API_KEY"],
        "base_url_env": ["OPENROUTER_BASE_URL"],
        "default_base_url": "https://openrouter.ai/api",
        "models_env": "OPENROUTER_MODELS",
        "default_models": [
            "openrouter/auto",
            "anthropic/claude-sonnet-4.5",
            "openai/gpt-5.1",
            "google/gemini-2.5-pro",
            "deepseek/deepseek-v3.2",
        ],
        "test_model": "openrouter/auto",
        "priority": 45,
        "weight": 100,
        "header_override": {
            "HTTP-Referer": "https://router.lazying.art",
            "X-OpenRouter-Title": "LazyRouter",
        },
    },
    {
        "id": "deepseek",
        "name": "LazyRouter / DeepSeek",
        "type": CHANNEL_TYPE_DEEPSEEK,
        "key_env": ["DEEPSEEK_API_KEY"],
        "base_url_env": ["DEEPSEEK_BASE_URL"],
        "default_base_url": "https://api.deepseek.com",
        "models_env": "DEEPSEEK_MODELS",
        "default_models": ["deepseek-chat", "deepseek-reasoner"],
        "test_model": "deepseek-chat",
        "priority": 55,
        "weight": 100,
    },
    {
        "id": "venice",
        "name": "LazyRouter / Venice",
        "type": CHANNEL_TYPE_OPENAI,
        "key_env": ["VENICE_API_KEY"],
        "base_url_env": ["VENICE_BASE_URL"],
        "default_base_url": "https://api.venice.ai/api",
        "models_env": "VENICE_MODELS",
        "default_models": [],
        "test_model": "",
        "priority": 40,
        "weight": 100,
        "models_required": True,
        "note": "Venice is configured as an OpenAI-compatible channel. Set VENICE_MODELS or run --fetch-models.",
    },
    {
        "id": "grsai",
        "name": "LazyRouter / GRSAI Compatible",
        "type": CHANNEL_TYPE_OPENAI,
        "key_env": ["GRSAI_API_KEY", "GRSAI"],
        "base_url_env": ["GRSAI_OPENAI_BASE_URL", "GRSAI_BASE_URL"],
        "default_base_url": "",
        "models_env": "GRSAI_MODELS",
        "default_models": [],
        "test_model": "",
        "priority": 35,
        "weight": 100,
        "base_url_required": True,
        "models_required": True,
        "note": (
            "GRSAI native Nano Banana image calls are not OpenAI-compatible. "
            "Only bootstrap this channel when a GRSAI-compatible OpenAI base URL and models are provided."
        ),
    },
]


DEFAULT_DB_CANDIDATES = [
    "/tmp/lazy-router-dev-data/lazyrouter.sqlite",
    "./data/lazyrouter.sqlite",
]


def parse_env_file(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        env[key] = value
    return env


def load_env(paths: list[str]) -> dict[str, str]:
    merged: dict[str, str] = {}
    for raw_path in paths:
        merged.update(parse_env_file(Path(raw_path).expanduser()))
    merged.update(os.environ)
    return merged


def first_env(env: dict[str, str], names: list[str]) -> tuple[str, str]:
    for name in names:
        value = env.get(name, "").strip()
        if value:
            return name, value
    return names[0], ""


def split_models(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.replace("\n", ",").split(",") if item.strip()]


def db_path_from_args(args: argparse.Namespace, env: dict[str, str]) -> str:
    if args.db:
        return args.db
    for name in ("LAZYROUTER_SQLITE_PATH", "LAZYINGROUTER_SQLITE_PATH", "SQLITE_PATH"):
        value = env.get(name, "").strip()
        if value:
            return value
    for candidate in DEFAULT_DB_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return DEFAULT_DB_CANDIDATES[0]


def fetch_models(provider: dict, key: str, base_url: str, limit: int) -> list[str]:
    endpoint = base_url.rstrip("/") + "/v1/models"
    headers = {
        "Authorization": "Bearer " + key,
        "User-Agent": "LazyRouter provider bootstrap",
    }
    headers.update(provider.get("header_override") or {})
    req = urllib.request.Request(endpoint, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"model fetch failed: {exc}") from exc
    data = payload.get("data")
    if not isinstance(data, list):
        return []
    models = []
    for item in data:
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            models.append(item["id"])
        elif isinstance(item, str):
            models.append(item)
    return models[:limit]


def resolved_provider(provider: dict, env: dict[str, str], fetch: bool, fetch_limit: int) -> dict:
    key_name, key = first_env(env, provider["key_env"])
    base_name, base_url = first_env(env, provider.get("base_url_env", []))
    if not base_url:
        base_url = provider.get("default_base_url", "")
    models = split_models(env.get(provider["models_env"])) or list(provider.get("default_models") or [])
    fetched = False
    fetch_error = ""
    if key and base_url and fetch and (not models or provider["id"] in {"venice", "grsai"}):
        try:
            fetched_models = fetch_models(provider, key, base_url, fetch_limit)
            if fetched_models:
                models = fetched_models
                fetched = True
        except RuntimeError as exc:
            fetch_error = str(exc)
    skip_reason = ""
    if not key:
        skip_reason = "missing " + " or ".join(provider["key_env"])
    elif provider.get("base_url_required") and not base_url:
        skip_reason = "missing " + " or ".join(provider.get("base_url_env", []))
    elif provider.get("models_required") and not models:
        skip_reason = f"missing {provider['models_env']} or successful --fetch-models result"
    return {
        **provider,
        "key_name": key_name,
        "key": key,
        "base_name": base_name,
        "base_url": base_url,
        "models": models,
        "models_fetched": fetched,
        "fetch_error": fetch_error,
        "skip_reason": skip_reason,
    }


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def quote_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def upsert_channel(conn: sqlite3.Connection, provider: dict, group: str) -> tuple[int, str]:
    columns = table_columns(conn, "channels")
    now = int(time.time())
    channel_info = {
        "is_multi_key": False,
        "multi_key_size": 0,
        "multi_key_status_list": None,
        "multi_key_polling_index": 0,
        "multi_key_mode": "",
    }
    models = provider["models"]
    test_model = provider.get("test_model") or (models[0] if models else "")
    values = {
        "type": provider["type"],
        "key": provider["key"],
        "test_model": test_model,
        "status": 1,
        "name": provider["name"],
        "weight": provider.get("weight", 100),
        "created_time": now,
        "base_url": provider["base_url"].rstrip("/"),
        "models": ",".join(models),
        "group": group,
        "model_mapping": "{}",
        "status_code_mapping": "{}",
        "priority": provider.get("priority", 0),
        "auto_ban": 1,
        "tag": "lazyrouter-provider",
        "setting": "{}",
        "param_override": "{}",
        "header_override": json.dumps(provider.get("header_override") or {}, separators=(",", ":")),
        "remark": f"Managed by scripts/bootstrap-provider-channels.py ({provider['id']}).",
        "channel_info": json.dumps(channel_info, separators=(",", ":")),
        "settings": "{}",
    }
    values = {key: value for key, value in values.items() if key in columns}
    existing = conn.execute("SELECT id FROM channels WHERE name = ?", (provider["name"],)).fetchone()
    if existing:
        channel_id = int(existing[0])
        update_values = {key: value for key, value in values.items() if key != "created_time"}
        assignments = ", ".join(f"{quote_identifier(key)} = ?" for key in update_values)
        conn.execute(
            f"UPDATE channels SET {assignments} WHERE id = ?",
            [*update_values.values(), channel_id],
        )
        action = "updated"
    else:
        col_sql = ", ".join(quote_identifier(key) for key in values)
        placeholders = ", ".join("?" for _ in values)
        cursor = conn.execute(
            f"INSERT INTO channels ({col_sql}) VALUES ({placeholders})",
            list(values.values()),
        )
        channel_id = int(cursor.lastrowid)
        action = "inserted"
    conn.execute("DELETE FROM abilities WHERE channel_id = ?", (channel_id,))
    for model_name in models:
        conn.execute(
            'INSERT INTO abilities ("group", "model", "channel_id", "enabled", "priority", "weight", "tag") '
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                group,
                model_name,
                channel_id,
                1,
                provider.get("priority", 0),
                provider.get("weight", 100),
                "lazyrouter-provider",
            ),
        )
    return channel_id, action


def enable_root_unpriced_models(conn: sqlite3.Connection) -> int:
    columns = table_columns(conn, "users")
    if "setting" not in columns or "role" not in columns:
        return 0
    rows = conn.execute("SELECT id, setting FROM users WHERE role >= 100").fetchall()
    changed = 0
    for user_id, raw_setting in rows:
        try:
            setting = json.loads(raw_setting or "{}")
            if not isinstance(setting, dict):
                setting = {}
        except json.JSONDecodeError:
            setting = {}
        if setting.get("accept_unset_model_ratio_model") is True:
            continue
        setting["accept_unset_model_ratio_model"] = True
        conn.execute("UPDATE users SET setting = ? WHERE id = ?", (json.dumps(setting, separators=(",", ":")), user_id))
        changed += 1
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap LazyRouter provider channels from environment variables.")
    parser.add_argument("--apply", action="store_true", help="Write channels to SQLite. Default is dry-run.")
    parser.add_argument("--db", help="Path to lazyrouter.sqlite. Defaults to SQLITE_PATH or local Docker dev path.")
    parser.add_argument("--env-file", action="append", default=[], help="Additional dotenv file to load.")
    parser.add_argument("--provider", action="append", help="Provider id to include. Can be repeated.")
    parser.add_argument(
        "--group",
        default=os.environ.get("LAZYROUTER_GROUP") or os.environ.get("LAZYINGROUTER_GROUP", "default"),
        help="LazyRouter group to attach abilities to. Legacy LAZYINGROUTER_GROUP is accepted as a fallback.",
    )
    parser.add_argument("--fetch-models", action="store_true", help="Fetch /v1/models from providers that have keys.")
    parser.add_argument("--fetch-limit", type=int, default=80, help="Maximum fetched models per provider.")
    parser.add_argument(
        "--allow-root-unpriced-models",
        action="store_true",
        help="Local/dev convenience: let root/admin users call models before production pricing is configured.",
    )
    args = parser.parse_args()

    default_env_files = [
        ".env",
        ".env.local",
        ".env.lazyrouter",
        ".env.lazyrouter.local",
        ".env.lazyingrouter",
        ".env.lazyingrouter.local",
    ]
    env = load_env([*default_env_files, *args.env_file])
    selected = set(args.provider or [])
    db_path = db_path_from_args(args, env)

    providers = [p for p in PROVIDERS if not selected or p["id"] in selected]
    if selected:
        unknown = sorted(selected.difference({p["id"] for p in PROVIDERS}))
        if unknown:
            print("Unknown provider(s): " + ", ".join(unknown), file=sys.stderr)
            return 2

    resolved = [resolved_provider(p, env, args.fetch_models, args.fetch_limit) for p in providers]
    ready = [p for p in resolved if not p["skip_reason"]]

    print(f"LazyRouter provider bootstrap ({'apply' if args.apply else 'dry-run'})")
    print(f"db={db_path}")
    print(f"group={args.group}")
    for provider in resolved:
        status = "ready" if not provider["skip_reason"] else "skipped"
        models_note = f"{len(provider['models'])} model(s)"
        if provider["models_fetched"]:
            models_note += ", fetched"
        line = (
            f"- {provider['id']}: {status}; key={'set' if provider['key'] else 'missing'}"
            f"; base={provider['base_url'] or 'missing'}; {models_note}"
        )
        if provider["skip_reason"]:
            line += f"; reason={provider['skip_reason']}"
        if provider["fetch_error"]:
            line += f"; fetch={provider['fetch_error']}"
        print(line)
        if provider.get("note"):
            print(f"  note: {provider['note']}")

    if not args.apply:
        if args.allow_root_unpriced_models:
            print("Would enable accept_unset_model_ratio_model for root/admin users.")
        print("No database changes made. Re-run with --apply to upsert ready providers.")
        return 0

    if not ready and not args.allow_root_unpriced_models:
        print("No ready providers to apply.")
        return 0
    if not Path(db_path).exists():
        print(f"SQLite database not found: {db_path}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(db_path)
    try:
        with conn:
            for provider in ready:
                channel_id, action = upsert_channel(conn, provider, args.group)
                print(f"{action}: {provider['id']} channel_id={channel_id} models={len(provider['models'])}")
            if args.allow_root_unpriced_models:
                changed = enable_root_unpriced_models(conn)
                print(f"root/admin unpriced-model access updated for {changed} user(s)")
    finally:
        conn.close()
    print("Done. Restart LazyRouter so the running process reloads channel cache.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
