[Back to the documentation index](README.md)

# The Build 12 Antigravity plugin alteration

## At a glance

**What ships**

The Antigravity plugin tree under `.antigravity` with its manifest and its PreToolUse hook wiring, plus the second extensions namespace entry in the portable manifest.

**What was proven**

The wiring and the contract sentences are pinned by the gate in this repo, and the dated sunset evidence and the v0.65.0 pin rest on the primary Google pages the brief cites.

**What is unverified**

No Antigravity product ran in this build, so the host enforcement of the hook contract stays unverified, as the brief states in its harness limit.

## Summary

Build 12 alters the plugin for Antigravity as a second
extensions namespace beside the portable core, with its
manifest and its hook wiring standing under .antigravity in
this repo. What ships here is that plugin tree and the second
namespace entry in the portable manifest. The contract lives
in the harness contract section below, and the gate at
scripts/check_antigravity.py pins it.

This document is the brief for Build 12, the Antigravity plugin
alteration. It records the Antigravity plugin format with
`plugin.json`, `skills/`, `agents/`, `rules/`, and `hooks.json`,
and a `PreToolUse` hook carrying the `deny`, `force_ask`, and
`auto_approve` decisions, per the primary Google docs read as
text on 2026-10-24. It records the dated October 9 2026 sunset
evidence with Antigravity as the named path, which confirms the
Antigravity first orientation the program already carried. It
records the v0.65.0 stable pin with the docs lag caveat naming
which page to trust. Decision 4 binds this build like every
other build. The brief and the hook wiring document the
contract and never enforce it. Enforcement stays on the shipped
scripts.

## The plugin format

The primary plugins page documents the plugin layout with
`plugin.json` as the required marker carrying the `$schema`
value `https://antigravity.google/schemas/v1/plugin.json`, and
the optional `mcp_config.json`, `hooks.json`,
`skills/<name>/SKILL.md`, `agents/`, and `rules/` components.
Workspace install is `.agents/plugins/` at the workspace root
and global install is `~/.gemini/config/plugins/`, with a
Marketplace tab in the Antigravity App.

The primary hooks page documents exactly six events,
`SessionStart`, `PreToolUse`, `PostToolUse`, `PreInvocation`,
`PostInvocation`, and `Stop`. Each hook runs a shell command
that receives JSON on stdin and returns JSON on stdout, and the
`PreToolUse` output contract carries a required `decision`
field.

The `decision` field carries `allow`, `auto_approve`, `deny`,
`ask`, `force_ask`, and `deny_unless_prior_grant` on the
primary page. This build's hook uses three of them, `deny`,
`force_ask`, and `auto_approve`, and the gate pins those three.

## The dated evidence

Starting October 9 2026, no new Gemini Code Assist Standard or
Enterprise subscriptions can be purchased. Existing
subscriptions continue through their contract terms. License
additions and annual renewals run to January 31 2027, and
monthly renewals run to December 31 2027. The page names
Antigravity as the forward path for agentic coding assistance.
The page's FAQ names the Gemini CLI to Antigravity CLI
migration guide as the concrete form of that path.

The Gemini Code Assist service on GitHub stands in split
form, with the consumer version deprecated on June 18 2026
and shut down on July 17 2026 and the enterprise version
not affected. No brief cites the config page as proof of
consumer availability, and a new adaptation on the
enterprise GitHub surface requires a current primary
status check first.

The October 9 2026 date is the page's content date, and this
brief never pins a page stamp, because a stamp is a moving
target. The round 24 lane read the sunset page live on
2026-10-24, and the decision record carries the stamp the page
showed that day.

## The version pin and the docs lag

v0.65.0 is the stable pin for the Gemini CLI extension bundle,
read from the GitHub releases page on 2026-10-24. The docs
changelog page at geminicli.com still renders v0.64.0, released
October 13 2026, so the docs lag is real and the brief trusts
the releases page over the docs page. A v0.66.0 pre-release
exists, `v0.66.0-preview.0` with an October 13 nightly tag, and
it is not stable, so the v0.65.0 pin stands.

The v0.66.0 pre-release hardens SKILL.md frontmatter parsing
for single line descriptions. The recognitio description
carries no colon, so the hardening does not interact with the
shipped skill, and the change stays an adjacent watch item with
no brief impact.

## The extension boundary

The Antigravity native shapes live as a second extensions
namespace beside the portable core, never blended into it.

No primary source names a reverse domain namespace for an
Antigravity plugin, so the portable manifest uses
`com.google.antigravity` as a documented placeholder following
the section 8 reverse domain convention, and the brief does not
present it as primary.

The build declares the Antigravity plugin manifest at
`.antigravity/plugin.json` and the hook wiring at
`.antigravity/hooks.json` under the new namespace, and the gate
resolves every declared path in the repo.

The primary Antigravity changelog's October 22 2026 plugin
skill loading fixes say every skill lives inside the plugin's
`skills` folder. This build's plugin names no skill entry,
because the canonical skill is already discoverable at
`.agents/skills/` on the primary documented Antigravity skills
discovery path, so the build ships no second skill copy.

The build ships the plugin manifest and the hook wiring, and
no agent, rule, or MCP component in this build.

## The documented harness contract

The harness path below is the repo-documented contract. This
lane has no Antigravity product and no live browser, so no
product run stands behind it, and the gate pins the wiring file
and the contract sentences, not the host's enforcement.

### S1. The wiring declares one PreToolUse entry

The shipped wiring at `.antigravity/hooks.json` declares one
`PreToolUse` entry, and the entry's matcher names
`invoke_subagent` with its Subagents spec fields, per the new
primary Subagents spec evidence. The matcher is the build's
declared mapping for the review run tool call.

Derives from the primary Subagents spec, which documents
`invoke_subagent` with its fields, and the primary hooks page
at antigravity.google/docs/hooks, which documents exactly six
events and the stdin and stdout JSON contract.

### S2. The event contract

On a matched tool call the hook receives the event JSON on
stdin and returns a JSON object on stdout carrying the required
`decision` field.

Derives from the primary hooks page at
antigravity.google/docs/hooks, which documents the stdin and
stdout JSON contract and the required `decision` field.

### S3. Deny

`deny` refuses the tool call with a reason when the packet
manifest is missing or not verified.

Derives from canonical skill, Stamping the gate report and
Completeness discipline, which read "Never let a review begin
on a packet whose verified flag is false."

### S4. Force ask

`force_ask` holds the tool call for user confirmation when the
packet manifest is unreadable or unparsable, because the hook
cannot prove the packet is whole.

Derives from canonical skill, Completeness discipline, which
never lets a review begin on a packet whose verified flag is
false, and keeps the unprovable packet in human hands.

### S5. Auto approve

`auto_approve` lets the tool call through without asking when
the packet manifest reads verified.

Derives from canonical skill, Stamping the gate report, which
stamps the review only on a verified packet.

### S6. The planned degraded state

A missing or unparseable hook file is a planned degraded state,
never a silent pass. The repo gate fails on a missing or
unparseable hook file, so the build cannot land without it. On
the host, a plugin without its hook file loads without the
Antigravity gate, and the review run falls back to the shipped
scripts, with `scripts/check_packet.py` refusing any review
before it starts on a packet whose manifest does not read
verified.

Derives from Decision 4, which binds this build like every
other build, and the Build 7 disabled mods degradation, which
the brief at docs/mod-build7.md documents as the same fallback.

### S7. The Claude Code only negative

The Build 7 mod hooks are Claude Code only on current evidence.
The primary hooks page documents exactly six events and names
no `agent.spawn` event, so the Build 12 hook is a stated
`PreToolUse` mapping and not a native spawn gate equivalent.

Derives from the primary hooks page at
antigravity.google/docs/hooks and the Build 7 brief at
docs/mod-build7.md, which documents the mod as the home
platform extension.

### S8. The honest harness limit

This lane has no Antigravity product and no live browser, so
the harness contract above is the repo-documented contract, and
the brief claims no product enforcement behavior it cannot run.
The gate pins the wiring file and the contract sentences, not
the host's enforcement.

Derives from Decision 4, which binds this build like every
other build, and R24-RT-04, which the round 24 red team filed
for this exact limit.

## The second packet guard

Every contract statement above carries a derivation note naming
the canonical skill section, the primary citation, or the
binding decision it restates. A statement with neither is a
rival instruction source and fails the round. The gate pins the
notes, so a later edit cannot add an underived statement in
silence.

## Skill tightness

The brief, its gate script at `scripts/check_antigravity.py`,
its tests, the `.antigravity/` plugin tree, and the manifest's
second namespace live outside the canonical skill text under
`docs/`, `scripts/`, `tests/`, `.antigravity/`, and
`agent-plugins-package/`. The skill description is untouched,
so the description protocol does not fire. The canonical skill
frontmatter holds exactly four keys, name, description, context,
and background, and the brief claims nothing else about it.
The deliverable remains the skill.

## Navigation

- [Documentation index](README.md)
- [Decisions](decisions.md)
- [Principles](principles.md)
