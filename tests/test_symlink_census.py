"""The symlink census pin.

The repo wide symlink question is whether any link stands
in the tree besides the one legitimate link, and a census
of the tree answers it. Exactly one symlink stands in the
tree and it is legitimate by design. The link at
.claude/skills/recognitio points at
../../.agents/skills/recognitio. No shipped check before
this one enumerated the tree, so a link planted outside
a guarded surface stood unnamed.

This test derives two censuses from git itself so it
audits the real tree and not a hardcoded file list. The
first census reads the committed tree at HEAD. The
second census reads the index, holding every entry in
the form it stands staged for the next commit. The test
holds each census to exactly that one path with exactly
that one target, so a planted link and a retarget of the
legitimate link both fail here once the plant or the
retarget stands committed or staged.

A link that stands in the working tree alone, neither
staged nor committed, stands outside this pin and the
pin makes no claim about it. A checkout made fresh from
a commit holds its index and its committed tree in
agreement, so the two censuses read the same there.
"""

import subprocess
import unittest
from pathlib import Path

# The root comes from the unresolved location of this
# file so a copy of this file planted as a link into
# another tree still censuses the tree the file actually
# sits in and never the tree the link points at.
ROOT = Path(__file__).absolute().parents[1]

EXPECTED = {
    ".claude/skills/recognitio": "../../.agents/skills/recognitio",
}


def census_from_listing(lines, blob_index):
    # The two listings place the blob hash in different
    # fields. A tree listing names the mode and the type
    # before the hash, and an index listing names the mode
    # before the hash and the stage after it.
    census = {}
    for line in lines:
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if parts[0] != "120000":
            continue
        blob = subprocess.run(
            ["git", "-C", str(ROOT), "cat-file", "-p",
             parts[blob_index]],
            capture_output=True, text=True,
        )
        census[path] = blob.stdout
    return census


class TestSymlinkCensus(unittest.TestCase):
    def test_the_committed_tree_holds_exactly_one_symlink(self):
        # The skip is for a tree under no git work tree at
        # all, as in an export or a tarball. A listing that
        # fails inside a work tree is a failure and not a
        # skip, so no plant can hide behind it there.
        inside = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse",
             "--is-inside-work-tree"],
            capture_output=True, text=True,
        )
        if inside.returncode != 0 or (
            inside.stdout.splitlines() != ["true"]
        ):
            self.skipTest("no git metadata stands over this tree")
        result = subprocess.run(
            ["git", "-C", str(ROOT), "ls-tree", "-r", "HEAD"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            self.fail("the tree listing failed inside a work tree")
        census = census_from_listing(result.stdout.splitlines(), 2)
        self.assertEqual(census, EXPECTED)
        staged = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "--stage"],
            capture_output=True, text=True,
        )
        if staged.returncode != 0:
            self.fail("the index listing failed inside a work tree")
        staged_census = census_from_listing(
            staged.stdout.splitlines(), 1
        )
        self.assertEqual(staged_census, EXPECTED)


if __name__ == "__main__":
    unittest.main()
