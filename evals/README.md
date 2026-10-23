# Evals

This directory holds the measurement layer for the recognitio
skill. It exists so the claims in the readme rest on runs that
anyone can repeat, rather than on the unit suite alone. The unit
suite measures the extractor. These files measure the skill.

## Layout

- `tasks/` holds the fixture review tasks for the paired run.
  Each task folder holds the raw diff, the packet and manifest
  the shipped extractor produced for the same change, and a
  planted file that names the defects and the grading rule.
- `RESULTS.md` records the paired run, its method and its
  numbers, with the limits stated beside them.
- `trigger-set.md` holds the saved trigger queries and
  `TRIGGER-RESULTS.md` records how the shipped description
  scored against them.
- `corpus.md` indexes the real failures from the audit cycles
  and maps each one to the regression test or fixture that now
  covers it.

## Runner note

Build a fresh fixture set before a new paired run, so the
packets come from the extractor under test and not from a saved
run. Each task is a two commit git history. The first commit is
the base and the second is the change under review. The raw diff
is the plain git diff between those commits. The packet is the
extractor run over the same range at its default tiers, and a
packet only counts when its manifest reports verified.

Run the two passes in a fixed order. The raw pass reads only the
diff and writes its findings down. The packet pass then reads
only the packet and writes its findings down. Neither pass may
open the planted file, and the planted file is opened only after
both sets of notes exist. Grade each planted defect found or not
found under the rule the planted file states, and write the
numbers and the limits into RESULTS.md in the same change.

A pass that wants the whole repo open has left the terms of the
run. The question this eval answers is narrow. It asks what a
reviewer finds from the packet that the same reviewer cannot
find from the raw diff alone, on tasks where part of the damage
lives outside the diff.
