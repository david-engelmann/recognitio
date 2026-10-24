#!/usr/bin/env python3
"""Pin the Build 11 CodeRabbit guidelines contract.

The brief at docs/coderabbit-review-brief.md records the
CodeRabbit rename direction, the focus toggle table as a
constraint, the Quiet Chill and Assertive profiles, the pre
merge checks with Error mode merge blocking, the October 2026
entries, and the guideline file provenance now shown in review
summaries, all from the primary CodeRabbit docs. Decision 4
binds this build like every other build. The guidelines advise
and never enforce, so this script pins the contract without a
CodeRabbit host. It requires the brief to keep the stated pins,
the focus constraint that high trims verbosity and never reads
as deeper review, the named focus and profile axes, the summary
fold at high, the rename direction, the guideline provenance,
and the fourth .claude/rules/ guideline source, and every
guideline to carry a checkable derivation note, so the scoped
guidance cannot become a rival instruction source. A later edit
that drops any of them fails the gate instead of drifting in
silence.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / "docs" / "coderabbit-review-brief.md"
DECISIONS = ROOT / "docs" / "decisions.md"

GUIDELINES_HEADING = "## The guidelines"

# Canonical skill sections a derivation note may name. These are
# the section titles of .agents/skills/recognitio/SKILL.md, and a
# note that names one says which canonical section the guideline
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

# Primary CodeRabbit citations a derivation note may name,
# written as URL stems so the note pins the surface the claim
# was read from.
PRIMARY_CITATIONS = (
    "docs.coderabbit.ai/changelog",
    "docs.coderabbit.ai/configuration",
    "docs.coderabbit.ai",
)

# Brief sentences the gate pins. Each is a fragment of the exact
# sentence the brief carries, so a later edit that softens or
# drops a stated pin, quote, or limit fails loudly.
PINNED = (
    ("the rename direction, Fix comments was Autofix",
     "Fix comments (formerly Autofix) fixes the review comments "
     "you select"),
    ("the rename direction, Autofix was Autopilot",
     "Autofix (formerly Autopilot) brings a pull request to "
     "completion"),
    ("the compat aliases",
     "keep working as aliases for a limited time for backward "
     "compatibility"),
    ("the focus constraint, high trims",
     "High trims verbosity"),
    ("the focus constraint, no deeper analysis",
     "It does not deepen analysis"),
    ("the never deeper reading",
     "must never treat it as deeper review"),
    ("the high table row",
     "reviews down to essential content only"),
    ("the cumulative table",
     "Higher levels are cumulative"),
    ("the leanest reviews caption",
     "Strip everything non-essential for the leanest reviews"),
    ("the summary fold at high",
     "moves from off to on at high"),
    ("the fold is not analysis",
     "folds the summary into the walkthrough"),
    ("the focus axis named",
     "On the focus axis"),
    ("the profile axis named",
     "On the profile axis"),
    ("the focus levels",
     "casual, balanced, or high"),
    ("the profile values",
     "quiet, chill, and assertive"),
    ("the Quiet launch",
     "July 2 2026"),
    ("the Quiet inline behavior",
     "only the most important comments posted inline"),
    ("the profile reference",
     "`quiet` for only the most important feedback"),
    ("the Error mode merge blocking",
     "requires resolution before merging"),
    ("the security merge blocking entry",
     "publishing alone does not block"),
    ("the block until the check passes",
     "can block the PR until the check passes"),
    ("the Automatic Approvals surface",
     "the Automatic Approvals surface"),
    ("the approval risk limits",
     "Optional risk limits keep pull requests above a chosen "
     "Merge Risk for human approval"),
    ("the Deep Scan linked repositories",
     "Deep Scan with linked repositories"),
    ("the 20 linked repositories limit",
     "up to 20 linked repositories"),
    ("the Deep Scan linked source platforms",
     "available in the scan trigger flow on GitHub Cloud and "
     "GitHub Enterprise Server and GitLab Cloud"),
    ("the Deep Scan linked source platform limit",
     "not available in that flow for self hosted GitLab or "
     "Azure DevOps or Bitbucket"),
    ("the Deep Scan linked source default branch pin",
     "pinned to a commit on each linked repository default "
     "branch"),
    ("the plan linked repository limit",
     "subject to the plan linked repository limit"),
    ("the manual versus automatic linking",
     "Essentials supports manual links"),
    ("the findings attached to primary",
     "remain attached to the primary repository"),
    ("the CLI v0.9.0 cloud tasks",
     "CLI v0.9.0 for cloud task work"),
    ("the signed Linux release verification",
     "verifies signed Linux releases"),
    ("the Deep Scan API on all plans",
     "code findings API on all plans"),
    ("the author approval key",
     "prevent pull request authors from using `@coderabbitai "
     "approve`"),
    ("the guideline provenance",
     "configured, auto-discovered, or an Agent Skill"),
    ("the fourth guideline source",
     "adds `.claude/rules/` as a fourth guideline source"),
    ("the paths scoping",
     "globs in `paths` are relative to the project root"),
    ("the pairing not a packet",
     "a review pairing source, never a second packet"),
    ("the no calendar negative",
     "the brief claims none"),
    ("the decision 4 statement",
     "Decision 4 binds this build like every other build"),
)

DECISION_HEADING = "## 20. Build 11"
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


def guidelines_section(raw):
    """The text of the guidelines section, or None when missing."""
    start = raw.find(GUIDELINES_HEADING)
    if start < 0:
        return None
    rest = raw[start + len(GUIDELINES_HEADING):]
    match = re.search(r"(?m)^## ", rest)
    if match:
        rest = rest[:match.start()]
    return rest


def guideline_blocks(section):
    """The guideline blocks in order, split on G numbered headings."""
    parts = re.split(r"(?m)^### G\d+\.", section)
    return [part for part in parts[1:]]


def brief_problems(root=None):
    """Problems with the Build 11 brief's stated contract."""
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "coderabbit-review-brief.md")
    if raw is None:
        return ["docs/coderabbit-review-brief.md is missing"]
    text = re.sub(r"\s+", " ", raw)
    problems = []
    for label, fragment in PINNED:
        if fragment not in text:
            problems.append(
                "docs/coderabbit-review-brief.md does not state %s"
                % label
            )
    return problems


def guidelines_problems(root=None):
    """Problems with the brief's derivation noted guidelines."""
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "coderabbit-review-brief.md")
    if raw is None:
        return ["docs/coderabbit-review-brief.md is missing"]
    problems = []
    section = guidelines_section(raw)
    if section is None:
        problems.append(
            "docs/coderabbit-review-brief.md carries no %r section"
            % GUIDELINES_HEADING
        )
        return problems
    blocks = guideline_blocks(section)
    if not blocks:
        problems.append(
            "docs/coderabbit-review-brief.md carries no G numbered "
            "guidelines"
        )
    for index, block in enumerate(blocks, start=1):
        flat = re.sub(r"\s+", " ", block)
        if "Derives from" not in flat:
            problems.append(
                "coderabbit guideline G%d carries no derivation "
                "note, so it would be a rival instruction source"
                % index
            )
            continue
        note = flat.split("Derives from", 1)[1]
        if not deliberate_source(note):
            problems.append(
                "coderabbit guideline G%d names no canonical skill "
                "section, primary CodeRabbit citation, or binding "
                "decision in its derivation note" % index
            )
    return problems


def _prefix_negated(low, start):
    """R37-RT-08. Whether a negation guards a match from
    before it in the same claim stretch.

    The stretch runs from the last clause reset before the
    match, a semicolon or a but or however or yet, to the
    match itself. A negation inside that stretch guards
    the match even when it stands far before the match
    word, as a subordinate clause places it, while a
    negation in an earlier clause joined by a reset word
    belongs to that clause and does not guard.

    R37F-RT-10. A comma and clause opening on a pronoun
    subject is a reset too. Two assertions joined that
    way are two claims, and a negation in the first
    negates its own claim only.
    """
    prefix = low[:start]
    cut = 0
    for reset in re.finditer(
        r";|\bbut\b|\bhowever\b|\byet\b"
        r"|,\s+and\s+(?:it|they|we|he|she|these|those)\b",
        prefix,
    ):
        cut = max(cut, reset.end())
    return bool(
        re.search(
            r"\b(not|never|no)\b|n't|\bunavailable\b",
            prefix[cut:],
        )
    )


def linked_problems(root=None):
    """R36-RT-04. No sentence may promise Deep Scan linked
    source on an excluded platform or state a linked
    repository figure other than the 20 limit.

    The brief states the platform limit beside the linked
    context sentence, that linked source is available in
    the scan trigger flow on GitHub Cloud and GitHub
    Enterprise Server and GitLab Cloud and is not available
    in that flow for self hosted GitLab or Azure DevOps or
    Bitbucket. A planted sentence that offers linked source
    on one of the excluded platforms without the negation,
    or that states a linked repository figure other than
    20, must fail the gate. The shipped limit sentence
    carries its own negation, so it is skipped.

    R37-RT-07. The branches read pairs of neighbouring
    sentences beside single sentences and bind an offer to
    a platform anywhere inside the unit, because the round
    37 review split the offer and the platform across a
    sentence boundary, stated the raised figure in a
    partner sentence holding no repository word, and
    pushed an offer and a platform past the span limit
    inside one long sentence.
    """
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "coderabbit-review-brief.md")
    if raw is None:
        return ["docs/coderabbit-review-brief.md is missing"]
    body = re.sub(r"(?m)^#{1,6} .*$", "", raw)
    text = re.sub(r"\s+", " ", body)
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", text)
        if sentence.strip()
    ]
    windows = [[part] for part in sentences]
    windows += [
        [first, second]
        for first, second in zip(sentences, sentences[1:])
    ]
    # R37F-RT-11. Triples join the reading, because the
    # fix review split both linked claims across three
    # sentences with a filler between the halves.
    windows += [
        [first, second, third]
        for first, second, third in zip(
            sentences, sentences[1:], sentences[2:]
        )
    ]
    problems = []
    for parts in windows:
        sentence = " ".join(parts)
        low = sentence.lower()
        # R36 gate repair. The figure branch reads spelled
        # figures as well as digits, and reads a figure
        # bound to the word repositories by a link verb as
        # well as by the linked pair, because the review
        # restated the raised limit in words and behind the
        # verb link and both passed the digit pair form.
        figure_texts = [
            match.group(1)
            for match in re.finditer(
                r"(\d+)\s+linked repositories", low
            )
        ]
        figure_texts.extend(
            match.group(1)
            for match in re.finditer(
                r"(" + _NUMBER_WORDS + r")\s+linked repositories",
                low,
            )
        )
        figure_texts.extend(
            match.group(1)
            for match in re.finditer(
                r"\blink\w*\b[^.]{0,20}?(\d+|"
                + _NUMBER_WORDS
                + r")\s+repositories\b",
                low,
            )
        )
        for figure_text in figure_texts:
            value = (
                int(figure_text)
                if figure_text.isdigit()
                else _word_value(figure_text)
            )
            if value != 20:
                problems.append(
                    "the coderabbit brief states %s linked "
                    "repositories, other than the pinned "
                    "limit of 20" % figure_text
                )
                return problems
        # R37-RT-07. A figure stated in a partner sentence
        # through a cap frame, the cap for that reading is
        # 50, binds to the linked repositories the other
        # sentence of the pair names, so the pair reading
        # judges the figure against the same limit.
        # Gate review repair. The frame binds only where
        # the frame sentence ties its cap to the reading of
        # the linked repositories, so a neighbouring limit
        # on another surface states no linked cap. A figure
        # other than the pinned figure that a later
        # restatement in the same sentence corrects to the
        # pinned figure across a correction word is
        # skipped, and a negation standing between the cap
        # word and its figure guards that figure.
        half_pairs = []
        if len(parts) > 1:
            for link_index, link_half in enumerate(parts):
                for frame_index, frame_half in enumerate(parts):
                    if link_index != frame_index:
                        half_pairs.append((link_half, frame_half))
        for link_half, frame_half in half_pairs:
                if "linked repositories" not in link_half.lower():
                    continue
                frame_low = frame_half.lower()
                if not re.search(
                    r"\b(reading|linked|repositories)\b", frame_low
                ):
                    continue
                frames = []
                for match in re.finditer(
                    r"\b(?:cap|limit)\b[^.]{0,40}?"
                    r"\b(?:is|of|at)\s+(\d+|"
                    + _NUMBER_WORDS
                    + r")\b",
                    frame_low,
                ):
                    frames.append(match)
                for match in re.finditer(
                    r"\bup to\s+(\d+|"
                    + _NUMBER_WORDS
                    + r")\b",
                    frame_low,
                ):
                    frames.append(match)
                # R37C-RT-06. A tied frame sentence can
                # state a second repository figure with no
                # frame of its own, the pinned 20 in the
                # trigger flow beside a 50 in the summary
                # report. Bare repository figures in the
                # frame sentence join the candidates and are
                # judged under the same guards, with the
                # prefix negation guard the frame form gets
                # from its own span.
                candidates = [(match, False) for match in frames]
                for match in re.finditer(
                    r"\b(\d+|" + _NUMBER_WORDS
                    + r")\s+repositories\b",
                    frame_low,
                ):
                    candidates.append((match, True))
                for match, bare in candidates:
                    value = (
                        int(match.group(1))
                        if match.group(1).isdigit()
                        else _word_value(match.group(1))
                    )
                    if value == 20:
                        continue
                    if bare and _prefix_negated(
                        frame_low, match.start()
                    ):
                        continue
                    if re.search(
                        r"\b(not|never)\b",
                        frame_low[match.start():match.end()],
                    ):
                        continue
                    corrected = False
                    restatement = re.search(
                        r"\b(?:is|of|at)\s+(20|twenty)\b"
                        r"|\bup to\s+(20|twenty)\b",
                        frame_low[match.end():],
                    )
                    if restatement is not None:
                        between = frame_low[
                            match.end():
                            match.end() + restatement.start()
                        ]
                        if re.search(
                            r"\b(no|not|actually|true|correct"
                            r"|rather)\b",
                            between,
                        ):
                            corrected = True
                    if corrected:
                        continue
                    problems.append(
                        "the coderabbit brief states a "
                        "linked repository cap of %s, other "
                        "than the pinned limit of 20"
                        % match.group(1)
                    )
                    return problems
        # R36 gate repair. The platform branch binds an
        # availability word to an excluded platform by
        # closeness in either direction, with any negation
        # inside the span between them guarding the pair.
        # The first repair required the word available as a
        # substring, which both missed works and offered
        # and supported and fired on unavailable and on a
        # sentence that offered linked source on an
        # included platform while naming an excluded one
        # under its own negation.
        # R37-RT-07. The binding now runs at unit scope
        # with no span limit, because the review pushed an
        # offer and a platform past the span inside one
        # sentence and split them across two sentences.
        if "linked" in low or "deep scan" in low:
            platforms = [
                match
                for match in re.finditer(
                    r"\b(self hosted gitlab|azure devops"
                    r"|bitbucket)\b",
                    low,
                )
            ]
            offers = [
                match
                for match in re.finditer(
                    r"\b(available|works|offered|supported"
                    r"|runs|enabled|provided|usable)\b",
                    low,
                )
            ]
            # R37F-RT-12. A platform negated inside its
            # own claim stretch states the limit for that
            # platform itself, so an offer in a partner
            # sentence does not bind to it. The stretch is
            # the platform's clause of its own sentence,
            # cut at the same resets the prefix guard
            # uses, on both sides of the platform.
            part_spans = []
            offset = 0
            for part in parts:
                part_spans.append(
                    (offset, offset + len(part), part.lower())
                )
                offset += len(part) + 1
            for platform in platforms:
                home_start, home_end, home = next(
                    (start, end, part_low)
                    for start, end, part_low in part_spans
                    if start <= platform.start() < end
                )
                local_start = platform.start() - home_start
                local_end = platform.end() - home_start
                pre = home[:local_start]
                cut = 0
                for reset in re.finditer(
                    r";|\bbut\b|\bhowever\b|\byet\b"
                    r"|,\s+and\s+(?:it|they|we|he|she|these"
                    r"|those)\b",
                    pre,
                ):
                    cut = max(cut, reset.end())
                post = home[local_end:]
                stop = len(post)
                first_reset = re.search(
                    r";|\bbut\b|\bhowever\b|\byet\b"
                    r"|,\s+and\s+(?:it|they|we|he|she|these"
                    r"|those)\b",
                    post,
                )
                if first_reset is not None:
                    stop = first_reset.start()
                if re.search(
                    r"\b(not|never|no)\b|n't|\bunavailable\b",
                    pre[cut:],
                ) or re.search(
                    r"\b(not|never|no)\b|n't|\bunavailable\b",
                    post[:stop],
                ):
                    continue
                for offer in offers:
                    start = min(platform.start(), offer.start())
                    end = max(platform.end(), offer.end())
                    span = low[max(0, start - 6):end + 12]
                    if re.search(
                        r"\b(not|never|no)\b|n't"
                        r"|\bunavailable\b",
                        span,
                    ):
                        continue
                    # R37-RT-08. A negation standing before
                    # the offer in the same claim stretch
                    # guards the pair as well, because the
                    # round 37 review placed the negation
                    # ahead of a subordinate clause and the
                    # span guard alone missed it.
                    if _prefix_negated(low, offer.start()):
                        continue
                    problems.append(
                        "the coderabbit brief promises Deep "
                        "Scan linked source on a platform the "
                        "scan trigger flow does not offer it on"
                    )
                    return problems
    return problems


_NUMBER_WORDS = (
    r"(?:twenty|thirty|forty|fifty|sixty|seventy|eighty"
    r"|ninety)(?:\s+(?:one|two|three|four|five|six|seven"
    r"|eight|nine))?|(?:one|two|three|four|five|six|seven"
    r"|eight|nine|ten|eleven|twelve|thirteen|fourteen"
    r"|fifteen|sixteen|seventeen|eighteen|nineteen)"
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


def _word_value(phrase):
    """The value of a spelled number phrase under a hundred."""
    value = 0
    for token in phrase.split():
        if token in _WORD_TENS:
            value += _WORD_TENS[token]
        elif token in _WORD_ONES:
            value += _WORD_ONES[token]
    return value


def decision_problems(root=None):
    """Problems with the Build 11 decision record."""
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "decisions.md")
    if raw is None:
        return ["docs/decisions.md is missing"]
    start = raw.find(DECISION_HEADING)
    if start < 0:
        return [
            "docs/decisions.md carries no Build 11 decision record"
        ]
    rest = raw[start + len(DECISION_HEADING):]
    match = re.search(r"(?m)^## ", rest)
    record = rest[:match.start()] if match else rest
    if DECISION_STATEMENT not in record:
        return [
            "the Build 11 decision record carries no decision 4 "
            "statement, which every landed build must record"
        ]
    return []


def coderabbit_problems(root=None):
    """Every Build 11 CodeRabbit guidelines problem."""
    problems = []
    problems.extend(brief_problems(root))
    problems.extend(guidelines_problems(root))
    problems.extend(linked_problems(root))
    problems.extend(decision_problems(root))
    return problems


def main(root=None):
    problems = coderabbit_problems(root)
    if problems:
        for problem in problems:
            print("check_coderabbit: %s" % problem, file=sys.stderr)
        return 1
    print(
        "check_coderabbit: the Build 11 CodeRabbit guidelines "
        "contract holds"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
