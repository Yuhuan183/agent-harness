#!/bin/bash
input=$(cat)

# Parse the complete payload with one jq process. Unit separator preserves empty fields.
PARSED=$(printf '%s' "$input" | jq -jr '
  [
    (.model.display_name // "Claude"),
    (.workspace.current_dir // ""),
    (.cost.total_cost_usd // 0),
    ((.context_window.used_percentage // 0) | floor),
    (.context_window.context_window_size // ""),
    (.cost.total_duration_ms // 0),
    (.cost.total_lines_added // ""),
    (.cost.total_lines_removed // ""),
    (.vim.mode // ""),
    (.agent.name // ""),
    (.version // ""),
    (.rate_limits.five_hour.used_percentage // ""),
    (.rate_limits.seven_day.used_percentage // ""),
    (.rate_limits.five_hour.resets_at // ""),
    (.rate_limits.seven_day.resets_at // ""),
    (.context_window.total_input_tokens // ""),
    (.context_window.total_output_tokens // ""),
    (.cost.total_api_duration_ms // 0),
    (.context_window.current_usage.cache_read_input_tokens // ""),
    (.context_window.current_usage.cache_creation_input_tokens // ""),
    (.context_window.current_usage.input_tokens // "")
  ] | map(tostring) | join("\u001f")
') || exit 0
IFS=$'\x1f' read -r MODEL DIR COST PCT CTX_SIZE DURATION_MS LINES_ADD LINES_DEL \
  VIM_MODE AGENT VERSION RATE_5H RATE_7D RESET_5H RESET_7D TOTAL_IN_TOKENS \
  TOTAL_OUT_TOKENS API_DURATION_MS CACHE_READ CACHE_CREATE CUR_INPUT <<< "$PARSED"
DIR=${DIR:-$PWD}

# Colors
RESET='\033[0m'; BOLD='\033[1m'; DIM='\033[2m'
CYAN='\033[36m'; GREEN='\033[32m'; YELLOW='\033[33m'
RED='\033[31m'; MAGENTA='\033[35m'; BLUE='\033[34m'; WHITE='\033[37m'
SEP="${DIM} | ${RESET}"

color_pct() {
  local val=$1
  if [ "$val" -ge 80 ]; then echo "$RED"
  elif [ "$val" -ge 50 ]; then echo "$YELLOW"
  else echo "$GREEN"; fi
}

fmt_dur() {
  local total_sec=$(($1 / 1000))
  local h=$((total_sec / 3600))
  local m=$(((total_sec % 3600) / 60))
  local s=$((total_sec % 60))
  if [ "$h" -gt 0 ]; then printf "%dh %02dm" "$h" "$m"
  elif [ "$m" -gt 0 ]; then printf "%dm %02ds" "$m" "$s"
  else printf "%ds" "$s"; fi
}

fmt_countdown() {
  local diff=$(($1 - $(date +%s)))
  if [ "$diff" -le 0 ]; then echo "now"; return; fi
  printf "%dh %dm" "$((diff / 3600))" "$(((diff % 3600) / 60))"
}

fmt_tokens() {
  local t=$1
  if [ -z "$t" ] || [ "$t" = "null" ]; then echo "0"; return; fi
  if [ "$t" -ge 1000000 ]; then
    printf "%d.%dM" "$((t / 1000000))" "$(((t % 1000000) / 100000))"
  elif [ "$t" -ge 1000 ]; then
    printf "%d.%dK" "$((t / 1000))" "$(((t % 1000) / 100))"
  else
    echo "$t"
  fi
}

CTX_LABEL=""
if [ -n "$CTX_SIZE" ]; then
  if [ "$CTX_SIZE" -ge 1000000 ]; then CTX_LABEL="${DIM}1M${RESET}"
  else CTX_LABEL="${DIM}200K${RESET}"; fi
fi

# Resolve repository data against workspace.current_dir, never the hook process cwd.
BRANCH=""
GIT_STATS=""
REPO_LINK="${DIR##*/}"
if GIT_STATUS=$(git -C "$DIR" status --porcelain=v1 --branch 2>/dev/null); then
  GIT_HEADER=${GIT_STATUS%%$'\n'*}
  BRANCH=${GIT_HEADER#\#\# }
  BRANCH=${BRANCH%%...*}
  [ "$BRANCH" = "HEAD (no branch)" ] && BRANCH=""

  GIT_M=0 GIT_A=0 GIT_D=0
  while IFS= read -r status_line; do
    [[ "$status_line" == "## "* ]] && continue
    status=${status_line:0:2}
    [[ "$status" == *M* ]] && GIT_M=$((GIT_M + 1))
    if [[ "$status" == "??" || "$status" == *A* ]]; then GIT_A=$((GIT_A + 1)); fi
    [[ "$status" == *D* ]] && GIT_D=$((GIT_D + 1))
  done <<< "$GIT_STATUS"

  PARTS=""
  [ "$GIT_M" -gt 0 ] && PARTS="${YELLOW}${GIT_M}M${RESET}"
  [ "$GIT_A" -gt 0 ] && { [ -n "$PARTS" ] && PARTS="${PARTS} "; PARTS="${PARTS}${GREEN}${GIT_A}A${RESET}"; }
  [ "$GIT_D" -gt 0 ] && { [ -n "$PARTS" ] && PARTS="${PARTS} "; PARTS="${PARTS}${RED}${GIT_D}D${RESET}"; }
  GIT_STATS=$PARTS

  REMOTE=$(git -C "$DIR" remote get-url origin 2>/dev/null)
  if [ -n "$REMOTE" ]; then
    case "$REMOTE" in
      git@github.com:*) REMOTE="https://github.com/${REMOTE#git@github.com:}" ;;
    esac
    REMOTE=${REMOTE%.git}
    REPO_NAME=${REMOTE##*/}
    REPO_LINK=$(printf '%b' "\e]8;;${REMOTE}\a${REPO_NAME}\e]8;;\a")
  fi
fi

[ "$PCT" -lt 0 ] && PCT=0
[ "$PCT" -gt 100 ] && PCT=100
BAR_COLOR=$(color_pct "$PCT")
BAR_W=15
FILLED=$((PCT * BAR_W / 100)); EMPTY=$((BAR_W - FILLED))
BAR=""
i=0
while [ "$i" -lt "$FILLED" ]; do BAR="${BAR}${BAR_COLOR}●${RESET}"; i=$((i + 1)); done
i=0
while [ "$i" -lt "$EMPTY" ]; do BAR="${BAR}${DIM}●${RESET}"; i=$((i + 1)); done
DUR=$(fmt_dur "$DURATION_MS")

CACHE_HIT=""
if [ -n "$CACHE_READ" ] && [ -n "$CUR_INPUT" ] && [ "$CUR_INPUT" != "0" ] && [ "$CUR_INPUT" != "null" ]; then
  CACHE_TOTAL=$((CACHE_READ + CUR_INPUT + ${CACHE_CREATE:-0}))
  if [ "$CACHE_TOTAL" -gt 0 ]; then
    CACHE_PCT=$((CACHE_READ * 100 / CACHE_TOTAL))
    CACHE_C=$(color_pct "$((100 - CACHE_PCT))")
    CACHE_HIT="${DIM}cache${RESET} ${CACHE_C}${CACHE_PCT}%${RESET}"
  fi
fi

# Line 1: model, repo, branch, edit stats, agent, and Vim mode.
L1="${CYAN}${BOLD}${MODEL}${RESET}"
[ -n "$CTX_LABEL" ] && L1="${L1} ${CTX_LABEL}"
[ -n "$VERSION" ] && L1="${L1} ${DIM}v${VERSION}${RESET}"
L1="${L1}${SEP}${WHITE}${REPO_LINK}${RESET}"
[ -n "$BRANCH" ] && L1="${L1} ${DIM}(${BRANCH})${RESET}"

LINES_PART=""
if [ -n "$LINES_ADD" ] && [ "$LINES_ADD" != "0" ]; then LINES_PART="${GREEN}+${LINES_ADD}${RESET}"; fi
if [ -n "$LINES_DEL" ] && [ "$LINES_DEL" != "0" ]; then
  [ -n "$LINES_PART" ] && LINES_PART="${LINES_PART} ${RED}-${LINES_DEL}${RESET}" || LINES_PART="${RED}-${LINES_DEL}${RESET}"
fi
[ -n "$LINES_PART" ] && L1="${L1}${SEP}${LINES_PART} ${DIM}lines${RESET}"
[ -n "$GIT_STATS" ] && L1="${L1}${SEP}${GIT_STATS}"
[ -n "$AGENT" ] && L1="${L1}${SEP}${MAGENTA}${AGENT}${RESET}"
[ -n "$VIM_MODE" ] && {
  if [ "$VIM_MODE" = "NORMAL" ]; then L1="${L1}${SEP}${BLUE}${BOLD}NOR${RESET}"
  else L1="${L1}${SEP}${GREEN}${BOLD}INS${RESET}"; fi
}

# Line 2: context, cost, duration, and rate limits.
COST_FMT=$(printf '$%.2f' "$COST")
L2="${BAR} ${DIM}${PCT}%${RESET}${SEP}${YELLOW}${COST_FMT}${RESET}${SEP}${DIM}${DUR}${RESET}"
if [ -n "$RATE_5H" ]; then
  R5_INT=$(printf "%.0f" "$RATE_5H"); R5_C=$(color_pct "$R5_INT")
  L2="${L2}${SEP}${DIM}5h${RESET} ${R5_C}${R5_INT}%${RESET}"
  [ -n "$RESET_5H" ] && [ "$RESET_5H" != "null" ] && L2="${L2} ${DIM}($(fmt_countdown "$RESET_5H"))${RESET}"
fi
if [ -n "$RATE_7D" ]; then
  R7_INT=$(printf "%.0f" "$RATE_7D"); R7_C=$(color_pct "$R7_INT")
  L2="${L2}${SEP}${DIM}7d${RESET} ${R7_C}${R7_INT}%${RESET}"
  [ -n "$RESET_7D" ] && [ "$RESET_7D" != "null" ] && L2="${L2} ${DIM}($(fmt_countdown "$RESET_7D"))${RESET}"
fi

# Line 3: cache, token totals, API wait, and current token detail.
L3=$CACHE_HIT
IN_FMT=$(fmt_tokens "$TOTAL_IN_TOKENS"); OUT_FMT=$(fmt_tokens "$TOTAL_OUT_TOKENS")
TOKENS_PART="${DIM}in:${RESET} ${CYAN}${IN_FMT}${RESET} ${DIM}out:${RESET} ${MAGENTA}${OUT_FMT}${RESET}"
[ -n "$L3" ] && L3="${L3}${SEP}${TOKENS_PART}" || L3=$TOKENS_PART
API_DUR=$(fmt_dur "$API_DURATION_MS")
if [ "$DURATION_MS" -gt 0 ] && [ "$API_DURATION_MS" -gt 0 ]; then
  L3="${L3}${SEP}${DIM}api wait${RESET} ${CYAN}${API_DUR}${RESET} ${DIM}($((API_DURATION_MS * 100 / DURATION_MS))%)${RESET}"
else
  L3="${L3}${SEP}${DIM}api wait${RESET} ${CYAN}${API_DUR}${RESET}"
fi
L3="${L3}${SEP}${DIM}cur${RESET} $(fmt_tokens "$CUR_INPUT") ${DIM}in${RESET} $(fmt_tokens "$CACHE_READ") ${DIM}read${RESET} $(fmt_tokens "$CACHE_CREATE") ${DIM}write${RESET}"

echo -e "$L1"
echo -e "$L2"
echo -e "$L3"
