#!/bin/sh
# Stands in for a CLI that cannot start — missing credentials, wrong version.
exec /usr/bin/env python3 "$(dirname "$0")/stub_agent.py" --stub-exit 1
