# Independent-verifier triggers

Dispatch exactly one `verifier` only when at least one holds:

- Failure could affect a security/trust boundary, money, destructive data, migrations, concurrency, public APIs, or cross-repo compatibility.
- Judgment-heavy integration cannot be proven mechanically.
- Acceptance depends on adversarial state or boundary behavior.
- Evidence conflicts, or reproduction fails.
- The user requests it.

Do not dispatch for docs-only changes, trivial config, decisive mechanical checks, low-risk direct work, or duplicate review of an already-verified surface.

Place the verifier at the smallest coherent integration boundary where the complete acceptance claim can be independently refuted. Focused tests, builds, and static checks remain intermediate evidence during iteration. Verify earlier for security, cross-language or FFI, serialization or pre-aggregation, irreversible-operation, and integration-blocking boundaries; this changes timing, not the one-verifier limit.
