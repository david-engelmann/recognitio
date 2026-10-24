# The Build 10 Cursor plugin

This document is the brief for Build 10, the Cursor plugin. It
exploits the Cursor Plugin manifest at `.cursor-plugin/plugin.json`
with its packaging rules, the six component set of Rules, Skills,
Agents, Commands, MCP Servers, and Hooks, the Bugbot rules in
`.cursor/BUGBOT.md` with the effort levels, and the second rule
surface at `.cursor/config/bugbot.yaml` with its precedence
order, distributed through the manually reviewed Cursor
Marketplace. The component set uses the primary term Agents, not
subagents. Decision 4 binds this build like every other build.
The plugin and the Bugbot rules advise and never enforce.
Enforcement stays on the shipped scripts.

## The manifest and the six components

A Cursor Plugin has a `.cursor-plugin/plugin.json` manifest. The
six components are Rules for persistent AI guidance and coding
standards in `.mdc` files, Skills for specialized agent
capabilities, Agents for custom agent configurations and prompts,
Commands for agent executable command files, MCP Servers for
Model Context Protocol integrations, and Hooks for automation
scripts triggered by events.

The packaging rules are primary. The manifest name is lowercase
kebab-case and must be unique. Explicit manifest paths replace
folder discovery for that component. Default discovery is
`skills/` with each subdirectory holding a `SKILL.md`, `rules/`
for `.md`, `.mdc`, and `.markdown` files, `agents/`,
`commands/`, `hooks/hooks.json`, and `mcp.json` at the plugin
root. All manifest paths must be relative with no `..` and no
absolute paths. The submission checklist requires local testing,
unique names, valid frontmatter on every component, and a README
documenting usage. A multi plugin repo uses
`.cursor-plugin/marketplace.json` at the repo root, and the whole
marketplace manifest must stay at or under 10 MB.

This plugin ships the manifest, the README, the skill as a real
directory copy under `skills/recognitio/`, and one rule file
under `rules/`. It ships no agents, no commands, no MCP servers,
and no hooks. The reviewer persona stays a Claude Code plugin
agent, so the Cursor plugin carries no second persona. The plugin
carries no `mcp.json`, mirroring the portable package's
documented omission. The duplicate skill residual stays
UNVERIFIED at primary, and the standing guidance is unchanged.
Never ship two separate copies of the same skill.

## The real directory copy

Symlinks in `~/.cursor/plugins/local` load only when the target
resolves to a directory inside that folder. Cursor skips a
symlink that points to a plugin repository elsewhere on disk.
The same page's own test protocol says `Copy your plugin files
into that folder.`

The repo ships its Claude skill as a mode 120000 symlink, which
is the safest known shape for that host, but the Cursor plugin
must not mirror that habit. The plugin's `skills/recognitio/`
directory holds real files, and the gate verifies the copy is a
real directory and byte identical to the canonical skill. A
symlink habit carried into the plugin folder would ship a hollow
plugin that loads nothing, silently.

The honest limitation is recorded here and in the decision
record. This box has no Cursor client, so the real client run is
owed. The protocol is a real directory copy at
`~/.cursor/plugins/local/recognitio`, a window reload, and a
confirm of every component in Customize. The local simulation of
the documented rule in this round's gate is the evidence that
stands in until that run happens.

## The variable contract

Cursor does not expand the standard's `${PLUGIN_ROOT}` and
`${PLUGIN_DATA}` variables in `mcp.json`. Use
`${CURSOR_PLUGIN_ROOT}` for the plugin root. The non expansion
claim is scoped to `mcp.json` on both primary pages, and this
brief does not generalize it beyond that scope.

The silent failure mode is two sided. Writing `${PLUGIN_ROOT}`
leaves a literal unexpanded string in the server path and the
MCP server fails to launch with no complaint about the variable.
Writing `${workspaceFolder}` resolves cleanly to the wrong
directory, because it resolves to the project root and not the
plugin install dir.

The submission checklist requires declaring every `${VAR}` from
`mcp.json` in the manifest `variables` schema, and the docs
describe `variables` as user set values from the dashboard. The
platform provided `${CURSOR_PLUGIN_ROOT}` is not a user set
value, so it is exempt from that checklist item. The fix lane
decision is pinned. Declare only non platform variables in
`variables`, and never declare `${CURSOR_PLUGIN_ROOT}` there.
The plugin ships no `mcp.json` today, so no variable declarations
exist to check, and the gate pins this decision for the lane
that adds one.

## The Bugbot rule surfaces

Bugbot reads `.cursor/config/bugbot.yaml` at the repo root from
the PR's base branch. The precedence order from highest to lowest
is the PR author's personal overrides for their own PRs, then
`.cursor/config/bugbot.yaml`, then team and organization settings
from the dashboard.

The only repo YAML field the primary page documents is
`autofix.mode`, and it can lower the Autofix mode from the
dashboard settings but it cannot raise it. For example, it can
change `Commit to Existing Branch` to `newBranch` or `disabled`,
but it cannot turn Autofix on when the dashboard has it off. The
shipped file sets `mode` to `disabled`. Autofix spawns a Cloud
Agent to repair findings, which is model judgment in place of
script enforcement, so decision 4 keeps it off in this repo.

If a field is missing or invalid, Bugbot ignores that field and
falls back to the next setting in the precedence order. A typo in
a YAML field name degrades silently to the dashboard setting with
no error surfaced to the repo, so the gate rejects unknown fields
instead of trusting Cursor to complain. Bugbot ignores files
larger than 64 KB, and the gate pins the shipped file under that
cap. A secondary analysis claims effort levels can be set per
repository in `bugbot.yaml`. The primary page documents no such
field, the brief follows the primary page, and an unknown effort
field in the shipped file would fall back silently, which is why
the gate rejects it.

## Effort is a dashboard setting

Bugbot Teams includes the ability to set the effort level Bugbot
uses for reviews. It is a dashboard team setting, billed from
prepaid credit. The four effort levels are Low, Default, High,
and Smart, with the stated cost and speed tradeoffs. A brief that
claims `bugbot.yaml` pins High effort would be inventing a
control the primary page does not grant. The honest control split
is BUGBOT.md for review guidance, `bugbot.yaml` for repo settings
with silent fallback, and the dashboard for effort. Smart effort
does not read the PR description, labels, or BUGBOT.md when it
chooses a level, so a team relying on Smart cannot steer the
effort choice through BUGBOT.md.

## The neutral default and the gate trap

The conclusions are verbatim. `success` means Bugbot found no
issues and there are no unresolved Bugbot comments from earlier
runs. `neutral` means Bugbot found issues, the run was cancelled
by a newer commit, or Bugbot hit an internal error, and this is
the default conclusion when Bugbot reports findings. `failure`
means Bugbot found issues and the check is configured to fail on
unresolved issues.

Requiring the status alone does not block merges on findings
because findings default to `neutral`. If fail on unresolved
issues behavior is available for the organization, enable it to
make unresolved findings produce a failing status. A gate that
merely requires the Bugbot check passes merges with open
findings, and the availability of fail on unresolved is
conditional on the organization, so the brief must not assume it
exists on every plan. The separate `Cursor Bugbot Autofix` check
uses only `success` or `neutral`, so requiring that check is
vacuous as a gate. Any story that leans on Bugbot as enforcement
must enable fail on unresolved where available and must never
read `neutral` as a pass.

## The BUGBOT.md caps

Each rule is truncated at 30,000 characters when included in a
review. Every `.md` or `.mdc` file linked from a
`.cursor/BUGBOT.md` file counts as its own rule with its own
30,000 character limit. The combined rules for a review are
capped at 100,000 characters, and anything past the cap may be
omitted. Required team rules are prioritized over non required
rules. The shipped BUGBOT.md stays far under these caps, and the
verbose run flag `bugbot run verbose=true` posts the table of
included rules with truncation flags for verification.

## The review rules

### B1. No invented findings

A Bugbot review never writes a finding of its own. It points at
guidance and at evidence, and judgement belongs to the review
skill downstream. A clean change with a valid exception gets no
finding.

Derives from canonical skill, The boundary, which reads "It does
not approve, reject, rank, or comment on the code. Those acts
belong to the review skill downstream, which keeps its own axes
and its own reporting rules."

### B2. The verified packet gates the review

A review is stamped only on a packet whose manifest reads
verified. A failed packet is a stop, never a smaller yes. When
verification fails, the review says what is missing in plain
words, naming the files or hunks that disagree.

Derives from canonical skill, Stamping the gate report and
Completeness discipline, which read "Never present a partial
packet as a complete one. Never let a review begin on a packet
whose verified flag is false."

### B3. Flag the instruction bearing files

A change that touches an instruction bearing file is flagged in
the review, because a change to such a file steers the next agent
that loads the tree. The name set is AGENTS.md and CLAUDE.md and
SKILL.md and GEMINI.md at any depth, the .cursorrules file name,
a Cursor rules file under a .cursor folder, and a Claude rules
file under a .claude/rules folder, with a rename flagged when
either its old name or its new name stands in the set.

Derives from canonical skill, The tier model, the T0 instruction
file flag.

### B4. Keep every rule inside the caps

Each rule stays under 30,000 characters when included in a
review, and the combined rules stay under 100,000 characters.
The verbose run flag posts the table of included rules with
truncation flags, so a rule that grew past its cap is caught by
inspection.

Derives from the primary Bugbot docs at cursor.com/docs/bugbot,
which state the per rule and combined truncation caps.

### B5. Never read neutral as a pass

Findings default to neutral, so a required Bugbot status alone
does not block merges on findings. The review treats unresolved
Bugbot comments as open work. Any merge gate built on Bugbot must
enable fail on unresolved issues where the organization offers
it, and must never read neutral as a pass.

Derives from the primary Bugbot docs at cursor.com/docs/bugbot,
which state the neutral default conclusion and the fail on
unresolved behavior.

### B6. Hard enforcement stays with the scripts

Bugbot reviews advise and never enforce. The packet gate, the
manifest recount, and the CI guards are what block a review. No
model judgement replaces a script check.

Derives from Decision 4, which binds this build like every other
build, and the primary Bugbot docs at cursor.com/docs/bugbot.

## Distribution

Every plugin is manually reviewed before it is listed. All
plugins must be open source, and we review each update before
publishing.

Reviewed updates auto deploy to clients pinned at the commit
SHA, with no user version pinning, per the Cursor staff post.
The primary pinning half reads `A running Cloud Agent, including
each agent in a Project, keeps the plugin versions it started
with. Start a new agent to pick up an update.`

No primary page states a review duration, so the latency is
carried as an unbounded risk. A plugin fix can sit in the review
queue for an unknown duration while installed clients stay pinned
at the old commit. Update submission is fire and forget with no
delivery promise.

The Security Review bot and the Bot Development Kit stay adjacent
ecosystem, not plugin surfaces. Security Review reads every pull
request and posts one review comment reporting exploitable bugs,
with style and quality staying with Bugbot. Neither is a plugin
component and neither is a packaging surface this brief builds
against.

Plugins now ship with prebuilt canvases, shared setup templates a
team can open and reuse, with Hex Canvas and Atlassian Canvas as
the two named examples. Canvases are setup templates, not review
surfaces, so they ride as an optional mention and not as a
packaged component.

## Skill tightness

The brief, its gate script at `scripts/check_cursor.py`, and its
tests live outside the canonical skill text under `docs/`,
`scripts/`, and `tests/`. The skill description is untouched, so
the description protocol does not fire. The deliverable remains
the skill.
