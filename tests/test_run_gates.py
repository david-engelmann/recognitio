"""Tests for the shipped gate runner at scripts/run_gates.py.

Round 14. The gate wiring lived only in the Makefile, and
the run records of the programme were frontier claims
reconstructed from step logs after the fact, so a gate run
whose later steps never ran could still be reported as a
full run. The runner answers that by holding each step
log and meta keyed to the git tree hash of the state
under test, by pinning the discover count against a floor
the suite itself holds, and by writing the frontier into
the run record as it goes. The scratch repositories and
stub steps here stand in for the real wiring, and the two
readings of the shipped tree, the Makefile step list and
the pinned floor against the loader census, hold the
runner to the gate it ships with.
"""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_runner():
    spec = importlib.util.spec_from_file_location(
        "run_gates_under_test", ROOT / "scripts" / "run_gates.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = load_runner()

OK_STUB = "print('stub step holds')\n"
FAIL_STUB = "import sys\nprint('stub step refuses')\nsys.exit(3)\n"


def suite_source(plain, plant=None):
    """A real suite of plain passing tests, with an optional plant.

    The suite stands as one module at the root of the
    scratch repository. The plant, where one is handed,
    is the source of one or more further methods of the
    class, their names sorting where the shape needs
    them, and the count the suite holds is the plain
    cases plus the plant methods. Round 34 delta 2
    restated the fixture on real suites. The stub
    discover of the earlier rounds wrote whatever count
    it was handed onto the channel, and a fixture that
    takes the count on trust cannot price a reading
    whose whole claim is that the count is measured
    against a suite that stands in the tree.
    """
    lines = [
        "import os\n",
        "import signal\n",
        "import subprocess\n",
        "import sys\n",
        "import unittest\n",
        "\n",
        "\n",
        "class TestScratchSuite(unittest.TestCase):\n",
    ]
    for index in range(plain):
        lines.append(
            "    def test_case_%03d(self):\n" % index
        )
        lines.append("        self.assertEqual(1, 1)\n")
    if plant is not None:
        lines.append(plant)
    return "".join(lines)


def exit_zero_plant(figure):
    """A last test that forges the report and ends the process.

    The plant writes the handed figure into the channel
    file the runner named and leaves through the hard
    exit, so the wrapper dies inside its own run with a
    clean exit code and no report of its own ever
    stands. This is the delta confirmation its Minor 1
    in shipped form.
    """
    return "".join([
        "    def test_z_plant(self):\n",
        "        channel = os.environ['RECOGNITIO_COUNT_FILE']\n",
        "        with open(channel, 'w') as handle:\n",
        "            handle.write('",
        str(figure),
        "\\n')\n",
        "        os._exit(0)\n",
    ])


def detached_writer_plant(figure):
    """A test that leaves a detached writer standing on the channel.

    The plant spawns a shell in its own session set to
    rewrite the channel file with the handed figure
    across a span that covers the runner its whole post
    step path, and the test itself passes. This is the
    delta confirmation its Minor 2 in shipped form.
    """
    return "".join([
        "    def test_z_plant(self):\n",
        "        channel = os.environ['RECOGNITIO_COUNT_FILE']\n",
        "        script = (\n",
        "            'i=0; while [ $((i=i+1)) -lt 400 ]; do '\n",
        "            'printf \"%s\\\\n\" \"",
        str(figure),
        "\" > \"$1\"; sleep 0.05; done'\n",
        "        )\n",
        "        subprocess.Popen(\n",
        "            ['sh', '-c', script, 'sh', channel],\n",
        "            stdout=subprocess.DEVNULL,\n",
        "            stderr=subprocess.DEVNULL,\n",
        "            start_new_session=True,\n",
        "        )\n",
        "        self.assertEqual(1, 1)\n",
    ])


def killed_step_plants(figure):
    """A suite that plants a report and then dies by signal.

    The first plant writes the handed figure into the
    channel file, and the last ends the process by
    signal, so the step fails with a forged count
    standing in its channel and no completion. The
    delta confirmation its first Note prices what the
    meta of such a step may carry.
    """
    return "".join([
        "    def test_a_plant(self):\n",
        "        channel = os.environ['RECOGNITIO_COUNT_FILE']\n",
        "        with open(channel, 'w') as handle:\n",
        "            handle.write('",
        str(figure),
        "\\n')\n",
        "    def test_z_plant(self):\n",
        "        os.kill(os.getpid(), signal.SIGKILL)\n",
    ])


def sabotage_plant(figure):
    """A test that destroys the report channel and prints a block.

    The plant makes a folder of the channel path, so
    the write the wrapper makes at the end of its run
    is refused and no report stands, and it prints a
    whole summary block at the handed figure to the
    error stream. The printed block is the strongest
    text the earlier readings priced, and it must
    carry nothing here.
    """
    return "".join([
        "    def test_z_plant(self):\n",
        "        channel = os.environ['RECOGNITIO_COUNT_FILE']\n",
        "        os.makedirs(channel)\n",
        "        sys.stderr.write('Ran ",
        str(figure),
        " tests in 0.9s\\n')\n",
        "        sys.stderr.write('\\n')\n",
        "        sys.stderr.write('OK\\n')\n",
        "        self.assertEqual(1, 1)\n",
    ])


def block_plant(*counts):
    """A test that prints whole summary blocks to its stream.

    Each count handed is printed as one whole summary
    block in the form the test runner closes with, in
    the order handed, and the genuine summary of the
    run stands in the same stream wherever the run
    puts it. No placement of the plants can carry the
    floor, because no printed line of any form is read
    for the count.
    """
    lines = ["    def test_z_plant(self):\n"]
    for count in counts:
        lines.append(
            "        sys.stderr.write("
            "'Ran %d tests in 0.9s\\n')\n" % count
        )
        lines.append("        sys.stderr.write('\\n')\n")
        lines.append("        sys.stderr.write('OK\\n')\n")
    lines.append("        self.assertEqual(1, 1)\n")
    return "".join(lines)


def bare_line_plant(figure):
    """A test that prints one bare count line to its stream."""
    return "".join([
        "    def test_z_plant(self):\n",
        "        sys.stderr.write('Ran ",
        str(figure),
        " tests\\n')\n",
        "        self.assertEqual(1, 1)\n",
    ])


TRUNCATE_PLANT = (
    "    def test_z_plant(self):\n"
    "        os._exit(0)\n"
)

LOAD_PRINT_SUITE = (
    "import unittest\n"
    "\n"
    "print('recognitio-measured-count 5')\n"
    "\n"
    "\n"
    "class TestScratchSuite(unittest.TestCase):\n"
    "    def test_a(self):\n"
    "        self.assertEqual(1, 1)\n"
    "    def test_b(self):\n"
    "        self.assertEqual(1, 1)\n"
    "    def test_c(self):\n"
    "        self.assertEqual(1, 1)\n"
)

COMBINED_SUITE = (
    "import os\n"
    "import subprocess\n"
    "import unittest\n"
    "\n"
    "channel = os.environ.get('RECOGNITIO_COUNT_FILE')\n"
    "if channel:\n"
    "    script = (\n"
    "        'i=0; while [ $((i=i+1)) -lt 40 ]; do '\n"
    "        'printf \"%s\\n\" \"5\" > \"$1\"; sleep 0.05; done'\n"
    "    )\n"
    "    subprocess.Popen(\n"
    "        ['sh', '-c', script, 'sh', channel],\n"
    "        start_new_session=True,\n"
    "    )\n"
    "    os._exit(0)\n"
    "\n"
    "\n"
    "class TestScratchSuite(unittest.TestCase):\n"
    "    def test_a(self):\n"
    "        self.assertEqual(1, 1)\n"
    "    def test_b(self):\n"
    "        self.assertEqual(1, 1)\n"
    "    def test_c(self):\n"
    "        self.assertEqual(1, 1)\n"
)

GENERATED_SUITE = (
    "import unittest\n"
    "\n"
    "\n"
    "class TestScratchSuite(unittest.TestCase):\n"
    "    def test_a(self):\n"
    "        self.assertEqual(1, 1)\n"
    "    def test_b(self):\n"
    "        self.assertEqual(1, 1)\n"
    "    def test_c(self):\n"
    "        self.assertEqual(1, 1)\n"
    "\n"
    "\n"
    "for _index in range(2):\n"
    "    setattr(\n"
    "        TestScratchSuite,\n"
    "        'test_generated_%d' % _index,\n"
    "        lambda self: None,\n"
    "    )\n"
)

CONDITIONAL_SUITE = (
    "import os\n"
    "import unittest\n"
    "\n"
    "\n"
    "class TestScratchSuite(unittest.TestCase):\n"
    "    if 'RECOGNITIO_COUNT_FILE' in os.environ:\n"
    "        def test_a(self):\n"
    "            self.assertEqual(1, 1)\n"
    "        def test_b(self):\n"
    "            self.assertEqual(1, 1)\n"
    "        def test_c(self):\n"
    "            self.assertEqual(1, 1)\n"
    "    else:\n"
    "        def test_a(self):\n"
    "            self.assertEqual(1, 1)\n"
    "        def test_b(self):\n"
    "            self.assertEqual(1, 1)\n"
    "        def test_c(self):\n"
    "            self.assertEqual(1, 1)\n"
    "        def test_d(self):\n"
    "            self.assertEqual(1, 1)\n"
    "        def test_e(self):\n"
    "            self.assertEqual(1, 1)\n"
)

SUBSTITUTE_SUITE = (
    "import unittest\n"
    "\n"
    "\n"
    "class TestScratchSuite(unittest.TestCase):\n"
    "    def test_a(self):\n"
    "        self.assertEqual(1, 2)\n"
    "    def test_b(self):\n"
    "        self.assertEqual(1, 2)\n"
    "    def test_c(self):\n"
    "        self.assertEqual(1, 2)\n"
    "\n"
    "\n"
    "def load_tests(loader, standard_tests, pattern):\n"
    "    class TestSynthetic(unittest.TestCase):\n"
    "        def test_x(self):\n"
    "            self.assertEqual(1, 1)\n"
    "        def test_y(self):\n"
    "            self.assertEqual(1, 1)\n"
    "        def test_z(self):\n"
    "            self.assertEqual(1, 1)\n"
    "    return loader.loadTestsFromTestCase(TestSynthetic)\n"
)

MUTATION_SUITE = (
    "import unittest\n"
    "\n"
    "\n"
    "class TestScratchSuite(unittest.TestCase):\n"
    "    def test_a(self):\n"
    "        self.assertEqual(1, 2)\n"
    "    def test_b(self):\n"
    "        self.assertEqual(1, 2)\n"
    "    def test_c(self):\n"
    "        self.assertEqual(1, 2)\n"
    "\n"
    "\n"
    "del TestScratchSuite.test_a\n"
    "del TestScratchSuite.test_b\n"
    "del TestScratchSuite.test_c\n"
    "TestScratchSuite.test_p = lambda self: None\n"
    "TestScratchSuite.test_q = lambda self: None\n"
    "TestScratchSuite.test_r = lambda self: None\n"
)

STATED_PLUS_SUITE = (
    "import unittest\n"
    "\n"
    "\n"
    "class TestScratchSuite(unittest.TestCase):\n"
    "    def test_a(self):\n"
    "        self.assertEqual(1, 1)\n"
    "    def test_b(self):\n"
    "        self.assertEqual(1, 1)\n"
    "    def test_c(self):\n"
    "        self.assertEqual(1, 1)\n"
    "\n"
    "\n"
    "def load_tests(loader, standard_tests, pattern):\n"
    "    class TestExtra(unittest.TestCase):\n"
    "        def test_x(self):\n"
    "            self.assertEqual(1, 1)\n"
    "    suite = unittest.TestSuite()\n"
    "    suite.addTests(standard_tests)\n"
    "    suite.addTests(loader.loadTestsFromTestCase(TestExtra))\n"
    "    return suite\n"
)

SPOOF_SUITE = (
    "import unittest\n"
    "\n"
    "\n"
    "class TestScratchSuite(unittest.TestCase):\n"
    "    def test_a(self):\n"
    "        self.assertEqual(1, 2)\n"
    "    def test_b(self):\n"
    "        self.assertEqual(1, 2)\n"
    "    def test_c(self):\n"
    "        self.assertEqual(1, 2)\n"
    "\n"
    "\n"
    "def load_tests(loader, standard_tests, pattern):\n"
    "    class TestForged(unittest.TestCase):\n"
    "        def test_a(self):\n"
    "            self.assertEqual(1, 1)\n"
    "        def test_b(self):\n"
    "            self.assertEqual(1, 1)\n"
    "        def test_c(self):\n"
    "            self.assertEqual(1, 1)\n"
    "    TestForged.__module__ = 'test_generated'\n"
    "    TestForged.__qualname__ = 'TestScratchSuite'\n"
    "    return loader.loadTestsFromTestCase(TestForged)\n"
)

SPOOF_SUBCLASS_SUITE = (
    "import unittest\n"
    "\n"
    "\n"
    "class TestScratchSuite(unittest.TestCase):\n"
    "    def test_a(self):\n"
    "        self.assertEqual(1, 2)\n"
    "    def test_b(self):\n"
    "        self.assertEqual(1, 2)\n"
    "    def test_c(self):\n"
    "        self.assertEqual(1, 2)\n"
    "\n"
    "\n"
    "def load_tests(loader, standard_tests, pattern):\n"
    "    class TestWorn(TestScratchSuite):\n"
    "        def test_a(self):\n"
    "            self.assertEqual(1, 1)\n"
    "        def test_b(self):\n"
    "            self.assertEqual(1, 1)\n"
    "        def test_c(self):\n"
    "            self.assertEqual(1, 1)\n"
    "    TestWorn.__module__ = 'test_generated'\n"
    "    TestWorn.__qualname__ = 'TestScratchSuite'\n"
    "    return loader.loadTestsFromTestCase(TestWorn)\n"
)

METHOD_REPLACED_SUITE = (
    "import unittest\n"
    "\n"
    "\n"
    "class TestScratchSuite(unittest.TestCase):\n"
    "    def test_a(self):\n"
    "        self.assertEqual(1, 1)\n"
    "    def test_b(self):\n"
    "        self.assertEqual(1, 2)\n"
    "    def test_c(self):\n"
    "        self.assertEqual(1, 1)\n"
    "\n"
    "\n"
    "def load_tests(loader, standard_tests, pattern):\n"
    "    TestScratchSuite.test_b = lambda self: None\n"
    "    return loader.loadTestsFromTestCase(TestScratchSuite)\n"
)

STATED_WHOLE_SUITE = (
    "import unittest\n"
    "\n"
    "\n"
    "class TestScratchSuite(unittest.TestCase):\n"
    "    def test_a(self):\n"
    "        self.assertEqual(1, 1)\n"
    "    def test_b(self):\n"
    "        self.assertEqual(1, 1)\n"
    "    def test_c(self):\n"
    "        self.assertEqual(1, 1)\n"
    "\n"
    "\n"
    "def load_tests(loader, standard_tests, pattern):\n"
    "    return loader.loadTestsFromTestCase(TestScratchSuite)\n"
)

BODY_SWAP_SUITE = (
    "import unittest\n"
    "\n"
    "\n"
    "class TestScratchSuite(unittest.TestCase):\n"
    "    def test_a(self):\n"
    "        self.assertEqual(1, 2)\n"
    "    def test_b(self):\n"
    "        self.assertEqual(1, 1)\n"
    "    def test_c(self):\n"
    "        self.assertEqual(1, 1)\n"
    "\n"
    "\n"
    "TestScratchSuite.test_a = lambda self: None\n"
)

UNICODE_SUITE = (
    "import unittest\n"
    "\n"
    "\n"
    "class TestScratchSuite(unittest.TestCase):\n"
    "    def test_a(self):\n"
    "        self.assertEqual(1, 1)\n"
    "    def test_b(self):\n"
    "        self.assertEqual(1, 1)\n"
    "    def test_café(self):\n"
    "        self.assertEqual(1, 1)\n"
)

NESTED_CLAIMANT_SUITE = (
    "import unittest\n"
    "\n"
    "\n"
    "class TestScratchSuite(unittest.TestCase):\n"
    "    def test_a(self):\n"
    "        self.assertEqual(1, 2)\n"
    "    def test_b(self):\n"
    "        self.assertEqual(1, 2)\n"
    "    def test_c(self):\n"
    "        self.assertEqual(1, 2)\n"
    "\n"
    "\n"
    "class Outer:\n"
    "    class Inner(unittest.TestCase):\n"
    "        def test_a(self):\n"
    "            self.assertEqual(1, 1)\n"
    "        def test_b(self):\n"
    "            self.assertEqual(1, 1)\n"
    "        def test_c(self):\n"
    "            self.assertEqual(1, 1)\n"
    "\n"
    "\n"
    "Outer.Inner.__qualname__ = 'TestScratchSuite'\n"
    "\n"
    "\n"
    "def load_tests(loader, standard_tests, pattern):\n"
    "    return loader.loadTestsFromTestCase(Outer.Inner)\n"
)

NESTED_CLAIMANT_HOOK_SUITE = (
    "import unittest\n"
    "\n"
    "\n"
    "class TestScratchSuite(unittest.TestCase):\n"
    "    def test_a(self):\n"
    "        self.assertEqual(1, 2)\n"
    "    def test_b(self):\n"
    "        self.assertEqual(1, 2)\n"
    "    def test_c(self):\n"
    "        self.assertEqual(1, 2)\n"
    "\n"
    "\n"
    "class Outer:\n"
    "    class Inner(unittest.TestCase):\n"
    "        def test_a(self):\n"
    "            self.assertEqual(1, 1)\n"
    "        def test_b(self):\n"
    "            self.assertEqual(1, 1)\n"
    "        def test_c(self):\n"
    "            self.assertEqual(1, 1)\n"
    "\n"
    "\n"
    "def load_tests(loader, standard_tests, pattern):\n"
    "    Outer.Inner.__qualname__ = 'TestScratchSuite'\n"
    "    return loader.loadTestsFromTestCase(Outer.Inner)\n"
)

CLASS_REBIND_SUITE = (
    "import unittest\n"
    "\n"
    "\n"
    "class TestScratchSuite(unittest.TestCase):\n"
    "    def test_a(self):\n"
    "        self.assertEqual(1, 2)\n"
    "    def test_b(self):\n"
    "        self.assertEqual(1, 2)\n"
    "    def test_c(self):\n"
    "        self.assertEqual(1, 2)\n"
    "\n"
    "\n"
    "class TestReplacement(unittest.TestCase):\n"
    "    def test_a(self):\n"
    "        self.assertEqual(1, 1)\n"
    "    def test_b(self):\n"
    "        self.assertEqual(1, 1)\n"
    "    def test_c(self):\n"
    "        self.assertEqual(1, 1)\n"
    "\n"
    "\n"
    "TestScratchSuite = TestReplacement\n"
)


class RunnerFixture(unittest.TestCase):
    """A scratch git repository with a real suite and stub steps.

    The scratch tree carries the shipped discover
    wrapper at the path the wiring names it, copied
    from the tree under test at the bytes that tree
    holds, so the discover step of the fixture is the
    shipped step and the runner takes the census of
    the fixture suite through the same machinery it
    takes the census of the real one.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "repo"
        self.root.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Gate Runner Test")
        self.logs = Path(self.tmp.name) / "logs"
        scripts = self.root / "scripts"
        scripts.mkdir()
        (scripts / "discover.py").write_bytes(
            (ROOT / "scripts" / "discover.py").read_bytes()
        )

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.root), *args],
            capture_output=True, text=True, check=True,
        )

    def write(self, name, text):
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def commit(self):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "scratch state")

    def write_suite(self, plain, plant=None):
        self.write(
            "test_generated.py", suite_source(plain, plant))

    def discover_steps(self):
        return [
            [sys.executable, "scripts/discover.py", "-s", "."],
            [sys.executable, "check_stub.py"],
        ]

    def steps(self, discover_count=5, failing=False):
        self.write_suite(discover_count)
        self.write("check_stub.py", OK_STUB)
        steps = self.discover_steps()
        if failing:
            self.write("fail_stub.py", FAIL_STUB)
            steps.insert(1, [sys.executable, "fail_stub.py"])
        return steps


class TestRunnerRecords(RunnerFixture):

    def test_a_passing_run_is_keyed_to_the_tree(self):
        steps = self.steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5
        )
        self.assertEqual(code, 0, record)
        self.assertEqual(record["verdict"], "pass")
        self.assertEqual(record["steps_not_run"], [])
        run_dir = self.logs / record["tree"]
        on_disk = json.loads(
            (run_dir / "run.json").read_text(encoding="utf-8")
        )
        self.assertEqual(on_disk["tree"], record["tree"])
        self.assertEqual(on_disk["head"], record["head"])
        discover_meta = json.loads(
            (run_dir / "01-discover.json").read_text(encoding="utf-8")
        )
        self.assertEqual(discover_meta["exit_code"], 0)
        self.assertEqual(discover_meta["count"], 5)
        self.assertEqual(discover_meta["reported_count"], 5)
        self.assertEqual(discover_meta["tree"], record["tree"])
        self.assertIn(
            "Ran 5 tests",
            (run_dir / "01-discover.log").read_text(encoding="utf-8"),
        )
        stub_meta = json.loads(
            (run_dir / "02-check_stub.json").read_text(
                encoding="utf-8")
        )
        self.assertEqual(stub_meta["step"], "check_stub")

    def test_a_dirty_tree_is_refused_until_the_flag_names_it(self):
        steps = self.steps()
        self.commit()
        self.write("check_stub.py", OK_STUB + "# local edit\n")
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5
        )
        self.assertEqual(code, 1)
        self.assertIn("refused", record["verdict"])
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5,
            allow_dirty=True,
        )
        self.assertEqual(code, 0, record)
        self.assertTrue(record["dirty"])

    def test_its_own_log_output_never_makes_the_tree_dirty(self):
        steps = self.steps()
        self.commit()
        inside = self.root / ".gate-logs"
        code, record = runner.run_gates(
            self.root, log_dir=inside, steps=steps, floor=5
        )
        self.assertEqual(code, 0, record)
        self.assertEqual(record["verdict"], "pass")
        self.assertFalse(record["dirty"])
        self.assertEqual(record["own_output_entries"], 0)
        code, record = runner.run_gates(
            self.root, log_dir=inside, steps=steps, floor=5
        )
        self.assertEqual(code, 0, record)
        self.assertEqual(record["verdict"], "pass")

    def test_a_failing_step_stops_with_the_frontier_named(self):
        steps = self.steps(failing=True)
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5
        )
        self.assertEqual(code, 1)
        self.assertEqual(record["failing_step"], "fail_stub")
        self.assertEqual(record["steps_completed"], ["discover"])
        self.assertEqual(record["steps_not_run"], ["check_stub"])
        on_disk = json.loads(
            (self.logs / record["tree"] / "run.json").read_text(
                encoding="utf-8")
        )
        self.assertEqual(on_disk["failing_step"], "fail_stub")
        self.assertFalse(
            (self.logs / record["tree"] / "03-check_stub.json").exists()
        )

    def test_a_discover_count_under_the_floor_fails_a_green_step(self):
        steps = self.steps(discover_count=2)
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5
        )
        self.assertEqual(code, 1)
        self.assertEqual(record["failing_step"], "discover")
        self.assertIn("pinned floor of 5", record["failure_reason"])

    def test_a_root_that_is_not_a_checkout_is_refused(self):
        plain = Path(self.tmp.name) / "plain"
        plain.mkdir()
        code, record = runner.run_gates(
            plain, log_dir=self.logs,
            steps=[[sys.executable, "discover.py"]], floor=5,
        )
        self.assertEqual(code, 1)
        self.assertIsNone(record["tree"])
        self.assertIn("not a git checkout", record["verdict"])


class TestRunnerAgainstTheShippedTree(unittest.TestCase):

    def test_the_makefile_step_list_is_the_check_wiring_in_order(self):
        steps = runner.parse_makefile_steps(
            (ROOT / "Makefile").read_text(encoding="utf-8")
        )
        names = [runner.step_name(step) for step in steps]
        self.assertEqual(len(names), 26)
        self.assertEqual(names[0], "discover")
        self.assertEqual(names[-1], "smoke_extract")
        for expected in (
            "check_skill", "check_version", "check_copy",
            "check_persona", "check_mod", "check_brand",
            "check_submissions", "check_test_vacuity",
        ):
            self.assertIn(expected, names)

    def test_the_pinned_floor_equals_the_loader_census(self):
        suite = unittest.TestLoader().discover(str(ROOT / "tests"))
        self.assertEqual(
            runner.PINNED_TEST_FLOOR, suite.countTestCases()
        )


if __name__ == "__main__":
    unittest.main()


class TestCountLineLastMatch(unittest.TestCase):
    """Round 15, restated in Round 34. The count is the block.

    Round 15 priced the first match reading, under which a
    stray earlier line could claim a count the step never
    printed as its verdict, and the reading took the last
    count line in its place. Round 34 priced the mirror
    shape, a bare count line printed after the real summary
    by a shutdown handler claiming the census the floor arm
    reads, and the reading now takes the last count line
    standing in the summary block form the test runner
    closes with its verdict word. The plants below hold
    both stray shapes and the block reading between them.

    The delta of Round 34 narrows the office of this
    reading. The red team confirmation priced the block
    forged whole, a planted summary block standing after
    the genuine one, and no reading over text the suite
    can write can tell that plant from the verdict it
    imitates. The discover count the floor arm judges is
    therefore taken by the runner itself from the
    sources of the suite the step names and never read
    from text at all, and this class now prices the
    artefact reading of the steps whose counts no arm
    judges. The floor shapes stand priced end to end
    in the rekey class below, against the census of
    the delta 3 form.
    """

    def setUp(self):
        self.mod = load_runner()

    def test_the_last_count_is_the_count_taken(self):
        output = (
            "Ran 9999 tests in 0.001s\n"
            "\n"
            "OK\n"
            "noise between the claims\n"
            "Ran 2 tests in 0.002s\n"
            "\n"
            "OK\n"
        )
        self.assertEqual(
            self.mod.count_line(output), (2, "Ran 2 tests")
        )

    def test_a_single_count_still_reads(self):
        self.assertEqual(
            self.mod.count_line("Ran 7 tests in 1.0s\n\nOK\n"),
            (7, "Ran 7 tests"),
        )

    def test_a_bare_line_before_the_block_claims_nothing(self):
        output = (
            "Ran 9999 tests\n"
            "noise between the claims\n"
            "Ran 2 tests in 0.002s\n"
            "\n"
            "OK\n"
        )
        self.assertEqual(
            self.mod.count_line(output), (2, "Ran 2 tests")
        )

    def test_a_bare_line_after_the_block_claims_nothing(self):
        output = (
            "Ran 3 tests in 0.1s\n"
            "\n"
            "OK\n"
            "Ran 3265 tests\n"
        )
        self.assertEqual(
            self.mod.count_line(output), (3, "Ran 3 tests")
        )

    def test_a_bare_count_line_alone_returns_no_count(self):
        self.assertEqual(
            self.mod.count_line("Ran 7 tests in 1.0s\n"),
            (None, None),
        )
        self.assertEqual(
            self.mod.count_line("Ran 7 tests\n\nOK\n"),
            (None, None),
        )

    def test_no_count_line_returns_no_count(self):
        self.assertEqual(self.mod.count_line("no counts\n"), (None, None))


class TestRunnerRekeyAndFloorArms(RunnerFixture):
    """Round 24. The end of run re-key and the null count arm.

    Red team Major 2 priced the runner keying its verdict
    once, before the first step, and never reading its tree
    again, so a mid run edit re-keyed the remaining steps to
    foreign bytes under the original tree in both directions.
    Standards Minor 1 priced the floor arm passing a discover
    step that printed no count at all. The step stubs below
    are the writers, standing in for the timed writers the
    audit drove, and each construction is deterministic.

    Round 24 delta. The red team confirmation priced the
    round trip the closing reading cannot see, a substitute
    held across one step own read and restored byte exact
    before the close, and the runner now reads the identity
    again after every step, so a movement stops the run at
    the step it followed and no later step runs over moved
    bytes. The first two constructions below changed their
    frontier under that reading by design, and the round
    trip pair prices the narrowed window and its residue.
    """

    def test_a_discover_step_reporting_no_count_fails_by_name(self):
        # Restated in the delta 3 form. The discover step
        # is a foreign script that prints its text and
        # reports nothing, while a real suite stands in
        # the root for the runner to take its census from.
        # The runner takes the census of the suite whole
        # from its sources, and the run still refuses,
        # because the report of the step is the cross
        # check on the census and a run with no report
        # standing against its census is not certified.
        # The meta count of the earlier form, which read
        # no count here, now reads the census taken from
        # the sources, and the report stands as none.
        self.write_suite(5)
        self.write("discover.py", "print('the suite holds')\n")
        self.write("check_stub.py", OK_STUB)
        steps = [
            [sys.executable, "discover.py"],
            [sys.executable, "check_stub.py"],
        ]
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5
        )
        self.assertEqual(code, 1, record)
        self.assertEqual(record["failing_step"], "discover")
        self.assertIn("reported no measured count",
                      record["failure_reason"])
        meta = json.loads(
            (self.logs / record["tree"] / "01-discover.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(meta["count"], 5)
        self.assertIsNone(meta["reported_count"])

    def test_a_step_that_dirties_the_tree_mid_run_is_refused(self):
        self.write("tracked.txt", "clean\n")
        self.write(
            "writer.py",
            "open('tracked.txt', 'a').write("
            "'a colon: lands mid run\\n')\n",
        )
        steps = self.steps()
        steps.insert(1, [sys.executable, "writer.py"])
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5
        )
        self.assertEqual(code, 1, record)
        self.assertIn("the tree moved during the run",
                      record["verdict"])
        # The delta reading stops the run at the step the
        # movement followed, so the check step never runs.
        self.assertEqual(record["steps_completed"],
                         ["discover", "writer"])
        self.assertEqual(record["steps_not_run"], ["check_stub"])
        self.assertEqual(record["movement_after_step"], "writer")
        self.assertFalse(record["dirty"])
        self.assertTrue(record["closing_dirty"])

    def test_a_step_that_cleans_a_refusing_tree_earns_no_pass(self):
        self.write(
            "tracked.txt", "a colon: stands committed\n")
        self.write(
            "restorer.py",
            "open('tracked.txt', 'w').write('clean\\n')\n",
        )
        self.write(
            "gate_stub.py",
            "import sys\n"
            "sys.exit(1 if ':' in open('tracked.txt').read()"
            " else 0)\n",
        )
        steps = self.steps()
        steps[1] = [sys.executable, "restorer.py"]
        steps.append([sys.executable, "gate_stub.py"])
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5
        )
        self.assertEqual(code, 1, record)
        self.assertIn("the tree moved during the run",
                      record["verdict"])
        # The delta reading stops the run at the step the
        # movement followed, so the gate step that would
        # have passed over the cleaned bytes never runs.
        self.assertEqual(record["steps_completed"],
                         ["discover", "restorer"])
        self.assertEqual(record["steps_not_run"], ["gate_stub"])
        self.assertEqual(record["movement_after_step"], "restorer")
        self.assertTrue(record["closing_dirty"])

    def test_a_step_that_commits_mid_run_is_refused(self):
        self.write(
            "committer.py",
            "import subprocess\n"
            "open('landed.txt', 'w').write('new\\n')\n"
            "subprocess.run(['git', 'add', '-A'], check=True)\n"
            "subprocess.run(['git', 'commit', '-q', '-m', "
            "'mid run'], check=True)\n",
        )
        steps = self.steps()
        steps.insert(1, [sys.executable, "committer.py"])
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5
        )
        self.assertEqual(code, 1, record)
        self.assertIn("the tree moved during the run",
                      record["verdict"])
        self.assertNotEqual(record["closing_head"], record["head"])
        self.assertNotEqual(record["closing_tree"], record["tree"])

    def test_step_metas_carry_the_terms_of_their_run(self):
        steps = self.steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5
        )
        self.assertEqual(code, 0, record)
        meta = json.loads(
            (self.logs / record["tree"] / "01-discover.json")
            .read_text(encoding="utf-8")
        )
        self.assertFalse(meta["dirty"])
        self.assertFalse(meta["allow_dirty"])
        self.write("check_stub.py", OK_STUB + "# local edit\n")
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5,
            allow_dirty=True,
        )
        self.assertEqual(code, 0, record)
        meta = json.loads(
            (self.logs / record["tree"] / "01-discover.json")
            .read_text(encoding="utf-8")
        )
        self.assertTrue(meta["dirty"])
        self.assertTrue(meta["allow_dirty"])


    def test_a_substitute_held_across_a_step_is_refused_there(self):
        # The confirmation round trip. The writer swaps
        # clean bytes over a refusing file, the judging step
        # would read them and pass, and the restorer returns
        # the committed bytes, so the closing state equals
        # the opening state and the J2 closing reading alone
        # passed the swap. The between steps reading meets
        # the movement at the step that made it.
        self.write("tracked.txt", "a colon: stands committed\n")
        self.write(
            "writer.py",
            "open('tracked.txt', 'w').write('clean\\n')\n")
        self.write(
            "gate_stub.py",
            "import sys\n"
            "sys.exit(1 if ':' in open('tracked.txt').read()"
            " else 0)\n")
        self.write(
            "restorer.py",
            "open('tracked.txt', 'w').write("
            "'a colon: stands committed\\n')\n")
        steps = [
            [sys.executable, "writer.py"],
            [sys.executable, "gate_stub.py"],
            [sys.executable, "restorer.py"],
        ]
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5
        )
        self.assertEqual(code, 1, record)
        self.assertIn("the tree moved during the run",
                      record["verdict"])
        self.assertEqual(record["movement_after_step"], "writer")
        self.assertEqual(record["steps_completed"], ["writer"])
        self.assertEqual(record["steps_not_run"],
                         ["gate_stub", "restorer"])
        self.assertTrue(record["closing_dirty"])

    def test_a_round_trip_inside_one_step_is_the_named_residue(self):
        # The residue the runner docstring names in the
        # open. A swap and a restore inside the span of one
        # step own execution never stands at a step
        # boundary, so no reading between steps can see it,
        # and the run passes. The plant prices the boundary
        # of the repair rather than claiming the window
        # closed whole.
        self.write("tracked.txt", "a colon: stands committed\n")
        self.write(
            "swapper.py",
            "open('tracked.txt', 'w').write('clean\\n')\n"
            "open('tracked.txt', 'w').write("
            "'a colon: stands committed\\n')\n")
        self.write("check_stub.py", OK_STUB)
        steps = [
            [sys.executable, "swapper.py"],
            [sys.executable, "check_stub.py"],
        ]
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5
        )
        self.assertEqual(code, 0, record)
        self.assertEqual(record["verdict"], "pass")
        self.assertNotIn("movement_after_step", record)

    def test_a_forged_summary_block_does_not_carry_the_floor(self):
        # Round 34 delta, the red team confirmation Minor,
        # restated on a real suite in the delta 3 form. A
        # test of the suite prints its genuine summary
        # block at three and then a whole forged summary
        # block claiming the floor, in the shape a shutdown
        # writer leaves after the genuine block in the
        # combined output. The block reading of the fix
        # pass took the forged block as the count of the
        # step. The floor arm now reads the runner its
        # census from the sources alone, so the run fails
        # at the census of three and the meta records that
        # count with no line beside it.
        self.write_suite(2, block_plant(3, 5))
        self.write("check_stub.py", OK_STUB)
        steps = self.discover_steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5
        )
        self.assertEqual(code, 1, record)
        self.assertEqual(record["failing_step"], "discover")
        self.assertIn("counted 3 tests", record["failure_reason"])
        meta = json.loads(
            (self.logs / record["tree"] / "01-discover.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(meta["count"], 3)
        self.assertEqual(meta["reported_count"], 3)
        self.assertIsNone(meta["count_line"])

    def test_a_forged_block_before_the_genuine_block_claims_nothing(self):
        # The mirror placement. A forged block printed
        # during the run, standing before the genuine
        # block in the combined output, is the same plant
        # at the other end of the log, and the census
        # taken from the sources answers it the same way.
        self.write_suite(2, block_plant(5, 3))
        self.write("check_stub.py", OK_STUB)
        steps = self.discover_steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5
        )
        self.assertEqual(code, 1, record)
        self.assertEqual(record["failing_step"], "discover")
        self.assertIn("counted 3 tests", record["failure_reason"])
        meta = json.loads(
            (self.logs / record["tree"] / "01-discover.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(meta["count"], 3)
        self.assertEqual(meta["reported_count"], 3)

    def test_a_planted_late_count_line_does_not_carry_the_floor(self):
        # Round 34 red team Minor 2, restated on a real
        # suite. The bare line the fix pass priced still
        # claims nothing, now because no printed line of
        # any form carries the floor.
        self.write_suite(2, bare_line_plant(3265))
        self.write("check_stub.py", OK_STUB)
        steps = self.discover_steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5
        )
        self.assertEqual(code, 1, record)
        self.assertEqual(record["failing_step"], "discover")
        self.assertIn("counted 3 tests", record["failure_reason"])
        meta = json.loads(
            (self.logs / record["tree"] / "01-discover.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(meta["count"], 3)
        self.assertIsNone(meta["count_line"])

    def test_a_printed_block_without_a_report_fails_by_name(self):
        # The count free control in its strong form,
        # restated in the delta 3 form. A test of the
        # suite destroys the report channel, so the step
        # reports nothing, and prints a whole summary
        # block at the floor figure. The run is refused
        # by name on the missing report, because the
        # printed block is text the suite could have
        # forged whole and no arm reads it. The meta
        # count of the earlier form, which read no count
        # here, now reads the census of three taken from
        # the sources.
        self.write_suite(2, sabotage_plant(5))
        self.write("check_stub.py", OK_STUB)
        steps = self.discover_steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5
        )
        self.assertEqual(code, 1, record)
        self.assertEqual(record["failing_step"], "discover")
        self.assertIn("reported no measured count",
                      record["failure_reason"])
        meta = json.loads(
            (self.logs / record["tree"] / "01-discover.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(meta["count"], 3)
        self.assertIsNone(meta["reported_count"])

    def test_a_stale_count_file_does_not_speak_for_a_later_run(self):
        # The runner clears the channel before the step
        # runs, so a count an earlier run left standing in
        # the run folder cannot carry a later run whose
        # step reports nothing.
        steps = self.steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5
        )
        self.assertEqual(code, 0, record)
        self.write("discover.py", "print('the suite holds')\n")
        steps = [
            [sys.executable, "discover.py"],
            [sys.executable, "check_stub.py"],
        ]
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5,
            allow_dirty=True,
        )
        self.assertEqual(code, 1, record)
        self.assertEqual(record["failing_step"], "discover")
        self.assertIn("reported no measured count",
                      record["failure_reason"])

    def test_a_late_line_below_the_block_count_leaves_the_verdict(self):
        # The control beside the plant, restated on a
        # real suite. A bare count line printed by a test
        # of a suite whose census from the sources meets
        # the floor changes nothing, because the reading
        # never reaches it.
        self.write_suite(4, bare_line_plant(2))
        self.write("check_stub.py", OK_STUB)
        steps = self.discover_steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5
        )
        self.assertEqual(code, 0, record)
        self.assertEqual(record["verdict"], "pass")
        meta = json.loads(
            (self.logs / record["tree"] / "01-discover.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(meta["count"], 5)
        self.assertEqual(meta["reported_count"], 5)


class TestRunnerUnreadableClosingIdentity(RunnerFixture):
    """Round 24 delta, standards confirmation Note 2.

    The unreadable closing identity arm of the end of run
    re-key shipped with no plant in the suite, the standards
    seat proving the behaviour by a probe whose step moved
    the git directory away mid run. This class plants that
    shape in the suite. The plant fails when the arm is
    struck, since a reading that treated an unreadable
    state as standing still would let the run continue over
    a root whose tree can no longer be named.
    """

    def test_a_step_that_moves_the_git_directory_away_is_refused(self):
        self.write(
            "mover.py",
            "import os\n"
            "os.rename('.git', '.git-away')\n")
        self.write("check_stub.py", OK_STUB)
        steps = [
            [sys.executable, "mover.py"],
            [sys.executable, "check_stub.py"],
        ]
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5
        )
        self.assertEqual(code, 1, record)
        self.assertIn("the tree moved during the run",
                      record["verdict"])
        self.assertIsNone(record["closing_tree"])
        self.assertIsNone(record["closing_head"])
        self.assertIsNone(record["closing_dirty"])
        self.assertEqual(record["movement_after_step"], "mover")
        self.assertEqual(record["steps_completed"], ["mover"])
        self.assertEqual(record["steps_not_run"], ["check_stub"])


class TestRunnerStaticCensus(RunnerFixture):
    """Round 34 delta 4. The floor binds the population itself.

    The delta 2 confirmation priced the composition
    that defeats a measured line and a channel report
    together, and the delta 3 pass answered it by
    taking the census from the sources in the runner
    its own process, with the channel report standing
    as a cross check on the count alone. The delta 3
    confirmation then priced the substitution at an
    equal count, a suite whose load tests hook or
    whose module level mutation swaps the population
    the run executes for another of the same size, so
    the census and the report agree in count while no
    stated test runs. The floor now holds the report
    against the census in identity as well as in
    count. The reading derives the identity multiset
    of the sources beside the census, the wrapper
    reports the identities of the cases in the suite
    it executed beside its count, and the arm refuses
    first on the count disagreement and then on the
    identity disagreement where the counts agree. The
    plants below are the shapes of the confirmations
    in shipped form, with the truncated run, the
    killed step, the combined writer, the suites whose
    populations their sources do not state, and the
    two substitution spellings the delta 3
    confirmation charged.

    Round 34 delta 5 then bound provenance beside
    identity. The wrapper holds every case of the
    suite it loaded against the classes as they
    loaded from the sources, and a case whose class
    is not the class object the loading produced
    under its name, or whose method is not the
    function that class held as it loaded, leaves no
    report standing, so the run refuses on the report
    that never stood. The delta 4 plants on the
    substitution and on the hook that adds cases
    stand repriced to that arm here, the mutation
    spelling stands on the identity arm as it stood,
    its mutation standing in the module its own
    loading, and the new plants price the name worn
    by another class in both its spellings, the
    method a hook replaces on its class, the hook
    that returns the stated cases whole, the body
    swap the sources themselves write, and the
    genuine suite whose names the ASCII family of
    the delta 4 report form refused.

    Round 34 delta 6 then keyed the record the
    holding trusts on the bindings themselves. The
    delta 5 confirmation priced the nested claimant,
    a class nested inside a plain class that a module
    level assignment dresses in the stated class its
    qualified name, claiming the stated name in a
    record keyed on the qualified name a class
    carries on itself, the first claimant holding the
    name. The record now takes every key from the
    path of binding names that reaches a class from
    the namespace of its module, so the nested class
    stands recorded under its own nested path and its
    cases find the stated class object under the
    stated name and stand unstated on it. The new
    plants price the nested claimant in the spelling
    the confirmation drove and in the spelling that
    makes the assignment inside the hook itself, and
    the class name the module body rebinds, which
    passes whole on the ground the body swap passes
    on, the object the loading leaves bound under a
    name being the statement of the sources under
    that name, read whole.
    """

    def discover_meta(self, record):
        return json.loads(
            (self.logs / record["tree"] / "01-discover.json")
            .read_text(encoding="utf-8")
        )

    def discover_log(self, record):
        return (
            self.logs / record["tree"] / "01-discover.log"
        ).read_text(encoding="utf-8")

    def test_the_suite_that_ends_the_process_refuses_on_its_report(self):
        # Minor 1 at the floor figure, repriced in the
        # delta 4 form. The plant writes the floor
        # figure into the channel and ends the process,
        # so the step exits clean on bytes the suite
        # wrote whole. Those bytes are a count standing
        # alone, and a count standing alone for a count
        # above zero is no report at all under the whole
        # form, so the run refuses on the report that
        # never stood in the form the reading takes, and
        # the census of three taken from the sources
        # stands in the meta with no report beside it.
        self.write_suite(2, exit_zero_plant(5))
        self.write("check_stub.py", OK_STUB)
        steps = self.discover_steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5
        )
        self.assertEqual(code, 1, record)
        self.assertEqual(record["failing_step"], "discover")
        self.assertIn("reported no measured count",
                      record["failure_reason"])
        meta = self.discover_meta(record)
        self.assertEqual(meta["count"], 3)
        self.assertIsNone(meta["reported_count"])
        self.assertIsNone(meta["reported_identities"])

    def test_the_suite_that_ends_the_process_above_the_floor(self):
        # Minor 1 above the floor figure, repriced the
        # same way. The size of the forged bytes buys
        # nothing, because a bare count is no report at
        # any size.
        self.write_suite(2, exit_zero_plant(9999))
        self.write("check_stub.py", OK_STUB)
        steps = self.discover_steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5
        )
        self.assertEqual(code, 1, record)
        self.assertEqual(record["failing_step"], "discover")
        self.assertIn("reported no measured count",
                      record["failure_reason"])
        meta = self.discover_meta(record)
        self.assertEqual(meta["count"], 3)
        self.assertIsNone(meta["reported_count"])
        self.assertIsNone(meta["reported_identities"])

    def test_the_detached_writer_cannot_carry_the_run(self):
        # Minor 2. The writer the suite leaves behind
        # rewrites the channel across the whole post
        # step span. Whatever of its work stands at the
        # reading, the run cannot pass, because the
        # census of three taken from the sources fails
        # the floor in its own words where the genuine
        # report stands, and refuses on the disagreement
        # where the forged one does. The priced claim is
        # the verdict and the census in the meta, and
        # both hold on either arm.
        self.write_suite(2, detached_writer_plant(5))
        self.write("check_stub.py", OK_STUB)
        steps = self.discover_steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5
        )
        self.assertEqual(code, 1, record)
        self.assertEqual(record["failing_step"], "discover")
        meta = self.discover_meta(record)
        self.assertEqual(meta["count"], 3)

    def test_a_truncated_run_reports_no_count(self):
        # The honest disagreement family in its plain
        # form. The suite holds the floor count whole,
        # and its last test ends the process, so the run
        # the step made never reports. The census taken
        # from the sources stands at the floor and the
        # run still refuses, on the report that never
        # stood.
        self.write_suite(4, TRUNCATE_PLANT)
        self.write("check_stub.py", OK_STUB)
        steps = self.discover_steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5
        )
        self.assertEqual(code, 1, record)
        self.assertEqual(record["failing_step"], "discover")
        self.assertIn("reported no measured count",
                      record["failure_reason"])
        meta = self.discover_meta(record)
        self.assertEqual(meta["count"], 5)
        self.assertIsNone(meta["reported_count"])

    def test_a_killed_step_keeps_no_planted_count_in_its_meta(self):
        # The confirmation its first Note. The suite
        # plants the floor figure in its channel and
        # then dies by signal. The run fails at the step
        # on its own exit, no floor reason stands in the
        # record, and the meta carries the census of
        # three taken from the sources with no report
        # beside it, the planted figure standing nowhere
        # in the record of the step.
        self.write_suite(1, killed_step_plants(5))
        self.write("check_stub.py", OK_STUB)
        steps = self.discover_steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5
        )
        self.assertEqual(code, 1, record)
        self.assertEqual(record["failing_step"], "discover")
        self.assertNotIn("failure_reason", record)
        meta = self.discover_meta(record)
        self.assertNotEqual(meta["exit_code"], 0)
        self.assertEqual(meta["count"], 3)
        self.assertIsNone(meta["reported_count"])

    def test_a_module_printing_the_measurement_form_claims_nothing(self):
        # The measuring line of the delta 2 form stands
        # nowhere in this design, because no measuring
        # run exists for a printed line to stand in for.
        # A suite module that prints a line of that form
        # at load prints text, and the census is taken
        # from the sources of the suite, so the run
        # fails at the census of three under the floor
        # with the genuine report of three standing
        # against it in agreement.
        self.write("test_generated.py", LOAD_PRINT_SUITE)
        self.write("check_stub.py", OK_STUB)
        steps = self.discover_steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5
        )
        self.assertEqual(code, 1, record)
        self.assertEqual(record["failing_step"], "discover")
        self.assertIn("counted 3 tests",
                      record["failure_reason"])
        meta = self.discover_meta(record)
        self.assertEqual(meta["count"], 3)
        self.assertEqual(meta["reported_count"], 3)

    def test_the_combined_leftover_writer_refuses_on_the_disagreement(self):
        # The delta 2 confirmation its Minor, whole,
        # repriced in the delta 4 form. The suite its
        # module, finding the channel name standing in
        # its environment, leaves a detached writer on
        # the channel and ends the host at load, so no
        # test body runs and the forged figure of five
        # stands alone in the channel at the reading.
        # That figure is a count standing alone, no
        # report at all under the whole form, so the run
        # refuses on the report that never stood in the
        # form the reading takes. The census is taken
        # from the sources, where the suite holds three
        # tests, and it stands in the meta with no report
        # beside it. The writer inherits the step its
        # output streams, so the step its reading waits
        # for the writer to finish, and the verdict is
        # structural and not raced.
        self.write("test_generated.py", COMBINED_SUITE)
        self.write("check_stub.py", OK_STUB)
        steps = self.discover_steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5
        )
        self.assertEqual(code, 1, record)
        self.assertEqual(record["failing_step"], "discover")
        self.assertIn("reported no measured count",
                      record["failure_reason"])
        meta = self.discover_meta(record)
        self.assertEqual(meta["count"], 3)
        self.assertIsNone(meta["reported_count"])
        self.assertIsNone(meta["reported_identities"])

    def test_a_suite_built_by_execution_reports_against_its_sources(self):
        # The boundary of the certified family, priced.
        # The suite builds two of its five tests by
        # execution at load, so its sources state three
        # and its run reports five. The census is the
        # three the sources state, and the run refuses
        # on the disagreement, which is the face the
        # runner states for a population that is not
        # statically enumerable from its sources.
        self.write("test_generated.py", GENERATED_SUITE)
        self.write("check_stub.py", OK_STUB)
        steps = self.discover_steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5
        )
        self.assertEqual(code, 1, record)
        self.assertEqual(record["failing_step"], "discover")
        self.assertIn("reported 5 tests",
                      record["failure_reason"])
        self.assertIn("census of 3 taken from the sources",
                      record["failure_reason"])

    def test_a_suite_defined_by_its_environment_refuses_by_name(self):
        # The conditional shape. The class defines five
        # test names across the arms of a condition on
        # the channel name, so the static reading counts
        # the five names standing in the sources. The
        # step its environment carries the name, so the
        # run defines three and reports three, and the
        # run refuses on the disagreement by name.
        self.write("test_generated.py", CONDITIONAL_SUITE)
        self.write("check_stub.py", OK_STUB)
        steps = self.discover_steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=5
        )
        self.assertEqual(code, 1, record)
        self.assertEqual(record["failing_step"], "discover")
        self.assertIn("reported 3 tests",
                      record["failure_reason"])
        self.assertIn("census of 5 taken from the sources",
                      record["failure_reason"])

    def test_the_load_tests_substitution_leaves_no_report(self):
        # The delta 3 confirmation its Minor, first
        # spelling, repriced in the delta 5 form. The
        # module states three failing tests and its
        # load tests hook returns three synthetic
        # trivial cases of a class the hook itself
        # defines, so the step runs green while none of
        # the stated tests executes. At delta 4 the run
        # refused on the identity disagreement, the
        # synthetic cases standing in the report under
        # their own class. The synthetic cases are not
        # cases of the class the sources state, so they
        # stand unstated to the wrapper its holding, no
        # report of the run stands, and the run refuses
        # on the report that never stood, the refusal
        # the wrapper names in the step its own log.
        self.write("test_generated.py", SUBSTITUTE_SUITE)
        self.write("check_stub.py", OK_STUB)
        steps = self.discover_steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=3
        )
        self.assertEqual(code, 1, record)
        self.assertEqual(record["failing_step"], "discover")
        self.assertIn("reported no measured count",
                      record["failure_reason"])
        meta = self.discover_meta(record)
        self.assertEqual(meta["count"], 3)
        self.assertIsNone(meta["reported_count"])
        self.assertIsNone(meta["reported_identities"])
        log = self.discover_log(record)
        self.assertIn("is not a stated case", log)
        self.assertIn("TestSynthetic", log)

    def test_the_mutation_spelling_refuses_on_the_identities(self):
        # The delta 3 confirmation its Minor, second
        # spelling. Module level code deletes the three
        # stated failing methods and assigns three
        # trivial methods under new names in their
        # place, so the run executes a population of
        # the same size under other identities and the
        # step runs green. The counts stand together at
        # three, and the run refuses on the identity
        # disagreement by name.
        self.write("test_generated.py", MUTATION_SUITE)
        self.write("check_stub.py", OK_STUB)
        steps = self.discover_steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=3
        )
        self.assertEqual(code, 1, record)
        self.assertEqual(record["failing_step"], "discover")
        self.assertIn("identities that disagree",
                      record["failure_reason"])
        self.assertIn("census of 3 taken from the sources",
                      record["failure_reason"])
        meta = self.discover_meta(record)
        self.assertEqual(meta["count"], 3)
        self.assertEqual(meta["reported_count"], 3)
        self.assertEqual(
            meta["reported_identities"],
            [
                "test_generated.TestScratchSuite.test_p",
                "test_generated.TestScratchSuite.test_q",
                "test_generated.TestScratchSuite.test_r",
            ],
        )

    def test_a_hook_adding_cases_leaves_no_report(self):
        # The stated cases plus synthetic cases,
        # repriced in the delta 5 form. At delta 4 the
        # hook its extra case stood in the report at
        # four against a census of three, and the count
        # arm refused in front of the identity arm. The
        # extra case is a case of a class the hook
        # itself defines, so it stands unstated to the
        # holding, no report of the run stands, and the
        # run refuses on the report that never stood.
        # The claim that survives the repricing is the
        # refusal itself, since a report carrying the
        # provenanced cases alone would have certified
        # the stated three while the run executed four.
        self.write("test_generated.py", STATED_PLUS_SUITE)
        self.write("check_stub.py", OK_STUB)
        steps = self.discover_steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=3
        )
        self.assertEqual(code, 1, record)
        self.assertEqual(record["failing_step"], "discover")
        self.assertIn("reported no measured count",
                      record["failure_reason"])
        meta = self.discover_meta(record)
        self.assertEqual(meta["count"], 3)
        self.assertIsNone(meta["reported_count"])
        self.assertIsNone(meta["reported_identities"])
        log = self.discover_log(record)
        self.assertIn("is not a stated case", log)
        self.assertIn("TestExtra", log)

    def test_the_spoofed_name_substitution_leaves_no_report(self):
        # The delta 4 confirmation its Minor, first
        # spelling. The hook builds a class of its own,
        # gives it the stated method names as trivial
        # bodies, and sets its module name and its
        # qualified name to the stated names, so its
        # cases name themselves with the identities of
        # the sources string for string and the run at
        # delta 4 passed whole at the floor. The class
        # is not the class the sources state under that
        # name, so its cases stand unstated to the
        # holding, no report of the run stands, and the
        # run refuses on the report that never stood,
        # the wrapper naming the ground in the step log.
        self.write("test_generated.py", SPOOF_SUITE)
        self.write("check_stub.py", OK_STUB)
        steps = self.discover_steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=3
        )
        self.assertEqual(code, 1, record)
        self.assertEqual(record["failing_step"], "discover")
        self.assertIn("reported no measured count",
                      record["failure_reason"])
        meta = self.discover_meta(record)
        self.assertEqual(meta["count"], 3)
        self.assertIsNone(meta["reported_count"])
        self.assertIsNone(meta["reported_identities"])
        log = self.discover_log(record)
        self.assertIn("is not a stated case", log)
        self.assertIn(
            "not the class the sources state", log)

    def test_the_spoofed_subclass_leaves_no_report(self):
        # The delta 4 confirmation its Minor, second
        # spelling. The hook builds a subclass of the
        # stated class that overrides every stated
        # method with a trivial body and sets the same
        # two attributes to the stated values, and the
        # run at delta 4 passed whole the same way. The
        # subclass is not the class the sources state
        # under that name either, so its cases stand
        # unstated and no report of the run stands.
        self.write("test_generated.py", SPOOF_SUBCLASS_SUITE)
        self.write("check_stub.py", OK_STUB)
        steps = self.discover_steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=3
        )
        self.assertEqual(code, 1, record)
        self.assertEqual(record["failing_step"], "discover")
        self.assertIn("reported no measured count",
                      record["failure_reason"])
        meta = self.discover_meta(record)
        self.assertEqual(meta["count"], 3)
        self.assertIsNone(meta["reported_count"])
        self.assertIsNone(meta["reported_identities"])
        log = self.discover_log(record)
        self.assertIn("is not a stated case", log)
        self.assertIn(
            "not the class the sources state", log)

    def test_a_hook_replacing_a_method_leaves_no_report(self):
        # A hook that returns instances of the stated
        # class with one method replaced on the class
        # after the loading. The stated test it
        # replaces stands failing and the replacement
        # is trivial, so at delta 4 the run passed
        # whole, the population and its identities
        # standing together. The replacement is not
        # the function the loading left in the class,
        # so the case carrying it stands unstated on
        # its provenance and no report of the run
        # stands, not on any judgement of its body.
        self.write("test_generated.py", METHOD_REPLACED_SUITE)
        self.write("check_stub.py", OK_STUB)
        steps = self.discover_steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=3
        )
        self.assertEqual(code, 1, record)
        self.assertEqual(record["failing_step"], "discover")
        self.assertIn("reported no measured count",
                      record["failure_reason"])
        meta = self.discover_meta(record)
        self.assertEqual(meta["count"], 3)
        self.assertIsNone(meta["reported_count"])
        self.assertIsNone(meta["reported_identities"])
        log = self.discover_log(record)
        self.assertIn("is not a stated case", log)
        self.assertIn(
            "is not the function the class held", log)

    def test_a_hook_returning_the_stated_cases_passes(self):
        # A hook that returns the stated cases whole
        # shapes nothing. The cases are cases of the
        # class the sources state, carrying the
        # functions the loading left, so they stand
        # stated to the holding, the report stands, and
        # the run passes whole at its floor with its
        # census and its report and its identities
        # together.
        self.write("test_generated.py", STATED_WHOLE_SUITE)
        self.write("check_stub.py", OK_STUB)
        steps = self.discover_steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=3
        )
        self.assertEqual(code, 0, record)
        self.assertEqual(record["verdict"], "pass")
        meta = self.discover_meta(record)
        self.assertEqual(meta["count"], 3)
        self.assertEqual(meta["reported_count"], 3)
        self.assertEqual(
            meta["reported_identities"],
            [
                "test_generated.TestScratchSuite.test_a",
                "test_generated.TestScratchSuite.test_b",
                "test_generated.TestScratchSuite.test_c",
            ],
        )

    def test_the_body_swap_in_the_sources_passes_as_stated(self):
        # The delta 4 confirmation its first Note,
        # pinned at the boundary the face now states.
        # Module level code rebinds a stated failing
        # method to a trivial body under its stated
        # name, and the run passes whole. The rebinding
        # stands in the module its own loading, so the
        # function as loaded is the rebound function
        # and the case stands stated, and the floor
        # certifies the population and its provenance
        # and no body a stated name carries, the
        # honesty of the body standing with the step
        # its own exit and with the vacuity guard. The
        # pass is the stated behaviour of the boundary,
        # and this test pins it so the boundary cannot
        # move in silence.
        self.write("test_generated.py", BODY_SWAP_SUITE)
        self.write("check_stub.py", OK_STUB)
        steps = self.discover_steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=3
        )
        self.assertEqual(code, 0, record)
        self.assertEqual(record["verdict"], "pass")
        meta = self.discover_meta(record)
        self.assertEqual(meta["count"], 3)
        self.assertEqual(meta["reported_count"], 3)
        self.assertEqual(
            meta["reported_identities"],
            [
                "test_generated.TestScratchSuite.test_a",
                "test_generated.TestScratchSuite.test_b",
                "test_generated.TestScratchSuite.test_c",
            ],
        )

    def test_a_genuine_suite_with_unicode_names_passes(self):
        # The delta 4 confirmation its second Note,
        # repaired. A genuine suite whose method names
        # carry a letter outside the ASCII family
        # refused at delta 4 on the report that never
        # stood, its census and its loader reading in
        # agreement, because the report reading took
        # only the ASCII segment family while its
        # sentence claimed the family the loader its
        # own names take. The reading now takes the
        # identifiers of the language, so the report of
        # the genuine run stands and the run passes
        # whole at its floor.
        self.write("test_generated.py", UNICODE_SUITE)
        self.write("check_stub.py", OK_STUB)
        steps = self.discover_steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=3
        )
        self.assertEqual(code, 0, record)
        self.assertEqual(record["verdict"], "pass")
        meta = self.discover_meta(record)
        self.assertEqual(meta["count"], 3)
        self.assertEqual(meta["reported_count"], 3)
        self.assertEqual(
            meta["reported_identities"],
            [
                "test_generated.TestScratchSuite.test_a",
                "test_generated.TestScratchSuite.test_b",
                "test_generated.TestScratchSuite.test_café",
            ],
        )

    def test_the_nested_claimant_leaves_no_report(self):
        # The delta 5 confirmation its Minor. A class
        # nested inside a plain class carries the
        # stated method names as trivial bodies, and a
        # module level assignment gives it the stated
        # class its qualified name before the loading
        # ends, and the hook returns its cases. At
        # delta 5 the record was keyed on the qualified
        # name a class carries, and the walk took the
        # namespace from its end, so the nested class
        # claimed the stated name in the record ahead
        # of the stated class and the run passed whole.
        # The record now takes its keys from the
        # bindings, so the nested class stands recorded
        # under its own nested path, its cases find the
        # stated class object under the stated name,
        # and they stand unstated on the object, so no
        # report of the run stands.
        self.write("test_generated.py", NESTED_CLAIMANT_SUITE)
        self.write("check_stub.py", OK_STUB)
        steps = self.discover_steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=3
        )
        self.assertEqual(code, 1, record)
        self.assertEqual(record["failing_step"], "discover")
        self.assertIn("reported no measured count",
                      record["failure_reason"])
        meta = self.discover_meta(record)
        self.assertEqual(meta["count"], 3)
        self.assertIsNone(meta["reported_count"])
        self.assertIsNone(meta["reported_identities"])
        log = self.discover_log(record)
        self.assertIn("is not a stated case", log)
        self.assertIn(
            "not the class the sources state", log)

    def test_the_nested_claimant_in_the_hook_leaves_no_report(self):
        # The late claim against the record the
        # loading leaves. The assignment that dresses
        # the nested class in the stated name stands
        # inside the hook itself, after the loading of
        # the module has ended and the record stands
        # taken. The record was never keyed on the
        # attribute the assignment writes, so the claim
        # lands no differently, and the run refuses on
        # the report that never stood on the same
        # ground.
        self.write(
            "test_generated.py", NESTED_CLAIMANT_HOOK_SUITE)
        self.write("check_stub.py", OK_STUB)
        steps = self.discover_steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=3
        )
        self.assertEqual(code, 1, record)
        self.assertEqual(record["failing_step"], "discover")
        self.assertIn("reported no measured count",
                      record["failure_reason"])
        meta = self.discover_meta(record)
        self.assertEqual(meta["count"], 3)
        self.assertIsNone(meta["reported_count"])
        self.assertIsNone(meta["reported_identities"])
        log = self.discover_log(record)
        self.assertIn("is not a stated case", log)
        self.assertIn(
            "not the class the sources state", log)

    def test_the_class_name_rebinding_in_the_sources_passes(self):
        # The boundary the face states for class
        # names, pinned beside the body swap. The
        # module states its tests as failing tests and
        # then rebinds the stated name in its own
        # namespace to a second class carrying the same
        # method names as passing bodies, the rebinding
        # standing in the module its own loading. The
        # object the loading leaves bound under the
        # name is the replacement, the census reads the
        # name to the same class, and the run passes
        # whole on the population the sources state
        # under that name, read whole, each identity
        # standing twice for the two names that resolve
        # to the one class. The pass is the stated
        # behaviour of the boundary, and this test pins
        # it so the boundary cannot move in silence.
        self.write("test_generated.py", CLASS_REBIND_SUITE)
        self.write("check_stub.py", OK_STUB)
        steps = self.discover_steps()
        self.commit()
        code, record = runner.run_gates(
            self.root, log_dir=self.logs, steps=steps, floor=6
        )
        self.assertEqual(code, 0, record)
        self.assertEqual(record["verdict"], "pass")
        meta = self.discover_meta(record)
        self.assertEqual(meta["count"], 6)
        self.assertEqual(meta["reported_count"], 6)
        self.assertEqual(
            meta["reported_identities"],
            [
                "test_generated.TestReplacement.test_a",
                "test_generated.TestReplacement.test_a",
                "test_generated.TestReplacement.test_b",
                "test_generated.TestReplacement.test_b",
                "test_generated.TestReplacement.test_c",
                "test_generated.TestReplacement.test_c",
            ],
        )


LOADER_PROBE = (
    "import sys, unittest\n"
    "suite = unittest.TestLoader().discover(sys.argv[1])\n"
    "print(suite.countTestCases())\n"
)

IDENTITY_PROBE = (
    "import sys, unittest\n"
    "suite = unittest.TestLoader().discover(sys.argv[1])\n"
    "def flat(node):\n"
    "    if isinstance(node, unittest.TestSuite):\n"
    "        for child in node:\n"
    "            yield from flat(child)\n"
    "    else:\n"
    "        yield node\n"
    "for case in flat(suite):\n"
    "    print(case.id())\n"
)

INHERIT_SUITE = (
    "import unittest\n"
    "\n"
    "\n"
    "class Mixin:\n"
    "    def test_mixin(self):\n"
    "        self.assertEqual(1, 1)\n"
    "\n"
    "\n"
    "class Fixture(unittest.TestCase):\n"
    "    def test_a(self):\n"
    "        self.assertEqual(1, 1)\n"
    "    def test_b(self):\n"
    "        self.assertEqual(1, 1)\n"
    "\n"
    "\n"
    "class TestChild(Mixin, Fixture):\n"
    "    def test_c(self):\n"
    "        self.assertEqual(1, 1)\n"
)

REEXPORT_ORIGIN = (
    "import unittest\n"
    "\n"
    "\n"
    "class TestOrigin(unittest.TestCase):\n"
    "    def test_a(self):\n"
    "        self.assertEqual(1, 1)\n"
    "    def test_b(self):\n"
    "        self.assertEqual(1, 1)\n"
)

ASSIGNED_SUITE = (
    "import unittest\n"
    "\n"
    "\n"
    "def _impl(self):\n"
    "    pass\n"
    "\n"
    "\n"
    "class TestAssigned(unittest.TestCase):\n"
    "    def test_a(self):\n"
    "        self.assertEqual(1, 1)\n"
    "    test_assigned = _impl\n"
)


class TestStaticCensusReading(unittest.TestCase):
    """Round 34 delta 4. The reading names what the loader loads.

    The census the floor reads is a static reading of
    the sources, and its claim to stand in for the
    loaded census rests on the two readings agreeing
    wherever a suite is statically enumerable. The
    shapes below stand counted both ways on scratch
    trees, by the shipped reading and by the loader
    itself in a child process, and the shipped suite
    stands counted by the shipped reading over the
    real tree against the pinned floor the suite
    itself holds. The delta 4 reading derives the
    identity multiset of the population beside the
    count, and the agreement below stands priced in
    identity as well as in count, over the scratch
    shapes and over the shipped suite whole.
    """

    def census_pair(self, files):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        for name, text in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        argv = [sys.executable, "scripts/discover.py", "-s", "."]
        static = runner.static_discover_census(root, argv)
        probe = subprocess.run(
            [sys.executable, "-c", LOADER_PROBE, str(root)],
            capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(probe.returncode, 0, probe.stderr)
        return static, int(probe.stdout.strip())

    def reading_pair(self, files):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        for name, text in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        argv = [sys.executable, "scripts/discover.py", "-s", "."]
        reading = runner.static_discover_reading(root, argv)
        probe = subprocess.run(
            [sys.executable, "-c", IDENTITY_PROBE, str(root)],
            capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(probe.returncode, 0, probe.stderr)
        loaded = sorted(
            line for line in probe.stdout.splitlines() if line
        )
        return reading, loaded

    def test_inheritance_and_mixins_count_as_the_loader_counts(self):
        static, loaded = self.census_pair(
            {"test_census_inherit.py": INHERIT_SUITE})
        self.assertEqual(loaded, 6)
        self.assertEqual(static, loaded)

    def test_a_reexported_class_counts_again_as_the_loader_counts(self):
        static, loaded = self.census_pair({
            "test_census_origin.py": REEXPORT_ORIGIN,
            "test_census_again.py": (
                "from test_census_origin import TestOrigin\n"),
        })
        self.assertEqual(loaded, 4)
        self.assertEqual(static, loaded)

    def test_package_folders_walk_and_loose_folders_do_not(self):
        one = (
            "import unittest\n"
            "\n"
            "\n"
            "class TestOne(unittest.TestCase):\n"
            "    def test_a(self):\n"
            "        self.assertEqual(1, 1)\n"
        )
        two = (
            "import unittest\n"
            "\n"
            "\n"
            "class TestTwo(unittest.TestCase):\n"
            "    def test_a(self):\n"
            "        self.assertEqual(1, 1)\n"
            "    def test_b(self):\n"
            "        self.assertEqual(1, 1)\n"
        )
        three = (
            "import unittest\n"
            "\n"
            "\n"
            "class TestThree(unittest.TestCase):\n"
            "    def test_a(self):\n"
            "        self.assertEqual(1, 1)\n"
            "    def test_b(self):\n"
            "        self.assertEqual(1, 1)\n"
            "    def test_c(self):\n"
            "        self.assertEqual(1, 1)\n"
        )
        static, loaded = self.census_pair({
            "test_census_top.py": one,
            "pkg/__init__.py": "",
            "pkg/test_census_deep.py": two,
            "loose/test_census_loose.py": three,
        })
        self.assertEqual(loaded, 3)
        self.assertEqual(static, loaded)

    def test_a_method_assigned_from_a_function_counts(self):
        static, loaded = self.census_pair(
            {"test_census_assigned.py": ASSIGNED_SUITE})
        self.assertEqual(loaded, 2)
        self.assertEqual(static, loaded)

    def test_the_shipped_suite_reading_equals_the_pinned_floor(self):
        argv = [sys.executable, "scripts/discover.py", "-s", "tests"]
        self.assertEqual(
            runner.static_discover_census(ROOT, argv),
            runner.PINNED_TEST_FLOOR,
        )

    def test_the_inherited_identities_agree_with_the_loader(self):
        reading, loaded = self.reading_pair(
            {"test_census_inherit.py": INHERIT_SUITE})
        self.assertIsNotNone(reading)
        count, identities = reading
        self.assertEqual(count, 6)
        self.assertEqual(identities, loaded)

    def test_the_reexported_identities_agree_with_the_loader(self):
        reading, loaded = self.reading_pair({
            "test_census_origin.py": REEXPORT_ORIGIN,
            "test_census_again.py": (
                "from test_census_origin import TestOrigin\n"),
        })
        self.assertIsNotNone(reading)
        count, identities = reading
        self.assertEqual(count, 4)
        self.assertEqual(identities, loaded)
        self.assertEqual(
            identities.count("test_census_origin.TestOrigin.test_a"),
            2,
        )

    def test_the_assigned_method_identity_agrees_with_the_loader(self):
        reading, loaded = self.reading_pair(
            {"test_census_assigned.py": ASSIGNED_SUITE})
        self.assertIsNotNone(reading)
        count, identities = reading
        self.assertEqual(count, 2)
        self.assertEqual(identities, loaded)

    def test_the_shipped_suite_identities_agree_with_the_loader(self):
        argv = [sys.executable, "scripts/discover.py", "-s", "tests"]
        reading = runner.static_discover_reading(ROOT, argv)
        self.assertIsNotNone(reading)
        count, identities = reading
        self.assertEqual(count, runner.PINNED_TEST_FLOOR)
        probe = subprocess.run(
            [sys.executable, "-c", IDENTITY_PROBE,
             str(ROOT / "tests")],
            capture_output=True, text=True, timeout=300,
        )
        self.assertEqual(probe.returncode, 0, probe.stderr)
        loaded = sorted(
            line for line in probe.stdout.splitlines() if line
        )
        self.assertEqual(identities, loaded)

    def test_a_step_naming_no_suite_takes_no_census(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        foreign = [sys.executable, "check_stub.py"]
        self.assertIsNone(
            runner.static_discover_census(root, foreign))
        missing = [
            sys.executable, "scripts/discover.py", "-s", "nope"]
        self.assertIsNone(
            runner.static_discover_census(root, missing))


class TestReportedCountForm(unittest.TestCase):
    """Round 34 delta 4. The channel reading takes one whole form.

    The confirmation its second Note priced the delta
    2 reading accepting a family of forms around the
    digits, the padded spellings and the leading zero
    among them, and that reading took exactly the form
    the wrapper then wrote. The delta 4 report carries
    the population beside the count, so the reading
    now accepts exactly the whole form the wrapper
    writes, the digits in their plain spelling as the
    first line and after them as many identity lines
    as the count states, each a dotted name standing
    in sorted order, and the acceptance set stands
    priced here so it cannot widen in silence. A count
    standing alone for a count above zero is no report
    at all under the reading, which is the shape the
    standing forgery plants reprice to.

    Round 34 delta 5 widened the segment family of an
    identity line from the ASCII letters to the
    identifiers of the language, the family the loader
    its own names take, since the delta 4 confirmation
    priced a genuine suite whose names carry a letter
    outside the ASCII family refusing on the form
    alone while its census and its loader reading
    agreed, and the sentence of the reading claimed
    the wider family all along.
    """

    def read(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "count.txt"
            if text is not None:
                path.write_bytes(text)
            return runner.reported_report(path)

    def test_the_wrapper_its_own_form_reads(self):
        self.assertEqual(
            self.read(
                b"2\n"
                b"test_plant.TestPlant.test_a\n"
                b"test_plant.TestPlant.test_b\n"
            ),
            (2, ["test_plant.TestPlant.test_a",
                 "test_plant.TestPlant.test_b"]),
        )
        self.assertEqual(self.read(b"0\n"), (0, []))

    def test_padding_and_leading_zeroes_read_no_count(self):
        self.assertIsNone(self.read(b" 5\n"))
        self.assertIsNone(self.read(b"5 \n"))
        self.assertIsNone(self.read(b"05\n"))
        self.assertIsNone(self.read(b"5\n\n"))
        self.assertIsNone(self.read(b"5"))
        self.assertIsNone(self.read(b""))

    def test_other_shapes_read_no_count(self):
        self.assertIsNone(self.read(b"5\r\n"))
        self.assertIsNone(self.read(b"five\n"))
        self.assertIsNone(self.read(b"-5\n"))
        self.assertIsNone(self.read(b"+5\n"))
        self.assertIsNone(self.read(b"5.0\n"))
        self.assertIsNone(self.read(None))
        self.assertIsNone(runner.reported_report(None))

    def test_a_count_standing_alone_reads_no_report(self):
        self.assertIsNone(self.read(b"5\n"))
        self.assertIsNone(self.read(b"12345\n"))
        self.assertIsNone(self.read(
            b"3\n"
            b"test_plant.TestPlant.test_a\n"
            b"test_plant.TestPlant.test_b\n"
        ))
        self.assertIsNone(self.read(
            b"1\n"
            b"test_plant.TestPlant.test_a\n"
            b"test_plant.TestPlant.test_b\n"
        ))
        self.assertIsNone(self.read(
            b"2\n"
            b"test_plant.TestPlant.test_b\n"
            b"test_plant.TestPlant.test_a\n"
        ))
        self.assertIsNone(self.read(
            b"2\n"
            b"test_plant.TestPlant.test_a\n"
            b"test_plant.TestPlant.test_b"
        ))

    def test_identity_line_shapes_read_no_report(self):
        self.assertIsNone(self.read(
            b"1\ntest_plant.TestPlant.test a\n"))
        self.assertIsNone(self.read(
            b"2\n"
            b"test_plant.TestPlant.test_a\n"
            b"\n"
        ))
        self.assertIsNone(self.read(b"1\ntest_a\n"))
        self.assertIsNone(self.read(
            b"1\ntest_plant.TestPlant.test_a\r\n"))

    def test_the_identifier_family_reads(self):
        # The family the loader its own names take. A
        # name carrying a letter outside the ASCII
        # family is an identifier of the language and
        # reads, and the locals segment a class built
        # inside a function carries reads beside it.
        self.assertEqual(
            self.read(
                "1\n"
                "test_plant.TestPlant.test_café\n"
                .encode("utf-8")
            ),
            (1, ["test_plant.TestPlant.test_café"]),
        )
        self.assertEqual(
            self.read(
                b"1\n"
                b"test_plant.load_tests.<locals>"
                b".TestExtra.test_x\n"
            ),
            (1, [
                "test_plant.load_tests.<locals>"
                ".TestExtra.test_x"
            ]),
        )

    def test_the_segment_family_edges_read_no_report(self):
        # The widened family is still one family. A
        # segment no identifier takes, an empty
        # segment, bytes that do not decode as the
        # UTF-8 the wrapper writes, and a count spelled
        # in the digits of another script all read as
        # no report.
        self.assertIsNone(self.read(
            b"1\ntest_plant.TestPlant.test-a\n"))
        self.assertIsNone(self.read(
            b"1\ntest_plant.9plant.test_a\n"))
        self.assertIsNone(self.read(
            b"1\ntest_plant..test_a\n"))
        self.assertIsNone(self.read(
            b"1\ntest_plant.TestPlant.test_\xff\n"))
        self.assertIsNone(self.read(b"\xd9\xa5\n"))


class TestDiscoverArguments(unittest.TestCase):
    """Round 34 delta 2. The derivation reads the shipped spellings.

    The runner names the suite it measures from the
    step its own arguments, so the derivation is priced
    on the two forms the gate ships and on a form it
    does not, which must name no suite and so no
    measurement.
    """

    def test_the_wrapper_form(self):
        self.assertEqual(
            runner.discover_arguments(
                [sys.executable, "scripts/discover.py",
                 "-s", "tests"]
            ),
            ("tests", "test*.py", None),
        )
        self.assertEqual(
            runner.discover_arguments(
                [sys.executable, "scripts/discover.py",
                 "-s", "tests", "-t", ".", "-p", "test_*.py"]
            ),
            ("tests", "test_*.py", "."),
        )

    def test_the_unittest_form(self):
        self.assertEqual(
            runner.discover_arguments(
                [sys.executable, "-m", "unittest", "discover",
                 "-s", "tests", "-t", "."]
            ),
            ("tests", "test*.py", "."),
        )

    def test_a_foreign_form_names_no_suite(self):
        self.assertIsNone(
            runner.discover_arguments(
                [sys.executable, "foreign.py"]
            )
        )
        self.assertIsNone(
            runner.discover_arguments(
                [sys.executable, "-m", "unittest"]
            )
        )
