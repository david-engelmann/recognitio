#!/usr/bin/env python3
"""Pin the Build 5 reviewer persona surface.

The plugin manifest declares the reviewer agent under the
`agents` key and names it as the session agent under the
`settings` key. The gate pins both keys, pins the agent
frontmatter field by field, and forbids a tool allowlist or
a permission mode on the persona as defense in depth,
because the persona changes the persona and not the tool
access. The persona prose sentence discipline lives in the
gate test suite beside the output style sentence check. See
docs/reviewer-persona.md for the brief and the primary
sources behind each rule.

Exits nonzero with one line per problem when anything fails.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_JSON = ROOT / ".claude-plugin" / "plugin.json"
AGENT_DECLARATION = "./agents/reviewer.md"
AGENT_NAME = "reviewer"

# The frontmatter control panel of the agent file, from the
# primary plugin components page. The shipped file sets the
# name and the description only, and every other field the
# page honors is pinned by shape below.
ALLOWED_FRONTMATTER_KEYS = {
    "name",
    "description",
    "model",
    "effort",
    "maxTurns",
    "disallowedTools",
    "isolation",
}
# Declaring one of these is a defect. A `tools` field would
# be a tool access widening, and a permission mode would be
# a bypass the persona must never carry, so both fail even
# though the host ignores the last four fields on plugin
# agents. The ban is a recognitio bound, not a host limit.
FORBIDDEN_FRONTMATTER_KEYS = {
    "tools",
    "permissionMode",
    "hooks",
    "mcpServers",
    "initialPrompt",
}
EFFORT_VALUES = ("low", "medium", "high")
MAX_TURNS_RE = re.compile(r"^[1-9][0-9]*$")
# Only `agent` and `subagentStatusLine` take effect in plugin
# settings, and every other key is dropped at load, so the
# shipped object carries the agent key and nothing else.
ALLOWED_SETTINGS_KEYS = {"agent", "subagentStatusLine"}
KEY_RE = re.compile(r"^([A-Za-z0-9_][A-Za-z0-9_.-]*)\s*:")


class DuplicateKeyError(ValueError):
    """A JSON object names one key twice."""


def strict_json_loads(text):
    """Parse JSON refusing a repeated key, like the version gate."""
    def reject(pairs):
        seen = {}
        for key, value in pairs:
            if key in seen:
                raise DuplicateKeyError("repeated key %r" % key)
            seen[key] = value
        return seen
    return json.loads(text, object_pairs_hook=reject)


def parse_frontmatter(text):
    """Split an agent file into its fields and its problems.

    Returns a pair of the field mapping and the problem list.
    A missing or unclosed block, a duplicate key, and a line
    that is not a key value pair are all problems, because the
    host loads an unparseable frontmatter with every field
    ignored and the gate must not bless a file the host
    silently neuters.
    """
    problems = []
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, ["the agent file has no frontmatter block"]
    fields = {}
    closed = False
    for lineno, line in enumerate(lines[1:], start=2):
        if line.strip() == "---":
            closed = True
            break
        if line[:1] in (" ", "\t"):
            problems.append(
                "frontmatter line %d is a continuation line, and "
                "the agent frontmatter carries no folded values"
                % lineno
            )
            continue
        match = KEY_RE.match(line)
        if not match:
            problems.append(
                "frontmatter line %d is not a key value pair" % lineno
            )
            continue
        key = match.group(1)
        if key in fields:
            problems.append("duplicate frontmatter key %r" % key)
            continue
        fields[key] = line.split(":", 1)[1].strip()
    if not closed:
        problems.append("the frontmatter block never closes")
    return fields, problems


def frontmatter_problems(text):
    """The agent frontmatter pins, field by field."""
    fields, problems = parse_frontmatter(text)
    for key in sorted(fields):
        if key in FORBIDDEN_FRONTMATTER_KEYS:
            problems.append(
                "frontmatter declares %r, which the persona must "
                "never carry" % key
            )
        elif key not in ALLOWED_FRONTMATTER_KEYS:
            problems.append(
                "frontmatter declares %r, which is outside the "
                "pinned field set" % key
            )
    name = fields.get("name", "")
    if name != AGENT_NAME:
        problems.append(
            "frontmatter name is %r, not the pinned %r"
            % (name, AGENT_NAME)
        )
    if not fields.get("description", "").strip():
        problems.append("frontmatter carries no description")
    model = fields.get("model")
    if model is not None and not model.strip():
        problems.append("frontmatter model is empty")
    effort = fields.get("effort")
    if effort is not None and effort not in EFFORT_VALUES:
        problems.append(
            "frontmatter effort is %r, outside %s"
            % (effort, "/".join(EFFORT_VALUES))
        )
    turns = fields.get("maxTurns")
    if turns is not None and not MAX_TURNS_RE.match(turns):
        problems.append(
            "frontmatter maxTurns is %r, not a positive integer" % turns
        )
    denied = fields.get("disallowedTools")
    if denied is not None:
        problems.extend(disallowed_tools_problems(denied))
    isolation = fields.get("isolation")
    if isolation is not None and isolation.strip('"') != "worktree":
        problems.append(
            "frontmatter isolation is %r, and worktree is the only "
            "valid value" % isolation
        )
    return problems


def disallowed_tools_problems(value):
    """The disallowedTools value reads as a list of tool names."""
    stripped = value.strip()
    if not (stripped.startswith("[") and stripped.endswith("]")):
        return [
            "frontmatter disallowedTools is %r, not a bracketed list"
            % value
        ]
    problems = []
    for entry in stripped[1:-1].split(","):
        name = entry.strip().strip("\"'")
        if not name:
            problems.append(
                "frontmatter disallowedTools names an empty tool"
            )
    return problems


def resolve_component(root, declared):
    """Resolve a declared component path the vendor way.

    The host resolves every component path against the plugin
    root, so the gate does the same and refuses a declaration
    that escapes the root or names no file.
    """
    if not declared.startswith("./"):
        return None
    candidate = (root / declared[2:]).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    if not candidate.is_file():
        return None
    return candidate


def manifest_problems(root):
    """The `agents` and `settings` manifest key pins."""
    problems = []
    path = root / ".claude-plugin" / "plugin.json"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return ["cannot read the plugin manifest: %s" % exc]
    try:
        manifest = strict_json_loads(text)
    except (json.JSONDecodeError, DuplicateKeyError) as exc:
        return ["the plugin manifest does not parse: %s" % exc]
    if not isinstance(manifest, dict):
        return ["the plugin manifest is not an object"]
    agents = manifest.get("agents")
    if agents != [AGENT_DECLARATION]:
        problems.append(
            "the manifest agents key is %r, not the pinned %r"
            % (agents, [AGENT_DECLARATION])
        )
    settings = manifest.get("settings")
    if not isinstance(settings, dict):
        problems.append(
            "the manifest settings key is %r, not an object" % settings
        )
    else:
        for key in sorted(settings):
            if key not in ALLOWED_SETTINGS_KEYS:
                problems.append(
                    "the manifest settings key carries %r, which "
                    "the host drops at load" % key
                )
        if settings.get("agent") != AGENT_NAME:
            problems.append(
                "the manifest settings agent is %r, not the pinned "
                "%r" % (settings.get("agent"), AGENT_NAME)
            )
    resolved = resolve_component(root, AGENT_DECLARATION)
    if resolved is None:
        problems.append(
            "the declared agent path %r does not resolve to a file "
            "under the plugin root" % AGENT_DECLARATION
        )
    elif resolved != (root / "agents" / "reviewer.md").resolve():
        problems.append(
            "the declared agent path resolves to %s, not the "
            "shipped agent file" % resolved
        )
    return problems


def persona_problems(root):
    """Every persona pin against one tree root."""
    problems = [
        "manifest: %s" % problem
        for problem in manifest_problems(root)
    ]
    agent = root / "agents" / "reviewer.md"
    try:
        text = agent.read_text(encoding="utf-8")
    except OSError as exc:
        problems.append("agent file: cannot read it: %s" % exc)
        return problems
    problems.extend(
        "agent file: %s" % problem
        for problem in frontmatter_problems(text)
    )
    return problems


def main(root=None):
    root = ROOT if root is None else root
    problems = persona_problems(root)
    if problems:
        for problem in problems:
            print("check_persona: %s" % problem, file=sys.stderr)
        return 1
    print("check_persona: the persona surface is pinned")
    return 0


if __name__ == "__main__":
    sys.exit(main())
