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
    ("seventeen", "17"),
    ("sixteen", "16"),
    ("twelve", "12"),
    ("dozen", "12"),
    ("four", "4"),
)

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


def normalise(text):
    """Lowercase text with spelled out numbers as digits."""
    out = text.lower()
    for word, digit in NUMBER_WORDS:
        out = re.sub(r"\b" + word + r"\b", digit, out)
    return out


def guarded(line):
    return any(word in line for word in GUARD_WORDS)


def negative_problems(text):
    """Meaning based negatives over one line at a time."""
    problems = []
    for raw in normalise(text).splitlines():
        line = raw.strip()
        if not line:
            continue
        if not re.search(r"\b(never|no sentence|not a wrapper)\b", line):
            if re.search(r"\b(wrapper|outer gate)\b[^.]{0,80}\b4\b", line):
                problems.append("wrapper exit plant: " + line[:120])
            elif re.search(r"\b4\b[^.]{0,80}\b(wrapper|outer gate)\b", line):
                problems.append("wrapper exit plant: " + line[:120])
        if guarded(line):
            continue
        if re.search(r"\b(12|16|17|19)\b[^.]{0,60}\b(parallel|concurrent|simultaneous|reviewers|workers|bots|side by side|together|at once)\b", line):
            problems.append("figure plant: " + line[:120])
        if re.search(r"\breturns 4\b", line):
            problems.append("wrapper exit plant: " + line[:120])
        if re.search(r"skills\.disabled blocks only", line):
            problems.append("disabled naming plant: " + line[:120])
        if re.search(r"skills\.enabled[^.]{0,80}\bbare name\b", line) and "prefixed" not in line:
            problems.append("enabled naming plant: " + line[:120])
        if re.search(r"legacy sse[^.]{0,40}\bactivat", line):
            problems.append("activation plant: " + line[:120])
        if re.search(r"\bcommands\b[^.]{0,40}\bagents\b[^.]{0,40}\bhooks\b[^.]{0,40}\b(light up|activat)", line):
            problems.append("activation plant: " + line[:120])
        if not re.search(r"\bnot\b[^.]{0,25}\bactivat", line) and "unverified" not in line:
            if re.search(r"\bactivat\w*\b[^.]{0,40}\b(hooks|commands|agents|client namespaces|legacy sse)\b", line):
                problems.append("activation plant: " + line[:120])
            elif re.search(r"\b(hooks|commands|agents|client namespaces|legacy sse)\b[^.]{0,40}\bactivat", line):
                problems.append("activation plant: " + line[:120])
        if re.search(r"\.agents/skills[^.]{0,40}\bdrift\b", line):
            problems.append("alias drift plant: " + line[:120])
        if re.search(r"\.agents/skills[^.]{0,60}\bdiscover\w*\b", line):
            problems.append("alias discovery plant: " + line[:120])
        if re.search(r"\.agents/skills[^.]{0,60}\b(winning|wins)\b", line):
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
