"""Regression tests for the packet check as a real verifier.

Rounds 2, 7 and 10 of the audit program showed the shipped packet
check stamping fabricated packets as verified. It never recounted
anything, never read the manifest counts, accepted manifests with
missing or forged keys, compared only the head of a range, and
rejected genuine packets whose filenames carry one of three
Unicode line separators, because its private display path copy
lacked the escapes the extractor prints. Every fabrication in
those records is rebuilt here against a genuine packet and must
now fail the check, and every genuine packet shape must still
pass. The fabrication tests fail against the pre fix checker,
which is the proof they test the fix and not the fixture.
"""

import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTRACT_PATH = (
    ROOT / ".agents" / "skills" / "recognitio" / "scripts" / "extract.py"
)
CHECK_PATH = ROOT / "scripts" / "check_packet.py"
SCHEMA_PATH = ROOT / "scripts" / "packet-manifest.schema.json"


def load_at(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check_mod = load_at(CHECK_PATH, "check_packet_verifier_side")
extract_mod = load_at(EXTRACT_PATH, "extract_for_verifier_tests")


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


def extract_packet(repo, out, *extra, env=None):
    with redirect_stderr(io.StringIO()):
        if env is None:
            code = extract_mod.main([
                "--repo", str(repo), "--out", str(out), *extra,
            ])
        else:
            original = os.environ
            os.environ = env
            try:
                code = extract_mod.main([
                    "--repo", str(repo), "--out", str(out), *extra,
                ])
            finally:
                os.environ = original
    if code != 0:
        raise AssertionError("extractor exited %d for %s" % (code, extra))
    return out


class VerifierFixture(unittest.TestCase):
    """A three commit repository and its genuine packets."""

    def setUp(self):
        self.tmp = RetryingTemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        init_repo(self.repo)
        (self.repo / "a.py").write_text(
            "def a():\n    return 1\n", encoding="utf-8"
        )
        self.sha_a = commit_all(self.repo, "A")
        (self.repo / "b.py").write_text(
            "def b():\n    return 1\n", encoding="utf-8"
        )
        self.sha_b = commit_all(self.repo, "B")
        (self.repo / "b.py").write_text(
            "def b():\n    return 2\n", encoding="utf-8"
        )
        (self.repo / "c.py").write_text(
            "def c():\n    return 1\n", encoding="utf-8"
        )
        self.head = commit_all(self.repo, "C")
        self.genuine = extract_packet(
            self.repo, Path(self.tmp.name) / "genuine",
            "--range", "HEAD~1..HEAD",
        )
        self.full = extract_packet(
            self.repo, Path(self.tmp.name) / "full",
            "--range", "HEAD~2..HEAD",
        )

    def clone(self, name, source=None):
        out = Path(self.tmp.name) / name
        shutil.copytree(source or self.genuine, out)
        return out

    def manifest(self, out):
        return json.loads((out / "manifest.json").read_text(encoding="utf-8"))

    def save_manifest(self, out, manifest):
        (out / "manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )

    def packet_text(self, out):
        return (out / "packet.md").read_text(encoding="utf-8")

    def save_packet(self, out, text):
        (out / "packet.md").write_text(text, encoding="utf-8")

    def run_check(self, out, *extra):
        with redirect_stderr(io.StringIO()):
            return check_mod.main(
                [str(out), "--repo", str(self.repo)] + list(extra)
            )


class TestFabricationBattery(VerifierFixture):
    """Every fabrication from rounds 2, 7 and 10 must now fail."""

    def test_the_genuine_packets_pass(self):
        self.assertEqual(self.run_check(self.clone("g1")), 0)
        self.assertEqual(self.run_check(self.clone("g2", self.full)), 0)

    def test_a_hand_written_fabricated_packet_fails(self):
        fake = Path(self.tmp.name) / "fake"
        fake.mkdir()
        (fake / "packet.md").write_text(
            "## T0 Triage\n\nWords.\n\n## T1 The change\n\n### mod.py\n\n"
            "Status: modified\n\nFabricated diff, no relation to the "
            "repo.\n\n## T2 Companions\n\nWords.\n\n## T3 History\n\n"
            "Words.\n\n## Verification recount\n\nRecount passed\n",
            encoding="utf-8",
        )
        (fake / "manifest.json").write_text(json.dumps({
            "verified": True,
            "head": self.head,
            "sections": [
                "## T0 Triage", "## T1 The change", "## T2 Companions",
                "## T3 History", "## Verification recount",
            ],
            "tiers": {
                "T2": {"included": True}, "T3": {"included": True},
            },
            "files": [{"path": "mod.py"}],
        }), encoding="utf-8")
        self.assertEqual(self.run_check(fake), 1)

    def test_a_packet_with_its_diff_evidence_stripped_fails(self):
        out = self.clone("stripped")
        lines = self.packet_text(out).split("\n")
        kept = [
            line for line in lines
            if not (line.startswith("+") or line.startswith("-"))
            or line.startswith("### ") or line.startswith("## ")
        ]
        self.save_packet(out, "\n".join(kept))
        self.assertEqual(self.run_check(out), 1)

    def test_a_manifest_without_files_or_tiers_keys_fails(self):
        out = self.clone("nokeys")
        manifest = self.manifest(out)
        del manifest["files"]
        del manifest["tiers"]
        self.save_manifest(out, manifest)
        self.assertEqual(self.run_check(out), 1)

    def test_a_verified_manifest_with_discrepancies_fails(self):
        out = self.clone("discrep")
        manifest = self.manifest(out)
        manifest["discrepancies"] = [
            "file in manifest but not in recount: b.py"
        ]
        manifest["error"] = "recount failed"
        self.save_manifest(out, manifest)
        self.assertEqual(self.run_check(out), 1)

    def test_an_unreceipted_extra_file_section_fails(self):
        out = self.clone("extra")
        text = self.packet_text(out)
        text = text.replace(
            "## T2 Companions",
            "### invented.py\n\nStatus: added\n\nFake diff.\n\n"
            "## T2 Companions",
            1,
        )
        self.save_packet(out, text)
        self.assertEqual(self.run_check(out), 1)

    def test_a_rewritten_diff_line_fails(self):
        out = self.clone("tamperline")
        text = self.packet_text(out)
        self.assertIn("return 2", text)
        self.save_packet(out, text.replace("return 2", "return 999"))
        self.assertEqual(self.run_check(out), 1)

    def test_a_rewritten_contents_sentence_fails(self):
        out = self.clone("tampercontents")
        text = self.packet_text(out)
        new, count = re.subn(
            r"This packet holds [^\n]*",
            "This packet holds 9 files, 99 hunks, 99 added lines "
            "and 99 deleted lines",
            text,
            count=1,
        )
        self.assertEqual(count, 1)
        self.save_packet(out, new)
        self.assertEqual(self.run_check(out), 1)

    def test_rewritten_manifest_counts_fail(self):
        out = self.clone("tampercounts")
        manifest = self.manifest(out)
        manifest["files"][0]["additions"] = 999
        manifest["files"][0]["hunks"] = 42
        self.save_manifest(out, manifest)
        self.assertEqual(self.run_check(out), 1)

    def test_a_deleted_companion_subsection_fails(self):
        out = self.clone("tampercompanion")
        text = self.packet_text(out)
        start = text.find("### Call sites")
        if start == -1:
            start = text.find("### Imports")
        end = text.find("\n## ", start)
        self.assertNotEqual(start, -1)
        self.assertNotEqual(end, -1)
        self.save_packet(out, text[:start] + text[end + 1:])
        self.assertEqual(self.run_check(out), 1)

    def test_a_forged_header_head_line_fails(self):
        out = self.clone("tamperheader")
        text = self.packet_text(out)
        new, count = re.subn(
            r"Head: [0-9a-f]{40}", "Head: " + "0" * 40, text, count=1
        )
        self.assertEqual(count, 1)
        self.save_packet(out, new)
        self.assertEqual(self.run_check(out), 1)

    def test_a_repeated_verified_key_fails(self):
        out = self.clone("dupkey")
        raw = (out / "manifest.json").read_text(encoding="utf-8")
        raw = raw.replace(
            '"verified": true',
            '"verified": false, "verified": true',
            1,
        )
        self.assertIn('"verified": false, "verified": true', raw)
        (out / "manifest.json").write_text(raw, encoding="utf-8")
        self.assertEqual(self.run_check(out), 1)

    def manifest_edit_fails(self, name, edit):
        out = self.clone(name)
        manifest = self.manifest(out)
        edit(manifest)
        self.save_manifest(out, manifest)
        self.assertEqual(self.run_check(out), 1)

    def test_an_extra_top_level_key_fails(self):
        self.manifest_edit_fails(
            "edit-extra", lambda m: m.update({"surprise": 1})
        )

    def test_file_records_stripped_to_the_path_fail(self):
        self.manifest_edit_fails(
            "edit-stripped",
            lambda m: m.update(
                {"files": [{"path": e["path"]} for e in m["files"]]}
            ),
        )

    def test_file_counts_rewritten_to_9999_fail(self):
        def edit(manifest):
            for entry in manifest["files"]:
                entry["additions"] = 9999
                entry["hunks"] = 9999
        self.manifest_edit_fails("edit-counts", edit)

    def test_an_emptied_tiers_object_fails(self):
        self.manifest_edit_fails(
            "edit-tiers", lambda m: m.update({"tiers": {}})
        )

    def test_a_zeroed_budget_fails(self):
        self.manifest_edit_fails(
            "edit-budget",
            lambda m: m.update({
                "budget": {
                    "budget_tokens": None,
                    "estimated_tokens": 0,
                    "dropped": [],
                }
            }),
        )

    def test_replaced_version_and_extractor_strings_fail(self):
        self.manifest_edit_fails(
            "edit-identity",
            lambda m: m.update({"version": "9.9.9", "extractor": "forged"}),
        )

    def test_a_zeroed_base_and_merge_base_fail(self):
        self.manifest_edit_fails(
            "edit-refs",
            lambda m: m.update({"base": "0" * 40, "merge_base": "0" * 40}),
        )

    def test_a_replaced_mode_and_label_fail(self):
        self.manifest_edit_fails(
            "edit-mode",
            lambda m: m.update({"mode": "pr", "label": "pull request 99"}),
        )

    def test_a_same_length_companion_tier_edit_fails(self):
        out = self.clone("samelength")
        text = self.packet_text(out)
        start = text.index("## T2 Companions")
        pos = text.index("deterministic", start)
        self.save_packet(
            out, text[:pos] + "deterministiz" + text[pos + 13:]
        )
        self.assertEqual(self.run_check(out), 1)

    def test_tier_file_counts_tampered_with_the_receipt_fail(self):
        out = self.clone("tierfiles")
        manifest = self.manifest(out)
        manifest["tiers"]["T2"]["files"] = 99
        self.save_manifest(out, manifest)
        text = self.packet_text(out)
        new, count = re.subn(
            r"T2 included at about ([0-9]+) tokens across [0-9]+ files",
            r"T2 included at about \1 tokens across 99 files",
            text,
            count=1,
        )
        self.assertEqual(count, 1)
        self.save_packet(out, new)
        self.assertEqual(self.run_check(out), 1)

    def test_a_merge_base_that_is_not_the_merge_base_fails(self):
        out = self.clone("wrongmb", self.full)
        manifest = self.manifest(out)
        manifest["merge_base"] = manifest["head"]
        self.save_manifest(out, manifest)
        self.assertEqual(self.run_check(out), 1)

    def test_emptied_exclusions_fail_on_a_packet_that_has_one(self):
        repo = Path(self.tmp.name) / "binrepo"
        init_repo(repo)
        (repo / "blob.bin").write_bytes(b"\x00\x01\x02")
        (repo / "m.py").write_text("x = 1\n", encoding="utf-8")
        commit_all(repo, "one")
        (repo / "blob.bin").write_bytes(b"\x00\x03\x04\x05")
        (repo / "m.py").write_text("x = 2\n", encoding="utf-8")
        commit_all(repo, "two")
        out = extract_packet(
            repo, Path(self.tmp.name) / "binpkt", "--range", "HEAD~1..HEAD"
        )
        manifest = self.manifest(out)
        self.assertTrue(manifest["exclusions"])
        with redirect_stderr(io.StringIO()):
            self.assertEqual(
                check_mod.main([str(out), "--repo", str(repo)]), 0
            )
        manifest["exclusions"] = []
        self.save_manifest(out, manifest)
        with redirect_stderr(io.StringIO()):
            self.assertEqual(
                check_mod.main([str(out), "--repo", str(repo)]), 1
            )


class TestDirectorySealingAndEncoding(VerifierFixture):
    """The directory pair, its encoding and its recorded command.

    Round 23 finding F7 showed the check following packet and
    manifest links separately and ignoring a nested packet inside
    a genuine one. Round 10 finding 4 showed a packet carrying a
    non UTF-8 filename byte passing while no UTF-8 reader could
    open it. Round 10 check 6 listed the recorded command among
    the manifest fields no check ever read back. Each test below
    builds a pair whose content is genuine, so the new rule is
    the only thing that can fail it.
    """

    def test_a_packet_reached_through_a_link_fails(self):
        elsewhere = self.clone("elsewhere")
        out = Path(self.tmp.name) / "linkpair"
        out.mkdir()
        shutil.copy(self.genuine / "manifest.json", out / "manifest.json")
        (out / "packet.md").symlink_to(elsewhere / "packet.md")
        self.assertEqual(self.run_check(out), 1)

    def test_a_manifest_reached_through_a_link_fails(self):
        elsewhere = self.clone("elsewhere2")
        out = Path(self.tmp.name) / "linkpair2"
        out.mkdir()
        shutil.copy(self.genuine / "packet.md", out / "packet.md")
        (out / "manifest.json").symlink_to(elsewhere / "manifest.json")
        self.assertEqual(self.run_check(out), 1)

    def test_a_nested_packet_directory_fails(self):
        out = self.clone("nesteddir")
        shutil.copytree(self.full, out / "inner")
        self.assertEqual(self.run_check(out), 1)

    def test_an_extra_file_beside_the_pair_fails(self):
        out = self.clone("extradir")
        (out / "notes.md").write_text("stale\n", encoding="utf-8")
        self.assertEqual(self.run_check(out), 1)

    def test_a_packet_dir_reached_through_a_link_passes(self):
        real = self.clone("realdir")
        link = Path(self.tmp.name) / "dirlink"
        link.symlink_to(real, target_is_directory=True)
        self.assertEqual(self.run_check(link), 0)

    def test_a_non_utf8_filename_packet_fails(self):
        repo = Path(self.tmp.name) / "nonutf8repo"
        init_repo(repo)
        (repo / "plain.py").write_text("x = 1\n", encoding="utf-8")
        commit_all(repo, "one")
        fd = os.open(
            str(repo).encode() + b"/" + b"bad\xfffile.py",
            os.O_CREAT | os.O_WRONLY,
        )
        os.write(fd, b"y = 1\n")
        os.close(fd)
        commit_all(repo, "two")
        out = extract_packet(
            repo, Path(self.tmp.name) / "nonutf8pkt",
            "--range", "HEAD~1..HEAD",
        )
        with self.assertRaises(UnicodeDecodeError):
            (out / "packet.md").read_bytes().decode("utf-8")
        with redirect_stderr(io.StringIO()):
            self.assertEqual(
                check_mod.main([str(out), "--repo", str(repo)]), 1
            )

    def test_a_forged_command_range_fails(self):
        out = self.clone("cmdforge")
        manifest = self.manifest(out)
        manifest["command"] = ["extract.py", "--range", "FORGED"]
        self.save_manifest(out, manifest)
        self.assertEqual(self.run_check(out), 1)

    def test_a_command_naming_the_wrong_mode_fails(self):
        out = self.clone("cmdmode")
        manifest = self.manifest(out)
        manifest["command"] = ["extract.py", "--commit", self.head]
        self.save_manifest(out, manifest)
        self.assertEqual(self.run_check(out), 1)

    def test_a_command_range_naming_another_head_fails(self):
        out = self.clone("cmdhead")
        manifest = self.manifest(out)
        manifest["command"] = [
            "extract.py", "--range", "%s..%s" % (self.sha_b, self.sha_b),
        ]
        self.save_manifest(out, manifest)
        self.assertEqual(self.run_check(out), 1)


class TestSubrangeStamp(VerifierFixture):
    """A subrange packet must not stamp for a wider range."""

    def test_the_subrange_packet_stamps_for_its_own_range(self):
        self.assertEqual(self.run_check(self.clone("sub-own")), 0)

    def test_the_subrange_packet_fails_for_the_wider_range(self):
        full_manifest = self.manifest(self.full)
        out = self.clone("sub-wide")
        self.assertEqual(
            self.run_check(
                out,
                "--expect-base", full_manifest["base"],
                "--expect-merge-base", full_manifest["merge_base"],
            ),
            1,
        )

    def test_the_full_packet_stamps_for_the_range_it_names(self):
        full_manifest = self.manifest(self.full)
        out = self.clone("full-named", self.full)
        self.assertEqual(
            self.run_check(
                out,
                "--expect-base", full_manifest["base"],
                "--expect-merge-base", full_manifest["merge_base"],
            ),
            0,
        )

    def test_the_full_packet_fails_for_a_narrower_expectation(self):
        sub_manifest = self.manifest(self.genuine)
        out = self.clone("full-narrow", self.full)
        self.assertEqual(
            self.run_check(
                out,
                "--expect-base", sub_manifest["base"],
                "--expect-merge-base", sub_manifest["merge_base"],
            ),
            1,
        )


class TestGenuineShapes(VerifierFixture):
    """Genuine packets of every shape the extractor makes must pass."""

    def check_repo_packet(self, repo, out, *extra):
        with redirect_stderr(io.StringIO()):
            return check_mod.main([str(out), "--repo", str(repo)])

    def test_a_tier_selection_packet_passes(self):
        out = extract_packet(
            self.repo, Path(self.tmp.name) / "tiersel",
            "--range", "HEAD~1..HEAD", "--tiers", "0,1",
        )
        self.assertEqual(self.check_repo_packet(self.repo, out), 0)

    def test_a_budget_dropped_packet_passes(self):
        out = extract_packet(
            self.repo, Path(self.tmp.name) / "budgeted",
            "--range", "HEAD~2..HEAD", "--budget", "800",
        )
        manifest = self.manifest(out)
        self.assertTrue(manifest["budget"]["dropped"])
        self.assertEqual(self.check_repo_packet(self.repo, out), 0)

    def test_a_rereview_packet_passes(self):
        findings = Path(self.tmp.name) / "findings.txt"
        findings.write_text(
            "b.py:2: the value changed\n", encoding="utf-8"
        )
        out = extract_packet(
            self.repo, Path(self.tmp.name) / "rereview",
            "--range", "HEAD~1..HEAD", "--since", "HEAD~2",
            "--findings", str(findings),
        )
        self.assertIn("## Re-review", self.manifest(out)["sections"])
        self.assertEqual(self.check_repo_packet(self.repo, out), 0)

    def test_a_root_commit_packet_passes(self):
        out = extract_packet(
            self.repo, Path(self.tmp.name) / "rootpkt",
            "--commit", self.sha_a,
        )
        clone = Path(self.tmp.name) / "rootrepo"
        subprocess.run(
            ["git", "clone", "-q", str(self.repo), str(clone)], check=True
        )
        git(clone, "checkout", "-q", self.sha_a)
        self.assertEqual(self.check_repo_packet(clone, out), 0)

    def test_a_rename_packet_passes(self):
        repo = Path(self.tmp.name) / "renamerepo"
        init_repo(repo)
        body = "".join(
            "def f%d():\n    return %d\n" % (i, i) for i in range(10)
        )
        (repo / "old.py").write_text(body, encoding="utf-8")
        commit_all(repo, "one")
        git(repo, "mv", "old.py", "new.py")
        (repo / "new.py").write_text(
            body.replace("return 3", "return 33", 1), encoding="utf-8"
        )
        commit_all(repo, "rename")
        out = extract_packet(
            repo, Path(self.tmp.name) / "renamepkt",
            "--range", "HEAD~1..HEAD",
        )
        self.assertEqual(self.manifest(out)["files"][0]["status"], "renamed")
        self.assertEqual(self.check_repo_packet(repo, out), 0)

    def test_a_typechange_packet_passes(self):
        repo = Path(self.tmp.name) / "typechangerepo"
        init_repo(repo)
        (repo / "a.py").write_text(
            "def a():\n    return 1\n", encoding="utf-8"
        )
        (repo / "thing").write_text("plain text\n", encoding="utf-8")
        commit_all(repo, "one")
        (repo / "thing").unlink()
        (repo / "thing").symlink_to("a.py")
        (repo / "a.py").write_text(
            "def a():\n    return 2\n", encoding="utf-8"
        )
        commit_all(repo, "typechange")
        out = extract_packet(
            repo, Path(self.tmp.name) / "typechangepkt",
            "--range", "HEAD~1..HEAD",
        )
        statuses = {
            entry["path"]: entry["status"]
            for entry in self.manifest(out)["files"]
        }
        self.assertEqual(statuses.get("thing"), "typechange")
        self.assertEqual(self.check_repo_packet(repo, out), 0)

    def test_a_lockfile_placeholder_packet_passes(self):
        repo = Path(self.tmp.name) / "lockrepo"
        init_repo(repo)
        (repo / "package-lock.json").write_text(
            '{"lock": 1}\n', encoding="utf-8"
        )
        (repo / "m.py").write_text("x = 1\n", encoding="utf-8")
        commit_all(repo, "one")
        (repo / "package-lock.json").write_text(
            '{"lock": 2}\n', encoding="utf-8"
        )
        (repo / "m.py").write_text("x = 2\n", encoding="utf-8")
        commit_all(repo, "two")
        out = extract_packet(
            repo, Path(self.tmp.name) / "lockpkt", "--range", "HEAD~1..HEAD"
        )
        self.assertEqual(self.check_repo_packet(repo, out), 0)

    def test_a_crlf_packet_passes(self):
        repo = Path(self.tmp.name) / "crlfrepo"
        init_repo(repo)
        git(repo, "config", "core.autocrlf", "false")
        (repo / "crlf.py").write_bytes(b"one = 1\r\ntwo = 2\r\n")
        commit_all(repo, "one")
        (repo / "crlf.py").write_bytes(b"one = 1\r\ntwo = 22\r\n")
        commit_all(repo, "two")
        out = extract_packet(
            repo, Path(self.tmp.name) / "crlfpkt", "--range", "HEAD~1..HEAD"
        )
        self.assertEqual(self.check_repo_packet(repo, out), 0)

    def test_unicode_separator_packets_pass(self):
        for label, char in (
            ("NEL", "\u0085"), ("LS", "\u2028"), ("PS", "\u2029"),
        ):
            with self.subTest(separator=label):
                repo = Path(self.tmp.name) / ("seprepo-" + label)
                init_repo(repo)
                name = "sep" + char + "file.py"
                (repo / name).write_text("x = 1\n", encoding="utf-8")
                commit_all(repo, "one")
                (repo / name).write_text("x = 2\n", encoding="utf-8")
                commit_all(repo, "two")
                out = extract_packet(
                    repo, Path(self.tmp.name) / ("sepout-" + label),
                    "--range", "HEAD~1..HEAD",
                )
                self.assertEqual(self.check_repo_packet(repo, out), 0)

    def test_a_pull_request_packet_passes(self):
        repo = Path(self.tmp.name) / "prrepo"
        init_repo(repo)
        (repo / "module.py").write_text(
            "def alpha():\n    return 1\n", encoding="utf-8"
        )
        base = commit_all(repo, "base")
        (repo / "module.py").write_text(
            "def alpha():\n    return 2\n", encoding="utf-8"
        )
        head = commit_all(repo, "work")
        bindir = Path(self.tmp.name) / "prbin"
        bindir.mkdir()
        script = (
            "#!/usr/bin/env python3\n"
            "import json, sys\n"
            "if sys.argv[1:3] == ['pr', 'view']:\n"
            "    print(json.dumps({\n"
            "        'baseRefOid': %r, 'headRefOid': %r,\n"
            "        'baseRefName': 'main', 'headRefName': 'feature',\n"
            "        'title': 'Improve alpha', 'body': 'Closes #42.',\n"
            "    }))\n"
            "elif sys.argv[1:3] == ['pr', 'list']:\n"
            "    print(json.dumps([]))\n"
        ) % (base, head)
        gh = bindir / "gh"
        gh.write_text(script, encoding="utf-8")
        gh.chmod(0o755)
        env = dict(os.environ)
        env["PATH"] = str(bindir) + os.pathsep + env["PATH"]
        out = extract_packet(
            repo, Path(self.tmp.name) / "prpkt", "--pr", "7", env=env
        )
        self.assertEqual(self.manifest(out)["mode"], "pr")
        self.assertEqual(self.check_repo_packet(repo, out), 0)


class TestDisplayPathAgreement(unittest.TestCase):
    """The two display path copies must agree on every name.

    The extractor prints packet headings with its copy and the
    checker compares manifest paths with its own, so a name the
    two render differently can never be stamped, or worse, can
    be stamped wrongly. This battery is the single behaviour the
    two copies are held to.
    """

    NAMES = (
        "plain.py",
        "with space.py",
        " leading.py",
        "trailing.py ",
        'quote".py',
        "single'quote.py",
        "back\\slash.py",
        "new\nline.py",
        "carriage\rreturn.py",
        "ta\tb.py",
        "next\u0085line.py",
        "line\u2028separator.py",
        "paragraph\u2029separator.py",
        "vertical\x0btab.py",
        "unit\x1fseparator.py",
        "delete\x7fchar.py",
        "emoji\U0001f600.py",
        "## forged heading.py",
        "a" * 60 + ".py",
        "dir/sub dir/file.py",
    )

    def test_the_two_copies_agree_on_the_battery(self):
        for name in self.NAMES:
            with self.subTest(name=name):
                self.assertEqual(
                    check_mod.display_path(name),
                    extract_mod.display_path(name),
                )

    def test_the_separator_escapes_are_the_extractor_spellings(self):
        self.assertEqual(
            check_mod.display_path("a\u0085b"), "a\\u0085b"
        )
        self.assertEqual(
            check_mod.display_path("a\u2028b"), "a\\u2028b"
        )
        self.assertEqual(
            check_mod.display_path("a\u2029b"), "a\\u2029b"
        )


class TestManifestSchema(unittest.TestCase):
    """The shipped schema and the strict manifest reading."""

    def test_the_schema_ships_and_parses(self):
        schema = check_mod.strict_json_loads(
            SCHEMA_PATH.read_text(encoding="utf-8")
        )
        self.assertEqual(schema["title"], "recognitio packet manifest")
        self.assertIn("files", schema["required"])

    def test_a_genuine_manifest_shape_validates(self):
        manifest = {
            "extractor": "recognitio extract.py",
            "version": extract_mod.EXTRACTOR_VERSION,
            "command": ["extract.py", "--range", "A..B"],
            "created_utc": "2026-10-27T00:00:00+00:00",
            "mode": "range",
            "label": "range A..B",
            "base": "a" * 40,
            "head": "b" * 40,
            "merge_base": "a" * 40,
            "since": None,
            "pr": None,
            "files": [{
                "path": "m.py", "old_path": None, "status": "modified",
                "status_code": "M", "additions": 1, "deletions": 1,
                "hunks": 1, "binary": False, "attribute_text": False,
                "binary_transition": False, "placeholder": None,
                "instruction_file": False,
            }],
            "exclusions": [],
            "selected_tiers": ["T0", "T1", "T2", "T3"],
            "tiers": {
                tier: {
                    "state": "included", "included": True,
                    "estimated_tokens": 10, "emitted_tokens": 10,
                    "files": 1,
                }
                for tier in ("T0", "T1", "T2", "T3")
            },
            "sections": [
                "## T0 Triage", "## T1 The change", "## T2 Companions",
                "## T3 History", "## Verification recount",
            ],
            "budget": {
                "budget_tokens": None, "estimated_tokens": 100,
                "dropped": [],
            },
            "cap_notes": [],
            "verified": True,
            "discrepancies": [],
        }
        self.assertEqual(check_mod.manifest_schema_problems(manifest), [])

    def test_schema_rejects_a_missing_key(self):
        problems = check_mod.manifest_schema_problems({"verified": True})
        self.assertTrue(problems)

    def test_schema_rejects_an_extra_key(self):
        manifest = {"verified": True, "surprise": 1}
        problems = check_mod.manifest_schema_problems(manifest)
        self.assertTrue(
            any("surprise" in problem for problem in problems), problems
        )

    def test_the_strict_reader_refuses_a_repeated_key(self):
        with self.assertRaises(check_mod.DuplicateKeyError):
            check_mod.strict_json_loads('{"verified": false, "verified": true}')

    def test_the_strict_reader_accepts_a_plain_object(self):
        self.assertEqual(
            check_mod.strict_json_loads('{"verified": true}'),
            {"verified": True},
        )


if __name__ == "__main__":
    unittest.main()
