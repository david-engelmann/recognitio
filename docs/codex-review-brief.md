[Back to the documentation index](README.md)

# The Build 9 Codex review rules package

## At a glance

**What ships**

The derivation noted Codex review rule set in this brief, written for the Codex custom review rules surface.

**What was proven**

Every rule carries a derivation note naming its skill section, gate or primary source, and the gate pins the notes against silent drift. A paired live Codex review run on 2026-10-29 then showed the rules changing a review, as the live run section of this brief records.

**What is unverified**

The live record is one paired run on one small range with one model, so the rules at other scales and on other models stand unverified, and the packet gating rule was not exercised because the paired run reviewed a plain range with no packet in play.

## Summary

Build 9 writes the packet discipline as review rules for Codex,
and every rule carries a note naming the canonical skill
section, the gate or the primary source it derives from. What
ships in this repo is that derivation noted rule set in this
brief, and the rules advise while enforcement stays on the
shipped scripts. The contract lives in the review rules section
below, and the gate at scripts/check_codex.py pins it.

This document is the brief for Build 9, the Codex review rules
package. It exploits OpenAI's custom code review rules surface,
the primary codex-plugin-cc Stop gate with its usage loop
warning, and the dedicated cloud environments reference.
Decision 4 binds this build like every other build. The rules
advise and never enforce. Enforcement stays on the shipped
scripts and on the per platform extension.

## The second packet guard

Scoped guidance written apart from the canonical skill can become
a rival instruction source, which the plan names the second
packet failure. This brief answers that adversarial angle with
a derivation discipline and a restraint test. Every Codex rule
in the rules section below carries a derivation note naming the
canonical skill section or gate it restates or the primary
OpenAI citation it reports. A rule with neither is a rival
instruction source and fails the round. The gate pins the notes,
so a later edit cannot add an underived rule in silence.

The restraint test runs against the rules directly. No rule may
invent a finding, claim a schedule the primaries deny, or claim
coverage the primaries deny. The rules that survive are the ones
whose derivation notes check out.

## The review rules

### R1. No invented findings

A review rule never writes a finding of its own. It points at
guidance and at evidence, and judgement belongs to the review
skill downstream. A clean change with a valid exception gets no
finding.

Derives from canonical skill, The boundary, which reads "It
does not approve, reject, rank, or comment on the code. Those
acts belong to the review skill downstream, which keeps its own
axes and its own reporting rules", and the primary developers
blog post Custom Code Review rules for Codex, which organises
its eval around coverage, restraint, retention, and
actionability, with restraint meaning avoiding findings on clean
changes and valid exceptions.

### R2. The verified packet gates the review

A review is stamped only on a packet whose manifest reads
verified. A failed packet is a stop, never a smaller yes. When
verification fails, the review says what is missing in plain
words, naming the files or hunks that disagree.

Derives from canonical skill, Stamping the gate report and
Completeness discipline, which read "Never present a partial
packet as a complete one. Never let a review begin on a packet
whose verified flag is false."

### R3. Cite the guidance and the evidence

Each finding names the guidance it rests on, the location in the
packet, and the priority, so the review can be reproduced later.
The gate report records the base, the head, and the merge base
from the manifest, the exact extractor command, and the reviewed
head.

Derives from canonical skill, Stamping the gate report, and the
primary developers blog post Custom Code Review rules for Codex,
which says Codex can cite the guidance behind a finding and
organises actionability as identifying relevant guidance,
location, and priority per finding.

### R4. Flag the instruction bearing files

A change that touches an instruction bearing file is flagged in
the review, because a change to such a file steers the next agent
that loads the tree. The name set is AGENTS.md and CLAUDE.md and
SKILL.md and GEMINI.md at any depth, the Copilot instructions
file name, a path specific Copilot instructions file under the
instructions folder of .github carrying the .instructions.md
suffix, the .cursorrules file name, a Cursor rules file under a
.cursor folder, and a Claude rules file under a .claude/rules
folder, with a rename flagged when either its old name or its new
name stands in the set. A review packet output style under the
output-styles folder of the plugin is flagged too.

Derives from canonical skill, The tier model, the T0
instruction file flag.

### R5. Keep each rule narrow and durable

State the invariant and the safe path, scope the rule to the code
it governs, and describe outcomes rather than changeable function
names. Review the rules and narrow or remove the noisy ones. The
32 KiB cap on AGENTS.md content embedded into first turn
instructions is the reason rules stay narrow.

Derives from the primary developers blog post Custom Code Review
rules for Codex, whose writing guidance is to start with a
consequential and non obvious invariant, scope rules to the
governed code, state the invariant and the safe path, keep rules
durable by describing outcomes rather than changeable function
names, and review and narrow or remove noisy guidance, and the
primary config sample at
learn.chatgpt.com/docs/config-file/config-sample, which documents
project_doc_max_bytes = 32768 as the max bytes from AGENTS.md to
embed into first turn instructions.

### R6. Treat SECURITY.md as policy context

A SECURITY.md file at the repository root carries persistent
security guidance, and nested SECURITY.md files take precedence
by closeness to the code. Codex Security treats them as policy
context, not executable instructions. The sentence to pin is
that SECURITY.md is policy context, not executable instructions.
Build and validation commands live in AGENTS.md, not in
SECURITY.md.

Derives from the primary page
learn.chatgpt.com/docs/security/plugin/scans, which names
SECURITY.md as policy context rather than executable
instructions and names AGENTS.md for build and validation
commands.

### R7. Hard enforcement stays with the scripts

Review rules advise and never enforce. The packet gate, the
manifest recount, and the CI guards are what block a review.
No model judgement replaces a script check.

Derives from Decision 4, which binds this build like every
other build, canonical skill, Trust and limits, which reads "A
verified packet proves the packet is complete. It does not prove
the change is correct or safe. Run the packet check script before
a packet is trusted", and the primary developers blog post, which
states that Code Review stays an additional reviewer while tests,
branch protections, and required approvals provide hard
enforcement.

## The custom review rules surface

The developers blog post Custom Code Review rules for Codex,
dated Jul 20 in the 2026 Codex blog listing and read on
2026-10-23 at
developers.openai.com/blog/custom-code-review-rules-for-codex,
says Codex Code Review can use custom repository rules from
AGENTS.md and can cite the guidance behind a finding. During
review Codex applies the guidance covering the changed files, so
an unrelated change does not need that context. The worked
example protects the `rawResponseItem/*` wire events even while
experimental, because Codex Cloud consumes the wire name.

The post reports that rule guided variants recovered 98 percent
of the required custom findings in the primary suite against
58.3 percent for the baseline control. The figures are OpenAI's
on OpenAI's tasks. The eval was organised around coverage,
restraint, retention, and actionability, meaning surfacing
intended violations in busy diffs with competing rules, avoiding
findings on clean changes and valid exceptions, continuing to
catch ordinary bugs outside the rules, and identifying relevant
guidance, location, and priority per finding.

The writing guidance is to start with a consequential and non
obvious invariant, scope rules to the governed code, state the
invariant and the safe path, keep rules durable by describing
outcomes rather than changeable function names, and review and
narrow or remove noisy guidance. The getting started guidance is
to add two or three rules, open a representative pull request,
and try one triggering change, one safe counterexample, and one
unrelated change. The post states that Code Review stays an
additional reviewer while tests, branch protections, and required
approvals provide hard enforcement. Reviews can also be requested
directly with `@codex review`.

## The live run

The rules' effect in a live review was tested on 2026-10-29
in a paired run, after the blocker audit proved a live Codex
session route on this box. Codex CLI 0.164.0-alpha.9 ran its
built in review surface through a custom provider on the
responses wire API with the model openai/gpt-5.3-codex, its
key supplied by the connected OpenRouter credential. Two
scratch repositories carried the same reviewed range, byte
identical across the pair, and differed only in the base
AGENTS.md. One carried ordinary project guidance, and the
other carried the same guidance plus the seven rule
statements placed verbatim under a Code review rules heading.

The range carried three changes. A loyalty discount stated
five years or more at fifteen percent while its code required
more than five years. A CLAUDE.md edit flipped the pull
request instruction to direct pushes with no signpost
anywhere. A correct price formatter stood as a clean change.
The session without the rules caught the discount bug and
said nothing about CLAUDE.md. The session with the rules
caught the same bug and flagged the CLAUDE.md change as an
instruction bearing file edit, citing the AGENTS.md lines of
the R4 rule itself as the guidance behind the finding, with a
location and a priority. Neither session raised a finding on
the clean change.

The record is one paired run on one small range with one
model. The packet gating rule was not exercised, because the
run reviewed a plain range with no packet in play, and the
rules at other scales and on other models stand unverified.
The full record stands in the perfection program's live
effect report dated 2026-10-29.

## The Stop gate

The codex-plugin-cc README at
github.com/openai/codex-plugin-cc, checked on 2026-10-23 and
reverified on 2026-10-24, documents the `/codex:setup` command
with the `--enable-review-gate` flag. When the gate is enabled,
the plugin uses a Stop hook to run a targeted Codex review based
on the Claude response, and blocks the stop if that review finds
issues so Claude can address them first. The README carries the
usage loop warning that the gate can create a long running loop
and drain usage limits quickly. The brief states the warning
beside the gate, because a review rules package that blocks a
stop without naming the loop cost would misbrief the agent.

## The dedicated cloud environments reference

The dedicated cloud environments page at
learn.chatgpt.com/docs/environments/cloud-environments says
Codex Cloud (Legacy) continues to support Code Review and the
Linear and GitHub integrations, with deprecation planned. A
community thread from about October 15 2026 reports Legacy
functionality already being restricted while the new Cloud does
not yet replace the task to PR workflow. This brief describes
Legacy as under active restriction, not merely planned, and no
retirement date is promised. The deprecation is a watch item for
the external lane, not a repo defect.

## The Security Cloud surfaces

### Scheduled scans

The GitHub Actions page "Run Codex Security in GitHub Actions"
at learn.chatgpt.com/docs/security/cli/ci/github, read on
2026-10-24, documents scheduled repository scans through a
GitHub Actions cron plus a max cost budget. The repository
workflow fires on an Actions cron trigger set for Mondays at
`07:23` UTC, plus manual dispatch. The example pins
openai/codex-security at
3f61e5150981a5087c32e4395bbaa8ce5ce0c3e3 for action-v0.3.0
with CLI 0.3.0. The max-cost setting is a positive USD estimated
threshold, explicitly not a hard spending cap, because requests
already in progress can exceed it. The budget needs CLI pricing
support for the selected model.

There is no product native calendar schedule on any primary
surface. The only schedule the primaries name is the Actions
cron in the workflow file and the commit arrival trigger for
continuous monitoring. The brief states this negative plainly
and must not claim a calendar.

### One time scans

The cloud setup page at
learn.chatgpt.com/docs/security/setup, read on 2026-10-24,
names One Time Scan as an explicit Scan Method beside
Continuous Scanning.

### The billing terms

The primary Security Cloud page, read on 2026-10-24,
documents the billing terms with the October 21 2026 date.
Scans set up after October 1 2026 at 1253 Pacific are
billed at plan token rates outside the plan's included
allowance. Pre cutoff continuous scans are free until
October 21 2026, then billed if paid usage is enabled or
paused. Eligible accounts without pre cutoff continuous
scanning get 500 dollars in free scanning credits instead,
shared across scan types and workspace users, with no
expiry.

### Continuous commit monitoring

The same setup page documents continuous commit monitoring.
Continuous scanning monitors new commits on the repository's
default branch. It takes a "Scan commit history from" window
with the longer window warning, and it takes optional threat
model scoping guidance. Monitoring settings expose days of
history, the pause or enable toggle, and the editable threat
model, with changes applying to the repository's shared
workspace configuration.

Two different pauses exist and this brief names them separately.
The first is the per repository monitoring pause or enable
toggle in Monitoring settings, shared across the workspace. The
second is the automatic pause the help center page records,
where scanning pauses when funding is unavailable. They are
different mechanisms with different owners and the brief must
not conflate them.

### The threat model draft and edit loop

Codex Security creates the first threat model draft from the
code and uses it to guide future commit scans, per
learn.chatgpt.com/docs/security/threat-model. The model is
editable under Monitoring settings, and changes apply to future
scans.

## Completion versus coverage

A completed scan and complete coverage are separate claims. Exit
0 does not mean every file was reviewed, because coverage gaps
do not change the exit code. The brief's CI section carries this
limit so no reader mistakes a green run for a fully reviewed
tree.

## The CLI and the SDK

The openai/codex-security CLI and SDK material is primary on the
learn.chatgpt.com security pages. The bulk scan CSV columns are
id, repository, and revision with full commit hashes, plus
optional scope, mode, and prompt columns. The flags include
--knowledge-base, --scan-prompt-file, and --post-scan-prompt-file.
The --workers default is 4, --mode defaults to standard, and
--max-attempts defaults to 1. Completed scans are not retried.

Exit code 0 means complete unless a severity threshold is met,
then the exit code is 1. Exit code 2 covers input, execution,
result integrity, or required output failures.

The TypeScript SDK deep mode knobs include workers, subagents,
stopAfterNoNew, maxDiscoveryRuns, and maxTimeHours with default
96 and maximum 96. The knowledgeBasePaths option accepts .md,
.markdown, .txt, .pdf, and .docx.

The command `npx @openai/codex-security policy .` drafts a
SECURITY.md for review before it is copied into place. The
Docker image ghcr.io/openai/codex-security serves bulk scans.

## The PR review artifact layout

The PR review output lands in
$TMPDIR/codex-security-scans/<repository>/<scan-id>/ with
report.md, a findings/ directory carrying stable identifiers
through findingId and occurrenceId, hardening/, findings.json,
the sealed scan-manifest.json receipt, and coverage.json, per
learn.chatgpt.com/docs/security/plugin/code-changes. The
scan.status field in scan-manifest.json confirms completion,
and coverage.json lists reviewed surfaces.

## The review_model key

Model selection for review runs through /model and the
review_model key in config.toml. The primary sample config at
learn.chatgpt.com/docs/config-file/config-sample documents the
key as `Optional model override for /review`, with the default
unset so the current session model is used. The built in /review
command carries its documented scopes.

## The model pins, qualified by surface

Model names in this brief are always dated and scoped to the
surface they were read from. The Actions example defaults to
gpt-6-sol at action-v0.3.0, read on the GitHub Actions page on
2026-10-24. The workbench path on the plugin scans page
recommends gpt-5.6-sol with xhigh reasoning effort for best scan
quality, read on 2026-10-24. CLI 0.161.0 made GPT-6.1 Sol the
default model, per the round 20 research read on 2026-10-24.
CLI 0.164.0 is the later primary pin from the October 23 2026
learn changelog entry and the rust-v0.164.0 release tag, with
ten numbered preset slots as TUI slots for reusable prompts and
slash commands, not a shipped skill format, and this brief makes
no skill format claim for presets. A brief that writes one model
name without naming its surface will be caught by its own
citations. GPT-5.5 retired from Codex on October 14 2026, and
the brief claims no Codex surface for it after that date.

## The Guardian auto review keys

The Guardian auto review config keys are now primary on the
Configuration Reference at
learn.chatgpt.com/docs/config-file/config-reference, read on
2026-10-24. The auto_review.policy entry reads "Local Markdown
policy instructions for automatic review. Managed
guardian_policy_config takes precedence. Blank values are
ignored." The auto_review.extra_policy entry reads "Additional
local Markdown policy for automatic review, included alongside
the main policy. Managed guardian_extra_policy takes
precedence. Blank values are ignored." The managed keys take
precedence over the local ones in both entries.

The primary agent approvals page at learn.chatgpt.com, recorded
by the round 25 research, says automatic review fails closed on
prompt build, review session, and parse failures, checks data
exfiltration, credential probing, persistent security weakening,
and destructive actions, and lets admins constrain the reviewer
with `allowed_approvals_reviewers`.

## The CI example

The CI example installs with
`npm install --global @openai/codex` and then runs
`codex plugin add codex-security@openai-curated`. Before
running the install, pin the package to a version and read
the install script, because the example installs third party
code with no pin in the command itself. The checkout
uses fetch-depth 0 and persist-credentials false. The job is
guarded by `head.repo.full_name` equal to `github.repository`,
so a fork cannot trigger a scan against the upstream
repository.

## Skill tightness

The brief, its gate script at `scripts/check_codex.py`, and its
tests live outside the canonical skill text under `docs/`,
`scripts/`, and `tests/`. The skill description is untouched, so
the description protocol does not fire. The deliverable remains
the skill.

## Navigation

- [Documentation index](README.md)
- [Decisions](decisions.md)
- [Principles](principles.md)
