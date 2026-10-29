#!/usr/bin/env python3
"""Pin the Build 5 reviewer persona surface.

The plugin manifest declares the reviewer agent under the
`agents` key and names it as the session agent under the
`settings` key. The gate pins both keys, pins the agent
frontmatter field by field, and forbids a tool allowlist or
a permission mode on the persona as defense in depth,
because the persona changes the persona and not the tool
access. The same settings object may ship as a settings
file at the plugin root, and the brief states that when
both shapes exist the file wins and the manifest key is
ignored, so the gate pins the file when it stands and
reads the manifest key only when no file stands. The
persona prose sentence discipline lives in the gate test
suite beside the output style sentence check. See
docs/reviewer-persona.md for the brief and the primary
sources behind each rule.

Exits nonzero with one line per problem when anything fails.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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
    if isolation is not None and isolation.strip("\"'") != "worktree":
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
    inner = stripped[1:-1].strip()
    if not inner:
        return ["frontmatter disallowedTools is an empty list"]
    for entry in inner.split(","):
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


def settings_object_problems(settings, carries_subject, agent_subject):
    """The settings object pins, shared by both shipped shapes.

    Only `agent` and `subagentStatusLine` take effect in
    plugin settings and every other key is dropped at load,
    so the shipped object carries the agent key and nothing
    outside the allowed set, and its agent value is the
    pinned persona name. The two subjects name the shape
    under judgement in the gate wording of that shape.
    """
    problems = []
    for key in sorted(settings):
        if key not in ALLOWED_SETTINGS_KEYS:
            problems.append(
                "%s carries %r, which the host drops at load"
                % (carries_subject, key)
            )
    if settings.get("agent") != AGENT_NAME:
        problems.append(
            "%s is %r, not the pinned %r"
            % (agent_subject, settings.get("agent"), AGENT_NAME)
        )
    return problems


def settings_file_problems(root):
    """The settings file at the plugin root, when it stands.

    The brief states that the settings object may ship as
    `settings.json` at the plugin root instead of inline
    under the manifest `settings` key, and that when both
    shapes exist the file wins. An absent file is no
    problem, because this plugin ships the manifest key
    only. A file that stands is read behind the guarded
    read pattern, so a path that is not a regular file
    draws a named problem and is never read, and a file
    that stands is held to the same object pins as the
    manifest key it overrides.
    """
    path = root / "settings.json"
    if not path.exists():
        return []
    if not path.is_file():
        return [
            "cannot read the settings file: "
            "it is not a regular file"
        ]
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return ["cannot read the settings file: %s" % exc]
    except UnicodeDecodeError as exc:
        return ["the settings file does not parse: %s" % exc]
    try:
        settings = strict_json_loads(text)
    except (json.JSONDecodeError, DuplicateKeyError) as exc:
        return ["the settings file does not parse: %s" % exc]
    if not isinstance(settings, dict):
        return ["the settings file is not an object"]
    return settings_object_problems(
        settings, "the settings file", "the settings file agent"
    )


def manifest_problems(root):
    """The `agents` and `settings` manifest key pins."""
    problems = []
    path = root / ".claude-plugin" / "plugin.json"
    if path.exists() and not path.is_file():
        return [
            "cannot read the plugin manifest: "
            "it is not a regular file"
        ]
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
    # When a settings file stands at the plugin root the
    # brief states that the file wins and the manifest key
    # is ignored, so the manifest settings key is pinned
    # only when no file stands. The file itself is pinned
    # by settings_file_problems on the same reading.
    if not (root / "settings.json").exists():
        settings = manifest.get("settings")
        if not isinstance(settings, dict):
            problems.append(
                "the manifest settings key is %r, not an object"
                % settings
            )
        else:
            problems.extend(
                settings_object_problems(
                    settings,
                    "the manifest settings key",
                    "the manifest settings agent",
                )
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


def agent_dir_problems(root):
    """The agents directory holds exactly the declared file.

    The manifest pin already requires the agents key to name
    the shipped file only, but a file can sit in the directory
    without a declaration and stay invisible to that pin. The
    host loads only declared agents, so the stray file is
    inert, yet a later manifest change could name it and turn
    dead weight into a live persona no gate step ever read.
    """
    directory = root / "agents"
    try:
        names = sorted(
            entry.name for entry in directory.iterdir() if entry.is_file()
        )
    except OSError as exc:
        return ["cannot read the agents directory: %s" % exc]
    if names != ["reviewer.md"]:
        return [
            "the agents directory holds %r, not just the shipped "
            "agent file" % (names,)
        ]
    return []


def persona_problems(root):
    """Every persona pin against one tree root."""
    problems = [
        "manifest: %s" % problem
        for problem in manifest_problems(root)
    ]
    problems.extend(
        "settings file: %s" % problem
        for problem in settings_file_problems(root)
    )
    problems.extend(
        "agent dir: %s" % problem for problem in agent_dir_problems(root)
    )
    agent = root / "agents" / "reviewer.md"
    if agent.exists() and not agent.is_file():
        problems.append(
            "agent file: cannot read it: "
            "it is not a regular file"
        )
        return problems
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
