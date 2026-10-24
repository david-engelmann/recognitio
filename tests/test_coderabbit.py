"""Build 11, the CodeRabbit guidelines build.

The brief at docs/coderabbit-review-brief.md records the rename
direction, the focus toggle table as a constraint, the Quiet
Chill and Assertive profiles, the pre merge checks with Error
mode merge blocking, the October 2026 entries, and the guideline
file provenance now shown in review summaries, all from the
primary CodeRabbit docs. These tests prove the pin fires for a
real reason on every load bearing claim the round 23 lanes
named. A deeper reading of high, a dropped rename direction, a
softened focus constraint, a dropped summary fold, a dropped
axis naming, a dropped Quiet launch, a dropped Error mode pin,
a dropped Automatic Approvals pin, a dropped Deep Scan pin, a
dropped provenance pin, a dropped .claude/rules/ pin, a dropped
pairing guard, a claimed calendar, a guideline without a
derivation note, a passing prose title mention, and a decision
record without a decision 4 statement each fail the CodeRabbit
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
        "coderabbit_" + name, path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestCheckCoderabbit(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_coderabbit")

    def make_layout(self, tmp):
        """A scratch tree with the brief and the record."""
        root = Path(tmp) / "root"
        for rel in (
            "docs/coderabbit-review-brief.md",
            "docs/decisions.md",
        ):
            source = ROOT / rel
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        return root

    def problems(self, root):
        return self.mod.coderabbit_problems(root)

    def read_brief(self, root):
        return (root / "docs" / "coderabbit-review-brief.md").read_text(
            encoding="utf-8"
        )

    def write_brief(self, root, text):
        (root / "docs" / "coderabbit-review-brief.md").write_text(
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
        self.assertEqual(self.mod.coderabbit_problems(ROOT), [])

    def test_the_scratch_layout_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            self.assertEqual(self.problems(root), [])

    def test_a_deeper_reading_of_high_fails(self):
        # R23-RT-03. High trims verbosity and never reads as deeper
        # review. A later edit that treats high as deeper analysis
        # must fail the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "It does not deepen analysis, and the brief must "
                "never treat it as deeper review.",
                "It deepens analysis for reviewers who want more "
                "depth.",
            )
            self.assertTrue(
                any("never deeper reading" in p for p in problems),
                problems,
            )

    def test_a_softened_focus_constraint_fails(self):
        # R23-RT-03. The focus table constrains the brief. Softening
        # the trims claim lets the deeper reading drift back in.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "High trims verbosity.",
                "High adjusts verbosity.",
            )
            self.assertTrue(
                any("high trims" in p for p in problems), problems
            )

    def test_a_dropped_rename_direction_fails(self):
        # R23-RT-03. The primary direction is Fix comments was
        # Autofix and Autofix was Autopilot. Reversing either half
        # must fail the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "Fix comments (formerly Autofix) fixes the review comments you select",
                "Autofix (formerly Fix comments) fixes the review "
                "comments you select",
            )
            self.assertTrue(
                any("Fix comments was Autofix" in p for p in problems),
                problems,
            )

    def test_a_dropped_alias_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "keep working as aliases for a limited time for "
                "backward compatibility.",
                "keep working forever with no sunset.",
            )
            self.assertTrue(
                any("compat aliases" in p for p in problems), problems
            )

    def test_a_dropped_high_row_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "reviews down to essential content only",
                "reviews down to whatever feels right",
            )
            self.assertTrue(
                any("high table row" in p for p in problems), problems
            )

    def test_a_dropped_summary_fold_pin_fails(self):
        # R23-SP-A2. The fold of the summary into the walkthrough
        # at high is pinned explicitly, so no reader counts it as
        # added analysis.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "moves from off to on at high and folds the summary into the walkthrough.",
                "stays off at high like every other setting.",
            )
            self.assertTrue(
                any("summary fold" in p for p in problems), problems
            )

    def test_a_dropped_axis_naming_fails(self):
        # R23-SP-A1. Every focus and profile sentence names its
        # axis, so a reader cannot mix high with assertive.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "On the focus axis, `reviews.focus` takes casual, "
                "balanced, or high",
                "`reviews.focus` takes casual, balanced, or high",
            )
            self.assertTrue(
                any("focus axis named" in p for p in problems),
                problems,
            )

    def test_a_dropped_quiet_launch_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "July 2 2026",
                "a recent date",
                count=0,
            )
            self.assertTrue(
                any("Quiet launch" in p for p in problems), problems
            )

    def test_a_dropped_error_blocking_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "requires resolution before merging.",
                "asks nicely for resolution before merging.",
            )
            self.assertTrue(
                any("Error mode merge blocking" in p for p in problems),
                problems,
            )

    def test_a_dropped_security_merge_blocking_pin_fails(self):
        # R27-SP-02. The October 5 2026 changelog entry says
        # publishing the CodeRabbit Security check alone does
        # not block. A later edit that drops the entry must fail
        # the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "publishing alone does not block.",
                "publishing alone blocks every merge.",
            )
            self.assertTrue(
                any("security merge blocking entry" in p
                    for p in problems),
                problems,
            )

    def test_a_dropped_auto_approvals_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "Optional risk limits keep pull requests above a "
                "chosen Merge Risk for human approval.",
                "Optional risk limits exist somewhere in the "
                "settings.",
            )
            self.assertTrue(
                any("approval risk limits" in p for p in problems),
                problems,
            )

    def test_a_dropped_deep_scan_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "prevent pull request authors from using "
                "`@coderabbitai approve` and `@coderabbitai resolve` "
                "on their own pull requests.",
                "lets pull request authors approve their own pull "
                "requests.",
            )
            self.assertTrue(
                any("author approval key" in p for p in problems),
                problems,
            )

    def test_a_dropped_deep_scan_limit_pin_fails(self):
        # R31-EX-04. The Build 11 brief pins the Deep Scan
        # linked repository limits, the manual versus
        # automatic linking distinction, the findings
        # attachment rule, and the CLI v0.9.0 cloud task
        # surface with its signed Linux release
        # verification.
        cases = (
            ("up to 20 linked repositories",
             "20 linked repositories limit"),
            ("subject to the plan linked repository limit",
             "plan linked repository limit"),
            ("Essentials supports manual links",
             "manual versus automatic linking"),
            ("remain attached to the primary repository",
             "findings attached to primary"),
            ("CLI v0.9.0 for cloud task work",
             "CLI v0.9.0 cloud tasks"),
            ("verifies signed Linux releases",
             "signed Linux release verification"),
        )
        for old, needle in cases:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                problems = self.break_brief(
                    root, old, "Some other sentence stands here."
                )
                self.assertTrue(
                    any(needle in p for p in problems),
                    (old, problems),
                )

    def test_a_dropped_provenance_pin_fails(self):
        # R23-RT-03. The guideline file provenance now shown in
        # review summaries is a pinned sentence.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "configured, auto-discovered, or an Agent Skill.",
                "configured or discovered somehow.",
                count=0,
            )
            self.assertTrue(
                any("guideline provenance" in p for p in problems),
                problems,
            )

    def test_a_dropped_claude_rules_pin_fails(self):
        # R23-EX-01. `.claude/rules/` is the fourth guideline
        # source, with `paths` frontmatter scoping.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "adds `.claude/rules/` as a fourth guideline source",
                "adds another guideline source",
            )
            self.assertTrue(
                any("fourth guideline source" in p for p in problems),
                problems,
            )

    def test_a_dropped_pairing_guard_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "Guideline files are a review pairing source, never "
                "a second packet.",
                "Guideline files are a handy second packet.",
            )
            self.assertTrue(
                any("pairing not a packet" in p for p in problems),
                problems,
            )

    def test_a_claimed_calendar_fails(self):
        # The brief states the no calendar negative plainly.
        # Dropping it lets a schedule claim drift in unpinned.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "There is no product native calendar schedule on any "
                "primary CodeRabbit surface, and the brief claims "
                "none.",
                "CodeRabbit runs reviews on a nightly calendar "
                "schedule.",
            )
            self.assertTrue(
                any("no calendar negative" in p for p in problems),
                problems,
            )

    def test_a_guideline_without_a_derivation_note_fails(self):
        # The second packet guard, carried over from Builds 9 and
        # 10. A guideline with no derivation note is a rival
        # instruction source.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "Derives from canonical skill, The tier model, the T0 instruction file flag.",
                "No derivation is offered for this guideline.",
            )
            self.assertTrue(
                any("no derivation note" in p for p in problems),
                problems,
            )

    def test_a_passing_prose_guideline_note_fails(self):
        # R21-ST-01, applied to the CodeRabbit guidelines. A note
        # that names a canonical section title in passing prose
        # without deriving from it must fail.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "Derives from canonical skill, The tier model, the T0 instruction file flag.",
                "Derives from the primary blog post. It shapes the\n"
                "Workflow of the review and nothing else.",
            )
            self.assertTrue(
                any(
                    "no canonical skill section" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_decision_record_without_decision_4_fails(self):
        # Every landed build records a decision 4 statement. A
        # Build 11 record without one fails the pin.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / "docs" / "decisions.md"
            text = path.read_text(encoding="utf-8")
            start = text.find("## 20. Build 11")
            self.assertNotEqual(start, -1)
            record = text[start:]
            broken = record.replace(
                "Decision 4 binds the build.",
                "Decision 4 is noted elsewhere.",
                1,
            )
            self.assertNotEqual(broken, record)
            path.write_text(text[:start] + broken, encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("decision 4" in p for p in problems), problems
            )


    def test_linked_source_plants_fail(self):
        # R36-RT-04. Linked source promised on an excluded
        # platform, and a linked repository limit above 20,
        # each passed while the pins stayed in place.
        cases = (
            ("Deep Scan linked source is available in the "
             "scan trigger flow for self hosted GitLab and "
             "Azure DevOps and Bitbucket.",
             "promises Deep Scan linked source"),
            ("A Deep Scan can read up to 50 linked "
             "repositories on any plan.",
             "above the pinned limit of 20"),
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

    def test_a_dropped_platform_limit_pin_fails(self):
        # R36-RT-04. The platform limit sentence folded
        # beside the linked context sentence is pinned, so
        # dropping it fails.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "not available in that flow for self hosted "
                "GitLab or Azure DevOps or Bitbucket",
                "available on every platform",
            )
            self.assertTrue(
                any("platform limit" in p for p in problems),
                problems,
            )

    def test_gate_review_linked_source_restated_plants_fail(self):
        # Gate review repair. The first platform branch
        # required the word available as a substring and
        # the figure branch read digits only, so the
        # review restated the promise with works and
        # offered and supported, raised the limit in
        # words, and hid the figure behind the verb link,
        # and each passed.
        cases = (
            ("Deep Scan linked source works in the scan "
             "trigger flow for self hosted GitLab.",
             "promises Deep Scan linked source"),
            ("Deep Scan linked source is offered in the "
             "scan trigger flow on Bitbucket.",
             "promises Deep Scan linked source"),
            ("Linked repositories are supported in the "
             "scan trigger flow on Azure DevOps.",
             "promises Deep Scan linked source"),
            ("A Deep Scan can read up to fifty linked "
             "repositories on any plan.",
             "linked repositories, above the pinned limit"),
            ("A Deep Scan can read up to twenty one linked "
             "repositories on any plan.",
             "linked repositories, above the pinned limit"),
            ("A Deep Scan can link 50 repositories to a "
             "primary repository on any plan.",
             "linked repositories, above the pinned limit"),
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

    def test_gate_review_linked_source_true_sentences_pass(self):
        # Gate review repair. The substring read of the
        # word available fired on unavailable, and the
        # sentence level read fired where an included
        # platform carried the offer and an excluded
        # platform stood under its own negation.
        cases = (
            "Linked source is unavailable in the scan "
            "trigger flow for self hosted GitLab.",
            "Linked source is available on GitHub Cloud, "
            "and self hosted GitLab is not among the "
            "supported platforms.",
        )
        for plant in cases:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                text = self.read_brief(root)
                self.write_brief(root, text + "\n\n" + plant + "\n")
                self.assertEqual(self.problems(root), [])

if __name__ == "__main__":
    unittest.main()
