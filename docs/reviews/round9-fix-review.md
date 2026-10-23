# Review of the round 9 fix change

## Summary

The change hardens the round 8 eval integrity gate against the
four round 9 red team findings, completes the corpus index for
round 8 and adds the round 9 section, and fixes the three
single finding lanes. In detail it adds a task-06 score
re-derivation from its transcript fences and its planted
grading rule, a source anchor record that the checksum refresh
cannot move, a strict JSON reader that refuses a repeated key
in every record the gate trusts, forward slash record keys on
every host, the corpus index under the checksum record with a
per section coverage floor, the completed round 8 corpus
section and the new round 9 section, a rewrite of the tiers
help string as two plain sentences, and a test pinning the
shipped help output against banned marks. It also records
decision 8 in the decisions file, which names the tasks 01 to
05 score distribution as a deliberate residual because those
passes survive only as curated notes. Verdict is APPROVE. The
gate holds at 217 tests with 16 new pinning tests, and every
finding of the round is closed in the tree or recorded as an
open deliberate decision.

## Findings by severity

### P1

None.

### P2

None. The four red team findings are each met in the tree.
R9-RT-01 is met by the task-06 re-derivation, with the tasks
01 to 05 remainder recorded openly as decision 8 rather than
hidden. R9-RT-02 is met by the source anchor record with the
checksum refresh refusing to run while an anchor is stale.
R9-RT-03 is met by the strict reader on every trusted record.
R9-RT-04 is met by the corpus coverage floor with the corpus
index itself under the checksum record.

### P3

None. R9-SP-01 is met by the completed round 8 corpus
section mapping the teardown repair and the narrowed
exemption to their tests, and the round 9 section records its
two record only repairs as uncovered in the open. R9-ST-01 is
met by the rewritten help string and the new pinning test.
R9-EX-01 is met by the as_posix record keys and its pinning
test.

## Nits

None. The change is prose clean under the program copy bar,
checked by an independent codepoint scan of the six touched
prose files with zero hits, and the version surfaces still
agree at 1.3.0 unreleased.

## What was checked

The packet under review is the round 9 fix set on branch
fix/round9-findings. Base is 0d054c1e69efe42d262b23bb0ecd97ccf22eed0e,
the five fix commits run a9af2d6 through f3ecc19, the
CHANGELOG entries land in the commit this review names, and
this review file is the only addition after that commit.
The commands run were `make check` with exit 0 and a suite
line of 217 tests with OK, the eval integrity step green with
the new checks named, and the copy scan over the changed
prose files with zero banned marks. The gate run happened on
the final head of this change.

Findings disposition. Fixed 0. Wrong 0. Intentional 0. Not
worth it 0.
