#!/usr/bin/env python3
"""Pin the Build 9 Codex review rules package contract.

The brief at docs/codex-review-brief.md is scoped Codex guidance
beside the canonical packet. It must never become a second packet,
a rival instruction source, so every rule it states carries a
derivation note naming the canonical skill section or gate it
restates or the primary OpenAI citation it reports. This script
pins that discipline without a Codex host. It requires every rule
in the rules section to carry a checkable derivation note, and it
pins the stated negatives and limits the round 21 lanes named.
The no product native calendar negative, the default branch only
continuous monitoring, the completed scan versus complete coverage
limit, the two distinct pauses, the per surface model pins, the
active restriction of Legacy with no promised retirement date,
the OpenAI owned figures, and the SECURITY.md policy context note
are all pinned as brief sentences, and the decision record must
name Build 9 with a decision 4 statement. A later edit that
drops any of them fails the gate instead of drifting in silence.
The round 5 repairs pin the canonical T0 name set in rule R4
member by member and as a whole, and refuse a scoped packet
gating claim family, stated as the packet gating rule
exercised in a run in any verb order, which the brief states
was not exercised, read sentence by sentence with a negated
claim clause stating no claim. Those families are narrow
and named, and prose outside them stays a human review
surface.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RULES_HEADING = "## The review rules"

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

# Primary OpenAI citations a derivation note may name, written as
# URL stems so the note pins the surface the claim was read from.
PRIMARY_CITATIONS = (
    "developers.openai.com/blog/custom-code-review-rules-for-codex",
    "learn.chatgpt.com/docs/security/",
    "learn.chatgpt.com/docs/environments/cloud-environments",
    "learn.chatgpt.com/docs/config-file/",
    "github.com/openai/codex-plugin-cc",
)

# Brief sentences the gate pins. Each is a fragment of the exact
# sentence the brief carries, so a later edit that softens or drops
# a stated negative or limit fails loudly.
PINNED = (
    ("the no calendar negative",
     "There is no product native calendar schedule"),
    ("the default branch only continuous monitoring",
     "monitors new commits on the repository's default branch"),
    ("the completed scan versus complete coverage limit",
     "A completed scan and complete coverage are separate claims"),
    ("the per repository monitoring pause",
     "the pause or enable toggle"),
    ("the automatic funding pause",
     "scanning pauses when funding is unavailable"),
    ("the Actions surface model pin",
     "The Actions example defaults to gpt-6-sol"),
    ("the workbench surface model pin",
     "recommends gpt-5.6-sol with xhigh reasoning effort"),
    ("the Legacy active restriction",
     "under active restriction"),
    ("the no promised retirement date",
     "no retirement date is promised"),
    ("the OpenAI owned figures",
     "OpenAI's on OpenAI's tasks"),
    ("the CLI 0.164.0 promotion",
     "CLI 0.164.0 is the later primary pin"),
    ("the SECURITY.md policy context note",
     "SECURITY.md is policy context, not executable instructions"),
    ("the auto review fails closed lifecycle",
     "fails closed on prompt build, review session, and parse "
     "failures"),
    ("the decision 4 statement",
     "Decision 4 binds this build like every other build"),
)

DECISION_HEADING = "## 18. Build 9"
DECISION_STATEMENT = "Decision 4 binds"


def rules_section(raw):
    """The text of the rules section, or None when it is missing."""
    start = raw.find(RULES_HEADING)
    if start < 0:
        return None
    rest = raw[start + len(RULES_HEADING):]
    match = re.search(r"(?m)^## ", rest)
    if match:
        rest = rest[:match.start()]
    return rest


def rule_blocks(section):
    """The rule blocks in order, split on their R numbered headings."""
    parts = re.split(r"(?m)^### R\d+\.", section)
    return [part for part in parts[1:]]


T0_MEMBERS = (
    ("the base names AGENTS.md and CLAUDE.md and SKILL.md and GEMINI.md at any depth",
     "AGENTS.md and CLAUDE.md and SKILL.md and GEMINI.md at any depth"),
    ("the Copilot instructions file name",
     "the Copilot instructions file name"),
    ("a path specific Copilot instructions file under the instructions folder of .github carrying the .instructions.md suffix",
     "a path specific Copilot instructions file under the instructions folder of .github carrying the .instructions.md suffix"),
    ("the .cursorrules file name", "the .cursorrules file name"),
    ("a Cursor rules file under a .cursor folder",
     "a Cursor rules file under a .cursor folder"),
    ("a Claude rules file under a .claude/rules folder",
     "a Claude rules file under a .claude/rules folder"),
    ("a Kimi plugin manifest named kimi.plugin.json at any depth",
     "A Kimi plugin manifest named kimi.plugin.json at any depth"),
    ("a Kimi plugin agent, hook script or manifest under a .kimi-plugin folder",
     "a Kimi plugin agent, hook script or manifest under a .kimi-plugin folder are flagged too"),
    ("the rename flag for either name",
     "A renamed file is flagged when either its old name or its new name stands in the set"),
    ("a review packet output style under the output-styles folder of the plugin",
     "A review packet output style under the output-styles folder of the plugin is flagged too"),
)

T0_SET_TEXT = (
    "The name set is AGENTS.md and CLAUDE.md and SKILL.md and "
    "GEMINI.md at any depth, the Copilot instructions file name, "
    "a path specific Copilot instructions file under the "
    "instructions folder of .github carrying the "
    ".instructions.md suffix, the .cursorrules file name, a "
    "Cursor rules file under a .cursor folder, and a Claude "
    "rules file under a .claude/rules folder. A Kimi plugin "
    "manifest named kimi.plugin.json at any depth and a Kimi "
    "plugin agent, hook script or manifest under a .kimi-plugin "
    "folder are flagged too. A renamed file is flagged when "
    "either its old name or its new name stands in the set. A "
    "review packet output style under the output-styles folder "
    "of the plugin is flagged too."
)


def t0_problems_for_section(section):
    """Problems with rule R4 stating the canonical T0 set."""
    problems = []
    for block in rule_blocks(section):
        flat = re.sub(r"\s+", " ", block)
        if "The name set is" not in flat:
            continue
        for label, fragment in T0_MEMBERS:
            if fragment not in flat:
                problems.append(
                    "docs/codex-review-brief.md rule R4 does not "
                    "state the canonical T0 member %s" % label
                )
        start = flat.find("The name set is")
        end_marker = "of the plugin is flagged too."
        end = flat.find(end_marker, start)
        stated = flat[start:end + len(end_marker)] if end >= 0 else ""
        if stated != T0_SET_TEXT:
            problems.append(
                "docs/codex-review-brief.md rule R4 states a "
                "name set that differs from the canonical T0 "
                "set, with a member missing or added"
            )
    return problems


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


def derivation_problems(section):
    """Problems with the rules derivation discipline."""
    problems = []
    blocks = rule_blocks(section)
    if not blocks:
        return ["the rules section carries no R numbered rules"]
    for index, block in enumerate(blocks, start=1):
        flat = re.sub(r"\s+", " ", block)
        if "Derives from" not in flat:
            problems.append(
                "rule R%d carries no derivation note, so it would be "
                "a rival instruction source" % index
            )
            continue
        note = flat.split("Derives from", 1)[1]
        if not deliberate_source(note):
            problems.append(
                "rule R%d names no canonical skill section, gate, or "
                "primary OpenAI citation in its derivation note"
                % index
            )
    return problems


def _claim_clause_negated(sentence, start):
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
    prefix = sentence[:start]
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
        re.search(r"\b(not|no|never)\b|n't", prefix[cut:])
    )


def _recovery_binding_problems(text):
    """Problems with a sentence binding the figures exchanged.

    Repair pass. The presence pins bind the figures in
    place, and this reading refuses the additive form of
    the same exchange, in the form the ZCode gate uses for
    its additive figure exchange. Any sentence that binds
    the 98 percent figure to the baseline subject or the
    58.3 percent figure to the rule guided subject states
    the exchange, wherever the sentence stands. The bound
    on the subject stretch keeps the shipped worked
    example sentence, which binds both figures correctly
    across a longer stretch, outside the reading.
    """
    low = re.sub(r"\s+", " ", text.lower())
    for sentence in re.split(r"(?<=[.!?])\s+", low):
        if (
            re.search(r"\bbaseline\b[^.]{0,80}\b98 percent\b", sentence)
            or re.search(
                r"\brule guided\b[^.]{0,80}\b58\.3 percent\b", sentence
            )
            or "98 percent for the baseline" in sentence
            or "58.3 percent for the rule guided" in sentence
        ):
            return [
                "docs/codex-review-brief.md binds the recovery "
                "figures to the wrong subjects, the baseline and "
                "rule guided figures exchanged"
            ]
    return []


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
    judged, and a sentence is operative when it speaks to
    or about the reviewing session, naming the reviewer or
    the session or addressing the reader as you, and it
    either carries a duty modal or opens with an imperative
    verb of the instruction family. A descriptive sentence
    about the session states no instruction and passes, and
    an instruction with no session subject stands outside
    this family and is left to its own pins. The identical
    reading stands in each of the nine brief gates, because
    the nine briefs share the one discipline and a closure
    that covered fewer than all nine would leave the same
    door open at the next brief.
    """
    outside = raw.replace(section, " ", 1) if section else raw
    flat = re.sub(r"\s+", " ", outside)
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
    for line in outside.splitlines():
        fragment = re.sub(r"^[#>*\-\d.\s`]+", "", line)
        judge(fragment, fragment.strip())
    return problems


def brief_problems(root=None):
    """Problems with the Build 9 brief's stated contract."""
    root = ROOT if root is None else root
    path = root / "docs" / "codex-review-brief.md"
    if path.exists() and not path.is_file():
        return [
            "cannot read docs/codex-review-brief.md, "
            "it is not a regular file"
        ]
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [
            "cannot read docs/codex-review-brief.md, it cannot "
            "be read as UTF-8 text"
        ]
    except OSError as exc:
        return ["cannot read docs/codex-review-brief.md, %s" % exc]
    text = re.sub(r"\s+", " ", raw)
    problems = []
    # Repair pass. The glance check is a scoped negative
    # family, not a literal membership test. A sentence
    # states the claim when it joins the packet gating
    # subject to an exercise verb form in either order, and
    # a negation in the claim clause states no claim.
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        low = sentence.lower()
        verb = re.search(r"\bexercis\w*\b", low)
        if (
            "packet gating" in low
            and verb
            and not _claim_clause_negated(low, verb.start())
        ):
            problems.append(
                "docs/codex-review-brief.md claims the packet "
                "gating rule was exercised in the paired run, beside "
                "its pinned sentence that it was not exercised"
            )
            break
    problems.extend(_recovery_binding_problems(text))
    section = rules_section(raw)
    if section is None:
        problems.append(
            "docs/codex-review-brief.md carries no %r section"
            % RULES_HEADING
        )
    else:
        problems.extend(derivation_problems(section))
        problems.extend(t0_problems_for_section(section))
    for label, fragment in PINNED:
        if fragment not in text:
            problems.append(
                "docs/codex-review-brief.md does not state %s" % label
            )
    if "98 percent" not in text or "58.3 percent" not in text:
        problems.append(
            "docs/codex-review-brief.md does not report the 98 "
            "percent against 58.3 percent figures"
        )
    # Round 5 second seat. The two evidence figures are
    # bound to their subjects, so exchanging them in place
    # refuses.
    if not re.search(r"recovered 98 percent", text):
        problems.append(
            "docs/codex-review-brief.md does not bind the 98 "
            "percent figure to the rule guided recovery"
        )
    if not re.search(r"58\.3 percent for the baseline", text):
        problems.append(
            "docs/codex-review-brief.md does not bind the "
            "58.3 percent figure to the baseline control"
        )
    problems.extend(round5_codex_claim_problems(text))
    if section is not None:
        problems.extend(
            operative_prose_problems(
                raw, section, "docs/codex-review-brief.md")
        )
    return problems


def round5_codex_claim_problems(text):
    """Problems with two additive claims the brief denies.

    Round 5 second seat. No sentence may claim a product
    native calendar schedule, which the scheduled scans
    section denies, and no sentence may state that a
    SECURITY.md file is executable instruction, which rule
    R6 denies. A sentence carrying the pinned denial states
    no claim and is skipped.
    """
    problems = []
    low = text.lower()
    for sentence in re.split(r"(?<=[.!?])\s+", low):
        if "calendar" in sentence and re.search(
            r"\bschedul\w*\b", sentence
        ) and not any(
            guard in sentence
            for guard in ("no product", "must not", "never", "no ")
        ):
            problems.append(
                "docs/codex-review-brief.md claims a product "
                "native calendar schedule, which its scheduled "
                "scans section denies"
            )
            break
    for sentence in re.split(r"(?<=[.!?])\s+", low):
        if (
            "security.md" in sentence
            and "executable instruction" in sentence
            and "not executable" not in sentence
            and "policy context" not in sentence
        ):
            problems.append(
                "docs/codex-review-brief.md states a "
                "SECURITY.md file is executable instruction, "
                "which rule R6 denies"
            )
            break
    return problems


def decision_problems(root=None):
    """Problems with the Build 9 decision record."""
    root = ROOT if root is None else root
    path = root / "docs" / "decisions.md"
    if path.exists() and not path.is_file():
        return [
            "cannot read docs/decisions.md, "
            "it is not a regular file"
        ]
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [
            "cannot read docs/decisions.md, it cannot be read "
            "as UTF-8 text"
        ]
    except OSError as exc:
        return ["cannot read docs/decisions.md, %s" % exc]
    start = raw.find(DECISION_HEADING)
    if start < 0:
        return [
            "docs/decisions.md carries no Build 9 decision record"
        ]
    rest = raw[start + len(DECISION_HEADING):]
    match = re.search(r"(?m)^## ", rest)
    record = rest[:match.start()] if match else rest
    if DECISION_STATEMENT not in record:
        return [
            "the Build 9 decision record carries no decision 4 "
            "statement, which every landed build must record"
        ]
    return []


def codex_problems(root=None):
    """Every Build 9 Codex review rules package problem."""
    problems = []
    problems.extend(brief_problems(root))
    problems.extend(decision_problems(root))
    return problems


def main(root=None):
    problems = codex_problems(root)
    if problems:
        for problem in problems:
            print("check_codex: %s" % problem, file=sys.stderr)
        return 1
    print("check_codex: the Build 9 Codex review rules hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
