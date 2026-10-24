# The Build 11 CodeRabbit guidelines build

This document is the brief for Build 11, the CodeRabbit
guidelines build. It exploits the Code Guidelines entry reading
`.claude/rules/` with `paths` frontmatter, pairing the packet
with the autonomous fix loop for the review fix cycle. It
records the rename direction as primary, with Fix comments
formerly Autofix and Autofix formerly Autopilot and compat
aliases kept. It records the focus toggle table as primary and
constrains the brief with it. High trims verbosity. It does not
deepen analysis, and the brief must never treat it as deeper
review. It records the Quiet, Chill, and Assertive profiles as
primary, with the July 2 2026 Quiet launch. It records the pre
merge checks with Error mode merge blocking, the Automatic
Approvals surface, and the approval risk limits as primary. It
records the October 2026 entries as primary, Deep Scan with
linked repositories, the Deep Scan API on all plans, and
`reviews.allow_author_approval`. It records the guideline file
provenance now shown in review summaries, where each file is
listed as configured, auto-discovered, or an Agent Skill.
Decision 4 binds this build like every other build. The
guidelines advise and never enforce. Enforcement stays on the
shipped scripts.

## The second packet guard

Scoped guidance written apart from the canonical skill can
become a rival instruction source, which the plan names the
second packet failure. This brief answers that adversarial angle
with a derivation discipline and a restraint test. Every
guideline in the guidelines section below carries a derivation
note naming the canonical skill section or the primary
CodeRabbit citation it restates or the binding decision it
follows. A guideline with neither is a rival instruction source
and fails the round. The gate pins the notes, so a later edit
cannot add an underived guideline in silence.

The restraint test runs against the guidelines directly. No
guideline may invent a finding, claim a schedule the primaries
deny, claim a deeper analysis the focus table denies, or claim
coverage the primaries deny. The guidelines that survive are the
ones whose derivation notes check out.

## The rename direction

The primary changelog dated October 14 2026 renames two
features so their names match what they do. Fix comments
(formerly Autofix) fixes the review comments you select, as a
one-off repair. Autofix (formerly Autopilot) brings a pull
request to completion, repeatedly fixing review feedback,
CodeRabbit findings, and failing CI checks until the pull
request is ready. The old commands, including the review
commands, keep working as aliases for a limited time for
backward compatibility.

## The focus table as a constraint

On the focus axis, `reviews.focus` takes casual, balanced, or
high and governs review output verbosity through the cumulative
toggle table. The primary focus page defines `high` as paring
reviews down to essential content only, trimming additional
walkthrough and metadata sections on top of the balanced
changes, and hiding several review sections entirely. Higher
levels are cumulative, so `high` applies everything `balanced`
does, plus more. The page's own example caption for high reads
"Strip everything non-essential for the leanest reviews".

One row of the primary focus table turns a setting on at high
rather than off. The `reviews.high_level_summary_in_walkthrough`
setting moves from off to on at high and folds the summary into
the walkthrough. The fold is pinned here explicitly so the high
trims verbosity characterization stays exact and no reader
counts the fold as added analysis.

There is no product native calendar schedule on any primary
CodeRabbit surface, and the brief claims none.

## The two axes

Two separate controls govern how a CodeRabbit review reads, and
the brief never conflates them. The focus control sets review
output verbosity. The profile control sets feedback volume and
scope. A reader who mixes the two will read high as a deeper
review through the assertive profile's wider scope, so each
section opens by naming its axis and the two controls are
never mixed.

## The profiles

On the profile axis, CodeRabbit offers the Quiet, Chill, and
Assertive profiles. The primary changelog dated July 2 2026
launched the Quiet review profile alongside the existing Chill
and Assertive profiles. Quiet keeps the pull request
conversation focused, with only the most important comments
posted inline and every other comment grouped into collapsed
sections in the review summary, so nothing is lost while the
inline noise stays low. The primary configuration reference
defines the three profile values, quiet, chill, and assertive,
as `quiet` for only the most important feedback, `chill` for
balanced feedback, and `assertive` for more feedback, noting
the last may feel nitpicky.

## The pre merge checks

The primary configuration reference defines the enforcement
levels as `off`, `warning`, and `error`. The `error` level
requires resolution before merging. When the request-changes
workflow is enabled, `error` can block the PR until the check
passes. The primary glossary defines the Automatic Approvals
surface. When a review leaves actionable comments, CodeRabbit
submits a Request changes review. Once the required comments are
resolved, the latest commit is reviewed, and pre-merge checks
pass, CodeRabbit approves. Optional risk limits keep pull
requests above a chosen Merge Risk for human approval.

The repo's own `.coderabbit.yaml` sets the pre merge checks to
warning mode, so nothing there blocks a merge. The file's own
comment records CodeRabbit as advisory step 0 in this repo.

The primary changelog dated October 5 2026 adds the security
merge blocking entry. Admins can publish the CodeRabbit Security
check with a severity threshold and require it in GitHub to
enforce merge blocking, and publishing alone does not block.

## The October 2026 entries

The primary changelog dated October 2 2026 adds Deep Scan with
linked repositories, so a scan can take context from linked
repositories to analyze the primary repository more thoroughly.
The Deep Scan linked repository limits are up to 20 linked
repositories subject to the plan linked repository limit.
Essentials supports manual links while Team, Advanced, and
Enterprise also support automatic linking. Linked repositories
provide read only context while findings and coverage remain
attached to the primary repository, so a packet that consumes
Deep Scan findings for a primary repository must not attribute
a linked repository finding to the linked repository itself.
The primary changelog dated October 1 2026 opens the Deep Scan
code findings API on all plans with a non-agentic API key and
the `security:read` permission. The same day's entry adds the
`reviews.allow_author_approval` setting, which defaults to true
and can be set to false to prevent pull request authors from
using `@coderabbitai approve` and `@coderabbitai resolve` on
their own pull requests.

The primary changelog dated October 8 2026 ships CLI v0.9.0
for cloud task work with cr code, including interactive
messages, side questions, plans, and delivery. It completes
shell commands and reads richer review JSON, and it verifies
signed Linux releases and recovers more reliably from login
and update failures. The signed Linux release verification is
the supply chain relevant change for a packet workflow that
installs the CLI.

The Deep Scan runtime verification entry of October 23 2026 is
not recorded here. It is Deep Scan detail rather than a new
surface, and the round 23 fix report records the skip for a
later round.

## The guideline file provenance

The primary changelog dated September 30 2026 lists the
repository guideline files CodeRabbit used for a review in the
review summary, showing for each file whether it was configured,
auto-discovered, or an Agent Skill.

The primary changelog dated October 15 2026 adds `.claude/rules/`
as a fourth guideline source beside the configured, auto
discovered, and Agent Skill files. CodeRabbit now reads Claude
Code rules from `.claude/rules/`. A rule with `paths` frontmatter
applies only to the files those globs match. A rule without
`paths` gets the scope CodeRabbit infers from its content, like
other guideline files. As in Claude Code, `paths` is the only
frontmatter field that affects a rule's scope, and globs in
`paths` are relative to the project root. A matching
`filePatterns` entry with `applyTo` still overrides a rule's
`paths` when needed.

The repo's own `.coderabbit.yaml` pairs through the knowledge
base code guidelines with file patterns on `AGENTS.md` and
`README.md`. The repo ships no `.claude/rules/` directory today,
so the fourth source is documented here but not exercised.

## The guidelines

### G1. No invented findings

A guideline never writes a finding of its own. It points at
guidance and at evidence, and judgement belongs to the review
skill downstream. A clean change with a valid exception gets no
finding.

Derives from canonical skill, The boundary, which reads "It does
not approve, reject, rank, or comment on the code. Those acts
belong to the review skill downstream, which keeps its own axes
and its own reporting rules."

### G2. The verified packet gates the review

A review is stamped only on a packet whose manifest reads
verified. A failed packet is a stop, never a smaller yes. When
verification fails, the review says what is missing in plain
words, naming the files or hunks that disagree.

Derives from canonical skill, Stamping the gate report and
Completeness discipline, which read "Never present a partial
packet as a complete one. Never let a review begin on a packet
whose verified flag is false."

### G3. Flag the instruction bearing files

A change that touches an instruction bearing file is flagged in
the review, because a change to such a file steers the next agent
that loads the tree. The name set is AGENTS.md and CLAUDE.md and
SKILL.md and GEMINI.md at any depth, the .cursorrules file name,
a Cursor rules file under a .cursor folder, and a Claude rules
file under a .claude/rules folder, with a rename flagged when
either its old name or its new name stands in the set.

Derives from canonical skill, The tier model, the T0 instruction
file flag.

### G4. Guidelines pair, they never replace the packet

Guideline files are a review pairing source, never a second
packet. A guideline restates the canonical skill or a primary
citation, and the verified packet's evidence wins every
disagreement. A guideline that invents an instruction the
canonical skill does not carry is a rival source and fails the
round.

Derives from canonical skill, The boundary, which keeps
judgement with the review skill downstream, and the round 20
plan's second packet guard, which names the guard this build
answers.

### G5. Hard enforcement stays with the scripts

Guidelines advise and never enforce. The packet gate, the
manifest recount, and the CI guards are what block a review. No
model judgement replaces a script check.

Derives from Decision 4, which binds this build like every other
build.

## Skill tightness

The brief, its gate script at `scripts/check_coderabbit.py`, and
its tests live outside the canonical skill text under `docs/`,
`scripts/`, and `tests/`. The skill description is untouched, so
the description protocol does not fire. The deliverable remains
the skill.
