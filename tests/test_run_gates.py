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
