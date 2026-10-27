[Back to the documentation index](README.md)

# The Build 14 Kimi managed plugin

## At a glance

**What ships**

The derivation noted Kimi managed plugin rule set in this brief, covering the manifest agents field, the hook events and the size limits.

**What was proven**

Every rule carries a derivation note naming its skill section or primary citation, and the gate pins the notes against silent drift.

**What is unverified**

No live Kimi run stands in this brief, so the rule set rests on the primary pages cited here and live plugin behaviour stays unverified.

## Summary

Build 14 carries recognitio into Kimi as a managed plugin, and
every rule in this brief carries a note naming the skill
section or the primary citation it reports. What ships in this
repo is that derivation noted rule set in this brief, pinned
by its gate, while enforcement stays on the shipped scripts.
The contract lives in the Kimi rules section below, and the
gate at scripts/check_kimi.py pins it.

This document is the brief for Build 14, the Kimi managed plugin.
It exploits the Kimi plugin surface as a review advisory layer
beside the canonical packet. Decision 4 binds this build like
every other build. The guidance advises and never enforces.
Enforcement stays on the shipped scripts and on the per platform
extension.

## The second packet guard

Scoped guidance written apart from the canonical skill can
become a rival instruction source, which the plan names the
second packet failure. This brief answers that adversarial
angle with a derivation discipline and a restraint test.
Every Kimi rule in the rules section below carries a
derivation note naming the canonical skill section or gate
it restates or the primary citation it reports. A rule with
neither is a rival instruction source and fails the round.
The gate pins the notes, so a later edit cannot add an
underived rule in silence.

The restraint test runs against the rules directly. No rule
may invent a finding, claim a schedule the primaries deny,
or claim coverage the primaries deny. The rules that survive
are the ones whose derivation notes check out.

## The Kimi rules

### R1. The agents manifest field with auto discovery

The manifest `agents` field takes one or more `./` paths within
the plugin root, pointing to agent files. When the field is
omitted, an `agents/` directory at the plugin root is auto
discovered. While the plugin is enabled, the plugin shipped
agents are discovered automatically, and the platform allows
the main agent to delegate to plugin agents as sub agents.
That sentence states a platform capability, not a promised
recognitio delegation path, so no recognitio agent file
needs a delegation handoff sentence for it.

Derives from the primary Kimi plugins page at
www.kimi.com/code/docs/en/kimi-code-cli/customization/plugins.html,
which documents the `agents` field and the `agents/` auto
discovery with delegation to plugin agents as sub agents.

### R2. The collision precedence

Plugin agents rank below every other file source. User level,
extra, project level, and `--agent-file` agents all win over the
plugin provided agent. Replacing a built in agent requires an
explicit `override: true` in the frontmatter. The full scope
order is explicit `--agent-file` over project over extra over
user over plugin over built in, so plugin agents outrank only
the built in ones. Unknown agent frontmatter fields are ignored,
so newer agent files stay readable by older versions.

Derives from the primary Kimi plugins page Plugin Agents section
at www.kimi.com/code/docs/en/kimi-code-cli/customization/plugins.html,
which states the precedence, and the primary Kimi agents page at
www.kimi.com/code/docs/en/kimi-code-cli/customization/agents.html,
which states the scope order and the ignored unknown fields.

### R3. The qualified names rule

Plugin skills are listed and invoked under their qualified
`<pluginId>:<skillName>` name. Invoking a plugin skill by its
bare name no longer works.

Derives from the primary MoonshotAI/kimi-code releases page at
github.com/MoonshotAI/kimi-code/releases, which states that
bare name invocation no longer works, with no release version
or date pinned for this change in this brief.

### R4. The hook working directory, kept in two scopes

Hooks such as `PreToolUse` and `Stop` run in the session's
project directory, not the directory the server was started
from. Each plugin hook runs with its working directory set to
the plugin root, so a plugin `command` can use `./` paths inside
the plugin. The brief keeps the two scopes distinct, because a
global hook reading relative paths against the plugin root would
read the wrong tree.

Derives from the primary MoonshotAI/kimi-code releases page at
github.com/MoonshotAI/kimi-code/releases, which documents the
session project directory, and the primary Kimi plugins page
Hooks in Plugins section, which sets the plugin scope working
directory to the plugin root.

### R5. The four hook events

The four hook events TurnStarted, UserPromptQueued, TaskStarted,
and SessionHeartbeat are configurable under `[[hooks]]` in
`config.toml`. They observe turn starts, queued user input, sub
task launches, and session heartbeats.

Derives from the primary Kimi whats new page at
www.kimi.com/code/docs/en/kimi-code/whats-new.html, which
announces the four events.

### R6. The hook observation rule

The four hook events are observation only on the Kimi host. A
hook script on any of them runs fire and forget, and its return
value does not affect the main flow. Only PreToolUse, Stop, and
UserPromptSubmit have return values that affect the main flow,
so no check on the four events can stop a turn. The managed
plugin wires each of the four events through an observation
check of its own. The primaries describe the events as
observation points.

Derives from the primary Kimi hooks page at
www.kimi.com/code/docs/en/kimi-code-cli/customization/hooks.html,
which states that only PreToolUse, Stop, and UserPromptSubmit
have return values that affect the main flow and that all
other events are observation only. Decision 4 binds this build
like every other build.

### R7. The size limits

Each `systemPrompt` field, the inline one and the
`systemPromptPath` file each, is limited to 32 KB of UTF-8
bytes. Oversized content is ignored and reported in the plugin
diagnostics. Across all enabled plugins, one prompt build
injects at most 64 KB of instructions. Contributions beyond the
budget are skipped with a warning.

Derives from the primary Kimi plugins page at
www.kimi.com/code/docs/en/kimi-code-cli/customization/plugins.html,
which states the 32 KB per field limit and the 64 KB prompt
build budget.

### R8. The unsupported runtime fields

Unsupported runtime fields such as `tools`, `apps`, `inject`,
and `configFile` appear as diagnostics and are ignored. The
managed plugin declares none of them.

Derives from the primary Kimi plugins page at
www.kimi.com/code/docs/en/kimi-code-cli/customization/plugins.html,
which lists the fields and the diagnostics posture.

### R9. The print mode CI persona

Print mode CI runs under the reviewer persona through
`kimi -p --agent reviewer`, which selects the named agent as the
main agent for a new session in print mode. Print mode no longer
exits after a single turn while background tasks are pending. It
stays alive and feeds each result back to the main agent. The CI
gate waits for the run to settle instead of assuming a single
turn exit. A fresh checkout CI run sets KIMI_CODE_TRUST_WORKSPACE
to mark the workspace trusted.

Derives from the primary Kimi agents page at
www.kimi.com/code/docs/en/kimi-code-cli/customization/agents.html,
which works the `kimi -p --agent reviewer` example, and the
primary Kimi whats new page at
www.kimi.com/code/docs/en/kimi-code/whats-new.html, which
documents the stay alive behavior.

### R10. The distribution scope and the reference layout

Plugins are currently installed per user and apply to all
projects. Project level installation scope is not yet supported.
Local installs are copied to the managed copy under
`$KIMI_CODE_HOME/plugins/managed/<id>/`, and the CLI always runs
from the managed copy, so editing the source directory after
install has no effect until a reinstall. The managed package
follows the reference layout of the alibaba/open-code-review
package, which ships `.kimi-plugin/plugin.json` beside
`.claude-plugin/` with a delegation mode where the host coding
agent performs the review. The primary plugins page names
exactly two valid manifest locations, `<plugin_root>/kimi.plugin.json`
and `<plugin_root>/.kimi-plugin/plugin.json`, with
`kimi.plugin.json` taking precedence when both exist. A bare
`plugin.json` at the repo root is not a valid manifest location.
No version is pinned for this reference layout in this brief.

Derives from the primary Kimi plugins page at
www.kimi.com/code/docs/en/kimi-code-cli/customization/plugins.html,
which documents the per user install scope and the managed copy,
and the alibaba/open-code-review repo at
github.com/alibaba/open-code-review, whose `.kimi-plugin/plugin.json`
sits beside `.claude-plugin/`.

## The Build 14 decision record

The Build 14 decision record lives at decision 24 in
`docs/decisions.md`. It names the manifest agents field with
auto discovery, the collision precedence, the qualified names
rule, the hook working directory in both scopes, the four hook
events with the observation only posture the primaries
state, the 32KB per field and 64KB total limits, the
unsupported field
diagnostics, the print mode CI persona with the stay alive
behavior, and the per user install scope with the reference
layout. Decision 4 binds this build like every other build.

## Skill tightness

The brief, its gate script at `scripts/check_kimi.py`, and its
tests live outside the canonical skill text under `docs/`,
`scripts/`, and `tests/`. The skill description is untouched, so
the description protocol does not fire. The deliverable remains
the skill.

- [Documentation index](README.md)
- [Decisions](decisions.md)
- [Principles](principles.md)
