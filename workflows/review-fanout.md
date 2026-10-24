# Review fan out, Build 6

This document is the runbook for the Build 6 review fan
out. One reviewer reads each file group, an adversarial
second pass re reads every finding, and a deterministic
validator gates the stamp. The fan out runs on the home
platform, where the `multiagent_20261001` default enables
dynamic workflows, and on Managed Agents. It is a home
platform extension beside the portable core, not a change
to the canonical skill text. Decision 4 binds it like
every other build.

## The shape of a run

A run has three phases. The orchestrator is the session
agent, which may be the Build 5 reviewer persona.

Phase one builds the packet. The extractor assembles a
verified packet from the local clone, and
`scripts/check_packet.py` validates the packet directory.
A run never starts on an unverified packet. When the
packet check fails, the run stops and the failure names
the files or hunks that disagree.

Phase two fans out. The orchestrator partitions the
packet's file list into groups and starts one reviewer
per group. Groups may overlap. Each reviewer reads the
packet and returns structured output through
`claude -p --json-schema` against the schema at
`workflows/findings.schema.json`, which lands in the
`structured_output` field. A reviewer that returns no
valid structured output has its group marked uncovered,
and the run stops.

Phase three is the adversarial second pass. A second
reviewer re reads every finding the first pass raised,
hunting both for findings that are wrong and for defects
the first pass missed. Every finding gets exactly one
verdict, confirm or contest, with cited evidence. A
defect the first pass missed is raised as a new finding
with the full schema shape. The second pass is not a
rubber stamp. A confirm with no cited evidence fails the
run.

The run record validator at `scripts/check_fanout.py`
gates the stamp after the second pass. No model judgment
replaces it.

## Grouping and dedupe

Groups partition the packet file list. The union of the
groups must equal the manifest file list exactly. A file
the groups drop is a packet defect, and a file the groups
add from outside the packet is a scope defect.

Groups may overlap, because some files deserve two
readers. Overlapping groups may raise the same finding
twice. Findings merge by identity, which is the file, the
line, and the rule together. The run record carries the
merged set, with each merged finding naming the groups
that raised it. Two records sharing one identity is a
dedupe failure, and a finding the merge drops is a
coverage failure.

## The second pass contract

The second pass reads every merged finding. For each one
it records confirm or contest with at least one evidence
path that stands in the manifest file list, plus a note
saying what it re checked. A contest must say why the
finding is wrong, with evidence. A new finding the first
pass missed carries the full finding shape from the
schema, including its own evidence.

The validator fails a run where any finding lacks a
verdict, where any verdict lacks evidence, where any
evidence path stands outside the packet, or where a new
finding breaks the schema. A second pass that confirms
everything with empty notes is the rubber stamp the
program hunts, and the evidence requirement is what
catches it.

## Concurrency caps

The caps below are the primary numbers the round 15
research closed. The workflow declares its caps in the
run record, and the validator fails a run whose caps
exceed them.

Local dynamic workflows run 16 agents concurrently, with
1000 agents started per run as the lifetime cap. Managed
Agents runs 64 concurrently, with 1000 started per run, a
24 hour default lifetime, and 10 runs open at once per
session. The 64 figure carries the platform's own note
that the API does not guarantee the number, so the
document records the cap as a planning number and a run
may use fewer threads.

A workflow may always run fewer agents than the caps. It
may never declare more.

## Platform limits the runbook records

Three platform facts shape the validator, all read on
primary. First, a run can end completed even though work
on its threads failed, so the validator proves coverage
thread by thread instead of trusting the run's end
state. Second, a run can create more than one thread for
the same piece of work, so the tools the agents call
must be safe to call twice, and the dedupe rule is the
answer to the double count. Third, the concurrency
numbers are planning numbers the host may undershoot, so
the validator pins them as ceilings, not as promises.

## The run record

The run record is one JSON object. It names the packet
manifest it ran on, lists the groups with their files,
carries each group's structured output, carries the
merged findings with their raising groups, carries the
second pass verdicts, and declares the concurrency caps.
`scripts/check_fanout.py` reads the schema at
`workflows/findings.schema.json` and validates every
finding against it, so the schema file is load bearing.

The shipped proof run at `workflows/proof-run/` shows a
complete record over a fixture packet, with overlapping
groups, a merged finding, a contested finding, and a
planted defect the first pass missed and the second pass
caught. The gate validates the proof on every run.
