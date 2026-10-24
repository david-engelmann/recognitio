"""Build 16, the ZCode plugin build.

The brief at docs/zcode-plugin-brief.md records the ZCode
native plugin with its manifest at .zcode-plugin/plugin.json,
the in client plugin marketplace distribution with the
version bump rule, the portable v1 shape losing output
styles and settings on ZCode, the register but not execute
behavior for channels, lspServers, outputStyles, and
settings, and the 1024 character description cap with the
100KB body truncation, all with derivation notes pinned by
the gate at scripts/check_zcode.py. These tests prove the
pin fires for a real reason on every load bearing claim the
build names. A dropped pin, a dropped derivation note, a
missing manifest, an over cap description, and a decision
record without a decision 4 statement each fail the ZCode
gate.
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
        "zcode_" + name, path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestCheckZcode(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_zcode")

    def make_layout(self, tmp):
        """A scratch tree with the brief, the manifest, the
        home manifest, the skill, and the record."""
        root = Path(tmp) / "root"
        for rel in (
            "docs/zcode-plugin-brief.md",
            "docs/decisions.md",
            ".zcode-plugin/plugin.json",
            ".claude-plugin/plugin.json",
            ".agents/skills/recognitio/SKILL.md",
        ):
            source = ROOT / rel
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        return root

    def problems(self, root):
        return self.mod.zcode_problems(root)

    def read_brief(self, root):
        return (root / "docs" / "zcode-plugin-brief.md").read_text(
            encoding="utf-8"
        )

    def write_brief(self, root, text):
        (root / "docs" / "zcode-plugin-brief.md").write_text(
            text, encoding="utf-8"
        )

    def break_brief(self, root, old, new, count=1):
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
        self.assertEqual(self.mod.zcode_problems(ROOT), [])

    def test_the_scratch_layout_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            self.assertEqual(self.problems(root), [])

    def test_a_dropped_version_bump_sentence_fails(self):
        # The version bump rule is the distribution claim:
        # no bump means no update offered.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "carries no version bump",
                "carries a version bump",
            )
            self.assertTrue(
                any("version bump" in p for p in problems),
                problems,
            )

    def test_a_dropped_register_not_execute_sentence_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "register but do not execute on ZCode",
                "register and execute on ZCode",
            )
            self.assertTrue(
                any("register but not execute" in p
                    for p in problems),
                problems,
            )

    def test_a_dropped_description_cap_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "runs at most 1024 characters",
                "runs at most 2048 characters",
            )
            self.assertTrue(
                any("description cap" in p for p in problems),
                problems,
            )

    def test_a_rule_without_a_derivation_note_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            anchor = "### Z2."
            self.assertIn(anchor, text)
            # Drop the Z1 derivation note: the note paragraph
            # after the Z1 content, before the Z2 heading.
            start = text.find("Derives from the primary ZCode")
            end = text.find("### Z2.", start)
            self.assertTrue(start > 0 and end > start)
            self.write_brief(root, text[:start] + text[end:])
            problems = self.problems(root)
            self.assertTrue(
                any("no derivation note" in p for p in problems),
                problems,
            )

    def test_a_missing_manifest_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            (root / ".zcode-plugin" / "plugin.json").unlink()
            problems = self.problems(root)
            self.assertTrue(
                any("missing manifest" in p for p in problems),
                problems,
            )

    def test_an_over_cap_description_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            manifest = root / ".zcode-plugin" / "plugin.json"
            text = manifest.read_text(encoding="utf-8")
            self.assertIn('"version": "1.3.0"', text)
            long_desc = "x" * 1025
            manifest.write_text(
                text.replace(
                    "Pulls the relevant changes",
                    long_desc,
                    1,
                ),
                encoding="utf-8",
            )
            problems = self.problems(root)
            self.assertTrue(
                any("over the 1024 limit" in p for p in problems),
                problems,
            )

    def test_a_mismatched_manifest_version_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            manifest = root / ".zcode-plugin" / "plugin.json"
            text = manifest.read_text(encoding="utf-8")
            manifest.write_text(
                text.replace('"1.3.0"', '"9.9.9"', 1),
                encoding="utf-8",
            )
            problems = self.problems(root)
            self.assertTrue(
                any("does not match the repo version" in p
                    for p in problems),
                problems,
            )

    def test_a_dropped_derivation_url_fails(self):
        # R31-SP-02. The ZCode derivation notes carry the
        # two retrievable zcode.z.ai page URLs, so a
        # repo-only reader can reopen the primary pages.
        cases = (
            ("https://zcode.z.ai/en/docs/skill",
             "skill page URL"),
            ("https://zcode.z.ai/en/docs/plugin",
             "plugin page URL"),
        )
        for old, needle in cases:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                text = self.read_brief(root)
                broken = text.replace(old, "")
                self.assertNotEqual(broken, text)
                self.write_brief(root, broken)
                problems = self.problems(root)
                self.assertTrue(
                    any(needle in p for p in problems),
                    (old, problems),
                )

    def test_a_decision_record_without_decision_4_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            record = root / "docs" / "decisions.md"
            text = record.read_text(encoding="utf-8")
            anchor = "## 27. Build 16"
            self.assertIn(anchor, text)
            # Replace only inside the Build 16 record, so
            # earlier decisions that share the statement are
            # untouched.
            head, _, rest = text.partition(anchor)
            self.assertIn("Decision 4 binds", rest)
            record.write_text(
                head + anchor
                + rest.replace("Decision 4 binds", "Decision 4 notes", 1),
                encoding="utf-8",
            )
            problems = self.problems(root)
            self.assertTrue(
                any("decision 4" in p for p in problems),
                problems,
            )


    def test_execution_and_cap_plants_fail(self):
        # R36-RT-05. An execution claim for the registered
        # fields and a doubled description cap each passed
        # while the pins stayed in place, because no check
        # read a contradicting brief sentence.
        cases = (
            ("ZCode executes the settings declared in a "
             "plugin manifest.", "executing a registered"),
            ("A plugin description on ZCode runs at most "
             "2048 characters.", "description cap of 2048"),
        )
        for plant, needle in cases:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                text = self.read_brief(root)
                self.write_brief(root, text + "\n\n" + plant + "\n")
                problems = self.problems(root)
                self.assertTrue(
                    any(needle in p for p in problems),
                    (plant, problems),
                )

    def test_gate_review_execution_and_cap_restated_plants_fail(self):
        # Gate review repair. The sentence level guard let
        # a first clause guard phrase exempt a second
        # clause execution claim, the patterns read one
        # word order and one verb stem, and the cap branch
        # read the digit characters form only, so the
        # review restated each claim outside those shapes.
        cases = (
            ("Until ZCode executes them, settings stay "
             "registered, and in practice ZCode executes "
             "the settings declared in a plugin manifest "
             "at startup.", "executing a registered"),
            ("The settings declared in a plugin manifest "
             "are executed by ZCode on startup.",
             "executing a registered"),
            ("ZCode runs the settings declared in a plugin "
             "manifest.", "executing a registered"),
            ("A plugin description on ZCode has a 2048 "
             "character limit.", "description cap of 2048"),
            ("A plugin description on ZCode runs at most "
             "two thousand and forty eight characters.",
             "description cap of 2048"),
            ("A plugin description on ZCode runs at most "
             "2048 chars.", "description cap of 2048"),
        )
        for plant, needle in cases:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                text = self.read_brief(root)
                self.write_brief(root, text + "\n\n" + plant + "\n")
                problems = self.problems(root)
                self.assertTrue(
                    any(needle in p for p in problems),
                    (plant, problems),
                )

    def test_gate_review_other_host_cap_sentence_passes(self):
        # Gate review repair. The first cap branch read
        # every character figure in a sentence holding the
        # word description, so a true sentence stating the
        # ZCode cap beside a different host figure failed.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root,
                text + "\n\nThe ZCode plugin description cap "
                "is 1024 characters, and a different host "
                "allows 2048 characters for its own "
                "description field.\n",
            )
            self.assertEqual(self.problems(root), [])

    def test_round37_its_own_cap_naming_zcode_fails(self):
        # R37-RT-09. The possessive belongs to ZCode itself
        # in this clause, so the its own skip no longer
        # shelters the doubled cap.
        plant = (
            "ZCode sets its own plugin description cap at "
            "2048 characters."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "description cap of 2048 characters, "
                    "other than the pinned cap of 1024" in p
                    for p in problems
                ),
                problems,
            )

    def test_round37_execution_split_by_parenthetical_fails(self):
        # R37-RT-09. A parenthetical clause isolates the
        # verb from the field under the clause split, and
        # the sentence scope reading must catch it.
        plant = (
            "ZCode executes, once the plugin manifest has "
            "been loaded and every declaration inside it "
            "has been read in full, the settings it "
            "declares."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "has ZCode executing a registered" in p
                    for p in problems
                ),
                problems,
            )

    def test_round37_figure_split_from_its_unit_fails(self):
        # R37-RT-09. The figure and its unit stand in
        # separate clauses behind a qualifier, and the
        # sentence extraction must still read the figure.
        plant = (
            "A plugin description on ZCode is capped at "
            "2048, measured in characters."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "description cap of 2048" in p
                    for p in problems
                ),
                problems,
            )

    def test_round37_different_host_clause_still_passes(self):
        # R37-RT-09 control. A figure scoped to a different
        # host in its own clause states no ZCode cap, and
        # the shipped 1024 beside it still passes.
        sentence = (
            "The brief states the ZCode description cap at "
            "1024 characters, while a different host sets "
            "its own description cap at 2048 characters."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root, text + "\n\n" + sentence + "\n"
            )
            self.assertEqual(self.problems(root), [])

    def test_round37_below_cap_figure_fails_as_other_than(self):
        # R37-ST-01. The cap rule tests inequality, so a
        # figure below the pinned cap fails too, and the
        # problem states the rule as other than.
        plant = (
            "A plugin description on ZCode is capped at "
            "512 characters."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "other than the pinned cap of 1024" in p
                    for p in problems
                ),
                problems,
            )

    def test_round37_fixreview_guard_inside_the_clause_fails(self):
        # R37F-RT-13. A guard removes only the text up to
        # its own phrase, so an execution claim standing
        # after the guard phrase inside the same clause
        # stays under judgement and fails.
        plant = (
            "ZCode can register but also executes the "
            "settings it declares."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "executing a registered plugin field" in p
                    for p in problems
                ),
                problems,
            )

    def test_round37_fixreview_inherited_cap_binds_to_zcode(self):
        # R37F-RT-14. A clause that has ZCode inherit the
        # figure a different host clause states binds that
        # figure to ZCode, so the skip no longer applies.
        plant = (
            "A plugin description on a different host is "
            "capped at 2048 characters, and ZCode inherits "
            "that cap for its plugin descriptions."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "description cap of 2048" in p
                    for p in problems
                ),
                problems,
            )

    def test_round37_fixreview_qualifier_behind_filler_fails(self):
        # R37F-RT-14. Short filler between the comma and
        # the qualifier verb states the same separated
        # figure, so the figure is extracted and fails.
        plant = (
            "On ZCode, a plugin description is capped at "
            "2048, with the limit measured in characters "
            "for every plugin."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "description cap of 2048" in p
                    for p in problems
                ),
                problems,
            )

    def test_round37_confirm2_execution_before_guard_fails(self):
        # R37C-RT-08. An execution claim standing before
        # the guard phrase in the same clause stays under
        # judgement, because the guard governs only its
        # own phrase.
        plant = (
            "ZCode executes the settings it declares and "
            "does not execute the settings it borrows."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any("execute" in p for p in problems), problems
            )

    def test_round37_confirm2_inheritance_deictic_limit_fails(self):
        # R37C-RT-09. The binding is the reference itself,
        # so uses that limit binds the different host
        # figure to ZCode the same way inherits that cap
        # does.
        plant = (
            "A plugin description on a different host is "
            "capped at 2048 characters, and ZCode uses that "
            "limit for its plugin descriptions."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "cap of 2048 characters" in p
                    for p in problems
                ),
                problems,
            )

    def test_round37_confirm2_separated_filler_nine_fails(self):
        # Unnumbered confirmation shape. Nine plain words
        # of filler before the qualifier verb state the
        # same separated figure inside the measured
        # allowance of twelve.
        plant = (
            "On ZCode, a plugin description is capped at "
            "2048, with the limit for every plugin in the "
            "workspace measured in characters for every "
            "plugin."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "cap of 2048 characters" in p
                    for p in problems
                ),
                problems,
            )


if __name__ == "__main__":
    unittest.main()
