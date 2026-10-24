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
    ("the hook blocking posture", "stops the turn it gates"),
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


# Claim words each shipped derivation note carries, so a note
# that names a path and a verb but never restates what the
# rule claims is still a bare citation. R29-RT-08.
NOTE_CLAIMS = {
    "R1": ("delegation", "auto discovery"),
    "R2": ("precedence", "scope order"),
    "R3": ("bare name",),
    "R4": ("project directory",),
    "R5": ("four events",),
    "R6": ("fails closed",),
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
    "R6": 4,
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
    clauses = _brief_clauses(root)
    if clauses is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    problems = []
    # R29-RT-01 and R29-RT-12. The posture is a meaning claim,
    # not a verb list: a failed check described as
    # non-blocking, tolerated, ignored, resumed, carried on,
    # or proceeding in any word order states it, and a
    # capitalised keyword states it too, because every clause
    # is lowercased first. A clause that negates its own
    # continuation verb is a correct restatement and is
    # skipped, but a failure said not to prevent, stop, block,
    # or halt a turn is itself the forbidden posture and is
    # never skipped.
    failure = re.compile(
        r"\b(failed|failing|failure|failures)\b"
        r"|\bcheck fails\b|\bhook fails\b"
    )
    continuation = re.compile(
        r"\b(proceeds|proceed|proceeding|continues|continue"
        r"|continuing|resumes|resume|resuming|carries on"
        r"|carry on|goes on|goes ahead|passes through"
        r"|pass through|allowed through|moves on"
        r"|moves forward|keeps going|advances|advance"
        r"|advancing)\b"
    )
    for clause in clauses:
        if "notification only" in clause:
            problems.append(
                "a kimi rule calls the four hook events "
                "notification only, which the blocking "
                "posture forbids"
            )
            break
        if re.search(r"\bnever (block|stop|halt)\b", clause):
            if "hook" in clause or "event" in clause or failure.search(clause):
                problems.append(
                    "a kimi rule lets a failed hook check pass "
                    "the turn through, which the blocking "
                    "posture forbids"
                )
                break
        failed = failure.search(clause)
        if failed:
            if re.search(
                r"\b(does not|do not|never)\s+(prevent|stop|block|halt)\b",
                clause,
            ):
                problems.append(
                    "a kimi rule lets a failed hook check pass "
                    "the turn through, which the blocking "
                    "posture forbids"
                )
                break
            match = continuation.search(clause)
            if match and not _neg_before(clause, match.start()):
                problems.append(
                    "a kimi rule lets a failed hook check pass "
                    "the turn through, which the blocking "
                    "posture forbids"
                )
                break
            if re.search(
                r"\b(tolerated|ignored|dismissed|overlooked"
                r"|advisory)\b",
                clause,
            ):
                problems.append(
                    "a kimi rule lets a failed hook check pass "
                    "the turn through, which the blocking "
                    "posture forbids"
                )
                break
        if re.search(r"\bnon[-\s]?blocking\b", clause):
            if "hook" in clause or "check" in clause:
                problems.append(
                    "a kimi rule lets a failed hook check pass "
                    "the turn through, which the blocking "
                    "posture forbids"
                )
                break
    # R31-RT-01. Clause splitting on but strips the hook subject
    # from a do not stop clause, and a not gated claim carries
    # no continuation verb at all, so both shapes are judged
    # at sentence level too. A hook or check subject paired
    # with a do not stop verb states the forbidden posture,
    # and a failure paired with not gated states it without
    # any verb.
    raw = read_text(root / "docs" / "kimi-plugin-brief.md")
    if raw is not None:
        for sentence in _sentences(raw):
            if ("hook" in sentence or "check" in sentence) and re.search(
                r"\b(does not|do not|never)\s+(stop|block|halt|prevent)\b",
                sentence,
            ):
                problems.append(
                    "a kimi rule lets a failed hook check pass "
                    "the turn through, which the blocking "
                    "posture forbids"
                )
                break
            if failure.search(sentence) and re.search(
                r"\bnot gated\b", sentence
            ):
                problems.append(
                    "a kimi rule lets a failed hook check pass "
                    "the turn through, which the blocking "
                    "posture forbids"
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


def limits_problems(root=None):
    """R28-RT-05. No sentence may inflate the size limits.

    The pin fragments prove the 32KB and 64KB figures are
    stated, but an added sentence stating a larger limit
    passes while the pins stay in place. Any kilobyte figure
    other than 32 or 64, and any megabyte figure at all, is
    an inflated limit.
    """
    root = ROOT if root is None else root
    clauses = _brief_clauses(root)
    if clauses is None:
        return ["docs/kimi-plugin-brief.md is missing"]
    problems = []
    # R29-RT-05 and R29-RT-12. A limit stated in bytes, in
    # KiB, in words, or as lifted or unlimited is still an
    # inflated limit, and a lowercased figure matches the
    # same pattern as an uppercased one.
    for clause in clauses:
        hit = None
        for match in re.finditer(r"(\d+)\s*kb\b", clause):
            if int(match.group(1)) not in (32, 64):
                if not _neg_before(clause, match.start(), 15):
                    hit = (
                        "a kimi rule states a size limit of %s "
                        "KB, which inflates the pinned 32KB and "
                        "64KB limits" % match.group(1)
                    )
        if hit is None and re.search(r"\d+\s*mb\b", clause):
            match = re.search(r"\d+\s*mb\b", clause)
            if not _neg_before(clause, match.start(), 15):
                hit = (
                    "a kimi rule states a size limit in "
                    "megabytes, which inflates the pinned "
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
                            "of %s bytes, which inflates the "
                            "pinned 32KB and 64KB limits"
                            % match.group(1)
                        )
        if hit is None:
            match = re.search(r"(\d+)\s*kib\b", clause)
            if match and int(match.group(1)) not in (32, 64):
                if not _neg_before(clause, match.start(), 15):
                    hit = (
                        "a kimi rule states a size limit of "
                        "%s KiB, which inflates the pinned "
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
                        "words above the pinned 32KB and 64KB "
                        "limits, which inflates the pinned "
                        "32KB and 64KB limits"
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


def hook_turn_verdict(event, mode, root=None):
    """The verdict a hook check returns for one event.

    Runs the fixture blocking check for the event. The check
    prints the event it ran and exits nonzero on a failed
    check. A nonzero exit is a blocked turn, which the Build
    14 blocking posture pins. Returns "blocked", "proceeds",
    or "unverified" when the check did not prove it ran the
    requested event and no other. A script that prints every
    event name on every invocation proves nothing about any
    single event, so its verdict is unverified.
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
    # R29-RT-14. The output must prove the requested event
    # ran and no other event did, or an echo of every event
    # name passes the probe for an event it never checked.
    for other in HOOK_EVENTS:
        if other != event and other in proc.stdout:
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
        "holds, with live blocking and pass checks on all four "
        "hook events"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
