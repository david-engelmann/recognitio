# Review of the round 14 fix change

## Summary

The change closes the round 14 findings and lands Build 4,
the headless print mode CI shape. In detail the packet output
style moves to `output-styles/packet.md` at the plugin root,
which is where the vendor manifest reference resolves the
declared path, and the existence pin resolves the declared
path against the plugin root the way the host does instead of
a hardcoded directory prefix. The style's derivation section
is pinned word for word, closing the blind spot the sentence
check used to skip. The sentence check matches whole
sentences instead of substrings, so an imperative inversion
of a pinned prohibition no longer passes. The frontmatter pin
checks the block parses the way the host reads it, naming
duplicate keys and unbalanced brackets. The tautological
pointer test is rewritten to plant the defect in real files
on a scratch tree and run the real pin against them. The
derivation names the stamping section among its sources, and
decision 9 states the evidence boundary for other hosts'
frontmatter behavior instead of the overstated claim. The
headless shape is defined in `docs/headless-review.md` with
its findings schema and fail closed contract, and
`scripts/check_headless.py` gates a captured run on the exit
code, the `permission_denials` list, the `structured_output`
presence, schema conformance and evidence standing in the
packet manifest. Decision 11 records the build. Verdict is
APPROVE.

## Findings by severity

### P1

None. R14-RT-05 is met by the relocation and the vendor style
path resolution in the pin, with a regression test planting
the old layout on a scratch tree and failing it.

### P2

None. R14-RT-01 is met by the word for word derivation pin,
with the nine red team plants all caught on scratch copies,
including the subheading shape that first slipped the region
regex. R14-RT-02 is met by the whole sentence membership
check. R14-EX-01 is met by sourcing. The headless docs page
gained the `permission_denials` text the same day the
external lane read the page without it, so the build keeps
the signal with the page as its primary source and carries
the two fail closed limits the lane recorded.

### P3

None. R14-RT-03 is met by the frontmatter readability check
with its duplicate key and unbalanced bracket plants pinned.
R14-RT-04 and R14-ST-01 are met by the rewritten pointer
test, which plants the defect in real manifest files and
runs the real pin. R14-SF-01 is met by the widened source
list. R14-EX-02 is met by the rephrased decision 9 sentence.

## Nits

None.

## What was checked

The packet under review is the round 14 fix set in the
worktree `~/workspace/recognitio-r14-fix` at base
b333ee3a497cfea682deed550747a2aca6c4f47e. The full gate ran
on the worktree with `make check` exiting 0 and a suite line
of 308 tests with OK, baseline 287 plus 15 headless tests
plus 6 net new style pin tests. The nine round 14 red team
plants were re-run against the fixed tree on scratch copies
and all nine are caught, with the pristine tree passing. The
new tests were revert checked. The headless suite errors on
the pristine tree with the module missing, and the updated
extraction flag test fails on the pristine extractor. The
copy bar scan over the changed prose files is clean. The
The change is not pushed. The push is the parent agent's act.

Findings disposition. Fixed 0. Wrong 0. Intentional 0. Not
worth it 0.
