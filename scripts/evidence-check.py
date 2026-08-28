#!/usr/bin/env python3
"""Is the recorded evidence still attached to anything real? Reports; never fails.

Two instruments, one question. Both were built after a 2026-08-08 check found
that most of this repo's evidence citations had quietly stopped resolving.

1. **Citations.** Every backtick-wrapped hex string in tracked markdown, sorted
   by what can be established about it: `resolves` here, `foreign` (the line
   carries a URL or names the repository it belongs to), `fingerprint` (one of
   this repo's own content hashes — a measured surface or a contract hash, which
   git was never going to resolve), and `unresolved` for the residual.

   The residual used to be called `dead`, with a docstring asserting those were
   all stale short SHAs. Re-checked 2026-08-17: of twenty, seven were upstream
   pins quoted without a link and thirteen were fingerprints. **Zero were stale
   local commits.** The bucket was reporting the shape of a token rather than its
   substance — the failure the traps call cluster B, in the instrument built to
   price evidence — and it had a clean, quotable, entirely wrong headline. The
   residual is now named for what is actually known, because after a rebase "was
   this ever a commit" is not answerable, and a bucket that answers it anyway is
   how the first false finding gets published.

   The original concern still stands on its own: a bare short SHA is not a
   durable anchor in a repo that rebases before merging. It is just not what
   this instrument was measuring.

2. **Trap evidence age.** Each trap declares its measured surface in
   `surface.tsv`; result rows stamped `[surface <short>]` are compared against
   the current fingerprint. A row whose stamp no longer matches is not wrong, it
   is *undated* - it measured rules that have since changed, and saying so is the
   whole point. Rows with no stamp predate the mechanism and count as unverified.

3. **Prose attestations.** A sentence claiming a dated local check is behavioural
   evidence exactly like a stamped result row, and until 2026-08-11 it was the
   only kind with no mechanism at all. Every line carrying both a verification
   verb and an ISO date is listed with its age, so the set is enumerable and
   re-checkable instead of being discovered by accident.

4. **Version attestations.** The subset that names a version of a tool this
   machine can be asked about, cross-checked against the live `--version`. This
   is the instrument with teeth, and it exists because both failures that
   prompted it were of this exact shape: the runtime guide attested "0.34.0
   verified locally" while the machine ran 0.33.0, and `RTK.md` attested rtk
   0.45.0 - read off `brew info`, which prints the formula's version directly
   above `Not installed` - while the only rtk here was 0.42.4.

   `differs` is not an accusation. A document legitimately records history (the
   before/after table in `RTK.md` names both versions on purpose), and a document
   may describe another machine. What it stops is the case where nobody looked.

Exit status is always 0. This is an attestation, not a gate: a stale row is a
fact to weigh, and the legitimate reasons for one (the rules improved) outnumber
the illegitimate ones by far. Making it fail-closed would only teach people to
stop stamping rows - and, now, to stop writing the date next to what they
checked, which would cost more than it saved.

Usage:
    scripts/evidence-check.py [--json] [--attestation-age DAYS]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CITATION = re.compile(r"`([0-9a-f]{7,40})`")
# A line that names another repository is citing that repository's history, and
# no amount of `git rev-parse` here will resolve it. The URL rule missed these
# because an upstream pin is usually quoted bare inside a table cell.
UPSTREAM_REPO = re.compile(
    r"mattpocock/skills|anthropics/claude-plugins|headroomlabs-ai|"
    r"Nanako0129/pilotfish|marketplace|upstream pin|上游|marketplace pin",
    re.IGNORECASE)
FINGERPRINT_WORD = re.compile(r"指紋|fingerprint|surface", re.IGNORECASE)
STAMP = re.compile(r"\[surface ([0-9a-f]{8})\]")
URL = re.compile(r"https?://")

# A verification verb next to an ISO date. Both halves are required: a bare date
# is a changelog entry, and a bare verb is a plan. Only the pair claims that
# something was actually checked on a particular day.
ISO_DATE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")
VERIFICATION_VERB = re.compile(
    r"查核|實測|驗證|重跑|verified|measured|re-run|reproduced", re.IGNORECASE)

# Tools whose claimed version can be checked against the machine. The key is the
# name as it appears in prose, the value is how to ask. Anything not listed is
# still inventoried by instrument 3, it just cannot be cross-checked.
PROBES = {
    "headroom": ("headroom", "--version"),
    "rtk": ("rtk", "--version"),
    "ripgrep": ("rg", "--version"),
    "claude code": ("claude", "--version"),
    "codex": ("codex", "--version"),
}
# Prose spellings that mean the same tool. `headroom-ai` is the PyPI package name
# and is what the version tables use.
ALIASES = {"headroom-ai": "headroom", "claude-code": "claude code"}
VERSION_TOKEN = re.compile(r"\bv?(\d+\.\d+(?:\.\d+)?)\b")

# The version has to be *adjacent* to the tool name. The first draft of this
# instrument attributed every number on any line mentioning a tool, and reported
# twenty "differences": percentages (`56.28`), an IP (`127.0.0`), Pilotfish's
# `1.3.10` on a line that also said Headroom, model names (`5.6`). A check that
# is mostly false positives gets skimmed and then ignored, which is worse than
# not having it - so the pattern now demands an explicit attribution and accepts
# only `rtk 0.45.0`, `headroom, version 0.34.0`, `Claude Code v2.1.226` shapes.
ATTRIBUTION = r"[\s,:]*(?:version\s+)?v?(\d+\.\d+(?:\.\d+)?)"

# A floor is not an attestation. `需要 Claude Code 2.1.207 以上版本` names the
# oldest release that works, so it differs from the local version on purpose and
# for as long as the requirement stands - reporting it as a discrepancy every
# run is how a report earns the right to be ignored. Satisfied floors are
# counted and dropped; an unmet one is the thing worth printing.
FLOOR = re.compile(
    # `起` is zh-TW's "from <version> onwards", the exact counterpart of the
    # English floors beside it. Without it, `Headroom v0.34 起已移除 …` filed as a
    # discrepancy on every run - a permanent finding about a sentence that is
    # still true, which is how a report teaches people to skip it.
    # `0.45+` is the same statement as `0.45 以上` and was read as an exact
    # version until 2026-08-21, when a comment saying `rtk 0.45+` reported
    # `match` on a machine that happened to run 0.45.0.
    r"以上|至少|\d\S*\s*起|or newer|or later|at least|minimum|\bmin\b|>=|\d\+|\+ ")

# A dated section title is a record of what was checked then, not a claim about
# now. `#### 2026-08-10 查核結果 (Headroom 0.34 升級)` names the version it was
# about, and rewriting it to today's version would destroy the thing it exists to
# preserve. Links to such a heading carry the same text and the same exemption.
HISTORY = re.compile(r"^#{1,6}\s+20\d\d-\d\d-\d\d|\]\(\S*#20\d\d-\d\d-\d\d")

# Only floors are compared against this machine, and that is a narrowing.
#
# The check was built for one shape: a document attesting "verified locally
# 0.34.0" while the machine ran 0.33.0. On 2026-08-21 it had six subjects and
# not one was that shape - two stated what PyPI and GitHub publish, one was a
# journal line recording a *wrong* past claim and reporting `match` because the
# machine had since caught up, one was a floor spelled `0.45+`, and two were
# real floors. Every `match` was a coincidence, and on a shared repository an
# exact version that is right on the machine that wrote it reads as a
# discrepancy on every other one.
#
# Deciding from the prose whether a line is about this machine was tried first
# and does not work: the research currency row saying "upstream only, not this
# machine" matched a locality pattern on the very word it uses to disclaim
# locality. A regex cannot separate a claim from its negation.
#
# So the rule is structural. Machine-local version records left the guidance
# tier on 2026-08-21 by policy, which means an exact version in a tracked
# document is now about upstream or about history, and a local binary
# adjudicates neither. Floors stay: a stated minimum is portable, true on every
# machine, and the one version statement a shared repository can hold.
#
# What this gives up, stated plainly: nothing mechanical now catches a
# machine-local version record reappearing in the guidance tier. That boundary
# is a policy and not a gate.
# Two ways a version on a line is not a claim about this machine now.
#
# `retracted`: the document itself has already declared it false. The
# 2026-08-20 Headroom round left two of them standing on purpose: the evidence
# tier records what was checked, including what was later overturned, so the
# wrong sentence stays visible next to the reason it was wrong. Reporting those
# forever is the FLOOR problem again - a permanent finding about a line that is
# not a claim any more, which is how a report earns the right to be skimmed.
#
# Three deliberate narrowings, because an exemption is also a way to silence a
# real finding:
#   * The marker carries a date, so it is a record rather than a switch.
#   * It has to sit on the same line as the version, so it cannot be set once at
#     the top of a file and quietly cover every claim below it.
#   * It is an HTML comment, invisible when rendered - a reader sees the prose
#     retraction the author had to write anyway, not the token that silenced the
#     scanner.
# Marking a *live* claim retracted does not hide a stale version; it writes a
# falsehood into the prose, which is a worse defect than a row in this report.
# `pinned`: the version is frozen by whatever the line describes and was never
# meant to track the local install - the release a cited paper reverse-engineered,
# or the build a finished batch of runs was probed against. Those never come true
# again, so without this they are permanent rows; and rewriting them to today's
# version would falsify a citation or an experimental condition, which is the
# opposite of what this instrument is for. Note the asymmetry that keeps it
# honest: a doc's own "checked on <date>, CLI was X" line stays unexempt, because
# that is the shape the 2026-08-20 Headroom drift hid in and the shape this
# instrument earns its keep on.
#
# The date on either marker is when the marker was applied, not when the fact
# was true - an exemption should say who took it out and when.
NOT_A_LIVE_CLAIM = re.compile(
    r"<!--\s*(?:retracted|pinned)\s+20\d\d-\d\d-\d\d\s*-->")


def tracked_markdown() -> list[Path]:
    listed = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "*.md"],
        capture_output=True, text=True, check=True).stdout.split()
    return [ROOT / name for name in listed]


def resolves(sha: str) -> bool:
    return subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--verify", "-q", f"{sha}^{{commit}}"],
        capture_output=True).returncode == 0


def known_fingerprints() -> set[str]:
    """The fingerprint each suite computes for its surface right now.

    Computed, not pattern-matched: whether a token is a commit or a content hash
    is a question about provenance, and this is the one part of it that can be
    answered positively. It only ever recognises *current* fingerprints —
    historical stamps are preserved in the READMEs on purpose ("the stamp stays
    at X because that is what produced these rows") and will never equal a fresh
    computation, which is why the residual bucket carries a caveat instead of
    pretending to be a defect list.
    """
    found: set[str] = set()
    for row in audit_traps():
        current = str(row.get("current") or "")
        if current:
            found.update({current, current[:8], current[:12]})
    return found


def audit_citations() -> dict[str, list[dict[str, object]]]:
    """Backticked hex, sorted by what can be established about it.

    The first draft had one residual bucket called `dead` and a docstring
    asserting those were all stale short SHAs. On 2026-08-17 that population had
    turned over completely: of twenty, seven were upstream pins written without
    a link and thirteen were this repo's own content fingerprints — measured
    surfaces and contract hashes, which git was never going to resolve. Zero
    were stale local commits.

    That is the failure the traps call cluster B, in the instrument built to
    price evidence: a checker keyed on the shape of a token (hex in backticks)
    rather than its substance (whether it is a git ref at all). So the classes
    now name what was established, and the residual is `unresolved` rather than
    `dead` — because after a rebase, "was this ever a commit" is not answerable,
    and a bucket that asserts it anyway invites exactly one clean false finding.
    """
    buckets: dict[str, list[dict[str, object]]] = {
        "resolves": [], "foreign": [], "fingerprint": [], "unresolved": []}
    fingerprints = known_fingerprints()
    seen: dict[str, dict[str, object]] = {}
    for path in tracked_markdown():
        relative = path.relative_to(ROOT).as_posix()
        for line in path.read_text(encoding="utf-8").splitlines():
            for sha in CITATION.findall(line):
                if sha.isdigit():
                    continue
                record = seen.setdefault(
                    sha, {"sha": sha, "sites": [], "linked": False,
                          "upstream": False, "stamped": False})
                if relative not in record["sites"]:
                    record["sites"].append(relative)
                record["linked"] = record["linked"] or bool(URL.search(line))
                record["upstream"] = record["upstream"] or bool(
                    UPSTREAM_REPO.search(line))
                # `[surface 20411df0]` and prose naming a fingerprint are the
                # two forms this repo writes content hashes in.
                record["stamped"] = record["stamped"] or bool(
                    re.search(rf"surface\s+{sha}", line)
                    or (FINGERPRINT_WORD.search(line) and sha in line))
    for sha, record in sorted(seen.items()):
        if resolves(sha):
            buckets["resolves"].append(record)
        elif record["linked"] or record["upstream"]:
            buckets["foreign"].append(record)
        elif record["stamped"] or sha in fingerprints:
            buckets["fingerprint"].append(record)
        else:
            buckets["unresolved"].append(record)
    return buckets


# Long enough to name the files a reader would check, short enough that a
# stamp from before a reorganisation does not bury the other surfaces.
DRIFT_LIST = 10


def audit_traps(drift: bool = False) -> list[dict[str, object]]:
    # `trap-surface.py` is not an importable module name (the hyphen), and
    # renaming it would break the command line it documents, so load it by path.
    location = ROOT / "evals" / "scripts" / "trap-surface.py"
    spec = importlib.util.spec_from_file_location("trap_surface", location)
    if spec is None or spec.loader is None:  # pragma: no cover - path typo
        raise SystemExit(f"cannot load {location}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fingerprint = module.fingerprint
    short = module.SHORT

    rows = []
    # Ask the fingerprint tool which suites exist rather than globbing here: the
    # two answers drifting apart is exactly how a suite ends up unaudited, and
    # `evals/replay/` sits one directory shallower than the traps do.
    for trap in module.traps():
        listing = module.listing_for(trap)
        try:
            current = fingerprint(trap)[0][:short]
        except module.SurfaceIncomplete as gone:
            # trap-surface used to exit with this message itself. Reading a
            # revision made it an exception instead, and an exception nobody
            # catches turns an actionable line into a traceback.
            rows.append({"trap": trap, "current": None, "missing": str(gone),
                         "result_rows": 0, "stamped": 0, "current_stamps": 0,
                         "stale_stamps": 0, "unstamped_rows": 0})
            continue
        readme = listing.parent / "README.md"
        text = readme.read_text(encoding="utf-8") if readme.exists() else ""
        stamps = STAMP.findall(text)
        # Result rows are counted by their date prefix, which is how s7-s10
        # write them. s11 reports a batch as one stamped block instead, so the
        # count would be zero while a stamp exists - and subtracting one from
        # the other produced "unverified -1" in the first run of this tool.
        # Report the two independently and never derive a negative: an
        # unrecognised table shape is a thing to look at, not a number to
        # invent.
        dated_rows = [line for line in text.splitlines()
                      if line.startswith("| 2026-")]
        # Split the unstamped rows on the only line that means anything: rows
        # older than the listing had nothing to record, rows younger than it
        # were supposed to record something and did not.
        began = convention_began(module, trap)
        predating = sum(1 for line in dated_rows
                        if began and line[2:12] < began and "[surface " not in line)
        # Per-group digests when the listing declares groups. Reported beside
        # the overall, never instead of it: the overall is what a stamp holds,
        # and the groups only answer the follow-up question a stale stamp
        # raises - which half moved. A listing with no headers yields one group
        # and this reads exactly as it did before.
        try:
            groups = module.group_fingerprints(trap)
        except Exception:
            groups = {}
        record = {
            "trap": trap,
            "current": current,
            "groups": groups if len(groups) > 1 else {},
            "result_rows": len(dated_rows),
            "stamped": len(stamps),
            "current_stamps": sum(1 for stamp in stamps if stamp == current),
            "stale_stamps": sum(1 for stamp in stamps if stamp != current),
            "unstamped_rows": max(0, len(dated_rows) - len(stamps)),
            "convention_began": began,
            "predating_rows": predating,
        }
        if drift:
            record["drift"] = [
                {"stamp": stamp, **surface_drift(module, trap, stamp, short)}
                for stamp in dict.fromkeys(s for s in stamps if s != current)
            ]
        rows.append(record)
    return rows


def convention_began(module, trap: str) -> str | None:
    """The day this trap's surface listing first existed.

    A result row cannot carry a fingerprint from before there was anything to
    fingerprint. 44 of the 45 dated rows in this tree are older than their own
    listing, and counting them as omissions makes the column read as a backlog
    that could be worked off - it cannot, and the only way to clear it would be
    to attach a number nobody measured. Derived from git rather than written
    down per trap, so a new suite gets the right boundary without anyone
    remembering to set one.
    """
    rel = module.listing_for(trap).relative_to(module.ROOT).as_posix()
    added = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%ad", "--date=short",
         "--follow", "--", rel],
        capture_output=True, text=True, cwd=module.ROOT).stdout.split()
    return added[-1] if added else None


def surface_drift(module, trap: str, stamp: str, short: int) -> dict:
    """Which listed files moved between the commit `stamp` names and HEAD.

    Stale is one word for two situations that call for opposite actions: the
    rules a result was produced under really did change, or a comment moved and
    the fingerprint - a hash of whole file bytes - moved with it. Both print the
    same way, so a reader with a mostly-stale board has no way to tell which
    rows are worth re-running and stops reading the column.

    A stamp names content, not a commit, so the commit has to be found: walk the
    commits that touched this surface and recompute the fingerprint at each. The
    listings here are short (9 to 51 paths) and so is their history (9 to 38
    commits), which is why a search is affordable at all. Unresolved is a real
    answer, not a failure: a stamp produced on a branch that was rebased, or
    before a listed file existed, has no commit on this branch that reproduces
    it.
    """
    listing = module.listing_for(trap).relative_to(module.ROOT).as_posix()
    paths = module.surface_paths(trap)
    log = subprocess.run(
        ["git", "log", "--format=%H", "--", listing, *paths],
        capture_output=True, text=True, cwd=module.ROOT)
    for commit in log.stdout.split():
        try:
            if module.fingerprint(trap, at=commit)[0][:short] != stamp:
                continue
        except module.SurfaceIncomplete:
            continue
        changed = subprocess.run(
            ["git", "diff", "--name-only", commit, "HEAD", "--", *paths],
            capture_output=True, text=True, cwd=module.ROOT)
        return {"commit": commit[:12],
                "changed": sorted(changed.stdout.split()),
                "surface_size": len(paths)}
    return {"commit": None, "changed": [], "surface_size": len(paths)}


def local_version(tool: str) -> str | None:
    """The version this machine reports for `tool`, or None if it cannot say.

    Cached per process: the same binary is named on many lines, and asking it
    once per line would make the report slower than the work it audits.
    """
    if tool in local_version.cache:  # type: ignore[attr-defined]
        return local_version.cache[tool]  # type: ignore[attr-defined]
    answer = None
    try:
        finished = subprocess.run(
            PROBES[tool], capture_output=True, text=True, timeout=15)
        found = VERSION_TOKEN.search(finished.stdout or finished.stderr)
        answer = found.group(1) if found else None
    except (OSError, subprocess.SubprocessError):
        # Not installed, not executable, or too slow to answer. All three mean
        # the same thing here: this machine cannot confirm or deny the claim.
        answer = None
    local_version.cache[tool] = answer  # type: ignore[attr-defined]
    return answer


local_version.cache = {}  # type: ignore[attr-defined]


def attribution_patterns() -> list[tuple[re.Pattern[str], str]]:
    """One compiled `<tool><version>` matcher per prose spelling."""
    spellings = list(ALIASES.items()) + [(name, name) for name in PROBES]
    # Longest spelling first so `headroom-ai 0.34.0` is read as the package and
    # not as `headroom` followed by something starting with a hyphen.
    spellings.sort(key=lambda pair: len(pair[0]), reverse=True)
    # And a left boundary, because longest-first only settles spellings this
    # scanner knows. `pilotfish-codex 1.7.1` is a different project's release and
    # was read as a claim about the Codex CLI, producing three differs against
    # the local 0.149.0 the moment that upstream entered the research notes
    # (2026-08-21). A tool name preceded by a word character or a hyphen is part
    # of a longer name, not the name.
    return [(re.compile(r"(?<![\w-])" + re.escape(spelling) + ATTRIBUTION,
                        re.IGNORECASE), canonical)
            for spelling, canonical in spellings]


def same_version(claimed: str, here: str) -> bool:
    """Whether a claim is satisfied by the local version.

    Prose truncates: `headroom 0.34` and `rtk 0.45+` both mean the release the
    machine reports as `0.34.0` / `0.45.0`. Treat the claim as a prefix, so a
    shorter claim matches, while `0.33` against `0.34.0` still differs.
    """
    return here == claimed or here.startswith(claimed + ".")


def as_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def attributions_in(line: str) -> list[tuple[str, str]]:
    """(tool, claimed version) pairs a single line explicitly attributes."""
    found: set[tuple[str, str]] = set()
    for pattern, tool in attribution_patterns():
        for match in pattern.finditer(line):
            found.add((tool, match.group(1)))
    return sorted(found)


def verdict_for(claimed: str, here: str | None, is_floor: bool) -> str:
    """How a claimed version stands against what the machine reports."""
    if here is None:
        return "unprobeable"
    # Floors first. A floor the machine meets exactly used to report `match`,
    # which read as "a local attestation was verified" - and after 2026-08-21
    # there is no such category left, so the label would be the only one of its
    # kind and would mean something it does not.
    if is_floor:
        return "floor-met" if as_tuple(here) >= as_tuple(claimed) else "floor-unmet"
    if same_version(claimed, here):
        return "match"
    return "differs"


def audit_attestations(today: date) -> list[dict[str, object]]:
    """Every line claiming a dated check, with its age in days."""
    rows = []
    for path in tracked_markdown():
        relative = path.relative_to(ROOT).as_posix()
        for number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1):
            if not VERIFICATION_VERB.search(line):
                continue
            stamps = ISO_DATE.findall(line)
            if not stamps:
                continue
            # The newest date on the line is the claim's own date; an older one
            # beside it is usually the thing being described.
            newest = max(stamps)
            try:
                age = (today - date.fromisoformat(newest)).days
            except ValueError:  # pragma: no cover - regex already shaped it
                continue
            rows.append({"site": f"{relative}:{number}", "date": newest,
                         "age_days": age, "line": line.strip()[:120]})
    return sorted(rows, key=lambda row: row["date"])


def audit_versions() -> list[dict[str, object]]:
    """Versions attributed to a probeable tool, against what it reports here."""
    rows = []
    for path in tracked_markdown():
        relative = path.relative_to(ROOT).as_posix()
        for number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1):
            if HISTORY.search(line) or NOT_A_LIVE_CLAIM.search(line):
                continue
            for tool, claimed in attributions_in(line):
                is_floor = bool(FLOOR.search(line))
                # A floor is portable and belongs to every machine; an exact
                # version only means something here if the line says it is
                # about here. Anything else states what upstream publishes,
                # and comparing that to a local binary is a category error
                # that happens to pass on whichever machine wrote it.
                if not is_floor:
                    rows.append({"site": f"{relative}:{number}", "tool": tool,
                                 "claimed": claimed, "local": None,
                                 "verdict": "not-local"})
                    continue
                here = local_version(tool)
                rows.append({"site": f"{relative}:{number}", "tool": tool,
                             "claimed": claimed, "local": here,
                             "verdict": verdict_for(claimed, here, is_floor)})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="machine-readable")
    parser.add_argument("--drift", action="store_true",
                        help="for each stale stamp, name the surface files that "
                             "moved since (walks history; seconds, not instant)")
    parser.add_argument("--attestation-age", type=int, default=30,
                        metavar="DAYS",
                        help="list dated claims at least this old (default 30)")
    args = parser.parse_args()

    citations = audit_citations()
    traps = audit_traps(args.drift)
    attestations = audit_attestations(date.today())
    versions = audit_versions()

    if args.json:
        print(json.dumps({"citations": citations, "traps": traps,
                          "attestations": attestations, "versions": versions},
                         indent=2))
        return 0

    total = sum(len(bucket) for bucket in citations.values())
    print(f"citations: {total} distinct, "
          f"{len(citations['resolves'])} resolve, "
          f"{len(citations['foreign'])} foreign (linked or names its repo), "
          f"{len(citations['fingerprint'])} content fingerprints, "
          f"{len(citations['unresolved'])} unresolved")
    if citations["unresolved"]:
        print("  (not a defect list: a historical `[surface …]` stamp or a "
              "contract hash lands here by design)")
    for record in citations["unresolved"]:
        print(f"  unresolved  {record['sha']}")
        for site in record["sites"]:
            print(f"              {site}")

    print()
    print("trap evidence:")
    for row in traps:
        if row.get("missing"):
            print(f"  {row['trap']:<22} surface unreadable: lists "
                  f"{row['missing']}, which is gone; fix the surface before "
                  "trusting any fingerprint")
            continue
        print(f"  {row['trap']:<22} surface {row['current']}  "
              f"dated-rows {row['result_rows']:>3}  "
              f"stamps {row['stamped']:>2}  "
              f"current {row['current_stamps']:>2}  "
              f"stale {row['stale_stamps']:>2}  "
              f"unstamped {row['unstamped_rows']:>3}")
        if row.get("groups"):
            # The follow-up a stale stamp raises. Printed only where a listing
            # declares groups, so the line appears where it says something.
            parts = "  ".join(f"{name} {digest}"
                              for name, digest in sorted(row["groups"].items()))
            print(f"      groups: {parts}")
        if row.get("predating_rows"):
            # Stated beside the counts, not inside them: `stamped` counts every
            # stamp in the file and `unstamped_rows` subtracts it from the dated
            # rows, so a stamp written outside a row already makes those two
            # disagree. Nesting a third number under one of them would present
            # that looseness as arithmetic.
            print(f"      {row['predating_rows']} dated row(s) predate this "
                  f"trap's listing (added {row['convention_began']}), so they "
                  "could not have been stamped")
        for entry in row.get("drift", []):
            if entry["commit"] is None:
                print(f"      {entry['stamp']}  no commit on this branch "
                      "reproduces it (rebased, or predates a listed file)")
                continue
            moved, listed = len(entry["changed"]), entry["surface_size"]
            print(f"      {entry['stamp']} = {entry['commit']}, "
                  f"{moved} of {listed} surface file(s) moved since:")
            for path in entry["changed"][:DRIFT_LIST]:
                print(f"        {path}")
            if moved > DRIFT_LIST:
                print(f"        ... and {moved - DRIFT_LIST} more")
            if moved * 2 > listed:
                print("        (most of the surface moved: read this as "
                      "\"re-run\", not as a diff to judge)")

    print()
    aged = [row for row in attestations if row["age_days"] >= args.attestation_age]
    print(f"prose attestations: {len(attestations)} dated claims, "
          f"{len(aged)} at least {args.attestation_age} days old")
    for row in aged:
        print(f"  {row['date']}  {row['age_days']:>4}d  {row['site']}")

    print()
    tally = {verdict: sum(1 for row in versions if row["verdict"] == verdict)
             for verdict in ("match", "differs", "floor-met", "floor-unmet",
                             "unprobeable", "not-local")}
    print(f"version attestations: {len(versions)} attributed, "
          f"{tally['match']} match, {tally['differs']} differ, "
          f"{tally['floor-met']} floors met, {tally['floor-unmet']} unmet, "
          f"{tally['unprobeable']} unprobeable, "
          f"{tally['not-local']} about upstream rather than this machine")
    for row in versions:
        if row["verdict"] not in ("differs", "floor-unmet"):
            continue
        print(f"  {row['verdict']:<11}{row['tool']}: doc says "
              f"{row['claimed']}, here {row['local']}")
        print(f"             {row['site']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
