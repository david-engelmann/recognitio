#!/usr/bin/env python3
"""Pin the Build 16 ZCode plugin build contract.

The brief at docs/zcode-plugin-brief.md records the ZCode
native plugin with its manifest at .zcode-plugin/plugin.json,
the in client plugin marketplace distribution with the
version bump rule, the portable v1 shape losing output
styles and settings on ZCode, the register but not execute
behavior for channels, lspServers, outputStyles, and
settings, the 1024 character description cap and the 100KB
body truncation, and the trust posture standing unchanged,
per the primary ZCode plugin documentation read in the
round 15 research sweep. Decision 4 binds this build like
every other build. The brief documents the contract and
never enforces it on a live ZCode client, so this script
pins the contract without a ZCode host. It requires the
brief to keep the stated pins with a derivation note on
every rule, the manifest at the native path with its name,
description, and version, the description under the cap,
the manifest version matching the repo version, and the
decision record with its decision 4 statement, so the
scoped guidance cannot become a rival instruction source
and a later edit cannot soften or drop a stated claim in
silence.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / "docs" / "zcode-plugin-brief.md"
MANIFEST = ROOT / ".zcode-plugin" / "plugin.json"
HOME_MANIFEST = ROOT / ".claude-plugin" / "plugin.json"
SKILL = ROOT / ".agents" / "skills" / "recognitio" / "SKILL.md"
DECISIONS = ROOT / "docs" / "decisions.md"

RULES_HEADING = "## The ZCode rules"

DESCRIPTION_LIMIT = 1024
BODY_LIMIT = 100 * 1024

# Canonical skill sections a derivation note may name. These are
# the section titles of .agents/skills/recognitio/SKILL.md, and a
# note that names one says which canonical section the rule
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

# Brief sentences the gate pins. Each is a fragment of the exact
# sentence the brief carries, so a later edit that softens or
# drops a stated pin, rule, or limit fails loudly.
PINNED = (
    ("the native manifest path",
     "with its manifest at `.zcode-plugin/plugin.json`"),
    ("the marketplace distribution",
     "through its in client plugin marketplace"),
    ("the version bump rule",
     "carries no version bump"),
    ("the no update without a bump",
     "offers no update for an installed plugin"),
    ("the portable shape losses",
     "loses output styles and settings on ZCode"),
    ("the register but not execute behavior",
     "register but do not execute on ZCode"),
    ("the four registered fields",
     "Channels, lspServers, outputStyles, and settings"),
    ("the description cap",
     "runs at most 1024 characters"),
    ("the body truncation",
     "truncated at 100KB"),
    ("the trust posture",
     "stand unchanged on ZCode"),
    ("the decision 4 statement",
     "Decision 4 binds this build like every other build"),
)

DECISION_HEADING = "## 27. Build 16"
DECISION_STATEMENT = "Decision 4 binds"


def read_text(path):
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def deliberate_source(note):
    """Whether the derivation note names a source on purpose.

    A canonical section title counts only when named right
    after the "canonical skill" attribution marker, and the
    primary ZCode documentation counts when named as the
    round 15 research read.
    """
    for title in CANONICAL_SECTIONS:
        if re.search(
            r"canonical skill[^.;]{0,200}" + re.escape(title), note
        ):
            return True
    return "primary ZCode plugin documentation" in note


def rules_section(raw):
    """The text of the rules section, or None when missing."""
    start = raw.find(RULES_HEADING)
    if start < 0:
        return None
    rest = raw[start + len(RULES_HEADING):]
    match = re.search(r"(?m)^## ", rest)
    if match:
        rest = rest[:match.start()]
    return rest


def rule_blocks(section):
    """The rule blocks in order, split on Z numbered headings."""
    parts = re.split(r"(?m)^### (Z\d+)\.", section)
    blocks = []
    for i in range(1, len(parts), 2):
        blocks.append((parts[i], parts[i + 1]))
    return blocks


def brief_problems(root=None):
    """Problems with the Build 16 brief's stated contract."""
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "zcode-plugin-brief.md")
    if raw is None:
        return ["docs/zcode-plugin-brief.md is missing"]
    text = re.sub(r"\s+", " ", raw)
    problems = []
    for label, fragment in PINNED:
        if fragment not in text:
            problems.append(
                "docs/zcode-plugin-brief.md does not state %s"
                % label
            )
    return problems


def rules_problems(root=None):
    """Problems with the brief's derivation noted rules."""
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "zcode-plugin-brief.md")
    if raw is None:
        return ["docs/zcode-plugin-brief.md is missing"]
    problems = []
    section = rules_section(raw)
    if section is None:
        problems.append(
            "docs/zcode-plugin-brief.md carries no %r section"
            % RULES_HEADING
        )
        return problems
    blocks = rule_blocks(section)
    if not blocks:
        problems.append(
            "docs/zcode-plugin-brief.md carries no Z numbered rules"
        )
    for name, block in blocks:
        flat = re.sub(r"\s+", " ", block)
        if "Derives from" not in flat:
            problems.append(
                "zcode rule %s carries no derivation note, so it "
                "would be a rival instruction source" % name
            )
            continue
        note = flat.split("Derives from", 1)[1]
        if not deliberate_source(note):
            problems.append(
                "zcode rule %s names no canonical skill section "
                "or primary ZCode documentation in its "
                "derivation note" % name
            )
    return problems


def manifest_problems(root=None):
    """Problems with the native ZCode manifest."""
    root = ROOT if root is None else root
    raw = read_text(root / ".zcode-plugin" / "plugin.json")
    if raw is None:
        return ["missing manifest at .zcode-plugin/plugin.json"]
    problems = []
    try:
        data = json.loads(raw)
    except ValueError as exc:
        return [".zcode-plugin/plugin.json does not parse: %s" % exc]
    for field in ("name", "description", "version"):
        if field not in data:
            problems.append(
                ".zcode-plugin/plugin.json carries no %s field"
                % field
            )
    if "description" in data:
        if len(data["description"]) > DESCRIPTION_LIMIT:
            problems.append(
                ".zcode-plugin/plugin.json description runs %d "
                "characters, over the %d limit"
                % (len(data["description"]), DESCRIPTION_LIMIT)
            )
    if "version" in data:
        home_raw = read_text(root / ".claude-plugin" / "plugin.json")
        if home_raw is not None:
            try:
                home = json.loads(home_raw)
            except ValueError:
                home = {}
            if home.get("version") != data["version"]:
                problems.append(
                    ".zcode-plugin/plugin.json version %s does "
                    "not match the repo version %s"
                    % (data["version"], home.get("version"))
                )
    return problems


def body_problems(root=None):
    """Problems with the shipped skill body against the cap."""
    root = ROOT if root is None else root
    raw = read_text(
        root / ".agents" / "skills" / "recognitio" / "SKILL.md"
    )
    if raw is None:
        return ["canonical skill is missing"]
    if len(raw.encode("utf-8")) > BODY_LIMIT:
        return [
            "canonical skill body runs over the 100KB ZCode "
            "truncation limit"
        ]
    return []


def decision_problems(root=None):
    """Problems with the Build 16 decision record."""
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "decisions.md")
    if raw is None:
        return ["docs/decisions.md is missing"]
    start = raw.find(DECISION_HEADING)
    if start < 0:
        return [
            "docs/decisions.md carries no Build 16 decision record"
        ]
    rest = raw[start + len(DECISION_HEADING):]
    match = re.search(r"(?m)^## ", rest)
    record = rest[:match.start()] if match else rest
    if DECISION_STATEMENT not in record:
        return [
            "the Build 16 decision record carries no decision 4 "
            "statement, which every landed build must record"
        ]
    return []


def zcode_problems(root=None):
    """Every Build 16 ZCode plugin build problem."""
    problems = []
    problems.extend(brief_problems(root))
    problems.extend(rules_problems(root))
    problems.extend(manifest_problems(root))
    problems.extend(body_problems(root))
    problems.extend(decision_problems(root))
    return problems


def main(root=None):
    problems = zcode_problems(root)
    if problems:
        for problem in problems:
            print("check_zcode: %s" % problem, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
