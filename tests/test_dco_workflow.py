import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SIGN_OFF = (
    "Signed-off-by: David Engelmann "
    "<81196676+david-engelmann@users.noreply.github.com>"
)


# The git location variables are scrubbed from the environment
# every fixture command runs under. An exported GIT_DIR defeats
# git -C, so a suite launched with the variables set would run
# its fixture work in the repository they name instead of in
# the fixture, writing real commits there under passing tests.
GIT_LOCATION_VARS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_NAMESPACE",
)


def scrubbed_git_env():
    """The caller environment with the git location names removed."""
    return {
        key: value
        for key, value in os.environ.items()
        if key not in GIT_LOCATION_VARS
    }


def git(repo, *args):
    result = subprocess.run(
        ["git", "-C", str(repo)] + list(args),
        env=scrubbed_git_env(),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(
            "git %s failed: %s" % (args, result.stderr)
        )
    return result.stdout.strip()


class RetryingTemporaryDirectory(tempfile.TemporaryDirectory):
    # A fixture repository can gain a file while its temporary
    # directory is being removed. CI job 120492623700 on Python
    # 3.10 failed in teardown with OSError Errno 39 Directory not
    # empty on the pack folder inside a fixture repository after
    # every assertion in the test had passed, and a rerun passed.
    # The cleanup shipped with Python 3.12 tolerates that race
    # and the one shipped with Python 3.10 does not. Removal here
    # retries a bounded number of times with a short pause and
    # then raises, so a tree that truly cannot be removed still
    # fails loudly instead of passing in silence.

    cleanup_attempts = 5
    cleanup_delay_seconds = 0.1

    def cleanup(self):
        last_error = None
        for attempt in range(self.cleanup_attempts):
            try:
                shutil.rmtree(self.name)
            except FileNotFoundError as error:
                if not os.path.exists(self.name):
                    last_error = None
                    break
                last_error = error
            except OSError as error:
                last_error = error
            else:
                last_error = None
                break
            if attempt + 1 < self.cleanup_attempts:
                time.sleep(self.cleanup_delay_seconds)
        if last_error is not None:
            raise last_error
        self._finalizer.detach()



class TestDcoWorkflow(unittest.TestCase):
    """The DCO job must read the trailer block, not the whole message.

    The check line is taken from the workflow itself and run against
    real commits, so reverting the workflow to a whole message grep
    makes the buried trailer case pass and this test fail.
    """

    def setUp(self):
        self.tmp = RetryingTemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.email", "test@example.com")
        git(self.repo, "config", "user.name", "Test User")
        git(self.repo, "config", "commit.gpgsign", "false")
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        self.pipeline = None
        for line in workflow.splitlines():
            stripped = line.strip()
            if (
                stripped.startswith("if ")
                and "git log -1" in stripped
                and "Signed-off-by" in stripped
            ):
                self.assertTrue(stripped.startswith("if ! "))
                self.assertTrue(stripped.endswith("; then"))
                self.pipeline = stripped[len("if ! "):-len("; then")]
        self.assertIsNotNone(self.pipeline)

    def tearDown(self):
        self.tmp.cleanup()

    def commit_message(self, name, message):
        msg = Path(self.tmp.name) / name
        msg.write_text(message, encoding="utf-8")
        git(self.repo, "commit", "--allow-empty", "-F", str(msg))
        return git(self.repo, "rev-parse", "HEAD")

    def check(self, sha):
        env = dict(os.environ)
        for var in GIT_LOCATION_VARS:
            env.pop(var, None)
        env["sha"] = sha
        result = subprocess.run(
            ["bash", "-c", self.pipeline],
            cwd=str(self.repo), env=env,
            capture_output=True, text=True,
        )
        return result.returncode

    def test_a_proper_trailer_passes(self):
        sha = self.commit_message(
            "good.txt", "A change\n\n%s\n" % SIGN_OFF
        )
        self.assertEqual(self.check(sha), 0)

    def test_a_buried_sign_off_is_not_a_trailer(self):
        sha = self.commit_message(
            "buried.txt",
            "A change\n\n%s\n\nA closing paragraph follows it.\n"
            % SIGN_OFF,
        )
        self.assertNotEqual(self.check(sha), 0)

    def test_a_wrong_sign_off_identity_fails(self):
        sha = self.commit_message(
            "wrong.txt",
            "A change\n\nSigned-off-by: Someone Else "
            "<someone@example.invalid>\n",
        )
        self.assertNotEqual(self.check(sha), 0)

    def test_the_workflow_exempts_dependabot_by_actor(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "if: github.event_name == 'pull_request' && "
            "github.actor != 'dependabot[bot]'",
            workflow,
        )

    def test_the_guidance_chronicle_records_the_catch_up(self):
        # The chronicle in AGENTS.md ended at the visual fix
        # pass while sixty landings in its own range stood
        # unrecorded. The catch up paragraphs name them in
        # landing order and close with this landing itself, so
        # dropping the catch up, or its closing self record,
        # fails here.
        agents = " ".join(
            (ROOT / "AGENTS.md").read_text(encoding="utf-8").split()
        )
        self.assertIn(
            "The chronicle catch up on 2026-10-30 then recorded "
            "the sixty landings the paragraphs above never named",
            agents,
        )
        self.assertIn(
            "counted the wordmark pair in its pin and qualified "
            "the fragment claim",
            agents,
        )
        self.assertIn(
            "This claims burn down landing then closed the set",
            agents,
        )

    def test_the_sign_off_position_stands_where_a_contributor_looks(self):
        # The DCO job demands the one exact owner trailer, which
        # no outsider can honestly produce, so the position has
        # to stand in the open before the first commit is made
        # and not only in the failure message after it. Dropping
        # the contributing note, or its statement that outside
        # pull requests are not taken, or the template line that
        # points at it, fails here.
        note_path = ROOT / "CONTRIBUTING.md"
        self.assertTrue(note_path.is_file())
        note = " ".join(note_path.read_text(encoding="utf-8").split())
        self.assertIn("Outside pull requests are not taken.", note)
        # The workflow skips the whole job when the actor is
        # dependabot[bot] and iterates non-merge commits only,
        # so the note must scope its every commit sentence to
        # the commits the job actually reaches. The unscoped
        # sentence coming back, or either carve out dropping,
        # fails here.
        self.assertIn(
            "Every non-merge commit a person puts on a pull "
            "request must carry one exact",
            note,
        )
        self.assertIn("dependabot[bot]", note)
        self.assertIn(
            "merge commits stand outside the list of commits "
            "it checks",
            note,
        )
        self.assertNotIn(
            "Every commit on a pull request must carry", note
        )
        self.assertIn(
            "nobody else can honestly sign his name to theirs", note
        )
        self.assertIn("the bug report template", note)
        template = " ".join(
            (ROOT / ".github" / "pull_request_template.md")
            .read_text(encoding="utf-8")
            .split()
        )
        self.assertIn("CONTRIBUTING.md states", template)
        self.assertIn("outside pull requests are not taken", template)
