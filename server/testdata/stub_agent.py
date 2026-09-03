#!/usr/bin/env python3
"""A fake `claude` CLI: just enough stream-json to test the relay.

The suite must never spawn the real binary — it costs money and its output is
nondeterministic. This stands in for it: read one JSON line per user turn from
stdin, answer with two assistant events and a result event, repeat until stdin
closes. Point `CAREER_EVIDENCE_AGENT_BIN` at it.

`--stub-exit <code>` makes it die immediately instead, which is how the
unauthenticated-CLI error path is tested.
"""

from __future__ import annotations

import json
import sys


def emit(event: dict) -> None:
    sys.stdout.write(json.dumps(event) + "\n")
    sys.stdout.flush()


def main() -> int:
    argv = sys.argv[1:]
    if "--stub-exit" in argv:
        code = int(argv[argv.index("--stub-exit") + 1])
        sys.stderr.write("stub agent: refusing to start\n")
        return code

    session_id = argv[argv.index("--session-id") + 1] if "--session-id" in argv else "stub"
    turn = 0
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            text = json.loads(line)["message"]["content"][0]["text"]
        except (ValueError, KeyError, IndexError, TypeError):
            text = line
        turn += 1
        for part in (f"You said: {text}", f"(stub turn {turn})"):
            emit({"type": "assistant", "session_id": session_id,
                  "message": {"role": "assistant",
                              "content": [{"type": "text", "text": part}]}})
        emit({"type": "result", "subtype": "success", "session_id": session_id,
              "is_error": False, "result": f"(stub turn {turn})"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
