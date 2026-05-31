#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SESSION="${LAZYINGROUTER_TMUX_SESSION:-lazyingrouter}"
PORT="${PORT:-3218}"
COMPOSE_FILE="${LAZYINGROUTER_COMPOSE_FILE:-docker-compose.lazyingrouter.yml}"
HEALTH_URL="http://127.0.0.1:${PORT}/api/status"
APP_URL="http://127.0.0.1:${PORT}/"

usage() {
  cat <<USAGE
Usage: $0 [--session NAME] [--port PORT] [--restart]

Starts or reuses LazyingRouter in a tmux session using tmux send-keys.

Environment:
  LAZYINGROUTER_TMUX_SESSION  tmux session name, default: lazyingrouter
  PORT                         host port, default: 3218
  LAZYINGROUTER_COMPOSE_FILE   compose file, default: docker-compose.lazyingrouter.yml

Examples:
  $0
  $0 --port 3219
  $0 --session lazyingrouter --restart
USAGE
}

RESTART=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --session)
      SESSION="${2:?missing session name}"
      shift 2
      ;;
    --port)
      PORT="${2:?missing port}"
      HEALTH_URL="http://127.0.0.1:${PORT}/api/status"
      APP_URL="http://127.0.0.1:${PORT}/"
      shift 2
      ;;
    --restart)
      RESTART=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

need_cmd tmux
need_cmd curl
need_cmd docker

if [[ ! -f "${REPO_ROOT}/${COMPOSE_FILE}" ]]; then
  echo "Compose file not found: ${REPO_ROOT}/${COMPOSE_FILE}" >&2
  exit 1
fi

if [[ "${RESTART}" == "1" ]] && tmux has-session -t "${SESSION}" 2>/dev/null; then
  tmux kill-session -t "${SESSION}"
fi

if ! tmux has-session -t "${SESSION}" 2>/dev/null; then
  tmux new-session -d -s "${SESSION}" -c "${REPO_ROOT}"
  tmux send-keys -t "${SESSION}" "cd '${REPO_ROOT}'" C-m
  tmux send-keys -t "${SESSION}" "export PORT='${PORT}'" C-m
  tmux send-keys -t "${SESSION}" "echo 'LazyingRouter tmux session: ${SESSION}'" C-m
  tmux send-keys -t "${SESSION}" "echo 'URL: ${APP_URL}'" C-m
  tmux send-keys -t "${SESSION}" "echo 'Health: ${HEALTH_URL}'" C-m
  tmux send-keys -t "${SESSION}" "if curl -fsS '${HEALTH_URL}' >/dev/null 2>&1; then echo 'LazyingRouter is already healthy; following container logs.'; docker logs -f --tail=120 lazying-router-dev 2>/dev/null || docker logs -f --tail=120 lazying-router 2>/dev/null || exec bash; else echo 'Starting LazyingRouter with docker compose...'; docker compose -f '${COMPOSE_FILE}' up --build; fi" C-m
fi

if curl -fsS "${HEALTH_URL}" >/dev/null 2>&1; then
  echo "LazyingRouter is available: ${APP_URL}"
else
  echo "LazyingRouter is starting: ${APP_URL}"
  echo "Health check pending: ${HEALTH_URL}"
fi

echo "tmux session: ${SESSION}"
echo "attach: tmux attach -t ${SESSION}"
