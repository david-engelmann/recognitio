# Review of the round 11 fix change

## Summary

The change closes the round 11 findings, clears the round 9 gate
verification debt the round 11 red team opened with, and lands
Build 1, the skill frontmatter control panel. In detail it adds
per task planted defect anchors for eval tasks 01 to 05 in
`scripts/check_evals.py`, hardens the task-06 grader against
note plants that deny imports and against doubled operand
overcounting, scopes the copy fence to sentences and the anchor
pins to effect level, adds the agreement pin regression test,
and corrects the round 9 review record inaccuracies the round
10 plan ordered fixed. The skill frontmatter gains the fork
context field and `background: false`, the skill text accounts for the
forked run with fork evidence accounting, and decisions 8 and 9
record the tasks 01 to 05 score distribution as a deliberate
residual and the five unset frontmatter fields as stated
limits. Verdict is APPROVE.

This record is written retrospectively in round 14 from the
round 11 fix report and the four round 11 audit reports. No
independent re-verification run stands behind it beyond what
the fix report records.

## Findings by severity

### P1

None.

### P2

None. R11-RT-01 is met by the per task planted anchors for
tasks 01 to 04 with the clean behavior anchor for task-05,
beside the documented anchor move and checksum refresh. The
round 9 gate debt R9G-RT-02 is met by the task-06 grader
hardening.

### P3

None. R9G-RT-03 is met by the sentence scoped fence and the
effect level anchors. R10-RT-01 is met by the same hardening.
R10-SF-01 is met by the agreement pin regression test. The
round 9 review record corrections are met by the corrected
record the fix report describes.

## Nits

None recorded.

## What was checked

The packet under review is the round 11 fix set pushed direct
to origin/main per the shipping rule. Base is
830923f9ceb7d6c021c5da9c40cfb42df5c612e3. The pushed head is
48442a14bc9e08fff72d5ffc52c6d9a1ab37c49f, with the mode-only
follow-up restoring the executable bits the Data API push
dropped. The fix report records the planted anchor proof for
R11-RT-01, the revert checks on the new tests, the copy bar
scan with two decisions.md violations caught and fixed before
the push, and the environmental caveat that the full gate
could not run on that lane's box. This retrospective review
raises no finding of its own against the change.

Findings disposition. Fixed 0. Wrong 0. Intentional 0. Not
worth it 0.
