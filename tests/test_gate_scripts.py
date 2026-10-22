import importlib.util
import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    path = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location("gate_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(repo, *args):
    result = subprocess.run(
        ["git", "-C", str(repo)] + list(args),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError("git %s failed: %s" % (" ".join(args), result.stderr))
    return result.stdout.strip()


EM_DASH = "\u2014"


class TestCheckCopy(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_copy")

    def write_tmp(self, tmp, name, text):
        path = Path(tmp) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def run_main_on(self, files):
        original = self.mod.PROSE_FILES
        self.mod.PROSE_FILES = files
        try:
            with redirect_stderr(io.StringIO()):
                return self.mod.main()
        finally:
            self.mod.PROSE_FILES = original

    def test_every_public_prose_surface_is_scanned(self):
        names = {str(path.relative_to(ROOT)) for path in self.mod.PROSE_FILES}
        for expected in (
            "README.md",
            "AGENTS.md",
            "CHANGELOG.md",
            "CLAUDE.md",
            "docs/decisions.md",
            "skills/recognitio/SKILL.md",
            ".github/pull_request_template.md",
            ".github/ISSUE_TEMPLATE/bug_report.md",
            ".github/ISSUE_TEMPLATE/feature_request.md",
            ".coderabbit.yaml",
        ):
            self.assertIn(expected, names)

    def test_em_dash_beside_a_url_is_still_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "page.md",
                "See https://example.com/spec for the plan %s truly.\n"
                % EM_DASH,
            )
            self.assertEqual(self.run_main_on([path]), 1)

    def test_semicolon_right_after_a_markdown_link_is_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "page.md",
                "See [guide](https://example.com/spec); then continue.\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)

    def test_colon_right_after_a_markdown_link_is_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "page.md",
                "See [guide](https://example.com/spec): then continue.\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)

    def test_a_markdown_link_with_clean_prose_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "page.md",
                "See [guide](https://example.com/spec) before continuing.\n",
            )
            self.assertEqual(self.run_main_on([path]), 0)

    def test_a_bare_url_line_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "page.md",
                "The plan lives at https://example.com/spec today.\n",
            )
            self.assertEqual(self.run_main_on([path]), 0)

    def test_em_dash_in_a_template_shaped_file_is_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "CLAUDE.md",
                "All guidance lives elsewhere %s read it first.\n" % EM_DASH,
            )
            self.assertEqual(self.run_main_on([path]), 1)

    def test_yaml_block_scalar_prose_is_scanned(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "reviews:\n  instructions: |\n"
                "    Be direct %s always.\n" % EM_DASH,
            )
            self.assertEqual(self.run_main_on([path]), 1)

    def test_yaml_keys_and_directives_are_syntax(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "# yaml-language-server: $schema=https://example.com/s.json\n"
                "language: \"en-US\"\n"
                "tone: \"Be direct and plain.\"\n",
            )
            self.assertEqual(self.run_main_on([path]), 0)


class TestCheckSkill(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_skill")

    def test_folded_description_is_measured_whole(self):
        text = (
            "---\nname: recognitio\n"
            "description: first part\n  second part\n---\n"
        )
        fields = self.mod.parse_frontmatter(text)
        self.assertEqual(fields["description"], "first part second part")

    def test_over_limit_folded_description_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "recognitio"
            skill_dir.mkdir()
            long_half = "x" * 600
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                "---\nname: recognitio\ndescription: %s\n  %s\n---\n\n# X\n"
                % (long_half, long_half),
                encoding="utf-8",
            )
            original = (self.mod.SKILL_DIR, self.mod.SKILL_MD, self.mod.EXTRACT)
            self.mod.SKILL_DIR = skill_dir
            self.mod.SKILL_MD = skill_md
            self.mod.EXTRACT = ROOT / "skills" / "recognitio" / "scripts" / "extract.py"
            try:
                with redirect_stderr(io.StringIO()) as captured:
                    code = self.mod.main()
            finally:
                self.mod.SKILL_DIR, self.mod.SKILL_MD, self.mod.EXTRACT = original
            self.assertEqual(code, 1)
            self.assertIn("over the 1024 limit", captured.getvalue())

    def test_the_real_skill_package_is_valid(self):
        self.assertEqual(self.mod.main(), 0)


class TestCheckPacket(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_packet")
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.email", "test@example.com")
        git(self.repo, "config", "user.name", "Test User")
        git(self.repo, "config", "commit.gpgsign", "false")
        (self.repo / "a.py").write_text("x = 1\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-m", "one")
        self.head = git(self.repo, "rev-parse", "HEAD")

    def tearDown(self):
        self.tmp.cleanup()

    def write_packet(self, name, manifest):
        out = Path(self.tmp.name) / name
        out.mkdir()
        (out / "packet.md").write_text("# packet\n", encoding="utf-8")
        if manifest is not None:
            (out / "manifest.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
        return out

    def run_check(self, out):
        with redirect_stderr(io.StringIO()):
            return self.mod.main([str(out), "--repo", str(self.repo)])

    def test_verified_packet_for_the_current_head_passes(self):
        out = self.write_packet(
            "good", {"verified": True, "head": self.head}
        )
        self.assertEqual(self.run_check(out), 0)

    def test_unverified_packet_fails(self):
        out = self.write_packet(
            "bad", {"verified": False, "head": self.head}
        )
        self.assertEqual(self.run_check(out), 1)

    def test_packet_for_a_stale_head_fails(self):
        out = self.write_packet(
            "stale", {"verified": True, "head": "0" * 40}
        )
        self.assertEqual(self.run_check(out), 1)

    def test_missing_manifest_fails(self):
        out = self.write_packet("empty", None)
        self.assertEqual(self.run_check(out), 1)

    def test_empty_packet_file_fails(self):
        out = self.write_packet(
            "hollow", {"verified": True, "head": self.head}
        )
        (out / "packet.md").write_text("", encoding="utf-8")
        self.assertEqual(self.run_check(out), 1)

    def test_null_manifest_fails(self):
        out = self.write_packet(
            "nullman", {"verified": True, "head": self.head}
        )
        (out / "manifest.json").write_text("null", encoding="utf-8")
        self.assertEqual(self.run_check(out), 1)

    def test_non_object_manifest_fails(self):
        out = self.write_packet(
            "listman", {"verified": True, "head": self.head}
        )
        (out / "manifest.json").write_text('["verified"]', encoding="utf-8")
        self.assertEqual(self.run_check(out), 1)


SIGN_OFF = (
    "Signed-off-by: David Engelmann "
    "<81196676+david-engelmann@users.noreply.github.com>"
)


class TestDcoWorkflow(unittest.TestCase):
    """The DCO job must read the trailer block, not the whole message.

    The check line is taken from the workflow itself and run against
    real commits, so reverting the workflow to a whole message grep
    makes the buried trailer case pass and this test fail.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
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


if __name__ == "__main__":
    unittest.main()
