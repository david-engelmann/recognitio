[Back to the documentation index](README.md)

# The ZCode plugin build

## At a glance

**What ships**

The native ZCode plugin manifest at `.zcode-plugin/plugin.json`, with the contract for the build stated as the rule set in this brief.

**What was proven**

The manifest and the rules are pinned by the gate in this repo, and the rules rest on the primary ZCode documentation read in the round 15 research sweep the brief cites.

**What is unverified**

No ZCode client is available on this box, so no live client behaviour stands proven and the brief documents the contract without enforcing it on a live client, in its own words.

## Summary

Build 16 carries recognitio into ZCode as a native plugin
whose manifest stands at .zcode-plugin/plugin.json in this
repo. That manifest ships here, and no ZCode client is
available on this box, so this build documents its contract
and never enforces it on a live client. The contract lives in
the ZCode rules section below, and the gate at
scripts/check_zcode.py pins it.

Recognitio ships on ZCode as a native plugin with its manifest
at `.zcode-plugin/plugin.json`. ZCode distributes plugins
through its in client plugin marketplace, and the portable
v1 shape loses output styles and settings on ZCode. The trust
posture and the trust text requirement stand unchanged.

## The second packet guard

Every rule below carries a derivation note naming the canonical
skill section it restates or the primary ZCode plugin
documentation it reports, pinned by the gate at
`scripts/check_zcode.py`, so the scoped guidance cannot become
a rival instruction source. The primary ZCode plugin
documentation was read in the round 15 research sweep on
2026-10-23, which recorded the complete plugin API as fully
primary documented after the earlier plugin on hold posture was
set because the API was undocumented. No ZCode client is
available on this box, so the brief documents the contract and
never enforces it on a live client.

## The ZCode rules

### Z1. The native manifest path

Recognitio ships on ZCode as a native plugin with its manifest
at `.zcode-plugin/plugin.json`.

Derives from the primary ZCode plugin documentation, read in
the round 15 research sweep at https://zcode.z.ai/en/docs/skill
and https://zcode.z.ai/en/docs/plugin, which documents the complete
plugin API with the manifest at `.zcode-plugin/plugin.json`.

### Z2. The marketplace distribution and the version bump rule

ZCode distributes plugins through its in client plugin
marketplace. A marketplace entry carries a version, and the
client offers no update for an installed plugin whose
marketplace entry carries no version bump. A new recognitio
release on ZCode ships with a bumped marketplace version, or
installed clients never see it.

Derives from the primary ZCode plugin documentation, read in
the round 15 research sweep at https://zcode.z.ai/en/docs/skill
and https://zcode.z.ai/en/docs/plugin, which documents the in client
plugin marketplace distribution with the version bump rule.

### Z3. The portable shape loses output styles and settings

The portable v1 shape loses output styles and settings on
ZCode. A packet output style and a settings block that ride
the portable core do not take effect on ZCode. The portable
core stays portable, and the ZCode native shapes ride beside
it as per platform extensions, never blended into it.

Derives from canonical skill, The boundary, which keeps the
portable core apart from per platform extensions, and the
primary ZCode plugin documentation, read in the round 15
research sweep, which documents which portable fields ZCode
honors.

### Z4. Channels, language servers, output styles, and settings register but do not execute

Channels, lspServers, outputStyles, and settings register but
do not execute on ZCode. A registered channel, language
server, output style, or settings block is visible to the
client but runs no code and changes no behavior until ZCode
executes it. No recognitio behavior depends on a registered
but unexecuted field.

Derives from the primary ZCode plugin documentation, read in
the round 15 research sweep at https://zcode.z.ai/en/docs/skill
and https://zcode.z.ai/en/docs/plugin, which documents the register but
not execute behavior for channels, lspServers, outputStyles,
and settings.

### Z5. The format limits

A ZCode plugin description runs at most 1024 characters, and
a plugin body over 100KB is truncated at 100KB. The shipped
recognitio description runs far under the cap, and the
shipped skill body runs far under the truncation limit.

Derives from the primary ZCode plugin documentation, read in
the round 15 research sweep at https://zcode.z.ai/en/docs/skill
and https://zcode.z.ai/en/docs/plugin, which documents the 1024
character description cap and the 100KB body truncation.

### Z6. The trust posture stands unchanged

The trust posture and the trust text requirement stand
unchanged on ZCode. The skill assembles evidence and nothing
more, and judgement about the code belongs to the review skill
downstream. No ZCode rule grants the packet merge authority,
names a review model, or approves a red packet.

Derives from canonical skill, Trust and limits, which keeps
untrusted content outside the packet's verified boundary, and
canonical skill, The boundary, which keeps judgement with the
review skill downstream. Decision 4 binds this build like
every other build.

## The Build 16 decision record

Decision 27 records this build. Decision 4 binds this build
like every other build.

## Skill tightness

The ZCode plugin adds no skill text. The canonical skill at
`.agents/skills/recognitio/SKILL.md` is unchanged by this
build, and no ZCode rule restates a packet workflow step.

## Navigation

- [Documentation index](README.md)
- [Decisions](decisions.md)
- [Principles](principles.md)
