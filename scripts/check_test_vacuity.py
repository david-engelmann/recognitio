#!/usr/bin/env python3
"""Reject test methods that carry no real assertion this
guard can follow.

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
counts in full.

Pure calls over constants count as constants on the same
reading. A call to a builtin whose result depends only on
its arguments, such as a length or a conversion or an
ordering, and a pure method call on a constant receiver,
such as a case form or a join, are constant expressions
when every argument is one, and a name that names a
builtin counts as a constant as well, so an assertion
whose operands are built only in those ways argues about
nothing in the same way a bare literal does. A call over
a value counts as a value, and a call to any other
function counts as a value, so a length or a conversion
or a sort of a fixture read keeps its credit in full. A
pure call over a name bound to a mutable container keeps
its credit as well, because the container can gain
contents through a nested function or a callback the
guard cannot see into, and the call then argues about
what the container holds at run time. A
constant binding stops standing where a mutating method
call is made on the name, because the value after such a
call is the value the call leaves behind and not the
value the binding wrote, so a container filled from a
fixture keeps the credit its contents earn.

The same reading reaches four spellings that settle a
call in the text of the same body. A name bound in the
body to a pure builtin stands for that builtin when it
is called, and a pure builtin reached as an attribute
of the builtins module counts in the same way, whether
the module stands under its own name or under an import
alias and whether the builtin came in through a from
import under another name. A comprehension counts as a
constant when its iterable is constant on this reading
and its element expression is constant for every item
the iterable holds, and a lambda called where it is
written counts by its body with its parameters bound
to the call arguments. A lambda held in a name and
called at a later point is not followed to that call,
and an alias bound to anything but a pure builtin is
not a pure call, so both shapes keep the credit a call
over a value keeps.

A helper is judged at each call site, so a
parameter bound to a scalar literal at the call, or left
at a scalar literal default, counts as a constant inside
the helper for that call, while a parameter passed a
fixture value counts as a value there. A parameter bound
to a list literal at the call stands under the mutable
container reading instead, for the reason that reading
records, so the call site binding does not settle what
the helper reads out of the list.

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

Discovery carries a floor, in the style of the sibling
discovery gates. A tests directory that does not stand, a
tests directory holding no test file, and a discovery that
finds no test method at all are each a problem by name, so
the guard never prints its success sentence over an absent
or empty suite. A discovered test file that stands empty
is a problem by name on the same reading, because a suite
file truncated to nothing would otherwise pass in silence
while the global floor still saw the files around it.
A scoped run of this guard alone therefore fails on the
absence the full gate would catch at the discover step.

An assertion about a mock call state argues about nothing
the suite exercises. A name bound in the body to a mock, or
to an attribute or a call of one, or handed in as a patch
stand in, is a mock on this reading, and an assertion whose
operands argue only about such a name and its call state,
the called flag and the call count and the recorded call
arguments among them, counts no more than a constant
assertion does. A direct assert call on the mock itself
already counted for nothing under the operand table. An
assertion standing beside it that touches a real return or
a real output keeps its credit in full, so a test that
checks a call and also checks what the call produced is
judged by the second assertion and not by the first.
The patch route honours every spelling that hands back a
mock, the bare patch and its object and multiple forms and
the same forms under the mock and unittest.mock module
spellings, while the dict patching spelling hands back the
patched mapping itself and stands outside the mock set, so
an assertion about that mapping entries keeps its credit.
The route also follows the patch family to where a test
actually holds it. A name the file imports a patch form
under stands for that form wherever the name is called, so
an import alias for the patch family is read as the patch
form it names. A patcher a body builds from a patch form
and starts by hand hands back its mock through the start
call, and that name is read as a mock as well. And a patch
form standing in a test method decorator list hands its
mock in as the method argument it binds, in argument order
after the receiver, so that parameter name is read as a
mock for that method. A test method the runtime builds
through a decorating wrapper stands outside this reading
here, as it does below, because the wrapper and not the
written decorator list decides what each parameter
receives. Where a hand written wrapper stands in the
written list beneath a patch decorator, this reading
still binds the first parameter after the receiver to
the patch mock, so it can credit the wrong parameter,
and a test in that shape asserting only over the mock
passes this guard while pinning nothing.
Mock provenance also reaches past the method body, to a
mock assigned to self in a setUp method of the same class,
to a mock built at module level, and to a mock handed back
by a helper function in the same file. A value handed back
by a helper in the same class settles at the call site the
way a helper parameter settles there, so a helper in the
same class whose returns all settle as constants hands
back constants alone, and an assertion whose operands are
all constants on that reading argues about nothing in the
same way a bare literal does, whatever the outcome of the
comparison would be at run time. A helper with a return
the reading cannot settle hands back a value on this
reading, so the common shape of a helper that reads a
fixture and hands back what it read keeps its credit in
full.

A fail call inside a conditional branch or a
conditional expression does not count as a real
assertion on its own. Such a call guards an earlier
step, as a listing failure guard does, and it runs only
when its branch runs, so a test whose other
assertions are trivial and whose only credited call is a
conditional fail carries no live assertion about the
values it was written to pin. A branch the guard can
prove from constants is not conditional in this sense,
because its body runs whenever the enclosing body runs.
A fail call outside every conditional branch still
counts, because it runs whenever the test runs.

The honest limits are recorded here and the printed success
line is narrowed to them. This guard catches vacuous bodies,
dead assertions, swallowed assertions and constant
laundering through names, and through helpers in the two
shapes it follows, an assertion held inside a helper it
judges at the call site, and a value a same class helper
hands back where every return of that helper settles as a
constant. An assertion over constants alone is refused on
that reading even where the comparison would fail at run
time, because a test that argues only about constants
pins nothing about the code under test whatever its
outcome. It does not catch a
subtle tautology that argues about fixture derived values,
such as reading one file twice and comparing the two reads,
because whether such a comparison can fail depends on what
the called code does at run time and no static reading of
one body can settle that in general. It does not follow a
mock constructor reached under another name, whether the
constructor stands imported under an alias, or bound first
to a plain name and called through that name, or reached
through a getattr call, because the provenance reading
matches the constructor spellings it holds and no others.
A patch form bound first to a plain name and called
through that name stands outside the reading in the same
way, because the alias reading follows names bound by
import and no others.
It does not enumerate
tests built at run time by decorators, by load_tests or by
attribute assignment, and it does not follow helpers held
in another class or another module. It does not settle
what a list holds where a helper parameter binds that
list at a call site, so a test that hands its helper a
list literal holding the very problems it expects, and
asserts over that parameter inside the helper, passes
this guard while pinning nothing.
Assertions guarded by a
data dependent condition that happens never to hold, and
assertions after a call that happens never to return, are
likewise beyond a static reading. The spec lane diff review
stays the guard for those shapes. The printed failure lines
are narrowed to the same limits. A refusal names the shapes
this guard follows and the reach of its sight, rather than
claiming a test cannot fail at run time, because a test
that delegates its assertion to a helper in another class
can fail for a real reason this guard does not follow.
"""

import ast
import builtins
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

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

# Names that name a builtin value on the constant reading,
# so a builtin name standing as an assertion operand counts
# beside the literal operands it is compared with.
BUILTIN_NAMES = {
    "abs",
    "all",
    "any",
    "bool",
    "bytearray",
    "bytes",
    "complex",
    "dict",
    "float",
    "frozenset",
    "int",
    "isinstance",
    "len",
    "list",
    "max",
    "min",
    "object",
    "repr",
    "reversed",
    "round",
    "set",
    "sorted",
    "str",
    "sum",
    "tuple",
    "type",
}

# Builtin calls whose result depends only on their arguments.
PURE_CALL_NAMES = {
    "abs",
    "all",
    "any",
    "bool",
    "bytearray",
    "bytes",
    "complex",
    "dict",
    "float",
    "frozenset",
    "int",
    "isinstance",
    "len",
    "list",
    "max",
    "min",
    "repr",
    "reversed",
    "round",
    "set",
    "sorted",
    "str",
    "sum",
    "tuple",
    "type",
}

# Method calls on a constant receiver whose result depends
# only on the receiver and their arguments.
PURE_METHOD_NAMES = {
    "capitalize",
    "casefold",
    "center",
    "count",
    "index",
    "join",
    "ljust",
    "lower",
    "lstrip",
    "removeprefix",
    "removesuffix",
    "replace",
    "rjust",
    "rsplit",
    "rstrip",
    "split",
    "strip",
    "swapcase",
    "title",
    "upper",
    "zfill",
}

BUILTIN_VALUES = {
    name: getattr(builtins, name)
    for name in BUILTIN_NAMES
    if hasattr(builtins, name)
}

# Method calls that change the object they are called on, so
# a constant binding stops standing at such a call in the
# same way it stops standing at a rebinding. A set built by
# a constructor call and then filled by update calls holds
# what the update calls put in it and not the empty set the
# constructor returned, so the binding is dropped there.
# Names that build a mock when called, in their plain and
# module qualified spellings alike. A test that asserts only
# about the call state of an object built by one of these
# asserts about a stand in and not about the code under test.
MOCK_CTOR_NAMES = {
    "Mock",
    "MagicMock",
    "NonCallableMock",
    "NonCallableMagicMock",
    "PropertyMock",
    "AsyncMock",
    "create_autospec",
}

# Call names that hand a mock in as a stand in when they are
# used as a context manager with a bound name. The names are
# the suffix forms that remain after a module prefix is
# stripped, because the same patch family stands under the
# bare spelling and under the mock and unittest.mock module
# spellings. The dict spelling stands outside the set by
# design, because its bound name holds the patched mapping
# itself and not a mock, so an assertion about the entries
# of that mapping is a real assertion.
MOCK_PATCH_NAMES = {"patch", "patch.object", "patch.multiple"}


def is_mock_patch_name(dotted):
    """Whether a dotted call name is a mock handing patch form."""
    if not dotted:
        return False
    parts = dotted.split(".")
    if parts[:2] == ["unittest", "mock"]:
        parts = parts[2:]
    elif parts[:1] == ["mock"]:
        parts = parts[1:]
    return ".".join(parts) in MOCK_PATCH_NAMES


MOCK_MODULE_PREFIXES = (
    ("unittest", "mock"),
    ("mock",),
)


def file_patch_aliases(tree):
    """Names the file binds to patch family forms by import.

    An import of a patch form under another name hands the
    test that form under the alias, from unittest.mock import
    patch as swap being the plain shape, and a dotted import
    of the mock module under an alias hands its patch forms
    under that root, and the module a from import binds
    under an alias stands in the map the same way. The
    mapping is name to dotted form, and
    only the mock handing forms stand in it, so the dict
    spelling imported under an alias still binds the patched
    mapping and stays outside the mock set.
    """
    aliases = {}

    def note(module_parts, imported, bound):
        dotted = ".".join(list(module_parts) + [imported])
        if is_mock_patch_name(dotted):
            aliases[bound] = dotted
        elif imported == "mock" and list(
            module_parts
        ) == ["unittest"]:
            aliases[bound] = "unittest.mock"

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if not node.module:
                continue
            parts = node.module.split(".")
            for alias in node.names:
                note(parts, alias.name, alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                if alias.asname:
                    for prefix in MOCK_MODULE_PREFIXES:
                        if tuple(parts[:len(prefix)]) == prefix:
                            aliases[alias.asname] = ".".join(parts)
                elif len(parts) > 1:
                    aliases.setdefault(parts[0], parts[0])
    return aliases


def resolve_patch_form(dotted, aliases):
    """The mock handing patch form a call target stands for.

    The target may spell a patch form directly, reach one
    through a module alias the file imported, or be a bare
    name the file imported a patch form under. Returns the
    dotted spelling the name table reads, or None.
    """
    if not dotted:
        return None
    if is_mock_patch_name(dotted):
        return dotted
    parts = dotted.split(".")
    for cut in range(len(parts), 0, -1):
        head = ".".join(parts[:cut])
        if head in aliases:
            rest = parts[cut:]
            candidate = ".".join([aliases[head]] + rest)
            if is_mock_patch_name(candidate):
                return candidate
            return None
    return None


def patch_decorator_mocks(func, aliases):
    """Parameter names a patch decorator hands a mock to.

    A patch form in the decorator list of a method binds one
    mock argument per decorator, in argument order after the
    receiver. The patch decorators stack from the bottom of
    the list upward, so the decorator nearest the method
    binds the first mock parameter. A method the patch
    decorators cannot be counted for, a starred or keyword
    only parameter standing where a mock would bind, binds
    nothing on this reading.
    """
    count = 0
    for decorator in func.decorator_list:
        target = decorator
        if isinstance(target, ast.Call):
            target = target.func
        if resolve_patch_form(dotted_node_name(target), aliases):
            count += 1
    if not count:
        return set()
    positional = [
        arg.arg
        for arg in list(func.args.posonlyargs) + list(func.args.args)
    ]
    names = positional[1:1 + count]
    if len(names) != count:
        return set()
    return set(names)


def dotted_node_name(node):
    """The dotted name an attribute chain spells, or None."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def mock_prefixed(dotted, mock_names):
    """Whether a dotted name or one of its prefixes is a mock."""
    if not dotted:
        return False
    parts = dotted.split(".")
    return any(
        ".".join(parts[:index]) in mock_names
        for index in range(1, len(parts) + 1)
    )


def call_dotted_name(func):
    """The dotted name a call target spells, or its leaf name."""
    parts = []
    node = func
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return parts[0] if parts else None


def root_name(node):
    """The plain name at the root of an attribute chain."""
    while isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def is_mock_producing(node, mock_names, return_names=(), aliases=()):
    """Whether an expression builds or reaches a mock object."""
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "start":
            return is_mock_producing(
                func.value, mock_names, return_names, aliases
            )
        dotted = call_dotted_name(func)
        leaf = dotted.rsplit(".", 1)[-1] if dotted else None
        if leaf in MOCK_CTOR_NAMES:
            return True
        if dotted in return_names or leaf in return_names:
            return True
        if resolve_patch_form(dotted, aliases):
            return True
        return root_name(func) in mock_names
    if isinstance(node, ast.Attribute):
        return root_name(node) in mock_names or mock_prefixed(
            dotted_node_name(node), mock_names
        )
    if isinstance(node, ast.Name):
        return node.id in mock_names
    if isinstance(node, ast.Subscript):
        return is_mock_producing(
            node.value, mock_names, return_names, aliases
        )
    return False


def _body_assignments(func):
    """Assignment pairs in one body, as target names and values.

    Plain and annotated assignments both stand, in walk
    order, and each target contributes the names it binds.
    """
    pairs = []
    for node in ast.walk(func):
        if isinstance(node, ast.Assign):
            targets = []
            for target in node.targets:
                targets.extend(bound_names(target))
            pairs.append((targets, node.value))
        elif isinstance(node, ast.AnnAssign) and (
            node.value is not None
        ):
            pairs.append(
                (bound_names(node.target), node.value)
            )
    return pairs


def mock_names_in_body(func, return_names=(), aliases=()):
    """Names bound to a mock anywhere in one function body.

    The reading is static and whole body, in the same spirit
    as the constant tracking. A name bound to a mock and
    later rebound to a real value would still read as a
    mock here, and an assertion about the call state of
    such a name argues about a stand in on either binding,
    so the over reading fails in the safe direction.
    """
    names = set(patch_decorator_mocks(func, aliases))
    assignments = []
    for node in ast.walk(func):
        if isinstance(node, ast.Assign):
            targets = []
            for target in node.targets:
                targets.extend(bound_names(target))
            assignments.append((targets, node.value))
        elif isinstance(node, ast.AnnAssign) and (
            node.value is not None
        ):
            assignments.append(
                (bound_names(node.target), node.value)
            )
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if item.optional_vars is None:
                    continue
                if not isinstance(item.context_expr, ast.Call):
                    continue
                dotted = call_dotted_name(item.context_expr.func)
                leaf = dotted.rsplit(".", 1)[-1] if dotted else None
                if resolve_patch_form(dotted, aliases) or (
                    leaf in MOCK_CTOR_NAMES
                ):
                    names.update(bound_names(item.optional_vars))
    changed = True
    while changed:
        changed = False
        for targets, value in assignments:
            if is_mock_producing(value, names, return_names, aliases):
                for name in targets:
                    if name not in names:
                        names.add(name)
                        changed = True
    return names


def own_returns(func):
    """Return nodes that belong to one function body itself."""
    found = []
    stack = list(func.body)
    while stack:
        node = stack.pop()
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            continue
        if isinstance(node, ast.Return) and node.value is not None:
            found.append(node)
        stack.extend(ast.iter_child_nodes(node))
    return found


def function_returns_mock(func, return_names, extra_mocks=(),
                          aliases=()):
    """Whether one function hands a mock back to its caller."""
    local = mock_names_in_body(
        func, return_names, aliases
    ) | set(extra_mocks)
    return any(
        is_mock_producing(node.value, local, return_names, aliases)
        for node in own_returns(func)
    )


def file_mock_provenance(tree, aliases=()):
    """Module mock names and names of helpers returning a mock.

    Mock provenance does not stop at a test method body. A
    mock built once at module level, and a mock handed back
    by a helper function in the same file, are stand ins in
    the test methods that reach them in the same way a mock
    built in the body is, so both routes are read here in
    one fixpoint over the file.
    """
    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    return_names = set()
    module_mocks = set()
    changed = True
    while changed:
        changed = False
        for stmt in tree.body:
            value = None
            targets = []
            if isinstance(stmt, ast.Assign):
                value = stmt.value
                for target in stmt.targets:
                    targets.extend(bound_names(target))
            elif isinstance(stmt, ast.AnnAssign) and (
                stmt.value is not None
            ):
                value = stmt.value
                targets = bound_names(stmt.target)
            if value is not None and is_mock_producing(
                value, module_mocks, return_names, aliases
            ):
                for name in targets:
                    if name not in module_mocks:
                        module_mocks.add(name)
                        changed = True
        for func in functions:
            if func.name in return_names:
                continue
            if function_returns_mock(
                func, return_names, module_mocks, aliases
            ):
                return_names.add(func.name)
                changed = True
    return module_mocks, return_names


def class_setup_mock_names(cls, return_names, module_mocks,
                           aliases=()):
    """Dotted self names a setUp method in one class binds to a mock."""
    names = set()
    for method in cls.body:
        if not isinstance(
            method, (ast.FunctionDef, ast.AsyncFunctionDef)
        ) or method.name != "setUp":
            continue
        local = (
            mock_names_in_body(method, return_names, aliases)
            | set(module_mocks)
            | set(names)
        )
        assignments = []
        for node in ast.walk(method):
            if isinstance(node, ast.Assign):
                assignments.append((node.targets, node.value))
            elif isinstance(node, ast.AnnAssign) and (
                node.value is not None
            ):
                assignments.append(([node.target], node.value))
        changed = True
        while changed:
            changed = False
            known = local | set(names)
            for targets, value in assignments:
                if not is_mock_producing(
                    value, known, return_names, aliases
                ):
                    continue
                for target in targets:
                    dotted = dotted_node_name(target)
                    if dotted and dotted.startswith("self."):
                        if dotted not in names:
                            names.add(dotted)
                            changed = True
    return names


def contains_mock_reference(node, mock_names):
    """Whether an expression mentions a mock bound name."""
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and child.id in mock_names:
            return True
        if isinstance(child, ast.Attribute) and mock_prefixed(
            dotted_node_name(child), mock_names
        ):
            return True
    return False


def mock_only_expression(node, mock_names):
    """Whether an expression argues only about mocks and constants.

    A pure call over a mock call state, a comparison of a
    call count against a literal, and a boolean joining of
    called flags all stay inside the mock on this reading.
    Any name that is not a mock, and any call that is not a
    pure call or a call on a mock, takes the expression
    outside it.
    """
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, ast.Name):
        return node.id in mock_names
    if isinstance(node, ast.Attribute):
        if mock_prefixed(dotted_node_name(node), mock_names):
            return True
        return mock_only_expression(node.value, mock_names)
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Attribute):
            if not mock_only_expression(func.value, mock_names):
                return False
        elif isinstance(func, ast.Name):
            if func.id not in mock_names and (
                func.id not in PURE_CALL_NAMES
            ):
                return False
        else:
            return False
        return all(
            mock_only_expression(arg, mock_names) for arg in node.args
        ) and all(
            mock_only_expression(keyword.value, mock_names)
            for keyword in node.keywords
        )
    if isinstance(node, ast.UnaryOp):
        return mock_only_expression(node.operand, mock_names)
    if isinstance(node, ast.BoolOp):
        return all(
            mock_only_expression(value, mock_names)
            for value in node.values
        )
    if isinstance(node, ast.BinOp):
        return mock_only_expression(
            node.left, mock_names
        ) and mock_only_expression(node.right, mock_names)
    if isinstance(node, ast.Compare):
        return mock_only_expression(
            node.left, mock_names
        ) and all(
            mock_only_expression(part, mock_names)
            for part in node.comparators
        )
    if isinstance(node, ast.IfExp):
        return all(
            mock_only_expression(part, mock_names)
            for part in (node.test, node.body, node.orelse)
        )
    if isinstance(node, ast.Subscript):
        return mock_only_expression(
            node.value, mock_names
        ) and mock_only_expression(node.slice, mock_names)
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return all(
            mock_only_expression(part, mock_names)
            for part in node.elts
        )
    return False


MUTATING_METHOD_NAMES = {
    "add",
    "append",
    "clear",
    "discard",
    "extend",
    "insert",
    "pop",
    "remove",
    "reverse",
    "setdefault",
    "sort",
    "update",
}


def is_stable_value(value):
    """Whether a tracked value cannot change under its name.

    A name bound to a mutable container can gain new
    contents through a nested function or a callback the
    guard cannot see into, so a pure call over such a name
    may well argue about the contents the container holds
    at run time. A name bound to a value built only from
    stable parts cannot change without a rebinding, and
    every rebinding is tracked, so a pure call over it is
    a constant in full.
    """
    if value is UNKNOWN:
        return False
    if value is builtins:
        return True
    if any(value is known for known in BUILTIN_VALUES.values()):
        return True
    if isinstance(value, (str, bytes, int, float, bool, type)):
        return True
    if value is None:
        return True
    if isinstance(value, (tuple, frozenset)):
        return all(is_stable_value(part) for part in value)
    return False


def is_pure_builtin_value(value):
    """Whether a tracked value is one of the pure builtins."""
    return any(
        value is BUILTIN_VALUES[name]
        for name in PURE_CALL_NAMES
        if name in BUILTIN_VALUES
    )


def names_builtins_module(node, values):
    """Whether an expression names the builtins module.

    The module stands under its own name unless a binding
    in the body shadows it, and under an import alias the
    binding itself carries the module, so both spellings
    resolve here while a name bound to anything else does
    not.
    """
    if not isinstance(node, ast.Name):
        return False
    if node.id in values:
        return values[node.id] is builtins
    return node.id == "builtins"


def resolve_pure_callable(func, values):
    """The pure builtin a call target stands for, or None.

    A bare name stands for a pure builtin when its spelling
    is one or when the name is bound in the body to one,
    and an attribute of the builtins module stands for the
    builtin it names. A name bound to anything else stands
    for that thing and not for the builtin its spelling
    would otherwise name.
    """
    if isinstance(func, ast.Name):
        if func.id in values:
            value = values[func.id]
            if is_pure_builtin_value(value):
                return value
            return None
        if func.id in PURE_CALL_NAMES:
            return BUILTIN_VALUES.get(func.id)
        return None
    if isinstance(func, ast.Attribute):
        if names_builtins_module(func.value, values) and (
            func.attr in PURE_CALL_NAMES
        ):
            return BUILTIN_VALUES.get(func.attr)
    return None


def locally_bound_names(node):
    """Names bound inside an expression by its own parts.

    A comprehension binds its target names and a lambda
    binds its parameter names, so a use of such a name
    inside the expression reads the binding the expression
    itself makes and not a name the enclosing body holds.
    """
    names = set()
    for child in ast.walk(node):
        if isinstance(child, ast.comprehension):
            names.update(bound_names(child.target))
        elif isinstance(child, ast.Lambda):
            arguments = child.args
            for group in (
                arguments.posonlyargs,
                arguments.args,
                arguments.kwonlyargs,
            ):
                for arg in group:
                    names.add(arg.arg)
            if arguments.vararg is not None:
                names.add(arguments.vararg.arg)
            if arguments.kwarg is not None:
                names.add(arguments.kwarg.arg)
    return names


def is_constant_call_argument(node, values):
    """Whether a call argument is a constant in full.

    The expression must be a constant expression, and every
    name inside it must be a builtin name or a name bound to
    a stable value, for the reason is_stable_value records.
    """
    if not is_constant_expression(node, values):
        return False
    bound = locally_bound_names(node)
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            if child.id in bound:
                continue
            if child.id in BUILTIN_NAMES:
                continue
            if child.id in values and not is_stable_value(
                values[child.id]
            ):
                return False
    return True


def lambda_scope(func, node, values):
    """The values inside a lambda called where it is written.

    The parameters stand bound to the call arguments that
    settle as constants, or to their defaults where the
    call passes nothing, and every other parameter stands
    unbound, so a body that reads it is not a constant.
    The shape of the call must match the shape of the
    lambda, so a starred argument, a double starred
    keyword or a call with more arguments than the lambda
    takes settles nothing and returns None.
    """
    if any(isinstance(arg, ast.Starred) for arg in node.args):
        return None
    if any(keyword.arg is None for keyword in node.keywords):
        return None
    arguments = func.args
    positional = [
        arg.arg
        for arg in list(arguments.posonlyargs)
        + list(arguments.args)
    ]
    scope = dict(values)
    params = list(positional)
    params.extend(arg.arg for arg in arguments.kwonlyargs)
    if arguments.vararg is not None:
        params.append(arguments.vararg.arg)
    if arguments.kwarg is not None:
        params.append(arguments.kwarg.arg)
    for param in params:
        scope.pop(param, None)
    if len(node.args) > len(positional) and (
        arguments.vararg is None
    ):
        return None
    keywords = {
        keyword.arg: keyword.value for keyword in node.keywords
    }
    extra = set(keywords) - set(params)
    if extra and arguments.kwarg is None:
        return None
    defaults = {}
    offset = len(positional) - len(arguments.defaults)
    for index, default in enumerate(arguments.defaults):
        defaults[positional[offset + index]] = default
    for index, param in enumerate(positional):
        if index < len(node.args):
            value = eval_constant(node.args[index], values)
        elif param in keywords:
            value = eval_constant(keywords[param], values)
        elif param in defaults:
            value = eval_constant(defaults[param], values)
        else:
            continue
        if value is not UNKNOWN:
            scope[param] = value
    kw_defaults = {
        arg.arg: default
        for arg, default in zip(
            arguments.kwonlyargs, arguments.kw_defaults
        )
    }
    for arg in arguments.kwonlyargs:
        param = arg.arg
        if param in keywords:
            value = eval_constant(keywords[param], values)
        elif kw_defaults.get(param) is not None:
            value = eval_constant(kw_defaults[param], values)
        else:
            continue
        if value is not UNKNOWN:
            scope[param] = value
    return scope


def bind_comprehension_target(target, item, scope):
    """Bind one comprehension item to its target names."""
    if isinstance(target, ast.Name):
        scope[target.id] = item
        return True
    if isinstance(target, (ast.Tuple, ast.List)):
        try:
            parts = list(item)
        except Exception:
            return False
        if len(parts) != len(target.elts):
            return False
        return all(
            bind_comprehension_target(elt, part, scope)
            for elt, part in zip(target.elts, parts)
        )
    return False


def eval_comprehension(node, values):
    """The value of a comprehension over constants, or UNKNOWN."""
    results = []

    def step(index, scope):
        if index == len(node.generators):
            if isinstance(node, ast.DictComp):
                key = eval_constant(node.key, scope)
                value = eval_constant(node.value, scope)
                if key is UNKNOWN or value is UNKNOWN:
                    return False
                results.append((key, value))
                return True
            element = eval_constant(node.elt, scope)
            if element is UNKNOWN:
                return False
            results.append(element)
            return True
        generator = node.generators[index]
        iterable = eval_constant(generator.iter, scope)
        if iterable is UNKNOWN:
            return False
        try:
            items = list(iterable)
        except Exception:
            return False
        for item in items:
            inner = dict(scope)
            if not bind_comprehension_target(
                generator.target, item, inner
            ):
                return False
            settled = True
            for condition in generator.ifs:
                outcome = eval_constant(condition, inner)
                if outcome is UNKNOWN:
                    return False
                if not outcome:
                    settled = False
                    break
            if not settled:
                continue
            if not step(index + 1, inner):
                return False
        return True

    if not step(0, dict(values)):
        return UNKNOWN
    if isinstance(node, ast.SetComp):
        try:
            return frozenset(results)
        except Exception:
            return UNKNOWN
    if isinstance(node, ast.GeneratorExp):
        return tuple(results)
    if isinstance(node, ast.DictComp):
        return tuple(results)
    return results


def is_constant_comprehension(node, values):
    """Whether a comprehension is built only from constants.

    The iterable of each generator must be a constant call
    argument on the enclosing reading, so an iterable held
    in a name bound to a mutable container keeps the
    credit the mutable container reading keeps, and the
    element expression must be constant for every item
    the iterable holds with the target names bound to
    that item.
    """
    def step(index, scope):
        if index == len(node.generators):
            if isinstance(node, ast.DictComp):
                return is_constant_expression(
                    node.key, scope
                ) and is_constant_expression(node.value, scope)
            return is_constant_expression(node.elt, scope)
        generator = node.generators[index]
        if not is_constant_call_argument(generator.iter, scope):
            return False
        iterable = eval_constant(generator.iter, scope)
        if iterable is UNKNOWN:
            return False
        try:
            items = list(iterable)
        except Exception:
            return False
        for item in items:
            inner = dict(scope)
            if not bind_comprehension_target(
                generator.target, item, inner
            ):
                return False
            settled = True
            for condition in generator.ifs:
                if not is_constant_expression(condition, inner):
                    return False
                outcome = eval_constant(condition, inner)
                if outcome is UNKNOWN:
                    return False
                if not outcome:
                    settled = False
                    break
            if not settled:
                continue
            if not step(index + 1, inner):
                return False
        return True

    return step(0, dict(values))


def eval_pure_call(node, values):
    """The value of a pure call over constants, or UNKNOWN."""
    args = []
    for arg in node.args:
        if isinstance(arg, ast.Starred):
            return UNKNOWN
        value = eval_constant(arg, values)
        if value is UNKNOWN:
            return UNKNOWN
        args.append(value)
    keywords = {}
    for keyword in node.keywords:
        if keyword.arg is None:
            return UNKNOWN
        value = eval_constant(keyword.value, values)
        if value is UNKNOWN:
            return UNKNOWN
        keywords[keyword.arg] = value
    func = node.func
    target = resolve_pure_callable(func, values)
    if target is not None:
        try:
            return target(*args, **keywords)
        except Exception:
            return UNKNOWN
    if isinstance(func, ast.Lambda):
        scope = lambda_scope(func, node, values)
        if scope is None:
            return UNKNOWN
        return eval_constant(func.body, scope)
    if isinstance(func, ast.Attribute):
        if func.attr not in PURE_METHOD_NAMES:
            return UNKNOWN
        receiver = eval_constant(func.value, values)
        if receiver is UNKNOWN:
            return UNKNOWN
        try:
            return getattr(receiver, func.attr)(*args, **keywords)
        except Exception:
            return UNKNOWN
    return UNKNOWN


def eval_constant(node, values, helpers=None):
    """The value of a pure constant expression, or UNKNOWN."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in values:
            return values[node.id]
        return BUILTIN_VALUES.get(node.id, UNKNOWN)
    if isinstance(node, ast.Call):
        if helpers:
            target = None
            if isinstance(node.func, ast.Name):
                target = node.func.id
            elif isinstance(node.func, ast.Attribute):
                target = node.func.attr
            if target in helpers:
                return constant_return_value(helpers[target], values)
        return eval_pure_call(node, values)
    if isinstance(
        node,
        (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp),
    ):
        return eval_comprehension(node, values)
    if isinstance(node, ast.Attribute):
        if names_builtins_module(node.value, values):
            return BUILTIN_VALUES.get(node.attr, UNKNOWN)
        if node.attr.startswith("_"):
            return UNKNOWN
        receiver = eval_constant(node.value, values)
        if receiver is UNKNOWN or not isinstance(
            receiver,
            (
                str,
                bytes,
                int,
                float,
                bool,
                tuple,
                list,
                dict,
                frozenset,
                type,
            ),
        ):
            return UNKNOWN
        try:
            return getattr(receiver, node.attr)
        except Exception:
            return UNKNOWN
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


def constant_return_value(func, values):
    """The constant a same class helper hands back, or UNKNOWN.

    Every return of the helper must settle as a constant on
    the file reading, judged in the helper scope where its
    parameters stand unbound, so a helper that reads a
    parameter or a fixture hands back a value the call
    site cannot settle. A name the helper binds to a
    constant before returning it settles the same way, on
    the body assignment reading the mock walk already
    makes. The reading counts the returns the body
    writes, and a path that leaves the helper without a
    written return is not counted among them. The
    settled returns need not agree with each other, because
    an assertion over a call whose every outcome is a known
    constant still argues about constants alone. A helper
    with no return hands back None at run time, which
    settles as that constant.
    """
    returns = own_returns(func)
    if not returns:
        return None
    local = dict(values)
    for targets, value in _body_assignments(func):
        settled_value = eval_constant(value, local)
        for name in targets:
            if settled_value is UNKNOWN:
                local.pop(name, None)
            else:
                local[name] = settled_value
    settled = UNKNOWN
    for node in returns:
        value = eval_constant(node.value, local)
        if value is UNKNOWN:
            return UNKNOWN
        settled = value
    return settled


def is_constant_expression(node, values, helpers=None):
    """Whether the expression is built only from constants."""
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, ast.Name):
        return node.id in values or node.id in BUILTIN_NAMES
    if isinstance(node, ast.Call):
        if helpers:
            target = None
            if isinstance(node.func, ast.Name):
                target = node.func.id
            elif isinstance(node.func, ast.Attribute):
                target = node.func.attr
            if target in helpers:
                return constant_return_value(
                    helpers[target], values
                ) is not UNKNOWN
        if not all(
            is_constant_call_argument(arg, values)
            for arg in node.args
        ):
            return False
        if not all(
            is_constant_call_argument(keyword.value, values)
            for keyword in node.keywords
        ):
            return False
        func = node.func
        if isinstance(func, (ast.Name, ast.Attribute)):
            if resolve_pure_callable(func, values) is not None:
                return True
            if isinstance(func, ast.Attribute):
                return func.attr in PURE_METHOD_NAMES and (
                    is_constant_call_argument(func.value, values)
                )
            return False
        if isinstance(func, ast.Lambda):
            scope = lambda_scope(func, node, values)
            if scope is None:
                return False
            return is_constant_expression(func.body, scope)
        return False
    if isinstance(
        node,
        (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp),
    ):
        return is_constant_comprehension(node, values)
    if isinstance(node, ast.Attribute):
        if names_builtins_module(node.value, values):
            return node.attr in BUILTIN_NAMES
        return is_constant_expression(node.value, values)
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

    def __init__(self, global_values, return_names=(),
                 extra_mocks=(), aliases=()):
        self.global_values = global_values
        self.conditional_depth = 0
        self.mock_names = set()
        self.return_names = set(return_names)
        self.extra_mocks = set(extra_mocks)
        self.aliases = dict(aliases)

    def walk_conditional_block(self, stmts, values, result, swallowed):
        self.conditional_depth += 1
        try:
            return self.walk_block(stmts, values, result, swallowed)
        finally:
            self.conditional_depth -= 1

    def collect(self, func, seed=None, param_values=None,
                param_mocks=None, extra_mocks=None):
        # A fresh body starts outside every conditional branch
        # of the body that defined or called it, because its
        # own branches are the ones that judge its calls.
        outer_depth = self.conditional_depth
        self.conditional_depth = 0
        # The mock names of a body are its own static bindings,
        # the mock parameters a caller handed in, and the mock
        # names of an enclosing body a nested function closes
        # over, which still stand in the set at this point.
        outer_mocks = self.mock_names
        self.mock_names = (
            mock_names_in_body(func, self.return_names, self.aliases)
            | set(param_mocks or ())
            | set(outer_mocks)
            | set(self.extra_mocks)
            | set(extra_mocks or ())
        )
        try:
            return self.collect_body(func, seed, param_values)
        finally:
            self.conditional_depth = outer_depth
            self.mock_names = outer_mocks

    def collect_body(self, func, seed=None, param_values=None):
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
                (
                    "assert",
                    stmt,
                    None,
                    dict(values),
                    False,
                    swallowed,
                    self.conditional_depth > 0,
                    frozenset(self.mock_names),
                )
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
            body_always = self.walk_conditional_block(
                stmt.body, body_values, result, swallowed
            )
            else_values = dict(values)
            else_always = False
            if stmt.orelse:
                else_always = self.walk_conditional_block(
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
            if known is not UNKNOWN:
                self.walk_block(
                    stmt.body, body_values, result, swallowed
                )
            else:
                self.walk_conditional_block(
                    stmt.body, body_values, result, swallowed
                )
            self.merge_outcomes(values, [values, body_values])
            if stmt.orelse:
                else_values = dict(values)
                self.walk_conditional_block(
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
            self.walk_conditional_block(
                stmt.body, body_values, result, swallowed
            )
            self.merge_outcomes(values, [values, body_values])
            if stmt.orelse:
                else_values = dict(values)
                self.walk_conditional_block(
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
                self.walk_conditional_block(
                    handler.body, handler_values, result, swallowed
                )
                outcomes.append(handler_values)
            if stmt.orelse:
                else_values = dict(values)
                self.walk_conditional_block(
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
        if isinstance(stmt, ast.Import):
            for alias in stmt.names:
                if alias.name == "builtins":
                    values[alias.asname or "builtins"] = builtins
                else:
                    name = (alias.asname or alias.name).split(".")[0]
                    values.pop(name, None)
            return False
        if isinstance(stmt, ast.ImportFrom):
            for alias in stmt.names:
                bound = alias.asname or alias.name
                if (
                    stmt.level == 0
                    and stmt.module == "builtins"
                    and alias.name in BUILTIN_VALUES
                ):
                    values[bound] = BUILTIN_VALUES[alias.name]
                else:
                    values.pop(bound.split(".")[0], None)
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
                self.walk_conditional_block(
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

    def walk_conditional_expr(self, node, values, result, swallowed):
        self.conditional_depth += 1
        try:
            self.walk_expr(node, values, result, swallowed)
        finally:
            self.conditional_depth -= 1

    def walk_expr(self, node, values, result, swallowed):
        if isinstance(node, ast.BoolOp):
            self.walk_expr(node.values[0], values, result, swallowed)
            for value in node.values[1:]:
                self.walk_conditional_expr(
                    value, values, result, swallowed
                )
            return
        if isinstance(node, ast.IfExp):
            self.walk_expr(node.test, values, result, swallowed)
            known = (
                eval_constant(node.test, values)
                if is_constant_expression(node.test, values)
                else UNKNOWN
            )
            if known is not UNKNOWN:
                branch = node.body if known else node.orelse
                self.walk_expr(branch, values, result, swallowed)
                return
            self.walk_conditional_expr(
                node.body, values, result, swallowed
            )
            self.walk_conditional_expr(
                node.orelse, values, result, swallowed
            )
            return
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
                            self.conditional_depth > 0,
                            frozenset(self.mock_names),
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
            if isinstance(func, ast.Attribute) and (
                func.attr in MUTATING_METHOD_NAMES
            ):
                base = func.value
                while isinstance(
                    base, (ast.Attribute, ast.Subscript)
                ):
                    base = base.value
                if isinstance(base, ast.Name):
                    values.pop(base.id, None)
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


def assertion_record_is_real(record, helpers=None):
    (kind, node, name, values, in_context, swallowed, conditional,
     mock_names) = record
    if swallowed:
        return False
    if kind == "assert":
        test = node.test
        if mock_names and contains_mock_reference(
            test, mock_names
        ) and mock_only_expression(test, mock_names):
            return False
        if is_constant_expression(test, values, helpers):
            return False
        if self_comparison(test):
            return False
        if isinstance(test, ast.UnaryOp) and isinstance(
            test.op, ast.Not
        ):
            if is_constant_expression(test.operand, values, helpers):
                return False
            if self_comparison(test.operand):
                return False
        return True
    if name == "fail":
        return not conditional
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
        is_constant_expression(operand, values, helpers)
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
    if mock_names and any(
        contains_mock_reference(operand, mock_names)
        for operand in operands
    ) and all(
        mock_only_expression(operand, mock_names)
        for operand in operands
    ):
        return False
    return True


def scope_is_real(result, resolve_call, helpers=None):
    if any(
        assertion_record_is_real(record, helpers)
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
        elif isinstance(stmt, ast.Import):
            for alias in stmt.names:
                if alias.name == "builtins":
                    values[alias.asname or "builtins"] = builtins
                else:
                    name = (alias.asname or alias.name).split(".")[0]
                    values.pop(name, None)
        elif isinstance(stmt, ast.ImportFrom):
            for alias in stmt.names:
                bound = alias.asname or alias.name
                if (
                    stmt.level == 0
                    and stmt.module == "builtins"
                    and alias.name in BUILTIN_VALUES
                ):
                    values[bound] = BUILTIN_VALUES[alias.name]
                else:
                    values.pop(bound, None)
    return values


def vacuity_problems(root=None):
    """Problems with vacuous test methods under tests/."""
    root = ROOT if root is None else root
    tests_dir = root / "tests"
    problems = []
    paths = set()
    if not tests_dir.is_dir():
        problems.append(
            "the tests directory is missing, so the guard "
            "discovered no test methods to judge"
        )
        return problems
    paths.update(tests_dir.glob("test*.py"))
    paths.update(tests_dir.glob("*_test.py"))
    if not paths:
        problems.append(
            "the tests directory holds no test files, so the "
            "guard discovered no test methods to judge"
        )
        return problems
    method_count = [0]
    for path in sorted(paths):
        if not path.is_file():
            problems.append(
                "%s does not parse, it is not a regular file"
                % path.name
            )
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            problems.append(
                "%s cannot be read as UTF-8 text, %s"
                % (path.name, exc)
            )
            continue
        except OSError as exc:
            problems.append(
                "%s does not parse, %s" % (path.name, exc)
            )
            continue
        if not text.strip():
            problems.append(
                "%s stands empty, so it holds no test "
                "methods for the guard to judge" % path.name
            )
            continue
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError as exc:
            problems.append(
                "%s does not parse, %s" % (path.name, exc)
            )
            continue
        global_values = module_global_values(tree)
        aliases = file_patch_aliases(tree)
        module_mocks, return_names = file_mock_provenance(
            tree, aliases
        )
        collector = Collector(
            global_values,
            return_names=return_names,
            extra_mocks=module_mocks,
            aliases=aliases,
        )

        def no_resolve(name, node, snapshot):
            return (False, False)

        def check(where, result, resolve_call, helpers=None):
            if not scope_is_real(result, resolve_call, helpers):
                problems.append(
                    "%s carries no real assertion in a "
                    "shape this guard follows, so it cannot "
                    "fail for a real reason within this "
                    "guard's sight" % where
                )
            if not scope_fixture(result, resolve_call):
                problems.append(
                    "%s never touches a fixture in a "
                    "shape this guard follows, so it "
                    "argues about nothing within this "
                    "guard's sight" % where
                )

        for item in tree.body:
            if isinstance(
                item, (ast.FunctionDef, ast.AsyncFunctionDef)
            ) and item.name.startswith("test"):
                method_count[0] += 1
                result = collector.collect(item)
                check(
                    "%s %s" % (path.name, item.name),
                    result,
                    no_resolve,
                    {item.name: item},
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
                # A helper reached through an attribute call is
                # a method, and the call arguments carry no
                # receiver, so the first declared parameter is
                # the receiver and not a call argument. Binding
                # the first literal to the receiver left the
                # real first parameter unbound, which is the
                # shape the round 107 helper plant used.
                decorator_names = set()
                for decorator in func.decorator_list:
                    if isinstance(decorator, ast.Name):
                        decorator_names.add(decorator.id)
                    elif isinstance(decorator, ast.Attribute):
                        decorator_names.add(decorator.attr)
                if (
                    positional
                    and isinstance(node.func, ast.Attribute)
                    and "staticmethod" not in decorator_names
                ):
                    positional = positional[1:]
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

            caller_mocks = [set()]

            def param_mock_names(func, node):
                names = set()
                arguments = func.args
                positional = [
                    arg.arg
                    for arg in (
                        list(arguments.posonlyargs)
                        + list(arguments.args)
                    )
                ]
                decorator_names = set()
                for decorator in func.decorator_list:
                    if isinstance(decorator, ast.Name):
                        decorator_names.add(decorator.id)
                    elif isinstance(decorator, ast.Attribute):
                        decorator_names.add(decorator.attr)
                if (
                    positional
                    and isinstance(node.func, ast.Attribute)
                    and "staticmethod" not in decorator_names
                ):
                    positional = positional[1:]
                keywords = {
                    keyword.arg: keyword.value
                    for keyword in node.keywords
                    if keyword.arg is not None
                }
                exprs = {}
                for index, param in enumerate(positional):
                    if index < len(node.args):
                        exprs[param] = node.args[index]
                    elif param in keywords:
                        exprs[param] = keywords[param]
                for arg in arguments.kwonlyargs:
                    if arg.arg in keywords:
                        exprs[arg.arg] = keywords[arg.arg]
                for param, expr in exprs.items():
                    if is_mock_producing(
                        expr, caller_mocks[0], return_names
                    ) or contains_mock_reference(
                        expr, caller_mocks[0]
                    ):
                        names.add(param)
                return names

            def resolve_call(name, node, snapshot):
                if name not in helpers:
                    return (False, False)
                bindings = param_bindings(
                    helpers[name], node, snapshot
                )
                param_mocks = param_mock_names(helpers[name], node)
                key = (
                    name,
                    repr(
                        sorted(
                            (param, repr(value))
                            for param, value in bindings.items()
                        )
                    ),
                    repr(sorted(param_mocks)),
                )
                if key in resolved:
                    return resolved[key]
                if key in visiting:
                    return (False, False)
                visiting.add(key)
                sub = collector.collect(
                    helpers[name], param_values=bindings,
                    param_mocks=param_mocks,
                )
                value = (
                    scope_is_real(sub, resolve_call, helpers),
                    scope_fixture(sub, resolve_call),
                )
                visiting.discard(key)
                resolved[key] = value
                return value

            setup_mocks = class_setup_mock_names(
                cls, return_names, module_mocks, aliases
            )
            collector.extra_mocks = (
                set(module_mocks) | set(setup_mocks)
            )
            for item in methods:
                if item.name.startswith("test"):
                    method_count[0] += 1
                    caller_mocks[0] = (
                        mock_names_in_body(item, return_names, aliases)
                        | set(module_mocks)
                        | set(setup_mocks)
                    )
                    result = collector.collect(
                        item,
                        extra_mocks=(
                            set(module_mocks) | set(setup_mocks)
                        ),
                    )
                    check(
                        "%s %s" % (path.name, item.name),
                        result,
                        resolve_call,
                        helpers,
                    )
    if method_count[0] == 0:
        problems.append(
            "the discovered test files hold no test methods, "
            "so the guard judged an empty suite"
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
