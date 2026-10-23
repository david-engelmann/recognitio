# Review of the round 4 fix change

## Summary

The change closes the round 4 findings. A renamed module is
searched under its old stem, YAML structure stands outside
the copy fence while prose values stay inside it, and a
findings path written with a leading ./ counts once under
its plain spelling. The change also completes the corpus
index with its round 2 section, gives decision 3 an explicit
trigger for a runnable incident suite, records a fresh eyes
rerun of the paired eval, and states where disposition counts
aggregate and when they are read. The verdict is approve
after the one finding below was fixed. That finding was in
the review record itself rather than in shipped behaviour,
and it is counted in the disposition line at the end.

## Findings by severity

### P1

No findings at this severity.

### P2

No findings at this severity.

### P3

- The round 2 section of the corpus index miscounted its own
  records only rows and dropped one incident.
  Evidence. The records only paragraph in `evals/corpus.md`
  at lines 76 to 94 opened with the word six while the
  sentences after it named seven fixes, and the round 2 spec
  finding on the corpus disclosure stood in neither the
  table nor the paragraph.
  Impact. A reader trusting the count would miss one round 2
  incident and the section would fail the completeness claim
  the index exists to carry.
  Action. Fixed in this change. The paragraph now opens with
  the word eight and names the missing disclosure finding
  beside the other seven records only fixes.

## Nits

No nits are carried under the cap.

## What was checked

The review ran on a packet built by the shipped extractor
for the range from the round 4 audited head to the head that
carried the code and docs fixes, before this report and its
one fix were committed. The packet manifest reports verified
and the packet check accepted the packet for that head. The
full diff was read beside the packet, with the code hunks in
the extractor and the copy gate read line by line and the
docs hunks read against the reports they answer. The new
tests for the three code findings were run on the fixed tree
and run again with each fix reverted, and the structure
tests and the findings tests failed on their reverts while
the control tests held. The corpus test names were extracted
from the index and checked against the suite, and every name
cited exists in it.

Findings disposition. Fixed 1. Wrong 0. Intentional 0. Not
worth it 0.
