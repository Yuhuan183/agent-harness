#!/usr/bin/env bash
# Which command *forms* can the permission matcher be made to allow at all?
# Verdict off the filesystem, like its two siblings here.
#
# Measured 2026-08-17, after `Bash(sh:*)` landed and `e1` still could not run its
# launcher. The matcher keys on the leading token, and that has consequences a
# grant string does not advertise:
#
#     sh x.sh                  allowed by Bash(sh:*)
#     FOO=1 sh x.sh            denied - the env assignment is the leading token
#     sh -c 'FOO=1 sh x.sh'    allowed - leading token is sh again
#     ./x.sh                   allowed only by a per-script Bash(./x.sh:*)
#
# So a fixture whose README documents `FOO=1 ./x.sh` hands the session two
# commands it cannot run, which is what made `e1` unpassable twice over.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work=$(mktemp -d /tmp/form-probe-XXXXXX); out=$(mktemp -d /tmp/form-out-XXXXXX)
printf '#!/usr/bin/env sh\ntouch "mark-$1"\n' > "$work/x.sh"; chmod +x "$work/x.sh"

read -r -d '' prompt <<EOF || true
Run each command exactly as written, in order. Do not rewrite or substitute. If
one is blocked, say so and continue.

1. sh x.sh A
2. FOO=1 sh x.sh B
3. sh -c 'FOO=1 sh x.sh C'
4. ./x.sh D

Then list which ran and which were blocked.
EOF

(cd "$work" && env -u ANTHROPIC_BASE_URL -u ANTHROPIC_MODEL -u ANTHROPIC_CUSTOM_HEADERS \
  REPLAY_WORKDIR="$work" PATH="$HERE/sandbox:$PATH" \
  claude --print "$prompt" --output-format text --permission-mode acceptEdits \
  --allowedTools "Bash(python3:*)" "Bash(sh:*)" "Bash(./x.sh:*)" \
  --strict-mcp-config > "$out/reply.txt" 2>&1)

for m in A B C D; do
  printf '  form %s: %s\n' "$m" "$([ -f "$work/mark-$m" ] && echo RAN || echo blocked)"
done
rm -rf "$work" "$out"
