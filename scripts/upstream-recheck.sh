#!/usr/bin/env bash
# Re-fetch the pinned upstream and check it is still what the ledger describes.
#
# The distillation's ATTRIBUTION files say a recheck must fetch upstream rather
# than re-read our own notes. This is that fetch, made repeatable: it pulls the
# four files at the recorded SHA and compares their hashes to the ones the ledger
# was written against.
#
# A mismatch does not mean upstream changed - the SHA pins content, so a mismatch
# means the fetch is wrong or the ledger's hashes were mistyped. Upstream *moving*
# shows up differently: resolve the marketplace pin and find a different SHA, then
# run this with that SHA to see which files actually differ.
#
#     scripts/upstream-recheck.sh [sha]
set -u
SHA="${1:-885e2ca4d842d139e9aef4e48d366c63cb1b8013}"
BASE="https://raw.githubusercontent.com/mattpocock/skills/$SHA"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
unreachable=0

# path                                   sha256(first 16)   bytes
read -r -d '' EXPECTED <<'ROWS' || true
skills/engineering/diagnosing-bugs/SKILL.md 77f3cf31bc99b2f4 8529
skills/engineering/tdd/SKILL.md             cb01f66bebfaa25f 3549
skills/engineering/tdd/tests.md             859f9e592c188fda 2214
skills/engineering/tdd/mocking.md           3ceb807fdf4a47d6 1481
ROWS

fail=0
printf 'pin %s\n' "$SHA"
while read -r path want_hash want_bytes; do
  [ -n "$path" ] || continue
  out="$tmp/$(printf '%s' "$path" | tr '/' '_')"
  code=$(curl -sS -w '%{http_code}' -o "$out" "$BASE/$path")
  if [ "$code" != "200" ]; then
    printf '  %-44s UNREACHABLE (HTTP %s)\n' "$path" "$code"
    unreachable=1; continue
  fi
  got_hash=$(shasum -a 256 "$out" | cut -c1-16)
  got_bytes=$(wc -c < "$out" | tr -d ' ')
  if [ "$got_hash" = "$want_hash" ] && [ "$got_bytes" = "$want_bytes" ]; then
    printf '  %-44s matches the ledger\n' "$path"
  else
    printf '  %-44s DIFFERS  hash %s (ledger %s)  bytes %s (ledger %s)\n' \
      "$path" "$got_hash" "$want_hash" "$got_bytes" "$want_bytes"; fail=1
  fi
done <<< "$EXPECTED"

echo
if [ "$unreachable" -ne 0 ]; then
  echo "could not fetch every file - that is not the same as a change."
  echo "A SHA that does not exist and a network failure both land here;"
  echo "check the ref resolves before concluding anything."
  exit 1
fi
if [ "$fail" -eq 0 ]; then
  echo "the ledger in docs/research/upstream-distillation-ledger.md describes these bytes"
else
  echo "at least one file is not what the ledger was written against - read before trusting it"
fi
exit "$fail"
