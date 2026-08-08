#!/usr/bin/env python3
"""PreToolUse[Agent] gate: leaf agents cannot dispatch another agent.

Claude Code 2.1.220 PreToolUse payloads carry the caller's frontmatter name in
`agent_type`; main-session calls omit the field. For the Agent tool, any
non-empty caller identity therefore means a leaf is trying to orchestrate.

Exit 0 allows; exit 2 blocks and returns stderr to the model. Unparseable input
stays fail-open because the hook cannot establish that it is an Agent call.
Once an Agent call carries a caller identity, the boundary fails closed.
"""
from __future__ import annotations

import json
import sys

try:  # Observability must never be able to break the boundary it observes.
    import denial_log
except Exception:  # noqa: BLE001
    denial_log = None


def deny(caller: object, payload: object = None) -> int:
    sys.stderr.write(
        f"[leaf-redispatch] blocked: leaf agent {caller!r} cannot dispatch "
        "another agent. Return the proposed dispatch to the main session; "
        "only the main task may orchestrate.\n"
    )
    if denial_log is not None:
        denial_log.record("leaf-redispatch", "leaf-tried-to-dispatch", payload,
                          caller=str(caller))
    return 2


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        return 0
    if not isinstance(payload, dict) or payload.get("tool_name") != "Agent":
        return 0
    caller = payload.get("agent_type")
    return deny(caller, payload) if caller else 0


if __name__ == "__main__":
    raise SystemExit(main())
