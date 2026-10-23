# Review of the round 8 fix change

## Summary

The change closes the round 8 findings. A new eval
integrity gate at `scripts/check_evals.py` stands wired
into the check and it pins every eval artefact file under
`evals/tasks/` and the results file and the per pass notes
under a checksum record, checks the results totals against
the per task entries the results table prints, rebuilds
every task diff and manifest from its sources file and runs
the shipped packet checker over each rebuilt packet, and
fails when the corpus index cites a test name the suite no
longer holds. A documented write flag refreshes the
checksum record for a deliberate eval update. The changelog
and the corpus index and the agent notes record the pass.
The verdict is approve with no findings, and the
disposition line at the end records that count.

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
for the range from the round 8 audited head to the head
that carried the code and docs fixes, before this report
was committed. The base of that range is
`e2688f3d4807bed79912287d8261d74850ee5cf8` and the head is
`9cf333a477b78adbd45ca6db9d915951d7ab5ecb`. The extractor
command `python3 skills/recognitio/scripts/extract.py`
with that range exited 0 and wrote a packet with 8 files
whose manifest reports verified true. The packet check
command `python3 scripts/check_packet.py` run against
that packet exited 0 and reported the packet verified for
the current head. The full gate command `make check` run
on that head exited 0 with 207 tests. The three edits the
round 8 red team planted were planted again one at a time
in a scratch copy of that head and the eval gate failed on
each one, naming the task-06 transcripts file and then the
task-02 planted file and then the results file, and the
results cell edit also failed the totals check with the
per task entries adding to 5 against a total row of 4.
The cited test rename the red team planted was planted in
the same copy and the eval gate failed naming
`test_the_real_skill_package_is_valid` as missing from the
suite, and every plant passed again once restored. The
same four plants were planted in a scratch copy of the
round 8 audited head with no eval gate standing in it and
the full gate on that copy stayed green, which is the
pre fix state the new gate answers. The corpus test names
were checked against the suite in this change and every
one of the 117 names the index now cites stands in the
suite. The full diff was read beside the packet, with the
new gate script and its tests read line by line and the
docs hunks read against the reports they answer.

Findings disposition. Fixed 0. Wrong 0. Intentional 0. Not
worth it 0.
