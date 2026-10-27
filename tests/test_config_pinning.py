"""Regression tests for the config pinning completeness fix.

Round 42 of the 300 round audit program measured the ambient
configuration surface the extractor pin list did not cover. A
submodule ignore setting deleted a submodule change from a
verified packet, attribute sources outside the reviewed tree
reshaped packets while the packet credited the tree, the diff
algorithm was pinned on body diffs but not on the counts the
manifest is built from, a log output encoding turned a packet
into bytes that are not valid UTF-8, blame attribution followed
clone mailmap and ignore revs state, the hash abbreviation
length reshaped three packet surfaces, the submodule display
setting rewrote or broke gitlink extraction, and two pathspec
mode variables in the caller environment broke extraction on
attribute marked files. Every test here fails against the pre
fix extractor and checker pair for the reason its docstring or
name states and passes against the fixed pair, apart from the
two control shapes that were already right and are named as
controls.
"""

import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
EXTRACT_PATH = (
    ROOT / ".agents" / "skills" / "recognitio" / "scripts" / "extract.py"
)
CHECK_PATH = ROOT / "scripts" / "check_packet.py"
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


def load_at(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


extract_mod = load_at(EXTRACT_PATH, "extract_for_config_pinning_tests")
check_mod = load_at(CHECK_PATH, "check_packet_for_config_pinning_tests")


class RetryingTemporaryDirectory(tempfile.TemporaryDirectory):
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


def git(repo, *args):
    result = subprocess.run(
        ["git", "-C", str(repo)] + list(args),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(
            "git %s failed: %s" % (" ".join(args), result.stderr)
        )
    return result.stdout.strip()


def init_repo(repo):
    repo.mkdir(parents=True, exist_ok=True)
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Test User")
    git(repo, "config", "commit.gpgsign", "false")


def commit_all(repo, message):
    git(repo, "add", "-A")
    git(repo, "commit", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def write_tree(repo, mapping):
    for name, content in mapping.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content)


def make_repo(tmp, commits):
    repo = Path(tmp) / "repo"
    init_repo(repo)
    for index, mapping in enumerate(commits):
        write_tree(repo, mapping)
        commit_all(repo, "commit %d" % index)
    return repo


def run_extract(repo, out, *extra):
    with redirect_stderr(io.StringIO()):
        code = extract_mod.main([
            "--repo", str(repo), "--out", str(out),
            "--range", "HEAD~1..HEAD",
        ] + list(extra))
    return code


def run_extract_tiers(repo, out):
    return run_extract(repo, out, "--tiers", "0,1")


def read_manifest(out):
    return json.loads((Path(out) / "manifest.json").read_text())


def read_packet(out):
    return (Path(out) / "packet.md").read_text(encoding="utf-8")


def global_home(tmp, name, settings):
    """A scratch home whose global config carries the given settings."""
    home = Path(tmp) / name
    home.mkdir(parents=True, exist_ok=True)
    lines = []
    section = None
    for key, value in settings:
        head, _, leaf = key.rpartition(".")
        if head != section:
            lines.append("[%s]" % head)
            section = head
        lines.append("\t%s = %s" % (leaf, value))
    (home / ".gitconfig").write_text("\n".join(lines) + "\n")
    xdg = Path(tmp) / (name + "-xdg")
    xdg.mkdir(parents=True, exist_ok=True)
    return {"HOME": str(home), "XDG_CONFIG_HOME": str(xdg)}


class TestPinLists(unittest.TestCase):
    """The pins stand in the shared list both programs carry."""

    def test_the_shared_pin_list_covers_the_round_42_knobs(self):
        pin = " ".join(extract_mod.GIT_PIN)
        for needle in (
            "diff.algorithm=histogram",
            "diff.ignoreSubmodules=none",
            "diff.submodule=short",
            "core.abbrev=7",
            "i18n.logOutputEncoding=UTF-8",
            "core.attributesFile=",
            "attr.tree=",
            "diff.renameLimit=0",
        ):
            self.assertIn(needle, pin)

    def test_the_packet_check_pin_list_matches_the_extractor(self):
        self.assertEqual(check_mod.GIT_PIN, extract_mod.GIT_PIN)

    def test_the_stat_fallback_carries_width_pins(self):
        calls = []

        def fake_run_git(repo, args, check=True, global_flags=()):
            calls.append((list(args), list(global_flags)))
            if args[0] == "merge-base":
                return extract_mod.Proc(0, "a" * 40 + "\n", "")
            if args[0] == "log":
                return extract_mod.Proc(0, "abc1234 a commit\n", "")
            if args[0] == "range-diff":
                return extract_mod.Proc(1, "", "range diff unavailable")
            return extract_mod.Proc(0, " fn.py | 1 +\n", "")

        with mock.patch.object(extract_mod, "run_git", fake_run_git):
            extract_mod.build_rereview(
                Path("."), "b" * 40, "c" * 40, "d" * 40, []
            )
        stat_call = next(
            c for c in calls if c[0][0] == "diff" and "--stat" in c[0]
        )
        for flag in (
            "--stat-width=80", "--stat-name-width=50",
            "--stat-graph-width=30",
        ):
            self.assertIn(flag, stat_call[0])
        self.assertIn("--attr-source=" + "c" * 40, stat_call[1])

    def test_the_helper_reader_carries_the_pin_list(self):
        captured = {}

        def fake_run_process(argv, cwd=None):
            captured["argv"] = list(argv)
            return subprocess.CompletedProcess(argv, 0, b"true\n", b"")

        with mock.patch.object(
            extract_mod, "run_process", fake_run_process
        ):
            extract_mod._git_read(
                Path("."), "rev-parse", "--show-toplevel"
            )
        argv = captured["argv"]
        self.assertIn("--literal-pathspecs", argv)
        for item in extract_mod.GIT_PIN:
            self.assertIn(item, argv)

    def test_child_env_scrubs_attribute_and_pathspec_variables(self):
        poisoned = {
            "GIT_ATTR_SOURCE": EMPTY_TREE,
            "GIT_ATTR_GLOBAL": "/tmp/forge-attrs",
            "GIT_ATTR_SYSTEM": "/tmp/forge-attrs",
            "GIT_LITERAL_PATHSPECS": "1",
            "GIT_GLOB_PATHSPECS": "1",
            "GIT_ICASE_PATHSPECS": "1",
            "GIT_NOGLOB_PATHSPECS": "1",
        }
        for module in (extract_mod, check_mod):
            with mock.patch.dict(os.environ, poisoned):
                env = module.scrubbed_child_env()
            for name in poisoned:
                self.assertNotIn(name, env)
            self.assertEqual(env["GIT_ATTR_NOSYSTEM"], "1")
            self.assertEqual(env["GIT_NO_REPLACE_OBJECTS"], "1")

    def test_the_blame_reading_carries_its_attribution_pins(self):
        calls = []

        def fake_run_git(repo, args, check=True, global_flags=()):
            return extract_mod.Proc(0, "/tmp/gitdir\n", "")

        def fake_run_argv(argv, cwd, check, label):
            calls.append((list(argv), cwd))
            return extract_mod.Proc(0, "", "")

        head = "c" * 40
        with mock.patch.object(extract_mod, "run_git", fake_run_git), \
                mock.patch.object(
                    extract_mod, "run_argv", fake_run_argv
                ):
            extract_mod.blame_section(
                Path("."), head,
                [{"path": "mod.py"}], {"mod.py": [(1, 2)]}, [],
            )
        argv, cwd = calls[0]
        self.assertEqual(cwd, "/tmp/gitdir")
        self.assertIn("--git-dir", argv)
        self.assertIn("mailmap.file=", argv)
        self.assertIn("mailmap.blob=%s:.mailmap" % head, argv)
        marker = argv.index("--ignore-revs-file")
        self.assertEqual(argv[marker + 1], "")
        self.assertIn("--no-textconv", argv)


def build_submodule_repo(tmp):
    """An outer repo whose head moves a submodule pointer and edits a file."""
    inner = Path(tmp) / "inner"
    init_repo(inner)
    write_tree(inner, {"lib.txt": "lib v1\n"})
    commit_all(inner, "v1")
    write_tree(inner, {"lib.txt": "lib v2\n"})
    commit_all(inner, "v2")
    inner_v1 = git(inner, "rev-parse", "HEAD~1")

    repo = Path(tmp) / "repo"
    init_repo(repo)
    write_tree(repo, {"main.py": "main\n"})
    commit_all(repo, "base")
    git(
        repo, "-c", "protocol.file.allow=always",
        "submodule", "add", "-q", str(inner), "sub",
    )
    git(repo / "sub", "checkout", "-q", inner_v1)
    commit_all(repo, "add sub at v1")
    write_tree(repo, {"main.py": "main\nmain2\n"})
    git(repo / "sub", "checkout", "-q", "main")
    commit_all(repo, "sub at v2 and main edit")
    return repo


class TestSubmodulePins(unittest.TestCase):
    """A submodule change survives ambient submodule settings."""

    def setUp(self):
        self.tmp = RetryingTemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = build_submodule_repo(self.tmp.name)
        self.clean_out = Path(self.tmp.name) / "clean"
        self.assertEqual(run_extract_tiers(self.repo, self.clean_out), 0)
        self.clean_packet = read_packet(self.clean_out)
        manifest = read_manifest(self.clean_out)
        self.assertTrue(manifest["verified"], manifest["discrepancies"])
        self.assertIn("sub", [f["path"] for f in manifest["files"]])

    def knobbed_packet(self, name):
        out = Path(self.tmp.name) / name
        code = run_extract_tiers(self.repo, out)
        self.assertEqual(code, 0)
        manifest = read_manifest(out)
        self.assertTrue(manifest["verified"], manifest["discrepancies"])
        self.assertIn("sub", [f["path"] for f in manifest["files"]])
        return read_packet(out)

    def test_ignore_all_in_clone_config_keeps_the_submodule_change(self):
        git(self.repo, "config", "diff.ignoreSubmodules", "all")
        self.assertEqual(self.knobbed_packet("clone"), self.clean_packet)

    def test_ignore_all_in_global_config_keeps_the_submodule_change(self):
        env = global_home(
            self.tmp.name, "home-ignore",
            [("diff.ignoreSubmodules", "all")],
        )
        with mock.patch.dict(os.environ, env):
            self.assertEqual(
                self.knobbed_packet("global"), self.clean_packet
            )

    def test_display_log_and_diff_in_clone_config_match_the_clean_packet(self):
        for value in ("log", "diff"):
            git(self.repo, "config", "diff.submodule", value)
            self.assertEqual(
                self.knobbed_packet("display-" + value),
                self.clean_packet,
            )
            git(self.repo, "config", "--unset", "diff.submodule")


SWAP_BASE = (
    "top0 = 0\ntop1 = 1\ntop2 = 2\ntop3 = 3\n"
    "def a():\n    x = 1\n    y = 2\n    z = 3\n    return x\n"
    "\n"
    "def b():\n    x = 1\n    y = 2\n    z = 3\n    return x\n"
    "bot0 = 0\nbot1 = 1\nbot2 = 2\nbot3 = 3\n"
)
SWAP_HEAD = (
    "top0 = 0\ntop1 = 1\ntop2 = 2\ntop3 = 3\n"
    "def b():\n    x = 1\n    y = 2\n    z = 3\n    return x\n"
    "\n"
    "def a():\n    x = 1\n    y = 2\n    z = 3\n    return x\n"
    "bot0 = 0\nbot1 = 1\nbot2 = 2\nbot3 = 3\n"
)


class TestAlgorithmPin(unittest.TestCase):
    """The manifest counts and the packet bodies use one algorithm."""

    def setUp(self):
        self.tmp = RetryingTemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = make_repo(self.tmp.name, [
            {"f.py": SWAP_BASE},
            {"f.py": SWAP_HEAD},
        ])
        self.clean_out = Path(self.tmp.name) / "clean"
        self.assertEqual(run_extract_tiers(self.repo, self.clean_out), 0)
        self.clean_packet = read_packet(self.clean_out)

    def assert_swap_counts(self, out):
        manifest = read_manifest(out)
        self.assertTrue(manifest["verified"], manifest["discrepancies"])
        entry = manifest["files"][0]
        self.assertEqual(
            (entry["additions"], entry["deletions"]), (2, 2), entry
        )

    def test_the_clean_swap_verifies_at_two_and_two(self):
        self.assert_swap_counts(self.clean_out)

    def test_patience_in_clone_config_still_verifies(self):
        git(self.repo, "config", "diff.algorithm", "patience")
        out = Path(self.tmp.name) / "clone"
        self.assertEqual(run_extract_tiers(self.repo, out), 0)
        self.assert_swap_counts(out)
        self.assertEqual(read_packet(out), self.clean_packet)

    def test_patience_in_global_config_still_verifies(self):
        env = global_home(
            self.tmp.name, "home-patience",
            [("diff.algorithm", "patience")],
        )
        out = Path(self.tmp.name) / "global"
        with mock.patch.dict(os.environ, env):
            self.assertEqual(run_extract_tiers(self.repo, out), 0)
        self.assert_swap_counts(out)
        self.assertEqual(read_packet(out), self.clean_packet)


class TestEncodingPin(unittest.TestCase):
    """A legacy encoded subject reaches the packet as UTF-8 text."""

    def build_legacy_repo(self, tmp):
        repo = Path(tmp) / "repo"
        init_repo(repo)
        write_tree(repo, {"f.py": "x = 1\n"})
        commit_all(repo, "base")
        write_tree(repo, {"f.py": "x = 2\n"})
        git(repo, "add", "-A")
        message = Path(tmp) / "message.bin"
        message.write_bytes(b"fix caf\xe9 bug in parser\n")
        result = subprocess.run(
            ["git", "-C", str(repo),
             "-c", "i18n.commitEncoding=ISO-8859-1",
             "commit", "-q", "-F", str(message)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return repo

    def assert_utf8_packet(self, repo, out):
        code = run_extract_tiers(repo, out)
        self.assertEqual(code, 0)
        raw = (Path(out) / "packet.md").read_bytes()
        text = raw.decode("utf-8")
        self.assertIn("fix caf\u00e9 bug in parser", text)
        manifest = read_manifest(out)
        self.assertTrue(manifest["verified"], manifest["discrepancies"])
        with redirect_stderr(io.StringIO()):
            self.assertEqual(
                check_mod.main([str(out), "--repo", str(repo)]), 0
            )

    def test_log_output_encoding_in_clone_config(self):
        with RetryingTemporaryDirectory() as tmp:
            repo = self.build_legacy_repo(tmp)
            git(repo, "config", "i18n.logOutputEncoding", "ISO-8859-1")
            self.assert_utf8_packet(repo, Path(tmp) / "out")

    def test_log_output_encoding_in_global_config(self):
        with RetryingTemporaryDirectory() as tmp:
            repo = self.build_legacy_repo(tmp)
            env = global_home(
                tmp, "home-enc",
                [("i18n.logOutputEncoding", "ISO-8859-1")],
            )
            with mock.patch.dict(os.environ, env):
                self.assert_utf8_packet(repo, Path(tmp) / "out")


PLAIN_COMMITS = [
    {"f.py": "x = 1\ny = 2\n"},
    {"f.py": "x = 9\ny = 2\n"},
]
MARKED_COMMITS = [
    {".gitattributes": "*.py binary\n", "f.py": "x = 1\ny = 2\n"},
    {"f.py": "x = 9\ny = 2\n"},
]


class TestAttributeConfinement(unittest.TestCase):
    """Attributes reach the packet from the reviewed tree alone."""

    def setUp(self):
        self.tmp = RetryingTemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def clean_run(self, repo, name="clean"):
        out = Path(self.tmp.name) / name
        self.assertEqual(run_extract_tiers(repo, out), 0)
        return out, read_packet(out)

    def test_clone_attributes_file_cannot_mark_a_plain_file(self):
        repo = make_repo(self.tmp.name, PLAIN_COMMITS)
        clean_out, clean_packet = self.clean_run(repo)
        self.assertEqual(read_manifest(clean_out)["exclusions"], [])
        planted = Path(self.tmp.name) / "attrs.txt"
        planted.write_text("f.py binary\n")
        git(repo, "config", "core.attributesFile", str(planted))
        out = Path(self.tmp.name) / "knobbed"
        self.assertEqual(run_extract_tiers(repo, out), 0)
        self.assertEqual(read_manifest(out)["exclusions"], [])
        self.assertEqual(read_packet(out), clean_packet)

    def test_global_attributes_file_cannot_mark_a_plain_file(self):
        repo = make_repo(self.tmp.name, PLAIN_COMMITS)
        _clean_out, clean_packet = self.clean_run(repo)
        planted = Path(self.tmp.name) / "attrs.txt"
        planted.write_text("f.py binary\n")
        env = global_home(
            self.tmp.name, "home-attrs",
            [("core.attributesFile", str(planted))],
        )
        out = Path(self.tmp.name) / "knobbed"
        with mock.patch.dict(os.environ, env):
            self.assertEqual(run_extract_tiers(repo, out), 0)
        self.assertEqual(read_manifest(out)["exclusions"], [])
        self.assertEqual(read_packet(out), clean_packet)

    def test_attr_tree_config_cannot_mark_a_plain_file(self):
        repo = make_repo(self.tmp.name, PLAIN_COMMITS)
        _clean_out, clean_packet = self.clean_run(repo)
        base = git(repo, "rev-parse", "HEAD~1")
        git(repo, "checkout", "-q", "-b", "attrs", base)
        write_tree(repo, {".gitattributes": "f.py binary\n"})
        commit_all(repo, "attrs")
        tree = git(repo, "rev-parse", "HEAD^{tree}")
        git(repo, "checkout", "-q", "main")
        git(repo, "config", "attr.tree", tree)
        out = Path(self.tmp.name) / "knobbed"
        self.assertEqual(run_extract_tiers(repo, out), 0)
        self.assertEqual(read_manifest(out)["exclusions"], [])
        self.assertEqual(read_packet(out), clean_packet)

    def test_working_tree_attributes_cannot_mark_a_plain_file(self):
        repo = make_repo(self.tmp.name, PLAIN_COMMITS)
        _clean_out, clean_packet = self.clean_run(repo)
        write_tree(repo, {".gitattributes": "f.py binary\n"})
        out = Path(self.tmp.name) / "knobbed"
        self.assertEqual(run_extract_tiers(repo, out), 0)
        self.assertEqual(read_manifest(out)["exclusions"], [])
        self.assertEqual(read_packet(out), clean_packet)

    def test_environment_attribute_source_cannot_strip_a_tree_marking(self):
        repo = make_repo(self.tmp.name, MARKED_COMMITS)
        clean_out, clean_packet = self.clean_run(repo)
        self.assertEqual(len(read_manifest(clean_out)["exclusions"]), 1)
        out = Path(self.tmp.name) / "knobbed"
        with mock.patch.dict(
            os.environ, {"GIT_ATTR_SOURCE": EMPTY_TREE}
        ):
            self.assertEqual(run_extract_tiers(repo, out), 0)
        self.assertEqual(read_packet(out), clean_packet)

    def test_the_receipt_names_the_tree_under_review(self):
        repo = make_repo(self.tmp.name, MARKED_COMMITS)
        out, _packet = self.clean_run(repo)
        receipts = read_manifest(out)["exclusions"]
        self.assertEqual(len(receipts), 1, receipts)
        self.assertIn(
            "attributes of the tree under review", receipts[0]["reason"]
        )
        self.assertNotIn("repository attributes", receipts[0]["reason"])

    def test_info_attributes_refuse_the_run_and_the_stamp(self):
        repo = make_repo(self.tmp.name, PLAIN_COMMITS)
        clean_out, _packet = self.clean_run(repo)
        info = repo / ".git" / "info" / "attributes"
        info.write_text("f.py binary\n")
        out = Path(self.tmp.name) / "knobbed"
        self.assertEqual(run_extract_tiers(repo, out), 2)
        self.assertFalse(read_manifest(out)["verified"])
        with redirect_stderr(io.StringIO()):
            self.assertEqual(
                check_mod.main([str(clean_out), "--repo", str(repo)]), 1
            )

    def test_info_attributes_holding_only_comments_do_not_refuse(self):
        repo = make_repo(self.tmp.name, PLAIN_COMMITS)
        info = repo / ".git" / "info" / "attributes"
        info.write_text("# a local note\n\n")
        out = Path(self.tmp.name) / "out"
        self.assertEqual(run_extract_tiers(repo, out), 0)
        self.assertTrue(read_manifest(out)["verified"])


def build_two_author_repo(tmp):
    """Lines written by one author and edited by a second author."""
    repo = Path(tmp) / "repo"
    init_repo(repo)
    git(repo, "config", "user.name", "Author A")
    git(repo, "config", "user.email", "a@example.com")
    write_tree(repo, {"f.py": "one\ntwo\n"})
    commit_all(repo, "base")
    git(repo, "config", "user.name", "Author B")
    git(repo, "config", "user.email", "b@example.com")
    write_tree(repo, {"f.py": "one edited\ntwo edited\n"})
    head = commit_all(repo, "edit")
    return repo, head


class TestBlameConfinement(unittest.TestCase):
    """Blame credit follows the reviewed tree and nothing beside it."""

    def setUp(self):
        self.tmp = RetryingTemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo, self.head = build_two_author_repo(self.tmp.name)
        self.clean_out = Path(self.tmp.name) / "clean"
        self.assertEqual(run_extract(self.repo, self.clean_out), 0)
        self.clean_packet = read_packet(self.clean_out)
        self.assertIn(
            "Author B %s lines 2" % self.head[:8], self.clean_packet
        )

    def knobbed_packet(self, name):
        out = Path(self.tmp.name) / name
        self.assertEqual(run_extract(self.repo, out), 0)
        manifest = read_manifest(out)
        self.assertTrue(manifest["verified"], manifest["discrepancies"])
        return read_packet(out)

    def test_mailmap_file_in_clone_config_does_not_rewrite_credit(self):
        planted = Path(self.tmp.name) / "mailmap.txt"
        planted.write_text("Carol C <b@example.com>\n")
        git(self.repo, "config", "mailmap.file", str(planted))
        packet = self.knobbed_packet("config-mailmap")
        self.assertEqual(packet, self.clean_packet)
        self.assertNotIn("Carol C", packet)

    def test_mailmap_blob_in_clone_config_does_not_rewrite_credit(self):
        planted = Path(self.tmp.name) / "mailmap.txt"
        planted.write_text("Carol C <b@example.com>\n")
        blob = git(self.repo, "hash-object", "-w", str(planted))
        git(self.repo, "config", "mailmap.blob", blob)
        packet = self.knobbed_packet("config-blob")
        self.assertEqual(packet, self.clean_packet)
        self.assertNotIn("Carol C", packet)

    def test_untracked_worktree_mailmap_does_not_rewrite_credit(self):
        (self.repo / ".mailmap").write_text("Dave D <b@example.com>\n")
        packet = self.knobbed_packet("worktree-mailmap")
        self.assertEqual(packet, self.clean_packet)
        self.assertNotIn("Dave D", packet)

    def test_ignore_revs_file_in_clone_config_does_not_move_credit(self):
        planted = Path(self.tmp.name) / "ignore.txt"
        planted.write_text(self.head + "\n")
        git(self.repo, "config", "blame.ignoreRevsFile", str(planted))
        packet = self.knobbed_packet("ignore-revs")
        self.assertEqual(packet, self.clean_packet)
        self.assertIn(
            "Author B %s lines 2" % self.head[:8], packet
        )

    def test_a_committed_mailmap_inside_the_range_still_applies(self):
        # A control shape. The mailmap file is reviewed content in
        # the recorded range, so its renaming is git canonical and
        # the fix leaves it in force.
        with RetryingTemporaryDirectory() as tmp:
            repo, _head = build_two_author_repo(tmp)
            git(repo, "config", "user.name", "Author A")
            git(repo, "config", "user.email", "a@example.com")
            write_tree(repo, {
                ".mailmap": "Mapped Name <a@example.com>\n",
                "f.py": "one again\ntwo again\n",
            })
            commit_all(repo, "edit with a committed mailmap")
            out = Path(tmp) / "out"
            self.assertEqual(run_extract(repo, out), 0)
            packet = read_packet(out)
            self.assertIn("Mapped Name", packet)


class TestAbbrevPin(unittest.TestCase):
    """Shortened hashes stand at the pinned length in every clone."""

    def setUp(self):
        self.tmp = RetryingTemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = make_repo(self.tmp.name, [
            {"mod.py": "a = 1\nb = 2\nc = 3\n"},
            {"mod.py": "a = 1\nb = 22\nc = 3\n"},
        ])
        self.since = git(self.repo, "rev-parse", "HEAD~1")
        self.clean_out = Path(self.tmp.name) / "clean"
        self.assertEqual(
            run_extract(
                self.repo, self.clean_out, "--since", self.since
            ),
            0,
        )
        self.clean_packet = read_packet(self.clean_out)

    def test_abbrev_40_in_clone_config_matches_the_clean_packet(self):
        git(self.repo, "config", "core.abbrev", "40")
        out = Path(self.tmp.name) / "clone"
        self.assertEqual(
            run_extract(self.repo, out, "--since", self.since), 0
        )
        self.assertEqual(read_packet(out), self.clean_packet)
        with redirect_stderr(io.StringIO()):
            self.assertEqual(
                check_mod.main([str(out), "--repo", str(self.repo)]), 0
            )

    def test_abbrev_4_in_global_config_matches_the_clean_packet(self):
        env = global_home(
            self.tmp.name, "home-abbrev", [("core.abbrev", "4")]
        )
        out = Path(self.tmp.name) / "global"
        with mock.patch.dict(os.environ, env):
            self.assertEqual(
                run_extract(self.repo, out, "--since", self.since), 0
            )
        self.assertEqual(read_packet(out), self.clean_packet)


class TestPathspecEnvScrub(unittest.TestCase):
    """Pathspec mode variables in the caller env cannot break a run."""

    def test_icase_and_glob_pathspec_variables_are_scrubbed(self):
        with RetryingTemporaryDirectory() as tmp:
            repo = make_repo(tmp, MARKED_COMMITS)
            for name, var in (
                ("icase", "GIT_ICASE_PATHSPECS"),
                ("glob", "GIT_GLOB_PATHSPECS"),
            ):
                out = Path(tmp) / ("out-" + name)
                with mock.patch.dict(os.environ, {var: "1"}):
                    code = run_extract_tiers(repo, out)
                self.assertEqual(code, 0, var)
                self.assertTrue(read_manifest(out)["verified"])


if __name__ == "__main__":
    unittest.main()
