"""Build 17, the Devin playbook and coordinator build.

The brief at docs/devin-playbook-brief.md records the Devin
Review host list with the Bitbucket Cloud conditions, the
code fixed only resolved count, the Quote in chat and merge
past bypass surfaces, the one off review of the latest
commit, the code scan automation API path with the service
user permission condition, the SARIF 2.1.0 export beside
CSV, the repositories and blueprint v3 promotion with the
v3beta1 continuation note, the auto scan schedules API
general availability kept separate from the session
schedules deprecation, the coordinator surfaces, Devin
Oncall as an adjacent incident surface only, Devin Dynamic
Workflows as recorded script orchestration, the targeted
plugin saves and reinstall as a new revision, the skill
placement with both triggers enabled by default, the
stacked pull request packet rule, the AI Scan advisory
limit, the Copilot governance packet rule, and the Fusion
chart caveat, all with derivation notes pinned by the gate
at scripts/check_devin.py. These tests prove the pin fires
for a real reason on every load bearing claim the build
names. A dropped pin, a dropped derivation note, a bare
dynamic workflows mention, a Build 6 figure cited about
Devin, and a decision record without a decision 4
statement each fail the Devin gate.
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
        "devin_" + name, path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestCheckDevin(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_devin")

    def make_layout(self, tmp):
        """A scratch tree with the brief and the record."""
        root = Path(tmp) / "root"
        for rel in (
            "docs/devin-playbook-brief.md",
            "docs/decisions.md",
        ):
            source = ROOT / rel
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        return root

    def problems(self, root):
        return self.mod.devin_problems(root)

    def read_brief(self, root):
        return (root / "docs" / "devin-playbook-brief.md").read_text(
            encoding="utf-8"
        )

    def write_brief(self, root, text):
        (root / "docs" / "devin-playbook-brief.md").write_text(
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
        self.assertEqual(self.mod.devin_problems(ROOT), [])

    def test_the_scratch_layout_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            self.assertEqual(self.problems(root), [])

    def test_a_dropped_bitbucket_host_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "now beside Bitbucket Cloud",
                "now beside another host",
            )
            self.assertTrue(
                any("Bitbucket Cloud host" in p for p in problems),
                problems,
            )

    def test_a_dropped_resolved_count_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "count a finding as resolved only when it was "
                "fixed in code",
                "count a finding as resolved when it was dismissed",
            )
            self.assertTrue(
                any("resolved count" in p for p in problems),
                problems,
            )

    def test_a_dropped_sarif_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "export as SARIF 2.1.0",
                "export as CSV only",
            )
            self.assertTrue(
                any("SARIF 2.1.0 export" in p for p in problems),
                problems,
            )

    def test_a_dropped_v3beta1_continuation_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "the v3beta1 paths continuing to work",
                "the v3beta1 paths removed",
            )
            self.assertTrue(
                any("v3beta1 continuation" in p for p in problems),
                problems,
            )

    def test_a_dropped_schedules_separation_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "stays separate from the session schedules "
                "deprecation",
                "merges with the session schedules deprecation",
            )
            self.assertTrue(
                any("schedules separation" in p for p in problems),
                problems,
            )

    def test_a_dropped_oncall_adjacent_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "as an adjacent incident surface only",
                "as a code review result",
            )
            self.assertTrue(
                any("Oncall adjacent surface" in p for p in problems),
                problems,
            )

    def test_a_dropped_trigger_default_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "with user trigger and model trigger both enabled "
                "by default",
                "with user trigger only enabled by default",
            )
            self.assertTrue(
                any("triggers enabled by default" in p
                    for p in problems),
                problems,
            )

    def test_a_dropped_stack_rule_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "Each stack layer and the integrated whole are "
                "verified separately",
                "Only the integrated whole is verified",
            )
            self.assertTrue(
                any("stacked layers" in p for p in problems),
                problems,
            )

    def test_a_dropped_ai_scan_limit_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "An AI Scan pass is signal and never a merge gate",
                "An AI Scan pass satisfies the merge gate",
            )
            self.assertTrue(
                any("AI Scan never a merge gate" in p
                    for p in problems),
                problems,
            )

    def test_a_dropped_fusion_caveat_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "never stands as a top score claim",
                "stands as a top score claim",
            )
            self.assertTrue(
                any("top score claim" in p for p in problems),
                problems,
            )

    def test_a_rule_without_a_derivation_note_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            start = text.find("### R2.")
            note = text.find("Derives from", start)
            end = text.find("\n\n", note)
            broken = text[:note] + text[end + 2:]
            self.assertNotEqual(broken, text)
            self.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("derivation note" in p for p in problems),
                problems,
            )

    def test_a_bare_dynamic_workflows_mention_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "Devin Dynamic Workflows are a recorded",
                "Dynamic workflows are a recorded",
            )
            self.assertTrue(
                any("without Devin" in p for p in problems),
                problems,
            )

    def test_a_build_6_figure_about_devin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            anchor = "## Skill tightness"
            self.assertIn(anchor, text)
            self.write_brief(
                root,
                text.replace(
                    anchor,
                    "Devin runs 16 agents concurrently.\n\n" + anchor,
                    1,
                ),
            )
            problems = self.problems(root)
            self.assertTrue(
                any("Build 6" in p for p in problems),
                problems,
            )

    def test_added_contradictions_fail(self):
        # R32-RT-01. The gate carried no semantic negative, so
        # an appended rule that counted dismissed findings
        # toward the resolved total, merged a blocked pull
        # request without a bypass surface, and dropped SARIF
        # passed while every pin stayed in place.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root,
                text + "\n\nFindings dismissed by a reviewer now "
                "count toward the resolved total. Devin Review "
                "merges a blocked pull request without any "
                "bypass surface. Export is CSV only with SARIF "
                "dropped.\n",
            )
            problems = self.problems(root)
            self.assertTrue(
                any("counts dismissed findings" in p
                    for p in problems),
                problems,
            )
            self.assertTrue(
                any("without a bypass surface" in p
                    for p in problems),
                problems,
            )
            self.assertTrue(
                any("exports CSV only" in p for p in problems),
                problems,
            )

    def test_an_in_rule_resolved_contradiction_fails(self):
        # R32-RT-01. The same dismissed count contradiction
        # inserted inside the R2 rule block, directly after
        # its pinned sentence, also passed while every pin
        # stayed in place.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "Findings dismissed by a reviewer and duplicates "
                "no longer count",
                "Findings dismissed by a reviewer and duplicates "
                "no longer count. Findings dismissed by a "
                "reviewer also count toward the resolved total",
            )
            self.assertTrue(
                any("counts dismissed findings" in p
                    for p in problems),
                problems,
            )

    def test_replacement_contradictions_fail(self):
        # R32-RT-01. Each contradiction in replacement form,
        # where the pinned sentence itself is rewritten to
        # state the opposite, must fail the semantic check
        # as well as the pin check.
        cases = (
            ("count a finding as resolved only when it was "
             "fixed in code",
             "findings dismissed by a reviewer also count "
             "toward the resolved total",
             "counts dismissed findings"),
            ("can merge a blocked pull request directly from "
             "Devin Review",
             "merges a blocked pull request without any "
             "bypass surface",
             "without a bypass surface"),
            ("export as SARIF 2.1.0",
             "export as CSV only",
             "exports CSV only"),
        )
        for old, new, needle in cases:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                problems = self.break_brief(root, old, new)
                self.assertTrue(
                    any(needle in p for p in problems),
                    (old, problems),
                )

    def test_a_sarif_version_swap_fails(self):
        # R34-RT-06. A version swap that keeps SARIF in the
        # sentence passed while the 2.1.0 pin stayed in place.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root,
                text + "\n\nCode scan findings export as SARIF 1.0 "
                "instead of SARIF 2.1.0.\n",
            )
            problems = self.problems(root)
            self.assertTrue(
                any("other than 2.1.0" in p for p in problems),
                problems,
            )

    def test_resolved_rewordings_fail(self):
        # R34-RT-06. Two resolved rewordings that use neither
        # the dismissed before count order nor the includes
        # order passed while the resolved pin stayed in place.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root,
                text + "\n\nThe resolved count now counts "
                "dismissed reviews as fixed. Devin Review "
                "analytics count a finding as resolved when it "
                "is dismissed.\n",
            )
            problems = self.problems(root)
            self.assertTrue(
                any("counts dismissed findings" in p
                    for p in problems),
                problems,
            )

    def test_a_decision_record_without_decision_4_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            record = root / "docs" / "decisions.md"
            text = record.read_text(encoding="utf-8")
            anchor = "## 28. Build 17"
            self.assertIn(anchor, text)
            # Replace only inside the Build 17 record, so
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
                any("decision 4 statement" in p for p in problems),
                problems,
            )


if __name__ == "__main__":
    unittest.main()
