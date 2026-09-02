# Local packaging only: the vault stays markdown on the host, mounted at
# /vault, and Obsidian keeps working on the same files while this runs.
FROM python:3.12-slim-bookworm

# Ghostscript and poppler back the PDF render endpoint; everything else is
# Python stdlib — no pip installs at all.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ghostscript poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY server/ /app/server

# Inside the container the server must bind its own interface to be reachable
# through the published port; compose publishes on the host's loopback only.
ENV CAREER_EVIDENCE_VAULT=/vault \
    CAREER_EVIDENCE_BIND=0.0.0.0

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/api/schema', timeout=2)"

ENTRYPOINT ["python3", "/app/server/serve.py", "--no-browser"]
