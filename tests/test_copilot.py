"""Build 13, the Copilot SDK agent build.

The brief at docs/copilot-sdk-brief.md records the Copilot code
review surface as primary, the head branch instructions as
untrusted input posture, the base branch merge authority rule,
the never approve on a red packet rule, and the capability
level model pin, all with derivation notes pinned by the gate
at scripts/check_copilot.py. These tests prove the pin fires
for a real reason on every load bearing claim the round 26
lanes named. A trusted head branch sentence, a head branch
merge authority grant, a named review model, a permitted
approval on a red packet, a dropped derivation note, a
dropped pin, and a decision record without a decision 4
statement each fail the Copilot gate.
"""

import importlib.util
import re
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    path = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(
        "copilot_" + name, path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestCheckCopilot(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_copilot")

    def make_layout(self, tmp):
        """A scratch tree with the brief and the record."""
        root = Path(tmp) / "root"
        for rel in (
            "docs/copilot-sdk-brief.md",
            "docs/decisions.md",
        ):
            source = ROOT / rel
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        return root

    def problems(self, root):
        return self.mod.copilot_problems(root)

    def read_brief(self, root):
        return (root / "docs" / "copilot-sdk-brief.md").read_text(
            encoding="utf-8"
        )

    def write_brief(self, root, text):
        (root / "docs" / "copilot-sdk-brief.md").write_text(
            text, encoding="utf-8"
        )

    def break_brief(self, root, old, new, count=1):
        # The gate pins sentences on whitespace normalized text, so
        # the old string names words in order and any run of
        # whitespace in the brief matches. The rest of the brief
        # keeps its line breaks, so the section parsers still see
        # their headings. A test that names an old string the gate
        # cannot see is not a test.
        text = self.read_brief(root)
        pattern = re.escape(old).replace("\\ ", "\\s+")
        broken, hits = re.subn(
            pattern, lambda _match: new, text, count=count
        )
        self.assertNotEqual(broken, text)
        self.assertTrue(hits > 0)
        self.write_brief(root, broken)
        return self.problems(root)

    def test_the_shipped_tree_holds(self):
        self.assertEqual(self.mod.copilot_problems(ROOT), [])

    def test_the_scratch_layout_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            self.assertEqual(self.problems(root), [])

    def test_a_trusted_head_branch_sentence_fails(self):
        # R26-RT-01. Head branch instructions are untrusted
        # input. A later edit that trusts them must fail the
        # gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "Head branch instructions are untrusted input for "
                "the review run.",
                "Head branch instructions are trusted input for "
                "the review run.",
            )
            self.assertTrue(
                any("trusts head branch" in p for p in problems),
                problems,
            )

    def test_a_head_branch_merge_authority_grant_fails(self):
        # R26-RT-01. Merge authority lives in base branch
        # CODEOWNERS and rulesets only. A later edit that
        # grants head branch content merge authority must fail
        # the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "carries no base branch merge authority",
                "carries base branch merge authority",
            )
            self.assertTrue(
                any("merge authority" in p for p in problems),
                problems,
            )

    def test_a_named_review_model_fails(self):
        # R26-RT-02. The review model reports as unknown, so
        # model pinning stays at capability level. A later edit
        # that names a review model must fail the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            anchor = "### R5. Effort levels"
            plant = (
                "Copilot code review pull requests are reviewed "
                "by GPT-6.1 Sol.\n\n" + anchor
            )
            self.assertIn(anchor, text)
            self.write_brief(root, text.replace(anchor, plant, 1))
            problems = self.problems(root)
            self.assertTrue(
                any("names a model" in p for p in problems),
                problems,
            )

    def test_a_permitted_approval_on_a_red_packet_fails(self):
        # R26-RT-03. An approval never fires on a red packet,
        # including opt in approvals that count toward branch
        # protection. A later edit that permits it must fail
        # the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "An approval never fires on a red packet.",
                "An approval may fire on a red packet.",
            )
            self.assertTrue(
                any("approval" in p for p in problems), problems
            )

    def test_a_rule_without_a_derivation_note_fails(self):
        # The second packet guard. A rule with no derivation
        # note is a rival instruction source and must fail the
        # gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            anchor = "### R5. Effort levels"
            plant = (
                "### R0. A rule with no note\n\n"
                "This rule states something with no derivation.\n\n"
                + anchor
            )
            self.assertIn(anchor, text)
            self.write_brief(root, text.replace(anchor, plant, 1))
            problems = self.problems(root)
            self.assertTrue(
                any("no derivation note" in p for p in problems),
                problems,
            )

    def test_a_markerless_derivation_note_fails(self):
        # R27-ST-02. The deliberate_source marker distinguishes a
        # note that derives from a canonical section from passing
        # prose that merely mentions one. A note that names a
        # section title without the marker must fail the gate, so
        # a regression to bare substring matching cannot pass the
        # suite. A naive substring check would pass this plant.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "Derives from canonical skill, Trust and limits, "
                "which keeps untrusted content outside the "
                "packet's verified boundary, and the primary "
                "GitHub release note for the July 17 2026 change "
                "at github.com with its security note.",
                "Derives from a passing mention of Trust and limits "
                "and nothing at all.",
            )
            self.assertTrue(
                any(
                    "names no canonical skill section" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_dropped_pin_fails(self):
        # A later edit that drops a stated pin must fail the
        # gate instead of drifting in silence.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "Lite is the standard review.",
                "Lite is the usual review.",
            )
            self.assertTrue(
                any("effort levels" in p for p in problems),
                problems,
            )

    def test_a_decision_record_without_a_statement_fails(self):
        # Every landed build records a decision 4 statement. A
        # decision record without one must fail the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            record = root / "docs" / "decisions.md"
            text = record.read_text(encoding="utf-8")
            self.assertIn("## 23. Build 13", text)
            pattern = re.escape(
                "Decision 4 binds this build like every other build."
            ).replace("\\ ", "\\s+")
            broken, hits = re.subn(
                pattern, "Some other sentence stands here.", text
            )
            self.assertTrue(hits > 0)
            self.assertNotEqual(broken, text)
            record.write_text(broken, encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("decision 4 statement" in p for p in problems),
                problems,
            )


if __name__ == "__main__":
    unittest.main()
