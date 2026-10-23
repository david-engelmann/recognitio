# Paired eval results

This file records paired runs of the recognitio skill. The same
fixture review tasks were reviewed under three input conditions.
One pass held only the raw diff. One pass held the raw diff plus
the changed file list. The other pass held only the recognitio
packet for the same change. The planted defects were graded the
same way in every pass.

## Method

Each of the first four tasks plants two defects. One defect sits
inside the diff itself, so either pass can find it from the
change alone. The other defect lives in an unchanged file that
the change breaks, so it can only be found with evidence about
that file, and it counts as found only when the pass names that
file and the exact place in it. A generic warning that some
caller somewhere might break does not count, because a reviewer
cannot act on it.

The fifth task is a clean control. It plants no defect at all,
so every defect a pass reports on it is a false lead, and the
false lead count is the number of defects the pass claims.

The original raw pass read only the diff.patch file of each
task. The fair raw pass read the diff.patch file plus the list
of files the change touches, so it knew the diff it held was
complete and no changed file was hidden from it. The packet
pass read only the packet.md file of each task, and every
packet in this run was produced by the shipped extractor and
carries a verified manifest. The planted.md file of each task
was opened only after the passes had written their notes.

## Numbers

| Task | Planted | Raw diff pass | Packet pass |
| --- | --- | --- | --- |
| task-01 | 2 | 1 | 2 |
| task-02 | 2 | 1 | 2 |
| task-03 | 2 | 1 | 2 |
| task-04 | 2 | 1 | 2 |
| Total | 8 | 4 | 8 |

Across the four tasks the raw diff pass found 4 of 8 planted
defects and the packet pass found 8 of 8. On the four defects
that sit inside the diff the passes tied at 4 of 4 each. On the
four defects that live in unchanged files the raw diff pass
found 0 of 4 and the packet pass found 4 of 4. The delta this
skill claims is the second row of that split, and the measured
delta in this run is four findings on four tasks.

The fair raw pass found the same 4 of 8. It tied the packet
pass at 4 of 4 on the defects inside the diff and it found 0 of
4 on the defects in unchanged files, exactly as the original
raw pass did. The construction limit is stated plainly for
both raw conditions. A raw pass holds no content from any
unchanged file, and the changed file list names no unchanged
file, so under the grading rule above an unchanged file defect
is unreachable by construction in either raw condition. The
fairer condition removes the doubt about whether the diff was
truncated. It cannot remove the absence of the evidence the
packet exists to gather.

On the clean task every pass claimed no defect. The raw pass,
the fair raw pass and the packet pass each recorded a false
lead count of zero on the one clean task in the set. One clean
task cannot carry a false lead rate anyone should quote, and
the count is recorded as a starting measurement rather than a
rate.

## Findings by task

task-01 D1 sits in shop.py, which calls the priced function with
two arguments after the change gives it a third required one.
The raw pass warned that unnamed callers would break. The packet
pass named shop.py line 5 and test_calc.py line 5 from the call
sites section. D2 is the doubled tax term in the changed return
line, and both passes found it.

task-02 D1 sits in test_parse.py, which expects a ValueError for
bad input the change now answers with None, and in server.py,
which passes the result on unchecked. The raw pass noted the
behaviour change without a place to act on. The packet pass
named both files from the companion tier. D2 is the plus one in
the changed return line, and both passes found it.

task-03 D1 sits in legacy.py, which still defines the old helper
name with the old hyphen behaviour after the rename. The raw pass
could not see the file at all. The packet pass named it from the
definitions section. D2 is the deleted separator in the changed
return line, and both passes found it.

task-04 D1 is the import cycle the change creates with data.py,
which already imports the changed module. The raw pass could
only guess at the other half of the cycle. The packet pass named
data.py line 1 from the call sites section and held the new
import in the imports section, so both halves stood on the page.
D2 is the trailing space and case change in the returned string,
and both passes found it.

task-05 plants nothing. The change adds the add_tax helper in
util.py and updates its one caller in page.py with the right
arguments, and test_util.py still calls the unchanged add
function it always called. The raw pass and the fair raw pass
read the diff and found no defect, and the packet pass read the
packet, saw the surviving add definition beside its test file
calls, and found no defect. No pass claimed a finding, so the
false lead count for the task is zero under all three input
conditions.

## Run notes

The original paired run over tasks 01 to 04 was run by the
round 1 fix lane on 2026-10-23. Its method was the two pass
method the head of this file describes in its original form.
The raw pass read only each diff file and the packet pass read
only each packet file, the notes were kept during that run,
and the planted file of each task was opened only after both
sets of notes existed. One reviewer ran both passes and graded
both passes.

The round 2 runs were run by the round 2 fix lane on
2026-10-23. The fair raw pass over tasks 01 to 04 read each
diff file plus the changed file list for the task and graded
its findings under the same rule as the original run. All
three passes over task-05 read their inputs in the same fixed
order, raw first and fair raw second and packet last, and
graded the task under the clean control rule above. The
round 2 lane had read the planted files of tasks 01 to 04 in
the audit record before it ran, so the round 2 passes are a
protocol demonstration graded under the stated rule rather
than blind evidence, and the numbers they produced agree with
the construction limit stated above rather than adding new
weight to the original run. The task-05 passes were run by the
lane that designed the task, which is the weakest form of the
clean control measurement, and the file says so in the open so
a later round can rerun it with fresh eyes.

## Limits

This is a small run and its limits are part of the result. Five
tasks and eight defects cannot carry a rate anyone should quote
beyond this repo, and one clean task cannot carry a false lead
rate at all. One reviewer ran both original passes and graded
both passes, so the grading is not blind and the passes are not
independent in the way a two-reviewer study would be. The tasks
were designed around the packet strengths, because the point of
the run is to measure the claimed delta, and a task set built
from ordinary review work would show a smaller one. The packet
pass also read more text than the raw pass on every task, so
part of the delta is simply that more evidence was on the page,
which is the product working as designed and also the reason
this run measures this skill on its own terms rather than
against every other way of gathering the same evidence. The
corpus index in this directory is the path to a harder set,
because it encodes failures nobody designed for this tool.
