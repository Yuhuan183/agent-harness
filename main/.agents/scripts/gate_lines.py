"""Canonical machine-check regexes for the leaf gate lines.

Single source shared by the production QC auditor (qc-gate-lines) and the
behavioral trap graders (evals/traps/*/grade.py). The authoritative template
text lives in the writer role contracts; change the shape there first, then
here, then re-run the trap grader self-tests.

Match against whitespace-collapsed text (re.sub(r"\\s+", " ", report)) —
reports wrap lines. INTENT captures the spec segment so graders can check
what the report claims the spec says.
"""

from __future__ import annotations

import re

# The spec-segment capture must not stop inside a decimal ("2.68"): a period
# only terminates the segment when followed by whitespace or end-of-text.
# Like the dash variants below, a short parenthetical naming the spec source
# ("the spec (README) says") is content-preserving and accepted.
INTENT = re.compile(
    r"INTENT: code does .+?; .+? expects? .+?; "
    r".*?spec(?:\s*\([^)]{1,40}\))? says (.+?)(?:\.(?=\s|$)|$)"
)
# The contract template uses an ASCII hyphen, but em/en dashes appear in the
# wild and carry the same content; accept all three. The count slot takes a
# decimal or the content-equivalent "none" (= 0); any other prose there is an
# off-template line, not a variant.
TWINS = re.compile(r"TWINS: searched .+? [-–—] found (?:\d+|none) other sites?")
# A found-0/none claim is the one TWINS shape whose truth QC must re-check by
# grep: 4/10 sampled leaves under-reported a real twin (evals/traps/s9).
TWINS_NONE = re.compile(r"TWINS: searched .+? [-–—] found (?:0|none) other sites?")
AUTH = re.compile(r'AUTH: user said "[^"]+"')
AUTH_CLAIM = re.compile(r'AUTH: user said "')

TEMPLATES = {"INTENT": INTENT, "TWINS": TWINS, "AUTH": AUTH}

# A gate line is owed at column one as plain text. Matching the pattern
# anywhere in the flattened report accepted `**INTENT: ...**`, a bulleted
# `- AUTH: ...`, a blockquoted line, and a mention buried mid-paragraph — so
# the recorded "format ✓" was looser than the contract the roles are given.
GATE_START = re.compile(r"(?m)^(INTENT|TWINS|AUTH): ")
# Same prefix reached any other way. Reported separately: a leaf that bolded
# its line needs to hear "off-template", not "missing".
GATE_ANYWHERE = re.compile(r"(INTENT|TWINS|AUTH): ")


def flatten(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def blocks(text: str) -> list[tuple[str, str]]:
    """Return (name, flattened block) for each gate line starting at column one.

    Reports wrap, so a gate line may span physical lines; a block runs until a
    blank line, the next gate prefix, or the end of the report.
    """
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if GATE_START.match(line)]
    found = []
    for position, index in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        body = []
        for line in lines[index:end]:
            if body and not line.strip():
                break
            body.append(line)
        found.append((GATE_START.match(lines[index]).group(1), flatten(" ".join(body))))
    return found


def find(name: str, text: str):
    """Anchored match for one owed gate line, or None if it is not on template."""
    for found_name, block in blocks(text):
        if found_name != name:
            continue
        match = TEMPLATES[name].match(block)
        if match:
            return match
    return None


def off_template(name: str, text: str) -> bool:
    """True when the prefix appears only somewhere it does not count."""
    if find(name, text):
        return False
    return any(match.group(1) == name for match in GATE_ANYWHERE.finditer(text))


# A spec segment naming only a value ("2.68") rather than the rule it came
# from. Observed on s7o4 and s7o5: present, well-formed, and useless, because
# the slot exists to carry what the spec says.
_VALUE_ONLY = re.compile(r"^[\s\"'`]*[-+]?[\d.,%]+[\s\"'`]*$")
_CJK = re.compile(r"[一-鿿぀-ヿ]")

# Ordinal weights, not calibrated quantities. They exist so the observed
# failure shapes land on distinct readings, and the ordering is the only
# claim: an absent line is worse than a present wrong one, a line that never
# reached column one is worse than one that did but missed the template, and a
# thin spec slot is the mildest of the four.
_PENALTY = {
    "not_at_column_one": 0.45,
    "off_template": 0.30,
    "non_english_template": 0.35,
    "value_only_spec": 0.20,
}


def distance(name: str, text: str) -> dict:
    """How far a report's gate line sits from the template: a score in [0, 1].

    The two functions above answer "does it count", which is what production QC
    gates on and what they must keep answering alone. This answers "how far
    off", which a pass/fail verdict cannot: a binary measure can demonstrate a
    large effect and can never put a floor under what remains. That asymmetry,
    and the three upstreams it applies to, are in
    docs/research/cross-upstream-synthesis.md under round three.

    1.0 is on template, 0.0 is nothing present at all, and every deduction
    names itself so a score stays actionable.

    An instrument, never a gate, and deliberately not wired into qc-gate-lines:
    no threshold on this scale has been justified by anything, and a gate in
    this repo needs a condition rather than a number.
    """
    defects: list[str] = []
    if not any(m.group(1) == name for m in GATE_ANYWHERE.finditer(text)):
        return {"score": 0.0, "defects": ["absent"]}

    own_blocks = [block for found, block in blocks(text) if found == name]
    match = find(name, text)
    if match is None:
        # Present but not counting. Which of the two it is matters: a bolded
        # line needs to hear "off-template", not "missing".
        defects.append("off_template" if own_blocks else "not_at_column_one")
    if own_blocks and _CJK.search(" ".join(own_blocks)):
        defects.append("non_english_template")
    if match is not None and name == "INTENT":
        if _VALUE_ONLY.match((match.group(1) or "").strip()):
            defects.append("value_only_spec")

    score = 1.0
    for defect in defects:
        score -= _PENALTY.get(defect, 0.0)
    return {"score": round(max(score, 0.0), 4), "defects": defects}
