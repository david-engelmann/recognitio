# Review of the round 6 fix change

## Summary

The change closes the round 6 findings. A copied entry no
longer writes re-review ranges under its source path and
findings paths are accounted under one plain composed
spelling, the marketplace entry sets strict to true beside a
gate check on the manifest pair so the plugin loads through
the marketplace route, the copy fence reads YAML structure
by structure while prose values still flag, changed
instruction files are flagged in the triage list and in the
manifest, and the skill file carries a size guard in the
gate. The change also completes the corpus index with its
round 4 and round 6 sections, amends the round 4 review
record with the identifiers its template requires, and adds
a replay eval task drawn from a real merged pull request
with verbatim transcripts beside its summary. The verdict
is approve after the one finding below was fixed. That
finding was in the draft record of the change itself rather
than in shipped behaviour, and it is counted in the
disposition line at the end.

## Findings by severity

### P1

No findings at this severity.

### P2

No findings at this severity.

### P3

- The changelog draft claimed a review report that did not
  stand in the tree yet.
  Evidence. The Added list in `CHANGELOG.md` at lines
  136 to 139 named this report at
  `docs/reviews/round6-fix-review.md` while the reviews
  folder held only the round 4 report at the audit that
  opened this change.
  Impact. A reader trusting the changelog would look for a
  record that did not exist, and the change would carry the
  same kind of unbacked claim this program exists to catch.
  Action. Fixed in this change. The claim was held back
  while the review ran and it returns only in the commit
  that adds this report, so the named file and the sentence
  that names it land together.

## Nits

No nits are carried under the cap.

## What was checked

The review ran on a packet built by the shipped extractor
for the range from the round 6 audited head to the head
that carried the code and docs fixes, before this report
was committed. The base of that range is
`8253d12130a84106f84553b7dae2e58b3154bfc5` and the head is
`803819f043aa8472a96888ab86046fafbf6dd731`. The extractor
command `python3 skills/recognitio/scripts/extract.py`
with that range exited 0 and wrote a packet with 22 files
whose manifest reports verified true. The packet check
command `python3 scripts/check_packet.py` run against
that packet exited 0 and reported the packet verified for
the current head. The full gate command `make check` run
on the tree as this change was adopted exited 0 with 188
tests. The new extractor tests for the copy ranges ran in
a scratch copy with the extractor fix reverted and exited
1 with 7 failures across 8 tests while the no copy control
held, and four new copy fence tests ran in the same
scratch copy with the fence fix reverted and all four
failed. A clean profile marketplace install of a clone of
the fixed head ran under the workspace Claude Code build
at version 2.1.309 and every step exited 0, with the plugin
list showing the plugin enabled and the plugin details
command inventorying the recognitio skill. The full diff
was read beside the packet, with the code hunks in the
extractor and the gate scripts read line by line and the
docs hunks read against the reports they answer. The
corpus test names were checked against the tests this
change adds and every name the new sections cite stands
in the suite.

Findings disposition. Fixed 1. Wrong 0. Intentional 0. Not
worth it 0.
