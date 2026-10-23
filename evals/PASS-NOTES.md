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

## The round 4 fresh eyes raw rerun over tasks 01 to 05

The round 4 fix lane ran this pass on 2026-10-23. The lane
did not design any of the five tasks. The pass held only the
diff.patch file of each task and wrote its findings down
before any packet pass ran and before any planted file was
opened for this rerun. The runner had read the results
summary in this directory while reading the tree before the
run, so this rerun stands as fresh eyes on the tasks rather
than as blind evidence, and the findings below are the ones
each input itself supports under the grading rule in
RESULTS.md.

On task-01 the pass found the doubled tax term in the changed
return line of `calc.py` and warned that callers passing two
arguments would break after the signature change. It named no
caller file or place, so the unchanged file defect does not
count as found. On task-02 the pass found the plus one in the
changed return line of `parse.py` and noted that bad input
now returns None instead of raising, with no unchanged file
or place named. On task-03 the pass found the deleted
separator in the changed return line of `util.py` and could
not see the legacy file at all. On task-04 the pass found the
trailing space and case change in the returned string of
`report.py` and could only guess at the other half of the
import cycle, naming no line from `data.py`. The pass
reported 4 of 8 planted defects, all four inside the diff
and none in an unchanged file.

On the clean control task-05 the raw pass claimed no defect.
The new helper takes two arguments and delegates to the
unchanged helper, and the one caller in the diff is updated
with two arguments. The false lead count for this condition
is zero.

## The round 4 fresh eyes packet rerun over tasks 01 to 05

The round 4 fix lane ran this pass on 2026-10-23 after the
raw rerun notes existed. Each packet was rebuilt from the
sources file of its task with the current extractor in the
round 4 fix tree, and every rebuilt packet carries a verified
manifest and a diff that matches the saved diff apart from
index lines. The planted file of each task was opened only
after both sets of rerun notes existed, and grading followed
each planted file strictly.

On task-01 the pass named `shop.py` line 5 and
`test_calc.py` line 5 from the call sites section, each
calling the priced function with two arguments against its
new three argument signature, and found the doubled tax
term. On task-02 the pass named `test_parse.py` lines 7 and
8 expecting a ValueError for bad input the change now
answers with None, and `server.py` line 5 passing the result
on unchecked, and found the plus one. On task-03 the pass
named `legacy.py` line 1 from the definitions section, still
defining the old helper name with the old hyphen behaviour,
and found the deleted separator. On task-04 the pass named
`data.py` line 1 from the call sites section and held the new
import in the imports section, so both halves of the import
cycle stood named, and found the trailing space and case
change. The pass reported 8 of 8 planted defects.

On the clean control task-05 the packet pass claimed no
defect. The packet shows the surviving add definition beside
its test file calls and the updated caller using the new
helper with the right arguments. The false lead count for
this condition is zero, so the clean control reads zero
under both conditions in this rerun.

The rerun totals agree with the numbers in RESULTS.md. The
raw condition found 4 of 8 and the packet condition found 8
of 8, with the split tied at 4 of 4 inside the diff and split
at 0 of 4 against 4 of 4 on unchanged files, and no number in
RESULTS.md moves on this evidence.

## The round 6 passes over the replay task-06

The round 6 fix lane ran these passes on 2026-10-23. The task
is a replay of a real merged pull request, built at fixture
scale from pull request 9 and its finding R4-01, and its
planted file says so in the open. The lane that ran both
passes also built the task, so these passes stand as a
protocol demonstration graded under the rule in the planted
file rather than as blind evidence, in the same terms the
round 2 passes over the earlier tasks record for themselves.
The full verbatim transcripts of both passes stand in
transcripts.md inside the task-06 folder, and this entry is
the summary that points at them.

The raw pass held only the diff.patch file. It found the
doubled subtotal in the changed return line of book.py and
warned that importers of the old module name would break,
without naming any importer, so the unchanged file defect
does not count as found. The raw pass reported 1 of 2 planted
defects.

The packet pass held only the packet.md file, produced by the
shipped extractor with a verified manifest. It named
report.py line 1 importing the old module name ledger after
the triage tier showed that module renamed to book.py, with
test_ledger.py line 1 carrying the same stale import in the
test files section, and it found the doubled subtotal. The
packet pass reported 2 of 2 planted defects.

Task-06 stands as an additional task beside the scored set.
Its numbers join no headline total in RESULTS.md, so the
recorded numbers over tasks 01 to 05 stay reproducible as
they stand.
