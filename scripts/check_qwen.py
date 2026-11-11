#!/usr/bin/env python3
"""Pin the Build 15 Qwen Code marketplace presence contract.

The brief at docs/qwen-code-brief.md records the Qwen figure
basis and scope table with no single figure presented as the
Qwen figure, the wrapper exits 0 1 and 3 kept separate from
the internal verify exit 4, the Agent Plugins v1 support
matrix in full, the Qoder and scoped npm routes, the
prefixed naming rule with its cancellation exception, the
shared skills alias with its precedence, the conversion
fidelity record with runtime invocation verified for
one scoped OpenRouter shape,
the bundled CLI version from the primary releases listing,
and the conditional publication draft with no listing file
shipped. Decision 4 binds this build like every other
build. The brief documents the contract and never enforces
it on a live Qwen host, so this script pins the contract
without a Qwen client. It requires the brief to keep the
stated pins with a derivation note on every rule, and it
runs a meaning based negative check with number
normalisation and a separation guard, so a reworded
contradiction inside its families fails instead of passing
on changed wording alone. The negative check covers the
figure family, the wrapper exit family, the activation
family, the alias discovery and precedence families, the
npm scope family, the conversion family and the
publication family, which refuses a prose claim that a
listing file ships or has shipped or that the marketplace
presence is published or listed, in present or past tense
and in a heading as well as in a sentence and as a bare
status word standing in a table cell beside a marketplace
cell, with markdown emphasis inside a cell stripped before
the cell is judged, and as a status stated under a table
whose row names the marketplace or the listing or Qwen,
in a caption line
standing directly under the table whose row points at the
caption, where the caption line opens with the words
Table caption or with the word Caption and states the
status in the stands published or stands listed form or
as the bare status word, or in a standalone status line
standing directly under the table in the stands form or
as the bare status word, while a caption line standing
after an intervening prose paragraph stands outside the
reading, judged on claim
carrying sentences regardless of
guard words elsewhere in the sentence. A live presence family beside it refuses a
claim that the build is live in the Qwen marketplace. A
paraphrase outside those families stays a human review
surface.
"""

import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RULES_HEADING = "## The Qwen rules"

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

PRIMARY_CITATIONS = (
    "qwenlm.github.io/qwen-code-docs",
    "github.com/QwenLM/qwen-code/releases",
)

PINNED = (
    ("the figure conflict unresolved",
     "not resolved to one figure"),
    ("the commands page conflicting summary",
     "conflicting summary and is not used"),
    ("the Step 3A scope row",
     "Step 3A small diff roster"),
    ("the same repo task row",
     "Same repo PR reviews"),
    ("the practice range row",
     "16 to 19 in practice"),
    ("the token table basis",
     "Token efficiency table"),
    ("the roster narrative basis",
     "Roster narrative"),
    ("the wrapper exit 0",
     "The review completed whatever it decided"),
    ("the wrapper exit 1",
     "It never reached a verdict"),
    ("the wrapper exit 3",
     "It completed with REQUEST_CHANGES and fail-on request-changes set"),
    ("the internal verify exit 4",
     "Internal verify refusal at the compose floor"),
    ("the compose floor variable",
     "QWEN_REVIEW_DEADLINE_COMPOSE_FLOOR_SECONDS"),
    ("the compose floor default",
     "default 1200 and 0 disabling the gate"),
    ("the supersession pointer",
     "superseded for Build 15 purposes by the round 31 note and the round 33 note"),
    ("the native load without conversion",
     "without converting or rewriting plugin.json"),
    ("the portable runtime support",
     "supports Agent Skills plus stdio and Streamable HTTP"),
    ("the not activated list",
     "Commands, agents, hooks, client namespaces, and legacy SSE MCP are not activated"),
    ("the client namespaces not activated",
     "are client namespaces Qwen does not activate"),
    ("the portable route skill only",
     "The portable route carries the SKILL ONLY"),
    ("the Qoder manifest path",
     ".qoder-plugin/plugin.json"),
    ("the R4 Qoder install path",
     "qwen extensions install ./recognitio-qwen/qoder-input"),
    ("the Qoder activation UNVERIFIED",
     "Activation of preserved Qoder commands and agents in Qwen stays UNVERIFIED"),
    ("the Qoder conversion",
     "converts the Qoder manifest to qwen-extension.json"),
    ("the scoped only rule",
     "Only scoped packages are supported"),
    ("the registry priority CLI flag",
     "The CLI flag first"),
    ("the registry fallback",
     "then registry.npmjs.org"),
    ("the package root manifest rule",
     "at the package root"),
    ("the prefixed registration",
     "registered as extension name plus skill name"),
    ("the bare name not an alias",
     "The bare skill name is not an alias"),
    ("the disabled either spelling",
     "blocks under either spelling"),
    ("the enabled prefixed only",
     "opts in under the prefixed name only"),
    ("the cancellation exception",
     "The cancellation exception holds for one bare pair"),
    ("the defaultDisabled plus enabled pair",
     "defaultDisabled with the bare name plus enabled with the bare name cancels"),
    ("the default-off prefixed requirement",
     "still requires the prefixed name in skills.enabled"),
    ("the shared alias read",
     "reads project skills from `.agents/skills/`"),
    ("the Qwen skills wins precedence",
     "the one in `.qwen/skills/` wins"),
    ("the shadow copy check",
     "checked for a shadow copy under `.qwen/skills/recognitio`"),
    ("the skill tree only fidelity",
     "File install fidelity holds for the SKILL TREE ONLY"),
    ("the byte identical install",
     "were byte identical to the canonical skill tree"),
    ("the round 37 skill line rewrite",
     "The installed SKILL.md differs from the canonical file in exactly one line"),
    ("the round 37 rules folder rewrite",
     "read as a Claude rules file under a .qwen/rules folder"),
    ("the round 37 field drop settled",
     "the author and license fields the input manifest carried are absent from the converted file"),
    ("the round 37 mirror newline",
     "losing only its trailing newline"),
    ("the round 37 fidelity limit",
     "Skill file byte fidelity does not hold for a Qoder install of the current canonical skill text"),
    ("the round 37 install record",
     "an install record file that has no canonical counterpart"),
    ("the Qoder originSource",
     "recorded originSource as Qoder"),
    ("the AgentPlugins originSource",
     "recorded originSource as AgentPlugins"),
    ("the side shape files carried in the round 37 install",
     "Side shape files ride in as files in the round 37"),
    ("the round 33 skill tree only scope",
     "The round 33 installs carried the skill tree only"),
    ("the side shape activation limit",
     "No activation of the preserved shapes inside a Qwen session is shown"),
    ("the installer mirror of the input manifest",
     "an installer mirror of the input manifest"),
    ("the installer mirror field sets",
     "three in the round 33 input"),
    ("the runtime scoped proof",
     "Runtime invocation stands verified for one scoped shape"),
    ("the runtime proof route",
     "through the OpenRouter third party route"),
    ("the runtime proof model",
     "qwen/qwen3-coder"),
    ("the runtime proof range",
     "11 added lines"),
    ("the scoped npm UNTESTED",
     "the scoped npm route is untested"),
    ("the hidden artifact record",
     "`.claude-plugin/plugin.json` artifact"),
    ("the frontmatter without editing",
     "without editing frontmatter"),
    ("the bundled CLI line",
     "This SDK release bundles CLI version 0.26.0"),
    ("the no tag claimed",
     "so no tag is claimed for it in this brief"),
    ("the conditional draft",
     "reads as a conditional draft"),
    ("the no central submission promise",
     "promises no central Qwen marketplace submission"),
    ("the no VS Code conflation",
     "is not Build 15 publication"),
    ("the release shapes UNVERIFIED",
     "Release asset shapes beyond the introduction page stay UNVERIFIED"),
    ("the no listing file shipped",
     "No Qwen listing file ships in this round"),
    ("the version stays",
     "The repo version stays 1.3.0"),
    ("the Copilot watch note",
     "rechecked after November 16"),
    ("the decision 13 suspended",
     "Decision 13 stays in its suspended state"),
    ("the decision 4 statement",
     "Decision 4 binds this build like every other build"),
)

DECISION_NOTE_MARKER = "Round 33 note"
DECISION_NOTE_PINS = (
    "12 versus 16",
    "conflicting summary",
    "wrapper exits are 0, 1, and 3",
    "internal verify exit 4",
    "QWEN_REVIEW_DEADLINE_COMPOSE_FLOOR_SECONDS",
    "no Qwen listing file ships",
    "version stays 1.3.0",
)

CHANGELOG_PINS = (
    "The round 33 pass lands Build 15",
    "docs/qwen-code-brief.md",
    "scripts/check_qwen.py",
    "figure resolution",
    "exit table scope",
    "Qoder",
    "scoped npm",
)

NUMBER_WORDS = (
    ("nineteen", "19"),
    ("eighteen", "18"),
    ("seventeen", "17"),
    ("sixteen", "16"),
    ("fifteen", "15"),
    ("fourteen", "14"),
    ("thirteen", "13"),
    ("twelve", "12"),
    ("eleven", "11"),
    ("ten", "10"),
    ("dozen", "12"),
    ("twenty", "20"),
    ("nine", "9"),
    ("eight", "8"),
    ("seven", "7"),
    ("six", "6"),
    ("five", "5"),
    ("four", "4"),
    ("three", "3"),
    ("two", "2"),
)

# Spelled numbers from round 34 repair round two.
# The digit range runs from 2 to 29, so the spelled list now
# runs from two to twenty in single word form. A hyphenated
# twenty one through twenty nine becomes twenty plus a unit
# word after hyphen normalisation, and the twenty token
# itself is already in range, so those forms fire too.
# One stays out, because a single agent is no figure claim.

# Lines carrying one of these words are statements about the
# correct record, not plants, so the negative patterns skip
# them. The brief table rows all carry a basis word, the
# correct exit sentences carry an internal verify word, and
# the correct not activated and not supported sentences
# carry their own negation word.
GUARD_WORDS = (
    "effort table",
    "roster narrative",
    "token efficiency",
    "conflicting summary",
    "internal verify",
    "internal verifier",
    "not activated",
    "not supported",
    "only scoped",
    "no central",
    "is not build 15 publication",
)


QODER_UNVERIFIED_SHAPE = (
    "activation of preserved qoder commands and agents "
    "in qwen stays unverified"
)

# Figure adverbs from G-01 and R-01.
# Shoulder to shoulder is the R-01 idiom for side by side.
# Alongside each other is the Y-01 idiom for side by side.
# Hyphen normalisation turns side by side in hyphen form
# into the spaced form before matching, so the attributive
# spelling fires as well as the spaced spelling.
FIGURE_ADVERBS = (
    "parallel|concurrent\\w*|simultaneous\\w*|"
    "side by side|together|at once|"
    "at the same time|in tandem|shoulder to shoulder|"
    "alongside each other"
)

# Generic agent nouns from G-01 and B2.
# A noun alone is ordinary roster prose, so the noun branch
# of the figure check also needs a scope word from
# FIGURE_SCOPE in the same sentence.
FIGURE_AGENTS = "reviewers?|workers?|bots?|agents?"

# Scope words that turn a generic agent count into a
# figure claim. Large and practice cover the G-01 scope
# shapes, high effort and top effort cover the shipped
# effort shapes, and same repository and same deadline
# cover the long F-Q17 shape.
FIGURE_SCOPE = (
    "large|high effort|top effort|practice|"
    "same repository|same deadline"
)

# Wrapper nouns from G-02 and R-02.
# Bare shell is the R-02 noun. A bare shell mention alone
# does not fire, because the wrapper check also needs an
# exit or code token in the same sentence.
WRAPPER_WORDS = "wrapper|outer gate|outer shell|outer layer|shell"

# Activation verbs from G-03 and R-03.
# Power up is the R-03 verb. Turn, switch, and power also
# appear in split form with the target before the particle,
# and the split pattern in negative_problems covers that
# shape, so the immediate particle forms here are not the
# only shapes that fire. Bring online is the Y-02 verb
# in split form, with the target between the stem and
# the online particle.
ACTIVATION_VERBS = (
    "activat\\w*|enabl\\w*|turn\\w* on|switch\\w* on|power\\w* up|"
    "bring\\w* online"
)

# Verb stems for the split activation shape.
# A stem plus a target plus an on or up particle in the
# same sentence fires, which covers switches hooks on and
# turns hooks on without listing every word order.
# Bring is the Y-02 stem, and its particle is online
# rather than on or up.
ACTIVATION_PARTICLE_VERBS = "turn\\w*|switch\\w*|power\\w*|bring\\w*"

ACTIVATION_TARGETS = (
    "hooks|commands|agents|client namespaces|legacy sse"
)

# Discovery verbs from G-04 and R-04.
# Picks up is the R-04 verb, in both word orders.
# Find is the Y-03 verb, in both word orders.
DISCOVERY_VERBS = "discover\\w*|pick\\w* up|find\\w*"

# Precedence verbs from G-04 and R-04.
# Outranks is the R-04 verb, in both word orders.
# Beaten is the Y-04 losing side form in passive shape
# only, used only in the losing side branch below, never
# as a winning verb. Active beats states winning, so it
# stays out and the shipped precedence sentence passes.
PRECEDENCE_VERBS = "winning|wins|prefer\\w*|outrank\\w*"

# Bounded window from B2.
# The longest G-01 plant puts its figure word about 100
# characters after its number, and the longest G-03 plant
# puts its target about 85 characters after its verb, so
# a 120 character window covers both with room to spare
# without letting a token anywhere in a long sentence fire.
WINDOW = "[^.]{0,120}"

# Sentence scope for the figure family from R36-E1-01.
# The figure check works one sentence unit at a time, so
# its span is the sentence itself with no character bound.
# A bounded window let one long adverbial spread push the
# simultaneity word 149 characters from its number inside
# a single sentence, which is a filler length escape and
# not a wording variant of a covered family. The figure
# family therefore reads its sentence with no character
# bound between the number and the simultaneity word,
# and the gate review repair binds the number to a
# generic agent noun so a number counting something else
# in the same long sentence stays out. The wrapper and
# activation families keep the bounded window above,
# because their tokens state separate claims that a long
# sentence can hold apart.

FIGURE_NUMBER = "([2-9]|1[0-9]|2[0-9])"


def normalise(text):
    """Lowercase text with spelled out numbers as digits."""
    out = text.lower().replace("-", " ")
    for word, digit in NUMBER_WORDS:
        out = re.sub(r"\b" + word + r"\b", digit, out)
    return out


def sentence_units(text):
    """Split normalised text into sentences for matching.

    Prose paragraphs join across wrapped lines, so a claim
    split across lines fires as one sentence. Table rows,
    headings, and code lines stay as their own units, so a
    table row cannot combine with the next paragraph into
    a false claim. Sentences inside a paragraph split on
    a terminator followed by whitespace, so a multi
    sentence line does not leak tokens across sentences.
    """
    return [
        unit for group in sentence_unit_groups(text) for unit in group
    ]


def sentence_unit_groups(text):
    """The sentence units grouped by their paragraph.

    R38-RT-13. The blank line flush in the unit split is
    the paragraph scope the brief format itself marks, so
    the groups keep it. A prose paragraph forms one group
    with every sentence in it, and a table row, heading,
    or code line forms a group of its own, so those units
    never join a neighbouring paragraph into a claim.
    """
    return [group for group, _barrier in _unit_groups(text)]


def _unit_groups(text):
    """The sentence unit groups, each tagged as a barrier.

    A prose paragraph group is no barrier. A table row,
    a heading, and a code line each form a group of their
    own and stand as barriers, the structural breaks the
    brief format itself marks between one claim unit and
    the next.
    """
    groups = []
    buffer = []
    in_code = False

    def flush():
        if not buffer:
            return
        joined = " ".join(buffer)
        buffer.clear()
        group = [
            sentence.strip()
            for sentence in re.split(
                r"(?<=[.!?])\s+", joined.strip()
            )
            if sentence.strip()
        ]
        if group:
            groups.append((group, False))

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            flush()
            continue
        if line.startswith("```"):
            flush()
            in_code = not in_code
            continue
        if in_code:
            flush()
            groups.append(([line], True))
            continue
        if line.startswith("|") or line.startswith("#"):
            flush()
            groups.append(([line], True))
            continue
        buffer.append(line)
    flush()
    return groups


def sentence_unit_scope_groups(text):
    """The prose sentence units grouped at claim scope.

    R38G-RT-03. A paragraph break alone does not end a
    figure claim in this brief, because consecutive prose
    paragraphs under one structural unit state claims
    across their break. The claim scope therefore runs
    over consecutive prose paragraph groups in order and
    stops at a barrier group, a table row or a heading or
    a code line, so a figure in one structural unit never
    joins a simultaneity word in the next. The figure
    guard stays scoped to the clause of the sentence that
    carries the figure, so a guard phrase standing in a
    neighbouring paragraph still shelters nothing.
    """
    groups = []
    current = []
    for group, barrier in _unit_groups(text):
        if barrier:
            if current:
                groups.append(current)
                current = []
            continue
        current = current + group
    if current:
        groups.append(current)
    return groups


def _bound_figure_span(sentence):
    """The span of the first figure number that binds to
    a generic agent noun, or None.

    A number counts as a figure only when a generic agent
    noun stands within the bounded window of it, in either
    direction. A number bound to another noun, source
    pages or routes or files, states no agent figure,
    however near a simultaneity word it sits.
    """
    for match in re.finditer(
        r"\b" + FIGURE_NUMBER + r"\b", sentence
    ):
        start = max(0, match.start() - 120)
        end = match.end() + 120
        if re.search(
            r"\b(" + FIGURE_AGENTS + r")\b", sentence[start:end]
        ):
            return match.start(), match.end()
    return None


def _bound_figure(sentence):
    """Whether a figure number binds to a generic agent noun."""
    return _bound_figure_span(sentence) is not None


def figure_problem(sentence):
    """Whether a sentence states a single Qwen figure.

    Gate review repair. The sentence scope span from
    R36-E1-01 fired on any number in a sentence with a
    simultaneity word, including a true sentence whose
    number counted source pages 251 characters from the
    word together. The figure now has to bind to a
    generic agent noun first, and the simultaneity word
    or the scope word in the same sentence does the
    rest, so the long adverbial spread in the E1 plant
    still fires on its reviewer count while a page count
    in a record sentence passes.
    """
    if not _bound_figure(sentence):
        return False
    if re.search(
        r"\b(" + FIGURE_ADVERBS + r")\b", sentence
    ):
        return True
    return bool(re.search(
        r"\b(" + FIGURE_SCOPE + r")\b", sentence
    ))


def wrapper_problem(sentence):
    """Whether a sentence states a wrapper exit outside its set.

    A wrapper noun plus a bare 4 is not enough. The
    sentence must also carry an exit, code, or return
    token, so a sentence about a wrapper supporting 4
    tools passes while an exit claim fires. Repair pass
    four widens the figure side from the 4 alone to any
    figure outside the wrapper set of 0 and 1 and 3,
    because the binding is the set membership and an
    added sentence assigning the wrapper an exit of 2 or
    5 states the same false membership as the 4 form.
    The widened side reads only figures standing in an
    exit figure position, after the word exit or exits
    with the word of standing between the exit word and
    its figure admitted beside the plain form, or in a
    list the word exits heads, or standing before a
    wrapper exit phrase, so a figure counting something
    else in the same sentence, the 2 tables the exits
    live in, states no membership.
    """
    if not re.search(
        r"\b(exit\w*|code|return\w*)\b", sentence
    ):
        return False
    if re.search(
        r"\b(" + WRAPPER_WORDS + r")\b" + WINDOW + r"\b4\b",
        sentence,
    ):
        return True
    if re.search(
        r"\b4\b" + WINDOW + r"\b(" + WRAPPER_WORDS + r")\b",
        sentence,
    ):
        return True
    if not re.search(r"\b(" + WRAPPER_WORDS + r")\b", sentence):
        return False
    figures = []
    for match in re.finditer(
        r"\bexits?\s+(?:is\s+|are\s+|of\s+)?"
        r"(\d+(?:\s*,\s*(?:and\s+)?\d+|\s+and\s+\d+)*)",
        sentence,
    ):
        figures.extend(re.findall(r"\d+", match.group(1)))
    for match in re.finditer(
        r"\b(\d+)\s+is\s+(?:a\s+|the\s+)?"
        r"(?:" + WRAPPER_WORDS + r")\s+exit",
        sentence,
    ):
        figures.append(match.group(1))
    return any(
        number not in ("0", "1", "3") for number in figures
    )


# The exit meaning fragments in normalised form, keyed by
# the exit each belongs to. Repair pass four. A sentence
# that pairs one exit with the meaning fragment of another
# states the swapped binding the presence pins cannot see,
# because the pinned sentences all still stand.
EXIT_MEANINGS = {
    0: "review completed whatever it decided",
    1: "never reached a verdict",
    3: "completed with request_changes",
    4: "internal verify refusal",
}


def _exit_meaning_problem(sentence):
    """The plant kind of a swapped exit meaning, or None.

    A sentence claims an exit in one of two shapes, the
    internal verify shape, which claims exit 4, and the
    wrapper shape, a wrapper word with an exit figure in
    the same sentence. When the sentence also carries the
    meaning fragment of a different exit, with no clause
    negation guarding that fragment, it states the other
    exit its meaning, and the kind names the claimed side.
    A sentence carrying the claimed exit its own fragment
    states the shipped pairing and passes.
    """
    claimed = None
    if "internal verify" in sentence:
        claimed = 4
    else:
        match = re.search(
            r"\b(?:" + WRAPPER_WORDS + r")\b[^.]{0,60}?"
            r"\bexit\w* (\d+)\b",
            sentence,
        ) or re.search(
            r"\bexit\w* (\d+)\b[^.]{0,60}?"
            r"\b(?:" + WRAPPER_WORDS + r")\b",
            sentence,
        )
        if match:
            claimed = int(match.group(1))
    if claimed is None:
        return None
    for number, fragment in EXIT_MEANINGS.items():
        if number == claimed:
            continue
        index = sentence.find(fragment)
        if index != -1 and not _claim_negated(sentence, index):
            if claimed == 4:
                return "internal verify exit"
            return "wrapper exit"
    return None


def _internal_verify_problem(sentence):
    """Whether a sentence gives the internal verify another exit.

    The internal verify exit is 4 alone, so a sentence
    that names the internal verify and places a figure
    other than 4 in an exit figure position, after the
    word exit with the word of standing between the exit
    word and its figure admitted beside the plain form,
    or standing before an internal verify exit
    phrase, states a false membership, judged with the
    same clause negation as the prose publication family.
    A sentence naming no figure in that position, or the
    figure 4, states no false membership here, so a
    figure counting something else in the same sentence,
    the 2 tables the exits live in, passes.
    """
    if "internal verify" not in sentence:
        return False
    figures = []
    for match in re.finditer(
        r"\bexits?\s+(?:is\s+|of\s+)?(\d+)\b", sentence
    ):
        figures.append(match)
    for match in re.finditer(
        r"\b(\d+)\s+is\s+(?:a\s+|the\s+)?internal verify exit",
        sentence,
    ):
        figures.append(match)
    for match in figures:
        if match.group(1) != "4":
            return not _claim_negated(sentence, match.start(1))
    return False


def activation_problem(sentence):
    """Whether a sentence activates a Qwen target."""
    if re.search(
        r"\b(" + ACTIVATION_VERBS + r")\b" + WINDOW + r"\b("
        + ACTIVATION_TARGETS + r")\b", sentence
    ):
        return True
    if re.search(
        r"\b(" + ACTIVATION_TARGETS + r")\b" + WINDOW + r"\b("
        + ACTIVATION_VERBS + r")\b", sentence
    ):
        return True
    if re.search(r"\b(on|up|online)\b", sentence):
        if re.search(
            r"\b(" + ACTIVATION_PARTICLE_VERBS + r")\b"
            + WINDOW + r"\b(" + ACTIVATION_TARGETS + r")\b",
            sentence,
        ):
            return True
        if re.search(
            r"\b(" + ACTIVATION_TARGETS + r")\b" + WINDOW
            + r"\b(" + ACTIVATION_PARTICLE_VERBS + r")\b",
            sentence,
        ):
            return True
    return False


def guarded(line):
    """Whether a sentence carries a guard word.

    The claim is that a sentence holding one of the guard
    words states its claim under a basis, a negation or a
    record framing the negative families exempt. The bound
    is the guard word list alone, read on the one sentence.
    """
    return any(word in line for word in GUARD_WORDS)


def _figure_guarded(sentence):
    """Whether the clause holding the bound figure is
    guarded.

    R37F-RT-16. A guard phrase exempts a figure from the
    clause that states the figure, because a record
    sentence names its basis beside its count. A guard
    phrase in a later contrast clause names a basis the
    claim separates itself from, separate from the roster
    narrative table, and a claim standing apart from its
    named basis in its own voice is an own voice claim,
    not a record sentence, so the exemption does not
    reach it.
    """
    span = _bound_figure_span(sentence)
    if span is None:
        return guarded(sentence)
    start = span[0]
    # Confirmation repair. An as joint is a clause edge
    # too, because a basis clause appended with as and
    # no comma states the same subordinate basis the
    # comma form states, and its guard phrase stands
    # outside the clause that holds the figure.
    # R38-RT-14. The subordinate joints are clause edges
    # as a class, not the as form alone, so a basis clause
    # appended with while or when or because or since or
    # whereas or although and no comma stands outside the
    # figure clause the same way.
    # R38G-RT-09. A basis appendage joined by the word
    # with and no comma is a clause edge of the same kind,
    # an appendage joint rather than a subordinator, so a
    # guard phrase standing inside that appendage stands
    # outside the figure clause too.
    markers = (
        ",", ";", " as ", " while ", " when ", " because ",
        " since ", " whereas ", " although ", " with ",
    )
    clause_start = 0
    for marker in markers:
        index = sentence.rfind(marker, 0, start)
        if index != -1:
            clause_start = max(
                clause_start, index + len(marker)
            )
    clause_end = len(sentence)
    for marker in markers:
        index = sentence.find(marker, start)
        if index != -1:
            clause_end = min(clause_end, index)
    return guarded(sentence[clause_start:clause_end])


def plant_sentence(raw):
    """One plant reading stated as a sentence naming its file.

    The readings inside the negative family collect a label
    and the sentence that drew it. The gate speaks in full
    sentences naming the surface, in the voice its sibling
    gates use, so the collected label is stated that way on
    the way out.
    """
    kind, _, rest = raw.partition(": ")
    if not rest:
        return raw
    return (
        "the Qwen brief at docs/qwen-code-brief.md carries "
        "a %s in the sentence %s" % (kind, rest)
    )


PUBLICATION_PATTERNS = (
    r"\ba listing file ships\b",
    r"\ba listing file (?:has|had) shipped\b",
    r"\ba listing file shipped\b",
    r"\bmarketplace presence (?:is|was|has been) "
    r"(?:published|listed)\b",
    r"\b(?:is|was|were|has been|have been) published\b",
    r"\bpublished in the qwen marketplace\b",
)


def _claim_negated(line, start):
    """Whether a negation guards a claim from its own clause.

    The clause runs from the last clause edge before the
    claim, a comma or a semicolon or a but or however or
    yet joint or a subordinating joint from the closed
    class, after or although or because or before or
    given that or if or in that or once or since or
    though or unless or until or when or whenever or
    whereas or wherever or whether or while or whilst
    or seeing that or so that, to the claim itself. A
    negation inside that stretch guards the claim, and
    a negation in an earlier clause belongs to that
    clause and guards nothing here. Negation is credited
    only within the claim's own clause, and a guard
    carried by bare as or by a participial phrase stands
    outside this reading.
    """
    prefix = line[:start]
    cut = 0
    for edge in re.finditer(
        r",|;|\bbut\b|\bhowever\b|\byet\b|\bafter\b|\balthough\b"
        r"|\bbecause\b|\bbefore\b|\bgiven that\b|\bif\b|\bin that\b"
        r"|\bonce\b|\bsince\b|\bthough\b|\bunless\b|\buntil\b"
        r"|\bwhen\b|\bwhenever\b|\bwhereas\b|\bwherever\b|\bwhether\b"
        r"|\bwhile\b|\bwhilst\b|\bseeing that\b|\bso that\b",
        prefix,
    ):
        cut = max(cut, edge.end())
    return bool(
        re.search(r"\b(not|no|never|nothing)\b|n't", prefix[cut:])
    )


def _table_cell_publication_claim(line):
    """Whether a table row states the publication claim in a cell.

    A status table is a claim surface in this brief, so a
    row that names the marketplace in one cell and carries
    the bare status word published or listed in another
    cell states the publication claim with no verb form at
    all. Markdown emphasis inside a cell is stripped before
    the cell is judged, so a status word wearing emphasis
    reads as the bare status word it carries. A cell
    carrying an honest status, a negated status among
    them, states no claim, because its cell text is not
    the bare status word.
    """
    if not line.lstrip().startswith("|"):
        return False
    cells = [
        re.sub(r"[*_`]", "", cell).strip()
        for cell in line.strip().strip("|").split("|")
    ]
    status = [
        index for index, cell in enumerate(cells)
        if cell in ("published", "listed")
    ]
    if not status:
        return False
    return any(
        index not in status
        and re.search(
            r"\b(marketplace|listing|qwen)\b", cell)
        for index, cell in enumerate(cells)
    )


def _publication_claim(line):
    """Whether a sentence states the publication claim.

    The family covers the present and past tense forms of
    the listing and published claims and the heading form
    that names the marketplace as published in, each judged
    with its own clause negation, so a negated claim states
    no claim while a guard word elsewhere in the sentence
    shelters nothing. The family also covers the table cell
    form, a bare status word standing in a cell beside a
    marketplace cell, and the forms the helper
    _caption_publication_claims reads, a status stated in
    a caption line standing directly under a table whose
    row names the marketplace or the listing or Qwen
    and points at the caption, where the caption line
    opens with the words Table caption or with the word
    Caption and states the status in the stands published
    or stands listed form or as the bare status word, and
    a status stated in a standalone status line standing
    directly under a table whose row names the
    marketplace or the listing or Qwen, in the stands
    form or as the bare status word. A caption line
    standing after an intervening prose paragraph stands
    outside the reading.
    """
    if _table_cell_publication_claim(line):
        return True
    for pattern in PUBLICATION_PATTERNS:
        match = re.search(pattern, line)
        if match and not _claim_negated(line, match.start()):
            return True
    return False


def _status_sentence(sentence):
    """Whether one sentence states the bare or stands status.

    The stands form states the status in the stands
    published or stands listed form, judged with the same
    clause negation as the prose family. The bare form is
    the status word standing as the whole sentence, so no
    negation can stand inside it.
    """
    match = re.search(
        r"\bstands? (?:published|listed)\b", sentence)
    if match and not _claim_negated(sentence, match.start()):
        return True
    return sentence.strip().rstrip(".!?") in (
        "published", "listed")


def _caption_publication_claims(text):
    """Caption and status line sentences that state the claim.

    Repair pass three. A claim split between a table cell
    and the caption standing under the table reads whole.
    Repair pass four widens the reading to the forms the
    scoping texts now name. The caption form covers a
    caption line standing directly under a table whose
    row names the marketplace or the listing or Qwen and
    points at the caption, where the caption line opens
    with the words Table caption or with the word Caption
    and a sentence of it states the status in the stands
    published or stands listed form or as the bare status
    word. The standalone form covers a status line
    standing directly under a table whose row names the
    marketplace or the listing or Qwen, stating the
    status in the stands form or as the bare status word,
    with no caption lead and no pointing row needed,
    because the line itself carries the status. A caption
    line standing after an intervening prose paragraph
    stands outside the reading, because the rows no
    longer stand directly before it. A caption under a
    row that names no marketplace states no claim in this
    reading.
    """
    claims = set()
    groups = sentence_unit_groups(text)
    for index, group in enumerate(groups):
        if not group:
            continue
        rows = []
        back = index - 1
        while (
            back >= 0 and groups[back]
            and groups[back][0].lstrip().startswith("|")
        ):
            rows.extend(groups[back])
            back -= 1
        if not rows:
            continue
        named = any(
            re.search(r"\b(marketplace|listing|qwen)\b", row)
            for row in rows
        )
        if not named:
            continue
        if re.match(r"^(table )?caption\b", group[0]):
            pointed = any(
                re.search(r"\b(marketplace|listing|qwen)\b", row)
                and "caption" in row
                for row in rows
            )
            if not pointed:
                continue
        for sentence in group:
            if _status_sentence(sentence):
                claims.add(sentence)
    return claims


def _live_presence_claim(line):
    """Whether a sentence claims the build is live in the marketplace.

    The live wording is a distinct member from the
    publication family, stated as the build standing live
    in the Qwen marketplace, with the same clause negation
    discipline.
    """
    for pattern in (
        r"\blive in the qwen marketplace\b",
        r"\bis live\b[^.]{0,40}\bqwen marketplace\b",
    ):
        match = re.search(pattern, line)
        if match and not _claim_negated(line, match.start()):
            return True
    return False


def negative_problems(text):
    """Meaning based negatives over sentences, not lines.

    Sentence scoping is the R-07 fix. A claim wrapped
    across lines joins into one sentence, so the number
    and the figure word share a sentence even when they
    never share a line. The shipped Qoder sentence keeps
    its exemption at sentence scope, because its shape is
    still present in its own sentence after joining, and
    a rewrap of that sentence keeps the exemption too.
    """
    problems = []
    caption_claims = _caption_publication_claims(normalise(text))
    for line in sentence_units(normalise(text)):
        if not re.search(r"\b(never|no sentence|not a wrapper)\b", line):
            if wrapper_problem(line):
                problems.append("wrapper exit plant: " + line[:120])
        # R37F-RT-16. The figure check reads the clause
        # scoped guard before the sentence guard skip, so
        # a figure whose own clause is unguarded fails
        # even when a contrast clause later in its
        # sentence carries a guard phrase.
        if figure_problem(line) and not _figure_guarded(line):
            problems.append("figure plant: " + line[:120])
        # Repair pass. The publication family and the live
        # presence family are judged on claim carrying
        # sentences regardless of guard words elsewhere in
        # the sentence, so they stand ahead of the guarded
        # sentence skip. The guarded readings of the other
        # families below keep their skip untouched.
        if _publication_claim(line) or line in caption_claims:
            problems.append("publication plant: " + line[:120])
        if _live_presence_claim(line):
            problems.append("live presence plant: " + line[:120])
        # Repair pass four. The exit membership and meaning
        # readings stand ahead of the guarded sentence skip
        # beside the publication family, because an internal
        # verify sentence carries its own guard word and a
        # guard word elsewhere in a sentence shelters no
        # swapped meaning.
        if _internal_verify_problem(line):
            problems.append(
                "internal verify exit plant: " + line[:120])
        meaning_kind = _exit_meaning_problem(line)
        if meaning_kind is not None:
            problems.append(
                meaning_kind + " plant: " + line[:120])
        if guarded(line):
            continue
        if re.search(r"\breturns? 4\b", line) and re.search(
            r"\b(" + WRAPPER_WORDS + r"|exit\w*)\b", line
        ):
            problems.append("wrapper exit plant: " + line[:120])
        if re.search(r"skills\.disabled blocks only", line):
            problems.append("disabled naming plant: " + line[:120])
        if re.search(r"skills\.enabled[^.]{0,80}\bbare name\b", line) and "prefixed" not in line:
            problems.append("enabled naming plant: " + line[:120])
        if re.search(r"legacy sse" + WINDOW + r"\b(" + ACTIVATION_VERBS + r")\b", line):
            problems.append("activation plant: " + line[:120])
        if re.search(
            r"\bcommands\b" + WINDOW + r"\bagents\b" + WINDOW
            + r"\bhooks\b" + WINDOW + r"\b(light up|"
            + ACTIVATION_VERBS + r")\b", line
        ):
            problems.append("activation plant: " + line[:120])
        if not re.search(
            r"\bnot\b[^.]{0,25}\b(activat\w*|enabl\w*|turn\w*|switch\w*|power\w*|bring\w*)",
            line,
        ) and QODER_UNVERIFIED_SHAPE not in line:
            if activation_problem(line):
                problems.append("activation plant: " + line[:120])
        if re.search(r"\.agents/skills" + WINDOW + r"\bdrift\b", line):
            problems.append("alias drift plant: " + line[:120])
        if re.search(r"\.agents/skills" + WINDOW + r"\b(?:" + DISCOVERY_VERBS + r")\b", line):
            problems.append("alias discovery plant: " + line[:120])
        elif re.search(r"\b(?:" + DISCOVERY_VERBS + r")\b" + WINDOW + r"\.agents/skills", line):
            problems.append("alias discovery plant: " + line[:120])
        if re.search(r"\.agents/skills" + WINDOW + r"\b(" + PRECEDENCE_VERBS + r")\b", line):
            problems.append("alias precedence plant: " + line[:120])
        elif re.search(r"\b(" + PRECEDENCE_VERBS + r")\b" + WINDOW + r"\.agents/skills", line):
            problems.append("alias precedence plant: " + line[:120])
        elif re.search(r"\.qwen/skills" + WINDOW + r"\b(los\w*|beaten)\b", line):
            problems.append("alias precedence plant: " + line[:120])
        if re.search(r"\bany npm package\b", line):
            problems.append("npm scope plant: " + line[:120])
        if re.search(r"\bunscoped\b[^.]{0,40}\b(work|install|valid)\b", line):
            problems.append("npm scope plant: " + line[:120])
        if re.search(r"converted bundle[^.]{0,60}\b(proven|verified|confirmed)\b", line):
            problems.append("conversion plant: " + line[:120])
        # R37-RT-01. Byte fidelity holds for the round 33
        # skill tree installs only, so a sentence that
        # claims byte identical output for a full or whole
        # conversion states more than the record proves.
        if re.search(r"\bbyte identical\b", line) and re.search(
            r"\b(full|entire|whole)\b", line
        ):
            problems.append("conversion fidelity plant: " + line[:120])
        # R38-EX-01. The unscoped denial that side shapes
        # do not ride in contradicts the round 37 full
        # bundle install recorded in the same section, so
        # its return in any form the repair removed fails.
        if re.search(r"side shapes do not ride in", line) or re.search(
            r"installed bundles contain only the skill tree", line
        ):
            problems.append("conversion plant: " + line[:120])
        if re.search(r"\bproven to run\b", line):
            problems.append("conversion plant: " + line[:120])
        if re.search(r"\bfull packet workflow in qwen\b", line) and "not" not in line:
            problems.append("conversion plant: " + line[:120])
        if re.search(r"central qwen marketplace[^.]{0,40}\b(submission|approval)\b", line):
            problems.append("publication plant: " + line[:120])
        if re.search(r"vs code marketplace[^.]{0,40}\b(publication|publish)\b", line):
            problems.append("publication plant: " + line[:120])
    # Gate review repair. The figure family also reads
    # the pairs of prose sentences that stand next to each
    # other, because the review split the agent count and
    # the simultaneity word across a sentence boundary in
    # both orders and each half passed alone. Table rows
    # and headings and code lines stay out of the pairs,
    # as they stay out of the sentence units themselves.
    # R37-RT-10. The reading now runs over windows of
    # neighbouring prose sentences, and the guard no
    # longer exempts a whole window. The round 37 review
    # split the count and the simultaneity word two
    # sentences apart with a filler between them, and
    # beside that it stood a planted figure next to a
    # guarded record sentence so the pair reading skipped
    # the joined unit whole. A window is exempt only when
    # every sentence in it that carries a bound figure is
    # guarded in the figure's own clause, so a basis label
    # on a neighbouring sentence or in a contrast clause
    # no longer shelters an unguarded figure.
    groups = sentence_unit_scope_groups(normalise(text))

    def window_problem(window):
        joined = " ".join(window)
        if not figure_problem(joined):
            return False
        if not any(
            _bound_figure(member) and not _figure_guarded(member)
            for member in window
        ):
            return False
        # R37F-RT-17. A member that carries the
        # simultaneity or scope word and a figure number
        # of its own, different from the window's bound
        # figure, heads its own claim, the two editors
        # working together on the packet format. Joining
        # its word to the window's count states a claim
        # neither member states, so the window does not
        # fire on it.
        bound_values = set()
        for member in window:
            span = _bound_figure_span(member)
            if span is not None:
                bound_values.add(member[span[0]:span[1]])
        # R38G-RT-05. The exemption is judged per member,
        # not per window. A member that heads its own claim
        # does not join the window's count, and it no
        # longer exempts the whole window either, because
        # the gate review stood such a member as a decoy
        # between the figure sentence and a pronoun member
        # that does join, and the window stated the claim
        # in full while the exemption sheltered it. The
        # window fires only where at least one simultaneity
        # or scope member actually joins the count.
        joined_claim = False
        for member in window:
            word = re.search(
                r"\b(" + FIGURE_ADVERBS + r"|" + FIGURE_SCOPE
                + r")\b",
                member,
            )
            if not word:
                continue
            own = {
                match.group(0)
                for match in re.finditer(
                    r"\b" + FIGURE_NUMBER + r"\b", member
                )
            }
            if own and not own <= bound_values:
                continue
            # R38-RT-15. A simultaneity or scope member
            # whose subject is an explicit noun phrase
            # other than the figure's agents heads its own
            # claim whether or not it carries a number, the
            # editors working together on the packet
            # format. Only a member whose subject is a
            # pronoun carrying the figure's subject
            # forward, or the agent noun itself, or Qwen,
            # joins the window's count into one claim.
            head = member[:word.start()]
            if re.match(
                r"\s*(they|it|these|those)\b", head
            ):
                joined_claim = True
                continue
            if "qwen" in head:
                joined_claim = True
                continue
            if re.search(
                r"\b(" + FIGURE_AGENTS + r")\b", head
            ):
                joined_claim = True
                continue
            if not re.search(r"[a-z]", head):
                joined_claim = True
                continue
        return joined_claim

    # R37F-RT-15. Windows ran to four neighbouring
    # sentences, because the fix review split the count
    # and the simultaneity word three sentences apart, and
    # the confirmation repair widened them to five.
    # R38-RT-13. The round 38 review split them one
    # sentence further again, across six sentences, so the
    # reading now runs at paragraph scope, over every
    # neighbouring window inside a paragraph group and
    # never across a paragraph break, a table row, a
    # heading, or a code line.
    # R38G-RT-03. The gate review split them across a
    # paragraph break, so the reading now runs at claim
    # scope, over every neighbouring window inside a scope
    # group of consecutive prose paragraphs, and still
    # never across a table row, a heading, or a code line.
    for group in groups:
        if len(group) < 2:
            continue
        for size in range(2, len(group) + 1):
            for index in range(len(group) - size + 1):
                window = group[index:index + size]
                if not window_problem(window):
                    continue
                if any(
                    figure_problem(member) for member in window
                ):
                    continue
                if any(
                    window_problem(window[start:start + sub])
                    for sub in range(2, size)
                    for start in range(size - sub + 1)
                ):
                    continue
                problems.append(
                    "figure plant: " + " ".join(window)[:120]
                )
    return [plant_sentence(problem) for problem in problems]


UTF8_UNREADABLE = []


def read_text(path):
    if path.exists() and not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        if str(path) not in UTF8_UNREADABLE:
            UTF8_UNREADABLE.append(str(path))
        return None
    except OSError:
        return None


def utf8_problems():
    """Problems naming the files the readings could not decode."""
    return [
        "%s cannot be read as UTF-8 text" % Path(path).name
        for path in UTF8_UNREADABLE
    ]


def repair_utf8_problems(problems):
    """Name the UTF-8 defect in place of the missing wording.

    A file that stands on disk holding damaged bytes is not
    a missing file, so a problem that calls a recorded
    undecodable file missing is replaced by the UTF-8
    problem for that file, in the shape the comate and copy
    readings use. A genuinely missing file records nothing
    here and keeps its missing wording.
    """
    if not UTF8_UNREADABLE:
        return problems
    kept = []
    labels = []
    for problem in problems:
        label = None
        if "missing" in problem:
            for path in UTF8_UNREADABLE:
                parts = Path(path).parts
                for size in range(len(parts), 0, -1):
                    candidate = "/".join(parts[-size:])
                    if candidate not in problem:
                        continue
                    if size == 1:
                        token = re.search(
                            r"[^\s]*" + re.escape(candidate),
                            problem,
                        )
                        if token and "/" in token.group(0):
                            continue
                    label = candidate
                    break
                if label is not None:
                    break
        if label is None:
            kept.append(problem)
        elif label not in labels:
            labels.append(label)
    for path in UTF8_UNREADABLE:
        name = Path(path).name
        if not any(label.endswith(name) for label in labels):
            labels.append(name)
    kept.extend(
        "%s cannot be read as UTF-8 text" % label
        for label in labels
    )
    return kept


def deliberate_source(note):
    """Whether a derivation note names a source on purpose.

    The claim is that a note counts only when it names a
    canonical skill section as its source, a primary Qwen
    citation, or a binding decision. A passing mention of a
    title states no derivation and does not count.
    """
    for title in CANONICAL_SECTIONS:
        if re.search(
            r"canonical skill[^.;]{0,200}" + re.escape(title), note
        ):
            return True
    if any(stem in note for stem in PRIMARY_CITATIONS):
        return True
    return "decision 26" in note or "Decision 4" in note or "decision 13" in note


def rules_section(raw):
    """The text of the rules section alone, or None.

    The claim is the rules section from its heading to the
    next section heading, so a marker standing in the
    navigation section after it is not judged as part of
    the last rule. The bound is the next level two heading.
    """
    start = raw.find(RULES_HEADING)
    if start < 0:
        return None
    rest = raw[start + len(RULES_HEADING):]
    match = re.search(r"(?m)^## ", rest)
    if match:
        rest = rest[:match.start()]
    return raw[start:start + len(RULES_HEADING) + len(rest)]


def derivation_problems(raw):
    """Problems with the derivation discipline of the rules.

    The claim is that every rule in the rules section
    carries a derivation note naming a checkable source and
    that at least ten rules stand. The bound is the rules
    section alone, cut at the next section heading.
    """
    section = rules_section(raw)
    if section is None:
        return ["the Qwen rules section is missing"]
    problems = []
    parts = re.split(r"\n### R\d+\. ", section)
    for part in parts[1:]:
        head = part.split("\n", 1)[0]
        if "Derives from" not in part:
            problems.append(
                "the Qwen brief at docs/qwen-code-brief.md "
                "carries a rule without derivation note, the "
                "rule headed " + head + ", so the rule names "
                "no source a reader can check"
            )
            continue
        note = part[part.find("Derives from"):]
        if not deliberate_source(note):
            problems.append(
                "the Qwen brief at docs/qwen-code-brief.md "
                "carries a rule whose derivation note names "
                "no source, the rule headed " + head + ", so "
                "the note names nothing a reader can check"
            )
    if len(parts) - 1 < 10:
        problems.append(
            "the Qwen brief at docs/qwen-code-brief.md "
            "carries fewer than ten Qwen rules, so the rules "
            "section the gate pins does not stand in full"
        )
    return problems


def decision_note(raw):
    """The round 33 decision note text, or None.

    The claim is the note from its marker heading to the
    next section heading of the decision record. The bound
    is that next heading, so a later record is not judged
    as part of this note.
    """
    start = raw.find(DECISION_NOTE_MARKER)
    if start < 0:
        return None
    end = raw.find("\n## ", start)
    return raw[start:] if end < 0 else raw[start:end]


def readme_qwen_section(raw):
    """The README Qwen Code section text, or None.

    The claim is the section from its heading to the next
    heading at either level. The bound is that next
    heading, so a neighbouring install section is not
    judged as part of the Qwen section.
    """
    start = raw.find("### Qwen Code")
    if start < 0:
        return None
    rest = raw[start:]
    for marker in ("\n### ", "\n## "):
        end = rest.find(marker, 1)
        if end > 0:
            return rest[:end]
    return rest


QWEN_WRAPPER_ROWS = (
    "| 0 | The review completed whatever it decided |",
    "| 1 | It never reached a verdict because a child failed or timed out or left no composed artifact |",
    "| 3 | It completed with REQUEST_CHANGES and fail-on request-changes set |",
)

QWEN_INTERNAL_ROWS = (
    "| 4 | Internal verify refusal at the compose floor |",
)


def _row_cells(row):
    """The cells of one normalised table row line."""
    return [cell.strip() for cell in row.strip("|").split("|")]


def _is_separator(row):
    """Whether a normalised table line is the separator row."""
    return bool(re.fullmatch(r"\|[\s:\-|]+\|", row))


def _block_rows(lines, start):
    """The data rows of the table whose header stands at start.

    The rows are the table lines standing after the header
    and its separator, up to the first line that is not a
    table line, returned with their line indexes so a row
    standing in a block is never counted twice.
    """
    found = {}
    index = start + 1
    while index < len(lines) and lines[index].startswith("|"):
        if not _is_separator(lines[index]):
            found[index] = lines[index]
        index += 1
    return found


def _labelled_exit_rows(lines, label):
    """The data rows of the exit table standing under a label."""
    for index, line in enumerate(lines):
        if line != label:
            continue
        for head in range(index + 1, len(lines)):
            if lines[head] == "| Exit | Meaning |":
                return _block_rows(lines, head)
            if lines[head].startswith("### "):
                break
        return {}
    return {}


def _census_problems(table, found_rows, pinned_rows):
    """Problems with rows standing outside a pinned census.

    Repair pass four. A presence pin proves the pinned
    rows stand, and the census is its other half, proving
    no row stands beside them. The rows standing in the
    table must be exactly the pinned set, each row whole,
    so a row added to the table, or a restated row standing
    anywhere in the brief in the form of a table row, is
    refused here, while a dropped row and a restated
    figure in a standing row refuse on the presence pins
    above.
    """
    extra = Counter(found_rows) - Counter(pinned_rows)
    problems = []
    for row in dict.fromkeys(found_rows):
        if extra[row] > 0:
            problems.append(
                "docs/qwen-code-brief.md " + table
                + " carries a row outside the pinned census, "
                "namely " + repr(row) + ", so the rows "
                "standing in the table are not the pinned set"
            )
    return problems


def _table_census_problems(raw):
    """Census problems over the three pinned brief tables.

    The R1 scope table is found by its header, and a stray
    row in the R1 form standing anywhere in the brief, a
    row whose page cell names one of the two R1 pages or
    whose scope cell names a pinned scope, joins the
    census wherever it stands. The two exit tables are
    found by their labels, and a stray exit row whose
    meaning cell states a pinned exit meaning joins the
    census of the table that meaning belongs to.
    """
    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in raw.splitlines()
    ]
    problems = []
    r1_found = {}
    for index, line in enumerate(lines):
        if line == "| Page | Scope | Figure | Basis |":
            r1_found.update(_block_rows(lines, index))
            break
    scopes = {_row_cells(row)[1] for row in QWEN_R1_ROWS}
    for index, line in enumerate(lines):
        if index in r1_found or not line.startswith("|"):
            continue
        cells = _row_cells(line)
        if len(cells) == 4 and (
            cells[0] in ("Code review page", "Commands page")
            or cells[1] in scopes
        ):
            r1_found[index] = line
    problems.extend(_census_problems(
        "R1 scope table",
        [r1_found[index] for index in sorted(r1_found)],
        QWEN_R1_ROWS,
    ))
    wrapper_found = _labelled_exit_rows(lines, "Wrapper exits")
    internal_found = _labelled_exit_rows(
        lines, "Internal verify exit")
    in_blocks = set(wrapper_found) | set(internal_found)
    wrapper_meanings = {
        _row_cells(row)[1] for row in QWEN_WRAPPER_ROWS}
    internal_meanings = {
        _row_cells(row)[1] for row in QWEN_INTERNAL_ROWS}
    for index, line in enumerate(lines):
        if index in in_blocks or not line.startswith("|"):
            continue
        cells = _row_cells(line)
        if len(cells) != 2 or not re.fullmatch(r"\d+", cells[0]):
            continue
        if cells[1] in wrapper_meanings:
            wrapper_found[index] = line
        elif cells[1] in internal_meanings:
            internal_found[index] = line
    problems.extend(_census_problems(
        "wrapper exit table",
        [wrapper_found[index] for index in sorted(wrapper_found)],
        QWEN_WRAPPER_ROWS,
    ))
    problems.extend(_census_problems(
        "internal verify exit table",
        [internal_found[index] for index in sorted(internal_found)],
        QWEN_INTERNAL_ROWS,
    ))
    return problems


QWEN_R1_ROWS = (
    "| Code review page | Step 3A small diff roster | Up to 16 parallel agents | Effort table |",
    "| Code review page | Same repo PR reviews | Up to 17 parallel tasks | Roster narrative |",
    "| Code review page | Same repo PR reviews in practice with finders | 16 to 19 in practice | Roster narrative |",
    "| Code review page | Local diff and file path reviews | 14 to 17 | Roster narrative |",
    "| Code review page | Cross repo lightweight mode with PR identity | 14 to 17 | Roster narrative |",
    "| Code review page | Cross repo lightweight mode without PR identity | 12 to 15 | Roster narrative |",
    "| Code review page | Review agents in Step 3 | 17 with 0 to 2 added | Token efficiency table |",
    "| Code review page | Review agents in Step 3 without Agent 1e | 16 | Token efficiency table |",
    "| Code review page | Local and file reviews | 15 | Token efficiency table |",
    "| Code review page | Cross repo reviews with PR identity | 15 | Token efficiency table |",
    "| Code review page | Cross repo reviews without PR identity | 13 | Token efficiency table |",
    "| Commands page | Built in skills table | 12 parallel agents at high effort | Conflicting summary not used |",
)


def operative_prose_problems(raw, section, label):
    """Problems with operative prose outside the section.

    The derivation discipline of this gate binds the
    numbered rules inside the disciplined section, and the
    rest of the brief stood outside every reading, so one
    plain prose sentence appended after the section, in
    the form of an instruction to the reviewing session,
    passed the gate while carrying an operative direction
    no rule carries and no derivation note names. This
    reading closes the brief as a whole. The disciplined
    section is removed and every remaining sentence is
    judged, and the skeleton of the section is judged
    beside it, the skeleton being the text of the section
    before its first numbered rule, so a stray paragraph
    standing in the preamble of the rules is judged on the
    same terms as one standing anywhere outside the
    section. The numbered rule blocks themselves stand
    exempt, because a rule states its instruction as a
    numbered rule carrying its derivation note, which is
    the one form this brief allows. A sentence is
    operative when it speaks to or about the reviewing
    session, naming the reviewer or
    the session or addressing the reader as you, and it
    either carries a duty modal or opens with an imperative
    verb of the instruction family. A descriptive sentence
    about the session states no instruction and passes, and
    an instruction with no session subject stands outside
    this family and is left to its own pins. The identical
    reading stands in each of the eleven brief gates,
    because the eleven rules briefs share the one discipline
    and a closure that covered fewer than all eleven would
    leave the same door open at the next brief.
    """
    outside = raw.replace(section, " ", 1) if section else raw
    skeleton = ""
    if section:
        skeleton = re.split(
            r"(?m)^### [A-Z]+\d+\.", section, maxsplit=1
        )[0]
    judged = outside + " " + skeleton if skeleton else outside
    flat = re.sub(r"\s+", " ", judged)
    problems = []
    reported = set()

    def judge(fragment, shown):
        low = fragment.lower()
        if not re.search(r"\b(reviewers?|sessions?|you)\b", low):
            return
        deontic = re.search(
            r"\b(must|shall|should|needs? to|has to|have to|"
            r"is required to|are required to)\b", low)
        imperative = re.match(
            r"\s*(always|never|print|begin|open|start|approve|"
            r"reject|show|display)\b", low)
        if (deontic or imperative) and shown not in reported:
            reported.add(shown)
            problems.append(
                "%s carries the operative sentence %r outside "
                "its disciplined section, and an instruction "
                "to the reviewing session stands in this brief "
                "only as a numbered rule carrying its "
                "derivation note" % (label, shown))

    for sentence in re.split(r"(?<=[.!?])\s+", flat):
        judge(sentence, sentence.strip())
    # An appended instruction stands on its own line at the
    # end of a brief whose last sentence carries no closing
    # mark, so the sentence split can fold it into the
    # trailing genuine sentence and hide its opening
    # imperative. Each line is therefore judged on its own
    # marks as well, with the markdown furniture stripped,
    # so the same instruction is refused in that folded
    # form too.
    for line in judged.splitlines():
        fragment = re.sub(r"^[#>*\-\d.\s`]+", "", line)
        judge(fragment, fragment.strip())
    return problems


def qwen_problems(root=None):
    """Every Build 15 Qwen Code marketplace presence problem.

    The claim is that the brief, the decision note, the
    changelog and the README Qwen section state the pinned
    contract and that no listing file ships in the tree. The
    bound is those surfaces alone, read at the root given.
    """
    root = ROOT if root is None else root
    UTF8_UNREADABLE.clear()
    problems = []
    brief = read_text(root / "docs" / "qwen-code-brief.md")
    if brief is None:
        return repair_utf8_problems([
            "the Qwen brief at docs/qwen-code-brief.md is "
            "missing, so no Qwen claim in it can be checked"
        ])
    flat = re.sub(r"\s+", " ", brief)
    # Round 5 second seat. Each row of the R1 scope table
    # is pinned whole, so exchanging two figures between
    # scopes refuses by row.
    # Repair pass four. The pin is now one half of a closed
    # census. The census over the R1 scope table and the
    # two R2 exit tables refuses any row standing outside
    # the pinned set, so an added row refuses beside the
    # dropped and restated rows the presence pins refuse.
    for row in QWEN_R1_ROWS:
        if row not in flat:
            problems.append(
                "docs/qwen-code-brief.md R1 scope table does "
                "not carry the pinned row %r" % row
            )
    problems.extend(_table_census_problems(brief))
    for name, fragment in PINNED:
        if re.sub(r"\s+", " ", fragment) not in flat:
            problems.append(
                "the Qwen brief at docs/qwen-code-brief.md "
                "carries a dropped pin, namely " + name + ", "
                "which the brief must state in its pinned form"
            )
    # Round 15. The version sentence stands twice in the
    # brief, and the presence pin above reads only that it
    # stands somewhere, so moving a single occurrence to a
    # new version left the brief contradicting itself in
    # silence. The census counts the occurrences and
    # refuses any count but the two the brief carries.
    version_sentence = "The repo version stays 1.3.0"
    # Round 16. The census counts the sentence only where
    # its figure ends the number as written, so an
    # occurrence whose figure runs on past the pinned
    # form, as a four component figure does, is not
    # counted as the pinned sentence standing. A full
    # stop that ends the sentence still counts, because
    # the figure there is complete before the stop.
    found = len(re.findall(
        r"The repo version stays 1\.3\.0(?!\d|\.\d)", flat
    ))
    if found != 2:
        problems.append(
            "the Qwen brief at docs/qwen-code-brief.md "
            "states the version sentence %r %d times, not "
            "the two occurrences the brief carries"
            % (version_sentence, found)
        )
    # Round 15 delta. The census above counts the correct
    # sentence and nothing else, so a contradictory sentence
    # of the same shape could stand beside the two counted
    # ones, and a moved occurrence could hide behind a
    # fresh correct sentence that restores the count.
    # Every sentence of the shape is therefore read for
    # its figure, and a figure that differs from the repo
    # version refuses by name.
    # Round 16. The figure is captured whole as written,
    # so a figure carrying a fourth component is read as
    # the figure it is and refused, not read as its
    # pinned prefix and passed.
    for token in re.findall(
        r"The repo version stays (\d+(?:\.\d+)+)", flat
    ):
        if token != "1.3.0":
            problems.append(
                "the Qwen brief at docs/qwen-code-brief.md "
                "states the repo version as %s beside the "
                "pinned 1.3.0, so the brief contradicts "
                "itself on the version it states" % token
            )
    if "Runtime invocation stays UNVERIFIED" in flat:
        problems.append(
            "the Qwen brief at docs/qwen-code-brief.md "
            "carries the stale runtime UNVERIFIED "
            "wording the live run of 2026-10-29 falsified for "
            "the one scoped shape the brief now records"
        )
    for stated in re.findall(
            r"live Qwen Code session on (\d{4}-\d{2}-\d{2})", flat):
        if stated != "2026-10-29":
            problems.append(
                "the Qwen brief at docs/qwen-code-brief.md "
                "states the first live session date as " + stated
                + ", which differs from the recorded live "
                "session date 2026-10-29"
            )
    for stated in re.findall(
            r"second live session on (\d{4}-\d{2}-\d{2})", flat):
        if stated != "2026-11-03":
            problems.append(
                "the Qwen brief at docs/qwen-code-brief.md "
                "states the second live session date as " + stated
                + ", which differs from the recorded live "
                "session date 2026-11-03"
            )
    # Round 16. A version figure standing in the brief
    # in the plain version form, the word version before
    # its figure, is read against the one figure the
    # brief carries in that form, the bundled command
    # line figure from the releases listing, so a fresh
    # sentence stating a version in that form refuses by
    # name whatever figure it states and however many
    # components the figure carries.
    for token in re.findall(r"version (\d+(?:\.\d+)+)", flat):
        if token != "0.26.0":
            problems.append(
                "the Qwen brief at docs/qwen-code-brief.md "
                "states a version as %s in the plain version "
                "form, which differs from the bundled command "
                "line figure 0.26.0 the brief carries in that "
                "form" % token
            )
    # Round 16. The conversion figures the brief states,
    # the installed file size against the canonical file
    # and the installer mirror size against its input,
    # stand pinned as the recorded constants of the
    # round 37 conversion record, because the converted
    # bundle does not ship in this tree to be remeasured.
    # A restated figure refuses by name.
    for stated, against in re.findall(
        r"the installed file runs ([\d,]+) bytes against "
        r"([\d,]+) for the canonical file", flat
    ):
        if (int(stated.replace(",", "")),
                int(against.replace(",", ""))) != (15231, 15233):
            problems.append(
                "the Qwen brief at docs/qwen-code-brief.md "
                "states the installed file at %s bytes "
                "against %s for the canonical file, which "
                "differs from the recorded conversion "
                "figures of 15,231 against 15,233"
                % (stated, against)
            )
    for stated, against in re.findall(
        r"at ([\d,]+) bytes against ([\d,]+) for the input",
        flat
    ):
        if (int(stated.replace(",", "")),
                int(against.replace(",", ""))) != (355, 356):
            problems.append(
                "the Qwen brief at docs/qwen-code-brief.md "
                "states the installer mirror at %s bytes "
                "against %s for the input, which differs "
                "from the recorded conversion figures of "
                "355 against 356" % (stated, against)
            )
    problems.extend(derivation_problems(brief))
    qwen_section = rules_section(brief)
    if qwen_section is not None:
        problems.extend(
            operative_prose_problems(
                brief, qwen_section, "docs/qwen-code-brief.md")
        )
    problems.extend(negative_problems(brief))
    decisions = read_text(root / "docs" / "decisions.md")
    if decisions is None:
        problems.append(
            "the decision record at docs/decisions.md is "
            "missing, so the round 33 decision note cannot "
            "be checked"
        )
    else:
        note = decision_note(decisions)
        if note is None:
            problems.append(
                "the decision record at docs/decisions.md "
                "carries no round 33 decision note, so the "
                "note the gate pins does not stand"
            )
        else:
            flat_note = re.sub(r"\s+", " ", note)
            for fragment in DECISION_NOTE_PINS:
                if fragment not in flat_note:
                    problems.append(
                        "the decision record at "
                        "docs/decisions.md carries a decision "
                        "note that drops the pinned fragment "
                        + fragment
                    )
            if "round 31 note" in flat_note and "Round 31 note" not in decisions:
                problems.append(
                    "the decision record at docs/decisions.md "
                    "carries no round 31 note, so the note the "
                    "gate pins does not stand"
                )
    changelog = read_text(root / "CHANGELOG.md")
    if changelog is None:
        problems.append(
            "the changelog at CHANGELOG.md is missing, so "
            "its pinned Qwen fragments cannot be checked"
        )
    else:
        flat_log = re.sub(r"\s+", " ", changelog)
        for fragment in CHANGELOG_PINS:
            if fragment not in flat_log:
                problems.append(
                    "the changelog at CHANGELOG.md drops the "
                    "pinned fragment " + fragment
                )
    readme = read_text(root / "README.md")
    if readme is None:
        problems.append(
            "the README at README.md is missing, so its "
            "Qwen section cannot be checked"
        )
    else:
        section = readme_qwen_section(readme)
        if section is None:
            problems.append("the README Qwen section is missing")
        elif "COMMIT_SHA" not in section:
            problems.append("the README Qwen section lacks its pinned form")
        elif (
            "@scope/my-extension" in section
            or "unpinned test form" in section
            or "scoped npm route is untested" in section
        ):
            problems.append(
                "the README Qwen section carries the scoped npm "
                "test form that belongs in the brief only"
            )
    for path in root.rglob("qwen-extension.json"):
        problems.append(
            "a Qwen listing file ships at " + str(path)
            + ", and no Qwen listing file may ship in "
            "this tree"
        )
    return repair_utf8_problems(problems)


def main(root=None):
    root = ROOT if root is None else root
    problems = qwen_problems(root)
    if problems:
        for problem in problems:
            print("check_qwen: " + problem, file=sys.stderr)
        return 1
    print(
        "check_qwen: the Build 15 Qwen Code marketplace "
        "presence contract holds"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
