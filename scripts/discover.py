#!/usr/bin/env python3
"""Run the test discover step compiling every module from source.

The discover step opens the gate, and the suite it runs is
the census the rest of the gate stands on. Through the
ordinary import system the step honours a compiled cache
standing beside a source file, and an unchecked hash based
cache is honoured without reading the source at all, so a
shadow compiled from a passing variant of a test module
executes in place of the source the tree carries while the
source on disk still holds the failing test, and nothing
in the run names the substitution. The gate loaders met
the same shape in Round 25 and answered it by compiling
the source bytes themselves. This wrapper is the discover
step its equivalent. A finder stands at the head of the
import search and answers only for a module whose source
stands under the discover its top level folder, and the
loader it returns compiles the source bytes it reads and
never consults a compiled cache, so the module that runs
is the module whose source stands in the tree. Every other
import in the run, the standard library and the modules
the tests load by path among them, goes through the
ordinary search untouched.

The wrapper takes the discover arguments the wiring names,
the start folder and the pattern and the top level folder
in the spellings the unittest command takes, and it prints
the summary the test runner prints and exits with the
verdict of the run, so the step the gate runs is unchanged
in everything but the bytes it executes.

The wrapper also measures the run it made. Where the gate
runner names a count file in its environment under
RECOGNITIO_COUNT_FILE, the wrapper writes the report of
that run to the named file once the run stands complete,
the count standing as the first line of the report, the
count being the number its own test runner reports for
the suite it executed, and the identities of the cases
in that suite standing after it, one to a line in sorted
order, and then leaves the process through the hard exit
with the verdict of the run. The hard exit is the seal
on the report. A suite module can register a shutdown
handler, and a handler that runs after the report stands
written could write the file again in its own words, so
the wrapper runs no shutdown handler the suite
registered and nothing the suite leaves behind speaks
after the report. The printed summary stays the human
artefact of the step. The report stands as the cross
check the gate runner holds against the census it takes
itself from the sources of the suite, and no count or
identity the floor arm judges is read out of text the
suite could print.

The wrapper also holds the suite it loaded against
the classes its sources produced. As each module the
finder answers for finishes loading from its source
bytes, the wrapper records the classes the loading
binds in that module its namespace and in the
namespaces of the classes standing in it, each under
the module name and the path of binding names that
reaches it from the module namespace, holding the
class object itself and the function the loading
left resolved for every test name in its ancestry.
The record takes its names from the bindings the
loading leaves standing and never from a name a
class carries on itself, so a nested class stands
recorded under its own nested path or not at all,
and no assignment to the qualified name a class
carries can move a class into a name the namespace
does not give it. The first object recorded under a
name holds the name against a later recording of
the same module, so an object built after the
loading that wears a stated name stands outside the
record by construction. Before the run is made,
every case of
the suite is held against the record, and a case
stands stated only where the class it is a case of
is the very object the record holds under the name
the case carries and the method it runs is the very
function the record holds for that name. A case the
loader builds for a module that failed to load
stands outside the holding, since the run it stands
in fails on it in its own words. Where any case
stands unstated the wrapper writes no report, and it
prints the refusal in its own output, naming the
first unstated case and the ground it stands
unstated on. Where the gate runner named a count
file the wrapper still leaves through the hard exit
with the verdict of the run, so the refusal the
runner speaks is the report that never stood. Where
no count file stands named no floor arm stands
behind the wrapper, and the wrapper refuses in its
own exit. The holding proves the population and its
provenance. It does not prove a stated body is
honest or meaningful, which stands with the run its
own verdict and with the vacuity guard elsewhere in
the gate.
"""

import argparse
import importlib.abc
import importlib.machinery
import importlib.util
import os
import sys
import unittest
from pathlib import Path


class _SourceLoader(importlib.machinery.SourceFileLoader):
    """A source loader that never reads a compiled cache.

    The inherited loader reads the cache standing beside
    the source wherever the cache claims the source, and
    an unchecked hash based cache makes that claim without
    reading the source at all. Compiling the bytes the
    file itself carries gives no cache a voice in what
    executes.
    """

    def get_code(self, fullname):
        return compile(
            self.get_data(self.path), self.path, "exec",
            dont_inherit=True,
        )

    def exec_module(self, module):
        super().exec_module(module)
        _record_loaded_module(module)


class _SourceFinder(importlib.abc.MetaPathFinder):
    """Answers for the modules whose source stands in one folder.

    The folder is the discover its top level folder, so the
    modules answered for are the suite its own modules and
    any package standing among them, the modules a shadow
    would impersonate. A name whose source stands nowhere
    in the folder is left to the ordinary search.
    """

    def __init__(self, root):
        self.root = Path(root)

    def find_spec(self, fullname, path=None, target=None):
        tail = fullname.rpartition(".")[2]
        if path:
            search = [
                Path(entry) for entry in path
                if Path(entry).resolve().is_relative_to(
                    self.root)
            ]
        else:
            search = [self.root]
        for entry in search:
            base = entry / tail
            module_path = base.with_suffix(".py")
            if module_path.is_file():
                loader = _SourceLoader(fullname, str(module_path))
                return importlib.util.spec_from_file_location(
                    fullname, module_path, loader=loader,
                )
            package_path = base / "__init__.py"
            if package_path.is_file():
                loader = _SourceLoader(
                    fullname, str(package_path))
                return importlib.util.spec_from_file_location(
                    fullname, package_path, loader=loader,
                    submodule_search_locations=[str(base)],
                )
        return None


# The record of the classes as they loaded, keyed on
# the module name and the path of binding names that
# reaches a class from the namespace of its module,
# holding the class object itself and the function
# resolved for every test name in its ancestry as the
# loading left it. The record is the holding the
# report stands on. A report states the identities of
# stated cases alone, and a suite carrying any other
# case leaves no report standing.
_STATED_CLASSES = {}

_UNSTATED = object()


def _held_function(value):
    """The function a class holds for one of its names.

    A plain definition stands in the class its body as
    the function itself. A static method or a class
    method stands there in its descriptor, and the
    function the descriptor wraps is the function a
    case of the class runs for that name.
    """
    if isinstance(value, (staticmethod, classmethod)):
        return value.__func__
    return value


def _record_loaded_module(module):
    """Record the classes a module states, as it loaded.

    The walk takes the bindings of the module its
    namespace in the order they stand, and the
    bindings of every class it reaches, and keys each
    class on the module name and the path of binding
    names that reaches it, so a class stands recorded
    under every name the loading binds it by in the
    namespaces that state it and under no other name.
    A nested class stands under its own nested path,
    and a class whose name on itself differs from the
    name its namespace binds it by stands recorded
    under the binding name alone, since no key of the
    record is read from the class object. An object
    is descended into once in the walk of one module,
    so a binding that reaches back to an object the
    walk has already descended into cannot carry the
    walk around a cycle. The first object recorded
    under a key holds the key against a later
    recording of the same module name, so the record
    holds the population the loading of the sources
    stated and nothing built after it. For every
    recorded class the walk resolves the function for
    every test name in the ancestry of the class, the
    nearest definition standing, which is the function
    a case of the class runs for that name as the
    loading left it.
    """
    descended = set()
    stack = [(vars(module), "")]
    while stack:
        namespace, prefix = stack.pop()
        for name, obj in list(namespace.items()):
            if not isinstance(obj, type):
                continue
            key = (module.__name__, prefix + name)
            if key not in _STATED_CLASSES:
                methods = {}
                for klass in obj.__mro__:
                    for meth, value in vars(klass).items():
                        if meth.startswith("test") and (
                            meth not in methods
                        ):
                            methods[meth] = _held_function(value)
                _STATED_CLASSES[key] = (obj, methods)
            if id(obj) not in descended:
                descended.add(id(obj))
                stack.append((vars(obj), prefix + name + "."))


def _measured_count_named():
    """The count file the gate runner named, or no name.

    The name rides in the environment the runner sets for
    the discover step alone. A wrapper run standing
    outside the runner, the wiring its own invocation
    among them, carries no name and reports nothing.
    """
    return os.environ.get("RECOGNITIO_COUNT_FILE") or None


def _suite_cases(suite):
    """The cases in a suite, flattened in run order.

    The suite the loader builds nests suites inside
    suites, so the walk flattens it to the cases
    themselves.
    """
    if isinstance(suite, unittest.TestSuite):
        for child in suite:
            yield from _suite_cases(child)
    elif isinstance(suite, unittest.TestCase):
        yield suite


def _suite_identities(suite):
    """The identities of the cases in a suite, in run order.

    Each case names itself in the form the loader
    names it, the module the class stands defined in
    and the class name and the method name.
    """
    for case in _suite_cases(suite):
        yield case.id()


def _unstated_ground(case):
    """The ground a case is not a stated case, or none.

    A case stands stated where the class it is a case
    of is the very class object the record holds under
    the name the case carries, and the method it runs
    is the very function the record holds for that
    name in that class. A case the loader builds for
    a module that failed to load states no identity of
    the suite and stands outside the holding, since
    the run it stands in fails on it in its own words.
    """
    cls = type(case)
    if cls is unittest.loader._FailedTest:
        return None
    entry = _STATED_CLASSES.get(
        (cls.__module__, cls.__qualname__))
    if entry is None:
        return (
            "no class the sources state stands under "
            "the name it carries"
        )
    stated, methods = entry
    if stated is not cls:
        return (
            "the class it is a case of is not the class "
            "the sources state under that name"
        )
    name = case._testMethodName
    held = methods.get(name, _UNSTATED)
    if held is _UNSTATED:
        return (
            "its method is not a method the class held "
            "as it loaded"
        )
    bound = getattr(case, name, None)
    if getattr(bound, "__func__", bound) is not held:
        return (
            "its method is not the function the class "
            "held for it as it loaded"
        )
    return None


def _write_measured_report(path, identities, result):
    """Write the report of the run just made to the named file.

    The report is the count of the run standing as the
    first line and the identities of the cases in the
    suite that ran standing after it, one to a line in
    sorted order, written whole as the content of the
    file. The identities are taken from the suite
    before the run is made, because the runner of the
    suite empties the suite as it runs it, so a reading
    taken after the run would name no case at all. A
    write the environment refuses leaves the file
    missing or standing in a shape the reading takes
    as no report, and the runner reads that as no
    report and refuses by name, so the failure lands
    closed and never as a count nobody measured.
    """
    lines = ["%d\n" % result.testsRun]
    for identity in identities:
        lines.append("%s\n" % identity)
    try:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("".join(lines))
    except OSError:
        pass


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run the test discover step from source."
    )
    parser.add_argument("-s", "--start-dir", default=".")
    parser.add_argument("-t", "--top-level-dir", default=None)
    parser.add_argument("-p", "--pattern", default="test*.py")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-q", "--quiet", action="store_true")
    args = parser.parse_args(argv)
    top = (
        Path(args.top_level_dir)
        if args.top_level_dir else Path(args.start_dir)
    )
    sys.meta_path.insert(0, _SourceFinder(top.resolve()))
    verbosity = 1
    if args.verbose:
        verbosity = 2
    if args.quiet:
        verbosity = 0
    loader = unittest.TestLoader()
    suite = loader.discover(
        args.start_dir, args.pattern, args.top_level_dir
    )
    identities = sorted(_suite_identities(suite))
    unstated = None
    for case in _suite_cases(suite):
        ground = _unstated_ground(case)
        if ground is not None:
            unstated = (case.id(), ground)
            break
    result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    code = 0 if result.wasSuccessful() else 1
    count_path = _measured_count_named()
    if unstated is not None:
        sys.stdout.flush()
        print(
            "the case %s is not a stated case, %s" % unstated,
            file=sys.stderr,
        )
        sys.stderr.flush()
        if count_path is not None:
            # The hard exit is the seal here as it is on
            # the report. Leaving by the ordinary path
            # would run every shutdown handler the suite
            # registered, and a handler could write a
            # report the wrapper never made into the file
            # the runner named, so no report of this run
            # stands anywhere. The verdict of the run is
            # carried in the exit as the report path
            # carries it, and the runner refuses on the
            # report that never stood.
            os._exit(code)
        return 1
    if count_path is not None:
        sys.stdout.flush()
        sys.stderr.flush()
        _write_measured_report(count_path, identities, result)
        # The hard exit is the seal on the measurement.
        # Leaving by the ordinary path would run every
        # shutdown handler the suite registered inside
        # this process, and a handler could write the
        # report file again after the measurement stands.
        # The verdict of the run is unchanged, carried in
        # the exit code as the ordinary path carries it.
        os._exit(code)
    return code


if __name__ == "__main__":
    sys.exit(main())
