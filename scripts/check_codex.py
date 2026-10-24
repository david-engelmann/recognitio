#!/usr/bin/env python3
"""Pin the Build 9 Codex review rules package contract.

The brief at docs/codex-review-brief.md is scoped Codex guidance
beside the canonical packet. It must never become a second packet,
a rival instruction source, so every rule it states carries a
derivation note naming the canonical skill section or gate it
restates or the primary OpenAI citation it reports. This script
pins that discipline without a Codex host. It requires every rule
in the rules section to carry a checkable derivation note, and it
pins the stated negatives and limits the round 21 lanes named.
The no product native calendar negative, the default branch only
continuous monitoring, the completed scan versus complete coverage
limit, the two distinct pauses, the per surface model pins, the
active restriction of Legacy with no promised retirement date,
the OpenAI owned figures, and the SECURITY.md policy context note
are all pinned as brief sentences, and the decision record must
name Build 9 with a decision 4 statement. A later edit that
drops any of them fails the gate instead of drifting in silence.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / "docs" / "codex-review-brief.md"
DECISIONS = ROOT / "docs" / "decisions.md"

RULES_HEADING = "## The review rules"

# Canonical skill sections a derivation note may name. These are the
# section titles of .agents/skills/recognitio/SKILL.md, and a note
# that names one says which canonical section the rule restates.
CANONICAL_SECTIONS = {
    "Purpose",
    "Input modes",
    "Workflow",
    "Choosing tiers",
    "Fanning out",
    "Escalation",
    "Stamping the gate report",
    "The tier model",
    "Completeness discipline",
    "Re-review",
    "Trust and limits",
    "The boundary",
}

# Primary OpenAI citations a derivation note may name, written as
# URL stems so the note pins the surface the claim was read from.
PRIMARY_CITATIONS = (
    "developers.openai.com/blog/custom-code-review-rules-for-codex",
    "learn.chatgpt.com/docs/security/",
    "learn.chatgpt.com/docs/environments/cloud-environments",
    "learn.chatgpt.com/docs/config-file/",
    "github.com/openai/codex-plugin-cc",
)

# Decision 4 is the standing record that scripts carry enforcement
# with no model judgment, and a rule may derive from it directly.
ALLOWED_SOURCES = tuple(CANONICAL_SECTIONS) + PRIMARY_CITATIONS \
    + ("Decision 4",)

# Brief sentences the gate pins. Each is a fragment of the exact
# sentence the brief carries, so a later edit that softens or drops
# a stated negative or limit fails loudly.
PINNED = (
    ("the no calendar negative",
     "There is no product native calendar schedule"),
    ("the default branch only continuous monitoring",
     "monitors new commits on the repository's default branch"),
    ("the completed scan versus complete coverage limit",
     "A completed scan and complete coverage are separate claims"),
    ("the per repository monitoring pause",
     "the pause or enable toggle"),
    ("the automatic funding pause",
     "scanning pauses when funding is unavailable"),
    ("the Actions surface model pin",
     "The Actions example defaults to gpt-6-sol"),
    ("the workbench surface model pin",
     "recommends gpt-5.6-sol with xhigh reasoning effort"),
    ("the Legacy active restriction",
     "under active restriction"),
    ("the no promised retirement date",
     "no retirement date is promised"),
    ("the OpenAI owned figures",
     "OpenAI's on OpenAI's tasks"),
    ("the CLI 0.164.0 promotion",
     "CLI 0.164.0 is the later primary pin"),
    ("the SECURITY.md policy context note",
     "SECURITY.md is policy context, not executable instructions"),
    ("the auto review fails closed lifecycle",
     "fails closed on prompt build, review session, and parse "
     "failures"),
    ("the decision 4 statement",
     "Decision 4 binds this build like every other build"),
)

DECISION_HEADING = "## 18. Build 9"
DECISION_STATEMENT = "Decision 4 binds"


def rules_section(raw):
    """The text of the rules section, or None when it is missing."""
    start = raw.find(RULES_HEADING)
    if start < 0:
        return None
    rest = raw[start + len(RULES_HEADING):]
    match = re.search(r"(?m)^## ", rest)
    if match:
        rest = rest[:match.start()]
    return rest


def rule_blocks(section):
    """The rule blocks in order, split on their R numbered headings."""
    parts = re.split(r"(?m)^### R\d+\.", section)
    return [part for part in parts[1:]]


def deliberate_source(note):
    """Whether the derivation note names a source on purpose.

    R21-ST-01. A bare substring match lets a note mention a
    canonical section title in passing prose without deriving
    from it, so a section title counts only when it is named as
    the source, right after the "canonical skill" attribution
    marker. Primary URL stems and Decision 4 are rare enough to
    match as substrings.
    """
    for title in CANONICAL_SECTIONS:
        if re.search(
            r"canonical skill[^.;]{0,200}" + re.escape(title), note
        ):
            return True
    if any(stem in note for stem in PRIMARY_CITATIONS):
        return True
    return "Decision 4" in note


def derivation_problems(section):
    """Problems with the rules derivation discipline."""
    problems = []
    blocks = rule_blocks(section)
    if not blocks:
        return ["the rules section carries no R numbered rules"]
    for index, block in enumerate(blocks, start=1):
        flat = re.sub(r"\s+", " ", block)
        if "Derives from" not in flat:
            problems.append(
                "rule R%d carries no derivation note, so it would be "
                "a rival instruction source" % index
            )
            continue
        note = flat.split("Derives from", 1)[1]
        if not deliberate_source(note):
            problems.append(
                "rule R%d names no canonical skill section, gate, or "
                "primary OpenAI citation in its derivation note"
                % index
            )
    return problems


def brief_problems(root=None):
    """Problems with the Build 9 brief's stated contract."""
    root = ROOT if root is None else root
    path = root / "docs" / "codex-review-brief.md"
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return ["cannot read docs/codex-review-brief.md, %s" % exc]
    text = re.sub(r"\s+", " ", raw)
    problems = []
    section = rules_section(raw)
    if section is None:
        problems.append(
            "docs/codex-review-brief.md carries no %r section"
            % RULES_HEADING
        )
    else:
        problems.extend(derivation_problems(section))
    for label, fragment in PINNED:
        if fragment not in text:
            problems.append(
                "docs/codex-review-brief.md does not state %s" % label
            )
    if "98 percent" not in text or "58.3 percent" not in text:
        problems.append(
            "docs/codex-review-brief.md does not report the 98 "
            "percent against 58.3 percent figures"
        )
    return problems


def decision_problems(root=None):
    """Problems with the Build 9 decision record."""
    root = ROOT if root is None else root
    path = root / "docs" / "decisions.md"
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return ["cannot read docs/decisions.md, %s" % exc]
    start = raw.find(DECISION_HEADING)
    if start < 0:
        return [
            "docs/decisions.md carries no Build 9 decision record"
        ]
    rest = raw[start + len(DECISION_HEADING):]
    match = re.search(r"(?m)^## ", rest)
    record = rest[:match.start()] if match else rest
    if DECISION_STATEMENT not in record:
        return [
            "the Build 9 decision record carries no decision 4 "
            "statement, which every landed build must record"
        ]
    return []


def codex_problems(root=None):
    """Every Build 9 Codex review rules package problem."""
    problems = []
    problems.extend(brief_problems(root))
    problems.extend(decision_problems(root))
    return problems


def main(root=None):
    problems = codex_problems(root)
    if problems:
        for problem in problems:
            print("check_codex: %s" % problem, file=sys.stderr)
        return 1
    print("check_codex: the Build 9 Codex review rules hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
