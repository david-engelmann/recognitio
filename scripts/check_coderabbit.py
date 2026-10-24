#!/usr/bin/env python3
"""Pin the Build 11 CodeRabbit guidelines contract.

The brief at docs/coderabbit-review-brief.md records the
CodeRabbit rename direction, the focus toggle table as a
constraint, the Quiet Chill and Assertive profiles, the pre
merge checks with Error mode merge blocking, the October 2026
entries, and the guideline file provenance now shown in review
summaries, all from the primary CodeRabbit docs. Decision 4
binds this build like every other build. The guidelines advise
and never enforce, so this script pins the contract without a
CodeRabbit host. It requires the brief to keep the stated pins,
the focus constraint that high trims verbosity and never reads
as deeper review, the named focus and profile axes, the summary
fold at high, the rename direction, the guideline provenance,
and the fourth .claude/rules/ guideline source, and every
guideline to carry a checkable derivation note, so the scoped
guidance cannot become a rival instruction source. A later edit
that drops any of them fails the gate instead of drifting in
silence.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / "docs" / "coderabbit-review-brief.md"
DECISIONS = ROOT / "docs" / "decisions.md"

GUIDELINES_HEADING = "## The guidelines"

# Canonical skill sections a derivation note may name. These are
# the section titles of .agents/skills/recognitio/SKILL.md, and a
# note that names one says which canonical section the guideline
# restates.
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

# Primary CodeRabbit citations a derivation note may name,
# written as URL stems so the note pins the surface the claim
# was read from.
PRIMARY_CITATIONS = (
    "docs.coderabbit.ai/changelog",
    "docs.coderabbit.ai/configuration",
    "docs.coderabbit.ai",
)

# Brief sentences the gate pins. Each is a fragment of the exact
# sentence the brief carries, so a later edit that softens or
# drops a stated pin, quote, or limit fails loudly.
PINNED = (
    ("the rename direction, Fix comments was Autofix",
     "Fix comments (formerly Autofix) fixes the review comments "
     "you select"),
    ("the rename direction, Autofix was Autopilot",
     "Autofix (formerly Autopilot) brings a pull request to "
     "completion"),
    ("the compat aliases",
     "keep working as aliases for a limited time for backward "
     "compatibility"),
    ("the focus constraint, high trims",
     "High trims verbosity"),
    ("the focus constraint, no deeper analysis",
     "It does not deepen analysis"),
    ("the never deeper reading",
     "must never treat it as deeper review"),
    ("the high table row",
     "reviews down to essential content only"),
    ("the cumulative table",
     "Higher levels are cumulative"),
    ("the leanest reviews caption",
     "Strip everything non-essential for the leanest reviews"),
    ("the summary fold at high",
     "moves from off to on at high"),
    ("the fold is not analysis",
     "folds the summary into the walkthrough"),
    ("the focus axis named",
     "On the focus axis"),
    ("the profile axis named",
     "On the profile axis"),
    ("the focus levels",
     "casual, balanced, or high"),
    ("the profile values",
     "quiet, chill, and assertive"),
    ("the Quiet launch",
     "July 2 2026"),
    ("the Quiet inline behavior",
     "only the most important comments posted inline"),
    ("the profile reference",
     "`quiet` for only the most important feedback"),
    ("the Error mode merge blocking",
     "requires resolution before merging"),
    ("the block until the check passes",
     "can block the PR until the check passes"),
    ("the Automatic Approvals surface",
     "the Automatic Approvals surface"),
    ("the approval risk limits",
     "Optional risk limits keep pull requests above a chosen "
     "Merge Risk for human approval"),
    ("the Deep Scan linked repositories",
     "Deep Scan with linked repositories"),
    ("the Deep Scan API on all plans",
     "code findings API on all plans"),
    ("the author approval key",
     "prevent pull request authors from using `@coderabbitai "
     "approve`"),
    ("the guideline provenance",
     "configured, auto-discovered, or an Agent Skill"),
    ("the fourth guideline source",
     "adds `.claude/rules/` as a fourth guideline source"),
    ("the paths scoping",
     "globs in `paths` are relative to the project root"),
    ("the pairing not a packet",
     "a review pairing source, never a second packet"),
    ("the no calendar negative",
     "the brief claims none"),
    ("the decision 4 statement",
     "Decision 4 binds this build like every other build"),
)

DECISION_HEADING = "## 20. Build 11"
DECISION_STATEMENT = "Decision 4 binds"


def read_text(path):
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


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


def guidelines_section(raw):
    """The text of the guidelines section, or None when missing."""
    start = raw.find(GUIDELINES_HEADING)
    if start < 0:
        return None
    rest = raw[start + len(GUIDELINES_HEADING):]
    match = re.search(r"(?m)^## ", rest)
    if match:
        rest = rest[:match.start()]
    return rest


def guideline_blocks(section):
    """The guideline blocks in order, split on G numbered headings."""
    parts = re.split(r"(?m)^### G\d+\.", section)
    return [part for part in parts[1:]]


def brief_problems(root=None):
    """Problems with the Build 11 brief's stated contract."""
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "coderabbit-review-brief.md")
    if raw is None:
        return ["docs/coderabbit-review-brief.md is missing"]
    text = re.sub(r"\s+", " ", raw)
    problems = []
    for label, fragment in PINNED:
        if fragment not in text:
            problems.append(
                "docs/coderabbit-review-brief.md does not state %s"
                % label
            )
    return problems


def guidelines_problems(root=None):
    """Problems with the brief's derivation noted guidelines."""
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "coderabbit-review-brief.md")
    if raw is None:
        return ["docs/coderabbit-review-brief.md is missing"]
    problems = []
    section = guidelines_section(raw)
    if section is None:
        problems.append(
            "docs/coderabbit-review-brief.md carries no %r section"
            % GUIDELINES_HEADING
        )
        return problems
    blocks = guideline_blocks(section)
    if not blocks:
        problems.append(
            "docs/coderabbit-review-brief.md carries no G numbered "
            "guidelines"
        )
    for index, block in enumerate(blocks, start=1):
        flat = re.sub(r"\s+", " ", block)
        if "Derives from" not in flat:
            problems.append(
                "coderabbit guideline G%d carries no derivation "
                "note, so it would be a rival instruction source"
                % index
            )
            continue
        note = flat.split("Derives from", 1)[1]
        if not deliberate_source(note):
            problems.append(
                "coderabbit guideline G%d names no canonical skill "
                "section, primary CodeRabbit citation, or binding "
                "decision in its derivation note" % index
            )
    return problems


def decision_problems(root=None):
    """Problems with the Build 11 decision record."""
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "decisions.md")
    if raw is None:
        return ["docs/decisions.md is missing"]
    start = raw.find(DECISION_HEADING)
    if start < 0:
        return [
            "docs/decisions.md carries no Build 11 decision record"
        ]
    rest = raw[start + len(DECISION_HEADING):]
    match = re.search(r"(?m)^## ", rest)
    record = rest[:match.start()] if match else rest
    if DECISION_STATEMENT not in record:
        return [
            "the Build 11 decision record carries no decision 4 "
            "statement, which every landed build must record"
        ]
    return []


def coderabbit_problems(root=None):
    """Every Build 11 CodeRabbit guidelines problem."""
    problems = []
    problems.extend(brief_problems(root))
    problems.extend(guidelines_problems(root))
    problems.extend(decision_problems(root))
    return problems


def main(root=None):
    problems = coderabbit_problems(root)
    if problems:
        for problem in problems:
            print("check_coderabbit: %s" % problem, file=sys.stderr)
        return 1
    print(
        "check_coderabbit: the Build 11 CodeRabbit guidelines "
        "contract holds"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
