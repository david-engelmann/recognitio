# Per pass eval notes

This file holds the notes behind the summary in RESULTS.md.
Each entry names who ran the pass, the condition the pass held,
and what the pass reported, so a reader can regrade a pass from
the record in the tree rather than from its summary alone. The
grading rule and the limits of every run stand in RESULTS.md
and they govern how these notes read.

## The original raw pass over tasks 01 to 04

The round 1 fix lane ran this pass on 2026-10-23. The pass held
only the diff.patch file of each task and wrote its findings
down before the packet pass ran and before any planted file was
opened. One reviewer ran this pass and the packet pass and
graded both.

On task-01 the pass found the doubled tax term in the changed
return line and warned that unnamed callers would break after
the signature change. It did not name the caller in shop.py.
On task-02 the pass found the plus one in the changed return
line and noted the behaviour change for bad input without a
place to act on. On task-03 the pass found the deleted
separator in the changed return line and could not see the
legacy file at all. On task-04 the pass found the trailing
space and case change in the returned string and could only
guess at the other half of the import cycle. The pass reported
4 of 8 planted defects, all four inside the diff and none in
an unchanged file.

## The original packet pass over tasks 01 to 04

The round 1 fix lane ran this pass on 2026-10-23 after the raw
pass notes existed. The pass held only the packet.md file of
each task, and every packet was produced by the shipped
extractor and carries a verified manifest. The planted file of
each task was opened only after both sets of notes existed.

On task-01 the pass named shop.py line 5 and test_calc.py
line 5 from the call sites section and found the doubled tax
term. On task-02 the pass named test_parse.py and server.py
from the companion tier and found the plus one. On task-03 the
pass named legacy.py from the definitions section and found
the deleted separator. On task-04 the pass named data.py line
1 from the call sites section and held the new import in the
imports section and found the trailing space and case change.
The pass reported 8 of 8 planted defects.

## The fair raw pass over tasks 01 to 04

The round 2 fix lane ran this pass on 2026-10-23. The pass
held the diff.patch file of each task plus the list of files
the change touches, so it knew the diff it held was complete
and no changed file was hidden from it. It graded its findings
under the same rule as the original run.

The pass reported the same 4 of 8. It tied the packet pass at
4 of 4 on the defects inside the diff and found 0 of 4 on the
defects in unchanged files, exactly as the original raw pass
did. The round 2 lane had read the planted files of tasks 01
to 04 in the audit record before it ran, so this pass stands
as a protocol demonstration graded under the stated rule
rather than blind evidence, and RESULTS.md says so in the
open.

## The three passes over the clean control task-05

The round 2 fix lane ran all three passes over task-05 on
2026-10-23 in the fixed order the runner note in this
directory states. The raw pass read the diff first, the fair
raw pass read the diff plus the changed file list second, and
the packet pass read the packet last. The lane that ran these
passes also designed the task, which is the weakest form of
the clean control measurement, and RESULTS.md says so in the
open.

The raw pass reported no defect. The fair raw pass reported
no defect. The packet pass read the surviving add definition
beside its test file calls and reported no defect. The false
lead count for the task is zero under all three input
conditions, recorded as a starting measurement on one clean
task rather than a rate.
