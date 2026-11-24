#!/usr/bin/env python3
"""Run the gate steps and key every verdict to the tree it ran on.

The Makefile wiring runs the steps and stops at the first
failure, and that wiring stays the gate. What the wiring
never produced is an artefact. A step printed a success
sentence to a terminal and left nothing behind, so a green
earned on one tree could not be told from a green earned on
another, a suite that lost test files printed the same
success at a lower count, and a green earned on a working
state carrying uncommitted edits certified a tree that was
never pushed. This runner is the shipped answer to that
family. It runs the same steps the Makefile check target
names, in the same order, and for each step it writes the
captured output to a log file named for the step and a meta
record beside it carrying the git tree hash of the tree
under test, the head, the step name, its exit code and its
count line where the step prints one. A run record names
the steps completed, the failing step where one failed,
and the steps never reached, so a stopped run names its
own frontier instead of leaving a reader to reconstruct it.

The tree identity is read from git before any step runs.
A working state that differs from its head is refused
unless the caller names the local mode with the allow
dirty flag, and a root that is not a git checkout at a
commit is refused outright, because a verdict that cannot
name its tree certifies nothing. The discover step count
is held against the pinned floor below, so the suite can
lose a test file in silence no longer. The floor moves
only in the same change that moves the census it pins.

The count the floor arm reads is taken, not parsed,
and the runner takes it itself from the sources of
the tree it gates. Before the discover step runs,
the runner derives the suite the step names from the
step its own arguments and reads the sources the
derivation names, walking the start folder and the
package folders under it for the files the pattern
names and parsing each file its syntax tree. In
each module the reading takes the classes standing
at module level, and a class stands as a test class
where its bases resolve, through the names the
module itself binds, to the unittest test case
class or to a test class the reading resolves in
the same module or in a module of the same tree.
For each name standing in the module its namespace
that resolves to a test class, by definition, by
import, or by a plain assignment of one name to
another, the reading counts the test names standing
in that class and in every ancestor it resolves, a
name counted once for the class however many of its
ancestors define it. The census is the sum over the
modules. No suite module is imported and no suite
code executes in the taking, and no byte of the
count travels a channel the suite can write, so
nothing the suite prints, writes, or leaves behind
can stand in for the census or move it. A file that
does not parse states no classes to the reading and
counts nothing, and its step fails on its own exit
in the run the step makes.

The reading derives the identities of the
population beside its count. For each name it
counts, the reading names one identity in the form
the loader names a case, the module the class
stands defined in and the class name and the test
name, and it keeps the identity once for each
namespace occurrence that resolves to the class, so
the identities stand as a multiset whose size is
the census and whose members are the cases the
loader loads from the sources. The floor arm holds
the run against the population in that form, so a
run whose cases are not the cases of the sources
disagrees with the reading in identity even where
its count agrees with the census.

The identities the report carries are not strings
the run is trusted to spell. The shipped wrapper
holds every case of the suite it loaded against
the classes as they loaded from the sources in its
own process. The record the holding trusts takes
its names from the bindings the loading leaves
standing in the namespace of each module and in
the namespaces of the classes standing in it, each
class standing under the path of binding names
that reaches it, and never from a name a class
carries on itself, so a class nested inside
another stands in the record under its own nested
path or not at all, and no assignment to the
qualified name a class carries can move it into a
name the namespace does not give it. A case stands
stated only where the class it is a case of is the
very class object the loading produced under the
name the case carries, and where the method it
runs is the very function that class held for the
name as it loaded, and
where any case of the suite stands unstated the
wrapper writes no report at all and names the case
and its ground in the step its own output. A
population wearing the identities of the sources
on a class the sources do not state therefore
leaves the floor arm the report that never stood
rather than an agreement of strings to judge, and
the discover step of the gate is the wrapper
itself, so the holding stands exercised over the
shipped suite at every gate run.

The floor therefore certifies suites whose test
identities are statically enumerable from their
sources in the form the reading above states, and
whose cases stand stated under the holding above,
cross checked against the run the step made. A
population built by execution, by methods a class
body builds in a loop or by names assigned at run
time or by a load tests hook shaping the suite as
it loads, runs under identities its sources do not
state, and where its count stands apart from the
census the run refuses on the count, and where its
count equals the census the run refuses on the
identities, by name in either arm rather than
certifying a population nobody took from the tree.
A hook that returns the cases of the sources whole
shapes nothing, and its run stands or falls with
the population it returns. The agreement between
this reading and the loaded suite over the shipped
suite stands pinned by the runner its own tests,
the pinned floor equalling both counts and the
identities of the reading equalling the identities
of the loaded suite on this tree.

The floor certifies the population and the
provenance of its cases, and it prices no body a
stated name carries. What a module its own loading
leaves standing in a class is the statement of the
sources. The bodies a class body states are its
statement, and a name a module body rebinds as the
module loads stands rebound in the function as
loaded, so a rebinding written in the sources
stands inside the claim and a run over it passes
on the population the sources state, the honesty
of the body standing with the step its own exit
and with the vacuity guard elsewhere in the gate.
The same ground holds for the name of a class
itself. A class name standing in a module its
namespace that the module body rebinds as the
module loads stands recorded as the object the
loading leaves bound under it, so a rebinding of
a class name written in the sources stands inside
the claim on the same footing, and the population
a run executes under that name is the population
the sources state under it, read whole.
What any code puts into a class after its module
has loaded is not the function as loaded. A hook
that replaces a stated method on its class as it
shapes the suite leaves its cases carrying a
function the loading never produced, and those
cases stand unstated on their provenance, not on
any judgement of the body that replaced it.

The shipped discover wrapper writes the report of
the run it made to a count file the runner names in
the environment of the step, the count of the run
standing as the first line of the file and the
identities of the cases in the suite it executed
standing after it, one to a line in sorted order.
The wrapper writes the report only where every
case of the suite stood stated under the holding,
and a suite carrying an unstated case leaves the
file with no report in it, whatever its tests
earned, and that report stands as the cross check
alone. A
report that does not stand against the census in
count and in identity, or no report where the step
exited clean, refuses the run by name, and a step
that fails or is killed leaves no report in its
meta, the report being read only where the step
exited clean. The file reading accepts exactly the
whole form the wrapper writes, the count in its
plain spelling and after it as many identity lines
as the count states, each one a dotted name in the
form a case names itself and the lines standing in
sorted order, and a count standing alone in the
file for a count above zero is no report at all
under the reading, since the form of the report is
the count and the population together. A count
taken from the step its output text would be a
count the suite under test could have printed
whole, summary block and all, in the words of its
own shutdown writers, and such a count certifies
nothing, so no arm of this runner reads one. The
count lines the metas of the other steps carry
stand as artefact notes that no arm judges.

One residue of the cross check stands named here
rather than closed. Module level code of the suite
executes inside the step, in the wrapper its own
process, and a suite whose module level code
subverts the wrapper it runs inside, or patches the
test runner in that shared process, can falsify the
holding and the report the cross check reads, and
a writer the suite leaves behind on the file can
write the report itself in the census its own
terms, the count and the identities of the sources
stated whole over a run that executed another
population, and such a suite stands outside the
claim of the floor, in the family the shipped gates
name for their in process machinery. The holding
speaks for the suite the wrapper loaded in its own
process and for no byte of the file, so the writer
on the file stands exactly where it stood before
the holding was built. What the forgery cannot
move is the census, which is taken from the sources
of the keyed tree in the runner its own process, so
a forged report must still state the population of
the sources whole and agree with a census the suite
cannot move without moving the tree the run keys
on, and a movement of the tree is the refusal this
runner prices at every step boundary. A discover
step whose arguments stand in neither spelling the
derivation reads gives the runner no suite it can
name and so no census it can take, and such a run
refuses by name where its step passes, since a
census nobody took cannot be certified from a
report alone.

The identity is read again after every step, and again
after the final step, and a run whose tree or dirty state
moved while its steps ran ends there in a refusal naming
the movement and the step it followed rather than in the
verdict its steps earned, because a verdict keyed to the
opening tree over bytes that tree never held is the
failure this runner exists to prevent. A writer that
returns the tree to its opening bytes inside the span of
one step own execution remains invisible to the reading,
and that residue stands named here rather than closed,
since no reading taken between steps can see a state
that never stood at a step boundary. A discover step
that reports no measured count fails the floor arm by
name, since a census that was never taken cannot be
held at or above the floor. Each step meta record carries the dirty state
and the allow dirty flag of its run beside the tree and
the head, so a step artefact quoted on its own shows the
terms it ran under.

One remainder stands named here rather than closed. The
submissions gate still measures its tree figures by
walking the working filesystem when it is run on its own,
outside this runner, so a standalone submissions verdict
is a working state verdict. Inside this runner the walk
runs on the state this runner just keyed, and the figures
the pack states are re-derived from the shipped tree by
the suite census beside it. The gate tests also still
assert most gate outcomes from in process summaries
rather than from artefacts like the ones this runner
writes, and that family stands as a named gap for a later
round to close with a subprocess smoke per gate script.

A second remainder stood named beside it in earlier
rounds, that the vacuity guard mirror of the discover set
reads the top level of the tests folder alone. Round 24
priced that sentence by execution and it does not hold.
The guard walks the tests folder recursively under both
file patterns the loader uses, a vacuous test file
standing in a subdirectory draws the guard refusals by
name, and the discover count sees the folder where the
loader sees it, so the blind spot the sentence named
stands closed in the shipped guard and the sentence
stands struck rather than carried. The runner own log
folder stands outside the dirtiness it judges, because a
runner that counted its own output as dirt could never
key a clean tree in its default shape, and the run
record names how many standing entries that exclusion
covered.

Exits zero only when every step ran and passed on the
keyed tree at or above the pinned floor.
"""

import argparse
import ast
import fnmatch
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PINNED_TEST_FLOOR = 3335

RAN_RE = re.compile(r"^Ran (\d+) tests", re.M)

# The tail that closes the test runner its own summary
# block. The count line carries its span, and the verdict
# word the runner prints stands under it with at most one
# blank line between. A count line standing without this
# tail is a line some other writer printed in the count
# form, before the block or after it, and no part of the
# verdict the step earned.
SUMMARY_TAIL_RE = re.compile(
    r" in [0-9]+(?:\.[0-9]+)?s[ \t]*\n(?:[ \t]*\n)?(?:OK|FAILED)\b"
)

OWN_OUTPUT_ROOT = ".gate-logs"

# The environment name under which the runner names the
# count file for the discover step. The shipped discover
# wrapper reads the name and writes the report of its
# run, its count and the identities of its cases, to the
# file it names, and that report stands as the cross
# check the floor arm holds against the census the
# runner takes from the sources, never as the count the
# floor reads itself.
COUNT_FILE_ENV = "RECOGNITIO_COUNT_FILE"


def parse_makefile_steps(text):
    """The check target recipe as a list of command lists.

    The recipe lines under the check target are the wiring,
    so the runner reads its step list from the Makefile
    itself and the two can never drift apart. The Python
    variable the Makefile spells stands for the interpreter
    running this script.
    """
    steps = []
    in_check = False
    for line in text.splitlines():
        if line.startswith("check:"):
            in_check = True
            continue
        if in_check:
            if line.startswith("\t"):
                recipe = line.strip()
                recipe = recipe.replace(
                    "$(PYTHON)", sys.executable
                )
                steps.append(recipe.split())
            elif line.strip():
                break
    return steps


def step_name(argv):
    """A short stable name for one step command."""
    if "unittest" in argv:
        return "discover"
    for part in argv:
        if part.endswith(".py"):
            return Path(part).stem
    return "-".join(argv[1:]) or argv[0]


# One empty grafts file stands created on first use and held
# for the life of the process, so the graft pin in the runner
# identity reads always names a file that stands in place. The
# empty file grafts nothing. A failure to create it leaves the
# pin unset, in which shape the runner refuses any root that is
# not a clean checkout anyway.
_GRAFT_PIN_PATH = None


def _graft_pin_path():
    """Create the runner's empty grafts file once and return it."""
    global _GRAFT_PIN_PATH
    if _GRAFT_PIN_PATH is None:
        try:
            import tempfile
            handle, path = tempfile.mkstemp(
                prefix="recognitio-grafts-"
            )
            os.close(handle)
            _GRAFT_PIN_PATH = path
        except OSError:
            return None
    return _GRAFT_PIN_PATH


def _git(root, *args):
    # Timeout basis. The runner asks git only for local
    # reads over one tree, in rev-parse and status and
    # diff shapes, and those reads measured in single
    # digit milliseconds on this tree in the Round 20 fix
    # pass. The 120 second bound is a stall guard in the
    # same figure the extractor carries for its children,
    # whose comment names the slowest legitimate command
    # at about 11 seconds under load, so a read still
    # working at this limit is read as stalled rather
    # than slow.
    env = dict(os.environ)
    graft_pin = _graft_pin_path()
    if graft_pin is not None:
        env["GIT_GRAFT_FILE"] = graft_pin
    try:
        out = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True, text=True, timeout=120, env=env,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout


def _porcelain_paths(line):
    """The paths a porcelain status line names.

    The line carries a two letter state and a space before
    the path, and a rename or a copy spells its pair with an
    arrow between the old name and the new one, so the
    reading returns both names of the pair where an arrow
    stands and the one name otherwise.
    """
    text = line[3:] if len(line) > 3 else ""
    if " -> " in text:
        old, new = text.split(" -> ", 1)
        return [
            old.strip().strip('"'),
            new.strip().strip('"'),
        ]
    return [text.strip().strip('"')]


def _is_own_output(line):
    """Whether a status line names only the runner output.

    The runner output stands apart only while it is
    untracked, because an untracked entry under the log
    folder can only be the runner own writing. A tracked
    entry under that folder, and any rename or copy whose
    either name stands outside it, is a change to the tree
    under test and never the runner output.
    """
    if line[:2] != "??":
        return False
    paths = _porcelain_paths(line)
    return bool(paths) and all(
        path == OWN_OUTPUT_ROOT
        or path.startswith(OWN_OUTPUT_ROOT + "/")
        for path in paths
    )


def tree_identity(root):
    """The head, the tree hash and the dirty state of a root.

    Returns None when the root is not a git checkout at a
    commit, because no verdict can be keyed to such a root.
    Standing entries under the runner own log folder are
    counted apart, because that folder is the runner output
    and never part of the tree under test.
    """
    head = _git(root, "rev-parse", "HEAD")
    tree = _git(root, "rev-parse", "HEAD^{tree}")
    if head is None or tree is None:
        return None
    status = _git(root, "status", "--porcelain")
    if status is None:
        return None
    entries = [
        line for line in status.splitlines() if line.strip()
    ]
    own = [line for line in entries if _is_own_output(line)]
    foreign = [line for line in entries if line not in own]
    return {
        "head": head.strip(),
        "tree": tree.strip(),
        "dirty": bool(foreign),
        "dirty_entries": foreign,
        "own_output_entries": len(own),
    }


def count_line(output):
    """The count a step printed, and the line that carried it.

    Only the discover step prints a count in a stable form,
    so the reading names that form and returns no count
    anywhere else rather than inventing one. The reading
    serves the steps whose counts no arm judges, whose
    printed lines stand in their metas as artefact notes.
    The discover step its count is never read here at all.
    It is taken by the runner itself, from a static
    reading of the sources of the suite the step names,
    and it stands in the discover meta with no line
    beside it, because no line carried it. The count is
    the one the test runner prints as its own verdict, so
    a count line carries the count only where it stands in
    the summary block the runner closes with its verdict
    word, the count line carrying its span and the verdict
    word standing under it with at most one blank line
    between. The last line standing in that form is the
    count. A bare count line standing before the block is
    a stray the step never printed as its verdict, the
    shape the first match reading once let overstate the
    count, and a bare count line standing after the block,
    in the words of a shutdown handler or any other late
    writer, is no part of the verdict either, the shape
    the last match reading let claim the census in its
    turn. A step whose output holds no summary block holds
    no count this reading will name.
    """
    chosen = None
    for match in RAN_RE.finditer(output):
        if SUMMARY_TAIL_RE.match(output, match.end()):
            chosen = match
    if chosen is not None:
        return int(chosen.group(1)), chosen.group(0)
    return None, None


# The count line of the report, the digits in their
# plain spelling. The class names the ASCII digits
# themselves, since the decimal class of a text
# pattern takes the digits of other scripts as well
# and the integer reading would follow it there.
_COUNT_LINE_RE = re.compile(r"(0|[1-9][0-9]*)")


def _identity_line(line):
    """Whether a line stands in the form a case names itself.

    A case names itself by dotted segments, the module
    and the class path and the method, and every
    segment of that naming is an identifier of the
    language the loader its own names are written in,
    the letters and marks an identifier takes, with
    the locals segment standing where a class built
    inside a function names its local standing, so
    the reading takes the segment family the loader
    its own names take and no other.
    """
    segments = line.split(".")
    if len(segments) < 2:
        return False
    for segment in segments:
        if segment == "<locals>":
            continue
        if not segment.isidentifier():
            return False
    return True


def reported_report(path):
    """The report the discover step made, or no report.

    The wrapper writes the report of its run as the
    whole content of the file the runner named for it,
    the count of the run standing as the first line in
    the form its write appends, the digits of the count
    in their plain spelling, and after it the identities
    of the cases in the suite it executed, one identity
    to a line in sorted order, each line closing with
    its newline and the file ending at the newline of
    its last line. The reading decodes the bytes of the
    file as the UTF-8 the wrapper writes them in and
    accepts exactly that whole form and nothing else,
    no padding around the digits, no leading zero on a
    count above zero, no carriage return standing with
    a newline, no identity standing out of its sorted
    place, and no count standing alone for a count
    above zero, because a reading that accepts a family
    of forms accepts spellings no report ever wrote and
    leaves its acceptance set to be argued shape by
    shape. A file that stands missing or unreadable, or
    bytes that do not decode, or a content standing in
    any other shape, reads as no report, and the floor
    arm refuses on that shape by name rather than
    falling back to the printed text. The reading
    returns the count and the identities together, the
    identities standing as the multiset the report
    states in the order it states them.
    """
    if path is None:
        return None
    try:
        data = path.read_bytes()
    except OSError:
        return None
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if not text.endswith("\n"):
        return None
    lines = text[:-1].split("\n")
    match = _COUNT_LINE_RE.fullmatch(lines[0])
    if match is None:
        return None
    count = int(match.group(1))
    identity_lines = lines[1:]
    if len(identity_lines) != count:
        return None
    identities = []
    for line in identity_lines:
        if not _identity_line(line):
            return None
        identities.append(line)
    if identities != sorted(identities):
        return None
    return count, identities


def discover_arguments(argv):
    """The suite a discover step names, in its own spellings.

    Returns the start folder, the pattern and the top
    level folder the step names, or no suite where the
    step stands in neither spelling the gate ships. The
    wrapper path form names the wrapper file among the
    arguments and its flags after it, and the unittest
    form names the discover word after the module words.
    The defaults are the wrapper its own, the start
    folder standing as the working folder, the pattern
    naming the test files, and the top level folder
    standing as the start folder where the step names
    none. Flags the wrapper takes without a value carry
    no part of the suite and are passed over.
    """
    rest = None
    if "-m" in argv and "unittest" in argv:
        try:
            rest = argv[argv.index("discover") + 1:]
        except ValueError:
            return None
    else:
        for index, part in enumerate(argv):
            if Path(part).name == "discover.py":
                rest = argv[index + 1:]
                break
    if rest is None:
        return None
    start = "."
    pattern = "test*.py"
    top = None
    index = 0
    while index < len(rest):
        part = rest[index]
        if part in ("-s", "--start-dir") and index + 1 < len(rest):
            start = rest[index + 1]
            index += 2
        elif part in ("-p", "--pattern") and index + 1 < len(rest):
            pattern = rest[index + 1]
            index += 2
        elif (
            part in ("-t", "--top-level-dir")
            and index + 1 < len(rest)
        ):
            top = rest[index + 1]
            index += 2
        else:
            index += 1
    return start, pattern, top


def _dotted_name(expr):
    """The dotted name an expression spells, or no name.

    An attribute chain standing on a plain name spells
    the name and its attributes in order. Any other
    shape, a call or a subscript standing at the foot
    of the chain among them, spells no name the reading
    can resolve.
    """
    parts = []
    while isinstance(expr, ast.Attribute):
        parts.append(expr.attr)
        expr = expr.value
    if isinstance(expr, ast.Name):
        parts.append(expr.id)
        parts.reverse()
        return tuple(parts)
    return None


_CONDITIONAL_BLOCKS = (ast.If, ast.Try) + (
    (ast.TryStar,) if hasattr(ast, "TryStar") else ()
)


def _block_statements(body):
    """The statements of a block and of its conditional arms.

    A statement standing inside a conditional arm at the
    same level takes its place in the namespace when its
    arm executes, so the reading walks the arms of the
    conditional and the guarded block beside the plain
    statements, in the order the source states them.
    """
    for node in body:
        yield node
        if isinstance(node, _CONDITIONAL_BLOCKS):
            for attr in ("body", "orelse", "finalbody"):
                inner = getattr(node, attr, None)
                if isinstance(inner, list):
                    yield from _block_statements(inner)
            if isinstance(node, (ast.Try,) + (
                (ast.TryStar,) if hasattr(ast, "TryStar") else ()
            )):
                for handler in node.handlers:
                    yield from _block_statements(handler.body)


class _ModuleReading:
    """One module of a suite, read from its sources alone.

    The reading holds the classes standing at module
    level, the names the module binds by its imports,
    the names standing in its namespace with the class
    or the dotted target each one resolves to, and the
    functions standing at module level. Nothing in the
    module has been imported or executed.
    """

    def __init__(self, name):
        self.name = name
        self.classes = {}
        self.bindings = {}
        self.namespace = {}
        self.functions = set()


def _read_module(name, data):
    """Read one module its syntax tree into a module reading.

    Bytes that do not parse state no classes to the
    reading, so a module the step cannot import either
    contributes nothing to the census, and its step
    fails on its own exit in the run the step makes.
    """
    reading = _ModuleReading(name)
    if data is None:
        return reading
    try:
        tree = ast.parse(data)
    except (SyntaxError, ValueError):
        return reading
    for node in _block_statements(tree.body):
        if isinstance(node, ast.ClassDef):
            reading.classes[node.name] = node
            reading.namespace[node.name] = ("class", name, node.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    reading.bindings[alias.asname] = tuple(
                        alias.name.split("."))
                    reading.namespace[alias.asname] = None
                else:
                    head = alias.name.split(".")[0]
                    reading.bindings[head] = (head,)
                    reading.namespace[head] = None
        elif isinstance(node, ast.ImportFrom):
            module = (
                tuple((node.module or "").split("."))
                if node.module else ()
            )
            if node.level:
                package = (
                    tuple(name.split(".")[:-node.level])
                    if name else ()
                )
                module = package + module
            for alias in node.names:
                local = alias.asname or alias.name
                target = module + (alias.name,)
                reading.bindings[local] = target
                reading.namespace[local] = ("dotted", target)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            reading.functions.add(node.name)
            reading.namespace[node.name] = None
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if isinstance(node.value, ast.Name):
                        reading.namespace[target.id] = (
                            reading.namespace.get(node.value.id))
                    else:
                        reading.namespace[target.id] = None
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                if isinstance(node.value, ast.Name):
                    reading.namespace[node.target.id] = (
                        reading.namespace.get(node.value.id))
                else:
                    reading.namespace[node.target.id] = None
    return reading


_TEST_CASE_DOTTED = ("unittest", "TestCase")
_TEST_CASE_DOTTED_LONG = ("unittest", "case", "TestCase")


class _SourceCensus:
    """The census of a suite, counted from the module readings.

    A class stands as a test class where its bases
    resolve, through the names its module binds, to the
    unittest test case class or to a test class the
    reading resolves in the same tree. For each name
    standing in a module its namespace that resolves to
    a test class, the census counts the test names of
    that class, the names standing in the class and in
    every ancestor the reading resolves, a name counted
    once for the class however many of its ancestors
    define it.
    """

    def __init__(self, modules):
        self.modules = modules
        self._is_test = {}
        self._methods = {}

    def _resolve_dotted(self, dotted):
        if dotted in (_TEST_CASE_DOTTED, _TEST_CASE_DOTTED_LONG):
            return "testcase"
        if len(dotted) >= 2:
            module = ".".join(dotted[:-1])
            cls = dotted[-1]
            reading = self.modules.get(module)
            if reading is not None and cls in reading.classes:
                return (module, cls)
        return None

    def _resolve_base(self, reading, expr):
        if isinstance(expr, ast.Subscript):
            return self._resolve_base(reading, expr.value)
        dotted = _dotted_name(expr)
        if dotted is None:
            return None
        head = dotted[0]
        if head in reading.bindings:
            return self._resolve_dotted(
                reading.bindings[head] + dotted[1:])
        if len(dotted) == 1 and head in reading.classes:
            return (reading.name, head)
        return self._resolve_dotted(dotted)

    def _resolve_namespace(self, entry):
        if entry is None:
            return None
        if entry[0] == "class":
            return (entry[1], entry[2])
        if entry[0] == "dotted":
            return self._resolve_dotted(entry[1])
        return None

    def _is_test_class(self, key, seen=None):
        if key in self._is_test:
            return self._is_test[key]
        if seen is None:
            seen = set()
        if key in seen:
            return False
        seen = seen | {key}
        module, cls = key
        reading = self.modules[module]
        node = reading.classes[cls]
        result = False
        for base in node.bases:
            resolved = self._resolve_base(reading, base)
            if resolved == "testcase":
                result = True
                break
            if resolved is not None and self._is_test_class(
                resolved, seen
            ):
                result = True
                break
        self._is_test[key] = result
        return result

    def _direct_names(self, reading, node):
        names = set()
        for stmt in _block_statements(node.body):
            if isinstance(
                stmt, (ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                if stmt.name.startswith("test"):
                    names.add(stmt.name)
            elif isinstance(stmt, ast.Assign):
                if isinstance(stmt.value, ast.Lambda) or (
                    isinstance(stmt.value, ast.Name)
                    and stmt.value.id in reading.functions
                ):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name) and (
                            target.id.startswith("test")
                        ):
                            names.add(target.id)
            elif isinstance(stmt, ast.AnnAssign):
                if isinstance(stmt.target, ast.Name) and (
                    stmt.target.id.startswith("test")
                ) and (
                    isinstance(stmt.value, ast.Lambda)
                    or (
                        isinstance(stmt.value, ast.Name)
                        and stmt.value.id in reading.functions
                    )
                ):
                    names.add(stmt.target.id)
        return names

    def _method_names(self, key, seen=None):
        if key in self._methods:
            return self._methods[key]
        if seen is None:
            seen = set()
        if key in seen:
            return set()
        seen = seen | {key}
        module, cls = key
        reading = self.modules[module]
        node = reading.classes[cls]
        names = self._direct_names(reading, node)
        for base in node.bases:
            resolved = self._resolve_base(reading, base)
            if resolved is not None and resolved != "testcase":
                names |= self._method_names(resolved, seen)
        self._methods[key] = names
        return names

    def total(self):
        total = 0
        for reading in self.modules.values():
            for entry in reading.namespace.values():
                resolved = self._resolve_namespace(entry)
                if resolved is None or resolved == "testcase":
                    continue
                if self._is_test_class(resolved):
                    total += len(self._method_names(resolved))
        return total

    def identities(self):
        """The identity multiset of the census, in sorted order.

        One identity stands for each test name of each
        class the census counts, keyed on the class the
        namespace name resolves to in the form the loader
        names a case, the defining module and the class
        name and the test name, and kept once for each
        namespace occurrence that resolves to the class,
        so the multiset holds the population the loader
        loads from the sources and its size is the total
        the census counts.
        """
        found = []
        for reading in self.modules.values():
            for entry in reading.namespace.values():
                resolved = self._resolve_namespace(entry)
                if resolved is None or resolved == "testcase":
                    continue
                if self._is_test_class(resolved):
                    for name in self._method_names(resolved):
                        found.append(
                            "%s.%s.%s"
                            % (resolved[0], resolved[1], name)
                        )
        return sorted(found)


def _source_census(root, argv):
    """The source census of the discover suite, or no census.

    The runner derives the suite the step names from the
    step its own arguments and reads the sources of that
    suite in its own process, walking the start folder
    and the package folders under it for the files the
    pattern names and parsing each file its syntax tree.
    No suite module is imported and no suite code
    executes in the taking, and no byte of the reading
    travels a channel the suite can write. A step whose
    arguments stand in neither shipped spelling names
    no suite and so no census, and a start folder that
    does not stand names none either, and the floor arm
    refuses on that shape by name.
    """
    named = discover_arguments(argv)
    if named is None:
        return None
    start, pattern, top = named
    start_dir = root / start
    top_dir = root / top if top is not None else start_dir
    if not start_dir.is_dir():
        return None
    modules = {}

    def module_name(path):
        rel = path.relative_to(top_dir)
        parts = list(rel.parts)
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        else:
            parts[-1] = parts[-1][:-3]
        return ".".join(parts)

    def visit(directory):
        try:
            entries = sorted(directory.iterdir())
        except OSError:
            return
        for entry in entries:
            if entry.is_dir():
                if entry.name == "__pycache__":
                    continue
                if (entry / "__init__.py").is_file():
                    visit(entry)
            elif entry.is_file() and fnmatch.fnmatch(
                entry.name, pattern
            ):
                try:
                    data = entry.read_bytes()
                except OSError:
                    data = None
                modules[module_name(entry)] = _read_module(
                    module_name(entry), data)

    try:
        visit(start_dir)
    except ValueError:
        return None
    return _SourceCensus(modules)


def static_discover_census(root, argv):
    """The census of the discover suite, taken from its sources."""
    census = _source_census(root, argv)
    if census is None:
        return None
    return census.total()


def static_discover_reading(root, argv):
    """The census and the identities of the discover suite.

    The reading the floor arm holds the run against, the
    count of the suite and the identity multiset of its
    population standing together, both taken from the
    sources by the one reading, or no reading where the
    step names no suite the reading can take.
    """
    census = _source_census(root, argv)
    if census is None:
        return None
    return census.total(), census.identities()


def run_gates(root, log_dir=None, allow_dirty=False, steps=None,
              floor=None):
    """Run the gate steps on one root and write their records.

    Returns the exit code and the run record. The record is
    also written to the log directory as it grows, so a run
    that stops early still leaves its frontier on disk.
    """
    root = Path(root)
    floor = PINNED_TEST_FLOOR if floor is None else floor
    if steps is None:
        makefile = root / "Makefile"
        steps = parse_makefile_steps(
            makefile.read_text(encoding="utf-8")
        )
    identity = tree_identity(root)
    if identity is None:
        record = {
            "verdict": "refused, the root is not a git checkout "
                       "at a commit, so no tree can be keyed",
            "tree": None,
            "head": None,
            "steps_completed": [],
            "failing_step": None,
            "steps_not_run": [step_name(s) for s in steps],
        }
        return 1, record
    if log_dir is None:
        log_dir = root / ".gate-logs"
    run_dir = Path(log_dir) / identity["tree"]
    run_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "verdict": "running",
        "tree": identity["tree"],
        "head": identity["head"],
        "dirty": identity["dirty"],
        "allow_dirty": bool(allow_dirty),
        "own_output_entries": identity["own_output_entries"],
        "pinned_test_floor": floor,
        "steps_completed": [],
        "failing_step": None,
        "steps_not_run": [step_name(s) for s in steps],
    }

    def write_record():
        (run_dir / "run.json").write_text(
            json.dumps(record, indent=1) + "\n", encoding="utf-8"
        )

    def closing_movement():
        """The fresh identity when the tree no longer stands as opened.

        The opening identity keys every artefact of the run,
        so the steps must have judged the state that identity
        names. A fresh tree or head that differs, or a dirty
        state or dirty entry set that differs, means some
        step judged bytes the opening tree never held, and
        no verdict the steps earned can stand keyed to that
        tree. A fresh identity that cannot be read at all
        counts as movement, because a verdict cannot stand
        when the standing state is unknown. Returns the
        fresh identity on movement and None otherwise.
        """
        closing = tree_identity(root)
        if closing is None:
            return {"unreadable": True}
        if (
            closing["tree"] != identity["tree"]
            or closing["head"] != identity["head"]
            or closing["dirty"] != identity["dirty"]
            or closing["dirty_entries"] != identity["dirty_entries"]
        ):
            return closing
        return None

    def refuse_for_movement(closing, after_step=None):
        record["verdict"] = (
            "refused, the tree moved during the run, so no "
            "verdict stands keyed to the tree the run opened on"
        )
        if after_step is not None:
            record["movement_after_step"] = after_step
        if closing.get("unreadable"):
            record["closing_tree"] = None
            record["closing_head"] = None
            record["closing_dirty"] = None
        else:
            record["closing_tree"] = closing["tree"]
            record["closing_head"] = closing["head"]
            record["closing_dirty"] = closing["dirty"]
            record["closing_dirty_entries"] = (
                closing["dirty_entries"]
            )
        write_record()
        return 1, record

    write_record()
    if identity["dirty"] and not allow_dirty:
        record["verdict"] = (
            "refused, the working state differs from its head "
            "and the allow dirty local mode was not named"
        )
        record["dirty_entries"] = identity["dirty_entries"]
        write_record()
        return 1, record
    names = [step_name(s) for s in steps]
    for index, argv in enumerate(steps):
        name = names[index]
        started = time.time()
        # The discover step its count is taken by the
        # runner from the sources of the suite the step
        # names, never read from its output and never
        # taken from the channel file. The runner takes
        # the census before the step runs, on the tree
        # the run keyed, and names a fresh count file in
        # the step environment for the wrapper its run
        # report, clearing any file standing there from
        # an earlier run. The report stands as a cross
        # check on the census alone, so bytes the suite
        # writes into the file can refuse the run and
        # can never carry it.
        count_path = None
        step_env = None
        census = None
        census_identities = None
        if name == "discover":
            reading = static_discover_reading(root, argv)
            if reading is not None:
                census, census_identities = reading
            count_path = run_dir / (
                "%02d-discover.count" % (index + 1)
            )
            try:
                count_path.unlink()
            except OSError:
                pass
            step_env = dict(os.environ)
            step_env[COUNT_FILE_ENV] = str(count_path)
        try:
            # Timeout basis. One step is one Makefile check
            # step, and the heaviest step is the test
            # discover. Its recorded spans stand at 380
            # seconds at 2,344 tests in run 302 and at
            # about 1,058 seconds for the full suite on the
            # slower check job of the Round 19 landing,
            # with the whole gate step at about 1,014
            # seconds on hosted run 42636057863. The 3,600
            # second bound stands above every recorded step
            # span as a stall ceiling for local runs on a
            # slow or loaded machine. It stands above the
            # 30 minute hosted job bound of 1,800 seconds,
            # so inside the hosted job the job bound fires
            # first and this bound binds only local runs.
            proc = subprocess.run(
                argv, cwd=str(root), capture_output=True,
                text=True, timeout=3600, env=step_env,
            )
            output = (proc.stdout or "") + (proc.stderr or "")
            code = proc.returncode
        except (OSError, subprocess.SubprocessError) as exc:
            output = "the step could not be run, %s" % exc
            code = 1
        # The identity stands read again before the step own
        # artefacts are written, so a state the step left
        # standing is read as it stood when the step ended,
        # and nothing the runner itself writes can stand
        # between the step and the reading.
        movement = closing_movement()
        (run_dir / ("%02d-%s.log" % (index + 1, name))).write_text(
            output, encoding="utf-8"
        )
        reported = None
        reported_identities = None
        if name == "discover":
            count, line = census, None
            # The report of a step that failed or was
            # killed is never read, so a count planted by
            # a dying suite stands nowhere in the meta of
            # a step that did not complete. The count the
            # meta carries for the discover step is the
            # runner its census taken from the sources,
            # and the report stands beside it as the
            # cross check, its count and the identities
            # of the cases it ran standing together.
            if code == 0:
                report = reported_report(count_path)
                if report is not None:
                    reported, reported_identities = report
        else:
            count, line = count_line(output)
        meta = {
            "step": name,
            "index": index + 1,
            "command": argv,
            "tree": identity["tree"],
            "head": identity["head"],
            "dirty": identity["dirty"],
            "allow_dirty": bool(allow_dirty),
            "exit_code": code,
            "count": count,
            "count_line": line,
            "seconds": round(time.time() - started, 3),
            "log": "%02d-%s.log" % (index + 1, name),
        }
        if name == "discover":
            meta["reported_count"] = reported
            meta["reported_identities"] = reported_identities
        (run_dir / ("%02d-%s.json" % (index + 1, name))).write_text(
            json.dumps(meta, indent=1) + "\n", encoding="utf-8"
        )
        failed = code != 0
        reason = None
        if name == "discover" and not failed:
            if census is None:
                failed = True
                reason = (
                    "the runner could not take the census "
                    "of the discover step from the sources "
                    "of the suite it names, so the run "
                    "cannot be held at or above the pinned "
                    "floor of %d" % floor
                )
            elif reported is None:
                failed = True
                reason = (
                    "the discover step reported no measured "
                    "count, so the run cannot be held at or "
                    "above the pinned floor of %d" % floor
                )
            elif reported != census:
                failed = True
                reason = (
                    "the discover step reported %d tests "
                    "against the runner its census of %d "
                    "taken from the sources of the suite, "
                    "so the run cannot be held at or above "
                    "the pinned floor of %d"
                    % (reported, census, floor)
                )
            elif reported_identities != census_identities:
                failed = True
                reason = (
                    "the discover step reported %d tests "
                    "under identities that disagree with "
                    "the identities of the runner its "
                    "census of %d taken from the sources "
                    "of the suite, so the run cannot be "
                    "held at or above the pinned floor "
                    "of %d"
                    % (reported, census, floor)
                )
            elif census < floor:
                failed = True
                reason = (
                    "the discover step counted %d tests, "
                    "under the pinned floor of %d"
                    % (census, floor)
                )
        if failed:
            record["failing_step"] = name
            if reason:
                record["failure_reason"] = reason
            record["steps_not_run"] = names[index + 1:]
            record["verdict"] = "failed at step %s" % name
            if movement is not None:
                return refuse_for_movement(
                    movement, after_step=name)
            write_record()
            return 1, record
        record["steps_completed"].append(name)
        record["steps_not_run"] = names[index + 1:]
        write_record()
        if movement is not None:
            return refuse_for_movement(movement, after_step=name)
    closing = closing_movement()
    if closing is not None:
        return refuse_for_movement(
            closing, after_step=names[-1] if names else None)
    missing = [
        name for index, name in enumerate(names)
        if not (run_dir / ("%02d-%s.json" % (index + 1, name))).is_file()
    ]
    if missing:
        record["verdict"] = (
            "failed, step meta records stand missing for %s"
            % ", ".join(missing)
        )
        write_record()
        return 1, record
    record["verdict"] = "pass"
    record["steps_not_run"] = []
    write_record()
    return 0, record


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run the gate steps with tree keyed records."
    )
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--log-dir", default=None)
    parser.add_argument("--allow-dirty", action="store_true")
    args = parser.parse_args(argv)
    code, record = run_gates(
        Path(args.root),
        log_dir=Path(args.log_dir) if args.log_dir else None,
        allow_dirty=args.allow_dirty,
    )
    print("run_gates: %s" % record["verdict"])
    if record.get("tree"):
        print(
            "run_gates: tree %s at head %s, %d steps completed"
            % (
                record["tree"], record["head"],
                len(record["steps_completed"]),
            )
        )
    return code


if __name__ == "__main__":
    sys.exit(main())
