#!/usr/bin/env python3
"""Reject test methods that cannot fail for a real reason.

R23-RT-01. The round 23 red team proved that softening a check
together with its paired test defeats the gate in silence. A
fix loop that replaces a test body with a vacuous pass, or with
a single assertion that is always true and no fixture at all,
keeps every other script green. This guard is the mechanical
answer for that attack shape. It parses every tests/test_*.py
with ast and requires each test method to carry a real
assertion and to touch a fixture.

A real assertion argues about a value. An assert statement
whose test is a bare constant, and a self.assert call whose
positional arguments are all constants, argue about nothing,
so neither counts. A with self.assertRaises block counts,
because it argues about the error a call raises. An assertion
may live in a same class helper the test calls, when the
helper's name starts with _assert, because the suite uses that
shape for shared pins.

A fixture touch means the body reaches for something beyond
the assertion itself. Any name other than self, True, False,
and None counts, and so does any attribute access that is not
the assertion call, like self.mod or self.extract or the
fixture state set up in setUp. A body of self.assertTrue(True)
touches nothing and fails both halves.

The honest limit is recorded in the decision record. This
guard catches vacuous bodies, not a subtle tautology that
argues about fixture derived values. The spec lane diff review
stays the guard for that shape.
"""

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = ROOT / "tests"

EXEMPT_NAMES = {"self", "True", "False", "None"}


def assertion_calls(method):
    """Every assert form call in the method body."""
    found = []
    for child in ast.walk(method):
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Attribute):
                name = func.attr
            elif isinstance(func, ast.Name):
                name = func.id
            else:
                continue
            if name.startswith("assert") or name.startswith("fail"):
                found.append((child, name))
    return found


def has_assert_statement(method):
    return any(
        isinstance(child, ast.Assert) for child in ast.walk(method)
    )


def is_nontrivial_assertion(call):
    """Whether the assertion argues about a value.

    A with self.assertRaises block argues about the raised
    error. Any other assert form with no positional arguments
    argues through its message or not at all, and one whose
    positional arguments are all bare constants argues about
    nothing, like self.assertTrue(True) or self.assertEqual(1, 1).
    """
    node, name = call
    if name == "assertRaises":
        return True
    args = node.args
    if not args:
        return True
    return any(
        not isinstance(arg, ast.Constant) for arg in args
    )


def real_assertion(method, helpers):
    """Whether the method carries a real assertion.

    helpers maps the names of the class's non test methods to
    whether they hold an assertion, so a test that delegates to
    a shared _assert helper still counts.
    """
    for child in ast.walk(method):
        if isinstance(child, ast.Assert) and not isinstance(
            child.test, ast.Constant
        ):
            return True
    if any(is_nontrivial_assertion(c) for c in assertion_calls(method)):
        return True
    for child in ast.walk(method):
        if isinstance(child, ast.Call) and isinstance(
            child.func, ast.Attribute
        ):
            target = child.func.attr
            if target in helpers and helpers[target]:
                return True
    return False


def fixture_touch(method):
    """Whether the body reaches beyond the assertion itself."""
    for child in ast.walk(method):
        if isinstance(child, ast.Name):
            if child.id not in EXEMPT_NAMES:
                return True
        elif isinstance(child, ast.Attribute):
            attr = child.attr
            if not attr.startswith("assert") and not attr.startswith(
                "fail"
            ):
                return True
    return False


def vacuity_problems(root=None):
    """Problems with vacuous test methods under tests/."""
    root = ROOT if root is None else root
    tests_dir = root / "tests"
    problems = []
    for path in sorted(tests_dir.glob("test_*.py")):
        try:
            tree = ast.parse(
                path.read_text(encoding="utf-8"), filename=str(path)
            )
        except (OSError, SyntaxError) as exc:
            problems.append(
                "%s does not parse, %s" % (path.name, exc)
            )
            continue
        for cls in [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
        ]:
            helpers = {}
            for item in cls.body:
                if isinstance(item, ast.FunctionDef) and not (
                    item.name.startswith("test_")
                ):
                    helpers[item.name] = bool(
                        assertion_calls(item)
                    ) or has_assert_statement(item)
            for item in cls.body:
                if isinstance(item, ast.FunctionDef) and item.name.startswith(
                    "test_"
                ):
                    where = "%s %s" % (path.name, item.name)
                    if not real_assertion(item, helpers):
                        problems.append(
                            "%s carries no real assertion, so it "
                            "cannot fail for a real reason" % where
                        )
                    if not fixture_touch(item):
                        problems.append(
                            "%s never touches a fixture, so it "
                            "argues about nothing the suite "
                            "exercises" % where
                        )
    return problems


def main(root=None):
    problems = vacuity_problems(root)
    if problems:
        for problem in problems:
            print("check_test_vacuity: %s" % problem, file=sys.stderr)
        return 1
    print(
        "check_test_vacuity: every test method carries a real "
        "assertion and touches a fixture"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
