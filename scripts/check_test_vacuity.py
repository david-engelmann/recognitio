#!/usr/bin/env python3
"""Reject test methods that cannot fail for a real reason.

R23-RT-01. The round 23 red team proved that softening a check
together with its paired test defeats the gate in silence. A
fix loop that replaces a test body with a vacuous pass, or with
a single assertion that is always true and no fixture at all,
keeps every other script green. This guard is the mechanical
answer for that attack shape. It parses every discovered test
file with ast and requires each test method to carry a real
assertion and to touch a fixture.

A real assertion argues about a value. An assert statement
whose test is a bare constant, and a self.assert call whose
positional arguments are all constants, argue about nothing,
so neither counts. A with self.assertRaises block counts,
because it argues about the error a call raises. An assertion
may live in a same class helper the test calls, because the
suite uses that shape for shared pins, but the helper body is
judged by the same rules as a test body, so a helper holding
only an always true assertion no longer launders one in.

Constants are tracked through simple assignments inside one
body. A name bound to a literal, or to an expression built
only from literals and such names, counts as a constant at
the points where that binding still stands, so a comparison
of one such name against itself, or of two such names, or of
a name against the literal it was bound to, argues about
nothing. A name bound to a computed value, a call result or
a fixture read counts as a value, so the common shape of a
literal expectation compared against a fixture result still
counts in full. A helper is judged at each call site, so a
parameter bound to a literal at the call, or left at a
literal default, counts as a constant inside the helper for
that call, while a parameter passed a fixture value counts
as a value there.

Only live assertions count. An assertion after a return or a
raise or a break or a continue in the same block never runs.
An assertion in a branch a constant condition closes never
runs. An assertion inside a try whose handler catches the
assertion error and does not raise again cannot fail the
test, and the same holds inside a suppress call for the
assertion error. An assertion inside a nested function
counts only when the enclosing body calls or passes that
function on.

Discovery matches the runners. Files are found with the
test*.py pattern the unittest loader uses and with the
*_test.py pattern pytest uses. Plain and asynchronous
methods whose names start with test are inspected, inside
classes and at module level.

The honest limits are recorded here and the printed success
line is narrowed to them. This guard catches vacuous bodies,
dead assertions, swallowed assertions and constant
laundering through names and helpers. It does not catch a
subtle tautology that argues about fixture derived values,
such as reading one file twice and comparing the two reads,
because whether such a comparison can fail depends on what
the called code does at run time and no static reading of
one body can settle that in general. It does not enumerate
tests built at run time by decorators, by load_tests or by
attribute assignment, and it does not follow helpers held
in another class or another module. Assertions guarded by a
data dependent condition that happens never to hold, and
assertions after a call that happens never to return, are
likewise beyond a static reading. The spec lane diff review
stays the guard for those shapes.
"""

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = ROOT / "tests"

EXEMPT_NAMES = {"self"}

UNKNOWN = object()

OPERAND_COUNTS = {
    "assertTrue": 1,
    "assertFalse": 1,
    "assertIsNone": 1,
    "assertIsNotNone": 1,
    "assertEqual": 2,
    "assertNotEqual": 2,
    "assertIs": 2,
    "assertIsNot": 2,
    "assertIn": 2,
    "assertNotIn": 2,
    "assertIsInstance": 2,
    "assertNotIsInstance": 2,
    "assertGreater": 2,
    "assertGreaterEqual": 2,
    "assertLess": 2,
    "assertLessEqual": 2,
    "assertAlmostEqual": 2,
    "assertNotAlmostEqual": 2,
    "assertSequenceEqual": 2,
    "assertListEqual": 2,
    "assertTupleEqual": 2,
    "assertSetEqual": 2,
    "assertDictEqual": 2,
    "assertMultiLineEqual": 2,
    "assertRegex": 2,
    "assertNotRegex": 2,
    "assertCountEqual": 2,
    "assertEquals": 2,
    "assertNotEquals": 2,
    "assertAlmostEquals": 2,
    "assertNotAlmostEquals": 2,
    "failIfEqual": 2,
    "failUnlessEqual": 2,
    "failIf": 1,
    "failUnless": 1,
    "failIfAlmostEqual": 2,
    "failUnlessAlmostEqual": 2,
}

SELF_COMPARISON_NAMES = {
    "assertEqual",
    "assertNotEqual",
    "assertIs",
    "assertIsNot",
    "assertGreater",
    "assertGreaterEqual",
    "assertLess",
    "assertLessEqual",
    "assertAlmostEqual",
    "assertNotAlmostEqual",
    "assertDictEqual",
    "assertListEqual",
    "assertTupleEqual",
    "assertSetEqual",
    "assertSequenceEqual",
    "assertMultiLineEqual",
    "assertCountEqual",
    "assertEquals",
    "assertNotEquals",
}

CONTEXT_NAMES = {
    "assertRaises",
    "assertRaisesRegex",
    "assertWarns",
    "assertWarnsRegex",
    "assertLogs",
    "assertNoLogs",
}

CALLABLE_CONTEXT_NAMES = {
    "assertRaises",
    "assertRaisesRegex",
    "assertWarns",
    "assertWarnsRegex",
}

SWALLOW_NAMES = {"AssertionError", "Exception", "BaseException"}


def eval_constant(node, values):
    """The value of a pure constant expression, or UNKNOWN."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return values.get(node.id, UNKNOWN)
    if isinstance(node, ast.UnaryOp):
        operand = eval_constant(node.operand, values)
        if operand is UNKNOWN:
            return UNKNOWN
        try:
            if isinstance(node.op, ast.Not):
                return not operand
            if isinstance(node.op, ast.USub):
                return -operand
            if isinstance(node.op, ast.UAdd):
                return +operand
            if isinstance(node.op, ast.Invert):
                return ~operand
        except Exception:
            return UNKNOWN
        return UNKNOWN
    if isinstance(node, ast.BoolOp):
        parts = [eval_constant(value, values) for value in node.values]
        if any(part is UNKNOWN for part in parts):
            return UNKNOWN
        if isinstance(node.op, ast.And):
            result = parts[-1]
            for part in parts:
                if not part:
                    result = part
                    break
            return result
        result = parts[-1]
        for part in parts:
            if part:
                result = part
                break
        return result
    if isinstance(node, ast.BinOp):
        left = eval_constant(node.left, values)
        right = eval_constant(node.right, values)
        if left is UNKNOWN or right is UNKNOWN:
            return UNKNOWN
        try:
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Mod):
                return left % right
        except Exception:
            return UNKNOWN
        return UNKNOWN
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        parts = [eval_constant(elt, values) for elt in node.elts]
        if any(part is UNKNOWN for part in parts):
            return UNKNOWN
        if isinstance(node, ast.Tuple):
            return tuple(parts)
        if isinstance(node, ast.List):
            return parts
        try:
            return frozenset(parts)
        except Exception:
            return UNKNOWN
    if isinstance(node, ast.Dict):
        keys = [eval_constant(key, values) for key in node.keys]
        vals = [eval_constant(value, values) for value in node.values]
        if any(part is UNKNOWN for part in keys + vals):
            return UNKNOWN
        try:
            return tuple(zip(keys, vals))
        except Exception:
            return UNKNOWN
    if isinstance(node, ast.Subscript):
        base = eval_constant(node.value, values)
        index = eval_constant(node.slice, values)
        if base is UNKNOWN or index is UNKNOWN:
            return UNKNOWN
        try:
            return base[index]
        except Exception:
            return UNKNOWN
    if isinstance(node, ast.Compare):
        left = eval_constant(node.left, values)
        parts = [eval_constant(comp, values) for comp in node.comparators]
        if left is UNKNOWN or any(part is UNKNOWN for part in parts):
            return UNKNOWN
        try:
            current = left
            for op, part in zip(node.ops, parts):
                if isinstance(op, ast.Eq):
                    outcome = current == part
                elif isinstance(op, ast.NotEq):
                    outcome = current != part
                elif isinstance(op, ast.Is):
                    outcome = current is part
                elif isinstance(op, ast.IsNot):
                    outcome = current is not part
                elif isinstance(op, ast.Lt):
                    outcome = current < part
                elif isinstance(op, ast.LtE):
                    outcome = current <= part
                elif isinstance(op, ast.Gt):
                    outcome = current > part
                elif isinstance(op, ast.GtE):
                    outcome = current >= part
                elif isinstance(op, ast.In):
                    outcome = current in part
                elif isinstance(op, ast.NotIn):
                    outcome = current not in part
                else:
                    return UNKNOWN
                if not outcome:
                    return False
                current = part
            return True
        except Exception:
            return UNKNOWN
    if isinstance(node, ast.IfExp):
        test = eval_constant(node.test, values)
        if test is UNKNOWN:
            return UNKNOWN
        branch = node.body if test else node.orelse
        return eval_constant(branch, values)
    if isinstance(node, ast.JoinedStr):
        parts = [eval_constant(value, values) for value in node.values]
        if any(part is UNKNOWN for part in parts):
            return UNKNOWN
        return "".join(str(part) for part in parts)
    if isinstance(node, ast.FormattedValue):
        return eval_constant(node.value, values)
    if isinstance(node, ast.Starred):
        return eval_constant(node.value, values)
    return UNKNOWN


def is_constant_expression(node, values):
    """Whether the expression is built only from constants."""
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, ast.Name):
        return node.id in values
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return all(
            is_constant_expression(elt, values) for elt in node.elts
        )
    if isinstance(node, ast.Dict):
        return all(
            key is None or is_constant_expression(key, values)
            for key in node.keys
        ) and all(
            is_constant_expression(value, values)
            for value in node.values
        )
    if isinstance(node, ast.UnaryOp):
        return is_constant_expression(node.operand, values)
    if isinstance(node, ast.BinOp):
        return is_constant_expression(
            node.left, values
        ) and is_constant_expression(node.right, values)
    if isinstance(node, ast.BoolOp):
        return all(
            is_constant_expression(value, values)
            for value in node.values
        )
    if isinstance(node, ast.Compare):
        return is_constant_expression(node.left, values) and all(
            is_constant_expression(comp, values)
            for comp in node.comparators
        )
    if isinstance(node, ast.IfExp):
        return all(
            is_constant_expression(part, values)
            for part in (node.test, node.body, node.orelse)
        )
    if isinstance(node, ast.Subscript):
        return is_constant_expression(
            node.value, values
        ) and is_constant_expression(node.slice, values)
    if isinstance(node, ast.JoinedStr):
        return all(
            is_constant_expression(value, values)
            for value in node.values
        )
    if isinstance(node, ast.FormattedValue):
        return is_constant_expression(node.value, values)
    if isinstance(node, ast.Starred):
        return is_constant_expression(node.value, values)
    return False


def self_comparison(node):
    """Whether a comparison sets a plain value against itself."""
    if not isinstance(node, ast.Compare):
        return False
    if len(node.ops) != 1 or len(node.comparators) != 1:
        return False
    if not isinstance(
        node.ops[0],
        (
            ast.Eq,
            ast.NotEq,
            ast.Is,
            ast.IsNot,
            ast.Lt,
            ast.LtE,
            ast.Gt,
            ast.GtE,
        ),
    ):
        return False
    left = node.left
    right = node.comparators[0]
    if isinstance(left, ast.Call) or isinstance(right, ast.Call):
        return False
    return ast.dump(left) == ast.dump(right)


def bound_names(target):
    names = []
    for child in ast.walk(target):
        if isinstance(child, ast.Name):
            names.append(child.id)
    return names


def handler_swallows_assertion(handler):
    """Whether a handler catches the assertion error for good."""
    if handler.type is None:
        catches = True
    else:
        names = set()
        for child in ast.walk(handler.type):
            if isinstance(child, ast.Name):
                names.add(child.id)
            elif isinstance(child, ast.Attribute):
                names.add(child.attr)
        catches = bool(names & SWALLOW_NAMES)
    if not catches:
        return False
    for child in ast.walk(handler):
        if isinstance(child, ast.Raise):
            return False
        if isinstance(child, ast.Assert):
            return False
        if isinstance(child, ast.Call):
            func = child.func
            name = None
            if isinstance(func, ast.Attribute):
                name = func.attr
            elif isinstance(func, ast.Name):
                name = func.id
            if name is not None and (
                name.startswith("assert") or name.startswith("fail")
            ):
                return False
    return True


def suppress_swallows(item):
    """Whether a with item suppresses the assertion error."""
    expr = item.context_expr
    if not isinstance(expr, ast.Call):
        return False
    func = expr.func
    name = None
    if isinstance(func, ast.Attribute):
        name = func.attr
    elif isinstance(func, ast.Name):
        name = func.id
    if name != "suppress":
        return False
    for arg in expr.args:
        for child in ast.walk(arg):
            if isinstance(child, ast.Name) and child.id in SWALLOW_NAMES:
                return True
            if isinstance(child, ast.Attribute) and (
                child.attr in SWALLOW_NAMES
            ):
                return True
    return False


class ScopeResult:
    def __init__(self):
        self.assertions = []
        self.called_names = []
        self.helper_calls = []
        self.referenced_names = set()
        self.fixture = False
        self.nested = {}
        self.context_call_ids = set()


class Collector:
    """Walk one body keeping only its live assertions."""

    def __init__(self, global_values):
        self.global_values = global_values

    def collect(self, func, seed=None, param_values=None):
        result = ScopeResult()
        values = dict(self.global_values if seed is None else seed)
        arguments = func.args
        params = set()
        for group in (
            arguments.posonlyargs,
            arguments.args,
            arguments.kwonlyargs,
        ):
            for arg in group:
                params.add(arg.arg)
        if arguments.vararg is not None:
            params.add(arguments.vararg.arg)
        if arguments.kwarg is not None:
            params.add(arguments.kwarg.arg)
        for name in params:
            values.pop(name, None)
        if param_values:
            values.update(param_values)
        self.walk_block(func.body, values, result, 0)
        for name, entry in list(result.nested.items()):
            node, snapshot = entry
            if name in result.referenced_names or (
                name in result.called_names
            ):
                sub = self.collect(node, seed=snapshot)
                result.assertions.extend(sub.assertions)
                result.called_names.extend(sub.called_names)
                result.helper_calls.extend(sub.helper_calls)
                result.fixture = result.fixture or sub.fixture
        return result

    def note_name(self, node, result):
        result.referenced_names.add(node.id)
        if node.id not in EXEMPT_NAMES:
            result.fixture = True

    def note_attribute(self, node, result):
        attr = node.attr
        if not attr.startswith("assert") and not attr.startswith(
            "fail"
        ):
            result.fixture = True

    def walk_block(self, stmts, values, result, swallowed):
        always = False
        for stmt in stmts:
            if always:
                break
            always = self.walk_stmt(stmt, values, result, swallowed)
        return always

    def merge_outcomes(self, values, outcomes):
        merged = {}
        names = set(values)
        for outcome in outcomes:
            names.update(outcome)
        for name in names:
            if all(name in outcome for outcome in outcomes):
                first = outcomes[0][name]
                if all(
                    outcome[name] is first
                    or outcome[name] == first
                    for outcome in outcomes
                ):
                    merged[name] = first
        values.clear()
        values.update(merged)

    def walk_stmt(self, stmt, values, result, swallowed):
        if isinstance(stmt, ast.Expr):
            self.walk_expr(stmt.value, values, result, swallowed)
            return False
        if isinstance(stmt, ast.Assign):
            self.walk_expr(stmt.value, values, result, swallowed)
            is_const = is_constant_expression(stmt.value, values)
            const_value = (
                eval_constant(stmt.value, values)
                if is_const
                else UNKNOWN
            )
            if all(
                isinstance(target, ast.Name)
                for target in stmt.targets
            ):
                for target in stmt.targets:
                    self.note_name(target, result)
                    if is_const:
                        values[target.id] = const_value
                    else:
                        values.pop(target.id, None)
                return False
            if (
                len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Tuple)
                and isinstance(stmt.value, ast.Tuple)
                and len(stmt.targets[0].elts) == len(stmt.value.elts)
                and all(
                    isinstance(elt, ast.Name)
                    for elt in stmt.targets[0].elts
                )
            ):
                for target, part in zip(
                    stmt.targets[0].elts, stmt.value.elts
                ):
                    self.note_name(target, result)
                    if is_constant_expression(part, values):
                        values[target.id] = eval_constant(
                            part, values
                        )
                    else:
                        values.pop(target.id, None)
                return False
            for target in stmt.targets:
                self.walk_expr(target, values, result, swallowed)
                for name in bound_names(target):
                    values.pop(name, None)
            return False
        if isinstance(stmt, ast.AnnAssign):
            if stmt.value is not None:
                self.walk_expr(stmt.value, values, result, swallowed)
            self.walk_expr(stmt.target, values, result, swallowed)
            for name in bound_names(stmt.target):
                if stmt.value is not None and is_constant_expression(
                    stmt.value, values
                ):
                    values[name] = eval_constant(stmt.value, values)
                else:
                    values.pop(name, None)
            return False
        if isinstance(stmt, ast.AugAssign):
            self.walk_expr(stmt.value, values, result, swallowed)
            self.walk_expr(stmt.target, values, result, swallowed)
            for name in bound_names(stmt.target):
                if name in values and is_constant_expression(
                    stmt.value, values
                ):
                    old = values[name]
                    rhs = eval_constant(stmt.value, values)
                    if old is UNKNOWN or rhs is UNKNOWN:
                        values[name] = UNKNOWN
                    else:
                        combined = ast.BinOp(
                            left=ast.Constant(value=old),
                            op=stmt.op,
                            right=ast.Constant(value=rhs),
                        )
                        values[name] = eval_constant(
                            combined, values
                        )
                else:
                    values.pop(name, None)
            return False
        if isinstance(stmt, ast.Return):
            if stmt.value is not None:
                self.walk_expr(stmt.value, values, result, swallowed)
            return True
        if isinstance(stmt, ast.Raise):
            if stmt.exc is not None:
                self.walk_expr(stmt.exc, values, result, swallowed)
            if stmt.cause is not None:
                self.walk_expr(stmt.cause, values, result, swallowed)
            return True
        if isinstance(stmt, (ast.Break, ast.Continue)):
            return True
        if isinstance(stmt, ast.Assert):
            result.assertions.append(
                ("assert", stmt, None, dict(values), False, swallowed)
            )
            self.walk_expr(stmt.test, values, result, swallowed)
            if stmt.msg is not None:
                self.walk_expr(stmt.msg, values, result, swallowed)
            return False
        if isinstance(stmt, ast.If):
            self.walk_expr(stmt.test, values, result, swallowed)
            known = (
                eval_constant(stmt.test, values)
                if is_constant_expression(stmt.test, values)
                else UNKNOWN
            )
            if known is not UNKNOWN:
                branch = stmt.body if known else stmt.orelse
                return self.walk_block(
                    branch, values, result, swallowed
                )
            body_values = dict(values)
            body_always = self.walk_block(
                stmt.body, body_values, result, swallowed
            )
            else_values = dict(values)
            else_always = False
            if stmt.orelse:
                else_always = self.walk_block(
                    stmt.orelse, else_values, result, swallowed
                )
            self.merge_outcomes(values, [body_values, else_values])
            return bool(stmt.orelse) and body_always and else_always
        if isinstance(stmt, ast.While):
            self.walk_expr(stmt.test, values, result, swallowed)
            known = (
                eval_constant(stmt.test, values)
                if is_constant_expression(stmt.test, values)
                else UNKNOWN
            )
            if known is not UNKNOWN and not known:
                self.walk_block(stmt.orelse, values, result, swallowed)
                return False
            body_values = dict(values)
            self.walk_block(stmt.body, body_values, result, swallowed)
            self.merge_outcomes(values, [values, body_values])
            if stmt.orelse:
                else_values = dict(values)
                self.walk_block(
                    stmt.orelse, else_values, result, swallowed
                )
                self.merge_outcomes(values, [values, else_values])
            return False
        if isinstance(stmt, (ast.For, ast.AsyncFor)):
            self.walk_expr(stmt.iter, values, result, swallowed)
            body_values = dict(values)
            for name in bound_names(stmt.target):
                body_values.pop(name, None)
            self.walk_expr(stmt.target, body_values, result, swallowed)
            self.walk_block(stmt.body, body_values, result, swallowed)
            self.merge_outcomes(values, [values, body_values])
            if stmt.orelse:
                else_values = dict(values)
                self.walk_block(
                    stmt.orelse, else_values, result, swallowed
                )
                self.merge_outcomes(values, [values, else_values])
            return False
        if isinstance(stmt, (ast.With, ast.AsyncWith)):
            body_swallowed = swallowed
            for item in stmt.items:
                if suppress_swallows(item):
                    body_swallowed = swallowed + 1
                if isinstance(item.context_expr, ast.Call):
                    result.context_call_ids.add(
                        id(item.context_expr)
                    )
                self.walk_expr(
                    item.context_expr, values, result, swallowed
                )
                if item.optional_vars is not None:
                    self.walk_expr(
                        item.optional_vars, values, result, swallowed
                    )
                    for name in bound_names(item.optional_vars):
                        values.pop(name, None)
            return self.walk_block(
                stmt.body, values, result, body_swallowed
            )
        try_types = [ast.Try]
        if hasattr(ast, "TryStar"):
            try_types.append(ast.TryStar)
        if isinstance(stmt, tuple(try_types)):
            swallows = any(
                handler_swallows_assertion(handler)
                for handler in stmt.handlers
            )
            body_values = dict(values)
            body_always = self.walk_block(
                stmt.body,
                body_values,
                result,
                swallowed + (1 if swallows else 0),
            )
            outcomes = [body_values]
            for handler in stmt.handlers:
                if handler.type is not None:
                    self.walk_expr(
                        handler.type, values, result, swallowed
                    )
                handler_values = dict(values)
                if handler.name:
                    handler_values.pop(handler.name, None)
                self.walk_block(
                    handler.body, handler_values, result, swallowed
                )
                outcomes.append(handler_values)
            if stmt.orelse:
                else_values = dict(values)
                self.walk_block(
                    stmt.orelse, else_values, result, swallowed
                )
                outcomes.append(else_values)
            self.merge_outcomes(values, outcomes)
            if stmt.finalbody:
                self.walk_block(
                    stmt.finalbody, values, result, swallowed
                )
            return body_always
        if isinstance(
            stmt, (ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            result.nested[stmt.name] = (stmt, dict(values))
            values.pop(stmt.name, None)
            for decorator in stmt.decorator_list:
                self.walk_expr(decorator, values, result, swallowed)
            return False
        if isinstance(stmt, ast.ClassDef):
            for decorator in stmt.decorator_list:
                self.walk_expr(decorator, values, result, swallowed)
            for base in stmt.bases:
                self.walk_expr(base, values, result, swallowed)
            body_values = dict(values)
            self.walk_block(stmt.body, body_values, result, swallowed)
            values.pop(stmt.name, None)
            return False
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            for alias in stmt.names:
                name = (alias.asname or alias.name).split(".")[0]
                values.pop(name, None)
            return False
        if isinstance(stmt, ast.Delete):
            for target in stmt.targets:
                self.walk_expr(target, values, result, swallowed)
                for name in bound_names(target):
                    values.pop(name, None)
            return False
        if isinstance(stmt, (ast.Global, ast.Nonlocal)):
            for name in stmt.names:
                values.pop(name, None)
            return False
        if isinstance(stmt, ast.Match):
            self.walk_expr(stmt.subject, values, result, swallowed)
            outcomes = []
            for case in stmt.cases:
                case_values = dict(values)
                if case.guard is not None:
                    self.walk_expr(
                        case.guard, case_values, result, swallowed
                    )
                self.walk_block(
                    case.body, case_values, result, swallowed
                )
                outcomes.append(case_values)
            if outcomes:
                self.merge_outcomes(values, outcomes + [dict(values)])
            return False
        for child in ast.iter_child_nodes(stmt):
            if isinstance(child, ast.expr):
                self.walk_expr(child, values, result, swallowed)
            elif isinstance(child, ast.stmt):
                self.walk_stmt(child, values, result, swallowed)
        return False

    def walk_expr(self, node, values, result, swallowed):
        if isinstance(node, ast.Lambda):
            for default in list(
                node.args.defaults
            ) + [
                item
                for item in node.args.kw_defaults
                if item is not None
            ]:
                self.walk_expr(default, values, result, swallowed)
            return
        if isinstance(node, ast.Call):
            func = node.func
            name = None
            if isinstance(func, ast.Attribute):
                name = func.attr
            elif isinstance(func, ast.Name):
                name = func.id
            if name is not None:
                result.called_names.append(name)
                result.helper_calls.append(
                    (name, node, dict(values))
                )
                if name.startswith("assert") or name.startswith(
                    "fail"
                ):
                    result.assertions.append(
                        (
                            "call",
                            node,
                            name,
                            dict(values),
                            id(node) in result.context_call_ids,
                            swallowed,
                        )
                    )
            if isinstance(func, ast.Lambda):
                lambda_values = dict(values)
                params = set()
                for group in (
                    func.args.posonlyargs,
                    func.args.args,
                    func.args.kwonlyargs,
                ):
                    for arg in group:
                        params.add(arg.arg)
                for param in params:
                    lambda_values.pop(param, None)
                self.walk_expr(
                    func.body, lambda_values, result, swallowed
                )
            else:
                self.walk_expr(func, values, result, swallowed)
            for arg in node.args:
                self.walk_expr(arg, values, result, swallowed)
            for keyword in node.keywords:
                self.walk_expr(
                    keyword.value, values, result, swallowed
                )
            return
        if isinstance(node, ast.NamedExpr):
            self.walk_expr(node.value, values, result, swallowed)
            if isinstance(node.target, ast.Name):
                self.note_name(node.target, result)
                if is_constant_expression(node.value, values):
                    values[node.target.id] = eval_constant(
                        node.value, values
                    )
                else:
                    values.pop(node.target.id, None)
            return
        if isinstance(node, ast.Name):
            self.note_name(node, result)
            return
        if isinstance(node, ast.Attribute):
            self.note_attribute(node, result)
            self.walk_expr(node.value, values, result, swallowed)
            return
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.expr):
                self.walk_expr(child, values, result, swallowed)
            elif isinstance(child, ast.stmt):
                self.walk_stmt(child, values, result, swallowed)
            elif isinstance(child, ast.comprehension):
                self.walk_expr(
                    child.iter, values, result, swallowed
                )
                if child.target is not None:
                    for name in bound_names(child.target):
                        values.pop(name, None)
                for condition in child.ifs:
                    self.walk_expr(
                        condition, values, result, swallowed
                    )


def assertion_record_is_real(record):
    kind, node, name, values, in_context, swallowed = record
    if swallowed:
        return False
    if kind == "assert":
        test = node.test
        if is_constant_expression(test, values):
            return False
        if self_comparison(test):
            return False
        if isinstance(test, ast.UnaryOp) and isinstance(
            test.op, ast.Not
        ):
            if is_constant_expression(test.operand, values):
                return False
            if self_comparison(test.operand):
                return False
        return True
    if name == "fail":
        return True
    if name in CONTEXT_NAMES:
        if in_context:
            return True
        if name in CALLABLE_CONTEXT_NAMES and len(node.args) >= 2:
            return True
        return False
    count = OPERAND_COUNTS.get(name)
    if count is None:
        return False
    operands = node.args[:count]
    if not operands:
        return False
    if all(
        is_constant_expression(operand, values)
        for operand in operands
    ):
        return False
    if (
        count == 2
        and name in SELF_COMPARISON_NAMES
        and len(operands) == 2
        and not isinstance(operands[0], ast.Call)
        and not isinstance(operands[1], ast.Call)
        and ast.dump(operands[0]) == ast.dump(operands[1])
    ):
        return False
    if count == 1:
        operand = operands[0]
        if self_comparison(operand):
            return False
        if isinstance(operand, ast.UnaryOp) and isinstance(
            operand.op, ast.Not
        ) and self_comparison(operand.operand):
            return False
    return True


def scope_is_real(result, resolve_call):
    if any(
        assertion_record_is_real(record)
        for record in result.assertions
    ):
        return True
    for name, node, snapshot in result.helper_calls:
        if resolve_call(name, node, snapshot)[0]:
            return True
    return False


def scope_fixture(result, resolve_call):
    if result.fixture:
        return True
    for name, node, snapshot in result.helper_calls:
        if resolve_call(name, node, snapshot)[1]:
            return True
    return False


def module_global_values(tree):
    """Module level names bound only to constant expressions."""
    values = {}
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign):
            is_const = is_constant_expression(stmt.value, values)
            for target in stmt.targets:
                for name in bound_names(target):
                    if (
                        is_const
                        and len(stmt.targets) == 1
                        and isinstance(target, ast.Name)
                    ):
                        values[name] = eval_constant(
                            stmt.value, values
                        )
                    else:
                        values.pop(name, None)
        elif isinstance(stmt, ast.AnnAssign) and (
            stmt.value is not None
        ):
            for name in bound_names(stmt.target):
                values.pop(name, None)
    return values


def vacuity_problems(root=None):
    """Problems with vacuous test methods under tests/."""
    root = ROOT if root is None else root
    tests_dir = root / "tests"
    problems = []
    paths = set()
    if tests_dir.is_dir():
        paths.update(tests_dir.glob("test*.py"))
        paths.update(tests_dir.glob("*_test.py"))
    for path in sorted(paths):
        try:
            tree = ast.parse(
                path.read_text(encoding="utf-8"), filename=str(path)
            )
        except (OSError, SyntaxError) as exc:
            problems.append(
                "%s does not parse, %s" % (path.name, exc)
            )
            continue
        global_values = module_global_values(tree)
        collector = Collector(global_values)

        def no_resolve(name, node, snapshot):
            return (False, False)

        def check(where, result, resolve_call):
            if not scope_is_real(result, resolve_call):
                problems.append(
                    "%s carries no real assertion, so it "
                    "cannot fail for a real reason" % where
                )
            if not scope_fixture(result, resolve_call):
                problems.append(
                    "%s never touches a fixture, so it "
                    "argues about nothing the suite "
                    "exercises" % where
                )

        for item in tree.body:
            if isinstance(
                item, (ast.FunctionDef, ast.AsyncFunctionDef)
            ) and item.name.startswith("test"):
                result = collector.collect(item)
                check(
                    "%s %s" % (path.name, item.name),
                    result,
                    no_resolve,
                )
        for cls in [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
        ]:
            methods = [
                item
                for item in cls.body
                if isinstance(
                    item, (ast.FunctionDef, ast.AsyncFunctionDef)
                )
            ]
            helpers = {
                item.name: item
                for item in methods
                if not item.name.startswith("test")
            }
            resolved = {}
            visiting = set()

            def param_bindings(func, node, snapshot):
                bindings = {}
                arguments = func.args
                positional = [
                    arg.arg
                    for arg in (
                        list(arguments.posonlyargs)
                        + list(arguments.args)
                    )
                ]
                defaults = {}
                offset = len(positional) - len(arguments.defaults)
                for index, default in enumerate(arguments.defaults):
                    defaults[positional[offset + index]] = default
                for arg, default in zip(
                    arguments.kwonlyargs, arguments.kw_defaults
                ):
                    if default is not None:
                        defaults[arg.arg] = default
                keywords = {
                    keyword.arg: keyword.value
                    for keyword in node.keywords
                    if keyword.arg is not None
                }
                starred = any(
                    isinstance(arg, ast.Starred) for arg in node.args
                )

                def bind(param, expr, values):
                    if expr is not None and is_constant_expression(
                        expr, values
                    ):
                        bindings[param] = eval_constant(
                            expr, values
                        )

                for index, param in enumerate(positional):
                    if starred:
                        break
                    if index < len(node.args):
                        bind(param, node.args[index], snapshot)
                    elif param in keywords:
                        bind(param, keywords[param], snapshot)
                    elif param in defaults:
                        bind(
                            param,
                            defaults[param],
                            global_values,
                        )
                for arg in arguments.kwonlyargs:
                    param = arg.arg
                    if param in keywords:
                        bind(param, keywords[param], snapshot)
                    elif param in defaults:
                        bind(
                            param,
                            defaults[param],
                            global_values,
                        )
                return bindings

            def resolve_call(name, node, snapshot):
                if name not in helpers:
                    return (False, False)
                bindings = param_bindings(
                    helpers[name], node, snapshot
                )
                key = (
                    name,
                    repr(
                        sorted(
                            (param, repr(value))
                            for param, value in bindings.items()
                        )
                    ),
                )
                if key in resolved:
                    return resolved[key]
                if key in visiting:
                    return (False, False)
                visiting.add(key)
                sub = collector.collect(
                    helpers[name], param_values=bindings
                )
                value = (
                    scope_is_real(sub, resolve_call),
                    scope_fixture(sub, resolve_call),
                )
                visiting.discard(key)
                resolved[key] = value
                return value

            for item in methods:
                if item.name.startswith("test"):
                    result = collector.collect(item)
                    check(
                        "%s %s" % (path.name, item.name),
                        result,
                        resolve_call,
                    )
    return problems


def main(root=None):
    problems = vacuity_problems(root)
    if problems:
        for problem in problems:
            print("check_test_vacuity: %s" % problem, file=sys.stderr)
        return 1
    print(
        "check_test_vacuity: every discovered test method "
        "carries a live nontrivial assertion and touches a "
        "fixture, within the limits the guard docstring records"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
