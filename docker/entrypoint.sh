#!/bin/sh
# Seed the agent's config directory from the host's, once, then start the
# dashboard. Only the credential is copied: the rest of ~/.claude is the
# user's own history, projects and settings, and the container has no business
# with any of it.
set -e

AGENT_CONFIG="${CLAUDE_CONFIG_DIR:-/agent-home/.claude}"
HOST_CONFIG=/host-claude

mkdir -p "$AGENT_CONFIG"

if [ -r "$HOST_CONFIG/.credentials.json" ] && [ ! -f "$AGENT_CONFIG/.credentials.json" ]; then
    cp "$HOST_CONFIG/.credentials.json" "$AGENT_CONFIG/.credentials.json"
    chmod 600 "$AGENT_CONFIG/.credentials.json"
    echo "Seeded the agent's credentials from $HOST_CONFIG (copied once; the"
    echo "named volume keeps them across restarts)."
elif [ ! -f "$AGENT_CONFIG/.credentials.json" ]; then
    echo "No agent credentials found. The dashboard runs, but the AI Interview"
    echo "will report that the agent cannot start. See docs/setup.md — either"
    echo "mount your host credentials or run 'claude setup-token' in here."
fi

exec "$@"
