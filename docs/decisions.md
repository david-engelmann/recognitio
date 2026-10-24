# Decisions

Design decisions that depart from the research sketch the skill was
commissioned from are recorded here, with the reason for each one.
The sketch lives outside this repo. This file is the in tree record
that the departures were chosen and not lost.

## 1. The packet is two files

A run writes one packet document and one manifest, and the tiers are
sections of the document. This supersedes the directory of tier files
in the sketch.

The reason is loading. One document arrives in one read, in tier
order, and a reviewer or an agent lane never has to assemble the
record from parts. The manifest stays a single receipt that a script
can check on its own, which is what the packet check does.

## 2. Whole function context instead of a fixed radius

The change tier carries whole enclosing function context and no fixed
line radius or hunk fusion. This supersedes the stated radius in the
sketch.

The reason is fidelity. A fixed radius cuts functions at arbitrary
lines and fusion hides where one hunk ended and the next began.
Whole function context matches what a careful reviewer opens by
hand, and the zero context diff still runs underneath for counting.

## 3. The evaluation corpus is deferred

The corpus of real pull requests from the design sketch, with
findings measured per tier per token, is not built yet.

The reason is order. A corpus measured against an extractor that
could silently drop files would certify the wrong thing. The
extractor and its gate had to be trustworthy first. The corpus
belongs to a later cycle, and this note is its placeholder so the
deferral stays visible.

The deferral condition has now expired, recorded on 2026-10-23.
The extractor hardening it waited for has landed and so has the
promotion to the working branch, and the corpus exists in its
first form as an index at `evals/corpus.md`, mapping each audit
incident to the regression test or fixture that now covers it.
The paired evidence the sketch called for lives at
`evals/RESULTS.md`. A corpus that runs as its own suite can still
follow when a round needs one.

A further note recorded on 2026-10-23 in round 2. The concrete
path from the index to a runnable corpus runs from any index row
to the regression test it names, and that test is part of the
suite the gate runs, so the corpus already runs on every gate
invocation in that form. A separate runnable incident suite that
replays the incidents as skill tasks stays deferred, and its
reason is duplication. Such a suite would rebuild the same
fixture histories the regression tests already build and grade
the extractor a second time, while the skill outcome measurement
belongs to the paired eval layer that now carries a clean task
and published run notes. A future round that needs findings per
tier per token can lift the incidents into tasks then, using the
tests and fixtures the index rows point at.

A further note recorded on 2026-10-23 in round 4. The deferral
above now carries an explicit trigger instead of an open ended
one. The incident rows lift into a runnable suite at the first
of three events. The first event is a provider adaptation build
whose brief needs the corpus rows as runnable skill tasks for its
evidence, because such a build gains a consumer that runs the
suite on purpose. The second event is the
opening of any round whose brief asks for findings measured
per tier per token, because that measurement needs tasks to
run the skill against and the index rows are those tasks in
waiting. The third event is the close of this audit program
under its stopping rule, if neither earlier event has fired
by then, because a deferral that outlives the program that
recorded it would leave the lift to chance. The reason for an
event based trigger rather than a date is that the cost the
round 2 note names is duplication, and duplication is only
worth paying when a consumer exists or when the program ends
and the record must stand on its own.

A further note recorded on 2026-10-23 in round 12. The first
event above is amended through the plan-round10 section 7
routing, and now reads as a provider adaptation build whose
brief needs the corpus rows as runnable skill tasks for its
evidence. The reason is that ruling 1 cancelled the standalone
tool outright, so the event as written could never fire, while
a provider adaptation build that needs incident replay tasks as
its eval evidence is the consumer this program can actually
produce. The second and third events stand unchanged. The
shorthand at evals/corpus.md that names the first event as a
standalone tool decision now defers to this amended wording,
and the corpus file itself is untouched by this round.

## 4. Enforcement ships as a script and as prose

Packet enforcement ships as the packet check script in this repo
plus the workflow steps in the skill text. Hooks belong to the
plugin layer, and plugin packaging is deferred by an earlier
decision.

The reason is reach. A script any agent can run today enforces the
rule in every environment the skill runs in, while a hook would
only exist where a plugin host loads it. When packaging lands, the
hook can call the same script and the rule does not move.

Packaging has now landed, recorded on 2026-10-23. The plugin
manifest and the marketplace listing live under `.claude-plugin/`
and enforcement stays script first, exactly as this decision
promised. No hook ships yet, and when one does it will call the
same packet check script and the rule will not move.

## 5. The smoke fixture stays independent

The smoke script builds its own small fixture history rather than
reusing the fixture the unit tests build.

The reason is diversity. Two independent fixtures mean a defect in
one cannot hide inside the other. The smoke history has the same
shape as the test history, with a module, a caller and a test file,
and the smoke asserts companion and history content, not only a
verified flag.

## 6. Generated files and lockfiles are placeholdered, never dropped

A file the extractor detects as generated or as a lockfile keeps its
place in the change tier as a named placeholder, with its lines and
hunks counted in the manifest and its name and reason in the packet
header.

The reason is the founding rule of the project. Nothing leaves the
packet silently. The reviewer trades the noise of a generated diff
for a receipt that names what was withheld and proves the counts
still cover it.

## 7. Main is the working branch

Recorded on 2026-10-23. Work branches off `main` and pull requests
target `main`, and release tags are cut from `main` by David
alone. The `dev` branch is vestigial and carries history only.

The reason is a ruling by David on 2026-10-22. The branch
ceremony that moved `main` only through promotion pull requests
cost an extra landing for every change and bought no safety the
gate and the reviews do not already give, so the ceremony was
dropped on the same evening the promotion it governed landed.
This decision supersedes the branch flow the repo opened with.

## 8. The eval gate re-derives the task-06 scores and leaves the tasks 01 to 05 distribution to the totals check

Recorded on 2026-10-23. The eval integrity gate derives the
task-06 raw and packet scores from the transcript fences, the
planted grading rule and the rebuilt artefacts, and fails when
the derived scores disagree with the recorded sentences in the
results file and the per pass notes. The gate does not derive
scores for tasks 01 to 05, because their passes survive only as
curated notes and a parser over that prose would manufacture
confidence the record does not carry. A moved score
distribution over tasks 01 to 05 that keeps every total and
every headline true still passes the gate after a checksum
refresh, and that residual stands here in the open as the
deliberate limit of the check rather than as a hidden gap.

The reason is evidence. Task-06 is the one task with verbatim
transcripts beside its summaries, so its scores can be tied leg
by leg to the words the passes actually wrote. The earlier tasks
have no transcript to tie to, and the round 9 red team proved
the gap is real by moving two cells with the totals unchanged.
Recording the limit beats pretending the totals check sees
what it cannot see.

A further note recorded on 2026-10-23 in round 11. The fixture
integrity counterpart to the residual above now lands. The gate
runs a planted defect anchor for each of tasks 01 to 04, probing
the rebuilt head for the effect each planted file describes, and
a clean behavior anchor for task-05, the clean control, pinning
its documented behavior instead of a planted defect. A sources
tamper that drops a defect fails the anchor even after the
documented anchor move and checksum refresh. The score
distribution residual above stands unchanged.

## 9. Build 1, the skill frontmatter control panel

Recorded on 2026-10-23 in round 11. The skill frontmatter gains
the Claude Code extension fields the round 11 external lane
graded from the primary docs, and nothing else. `context: fork`
runs the skill in an isolated subagent, because packet assembly
does git reads and file writes that should not pollute the
review conversation, and `background: false` keeps the run
synchronous so the reviewer waits for the packet instead of
racing it. The skill text accounts for the fork, and a forked run
returns only the packet directory, the manifest's verified flag,
and the base, head, and merge base refs, while the reviewer opens
the packet file itself for the evidence.

Five fields stay unset on purpose, and each omission is a limit
stated here rather than a promise. `disable-model-invocation`
stays at its default false, because setting it true changes the
trigger mechanism the description protocol tests. `paths` stays
unset, because review requests span every file and the primary
docs promise only narrower auto activation, not a smaller skill.
`arguments` stays unset, because the skill takes its inputs from
the invoking message and declaring placeholders without using
them would be a dead control. `model` and `effort` stay unset,
because a model pin names a moving target the retirements keep
moving, and both fields are silently not used when the session
or the organization does not support them.

Two carve outs to the description protocol follow from the field
grading. A future change that sets `disable-model-invocation`
to true, or that sets `paths` to narrow auto activation, counts
as a trigger surface change and reruns the full trigger protocol
with two judge families, because the skill the model can no
longer auto invoke is not the skill the protocol tested. The six
Agent Skills spec fields remain the portability floor, and every
panel field above it is documented as a Claude Code extension.
What other hosts do with an unrecognized frontmatter field has
no primary source on record, so the record treats it as unknown.
Hard fail is documented only on Anthropic's own distribution
paths, meaning the claude.ai upload, the Skills API, and the
packaging path, which the round 11 external lane records.

## 10. Build 3, the packet output style

The plugin ships the review packet as an output style under
`output-styles/packet.md` at the plugin root, declared in both the
plugin manifest and the marketplace entry with `force-for-plugin`
set to true. The style is a second spelling of the packet the
extractor writes, and the boundary of decision 4 does not move.
Format is not enforcement. Every enforcement claim stays on the
deterministic scripts and the skill workflow steps, and the style
carries no instruction beyond the canonical skill text. A host
that ignores the style falls back to the prose packet, which
enforces every guarantee unchanged.

The style shows its derivation in the open. Its derivation
section names `.agents/skills/recognitio/SKILL.md` as its only
source, and the gate pins the guarantee sentences against that
text, checks the style's heading list against the extractor's
headings, and fails any style sentence that is not a sentence
the canonical text carries. The `force-for-plugin` spelling and
its true value are pinned, because the host ignores a
misspelling in silence.

The style's reach is stated as a limit. It reaches the main
conversation and the forked extraction run, because the skill
runs its extraction in a fork and a fork inherits the session
style. It does not reach other subagents, which run their own
system prompt. Enabling the plugin overrides the output style
chosen in the user's own settings, and when another enabled
plugin forces its own style and loads first, that style wins.
The README discloses all of this.

The style path joins the instruction name set. A change to the
style steers the next agent that loads the tree exactly the way
the flagged names do, so the extractor flags it in triage and
in the manifest, and the copy fence scans the plugin directory
by rule.

Recorded on 2026-10-23 in round 17. The plugin agent files
join the same set. A change to a file under the plugin root
`agents/` folder steers the session agent's system prompt,
which is the same steering with higher privilege under the
manifest `settings` key, so the extractor flags it the way
decision 10 flags the style. The rule mirrors the style rule,
root level and Markdown only, because no primary source
covers a deeper `agents/` folder as a plugin surface. The
round 17 red team demonstrated the gap live with a planted
system prompt widening the extractor did not flag, and the
regression test carries that plant.

## 11. Build 4, the headless print mode CI shape

Recorded on 2026-10-23 in round 14. The unattended review shape
runs `claude -p` with `--output-format stream-json`,
`--permission-mode dontAsk`, and `--permission-prompts none`,
with the packet piped in so the run needs no file read
permission, and `--json-schema` carrying the findings schema.
The gate script at `scripts/check_headless.py` reads the
stream's final result message and the run's exit code and fails
the run closed on the first problem it names.

The denial signal is primary sourced. The headless docs page,
in the section on turning off permission prompts in
unattended runs, says denials appear as `permission_denied`
system messages and the final result message lists them in
`permission_denials`. The round 14 external lane read the page
before that text landed and filed R14-EX-01 against the plan's
wording, and the page gained the text the same day, so the
build keeps the signal and cites the page. Denial detection is
the exit code plus the result message parsing, meaning a
nonzero exit fails the run, a non empty `permission_denials`
list fails the run, and a missing `structured_output` field
fails the run, because the docs say a run that ends without
valid structured output carries no such field and an in run
failure prints as the result on stdout, so exit zero is not
proof of a clean run.

The findings must match the schema the doc pins, and every
evidence path a finding cites must stand in the packet
manifest's file list, because a run with missing evidence must
never read green. A pass verdict beside a non empty findings
list fails too, because the two contradict each other. The
check cannot run a live host on the gate box, so its
adversarial pass runs against fixtures, and the doc says so in
the open. Decision 4 still binds the shape. The headless run
is a review consumer of the packet, and no model judgment in
it replaces a script check.

## 12. Build 16, the ZCode plugin build, posture reversed

Recorded on 2026-10-23 in round 16 under the retrospective
correction convention. The round 15 plan proposed this change
and the round 16 fix lane records it. The "plugin on hold"
posture is withdrawn, because the ZCode plugin API is now
fully primary documented. The build ships recognitio as a
ZCode plugin with the manifest at
`.zcode-plugin/plugin.json`, the flat skills layout, and a
custom marketplace through a GitHub repo carrying
`marketplace.json`. The brief respects the format limits, a
1024 character description cap and 100KB body truncation, and
notes that ZCode preloads the Claude Code marketplace and
reads `.claude-plugin/plugin.json` as a fallback. The trust
posture the plan already required stands unchanged. The data
upload controversy means the trust text must be explicit that
the skill is local git only and exfiltrates nothing.

## 13. Build 18, the Trae skill build, condition lifted

Recorded on 2026-10-23 in round 16 under the retrospective
correction convention. The round 15 plan proposed this change
and the round 16 fix lane records it. The round 15 research
primary confirmed Agent Skills support in Trae CLI and IDE,
so the condition lifts and the build proceeds as documented.
Global skills live at `~/.traecli/skills`, project skills at
`.traecli/skills/`, IDE skills at `.trae/skills/` and
`~/.traecn/skills`, with `SKILL.md` carrying name and
description frontmatter, plus auto skills from
`.agents/skills`.

## 14. Build 5, the plugin reviewer persona as the main thread

Recorded on 2026-10-23 in round 16. The plugin ships an agent
file at `agents/reviewer.md`, declares it under the `agents`
key of the plugin manifest, and names it as the session
agent under the manifest `settings` key, exploiting the host
`agent` key the round 15 research confirmed on the primary
plugin components page. The persona changes the persona and
not the tool access. The precedence rules are written as
host behavior and the cannot widen statement sits on the
persona side, per the round 16 spec finding. The gate pins
the manifest keys, the agent frontmatter field by field,
and forbids a tool allowlist and a permission mode as
defense in depth, and the sentence discipline reaches the
persona prose. The brief lives at
`docs/reviewer-persona.md`. Decision 4 binds the build like
every other build. The `disable-model-invocation` field
stays at its default false, so scheduled runs through
`/loop` keep working.

## 15. Build 6, dynamic workflows for review fan out

Recorded on 2026-10-23 in round 17. The review fans out one
reviewer per file group with an adversarial second pass,
exploiting the `multiagent_20261001` default the round 15
research confirmed on primary, with subagents and workflows
both enabled by default, and schema validated JSON findings
through `claude -p --json-schema`, which returns structured
output in the `structured_output` field.

The runbook at `workflows/review-fanout.md` orders three
phases. The extractor builds a verified packet and
`scripts/check_packet.py` validates it before any reviewer
spawns. One reviewer per group returns structured output
against the findings schema at
`workflows/findings.schema.json`. The adversarial second
pass re reads every finding, confirms or contests each one
with cited evidence, and raises what the first pass missed
as new findings. Groups may overlap, and findings merge by
the identity of file, line, and rule.

Decision 4 binds the build. The run record validator at
`scripts/check_fanout.py` gates the stamp after the second
pass, and no model judgment replaces it. The validator
proves coverage group by group, proves the merge deduped,
requires an evidenced verdict for every finding, and pins
the concurrency caps at or under the primary numbers, 16
concurrent locally and 64 on managed runs with 1000 agents
started per run. A run may use fewer agents and never more.

Three platform limits are recorded, all read on primary.
The 64 figure carries the platform's own note that the API
does not guarantee the number, so the caps are planning
numbers. A run can create more than one thread for the same
piece of work, so the dedupe rule is the answer to the
double count. A run can end completed even though work on
its threads failed, so the validator proves coverage
instead of trusting the run's end state.

Skill tightness holds. The runbook, the schema, the
validator, and the shipped proof run under
`workflows/proof-run/` live outside the canonical skill
text, and the description protocol is untouched. The proof
run shows overlapping groups, a merged finding, a
contested finding, and a planted defect the first pass
missed and the second pass caught, and the gate validates
it on every run.

## 16. Build 7, the Claude Code mod with in process hooks

Recorded on 2026-10-23 in round 18. The mod gates the
reviewer fan out at spawn time, exploiting the Mods
surface the round 15 research confirmed on primary. The
hooks module at `hooks/register.js`, named by
`hooks/hooks.json`, registers one hook on the
`agent.spawn` event. The hook reads the review packet
manifest named by `RECOGNITIO_PACKET_DIR` and denies the
spawn unless the manifest reads verified, applying the
shipped deterministic rule and never a model judgment.
The registration carries a `.catch` handler returning
the deny shape for `agent.spawn`, so a hook crash fails
closed. The brief at `docs/mod-build7.md` records the
second layer fail open as a stated limit. If the catch
handler itself throws or times out, the host skips the
hook as if it had no handler and the spawn proceeds.

The brief strikes the `onFailure` language as a category
error and the `--mod` flag as withdrawn, and narrows the
`agent.spawn` claim to model choice and deny, which is
what the primary Mods reference documents. Prompt
rewriting by the hook stays unverified. The hook sees
only in session agent spawns. Reviewers the runbook
starts as `claude -p` subprocesses stay gated by
`scripts/check_fanout.py`. When mods are disabled or
unavailable, the mod never loads and the packet scripts
gate unchanged, which is the decision 4 degradation.
The mod leaves `disable-model-invocation` at its default
false with no deny rule, so scheduled `/loop` runs keep
working. The deployment gate is `claude plugin validate
--json` with its `gatingHooks` `hasCatch` flags, and the
host side test story is `claude plugin test` running the
`*.test.ts` files under `hooks/`. Where the CLI is
absent, `scripts/check_mod.py` pins the same contract
deterministically in the repo gate.

Skill tightness holds. The mod, its tests, and the brief
live outside the canonical skill text, and the
description protocol is untouched.

## 17. Build 8, the Agent Plugins 1.0.0 portable package

Recorded on 2026-10-23 in round 19. The package at
`agent-plugins-package/` carries only the portable core, the
manifest at `agent-plugins-package/plugin.json` and the skills
tree at `agent-plugins-package/skills/`, against the Agent
Plugins Specification v1.0.0 the round 19 spec lane read on
primary.

The manifest schema is closed. Section 5 permits exactly the ten
top level fields `$schema`, `name`, `version`, `description`,
`author`, `homepage`, `repository`, `license`, `keywords` and
`extensions`, with the canonical `$schema` value
`https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`.
The repo native manifest keys `agents`, `settings`,
`outputStyles` and `skills` are unknown top level fields under
that schema, and a conformant client must ignore them without
assigning them semantics, so reusing them would silently drop
the persona, the session agent setting, the forced output style
and the hook wiring. The portable manifest carries none of them
at the top level, and the gate fails any top level field outside
the permitted set. That is the inversion guard the spec lane
named, the portable package that silently drops the native
enforcement, closed before it could land.

The Claude Code native shapes ride as per platform extensions
beside the portable core under the section 8 mechanism. Build 8
uses the repo root representation for the shape files and the
extension manifest data representation to declare them. The
shapes do not move into the package. The agent persona at
`agents/reviewer.md`, the output style at
`output-styles/packet.md`, the mod hooks at `hooks/hooks.json`
and `hooks/register.js`, the headless runbook at
`docs/headless-review.md` with `scripts/check_headless.py`, and
the fan out workflow at `workflows/review-fanout.md` with
`workflows/findings.schema.json` stay where the home platform
install expects them, and the portable manifest declares each
one under the `com.anthropic.claude-code` reverse domain
namespace, with the native install path named at
`.claude-plugin/plugin.json` and
`.claude-plugin/marketplace.json`. The gate resolves every
declared path in the repo. The mod hooks cannot ride in the
portable core at all, because version 1.0 defines exactly two
component types, skills and MCP servers, so the extension
mechanism is the only honest ride for them.

Recognitio ships no MCP servers, so the package omits
`mcp.json`, which section 6 permits. The gate pins the omission,
so a later edit cannot quietly add a server the trust text never
approved.

The package skill at `agent-plugins-package/skills/recognitio/`
is a second spelling of the canonical skill at
`.agents/skills/recognitio/` by construction, because section 6
fixes skill discovery at `skills/` with one immediate child
directory per skill. The canonical is the only spelling that
ever changes, and the gate pins the package copy byte identical
to the canonical on every run, file by file across the whole
skill tree.

The package does not install natively in Claude Code on current
evidence. No primary source puts Claude Code among the
implementing hosts, and the brief at
`docs/agent-plugins-brief.md` states the negative plainly with
the gate pinning the sentence. The brief keeps the two
governances distinct. The Agentic AI Foundation governs the
Agent Skills standard, and the Agent Plugins project is governed
separately under its own Technical Charter. The 70 plus platform
integrations are Agent Skills integrations, not Agent Plugins
implementing hosts.

Decision 4 binds the build. The package is a packaging format
with no execution or enforcement semantics, and enforcement
stays on the shipped scripts and the per platform extension.

Skill tightness holds. The package, its gate script at
`scripts/check_package.py`, and the brief live outside the
canonical skill text, and the description protocol is untouched.

## 18. Build 9, the Codex review rules package

Recorded on 2026-10-24 in round 21. The brief at
`docs/codex-review-brief.md` exploits OpenAI's custom code
review rules surface, the primary codex-plugin-cc Stop gate
with its usage loop warning, and the dedicated cloud
environments reference. The rules section states seven rules,
and every rule carries a derivation note naming the canonical
skill section or gate it restates or the primary OpenAI
citation it reports. A rule with neither is a rival instruction
source and fails the round, which is the second packet guard
the round 20 plan named. The gate at `scripts/check_codex.py`
pins the notes, so a later edit cannot add an underived rule in
silence, and the restraint test runs against the rules
directly, with no invented finding, no claimed schedule, and no
claimed coverage surviving.

The brief rests the Security Cloud surface on the three primary
citations. Scheduled scans through the GitHub Actions page with
the cron plus max cost budget, one time scans, and continuous
commit monitoring with the scan window, threat model scoping,
pause, and resume. It states the no product native calendar
schedule negative plainly. Continuous monitoring covers the
default branch only, and a completed scan and complete coverage
are separate claims, so exit 0 does not mean every file was
reviewed. The two pauses are named separately, the per
repository monitoring pause or enable toggle in Monitoring
settings and the automatic pause when funding is unavailable.
The model pins are dated and scoped to the surface they were
read from. The Actions example defaults to gpt-6-sol at
action-v0.3.0, the workbench recommends gpt-5.6-sol with xhigh
reasoning effort, and CLI 0.161.0 made GPT-6.1 Sol the default
model. The 98 percent rule guided against 58.3 percent baseline
figures are flagged as OpenAI's on OpenAI's tasks. Codex Cloud
Legacy is described as under active restriction with no
retirement date promised, as a watch item for the external lane.
The Guardian auto review keys, the review_model key, and
project_doc_max_bytes at 32768 are primary on the
configuration reference and the sample config, read on
2026-10-24. The brief folds in the openai/codex-security CLI
and SDK material, the bulk scan CSV schema, the exit code
contract, the deep mode knobs, the policy command, and the
ghcr.io image, the PR review artifact layout with the sealed
scan manifest receipt and coverage.json, the threat model draft
and edit loop, and the CI example with the same repo guard.
SECURITY.md is policy context, not executable instructions.
The Codex max diff size stays unfound on primary and is not
load bearing.

Decision 4 binds the build. The rules advise and never
enforce, and enforcement stays on the shipped scripts and the
per platform extension.

Skill tightness holds. The brief, its gate script at
`scripts/check_codex.py`, and its tests live outside the
canonical skill text, and the description protocol is untouched.

## 19. Build 10, the Cursor plugin

Recorded on 2026-10-24 in round 22. The brief at
`docs/cursor-plugin-brief.md` exploits the Cursor Plugin
manifest at `.cursor-plugin/plugin.json` with its packaging
rules, the six component set using the primary term Agents, the
Bugbot rules in `.cursor/BUGBOT.md` with the effort levels, and
the second rule surface at `.cursor/config/bugbot.yaml` with its
precedence order, distributed through the manually reviewed
Cursor Marketplace.

The plugin ships the manifest, the README, the skill as a real
directory copy under `skills/recognitio/`, and one rule file
under `rules/`. It ships no agents, no commands, no MCP servers,
and no hooks. The reviewer persona stays a Claude Code plugin
agent, so the Cursor plugin carries no second persona. The
plugin copy is real files because Cursor skips a symlink that
points to a plugin repository elsewhere on disk, and the gate
verifies the copy is a real directory and byte identical to the
canonical skill. This box has no Cursor client, so the real
client run is owed and recorded as the honest limitation. The
duplicate skill residual stays UNVERIFIED at primary, and the
standing guidance is unchanged. Never ship two separate copies
of the same skill.

The Bugbot surface pins the round 22 findings. Effort level is a
Teams dashboard setting billed from prepaid credit, and no
`bugbot.yaml` field pins it. Smart effort does not read the PR
description, labels, or BUGBOT.md when it chooses a level.
Findings default to neutral, so a gate built on Bugbot must
enable fail on unresolved where available and must never read
neutral as a pass. The shipped `bugbot.yaml` sets
`autofix.mode` to `disabled`, the only documented repo field,
because Autofix is model judgment in place of script
enforcement. Unknown fields fall back silently down the
precedence order, so the gate rejects them. The platform
provided `${CURSOR_PLUGIN_ROOT}` is exempt from the manifest
variables schema checklist item, which covers user set values
only. Marketplace update review latency has no stated SLA and is
carried as an unbounded risk. The prebuilt canvases ride as an
optional mention, not a packaged component.

Decision 4 binds the build. The plugin and the Bugbot rules
advise and never enforce, and enforcement stays on the shipped
scripts.

Skill tightness holds. The brief, its gate script at
`scripts/check_cursor.py`, and its tests live outside the
canonical skill text, and the description protocol is untouched.
