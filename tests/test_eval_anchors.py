"""Regression tests for the round 11 eval integrity repairs.

The round 11 red team filed R11-RT-01 because tasks 01 to 05 had
no planted defect anchor, and confirmed the round 9 gate shapes
R9G-RT-02 and R9G-RT-03 plus the round 10 R10-RT-01 token plant
still reproduce. The round 10 spec lane filed R10-SF-01 because
the two summaries agreement branch had no pinning test. Each
test below fails when its repair is reverted.
"""

import importlib.util
import io
import json
import re
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    path = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location("gate_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_fixture(tmp):
    """A scratch tree with the evals, tests, scripts and skill extractor."""
    root = Path(tmp) / "root"
    shutil.copytree(ROOT / "evals", root / "evals")
    shutil.copytree(ROOT / "tests", root / "tests")
    shutil.copytree(ROOT / "scripts", root / "scripts")
    skill_scripts = root / ".agents" / "skills" / "recognitio" / "scripts"
    skill_scripts.mkdir(parents=True)
    shutil.copy2(
        ROOT / ".agents" / "skills" / "recognitio" / "scripts" / "extract.py",
        skill_scripts / "extract.py",
    )
    return root


class TestFenceGraderTightening(unittest.TestCase):
    """The grader needs evidence level ties, not token presence."""

    def setUp(self):
        self.mod = load_script("check_evals")
        task_dir = ROOT / "evals" / "tasks" / "task-06"
        self.d1_file, self.old_module, _, rule_problems = (
            self.mod.task06_planted_rule(task_dir)
        )
        self.assertEqual(rule_problems, [])
        fences, fence_problems = self.mod.transcript_fences(task_dir)
        self.assertEqual(fence_problems, [])
        self.raw_fence, self.packet_fence = fences
        self.operand = "subtotal"

    def grade(self, fence):
        return self.mod.task06_grade_fence(
            fence, self.d1_file, self.old_module, self.operand
        )

    def test_pristine_fences_grade_as_recorded(self):
        self.assertEqual(self.grade(self.raw_fence), (0, 1))
        self.assertEqual(self.grade(self.packet_fence), (1, 1))

    def test_a_casual_filename_note_does_not_move_d1(self):
        planted = self.raw_fence + "\nNo report.py seen in the diff.\n"
        self.assertEqual(self.grade(planted), (0, 1))

    def test_a_doubling_denial_gets_no_credit(self):
        denial = self.packet_fence.replace(
            "Finding 2. The changed return line in book.py returns "
            "subtotal plus subtotal, so every total comes back doubled.",
            "Finding 2. The return line returns subtotal, plus the "
            "surrounding code looks fine, with an explicit statement "
            "that no doubling defect was found.",
        )
        self.assertIn("no doubling defect was found", denial)
        self.assertEqual(self.grade(denial), (1, 0))

    def test_a_plus_side_overcount_gets_no_credit(self):
        fence = (
            "The return line computes subtotal. On the plus side, "
            "the rename looks fine."
        )
        self.assertEqual(self.grade(fence), (0, 0))

    def test_kindred_doubling_words_credit(self):
        doubling = (
            "The return line is doubling the subtotal, "
            "so every total comes back wrong."
        )
        duplicated = "The new return line has a duplicated subtotal term."
        self.assertEqual(self.grade(doubling), (0, 1))
        self.assertEqual(self.grade(duplicated), (0, 1))


class TestEffectAnchors(unittest.TestCase):
    """The anchors check the defect effect, not the defect text."""

    def setUp(self):
        self.mod = load_script("check_evals")

    def task06_sources(self):
        path = ROOT / "evals" / "tasks" / "task-06" / "sources.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_a_shimmed_task06_head_fails_the_d1_effect_anchor(self):
        sources = self.task06_sources()
        sources["head"]["ledger.py"] = "from book import total\n"
        with tempfile.TemporaryDirectory() as tmp:
            repo, _base, _head, diff = self.mod.build_fixture_repo(
                tmp, sources
            )
            _operand, problems = self.mod.task06_anchor_problems(
                repo, diff, "report.py", "ledger", "book"
            )
        self.assertEqual(len(problems), 1)
        self.assertIn("D1 defect", problems[0])
        self.assertIn("succeeds", problems[0])

    def test_a_commented_task06_doubling_fails_the_d2_effect_anchor(self):
        sources = self.task06_sources()
        sources["head"]["book.py"] = (
            '"""Ledger helpers."""\n'
            "\n"
            "\n"
            "def total(items):\n"
            "    subtotal = sum(items)\n"
            "    # return subtotal + subtotal\n"
            "    return subtotal\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            repo, _base, _head, diff = self.mod.build_fixture_repo(
                tmp, sources
            )
            _operand, problems = self.mod.task06_anchor_problems(
                repo, diff, "report.py", "ledger", "book"
            )
        self.assertEqual(len(problems), 1)
        self.assertIn("D2 defect", problems[0])
        self.assertIn("instead of the doubled", problems[0])

    def test_task01_three_argument_tamper_fails_the_task_anchor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_fixture(tmp)
            sources_path = root / "evals" / "tasks" / "task-01" / "sources.json"
            sources = json.loads(sources_path.read_text(encoding="utf-8"))
            sources["head"]["shop.py"] = (
                "from calc import price\n\n\ndef total():\n    return price(2, 3, 0)\n"
            )
            sources_path.write_text(json.dumps(sources), encoding="utf-8")
            problems = self.mod.task_anchor_problems(root, "task-01")
        self.assertTrue(problems)
        self.assertTrue(
            any("D1 defect of task-01" in problem for problem in problems),
            problems,
        )

    def test_task_anchors_pass_on_the_real_tree(self):
        for task_name in ("task-01", "task-02", "task-03", "task-04", "task-05"):
            with self.subTest(task=task_name):
                self.assertEqual(
                    self.mod.task_anchor_problems(ROOT, task_name), []
                )


class TestAgreementPin(unittest.TestCase):
    """The two summaries agreement branch needs its pinning test."""

    def setUp(self):
        self.mod = load_script("check_evals")

    def test_a_single_summary_move_fails_the_agreement_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_fixture(tmp)
            target = root / "evals" / "RESULTS.md"
            text = target.read_text(encoding="utf-8")
            text = re.sub(
                r"The raw pass reported 1 of 2 on this\s+task",
                "The raw pass reported 2 of 2 on this task",
                text,
                count=1,
            )
            self.assertIn(
                "The raw pass reported 2 of 2 on this task", text
            )
            target.write_text(text, encoding="utf-8")
            self.mod.write_checksums(root)
            self.assertEqual(self.mod.checksum_problems(root), [])
            problems = self.mod.task06_problems(root)
            self.assertTrue(
                any("disagree" in problem for problem in problems),
                problems,
            )


if __name__ == "__main__":
    unittest.main()
