# The Build 15 Qwen Code marketplace presence brief

This document is the brief for Build 15, the Qwen Code
marketplace presence. It is a conditional draft. The
conditional publication decision stays with David, and
nothing in this brief presents Build 15 as published.
Decision 4 binds this build like every other build. The
guidance advises and never enforces. Enforcement stays on
the shipped scripts and on the per platform extension.

No Qwen listing file ships in this round. There is no
qwen-extension.json file in this repo and no new hidden
directory manifest, so no Qwen listing version exists
for the version check to check. The repo version stays
1.3.0 and this brief claims no version bump.

Every Qwen rule in the rules section below carries a
derivation note naming the canonical skill section it
restates or the primary Qwen citation it reports or the
binding decision it follows. A rule with neither is a
rival instruction source and fails the round. The gate
pins the notes, so a later edit cannot add an underived
rule in silence.

Every Qwen citation in this brief was read on
2026-10-24. No Qwen page read for this brief shows a
revision date in its text, so no page date is claimed
for any of them and no search index date is treated as
a page date. Recheck the pages before citing a figure
again, because the pages are undated and a figure on
them could move without a visible revision stamp.

The Qwen review pipeline figures in this brief describe
Qwen own review skill. They are not recognitio packet
figures and must not be read as packet assembly claims.
The packet workflow itself is unchanged by every route
in this brief. Extraction still runs on the local clone
with the Python standard library extractor, and no route
in this brief changes extraction, tiers, budgets, or the
manifest flag.

## The Qwen rules

### R1. The figure basis and scope table

No single figure in this brief stands as the Qwen
figure. The conflict between the two primary pages is
not resolved to one figure and not resolved by date.
Both pages were live on 2026-10-24 and neither shows a
revision date. The code review page supplies the scoped
table because the commands page itself points to it
for full documentation, but that pointer does not
resolve the conflict. The commands page figure is a
conflicting summary and is not used.

| Page | Scope | Figure | Basis |
| Code review page | Step 3A small diff roster | Up to 16 parallel agents | Effort table |
| Code review page | Same repo PR reviews | Up to 17 parallel tasks | Roster narrative |
| Code review page | Same repo PR reviews in practice with finders | 16 to 19 in practice | Roster narrative |
| Code review page | Local diff and file path reviews | 14 to 17 | Roster narrative |
| Code review page | Cross repo lightweight mode with PR identity | 14 to 17 | Roster narrative |
| Code review page | Cross repo lightweight mode without PR identity | 12 to 15 | Roster narrative |
| Code review page | Review agents in Step 3 | 17 with 0 to 2 added | Token efficiency table |
| Code review page | Review agents in Step 3 without Agent 1e | 16 | Token efficiency table |
| Code review page | Local and file reviews | 15 | Token efficiency table |
| Code review page | Cross repo reviews with PR identity | 15 | Token efficiency table |
| Code review page | Cross repo reviews without PR identity | 13 | Token efficiency table |
| Commands page | Built in skills table | 12 parallel agents at high effort | Conflicting summary not used |

A scope total in this brief always names its basis.
The roster narrative and the token efficiency table
give different scope totals on the same page, so a
total quoted without its basis is an incomplete claim.
The commands page figure matches no same repo high
effort figure on the code review page, and this brief
invents no scope for it to rescue it.

Derives from the primary Qwen code review page at
qwenlm.github.io/qwen-code-docs/en/users/features/code-review
and the primary Qwen commands page at
qwenlm.github.io/qwen-code-docs/en/users/features/commands
both read on 2026-10-24, and from binding decision 26
with its round 31 note and round 33 note.

### R2. The wrapper exits and the internal verify exit

The wrapper exits and the internal verify exit live in
two separate tables. They are never combined into one
table and no sentence in this brief lists the internal
verify exit beside the wrapper exits as a wrapper
outcome.

Wrapper exits

| Exit | Meaning |
| 0 | The review completed whatever it decided |
| 1 | It never reached a verdict because a child failed or timed out or left no composed artifact |
| 3 | It completed with REQUEST_CHANGES and fail-on request-changes set |

The code 3 rather than 2 lets a gate distinguish a
blocking review from a broken tool.

Internal verify exit

| Exit | Meaning |
| 4 | Internal verify refusal at the compose floor |

Once the floor or less remains, the agent prompt with
role verify refuses to build, shown as a VERIFY BUDGET
line with exit 4. Findings in hand keep an unverified
tag which caps the verdict, and compose review and
submission run. The compose floor variable is
QWEN_REVIEW_DEADLINE_COMPOSE_FLOOR_SECONDS with
default 1200 and 0 disabling the gate. The compose
floor note attaches to the internal verify exit only.

The decision 26 main paragraph is superseded for
Build 15 purposes by the round 31 note and the round
33 note. No Build 15 sentence copies the main
paragraph phrasing without that qualification.

Derives from the primary Qwen code review page at
qwenlm.github.io/qwen-code-docs/en/users/features/code-review
read on 2026-10-24, and from binding decision 26 with
its round 31 note and round 33 note.

### R3. The Agent Plugins v1 support matrix

Qwen Code natively loads portable Agent Plugins v1
packages without converting or rewriting plugin.json,
mcp.json, or SKILL.md files. The portable runtime
supports Agent Skills plus stdio and Streamable HTTP
MCP servers. Commands, agents, hooks, client
namespaces, and legacy SSE MCP are not activated.

The recognitio plugin.json namespaces for Claude Code
and Antigravity are client namespaces Qwen does not
activate under that matrix. The portable route carries
the SKILL ONLY. It does not carry the reviewer
persona, the hooks, the output style, or the fanout
workflow into Qwen.

Derives from the primary Qwen extension introduction
page at
qwenlm.github.io/qwen-code-docs/en/users/extension/introduction
read on 2026-10-24, and from the canonical skill
section Purpose which states the skill assembles
evidence only.

### R4. The install routes

Qwen Code installs an extension from a git URL, a
local path, an archive, an archive URL, an npm
package, or a marketplace. Marketplace sources power
the Discover tab, and those sources are Claude plugin
marketplaces. The routes this brief carries are the
GitHub repo install, the marketplace source add, the
scoped npm route, the Qoder route, and the Agent
Plugins v1 route.

Qoder route. Qwen Code supports Qoder plugins
containing a `.qoder-plugin/plugin.json` manifest.
The installer converts the Qoder manifest to
qwen-extension.json and preserves standard commands,
agents, and skills directories. MCP servers from a
root `.mcp.json` file are included. A root
system-prompt.md file loads as extension context with
QWEN.md and other context files retained and
deduplicated.

```bash
git clone https://github.com/david-engelmann/recognitio.git recognitio-qwen
git -C recognitio-qwen checkout COMMIT_SHA
qwen extensions install ./recognitio-qwen/qoder-input
```

The Qoder conversion command above carries its pinned
form in this same section. Replace COMMIT_SHA with the
commit SHA you reviewed, then build the Qoder input
from that checkout. No Qoder manifest for recognitio
ships in this repo, so a Qoder input is built from a
checkout for a test and is not a shipped listing.
Activation of preserved Qoder commands and agents in Qwen stays UNVERIFIED. The primary extension
introduction page says the installer preserves those
directories and does not state whether they activate.

Agent Plugins v1 route. Qwen Code natively loads
portable Agent Plugins v1 packages without converting
or rewriting plugin.json, mcp.json, or SKILL.md files.

```bash
git clone https://github.com/david-engelmann/recognitio.git recognitio-qwen
git -C recognitio-qwen checkout COMMIT_SHA
qwen extensions install ./recognitio-qwen/agent-plugins-package
```

The Agent Plugins command above carries its pinned
form in this same section. Replace COMMIT_SHA with the
commit SHA you reviewed.

Scoped npm route. Only scoped packages are supported.
Registry resolution follows this priority in order.
The CLI flag first, then the scoped registry from a
scoped `.npmrc` file, then the default registry from a
`.npmrc` file, then registry.npmjs.org. An npm
extension must include either a native
qwen-extension.json or an Agent Plugins v1 plugin.json
at the package root.

```bash
qwen extensions install @scope/my-extension@1.2.0
```

The scoped npm form above is an unpinned test form in
shape only. No scoped recognitio package is published
in this round, the scoped npm route is untested, and
the form above must not be read as a real package
name or a real install. Unscoped names are not
supported.

GitHub repo install and marketplace source add.

```bash
qwen extensions install david-engelmann/recognitio
qwen extensions sources add david-engelmann/recognitio
```

The repo install and source add forms above are
conditional draft forms. They describe paths the
primary extension page shows, not a published listing.

Derives from the primary Qwen extension introduction
page at
qwenlm.github.io/qwen-code-docs/en/users/extension/introduction
read on 2026-10-24.

### R5. The prefixed naming rule

An extension skill always carries its owner,
registered as extension name plus skill name with a
colon between them, for example rust plus pdf written
as one prefixed name. The bare skill name is not an
alias. The prefix is added at load and is not written
into SKILL.md. Extension commands differ, named after
files and prefixed only on collision.

Three naming cases hold.

- skills.disabled blocks under either spelling, so a
disabled entry written with the bare name still hides
the prefixed skill.
- skills.enabled opts in under the prefixed name
only, so an enabled entry with the bare name alone
does not opt an extension skill in.
- The cancellation exception holds for one bare pair.
A pre-prefix opt-in sitting in skills.defaultDisabled
with the same spelling cancels against an enabled
entry with the same spelling, so defaultDisabled with
the bare name plus enabled with the bare name cancels
the entry and the skill ends up enabled per workspace
enablement or extension default. A default-off skill
still requires the prefixed name in skills.enabled.

Derives from the primary Qwen skills page at
qwenlm.github.io/qwen-code-docs/en/users/features/skills
read on 2026-10-24.

### R6. The shared skills alias and its precedence

Qwen Code reads project skills from `.agents/skills/`.
If both folders contain a skill with the same name,
the one in `.qwen/skills/` wins. The same precedence
holds for personal skills, with the home Qwen skills
folder winning over the home agents skills folder.

The repo canonical skill lives at
`.agents/skills/recognitio/` in this repo. That repo
layout fact is not the Qwen discovery rule. Inside
Qwen, the agents skills folder is a read alias with
lower precedence than the Qwen skills folder on a
same-name collision. A test tree must be checked for
a shadow copy under `.qwen/skills/recognitio` before
any load claim is made about the project copy, because
the winning copy on a collision is the Qwen skills
copy, not the agents skills copy.

Derives from the primary Qwen skills page at
qwenlm.github.io/qwen-code-docs/en/users/features/skills
read on 2026-10-24, and from the canonical skill
section Purpose which states the skill assembles
evidence only.

### R7. The conversion fidelity record

File install fidelity holds for the SKILL TREE ONLY.
In the round 33 test, a Qoder-only input carrying
only the Qoder manifest was installed with the Qwen
CLI, and the Agent Plugins v1 package was installed
with the Qwen CLI, each in a scratch home. The
installed SKILL.md and extract.py files were byte
identical to the canonical skill tree in both installs.
The Qoder install recorded originSource as Qoder and
created a qwen-extension.json carrying only name,
version, and description, which mirrors the minimal
input manifest and is not proof that Qwen drops
fields. The Agent Plugins v1 install recorded
originSource as AgentPlugins and retained plugin.json
at the installed root with no conversion file created.
The installed bundles listed skill recognitio in the
extensions list without editing frontmatter.

The round 37 full bundle attempt adds the exception
this record needs. A Qoder input of 14 files, built
from the canonical tree at the round 36 head and
holding the skill tree with its side shapes, was
installed with Qwen CLI 0.26.0 in a scratch home.
Twelve payload files and the retained Qoder manifest
were byte identical to the canonical tree. Three
conversion differences stand against that result. The
installed SKILL.md differs from the canonical file in
exactly one line, the T0 tier paragraph, where the
words a Claude rules file under a .claude/rules folder
in the canonical text read as a Claude rules file
under a .qwen/rules folder in the installed text, and
the installed file runs 15231 bytes against 15233 for
the canonical file. The installer left the matching
spelling inside extract.py untouched, so the installed
bundle names one folder in its skill prose and tests
for another in its extractor code. The converted
qwen-extension.json carries only name and version and
description, and the author and license fields the
input manifest carried are absent from the converted
file, which settles the question the round 33 record
left open on whether the conversion drops fields. The
installer mirror at .claude-plugin/plugin.json carries
the input manifest fields and values at 355 bytes
against 356 for the input, losing only its trailing
newline. The install also added an install record file
that has no canonical counterpart. Skill file byte
fidelity does not hold for a Qoder install of the
current canonical skill text, and this brief claims
byte fidelity for the round 33 skill tree installs
only.

Side shape files ride in as files in the round 37
full bundle install. The round 33 installs carried
the skill tree only because their inputs held nothing
else. The round 37 full bundle install preserved the
side shape files byte for byte, the reviewer persona,
the hooks, the output style, and the fanout workflow
among them. No activation of the preserved shapes
inside a Qwen session is shown, and the extensions
list for that install names the skill and the agent
only, so file carriage is the whole of what the
record proves for those shapes.

Runtime invocation stays UNVERIFIED. No authenticated
Qwen session was run in the round 33 test, so no
claim is made that a Qwen session invokes the
installed skill or runs extract.py through it. The
scoped npm route stays UNTESTED. Publishing a scoped
package is an outward publication this round does not
perform, so no registry install is claimed. The input
shape conformance is noted only, because the package
carries plugin.json at its root as the primary page
requires.

The Qoder installs also added a hidden
`.claude-plugin/plugin.json` artifact, beside the
retained Qoder manifest and the created
qwen-extension.json. That artifact is an installer
mirror of the input manifest. Its fields are the
fields the input carried, three in the round 33
input, being name and version and description, and
five in the round 37 input, the same three beside an
author object and license. It carries no skill
content, and it is not a second skill. A top level
listing hides it, so any future conversion diff must
include hidden files.

Derives from the round 33 conversion test recorded in
this brief and from the primary Qwen extension
introduction page at
qwenlm.github.io/qwen-code-docs/en/users/extension/introduction
read on 2026-10-24.

### R8. The bundled CLI version

The latest entry on the primary GitHub QwenLM
qwen-code releases listing read on 2026-10-24 states
the bundled CLI version line in these words. This SDK
release bundles CLI version 0.26.0. The fetched
listing text shows no tag beside that entry, so no
tag is claimed for it in this brief. An npm view of
the CLI package also returns 0.26.0, which supports
the listing line but is not release page proof on
its own. The conversion test in this brief ran the
0.26.0 CLI from a scratch install with no global
install.

Derives from the primary GitHub QwenLM qwen-code
releases listing at github.com/QwenLM/qwen-code/releases
read on 2026-10-24.

### R9. The conditional publication draft

This brief reads as a conditional draft. It describes
only routes the primary extension page shows, namely
a GitHub repo install, a marketplace source add, a
scoped npm package, a Qoder plugin, an Agent Plugins
v1 package, and the Discover tab fed by Claude
marketplaces. It promises no central Qwen marketplace
submission and no approval path, because no such path
appears on the primary extension page. VS Code
Marketplace publication is not Build 15 publication,
because the Companion is an IDE product and not CLI
skill presence. The conditional publication decision
stays with David.

Release asset shapes beyond the introduction page
stay UNVERIFIED. The linked releasing page returned
an error when opened in round 33, so no branch shape
and no archive shape is promised in this brief.

Derives from the primary Qwen extension introduction
page at
qwenlm.github.io/qwen-code-docs/en/users/extension/introduction
read on 2026-10-24, and from binding decision 26
which keeps the conditional publication decision with
David.

### R10. The watch items and the limits of this round

No Qwen listing file ships in this round and no Qwen
listing version exists for the version check to
check, as stated at the head of this brief. The repo
version stays 1.3.0.

Copilot dates are watch items only in this round. No
Copilot doc changes land in round 33 for the
November 16 retirements or the Teams legacy dates,
and no October 19 code review exclusion is copied
onto the November 16 retirements. The Copilot dates
are rechecked after November 16 and after the
October 22 through October 26 window ends.

Decision 13 stays in its suspended state. No Trae
material lands in this round. No harness work lands
in this round. No release tag is cut in this round.
No Qwen docs snippet of unestablished provenance is
used as evidence in this brief. No Open Code Review
version claim appears in this brief, because no fresh
primary releases read supports one here.

Derives from binding decision 26, from binding
decision 13 in its suspended state, and from the
round 33 audit record.
