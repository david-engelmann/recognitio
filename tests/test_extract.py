import copy
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTRACT = ROOT / "skills" / "recognitio" / "scripts" / "extract.py"

spec = importlib.util.spec_from_file_location("recognitio_extract", EXTRACT)
extract_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extract_mod)

MODULE_V1 = '''"""Fixture module."""


def alpha():
    marker = "ALPHA_TOP_SENTINEL"
    step01 = 1
    step02 = 2
    step03 = 3
    step04 = 4
    step05 = 5
    step06 = 6
    step07 = 7
    step08 = 8
    value = "original"
    total = step01 + step02 + step03 + step04
    total += step05 + step06 + step07 + step08
    return marker, value, total


def beta():
    return "beta-original"
'''

MODULE_V2 = MODULE_V1.replace('value = "original"', 'value = "updated"')
MODULE_V3 = MODULE_V2.replace('return "beta-original"', 'return "beta-updated"')

OTHER = '''"""Helper module."""


def helper():
    return "helped"
'''

CALLER = '''from module import alpha


def run():
    return alpha()
'''

TEST_MODULE = '''from module import alpha


def test_alpha():
    assert alpha()[0] == "ALPHA_TOP_SENTINEL"
'''


def git(repo, *args):
    result = subprocess.run(
        ["git", "-C", str(repo)] + list(args),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError("git %s failed: %s" % (" ".join(args), result.stderr))
    return result.stdout.strip()


def init_repo(repo):
    repo.mkdir(parents=True, exist_ok=True)
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Test User")
    git(repo, "config", "commit.gpgsign", "false")


def write_tree(repo, mapping):
    for name, content in mapping.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content)


def commit_all(repo, message):
    git(repo, "add", "-A")
    git(repo, "commit", "-m", message)


def make_repo(tmp, commits):
    """Build a repo on main from a list of per commit file mappings."""
    repo = Path(tmp) / "repo"
    init_repo(repo)
    for index, mapping in enumerate(commits):
        write_tree(repo, mapping)
        commit_all(repo, "commit %d" % index)
    return repo


def run_extract_cli(repo, out, *args, env=None):
    cmd = [
        sys.executable, str(EXTRACT),
        "--out", str(out),
        "--repo", str(repo),
    ] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def read_manifest(out):
    return json.loads((Path(out) / "manifest.json").read_text())


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        init_repo(self.repo)
        write_tree(self.repo, {
            "module.py": MODULE_V1,
            "other.py": OTHER,
            "caller.py": CALLER,
            "test_module.py": TEST_MODULE,
        })
        commit_all(self.repo, "initial")
        git(self.repo, "checkout", "-b", "feature")
        (self.repo / "module.py").write_text(MODULE_V2)
        (self.repo / "other.py").rename(self.repo / "helper.py")
        commit_all(self.repo, "edit alpha and rename other")
        self.first_feature_commit = git(self.repo, "rev-parse", "HEAD")
        (self.repo / "module.py").write_text(MODULE_V3)
        commit_all(self.repo, "edit beta")

    def tearDown(self):
        self.tmp.cleanup()

    def run_extract(self, *extra):
        out = Path(self.tmp.name) / ("out%d" % len(list(Path(self.tmp.name).glob('out*'))))
        result = run_extract_cli(
            self.repo, out, "--range", "main...feature", *extra
        )
        return result, out


class TestRangeExtraction(Fixture):
    def test_packet_contains_full_enclosing_function(self):
        result, out = self.run_extract()
        self.assertEqual(result.returncode, 0, result.stderr)
        packet = (out / "packet.md").read_text()
        self.assertIn("The pericope for", packet)
        self.assertIn("ALPHA_TOP_SENTINEL", packet)
        self.assertIn('"updated"', packet)

    def test_manifest_verifies_and_records_rename(self):
        result, out = self.run_extract()
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = read_manifest(out)
        self.assertTrue(manifest["verified"], manifest["discrepancies"])
        renamed = [f for f in manifest["files"] if f["path"] == "helper.py"]
        self.assertEqual(len(renamed), 1, manifest["files"])
        self.assertEqual(renamed[0]["status"], "renamed")
        self.assertEqual(renamed[0]["old_path"], "other.py")
        module = [f for f in manifest["files"] if f["path"] == "module.py"]
        self.assertEqual(len(module), 1)
        self.assertGreaterEqual(module[0]["hunks"], 1)
        self.assertEqual(module[0]["additions"], 2)
        self.assertEqual(module[0]["deletions"], 2)

    def test_verify_counts_reports_dropped_file(self):
        result, out = self.run_extract()
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = read_manifest(out)
        mb = manifest["merge_base"]
        head = manifest["head"]
        clean = extract_mod.verify_counts(
            self.repo, mb, head, copy.deepcopy(manifest["files"])
        )
        self.assertEqual(clean, [])
        tampered = copy.deepcopy(manifest["files"])
        tampered = [f for f in tampered if f["path"] != "helper.py"]
        self.assertNotEqual(len(tampered), len(manifest["files"]))
        discrepancies = extract_mod.verify_counts(self.repo, mb, head, tampered)
        self.assertTrue(
            discrepancies,
            "dropping a file from the manifest must produce discrepancies",
        )
        self.assertTrue(
            any("helper.py" in item for item in discrepancies),
            discrepancies,
        )

    def test_verify_counts_reports_forged_line_counts(self):
        result, out = self.run_extract()
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = read_manifest(out)
        tampered = copy.deepcopy(manifest["files"])
        for entry in tampered:
            entry["additions"] = 9999
            entry["deletions"] = 8888
        discrepancies = extract_mod.verify_counts(
            self.repo, manifest["merge_base"], manifest["head"], tampered
        )
        self.assertTrue(
            any("line count mismatch" in item for item in discrepancies),
            discrepancies,
        )

    def test_packet_includes_call_sites_and_test_companions(self):
        result, out = self.run_extract()
        self.assertEqual(result.returncode, 0, result.stderr)
        packet = (out / "packet.md").read_text()
        self.assertIn("Call sites for alpha", packet)
        self.assertIn("caller.py", packet)
        self.assertIn("test_module.py", packet)
        self.assertIn("Test User", packet)

    def test_since_mode_produces_rereview_packet(self):
        result, out = self.run_extract("--since", self.first_feature_commit)
        self.assertEqual(result.returncode, 0, result.stderr)
        packet = (out / "packet.md").read_text()
        self.assertIn("## Re-review", packet)
        self.assertIn("edit beta", packet)
        manifest = read_manifest(out)
        self.assertTrue(manifest["verified"], manifest["discrepancies"])
        self.assertEqual(manifest["since"], self.first_feature_commit)


class TestFunctionOnFirstLine(unittest.TestCase):
    """A function starting on line 1 yields no hunk header context.

    The extractor must still learn its name from the context lines of the
    whole function diff, or T2 and T3 silently lose the function.
    """

    def test_call_sites_found_when_function_starts_the_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, [
                {
                    "m.py": (
                        'def alpha():\n'
                        '    marker = "TOP"\n'
                        "    a = 1\n    b = 2\n    c = 3\n    d = 4\n"
                        '    value = "v1"\n'
                        "    return marker, value\n"
                    ),
                    "caller.py": "from m import alpha\n\nprint(alpha())\n",
                },
                {"m.py": (
                    'def alpha():\n'
                    '    marker = "TOP"\n'
                    "    a = 1\n    b = 2\n    c = 3\n    d = 4\n"
                    '    value = "v2"\n'
                    "    return marker, value\n"
                )},
            ])
            out = Path(tmp) / "out"
            result = run_extract_cli(repo, out, "--commit", "HEAD")
            self.assertEqual(result.returncode, 0, result.stderr)
            packet = (out / "packet.md").read_text()
            self.assertIn("Call sites for alpha", packet)
            self.assertIn("caller.py", packet)


class TestPinnedOutputFormats(unittest.TestCase):
    """Ambient git configuration must not reshape a verified packet."""

    def test_unicode_filename_keeps_its_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, [
                {"caf\u00e9.py": "def a():\n    return 1\n"},
                {"caf\u00e9.py": "def a():\n    return 2\n"},
            ])
            out = Path(tmp) / "out"
            result = run_extract_cli(repo, out, "--range", "HEAD~1..HEAD")
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = read_manifest(out)
            self.assertTrue(manifest["verified"], manifest["discrepancies"])
            self.assertEqual(manifest["files"][0]["path"], "caf\u00e9.py")
            self.assertGreaterEqual(manifest["files"][0]["hunks"], 1)
            self.assertIn("return 2", (out / "packet.md").read_text())

    def test_directory_name_with_space_and_b_fragment(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, [
                {"a b/c.py": "x = 1\n"},
                {"a b/c.py": "x = 2\n"},
            ])
            out = Path(tmp) / "out"
            result = run_extract_cli(repo, out, "--range", "HEAD~1..HEAD")
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = read_manifest(out)
            self.assertTrue(manifest["verified"], manifest["discrepancies"])
            self.assertIn("x = 2", (out / "packet.md").read_text())

    def test_noprefix_and_colour_config_do_not_hide_the_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, [
                {"mod.py": "v = 'v1'\n"},
                {"mod.py": "v = 'v2'\n"},
            ])
            git(repo, "config", "diff.noprefix", "true")
            git(repo, "config", "color.ui", "always")
            out = Path(tmp) / "out"
            result = run_extract_cli(repo, out, "--range", "HEAD~1..HEAD")
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = read_manifest(out)
            self.assertTrue(manifest["verified"], manifest["discrepancies"])
            self.assertIn("'v2'", (out / "packet.md").read_text())

    def test_external_diff_driver_is_not_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, [
                {"mod.py": "v = 'v1'\n"},
                {"mod.py": "v = 'v2'\n"},
            ])
            git(repo, "config", "diff.external", "/bin/true")
            out = Path(tmp) / "out"
            result = run_extract_cli(repo, out, "--range", "HEAD~1..HEAD")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("'v2'", (out / "packet.md").read_text())

    def test_textconv_filter_is_not_applied(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            init_repo(repo)
            script = Path(tmp) / "conv.sh"
            script.write_text("#!/bin/sh\necho HIDDEN\n")
            script.chmod(0o755)
            write_tree(repo, {
                ".gitattributes": "*.py diff=drv\n",
                "mod.py": "v = 'v1'\n",
            })
            commit_all(repo, "one")
            git(repo, "config", "diff.drv.textconv", str(script))
            write_tree(repo, {"mod.py": "v = 'v2'\n"})
            commit_all(repo, "two")
            out = Path(tmp) / "out"
            result = run_extract_cli(repo, out, "--range", "HEAD~1..HEAD")
            self.assertEqual(result.returncode, 0, result.stderr)
            packet = (out / "packet.md").read_text()
            self.assertIn("'v2'", packet)
            self.assertNotIn("HIDDEN", packet)


class TestBinaryAndAttributeMarking(unittest.TestCase):
    def test_binary_file_gets_a_placeholder_not_a_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, [
                {"a.py": "x = 1\n", "blob.bin": bytes(range(256))},
                {"a.py": "x = 2\n", "blob.bin": bytes(range(255, -1, -1))},
            ])
            out = Path(tmp) / "out"
            result = run_extract_cli(repo, out, "--range", "HEAD~1..HEAD")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            manifest = read_manifest(out)
            self.assertTrue(manifest["verified"], manifest["discrepancies"])
            blob = [f for f in manifest["files"] if f["path"] == "blob.bin"]
            self.assertEqual(len(blob), 1)
            self.assertTrue(blob[0]["binary"])
            self.assertIn("256 bytes", (out / "packet.md").read_text())
            self.assertTrue(
                any(e["path"] == "blob.bin" for e in manifest["exclusions"])
            )

    def test_latin1_source_does_not_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, [
                {"legacy.py": b"# caf\xe9\nx = 1\n"},
                {"legacy.py": b"# caf\xe9\nx = 2\n"},
            ])
            out = Path(tmp) / "out"
            result = run_extract_cli(repo, out, "--range", "HEAD~1..HEAD")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertTrue(read_manifest(out)["verified"])

    def test_attribute_binary_marking_over_text_is_counted_as_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, [
                {".gitattributes": "mod.py binary\n", "mod.py": "v = 'v1'\n"},
                {"mod.py": "v = 'v2'\n"},
            ])
            out = Path(tmp) / "out"
            result = run_extract_cli(repo, out, "--range", "HEAD~1..HEAD")
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = read_manifest(out)
            self.assertTrue(manifest["verified"], manifest["discrepancies"])
            mod = [f for f in manifest["files"] if f["path"] == "mod.py"][0]
            self.assertEqual(mod["additions"], 1)
            self.assertEqual(mod["deletions"], 1)
            self.assertGreaterEqual(mod["hunks"], 1)
            self.assertIn("'v2'", (out / "packet.md").read_text())
            self.assertTrue(
                any(
                    e["path"] == "mod.py" and e["shown_as_text"]
                    for e in manifest["exclusions"]
                ),
                manifest["exclusions"],
            )


class TestShallowAndRootCommits(unittest.TestCase):
    def test_shallow_clone_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = make_repo(tmp, [{"a.py": "x = 1\n"}, {"a.py": "x = 2\n"}])
            shallow = Path(tmp) / "shallow"
            subprocess.run(
                ["git", "clone", "-q", "--depth", "1",
                 "file://" + str(src), str(shallow)],
                check=True, capture_output=True, text=True,
            )
            out = Path(tmp) / "out"
            result = run_extract_cli(shallow, out, "--commit", "HEAD")
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("shallow", result.stderr)

    def test_root_commit_records_no_merge_base(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, [{"a.py": "x = 1\n"}, {"a.py": "x = 2\n"}])
            root = git(repo, "rev-list", "--max-parents=0", "HEAD")
            out = Path(tmp) / "out"
            result = run_extract_cli(repo, out, "--commit", root)
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = read_manifest(out)
            self.assertTrue(manifest["verified"], manifest["discrepancies"])
            self.assertIsNone(manifest["merge_base"])
            self.assertIsNone(manifest["base"])


FAKE_GH_VIEW = '''#!/usr/bin/env python3
import json
import sys

if sys.argv[1:3] == ["pr", "view"]:
    print(json.dumps({
        "baseRefOid": __BASE__,
        "headRefOid": __HEAD__,
        "baseRefName": "main",
        "headRefName": "feature",
        "title": "Improve alpha",
        "body": "Implements the plan in https://example.com/spec "
                "and closes #42.",
    }))
elif sys.argv[1:3] == ["pr", "list"]:
    print(json.dumps([{
        "number": 5, "title": "Earlier work", "state": "MERGED",
        "files": [{"path": "module.py"}],
    }]))
'''


def install_fake_gh(tmp, base_oid, head_oid):
    bindir = Path(tmp) / "bin"
    bindir.mkdir(exist_ok=True)
    script = FAKE_GH_VIEW.replace("__BASE__", json.dumps(base_oid))
    script = script.replace("__HEAD__", json.dumps(head_oid))
    gh = bindir / "gh"
    gh.write_text(script)
    gh.chmod(0o755)
    env = dict(os.environ)
    env["PATH"] = str(bindir) + os.pathsep + env["PATH"]
    return env


class TestPullRequestMode(Fixture):
    def test_pr_packet_carries_title_body_and_spec_reference(self):
        base = git(self.repo, "rev-parse", "main")
        head = git(self.repo, "rev-parse", "feature")
        env = install_fake_gh(self.tmp.name, base, head)
        out = Path(self.tmp.name) / "prout"
        result = run_extract_cli(self.repo, out, "--pr", "7", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        packet = (out / "packet.md").read_text()
        self.assertIn("Pull request #7: Improve alpha", packet)
        self.assertIn("https://example.com/spec", packet)
        self.assertIn("#42", packet)
        manifest = read_manifest(out)
        self.assertTrue(manifest["verified"], manifest["discrepancies"])
        self.assertEqual(manifest["pr"]["title"], "Improve alpha")
        self.assertIn(
            "https://example.com/spec", manifest["pr"]["spec_references"]
        )
        self.assertIn("#5 Earlier work", packet)

    def test_pr_with_unfetched_head_fails_loudly(self):
        base = git(self.repo, "rev-parse", "main")
        env = install_fake_gh(
            self.tmp.name, base, "1111111111111111111111111111111111111111"
        )
        out = Path(self.tmp.name) / "prout"
        result = run_extract_cli(self.repo, out, "--pr", "7", env=env)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("not in the local clone", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        manifest = read_manifest(out)
        self.assertFalse(manifest["verified"])


class TestBudget(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = make_repo(self.tmp.name, [
            {
                "module.py": MODULE_V1,
                "caller.py": CALLER,
                "test_module.py": TEST_MODULE,
            },
            {"module.py": MODULE_V2},
        ])

    def tearDown(self):
        self.tmp.cleanup()

    def test_budget_that_fits_keeps_every_tier(self):
        out = Path(self.tmp.name) / "fits"
        result = run_extract_cli(
            self.repo, out, "--range", "HEAD~1..HEAD", "--budget", "100000"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = read_manifest(out)
        for tier in ("T0", "T1", "T2", "T3"):
            self.assertEqual(manifest["tiers"][tier]["state"], "included")
        self.assertEqual(manifest["tiers"]["T1"]["files"], 1)
        self.assertEqual(manifest["tiers"]["T2"]["files"], 1)

    def test_budget_sheds_t3_then_t2_and_stays_inside(self):
        full_out = Path(self.tmp.name) / "full"
        result = run_extract_cli(self.repo, full_out, "--range", "HEAD~1..HEAD")
        self.assertEqual(result.returncode, 0, result.stderr)
        full_tokens = len((full_out / "packet.md").read_bytes()) // 4
        out = Path(self.tmp.name) / "shed"
        result = run_extract_cli(
            self.repo, out, "--range", "HEAD~1..HEAD",
            "--budget", str(full_tokens - 40),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        packet_tokens = len((out / "packet.md").read_bytes()) // 4
        self.assertLessEqual(packet_tokens, full_tokens - 40)
        manifest = read_manifest(out)
        self.assertEqual(manifest["tiers"]["T3"]["state"], "dropped")
        self.assertGreater(manifest["tiers"]["T3"]["estimated_tokens"], 0)
        self.assertTrue(manifest["budget"]["dropped"])

    def test_budget_below_the_change_itself_fails(self):
        out = Path(self.tmp.name) / "tiny"
        result = run_extract_cli(
            self.repo, out, "--range", "HEAD~1..HEAD", "--budget", "10"
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("never truncated", result.stderr)
        self.assertFalse((out / "packet.md").exists())
        self.assertFalse(read_manifest(out)["verified"])


class TestTierSelection(Fixture):
    def test_tiers_selector_limits_the_packet(self):
        result, out = self.run_extract("--tiers", "0-1")
        self.assertEqual(result.returncode, 0, result.stderr)
        packet = (out / "packet.md").read_text()
        self.assertIn("Not selected for this run", packet)
        self.assertNotIn("Call sites for alpha", packet)
        manifest = read_manifest(out)
        self.assertEqual(manifest["tiers"]["T2"]["state"], "not selected")
        self.assertEqual(manifest["tiers"]["T3"]["state"], "not selected")
        self.assertEqual(manifest["selected_tiers"], ["T0", "T1"])

    def test_tiers_selector_cannot_drop_the_change(self):
        out = Path(self.tmp.name) / "bad"
        result = run_extract_cli(
            self.repo, out, "--range", "main...feature", "--tiers", "3"
        )
        self.assertEqual(result.returncode, 2, result.stderr)


class TestOutputReceipts(Fixture):
    def test_failed_run_replaces_the_previous_verified_packet(self):
        result, out = self.run_extract()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(read_manifest(out)["verified"])
        failed = run_extract_cli(
            self.repo, out, "--range", "main...feature", "--budget", "1"
        )
        self.assertEqual(failed.returncode, 2, failed.stderr)
        self.assertFalse((out / "packet.md").exists())
        self.assertFalse(read_manifest(out)["verified"])

    def test_empty_change_writes_a_failure_receipt(self):
        out = Path(self.tmp.name) / "empty"
        result = run_extract_cli(
            self.repo, out, "--range", "feature..feature"
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertFalse(read_manifest(out)["verified"])

    def test_bad_ref_fails_without_a_traceback(self):
        out = Path(self.tmp.name) / "badref"
        result = run_extract_cli(
            self.repo, out, "--range", "nope..feature"
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn("Traceback", result.stderr)


class TestFailClosedEndToEnd(Fixture):
    def test_failed_verification_exits_3_with_unverified_manifest(self):
        out = Path(self.tmp.name) / "forced"
        original = extract_mod.verify_counts
        extract_mod.verify_counts = (
            lambda *a: ["forced discrepancy for the fail closed test"]
        )
        try:
            with redirect_stderr(io.StringIO()) as captured:
                code = extract_mod.main([
                    "--range", "main...feature",
                    "--out", str(out),
                    "--repo", str(self.repo),
                ])
        finally:
            extract_mod.verify_counts = original
        self.assertEqual(code, 3)
        manifest = read_manifest(out)
        self.assertFalse(manifest["verified"])
        self.assertIn(
            "forced discrepancy for the fail closed test",
            manifest["discrepancies"],
        )
        self.assertIn("forced discrepancy", captured.getvalue())


class TestReReviewSemantics(unittest.TestCase):
    def test_unrelated_since_produces_a_scoped_empty_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, [
                {"a.py": "x = 1\n"},
                {"a.py": "x = 2\n"},
            ])
            git(repo, "checkout", "--orphan", "orphan")
            git(repo, "commit", "--allow-empty", "-m", "orphan")
            orphan = git(repo, "rev-parse", "HEAD")
            git(repo, "checkout", "main")
            out = Path(tmp) / "out"
            result = run_extract_cli(
                repo, out, "--range", "HEAD~1..HEAD", "--since", orphan
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            packet = (out / "packet.md").read_text()
            self.assertIn("shares no usable history", packet)
            self.assertNotIn("Commits since the previous review", packet)

    def test_since_alone_is_not_a_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, [{"a.py": "x = 1\n"}])
            out = Path(tmp) / "out"
            result = run_extract_cli(repo, out, "--since", "HEAD")
            self.assertEqual(result.returncode, 2, result.stderr)

    def test_findings_accounting_marks_addressed_and_unaddressed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, [
                {"mod.py": "a = 1\nb = 2\nc = 3\nd = 4\ne = 5\n"},
                {"note.txt": "a note\n"},
            ])
            previous = git(repo, "rev-parse", "HEAD")
            write_tree(repo, {"mod.py": "a = 1\nb = 2\nc = 3\nd = 4\ne = 55\n"})
            commit_all(repo, "fix the e line")
            findings = Path(tmp) / "findings.txt"
            findings.write_text(
                "mod.py:5: the e line is wrong\n"
                "mod.py:2: question about the b line\n"
            )
            out = Path(tmp) / "out"
            result = run_extract_cli(
                repo, out, "--range", "HEAD~2..HEAD",
                "--since", previous, "--findings", str(findings),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            packet = (out / "packet.md").read_text()
            self.assertIn("Prior findings accounting", packet)
            self.assertIn("Findings addressed: 1 of 2", packet)
            self.assertIn("addressed, the anchored lines changed", packet)
            self.assertIn(
                "unaddressed, the anchored lines are unchanged", packet
            )


class TestPathEdgeCases(unittest.TestCase):
    def test_call_sites_found_for_colon_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, [
                {
                    "m.py": "def beta():\n    return 1\n",
                    "we:ird.py": (
                        "from m import beta\n\n\ndef use():\n    return beta()\n"
                    ),
                },
                {"m.py": "def beta():\n    return 2\n"},
            ])
            out = Path(tmp) / "out"
            result = run_extract_cli(repo, out, "--range", "HEAD~1..HEAD")
            self.assertEqual(result.returncode, 0, result.stderr)
            packet = (out / "packet.md").read_text()
            self.assertIn("Call sites for beta", packet)
            self.assertIn("we:ird.py", packet)

    def test_crlf_bytes_survive_into_the_packet(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, [
                {"crlf.py": b"a = 1\r\nb = 2\r\n"},
                {"crlf.py": b"a = 9\r\nb = 2\r\n"},
            ])
            out = Path(tmp) / "out"
            result = run_extract_cli(repo, out, "--range", "HEAD~1..HEAD")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(b"a = 9\r\n", (out / "packet.md").read_bytes())


class TestTierContent(unittest.TestCase):
    def test_t2_carries_imports_and_definitions(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, [
                {
                    "module.py": (
                        "import os\n\n\ndef alpha():\n    return os.sep\n"
                    ),
                    "defs.py": "def alpha():\n    return 'other'\n",
                },
                {"module.py": (
                    "import os\n\n\ndef alpha():\n    return os.sep + 'x'\n"
                )},
            ])
            out = Path(tmp) / "out"
            result = run_extract_cli(repo, out, "--range", "HEAD~1..HEAD")
            self.assertEqual(result.returncode, 0, result.stderr)
            packet = (out / "packet.md").read_text()
            self.assertIn("### Imports of the changed files", packet)
            self.assertIn("import os", packet)
            self.assertIn("### Definitions of changed names elsewhere", packet)
            self.assertIn("defs.py", packet)

    def test_prior_prs_degrade_honestly_without_github(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, [
                {"module.py": MODULE_V1},
                {"module.py": MODULE_V2},
            ])
            bindir = Path(tmp) / "bin"
            bindir.mkdir()
            (bindir / "git").symlink_to(subprocess.run(
                ["which", "git"], capture_output=True, text=True
            ).stdout.strip())
            env = dict(os.environ)
            env["PATH"] = str(bindir)
            out = Path(tmp) / "out"
            result = run_extract_cli(
                repo, out, "--range", "HEAD~1..HEAD", env=env
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            packet = (out / "packet.md").read_text()
            self.assertIn("Prior pull requests are unavailable", packet)


if __name__ == "__main__":
    unittest.main()
