"""The eval gate fixture writer key screening.

Round 36 Finding F5 and round 247 duty 2 of the 300 round
programme. The writer in scripts/check_evals.py takes each
sources key as a path under the fixture repository. Before
the screening, a crafted sources file wrote outside the
fixture through a parent key, an absolute key, and a mid
path traversal key, replaced the fixture identity through a
git config key, planted a hook through a hooks key, and ran
a planted command through a clean filter chain the gate own
staging step fired. These tests hand the builder each shape
and require a refusal that names the key, with nothing
written anywhere, beside a clean control that still builds.
"""

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    path = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(
        "screening_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CLEAN = {"a.py": "x = 1\n"}
HEAD = {"a.py": "x = 2\n"}


class TestEvalWriterScreening(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_evals")

    def attempt(self, base, head, tmp):
        sources = {"base": base, "head": head}
        return self.mod.build_fixture_repo(tmp, sources)

    def assert_refused(self, base, head, needle):
        with tempfile.TemporaryDirectory() as tmp:
            outside = Path(tmp) / "outside.txt"
            marker = Path(tmp) / "marker.txt"
            base = {
                k.replace("__OUT__", str(outside)):
                v.replace("__OUT__", str(outside)).replace(
                    "__MARKER__", str(marker))
                for k, v in base.items()
            }
            head = {
                k.replace("__OUT__", str(outside)):
                v.replace("__OUT__", str(outside)).replace(
                    "__MARKER__", str(marker))
                for k, v in head.items()
            }
            with self.assertRaises(AssertionError) as caught:
                self.attempt(base, head, tmp)
            self.assertIn(needle, str(caught.exception))
            self.assertFalse(
                outside.exists(),
                "the escape wrote its planted file outside "
                "the fixture repository")
            self.assertFalse(
                marker.exists(),
                "a planted command ran during the build")
            self.assertFalse(
                (Path(tmp) / "repo").exists(),
                "the builder created the fixture repository "
                "before screening the keys")

    def test_the_clean_control_still_builds(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, base, head, diff = self.attempt(
                dict(CLEAN), dict(HEAD), tmp)
            self.assertTrue((repo / "a.py").is_file())
            self.assertIn(b"x = 2", diff)

    def test_a_parent_key_is_refused(self):
        self.assert_refused(
            dict(CLEAN),
            {"../outside.txt": "parent planted\n", **HEAD},
            "parent segment")

    def test_parent_keys_in_the_base_mapping_are_refused(self):
        self.assert_refused(
            {"../../outside.txt": "parent planted\n", **CLEAN},
            dict(HEAD),
            "parent segment")

    def test_an_absolute_key_is_refused(self):
        self.assert_refused(
            dict(CLEAN),
            {"__OUT__": "absolute planted\n", **HEAD},
            "absolute")

    def test_a_mid_path_traversal_key_is_refused(self):
        self.assert_refused(
            dict(CLEAN),
            {"sub/../../outside.txt": "mid planted\n", **HEAD},
            "parent segment")

    def test_a_git_config_key_is_refused(self):
        planted = (
            "[user]\n\tname = Planted Identity\n"
            "\temail = planted@example.invalid\n"
        )
        self.assert_refused(
            {".git/config": planted, **CLEAN},
            dict(HEAD),
            "git directory")

    def test_a_git_hooks_key_is_refused(self):
        hook = "#!/bin/sh\ntouch __MARKER__\n"
        self.assert_refused(
            dict(CLEAN),
            {".git/hooks/pre-commit": hook, **HEAD},
            "git directory")

    def test_a_clean_filter_chain_is_refused_at_its_config_key(self):
        config = (
            "[user]\n\tname = Eval Fixture\n"
            "\temail = eval@example.com\n"
            "[filter \"planted\"]\n\tclean = touch __MARKER__ #\n"
        )
        base = {
            ".git/config": config,
            ".gitattributes": "*.py filter=planted\n",
            **CLEAN,
        }
        self.assert_refused(base, dict(HEAD), "git directory")

    def test_a_dot_slash_git_config_key_is_refused(self):
        planted = (
            "[user]\n\tname = Planted Identity\n"
            "\temail = planted@example.invalid\n"
        )
        self.assert_refused(
            {"./.git/config": planted, **CLEAN},
            dict(HEAD),
            "git directory")

    def test_a_double_slash_git_config_key_is_refused(self):
        planted = (
            "[user]\n\tname = Planted Identity\n"
            "\temail = planted@example.invalid\n"
        )
        self.assert_refused(
            {".//.git/config": planted, **CLEAN},
            dict(HEAD),
            "git directory")

    def test_a_dot_slash_git_hooks_key_is_refused(self):
        hook = "#!/bin/sh\ntouch __MARKER__\n"
        self.assert_refused(
            dict(CLEAN),
            {"./.git/hooks/pre-commit": hook, **HEAD},
            "git directory")

    def test_a_dot_slash_clean_filter_chain_is_refused_before_any_git_command(self):
        # The full round 247 chain through the prefix spelling.
        # The refusal must land before the builder creates the
        # fixture repository, so no git command of the gate ever
        # runs with the planted filter standing in its config,
        # and the marker the filter would plant never appears.
        config = (
            "[user]\n\tname = Eval Fixture\n"
            "\temail = eval@example.com\n"
            "[filter \"planted\"]\n\tclean = touch __MARKER__ #\n"
        )
        base = {
            "./.git/config": config,
            ".gitattributes": "*.py filter=planted\n",
            **CLEAN,
        }
        self.assert_refused(base, dict(HEAD), "git directory")

    def test_the_writer_itself_refuses_a_parent_key(self):
        # The screening stands in the writer as well as in the
        # builder entry, so a caller that reaches the writer
        # directly is refused before the deletion pass runs.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            (repo / "keep.txt").write_text("keep\n")
            with self.assertRaises(AssertionError) as caught:
                self.mod.write_fixture(
                    repo, {"../outside.txt": "planted\n"})
            self.assertIn("parent segment", str(caught.exception))
            self.assertEqual(
                (repo / "keep.txt").read_text(), "keep\n")
            self.assertFalse((Path(tmp) / "outside.txt").exists())


if __name__ == "__main__":
    unittest.main()
