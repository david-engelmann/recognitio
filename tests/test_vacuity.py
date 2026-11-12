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

    def test_a_missing_tests_directory_fails_the_guard(self):
        # Round 4 audit Major 2. The guard judged whatever
        # discovery reached, so a tree holding no tests at
        # all read as a suite with no vacuous test in it.
        # The discovery floor refuses by name instead.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            root.mkdir()
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "tests directory is missing" in p
                    for p in problems
                ),
                problems,
            )

    def test_an_empty_tests_directory_fails_the_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {})
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "holds no test files" in p for p in problems
                ),
                problems,
            )

    def test_a_suite_with_no_test_methods_fails_the_guard(self):
        body = (
            "import unittest\n"
            "\n"
            "\n"
            "def helper():\n"
            "    return 1\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "hold no test methods" in p for p in problems
                ),
                problems,
            )

    def test_the_floor_refusal_exits_nonzero_without_the_success_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            root.mkdir()
            err = io.StringIO()
            out = io.StringIO()
            with contextlib.redirect_stderr(err):
                with contextlib.redirect_stdout(out):
                    code = self.mod.main(root)
            self.assertEqual(code, 1)
            self.assertIn(
                "tests directory is missing", err.getvalue()
            )
            self.assertNotIn("stands clear", out.getvalue())

    def test_a_mock_only_assertion_fails(self):
        # Round 4 red team Minor 1. A method whose only
        # assertions read back a mock's own call bookkeeping
        # argues about the stand-in and never about a value
        # the code under test returned.
        body = (
            "import unittest\n"
            "from unittest import mock\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_mocked_case(self):\n"
            "        touched = ROOT.name\n"
            "        m = mock.Mock()\n"
            "        m.run()\n"
            "        self.assertTrue(m.run.called)\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            problems = self.problems(root)
            self.assertTrue(
                any("no real assertion" in p for p in problems),
                problems,
            )

    def test_a_mock_call_count_assertion_fails(self):
        body = (
            "import unittest\n"
            "from unittest import mock\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_mocked_case(self):\n"
            "        touched = ROOT.name\n"
            "        m = mock.Mock()\n"
            "        m.run()\n"
            "        self.assertEqual(m.run.call_count, 1)\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            problems = self.problems(root)
            self.assertTrue(
                any("no real assertion" in p for p in problems),
                problems,
            )

    def test_a_plain_assert_on_a_mock_called_flag_fails(self):
        body = (
            "import unittest\n"
            "from unittest import mock\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_mocked_case(self):\n"
            "        touched = ROOT.name\n"
            "        m = mock.Mock()\n"
            "        m.run()\n"
            "        assert m.run.called\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            problems = self.problems(root)
            self.assertTrue(
                any("no real assertion" in p for p in problems),
                problems,
            )

    def test_a_mock_assertion_beside_a_real_assertion_passes(self):
        # The control. Mock bookkeeping beside an assertion
        # on a value a real function computed is a real test,
        # and the extension must leave it standing, which is
        # what lets the genuine suite pass with no new
        # problems.
        body = (
            "import unittest\n"
            "from unittest import mock\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "def measure(text):\n"
            "    return len(text)\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_mixed_case(self):\n"
            "        touched = ROOT.name\n"
            "        m = mock.Mock()\n"
            "        m.run()\n"
            "        self.assertTrue(m.run.called)\n"
            "        self.assertEqual(measure(touched), 0)\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            self.assertEqual(self.problems(root), [])

    def test_a_helper_asserting_on_a_passed_mock_fails(self):
        # The helper form. A mock handed to a same-file
        # helper that asserts on its call state stays
        # mock-only across the call.
        body = (
            "import unittest\n"
            "from unittest import mock\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def _check(self, m):\n"
            "        self.assertTrue(m.run.called)\n"
            "\n"
            "    def test_a_mocked_case(self):\n"
            "        touched = ROOT.name\n"
            "        m = mock.Mock()\n"
            "        m.run()\n"
            "        self._check(m)\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            problems = self.problems(root)
            self.assertTrue(
                any("no real assertion" in p for p in problems),
                problems,
            )

    def patch_body(self, header, with_expr):
        return (
            header
            + "import unittest\n"
            + "from pathlib import Path\n"
            + "ROOT = Path('.')\n"
            + "\n"
            + "\n"
            + "class TestSomething(unittest.TestCase):\n"
            + "    def test_a_mocked_case(self):\n"
            + "        touched = ROOT.name\n"
            + "        with " + with_expr + " as m:\n"
            + "            m()\n"
            + "            self.assertTrue(m.called)\n"
        )

    def assert_patch_spelling_fails(self, header, with_expr):
        body = self.patch_body(header, with_expr)
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            problems = self.problems(root)
            self.assertTrue(
                any("no real assertion" in p for p in problems),
                problems,
            )

    def test_a_mock_only_patch_spelling_fails(self):
        # Round 4 fix repair. Every patch spelling that
        # hands back a mock marks its bound name as a mock,
        # in the refused shape of a fixture touch, the stand
        # in called, and assertions only on its call
        # bookkeeping.
        self.assert_patch_spelling_fails(
            "from unittest.mock import patch\n",
            "patch('os.getcwd')",
        )

    def test_a_mock_only_patch_object_spelling_fails(self):
        self.assert_patch_spelling_fails(
            "from unittest.mock import patch\n",
            "patch.object(Path, 'name')",
        )

    def test_a_mock_only_patch_multiple_spelling_fails(self):
        self.assert_patch_spelling_fails(
            "from unittest.mock import patch\n",
            "patch.multiple('os', getcwd=True)",
        )

    def test_a_mock_only_mock_patch_spelling_fails(self):
        # The red team plant B6 shape, the spelling the
        # shipped suite itself uses for this work.
        self.assert_patch_spelling_fails(
            "from unittest import mock\n",
            "mock.patch('os.getcwd')",
        )

    def test_a_mock_only_mock_patch_object_spelling_fails(self):
        self.assert_patch_spelling_fails(
            "from unittest import mock\n",
            "mock.patch.object(Path, 'name')",
        )

    def test_a_mock_only_mock_patch_multiple_spelling_fails(self):
        self.assert_patch_spelling_fails(
            "from unittest import mock\n",
            "mock.patch.multiple('os', getcwd=True)",
        )

    def test_a_mock_only_unittest_mock_patch_spelling_fails(self):
        self.assert_patch_spelling_fails(
            "import unittest.mock\n",
            "unittest.mock.patch('os.getcwd')",
        )

    def test_a_mock_only_unittest_mock_patch_object_fails(self):
        self.assert_patch_spelling_fails(
            "import unittest.mock\n",
            "unittest.mock.patch.object(Path, 'name')",
        )

    def test_a_mock_only_unittest_mock_patch_multiple_fails(self):
        self.assert_patch_spelling_fails(
            "import unittest.mock\n",
            "unittest.mock.patch.multiple('os', getcwd=True)",
        )

    def test_a_patch_dict_bound_dictionary_assertion_passes(self):
        # The control in the other direction. The dict
        # patching spelling binds the patched mapping
        # itself, so an assertion about its entries is a
        # real assertion and keeps its credit.
        body = (
            "import unittest\n"
            "from unittest import mock\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_dict_case(self):\n"
            "        touched = ROOT.name\n"
            "        config = {'mode': 'old'}\n"
            "        with mock.patch.dict(\n"
            "            config, {'mode': 'new'}\n"
            "        ) as bound:\n"
            "            self.assertEqual(bound['mode'], 'new')\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            self.assertEqual(self.problems(root), [])

    def test_a_mock_patch_beside_a_real_assertion_passes(self):
        # The control. A stand in bound through mock.patch
        # stands beside an assertion on a real return, and
        # the second assertion keeps the test standing.
        body = (
            "import unittest\n"
            "from unittest import mock\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "def measure(text):\n"
            "    return len(text)\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_mixed_case(self):\n"
            "        touched = ROOT.name\n"
            "        with mock.patch('os.getcwd') as m:\n"
            "            m()\n"
            "            self.assertTrue(m.called)\n"
            "        self.assertEqual(measure(touched), 0)\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            self.assertEqual(self.problems(root), [])

    def test_a_setup_mock_assertion_fails(self):
        # The red team plant B8 shape. A mock assigned to
        # self in setUp is a stand in in the test method
        # that asserts on it.
        body = (
            "import unittest\n"
            "from unittest import mock\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def setUp(self):\n"
            "        self.m = mock.Mock()\n"
            "\n"
            "    def test_a_mocked_case(self):\n"
            "        touched = ROOT.name\n"
            "        self.m.run()\n"
            "        self.assertTrue(self.m.run.called)\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            problems = self.problems(root)
            self.assertTrue(
                any("no real assertion" in p for p in problems),
                problems,
            )

    def test_a_module_level_mock_assertion_fails(self):
        # The red team plant B9 shape.
        body = (
            "import unittest\n"
            "from unittest import mock\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "m = mock.Mock()\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_mocked_case(self):\n"
            "        touched = ROOT.name\n"
            "        m.run()\n"
            "        self.assertTrue(m.run.called)\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            problems = self.problems(root)
            self.assertTrue(
                any("no real assertion" in p for p in problems),
                problems,
            )

    def test_a_helper_returned_mock_assertion_fails(self):
        # The red team plant B10 shape.
        body = (
            "import unittest\n"
            "from unittest import mock\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "def make_mock():\n"
            "    return mock.Mock()\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_mocked_case(self):\n"
            "        touched = ROOT.name\n"
            "        m = make_mock()\n"
            "        m.run()\n"
            "        self.assertTrue(m.run.called)\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(tmp, {"test_x.py": body})
            problems = self.problems(root)
            self.assertTrue(
                any("no real assertion" in p for p in problems),
                problems,
            )

    def test_an_undecodable_test_file_is_named_not_raised(self):
        # Round 4 red team Minor 3. A test file holding
        # damaged bytes draws the named UTF-8 problem in
        # the family wording and never a traceback.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            tests = root / "tests"
            tests.mkdir(parents=True)
            (tests / "test_x.py").write_bytes(b"\xff\xfe\x00bad")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "test_x.py" in p
                    and "cannot be read as UTF-8 text" in p
                    for p in problems
                ),
                problems,
            )

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


    def test_a_fixture_read_compared_with_itself_fails(self):
        # Round 19 red team V3, Major. The self comparison
        # plants this suite carried before this round bound
        # their names to constants, so the constant reading
        # refused them with or without the self comparison
        # reading, and that reading stood unpriced. A name
        # read from a fixture at run time is no constant,
        # and comparing it with itself still argues about
        # nothing, so the guard must refuse this case on
        # the self comparison reading alone.
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_self_compared_read(self):\n"
            "        value = (ROOT / 'fixture.txt').read_text()\n"
            "        assert value == value\n"
            "        touched = ROOT.name\n"
        )
        self.assert_vacuous(body)
        # The control. The same case comparing its read
        # against a second read stands clean, so the
        # refusal above turns on the self comparison and
        # not on the fixture shape around it.
        control = body.replace(
            "assert value == value",
            "assert value == (ROOT / 'other.txt').read_text()",
        )
        self.assertNotEqual(control, body)
        self.assert_clean(control)

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

    def test_a_pure_builtin_aliased_through_a_name_fails(self):
        # The round 131 battery. A name bound in the same
        # body to a pure builtin stands for that builtin, so
        # calling the name over constants argues about
        # nothing in the same way calling the builtin does.
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_quieted_case(self):\n"
            "        measure = len\n"
            '        self.assertEqual(measure("abcd"), 4)\n'
            "        touched = ROOT.name\n"
        )
        self.assert_vacuous(body)

    def test_a_pure_builtin_through_the_builtins_module_fails(
        self,
    ):
        body = (
            "import builtins\n"
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_quieted_case(self):\n"
            '        self.assertEqual(builtins.len("abcd"), 4)\n'
            "        touched = ROOT.name\n"
        )
        self.assert_vacuous(body)

    def test_a_pure_builtin_through_an_import_alias_fails(self):
        body = (
            "import builtins as b\n"
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_quieted_case(self):\n"
            '        self.assertEqual(b.len("abcd"), 4)\n'
            "        touched = ROOT.name\n"
        )
        self.assert_vacuous(body)

    def test_a_pure_call_in_a_comprehension_over_constants_fails(
        self,
    ):
        self.assert_vacuous(
            quieted_body(
                "self.assertEqual("
                '[len(w) for w in ["a", "bb"]], [1, 2])'
            )
        )

    def test_a_pure_call_in_a_generator_expression_fails(self):
        self.assert_vacuous(
            quieted_body(
                "self.assertEqual("
                'sum(len(w) for w in ["a", "bb"]), 3)'
            )
        )

    def test_an_immediately_called_lambda_over_constants_fails(
        self,
    ):
        self.assert_vacuous(
            quieted_body(
                "self.assertEqual("
                '(lambda text: len(text))("abcd"), 4)'
            )
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

    def test_an_alias_to_another_function_still_counts(self):
        # An alias bound to a function outside the pure
        # builtin set keeps its credit, because a static
        # reading cannot settle what that function does.
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "def measure(text):\n"
            "    return len(text) + len(ROOT.name)\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_real_case(self):\n"
            "        alias = measure\n"
            '        self.assertEqual(alias("abcd"), 5)\n'
        )
        self.assert_clean(body)

    def test_a_comprehension_over_a_computed_iterable_counts(
        self,
    ):
        # A comprehension over an iterable the reading
        # cannot settle argues about what the iterable
        # holds at run time, so it keeps its credit.
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_real_case(self):\n"
            "        words = ROOT.name.split()\n"
            "        self.assertEqual("
            "[len(w) for w in words], [1])\n"
        )
        self.assert_clean(body)

    def test_a_stored_lambda_still_counts(self):
        # A lambda held in a name and called at a later
        # point is not followed to that call, so the call
        # keeps the credit a call over a value keeps.
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_real_case(self):\n"
            "        func = lambda text: len(text)\n"
            '        self.assertEqual(func("abcd"), 4)\n'
            "        touched = ROOT.name\n"
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

    def test_a_helper_in_another_class_is_not_followed(self):
        # The guard follows helpers held in the same class
        # only, a limit its docstring records. A test whose
        # only assertion lives in a helper on another class
        # is refused, and the refusal names the shapes this
        # guard follows rather than claiming the test cannot
        # fail at run time, because the delegated assertion
        # does run there and can fail there. The round 5
        # discharge refusal named eleven shipped tests of
        # exactly this shape before their helpers moved
        # into their own classes.
        body = (
            "import unittest\n"
            "\n"
            "\n"
            "class InnerCase(unittest.TestCase):\n"
            "    def assert_plant_kind(self, problems, kind):\n"
            "        self.assertTrue(\n"
            "            any(kind in p for p in problems),\n"
            "            problems,\n"
            "        )\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def setUp(self):\n"
            "        self.inner = InnerCase()\n"
            "\n"
            "    def test_a_delegated_case(self):\n"
            "        problems = self.mod.negative_problems(\n"
            "            'The wrapper exit 2 covers a broken "
            "tool.'\n"
            "        )\n"
            "        self.inner.assert_plant_kind(\n"
            "            problems, 'wrapper exit')\n"
        )
        problems = self.guard_problems(body)
        self.assertTrue(
            any(
                "no real assertion in a shape this guard "
                "follows" in p
                for p in problems
            ),
            problems,
        )

    def test_a_fixture_refusal_names_the_followed_shapes(self):
        # The companion pin for the fixture refusal. The
        # round 5 wording fix narrowed that refusal tail to
        # the shapes this guard follows in the same edit as
        # the assertion refusal, and this plant holds the
        # scoped substring so a silent revert of the fixture
        # string alone fails here. The body is the standing
        # fixture plant shape, a real looking assertion that
        # never reaches for a fixture.
        body = (
            "import unittest\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_quieted_case(self):\n"
            '        self.assertTrue("x" in "xyz")\n'
        )
        problems = self.guard_problems(body)
        self.assertTrue(
            any(
                "never touches a fixture in a shape this "
                "guard follows" in p
                for p in problems
            ),
            problems,
        )

    def test_an_empty_test_file_fails_the_guard(self):
        # The discovery floor is per file as well as
        # global. A test file truncated to nothing would
        # otherwise pass in silence while the files around
        # it still gave the global floor its methods, so
        # the empty file is a problem by name.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_tree(
                tmp,
                {
                    "test_real.py": REAL_TEST,
                    "test_empty.py": "",
                    "test_blank.py": "  \n\n  ",
                },
            )
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "test_empty.py" in p
                    and "stands empty" in p
                    for p in problems
                ),
                problems,
            )
            self.assertTrue(
                any(
                    "test_blank.py" in p
                    and "stands empty" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_container_literal_handed_to_a_helper_still_counts(self):
        # A recorded limit, pinned rather than hidden. A
        # test that hands its same class helper a container
        # literal holding the very problems it expects, and
        # asserts over that parameter inside the helper,
        # pins nothing, because the helper passes on the
        # literal alone. The guard credits it anyway,
        # because what a container holds is not settled
        # where a parameter binds it at a call site, a
        # limit the guard docstring records with the spec
        # lane diff review as the guard for the shape. If
        # the guard ever learns to settle that binding,
        # this test fails and the limit record must move
        # with it.
        body = (
            "import unittest\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def assert_plant_kind(self, problems, "
            "kind):\n"
            "        self.assertTrue(\n"
            "            any(kind in p for p in problems),\n"
            "            problems,\n"
            "        )\n"
            "\n"
            "    def test_a_quieted_case(self):\n"
            "        self.assert_plant_kind(\n"
            "            ['carries a figure plant in the "
            "sentence'],\n"
            "            'figure')\n"
        )
        self.assert_clean(body)

    def test_a_patch_imported_under_an_alias_fails(self):
        # Round 9 red team Blocker B1, first spelling. The
        # patch form imported under another name hands back
        # the same mock, so a test asserting only on its
        # call state argues about the stand in.
        body = (
            "import unittest\n"
            "from unittest.mock import patch as swap\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_mocked_case(self):\n"
            "        touched = ROOT.name\n"
            "        with swap('some.module.run') as m:\n"
            "            m()\n"
            "            self.assertTrue(m.called)\n"
            "            self.assertEqual(m.call_count, 1)\n"
        )
        self.assert_vacuous(body)

    def test_a_patch_object_under_an_alias_fails(self):
        body = (
            "import unittest\n"
            "from unittest.mock import patch as swap\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_mocked_case(self):\n"
            "        touched = ROOT.name\n"
            "        with swap.object(Path, 'name') as m:\n"
            "            m()\n"
            "            self.assertTrue(m.called)\n"
        )
        self.assert_vacuous(body)

    def test_a_patcher_started_by_hand_fails(self):
        # Round 9 red team Blocker B1, second spelling. A
        # patcher built from a patch form hands its mock
        # back through the start call, so the name the
        # start call binds is a mock on the same reading.
        body = (
            "import unittest\n"
            "from unittest.mock import patch\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_mocked_case(self):\n"
            "        touched = ROOT.name\n"
            "        patcher = patch('some.module.run')\n"
            "        m = patcher.start()\n"
            "        m()\n"
            "        self.assertTrue(m.called)\n"
            "        self.assertEqual(m.call_count, 1)\n"
            "        patcher.stop()\n"
        )
        self.assert_vacuous(body)

    def test_a_patch_reached_through_a_module_alias_fails(self):
        # Round 9 confirmation repair. The mock module
        # itself bound under an alias by a from import
        # hands its patch forms under that root, the same
        # binding a dotted import under an alias makes, so
        # a test asserting only on the mock call state is
        # refused the same way.
        body = (
            "import unittest\n"
            "from unittest import mock as umock\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_mocked_case(self):\n"
            "        touched = ROOT.name\n"
            "        with umock.patch('some.module.run') as m:\n"
            "            m()\n"
            "            self.assertTrue(m.called)\n"
        )
        self.assert_vacuous(body)

    def test_a_helper_returning_a_bound_constant_fails(self):
        # Round 9 confirmation repair, second seat. A
        # helper that binds a constant to a name and hands
        # the name back hands back the constant, so a test
        # asserting the call against that constant argues
        # about constants alone in the same way.
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def pinned(self):\n"
            "        value = 'abc'\n"
            "        return value\n"
            "\n"
            "    def test_a_quieted_case(self):\n"
            "        touched = ROOT.name\n"
            "        self.assertEqual(self.pinned(), 'abc')\n"
        )
        self.assert_vacuous(body)

    def test_a_patch_form_bound_to_a_plain_name_is_a_limit(self):
        # Round 9 red team delta confirmation. A patch
        # form handed on to a plain name by assignment
        # stands outside the guard reading by its recorded
        # limit, in the same family as a mock constructor
        # bound the same way, so this body passes clean and
        # pins the limit where it stands.
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "from unittest.mock import patch as swap\n"
            "ROOT = Path('.')\n"
            "swap2 = swap\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_quieted_case(self):\n"
            "        touched = ROOT.name\n"
            "        with swap2('some.module.run') as m:\n"
            "            m()\n"
            "            self.assertTrue(m.called)\n"
        )
        self.assert_clean(body)

    def test_a_mock_only_test_under_a_wrapper_is_a_limit(self):
        # Round 9 red team delta confirmation. A patch
        # decorator stacked over a hand written wrapper
        # leaves the parameter binding to the wrapper, and
        # the guard docstring records that a mock only test
        # in this shape passes while pinning nothing, so
        # this body passes clean and pins the limit.
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "from unittest.mock import patch\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "def inject(fn):\n"
            "    def wrapper(self):\n"
            "        return fn(self, 'real-value')\n"
            "    return wrapper\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    @patch('some.module.run')\n"
            "    @inject\n"
            "    def test_a_quieted_case(self, supplied, m):\n"
            "        touched = ROOT.name\n"
            "        m()\n"
            "        self.assertTrue(m.called)\n"
        )
        self.assert_clean(body)

    def test_a_patcher_started_in_one_expression_fails(self):
        # Round 9 confirmation repair. A patch form started
        # in the same expression that builds it hands back
        # the same mock a named patcher hands back through
        # its start call, so the name that start call binds
        # is a mock on the same reading.
        body = (
            "import unittest\n"
            "from unittest.mock import patch\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_mocked_case(self):\n"
            "        touched = ROOT.name\n"
            "        m = patch('some.module.run').start()\n"
            "        m()\n"
            "        self.assertTrue(m.called)\n"
            "        self.assertEqual(m.call_count, 1)\n"
        )
        self.assert_vacuous(body)

    def test_a_mock_handed_in_by_a_patch_decorator_fails(self):
        # Round 9 red team Blocker B1, third spelling. A
        # patch form in the decorator list hands its mock
        # in as the method argument it binds, the shape
        # the guard docstring names as a patch stand in.
        body = (
            "import unittest\n"
            "from unittest.mock import patch\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    @patch('some.module.run')\n"
            "    def test_a_mocked_case(self, m):\n"
            "        touched = ROOT.name\n"
            "        m()\n"
            "        self.assertTrue(m.called)\n"
            "        self.assertEqual(m.call_count, 1)\n"
        )
        self.assert_vacuous(body)

    def test_a_patch_dict_under_an_alias_still_passes(self):
        # The control in the other direction. The dict
        # spelling under an import alias still binds the
        # patched mapping itself, so an assertion about
        # its entries keeps its credit.
        body = (
            "import unittest\n"
            "from unittest.mock import patch as swap\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def test_a_dict_case(self):\n"
            "        touched = ROOT.name\n"
            "        config = {'mode': 'old'}\n"
            "        with swap.dict(\n"
            "            config, {'mode': 'new'}\n"
            "        ) as bound:\n"
            "            self.assertEqual(bound['mode'], 'new')\n"
        )
        self.assert_clean(body)

    def test_a_decorator_mock_beside_a_real_assertion_passes(self):
        # The control. A stand in handed in by a patch
        # decorator stands beside an assertion on a real
        # return, and the second assertion keeps the test
        # standing.
        body = (
            "import unittest\n"
            "from unittest.mock import patch\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "def measure(text):\n"
            "    return len(text)\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    @patch('some.module.run')\n"
            "    def test_a_mixed_case(self, m):\n"
            "        touched = ROOT.name\n"
            "        m()\n"
            "        self.assertTrue(m.called)\n"
            "        self.assertEqual(measure(touched), 0)\n"
        )
        self.assert_clean(body)

    def test_a_constant_laundered_through_a_helper_return_fails(self):
        # Round 9 red team Blocker B2. A same class helper
        # whose returns all settle as constants hands back
        # constants alone, so an assertion comparing its
        # call against a literal argues about nothing.
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def pinned(self):\n"
            "        return 'abc'\n"
            "\n"
            "    def test_a_quieted_case(self):\n"
            "        touched = ROOT.name\n"
            "        self.assertEqual(self.pinned(), 'abc')\n"
        )
        self.assert_vacuous(body)

    def test_a_helper_returning_a_fixture_read_still_passes(self):
        # The control in the other direction. A helper
        # that hands back what it read from a fixture
        # returns a value the reading cannot settle, so
        # the assertion over its call keeps its credit.
        body = (
            "import unittest\n"
            "from pathlib import Path\n"
            "ROOT = Path('.')\n"
            "\n"
            "\n"
            "class TestSomething(unittest.TestCase):\n"
            "    def pinned(self):\n"
            "        return ROOT.name\n"
            "\n"
            "    def test_a_case(self):\n"
            "        touched = ROOT.name\n"
            "        self.assertEqual(self.pinned(), 'abc')\n"
        )
        self.assert_clean(body)


if __name__ == "__main__":
    unittest.main()
