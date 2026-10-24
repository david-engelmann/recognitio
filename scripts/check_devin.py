#!/usr/bin/env python3
"""Pin the Build 17 Devin playbook and coordinator build contract.

The brief at docs/devin-playbook-brief.md records the Devin
Review host list with the Bitbucket Cloud conditions, the code
fixed only resolved count, the Quote in chat and merge past
bypass surfaces, the one off review of the latest commit, the
code scan automation API path with the service user permission
condition, the SARIF 2.1.0 export beside CSV, the repositories
and blueprint v3 promotion with the v3beta1 continuation note,
the auto scan schedules API general availability kept separate
from the session schedules deprecation, the coordinator
surfaces, Devin Oncall as an adjacent incident surface only,
Devin Dynamic Workflows as recorded script orchestration, the
targeted plugin saves and reinstall as a new revision, the
skill placement with both triggers enabled by default, the
stacked pull request packet rule, the AI Scan advisory limit,
the Copilot governance packet rule, and the Fusion chart
caveat, per the round 30 Devin delta. Decision 4 binds this
build like every other build. The brief documents the contract
and never enforces it on a live Devin host, so this script
pins the contract without a Devin client. It requires the
brief to keep the stated pins with a derivation note on
every rule, every Devin Dynamic Workflows mention qualified
with Devin, and the decision record with its decision 4
statement, so the scoped guidance cannot become a rival
instruction source and a later edit cannot soften or drop a
stated claim in silence.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / "docs" / "devin-playbook-brief.md"
SKILL = ROOT / ".agents" / "skills" / "recognitio" / "SKILL.md"
DECISIONS = ROOT / "docs" / "decisions.md"

RULES_HEADING = "## The Devin rules"

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

# Primary Devin citations a derivation note may name. A note
# that names one says which primary page the rule reports.
PRIMARY_CITATIONS = (
    "docs.devin.ai",
    "cognition.com/blog/local-fusion",
)

# Brief sentences the gate pins. Each is a fragment of the exact
# sentence the brief carries, so a later edit that softens or
# drops a stated pin, rule, or limit fails loudly.
PINNED = (
    ("the Bitbucket Cloud host",
     "now beside Bitbucket Cloud"),
    ("the automatic webhook install",
     "installs its webhooks automatically"),
    ("the personal account link",
     "links a personal Bitbucket Cloud account"),
    ("the code fixed only resolved count",
     "count a finding as resolved only when it was fixed in code"),
    ("the dismissed findings exclusion",
     "Findings dismissed by a reviewer and duplicates no longer count"),
    ("the Quote in chat surface",
     "carries a Quote in chat button"),
    ("the merge past bypass surface",
     "can merge a blocked pull request directly from Devin Review"),
    ("the one off review of the latest commit",
     "offers a one off review of the latest commit"),
    ("the no automatic enrollment",
     "without turning on automatic review"),
    ("the code scan automation API path",
     "can be created and updated through the API"),
    ("the service user permission condition",
     "the service user role needs the relevant scan permission"),
    ("the runtime validation evidence",
     "include recorded runtime validation results"),
    ("the SARIF 2.1.0 export",
     "export as SARIF 2.1.0"),
    ("the CSV beside SARIF",
     "in addition to CSV"),
    ("the v3 promotion",
     "are part of the stable v3 API"),
    ("the v3beta1 continuation",
     "the v3beta1 paths continuing to work"),
    ("the auto scan schedules general availability",
     "are generally available in the v3 org and enterprise APIs"),
    ("the schedules separation",
     "stays separate from the session schedules deprecation"),
    ("the session schedules deprecation date",
     "deprecation is dated September 10"),
    ("the devin_schedule deprecation",
     "devin_schedule Terraform resource deprecated in favor of "
     "devin_automation"),
    ("the converted schedule pointer",
     "points at the replacement automation"),
    ("the no end date published",
     "No end date for the migration phase is published"),
    ("the time sensitive flag stays set",
     "the time sensitive flag stays set"),
    ("the structured questions",
     "ask structured questions with clickable choices"),
    ("the shared Outpost runs",
     "run their sessions on a shared Outpost"),
    ("the plain language schedule display",
     "in plain language instead of raw RRULE text"),
    ("the Linear triggered child sessions",
     "from Linear automations or allowlisted Linear bots"),
    ("the Oncall adjacent surface",
     "as an adjacent incident surface only"),
    ("the Oncall Lite mode",
     "can run in Lite mode"),
    ("the Devin Dynamic Workflows recorded shape",
     "are a recorded, resumable script orchestration option"),
    ("the enterprise enablement secondary mark",
     "carried as secondary in this brief"),
    ("the targeted plugin saves",
     "into a specific uploaded plugin by naming it"),
    ("the reinstall as a new revision",
     "by reinstalling it, keeping the plugin version history"),
    ("the skill placement path",
     ".agents/skills/skill-name/SKILL.md"),
    ("the automatic discovery across repositories",
     "automatically discovered across connected repositories"),
    ("the both triggers enabled by default",
     "with user trigger and model trigger both enabled by default"),
    ("the Devin extension not portable core",
     "is a Devin extension, not a portable Agent Skills core item"),
    ("the human curation before procedure",
     "passes human curation before entering packet procedure"),
    ("the stacked layers verified separately",
     "Each stack layer and the integrated whole are verified separately"),
    ("the AI Scan never a merge gate",
     "An AI Scan pass is signal and never a merge gate"),
    ("the Copilot explicit choices",
     "Explicit Copilot feature choices are recorded"),
    ("the October 22 through October 26 window",
     "during the October 22 through October 26 rollout window"),
    ("the Fusion 68.1 figure",
     "scores 68.1 at 31 percent lower cost"),
    ("the higher Sonnet 5.5 figure",
     "with Sonnet 5.5 at 68.4"),
    ("the never a top score claim",
     "never stands as a top score claim"),
    ("the decision 4 statement",
     "Decision 4 binds this build like every other build"),
)

DECISION_HEADING = "## 28. Build 17"
DECISION_STATEMENT = "Decision 4 binds"


def read_text(path):
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def deliberate_source(note):
    """Whether the derivation note names a source on purpose.

    A canonical section title counts only when named right
    after the "canonical skill" attribution marker, and a
    primary Devin citation counts when named as a Devin page
    or the Cognition Fusion post.
    """
    for title in CANONICAL_SECTIONS:
        if re.search(
            r"canonical skill[^.;]{0,200}" + re.escape(title), note
        ):
            return True
    if any(stem in note for stem in PRIMARY_CITATIONS):
        return True
    return "Decision 4" in note


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
    """The rule blocks in order, split on R numbered headings."""
    parts = re.split(r"(?m)^### (R\d+)\.", section)
    blocks = []
    for i in range(1, len(parts), 2):
        blocks.append((parts[i], parts[i + 1]))
    return blocks


def brief_problems(root=None):
    """Problems with the Build 17 brief's stated contract."""
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "devin-playbook-brief.md")
    if raw is None:
        return ["docs/devin-playbook-brief.md is missing"]
    text = re.sub(r"\s+", " ", raw)
    problems = []
    for label, fragment in PINNED:
        if fragment not in text:
            problems.append(
                "docs/devin-playbook-brief.md does not state %s"
                % label
            )
    return problems


def rules_problems(root=None):
    """Problems with the brief's derivation noted rules."""
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "devin-playbook-brief.md")
    if raw is None:
        return ["docs/devin-playbook-brief.md is missing"]
    problems = []
    section = rules_section(raw)
    if section is None:
        problems.append(
            "docs/devin-playbook-brief.md carries no %r section"
            % RULES_HEADING
        )
        return problems
    blocks = rule_blocks(section)
    if not blocks:
        problems.append(
            "docs/devin-playbook-brief.md carries no R numbered rules"
        )
    for name, block in blocks:
        flat = re.sub(r"\s+", " ", block)
        if "Derives from" not in flat:
            problems.append(
                "devin rule %s carries no derivation note, so it "
                "would be a rival instruction source" % name
            )
            continue
        note = flat.split("Derives from", 1)[1]
        if not deliberate_source(note):
            problems.append(
                "devin rule %s names no canonical skill section, "
                "primary Devin citation, or binding decision in its "
                "derivation note" % name
            )
    return problems


def naming_problems(root=None):
    """Problems with the Devin Dynamic Workflows naming guard.

    Every Devin Dynamic Workflows mention must name Devin, so
    the Build 6 Claude Code fan out surface is never confused
    with Devin Dynamic Workflows, and the brief must never cite
    the Build 6 figures as evidence about Devin.
    """
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "devin-playbook-brief.md")
    if raw is None:
        return ["docs/devin-playbook-brief.md is missing"]
    flat = re.sub(r"\s+", " ", raw).lower()
    problems = []
    for match in re.finditer(r"dynamic workflows", flat):
        before = flat[max(0, match.start() - 6):match.start()]
        if before != "devin ":
            problems.append(
                "docs/devin-playbook-brief.md names dynamic "
                "workflows without Devin, which confuses the "
                "Build 6 surface with Devin Dynamic Workflows"
            )
            break
    if "16 agents" in flat:
        problems.append(
            "docs/devin-playbook-brief.md cites the Build 6 "
            "figures as evidence about Devin"
        )
    return problems


def decision_problems(root=None):
    """Problems with the Build 17 decision record."""
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "decisions.md")
    if raw is None:
        return ["docs/decisions.md is missing"]
    start = raw.find(DECISION_HEADING)
    if start < 0:
        return [
            "docs/decisions.md carries no Build 17 decision record"
        ]
    rest = raw[start + len(DECISION_HEADING):]
    match = re.search(r"(?m)^## ", rest)
    record = rest[:match.start()] if match else rest
    if DECISION_STATEMENT not in record:
        return [
            "the Build 17 decision record carries no decision 4 "
            "statement, which every landed build must record"
        ]
    return []


def devin_problems(root=None):
    """Every Build 17 Devin playbook and coordinator problem."""
    problems = []
    problems.extend(brief_problems(root))
    problems.extend(rules_problems(root))
    problems.extend(naming_problems(root))
    problems.extend(decision_problems(root))
    return problems


def main(root=None):
    problems = devin_problems(root)
    if problems:
        for problem in problems:
            print("check_devin: %s" % problem, file=sys.stderr)
        return 1
    print("check_devin: the Build 17 Devin contract holds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
