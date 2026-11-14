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

DISCOVER_STUB = (
    "import sys\n"
    "print('Ran %d tests in 0.1s')\n"
    "print('OK')\n"
)
OK_STUB = "print('stub step holds')\n"
FAIL_STUB = "import sys\nprint('stub step refuses')\nsys.exit(3)\n"


class RunnerFixture(unittest.TestCase):
    """A scratch git repository with stub gate steps."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "repo"
        self.root.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Gate Runner Test")
        self.logs = Path(self.tmp.name) / "logs"

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

    def steps(self, discover_count=5, failing=False):
        self.write("discover.py", DISCOVER_STUB % discover_count)
        self.write("check_stub.py", OK_STUB)
        steps = [
            [sys.executable, "discover.py"],
            [sys.executable, "check_stub.py"],
        ]
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
    """Round 15. The count parser takes the last count line."""

    def setUp(self):
        self.mod = load_runner()

    def test_the_last_count_is_the_count_taken(self):
        output = (
            "Ran 9999 tests in 0.001s\n"
            "noise between the claims\n"
            "Ran 2 tests in 0.002s\n"
        )
        self.assertEqual(
            self.mod.count_line(output), (2, "Ran 2 tests")
        )

    def test_a_single_count_still_reads(self):
        self.assertEqual(
            self.mod.count_line("Ran 7 tests in 1.0s\n"),
            (7, "Ran 7 tests"),
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

    def test_a_discover_step_printing_no_count_fails_by_name(self):
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
        self.assertIn("printed no count", record["failure_reason"])
        meta = json.loads(
            (self.logs / record["tree"] / "01-discover.json")
            .read_text(encoding="utf-8")
        )
        self.assertIsNone(meta["count"])

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
