#!/usr/bin/env python3
"""PreToolUse[Agent] gate: leaf agents cannot dispatch another agent.

Claude Code 2.1.220 PreToolUse payloads carry the caller's frontmatter name in
`agent_type`; main-session calls omit the field. For the Agent tool, any
non-empty caller identity therefore means a leaf is trying to orchestrate.

Exit 0 allows; exit 2 blocks and returns stderr to the model. Unparseable input
stays fail-open because the hook cannot establish that it is an Agent call.
Once an Agent call carries a caller identity, the boundary fails closed.

Why this gate cannot attest to its own health. `verifier-quota` counts payloads
that arrived without its carrier, because every healthy payload should have one
and a run of misses means the field is gone. The inverse holds here: the field
is *absent* on every healthy dispatch and present only when a leaf misbehaves,
which should never happen. So an absent carrier is indistinguishable from a
correct main-session call, no count separates the two, and a gate that has
never fired looks identical to a gate that can no longer fire.

That leaves the runtime version as the only observable that moves. The field is
undocumented payload shape, so a runtime that changes it breaks this boundary
silently — the same field name went empty on SubagentStop payloads between
2.1.220 and 2.1.238 without any release note. `CARRIER_VALIDATED_ON` records the
newest runtime on which a leaf's Agent call was *observed* to carry
`agent_type`; weekly-integrity compares it against the live runtime and asks for
re-validation when the runtime has moved past it. Re-validation is not
automatable from here: it takes one real dispatch whose leaf attempts a nested
one, and only that can distinguish a well-behaved fleet from a dead gate.
"""
from __future__ import annotations

import json
import sys

# Newest Claude Code on which a leaf's Agent call was observed to carry
# `agent_type`. Advance it only after re-observing that, never to silence the
# weekly finding: the whole value of the pin is that it stops being true.
#
# 2.1.241 (2026-08-24): a `general-purpose` leaf was briefed to attempt one
# Agent dispatch. The gate refused it and the denial log recorded
# `caller=general-purpose` - the field is still populated, and the boundary
# still closes. That row is also the first time this gate has fired outside a
# test, so before it the log could not have distinguished a live gate from a
# dead one either.
CARRIER_VALIDATED_ON = (2, 1, 241)

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
