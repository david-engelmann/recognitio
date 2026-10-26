[Back to the documentation index](README.md)

# The Build 8 portable package, Agent Plugins 1.0.0

## Summary

Build 8 packages the portable core on its own as a skills tree
under a single manifest, with no MCP file in the package and the
Claude Code native shapes left where they stand at the repo
root. The package ships in this repo under
agent-plugins-package, and the skill it carries is a byte
identical copy of the canonical skill. The contract lives in
the closed manifest section below, and the gate at
scripts/check_package.py pins the package shape.

This document is the brief for the Build 8 portable package. The
package lives at `agent-plugins-package/` and carries only the
portable core, the closed schema manifest at
`agent-plugins-package/plugin.json` and the skills tree at
`agent-plugins-package/skills/`. The Claude Code native shapes
ride beside the portable core at the repo root as per platform
extensions. Decision 4 binds this build like every other build.
The package is a packaging format with no execution or
enforcement semantics. Enforcement stays on the shipped scripts
and on the per platform extension.

## The closed manifest schema

Section 5 of the specification permits exactly ten top level
fields in `plugin.json`. They are `$schema`, `name`, `version`,
`description`, `author`, `homepage`, `repository`, `license`,
`keywords` and `extensions`. Any other top level field does not
conform. Conformant clients must report and ignore each unknown
field and must not assign semantics to unknown fields. The
portable manifest carries the canonical `$schema` value
`https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`.

This is the inversion guard the round 19 spec lane named. The
repo native manifest at `.claude-plugin/plugin.json` carries the
keys `agents`, `settings`, `outputStyles` and `skills`, and none
of them is in the permitted set. A portable manifest that reused
those keys would load on a conformant client as a bare skill
with no persona, no forced style and no hook wiring, and it
would do so without an error. The portable manifest therefore
carries none of them at the top level. The gate pins the closed
schema and fails any top level field outside the permitted set.

## The native shapes as per platform extensions

Section 8 of the specification gives the extension mechanism.
Client specific manifest data goes under `extensions` keyed by
reverse domain namespace, and client specific files go under a
top level directory named for that namespace. A client may use
either or both, and the specification assigns no portable
semantics to extension data or files. Each client defines its
own.

Build 8 uses the repo root representation for the native shape
files and the extension manifest data representation to declare
them. The native shapes do not move into the package. They stay
where the home platform install expects them, and the portable
manifest declares each one under the `com.anthropic.claude-code`
namespace. The declared shapes are the agent persona at
`agents/reviewer.md`, the output style at
`output-styles/packet.md`, the mod hooks at `hooks/hooks.json`
and `hooks/register.js`, the headless runbook at
`docs/headless-review.md` with its script at
`scripts/check_headless.py`, and the fan out workflow at
`workflows/review-fanout.md` with its schema at
`workflows/findings.schema.json`. The native install path is
named by `nativeManifest` at `.claude-plugin/plugin.json` and
`nativeMarketplace` at `.claude-plugin/marketplace.json`. The
gate resolves every declared path in the repo, so a renamed
shape breaks the gate instead of dangling.

The mod hooks cannot ride in the portable core at all. Version
1.0 defines exactly two component types, skills and MCP servers,
so hooks are outside the version 1.0 format. The inversion is
structural here and not only a risk, and the extension mechanism
is the only honest ride for them.

## The mcp.json disposition

Recognitio ships no MCP servers. The package omits `mcp.json`,
which section 6 permits, since a missing fixed component
location is not an error. The alternative the spec allows, an
empty `mcpServers` object, would suggest a server surface the
repo does not have. The omission is the honest shape, and the
gate pins it, so a later edit cannot quietly add a server the
trust text never approved.

## The skills single source rule

Section 6 fixes skill discovery at `skills/` with one immediate
child directory per skill, and the Agent Skills specification
owns the `SKILL.md` format. The package skill at
`agent-plugins-package/skills/recognitio/` is therefore a second
spelling of the canonical skill at
`.agents/skills/recognitio/` by construction. The canonical is
the only spelling that ever changes. The package copy is pinned
byte identical to the canonical by the gate on every run, file
by file across the whole skill tree. A drifted copy fails the
gate.

## The honesty sentence

The package does not install natively in Claude Code on current evidence.

No primary source puts Claude Code among the implementing hosts
the round 15 research closed, which are ChatGPT, Codex, GitHub
Copilot, VS Code, Cursor and Kiro. Plugin authors ship Claude
Code native plugins through the marketplace route and ship
skills separately through the open Agent Skills format. The
brief states the negative plainly and the gate pins the
sentence, so a later edit cannot quietly claim the install the
evidence does not support. The `.claude-plugin/` install path
is unaffected. The portable package adds beside it and replaces
nothing.

## The two governances

The Agent Skills donation and the Agent Plugins format are
separate governances, and this brief cites each for what it
governs. The Agentic AI Foundation governs the Agent Skills
standard, which the 1.0 specification references normatively as
the source of truth for the `SKILL.md` format. Anthropic
donated the standard to the foundation on 2026-10-22,
announced at AGNTCon and MCPCon, and the transfer is now recorded
as primary on both halves, read from the Linux Foundation
release and Anthropic's own post in round 20. Governance for the
Agent Plugins project itself is defined separately from the
portable package format in its own Technical Charter, as the
1.0 spec text states. The 70 plus platform integrations the
donation reports are Agent Skills integrations, not Agent
Plugins implementing hosts, and this brief does not treat them
as such.

## Skill tightness

The package, its gate script and this brief live outside the
canonical skill text under `agent-plugins-package/`, `scripts/`
and `docs/`. The skill description is untouched, so the
description protocol does not fire. The deliverable remains the
skill.

## Navigation

- [Documentation index](README.md)
- [Decisions](decisions.md)
- [Principles](principles.md)
- [The headless review shape](headless-review.md)
