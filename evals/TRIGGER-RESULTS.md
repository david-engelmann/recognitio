# Trigger results

This file records how the shipped skill description scored
against the saved trigger set in this directory.

## Method

The set holds twenty queries. Ten should trigger the skill and
ten are near misses that should not. Each query was judged three
times against the shipped description, in three separate passes
over the set in different orders, and the majority verdict of
the three passes is the recorded verdict for the query. A query
counts as a misroute when its majority verdict disagrees with
its label in the set. The threshold set before scoring was that
the description stands when at most one query misroutes and the
misroute shows no pattern, and it gets a proposed replacement
when any misroute repeats across a class of near misses.

The weakness of the method is stated plainly. One judge ran all
three passes, and that judge wrote the set, so the passes are
repeated but they are not independent in the way passes by
different judges or by a live router would be. The numbers
below measure whether the description reads as routing these
queries correctly. They do not measure a production router, and
a future run with fresh judges could move them.

## Outcome

The queries that should trigger the skill scored 10 of 10 in every pass. Every
phrasing that asks for extraction, a packet, a re-review after
new commits, or a completeness confirmation routed to the skill
under the shipped text.

The near misses scored 9 of 10. Nine routed away from the skill
in every pass, including the two word collisions on extract and
on review. One query misrouted by majority. Query 11, which
asks for a review of a pull request and a merge verdict, routed
to the skill in two of three passes, because the description
invites pulling a diff for review and says nothing about the
boundary the skill body draws, where assembling evidence is
this skill and judging the change is not. The third pass routed
it away and flagged it as the borderline case of the set.

The total is 19 of 20 by majority verdict. The threshold holds,
and the single misroute still earns a proposal, because it sits
exactly on the boundary the skill cares most about.

## Proposed tightened description

The proposal below adds one boundary sentence to the shipped
description and changes nothing else. It is a proposal recorded
here and flagged in the pull request that carries this file,
and it is not applied in that pull request, because a new
description should win its own scored run before it ships.

Proposed text. Extracts the changes from a pull request, a
commit range, or a single commit and assembles them with their
surrounding context into one verified packet, so a review can
start from evidence instead of a bare diff. Use it when someone
asks to extract changes, pull a diff for review, prepare a
review packet, re-review a change after new commits, or confirm
that everything in a change is present before review begins.
The skill assembles evidence only. It does not conduct the
review itself, judge whether a change is safe to merge, or fix
findings.

Judged against the same set in one further pass, the proposal
routes query 11 away from the skill and moves no other verdict,
for 20 of 20 on that single pass. That pass is evidence for the
proposal and not a shipped result, and the proposal should be
scored three times by fresh passes before anyone applies it.
