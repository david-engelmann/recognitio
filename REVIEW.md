# Review guidance for this repo

This file says how a review runs here. It names what failure
looks like in this repo, the paths a reviewer may skip, the nit
cap, the evidence every finding owes, and the stopping rule the
audit program runs under.

## What failure looks like

Failure in this repo has one main shape. A verified stamp
standing on content nobody recounted is failure, and so is a
packet that hides a file behind silence. A finding that reports
a defect the packet never held is a packet defect until proven
otherwise, and it gets reported as one.

## Paths a reviewer may skip

- Generated packets and manifests under `evals/tasks/` are
  fixtures. Review the task design and the results instead, and
  regenerate a packet rather than reading a saved one line by
  line.
- Fixture repositories the tests build in temporary directories
  are inputs, not product. The builder code in the tests is the
  reviewable surface.
- The licence file is standard text the repo did not author.

## The nit cap

A review carries at most three nits. A fourth nit means the
weaker ones get dropped, and style-only findings are dropped
rather than posted at all. Nits never outrank a correctness
finding in the report.

## The evidence rule

Every finding names a file and a line as its evidence and says
what breaks because of it. A concern that cannot point at a
line is a question for the author and it is posted as one, not
as a finding.

## The review report shape

A review report opens with a summary and groups its findings by
severity. Every finding carries its evidence and its impact and
closes with an action item. The checked record at the end of the
report also carries a findings disposition count in four parts,
covering how many findings were fixed, how many were wrong, how
many describe behaviour that is intentional, and how many were
not worth the change they asked for. That count is the standing
signal for whether review findings earn their place, and every
report that follows the template adds one more record of it.
The template below is the shape a report follows in this repo.

The counts aggregate in the checked records themselves. No
separate ledger is kept, because a second home for the numbers
would drift from the reports that carry them. A reader who
wants the signal sums the four counts over every report in
the tree that was written from this template. The counts are
read as a signal together at each program refinement round,
which is every fifth round of the audit program, and again at
any release and at the close of the program. A single report
is one observation and says little on its own. The summed
record across the reports since the last reading is what gets
judged, and a rising share of wrong or not worth it findings
is the shape that says the review is spending effort in the
wrong places.

```
# Review of the change under review

## Summary

What the change does and the scope it touches, in plain words.
The verdict, and the one reason that carries it.

## Findings by severity

### P1

- The finding in one line.
  Evidence. The file and line the finding rests on.
  Impact. What breaks because of it.
  Action. The fix, or the decision owed and who owes it.

### P2

- The finding in one line.
  Evidence. The file and line the finding rests on.
  Impact. What breaks because of it.
  Action. The fix, or the decision owed and who owes it.

### P3

- The finding in one line.
  Evidence. The file and line the finding rests on.
  Impact. What breaks because of it.
  Action. The fix, or the decision owed and who owes it.

## Nits

At most three, under the nit cap above.

## What was checked

The packet the review ran on, with its base and head, and the
commands that were run and their exit codes.

Findings disposition. Fixed 0. Wrong 0. Intentional 0. Not
worth it 0.
```

## The stopping rule

Audit rounds run until two consecutive rounds come back dry,
meaning no new finding of any severity in either round. The
program this file serves stops at that point and not before.
After three rounds on one change without convergence the author
rethinks the approach instead of booking a fourth pass over the
same shape.
