[Back to the documentation index](README.md)

# The Codex plugin build

## At a glance

**What ships**

The OpenAI extension object in the portable manifest at
`agent-plugins-package/plugin.json`, the repo marketplace at
`.agents/plugins/marketplace.json` that offers the package to
Codex, and the `agents/openai.yaml` file inside the skill
folder, with the contract for the build stated as the rule set
in this brief.

**What was proven**

The Codex CLI on this box registered the repo marketplace,
listed the plugin with its source at the portable package,
and installed it into a scratch home cache with the package
files inside, and the manifest, the marketplace, and the
skill folder file are pinned by the gate in this repo.

**What is unverified**

Invocation inside a live Codex session stays unverified,
because no signed in Codex session stands on this box and a
live session is the only surface that exercises the skill.

## Summary

Build 19 carries recognitio into Codex as a plugin. The skill
itself needed no move, because the canonical skill already
stands in the location Codex scans. What ships is the OpenAI
presentation of the portable package, the repo marketplace
that offers it, and the one Codex specific file inside the
skill folder. The contract lives in the Codex plugin rules
section below, and the gate at scripts/check_codex_plugin.py
pins it.

This document is the brief for Build 19, the Codex plugin
build. It rests on three primary OpenAI surfaces read on
2026-10-27, the Build skills page, the Package your plugin
page, and the ChatGPT and Codex changelog. Decision 4 binds
this build like every other build. The rules advise while
enforcement stays on the shipped scripts.

## The second packet guard

Every rule below carries a derivation note naming the
canonical skill section it restates or the primary OpenAI
citation it reports, pinned by the gate at
`scripts/check_codex_plugin.py`, so the scoped guidance
cannot become a rival instruction source. A rule with neither
is a rival instruction source and fails the build.

## The Codex plugin rules

### X1. The skill already stands in the Codex location

Codex scans `.agents/skills` in every directory from the
working directory up to the repository root, and it follows
symlinked skill folders when it scans. The canonical skill at
`.agents/skills/recognitio` is therefore already a Codex skill
in any repo that checks it in, and this build adds no second
copy of the skill for Codex. The Codex changelog entry dated
2025-12-19 announces agent skills in Codex, in the Codex CLI
and the IDE extensions, with explicit invocation by typing
`$` and the skill name.

Derives from the primary Build skills page at
developers.openai.com/codex/skills, read on 2026-10-27, which
documents the scan locations and the symlink behaviour, and
the primary changelog at learn.chatgpt.com/docs/changelog,
whose entry dated 2025-12-19 announces agent skills in Codex.

### X2. The skill folder carries one Codex file

The skill folder carries `agents/openai.yaml`, the file the
primary skills page names for UI metadata, invocation policy,
and tool dependencies. Its interface block names the display
name, a short description, the brand colour from the palette
record, and a default prompt. Its policy block leaves
implicit invocation on, because the skill is meant to trigger
on a matching request as well as on an explicit call. The
file declares no dependencies, because the packet workflow
runs on local git and the Python standard library and needs
no MCP tool. The file is part of the canonical skill folder,
so every byte identical copy of the skill carries it too.

Derives from the primary Build skills page at
developers.openai.com/codex/skills, read on 2026-10-27, which
documents the `agents/openai.yaml` fields and names
`allow_implicit_invocation` with a default of true, and from
canonical skill, Trust and limits, which keeps the workflow
on local git only.

### X3. The plugin identity rides the portable manifest

The OpenAI specific settings live in the `extensions` object
of the portable manifest under the `com.openai` namespace,
beside the Claude Code and Antigravity namespaces the package
already carries. The extension holds one interface object
with the display name, the short and long descriptions, the
developer name, the category, the capabilities, the website,
the default prompt, the brand colour, and the logo paths.
Portable identity stays at the manifest root, where the name,
the version, and the description already stand. When the
extension object is present it replaces the entire
`.codex-plugin/plugin.json` overlay, so this build ships no
`.codex-plugin` directory and no second manifest for a host
to disagree with.

Derives from the primary Package your plugin page at
developers.openai.com/plugins/build/plugins, read on
2026-10-27, which places OpenAI specific presentation under
`extensions.com.openai` in the root manifest and states the
replacement rule for the compatibility overlay.

### X4. The interface carries the brand icon from the package assets

The interface names the brand icon for both its logo and its
composer icon, at `./assets/icon-512.png` inside the package.
The primary structure for a portable plugin names an assets
directory beside the manifest and the skills tree, and its
path rules keep extension paths relative to the plugin root
with a `./` prefix and store visual assets under `./assets/`
when possible. The shipped icon file is byte identical to the
brand master at `docs/brand/recognitio-icon-512.png`, and the
gate pins the equality so the copy cannot drift from the
brand record.

Derives from the primary Package your plugin page at
developers.openai.com/plugins/build/plugins, read on
2026-10-27, which documents the plugin structure and the path
rules, and from the brand record at `docs/brand/palette.json`
and its gate at `scripts/check_brand.py`.

### X5. The repo marketplace offers the package

The repo marketplace stands at `.agents/plugins/marketplace.json`
and offers the one plugin this repo ships. Its entry names the
plugin, points its local source at `./agent-plugins-package`
with the path read from the marketplace root at the repo
root, and carries the installation and authentication policy
fields and the category the primary page requires on every
entry. The category matches the category in the plugin
interface, so the catalog and the package describe the same
shelf. The marketplace name is recognitio and its display
name is Recognitio.

Derives from the primary Package your plugin page at
developers.openai.com/plugins/build/plugins, read on
2026-10-27, which documents the repo marketplace location,
the source path rules, and the required policy and category
fields on each entry.

### X6. No directory listing is claimed

No universal plugin directory listing exists or has been
submitted for recognitio. The primary page separates the
public universal directory, where a plugin is published once
through the submission portal, from local and repo
marketplaces, which are authoring, testing, and team
distribution sources. This build ships only the repo
marketplace route. A listing in the universal directory is a
submission its owner makes, and nothing in this build
performs one or claims one.

Derives from the primary Package your plugin page at
developers.openai.com/plugins/build/plugins, read on
2026-10-27, which separates the universal plugin directory
from local and repo marketplaces and names the submission
portal as the publication route.

### X7. The trust posture stands unchanged

The trust posture and the trust text requirement stand
unchanged on Codex. The skill assembles evidence and nothing
more, and judgement about the code belongs to the review
skill downstream. Recognitio ships no MCP servers and no
apps, so the extension declares neither an apps mapping nor
hooks, and the package still carries no `mcp.json`. No Codex
rule grants the packet merge authority, names a review model,
or approves a red packet.

Derives from canonical skill, Trust and limits, and canonical
skill, The boundary, which keeps judgement with the review
skill downstream. Decision 4 binds this build like every
other build.

## The CLI probe

On 2026-10-27 the Codex CLI on this box, version
0.164.0-alpha.9, registered the repo marketplace and listed
recognitio@recognitio with its source at the portable
package. The probe ran with a scratch Codex home, so no user
configuration was touched. The marketplace add command named
the marketplace recognitio and its root at this repo, the
marketplace list command showed the same root, and the plugin
list command resolved the entry through to
`agent-plugins-package` with a status of not installed.

The plugin add command then installed recognitio@recognitio
into the scratch home cache at
plugins/cache/recognitio/recognitio/1.3.0, and the plugin
list showed it installed and enabled, with the installed
files holding the manifest, the brand icon, and the skill
with its `agents/openai.yaml` and its extractor. The first
probe stopped at an unrecognized install subcommand and
reported installation unverified, and the review of this
build corrected that sentence, because the install
subcommand is named add. Invocation inside a live Codex
session stays unverified. No claim in this brief rests on a
live session.

## The Build 19 decision record

Decision 29 records this build. Decision 4 binds this build
like every other build.

## Skill tightness

The build adds one file to the skill folder,
`agents/openai.yaml`, and no skill text. The canonical skill
at `.agents/skills/recognitio/SKILL.md` is unchanged by this
build, the skill description is untouched, and no Codex rule
restates a packet workflow step.

## Navigation

- [Documentation index](README.md)
- [Decisions](decisions.md)
- [Principles](principles.md)
