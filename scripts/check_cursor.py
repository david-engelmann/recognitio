#!/usr/bin/env python3
"""Pin the Build 10 Cursor plugin contract.

The brief at docs/cursor-plugin-brief.md exploits the Cursor
Plugin manifest, the six component packaging rules, the Bugbot
rules in .cursor/BUGBOT.md, and the .cursor/config/bugbot.yaml
repo config. Decision 4 binds this build like every other build.
The plugin and the Bugbot rules advise and never enforce, so this
script pins the contract without a Cursor host. It requires the
manifest to name the plugin in lowercase kebab-case with
relative paths only, every manifest path and every marketplace
entry path to resolve from the one plugin root, which is the
repository root in this tree, the skill copy to be a real directory that
is byte identical to the canonical skill because the host skips
symlinks that point outside the local plugin folder, every
Bugbot rule to carry a checkable derivation note, the shipped
bugbot.yaml to hold only documented fields because unknown fields
fall back silently, and the brief to keep the stated pins, the
verbatim primary quotes, and the desktop run record that
discharged the client run the brief once carried as owed. A
later edit that drops any of them fails the gate instead of
drifting in silence. The gate also pins the README Cursor
passage to the shipped package position, because no Cursor
Marketplace listing exists or has been submitted, and it
refuses the stale marketplace distribution wording outright.
The gate pins the plugin README under .cursor-plugin to the
same shipped package position and refuses the same stale
wording in that file, because the round 1 addendum found the
claim surviving there after the root README was corrected.
The round 5 repairs extend the stale wording refusal to the
brief itself, pin the canonical T0 name set in rule B3 and in
the shipped Bugbot rule B3, refuse operative content after
the final Bugbot rule derivation note and any auto approve
or auto merge claim or plainly worded merge claim in that
file, pin the operative header sentence of the Bugbot YAML
config, refuse a scoped Bugbot verified claim family in the
brief beside its unverified pin, stated as Bugbot behaviour
on a real pull request verified or confirmed or proven and
read sentence by sentence with a negated claim clause
stating no claim, and pin the README pinning block command
in the form the brief states. Each of those families is
narrow and named, and prose outside them stays a human
review surface.
"""

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RULES_HEADING = "## The review rules"

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

# Primary Cursor citations a derivation note may name, written as
# URL stems so the note pins the surface the claim was read from.
PRIMARY_CITATIONS = (
    "cursor.com/docs/bugbot",
    "cursor.com/docs/plugins",
    "cursor.com/docs/reference/plugins",
    "cursor.com/docs/mcp",
    "cursor.com/docs/skills",
)

# The manifest component keys the primary packaging rules name.
COMPONENT_KEYS = ("skills", "rules", "agents", "commands")

# The shipped component values the brief pins in its own
# sentences. Agreement between the manifest and the
# marketplace entry plus resolvability from the plugin root
# is not enough on its own, because both files can repoint
# together at another real in root target and keep agreeing
# while the shipped components move. The gate therefore
# pins the values themselves beside the agreement.
SHIPPED_SKILLS = ["./.cursor-plugin/skills/recognitio/"]
SHIPPED_RULES = ["./.cursor-plugin/rules/recognitio.mdc"]
SHIPPED_LOGO = "docs/brand/recognitio-icon.svg"

# The shipped manifest description, pinned as a value so the
# entry and metadata descriptions the marketplace checks
# compare against it cannot drift as one body with it.
SHIPPED_DESCRIPTION = (
    "Pulls the relevant changes from a pull request or a "
    "commit range, with the context a reviewer needs, into "
    "one verified review packet."
)

# The shipped manifest author and marketplace name, pinned
# as values so the marketplace owner agreement the gate
# checks has an anchor of its own instead of two texts
# that can drift together.
SHIPPED_AUTHOR_NAME = "David Engelmann"
SHIPPED_AUTHOR_EMAIL = (
    "81196676+david-engelmann@users.noreply.github.com"
)
SHIPPED_MARKETPLACE_NAME = "recognitio-marketplace"
SHIPPED_PLUGIN_NAME = "recognitio"

# Manifest top level keys the shipped manifest may carry. The
# list is closed on purpose, so an invented manifest key fails
# the gate instead of riding along unexamined.
MANIFEST_KEYS = (
    "name", "version", "description", "license", "author",
    "skills", "rules", "agents", "commands", "variables", "logo",
    "displayName", "homepage", "repository", "keywords",
    "category", "tags",
)

# The discovery field values the primary manifest schema
# names and the top 20 program filled. The discovery gate
# at scripts/check_discovery.py pins the agreement of these
# values with the Claude surfaces.
DISCOVERY_FIELDS = {
    "displayName": "Recognitio",
    "homepage": "https://github.com/david-engelmann/recognitio",
    "repository": "https://github.com/david-engelmann/recognitio",
    "category": "developer-tools",
    "keywords": [
        "agent-skills", "code-review", "diff", "git",
        "pull-request", "review-packet",
    ],
    "tags": [
        "agent-skills", "code-review", "diff", "git",
        "pull-request", "review-packet",
    ],
}

# The only repo bugbot.yaml fields the primary docs name. An
# unknown field falls back silently down the precedence order,
# so the gate rejects it outright.
BUGBOT_YAML_FIELDS = {"autofix"}
AUTOFIX_FIELDS = {"mode"}
# The autofix.mode values the primary page names in its example.
AUTOFIX_MODES = {"newBranch", "disabled"}
# The one autofix.mode value this build ships. The brief states
# that the shipped file sets mode to disabled and that decision 4
# keeps Autofix off in this repo, and the shipped file states the
# same position in its own comment. The gate therefore pins the
# exact shipped value beside the primary vocabulary above, so a
# move to newBranch fails here even though the primary page names
# that value, because newBranch turns Autofix on.
PINNED_AUTOFIX_MODE = "disabled"

YAML_SIZE_LIMIT = 64 * 1024
RULE_CHAR_LIMIT = 30000
RULES_COMBINED_LIMIT = 100000
MARKETPLACE_SIZE_LIMIT = 10 * 1024 * 1024

VERSION_SHAPE = r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
NAME_SHAPE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_KEY = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*:\s*\S")

# Brief sentences the gate pins. Each is a fragment of the exact
# sentence the brief carries, so a later edit that softens or
# drops a stated pin, quote, or limit fails loudly.
PINNED = (
    ("the symlink skip",
     "Cursor skips a symlink that points to a plugin repository "
     "elsewhere on disk"),
    ("the copy protocol",
     "Copy your plugin files into that folder"),
    ("the open source requirement",
     "All plugins must be open source"),
    ("the manual review of every update",
     "we review each update before publishing"),
    ("the plugin root variable",
     "Use `${CURSOR_PLUGIN_ROOT}` for the plugin root"),
    ("the no expansion scope",
     "Cursor does not expand the standard's `${PLUGIN_ROOT}` and "
     "`${PLUGIN_DATA}` variables in `mcp.json`"),
    ("the yaml read surface",
     "Bugbot reads `.cursor/config/bugbot.yaml` at the repo root "
     "from the PR's base branch"),
    ("the precedence order",
     "then `.cursor/config/bugbot.yaml`, then team and "
     "organization settings from the dashboard"),
    ("the autofix lower only",
     "it can lower the Autofix mode from the dashboard settings "
     "but it cannot raise it"),
    ("the silent fallback",
     "Bugbot ignores that field and falls back to the next "
     "setting in the precedence order"),
    ("the 64 KB yaml cap",
     "ignores files larger than 64 KB"),
    ("the effort dashboard setting",
     "Bugbot Teams includes the ability to set the effort level "
     "Bugbot uses for reviews"),
    ("the four effort levels",
     "The four effort levels are Low, Default, High, and Smart"),
    ("the Smart limit",
     "does not read the PR description, labels, or BUGBOT.md "
     "when it chooses a level"),
    ("the neutral default",
     "this is the default conclusion when Bugbot reports "
     "findings"),
    ("the gate trap",
     "Requiring the status alone does not block merges on "
     "findings because findings default to `neutral`"),
    ("the fail on unresolved",
     "enable it to make unresolved findings produce a failing "
     "status"),
    ("the vacuous autofix check",
     "uses only `success` or `neutral`, so requiring that check "
     "is vacuous"),
    ("the 30k per rule cap",
     "truncated at 30,000 characters"),
    ("the 100k combined cap",
     "capped at 100,000 characters"),
    ("the unbounded latency",
     "carried as an unbounded risk"),
    ("the update pinning",
     "keeps the plugin versions it started with"),
    ("the variables schema decision",
     "never declare `${CURSOR_PLUGIN_ROOT}` there"),
    ("the mcp omission",
     "The plugin carries no `mcp.json`"),
    ("the discovery fields",
     "The manifest also carries the discovery fields the "
     "primary manifest schema names"),
    ("the discovery values",
     "The plugin sets displayName to Recognitio and homepage "
     "and repository to the repository page"),
    ("the canvases mention",
     "Hex Canvas and Atlassian Canvas"),
    ("the duplicate skill guidance",
     "Never ship two separate copies of the same skill"),
    ("the Security Review separation",
     "Security Review is a separate bot from Bugbot"),
    ("the Security Review scope",
     "injection across SQL, command, and template surfaces"),
    ("the Security Review team rules",
     "enforces them on every pull request"),
    ("the Security Review draft skip",
     "Draft pull requests are skipped"),
    ("the Security Review plan gate",
     "gated to Teams and Enterprise plans"),
    ("the review-security skill",
     "built in review-security skill"),
    ("the Origin launch path",
     "Origin App Marketplace launched October 13 2026"),
    ("the Origin not only plugin path",
     "not the only CodeRabbit in Cursor path"),
    ("the decision 4 statement",
     "Decision 4 binds this build like every other build"),
    ("the CLI attempt manifest absence",
     "no session included a recognitio plugin manifest"),
    ("the plugin tree not an installed plugin on the CLI surface",
     "a plugin tree at a repo root did not present as an "
     "installed plugin on that surface"),
    ("the shipped tree skill entry spelling",
     "the entry pointed at the .claude/skills spelling "
     "of the canonical skill"),
    ("the duplicate resolution on the CLI surface",
     "both repeat sessions resolved the entry to that "
     "copy"),
    ("the plugin tree copy never a skill entry",
     "the plugin tree copy never appeared as a skill "
     "entry in any session"),
    ("the skill count instability",
     "no claim in this note rests on a skill count"),
    ("the CLI rule surface observation",
     "no session named the plugin rule file or BUGBOT.md "
     "as in effect on that surface"),
    ("the duplicate residual settled at registration",
     "The duplicate skill residual is settled at the "
     "level of desktop registration"),
    ("the desktop run build",
     "the official Cursor desktop build 3.27.12 for "
     "Linux ran here under a virtual display"),
    ("the desktop plugin load record",
     "recorded the recognitio plugin loaded with zero "
     "failures five times in the first launch"),
    ("the desktop load before sign in",
     "every recorded load happened before any sign-in"),
    ("the Customize backing records confirm",
     "the Customize backing records, which list a skill "
     "entry and a rule entry pointing at the local "
     "plugin copies"),
    ("the desktop duplicate registration",
     "the Customize backing records held two recognitio "
     "skill entries side by side"),
    ("the desktop duplicate no dedupe",
     "the desktop deduped neither entry"),
    ("the invocation precedence settled on the CLI surface",
     "Invocation precedence is settled on the agent CLI "
     "surface"),
    ("the precedence open on the desktop client alone",
     "stays open on the desktop client alone"),
    ("the CLI precedence session states",
     "two in the shipped state and two in the duplicate "
     "state"),
    ("the CLI precedence copy markers",
     "a distinct marker line appended to each copy of "
     "the skill"),
    ("the installed plugin copy in the CLI precedence home",
     "installed at .cursor/plugins/local/recognitio in "
     "the session home"),
    ("the shipped state workspace invocation",
     "each session invoked the workspace copy at the "
     ".claude/skills/recognitio/SKILL.md spelling"),
    ("the plugin copy second entry never invoked",
     "registered as a second entry and was never invoked"),
    ("the duplicate state added copy invocation",
     "each session invoked the added copy at "
     ".cursor/skills/recognitio/SKILL.md"),
    ("the duplicate seat taken outright",
     "took the workspace seat outright while the .claude "
     "spelling entry left the catalog"),
    ("the plugin tree no entry in the CLI precedence run",
     "The repo root plugin tree at .cursor-plugin "
     "appeared as an entry in no session"),
    ("the desktop sign in landing failure",
     "no signed-in desktop session could be landed on "
     "this box"),
    ("the desktop poll received no completed sign in",
     "login-session poll never received a completed "
     "sign-in across the original run and the repaired "
     "relaunch"),
    ("the precedence evidence record",
     "the evidence stands in the desktop precedence "
     "report and the sign-in repair report"),
    ("the marketplace and Bugbot items unverified",
     "Marketplace installation from a listing and Bugbot "
     "behaviour on a real pull request stay UNVERIFIED"),
    ("the single plugin root base",
     "every path the manifest and the marketplace entry "
     "carry resolves from that one base"),
    ("the shipped component paths",
     "The shipped skills value is "
     "`./.cursor-plugin/skills/recognitio/` and the shipped "
     "rules value is `./.cursor-plugin/rules/recognitio.mdc`"),
    ("the local load nested manifest",
     "the local load route copies this repository folder "
     "into the local plugin folder, so the manifest sits at "
     "`.cursor-plugin/plugin.json` inside the copied folder"),
    ("the corrected layout run unverified",
     "a fresh desktop run of the corrected layout stands "
     "UNVERIFIED"),
    ("the glance layout bound",
     "The desktop load stands proven for the layout that "
     "stood before the later correction, and a fresh desktop "
     "run of the corrected layout stands unverified"),
)

# Brief fragments the desktop verification run of 2026-10-25
# superseded. The positive pins prove the corrected sentences
# are stated, but a restored stale sentence would pass beside
# them, so the gate also refuses the old wordings outright.
STALE = (
    "no Cursor client",
    "the real client run is owed",
    "desktop client run remains owed",
    "stands in until that run happens",
    "load behaviour in the desktop client stays UNVERIFIED",
    "stays UNVERIFIED for the desktop client",
    "duplicate skill residual stays UNVERIFIED",
)

# Brief fragments the agent CLI precedence run of
# 2026-10-25 superseded. The run settled invocation
# precedence on that surface, so the open wording it
# replaced fails the gate even beside the settled
# sentences.
STALE_PRECEDENCE = (
    "Invocation precedence stays open",
    "with no precedence field in the Customize data",
    "a sign-in the run did not perform",
)

# README Cursor passage fragments the gate pins. The plugin
# ships in this repo as a plugin package and no Cursor
# Marketplace listing exists or has been submitted, so the
# README states that position and the local load route.
README_PINNED = (
    ("the plugin package position",
     "The plugin ships in this repo as a plugin package"),
    ("the no listing position",
     "No Cursor Marketplace listing exists or has been "
     "submitted"),
    ("the local load route position",
     "so the local load route below is the route"),
    ("the local load test",
     "For a local load test, copy this repository folder "
     "into the local plugin folder"),
)

# README wording the gate refuses outright. The positive
# pins prove the corrected sentences are stated, but a
# restored stale sentence would pass beside them.
README_STALE = (
    "distributed through the manually reviewed Cursor "
    "Marketplace",
    "distributed through the Cursor Marketplace",
    "reviewed updates auto deploy",
)

# Plugin README Installing fragments the gate pins. The
# plugin README states the same shipped package position as
# the root README, and its local load sentence names this
# folder and its local load command.
PLUGIN_README_PINNED = (
    ("the plugin package position",
     "The plugin ships in this repo as a plugin package"),
    ("the no listing position",
     "No Cursor Marketplace listing exists or has been "
     "submitted"),
    ("the local load route position",
     "so the local load route below is the route"),
    ("the local load test",
     "For a local load test, copy this repository folder "
     "into the local plugin folder"),
    ("the local load command",
     "cp -r . ~/.cursor/plugins/local/recognitio"),
)

# Plugin README wording the gate refuses outright. The list
# covers the whole marketplace behaviour passage the file
# once carried, including the manual review claim, the auto
# deploy claim, and the Cloud Agent version claim tied to
# marketplace updates.
PLUGIN_README_STALE = (
    "distributed through the manually reviewed Cursor "
    "Marketplace",
    "distributed through the Cursor Marketplace",
    "Every plugin is manually reviewed before it is listed",
    "manually reviewed before it is listed",
    "all plugins must be open source",
    "Reviewed updates auto deploy",
    "reviewed updates auto deploy",
    "auto deploy to clients pinned at the commit SHA",
    "with no user version pinning",
    "A running Cloud Agent keeps the plugin versions "
    "it started with",
    "keeps the plugin versions it started with",
)

DECISION_HEADING = "## 19. Build 10"
DECISION_STATEMENT = "Decision 4 binds"


class DuplicateKeyError(ValueError):
    """A JSON object holds the same key twice."""


def _reject_duplicate_keys(pairs):
    record = {}
    for key, value in pairs:
        if key in record:
            raise DuplicateKeyError("repeated key %r" % (key,))
        record[key] = value
    return record


def strict_json_loads(text):
    """Parse JSON refusing a repeated key in any object."""
    return json.loads(text, object_pairs_hook=_reject_duplicate_keys)


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
    """The rule blocks in order, split on their B numbered headings."""
    parts = re.split(r"(?m)^### B\d+\.", section)
    return [part for part in parts[1:]]


def is_bytecode_cache(path):
    """Whether a path is a compiled bytecode cache file.

    Only a bytecode file standing inside a cache directory is
    build state. A cache name alone excludes nothing, so a
    manifest or plugin file wearing a cache folder name or a
    cache suffix is counted like any other file, which is the
    census blindness rounds 286 and 294 filed. The bytecode
    file must stand directly in the cache directory, the one
    shape an interpreter writes, so a payload nested below a
    cache directory is counted like any other file.
    """
    return (
        len(path.parts) >= 2
        and path.parts[-2] == "__pycache__"
        and path.suffix == ".pyc"
    )


def tree_bytes(directory):
    """Map every file under a directory to its bytes.

    Compiled bytecode caches are build state, not skill content,
    so bytecode cache files are excluded the way the portable
    package check excludes them. The exclusion is keyed on the
    bytecode shape alone, so a file that merely wears a cache
    name is read and compared like any other file.
    """
    found = {}
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        if is_bytecode_cache(path):
            continue
        rel = str(path.relative_to(directory))
        found[rel] = path.read_bytes()
    return found


def _resolve_from_root(root, value):
    """The resolved target of a path read from the plugin root.

    Returns the target when it stays inside the root and
    None when it escapes, so every manifest and entry path
    reading in this gate resolves from the one base through
    the same sequence instead of through copies that can
    drift apart on the base question.
    """
    target = (root / value).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return None
    return target


def _same_path_values(value, shipped):
    """Whether a component value carries the shipped paths.

    A trailing slash on a directory value names the same
    directory with or without it, so the comparison reads
    past that spelling alone and pins the target itself.
    """
    if not isinstance(value, list) or len(value) != len(shipped):
        return False
    return all(
        isinstance(item, str)
        and item.rstrip("/") == pinned.rstrip("/")
        for item, pinned in zip(value, shipped)
    )


def manifest_problems(root=None):
    """Problems with the Cursor plugin manifest."""
    root = ROOT if root is None else root
    path = root / ".cursor-plugin" / "plugin.json"
    raw = read_text(path)
    if raw is None:
        return [".cursor-plugin/plugin.json is missing"]
    try:
        data = strict_json_loads(raw)
    except (ValueError, DuplicateKeyError) as exc:
        return [".cursor-plugin/plugin.json does not parse, %s" % exc]
    if not isinstance(data, dict):
        return [".cursor-plugin/plugin.json is not an object"]
    problems = []
    unknown = sorted(set(data) - set(MANIFEST_KEYS))
    if unknown:
        problems.append(
            ".cursor-plugin/plugin.json carries unknown keys %s, "
            "so the manifest shape is not the pinned one"
            % ", ".join(unknown)
        )
    name = data.get("name")
    if not isinstance(name, str) or not NAME_SHAPE.match(name):
        problems.append(
            ".cursor-plugin/plugin.json names %r, which is not "
            "lowercase kebab-case" % (name,)
        )
    elif name != SHIPPED_PLUGIN_NAME:
        problems.append(
            ".cursor-plugin/plugin.json names %r and the "
            "shipped plugin name is %r, so the plugin "
            "renamed itself while every name agreement "
            "check still passed"
            % (name, SHIPPED_PLUGIN_NAME)
        )
    version = data.get("version")
    claude_raw = read_text(root / ".claude-plugin" / "plugin.json")
    claude_version = None
    if claude_raw is not None:
        try:
            claude_version = strict_json_loads(claude_raw).get(
                "version"
            )
        except (ValueError, DuplicateKeyError):
            claude_version = None
    if not isinstance(version, str) or not re.fullmatch(
        VERSION_SHAPE, version
    ):
        problems.append(
            ".cursor-plugin/plugin.json carries no valid version"
        )
    elif version != claude_version:
        problems.append(
            ".cursor-plugin/plugin.json is at version %s while the "
            "Claude Code manifest is at %s, so the surfaces "
            "disagree" % (version, claude_version)
        )
    if not data.get("description"):
        problems.append(
            ".cursor-plugin/plugin.json carries no description"
        )
    elif not isinstance(data.get("description"), str):
        problems.append(
            ".cursor-plugin/plugin.json carries description %r, "
            "which is not the string the primary manifest schema "
            "names" % (data.get("description"),)
        )
    elif data.get("description") != SHIPPED_DESCRIPTION:
        problems.append(
            ".cursor-plugin/plugin.json carries description %r "
            "and the shipped description is %r, so the manifest "
            "text moved while every agreement check would still "
            "pass" % (data.get("description"), SHIPPED_DESCRIPTION)
        )
    author = data.get("author")
    if isinstance(author, dict):
        for key in sorted(set(author) - {"name", "email"}):
            problems.append(
                ".cursor-plugin/plugin.json author carries "
                "the %r key, which is not an author key the "
                "agreement pins, so it stands unexamined"
                % key
            )
    if not isinstance(author, dict) or (
        author.get("name") != SHIPPED_AUTHOR_NAME
        or author.get("email") != SHIPPED_AUTHOR_EMAIL
    ):
        problems.append(
            ".cursor-plugin/plugin.json carries author %r and "
            "the shipped author is %s at %s, so the agreement "
            "the marketplace owner is checked against has no "
            "anchor" % (
                author, SHIPPED_AUTHOR_NAME, SHIPPED_AUTHOR_EMAIL
            )
        )
    for field, expected in DISCOVERY_FIELDS.items():
        if data.get(field) != expected:
            problems.append(
                ".cursor-plugin/plugin.json carries %s %r and "
                "the pinned discovery value is %r"
                % (field, data.get(field), expected)
            )
    if not _same_path_values(data.get("skills"), SHIPPED_SKILLS):
        problems.append(
            ".cursor-plugin/plugin.json carries skills %r and "
            "the shipped skills value is %r, so the manifest "
            "does not carry the component path the brief pins"
            % (data.get("skills"), SHIPPED_SKILLS)
        )
    if not _same_path_values(data.get("rules"), SHIPPED_RULES):
        problems.append(
            ".cursor-plugin/plugin.json carries rules %r and "
            "the shipped rules value is %r, so the manifest "
            "does not carry the component path the brief pins"
            % (data.get("rules"), SHIPPED_RULES)
        )
    # The brief pins the shipped shape as carrying no
    # agents and no commands, the same sentence whose MCP
    # limb the mcp.json absence check below enforces. A
    # manifest that gains either component key certifies a
    # plugin the brief says does not ship, however well its
    # paths resolve, so the absence itself is pinned here.
    for key in ("agents", "commands"):
        if key in data:
            problems.append(
                ".cursor-plugin/plugin.json carries %s %r, "
                "and the brief pins the plugin as shipping "
                "no %s, so the component stands refused"
                % (key, data.get(key), key)
            )
    logo = data.get("logo")
    if logo is not None:
        if logo != SHIPPED_LOGO:
            problems.append(
                ".cursor-plugin/plugin.json names the logo %r "
                "and the shipped logo value is %r"
                % (logo, SHIPPED_LOGO)
            )
        if not isinstance(logo, str) or os.path.isabs(logo) \
                or ".." in Path(logo).parts:
            problems.append(
                ".cursor-plugin/plugin.json names the logo %r, "
                "which is not a relative path inside the plugin "
                "root" % (logo,)
            )
        else:
            target = _resolve_from_root(root, logo)
            if target is None:
                problems.append(
                    ".cursor-plugin/plugin.json names the logo "
                    "%r, which escapes the plugin root" % (logo,)
                )
            elif target.is_symlink() or not target.is_file():
                problems.append(
                    ".cursor-plugin/plugin.json names the "
                    "logo %r, which is not a real file at "
                    "the plugin root" % (logo,)
                )
    plugin_dir = root / ".cursor-plugin"
    # Every manifest path resolves from the one plugin root,
    # the folder that holds the .cursor-plugin folder, which
    # is the repository root in this tree. A path written
    # from the manifest folder instead resolves nowhere from
    # that base, so the gate reads each path from the root.
    for key in COMPONENT_KEYS:
        entries = data.get(key, [])
        if not isinstance(entries, list):
            problems.append(
                ".cursor-plugin/plugin.json carries a non list %s "
                "component" % key
            )
            continue
        for entry in entries:
            if not isinstance(entry, str):
                problems.append(
                    ".cursor-plugin/plugin.json carries a non string "
                    "path under %s" % key
                )
                continue
            if os.path.isabs(entry) or ".." in Path(entry).parts:
                problems.append(
                    ".cursor-plugin/plugin.json declares %r under "
                    "%s, which is not a relative path inside the "
                    "plugin" % (entry, key)
                )
                continue
            target = _resolve_from_root(root, entry)
            if target is None:
                problems.append(
                    ".cursor-plugin/plugin.json declares %r under "
                    "%s, which escapes the plugin root"
                    % (entry, key)
                )
                continue
            if entry.rstrip("/").endswith(".mdc") or entry.endswith(
                (".md", ".markdown")
            ):
                if target.is_symlink() or not target.is_file():
                    problems.append(
                        ".cursor-plugin/plugin.json declares %r "
                        "under %s, which is not a real file"
                        % (entry, key)
                    )
                    continue
                front = read_text(target)
                if front is None or not front.startswith("---"):
                    problems.append(
                        "%s carries no frontmatter block" % entry
                    )
                elif "\n---" not in front[3:]:
                    problems.append(
                        "%s carries an unclosed frontmatter block"
                        % entry
                    )
                else:
                    head = front[3:].split("\n---", 1)[0]
                    if not any(
                        FRONTMATTER_KEY.match(line)
                        for line in head.splitlines()
                    ):
                        problems.append(
                            "%s carries no description in its "
                            "frontmatter" % entry
                        )
            else:
                if target.is_symlink():
                    problems.append(
                        ".cursor-plugin/plugin.json declares %r "
                        "under %s, which is a symlink the host "
                        "would skip" % (entry, key)
                    )
                elif not target.is_dir():
                    problems.append(
                        ".cursor-plugin/plugin.json declares %r "
                        "under %s, which is not a real directory"
                        % (entry, key)
                    )
    variables = data.get("variables", {})
    if not isinstance(variables, dict):
        problems.append(
            ".cursor-plugin/plugin.json carries a non object "
            "variables schema"
        )
    elif variables:
        # The brief ties every declared name to a variable
        # the plugin own mcp.json uses, in the checklist
        # sentence that requires declaring every such
        # variable, and its decision permits only non
        # platform variables there. The user set values the
        # brief names are the values a user sets for a
        # variable the plugin declares, not a licence to
        # invent declaration names, so a declared name with
        # no such correspondence is refused, and an entry
        # standing as a bare value is no schema at all. The
        # plugin ships no mcp.json today and the absence
        # check below refuses one, so the correspondence
        # set stands empty on the shipped tree, and the
        # lane that adds an mcp.json widens it by the file
        # it adds.
        used = set()
        mcp_path = plugin_dir / "mcp.json"
        if mcp_path.is_file():
            # The correspondence reads the file as the
            # structure it is, not as raw text, so a
            # mention inside a description string earns
            # nothing and a file that does not parse
            # earns nothing. The names are read from the
            # file's string values, with a description
            # excepted at any depth and in any shape, in
            # the spellings the hosts substitute, the
            # braced form with its operator value and
            # spacing spellings and the braceless form
            # beside it.
            try:
                mcp_data = json.loads(
                    mcp_path.read_text(encoding="utf-8")
                )
            except ValueError:
                mcp_data = None
            values = []

            def collect(node, key=None, suppressed=False):
                suppressed = (
                    suppressed or key == "description"
                )
                if isinstance(node, dict):
                    for name, value in node.items():
                        collect(value, name, suppressed)
                elif isinstance(node, list):
                    for value in node:
                        collect(value, key, suppressed)
                elif isinstance(node, str) and (
                    not suppressed
                ):
                    values.append(node)

            if mcp_data is not None:
                collect(mcp_data)
            for value in values:
                used.update(
                    re.findall(
                        r"\$\{\s*(?:#|!)?\s*"
                        r"([A-Za-z_][A-Za-z0-9_]*)"
                        r"(?:[:]?[-=+?%/#@^,:][^}]*)?\s*\}"
                        r"|\$([A-Za-z_][A-Za-z0-9_]*)",
                        value,
                    )
                )
            used = {
                name
                for pair in used
                for name in pair
                if name
            }
        for key in sorted(variables):
            if key not in used:
                problems.append(
                    ".cursor-plugin/plugin.json declares "
                    "variable %r, which no variable in the "
                    "plugin mcp.json corresponds to"
                    % (key,)
                )
            elif not isinstance(variables[key], dict):
                problems.append(
                    ".cursor-plugin/plugin.json carries "
                    "variable %r standing as %r, which is "
                    "not the schema object the variables "
                    "decision names"
                    % (key, variables[key])
                )
    if isinstance(variables, dict) and (
        "CURSOR_PLUGIN_ROOT" in variables
    ):
        problems.append(
            ".cursor-plugin/plugin.json declares "
            "CURSOR_PLUGIN_ROOT in its variables schema, but the "
            "platform provided root is exempt from that checklist "
            "item"
        )
    if (plugin_dir / "mcp.json").exists():
        problems.append(
            ".cursor-plugin/mcp.json exists, but the brief pins "
            "the plugin as shipping no MCP servers"
        )
    return problems


def marketplace_problems(root=None):
    """Problems with the Cursor marketplace listing."""
    root = ROOT if root is None else root
    path = root / ".cursor-plugin" / "marketplace.json"
    raw = read_text(path)
    if raw is None:
        return [".cursor-plugin/marketplace.json is missing"]
    if len(raw.encode("utf-8")) > MARKETPLACE_SIZE_LIMIT:
        return [
            ".cursor-plugin/marketplace.json is over the 10 MB "
            "marketplace manifest cap"
        ]
    try:
        data = strict_json_loads(raw)
    except (ValueError, DuplicateKeyError) as exc:
        return [
            ".cursor-plugin/marketplace.json does not parse, %s" % exc
        ]
    if not isinstance(data, dict):
        return [".cursor-plugin/marketplace.json is not an object"]
    problems = []
    if data.get("name") != SHIPPED_MARKETPLACE_NAME:
        problems.append(
            ".cursor-plugin/marketplace.json names %r and the "
            "shipped marketplace name is %r, so the file's own "
            "name moved while its key set stayed closed"
            % (data.get("name"), SHIPPED_MARKETPLACE_NAME)
        )
    # The marketplace file's own key set is closed, the way
    # the entry key set below is closed, because a key no
    # reading examines can carry a component or a claim the
    # gate never sees in a file the gate claims to pin.
    for key in sorted(
        set(data) - {"name", "owner", "metadata", "plugins"}
    ):
        problems.append(
            ".cursor-plugin/marketplace.json carries the %r "
            "key, which is not a key of the marketplace file "
            "the agreement pins, so it stands unexamined"
            % key
        )
    manifest_raw = read_text(root / ".cursor-plugin" / "plugin.json")
    name = version = None
    manifest_skills = manifest_logo = None
    manifest_description = None
    manifest_components = {}
    if manifest_raw is not None:
        try:
            manifest = strict_json_loads(manifest_raw)
            name = manifest.get("name")
            version = manifest.get("version")
            manifest_skills = manifest.get("skills")
            manifest_logo = manifest.get("logo")
            manifest_description = manifest.get("description")
            for key in COMPONENT_KEYS:
                manifest_components[key] = manifest.get(key)
        except (ValueError, DuplicateKeyError):
            pass
    entries = data.get("plugins")
    if not isinstance(entries, list) or len(entries) != 1:
        problems.append(
            ".cursor-plugin/marketplace.json does not list exactly "
            "one plugin entry"
        )
    else:
        entry = entries[0]
        if entry.get("name") != name:
            problems.append(
                ".cursor-plugin/marketplace.json names %r while "
                "the manifest names %r" % (entry.get("name"), name)
            )
        if entry.get("version") != version:
            problems.append(
                ".cursor-plugin/marketplace.json is at version %r "
                "while the manifest is at %r"
                % (entry.get("version"), version)
            )
        if entry.get("description") != manifest_description:
            problems.append(
                ".cursor-plugin/marketplace.json entry carries "
                "description %r while the manifest carries %r, "
                "so the listing text a reader meets is not the "
                "manifest text the gate pins"
                % (entry.get("description"), manifest_description)
            )
        # The entry paths resolve from the entry source, and
        # the entry source names the plugin root, so the entry
        # must carry the manifest values themselves. An entry
        # path written from another base resolves nowhere
        # under its own source.
        if entry.get("source") != "./":
            problems.append(
                ".cursor-plugin/marketplace.json entry carries "
                "source %r, which is not the plugin root the "
                "manifest stands at" % (entry.get("source"),)
            )
        if entry.get("skills") != manifest_skills:
            problems.append(
                ".cursor-plugin/marketplace.json entry carries "
                "skills %r while the manifest carries %r, so "
                "the entry paths do not resolve from the entry "
                "source"
                % (entry.get("skills"), manifest_skills)
            )
        if entry.get("logo") != manifest_logo:
            problems.append(
                ".cursor-plugin/marketplace.json entry carries "
                "logo %r while the manifest carries %r"
                % (entry.get("logo"), manifest_logo)
            )
        # The entry agreement covers every key the entry
        # carries, not only the shipped ones. A key outside
        # the entry shape the agreement pins rides
        # unexamined, and a component key the shipped entry
        # does not carry must still agree with the manifest
        # and resolve from the plugin root, because a host
        # reading such a field from the entry would follow
        # it where it points.
        entry_keys = {
            "name", "version", "description", "source",
            "skills", "logo",
        } | set(COMPONENT_KEYS)
        for key in sorted(set(entry) - entry_keys):
            problems.append(
                ".cursor-plugin/marketplace.json entry carries "
                "the %r key, which is not an entry key the "
                "agreement pins, so it stands unexamined"
                % key
            )
        # The agents and commands absence the manifest pin
        # holds stands on the entry as well, because an entry
        # carrying either component certifies the same plugin
        # the brief says does not ship, whether or not the
        # manifest agrees with it.
        for key in ("agents", "commands"):
            if key in entry:
                problems.append(
                    ".cursor-plugin/marketplace.json entry "
                    "carries %s %r, and the brief pins the "
                    "plugin as shipping no %s, so the "
                    "component stands refused"
                    % (key, entry.get(key), key)
                )
        for key in ("rules",):
            if key not in entry:
                continue
            if entry.get(key) != manifest_components.get(key):
                problems.append(
                    ".cursor-plugin/marketplace.json entry "
                    "carries %s %r while the manifest carries "
                    "%r, so the entry paths do not resolve "
                    "from the entry source"
                    % (key, entry.get(key),
                       manifest_components.get(key))
                )
                continue
            for item in entry.get(key) or []:
                target = (
                    _resolve_from_root(root, item)
                    if isinstance(item, str) else None
                )
                if target is None or target.is_symlink() \
                        or not (target.is_file()
                                or target.is_dir()):
                    problems.append(
                        ".cursor-plugin/marketplace.json entry "
                        "carries %s %r, which does not resolve "
                        "from the plugin root" % (key, item)
                    )
    metadata = data.get("metadata", {})
    if not isinstance(metadata, dict):
        problems.append(
            ".cursor-plugin/marketplace.json carries metadata "
            "%r, which is not the object the entry format "
            "names, so its key set, version, and description "
            "stand unexamined" % (metadata,)
        )
    if isinstance(metadata, dict):
        for key in sorted(
            set(metadata) - {"description", "version"}
        ):
            problems.append(
                ".cursor-plugin/marketplace.json metadata "
                "carries the %r key, which is not a metadata "
                "key the agreement pins, so it stands "
                "unexamined" % key
            )
        if metadata.get("version") != version:
            problems.append(
                ".cursor-plugin/marketplace.json metadata is at "
                "version %r while the manifest is at %r"
                % (metadata.get("version"), version)
            )
        if (
            manifest_description is not None
            and metadata.get("description") != manifest_description
        ):
            problems.append(
                ".cursor-plugin/marketplace.json metadata "
                "carries description %r while the manifest "
                "carries %r, so the listing's second display "
                "text disagrees with the manifest"
                % (
                    metadata.get("description"),
                    manifest_description,
                )
            )
    owner = data.get("owner")
    if not isinstance(owner, dict):
        problems.append(
            ".cursor-plugin/marketplace.json carries owner %r, "
            "which is not the object the entry format names"
            % (owner,)
        )
    else:
        for key in sorted(set(owner) - {"name", "email"}):
            problems.append(
                ".cursor-plugin/marketplace.json owner carries "
                "the %r key, which is not an owner key the "
                "agreement pins, so it stands unexamined" % key
            )
        manifest_author = None
        if manifest_raw is not None:
            try:
                manifest_author = strict_json_loads(
                    manifest_raw
                ).get("author")
            except (ValueError, DuplicateKeyError):
                manifest_author = None
        if isinstance(manifest_author, dict):
            for field in ("name", "email"):
                if owner.get(field) != manifest_author.get(field):
                    problems.append(
                        ".cursor-plugin/marketplace.json owner "
                        "carries %s %r while the manifest author "
                        "carries %r, so the listing names a "
                        "different owner than the plugin"
                        % (
                            field,
                            owner.get(field),
                            manifest_author.get(field),
                        )
                    )
    return problems


def skill_copy_problems(root=None):
    """Problems with the real directory copy of the skill."""
    root = ROOT if root is None else root
    copy_dir = root / ".cursor-plugin" / "skills" / "recognitio"
    canonical = root / ".agents" / "skills" / "recognitio"
    if copy_dir.is_symlink():
        return [
            ".cursor-plugin/skills/recognitio is a symlink, which "
            "the host skips when it points outside the local "
            "plugin folder"
        ]
    if not copy_dir.is_dir():
        return [".cursor-plugin/skills/recognitio is not a directory"]
    if not canonical.is_dir():
        return ["the canonical skill directory is missing"]
    copy_files = tree_bytes(copy_dir)
    canonical_files = tree_bytes(canonical)
    problems = []
    for name in sorted(set(copy_files) | set(canonical_files)):
        if name not in canonical_files:
            problems.append(
                ".cursor-plugin/skills/recognitio carries an extra "
                "file %s the canonical skill does not hold" % name
            )
        elif name not in copy_files:
            problems.append(
                ".cursor-plugin/skills/recognitio is missing the "
                "file %s the canonical skill holds" % name
            )
        elif copy_files[name] != canonical_files[name]:
            problems.append(
                ".cursor-plugin/skills/recognitio/%s drifts from "
                "the canonical skill" % name
            )
    return problems


def bugbot_rules_problems(root=None):
    """Problems with the BUGBOT.md review rules."""
    root = ROOT if root is None else root
    raw = read_text(root / ".cursor" / "BUGBOT.md")
    if raw is None:
        return [".cursor/BUGBOT.md is missing"]
    problems = []
    section = rules_section(raw)
    if section is None:
        problems.append(
            ".cursor/BUGBOT.md carries no %r section" % RULES_HEADING
        )
        return problems
    blocks = rule_blocks(section)
    if not blocks:
        problems.append(
            ".cursor/BUGBOT.md carries no B numbered rules"
        )
    total = 0
    for index, block in enumerate(blocks, start=1):
        flat = re.sub(r"\s+", " ", block)
        total += len(flat)
        if len(flat) > RULE_CHAR_LIMIT:
            problems.append(
                "BUGBOT.md rule B%d runs %d characters, over the "
                "30,000 character per rule cap" % (index, len(flat))
            )
        if "Derives from" not in flat:
            problems.append(
                "BUGBOT.md rule B%d carries no derivation note, so "
                "it would be a rival instruction source" % index
            )
            continue
        note = flat.split("Derives from", 1)[1]
        if not deliberate_source(note):
            problems.append(
                "BUGBOT.md rule B%d names no canonical skill "
                "section, gate, or primary Cursor citation in its "
                "derivation note" % index
            )
    if total > RULES_COMBINED_LIMIT:
        problems.append(
            "the BUGBOT.md rules run %d characters combined, over "
            "the 100,000 character cap" % total
        )
    return problems


def _strip_yaml_comment(line):
    """The line with its hash comment removed.

    A hash starts a comment at the start of a line or after
    whitespace. A hash inside a plain scalar value is kept.
    """
    index = 0
    while True:
        found = line.find("#", index)
        if found < 0:
            return line
        if found == 0 or line[found - 1] in (" ", "\t"):
            return line[:found]
        index = found + 1


def parse_pinned_yaml(text):
    """Parse the pinned bugbot.yaml subset.

    The shipped file is mappings with two space indents, plain
    scalar keys and values, and hash comments. Anything outside
    that shape is a problem the caller reports, because the gate
    pins this file field by field.
    """
    root = {}
    stack = [(-1, root)]
    for number, raw_line in enumerate(text.splitlines(), start=1):
        line = _strip_yaml_comment(raw_line).rstrip()
        if not line.strip():
            continue
        if "\t" in line:
            raise ValueError("line %d uses a tab" % number)
        indent = len(line) - len(line.lstrip(" "))
        if indent % 2:
            raise ValueError("line %d has an odd indent" % number)
        if ":" not in line:
            raise ValueError("line %d carries no key" % number)
        key, _, value = line.strip().partition(":")
        key = key.strip()
        value = value.strip()
        if not re.fullmatch(r"[A-Za-z0-9_-]+", key):
            raise ValueError("line %d carries a bad key" % number)
        while stack and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1]
        if key in parent:
            raise ValueError("line %d repeats a key" % number)
        if value:
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", value):
                raise ValueError(
                    "line %d carries a bad value" % number
                )
            parent[key] = value
        else:
            child = {}
            parent[key] = child
            stack.append((indent, child))
    return root


def bugbot_yaml_problems(root=None):
    """Problems with the shipped bugbot.yaml.

    The primary page documents autofix.mode as the only repo
    YAML field, and an unknown field falls back silently down
    the precedence order, so the gate rejects unknown fields
    instead of trusting Cursor to complain. The mode itself is
    pinned to the disabled value the brief states, because
    decision 4 keeps Autofix off in this repo.
    """
    root = ROOT if root is None else root
    path = root / ".cursor" / "config" / "bugbot.yaml"
    raw = read_text(path)
    if raw is None:
        return [".cursor/config/bugbot.yaml is missing"]
    problems = []
    if len(raw.encode("utf-8")) > YAML_SIZE_LIMIT:
        problems.append(
            ".cursor/config/bugbot.yaml is over the 64 KB cap "
            "Bugbot ignores"
        )
    try:
        data = parse_pinned_yaml(raw)
    except ValueError as exc:
        return [
            ".cursor/config/bugbot.yaml does not parse, %s" % exc
        ]
    unknown = sorted(set(data) - BUGBOT_YAML_FIELDS)
    if unknown:
        problems.append(
            ".cursor/config/bugbot.yaml carries unknown fields %s, "
            "which would fall back silently down the precedence "
            "order" % ", ".join(unknown)
        )
        return problems
    autofix = data.get("autofix", {})
    if not isinstance(autofix, dict):
        problems.append(
            ".cursor/config/bugbot.yaml carries a non mapping "
            "autofix field"
        )
        return problems
    unknown = sorted(set(autofix) - AUTOFIX_FIELDS)
    if unknown:
        problems.append(
            ".cursor/config/bugbot.yaml carries unknown autofix "
            "fields %s, which would fall back silently"
            % ", ".join(unknown)
        )
        return problems
    mode = autofix.get("mode")
    if mode not in AUTOFIX_MODES:
        problems.append(
            ".cursor/config/bugbot.yaml sets autofix.mode to %r, "
            "which is not a mode the primary page names" % (mode,)
        )
    elif mode != PINNED_AUTOFIX_MODE:
        problems.append(
            ".cursor/config/bugbot.yaml sets autofix.mode to %r, "
            "but the brief pins the shipped mode to %r because "
            "decision 4 keeps Autofix off in this repo"
            % (mode, PINNED_AUTOFIX_MODE)
        )
    return problems


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
    """Problems with the Build 10 brief's stated contract."""
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "cursor-plugin-brief.md")
    if raw is None:
        return ["docs/cursor-plugin-brief.md is missing"]
    text = re.sub(r"\s+", " ", raw)
    problems = []
    for label, fragment in PINNED:
        if fragment not in text:
            problems.append(
                "docs/cursor-plugin-brief.md does not state %s" % label
            )
    for fragment in STALE:
        if fragment in text:
            problems.append(
                "docs/cursor-plugin-brief.md states the stale "
                "pre desktop run claim %r, which the desktop "
                "verification run of 2026-10-25 superseded"
                % fragment
            )
    for fragment in STALE_PRECEDENCE:
        if fragment in text:
            problems.append(
                "docs/cursor-plugin-brief.md states the stale "
                "open precedence claim %r, which the agent CLI "
                "precedence run of 2026-10-25 superseded"
                % fragment
            )
    section = rules_section(raw)
    if section is not None:
        problems.extend(
            operative_prose_problems(
                raw, section, "docs/cursor-plugin-brief.md")
        )
    return problems


def brief_negative_problems(root=None):
    """R36-RT-03. No brief sentence may state a repository cap
    figure, a bugbot.yaml effort pin, or a merge blocking
    neutral conclusion.

    The pins prove the correct sentences are stated, but an
    added sentence passes while the pins stay in place,
    because no check read the contradicting sentence. The
    repository cap conflict R35-C-01 stands unresolved on
    the primary pages, so a sentence may state a cap figure
    only with the conflict named beside it in the same
    sentence, and the safer form names no figure. Effort is
    a dashboard setting only, so a sentence that pins or
    sets effort in bugbot.yaml in the brief's own voice
    fails, while the shipped sentences that report and
    reject a secondary claim about such a field are skipped
    on their attribution words. Findings default to a
    neutral conclusion and requiring the status alone does
    not block merges, so a sentence that has a neutral
    conclusion blocking merges without a negation fails.
    """
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "cursor-plugin-brief.md")
    if raw is None:
        return ["docs/cursor-plugin-brief.md is missing"]
    body = re.sub(r"(?m)^#{1,6} .*$", "", raw)
    text = re.sub(r"\s+", " ", body)
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", text)
        if sentence.strip()
    ]
    # R38-RT-05 and R38-RT-07. A claim in this brief lives
    # inside one paragraph, so the cross sentence readings
    # group the sentences by the blank line breaks the
    # brief format itself marks, instead of stopping at a
    # fixed pair count the next split steps past.
    # R38G-RT-04. The gate review split both claims across
    # a paragraph break inside one block, so the readings
    # now group at claim scope, the headed block, every
    # paragraph under one heading read as one group of
    # sentences in order, and a heading starts a new group.
    # The neutral guard stays scoped to the stretch before
    # its own blocking verb and the cap reading keeps its
    # deictic binding, so a guard or a figure in a
    # neighbouring paragraph joins only through the claim
    # halves themselves.
    groups = []
    for chunk in re.split(r"(?m)^#{1,6} .*$", raw):
        flat = re.sub(r"\s+", " ", chunk)
        group = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", flat)
            if sentence.strip()
        ]
        if group:
            groups.append(group)
    problems = []
    # R37-RT-06. The cap and effort branches now read the
    # whole sentence with no measured reach, because the
    # round 37 review pushed the bound words past the
    # reaches behind filler. A cap figure binds to the word
    # repositories anywhere in its sentence unless the
    # figure is bound elsewhere first, by the count noun
    # right after it or by a unit word in its own unit
    # position, as a character count is. The neutral branch
    # reads pairs of neighbouring sentences beside single
    # sentences, because the review carried the conclusion
    # across a sentence boundary on a pronoun and neither
    # sentence alone held the pairing.
    unit_words = (
        r"(?:characters?|chars|bytes?|kb|kib|mb|lines?"
        r"|files?|rules?|seconds?|minutes?|tokens?"
        r"|percent|words?)"
    )

    def cap_figure(low):
        figures = list(
            re.finditer(
                r"\b(\d[\d,]*\d|\d+|three hundred"
                r"|five hundred)\b",
                low,
            )
        )
        targets = list(re.finditer(r"\brepositories\b", low))
        for figure in figures:
            # R37F-RT-09. A figure followed directly by a
            # plural count noun binds to that noun, not to
            # a repositories word later in the sentence. A
            # workspace listing 500 issues across its
            # repositories counts issues, so the figure is
            # not a repository cap figure at all.
            following = re.match(
                r"[\s,]*([a-z]+)", low[figure.end():]
            )
            if (
                following
                and following.group(1).endswith("s")
                and following.group(1) != "repositories"
            ):
                continue
            for target in targets:
                if figure.end() <= target.start():
                    between = low[figure.end():target.start()]
                    # R37F-RT-07. Ahead of the target, a
                    # unit word rebinds the figure only in
                    # the figure's own unit position, right
                    # after the figure. A unit word inside a
                    # parenthetical later in the stretch,
                    # counting files separately, leaves the
                    # figure bound to repositories.
                    if re.match(
                        r"[\s,]*%s\b" % unit_words, between
                    ):
                        continue
                elif target.end() <= figure.start():
                    # Confirmation repair. Behind the
                    # target the same position rule holds.
                    # A unit word inside a parenthetical
                    # between the target and the figure,
                    # counting files separately, is not in
                    # the figure's unit position, which
                    # behind the target reads right after
                    # the figure, so it does not rebind.
                    if re.match(
                        r"[\s,]*%s\b" % unit_words,
                        low[figure.end():],
                    ):
                        continue
                else:
                    continue
                return figure.group(1)
        return None

    for sentence in sentences:
        low = sentence.lower()
        # R36 gate repair. The cap branch binds a figure to
        # the word repositories at any short distance, in
        # digits or in the spelled hundred forms, with no
        # bounding verb required and no two figure
        # exemption, because a sentence naming both figures
        # still cites cap figures and the conflict note is
        # the only thing that makes a citation honest. The
        # sentence that names both figures with the conflict
        # named beside them passes on the conflict word.
        cap = cap_figure(low)
        if cap and "conflict" not in low:
            problems.append(
                "the cursor brief states a repository cap "
                "figure of %s with no R35-C-01 conflict "
                "note beside it" % cap
            )
            return problems
        # R37F-RT-09. The effort binding reads the
        # sentence's coordinating units, split at a comma
        # and or comma but or a semicolon. Effort in one
        # unit and a pin verb in the next state no pin,
        # while the parenthetical commas of the round 37
        # plant open no unit, so its effort and its pin
        # verb stay in one unit and still fail.
        effort_units = re.split(r",\s+(?:and|but)\s+|;\s*", low)
        # R37C-RT-05. A sentence with no comma and no
        # semicolon joins its units with the plain joint
        # alone, so the split reads the plain and and but
        # joints there too. A sentence carrying commas
        # keeps the comma rule, because its commas may
        # set off a parenthetical whose plain joints open
        # no unit.
        if "," not in low and ";" not in low:
            effort_units = [
                piece
                for unit_text in effort_units
                for piece in re.split(
                    r"\s+(?:and|but)\s+", unit_text
                )
            ]
        for unit_text in effort_units:
            if (
                "bugbot.yaml" in unit_text
                and (
                    re.search(
                        r"\beffort\b[^.]*"
                        r"\b(pin\w*|set|configur\w*|control\w*)\b",
                        unit_text,
                    )
                    or re.search(
                        r"\b(pin\w*|set|configur\w*|control\w*)\b"
                        r"[^.]*\beffort\b",
                        unit_text,
                    )
                )
                and not re.search(
                    r"\b(claims|secondary|no such|inventing"
                    r"|not|never|cannot)\b",
                    unit_text,
                )
            ):
                problems.append(
                    "the cursor brief pins Bugbot effort in "
                    "bugbot.yaml, which the dashboard only effort "
                    "pin forbids"
                )
                return problems
    # R38-RT-07. A cap claim can state its figure in one
    # sentence and name repositories as what the figure
    # counts in the next, where the second sentence opens
    # with a deictic word carrying the figure forward,
    # those are repositories counted. That pair reads as
    # one claim, judged by the same cap binding and the
    # same conflict note rule as a single sentence. The
    # pair reading runs over the claim scope groups, so
    # the two halves may stand in neighbouring paragraphs
    # of one block.
    for group in groups:
        for index, first in enumerate(group):
            for second in group[index + 1:]:
                low_second = second.lower()
                if not re.match(
                    r"(those|these|that|they|it)\b", low_second
                ):
                    continue
                if "repositories" not in low_second:
                    continue
                joined = first + " " + second
                cap = cap_figure(joined.lower())
                if cap and "conflict" not in joined.lower():
                    problems.append(
                        "the cursor brief states a repository cap "
                        "figure of %s with no R35-C-01 conflict "
                        "note beside it" % cap
                    )
                    return problems
    # R38-RT-05. The neutral reading runs over every
    # neighbouring window inside a paragraph, not only
    # pairs, because the round 38 review split the claim
    # across three sentences with a filler between the
    # halves and no pair held both halves. The windows
    # now run inside the claim scope groups, so a split
    # across a paragraph break inside one block is read
    # the same way.
    units = []
    for group in groups:
        for start in range(len(group)):
            for end in range(start + 1, len(group) + 1):
                units.append(" ".join(group[start:end]))
    for unit in units:
        low = unit.lower()
        block = re.search(
            r"\b(blocks?|blocked|stops?|stopped|halts?"
            r"|prevent\w*)\b",
            low,
        )
        # R37F-RT-08. The negation guard reads the stretch
        # right before the blocking verb, and the stretch
        # stops at a coordinating and. A negation that
        # modifies an earlier verb joined by and, never
        # sits idle and blocks, negates that verb and not
        # the blocking one.
        # R37C-RT-04. The stretch also stops at a comma,
        # because a comma splice joins the verbs the same
        # way and a negation before the comma modifies the
        # earlier verb alone.
        # R38-RT-06. The stretch also stops at a semicolon,
        # because a semicolon joins the verbs the same way
        # and a negation before it modifies the earlier
        # verb alone.
        if block and "neutral" in low and not re.search(
            r"\b(does not|do not|not|never|no)\b"
            r"(?:(?!\band\b)[^.,;]){0,30}$",
            low[:block.start()],
        ):
            problems.append(
                "the cursor brief has a neutral Bugbot "
                "conclusion blocking merges, which the "
                "neutral default pin forbids"
            )
            return problems
    return problems


def readme_problems(root=None):
    """Problems with the README Cursor passage."""
    root = ROOT if root is None else root
    raw = read_text(root / "README.md")
    if raw is None:
        return ["README.md is missing"]
    text = re.sub(r"\s+", " ", raw)
    problems = []
    for label, fragment in README_PINNED:
        if fragment not in text:
            problems.append(
                "README.md does not state %s" % label
            )
    for fragment in README_STALE:
        if fragment in text:
            problems.append(
                "README.md states the stale Cursor "
                "Marketplace distribution claim %r"
                % fragment
            )
    joined = raw.replace("\\\n", "")
    joined = re.sub(r"\s+", " ", joined)
    pinning = (
        "cp -r recognitio-pinned "
        "~/.cursor/plugins/local/recognitio"
    )
    if pinning not in joined:
        problems.append(
            "README.md pinning block does not copy the pinned "
            "repository folder with the command %r" % pinning
        )
    if "recognitio-pinned/.cursor-plugin" in joined:
        problems.append(
            "README.md pinning block copies "
            "recognitio-pinned/.cursor-plugin instead of the "
            "pinned repository folder"
        )
    return problems


def plugin_readme_problems(root=None):
    """Problems with the plugin README Installing passage."""
    root = ROOT if root is None else root
    raw = read_text(root / ".cursor-plugin" / "README.md")
    if raw is None:
        return [".cursor-plugin/README.md is missing"]
    text = re.sub(r"\s+", " ", raw)
    problems = []
    for label, fragment in PLUGIN_README_PINNED:
        if fragment not in text:
            problems.append(
                ".cursor-plugin/README.md does not state %s"
                % label
            )
    for fragment in PLUGIN_README_STALE:
        if fragment in text:
            problems.append(
                ".cursor-plugin/README.md states the stale "
                "Cursor Marketplace distribution claim %r"
                % fragment
            )
    return problems


def decision_problems(root=None):
    """Problems with the Build 10 decision record."""
    root = ROOT if root is None else root
    raw = read_text(root / "docs" / "decisions.md")
    if raw is None:
        return ["docs/decisions.md is missing"]
    start = raw.find(DECISION_HEADING)
    if start < 0:
        return ["docs/decisions.md carries no Build 10 decision record"]
    rest = raw[start + len(DECISION_HEADING):]
    match = re.search(r"(?m)^## ", rest)
    record = rest[:match.start()] if match else rest
    if DECISION_STATEMENT not in record:
        return [
            "the Build 10 decision record carries no decision 4 "
            "statement, which every landed build must record"
        ]
    return []


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


def t0_set_problems(flat_block, surface):
    """Problems with one rule block stating the canonical T0 set."""
    problems = []
    for label, fragment in T0_MEMBERS:
        if fragment not in flat_block:
            problems.append(
                "%s does not state the canonical T0 member %s"
                % (surface, label)
            )
    start = flat_block.find("The name set is")
    if start < 0:
        problems.append(
            "%s does not state the canonical T0 name set" % surface
        )
    else:
        end_marker = "of the plugin is flagged too."
        end = flat_block.find(end_marker, start)
        stated = (
            flat_block[start:end + len(end_marker)]
            if end >= 0 else ""
        )
        if stated != T0_SET_TEXT:
            problems.append(
                "%s states a name set that differs from the "
                "canonical T0 set, with a member missing or added"
                % surface
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


def round5_cursor_problems(root=None):
    """Round 5 problems for the brief, Bugbot tail and YAML header."""
    root = ROOT if root is None else root
    problems = []
    raw = read_text(root / "docs" / "cursor-plugin-brief.md")
    if raw is not None:
        text = re.sub(r"\s+", " ", raw)
        for fragment in README_STALE:
            if fragment in text:
                problems.append(
                    "docs/cursor-plugin-brief.md states the stale "
                    "Cursor Marketplace distribution claim %r"
                    % fragment
                )
        # Repair pass. The verified check is a scoped
        # negative family, not a literal membership test. A
        # sentence states the claim when it joins the Bugbot
        # subject and the pull request object to a verified
        # or confirmed or proven verb form, and a negation
        # in the claim clause states no claim. The honest
        # unverified wording carries no such verb form.
        for sentence in re.split(r"(?<=[.!?])\s+", text):
            low = sentence.lower()
            verb = re.search(
                r"\b(verified|confirmed|proven)\b", low)
            if (
                "bugbot" in low
                and "pull request" in low
                and verb
                and not _claim_clause_negated(low, verb.start())
            ):
                problems.append(
                    "docs/cursor-plugin-brief.md claims Bugbot "
                    "behaviour on a real pull request is verified, "
                    "beside its pinned unverified sentence"
                )
                break
        section = rules_section(raw)
        if section is not None:
            for block in rule_blocks(section):
                flat = re.sub(r"\s+", " ", block)
                if "The name set is" in flat:
                    problems.extend(t0_set_problems(
                        flat, "docs/cursor-plugin-brief.md rule B3"))
    bugbot = read_text(root / ".cursor" / "BUGBOT.md")
    if bugbot is not None:
        # Heading lines are structure, not claims, so the
        # merge claim scan reads the file with its headings
        # removed, the reading the ZCode gate uses for its
        # own negative scan. A heading that carries a
        # negation word would otherwise join the sentence
        # after it and shelter the claim that follows.
        flat_all = re.sub(
            r"\s+", " ",
            re.sub(r"(?m)^#{1,6} .*$", "", bugbot),
        )
        # Repair pass. The merge claim family covers the
        # merge verb forms with a pull request object, with
        # or without autonomy wording, beside the auto forms
        # the first reading named. The reading runs at clause
        # scope, and a clause that denies the claim or warns
        # against it states no claim.
        # Repair pass two. The object also stands in its
        # abbreviated form, the word PRs, in the same active
        # and passive forms, so a claim stated in the
        # abbreviation the shipped briefs themselves use for
        # the same object states the claim as well.
        # Repair pass three. The family also covers the
        # autonomy form, a merge verb joined in its clause
        # to an autonomy marker, on its own or by itself or
        # automatically or without asking or without human
        # review, whatever the object is, a pronoun or a
        # definite description included, with negation read
        # at clause scope as above. A merge carried by
        # reference with no autonomy claim and no spelled
        # object stands outside the family.
        merge_claim = False
        for sentence in re.split(r"(?<=[.!?])\s+", flat_all):
            low = sentence.lower()
            clauses = re.split(r",\s+and\s+|,\s+|;\s*", low)
            for clause in clauses:
                if re.search(
                    r"auto(?:matically)?\s+(?:approve|merge)"
                    r"|approv\w+ and merg\w+"
                    r"|auto approve|auto merge",
                    clause,
                ):
                    merge_claim = True
                    break
                verb = re.search(r"\bmerg\w*\b", clause)
                if not verb:
                    continue
                if "warn" in clause:
                    continue
                if re.search(
                    r"\b(not|no|never)\b|n't",
                    clause[:verb.start()],
                ):
                    continue
                if re.search(
                    r"\bmerg\w*\b[^.]{0,60}"
                    r"\b(?:pull requests?|prs)\b", clause
                ) or re.search(
                    r"\b(?:pull requests?|prs)\b[^.]{0,60}"
                    r"\bmerg\w*\b", clause
                ):
                    merge_claim = True
                    break
                if re.search(
                    r"\bon its own\b|\bby itself\b"
                    r"|\bautomatically\b|\bwithout asking\b"
                    r"|\bwithout human review\b",
                    clause,
                ):
                    merge_claim = True
                    break
            if merge_claim:
                break
        if merge_claim:
            problems.append(
                ".cursor/BUGBOT.md claims an auto approve or auto "
                "merge behaviour, which its own final rule forbids"
            )
        section = rules_section(bugbot)
        if section is not None:
            blocks = rule_blocks(section)
            for block in blocks:
                flat = re.sub(r"\s+", " ", block)
                if "The name set is" in flat:
                    problems.extend(t0_set_problems(
                        flat, ".cursor/BUGBOT.md rule B3"))
            # Repair pass. The tail reading runs over
            # everything after the final rule derivation
            # note in the file, headings included, so
            # operative content under a fresh heading after
            # the final rule stands inside the reading. The
            # last block reading stands beside it for a tail
            # inside the final block itself.
            # Repair pass two. The tail anchor is the
            # derivation note of the final rule block as
            # the rules are parsed, not the last derivation
            # shaped marker standing in the file. A tail
            # that closes with a fresh derivation note
            # cannot move the anchor past its own operative
            # content that way. Everything after the final
            # rule note paragraph is judged as tail, and
            # any content there except whitespace is the
            # tail problem, headings and derivation shaped
            # notes included.
            # Repair pass three. The final rule derivation
            # note paragraph may carry the derivation note
            # and nothing else, so any further sentence
            # standing inside that paragraph is the tail
            # problem as well, and the reading judges the
            # paragraph itself beside everything after it.
            tail_found = False
            headings = list(
                re.finditer(r"(?m)^### B\d+\.", bugbot))
            if headings:
                note_start = bugbot.find(
                    "Derives from", headings[-1].start())
                if note_start >= 0:
                    note_break = re.search(
                        r"\n\s*\n", bugbot[note_start:])
                    note_end = (
                        note_start + note_break.end()
                        if note_break else len(bugbot)
                    )
                    if bugbot[note_end:].strip():
                        tail_found = True
                    note_paragraph = re.sub(
                        r"\s+", " ",
                        bugbot[note_start:note_end])
                    note_sentences = [
                        part for part in re.split(
                            r"(?<=[.!?])\s+", note_paragraph)
                        if part.strip()
                    ]
                    if len(note_sentences) > 1:
                        tail_found = True
            if tail_found:
                problems.append(
                    ".cursor/BUGBOT.md carries operative "
                    "content after the final rule block, "
                    "past its derivation note"
                )
    # Round 5 second seat. Rule B4 restates the caps in its
    # own sentences in both surfaces, bound to their
    # figures, and no sentence in either surface may attach
    # the combined figure to a single rule or the per rule
    # figure to the combined rules. Repair pass three
    # extends the exchange reading to the Bugbot surface
    # beside the brief surface it already covered, in the
    # additive form the Codex and Devin gates use. The
    # reading runs at clause scope on both surfaces, so a
    # sentence that binds both figures correctly, each in
    # its own clause, stands clean, and a scope word and
    # its figure split across clauses stand outside the
    # reading.
    for surface, surface_raw in (
        ("docs/cursor-plugin-brief.md", raw),
        (".cursor/BUGBOT.md", bugbot),
    ):
        if surface_raw is None:
            continue
        b4_start = surface_raw.find("### B4.")
        b4_end = surface_raw.find("### B5.", b4_start)
        b4_block = re.sub(
            r"\s+", " ",
            surface_raw[b4_start:b4_end] if b4_start >= 0 else "",
        )
        if "Each rule stays under 30,000 characters" not in b4_block:
            problems.append(
                "%s rule B4 does not bind the per rule cap "
                "to 30,000 characters" % surface
            )
        if "combined rules stay under 100,000 characters" not in b4_block:
            problems.append(
                "%s rule B4 does not bind the combined cap "
                "to 100,000 characters" % surface
            )
    for surface, surface_raw in (
        ("docs/cursor-plugin-brief.md", raw),
        (".cursor/BUGBOT.md", bugbot),
    ):
        if surface_raw is None:
            continue
        low = re.sub(r"\s+", " ", surface_raw.lower())
        exchanged = False
        for sentence in re.split(r"(?<=[.!?])\s+", low):
            clauses = re.split(
                r",\s+and\s+|,\s+|;\s*", sentence)
            for clause in clauses:
                if re.search(
                    r"\bcombined\b[^.]{0,60}\b30,000\b", clause
                ) or re.search(
                    r"\b(each rule|per rule|single rule)\b[^.]{0,60}"
                    r"\b100,000\b",
                    clause,
                ):
                    exchanged = True
                    break
            if exchanged:
                break
        if exchanged:
            problems.append(
                "%s attaches a cap "
                "figure to the wrong scope, the combined and "
                "per rule caps exchanged" % surface
            )
    yaml_raw = read_text(root / ".cursor" / "config" / "bugbot.yaml")
    if yaml_raw is not None:
        flat_yaml = re.sub(r"\s+", " ", yaml_raw.replace("#", " "))
        pinned = (
            "It can lower the Autofix mode from the dashboard "
            "setting, but it cannot raise it."
        )
        if pinned not in flat_yaml:
            problems.append(
                ".cursor/config/bugbot.yaml does not state its "
                "operative header sentence that it can lower the "
                "Autofix mode and cannot raise it"
            )
        if "can raise the Autofix mode" in flat_yaml:
            problems.append(
                ".cursor/config/bugbot.yaml claims it can raise "
                "the Autofix mode, which its operative header "
                "sentence forbids"
            )
    return problems


def cursor_problems(root=None):
    """Every Build 10 Cursor plugin problem."""
    UTF8_UNREADABLE.clear()
    problems = []
    problems.extend(manifest_problems(root))
    problems.extend(marketplace_problems(root))
    problems.extend(skill_copy_problems(root))
    problems.extend(bugbot_rules_problems(root))
    problems.extend(bugbot_yaml_problems(root))
    problems.extend(brief_problems(root))
    problems.extend(brief_negative_problems(root))
    problems.extend(readme_problems(root))
    problems.extend(plugin_readme_problems(root))
    problems.extend(decision_problems(root))
    problems.extend(round5_cursor_problems(root))
    return repair_utf8_problems(problems)


def main(root=None):
    problems = cursor_problems(root)
    if problems:
        for problem in problems:
            print("check_cursor: %s" % problem, file=sys.stderr)
        return 1
    print("check_cursor: the Build 10 Cursor plugin contract holds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
