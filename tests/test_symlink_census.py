"""The symlink census pin.

Round 89 settled the repo wide symlink question with a
census of the committed tree. Exactly one symlink stands
in the tree and it is legitimate by design. The home
platform spelling of the skill at the Claude skills path
points at the canonical skill under the agents folder.
No shipped check before this one enumerated the tree, so
a link planted outside a guarded surface stood unnamed.

This test derives the census from git itself so it audits
the real committed tree and not a hardcoded file list. It
holds the census to exactly that one path with exactly
that one target so a planted link anywhere in the tree
and a retarget of the legitimate link both fail here.
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
        census = {}
        for line in result.stdout.splitlines():
            meta, _, path = line.partition("\t")
            parts = meta.split()
            if parts[0] != "120000":
                continue
            blob = subprocess.run(
                ["git", "-C", str(ROOT), "cat-file", "-p", parts[2]],
                capture_output=True, text=True,
            )
            census[path] = blob.stdout
        self.assertEqual(census, EXPECTED)


if __name__ == "__main__":
    unittest.main()
