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

## The stopping rule

Audit rounds run until two consecutive rounds come back dry,
meaning no new finding of any severity in either round. The
program this file serves stops at that point and not before.
After three rounds on one change without convergence the author
rethinks the approach instead of booking a fourth pass over the
same shape.
