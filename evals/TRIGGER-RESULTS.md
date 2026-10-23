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
1 and it was still a proposal when the round 2 section above
was written, and that section applied nothing. Round 3 applied
it, and the round 3 section at the end of this file records
the held out run that settled it.

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
passes before anyone applies it, and the round 2 change that
recorded this applied nothing.

## Round 3 held out run

The proposal text above was frozen as written before this run
began, and it was not edited afterward. A fresh held out set
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

The held out set stands below with the labels that were fixed
before scoring, so this run can be regraded from this file
alone. The per pass verdicts follow the set. Every query a
pass is not recorded as missing was judged correctly in that
pass.

Should trigger. H1 Gather the diff for pull request 482
together with the functions around it so the review can begin
from the full picture. H2 Take the commits on this branch
since the release and bundle them into a single packet with
their callers and tests. H3 We amended the branch again.
Rebuild the packet for the same change so I can check it
against the last reviewed head. H4 Pull out everything that
changed in the last commit, including the enclosing functions,
and lay it out for review. H5 Before anyone starts reviewing,
make sure the packet for this range holds every file and hunk
in the change. H6 Assemble the change from main to this
feature branch with its history into one document for the
reviewers. H7 Fetch the changes in PR 77 from the local clone
and package them with the test files that touch them. H8 I
want to re-check a change after a rebase. Build the packet
again against the previous reviewed revision. H9 Collect the
diff for the hotfix range plus the definitions of the names
it changes into a single verified bundle. H10 Prepare the
evidence pack a reviewer needs for this pull request, with
blame and prior work on the same files.

Should not trigger. N1 Read this packet and tell me which
findings are blockers and which are nits. N2 Approve pull
request 482 and leave the approval comment. N3 Take the
packet for this branch and write the review comments directly
on the pull request. N4 Patch the bug this packet points at
and push the fix. N5 Using the packet as your source, draft
the release notes entry for this change. N6 Stamp this change
as reviewed and record the verdict in the gate report. N7
Explain to the team in plain language what this packet says
changed and why it matters. N8 Write the missing tests for
the function this packet flags as untested. N9 Cherry pick
the commits in this packet onto the release branch. N10 Turn
the findings in this packet into tickets ranked by severity.

Per pass verdicts for the shipped description. The first pass
scored 10 of 10 on the should trigger group and 9 of 10 on
the near misses and missed N5. The second pass scored 9 of 10
on the should trigger group and 10 of 10 on the near misses
and missed H7. The third pass scored 10 of 10 on both groups
and missed nothing. Per pass verdicts for the proposal. Every
pass scored 10 of 10 on both groups and missed nothing.
