#!/usr/bin/env python3
"""Pin the Build 10 Cursor plugin contract.

The brief at docs/cursor-plugin-brief.md exploits the Cursor
Plugin manifest, the six component packaging rules, the Bugbot
rules in .cursor/BUGBOT.md, and the .cursor/config/bugbot.yaml
repo config, distributed through the manually reviewed Cursor
Marketplace. Decision 4 binds this build like every other build.
The plugin and the Bugbot rules advise and never enforce, so this
script pins the contract without a Cursor host. It requires the
manifest to name the plugin in lowercase kebab-case with
relative paths only, the skill copy to be a real directory that
is byte identical to the canonical skill because the host skips
symlinks that point outside the local plugin folder, every
Bugbot rule to carry a checkable derivation note, the shipped
bugbot.yaml to hold only documented fields because unknown fields
fall back silently, and the brief to keep the stated pins, the
verbatim primary quotes, and the honest limitation that the real
client run is still owed. A later edit that drops any of them
fails the gate instead of drifting in silence.
"""

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / ".cursor-plugin"
PLUGIN_JSON = PLUGIN_DIR / "plugin.json"
MARKETPLACE_JSON = PLUGIN_DIR / "marketplace.json"
SKILL_COPY = PLUGIN_DIR / "skills" / "recognitio"
CANONICAL_SKILL = ROOT / ".agents" / "skills" / "recognitio"
BUGBOT_MD = ROOT / ".cursor" / "BUGBOT.md"
BUGBOT_YAML = ROOT / ".cursor" / "config" / "bugbot.yaml"
BRIEF = ROOT / "docs" / "cursor-plugin-brief.md"
DECISIONS = ROOT / "docs" / "decisions.md"
CLAUDE_PLUGIN_JSON = ROOT / ".claude-plugin" / "plugin.json"

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

# Manifest top level keys the shipped manifest may carry. The
# list is closed on purpose, so an invented manifest key fails
# the gate instead of riding along unexamined.
MANIFEST_KEYS = (
    "name", "version", "description", "license", "author",
    "skills", "rules", "agents", "commands", "variables",
)

# The only repo bugbot.yaml fields the primary docs name. An
# unknown field falls back silently down the precedence order,
# so the gate rejects it outright.
BUGBOT_YAML_FIELDS = {"autofix"}
AUTOFIX_FIELDS = {"mode"}
# The autofix.mode values the primary page names in its example.
AUTOFIX_MODES = {"newBranch", "disabled"}

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
    ("the owed client run",
     "the real client run is owed"),
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


def read_text(path):
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
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


def tree_bytes(directory):
    """Map every file under a directory to its bytes.

    Compiled bytecode caches are build state, not skill content,
    so they are excluded the way the portable package check
    excludes them.
    """
    found = {}
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        rel = str(path.relative_to(directory))
        if "__pycache__" in rel or rel.endswith(".pyc"):
            continue
        found[rel] = path.read_bytes()
    return found


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
    plugin_dir = root / ".cursor-plugin"
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
            target = (plugin_dir / entry).resolve()
            try:
                target.relative_to(plugin_dir.resolve())
            except ValueError:
                problems.append(
                    ".cursor-plugin/plugin.json declares %r under "
                    "%s, which escapes the plugin directory"
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
    elif "CURSOR_PLUGIN_ROOT" in variables:
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
    manifest_raw = read_text(root / ".cursor-plugin" / "plugin.json")
    name = version = None
    if manifest_raw is not None:
        try:
            manifest = strict_json_loads(manifest_raw)
            name = manifest.get("name")
            version = manifest.get("version")
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
    metadata = data.get("metadata", {})
    if isinstance(metadata, dict) and metadata.get("version") \
            != version:
        problems.append(
            ".cursor-plugin/marketplace.json metadata is at version "
            "%r while the manifest is at %r"
            % (metadata.get("version"), version)
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
    instead of trusting Cursor to complain.
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
    groups = []
    for block in re.split(r"\n\s*\n", body):
        flat = re.sub(r"\s+", " ", block)
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
    # same conflict note rule as a single sentence.
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
    # halves and no pair held both halves.
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


def cursor_problems(root=None):
    """Every Build 10 Cursor plugin problem."""
    problems = []
    problems.extend(manifest_problems(root))
    problems.extend(marketplace_problems(root))
    problems.extend(skill_copy_problems(root))
    problems.extend(bugbot_rules_problems(root))
    problems.extend(bugbot_yaml_problems(root))
    problems.extend(brief_problems(root))
    problems.extend(brief_negative_problems(root))
    problems.extend(decision_problems(root))
    return problems


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
