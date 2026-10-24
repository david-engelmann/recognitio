#!/usr/bin/env python3
"""Pin the Build 17 Devin playbook and coordinator build contract.

The brief at docs/devin-playbook-brief.md records the Devin
Review host list with the Bitbucket Cloud conditions, the code
fixed only resolved count, the Quote in chat and merge past
bypass surfaces, the one off review of the latest commit, the
code scan automation API path with the service user permission
condition, the SARIF 2.1.0 export beside CSV, the repositories
and blueprint v3 promotion with the v3beta1 continuation note,
the auto scan schedules API general availability kept separate
from the session schedules deprecation, the coordinator
surfaces, Devin Oncall as an adjacent incident surface only,
Devin Dynamic Workflows as recorded script orchestration, the
targeted plugin saves and reinstall as a new revision, the
skill placement with both triggers enabled by default, the
stacked pull request packet rule, the AI Scan advisory limit,
the Copilot governance packet rule, and the Fusion chart
caveat, per the round 30 Devin delta. Decision 4 binds this
build like every other build. The brief documents the contract
and never enforces it on a live Devin host, so this script
pins the contract without a Devin client. It requires the
brief to keep the stated pins with a derivation note on
every rule, every Devin Dynamic Workflows mention qualified
with Devin, and the decision record with its decision 4
statement, so the scoped guidance cannot become a rival
instruction source and a later edit cannot soften or drop a
stated claim in silence.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / "docs" / "devin-playbook-brief.md"
SKILL = ROOT / ".agents" / "skills" / "recognitio" / "SKILL.md"
DECISIONS = ROOT / "docs" / "decisions.md"

RULES_HEADING = "## The Devin rules"

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

# Primary Devin citations a derivation note may name. A note
# that names one says which primary page the rule reports.
PRIMARY_CITATIONS = (
    "docs.devin.ai",
    "cognition.com/blog/local-fusion",
)

# Brief sentences the gate pins. Each is a fragment of the exact
# sentence the brief carries, so a later edit that softens or
# drops a stated pin, rule, or limit fails loudly.
PINNED = (
    ("the Bitbucket Cloud host",
     "now beside Bitbucket Cloud"),
    ("the automatic webhook install",
     "installs its webhooks automatically"),
    ("the personal account link",
     "links a personal Bitbucket Cloud account"),
    ("the code fixed only resolved count",
     "count a finding as resolved only when it was fixed in code"),
    ("the dismissed findings exclusion",
     "Findings dismissed by a reviewer and duplicates no longer count"),
    ("the Quote in chat surface",
     "carries a Quote in chat button"),
    ("the merge past bypass surface",
     "can merge a blocked pull request directly from Devin Review"),
    ("the one off review of the latest commit",
     "offers a one off review of the latest commit"),
    ("the no automatic enrollment",
     "without turning on automatic review"),
    ("the code scan automation API path",
     "can be created and updated through the API"),
    ("the service user permission condition",
     "the service user role needs the relevant scan permission"),
    ("the runtime validation evidence",
     "include recorded runtime validation results"),
    ("the SARIF 2.1.0 export",
     "export as SARIF 2.1.0"),
    ("the CSV beside SARIF",
     "in addition to CSV"),
    ("the v3 promotion",
     "are part of the stable v3 API"),
    ("the v3beta1 continuation",
     "the v3beta1 paths continuing to work"),
    ("the auto scan schedules general availability",
     "are generally available in the v3 org and enterprise APIs"),
    ("the schedules separation",
     "stays separate from the session schedules deprecation"),
    ("the session schedules deprecation date",
     "deprecation is dated September 10"),
    ("the devin_schedule deprecation",
     "devin_schedule Terraform resource deprecated in favor of "
     "devin_automation"),
    ("the converted schedule pointer",
     "points at the replacement automation"),
    ("the no end date published",
     "No end date for the migration phase is published"),
    ("the time sensitive flag stays set",
     "the time sensitive flag stays set"),
    ("the structured questions",
     "ask structured questions with clickable choices"),
    ("the shared Outpost runs",
     "run their sessions on a shared Outpost"),
    ("the plain language schedule display",
     "in plain language instead of raw RRULE text"),
    ("the Linear triggered child sessions",
     "from Linear automations or allowlisted Linear bots"),
    ("the Oncall adjacent surface",
     "as an adjacent incident surface only"),
    ("the Oncall Lite mode",
     "can run in Lite mode"),
    ("the Devin Dynamic Workflows recorded shape",
     "are a recorded, resumable script orchestration option"),
    ("the enterprise enablement secondary mark",
     "carried as secondary in this brief"),
    ("the targeted plugin saves",
     "into a specific uploaded plugin by naming it"),
    ("the reinstall as a new revision",
     "by reinstalling it, keeping the plugin version history"),
    ("the skill placement path",
     ".agents/skills/skill-name/SKILL.md"),
    ("the automatic discovery across repositories",
     "automatically discovered across connected repositories"),
    ("the both triggers enabled by default",
     "with user trigger and model trigger both enabled by default"),
    ("the Devin extension not portable core",
     "is a Devin extension, not a portable Agent Skills core item"),
    ("the human curation before procedure",
     "passes human curation before entering packet procedure"),
    ("the stacked layers verified separately",
     "Each stack layer and the integrated whole are verified separately"),
    ("the AI Scan never a merge gate",
     "An AI Scan pass is signal and never a merge gate"),
    ("the Copilot explicit choices",
     "Explicit Copilot feature choices are recorded"),
    ("the October 22 through October 26 window",
     "during the October 22 through October 26 rollout window"),
    ("the Fusion 68.1 figure",
     "scores 68.1 at 31 percent lower cost"),
    ("the higher Sonnet 5.5 figure",
     "with Sonnet 5.5 at 68.4"),
    ("the never a top score claim",
     "never stands as a top score claim"),
    ("the decision 4 statement",
     "Decision 4 binds this build like every other build"),
)

DECISION_HEADING = "## 28. Build 17"
DECISION_STATEMENT = "Decision 4 binds"

# Shared diagnostic strings from round 34 repair round two.
# Lifting them to constants keeps the three resolved blocks
# and the two SARIF blocks on one wording, so a future
# wording change cannot drift across blocks.
RESOLVED_PROBLEM = (
    "a devin rule counts dismissed findings toward "
    "the resolved total, which the code fixed only "
    "resolved count forbids"
)

SARIF_PROBLEM = (
    "a devin rule exports a SARIF version other "
    "than 2.1.0, which the SARIF 2.1.0 export "
    "beside CSV forbids"
)

# Generic equivalence verbs from G-05 and B1.
# Count, treat, and include are the G-05 verbs, and
# consider, regard, classify, and mark were added in
# the first repair. None of them fires alone any more.
# B1 requires the verb to be followed within the
# sentence by an equivalence phrase, so ordinary
# sentences that merely mention both kinds of finding
# with one of these verbs pass.
RESOLVED_VERBS = (
    "count\\w*|treat\\w*|includ\\w*|consider\\w*|"
    "regard\\w*|classif\\w*|mark\\w*"
)

# Equivalence phrases from G-05 and B1.
# As resolved and as fixed cover the G-05 plants when a
# listed verb precedes them in the same sentence.
# Membership phrases from R-05, B3, and Y-05.
# Part of covers the R-05 verb free plant, and go into
# and belong in cover the Y-05 verb free plants, and
# each states the same membership with no listed verb
# at all. A membership phrase fires only when resolved
# follows it within 15 characters. The R-05 plant puts
# resolved 5 characters after part of, while the B3
# audit trail probe puts resolved 21 characters after
# part of, so 15 keeps the plant caught and lets the
# probe pass. A bare part of test with no resolved
# bound is the B3 failure and is not used here.
# Measured gaps for this bound are plant gap 5 and probe
# gap 21 with bound 15. With bound 15, filler from 16 to
# 20 escapes by design, because any bound below the 21
# probe gap leaves a filler zone above it that escapes,
# and for bound 15 that zone is exactly 16 to 20.
EQUIVALENCE_PHRASES = "as resolved|as fixed"
MEMBERSHIP_PHRASES = "part of|go into|belong in"

# Modifier chain gap from R36-E1-02. A membership phrase
# and resolved can also be joined by a run of pure
# modifiers, articles and conjunctions and adjective or
# adverb shaped words and nothing else, at any length.
# The E1 plants put a 41 character modifier run there,
# far past the 15 and 20 character bounds, while the B3
# probe puts a noun phrase there, the audit trail, which
# starts a second claim unit and so stays out. Modifier
# shaped means an article or conjunction or a word
# carrying a derivational adjective or adverb suffix. A
# gap holding any other word shape is not a modifier
# chain and this branch does not fire on it, so filler
# that smuggles a noun or a verb into the gap still
# escapes by design, as the bound comment above records
# for its own zone.
MODIFIER_WORD = (
    r"(?:the|and|or|[a-z]+(?:ly|ous|ive|al|ic|ed|ing|ful"
    r"|less|able|ible|ent|ant|ary|ory))"
)
MEMBERSHIP_MODIFIER_GAP = (
    r"(?:\s+" + MODIFIER_WORD + r")*\s+"
)

# Spelled SARIF version words from W-07, mirroring the
# Qwen gate number word normalisation. A spelled version
# after SARIF counts the same as its digit form, so
# version two fails while version two point one point
# zero passes as the shipped 2.1.0 pin in spelled form.
SARIF_NUMBER_WORDS = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
}


def spelled_sarif_problem(low):
    """Whether a spelled SARIF version differs from 2.1.0."""
    word = (
        "zero|one|two|three|four|five|six|seven|eight|nine|ten"
    )
    prefix = r"\bsarif(?:\s+version)?\s+v?\s*"
    dotted = re.search(
        prefix + "(" + word + r")\s+point\s+(" + word
        + r")\s+point\s+(" + word + r")\b", low
    )
    if dotted:
        version = ".".join(
            SARIF_NUMBER_WORDS[name] for name in dotted.groups()
        )
        return version != "2.1.0"
    if re.search(
        prefix + "(" + word + r")\s+point\s+(" + word + r")\b",
        low,
    ):
        return True
    bare = re.search(
        prefix + "(" + word + r")\b(?!\s+point\b)", low
    )
    return bool(bare)


def read_text(path):
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def deliberate_source(note):
    """Whether the derivation note names a source on purpose.

    A canonical section title counts only when named right
    after the "canonical skill" attribution marker, and a
    primary Devin citation counts when named as a Devin page
    or the Cognition Fusion post.
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
    """Problems with the Build 17 brief's stated contract."""
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "devin-playbook-brief.md")
    if raw is None:
        return ["docs/devin-playbook-brief.md is missing"]
    text = re.sub(r"\s+", " ", raw)
    problems = []
    for label, fragment in PINNED:
        if fragment not in text:
            problems.append(
                "docs/devin-playbook-brief.md does not state %s"
                % label
            )
    return problems


def rules_problems(root=None):
    """Problems with the brief's derivation noted rules."""
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "devin-playbook-brief.md")
    if raw is None:
        return ["docs/devin-playbook-brief.md is missing"]
    problems = []
    section = rules_section(raw)
    if section is None:
        problems.append(
            "docs/devin-playbook-brief.md carries no %r section"
            % RULES_HEADING
        )
        return problems
    blocks = rule_blocks(section)
    if not blocks:
        problems.append(
            "docs/devin-playbook-brief.md carries no R numbered rules"
        )
    for name, block in blocks:
        flat = re.sub(r"\s+", " ", block)
        if "Derives from" not in flat:
            problems.append(
                "devin rule %s carries no derivation note, so it "
                "would be a rival instruction source" % name
            )
            continue
        note = flat.split("Derives from", 1)[1]
        if not deliberate_source(note):
            problems.append(
                "devin rule %s names no canonical skill section, "
                "primary Devin citation, or binding decision in its "
                "derivation note" % name
            )
    return problems


def naming_problems(root=None):
    """Problems with the Devin Dynamic Workflows naming guard.

    Every Devin Dynamic Workflows mention must name Devin, so
    the Build 6 Claude Code fan out surface is never confused
    with Devin Dynamic Workflows, and the brief must never cite
    the Build 6 figures as evidence about Devin.
    """
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "devin-playbook-brief.md")
    if raw is None:
        return ["docs/devin-playbook-brief.md is missing"]
    flat = re.sub(r"\s+", " ", raw).lower()
    problems = []
    for match in re.finditer(r"dynamic workflows", flat):
        before = flat[max(0, match.start() - 6):match.start()]
        if before != "devin ":
            problems.append(
                "docs/devin-playbook-brief.md names dynamic "
                "workflows without Devin, which confuses the "
                "Build 6 surface with Devin Dynamic Workflows"
            )
            break
    if "16 agents" in flat:
        problems.append(
            "docs/devin-playbook-brief.md cites the Build 6 "
            "figures as evidence about Devin"
        )
    return problems


def semantic_problems(root=None):
    """R32-RT-01. No sentence may contradict the resolved count,
    the bypass surface, or the SARIF export shape.

    The pins prove the correct sentences are stated, but an
    added sentence or an in place rewrite passes while the
    pins stay in place, because no check reads the
    contradicting sentence. This check reads every sentence
    in the whole brief, inside and outside the rules
    section, so an appended rule contradicts just as loudly
    as an in rule rewrite. Sentences that state the correct
    posture with a negation, such as dismissed findings no
    longer counting, the bypass path never assumed absent,
    or CSV alone never named as the export shape, are
    skipped.
    """
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "devin-playbook-brief.md")
    if raw is None:
        return ["docs/devin-playbook-brief.md is missing"]
    sentences = [
        sentence.strip()
        for sentence in re.split(
            r"(?<=[.!?])\s+", re.sub(r"\s+", " ", raw)
        )
        if sentence.strip()
    ]
    problems = []
    seen = set()
    for sentence in sentences:
        low = sentence.lower()
        negated = bool(
            re.search(r"\b(no longer|never)\b", low)
            or re.search(r"\bnot\b.{0,20}\bcount\w*\b", low)
        )
        if "resolved" not in seen and not negated and (
            re.search(r"\bdismissed\b.{0,50}\bcount\w*\b", low)
            or re.search(
                r"\bresolved\b.{0,30}\bincludes?\b.{0,30}"
                r"\bdismissed\b",
                low,
            )
        ):
            problems.append(RESOLVED_PROBLEM)
            seen.add("resolved")
        correct_definition = bool(
            re.search(
                r"\b(excluded|only when|fixed in code|code fixed only)\b",
                low,
            )
        )
        if (
            "resolved" not in seen
            and not negated
            and not correct_definition
            and (
                re.search(
                    r"\bresolved\b.{0,60}\bcount\w*\b.{0,40}"
                    r"\bdismissed\b",
                    low,
                )
                or re.search(
                    r"\bcount\w*\b.{0,60}\bresolved\b.{0,40}"
                    r"\bdismissed\b",
                    low,
                )
            )
        ):
            problems.append(RESOLVED_PROBLEM)
            seen.add("resolved")
        verb_then_equivalence = bool(re.search(
            r"\b(" + RESOLVED_VERBS + r")\b.{0,80}\b("
            + EQUIVALENCE_PHRASES + r")\b",
            low,
        ))
        membership_near_resolved = bool(re.search(
            r"\b(" + MEMBERSHIP_PHRASES + r")\b.{0,15}\bresolved\b",
            low,
        ))
        # Modifier chain from R36-E1-02. A membership phrase
        # followed by a pure modifier chain and then
        # resolved states the same membership at any gap
        # length, so it fires beside the bounded form.
        membership_modifier_chain = bool(re.search(
            r"\b(" + MEMBERSHIP_PHRASES + r")\b"
            + MEMBERSHIP_MODIFIER_GAP + r"resolved\b",
            low,
        ))
        # Verb plus membership from S4. A listed verb within
        # 30 of a membership phrase with resolved within 20
        # of the phrase restores the long filler verb shape.
        # The 19 filler comprehensive shape fires while the
        # 21 filler audit trail shape stays out, and a probe
        # with no listed verb stays out on the verb test
        # alone even before the bounds are reached.
        verb_then_membership_near_resolved = bool(re.search(
            r"\b(" + RESOLVED_VERBS + r")\b.{0,30}\b("
            + MEMBERSHIP_PHRASES + r")\b.{0,20}\bresolved\b",
            low,
        ))
        if (
            "resolved" not in seen
            and not negated
            and not correct_definition
            and "dismissed" in low
            and "resolved" in low
            and (
                verb_then_equivalence
                or membership_near_resolved
                or membership_modifier_chain
                or verb_then_membership_near_resolved
            )
        ):
            problems.append(RESOLVED_PROBLEM)
            seen.add("resolved")
        if "bypass" not in seen and (
            re.search(r"without (any )?bypass", low)
            or re.search(r"\bno bypass\b", low)
            or (
                "assume" not in low
                and re.search(
                    r"\bbypass (surface|path)\b.{0,20}\babsent\b",
                    low,
                )
            )
            or re.search(
                r"\bbypass\b.{0,20}\b(not needed|not required"
                r"|unnecessary)\b",
                low,
            )
        ):
            problems.append(
                "a devin rule merges a blocked pull request "
                "without a bypass surface, which the merge past "
                "bypass surface forbids"
            )
            seen.add("bypass")
        if "sarif" not in seen and (
            re.search(r"\bcsv only\b", low)
            or (not negated and re.search(r"\bcsv alone\b", low))
            or re.search(
                r"\bsarif\b.{0,30}\b(dropped|removed|absent)\b",
                low,
            )
            or re.search(r"without sarif", low)
        ):
            problems.append(
                "a devin rule exports CSV only, which the SARIF "
                "2.1.0 export beside CSV forbids"
            )
            seen.add("sarif")
        if "sarif" not in seen and "sarif" in low:
            versions = re.findall(r"\b\d+\.\d+(?:\.\d+)?\b", low)
            if any(version != "2.1.0" for version in versions):
                problems.append(SARIF_PROBLEM)
                seen.add("sarif")
        if "sarif" not in seen and "sarif" in low:
            # Bare version from R-06, with an optional v prefix.
            # The lookahead still lets the full 2.1.0 pin pass,
            # because its 2 is followed by a dot digit.
            bare = re.search(
                r"\bsarif(?:\s+version)?\s*v?(\d+)(?!\.\d)", low
            )
            if bare:
                problems.append(SARIF_PROBLEM)
                seen.add("sarif")
        if "sarif" not in seen and "sarif" in low:
            # Spelled version from W-07, checked after the
            # digit blocks so a digit pin still decides first.
            if spelled_sarif_problem(low):
                problems.append(SARIF_PROBLEM)
                seen.add("sarif")
    return problems


def decision_problems(root=None):
    """Problems with the Build 17 decision record."""
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "decisions.md")
    if raw is None:
        return ["docs/decisions.md is missing"]
    start = raw.find(DECISION_HEADING)
    if start < 0:
        return [
            "docs/decisions.md carries no Build 17 decision record"
        ]
    rest = raw[start + len(DECISION_HEADING):]
    match = re.search(r"(?m)^## ", rest)
    record = rest[:match.start()] if match else rest
    if DECISION_STATEMENT not in record:
        return [
            "the Build 17 decision record carries no decision 4 "
            "statement, which every landed build must record"
        ]
    return []


def devin_problems(root=None):
    """Every Build 17 Devin playbook and coordinator problem."""
    problems = []
    problems.extend(brief_problems(root))
    problems.extend(rules_problems(root))
    problems.extend(naming_problems(root))
    problems.extend(semantic_problems(root))
    problems.extend(decision_problems(root))
    return problems


def main(root=None):
    problems = devin_problems(root)
    if problems:
        for problem in problems:
            print("check_devin: %s" % problem, file=sys.stderr)
        return 1
    print("check_devin: the Build 17 Devin contract holds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
