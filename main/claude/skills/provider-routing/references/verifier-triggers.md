# Independent-verifier triggers

Dispatch at most one outcome `verifier` per top-level task, only when at least one holds:

- Failure could affect a security/trust boundary, money, destructive data, migrations, concurrency, public APIs, or cross-repo compatibility.
- Judgment-heavy integration cannot be proven mechanically.
- Acceptance depends on adversarial state or boundary behavior.
- Evidence conflicts, or reproduction fails.
- The user requests it.

Do not dispatch for docs-only changes, trivial config, decisive mechanical checks, low-risk direct work, or duplicate review of an already-verified surface.

## Which provider verifies

Route the outcome `verifier` to the provider that did not produce the claim: Claude-produced work verifies on the Codex `verifier` (`sandbox_mode = "read-only"`, resolver-supplied model and effort), Codex-produced work verifies on the Claude `verifier`. A verifier drawn from the producer's own model family inherits its blind spots, so the independence is the point of the role, not a preference between the two sides.

This is not a ranking, and it does not need one: CP-first still governs which provider *produces*, and neither verifier cell is near the sample floor. The local samples as of 2026-08-06 both point the same way without settling anything — Codex Sol/high n=7, accepted 7/7, 29s median; Claude Opus/high n=2, the single record carrying cost telemetry at $5.93 and 462s. Read that as a reason to sample Codex first, not as a verdict.

When the independent side is unavailable, refuses, or its short usage window is near its limit, verify on the producing provider and name that in the verdict. A same-provider verdict is weaker evidence and never satisfies a security trigger on its own.

Place the verifier at the smallest coherent integration boundary where the complete acceptance claim can be independently refuted. Focused tests, builds, and static checks remain intermediate evidence during iteration. Verify earlier for security, cross-language or FFI, serialization or pre-aggregation, irreversible-operation, and integration-blocking boundaries; this changes timing, not the one-verifier limit.
