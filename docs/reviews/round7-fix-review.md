# Review of the round 7 fix change

## Summary

The change closes the round 7 findings. The manifest
conflict gate now follows the host on a missing strict key
and reads the experimental object of an entry for the whole
conflict field set, the instruction file flag covers the
path specific Copilot instructions files and the Claude
rules files, the skill file size guard counts bytes beside
characters, the re-review verdict rests on the content
change of the anchored lines with line endings normalised
away, and the stateful YAML reader of the copy fence stands
as named helpers under the recorded function ceiling with
an AST test pinning that ceiling. The changelog states the
shipped manifest rule and the corpus index completes its
round 6 section and gains a round 7 section. The verdict
is approve with no findings, and the disposition line at
the end records that count.

## Findings by severity

### P1

No findings at this severity.

### P2

No findings at this severity.

### P3

No findings at this severity.

## Nits

No nits are carried under the cap.

## What was checked

The review ran on a packet built by the shipped extractor
for the range from the round 7 audited head to the head
that carried the code and docs fixes, before this report
was committed. The base of that range is
`d34f0d59434e21cf32d6df81bdc0536fef3cf7b6` and the head is
`1d01323887183a1a3cb8519e9fd6a12cedec9f18`. The extractor
command `python3 skills/recognitio/scripts/extract.py`
with that range exited 0 and wrote a packet with 10 files
whose manifest reports verified true. The packet check
command `python3 scripts/check_packet.py` run against
that packet exited 0 and reported the packet verified for
the current head. The full gate command `make check` run
on that head exited 0 with 199 tests. The new tests for
the strict states and for the experimental home and for
the byte size guard and for the line endings verdict were
each run in a scratch worktree with their fix reverted and
each failed on the reverted shape and passed again when
the fix was restored. The refactored YAML reader was run
against the reader it replaced over 26 YAML shapes and
both readers yielded the same prose on every shape. The
corpus test names were checked against the suite in this
change and every one of the 109 names the index now cites
stands in the suite. The full diff was read beside the
packet, with the code hunks in the extractor and the gate
scripts read line by line and the docs hunks read against
the reports they answer.

Findings disposition. Fixed 0. Wrong 0. Intentional 0. Not
worth it 0.
