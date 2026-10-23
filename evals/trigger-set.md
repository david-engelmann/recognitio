# Trigger set

Twenty realistic queries for the recognitio skill. Ten should
trigger the skill and ten are near misses that should not. The
labels were fixed before any scoring pass ran. The shipped
description in the frontmatter of the skill file is the text
under test, and TRIGGER-RESULTS.md in this directory records
the outcome.

## Should trigger

1. Extract the changes in pull request 123 into a packet I can review.
2. Pull the diff for the feature branch so we can review it.
3. Prepare a review packet for the range main...fix-login.
4. We pushed new commits. Re-review the change since the last reviewed head.
5. Confirm that everything in this change is present before review begins.
6. Assemble the context around this commit range for the reviewers.
7. Get the changes from that single commit with their enclosing functions.
8. Build the pericope for this pull request.
9. I need the full change plus its call sites and history before I start reviewing.
10. Extract the changes between the release tag and HEAD into one verified packet.

## Should not trigger

11. Review pull request 123 and tell me whether it is safe to merge.
12. Use the packet from the last review and fix the findings it lists.
13. Write unit tests for the changed function named in this packet.
14. Explain in plain words what changed between main and this branch for a reader who will not see the diff.
15. Check the packet is verified, then merge the pull request.
16. Summarise this pull request in one sentence for the changelog, using its packet.
17. Review the packet and rank its findings by severity.
18. Open a pull request for this branch and attach its diff as a comment.
19. Extract the text from this PDF.
20. Prepare a slide deck reviewing the design held in this packet.
