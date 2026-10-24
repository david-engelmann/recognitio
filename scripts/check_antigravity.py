#!/usr/bin/env python3
"""Pin the Build 12 Antigravity plugin alteration contract.

The brief at docs/antigravity-plugin-brief.md records the
Antigravity plugin format with plugin.json, skills/, agents/,
rules/, and hooks.json, and a PreToolUse hook carrying the
deny, force_ask, and auto_approve decisions, per the primary
Google docs read as text on 2026-10-24. It records the dated
October 9 2026 sunset evidence with Antigravity as the named
path, the v0.65.0 stable pin with the docs lag caveat, and the
Antigravity native shapes as a second extensions namespace
beside the portable core, never blended into it. Decision 4
binds this build like every other build. The brief and the
hook wiring document the contract and never enforce it, so
this script pins the contract without an Antigravity host. It
requires the brief to keep the stated pins, the dated sunset
sentences, the no page stamp discipline, the version pin and
the docs lag caveat, the extension boundary sentence, the
namespace placeholder sentence, the hook file with its
PreToolUse entry and its three decisions, the documented
harness contract with a derivation note on every contract
statement, and the decision record with its decision 4
statement, so the scoped guidance cannot become a rival
instruction source and a later edit cannot soften or drop a
dated claim in silence.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / "docs" / "antigravity-plugin-brief.md"
DECISIONS = ROOT / "docs" / "decisions.md"

STATEMENTS_HEADING = "## The documented harness contract"

# Canonical skill sections a derivation note may name. These are
# the section titles of .agents/skills/recognitio/SKILL.md, and a
# note that names one says which canonical section the contract
# statement restates.
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
PRIMARY_CITATIONS = (
    "antigravity.google/docs/plugins",
    "antigravity.google/docs/hooks",
    "antigravity.google/docs/changelog",
    "docs.cloud.google.com/gemini/docs/codeassist/sunset",
    "github.com/google-gemini/gemini-cli/releases",
    "geminicli.com/docs/changelogs",
)

# Brief sentences the gate pins. Each is a fragment of the exact
# sentence the brief carries, so a later edit that softens or
# drops a stated pin, quote, date, or limit fails loudly.
PINNED = (
    ("the primary read date",
     "per the primary Google docs read as text on 2026-10-24"),
    ("the required plugin.json marker",
     "`plugin.json` as the required marker"),
    ("the six hook events",
     "`SessionStart`, `PreToolUse`, `PostToolUse`, `PreInvocation`, "
     "`PostInvocation`, and `Stop`"),
    ("the three hook decisions",
     "This build's hook uses three of them, `deny`, `force_ask`, "
     "and `auto_approve`"),
    ("the sunset halt",
     "Starting October 9 2026, no new Gemini Code Assist Standard "
     "or Enterprise subscriptions can be purchased"),
    ("the contract terms",
     "Existing subscriptions continue through their contract terms"),
    ("the renewal dates",
     "License additions and annual renewals run to January 31 2027"),
    ("the named path",
     "The page names Antigravity as the forward path for agentic "
     "coding assistance"),
    ("the migration guide",
     "The page's FAQ names the Gemini CLI to Antigravity CLI "
     "migration guide"),
    ("the no stamp discipline",
     "this brief never pins a page stamp, because a stamp is a "
     "moving target"),
    ("the sunset read date",
     "The round 24 lane read the sunset page live on 2026-10-24"),
    ("the GitHub split form",
     "The Gemini Code Assist service on GitHub stands in split "
     "form"),
    ("the GitHub consumer deprecation",
     "the consumer version deprecated on June 18 2026"),
    ("the GitHub consumer shutdown",
     "shut down on July 17 2026"),
    ("the GitHub enterprise unaffected",
     "the enterprise version not affected"),
    ("the config page posture",
     "No brief cites the config page as proof of consumer "
     "availability"),
    ("the enterprise status check",
     "requires a current primary status check first"),
    ("the v0.65.0 pin",
     "v0.65.0 is the stable pin for the Gemini CLI extension bundle"),
    ("the docs lag",
     "the brief trusts the releases page over the docs page"),
    ("the pre-release",
     "it is not stable, so the v0.65.0 pin stands"),
    ("the frontmatter watch",
     "the change stays an adjacent watch item with no brief impact"),
    ("the extension boundary",
     "The Antigravity native shapes live as a second extensions "
     "namespace beside the portable core, never blended into it"),
    ("the no primary namespace",
     "No primary source names a reverse domain namespace for an "
     "Antigravity plugin"),
    ("the namespace placeholder",
     "the portable manifest uses `com.google.antigravity` as a "
     "documented placeholder"),
    ("the not primary",
     "the brief does not present it as primary"),
    ("the declared paths",
     "the gate resolves every declared path in the repo"),
    ("the skills folder rule",
     "every skill lives inside the plugin's `skills` folder"),
    ("the no second skill copy",
     "so the build ships no second skill copy"),
    ("the Antigravity first orientation",
     "which confirms the Antigravity first orientation the program "
     "already carried"),
    ("the stdin stdout contract",
     "receives the event JSON on stdin and returns a JSON object "
     "on stdout"),
    ("the deny mapping",
     "`deny` refuses the tool call with a reason when the packet "
     "manifest is missing or not verified"),
    ("the force_ask mapping",
     "`force_ask` holds the tool call for user confirmation when "
     "the packet manifest is unreadable or unparsable"),
    ("the auto_approve mapping",
     "`auto_approve` lets the tool call through without asking when "
     "the packet manifest reads verified"),
    ("the degraded state",
     "A missing or unparseable hook file is a planned degraded "
     "state, never a silent pass"),
    ("the host fallback",
     "the review run falls back to the shipped scripts"),
    ("the Claude Code only negative",
     "The Build 7 mod hooks are Claude Code only on current "
     "evidence"),
    ("the honest limit",
     "the brief claims no product enforcement behavior it cannot "
     "run"),
    ("the four frontmatter keys",
     "The canonical skill frontmatter holds exactly four keys, "
     "name, description, context, and background"),
    ("the second packet guard",
     "A statement with neither is a rival instruction source and "
     "fails the round"),
    ("the decision 4 statement",
     "Decision 4 binds this build like every other build"),
)

DECISION_HEADING = "## 22. Build 12"
DECISION_STATEMENT = "Decision 4 binds"

NAMESPACE = "com.google.antigravity"
HOOK_DECISIONS = ("deny", "force_ask", "auto_approve")


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


def statements_section(raw):
    """The text of the harness contract section, or None."""
    start = raw.find(STATEMENTS_HEADING)
    if start < 0:
        return None
    rest = raw[start + len(STATEMENTS_HEADING):]
    match = re.search(r"(?m)^## ", rest)
    if match:
        rest = rest[:match.start()]
    return rest


def statement_blocks(section):
    """The contract statement blocks in order, split on S headings."""
    parts = re.split(r"(?m)^### S\d+\.", section)
    return [part for part in parts[1:]]


def brief_problems(root=None):
    """Problems with the Build 12 brief's stated contract."""
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "antigravity-plugin-brief.md")
    if raw is None:
        return ["docs/antigravity-plugin-brief.md is missing"]
    text = re.sub(r"\s+", " ", raw)
    problems = []
    for label, fragment in PINNED:
        if fragment not in text:
            problems.append(
                "docs/antigravity-plugin-brief.md does not state %s"
                % label
            )
    return problems


def statements_problems(root=None):
    """Problems with the brief's derivation noted statements."""
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "antigravity-plugin-brief.md")
    if raw is None:
        return ["docs/antigravity-plugin-brief.md is missing"]
    problems = []
    section = statements_section(raw)
    if section is None:
        problems.append(
            "docs/antigravity-plugin-brief.md carries no %r section"
            % STATEMENTS_HEADING
        )
        return problems
    blocks = statement_blocks(section)
    if not blocks:
        problems.append(
            "docs/antigravity-plugin-brief.md carries no S numbered "
            "contract statements"
        )
    for index, block in enumerate(blocks, start=1):
        flat = re.sub(r"\s+", " ", block)
        if "Derives from" not in flat:
            problems.append(
                "antigravity contract statement S%d carries no "
                "derivation note, so it would be a rival instruction "
                "source" % index
            )
            continue
        note = flat.split("Derives from", 1)[1]
        if not deliberate_source(note):
            problems.append(
                "antigravity contract statement S%d names no canonical "
                "skill section, primary citation, or binding decision "
                "in its derivation note" % index
            )
    return problems


def hook_problems(root=None):
    """Problems with the shipped PreToolUse hook wiring.

    A missing or unparseable hook file is a planned degraded
    state, never a silent pass, so either fails this gate. The
    wiring must declare one PreToolUse entry carrying the three
    decisions the build pins, or the documented contract has no
    file behind it.
    """
    root = ROOT if root is None else root
    path = root / ".antigravity" / "hooks.json"
    raw = read_text(path)
    if raw is None:
        return [
            ".antigravity/hooks.json is missing, so the PreToolUse "
            "wiring the brief documents has no file behind it"
        ]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return [
            ".antigravity/hooks.json does not parse, %s, so the "
            "PreToolUse wiring is not a planned state" % exc
        ]
    if not isinstance(data, dict):
        return [".antigravity/hooks.json is not a JSON object"]
    hooks = data.get("hooks")
    if not isinstance(hooks, list) or not hooks:
        return [
            ".antigravity/hooks.json carries no hook entries"
        ]
    entries = [
        entry for entry in hooks
        if isinstance(entry, dict) and entry.get("event") == "PreToolUse"
    ]
    if not entries:
        return [
            ".antigravity/hooks.json carries no PreToolUse entry, so "
            "the build's declared mapping names no event"
        ]
    problems = []
    for entry in entries:
        decisions = entry.get("decisions")
        if not isinstance(decisions, list):
            problems.append(
                "the PreToolUse entry carries no decisions list"
            )
            continue
        for decision in HOOK_DECISIONS:
            if decision not in decisions:
                problems.append(
                    "the PreToolUse entry does not carry the %r "
                    "decision the brief pins" % decision
                )
    return problems


def strict_json_loads(text):
    """Parse JSON refusing a repeated key, like the other gates."""
    def reject(pairs):
        seen = {}
        for key, value in pairs:
            if key in seen:
                raise ValueError("repeated key %r" % key)
            seen[key] = value
        return seen
    return json.loads(text, object_pairs_hook=reject)


def manifest_problems(root=None):
    """Problems with the Build 12 manifest namespace.

    The Build 12 manifest must declare the Antigravity shapes
    under the new namespace. Path resolution for every
    namespace lives in scripts/check_package.py, so this check
    pins the declaration the Build 12 brief states.
    """
    root = ROOT if root is None else root
    path = root / "agent-plugins-package" / "plugin.json"
    raw = read_text(path)
    if raw is None:
        return ["the portable manifest at %s is missing" % path]
    try:
        data = strict_json_loads(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        return ["the portable manifest does not parse, %s" % exc]
    if not isinstance(data, dict):
        return ["the portable manifest is not a JSON object"]
    extensions = data.get("extensions")
    if not isinstance(extensions, dict):
        return [
            "the portable manifest carries no extensions object for "
            "the per platform native shapes"
        ]
    if not isinstance(extensions.get(NAMESPACE), dict):
        return [
            "the extensions object names no %r namespace for the "
            "Antigravity native shapes, so the Build 12 shapes ride "
            "undeclared" % NAMESPACE
        ]
    return []


def decision_problems(root=None):
    """Problems with the Build 12 decision record."""
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "decisions.md")
    if raw is None:
        return ["docs/decisions.md is missing"]
    start = raw.find(DECISION_HEADING)
    if start < 0:
        return [
            "docs/decisions.md carries no Build 12 decision record"
        ]
    rest = raw[start + len(DECISION_HEADING):]
    match = re.search(r"(?m)^## ", rest)
    record = rest[:match.start()] if match else rest
    if DECISION_STATEMENT not in record:
        return [
            "the Build 12 decision record carries no decision 4 "
            "statement, which every landed build must record"
        ]
    return []


def antigravity_problems(root=None):
    """Every Build 12 Antigravity plugin alteration problem."""
    problems = []
    problems.extend(brief_problems(root))
    problems.extend(statements_problems(root))
    problems.extend(hook_problems(root))
    problems.extend(manifest_problems(root))
    problems.extend(decision_problems(root))
    return problems


def main(root=None):
    problems = antigravity_problems(root)
    if problems:
        for problem in problems:
            print("check_antigravity: %s" % problem, file=sys.stderr)
        return 1
    print(
        "check_antigravity: the Build 12 Antigravity plugin "
        "alteration contract holds"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
