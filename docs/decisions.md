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

## 4. Enforcement ships as a script and as prose

Packet enforcement ships as the packet check script in this repo
plus the workflow steps in the skill text. Hooks belong to the
plugin layer, and plugin packaging is deferred by an earlier
decision.

The reason is reach. A script any agent can run today enforces the
rule in every environment the skill runs in, while a hook would
only exist where a plugin host loads it. When packaging lands, the
hook can call the same script and the rule does not move.

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
