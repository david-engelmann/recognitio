#!/usr/bin/env python3
"""Pin the Build 15 Qwen Code marketplace presence contract.

The brief at docs/qwen-code-brief.md records the Qwen figure
basis and scope table with no single figure presented as the
Qwen figure, the wrapper exits 0 1 and 3 kept separate from
the internal verify exit 4, the Agent Plugins v1 support
matrix in full, the Qoder and scoped npm routes, the
prefixed naming rule with its cancellation exception, the
shared skills alias with its precedence, the conversion
fidelity record with runtime invocation left UNVERIFIED,
the bundled CLI version from the primary releases listing,
and the conditional publication draft with no listing file
shipped. Decision 4 binds this build like every other
build. The brief documents the contract and never enforces
it on a live Qwen host, so this script pins the contract
without a Qwen client. It requires the brief to keep the
stated pins with a derivation note on every rule, and it
runs a meaning based negative check with number
normalisation and a separation guard, so a reworded
contradiction fails instead of passing on changed wording
alone.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / "docs" / "qwen-code-brief.md"
DECISIONS = ROOT / "docs" / "decisions.md"
CHANGELOG = ROOT / "CHANGELOG.md"
README = ROOT / "README.md"

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
    ("the Qoder originSource",
     "recorded originSource as Qoder"),
    ("the AgentPlugins originSource",
     "recorded originSource as AgentPlugins"),
    ("the side shapes not carried",
     "Side shapes do not ride in"),
    ("the runtime UNVERIFIED",
     "Runtime invocation stays UNVERIFIED"),
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
FIGURE_AGENTS = "reviewers?|workers?|bots?"

# Scope words that turn a generic agent count into a
# figure claim. Large and practice cover the G-01 scope
# shapes, high effort and top effort cover the shipped
# effort shapes, and same repository and same deadline
# cover the long F-Q17 shape.
FIGURE_SCOPE = (
    "large|high effort|top effort|practice|"
    "same repository|same deadline"
)

FIGURE_WORDS = FIGURE_ADVERBS + "|" + FIGURE_AGENTS

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
# not a wording variant of a covered family. The wrapper
# and activation families keep the bounded window above,
# because their tokens state separate claims that a long
# sentence can hold apart.
FIGURE_SPAN = ".*"

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
    units = []
    buffer = []
    in_code = False

    def flush():
        if not buffer:
            return
        joined = " ".join(buffer)
        buffer.clear()
        for sentence in re.split(r"(?<=[.!?])\s+", joined.strip()):
            if sentence.strip():
                units.append(sentence.strip())

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
            units.append(line)
            continue
        if line.startswith("|") or line.startswith("#"):
            flush()
            units.append(line)
            continue
        buffer.append(line)
    flush()
    return units


def figure_problem(sentence):
    """Whether a sentence states a single Qwen figure."""
    if re.search(
        r"\b" + FIGURE_NUMBER + r"\b" + FIGURE_SPAN + r"\b("
        + FIGURE_ADVERBS + r")\b", sentence
    ):
        return True
    if re.search(
        r"\b(" + FIGURE_ADVERBS + r")\b" + FIGURE_SPAN + r"\b"
        + FIGURE_NUMBER + r"\b", sentence
    ):
        return True
    if not re.search(
        r"\b(" + FIGURE_SCOPE + r")\b", sentence
    ):
        return False
    if re.search(
        r"\b" + FIGURE_NUMBER + r"\b" + FIGURE_SPAN + r"\b("
        + FIGURE_AGENTS + r")\b", sentence
    ):
        return True
    return bool(re.search(
        r"\b(" + FIGURE_AGENTS + r")\b" + FIGURE_SPAN + r"\b"
        + FIGURE_NUMBER + r"\b", sentence
    ))


def wrapper_problem(sentence):
    """Whether a sentence states a wrapper exit of 4.

    A wrapper noun plus a bare 4 is not enough. The
    sentence must also carry an exit, code, or return
    token, so a sentence about a wrapper supporting 4
    tools passes while an exit claim fires.
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
    return bool(re.search(
        r"\b4\b" + WINDOW + r"\b(" + WRAPPER_WORDS + r")\b",
        sentence,
    ))


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
    return any(word in line for word in GUARD_WORDS)


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
    for line in sentence_units(normalise(text)):
        if not re.search(r"\b(never|no sentence|not a wrapper)\b", line):
            if wrapper_problem(line):
                problems.append("wrapper exit plant: " + line[:120])
        if guarded(line):
            continue
        if figure_problem(line):
            problems.append("figure plant: " + line[:120])
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
        if re.search(r"\bproven to run\b", line):
            problems.append("conversion plant: " + line[:120])
        if re.search(r"\bfull packet workflow in qwen\b", line) and "not" not in line:
            problems.append("conversion plant: " + line[:120])
        if re.search(r"central qwen marketplace[^.]{0,40}\b(submission|approval)\b", line):
            problems.append("publication plant: " + line[:120])
        if re.search(r"vs code marketplace[^.]{0,40}\b(publication|publish)\b", line):
            problems.append("publication plant: " + line[:120])
    return problems


def read_text(path):
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def deliberate_source(note):
    for title in CANONICAL_SECTIONS:
        if re.search(
            r"canonical skill[^.;]{0,200}" + re.escape(title), note
        ):
            return True
    if any(stem in note for stem in PRIMARY_CITATIONS):
        return True
    return "decision 26" in note or "Decision 4" in note or "decision 13" in note


def rules_section(raw):
    start = raw.find(RULES_HEADING)
    if start < 0:
        return None
    return raw[start:]


def derivation_problems(raw):
    section = rules_section(raw)
    if section is None:
        return ["the Qwen rules section is missing"]
    problems = []
    parts = re.split(r"\n### R\d+\. ", section)
    for part in parts[1:]:
        head = part.split("\n", 1)[0]
        if "Derives from" not in part:
            problems.append("rule without derivation note: " + head)
            continue
        note = part[part.find("Derives from"):]
        if not deliberate_source(note):
            problems.append("derivation note names no source: " + head)
    if len(parts) - 1 < 10:
        problems.append("fewer than ten Qwen rules found")
    return problems


def decision_note(raw):
    start = raw.find(DECISION_NOTE_MARKER)
    if start < 0:
        return None
    end = raw.find("\n## ", start)
    return raw[start:] if end < 0 else raw[start:end]


def readme_qwen_section(raw):
    start = raw.find("### Qwen Code")
    if start < 0:
        return None
    rest = raw[start:]
    for marker in ("\n### ", "\n## "):
        end = rest.find(marker, 1)
        if end > 0:
            return rest[:end]
    return rest


def qwen_problems(root):
    problems = []
    brief = read_text(root / "docs" / "qwen-code-brief.md")
    if brief is None:
        return ["the Qwen brief is missing"]
    flat = re.sub(r"\s+", " ", brief)
    for name, fragment in PINNED:
        if re.sub(r"\s+", " ", fragment) not in flat:
            problems.append("dropped pin: " + name)
    problems.extend(derivation_problems(brief))
    problems.extend(negative_problems(brief))
    decisions = read_text(root / "docs" / "decisions.md")
    if decisions is None:
        problems.append("the decision record is missing")
    else:
        note = decision_note(decisions)
        if note is None:
            problems.append("the round 33 decision note is missing")
        else:
            flat_note = re.sub(r"\s+", " ", note)
            for fragment in DECISION_NOTE_PINS:
                if fragment not in flat_note:
                    problems.append("decision note drops: " + fragment)
            if "round 31 note" in flat_note and "Round 31 note" not in decisions:
                problems.append("the round 31 note is missing")
    changelog = read_text(root / "CHANGELOG.md")
    if changelog is None:
        problems.append("the changelog is missing")
    else:
        flat_log = re.sub(r"\s+", " ", changelog)
        for fragment in CHANGELOG_PINS:
            if fragment not in flat_log:
                problems.append("changelog drops: " + fragment)
    readme = read_text(root / "README.md")
    if readme is None:
        problems.append("the README is missing")
    else:
        section = readme_qwen_section(readme)
        if section is None:
            problems.append("the README Qwen section is missing")
        elif "COMMIT_SHA" not in section or "unpinned test form" not in section:
            problems.append("the README Qwen section lacks its pinned form")
    for path in root.rglob("qwen-extension.json"):
        if "scratch" not in str(path):
            problems.append("a Qwen listing file ships: " + str(path))
    return problems


def main():
    problems = qwen_problems(ROOT)
    if problems:
        for problem in problems:
            print("check_qwen: " + problem)
        return 1
    print("check_qwen: Qwen contract holds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
