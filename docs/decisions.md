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
panel field above it is documented as a Claude Code extension
that other hosts silently ignore or hard fail per their own
rules, which the round 11 external lane records.
