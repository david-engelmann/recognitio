# Evals

This directory holds the measurement layer for the recognitio
skill. It exists so the claims in the readme rest on runs that
anyone can repeat, rather than on the unit suite alone. The unit
suite measures the extractor. These files measure the skill.

## Layout

- `tasks/` holds the fixture review tasks for the paired run.
  Each task folder holds the raw diff, the packet and manifest
  the shipped extractor produced for the same change, a sources
  file with the exact contents of both commits, and a planted
  file that names the defects and the grading rule.
- `RESULTS.md` records the paired run, its method and its
  numbers, with the limits stated beside them.
- `PASS-NOTES.md` holds the per pass notes behind the results
  summary, naming who ran each pass, the condition it held and
  what it reported.
- `checksums.json` holds the checksum record the eval
  integrity gate reads. Every artefact file under `tasks/`
  and the results file and the per pass notes and the corpus
  index stand in it by digest, and a deliberate update
  refreshes the record with the write flag of the gate script.
  The record loads through a strict reader that refuses a
  repeated key, and its keys use the forward slash spelling on
  every host.
- `source-anchors.json` holds a digest of each task sources
  file. The anchor stands apart from the checksum refresh, so
  a deliberate sources change moves the anchor first with the
  anchor write flag of the gate script, as its own committed
  step.
- `corpus-coverage.json` holds the cited test names of each
  corpus section. The coverage stands apart from the checksum
  refresh, so a deliberate index change moves the coverage
  first with the coverage write flag of the gate script, as
  its own committed step.
- `tasks/task-06/transcripts.md` holds the full verbatim
  transcripts of the two passes over the replay task, under
  the publication standard that every run from round 6 onward
  keeps its transcript beside its summary. The eval integrity
  gate re-derives the task-06 scores from these transcripts
  and the planted grading rule and fails when the derived
  scores disagree with the recorded summaries.
- `trigger-set.md` holds the saved trigger queries and
  `TRIGGER-RESULTS.md` records how the shipped description
  scored against them.
- `corpus.md` indexes the real failures from the audit cycles
  and maps each one to the regression test or fixture that now
  covers it.

## Runner note

Build a fresh fixture set before a new paired run, so the
packets come from the extractor under test and not from a saved
run. Each task folder carries a sources file that holds the
exact file contents of both commits, so any reader can rebuild
the history from this repo alone. The rebuild runs in five
steps. First make a fresh git repository. Then write the base
files from the sources file and commit them. Then write the
head files over them and commit again. Then take the plain git
diff between the two commits as the raw diff. Then run the
extractor over the same range at its default tiers. Commit
hashes from a rebuild will differ from the saved manifest,
because commit metadata differs, and the file contents and the
diff and the packet sections are what must match. Each task is
a two-commit git history. The first commit is the base and the
second is the change under review. A packet only counts when
its manifest reports verified. The regeneration gate at
`scripts/check_regeneration.py` runs this rebuild on every
check and fails when a shipped packet or manifest has drifted
from what the rebuild produces.

Run the three passes in a fixed order. The raw pass reads only
the diff and writes its findings down. The fair raw pass then
reads the diff plus the list of files the change touches and
writes its findings down. The packet pass then reads only the
packet and writes its findings down. No pass may open the
planted file, and the planted file is opened only after all
three sets of notes exist. Grade each planted defect found or
not found under the rule the planted file states. Run every
pass over the clean control task as well, where the task plants
nothing and every defect a pass reports counts as a false lead.
Write the numbers and the limits into RESULTS.md in the same
change, and write the per pass notes into PASS-NOTES.md in the
same change, naming who ran each pass, the condition it held,
and what it reported.

A pass that wants the whole repo open has left the terms of the
run. The question this eval answers is narrow. It asks what a
reviewer finds from the packet that the same reviewer cannot
find from the raw diff alone, on tasks where part of the damage
lives outside the diff.
