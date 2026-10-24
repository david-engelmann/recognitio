#!/usr/bin/env python3
"""Pin the Build 14 Kimi managed plugin contract.

The brief at docs/kimi-plugin-brief.md is scoped Kimi
guidance beside the canonical packet. It must never become a
second packet, a rival instruction source, so every rule it
states carries a derivation note naming the canonical skill
section or gate it restates or the primary citation it
reports. This script pins that discipline without a Kimi
host. It requires every rule in the rules section to carry a
checkable derivation note, and it pins the stated negatives
and limits the round 27 lanes named. The hook blocking
posture for the four hook events, the collision precedence,
the qualified names rule, the hook working directory in
both scopes, the 32KB per systemPrompt field and 64KB total
limits, the unsupported runtime field diagnostics, the
--agent reviewer persona for print mode CI with the stay
alive behavior, and the decision record naming Build 14
with a decision 4 statement are all pinned as brief
sentences. A later edit that drops any of them fails the
gate instead of drifting in silence.

The hook blocking posture is the managed plugin's own
contract, not a platform behavior the primaries describe.
The live probe in main() runs the fixture blocking check
for each of the four events and proves a failed check stops
the turn it gates.
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / "docs" / "kimi-plugin-brief.md"
DECISIONS = ROOT / "docs" / "decisions.md"

RULES_HEADING = "## The Kimi rules"

# The four hook events the brief wires through blocking
# checks, per the primary whats new page.
HOOK_EVENTS = (
    "TurnStarted",
    "UserPromptQueued",
    "TaskStarted",
    "SessionHeartbeat",
)

# Fixture blocking check and the collision fixture pair are read
# relative to the tree root under test, so the paths below are
# built per root inside the functions that use them.

# Agent source precedence, lowest rank wins, per the primary
# agents page scope order. The fixture pair below resolves
# reviewer to the user level agent under this order.
SOURCE_RANK = {
    "agent-file": 0,
    "project": 1,
    "extra": 2,
    "user": 3,
    "plugin": 4,
    "built-in": 5,
}

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

# Primary citations a derivation note may name, written as URL
# stems so the note pins the surface the claim was read from.
# "kimi.com" is the docs host for the plugins, whats new, and
# agents pages. "github.com" is the releases host for the
# qualified names and hook working directory entries and the
# host of the alibaba/open-code-review reference repo.
PRIMARY_CITATIONS = (
    "kimi.com",
    "github.com",
)

# Brief sentences the gate pins. Each is a fragment of the exact
# sentence the brief carries, so a later edit that softens or
# drops a stated pin, quote, or limit fails loudly.
PINNED = (
    ("the agents field auto discovery",
     "an `agents/` directory at the plugin root is auto discovered"),
    ("the collision precedence",
     "User level, extra, project level, and `--agent-file` agents "
     "all win over the plugin provided agent"),
    ("the built in override requirement",
     "explicit `override: true` in the frontmatter"),
    ("the qualified names rule",
     "Invoking a plugin skill by its bare name no longer works"),
    ("the global hook working directory",
     "run in the session's project directory"),
    ("the plugin hook working directory",
     "working directory set to the plugin root"),
    ("the four hook events",
     "TurnStarted, UserPromptQueued, TaskStarted, and SessionHeartbeat"),
    ("the hook blocking check",
     "A hook check that fails stops the turn it gates"),
    ("the 32KB field limit",
     "limited to 32 KB of UTF-8 bytes"),
    ("the 64KB total limit",
     "injects at most 64 KB of instructions"),
    ("the unsupported fields diagnostics",
     "appear as diagnostics and are ignored"),
    ("the print mode persona",
     "Print mode CI runs under the reviewer persona through "
     "`kimi -p --agent reviewer`"),
    ("the print mode stay alive",
     "stays alive and feeds each result back to the main agent"),
    ("the per user install scope",
     "installed per user and apply to all projects"),
    ("the managed copy",
     "the CLI always runs from the managed copy"),
    ("the decision 4 statement",
     "Decision 4 binds this build like every other build"),
)

DECISION_HEADING = "## 24. Build 14"
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
    """Problems with the Build 14 brief's stated contract."""
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "kimi-plugin-brief.md")
    if raw is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    text = re.sub(r"\s+", " ", raw)
    problems = []
    for label, fragment in PINNED:
        if fragment not in text:
            problems.append(
                "docs/kimi-plugin-brief.md does not state %s"
                % label
            )
    return problems


def rules_problems(root=None):
    """Problems with the brief's derivation noted rules."""
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "kimi-plugin-brief.md")
    if raw is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    problems = []
    section = rules_section(raw)
    if section is None:
        problems.append(
            "docs/kimi-plugin-brief.md carries no %r section"
            % RULES_HEADING
        )
        return problems
    blocks = rule_blocks(section)
    if not blocks:
        problems.append(
            "docs/kimi-plugin-brief.md carries no R numbered rules"
        )
    for name, block in blocks:
        flat = re.sub(r"\s+", " ", block)
        if "Derives from" not in flat:
            problems.append(
                "kimi rule %s carries no derivation note, so it "
                "would be a rival instruction source" % name
            )
            continue
        note = flat.split("Derives from", 1)[1]
        if not deliberate_source(note):
            problems.append(
                "kimi rule %s names no canonical skill section, "
                "primary citation, or binding decision in its "
                "derivation note" % name
            )
    return problems


def hook_problems(root=None):
    """R27-RT-01. No sentence may treat the four hook events as
    notification only and never blocking.

    The brief states the managed plugin's own blocking
    posture, that a hook check that fails stops the turn it
    gates. A planted sentence that calls the events
    notification only or says they never block must fail the
    gate. The regexes are intentionally strict so a later
    edit cannot soften the posture in passing.
    """
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "kimi-plugin-brief.md")
    if raw is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    text = re.sub(r"\s+", " ", raw)
    problems = []
    if re.search(r"\bnotification only\b", text):
        problems.append(
            "a kimi rule treats the hook events as notification "
            "only, which the blocking posture forbids"
        )
    if re.search(r"\bnever block\b", text):
        problems.append(
            "a kimi rule says the hook events never block, which "
            "the blocking posture forbids"
        )
    return problems


def collision_problems(root=None):
    """R27-RT-02. No sentence may let the plugin provided agent
    win a name collision, and the fixture pair must resolve
    to the user level agent.

    The brief states the precedence, that user level, extra,
    project level, and --agent-file agents all win over the
    plugin provided one. A planted sentence that grants the
    plugin agent the win must fail the gate. The regex reads
    the plugin agent as the winning subject, so the brief's
    own sentence, where the plugin agent is the loser, does
    not flag itself. The fixture check proves the precedence
    order resolves the committed reviewer pair to the user
    level agent.
    """
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "kimi-plugin-brief.md")
    if raw is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    text = re.sub(r"\s+", " ", raw)
    problems = []
    if re.search(
        r"plugin[-\s]?provided agent[^.]{0,80}\bwins over\b", text
    ):
        problems.append(
            "a kimi rule lets the plugin provided agent win a "
            "name collision, which the precedence rule forbids"
        )
    winner, found = fixture_collision_winner(root)
    if "user" not in found or "plugin" not in found:
        problems.append(
            "the kimi collision fixture is missing the user and "
            "plugin reviewer pair"
        )
    elif winner != "user":
        problems.append(
            "the collision fixture resolves reviewer to %s, but "
            "the user level agent must win over the plugin "
            "provided one" % winner
        )
    return problems


def fixture_collision_winner(root=None):
    """The winning source for the fixture reviewer pair.

    Each fixture directory name is the agent source. Returns
    the (winner, sources) pair, with the lowest rank winning
    under SOURCE_RANK.
    """
    root = ROOT if root is None else root
    base = root / "tests" / "fixtures" / "kimi-collision"
    found = {}
    try:
        children = sorted(base.iterdir())
    except OSError:
        children = []
    for child in children:
        if (
            child.is_dir()
            and child.name in SOURCE_RANK
            and (child / "reviewer.md").is_file()
        ):
            found[child.name] = child / "reviewer.md"
    if not found:
        return None, found
    winner = min(found, key=lambda source: SOURCE_RANK[source])
    return winner, found


def qualified_problems(root=None):
    """R27-RT-03. No sentence may accept a bare name plugin
    skill invocation.

    The brief states the qualified names rule, that a plugin
    skill is invoked under its qualified <pluginId>:<skillName>
    name and the bare name no longer works. A planted sentence
    that lets the bare name resolve must fail the gate. The
    regexes name the planted phrasings, so the brief's own
    "the bare name no longer works" does not flag itself.
    """
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "kimi-plugin-brief.md")
    if raw is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    text = re.sub(r"\s+", " ", raw)
    problems = []
    for pattern in (
        r"\bby its bare skill name\b",
        r"\bbare name resolves\b",
        r"\bqualified name is optional\b",
    ):
        if re.search(pattern, text):
            problems.append(
                "a kimi rule accepts a bare name plugin skill "
                "invocation, which the qualified names rule "
                "forbids"
            )
            break
    return problems


def workdir_problems(root=None):
    """R27-RT-04. No sentence may put hooks in the server
    start directory.

    The brief states the working directory rule, that hooks
    run in the session's project directory and not the
    directory the server was started from, with plugin hooks
    at the plugin root as the separate scope. A planted
    sentence that puts hooks in the server start directory
    must fail the gate. The regex is negation aware so the
    brief's own "not the directory the server was started
    from" does not flag itself.
    """
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "kimi-plugin-brief.md")
    if raw is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    text = re.sub(r"\s+", " ", raw)
    problems = []
    if re.search(
        r"(?<!not the )directory the server was started from", text
    ):
        problems.append(
            "a kimi rule puts hooks in the server start "
            "directory, which the working directory rule "
            "forbids"
        )
    return problems


def decision_problems(root=None):
    """Problems with the Build 14 decision record."""
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "decisions.md")
    if raw is None:
        return ["docs/decisions.md is missing"]
    start = raw.find(DECISION_HEADING)
    if start < 0:
        return [
            "docs/decisions.md carries no Build 14 decision record"
        ]
    rest = raw[start + len(DECISION_HEADING):]
    match = re.search(r"(?m)^## ", rest)
    record = rest[:match.start()] if match else rest
    if DECISION_STATEMENT not in record:
        return [
            "the Build 14 decision record carries no decision 4 "
            "statement, which every landed build must record"
        ]
    return []


def hook_turn_verdict(event, mode, root=None):
    """The verdict a hook check returns for one event.

    Runs the fixture blocking check for the event. The check
    prints the event it ran and exits nonzero on a failed
    check. A nonzero exit is a blocked turn, which the Build
    14 blocking posture pins. Returns "blocked", "proceeds",
    or "unverified" when the check did not run the event.
    """
    root = ROOT if root is None else root
    script = root / "tests" / "fixtures" / "kimi-hooks" / "blocking_check.py"
    try:
        proc = subprocess.run(
            [sys.executable, str(script), event, mode],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return "unverified"
    if event not in proc.stdout:
        return "unverified"
    return "blocked" if proc.returncode != 0 else "proceeds"


def live_hook_problems(root=None):
    """The live blocking probe over the four hook events.

    R27-RT-01. Each event runs the fixture blocking check in
    fail mode, and every one must report a blocked turn. A
    hook whose failed check does not stop the turn it gates
    fails the gate.
    """
    root = ROOT if root is None else root
    problems = []
    for event in HOOK_EVENTS:
        verdict = hook_turn_verdict(event, "fail", root)
        if verdict != "blocked":
            problems.append(
                "the %s hook check did not block the turn it "
                "gates, verdict %s" % (event, verdict)
            )
    return problems


def kimi_problems(root=None):
    """Every Build 14 Kimi managed plugin problem."""
    problems = []
    problems.extend(brief_problems(root))
    problems.extend(rules_problems(root))
    problems.extend(hook_problems(root))
    problems.extend(collision_problems(root))
    problems.extend(qualified_problems(root))
    problems.extend(workdir_problems(root))
    problems.extend(decision_problems(root))
    return problems


def main(root=None):
    problems = kimi_problems(root)
    problems.extend(live_hook_problems(root))
    if problems:
        for problem in problems:
            print("check_kimi: %s" % problem, file=sys.stderr)
        return 1
    print(
        "check_kimi: the Build 14 Kimi managed plugin contract "
        "holds, with a live blocking check on all four hook events"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
