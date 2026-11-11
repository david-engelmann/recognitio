[Back to the documentation index](README.md)

# The hosted diff evidence

This page records the evidence the hosted diff claim in the
principles and the README rests on. The claim is that a hosted
diff can leave part of a change out while the response reads
as a success, so a review that trusts it can judge a change
it never fully saw. Two kinds of evidence stand behind the
claim. The first is the documented limit set the host itself
publishes. The second is a comparison measured on this repo
through the host API on 2026-11-11.

## The documented limits

The host documentation states the limits of a diff response
in its repository limits and its REST documentation for
commits, both read on 2026-11-11.

- No total diff may exceed 20,000 lines or 1 MB of raw diff
  data.
- No single file diff may exceed 20,000 lines or 500 KB.
- A single diff shows at most 300 files.
- The comparison response lists at most 300 changed files
  for the whole comparison, and paging can extend the list
  to 3,000 files.
- A commit list returned without paging parameters stops at
  250 commits.

The documentation states no flag a response raises when a
limit cuts its content. A response that met a limit and one
that did not arrive in the same shape.

## The measured comparison

On 2026-11-11 the comparison between the root commit of
this repo and its then current head was read through the
host API. The root commit is a54563ec and the head was the
capstone round 15 landing at 167aed36. The commit list for
the repo held 322 commits across four pages. The response
reported the comparison as ahead and named 321 commits in
its total, a total that counts the root commit itself, so
the range carries 320 descendants of the root, while the
commit list it carried held 250
entries, the documented unpaged cap met exactly. Thirteen
fields stood at the top level of the response, and none of
them reports that a list was cut or that patch content was
dropped.

The two trees differ at 272 paths. The response carried
272 file entries, 270 added and 2 modified, and 144 of
them carried a patch while 128 carried none. Every entry
without a patch was an added file. The largest entries
without a patch are the demo recordings, headed by the
WebM form at 24,222,065 bytes, and fourteen of them
measure under 5,000 bytes, among them a test fixture at
146 bytes and a test module at 3,515 bytes. The largest
patches the response carried measured 71,725 characters
for the capture record, 68,950 for the eval corpus and
67,464 for the decision record.

A reader of that response holds every file name, and 128
of the 272 entries arrive with no content at all, and
nothing in the response says so. That is the failure the
local clone rule exists to refuse.
