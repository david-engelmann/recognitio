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

import contextlib
import importlib.util
import io
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


def quieted_body(assertion):
    return (
        "import unittest\n"
        "from pathlib import Path\n"
        "ROOT = Path('.')\n"
        "\n"
        "\n"
        "class TestSomething(unittest.TestCase):\n"
        "    def test_a_quieted_case(self):\n"
        "        " + assertion + "\n"
        "        touched = ROOT.name\n"
    )


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

    def guard_problems(self, body):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            return self.problems(root)

    def assert_vacuous(self, body):
        problems = self.guard_problems(body)
        self.assertTrue(
            any("no real assertion" in p for p in problems),
            problems,
        )

    def assert_clean(self, body):
        self.assertEqual(self.guard_problems(body), [])

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

    def test_a_helper_holding_only_an_always_true_assertion_fails(self):
        # The round 3 helper defeat. The helper body is judged
        # by the same rules as a test body, so moving the
        # vacuous assertion one level down no longer launders
        # it back in.
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def _assert_pin(self, root):\n"
            "        self.assertTrue(True)\n"
            "\n"
            "    def test_a_delegated_case(self):\n"
            "        self._assert_pin(ROOT)\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            problems = self.problems(root)
            self.assertTrue(
                any("no real assertion" in p for p in problems),
                problems,
            )

    def test_a_constant_laundered_through_a_name_fails(self):
        # The round 19 name laundering. A name bound to a
        # literal in the same body is a constant at the point
        # of the assertion, so comparing it with itself or
        # with the literal argues about nothing.
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_quieted_case(self):\n"
            "        expected = 1\n"
            "        self.assertEqual(expected, expected)\n"
            "        touched = ROOT.name\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            problems = self.problems(root)
            self.assertTrue(
                any("no real assertion" in p for p in problems),
                problems,
            )
        body = body.replace(
            "self.assertEqual(expected, expected)",
            "self.assertEqual(expected, 1)",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            problems = self.problems(root)
            self.assertTrue(
                any("no real assertion" in p for p in problems),
                problems,
            )

    def test_a_constant_shared_by_two_names_fails(self):
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_quieted_case(self):\n"
            "        first = second = 1\n"
            "        self.assertEqual(first, second)\n"
            "        touched = ROOT.name\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            problems = self.problems(root)
            self.assertTrue(
                any("no real assertion" in p for p in problems),
                problems,
            )

    def test_a_helper_left_at_a_literal_default_fails(self):
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def _assert_pin(self, value=1):\n"
            "        self.assertEqual(value, 1)\n"
            "        touched = ROOT.name\n"
            "\n"
            "    def test_a_delegated_case(self):\n"
            "        self._assert_pin()\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            problems = self.problems(root)
            self.assertTrue(
                any("no real assertion" in p for p in problems),
                problems,
            )

    def test_a_literal_expectation_against_a_result_passes(self):
        # The common honest shape. A literal held in a name
        # and compared against a fixture result argues about
        # the result, so it still counts in full.
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_real_case(self):\n"
            '        expected = "the pin"\n'
            "        self.assertEqual(self.mod.pin(ROOT), expected)\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            self.assertEqual(self.problems(root), [])

    def test_an_assertion_after_a_return_fails(self):
        # The round 19 execution blindness. An assertion in
        # dead code never runs, so it cannot fail the test.
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_quieted_case(self):\n"
            "        return\n"
            '        self.assertEqual(ROOT.read_text(), "nope")\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            problems = self.problems(root)
            self.assertTrue(
                any("no real assertion" in p for p in problems),
                problems,
            )

    def test_an_assertion_swallowed_by_its_except_clause_fails(self):
        # The round 19 swallowed assertion. A handler that
        # catches the assertion error and passes keeps the
        # test green whatever the assertion says.
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_quieted_case(self):\n"
            "        try:\n"
            '            self.assertEqual(ROOT.read_text(), "nope")\n'
            "        except AssertionError:\n"
            "            pass\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            problems = self.problems(root)
            self.assertTrue(
                any("no real assertion" in p for p in problems),
                problems,
            )

    def test_an_assertion_after_a_conditional_return_still_counts(self):
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_real_case(self):\n"
            "        if ROOT is None:\n"
            "            return\n"
            '        self.assertEqual(ROOT.read_text(), "nope")\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            self.assertEqual(self.problems(root), [])

    def test_an_assertion_whose_handler_reraises_still_counts(self):
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_real_case(self):\n"
            "        try:\n"
            '            self.assertEqual(ROOT.read_text(), "nope")\n'
            "        except AssertionError:\n"
            "            raise\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            self.assertEqual(self.problems(root), [])

    def test_an_async_test_with_a_bare_pass_body_fails(self):
        # The round 19 enumeration blindness. The runner
        # runs asynchronous test methods, so the guard
        # inspects them beside plain ones.
        body = (
            "import unittest\n"
            "\n"
            "\n"
            "class TestSomething(unittest.IsolatedAsyncioTestCase):\n"
            "    async def test_a_quieted_case(self):\n"
            "        pass\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            problems = self.problems(root)
            self.assertTrue(
                any("no real assertion" in p for p in problems),
                problems,
            )

    def test_an_async_test_with_a_real_assertion_passes(self):
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.IsolatedAsyncioTestCase):\n"
            "    async def test_a_real_case(self):\n"
            '        self.assertEqual(ROOT.read_text(), "nope")\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            self.assertEqual(self.problems(root), [])

    def test_a_vacuous_test_in_a_discovery_named_file_fails(self):
        # The runner discovery pattern is wider than the old
        # guard glob, so a file the runner reaches stands
        # under the guard as well.
        body = (
            "import unittest\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_quieted_case(self):\n"
            "        pass\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"testprobe_r19.py": body})
            problems = self.problems(root)
            self.assertTrue(
                any("no real assertion" in p for p in problems),
                problems,
            )

    def test_a_vacuous_module_level_test_function_fails(self):
        body = (
            "def test_a_quieted_case():\n"
            "    pass\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            problems = self.problems(root)
            self.assertTrue(
                any("no real assertion" in p for p in problems),
                problems,
            )

    def test_a_conditional_fail_beside_a_trivial_assertion_fails(self):
        # The round 99 census shape. A fail call that guards
        # a listing step runs only on its branch, so it
        # cannot stand in for the assertion it guards, and
        # an always true assertion beside it argues nothing.
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_quieted_case(self):\n"
            "        result = ROOT.read_text()\n"
            "        if result is None:\n"
            "            self.fail('the listing failed')\n"
            "        self.assertTrue(True)\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            problems = self.problems(root)
            self.assertTrue(
                any("no real assertion" in p for p in problems),
                problems,
            )

    def test_a_conditional_fail_beside_a_real_assertion_passes(self):
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_real_case(self):\n"
            "        result = ROOT.read_text()\n"
            "        if result is None:\n"
            "            self.fail('the listing failed')\n"
            '        self.assertEqual(result, "nope")\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            self.assertEqual(self.problems(root), [])

    def test_an_unconditional_fail_still_counts(self):
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_real_case(self):\n"
            "        result = ROOT.read_text()\n"
            "        self.fail('the listing failed')\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            self.assertEqual(self.problems(root), [])

    def test_a_fail_in_a_loop_else_beside_a_trivial_assertion_fails(self):
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_quieted_case(self):\n"
            "        for name in ROOT.iterdir():\n"
            "            break\n"
            "        else:\n"
            "            self.fail('the accounting never settled')\n"
            "        self.assertTrue(True)\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            problems = self.problems(root)
            self.assertTrue(
                any("no real assertion" in p for p in problems),
                problems,
            )

    def test_a_short_circuited_fail_beside_a_trivial_assertion_fails(self):
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_quieted_case(self):\n"
            "        result = ROOT.read_text()\n"
            "        result or self.fail('the listing failed')\n"
            "        self.assertTrue(True)\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            problems = self.problems(root)
            self.assertTrue(
                any("no real assertion" in p for p in problems),
                problems,
            )

    def test_a_ternary_fail_beside_a_trivial_assertion_fails(self):
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_quieted_case(self):\n"
            "        result = ROOT.read_text()\n"
            "        self.fail('the listing failed') "
            "if result is None else None\n"
            "        self.assertTrue(True)\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            problems = self.problems(root)
            self.assertTrue(
                any("no real assertion" in p for p in problems),
                problems,
            )

    def test_a_length_of_a_constant_string_fails(self):
        # The round 107 battery. A pure call over constants
        # argued about nothing under the old reading, because
        # a call was never a constant expression there.
        self.assert_vacuous(
            quieted_body('self.assertEqual(len("abcd"), 4)')
        )

    def test_an_integer_of_a_constant_string_fails(self):
        self.assert_vacuous(
            quieted_body('self.assertEqual(int("42"), 42)')
        )

    def test_a_sorted_constant_list_fails(self):
        self.assert_vacuous(
            quieted_body(
                "self.assertEqual(sorted([3, 1, 2]), [1, 2, 3])"
            )
        )

    def test_an_upper_case_of_a_constant_string_fails(self):
        self.assert_vacuous(
            quieted_body('self.assertEqual("abc".upper(), "ABC")')
        )

    def test_a_boolean_of_a_constant_fails(self):
        self.assert_vacuous(quieted_body("self.assertTrue(bool(1))"))

    def test_an_instance_check_against_a_builtin_name_fails(self):
        self.assert_vacuous(
            quieted_body('self.assertIsInstance("x", str)')
        )

    def test_a_type_of_a_constant_against_a_builtin_name_fails(self):
        self.assert_vacuous(
            quieted_body("self.assertEqual(type(1), int)")
        )

    def test_a_string_of_a_constant_number_fails(self):
        self.assert_vacuous(
            quieted_body('self.assertEqual(str(42), "42")')
        )

    def test_a_maximum_of_two_constants_fails(self):
        self.assert_vacuous(
            quieted_body("self.assertEqual(max(1, 9), 9)")
        )

    def test_an_absolute_value_of_a_constant_fails(self):
        self.assert_vacuous(
            quieted_body("self.assertEqual(abs(-3), 3)")
        )

    def test_a_join_of_a_constant_list_fails(self):
        self.assert_vacuous(
            quieted_body(
                'self.assertEqual(",".join(["a", "b"]), "a,b")'
            )
        )

    def test_a_pure_call_through_a_helper_with_a_literal_fails(self):
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def _check(self, value):\n"
            "        self.assertEqual(len(value), 4)\n"
            "\n"
            "    def test_a_quieted_case(self):\n"
            "        self._check('abcd')\n"
        )
        self.assert_vacuous(body)

    def test_a_pure_call_laundered_through_a_name_fails(self):
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_quieted_case(self):\n"
            '        count = len("abcd")\n'
            "        self.assertEqual(count, 4)\n"
            "        touched = ROOT.name\n"
        )
        self.assert_vacuous(body)

    def test_a_plain_assert_over_a_pure_call_fails(self):
        self.assert_vacuous(
            quieted_body('assert len("abcd") == 4')
        )

    def test_a_length_of_a_fixture_read_still_counts(self):
        # The same call over a value is a real assertion, so
        # the pure call reading must not take its credit.
        self.assert_clean(
            quieted_body(
                "self.assertEqual(len(ROOT.read_text()), 4)"
            )
        )

    def test_a_conversion_of_a_fixture_read_still_counts(self):
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_real_case(self):\n"
            "        data = ROOT.read_text()\n"
            "        self.assertEqual(int(data), 42)\n"
        )
        self.assert_clean(body)

    def test_a_sort_of_a_computed_value_still_counts(self):
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_real_case(self):\n"
            "        result = self.mod.pin(ROOT)\n"
            "        self.assertEqual(sorted(result), [1, 2])\n"
        )
        self.assert_clean(body)

    def test_an_instance_check_on_a_value_still_counts(self):
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_real_case(self):\n"
            "        data = ROOT.read_text()\n"
            "        self.assertIsInstance(data, str)\n"
        )
        self.assert_clean(body)

    def test_a_type_check_on_a_value_still_counts(self):
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_real_case(self):\n"
            "        data = ROOT.read_text()\n"
            "        self.assertEqual(type(data), str)\n"
        )
        self.assert_clean(body)

    def test_a_case_form_of_a_value_still_counts(self):
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_real_case(self):\n"
            "        data = ROOT.read_text()\n"
            '        self.assertEqual(data.upper(), "ABC")\n'
        )
        self.assert_clean(body)

    def test_a_pure_call_through_a_helper_on_a_value_counts(self):
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def _check(self, value):\n"
            "        self.assertEqual(len(value), 4)\n"
            "\n"
            "    def test_a_real_case(self):\n"
            "        self._check(ROOT.read_text())\n"
        )
        self.assert_clean(body)

    def test_a_length_of_a_callback_filled_list_still_counts(self):
        # A list filled by a nested function holds what the
        # callback put in it at run time, so a length over
        # the name argues about that filling and not about
        # the empty list the binding wrote.
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_real_case(self):\n"
            "        calls = []\n"
            "\n"
            "        def counting(item):\n"
            "            calls.append(item)\n"
            "\n"
            "        counting(ROOT.name)\n"
            "        self.assertEqual(len(calls), 1, calls)\n"
        )
        self.assert_clean(body)

    def test_a_set_filled_from_a_fixture_still_counts(self):
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_real_case(self):\n"
            "        found = set()\n"
            "        found.update([ROOT.name])\n"
            "        self.assertEqual(found, {'.'})\n"
        )
        self.assert_clean(body)

    def test_the_success_line_names_the_limits_it_keeps(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self.mod.main(ROOT)
        self.assertEqual(code, 0)
        self.assertIn("within the limits", out.getvalue())

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
