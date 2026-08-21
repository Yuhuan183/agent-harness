#!/usr/bin/env python3
"""What actually fills a window, from this machine's real sessions. Reports; never fails.

Why this exists. `docs/architecture/context-engineering.md` said the resident
load is not where the cost is - that the window is really eaten by large
outputs, exploration dumps and pasted content - and that sentence had no number
behind it. Meanwhile three report scripts and a row of word budgets guard the
resident side down to the word. Guarding the small half precisely while the
large half goes unmeasured is the kind of mistake that looks like discipline.

What it measures, and how much to trust each number:

- **floor and peak are exact.** They come from `usage` on real requests
  (`input_tokens + cache_creation + cache_read`), so "resident load is a sixth
  of a peak window" is an observation, not an estimate. Floor is the smallest
  prompt among a session's first requests: everything resident plus the opening
  message.
- **the attribution is approximate.** Transcript blocks are re-estimated with a
  CJK-aware rule (a CJK character costs about one token, other text about four
  characters each), and the result under-counts real growth by a factor this
  script prints rather than hides. The factor is not a constant - it ranges
  widely across sessions - so read the shares as an ordering, not as
  percentages. The ordering is what decisions need anyway.

Why the factor is there at all: a transcript is not the prompt. Per-block
framing, injected content the transcript does not record as an attachment, and
tool results stored differently from how they are sent all land in the gap. That
gap is the honest limit of this instrument and is printed on every run.

Evidence class: machine-local. This reads one developer's transcripts, so it
says what this machine's work looks like, not what the repo mandates.

Usage:
    scripts/context-inflow-report.py [--sessions N] [--json]
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CJK = re.compile(r"[　-〿㐀-鿿＀-￯]")
MIN_REQUESTS = 20


def estimate(text: str) -> int:
    if not text:
        return 0
    cjk = len(CJK.findall(text))
    return cjk + (len(text) - cjk) // 4


def blob(block: object) -> str:
    if isinstance(block, str):
        return block
    if not isinstance(block, dict):
        return str(block)
    kind = block.get("type")
    if kind in ("text", "thinking"):
        return block.get("text") or block.get("thinking") or ""
    if kind == "tool_use":
        return json.dumps(block.get("input") or {}, ensure_ascii=False)
    if kind == "tool_result":
        content = block.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(blob(item) for item in content)
        return json.dumps(content, ensure_ascii=False) if content else ""
    return json.dumps(block, ensure_ascii=False)


def transcripts(directory: str | None = None) -> list[str]:
    if directory:
        return sorted(glob.glob(os.path.join(directory, "*.jsonl")))
    slug = str(ROOT).replace("/", "-")
    return sorted(glob.glob(os.path.expanduser(f"~/.claude/projects/{slug}/*.jsonl")))


def read_session(path: str) -> dict | None:
    source = collections.Counter()
    results = collections.Counter()
    calls = collections.Counter()
    tool_of: dict[str, str] = {}
    running, points, blocks = 0, [], 0

    for line in open(path, encoding="utf-8"):
        try:
            row = json.loads(line)
        except ValueError:
            continue
        kind = row.get("type")
        if kind == "attachment":
            size = estimate(json.dumps(row.get("attachment") or {}, ensure_ascii=False))
            source["注入 (skill 清單, hook 回覆, 檔案差異…)"] += size
            running += size
            blocks += 1
        elif kind in ("assistant", "user"):
            message = row.get("message") or {}
            content = message.get("content")
            items = [content] if isinstance(content, str) else (content or [])
            for block in items:
                size = estimate(blob(block))
                running += size
                blocks += 1
                if not isinstance(block, dict):
                    source["使用者訊息"] += size
                    continue
                btype = block.get("type")
                if btype == "tool_use":
                    tool_of[block.get("id")] = block.get("name", "?")
                    source["模型: 工具呼叫參數"] += size
                    calls[block.get("name", "?")] += size
                elif btype == "tool_result":
                    source["工具結果"] += size
                    results[tool_of.get(block.get("tool_use_id"), "?")] += size
                elif btype == "thinking":
                    source["模型: thinking"] += size
                elif btype == "text" and kind == "assistant":
                    source["模型: 回覆文字"] += size
                else:
                    source["使用者訊息"] += size
            usage = message.get("usage") or {}
            if usage:
                total = (usage.get("input_tokens", 0)
                         + usage.get("cache_creation_input_tokens", 0)
                         + usage.get("cache_read_input_tokens", 0))
                if total:
                    points.append((running, total))

    if len(points) < MIN_REQUESTS:
        return None
    low = points[len(points) // 10]
    high = max(points, key=lambda p: p[1])
    return {
        "session": os.path.basename(path)[:8],
        "requests": len(points),
        "floor": min(v for _, v in points[:5] if v > 0),
        "peak": high[1],
        # how much real window growth one estimated token corresponds to
        "factor": ((high[1] - low[1]) / (high[0] - low[0])
                   if high[0] > low[0] else None),
        "source": source,
        "results": results,
        "calls": calls,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sessions", type=int, default=0,
                        help="use only the N most recent (0 = all)")
    parser.add_argument("--transcripts", default=None,
                        help="read this directory instead of the CLI's "
                             "(the suite uses it; there is no other reason)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    paths = transcripts(args.transcripts)
    if args.sessions:
        paths = paths[-args.sessions:]
    sessions = [s for s in (read_session(p) for p in paths) if s]
    if not sessions:
        where = args.transcripts or f"~/.claude/projects/{str(ROOT).replace('/', '-')}/"
        print(f"no session with >= {MIN_REQUESTS} model requests under {where}")
        return 0

    source = collections.Counter()
    results = collections.Counter()
    calls = collections.Counter()
    for s in sessions:
        source.update(s["source"])
        results.update(s["results"])
        calls.update(s["calls"])

    floors = [s["floor"] for s in sessions]
    peaks = [s["peak"] for s in sessions]
    shares = [s["floor"] / s["peak"] for s in sessions]
    factors = sorted(s["factor"] for s in sessions if s["factor"])

    report = {
        "sessions": len(sessions),
        "floor_median": statistics.median(floors),
        "peak_median": statistics.median(peaks),
        "floor_share_median": statistics.median(shares),
        "factor_median": statistics.median(factors) if factors else None,
        "factor_range": [factors[0], factors[-1]] if factors else None,
        "source": dict(source.most_common()),
        "results": dict(results.most_common(6)),
        "calls": dict(calls.most_common(6)),
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    print(f"{len(sessions)} 個工作階段 (至少 {MIN_REQUESTS} 次模型請求)\n")
    print("實測, 沒有估算成分:")
    print(f"  常駐 + 開場的窗口   中位數 {statistics.median(floors):>9,.0f} tokens")
    print(f"  見過的最大窗口       中位數 {statistics.median(peaks):>9,.0f} tokens")
    print(f"  常駐佔最大窗口       中位數 {statistics.median(shares):>9.1%}")

    if factors:
        print(f"\n以下是估算. 校準: 每 1 個估算 token 對應實際成長 "
              f"{statistics.median(factors):.2f} (範圍 {factors[0]:.2f}–{factors[-1]:.2f}).")
        print("  倍率不固定, 所以把下面當排序讀, 不要當百分比讀.")

    total = sum(source.values()) or 1
    print("\n窗口裡的內容, 按來源:")
    for name, size in source.most_common():
        print(f"  {size / total:6.1%}  {name}")

    for label, counter in (("工具結果來自", results), ("工具呼叫參數來自", calls)):
        subtotal = sum(counter.values()) or 1
        print(f"\n{label}:")
        for name, size in counter.most_common(6):
            print(f"  {size / subtotal:6.1%}  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
