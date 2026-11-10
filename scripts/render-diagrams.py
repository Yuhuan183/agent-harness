#!/usr/bin/env python3
# Read: before landing a document that adds or changes a Mermaid block or a diagram source
"""Check Mermaid blocks in Markdown, or export Mermaid sources to SVG.

  render-diagrams.py check [FILE.md ...]   render every ```mermaid block to a
                                           temporary SVG; report the blocks
                                           that fail. Default files: README.md
                                           and docs/**/*.md except docs/research.
  render-diagrams.py export FILE.mmd ...   write FILE.svg beside each source.

The renderer is @mermaid-js/mermaid-cli, pinned below and run through npx.
Its first run downloads a headless Chrome into the user cache, not into this
repository. Exit status: 0 when every block renders, 1 when one fails, 2 when
the renderer cannot start.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Pinned 2026-11-10: 11.17.0 was released 2026-09-02. The 12.x line was newer
# than two months at the time and is not needed for the diagram types used.
MERMAID_CLI = "@mermaid-js/mermaid-cli@11.17.0"
ROOT = Path(__file__).resolve().parents[1]
FENCE = re.compile(r"^```mermaid\s*\n(.*?)^```\s*$", re.M | re.S)


def renderer() -> list[str]:
    if shutil.which("npx") is None:
        print("ERROR: npx not found; install Node.js to render Mermaid",
              file=sys.stderr)
        sys.exit(2)
    return ["npx", "--yes", "-p", MERMAID_CLI, "mmdc", "--quiet"]


def render(source: Path, target: Path) -> tuple[bool, str]:
    result = subprocess.run(
        [*renderer(), "-i", str(source), "-o", str(target)],
        capture_output=True, text=True)
    lines = (result.stderr or result.stdout).strip().splitlines()
    errors = [line.strip() for line in lines if "error" in line.lower()]
    return result.returncode == 0, (errors or lines or [""])[0]


def default_documents() -> list[Path]:
    docs = [ROOT / "README.md"]
    docs += [p for p in sorted((ROOT / "docs").rglob("*.md"))
             if "research" not in p.relative_to(ROOT / "docs").parts]
    return docs


def check(paths: list[Path]) -> int:
    failures = 0
    blocks = 0
    with tempfile.TemporaryDirectory() as temp:
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for index, match in enumerate(FENCE.finditer(text)):
                blocks += 1
                line = text.count("\n", 0, match.start()) + 1
                source = Path(temp) / f"block{blocks}.mmd"
                source.write_text(match.group(1), encoding="utf-8")
                ok, message = render(source, source.with_suffix(".svg"))
                if not ok:
                    failures += 1
                    print(f"{path}:{line}: mermaid block {index + 1} fails: {message}")
    print(f"{blocks} mermaid blocks checked, {failures} failed")
    return 1 if failures else 0


def export(paths: list[Path]) -> int:
    failures = 0
    for source in paths:
        ok, message = render(source, source.with_suffix(".svg"))
        print(f"{source.with_suffix('.svg')}: {'written' if ok else 'FAILED ' + message}")
        failures += 0 if ok else 1
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in ("check", "export"):
        print(__doc__, file=sys.stderr)
        return 2
    command, files = argv[0], [Path(arg) for arg in argv[1:]]
    if command == "export":
        if not files:
            print("ERROR: export needs at least one .mmd file", file=sys.stderr)
            return 2
        return export(files)
    return check(files or default_documents())


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
