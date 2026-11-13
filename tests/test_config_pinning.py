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
evals_mod = load_at(
    ROOT / "scripts" / "check_evals.py", "check_evals_for_pinning_tests"
)

# The extractor pin list in full, spelled out as data. The
# full pin tests below read this list for exact equality,
# so a change here is a deliberate restatement and not a
# drift.
EXTRACTOR_GIT_PIN = [
    "-c", "core.quotepath=false",
    "-c", "diff.noprefix=false",
    "-c", "diff.mnemonicPrefix=false",
    "-c", "color.ui=false",
    "-c", "color.diff=false",
    "-c", "color.grep=false",
    "-c", "color.status=false",
    "-c", "grep.column=false",
    "-c", "diff.interHunkContext=0",
    "-c", "diff.renameLimit=0",
    "-c", "diff.algorithm=histogram",
    "-c", "diff.ignoreSubmodules=none",
    "-c", "diff.submodule=short",
    "-c", "core.abbrev=7",
    "-c", "i18n.logOutputEncoding=UTF-8",
    "-c", "core.attributesFile=",
    "-c", "attr.tree=",
]

# The eval gate carries a narrower pin for its own git
# reads, the nine knobs below, and the narrowness is
# deliberate. It stands pinned as its own literal list so
# it can only change by restatement.
EVALS_GIT_PIN = [
    "-c", "core.quotepath=false",
    "-c", "diff.noprefix=false",
    "-c", "diff.mnemonicPrefix=false",
    "-c", "color.ui=false",
    "-c", "color.diff=false",
    "-c", "color.status=false",
    "-c", "color.grep=false",
    "-c", "grep.column=false",
    "-c", "diff.interHunkContext=0",
]


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

    def test_the_extractor_pin_list_stands_in_full(self):
        # Round 9 spec Note 1. The needles test above reads
        # the joined list for membership, so a knob dropped
        # from the list, renamed, or moved out of order
        # passes it while the pin the packet is built under
        # changes. The list stands here in full and in
        # order, and the packet checker copy is held equal
        # to it by the test above.
        self.assertEqual(extract_mod.GIT_PIN, EXTRACTOR_GIT_PIN)
        self.assertEqual(check_mod.GIT_PIN, EXTRACTOR_GIT_PIN)

    def test_the_eval_gate_pin_list_stands_as_its_own_list(self):
        # The eval gate's copy was never compared against
        # any pin before this round. It is a narrower list
        # by design, covering the reads that gate performs,
        # and it stands pinned as that list so widening or
        # narrowing it is a restatement and not a drift.
        # The two colour knobs stand in the other order
        # from the extractor list, which is part of the
        # shipped shape this pin records.
        self.assertEqual(evals_mod.GIT_PIN, EVALS_GIT_PIN)

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
            env=scrubbed_git_env(),
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

    @unittest.skipUnless(hasattr(os, "mkfifo"), "no mkfifo on this host")
    def test_info_attributes_standing_as_a_fifo_do_not_block(self):
        # Scope addition beside round 178 New Minor 1. The
        # clone attributes reading read the info attributes
        # file with a plain read and no regular file test,
        # so a FIFO standing at that path blocked the open
        # the same way a FIFO findings file did, and the git
        # calls the run makes read the same path and block
        # on it as well, so no silent treatment can save
        # this door. The run must refuse the pipe by name
        # before any of those calls, at exit 2. The run is
        # a bounded subprocess because an in process run
        # that still reads the FIFO would hang this test
        # process itself.
        repo = make_repo(self.tmp.name, PLAIN_COMMITS)
        info = repo / ".git" / "info" / "attributes"
        if info.exists() or info.is_symlink():
            info.unlink()
        os.mkfifo(info)
        out = Path(self.tmp.name) / "out"
        cmd = [
            sys.executable, str(EXTRACT_PATH),
            "--repo", str(repo), "--out", str(out),
            "--range", "HEAD~1..HEAD", "--tiers", "0,1",
        ]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10
            )
        except subprocess.TimeoutExpired:
            self.fail(
                "the extractor did not finish inside ten "
                "seconds, so it blocked on the info "
                "attributes path"
            )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("named pipe", result.stderr)
        self.assertFalse(read_manifest(out)["verified"])


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


class TestGateScrubParity(unittest.TestCase):
    """Every gate that runs git carries the full scrub.

    Round 4 standards Major 2. The extractor and the packet
    checker scrubbed the attribute sources, the replace refs
    and the pathspec modes, while four sibling gates that also
    run git scrubbed only the location family, so the same
    poisoned environment that the hardened pair refused could
    still reshape their readings. One poisoned environment is
    held over every shipped scrub helper and every helper
    must produce the hardened result.
    """

    FORCED_OFF = ("GIT_NO_REPLACE_OBJECTS", "GIT_ATTR_NOSYSTEM")

    # The graft file name stands forced on rather than dropped
    # in the pair that runs the extraction and its recount, and
    # dropped in the sibling gates, so the absence reading below
    # exempts it and the forced value reading holds it to the
    # empty file the run controls.
    GRAFT_PINNED = ("extract", "check_packet")

    def dropped_names(self):
        # The planted key set is derived from the scrub
        # tuples the helpers themselves carry, so the plant
        # and the scrub cannot drift apart by hand. Every
        # name any shipped helper lists in its location or
        # scrub tuple or its driver or attribute or pathspec
        # tuple is planted, apart from the two names the
        # scrub forces on rather than drops. The config
        # family stands behind a prefix rather than a tuple,
        # so its planted names are built from that prefix.
        names = set()
        for _label, _helper, module in self.scrub_helpers():
            for attr in (
                "GIT_SCRUB_VARS",
                "GIT_LOCATION_VARS",
                "GIT_DRIVER_ENV_VARS",
                "GIT_ATTR_ENV_VARS",
                "GIT_PATHSPEC_ENV_VARS",
            ):
                names.update(getattr(module, attr, ()))
        names.difference_update(self.FORCED_OFF)
        return names

    def poisoned_env(self):
        poisoned = {
            name: "/tmp/forge" for name in self.dropped_names()
        }
        prefix = extract_mod.GIT_CONFIG_ENV_PREFIX
        poisoned[prefix + "_COUNT"] = "1"
        poisoned[prefix + "_KEY_0"] = "diff.drv.textconv"
        poisoned[prefix + "_VALUE_0"] = "/tmp/forge.sh"
        poisoned[prefix + "_PARAMETERS"] = (
            "'diff.drv.textconv=/tmp/forge.sh'"
        )
        return poisoned

    def scrub_helpers(self):
        # The helper set is discovered from the tree rather
        # than named by hand. Every shipped file that
        # carries a scrub helper of this family stands in
        # the set, being the canonical extractor and every
        # file under scripts that defines one of the two
        # helper spellings, the packet checker and the gate
        # scripts and the smoke script among them. A future
        # gate carrying the helper joins the parity test
        # when it lands, with no list to remember to extend.
        candidates = [EXTRACT_PATH]
        candidates.extend(
            sorted((ROOT / "scripts").glob("*.py"))
        )
        helpers = []
        seen = set()
        for path in candidates:
            if path in seen:
                continue
            seen.add(path)
            text = path.read_text(encoding="utf-8")
            helper_name = None
            for spelling in (
                "scrubbed_child_env",
                "scrubbed_git_env",
            ):
                if ("def " + spelling) in text:
                    helper_name = spelling
                    break
            if helper_name is None:
                continue
            label = (
                "extract"
                if path == EXTRACT_PATH
                else path.stem
            )
            module = load_at(
                path, "scrub_parity_discovered_" + label
            )
            helpers.append(
                (label, getattr(module, helper_name), module)
            )
        return helpers

    def test_the_discovery_finds_every_hand_named_helper(self):
        # The discovery must find exactly the helpers the
        # hand written list named on this tree, no fewer.
        labels = {
            label for label, _helper, _module in self.scrub_helpers()
        }
        self.assertEqual(
            labels,
            {
                "extract",
                "check_packet",
                "check_evals",
                "check_fanout",
                "check_regeneration",
                "smoke_extract",
            },
        )

    def test_the_derived_poison_covers_the_named_five(self):
        # The derivation stands on the shipped tuples, and
        # these five names stand in those tuples today, so
        # a tuple that lost one of them in every helper at
        # once would shrink the plant in silence without
        # this pin.
        dropped = self.dropped_names()
        for name in (
            "GIT_COMMON_DIR",
            "GIT_ALTERNATE_OBJECT_DIRECTORIES",
            "GIT_DIFF_OPTS",
            "GIT_PAGER",
            "GIT_EXEC_PATH",
        ):
            self.assertIn(name, dropped)

    def test_every_gate_scrub_drops_the_poisoned_families(self):
        poisoned = self.poisoned_env()
        planted = set(poisoned)
        poisoned["GIT_NO_REPLACE_OBJECTS"] = "0"
        for label, helper, _module in self.scrub_helpers():
            with mock.patch.dict(os.environ, poisoned):
                env = helper()
            for name in planted:
                if name == "GIT_GRAFT_FILE" and label in self.GRAFT_PINNED:
                    continue
                self.assertNotIn(name, env, "%s kept %s" % (label, name))
            for name in self.FORCED_OFF:
                self.assertEqual(
                    env[name], "1", "%s left %s unset" % (label, name)
                )
            if label in self.GRAFT_PINNED:
                pin = Path(env["GIT_GRAFT_FILE"])
                self.assertTrue(pin.is_file(), label)
                self.assertEqual(pin.read_bytes(), b"", label)
            self.assertIn("PATH", env)


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
