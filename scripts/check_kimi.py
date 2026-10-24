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
for each of the four events in both modes and proves a
failed check stops the turn it gates while a passing check
lets the turn proceed.
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
    ("the delegation sentence",
     "the platform allows the main agent to delegate to "
     "plugin agents as sub agents"),
    ("the unknown fields sentence",
     "Unknown agent frontmatter fields are ignored"),
    ("the event meaning mapping",
     "They observe turn starts, queued user input, sub "
     "task launches, and session heartbeats"),
    ("the configurable hooks sentence",
     "configurable under `[[hooks]]` in `config.toml`"),
    ("the oversized diagnostics sentence",
     "Oversized content is ignored and reported in the "
     "plugin diagnostics"),
    ("the skipped with a warning sentence",
     "Contributions beyond the budget are skipped with "
     "a warning"),
    ("the project scope sentence",
     "Project level installation scope is not yet supported"),
    ("the reference layout sentence",
     "ships `.kimi-plugin/plugin.json` beside `.claude-plugin/`"),
)

# Decision 24 fragments the gate pins. A record that keeps only
# the decision 4 statement and drops the rest is a gutted
# record, not a decision, so every fragment below must be
# present in the record.
DECISION_PINNED = (
    ("the agents field", "manifest `agents` field takes"),
    ("the collision precedence",
     "all win over the plugin provided agent"),
    ("the qualified names rule", "bare name no longer works"),
    ("the global hook working directory",
     "session's project directory"),
    ("the plugin hook working directory",
     "working directory set to the plugin root"),
    ("the 32KB field limit", "limited to 32 KB"),
    ("the 64KB total limit", "64 KB total"),
    ("the unsupported fields diagnostics",
     "appear as diagnostics and are ignored"),
    ("the print mode persona", "kimi -p --agent reviewer"),
    ("the hook blocking posture", "stops the turn it gates"),
    ("the per user install scope",
     "install per user and apply to all projects"),
    ("the reference layout", ".kimi-plugin/plugin.json"),
)

# The sentence that explains the decision numbering gap.
# Decision 20 is followed by decision 22 and no decision 21
# exists anywhere in the tree, so the record must say so.
NUMBERING_NOTE = "No decision 21 exists in this record"

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
    marker. R28-RT-07. A bare citation is not a derivation, so
    a primary citation counts only when the note names a
    specific page path and states the claim it supports, and
    Decision 4 counts only when the note says what it binds
    the rule to. A note that says only a host stem or only a
    decision number derives from nothing.
    """
    claim_words = (
        "states", "documents", "announces", "lists", "sets",
        "describes", "works", "ships", "covers", "records",
        "names", "fails closed", "keeps",
    )
    for title in CANONICAL_SECTIONS:
        match = re.search(
            r"canonical skill[^.;]{0,200}" + re.escape(title), note
        )
        if match:
            rest = note[match.end():]
            if len(rest.strip()) >= 15 and any(
                word in rest for word in claim_words
            ):
                return True
    if re.search(r"(kimi\.com|github\.com)/\S+", note):
        if len(note.strip()) >= 40 and any(
            word in note for word in claim_words
        ):
            return True
    if "Decision 4" in note:
        rest = note.split("Decision 4", 1)[1]
        if len(rest.strip()) >= 20 and any(
            word in rest for word in claim_words
        ):
            return True
    return False


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
    # R28-RT-06. A rule that does not volunteer for R numbering
    # escapes the check above, so every other level 3 heading
    # inside the rules section is itself a problem, and so is
    # any rule shaped heading after the rules section.
    for heading in re.findall(r"(?m)^### (.+)$", section):
        if not re.match(r"R\d+\.", heading):
            problems.append(
                "docs/kimi-plugin-brief.md carries an unnumbered "
                "rule heading %r inside the rules section, so it "
                "escapes the derivation check" % heading
            )
    tail = raw[raw.find(RULES_HEADING):]
    for heading in re.findall(r"(?m)^#{2,3} (.+)$", tail):
        if heading == "The Kimi rules":
            continue
        if re.match(r"R\d+\.", heading):
            continue
        if "rule" in heading.lower():
            problems.append(
                "docs/kimi-plugin-brief.md carries a rule shaped "
                "heading %r outside the R numbered rules, so it "
                "escapes the derivation check" % heading
            )
    intro = re.split(r"(?m)^### ", section, maxsplit=1)[0]
    if intro.strip():
        problems.append(
            "docs/kimi-plugin-brief.md carries a bare paragraph "
            "in the rules section before the R numbered rules, "
            "so it escapes the derivation check"
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
        # R28-RT-06. A bare paragraph planted after a rule's
        # derivation note sits inside that rule's block and
        # inherits its note, so any paragraph after the note
        # paragraph is a rule shaped paragraph outside a rule.
        paragraphs = [
            para.strip()
            for para in re.split(r"\n\s*\n", block)
            if para.strip()
        ]
        for index, para in enumerate(paragraphs):
            if "Derives from" in para:
                for later in paragraphs[index + 1:]:
                    problems.append(
                        "kimi rule %s carries a paragraph after "
                        "its derivation note, so a planted rule "
                        "sentence would escape the check" % name
                    )
                    break
                break
    return problems


def numbering_problems(root=None):
    """R28-RT-13. The decision numbering gap must be explained.

    Decision 20 is followed by decision 22 and no decision 21
    exists anywhere in the tree. The record must carry the
    dated explanation, or a later reader cannot tell a gap
    from a deletion.
    """
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "decisions.md")
    if raw is None:
        return ["docs/decisions.md is missing"]
    headings = re.findall(r"(?m)^## (\d+)\.", raw)
    if "21" in headings:
        return []
    if NUMBERING_NOTE in raw:
        return []
    return [
        "docs/decisions.md jumps from decision 20 to decision "
        "22 with no explanation for the missing decision 21"
    ]


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
    # R28-RT-01. The posture is defeated by rewording, so the
    # check is semantic, not a phrase list. A failed check
    # subject near a proceeds or continues verb, a hook
    # failure called advisory, or a failure said never to
    # stop a turn all state the same forbidden posture. The
    # brief's own sentence pairs a failed check with stops,
    # never with proceeds, so it does not flag itself.
    hook_failure = (
        r"(failed|failing|failure|failures|hook check|hook "
        r"failures|a failed check)"
    )
    for pattern in (
        hook_failure + r"[^.]{0,80}\b(proceeds|continues|goes ahead"
        r"|is allowed through|passes through)\b",
        r"\bhook (failures|failure) (are|is) advisory\b",
        r"\b(failures|failure) (are|is) advisory\b",
        r"\badvisory (only|check|hook)\b",
        r"\bnever (stop|prevent|halt)\b[^.]{0,40}\b(turn|session)\b",
        r"\bdoes not (block|stop|halt)\b[^.]{0,40}\b(turn|session)\b",
        r"\bnot (block|stop|halt)\b[^.]{0,40}\b(turn|session)\b",
        r"\bfailed check[^.]{0,60}\blog(s|ged)? a warning\b",
    ):
        if re.search(pattern, text):
            problems.append(
                "a kimi rule lets a failed hook check pass the "
                "turn through, which the blocking posture "
                "forbids"
            )
            break
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
    # R28-RT-02. The precedence is defeated by rewording, so
    # the check is semantic. A plugin subject paired with a
    # winning verb, or a resolution to the plugin copy, states
    # the same forbidden win. The brief's own sentence puts
    # the plugin agent after win over, as the loser, so it
    # does not flag itself.
    plugin_subject = (
        r"plugin[-\s]?(provided )?(agent|copy)"
    )
    for pattern in (
        plugin_subject + r"[^.]{0,80}\b(wins|resolves|takes "
        r"precedence|takes priority|prevails|overrides|is "
        r"selected|is chosen|is preferred)\b",
        r"\b(resolves to|selects|chooses|picks) the plugin "
        r"(copy|agent)\b",
        r"\bplugin (copy|agent) is (selected|chosen|preferred)\b",
        r"\bcollision[^.]{0,80}\bplugin (copy|agent) wins\b",
    ):
        if re.search(pattern, text):
            problems.append(
                "a kimi rule lets the plugin provided agent win a "
                "name collision, which the precedence rule "
                "forbids"
            )
            break
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
    # R28-RT-03. The rule is defeated by rewording, so a bare
    # name subject paired with an acceptance verb is forbidden
    # in any phrasing. A segment that says the bare name no
    # longer works, or does not work, is the brief's own
    # negative sentence and is skipped.
    for match in re.finditer(
        r"\bbare name\b[^.]{0,60}\b(works|is accepted|accepted|"
        r"resolves|is sufficient|is allowed|is enough)\b", text
    ):
        segment = match.group(0)
        if "no longer" in segment or "does not" in segment:
            continue
        if re.search(r"\bnot\b[^.]{0,20}$", segment):
            continue
        problems.append(
            "a kimi rule accepts a bare name plugin skill "
            "invocation, which the qualified names rule "
            "forbids"
        )
        break
    for pattern in (
        r"\binvoke (a plugin skill )?by the bare name\b",
        r"\binvoking (a plugin skill )?by the bare name\b",
        r"\bbare name invocation is (allowed|accepted)\b",
    ):
        if re.search(pattern, text):
            segment = text[
                max(0, re.search(pattern, text).start() - 30):
                re.search(pattern, text).end() + 30
            ]
            if "no longer" in segment:
                continue
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
    # R28-RT-04. The same claim in noun form defeats the
    # clause form above, so the noun form is forbidden too.
    # A noun form preceded by a negation is the brief's own
    # distinction and is skipped.
    for match in re.finditer(
        r"\bserver[-\s]?start directory\b", text
    ):
        before = text[max(0, match.start() - 30):match.start()]
        if re.search(r"\bnot (the )?$" , before):
            continue
        if "not the" in before[-12:]:
            continue
        problems.append(
            "a kimi rule puts hooks in the server start "
            "directory, which the working directory rule "
            "forbids"
        )
        break
    for match in re.finditer(
        r"\bserver's start directory\b", text
    ):
        before = text[max(0, match.start() - 30):match.start()]
        if re.search(r"\bnot (the )?$" , before):
            continue
        problems.append(
            "a kimi rule puts hooks in the server start "
            "directory, which the working directory rule "
            "forbids"
        )
        break
    return problems


def limits_problems(root=None):
    """R28-RT-05. No sentence may inflate the size limits.

    The pin fragments prove the 32KB and 64KB figures are
    stated, but an added sentence stating a larger limit
    passes while the pins stay in place. Any kilobyte figure
    other than 32 or 64, and any megabyte figure at all, is
    an inflated limit.
    """
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "kimi-plugin-brief.md")
    if raw is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    text = re.sub(r"\s+", " ", raw)
    problems = []
    for match in re.finditer(r"(\d+)\s*KB", text):
        if int(match.group(1)) not in (32, 64):
            problems.append(
                "a kimi rule states a size limit of %s KB, "
                "which inflates the pinned 32KB and 64KB "
                "limits" % match.group(1)
            )
            break
    if re.search(r"\d+\s*MB", text):
        problems.append(
            "a kimi rule states a size limit in megabytes, "
            "which inflates the pinned 32KB and 64KB limits"
        )
    return problems


def persona_problems(root=None):
    """R28-RT-05. No sentence may run print mode CI without
    a persona.

    The persona pin proves the reviewer persona is stated,
    but an added sentence running CI without any persona
    passes while the pin stays in place.
    """
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "kimi-plugin-brief.md")
    if raw is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    text = re.sub(r"\s+", " ", raw)
    for pattern in (
        r"\bwithout (any |a )?persona\b",
        r"\bno persona\b",
        r"\bpersona[-\s]?free\b",
        r"\bruns without\b[^.]{0,40}\bpersona\b",
    ):
        if re.search(pattern, text):
            return [
                "a kimi rule runs print mode CI without a "
                "persona, which the print mode persona rule "
                "forbids"
            ]
    return []


def unsupported_problems(root=None):
    """R28-RT-05. No sentence may honour unsupported fields.

    The diagnostics pin proves the fields are ignored, but
    an added sentence honouring and executing them passes
    while the pin stays in place.
    """
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "kimi-plugin-brief.md")
    if raw is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    text = re.sub(r"\s+", " ", raw)
    for pattern in (
        r"\bunsupported[^.]{0,80}\b(honour|honor|execut|appl"
        r"y|enforc)",
        r"\bhonour(ed)? and executed\b",
        r"\bhonor(ed)? and executed\b",
    ):
        if re.search(pattern, text):
            return [
                "a kimi rule honours unsupported runtime "
                "fields, which the diagnostics rule forbids"
            ]
    return []


def managed_problems(root=None):
    """R28-RT-05. No sentence may let source edits take
    effect without a reinstall.

    The managed copy pin proves the CLI runs from the
    managed copy, but an added sentence letting a source
    edit take effect immediately passes while the pin stays
    in place.
    """
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "kimi-plugin-brief.md")
    if raw is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    text = re.sub(r"\s+", " ", raw)
    for pattern in (
        r"\btakes? effect immediately\b",
        r"\bwithout a reinstall\b",
        r"\bsource (directory|edit)[^.]{0,60}\btakes? effect\b",
    ):
        if re.search(pattern, text):
            return [
                "a kimi rule lets a source edit take effect "
                "without a reinstall, which the managed copy "
                "rule forbids"
            ]
    return []


def scope_problems(root=None):
    """R28-RT-05. No sentence may install plugins per project.

    The per user pin proves the scope is stated, but an
    added sentence installing per project passes while the
    pin stays in place.
    """
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "kimi-plugin-brief.md")
    if raw is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    text = re.sub(r"\s+", " ", raw)
    for pattern in (
        r"\binstall(?:s|ed|ing)? per project\b",
        r"\bper project (only|scope|install)",
        r"\bappl(?:y|ies) to one project only\b",
        r"\bone project only\b",
    ):
        if re.search(pattern, text):
            return [
                "a kimi rule installs plugins per project, "
                "which the per user scope rule forbids"
            ]
    return []


def fixture_content_problems(root=None):
    """R28-RT-10. The collision fixture contents must agree
    with the precedence they prove.

    The fixture pair is checked by directory name only
    unless the contents are read, so a swapped or hostile
    fixture passes in silence. The user fixture must state
    the user win and the plugin fixture must state the
    plugin loss.
    """
    root = ROOT if root is None else root
    base = root / "tests" / "fixtures" / "kimi-collision"
    problems = []
    user_text = read_text(base / "user" / "reviewer.md")
    plugin_text = read_text(base / "plugin" / "reviewer.md")
    if user_text is None or plugin_text is None:
        return [
            "the kimi collision fixture is missing the user and "
            "plugin reviewer pair"
        ]
    if "wins" not in user_text:
        problems.append(
            "the user collision fixture does not state the "
            "user win, so the fixture pair no longer proves "
            "the precedence"
        )
    if "loses" not in plugin_text:
        problems.append(
            "the plugin collision fixture does not state the "
            "plugin loss, so the fixture pair no longer proves "
            "the precedence"
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
    # R28-RT-09. A record that keeps the statement and drops
    # everything else is gutted, so every load bearing
    # fragment must be present in the record.
    flat = re.sub(r"\s+", " ", record)
    problems = []
    for label, fragment in DECISION_PINNED:
        if fragment not in flat:
            problems.append(
                "the Build 14 decision record does not state "
                "%s" % label
            )
    return problems


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

    R27-RT-01 and R28-RT-11. Each event runs the fixture
    blocking check in fail mode, and every one must report
    a blocked turn, and in pass mode, and every one must
    report a turn that proceeds. A fixture that always
    blocks passes the fail probe and fails the pass probe,
    so fail mode alone proves nothing about a passing check.
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
        verdict = hook_turn_verdict(event, "pass", root)
        if verdict != "proceeds":
            problems.append(
                "the %s hook check did not let a passing check "
                "proceed, verdict %s" % (event, verdict)
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
    problems.extend(limits_problems(root))
    problems.extend(persona_problems(root))
    problems.extend(unsupported_problems(root))
    problems.extend(managed_problems(root))
    problems.extend(scope_problems(root))
    problems.extend(fixture_content_problems(root))
    problems.extend(decision_problems(root))
    problems.extend(numbering_problems(root))
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
        "holds, with live blocking and pass checks on all four "
        "hook events"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
