[Back to the documentation index](README.md)

# The Build 13 Copilot SDK agent build

## Summary

Build 13 builds a Copilot SDK agent as a review advisory layer
beside the canonical packet, and every rule in it carries a
note naming the skill section or the primary citation it
reports. What ships in this repo is that derivation noted rule
set in this brief, and the guidance advises while enforcement
stays on the shipped scripts. The contract lives in the SDK
rules section below, and the gate at scripts/check_copilot.py
pins it.

This document is the brief for Build 13, the Copilot SDK agent
build. It exploits the Copilot code review surface as a review
advisory layer beside the canonical packet. Decision 4 binds
this build like every other build. The guidance advises and
never enforces. Enforcement stays on the shipped scripts and
on the per platform extension.

## The second packet guard

Scoped guidance written apart from the canonical skill can
become a rival instruction source, which the plan names the
second packet failure. This brief answers that adversarial
angle with a derivation discipline and a restraint test.
Every Copilot rule in the rules section below carries a
derivation note naming the canonical skill section or gate
it restates or the primary citation it reports. A rule with
neither is a rival instruction source and fails the round.
The gate pins the notes, so a later edit cannot add an
underived rule in silence.

The restraint test runs against the rules directly. No rule
may invent a finding, claim a schedule the primaries deny,
or claim coverage the primaries deny. The rules that survive
are the ones whose derivation notes check out.

## The SDK rules

### R1. Head branch instructions are untrusted input

Head branch instructions are untrusted input for the review
run. The July 17 2026 head branch change loads head branch
content into the review context, and the primary release
note carries its security note on that behavior. Nothing in
this brief treats head branch content as a trusted source.

Derives from canonical skill, Trust and limits, which keeps
untrusted content outside the packet's verified boundary,
and the primary GitHub release note for the July 17 2026 change at github.blog/changelog/2026-07-17-copilot-code-review-customization-and-configurability-improvements with its security note.

### R2. Merge authority lives in base branch CODEOWNERS and rulesets

Merge authority lives in base branch CODEOWNERS and
rulesets only. A merge approval authored by head branch
instructions carries no base branch merge authority. The
review run advises, and the merge gate belongs to the base
branch controls.

Derives from canonical skill, The boundary, which keeps
judgement with the review skill downstream and never lets
the packet grant merge authority, for the CODEOWNERS and
rulesets half, and the primary GitHub release note for the
July 17 2026 change at
github.blog/changelog/2026-07-17-copilot-code-review-customization-and-configurability-improvements
with its security note for the head branch approval half.

### R3. Never approve on a red packet

An approval never fires on a red packet. A packet whose
verified flag is false is not a packet, and no review
begins on it as if it were whole. This holds for opt in
approvals too, including the ones that count toward branch
protection. An approval firing on an unverified packet and
counting toward branch protection would let unverified
code satisfy the merge gate.

Derives from canonical skill, Stamping the gate report and
Completeness discipline, which read "Never present a
partial packet as a complete one. Never let a review begin
on a packet whose verified flag is false."

### R4. Model pinning stays at capability level

The review model reports as unknown, so model pinning stays
at capability level. No rule in this brief names a review
model for Copilot code review. The October 19 2026 model
deprecation coverage names chat, inline edits, ask and
agent modes, and completions, and does not name code
review, so this brief claims no deprecation for code review
from that entry.

Derives from the primary docs.github.com configure page,
which names no model identity for code review, and the
primary github.blog October 19 2026 deprecation entry,
whose coverage list names no code review.

### R5. Effort levels

Lite is the standard review. Balanced is deeper analysis of
complex logic, security sensitive code, and cross service
changes. Max is coming soon and not available yet. Effort
is independent of the automatic review switch, and
automatic reviews go through branch rulesets with optional
new push and draft pull request switches.

Derives from the primary docs.github.com configure page,
read on October 24 2026.

### R6. Approvals in public preview

Copilot approvals are in public preview and subject to
change. They are off by default, with three approval
levels and up to 15 file path globs per rule, and a count
toward merge toggle. Organization and enterprise policies
govern their availability, with disabled everywhere as the
enterprise default.

Derives from the primary docs.github.com configure page,
read on October 24 2026, which records the Sept 1 2026
preview with the off by default posture.

### R7. Review cost

Review cost is documented on docs.github.com with
attribution rules and budget controls that can block
reviews. The brief reports the cost surface as stated and
invents no pricing of its own.

Derives from the primary docs.github.com review cost
documentation.

### R8. Microsoft Agent Framework integration

The Microsoft Agent Framework integration is stable for
.NET and Python with the AsAIAgent pattern, approval gates,
and the containerized run security recommendation. The
local sandboxing GA in Copilot CLI from the October 9 2026
weekly releases strengthens the containerized run
recommendation.

Derives from the supplementary Microsoft Agent Framework
documentation at learn.microsoft.com, which carries no page
path in this brief, and the primary Microsoft Agent Framework
devblog at
devblogs.microsoft.com/agent-framework/build-production-ready-agents-with-the-github-copilot-harness-and-agent-framework/
which states the integration is stable for both .NET and
Python, and the primary October 9 2026 weekly release notes
at
github.blog/changelog/2026-10-09-github-copilot-weekly-releases-october-5/.

### R9. The code review API surface

Reviews are requestable through REST and GraphQL with an
optional per request effort level. Balanced is the default
for new and existing repos and orgs since September 28
2026, and explicit Lite selections are respected. The API
surface is GA on Pro, Pro Plus, Max, Business, and
Enterprise.

Derives from the primary github.blog October 2 2026 code
review API entry.

### R10. The settings surface

Every Copilot plan carries a dedicated personal settings
page for code review. Enterprise wide default review
effort ships with organization and repository overrides.

Derives from the primary September 23 2026 settings
surface entry at docs.github.com/copilot.

### R11. The improved review experience

The improved review experience brings a refreshed overview
comment with assessment, effort used, and grouped
findings, self auto resolution between reviews, and
generated commit messages for accepted suggestions.

Derives from the primary September 18 2026 improved
review experience entry at github.blog/changelog.

### R12. The retirement wave

Claude Opus 4.8, Claude Opus 5, and GPT-5.6 Terra retire
on November 16 2026, with an individual annual plan
exception for Opus 4.8. This brief claims the retirement
across all GitHub Copilot experiences as the primary entry
states it and no more, and names no code review claim from
that entry.

Derives from the primary github.blog October 15 2026
retirement entry.

### R13. The bot authored pull request surface

The attribution section records the bot authored pull
request surface from the August 27 and September 11 2026
changelog entries, now primary. The Lite ensemble figures
stay vendor reported and are never presented as
independent measurement.

Derives from the primary github.blog August 27 and
September 11 2026 changelog entries, with the vendor
reported caveat on the Lite ensemble figures.

### R14. The usage metrics

The October 22 2026 usage metrics name skill agents and
MCP servers as additive SDK usage metering. The metrics
are client telemetry that undercounts, so this brief
reads them as adoption trends and never as exact
accounting.

Derives from the primary October 22 2026 usage metrics
entry at github.blog/changelog, with the client telemetry
undercount caveat.

## Currency notes

The October 22 through October 26 2026 global default
enforcement window rolls out gradually through October 26
2026. The policy applies to eligible settings on
"Features and clients" and "MCP servers in Copilot".
Eligible features left unconfigured are set according to
the global policy, explicit choices are preserved, and
preview features remain opt in. R9 and R10 state defaults,
so a packet workflow records its Copilot feature choices
explicitly instead of relying on a default set during this
window. The primary entry names no code review policy page,
so this brief names none, and the explicit choice note
above covers the settings on the two pages the primary
names.

Derives from the primary github.blog October 22 2026
global default entry, which names the two pages above and
the explicit choice preservation.

The October 19 2026 model policy API is generally
available, with GET and PATCH endpoints for enterprises,
enterprise teams, agent apps, and organizations.

Derives from the primary github.blog October 19 2026 model
policy API entry.

The October 23 2026 totals by client metrics add a
totals_by_client measure of model traffic from any tool
that uses Copilot, with client values including opencode,
claude_code, codex, zed, copilot_cli, github_app,
cloud_agent, code_review, vscode, and jetbrains. Client
is a best effort grouping, not a verified identity, and
request_count counts model calls, not prompts. Copilot
metrics no longer cover only Copilot surfaces, and this
brief does not describe the October 23 totals as
undercounting on that entry alone, because the undercount
caveat belongs to the October 22 client telemetry entry
at R14.

Derives from the primary github.blog October 23 2026
totals by client entry, which lists the client values and
the best effort and calls not prompts caveats.

The October 23 2026 Teams legacy entry says the legacy
GitHub app will be renamed GitHub deprecated and retired
on November 16 2026.

Derives from the primary github.blog October 23 2026
Teams legacy entry.

Gemini 4 Argon general availability in Copilot is dated
October 13 2026, on Pro Plus, Max, Business, and
Enterprise.

Derives from the primary github.blog October 13 2026
Gemini 4 Argon entry.

## Stated limits

The head branch change record stays current as of the
July 17 2026 primary entry. The November 16 2026
retirement wave shows no movement as of October 24 2026.
Round 32 note, recorded on 2026-10-24. Re-check the
November 16 Copilot model retirements and the Teams
legacy retirement after November 16 2026 against the
primary entries, and re-read the October 22 through
October 26 global default window after October 26 2026,
when that window ends.
The Lite ensemble figures stay vendor reported. The usage
metrics stay client telemetry that undercounts. The
October 19 2026 deprecation coverage never names code
review, and this brief never claims it does.

## Skill tightness

The brief, its gate script at `scripts/check_copilot.py`,
and its tests live outside the canonical skill text under
`docs/`, `scripts/`, and `tests/`. The skill description
is untouched, so the description protocol does not fire.
The deliverable remains the skill.

## Navigation

- [Documentation index](README.md)
- [Decisions](decisions.md)
- [Principles](principles.md)
