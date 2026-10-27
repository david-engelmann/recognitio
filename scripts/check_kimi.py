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
and limits the round 27 lanes named. The observation only
posture for the four hook events, the collision precedence,
the qualified names rule, the hook working directory in
both scopes, the 32KB per systemPrompt field and 64KB total
limits, the unsupported runtime field diagnostics, the
--agent reviewer persona for print mode CI with the stay
alive behavior, and the decision record naming Build 14
with a decision 4 statement are all pinned as brief
sentences. A later edit that drops any of them fails the
gate instead of drifting in silence.

The four hook events are observation only on the Kimi host,
per the primary Kimi hooks page. Only PreToolUse, Stop, and
UserPromptSubmit have return values that affect the main
flow, so no check on the four events can block anything.
The live probe in main() runs the fixture observation check
the way the host runs a hook, with the event as JSON on
stdin and no arguments, and proves the check runs for each
of the four events and exits 0.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / "docs" / "kimi-plugin-brief.md"
DECISIONS = ROOT / "docs" / "decisions.md"

RULES_HEADING = "## The Kimi rules"

# The four hook events the brief wires through observation
# checks, per the primary whats new page.
HOOK_EVENTS = (
    "TurnStarted",
    "UserPromptQueued",
    "TaskStarted",
    "SessionHeartbeat",
)

# Fixture observation check and the collision fixture pair are read
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
    ("the hook observation posture",
     "The four hook events are observation only on the Kimi host"),
    ("the blocking events list",
     "Only PreToolUse, Stop, and UserPromptSubmit have return "
     "values that affect the main flow"),
    ("the no blocking consequence",
     "no check on the four events can stop a turn"),
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
    ("the trust workspace variable",
     "KIMI_CODE_TRUST_WORKSPACE"),
    ("the unversioned reference layout",
     "No version is pinned for this reference layout"),
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
    ("the hook observation posture",
     "observation only on the Kimi host"),
    ("the blocking events list",
     "Only PreToolUse, Stop, and UserPromptSubmit have return "
     "values that affect the main flow"),
    ("the per user install scope",
     "install per user and apply to all projects"),
    ("the reference layout", ".kimi-plugin/plugin.json"),
    # R29-RT-11. These three sentences were stated in
    # decision 24 and unpinned, so dropping them shipped in
    # silence. They join the pin list with the stay alive
    # sentence.
    ("the built in override",
     "replacing a built in agent requires an explicit"),
    ("the four hook events",
     "TurnStarted, UserPromptQueued, TaskStarted, and "
     "SessionHeartbeat"),
    ("the configurable hooks",
     "configurable under `[[hooks]]` in `config.toml`"),
    ("the stay alive",
     "print mode stays alive while background tasks are pending"),
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


# Negation words that can scope over a forbidden claim in the
# same clause. A clause that negates its own forbidden verb is
# a correct restatement, not a contradiction, so the negative
# groups skip it. Negations that ARE the forbidden claim, such
# as a failure said not to stop a turn, are matched by explicit
# patterns before this skip is consulted.
NEG_WORDS = (
    "does not", "do not", "did not", "doesn't", "don't",
    "never", "no longer", "cannot", "can't", "is not",
    "are not", "was not", "were not", "will not", "won't",
)


def _sentences(text):
    """Lowercase sentences of whitespace normalised text.

    Every negative group runs on these sentences, so a
    capitalised keyword at the start of a sentence matches the
    same pattern as the same word mid sentence. R29-RT-12.
    """
    flat = re.sub(r"\s+", " ", text).lower()
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", flat)
        if sentence.strip()
    ]


def _clauses(sentence):
    """Clauses of one sentence, split on but, however, and
    semicolons, so a negation carve out applies to its own
    clause only and never swallows a later contradicting
    clause in the same sentence. R29-RT-03."""
    parts = re.split(
        r"\s+but\s+|,\s*but\s+|;\s+|\s+however\s*,?\s*", sentence
    )
    return [part.strip() for part in parts if part.strip()]


def _neg_before(clause, index, window=50):
    """Whether a negation word stands shortly before index in
    the clause."""
    before = clause[max(0, index - window):index]
    if re.search(r"\bnot\b", before):
        return True
    return any(word in before for word in NEG_WORDS)


def _brief_clauses(root):
    """Every clause of the brief, lowercased, in order."""
    raw = read_text(root / "docs" / "kimi-plugin-brief.md")
    if raw is None:
        return None
    clauses = []
    for sentence in _sentences(raw):
        clauses.extend(_clauses(sentence))
    return clauses


def _brief_sentences(root):
    """Every sentence of the brief, lowercased, in order."""
    raw = read_text(root / "docs" / "kimi-plugin-brief.md")
    if raw is None:
        return None
    return _sentences(raw)


# Claim words each shipped derivation note carries, so a note
# that names a path and a verb but never restates what the
# rule claims is still a bare citation. R29-RT-08.
NOTE_CLAIMS = {
    "R1": ("delegation", "auto discovery"),
    "R2": ("precedence", "scope order"),
    "R3": ("bare name",),
    "R4": ("project directory",),
    "R5": ("four events",),
    "R6": ("observation", "return values"),
    "R7": ("32 kb", "64 kb"),
    "R8": ("diagnostics",),
    "R9": ("stay alive", "reviewer persona"),
    "R10": ("managed copy", "per user"),
}

# Content sentence counts per shipped rule, counting only the
# paragraphs between the rule title and its derivation note.
# A sentence planted inside an existing content paragraph
# changes the count, which is the only shape check that can
# see it. R29-RT-07.
RULE_CONTENT_SENTENCES = {
    "R1": 4,
    "R2": 5,
    "R3": 2,
    "R4": 3,
    "R5": 2,
    "R6": 5,
    "R7": 4,
    "R8": 2,
    "R9": 5,
    "R10": 7,
}

# Headings allowed after the rules section. Any other heading
# after the rules section is a new section carrying unchecked
# rule shaped text. R29-RT-07.
POST_RULES_HEADINGS = (
    "The Build 14 decision record",
    "Skill tightness",
)

# Generic words that never count as restating a rule's claim.
_GENERIC_WORDS = {
    "plugin", "plugins", "agent", "agents", "kimi", "skill",
    "skills", "rule", "rules", "brief", "page", "docs",
    "document", "documents", "states", "state", "primary",
    "canonical", "section", "build", "builds", "review",
    "reviewer", "packet", "packets", "code", "mode",
}


def deliberate_source(note, rule=None, content=None):
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
    decision number derives from nothing. R29-RT-08. A note
    must also restate the rule's claim in its own words, so a
    shipped rule's note must carry one of its claim words,
    and a new rule's note must carry one distinctive word
    from its own content, so a path plus a verb with no claim
    is still a bare citation.
    """
    note = note.lower()
    claim_words = (
        "states", "documents", "announces", "lists", "sets",
        "describes", "works", "ships", "covers", "records",
        "names", "fails closed", "keeps",
    )
    shaped = False
    for title in CANONICAL_SECTIONS:
        match = re.search(
            r"canonical skill[^.;]{0,200}" + re.escape(title.lower()),
            note,
        )
        if match:
            rest = note[match.end():]
            if len(rest.strip()) >= 15 and any(
                word in rest for word in claim_words
            ):
                shaped = True
    if re.search(r"(kimi\.com|github\.com)/\S+", note):
        if len(note.strip()) >= 40 and any(
            word in note for word in claim_words
        ):
            shaped = True
    if "decision 4" in note:
        rest = note.split("decision 4", 1)[1]
        if len(rest.strip()) >= 20 and any(
            word in rest for word in claim_words
        ):
            shaped = True
    if not shaped:
        return False
    if rule in NOTE_CLAIMS:
        return any(word in note for word in NOTE_CLAIMS[rule])
    if content:
        words = set()
        for token in re.findall(r"[a-z0-9]+", content.lower()):
            if len(token) >= 4 and token not in _GENERIC_WORDS:
                words.add(token)
        return any(word in note for word in words)
    return True


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
    # R28-RT-06 and R29-RT-07. A rule that does not volunteer
    # for R numbering escapes the check above, so every heading
    # at any level inside the rules section that is not an R
    # numbered heading is itself a problem, and so is any
    # heading after the rules section that is not an R heading
    # or a heading the shipped brief already carries.
    for line in section.splitlines():
        if re.match(r"^#{1,6} ", line):
            if not re.match(r"^### R\d+\.", line):
                problems.append(
                    "docs/kimi-plugin-brief.md carries an "
                    "unnumbered heading %r inside the rules "
                    "section, so it escapes the derivation "
                    "check" % line.strip()
                )
    tail = raw[raw.find(RULES_HEADING):]
    for heading in re.findall(r"(?m)^#{1,6} (.+)$", tail):
        if heading == "The Kimi rules":
            continue
        if re.match(r"R\d+\.", heading):
            continue
        if heading in POST_RULES_HEADINGS:
            continue
        problems.append(
            "docs/kimi-plugin-brief.md carries a heading %r "
            "outside the R numbered rules, so it escapes the "
            "derivation check" % heading
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
        paragraphs = [
            para.strip()
            for para in re.split(r"\n\s*\n", block)
            if para.strip()
        ]
        note_index = None
        for index, para in enumerate(paragraphs):
            if "Derives from" in para:
                note_index = index
                break
        if note_index is None:
            continue
        # R29-RT-07. A sentence appended to the note paragraph
        # itself inherits the note for free, so every sentence
        # after the first in that paragraph must itself be a
        # derivation sentence or the Decision 4 binding
        # sentence the shipped R6 note carries.
        note_para = re.sub(r"\s+", " ", paragraphs[note_index])
        note_sentences = re.split(
            r"(?<=[.!?])\s+", note_para
        )
        for later in note_sentences[1:]:
            low = later.strip().lower()
            if low.startswith("derives from"):
                continue
            if low.startswith("decision 4 binds"):
                continue
            problems.append(
                "kimi rule %s carries a sentence after its "
                "derivation note that states no derivation, "
                "so a planted rule sentence would escape the "
                "check" % name
            )
            break
        # R29-RT-07. A sentence planted inside an existing
        # content paragraph is invisible to every heading and
        # paragraph check, so the content sentence count per
        # shipped rule is pinned. A new rule has no count and
        # is judged by its derivation note instead.
        if name in RULE_CONTENT_SENTENCES:
            content_paras = paragraphs[1:note_index]
            count = 0
            for para in content_paras:
                flat_para = re.sub(r"\s+", " ", para)
                count += len(
                    re.split(r"(?<=[.!?])\s+", flat_para)
                )
            if count != RULE_CONTENT_SENTENCES[name]:
                problems.append(
                    "kimi rule %s carries %d content sentences, "
                    "not the pinned %d, so a planted sentence "
                    "inside its content would escape the check"
                    % (name, count, RULE_CONTENT_SENTENCES[name])
                )
        content_text = " ".join(paragraphs[1:note_index])
        note = flat.split("Derives from", 1)[1]
        if not deliberate_source(note, rule=name, content=content_text):
            problems.append(
                "kimi rule %s names no canonical skill section, "
                "primary citation, or binding decision in its "
                "derivation note" % name
            )
        # R28-RT-06. A bare paragraph planted after a rule's
        # derivation note sits inside that rule's block and
        # inherits its note, so any paragraph after the note
        # paragraph is a rule shaped paragraph outside a rule.
        if note_index + 1 < len(paragraphs):
            problems.append(
                "kimi rule %s carries a paragraph after "
                "its derivation note, so a planted rule "
                "sentence would escape the check" % name
            )
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
    problems = []
    # R29-RT-16. A decision heading and a note saying no such
    # decision exists must not both pass, and an empty heading
    # must not pass on its own. The two conditions are a
    # coherence check, not two presence checks.
    parts = re.split(r"(?m)^## (\d+)\.", raw)
    bodies = {}
    for index in range(1, len(parts), 2):
        bodies[parts[index]] = parts[index + 1]
    for number, body in bodies.items():
        rest = re.split(r"(?m)^## ", body, maxsplit=1)[0]
        if not rest.strip():
            problems.append(
                "docs/decisions.md carries an empty decision %s "
                "heading, so the record claims a decision it "
                "does not state" % number
            )
    if "21" in bodies and NUMBERING_NOTE in raw:
        problems.append(
            "docs/decisions.md both carries a decision 21 "
            "heading and says no decision 21 exists, so the "
            "numbering note and the headings disagree"
        )
    if "21" not in bodies and NUMBERING_NOTE not in raw:
        problems.append(
            "docs/decisions.md jumps from decision 20 to decision "
            "22 with no explanation for the missing decision 21"
        )
    return problems


def hook_problems(root=None):
    """No sentence may claim blocking on the four hook events.

    The primary Kimi hooks page lists TurnStarted,
    UserPromptQueued, TaskStarted, and SessionHeartbeat as
    observation only, with the blocking column empty for every
    one of them, and states that only PreToolUse, Stop, and
    UserPromptSubmit have return values that affect the main
    flow. A planted sentence that wires one of the four events
    through a blocking check, or says a hook check on them
    stops or blocks or gates a turn, states a contract the
    host cannot honor and must fail the gate. A sentence that
    negates the blocking verb states the true posture and is
    skipped. Calling the events notification only also fails,
    because Notification is a separate event on the same page
    and the four are observation only, not notifications.
    """
    root = ROOT if root is None else root
    clauses = _brief_clauses(root)
    if clauses is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    problems = []
    blocking_problem = (
        "a kimi rule claims blocking on one of the four "
        "observation only hook events, which the primary "
        "hooks page denies"
    )
    stop_verb = re.compile(
        r"\b(stops?|blocks?|halts?|prevents?|gates?)\b"
        r"\s+(the\s+|a\s+|each\s+|every\s+)?"
        r"(turn|session|main flow|operation)\b"
    )
    event_names = tuple(name.lower() for name in HOOK_EVENTS)
    for clause in clauses:
        if "notification only" in clause:
            problems.append(
                "a kimi rule calls the four hook events "
                "notification only, which mislabels the "
                "observation only events the primary hooks "
                "page lists"
            )
            break
        if "blocking check" in clause or "blocking posture" in clause:
            problems.append(blocking_problem)
            break
        subject = (
            "hook" in clause or "check" in clause
            or "event" in clause or "four" in clause
            or any(name in clause for name in event_names)
        )
        if re.search(r"\bblockable\b", clause) and subject:
            problems.append(blocking_problem)
            break
        # The word blocking itself, used of a hook, a check,
        # or one of the four events, claims the posture
        # however the sentence is built, unless the clause
        # negates it or names the blocking events list the
        # brief pins for the three other events.
        block_word = re.search(r"\bblocking\b", clause)
        if block_word and subject:
            before = clause[:block_word.start()]
            if not re.search(
                r"\b(no|not|never|cannot|can't|non)\b", before
            ) and "pretooluse" not in clause:
                problems.append(blocking_problem)
                break
        match = stop_verb.search(clause)
        if match and subject:
            before = clause[:match.start()]
            if not re.search(
                r"\b(no|not|never|cannot|can't)\b", before
            ):
                problems.append(blocking_problem)
                break
        if re.search(
            r"\bturn (is|was) (gated|blocked|stopped|halted)\b",
            clause,
        ) and subject:
            problems.append(blocking_problem)
            break
        if re.search(r"\bgated by a (hook|check)\b", clause):
            problems.append(blocking_problem)
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
    clauses = _brief_clauses(root)
    if clauses is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    problems = []
    # R29-RT-02 and R29-RT-12. The precedence is an ordering
    # claim, not a verb list: any clause that puts the plugin
    # above the user, the user below the plugin, or the
    # collision resolving to the plugin in any noun form
    # states it. The brief's own sentences put the plugin
    # below the user, or outranking only the built in agents,
    # and are skipped on those shapes.
    ordering = re.compile(
        r"\bplugin\b.{0,60}\b(wins|win|outranks|outrank"
        r"|prevails|prevail|overrides|override|favours"
        r"|favors|favour|favor|takes precedence"
        r"|takes priority|is selected|is chosen"
        r"|is preferred|rank above|ranks above)\b"
    )
    for clause in clauses:
        if "win over the plugin" in clause:
            continue
        match = ordering.search(clause)
        if match:
            if re.search(
                r"outranks? only the built in", clause
            ):
                pass
            elif not _neg_before(clause, match.start()):
                problems.append(
                    "a kimi rule lets the plugin provided agent "
                    "win a name collision, which the precedence "
                    "rule forbids"
                )
                break
            else:
                continue
        if re.search(
            r"\b(resolves to|resolving to|resolution)\b"
            r".{0,40}\bplugin\b",
            clause,
        ):
            problems.append(
                "a kimi rule lets the plugin provided agent win "
                "a name collision, which the precedence rule "
                "forbids"
            )
            break
        if re.search(
            r"\bplugin (copy|agent)\b.{0,40}\bis the one that "
            r"(runs|executes)\b",
            clause,
        ):
            problems.append(
                "a kimi rule lets the plugin provided agent win "
                "a name collision, which the precedence rule "
                "forbids"
            )
            break
        # R32-RT-04. Precedence stated as a loser, where the
        # agent file agent is not the one that runs in a
        # collision, states the same plugin win without any
        # winning verb, because only the plugin agent is
        # left to run.
        if re.search(
            r"\bis not the one that (runs|executes)\b", clause
        ) and (
            "collision" in clause
            or re.search(
                r"\b(agent-file|agent file|user|project|extra)\b",
                clause,
            )
        ):
            problems.append(
                "a kimi rule lets the plugin provided agent win "
                "a name collision, which the precedence rule "
                "forbids"
            )
            break
        # R31-RT-02. A plugin win stated as a default or as
        # an agent file loss states the same ordering claim
        # without any winning verb. A plugin agent that is
        # not the default is a correct restatement and is
        # skipped.
        if re.search(
            r"\bplugin (agent|copy)?\b.{0,40}\bis the default\b",
            clause,
        ) and "not the default" not in clause:
            problems.append(
                "a kimi rule lets the plugin provided agent win "
                "a name collision, which the precedence rule "
                "forbids"
            )
            break
        if re.search(
            r"\b(user|agent-file|agent file|project|extra)\b"
            r".{0,40}\b(loses|loses to|defers?|defer"
            r"|yields?|bows?)\b.{0,30}\bplugin\b",
            clause,
        ):
            problems.append(
                "a kimi rule lets the plugin provided agent win "
                "a name collision, which the precedence rule "
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
    problems = []
    # R29-RT-03 and R29-RT-12. Bare name acceptance is a
    # meaning claim across number, synonym, and word order:
    # bare names in the plural, unqualified names, short
    # names, names alone, and a qualification requirement
    # being absent all state it. Negation is judged per
    # segment, so a sentence that negates the bare name in
    # one clause and accepts it in the next still fails.
    bare = re.compile(
        r"\bbare (name|names|skill name|skill names)\b"
    )
    acceptance = re.compile(
        r"\b(works|work|is accepted|accepted|resolves|resolve"
        r"|is sufficient|is allowed|is enough)\b"
    )
    for sentence in _sentences(raw):
        segments = _clauses(sentence)
        # R38-RT-04. Two clauses joined by the word yet with
        # no comma are two clauses, the same joint the plain
        # and form makes, so the bare name reading cuts the
        # segment there too. The adverb form not yet is no
        # joint, so a segment ending in the word not keeps
        # its yet.
        split_segments = []
        for segment in segments:
            pieces = re.split(r",\s*yet\s+|\s+yet\s+", segment)
            merged = [pieces[0]]
            for piece in pieces[1:]:
                if merged[-1].rstrip().endswith(" not"):
                    merged[-1] = merged[-1] + " yet " + piece
                else:
                    merged.append(piece)
            split_segments.extend(merged)
        segments = split_segments
        earlier_bare = False
        hit = False
        for segment in segments:
            if re.search(
                r"\b(unqualified names?|short names?)\b"
                r".{0,40}\b(works|work|accepted|accept|resolves?"
                r"|sufficient|allowed|enough)\b",
                segment,
            ):
                match = re.search(
                    r"\b(works|work|accepted|accept|resolves?"
                    r"|sufficient|allowed|enough)\b",
                    segment,
                )
                if not _neg_before(segment, match.start()):
                    hit = True
            if re.search(
                r"\bqualification is (optional|not required)\b"
                r"|\bno qualification (is )?required\b"
                r"|\bqualified name is optional\b",
                segment,
            ):
                hit = True
            if "name alone" in segment and (
                "call" in segment or "invok" in segment
            ):
                hit = True
            # R31-RT-03. Bare name acceptance stated as a
            # short name answered to, or as just its skill
            # name being fine, states the same acceptance
            # without the bare name noun.
            if re.search(
                r"\banswer\w*\b.{0,30}\b(short|just|bare|plain) "
                r"(name|names)\b",
                segment,
            ):
                hit = True
            # R32-RT-04. Bare name acceptance stated as a
            # plain name answered to states the same
            # acceptance without the bare name noun.
            if re.search(
                r"\bplain names?\b", segment
            ) and re.search(
                r"\b(answer\w*|respond\w*)\b", segment
            ):
                hit = True
            if re.search(
                r"\bjust (its|the) (skill )?names?\b"
                r".{0,30}\b(fine|works?|allowed|accepted"
                r"|sufficient|enough)\b",
                segment,
            ):
                hit = True
            if re.search(
                r"\binvoke (a plugin skill )?by the bare name\b"
                r"|\binvoking (a plugin skill )?by the bare name\b"
                r"|\bbare name invocation is (allowed|accepted)\b",
                segment,
            ):
                match = re.search(
                    r"\bby the bare name\b|\binvocation is\b",
                    segment,
                )
                if not _neg_before(segment, match.start()):
                    hit = True
            if "by its bare skill name" in segment:
                hit = True
            # R36-RT-02. Bare name acceptance stated with the
            # bare name as the subject of an invocation verb
            # states the same acceptance. The shipped record
            # puts the verb before the bare name and then
            # negates the working of it, so this branch needs
            # the bare name first and no no longer after it.
            # R37-RT-05. Both verb branches now read the
            # whole segment, because the round 37 review
            # stated the acceptance with filler between the
            # bare name and the invocation verb, past the
            # measured reach of each branch. The bare name
            # and its verb in one segment state the claim
            # however much filler stands between them.
            invoke_match = re.search(
                r"\bbare (skill )?names?\b[^.]*"
                r"\binvok\w*\b",
                segment,
            )
            if invoke_match and "no longer" not in segment:
                verb = re.search(r"\binvok\w*\b", segment)
                # R37F-RT-05. The negation guard reads the
                # verb's own clause of the segment. A
                # negation before a coordinating and or but
                # negates that earlier clause, not the
                # invocation this clause states.
                prefix = segment[:verb.start()]
                boundary = 0
                # Confirmation repair. The clause boundary
                # is the coordinating joint itself, with or
                # without its comma, because two clauses
                # joined by a plain and are still two
                # clauses and a negation in the first does
                # not reach the invocation in the second.
                for joint in re.finditer(
                    r",\s+(?:and|but|yet)\s+|\s+(?:and|yet)\s+",
                    prefix,
                ):
                    boundary = joint.end()
                if not _neg_before(
                    segment[boundary:], verb.start() - boundary
                ):
                    hit = True
            # Gate review repair. Bare name acceptance
            # stated with a response verb before the bare
            # name, plugin skills responding to a bare name,
            # states the same acceptance with the verb on
            # the other side of the name.
            respond_match = re.search(
                r"\b(respond\w*|answer\w*)\b[^.]*"
                r"\bbare (skill )?names?\b",
                segment,
            )
            if respond_match and not _neg_before(
                segment, respond_match.start()
            ):
                hit = True
            has_bare = bool(bare.search(segment))
            for match in acceptance.finditer(segment):
                if has_bare and not _neg_before(
                    segment, match.start()
                ):
                    hit = True
                if (
                    not has_bare
                    and earlier_bare
                    and "plugin skill" in segment
                    and not _neg_before(segment, match.start())
                ):
                    hit = True
            if has_bare:
                earlier_bare = True
        if hit:
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
    problems = []
    # R29-RT-04 and R29-RT-12. The working directory claim is
    # a location claim, not two noun phrases: any sentence
    # that places hooks in a server directory, a server
    # working directory, a startup directory, or a launch
    # directory states it, in any case. A location preceded
    # by a negation is the brief's own distinction and is
    # skipped, and a plugin hook said to run in the session
    # project directory contradicts the plugin root scope.
    location = re.compile(
        r"\bserver\b.{0,50}\bdirectory\b"
        r"|\bdirectory\b.{0,50}\bserver was (started|launched)\b"
    )
    # R31-RT-04. A server location stated as a process cwd or
    # as a checkout directory of the server states the same
    # location claim without the server directory word pair.
    cwd_location = re.compile(
        r"\bserver\b.{0,30}\bcwd\b"
        r"|\bcwd\b.{0,30}\bserver\b"
        r"|\bdirectory\b.{0,30}\bof the server\b"
    )
    for sentence in _sentences(raw):
        for clause in _clauses(sentence):
            match = location.search(clause)
            if match:
                negated = _neg_before(clause, match.start())
                negated = negated or bool(
                    re.search(
                        r"\b(not|never)\b",
                        clause[match.start():match.end()],
                    )
                )
                if not negated:
                    problems.append(
                        "a kimi rule puts hooks in the server "
                        "start directory, which the working "
                        "directory rule forbids"
                    )
                    break
            cwd_match = cwd_location.search(clause)
            if cwd_match and "hook" in clause:
                negated = _neg_before(clause, cwd_match.start())
                negated = negated or bool(
                    re.search(
                        r"\b(not|never)\b",
                        clause[cwd_match.start():cwd_match.end()],
                    )
                )
                if not negated:
                    problems.append(
                        "a kimi rule puts hooks in the server "
                        "start directory, which the working "
                        "directory rule forbids"
                    )
                    break
            if re.search(
                r"\bplugin hooks?\b.{0,40}\bsession\b"
                r".{0,30}\bproject directory\b",
                clause,
            ):
                if not _neg_before(clause, 0):
                    problems.append(
                        "a kimi rule puts hooks in the server "
                        "start directory, which the working "
                        "directory rule forbids"
                    )
                    break
        if problems:
            break
    return problems


_WORD_ONES = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19,
}

_WORD_TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}


def _word_number_before(clause, index):
    """The spelled number ending just before index.

    Returns the value and the start of the number phrase,
    or None. A tens word with a ones word after it reads
    as the two together, so sixty four reads as 64.
    """
    tokens = clause[:index].split()
    if not tokens:
        return None
    last = tokens[-1]
    if last in _WORD_TENS:
        start = index - len(last)
        return _WORD_TENS[last], start
    if last in _WORD_ONES:
        start = index - len(last)
        if len(tokens) > 1 and tokens[-2] in _WORD_TENS:
            start = index - len(last) - len(tokens[-2]) - 1
            return _WORD_TENS[tokens[-2]] + _WORD_ONES[last], start
        return _WORD_ONES[last], start
    return None


def _clause_figures(clause):
    """Every size figure in a clause as a KB value.

    Each entry is the value in KB, the start, and the end.
    Byte figures count only as whole kilobytes, since the
    census below judges the rest. Spelled figures count
    the same as digit figures.
    """
    figures = []
    covered = []
    for match in re.finditer(
        r"(?<![\w-])(\d+)\s*(?:kb|kib)\b", clause
    ):
        figures.append(
            (int(match.group(1)), match.start(), match.end())
        )
        covered.append((match.start(), match.end()))
    for match in re.finditer(
        r"(?<![\w-])(\d[\d,]*)\s*bytes\b", clause
    ):
        value = int(match.group(1).replace(",", ""))
        if value % 1024 == 0:
            figures.append(
                (value // 1024, match.start(), match.end())
            )
            covered.append((match.start(), match.end()))
    for match in re.finditer(r"\b(?:kb|kib)\b", clause):
        if any(
            start <= match.start() < end for start, end in covered
        ):
            continue
        spelled = _word_number_before(clause, match.start())
        if spelled is not None:
            value, start = spelled
            figures.append((value, start, match.end()))
    return figures


def _swap_problem(sentence):
    """Whether a sentence swaps the per field and total figures.

    Every figure in the sentence binds to its nearest scope
    word in the same sentence, and a scope word may bind
    more than one figure. A figure bound to the field scope
    must be 32 and a figure bound to the total scope must
    be 64.

    R37-RT-04. The reading is the whole sentence, not one
    clause, and the binding carries no gap limit and no one
    figure per scope word rule. The clause reading let a
    swap hide behind a semicolon clause holding the figure
    and no scope word, behind a second figure the single
    field word could not also bind, and behind filler that
    pushed the figure past the gap limit, and each shape
    stated the same swap.

    R37F-RT-04 and R37F-RT-06. Nearest is not the whole
    binding rule. A scope word standing after the figure
    across an of, 64 KB of total content, names the
    content the figure measures rather than the scope of
    the limit, so it binds only when no other scope word
    stands in the sentence. And a scope word in the
    figure's own comma clause binds ahead of a nearer
    scope word across the comma, because the comma clause
    is where the sentence states that figure's limit.
    The binding ranks scope words by those two rules
    first and by gap last.
    """
    if not re.search(
        r"systemprompt|prompt|field|limit|total|budget", sentence
    ):
        return None
    figures = _clause_figures(sentence)
    if not figures:
        return None
    markers = []
    for match in re.finditer(r"\bfields?\b", sentence):
        markers.append(("field", match.start(), match.end()))
    for match in re.finditer(
        r"\b(total|overall|combined|aggregate|budget)\b", sentence
    ):
        markers.append(("total", match.start(), match.end()))
    if not markers:
        return None
    # Confirmation repair. A paired statement, the field
    # figure standing beside its own field word, is the
    # one form where an after figure total word binds on
    # its own statement rather than on the field subject.
    paired = any(
        value2 == 32
        and any(
            other == "field"
            and max(ostart - fend2, start2 - oend, 0) <= 30
            for other, ostart, oend in markers
        )
        for value2, start2, fend2 in figures
    )
    for value, fstart, fend in figures:
        # A field scope word standing before the figure is
        # the sentence subject for the figure, so an after
        # figure total word that a later field word in the
        # same sentence restates as the per field scope is
        # a decoy in the same family as the of forms.
        field_before = any(
            name == "field" and mend <= fstart
            for name, mstart, mend in markers
        )
        scope = None
        best_key = None
        for name, mstart, mend in markers:
            if mstart >= fend:
                between = sentence[fend:mstart]
                decoy = 1 if re.search(r"\bof\b", between) else 0
                # R37C-RT-03. A total word right after the
                # figure whose own of phrase names field
                # content, 64 KB total of all field content,
                # measures that field content, so it ranks
                # as a decoy the same way.
                if name == "total" and re.search(
                    r"\bof\b[^.]*\bfields?\b", sentence[mend:]
                ):
                    decoy = 1
                # Spec confirmation candidate. A total word
                # after the figure in a sentence whose field
                # subject stands before the figure and whose
                # per field restatement stands right after
                # the total word, 64 KB in total content per
                # field, measures the field content the
                # subject names, so it ranks as a decoy too.
                # The restatement reach is a measured bound.
                # The plant restates at a gap of 13 and the
                # shipped summary sentence names its next
                # field topic at a gap of 25, so the bound
                # stands at 20 and a restatement past it
                # escapes by design.
                if (
                    name == "total"
                    and field_before
                    and any(
                        other == "field"
                        and 0 <= ostart - mend <= 20
                        for other, ostart, oend in markers
                    )
                ):
                    decoy = 1
                # R37C-RT-03. The same content naming with
                # no of and no restatement, 64 KB total
                # content under a field subject, still
                # names the content the field holds, so the
                # total word ranks as a decoy whenever the
                # sentence carries no paired field figure
                # statement of its own.
                if (
                    name == "total"
                    and field_before
                    and not paired
                ):
                    decoy = 1
            else:
                between = sentence[mend:fstart]
                decoy = 0
            crossed = (
                1 if ("," in between or ";" in between) else 0
            )
            gap = max(mstart - fend, fstart - mend, 0)
            key = (decoy, crossed, gap)
            if best_key is None or key < best_key:
                best_key = key
                scope = name
        if scope is None:
            continue
        if _neg_before(sentence, fstart, 15):
            continue
        if scope == "field" and value != 32:
            return (
                "a kimi rule states a per field limit of "
                "%s KB, other than the pinned 32KB per "
                "field figure" % value
            )
        if scope == "total" and value != 64:
            return (
                "a kimi rule states a total limit of %s "
                "KB, other than the pinned 64KB total "
                "figure" % value
            )
    return None


def limits_problems(root=None):
    """R28-RT-05. No sentence may state a size limit outside
    the pinned pair.

    The pin fragments prove the 32KB and 64KB figures are
    stated, but an added sentence stating a different limit
    passes while the pins stay in place. Any kilobyte figure
    other than 32 or 64, and any megabyte figure at all, is
    a limit outside the pinned pair. A swapped figure, the
    total figure bound to the per field scope or the per
    field figure bound to the total scope, is the same
    violation stated with both figures inside the allowed
    pair.
    """
    root = ROOT if root is None else root
    clauses = _brief_clauses(root)
    if clauses is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    problems = []
    # R36-RT-02, repaired at the gate review. The per field
    # figure and the total figure swapped state the same
    # violation with both figures inside the allowed pair,
    # so the figure census below passes them. The first
    # repair bound a figure to a scope through a short list
    # of limit phrases in the digit kilobyte form only, and
    # the gate review restated the swap with other verbs,
    # with spelled figures, and in bytes and KiB, and each
    # restatement passed. The binding now reads scope
    # itself. Every size figure in a limit clause, in
    # digits or in words, in KB or KiB or bytes, binds to
    # the nearest scope word in the clause, field words to
    # the per field scope and total words to the total
    # scope, closest pairs first so one scope word binds
    # one figure. A figure bound to the field scope must
    # be the 32 figure and a figure bound to the total
    # scope must be the 64 figure. The derivation note
    # clause that states the 32 per field limit and the 64
    # prompt build budget in one breath binds its 32 to
    # the field word beside it and its 64 to the budget
    # word beside it, so it passes.
    # R37-RT-04. The swap reading moved from the clause to
    # the sentence, and the binding dropped its one figure
    # per scope word rule and its gap limit. The round 37
    # review restated the swap behind a semicolon clause
    # holding no scope word, as a second figure the single
    # field word could not also bind, and past the gap
    # limit behind filler, and each shape passed the clause
    # reading. Every figure in a sentence now binds to its
    # nearest scope word in that sentence, and a scope word
    # may bind more than one figure.
    sentences = _brief_sentences(root)
    if sentences is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    for sentence in sentences:
        swap = _swap_problem(sentence)
        if swap is not None:
            problems.append(swap)
            break
    # R29-RT-05 and R29-RT-12. A limit stated in bytes, in
    # KiB, in words, or as lifted or unlimited is still a
    # limit outside the pinned pair, and a lowercased
    # figure matches the same pattern as an uppercased one.
    for clause in clauses:
        hit = None
        for match in re.finditer(r"(\d+)\s*kb\b", clause):
            if int(match.group(1)) not in (32, 64):
                if not _neg_before(clause, match.start(), 15):
                    hit = (
                        "a kimi rule states a size limit of %s "
                        "KB, other than the pinned 32KB and "
                        "64KB limits" % match.group(1)
                    )
        if hit is None and re.search(r"\d+\s*mb\b", clause):
            match = re.search(r"\d+\s*mb\b", clause)
            if not _neg_before(clause, match.start(), 15):
                hit = (
                    "a kimi rule states a size limit in "
                    "megabytes, other than the pinned "
                    "32KB and 64KB limits"
                )
        if hit is None:
            match = re.search(
                r"(?<![\w-])(\d[\d,]*)\s*bytes\b", clause
            )
            if match:
                value = int(match.group(1).replace(",", ""))
                if value not in (32768, 65536):
                    if not _neg_before(clause, match.start(), 15):
                        hit = (
                            "a kimi rule states a size limit "
                            "of %s bytes, other than the "
                            "pinned 32KB and 64KB limits"
                            % match.group(1)
                        )
        if hit is None:
            match = re.search(r"(\d+)\s*kib\b", clause)
            if match and int(match.group(1)) not in (32, 64):
                if not _neg_before(clause, match.start(), 15):
                    hit = (
                        "a kimi rule states a size limit of "
                        "%s KiB, other than the pinned "
                        "32KB and 64KB limits"
                        % match.group(1)
                    )
        if hit is None and "kilobyte" in clause:
            spelled = (
                "thirty" in clause and "two" in clause
            ) or (
                "sixty" in clause and "four" in clause
            )
            if not spelled and (
                "systemprompt" in clause or "prompt" in clause
                or "field" in clause or "limit" in clause
            ):
                kilo_at = clause.find("kilobyte")
                if not _neg_before(clause, kilo_at, 50):
                    hit = (
                        "a kimi rule states a size limit in "
                        "words, other than the pinned 32KB "
                        "and 64KB limits"
                    )
        if hit is None and re.search(
            r"\b(unlimited|no limit|without a limit"
            r"|without any limit)\b",
            clause,
        ):
            if (
                "systemprompt" in clause or "prompt" in clause
                or "field" in clause or "size" in clause
            ):
                if not re.search(
                    r"\b(not|never) unlimited\b", clause
                ) and not re.search(
                    r"\b(not|never) (have )?no limit\b", clause
                ):
                    hit = (
                        "a kimi rule states a size limit with "
                        "no limit, which inflates the pinned "
                        "32KB and 64KB limits"
                    )
        if hit is None and re.search(
            r"\blimit(s)? (is|are) lifted\b", clause
        ):
            if not re.search(r"\b(not|never) lifted\b", clause):
                hit = (
                    "a kimi rule states a size limit that is "
                    "lifted, which inflates the pinned 32KB "
                    "and 64KB limits"
                )
        if hit is not None:
            problems.append(hit)
            break
    return problems


def persona_problems(root=None):
    """R28-RT-05. No sentence may run print mode CI without
    a persona.

    The persona pin proves the reviewer persona is stated,
    but an added sentence running CI without any persona
    passes while the pin stays in place.
    """
    root = ROOT if root is None else root
    clauses = _brief_clauses(root)
    if clauses is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    # R29-RT-05, R29-RT-12, and R29-RT-15. A different
    # persona, a persona-less run, a skipped persona step, or
    # no agent selected all contradict the reviewer persona
    # pin, and a capitalised keyword matches too. A clause
    # that negates its own persona absence, such as a run
    # that does not run without a persona, is a correct
    # restatement and is skipped.
    patterns = (
        r"\bwithout (any |a |an )?persona\b",
        r"\bno persona\b",
        r"\bpersona[-\s]?(free|less)\b",
        r"\bdefault persona\b",
        r"\bskips? (the )?persona (step)?\b",
        r"\bpersona step (is )?skipped\b",
        r"\bno agent (selected|chosen)?\b",
        r"\bwithout (an )?agent\b",
    )
    for clause in clauses:
        for pattern in patterns:
            match = re.search(pattern, clause)
            if match and not _neg_before(clause, match.start()):
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
    clauses = _brief_clauses(root)
    if clauses is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    # R29-RT-05 and R29-RT-12. An unsupported field taking
    # effect states the forbidden claim in either word order,
    # and so does a field beyond the supported set being
    # executed, so the clause is judged by the pair of tokens
    # it carries, not by their order. A clause that negates
    # its own effect verb is a correct restatement.
    effect = re.compile(
        r"\b(honour\w*|honor\w*|execut\w*|appl\w*|enforc\w*"
        r"|respect\w*|used|takes? effect|in effect"
        r"|passed through|pass through|forward\w*)\b"
    )
    for clause in clauses:
        unsupported = (
            "unsupported" in clause
            or "beyond the supported set" in clause
            or "outside the supported set" in clause
        )
        if not unsupported:
            continue
        match = effect.search(clause)
        if match and not _neg_before(clause, match.start()):
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
    clauses = _brief_clauses(root)
    if clauses is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    # R29-RT-05 and R29-RT-15. A source edit taking effect, a
    # CLI running from the source, a live pickup, a hot
    # reload, or an edit landing with no reinstall all state
    # the same forbidden claim, with or without the words
    # immediately or directory. A clause that negates its own
    # take effect verb, such as an edit that does not take
    # effect immediately, is a correct restatement.
    problem = (
        "a kimi rule lets a source edit take effect "
        "without a reinstall, which the managed copy "
        "rule forbids"
    )
    for clause in clauses:
        has_source = (
            "source" in clause or "managed copy" in clause
        )
        if not has_source:
            continue
        negated_take = bool(
            re.search(
                r"\b(does not|do not|never)\b.{0,30}"
                r"\btakes? effect\b",
                clause,
            )
        )
        if not negated_take and re.search(
            r"\btakes? effect\b", clause
        ):
            return [problem]
        if re.search(r"\bruns? from the source\b", clause):
            return [problem]
        # R31-RT-06. A managed copy refresh from the source
        # states a source effect with no takes effect verb
        # and no reinstall word.
        if re.search(r"\brefresh\w*\b", clause):
            return [problem]
        if re.search(
            r"\b(picked up|hot[-\s]?reloads?|live reloads?)\b",
            clause,
        ):
            return [problem]
        if re.search(
            r"\bwithout (a )?reinstall\b"
            r"|\bwithout reinstalling\b"
            r"|\bno reinstall\b",
            clause,
        ):
            return [problem]
    return []


def scope_problems(root=None):
    """R28-RT-05. No sentence may install plugins per project.

    The per user pin proves the scope is stated, but an
    added sentence installing per project passes while the
    pin stays in place.
    """
    root = ROOT if root is None else root
    clauses = _brief_clauses(root)
    if clauses is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    # R29-RT-05, R29-RT-12, and R29-RT-15. A project scope
    # claim in any of its shapes, a single project, each
    # project, a project level scope, or a per workspace
    # install, states the same forbidden claim. The brief's
    # own sentence, that project level scope is not yet
    # supported, is skipped, and a clause that negates its
    # own scope claim, such as plugins that do not install
    # per project, is a correct restatement.
    problem = (
        "a kimi rule installs plugins per project, "
        "which the per user scope rule forbids"
    )
    patterns = (
        r"\binstall\w*.{0,30}\b(per project|per workspace"
        r"|each project|for each project)\b",
        r"\bscoped? (to|at|for) (a )?(single|one|each) project\b",
        r"\bscope\b.{0,30}\bproject level\b",
        r"\bproject level\b.{0,30}\bscope\b",
        r"\bappl\w* to (a )?(single|one) project\b",
        r"\bappl\w*.{0,20}\bper workspace\b",
        r"\bone project only\b",
        r"\bproject (level )?scope is (supported|available)\b",
    )
    for clause in clauses:
        if "not yet supported" in clause:
            continue
        for pattern in patterns:
            match = re.search(pattern, clause)
            if match and not _neg_before(clause, match.start()):
                return [problem]
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
    # R29-RT-09. Word presence is not meaning: a fixture
    # that says the plugin wins still contains the word wins,
    # so each fixture must state its own side's outcome in a
    # sentence whose subject and outcome agree, and neither
    # fixture may carry a hostile instruction line.
    hostile = re.compile(
        r"ignore (all )?prior instructions"
        r"|ignore (all )?previous instructions"
        r"|disregard (all )?(prior|previous) instructions"
        r"|approve every packet"
    )
    for label, text in (
        ("user", user_text),
        ("plugin", plugin_text),
    ):
        if hostile.search(text.lower()):
            problems.append(
                "the %s collision fixture carries a hostile "
                "instruction, so the fixture pair no longer "
                "proves the precedence" % label
            )
    user_sentences = _sentences(user_text)
    # The fixture file itself supplies the subject: the user
    # fixture must carry a sentence where the win lands over
    # the plugin, and the plugin fixture one where the loss
    # lands to the user. A sentence where the plugin wins is
    # the inverted precedence even though it contains wins.
    user_win = any(
        re.search(
            r"\bwins\b.{0,40}\bplugin\b",
            sentence,
        )
        for sentence in user_sentences
    )
    user_inverted = any(
        re.search(
            r"\bplugin\b.{0,50}\bwins\b",
            sentence,
        )
        for sentence in user_sentences
    )
    if not user_win or user_inverted:
        problems.append(
            "the user collision fixture does not state the "
            "user win, so the fixture pair no longer proves "
            "the precedence"
        )
    plugin_sentences = _sentences(plugin_text)
    plugin_loss = any(
        re.search(
            r"\bloses\b.{0,40}\buser\b",
            sentence,
        )
        for sentence in plugin_sentences
    )
    plugin_inverted = any(
        re.search(
            r"\buser\b.{0,50}\bloses\b.{0,40}\bplugin\b",
            sentence,
        )
        for sentence in plugin_sentences
    )
    if not plugin_loss or plugin_inverted:
        problems.append(
            "the plugin collision fixture does not state the "
            "plugin loss, so the fixture pair no longer proves "
            "the precedence"
        )
    return problems


def autodiscovery_problems(root=None):
    """R29-RT-06 and R29-ST-01. No sentence may deny the
    agents auto discovery or say the agents field is
    ignored.

    The presence pins prove the auto discovery sentence
    and the agents field sentence exist, but an added
    sentence denying either passes while the pins stay in
    place.
    """
    root = ROOT if root is None else root
    clauses = _brief_clauses(root)
    if clauses is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    problem = (
        "a kimi rule denies the agents auto discovery, "
        "which the agents field rule forbids"
    )
    for clause in clauses:
        if "agents" not in clause:
            continue
        if re.search(
            r"\bagents? (directory|field)\b.{0,60}"
            r"\bnot (auto )?discover\w*\b",
            clause,
        ):
            return [problem]
        # R31-ST-01. A no form of discovery and a bare agents
        # subject deny auto discovery without the not form
        # the old pattern needed.
        if re.search(
            r"\bno agents? (directory|field)\b.{0,40}"
            r"\bauto discover\w*\b",
            clause,
        ):
            return [problem]
        if re.search(
            r"\bagents? are not (auto )?discover\w*\b",
            clause,
        ):
            return [problem]
        match = re.search(
            r"\bagents field\b.{0,40}"
            r"\b(ignored|disregarded|unused)\b",
            clause,
        )
        if match and "not " not in clause[:match.start()][-12:]:
            return [problem]
    return []


def builtin_override_problems(root=None):
    """R29-RT-06 and R29-ST-01. No sentence may replace a
    built in agent without an override.

    The presence pin proves the override sentence exists,
    but an added sentence dropping the override passes
    while the pin stays in place.
    """
    root = ROOT if root is None else root
    clauses = _brief_clauses(root)
    if clauses is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    patterns = (
        r"\bneeds? no override\b",
        r"\bwithout (an |the |any )?override\b",
        r"\bdoes not (need|require) an override\b",
        r"\boverride (is )?not required\b",
        r"\boverride (is )?optional\b",
        r"\bno override (flag )?needed\b",
    )
    for clause in clauses:
        if "built" not in clause or "override" not in clause:
            continue
        for pattern in patterns:
            if re.search(pattern, clause):
                return [
                    "a kimi rule replaces a built in agent "
                    "without an override, which the collision "
                    "precedence rule forbids"
                ]
    return []


def hook_events_problems(root=None):
    """R29-RT-06 and R29-ST-01. No sentence may deny the
    four hook events, their configurability, or one
    event firing.

    The hook negative forbids calling the events
    notification only, but a sentence saying one event
    never fires or that only three events exist passes
    while the pin stays in place.
    """
    root = ROOT if root is None else root
    clauses = _brief_clauses(root)
    if clauses is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    problem = (
        "a kimi rule denies the four hook events, which "
        "the hook events rule forbids"
    )
    for clause in clauses:
        # R31-ST-01 and R31-RT-06. An event denial with no
        # event noun, a does not fire form, and a fifth count
        # claim state the denial without the old pattern's
        # event word and never form, so they are judged
        # without the event requirement.
        if re.search(
            r"\b(turnstarted|userpromptqueued|taskstarted"
            r"|sessionheartbeat)\b.{0,40}"
            r"\b(never|does not|do not|not)\s+"
            r"(fires?|runs?|triggers?)\b",
            clause,
        ):
            return [problem]
        if re.search(
            r"\b(five|six|seven|5|6|7)\b.{0,30}\bhook events?\b"
            r"|\ba fifth event\b",
            clause,
        ):
            return [problem]
        if "event" not in clause:
            continue
        if re.search(
            r"\bhook events?\b.{0,60}\bnot configurable\b",
            clause,
        ):
            return [problem]
        if re.search(
            r"\bonly (three|two|one|3|2|1) hook events?\b",
            clause,
        ):
            return [problem]
        if re.search(
            r"\bconfigurable only in a different file\b",
            clause,
        ):
            return [problem]
    return []


def stayalive_problems(root=None):
    """R29-RT-06 and R29-ST-01. No sentence may say print
    mode exits after a single turn or never stays alive.

    The persona negative forbids a persona free CI run,
    but a sentence saying print mode exits after the
    first result passes while the pin stays in place.
    """
    root = ROOT if root is None else root
    clauses = _brief_clauses(root)
    if clauses is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    problem = (
        "a kimi rule says print mode exits after a single "
        "turn, which the print mode persona rule forbids"
    )
    for clause in clauses:
        if "print mode" not in clause:
            continue
        match = re.search(r"\bexits?\b", clause)
        if match and not _neg_before(clause, match.start()):
            return [problem]
        if re.search(
            r"\b(never|does not|do not) stays? alive\b",
            clause,
        ):
            return [problem]
    return []


def oversized_problems(root=None):
    """R29-RT-06. No sentence may say oversized content
    is accepted or injected.

    The limits pin proves the 32KB and 64KB sentences
    exist, but an added sentence accepting oversized
    content passes while the pins stay in place.
    """
    root = ROOT if root is None else root
    clauses = _brief_clauses(root)
    if clauses is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    for clause in clauses:
        if "oversized" not in clause:
            continue
        if re.search(
            r"\b(accepted|injected|included|used)\b",
            clause,
        ):
            return [
                "a kimi rule accepts oversized content, "
                "which the size limits rule forbids"
            ]
        if re.search(r"\bnot ignored\b", clause):
            return [
                "a kimi rule accepts oversized content, "
                "which the size limits rule forbids"
            ]
    return []


def skipped_problems(root=None):
    """R29-RT-06. No sentence may say beyond budget
    contributions are injected anyway.

    The limits pin proves the skip sentence exists, but
    an added sentence injecting beyond budget content
    passes while the pin stays in place.
    """
    root = ROOT if root is None else root
    clauses = _brief_clauses(root)
    if clauses is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    for clause in clauses:
        if "budget" not in clause:
            continue
        if re.search(r"\binjected\b", clause):
            return [
                "a kimi rule injects beyond budget "
                "contributions, which the size limits "
                "rule forbids"
            ]
        if re.search(r"\bnot skipped\b", clause):
            return [
                "a kimi rule injects beyond budget "
                "contributions, which the size limits "
                "rule forbids"
            ]
    return []


def delegation_problems(root=None):
    """R29-RT-06. No sentence may deny delegation to
    plugin agents.

    The agents pin proves the delegation sentence
    exists, but an added sentence denying delegation
    passes while the pin stays in place.
    """
    root = ROOT if root is None else root
    clauses = _brief_clauses(root)
    if clauses is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    for clause in clauses:
        if "delegat" not in clause:
            continue
        if re.search(
            r"\b(does not|do not|never) (allow|permit|support)"
            r"\b.{0,60}\bdelegat\w*\b",
            clause,
        ):
            return [
                "a kimi rule denies delegation to plugin "
                "agents, which the agents field rule "
                "forbids"
            ]
        if re.search(r"\bno delegation\b", clause):
            return [
                "a kimi rule denies delegation to plugin "
                "agents, which the agents field rule "
                "forbids"
            ]
        # R31-RT-06. A cannot delegate claim denies
        # delegation without the allow verb the old pattern
        # needed.
        if re.search(
            r"\b(cannot|can not)\b.{0,20}\bdelegat\w*\b",
            clause,
        ):
            return [
                "a kimi rule denies delegation to plugin "
                "agents, which the agents field rule "
                "forbids"
            ]
    return []


def unknownfields_problems(root=None):
    """R29-RT-06. No sentence may say unknown fields
    cause an error or are rejected.

    The collision pin proves the ignored sentence
    exists, but an added sentence erroring on unknown
    fields passes while the pin stays in place.
    """
    root = ROOT if root is None else root
    clauses = _brief_clauses(root)
    if clauses is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    for clause in clauses:
        if "unknown" not in clause or "field" not in clause:
            continue
        if re.search(
            r"\b(cause an error|error|rejected|fails?)\b",
            clause,
        ):
            return [
                "a kimi rule errors on unknown fields, "
                "which the collision precedence rule "
                "forbids"
            ]
    return []


def manifest_problems(root=None):
    """R29-RT-06. No sentence may claim a bare root
    plugin.json is valid or that only one manifest
    location exists.

    The reference layout pin proves the two locations
    exist, but an added sentence narrowing them to one
    passes while the pin stays in place.
    """
    root = ROOT if root is None else root
    clauses = _brief_clauses(root)
    if clauses is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    for clause in clauses:
        if "manifest" not in clause and "plugin.json" not in clause:
            continue
        if re.search(
            r"\bbare plugin\.json\b.{0,60}\bvalid\b",
            clause,
        ):
            return [
                "a kimi rule claims a bare root plugin.json "
                "is valid, which the reference layout rule "
                "forbids"
            ]
        if re.search(
            r"\bonly one (valid )?manifest location\b",
            clause,
        ):
            return [
                "a kimi rule claims only one manifest "
                "location exists, which the reference "
                "layout rule forbids"
            ]
        # R31-RT-06. A manifest claim that a location is
        # ignored narrows the two locations without saying
        # only one exists.
        if re.search(
            r"\b(kimi\.plugin\.json|plugin\.json)\b.{0,40}"
            r"\b(ignored|disregarded|not loaded|not read)\b",
            clause,
        ):
            return [
                "a kimi rule claims a manifest location is "
                "ignored, which the reference layout rule "
                "forbids"
            ]
    return []


def eventmeaning_problems(root=None):
    """R29-RT-06. No sentence may narrow the four events
    to session starts only.

    The events pin proves the four event names exist,
    but an added sentence observing only session starts
    passes while the pin stays in place.
    """
    root = ROOT if root is None else root
    clauses = _brief_clauses(root)
    if clauses is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    for clause in clauses:
        if "event" not in clause:
            continue
        if re.search(
            r"\b(observe|cover|track|watch)\b.{0,40}"
            r"\bonly session starts\b",
            clause,
        ):
            return [
                "a kimi rule narrows the four events to "
                "session starts, which the hook events "
                "rule forbids"
            ]
        if re.search(r"\bonly session starts\b", clause):
            return [
                "a kimi rule narrows the four events to "
                "session starts, which the hook events "
                "rule forbids"
            ]
    return []


def decision4_problems(root=None):
    """R29-RT-06. No sentence may deny that decision 4 binds.

    The presence pin proves the decision 4 sentence exists
    in the brief, but an added sentence denying it passed
    while the pin stayed in place, which left the decision
    25 universal sentence one claim short of true.
    """
    root = ROOT if root is None else root
    clauses = _brief_clauses(root)
    if clauses is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    for clause in clauses:
        if "decision 4" not in clause:
            continue
        if re.search(
            r"\b(does not|do not|never) binds?\b", clause
        ):
            return [
                "a kimi rule denies that decision 4 binds, "
                "which the decision 4 statement forbids"
            ]
    return []


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
    # R29-RT-11. Fragment presence cannot tell affirmation
    # from negation, so a record that keeps its fragments
    # and disowns them must fail on the disowning sentence.
    low = flat.lower()
    for pattern in (
        r"none of the sentences above",
        r"none of the above states",
        r"does not state the current contract",
        r"is not the current contract",
    ):
        if re.search(pattern, low):
            problems.append(
                "the Build 14 decision record disowns its own "
                "statements, so keeping its fragments states "
                "no contract"
            )
            break
    return problems


def hook_observation_verdict(event, root=None):
    """The verdict an observation check returns for one event.

    Runs the fixture observation check the way the Kimi host
    runs a hook, with the event details as JSON on stdin and
    no arguments. The check prints the event it ran and exits
    0. Returns "observed" only when the run proves it read
    the requested event from stdin and no other, and exits 0
    as an observation hook must. Any other outcome, a nonzero
    exit, a crash, or output naming another event, returns
    "unverified", because a script that prints every event
    name on every invocation proves nothing about any single
    event.
    """
    root = ROOT if root is None else root
    script = root / "tests" / "fixtures" / "kimi-hooks" / "observation_check.py"
    payload = json.dumps({
        "hook_event_name": event,
        "session_id": "session_probe",
        "client_type": "kimi_code_cli",
        "cwd": ".",
    })
    try:
        proc = subprocess.run(
            [sys.executable, str(script)],
            input=payload,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return "unverified"
    if proc.returncode != 0:
        return "unverified"
    if event not in proc.stdout:
        return "unverified"
    for other in HOOK_EVENTS:
        if other != event and other in proc.stdout:
            return "unverified"
    return "observed"


def live_hook_problems(root=None):
    """The live observation probe over the four hook events.

    Each event runs the fixture observation check the way
    the host runs it, and every one must report an observed
    verdict. A fixture that reads its event from arguments
    crashes under this invocation, and a fixture that exits
    nonzero claims an effect an observation only event
    cannot have, so both fail here.
    """
    root = ROOT if root is None else root
    problems = []
    for event in HOOK_EVENTS:
        verdict = hook_observation_verdict(event, root)
        if verdict != "observed":
            problems.append(
                "the %s hook observation check did not run "
                "as the host runs it, verdict %s"
                % (event, verdict)
            )
    return problems


def kimi_problems(root=None):
    """Every Build 14 Kimi managed plugin problem.

    R29-RT-17. The live hook probe is part of the gate,
    not a side call in main, so a caller importing this
    function runs the whole contract including the probe.
    """
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
    problems.extend(autodiscovery_problems(root))
    problems.extend(builtin_override_problems(root))
    problems.extend(hook_events_problems(root))
    problems.extend(stayalive_problems(root))
    problems.extend(oversized_problems(root))
    problems.extend(skipped_problems(root))
    problems.extend(delegation_problems(root))
    problems.extend(unknownfields_problems(root))
    problems.extend(manifest_problems(root))
    problems.extend(eventmeaning_problems(root))
    problems.extend(decision4_problems(root))
    problems.extend(fixture_content_problems(root))
    problems.extend(decision_problems(root))
    problems.extend(numbering_problems(root))
    problems.extend(live_hook_problems(root))
    return problems


def main(root=None):
    problems = kimi_problems(root)
    if problems:
        for problem in problems:
            print("check_kimi: %s" % problem, file=sys.stderr)
        return 1
    print(
        "check_kimi: the Build 14 Kimi managed plugin contract "
        "holds, with live observation checks on all four "
        "hook events"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
