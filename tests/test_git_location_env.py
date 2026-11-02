"""The git location variables burden on the test harness.

Round 44 Finding F3 and round 247 duty 3 of the 300 round
programme. The fixture helpers in the suite ran git with the
caller environment inherited, and an exported GIT_DIR defeats
git -C, so a suite launched with GIT_DIR and GIT_WORK_TREE
pointed at a bystander repository ran its fixture work in
that repository instead. Five burden tests passed while the
bystander head moved by three planted commits and its status
read clean afterwards, because the writes were commits and
not dirt. These tests rebuild that shape in a subprocess, so
the polluted environment is the real launch environment of
the burden run, and they read the bystander log before and
after as the sentinel.
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BURDEN = (
    "tests.test_dco_workflow.TestDcoWorkflow",
    "tests.test_gate_scripts.TestCheckEvals."
    "test_child_env_scrubs_config_and_driver_variables",
    "tests.test_review_chain",
    "tests.test_symlink_census",
    "tests.test_check_packet_verifier.TestRound27ShallowAndState."
    "test_a_genuine_packet_in_a_shallow_clone_names_shallow",
    "tests.test_submissions.TestCheckSubmissions."
    "test_the_pack_figures_match_the_measured_tree",
)


def git(repo, *args):
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in (
            "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
            "GIT_OBJECT_DIRECTORY",
            "GIT_ALTERNATE_OBJECT_DIRECTORIES",
            "GIT_COMMON_DIR", "GIT_NAMESPACE",
        )
    }
    result = subprocess.run(
        ["git", "-C", str(repo)] + list(args),
        capture_output=True, text=True, env=env,
    )
    if result.returncode != 0:
        raise AssertionError(
            "git %s failed: %s" % (" ".join(args), result.stderr))
    return result.stdout.strip()


class TestGitLocationBurden(unittest.TestCase):
    def make_victim(self, tmp):
        victim = Path(tmp) / "victim"
        victim.mkdir()
        git(victim, "init", "-b", "main")
        git(victim, "config", "user.email", "victim@example.invalid")
        git(victim, "config", "user.name", "Victim")
        git(victim, "config", "commit.gpgsign", "false")
        (victim / "a.py").write_text("x = 1\n")
        git(victim, "add", "-A")
        git(victim, "commit", "-m", "base")
        return victim

    def test_the_burden_tests_leave_a_bystander_head_unmoved(self):
        with tempfile.TemporaryDirectory() as tmp:
            victim = self.make_victim(tmp)
            before = git(victim, "rev-parse", "HEAD")
            env = dict(os.environ)
            env["GIT_DIR"] = str(victim / ".git")
            env["GIT_WORK_TREE"] = str(victim)
            env["GIT_INDEX_FILE"] = str(victim / ".git" / "index")
            run = subprocess.run(
                [sys.executable, "-m", "unittest"] + list(BURDEN),
                cwd=str(ROOT), capture_output=True, text=True,
                env=env, timeout=600,
            )
            self.assertEqual(
                run.returncode, 0, run.stderr[-2000:] + run.stdout)
            self.assertIn("OK", run.stderr)
            self.assertEqual(git(victim, "rev-parse", "HEAD"), before)
            self.assertEqual(git(victim, "log", "--format=%s"), "base")
            self.assertEqual(git(victim, "status", "--porcelain"), "")


if __name__ == "__main__":
    unittest.main()
