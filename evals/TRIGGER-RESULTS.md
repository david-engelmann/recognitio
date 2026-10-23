# Trigger results

This file records how the shipped skill description scored
against the saved trigger set in this directory. The set was
strengthened in round 2 and this file records the round 2 runs
and the round 3 held out run that settled the proposal. The
round 1 runs over the earlier set are history now, and the
outcome they recorded was 19 of 20 by majority verdict with
query 11 as the one misroute.

## Method

The set holds twenty queries. Ten should trigger the skill and
ten are near misses that should not. The near misses in this set
are genuinely confusable with the work the skill does. They ask
for a merge verdict, for fixes driven by a packet, for tests of
a function a packet names, for a plain words account of a
change, for a merge once a packet checks out, for a summary
drawn from a packet, for findings ranked from a packet, for a
pull request with its diff attached, for text extraction from a
PDF, and for a slide deck built on a packet. The labels were
fixed before any scoring pass ran.

Two independent passes scored the strengthened set. The first
pass was judged by the round 2 fix lane from the shipped
description alone, and its verdicts were written down before
the second pass ran. The second pass was judged by a model
outside this repo and outside this program, reached through
the OpenRouter API as openai/gpt-4o-mini at temperature zero,
given the shipped description alone and the twenty queries in
a shuffled order with no labels. Agreement between the passes
is reported beside each score, because two judges who disagree
are evidence about the description and not noise to average
away.

The winner discipline stands. No description change is applied
without a winning scored run, meaning repeated fresh passes on
data the proposal was not written against. A single strong pass
for a proposal is evidence for it and nothing more.

## Outcome

The first pass scored 20 of 20. Every should trigger query
routed to the skill, and every near miss routed away, query 11
included.

The second pass scored 13 of 20. On the should trigger group it
scored 8 of 10. It missed query 2, which asks to pull the diff
for the feature branch for review, and query 8, which asks to
build the pericope and uses the in house name an outside judge
cannot know. On the near misses it scored 5 of 10. It routed
query 12 on fixing findings, query 14 on explaining a change,
query 15 on merging after a packet check, query 16 on
summarising from a packet, and query 17 on ranking packet
findings to the skill.

The two passes agree on 13 of 20 queries, and they disagree
on exactly the seven queries the second pass got wrong. The
gap between the passes is the honest headline of
this round. A judge who knows the boundary the skill body
draws routes these queries cleanly, and a judge who holds only
the description routes review shaped work to the skill about
half the time, because the shipped text invites pulling a diff
for review and says nothing about judging, fixing, ranking or
merging.

## Proposed tightened description

The proposal below adds one boundary sentence to the shipped
description and changes nothing else. It was recorded in round
1 and it is still a proposal. It is not applied in this change.

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

The same outside judge scored the proposal once, under the
same conditions as the second pass above, and it scored 19 of
20. Its only miss was query 8 and the pericope name. That pass
is evidence for the proposal and not a shipped result, and the
proposal was written against the old set, so this set is not
held out data for it. The proposal should win repeated fresh
passes before anyone applies it, and this round applies
nothing.

## Round 3 held out run

The proposal text above was frozen as written before this run
began, and it was not edited afterwards. A fresh held out set
of twenty queries was written after the freeze. No query in
the held out set appears in the saved trigger set in this
directory, and the near misses are packet adjacent work of the
same confusable kind as the strengthened set. The labels were
fixed before any scoring pass ran.

The held out should trigger queries ask to gather a diff with
the functions around it, to bundle branch commits into a
packet with their callers and tests, to rebuild a packet after
an amend, to pull a single commit with its enclosing
functions, to confirm a packet holds every file and hunk, to
assemble a change with its history for reviewers, to package a
pull request with the test files that touch it, to rebuild a
packet after a rebase against the previous reviewed revision,
to collect a hotfix range with the definitions of the names it
changes, and to prepare an evidence pack with blame and prior
work. The held out near misses ask to judge which findings in
a packet are blockers, to approve a pull request, to write
review comments from a packet, to patch the bug a packet
points at, to draft release notes from a packet, to stamp a
change as reviewed, to explain a packet in plain language, to
write tests a packet calls for, to cherry pick the commits in
a packet, and to turn packet findings into ranked tickets.

Three passes scored each description. Every pass was judged
by the outside model from round 2, openai/gpt-4o-mini through
OpenRouter at temperature zero, given nothing but the
description under test and the twenty queries in a shuffled
order with no labels. The three passes used three different
shuffles. The winner discipline for this run was fixed before
the scores were read. The proposal would be applied only if
it outscored the shipped description in total across the
three passes and lost no single pass.

The shipped description scored 19 of 20 in the first pass,
19 of 20 in the second pass, and 20 of 20 in the third pass,
for a total of 58 of 60. Its misses were the release notes
near miss in the first pass and the local clone pull request
query in the second pass. The proposal scored 20 of 20 in
every pass, for a total of 60 of 60. The proposal won two
passes and tied the third and lost none, so it met the
discipline and it is applied to the skill file in this
change. The shipped description the passes scored against is
the text the proposal section above was written against, and
the applied text is that proposal word for word.
