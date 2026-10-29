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
    ("the ZCode skill page URL",
     "https://zcode.z.ai/en/docs/skill"),
    ("the ZCode plugin page URL",
     "https://zcode.z.ai/en/docs/plugin"),
    ("the decision 4 statement",
     "Decision 4 binds this build like every other build"),
)

DECISION_HEADING = "## 27. Build 16"
DECISION_STATEMENT = "Decision 4 binds"


def read_text(path):
    if path.exists() and not path.is_file():
        return None
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


def negative_problems(root=None):
    """R36-RT-05. No sentence may execute the registered
    fields or state a description figure other than the
    pinned cap.

    The pins prove the correct sentences are stated, but an
    added sentence passes while the pins stay in place,
    because no check read the contradicting sentence. The
    brief states the register but do not execute behavior
    for channels, lspServers, outputStyles, and settings,
    and a description cap of 1024 characters. A planted
    sentence that has ZCode executing settings from a
    plugin manifest, or that states a description figure
    other than 1024 characters, must fail the gate. The
    shipped sentences that state the negative posture, or
    that hold execution in a future conditional, carry
    their guard words and are skipped.
    """
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "zcode-plugin-brief.md")
    if raw is None:
        return ["docs/zcode-plugin-brief.md is missing"]
    body = re.sub(r"(?m)^#{1,6} .*$", "", raw)
    text = re.sub(r"\s+", " ", body)
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", text)
        if sentence.strip()
    ]
    problems = []
    for sentence in sentences:
        low = sentence.lower()
        # R36 gate repair. Guards judge one clause at a
        # time, never the whole sentence, because the
        # review rode a guard phrase in a first clause
        # while a second clause asserted the execution the
        # guard belongs to. The execution patterns read
        # the passive order and the verb runs beside the
        # execute stem. The description branch reads the
        # singular character form, the short chars form,
        # and spelled figures beside the digit form, and a
        # clause that scopes its figure to a different host
        # states no ZCode cap and is skipped.
        # R37-RT-09. The execution reading now removes the
        # guarded clauses and judges what remains at
        # sentence scope, and the description reading
        # extracts figures from the whole sentence and
        # judges each against its own clause.
        spans = _clause_spans(low)
        # R37F-RT-13. A guard removes only the text it
        # governs, up to the end of the guard phrase
        # itself. A clause carrying a guard phrase and an
        # execution claim after it, register but also
        # executes, keeps the execution text under
        # judgement instead of dropping the whole clause.
        # Confirmation repair. The text before the first
        # guard phrase of a clause stays under judgement
        # too, because an execution claim standing before
        # a guard phrase in the same clause, executes the
        # settings it declares and does not execute the
        # borrowed ones, is a claim the guard does not
        # govern either.
        # R38-RT-10. A guard phrase removes only its own
        # words, and every other word of the clause stays
        # under judgement, including the text standing
        # between two guard phrases. The earlier cut kept
        # only the text before the first guard phrase and
        # after the last one, so an execution claim placed
        # between two guard phrases was dropped with the
        # governed text and never judged.
        judged_parts = []
        for text, offset in spans:
            judged_text = text
            for guard in _CLAUSE_GUARDS:
                judged_text = judged_text.replace(guard, " ")
            judged_parts.append(judged_text)
        judged = " ".join(judged_parts)
        problem = _execution_problem(judged)
        if problem is not None:
            problems.append(problem)
            return problems
        problem = _description_problem(low, spans)
        if problem is not None:
            problems.append(problem)
            return problems
    return problems


_CLAUSE_GUARDS = (
    "do not execute",
    "does not execute",
    "not execute",
    "never execute",
    "register but",
    "runs no code",
    "unexecuted",
    "until zcode executes",
)

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


def _word_number_value(tokens):
    """The value of a spelled number token run, or None."""
    total = 0
    current = 0
    for token in tokens:
        if token in _WORD_ONES:
            current += _WORD_ONES[token]
        elif token in _WORD_TENS:
            current += _WORD_TENS[token]
        elif token == "hundred":
            current *= 100
        elif token == "thousand":
            total += (current or 1) * 1000
            current = 0
        elif token == "and":
            continue
        else:
            return None
    return total + current


def _description_figures(sentence):
    """Every character figure in a sentence, with its start.

    Each entry is the figure text and the offset where the
    figure starts, so the caller can judge the figure
    against the clause that holds it. Digits standing
    directly before the unit word are one form. A digit
    separated from its unit by a qualifier clause, capped
    at 2048, measured in characters, is the same figure in
    another form, and a spelled run before the unit word
    is the third form.
    """
    figures = []
    covered = []
    for match in re.finditer(
        r"(\d+)\s*(?:character|characters|chars)\b", sentence
    ):
        figures.append((match.group(1), match.start(1)))
        covered.append((match.start(), match.end()))
    # R37F-RT-14. Short filler before the qualifier verb,
    # with the limit measured in characters, states the
    # same separated figure, so a few plain words may
    # stand between the comma and the qualifier.
    # Confirmation repair. The filler allowance was a
    # measured bound at twelve plain words.
    # R38-RT-12. Fourteen plain words defeated that bound
    # the same way nine defeated the six word allowance
    # before it, so the reading no longer counts filler
    # words at all. The qualifier phrase itself, a
    # qualifier verb with in characters, is what binds
    # the figure, and the stretch between the comma and
    # the qualifier may hold any words of the same clause,
    # stopping only at a semicolon or the sentence end.
    for match in re.finditer(
        r"(?<![\d.])(\d+)(?![\d.])\s*,\s*"
        r"[^.;]*?"
        r"(?:measured|counted|expressed|given|stated)"
        r"\s+in\s+(?:characters?|chars)\b",
        sentence,
    ):
        figures.append((match.group(1), match.start(1)))
        covered.append((match.start(), match.end()))
    for match in re.finditer(
        r"\b(?:character|characters|chars)\b", sentence
    ):
        if any(
            start <= match.start() < end for start, end in covered
        ):
            continue
        tokens = sentence[:match.start()].split()
        run = []
        for token in reversed(tokens):
            if (
                token in _WORD_ONES
                or token in _WORD_TENS
                or token in ("hundred", "thousand", "and")
            ):
                run.append(token)
            else:
                break
        run.reverse()
        while run and run[-1] == "and":
            run.pop()
        if run:
            value = _word_number_value(run)
            if value is not None:
                start = match.start() - len(" ".join(run)) - 1
                figures.append((str(value), max(0, start)))
    return figures


def _clause_spans(low):
    """The clauses of one sentence with their start offsets.

    The split is the gate clause split, on comma and, on a
    bare comma, and on a semicolon, and each entry is the
    clause text and the offset where it starts in the
    sentence.
    """
    spans = []
    start = 0
    for match in re.finditer(r",\s+and\s+|,\s+|;\s*", low):
        spans.append((low[start:match.start()], start))
        start = match.end()
    spans.append((low[start:], start))
    return [
        (clause.strip(), offset + (len(clause) - len(clause.lstrip())))
        for clause, offset in spans
        if clause.strip()
    ]


def _execution_problem(judged):
    """Whether the judged text executes a registered field.

    R37-RT-09. The judged text is the sentence with the
    guarded text removed, and the patterns read it at
    sentence scope. The clause at a time reading let a
    parenthetical clause isolate the execution verb from
    the field it executes, so neither clause fired alone.
    A guard removes only the text up to its own phrase, so
    a guard phrase in one clause still cannot shelter an
    execution claim in another, or one standing after the
    guard phrase inside its own clause.
    """
    if (
        re.search(
            r"\bzcode\s+(execut\w*|runs?|ran)\b[^.]*"
            r"\b(settings|channels|lspservers|outputstyles)\b",
            judged,
        )
        or re.search(
            r"\bexecut\w*\b[^.]*\b(settings|channels"
            r"|lspservers|outputstyles)\b",
            judged,
        )
        or re.search(
            r"\b(settings|channels|lspservers|outputstyles)\b"
            r"[^.]*\b(are|is|were|was|gets?)\s+"
            r"(?:\w+ly\s+)?(execut\w*|run|ran)\b"
            r"[^.]*\bzcode\b",
            judged,
        )
    ):
        return (
            "the zcode brief has ZCode executing a "
            "registered plugin field, which the register "
            "but do not execute rule forbids"
        )
    return None


def _description_problem(sentence, spans):
    """Whether a sentence states a description figure
    other than the pinned cap.

    Figures are extracted from the whole sentence and each
    figure is judged against the clause that holds it. A
    clause that scopes its figure to a different host
    states no ZCode cap and its figure is skipped, but a
    clause that names ZCode states the ZCode cap even when
    it calls the cap its own, because the possessive in
    that clause belongs to ZCode itself. R37-RT-09.
    """
    for figure, start in _description_figures(sentence):
        clause = ""
        for text, offset in spans:
            if offset <= start:
                clause = text
        if "description" not in clause:
            continue
        if "zcode" not in clause and re.search(
            r"\b(different|another|other)\s+host\b|\bits own\b",
            clause,
        ):
            # R37F-RT-14. The skip stands only while no
            # clause of the sentence binds that cap to
            # ZCode by reference. A sentence that has
            # ZCode inherit or adopt that cap states the
            # figure as the ZCode cap after all.
            # Confirmation repair. The binding is the
            # reference itself, an inheritance verb or a
            # deictic naming of the cap or the limit, so
            # uses that limit binds the same way inherits
            # that cap does.
            # R38-RT-11. The reference forms include the
            # same figure naming, uses the same figure,
            # beside the same cap and same limit forms, and
            # the binding verbs include the use and follow
            # and apply forms beside inherit and adopt.
            if re.search(
                r"\bzcode\b[^.]*(\b(inherit\w*|adopt\w*"
                r"|us\w+|follow\w*|appl\w*)\b"
                r"|\b(that|this)\s+(cap|limit|figure)\b"
                r"|\bsame\s+(cap|limit|figure|number)\b)",
                sentence,
            ):
                pass
            else:
                continue
        if int(figure) != 1024:
            return (
                "the zcode brief states a plugin "
                "description cap of %s characters, "
                "other than the pinned cap of 1024" % figure
            )
    return None


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
    problems.extend(negative_problems(root))
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
