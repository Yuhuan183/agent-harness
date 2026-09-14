# Independent-verifier triggers

Dispatch at most one outcome `verifier` per top-level task, only when at least one holds:

- Failure could affect a security/trust boundary, money, destructive data, migrations, concurrency, public APIs, or cross-repo compatibility.
- Judgment-heavy integration cannot be proven mechanically.
- Acceptance depends on adversarial state or boundary behavior.
- Evidence conflicts, or reproduction fails.
- The user requests it.

Do not dispatch for docs-only changes, trivial config, decisive mechanical checks, low-risk direct work, or duplicate review of an already-verified surface.

## Which provider verifies

Independence is the point of the role, so a `verifier` never grades the context that produced the claim: it starts from the claim and the diff in a fresh context, with no memory of the reasoning that reached them.

That independence was bought with a second provider until 2026-09-14 — Claude-produced work verified on the Codex `verifier` and the reverse — on the argument that a verifier from the producer's own model family inherits its blind spots. The bundle is gone and the argument is not, so what remains is the weaker guarantee, stated plainly rather than implied: a fresh context on the same model removes the producer's working state, not its family's blind spots. Treat a same-family verdict as evidence that the claim survives re-derivation, which is less than it used to mean.

When the independent side is unavailable, refuses, or its short usage window is near its limit, verify on the producing provider and name that in the verdict. A same-provider verdict is weaker evidence and never satisfies a security trigger on its own.

Place the verifier at the smallest coherent integration boundary where the complete acceptance claim can be independently refuted. Focused tests, builds, and static checks remain intermediate evidence during iteration. Verify earlier for security, cross-language or FFI, serialization or pre-aggregation, irreversible-operation, and integration-blocking boundaries; this changes timing, not the one-verifier limit.
