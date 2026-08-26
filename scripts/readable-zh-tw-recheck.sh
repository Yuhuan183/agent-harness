#!/usr/bin/env bash
# Re-fetch readable-zh-tw's upstream and check it is still what the研究 doc describes.
#
# Same contract as scripts/upstream-recheck.sh, different upstream: that one
# covers the Matt Pocock engineering skills, this one covers speak-human-tw,
# which `readable-zh-tw` is derived from. Two near-identical scripts is the
# concrete argument for a parameterised one; it is recorded in the research doc
# rather than acted on, because two is not yet a pattern.
#
# A mismatch does not mean upstream changed - the SHA pins content, so a mismatch
# means the fetch is wrong or the hashes were mistyped. Upstream *moving* shows up
# differently: resolve the tag or branch, find a different SHA, then run this with
# that SHA to see which files actually differ.
#
#     scripts/readable-zh-tw-recheck.sh [sha]
#
# The default is the pin ATTRIBUTION.md records. It has moved twice since the
# distillation - 2c27cca (master on 2026-07-18, not the v1.4.0 tag the original
# commit message named) -> 8f1cdb5 -> aa37c20b - while the expected hashes below
# never moved with it, because every advance was star-history churn outside these
# six files. That is also how the default drifts unnoticed: it sat at 8f1cdb5 for
# two days after ATTRIBUTION advanced, so the script and the file it answers to
# described different commits (found and fixed 2026-08-26; the test that now
# holds the three sites together is named in the research doc).
# To see what has landed since, resolve master and pass that:
#
#     scripts/readable-zh-tw-recheck.sh "$(curl -sS \
#       https://api.github.com/repos/Raymondhou0917/speak-human-tw/commits/master \
#       | sed -n 's/.*"sha": "\([0-9a-f]\{40\}\)".*/\1/p' | head -1)"
set -u
SHA="${1:-aa37c20be932c56079ea73e8e7421770057b0835}"
BASE="https://raw.githubusercontent.com/Raymondhou0917/speak-human-tw/$SHA"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
unreachable=0

# Only the files this repo actually derives from. `scenes.md` is listed because
# our 判情境 table came from it; `examples.md` is not, because those examples were
# rewritten rather than adapted and nothing here tracks them.
#
# path                              sha256(first 16)   bytes  (at the pin)
read -r -d '' EXPECTED <<'ROWS' || true
SKILL.md                            83659ca11673d3e4 20872
references/patterns.md              61a56a00b3442ced 28393
references/humanize.md              0c782b76ac05540b 6738
references/protected-list.md        59d981e3425bdef5 3958
references/taiwan-localization.md   881f1606fcc49fad 5408
references/scenes.md                23b2d6e2d4c05804 4691
ROWS

fail=0
printf 'pin %s\n' "$SHA"
while read -r path want_hash want_bytes; do
  [ -n "$path" ] || continue
  out="$tmp/$(printf '%s' "$path" | tr '/' '_')"
  code=$(curl -sS -w '%{http_code}' -o "$out" "$BASE/$path")
  if [ "$code" != "200" ]; then
    printf '  %-36s UNREACHABLE (HTTP %s)\n' "$path" "$code"
    unreachable=1; continue
  fi
  got_hash=$(shasum -a 256 "$out" | cut -c1-16)
  got_bytes=$(wc -c < "$out" | tr -d ' ')
  if [ "$got_hash" = "$want_hash" ] && [ "$got_bytes" = "$want_bytes" ]; then
    printf '  %-36s matches the pin\n' "$path"
  else
    printf '  %-36s DIFFERS  hash %s (pinned %s)  bytes %s (pinned %s)\n' \
      "$path" "$got_hash" "$want_hash" "$got_bytes" "$want_bytes"; fail=1
  fi
done <<< "$EXPECTED"

echo
if [ "$unreachable" -ne 0 ]; then
  echo "could not fetch every file - that is not the same as a change;"
  echo "a SHA that does not exist and a network failure both land here."
  echo "Check the ref resolves before concluding anything."
  exit 1
fi
if [ "$fail" -eq 0 ]; then
  echo "docs/research/readable-zh-tw-upstream.md describes these bytes"
else
  echo "at least one file is not what the research doc was written against - read before trusting it"
fi
exit "$fail"
