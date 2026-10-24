"""The test vacuity guard.

R23-RT-01. The round 23 red team proved that softening a check
together with its paired test defeats the gate in silence. The
guard at scripts/check_test_vacuity.py is the mechanical answer
for that attack shape. These tests prove it fires for a real
reason. A test body that is a bare pass, a single assertion
that is always true, a constant equality with no fixture, and
a real looking assertion that never touches a fixture each fail
the guard, while the shipped suite passes it.
"""

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    path = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(
        "vacuity_" + name, path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REAL_TEST = '''import unittest


class TestSomething(unittest.TestCase):
    def test_a_real_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            problems = self.mod.some_problems(root)
            self.assertEqual(problems, [])
'''


class TestCheckTestVacuity(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_test_vacuity")

    def make_tree(self, tmp, files):
        root = Path(tmp) / "root"
        tests = root / "tests"
        tests.mkdir(parents=True)
        for name, body in files.items():
            (tests / name).write_text(body, encoding="utf-8")
        return root

    def problems(self, root):
        return self.mod.vacuity_problems(root)

    def test_the_shipped_suite_holds(self):
        self.assertEqual(self.mod.vacuity_problems(ROOT), [])

    def test_a_real_test_method_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": REAL_TEST})
            self.assertEqual(self.problems(root), [])

    def test_a_bare_pass_body_fails(self):
        # The laziest softening. A test body that is only a pass
        # cannot fail for a real reason.
        body = (
            "import unittest\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_quieted_case(self):\n"
            "        pass\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            problems = self.problems(root)
            self.assertTrue(
                any("no real assertion" in p for p in problems),
                problems,
            )

    def test_an_always_true_assertion_fails(self):
        # R23-RT-01. The demonstrated attack shape. A single
        # assertion that is always true, with no fixture at all,
        # keeps the suite green while the finding stays quieted.
        body = (
            "import unittest\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_quieted_case(self):\n"
            "        self.assertTrue(True)\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            problems = self.problems(root)
            self.assertTrue(
                any("no real assertion" in p for p in problems),
                problems,
            )
            self.assertTrue(
                any("never touches a fixture" in p for p in problems),
                problems,
            )

    def test_a_constant_equality_without_a_fixture_fails(self):
        body = (
            "import unittest\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_quieted_case(self):\n"
            "        self.assertEqual(1, 1)\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            problems = self.problems(root)
            self.assertTrue(
                any("no real assertion" in p for p in problems),
                problems,
            )

    def test_an_assertion_without_a_fixture_touch_fails(self):
        # A real looking assertion that argues about nothing the
        # suite exercises. The assertion form is fine, but the
        # body never reaches for a fixture.
        body = (
            "import unittest\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_quieted_case(self):\n"
            '        self.assertTrue("x" in "xyz")\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            problems = self.problems(root)
            self.assertTrue(
                any("never touches a fixture" in p for p in problems),
                problems,
            )

    def test_a_shared_assert_helper_still_counts(self):
        # The suite uses shared _assert helpers for repeated pins.
        # A test that delegates to one carries a real assertion.
        body = (
            "import unittest\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def _assert_pin(self, root):\n"
            "        self.assertEqual(self.mod.pin(root), [])\n"
            "\n"
            "    def test_a_delegated_case(self):\n"
            "        self._assert_pin(ROOT)\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            self.assertEqual(self.problems(root), [])


if __name__ == "__main__":
    unittest.main()
