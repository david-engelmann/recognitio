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
binds this build like every other build. The brief documents
the contract and the shipped hook wiring enforces it through
the packet gate script, and this script pins the contract
without an Antigravity host. It
requires the brief to keep the stated pins, the dated sunset
sentences, the no page stamp discipline, the version pin and
the docs lag caveat, the extension boundary sentence, the
namespace placeholder sentence, the plugin manifest with
exactly the keys its primary schema permits, the hook file
in the primary hooks form with its one named hook, its one
PreToolUse entry, its matcher and its one command handler
naming the shipped packet gate script, the documented
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
    ("the manifest key set",
     "the shipped manifest at `.antigravity/plugin.json` carries "
     "exactly those three keys and no version and no notes field"),
    ("the wiring form",
     "Its top level maps one hook name, `recognitio-packet-gate`, "
     "to its event configuration"),
    ("the command handler",
     "its one handler is a command handler naming the shipped "
     "packet gate script"),
    ("the staging copy",
     "The shipped pair is a staging copy a user places into "
     "a plugin directory"),
    ("the hook enforcement correction",
     "The hook wiring now enforces the contract through the "
     "shipped packet gate script"),
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

# The dated correction the round 39 pricing ordered for this
# record. The round 24 text that the wiring documents the
# contract and never enforces it stands in the record, and
# the correction beside it states the current position, so
# both fragments must stand or the record contradicts the
# shipped wiring in silence again.
DECISION_CORRECTION_DATE = "A correction recorded on 2026-10-31"
DECISION_CORRECTION = (
    "now enforces the contract through the shipped "
    "packet gate script"
)

NAMESPACE = "com.google.antigravity"
HOOK_MATCHER = "invoke_subagent"

# The one hook name the shipped wiring declares, the command
# its one handler runs, and the script that command names,
# read relative to the .antigravity plugin root in the form
# the primary hooks page examples use. The decision contract
# the script implements is the brief contract statements S3
# and S4 and S5, and the shipped tests run the script itself
# over the packet manifest states those statements name.
HOOK_NAME = "recognitio-packet-gate"
HOOK_COMMAND = "python3 ./scripts/packet_gate.py"
HOOK_SCRIPT = "scripts/packet_gate.py"

# The keys the primary plugins page schema permits in the
# plugin manifest, beside the $schema key its own example
# carries. The schema names the name and the description as
# its only properties and sets additional properties to
# false, so a version or a notes key in the shipped manifest
# is a forbidden field, however true its value reads.
MANIFEST_KEYS = {"$schema", "name", "description"}
MANIFEST_SCHEMA = "https://antigravity.google/schemas/v1/plugin.json"
MANIFEST_NAME = "recognitio"


def read_text(path):
    if path.exists() and not path.is_file():
        return None
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


def read_hook_wiring(path):
    """The hook wiring text and any problem reading it.

    Returns a pair of the text and the problem, with exactly
    one of the two standing. The reading tests existence and
    the symlink shape first and the regular file shape second
    and only then reads, in the guarded shape the persona and
    CodeRabbit and version gates use, so a FIFO or a link to
    a FIFO or a directory at the wiring path draws the named
    not a regular file problem and is never opened. A dangling
    link stands at the path but names no regular file, so it
    draws the same problem. The wiring ships in the tree, so
    an absent path draws the named missing problem rather
    than passing in silence. Bytes that are not UTF-8 draw
    the named does not parse problem and never a traceback.
    """
    if path.is_symlink() or path.exists():
        if not path.is_file():
            return None, ".antigravity/hooks.json is not a regular file"
        try:
            return path.read_text(encoding="utf-8"), None
        except (OSError, UnicodeDecodeError) as exc:
            return None, (
                ".antigravity/hooks.json does not parse, %s, so the "
                "PreToolUse wiring is not a planned state" % exc
            )
    return None, (
        ".antigravity/hooks.json is missing, so the PreToolUse "
        "wiring the brief documents has no file behind it"
    )


def hook_problems(root=None):
    """Problems with the shipped PreToolUse hook wiring.

    A missing or unparseable hook file is a planned degraded
    state, never a silent pass, so either fails this gate. The
    wiring must stand in the form the primary hooks page
    documents, a top level mapping from hook names to event
    configurations, because a host reading that form finds no
    named hook and nothing to execute in any other shape.
    Statement S1 of the brief states that the wiring maps the
    one hook name to one PreToolUse entry, that the entry
    matcher names invoke_subagent, and that the entry carries
    one command handler naming the shipped packet gate
    script, so the wiring must stand in exactly that shape
    and the script the command names must stand in the tree
    as a regular file. The decisions the script returns are
    the brief contract statements S3 and S4 and S5, and the
    shipped tests run the script itself over the packet
    manifest states those statements name. An enabled flag
    on the hook configuration is part of that shape, so a
    non boolean value fails, and a false value fails by
    name as well, because a host reading that flag runs no
    hook at all and the gate must not certify wiring that
    stands switched off.
    """
    root = ROOT if root is None else root
    path = root / ".antigravity" / "hooks.json"
    raw, problem = read_hook_wiring(path)
    if problem is not None:
        return [problem]
    try:
        data = strict_json_loads(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        return [
            ".antigravity/hooks.json does not parse, %s, so the "
            "PreToolUse wiring is not a planned state" % exc
        ]
    if not isinstance(data, dict):
        return [".antigravity/hooks.json is not a JSON object"]
    problems = []
    for key in sorted(set(data) - {HOOK_NAME}):
        problems.append(
            ".antigravity/hooks.json carries the top level key "
            "%r, which is not the one hook name the brief "
            "states, so a host reading the primary form finds "
            "no named hook under it" % key
        )
    config = data.get(HOOK_NAME)
    if config is None:
        problems.append(
            ".antigravity/hooks.json maps no hook named %r, so "
            "the wiring names no hook a host can run" % HOOK_NAME
        )
        return problems
    if not isinstance(config, dict):
        problems.append(
            "the %r hook value is not an event configuration "
            "object" % HOOK_NAME
        )
        return problems
    for key in sorted(set(config) - {"PreToolUse", "enabled"}):
        problems.append(
            "the %r hook carries the %r key, which is not "
            "the one PreToolUse event configuration or the "
            "enabled flag the primary form carries"
            % (HOOK_NAME, key)
        )
    if "enabled" in config and not isinstance(
        config.get("enabled"), bool
    ):
        problems.append(
            "the %r hook carries an enabled value that is "
            "not a boolean" % HOOK_NAME
        )
    if config.get("enabled") is False:
        problems.append(
            "the %r hook carries enabled false, so the "
            "wiring stands switched off and a host reading "
            "that flag runs no hook at all, while the gate "
            "would still certify the wiring" % HOOK_NAME
        )
    entries = config.get("PreToolUse")
    if not isinstance(entries, list) or not entries:
        problems.append(
            ".antigravity/hooks.json carries no PreToolUse "
            "entry under the %r hook, so the wiring names no "
            "event a host can run" % HOOK_NAME
        )
        return problems
    if len(entries) != 1:
        problems.append(
            ".antigravity/hooks.json declares %d PreToolUse "
            "entries, so the wiring does not declare the one "
            "PreToolUse entry the brief states" % len(entries)
        )
    entry = entries[0]
    if not isinstance(entry, dict):
        problems.append("the PreToolUse entry is not an object")
        return problems
    for key in sorted(set(entry) - {"matcher", "hooks"}):
        problems.append(
            "the PreToolUse entry carries the %r key, which "
            "the primary entry form does not carry" % key
        )
    if entry.get("matcher") != HOOK_MATCHER:
        problems.append(
            "the PreToolUse entry matcher names %r, not %r, so "
            "the wiring is not the build's declared mapping "
            "for the review run tool call"
            % (entry.get("matcher"), HOOK_MATCHER)
        )
    handlers = entry.get("hooks")
    if not isinstance(handlers, list) or not handlers:
        problems.append(
            "the PreToolUse entry carries no hooks array, so "
            "it names no handler a host can run"
        )
        return problems
    if len(handlers) != 1:
        problems.append(
            "the PreToolUse entry declares %d handlers, so "
            "the wiring does not declare the one command "
            "handler the brief states" % len(handlers)
        )
    handler = handlers[0]
    if not isinstance(handler, dict):
        problems.append("the PreToolUse handler is not an object")
        return problems
    for key in sorted(set(handler) - {"type", "command", "timeout"}):
        problems.append(
            "the PreToolUse handler carries the %r key, which "
            "the primary handler form does not carry" % key
        )
    if "timeout" in handler and (
        not isinstance(handler.get("timeout"), int)
        or isinstance(handler.get("timeout"), bool)
        or handler.get("timeout") <= 0
    ):
        problems.append(
            "the PreToolUse handler carries a timeout that "
            "is not a positive integer number of seconds"
        )
    if handler.get("type") != "command":
        problems.append(
            "the PreToolUse handler carries type %r, not "
            "'command', so it names no command a host can run"
            % (handler.get("type"),)
        )
    if handler.get("command") != HOOK_COMMAND:
        problems.append(
            "the PreToolUse handler command reads %r, not %r, "
            "so the wiring does not run the shipped packet "
            "gate script"
            % (handler.get("command"), HOOK_COMMAND)
        )
    script = root / ".antigravity" / HOOK_SCRIPT
    if script.is_symlink() or not script.is_file():
        problems.append(
            "the packet gate script at .antigravity/%s is "
            "missing or not a regular file, so the command "
            "the wiring names runs nothing" % HOOK_SCRIPT
        )
    return problems


def plugin_manifest_problems(root=None):
    """Problems with the shipped Antigravity plugin manifest.

    The schema the primary plugins page prints permits the
    name and the description beside the $schema key its own
    example carries, and sets additional properties to
    false. A shipped manifest carrying any further key, a
    version or a notes field among them, fails that schema
    in the schema's own words, so this gate reads the
    manifest the brief declares and refuses every key
    outside the permitted set by name.
    """
    root = ROOT if root is None else root
    path = root / ".antigravity" / "plugin.json"
    raw = read_text(path)
    if raw is None:
        return [".antigravity/plugin.json is missing"]
    try:
        data = strict_json_loads(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        return [".antigravity/plugin.json does not parse, %s" % exc]
    if not isinstance(data, dict):
        return [".antigravity/plugin.json is not a JSON object"]
    problems = []
    for key in sorted(set(data) - MANIFEST_KEYS):
        problems.append(
            ".antigravity/plugin.json carries the %r key, "
            "which the primary manifest schema forbids, so "
            "the manifest does not validate against its own "
            "$schema" % key
        )
    for key in sorted(MANIFEST_KEYS - set(data)):
        problems.append(
            ".antigravity/plugin.json carries no %r key, "
            "which the primary manifest schema names" % key
        )
    if "$schema" in data and data.get("$schema") != MANIFEST_SCHEMA:
        problems.append(
            ".antigravity/plugin.json carries $schema %r, not "
            "the value the primary plugins page names"
            % (data.get("$schema"),)
        )
    if "name" in data and data.get("name") != MANIFEST_NAME:
        problems.append(
            ".antigravity/plugin.json names %r, not %r"
            % (data.get("name"), MANIFEST_NAME)
        )
    if "description" in data and not data.get("description"):
        problems.append(
            ".antigravity/plugin.json carries no description"
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
    problems = []
    if DECISION_STATEMENT not in record:
        problems.append(
            "the Build 12 decision record carries no decision 4 "
            "statement, which every landed build must record"
        )
    flat = re.sub(r"\s+", " ", record)
    if DECISION_CORRECTION_DATE not in flat \
            or DECISION_CORRECTION not in flat:
        problems.append(
            "the Build 12 decision record carries no dated "
            "correction recording that the hook wiring now "
            "enforces the contract through the shipped packet "
            "gate script, so its round 24 never enforce "
            "statement stands uncorrected beside the shipped "
            "wiring"
        )
    return problems


def antigravity_problems(root=None):
    """Every Build 12 Antigravity plugin alteration problem."""
    problems = []
    problems.extend(brief_problems(root))
    problems.extend(statements_problems(root))
    problems.extend(plugin_manifest_problems(root))
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
