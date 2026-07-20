# Briefs and Stops

Use only after delegation passes the dispatch brake.

## Worker brief

```markdown
## Outcome
## In scope / out of scope / excluded adjacent capabilities
## Minimum sources
## May write / must not write / secondary writes
## Local checks and output
## Time, retry, scope, and failure stops
## Return when assumptions fail
```

Do not ask an agent to rediscover settled conclusions. For independent verification, provide artifacts and acceptance criteria without the implementer's preferred conclusion.

## Ownership

For each workstream, list required reads, allowed writes, forbidden writes, secondary writes, and integration owner. Shared schemas, registries, indexes, generated output, config, and lockfiles need one owner or pre-fan-out convergence.

## Stop guide

| Signal | Response |
|---|---|
| Same-cause failure | Change brief, boundary, primitive, or gate |
| Ownership or approved boundary crossed | Stop and return control to main |
| Conclusions conflict | Recheck primary evidence in main |
| Integration backlog grows | Stop fan-out and synthesize |
| Agent starts global/live checks | Preserve work and centralize the gate |
| Retry/rate-limit cascade | Reduce concurrency or batch size |

Known one-file fix stays direct. Independent read-only sources may fan out. Shared registries converge before builders start.
