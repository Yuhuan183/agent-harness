---
name: headroom-protocol
description: Manually compress an unusually large read-only blob when Headroom MCP tools exist and proxy routing is absent. Not for ordinary CLI work, small blobs, editable content, or exact error diagnosis.
---

# Headroom Protocol

Use this only as a manual compression path outside transparent proxy routing.

1. Confirm `headroom_compress` exists and proxy routing is absent. Check `http://127.0.0.1:8787/livez` only when routing is uncertain.
2. Compress disposable read-only analysis input, typically over 200 lines or several KB.
3. Keep the hash; use `headroom_retrieve` when exact text is later needed.
4. Reopen the exact source before editing, quoting, or byte comparison.
5. If compression was material, call `headroom_stats` and report actual savings.

Do not compress the only editable copy, exact code/errors, small outputs, or content already covered by proxy routing. This protocol changes neither routing, authentication, nor model selection.
