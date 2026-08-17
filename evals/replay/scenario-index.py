#!/usr/bin/env python3
"""Render the scenario index from the scenarios themselves.

Generated rather than maintained, for the reason `e4` exists: a table typed
beside the artifact that already states the same thing is the failure this
directory keeps cataloguing. Every column here is read out of the scenario's own
frontmatter, so the index cannot disagree with what a run would be graded
against.

`--check` compares the block currently in `README.md` and exits 1 on drift; the
contract suite calls it that way, so a new scenario without an index row is red
rather than merely undocumented.

Usage:
    scenario-index.py            # print the block
    scenario-index.py --write    # splice it into README.md
    scenario-index.py --check    # exit 1 if README.md is out of date
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCENARIOS = HERE / "scenarios"
README = HERE / "README.md"

START = "<!-- scenario-index:start -->"
END = "<!-- scenario-index:end -->"

# What the leading letter groups. The prefixes were always a taxonomy; nothing
# wrote the key down, which is what made a directory listing unreadable.
FAMILIES = {
    "r": "lifecycle 三問 — 中斷, 連續 correction, 衝突的 leaf",
    "m": "上限請求為什麼不觸發 DECISION — 操弄系列",
    "d": "派工子句",
    "p": "契約對上 client 指令",
    "q": "隔離的 leaf 帶回來的東西夠不夠裁決",
    "v": "驗證子句 — 用產出正確性定價",
    "x": "語言底線",
    "e": "工程 skill 蒸餾的驗收格 (M1)",
}


def field(text: str, name: str) -> str:
    """One frontmatter value, folded to a single line."""
    head = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not head:
        return ""
    found = re.search(rf"^{name}:\s*(.+?)(?=\n\S+:|\Z)", head.group(1), re.M | re.S)
    return " ".join(found.group(1).split()) if found else ""


def rows() -> list[tuple[str, str, str]]:
    collected = []
    for path in sorted(SCENARIOS.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        collected.append((
            field(text, "id") or path.stem,
            field(text, "measures"),
            field(text, "fixture"),
        ))
    return collected


def family_of(scenario_id: str) -> str:
    letter = scenario_id[0]
    return letter if letter in FAMILIES else "?"


def block() -> str:
    lines = [START, "",
             "前綴是分組, 這裡是那把鑰匙:", ""]
    for letter, meaning in FAMILIES.items():
        lines.append(f"- **`{letter}`** — {meaning}")
    lines += ["", "| 情境 | 量什麼 | fixture |", "|---|---|---|"]
    for scenario_id, measures, fixture in rows():
        code = f"`{fixture}`" if fixture else "—"
        lines.append(f"| `{scenario_id}` | {measures} | {code} |")
    lines += ["",
              f"共 {len(rows())} 個情境. 這張表由 `scenario-index.py` 從各情境的 "
              "frontmatter 生成, 契約測試會比對; 手改這裡不會生效.",
              "", END]
    return "\n".join(lines) + "\n"


def spliced() -> str:
    text = README.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END) + r"\n",
                         re.S)
    if not pattern.search(text):
        raise SystemExit(f"{README}: no {START} … {END} block to fill")
    return pattern.sub(block(), text)


def main() -> int:
    argument = sys.argv[1] if len(sys.argv) > 1 else ""
    if argument == "--write":
        README.write_text(spliced(), encoding="utf-8")
        print(f"wrote {len(rows())} rows into {README.name}")
        return 0
    if argument == "--check":
        if README.read_text(encoding="utf-8") == spliced():
            return 0
        print(f"{README.name}: scenario index is out of date; "
              "run scenario-index.py --write", file=sys.stderr)
        return 1
    print(block(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
