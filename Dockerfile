# Local packaging only: the vault stays markdown on the host, mounted at
# /vault, and Obsidian keeps working on the same files while this runs.

# The agent CLI ships as a single self-contained binary, fetched from
# Anthropic's release channel and checked against the manifest's SHA-256 —
# pinned, not "latest", so an image build is reproducible and the flags the
# server passes stay the ones that were verified. Nothing here is installed
# with npm or pip: server/ is stdlib-only and stays that way.
FROM python:3.12-slim-bookworm AS agent
ARG CLAUDE_VERSION=2.1.251
ARG TARGETARCH=amd64
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*
RUN set -eu; \
    case "$TARGETARCH" in \
      amd64) platform=linux-x64 ;; \
      arm64) platform=linux-arm64 ;; \
      *) echo "unsupported architecture: $TARGETARCH" >&2; exit 1 ;; \
    esac; \
    base=https://downloads.claude.ai/claude-code-releases/$CLAUDE_VERSION; \
    curl -fsSL "$base/manifest.json" -o /tmp/manifest.json; \
    checksum=$(python3 -c "import json;print(json.load(open('/tmp/manifest.json'))['platforms']['$platform']['checksum'])"); \
    curl -fsSL "$base/$platform/claude" -o /usr/local/bin/claude; \
    echo "$checksum  /usr/local/bin/claude" | sha256sum -c -; \
    chmod 0755 /usr/local/bin/claude

FROM python:3.12-slim-bookworm

# Ghostscript and poppler back the PDF render endpoint; everything else is
# Python stdlib — no pip installs at all.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ghostscript poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY --from=agent /usr/local/bin/claude /usr/local/bin/claude
COPY server/ /app/server
# The interview workflow the agent is told to read lives in the skill, so the
# skill has to exist in the image. It is read-only here, like the rest of /app.
COPY .agents/skills /app/.agents/skills
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh

# The agent's config and its own session storage live on a named volume, so
# `--resume` still works after the container is replaced. Created with /tmp's
# permissions because compose seeds the volume from this directory and the
# container runs as whatever UID matches the host's vault.
RUN mkdir -p /agent-home && chmod 1777 /agent-home

# Inside the container the server must bind its own interface to be reachable
# through the published port; compose publishes on the host's loopback only.
ENV CAREER_EVIDENCE_VAULT=/vault \
    CAREER_EVIDENCE_BIND=0.0.0.0 \
    HOME=/agent-home \
    CLAUDE_CONFIG_DIR=/agent-home/.claude

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/api/schema', timeout=2)"

ENTRYPOINT ["/usr/local/bin/entrypoint.sh", "python3", "/app/server/serve.py", "--no-browser"]
