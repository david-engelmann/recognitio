# The Build 17 Devin playbook and coordinator build

This document is the brief for Build 17, the Devin playbook and
coordinator build. It exploits the Devin Review surface as a
review advisory layer beside the canonical packet and records
the Devin coordinator surfaces a packet workflow can trigger
or must guard against. Decision 4 binds this build like every
other build. The guidance advises and never enforces.
Enforcement stays on the shipped scripts and on the per
platform extension.

## The second packet guard

Scoped guidance written apart from the canonical skill can
become a rival instruction source, which the plan names the
second packet failure. This brief answers that adversarial
angle with a derivation discipline and a restraint test.
Every Devin rule in the rules section below carries a
derivation note naming the canonical skill section or the
primary Devin citation it reports or the binding decision it
follows. A rule with neither is a rival instruction source
and fails the round. The gate pins the notes, so a later edit
cannot add an underived rule in silence.

The restraint test runs against the rules directly. No rule
may invent a finding, claim a schedule the primaries deny,
claim coverage the primaries deny, or present a Devin
extension as portable Agent Skills core material. The rules
that survive are the ones whose derivation notes check out.

This brief names the Build 6 Claude Code fan out surface
only as a distinct surface. It never cites the Build 6
figures as evidence about Devin, and every Devin Dynamic
Workflows mention in this brief names Devin.

## The Devin rules

### R1. The Devin Review host list

Devin Review runs beside GitHub Enterprise Server and
GitLab and now beside Bitbucket Cloud. A Bitbucket Cloud
review installs its webhooks automatically, and a member
links a personal Bitbucket Cloud account so Devin Review
posts as that member. A host added without its conditions
is an incomplete host claim, so a packet that names
Bitbucket Cloud names the automatic webhook install and
the personal account link beside it.

Derives from the primary Devin recent updates feed at
docs.devin.ai/release-notes/overview, read in the round 30
research sweep, which states the Bitbucket Cloud support
with the automatic webhook install and the personal account
link conditions.

### R2. The code fixed only resolved count

Devin Review analytics count a finding as resolved only
when it was fixed in code, by a later push or by Devin.
Findings dismissed by a reviewer and duplicates no longer
count, so resolved numbers run lower than a dismissal
inclusive count would. A packet that compares Devin
resolved counts across time notes this definition change,
and this brief never presents a Devin resolved count as a
dismissal inclusive count.

Derives from the primary Devin recent updates feed at
docs.devin.ai/release-notes/overview, read in the round 30
research sweep, which states the code fixed only resolved
count definition with dismissed findings and duplicates
excluded.

### R3. Quote in chat and the merge past bypass

Each Devin Review finding carries a Quote in chat button
on its inline comment and in the findings list. A user
whose GitHub account may bypass a repository merge
requirement can merge a blocked pull request directly from
Devin Review after confirming. A packet workflow that
treats Devin Review as read only must not assume the
bypass path is absent, because the bypass surface is a
guard relevant item for any workflow that relies on a
merge requirement holding.

Derives from the primary Devin recent updates feed at
docs.devin.ai/release-notes/overview, read in the round 30
research sweep, which states the Quote in chat surface and
the merge past bypass surface.

### R4. The one off review of the latest commit

A pull request reviewed at an earlier commit with newer
unreviewed commits says the latest changes have not been
reviewed and offers a one off review of the latest commit
without turning on automatic review. Commenting with the
Devin review command on a pull request gets a reaction
when the review starts and a reaction when it completes.
A packet workflow that wants a single review pass takes
the one off review and does not assume a standing
subscription follows it.

Derives from the primary Devin recent updates feed at
docs.devin.ai/release-notes/overview, read in the round 30
research sweep, which states the one off review of the
latest commit without automatic enrollment and the review
command reactions.

### R5. The code scan automation API path

Code scan automations can be created and updated through
the API with a service user API key, where the service
user role needs the relevant scan permission, and not
only from the Automations UI. An automation claim that
names the API path without the service user permission
condition overstates who can run it, so a packet that
triggers a code scan automation through the API names
the permission condition beside the path.

Derives from the primary Devin recent updates feed at
docs.devin.ai/release-notes/overview, read in the round 30
research sweep, which states the code scan automation API
path with the service user permission condition.

### R6. Runtime validation evidence in scan reports

Security scan reports include recorded runtime validation
results and supporting artifacts for open and dismissed
findings at every severity, with dismissed false positives
summarized separately, and the findings API exposes these
results. A packet that consumes Devin scan findings reads
the runtime validation field and must not treat absence
of a validation record as a failed validation, because
absence of a record and a failed validation are separate
states.

Derives from the primary Devin recent updates feed at
docs.devin.ai/release-notes/overview, read in the round 30
research sweep, which states the runtime validation
evidence in scan reports and in the findings API.

### R7. The SARIF 2.1.0 export beside CSV

Code scan findings export as SARIF 2.1.0 from the scan
page export menu and from the findings export API, in
addition to CSV. A packet that already consumes CSV
findings adds SARIF as a second export shape without
changing the finding set, and this brief never names a
different SARIF version or CSV alone as the export shape.

Derives from the primary Devin recent updates feed at
docs.devin.ai/release-notes/overview, read in the round 30
research sweep, which states the SARIF 2.1.0 export shape
beside CSV.

### R8. Repositories and blueprint v3 promotion

Repositories and blueprint endpoints are part of the
stable v3 API, with the v3beta1 paths continuing to work
for existing clients, and repository responses gain a
repo full name field. A packet that cites the v3
promotion carries the v3beta1 continuation note beside
it, because dropping the note turns a promotion into a
replacement claim.

Derives from the primary Devin recent updates feed at
docs.devin.ai/release-notes/overview, read in the round 30
research sweep, which states the repositories and
blueprint v3 promotion with the v3beta1 continuation note.

### R9. Auto scan schedules API general availability

Code scan auto scan schedule routes are generally
available in the v3 org and enterprise APIs. This
general availability is a scan schedules story and stays
separate from the session schedules deprecation in R10,
because merging the two schedules stories is a category
error and a reader must not read the session schedules
deprecation as a scan schedules removal.

Derives from the primary Devin recent updates feed at
docs.devin.ai/release-notes/overview, read in the round 30
research sweep, which states the auto scan schedules API
general availability in the v3 org and enterprise APIs.

### R10. The session schedules deprecation

The session schedules deprecation is dated September 10,
with the devin_schedule Terraform resource deprecated in
favor of devin_automation. Read, update, and delete keep
working for existing schedules, and a converted schedule
GET response points at the replacement automation. No
end date for the migration phase is published, so the
time sensitive flag stays set and no end date is claimed
in this brief. The Automations migration path stays the
documented current surface, and a migrated organization
sees a POST 403 on the old schedules route from
September 24 2026.

Derives from the primary Devin API release notes at
docs.devin.ai/api-reference/release-notes, read in the
round 30 research sweep, which date the session schedules
deprecation to September 10 with no end date published.

### R11. The coordinator surfaces

Devin automations ask structured questions with clickable
choices in their sessions, run their sessions on a shared
Outpost chosen in the automation editor, display schedules
with a start or end date or several times of day or a
bare hourly cadence in plain language instead of raw
RRULE text, and start and manage child Devin sessions
from Linear automations or allowlisted Linear bots. A
coordinator playbook that fans out child sessions from
Linear uses these surfaces together, and no one of them
is a code review result on its own.

Derives from the primary Devin recent updates feed at
docs.devin.ai/release-notes/overview, read in the round 30
research sweep, which states the structured questions,
the shared Outpost runs, the plain language schedule
display, and the Linear triggered child sessions.

### R12. Devin Oncall as an adjacent incident surface

Devin Oncall is generally available as an adjacent
incident surface only, never as a code review result.
Responders watch Slack or Microsoft Teams channels and
PagerDuty incidents and investigate using telemetry
tools, code, deployments, and runbooks, and Oncall
responders and incident investigations can run in Lite
mode. A packet that cites an Oncall investigation cites
it as incident handling, never as a review finding.

Derives from the primary Devin recent updates feed at
docs.devin.ai/release-notes/overview, read in the round 30
research sweep, which states the Devin Oncall general
availability with Lite mode as an adjacent incident
surface.

### R13. Devin Dynamic Workflows as recorded script orchestration

Devin Dynamic Workflows are a recorded, resumable script
orchestration option for structured orchestration, such
as a wide fan out with a combine step or stages whose
prompts are built from earlier results. The enterprise
enablement condition is carried as secondary in this
brief, because a secondary report dated October 13 2026
states that enterprise admins must enable the feature
before their organizations can use it, and the primary
page does not yet state it in the same words.

Derives from the primary Devin advanced capabilities page
at docs.devin.ai/work-with-devin/advanced-capabilities,
read in the round 30 research sweep, which states the
recorded, resumable script shape, with the enterprise
enablement condition marked secondary.

### R14. Targeted plugin saves and reinstall as a new revision

Devin saves a skill, rule, MCP server, or hook into a
specific uploaded plugin by naming it, instead of only
the default one, and updates all files of an already
uploaded plugin, including companion scripts, by
reinstalling it, keeping the plugin version history. A
packet that ships as a Devin plugin names the target
plugin explicitly and uses reinstall for updates, so the
version history stays intact and no update silently
forks the plugin.

Derives from the primary Devin recent updates feed at
docs.devin.ai/release-notes/overview, read in the round 30
research sweep, which states the targeted plugin saves by
naming a specific uploaded plugin and the reinstall as a
new revision keeping version history.

### R15. The Devin skill placement

Devin skills are SKILL.md files at
.agents/skills/skill-name/SKILL.md in the repository,
automatically discovered across connected repositories,
with user trigger and model trigger both enabled by
default. The path coincides with the portable path, but
the discovery behavior and the trigger defaults are
Devin hosting behavior, so a packet that cites this
placement cites it as a Devin surface, never as portable
core behavior.

Derives from the primary Devin docs skills pages at
docs.devin.ai, read in the round 30 research sweep, which
place skills at .agents/skills/skill-name/SKILL.md with
automatic discovery across connected repositories and user
trigger and model trigger both enabled by default.

### R16. Devin Dynamic Workflows scripts in skills and auto suggested content

A Devin Dynamic Workflows script in a skill is a Devin
extension, not a portable Agent Skills core item, so a
packet workflow that moves a skill to another host must
not assume the script travels with it. Auto suggested
skill content passes human curation before entering
packet procedure, because self generated procedure does
not reliably help and an uncurated suggestion must never
become a packet step on its own authority.

Derives from the primary Devin docs skills pages at
docs.devin.ai, read in the round 30 research sweep, which
carry the Devin Dynamic Workflows script in a skill as a
Devin extension, and the SkillsBench self generated record,
which requires human curation before auto suggested content
enters procedure.

### R17. The stacked pull request packet rule

Each stack layer and the integrated whole are verified
separately. A packet that covers a stack verifies every
layer on its own evidence and then verifies the
integrated whole, because a layer that passes alone can
still break the whole and a whole that passes can still
hide a layer that never verified.

Derives from canonical skill, Completeness discipline,
which verifies the whole change, applied per stack layer
and to the integrated whole.

### R18. The AI Scan advisory limit

An AI Scan pass is signal and never a merge gate. A
packet that cites an AI Scan pass cites it as advisory
evidence only, and no workflow in this brief lets an AI
Scan pass satisfy a merge requirement on its own.

Derives from canonical skill, Trust and limits, which
never lets a signal stand as a gate, and the round 30
record that AI Scan stays advisory only.

### R19. The Copilot governance packet rule

Explicit Copilot feature choices are recorded rather
than relying on a default set during the October 22
through October 26 rollout window. A packet workflow
that runs during or after that window records its
Copilot feature choices explicitly, because an
unconfigured setting in that window takes the global
default instead of a choice the packet made.

Derives from canonical skill, Trust and limits, which
records explicit choices rather than relying on defaults,
and the Build 13 global default note in
docs/copilot-sdk-brief.md, which records the October 22
through October 26 2026 global default window with
explicit choices preserved.

### R20. The Fusion chart caveat

The Fusion score claim, where this brief mentions it,
carries the chart caveat and never stands as a top score
claim. The Cognition footnote updated October 19 2026
states that Fusion with Opus 5.5 and GPT-6 Luna scores
68.1 at 31 percent lower cost than Claude Code with Opus
5.5, while the same chart lists Claude Code with Sonnet
5.5 at 68.4, above the Fusion pairing at 68.1. The cost
comparison and the score comparison are separate claims,
and only the cost comparison against Claude Code with
Opus 5.5 is stated in the footnote itself.

Derives from the primary Cognition Fusion post at
cognition.com/blog/local-fusion, read in the round 30
research sweep, which carries the footnote updated
October 19 2026, with the higher Sonnet 5.5 figure from
the same chart carried beside it.

## The Build 17 decision record

Decision 28 records this build. Decision 4 binds this build
like every other build.

## Skill tightness

The brief, its gate script at `scripts/check_devin.py`, and its
tests live outside the canonical skill text under `docs/`,
`scripts/`, and `tests/`. The skill description is untouched, so
the description protocol does not fire. The deliverable remains
the skill. No Devin surface in this brief enters the canonical
skill text, because every Devin mechanic above is Devin
hosting behavior, not portable core procedure.
