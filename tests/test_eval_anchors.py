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


class TestEvalProseNames(unittest.TestCase):
    """The eval prose beside the index is read for cited names.

    The burn-down red team re-check filed the blind spot as a
    note. A stale test name planted in the per pass notes
    survived every gate, because the corpus check read the
    index alone and the checksum refresh re-records bytes
    without reading citations. Each test below fails when the
    prose check is reverted.
    """

    def setUp(self):
        self.mod = load_script("check_evals")

    def test_a_live_name_cited_in_the_pass_notes_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_fixture(tmp)
            target = root / "evals" / "PASS-NOTES.md"
            text = target.read_text(encoding="utf-8")
            target.write_text(
                text + "\nA note citing "
                "`test_the_real_skill_package_is_valid` in the "
                "gate script suite.\n",
                encoding="utf-8",
            )
            self.assertEqual(self.mod.eval_prose_problems(root), [])

    def test_a_renamed_test_cited_in_the_pass_notes_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_fixture(tmp)
            target = root / "evals" / "PASS-NOTES.md"
            text = target.read_text(encoding="utf-8")
            target.write_text(
                text + "\nA note citing "
                "`test_the_real_skill_package_is_valid` in the "
                "gate script suite.\n",
                encoding="utf-8",
            )
            suite_file = root / "tests" / "test_gate_scripts.py"
            suite_text = suite_file.read_text(encoding="utf-8")
            suite_text = suite_text.replace(
                "def test_the_real_skill_package_is_valid",
                "def test_the_real_skill_package_stays_valid",
            )
            self.assertIn(
                "test_the_real_skill_package_stays_valid", suite_text
            )
            suite_file.write_text(suite_text, encoding="utf-8")
            problems = self.mod.eval_prose_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("PASS-NOTES.md", problems[0])
            self.assertIn(
                "test_the_real_skill_package_is_valid", problems[0]
            )

    def test_a_name_that_never_existed_in_the_results_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_fixture(tmp)
            target = root / "evals" / "RESULTS.md"
            text = target.read_text(encoding="utf-8")
            target.write_text(
                text + "\nA row citing "
                "`test_a_name_that_never_existed` in the gate "
                "script suite.\n",
                encoding="utf-8",
            )
            problems = self.mod.eval_prose_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("RESULTS.md", problems[0])
            self.assertIn(
                "test_a_name_that_never_existed", problems[0]
            )

    def test_a_call_spelling_citation_in_the_pass_notes_fails(self):
        # Red team re-review of the burndown stack. The call
        # spelling, the name with its parentheses, is a
        # citation a reader reads as one, so it is read as one.
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_fixture(tmp)
            target = root / "evals" / "PASS-NOTES.md"
            text = target.read_text(encoding="utf-8")
            target.write_text(
                text + "\nA note citing "
                "`test_a_name_that_never_existed()` in the "
                "gate script suite.\n",
                encoding="utf-8",
            )
            problems = self.mod.eval_prose_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("PASS-NOTES.md", problems[0])
            self.assertIn(
                "test_a_name_that_never_existed", problems[0]
            )

    def test_a_node_id_citation_in_the_results_fails(self):
        # Red team re-review of the burndown stack. The node
        # id spelling names the file first and the test after
        # the colons, and it is read as the citation it is.
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_fixture(tmp)
            target = root / "evals" / "RESULTS.md"
            text = target.read_text(encoding="utf-8")
            target.write_text(
                text + "\nA row citing "
                "`tests/test_qwen.py::"
                "test_a_name_that_never_existed` in the gate "
                "script suite.\n",
                encoding="utf-8",
            )
            problems = self.mod.eval_prose_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("RESULTS.md", problems[0])
            self.assertIn(
                "test_a_name_that_never_existed", problems[0]
            )

    def test_two_names_in_one_span_with_a_stale_name_fails(self):
        # Red team re-review of the burndown stack. One span
        # can carry two citations, and every name in the span
        # is read, so the stale one is named beside the live
        # one passing.
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_fixture(tmp)
            target = root / "evals" / "PASS-NOTES.md"
            text = target.read_text(encoding="utf-8")
            target.write_text(
                text + "\nA note citing "
                "`test_a_name_that_never_existed and "
                "test_the_real_skill_package_is_valid` in "
                "the gate script suite.\n",
                encoding="utf-8",
            )
            problems = self.mod.eval_prose_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("PASS-NOTES.md", problems[0])
            self.assertIn(
                "test_a_name_that_never_existed", problems[0]
            )

    def test_a_stale_name_in_an_uppercase_extension_artefact_fails(self):
        # Red team re-review of the burndown stack. An
        # artefact under an uppercase Markdown extension
        # stands at the evals root all the same, and the
        # check reads it with the rest.
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_fixture(tmp)
            target = root / "evals" / "NEW-NOTES.MD"
            target.write_text(
                "A note citing "
                "`test_a_name_that_never_existed` in the "
                "gate script suite.\n",
                encoding="utf-8",
            )
            problems = self.mod.eval_prose_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("NEW-NOTES.MD", problems[0])
            self.assertIn(
                "test_a_name_that_never_existed", problems[0]
            )

    def test_a_stale_name_after_a_code_fence_in_the_pass_notes_fails(self):
        # Red team re-check of the burndown stack. A fenced
        # block standing before a citation must not silence
        # it. The span reader pairs backtick runs by their
        # length, so the fence reads as one span and the
        # citation after it is read as a citation.
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_fixture(tmp)
            target = root / "evals" / "PASS-NOTES.md"
            text = target.read_text(encoding="utf-8")
            target.write_text(
                text + "\n```\npytest -q tests\n```\n\n"
                "A note citing "
                "`test_a_name_that_never_existed` in the "
                "gate script suite.\n",
                encoding="utf-8",
            )
            problems = self.mod.eval_prose_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("PASS-NOTES.md", problems[0])
            self.assertIn(
                "test_a_name_that_never_existed", problems[0]
            )

    def test_a_live_name_after_a_code_fence_in_the_pass_notes_passes(self):
        # Control. A live name cited after a fence passes
        # in both states, before the fix because the
        # silenced reader saw no citation at all and after
        # it because the citation it reads is live.
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_fixture(tmp)
            target = root / "evals" / "PASS-NOTES.md"
            text = target.read_text(encoding="utf-8")
            target.write_text(
                text + "\n```\npytest -q tests\n```\n\n"
                "A note citing "
                "`test_the_real_skill_package_is_valid` in "
                "the gate script suite.\n",
                encoding="utf-8",
            )
            self.assertEqual(self.mod.eval_prose_problems(root), [])

    def test_a_file_mention_in_the_pass_notes_passes(self):
        # Control. A test file spelled with its suffix is a
        # file mention, not a name citation, in both the
        # fixed state and the state before the fix.
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_fixture(tmp)
            target = root / "evals" / "PASS-NOTES.md"
            text = target.read_text(encoding="utf-8")
            target.write_text(
                text + "\nA note naming the file "
                "`tests/test_qwen.py` beside the suite.\n",
                encoding="utf-8",
            )
            self.assertEqual(self.mod.eval_prose_problems(root), [])


if __name__ == "__main__":
    unittest.main()
