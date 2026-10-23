# Paired eval results

This file records a paired run of the recognitio skill. The same
four fixture review tasks were reviewed twice. One pass held only
the raw diff. The other pass held only the recognitio packet for
the same change. The planted defects were graded the same way in
both passes.

## Method

Each task plants two defects. One defect sits inside the diff
itself, so either pass can find it from the change alone. The
other defect lives in an unchanged file that the change breaks,
so it can only be found with evidence about that file, and it
counts as found only when the pass names that file and the exact
place in it. A generic warning that some caller somewhere might
break does not count, because a reviewer cannot act on it.

The raw pass read only the diff.patch file of each task. The
packet pass read only the packet.md file of each task, and every
packet in this run was produced by the shipped extractor and
carries a verified manifest. The planted.md file of each task was
opened only after both passes had written their notes. The notes
themselves were kept during the run and they agree line for line
with the findings table below.

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

## Limits

This is a small run and its limits are part of the result. Four
tasks and eight defects cannot carry a rate anyone should quote
beyond this repo. One reviewer ran both passes and graded both
passes, so the grading is not blind and the passes are not
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
