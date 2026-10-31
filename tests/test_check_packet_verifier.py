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

import hashlib
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
from types import SimpleNamespace

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



def findings_text_for(repo, since, body):
    """A findings file body with the header this run requires."""
    head = git(repo, "rev-parse", "HEAD")
    since_sha = git(repo, "rev-parse", since) if since else "none"
    return (
        "# recognitio-findings 1\n# packet-head: %s\n# since: %s\n"
        % (head, since_sha)
    ) + body


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

    def run_check_captured(self, out, *extra):
        stream = io.StringIO()
        with redirect_stderr(stream):
            code = check_mod.main(
                [str(out), "--repo", str(self.repo)] + list(extra)
            )
        return code, stream.getvalue()


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

    def test_a_packet_dir_spelling_with_a_missing_segment_then_a_parent_segment_stamps(self):
        out = self.clone("spelldir")
        spelling = str(out) + "/missing/.."
        self.assertEqual(self.run_check(spelling), 0)
        self.assertEqual(self.run_check(out), 0)

    def test_the_spellings_that_already_work_still_stamp(self):
        out = self.clone("spellcontrols")
        self.assertEqual(self.run_check(str(out) + "/"), 0)
        self.assertEqual(self.run_check(str(out) + "/./"), 0)
        self.assertEqual(self.run_check(out), 0)

    def test_the_extractor_and_the_checker_agree_on_the_split_spelling(self):
        plain = Path(self.tmp.name) / "spellpair"
        spelling = str(plain) + "/missing/.."
        extract_packet(
            self.repo, spelling, "--range", "HEAD~1..HEAD"
        )
        self.assertTrue((plain / "packet.md").is_file())
        self.assertTrue((plain / "manifest.json").is_file())
        self.assertEqual(self.run_check(spelling), 0)
        self.assertEqual(self.run_check(plain), 0)

    def test_the_extractor_and_the_checker_agree_on_a_dot_segment_after_a_missing_segment(self):
        spelling = str(Path(self.tmp.name)) + "/missing/./dotpair"
        resolved = Path(self.tmp.name) / "missing" / "dotpair"
        extract_packet(
            self.repo, spelling, "--range", "HEAD~1..HEAD"
        )
        self.assertTrue((resolved / "packet.md").is_file())
        self.assertTrue((resolved / "manifest.json").is_file())
        self.assertEqual(self.run_check(spelling), 0)
        self.assertEqual(self.run_check(resolved), 0)

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


class TestPacketDirectoryLoopShapes(VerifierFixture):
    """A loop spelling of the packet directory refuses by name.

    Round 255 New Minor 1 and round 271. The checker resolved
    the packet directory argument before any problem list
    existed, so a symlink loop at that argument raised through
    the resolve call uncaught and the run handed the caller a
    traceback and no named problem, while every sibling shape
    at the same argument refused by name. Round 258 New Note 1
    stands in the last two tests of this class.
    """

    def make_loop(self, name):
        loop = Path(self.tmp.name) / name
        loop.symlink_to(loop)
        return loop

    def test_a_symlink_loop_as_the_packet_directory_refuses_by_name(self):
        loop = self.make_loop("packetloop")
        code, err = self.run_check_captured(loop)
        self.assertEqual(code, 1)
        self.assertIn("cannot be resolved", err)
        self.assertIn("Symlink loop", err)
        self.assertNotIn("Traceback", err)

    def test_a_symlink_loop_in_an_intermediate_component_refuses_by_name(self):
        loop = self.make_loop("midloop")
        code, err = self.run_check_captured(loop / "genuine")
        self.assertEqual(code, 1)
        self.assertIn("cannot be resolved", err)
        self.assertIn("Symlink loop", err)
        self.assertNotIn("Traceback", err)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "no mkfifo on this host")
    def test_a_fifo_as_the_packet_directory_keeps_its_reading(self):
        fifo = Path(self.tmp.name) / "packetfifo"
        os.mkfifo(fifo)
        code, err = self.run_check_captured(fifo)
        self.assertEqual(code, 1)
        self.assertIn("no packet.md in", err)
        self.assertNotIn("Traceback", err)

    def test_a_regular_file_as_the_packet_directory_keeps_its_reading(self):
        plain = Path(self.tmp.name) / "packetfile"
        plain.write_text("not a directory\n", encoding="utf-8")
        code, err = self.run_check_captured(plain)
        self.assertEqual(code, 1)
        self.assertIn("no packet.md in", err)
        self.assertNotIn("Traceback", err)

    def test_a_failure_manifest_draws_no_claims_verified_sentence(self):
        # Round 258 New Note 1. A manifest whose verified flag
        # is false never claimed verified, so the sentence
        # stating that claim must not print beside the correct
        # not verified refusal on that shape.
        out = self.clone("failuremanifest")
        manifest = self.manifest(out)
        manifest["verified"] = False
        manifest["discrepancies"] = ["a recount disagreement"]
        self.save_manifest(out, manifest)
        code, err = self.run_check_captured(out)
        self.assertEqual(code, 1)
        self.assertIn("does not report verified", err)
        self.assertNotIn("claims verified", err)

    def test_a_verified_manifest_with_discrepancies_keeps_the_sentence(self):
        # The control beside round 258 New Note 1. A manifest
        # that does claim verified while carrying a non empty
        # discrepancy list still draws the sentence in full.
        out = self.clone("verifieddiscrep")
        manifest = self.manifest(out)
        manifest["discrepancies"] = [
            "file in manifest but not in recount: b.py"
        ]
        self.save_manifest(out, manifest)
        code, err = self.run_check_captured(out)
        self.assertEqual(code, 1)
        self.assertIn("claims verified", err)


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
            "--range", "HEAD~2..HEAD", "--budget", "1000",
        )
        manifest = self.manifest(out)
        self.assertTrue(manifest["budget"]["dropped"])
        self.assertEqual(self.check_repo_packet(self.repo, out), 0)

    def test_a_rereview_packet_passes(self):
        findings = Path(self.tmp.name) / "findings.txt"
        findings.write_text(
            findings_text_for(self.repo, "HEAD~2", "b.py:2: the value changed\n"),
            encoding="utf-8",
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


class TestFindingsHashBinding(VerifierFixture):
    """A findings hash stands only on a run that used a findings file.

    Round 98 finding 1 built a genuine range packet with no
    findings file, whose manifest honestly records no hash,
    and then replaced that record with an invented hex string
    of the right shape. The packet stamped verified, because
    no reading compared the field against anything where no
    findings path stands in the recorded command. The tests
    below hold the correct forms on both sides of the rule and
    fail against the pre fix checker on the invented hash.

    Round 114 finding 1 then appended a findings flag naming
    an absent file to a genuine since packet and set an
    invented hash beside it. The pairing reading was satisfied
    by the genuine since flag and the hash was never compared,
    because no file stood there and the packet carried no
    findings accounting for the fallback reading to stand on.
    The appended flag tests below hold that shape on both
    spellings and on a directory, and they fail against the
    checker as it stood before this second fix.
    """

    def run_check_capture(self, out):
        stream = io.StringIO()
        with redirect_stderr(stream):
            code = check_mod.main(
                [str(out), "--repo", str(self.repo)]
            )
        return code, stream.getvalue()

    def test_a_genuine_packet_with_no_findings_file_passes_with_a_null_hash(self):
        manifest = self.manifest(self.genuine)
        self.assertIsNone(manifest["findings_sha256"])
        self.assertNotIn("--findings", manifest["command"])
        self.assertEqual(self.run_check(self.clone("nohash")), 0)

    def test_an_invented_findings_hash_on_a_packet_with_no_findings_file_fails(self):
        out = self.clone("inventedhash")
        manifest = self.manifest(out)
        self.assertIsNone(manifest["findings_sha256"])
        manifest["findings_sha256"] = "0123456789abcdef" * 4
        self.save_manifest(out, manifest)
        code, output = self.run_check_capture(out)
        self.assertEqual(code, 1)
        self.assertIn(
            "the manifest records a findings hash but its "
            "command carries no findings flag",
            output,
        )

    def test_a_genuine_rereview_packet_with_a_real_findings_hash_passes(self):
        findings = Path(self.tmp.name) / "real-findings.txt"
        findings.write_text(
            findings_text_for(
                self.repo, "HEAD~2", "b.py:2: the value changed\n"
            ),
            encoding="utf-8",
        )
        out = extract_packet(
            self.repo, Path(self.tmp.name) / "realhash",
            "--range", "HEAD~1..HEAD", "--since", "HEAD~2",
            "--findings", str(findings),
        )
        manifest = self.manifest(out)
        self.assertIn("--findings", manifest["command"])
        self.assertEqual(
            manifest["findings_sha256"],
            hashlib.sha256(findings.read_bytes()).hexdigest(),
        )
        self.assertEqual(self.run_check(out), 0)

    def make_since_only(self, name="sinceonly114"):
        out = extract_packet(
            self.repo, Path(self.tmp.name) / name,
            "--range", "HEAD~1..HEAD", "--since", "HEAD~2",
        )
        manifest = self.manifest(out)
        self.assertIsNone(manifest["findings_sha256"])
        self.assertNotIn("--findings", manifest["command"])
        self.assertNotIn(
            "### Prior findings accounting", self.packet_text(out)
        )
        return out

    def make_real_findings(self, name="real114-findings.txt"):
        findings = Path(self.tmp.name) / name
        findings.write_text(
            findings_text_for(
                self.repo, "HEAD~2", "b.py:2: the value changed\n"
            ),
            encoding="utf-8",
        )
        return findings

    def smuggled_since_packet(self, name, tokens, digest="b" * 64):
        out = self.clone(name, self.make_since_only(name + "-base"))
        manifest = self.manifest(out)
        manifest["command"] = manifest["command"] + tokens
        manifest["findings_sha256"] = digest
        self.save_manifest(out, manifest)
        return out

    def test_an_appended_findings_flag_with_an_invented_hash_fails(self):
        absent = str(Path(self.tmp.name) / "absent-findings.txt")
        out = self.smuggled_since_packet(
            "smuggleplain", ["--findings", absent]
        )
        code, output = self.run_check_capture(out)
        self.assertEqual(code, 1)
        self.assertIn(
            "the manifest records a findings hash but the "
            "findings file its command records cannot be read",
            output,
        )

    def test_an_appended_equals_findings_flag_with_an_invented_hash_fails(self):
        absent = str(Path(self.tmp.name) / "absent-findings.txt")
        out = self.smuggled_since_packet(
            "smuggleequal", ["--findings=" + absent]
        )
        code, output = self.run_check_capture(out)
        self.assertEqual(code, 1)
        self.assertIn(
            "the manifest records a findings hash but the "
            "findings file its command records cannot be read",
            output,
        )

    def test_an_appended_findings_flag_with_an_empty_value_fails(self):
        out = self.smuggled_since_packet(
            "smuggleempty", ["--findings="]
        )
        code, output = self.run_check_capture(out)
        self.assertEqual(code, 1)
        self.assertIn(
            "the manifest records a findings hash but the "
            "findings file its command records cannot be read",
            output,
        )

    def test_an_appended_findings_flag_naming_a_directory_fails(self):
        directory = Path(self.tmp.name) / "findings-dir"
        directory.mkdir()
        out = self.smuggled_since_packet(
            "smuggledir", ["--findings", str(directory)]
        )
        code, output = self.run_check_capture(out)
        self.assertEqual(code, 1)
        self.assertIn(
            "the manifest records a findings hash but the "
            "findings file its command records cannot be read",
            output,
        )

    def test_an_appended_findings_flag_with_a_mismatched_hash_fails(self):
        findings = self.make_real_findings()
        out = self.smuggled_since_packet(
            "smugglemismatch", ["--findings", str(findings)]
        )
        code, output = self.run_check_capture(out)
        self.assertEqual(code, 1)
        self.assertIn("is not the findings hash", output)

    def test_duplicated_findings_flags_are_read_at_the_last_value(self):
        findings = self.make_real_findings("dup114-findings.txt")
        absent = str(Path(self.tmp.name) / "absent-findings.txt")
        out = self.smuggled_since_packet(
            "smuggledup",
            ["--findings", str(findings), "--findings", absent],
        )
        code, output = self.run_check_capture(out)
        self.assertEqual(code, 1)
        self.assertIn(
            "the manifest records a findings hash but the "
            "findings file its command records cannot be read",
            output,
        )

    def test_a_genuine_rereview_packet_in_equals_form_passes(self):
        findings = self.make_real_findings("eq114-findings.txt")
        source = extract_packet(
            self.repo, Path(self.tmp.name) / "eq114",
            "--range", "HEAD~1..HEAD", "--since", "HEAD~2",
            "--findings", str(findings),
        )
        out = self.clone("eq114clone", source)
        manifest = self.manifest(out)
        command = []
        index = 0
        while index < len(manifest["command"]):
            token = manifest["command"][index]
            if token == "--findings":
                command.append(
                    "--findings=" + manifest["command"][index + 1]
                )
                index += 2
            else:
                command.append(token)
                index += 1
        manifest["command"] = command
        self.save_manifest(out, manifest)
        self.assertEqual(self.run_check(out), 0)

    def test_the_extractor_clears_a_stale_hash_when_no_findings_file_is_named(self):
        args = SimpleNamespace(
            findings=None, findings_sha256="a" * 64
        )
        self.assertEqual(extract_mod.load_findings(args), [])
        self.assertIsNone(args.findings_sha256)


class TestSizedDiffFence(VerifierFixture):
    """A diff body holding a bare fence line must not desync the check.

    Round 91 of the audit program built this fixture against the
    shipped pair and the shipped check refused the packet the
    extractor had just stamped verified, naming the second file
    as missing from a change tier that plainly held it. The
    hunk in the first file carries one bare fence line as
    context, and under the old fixed three backtick fence that
    line closed the diff block early for every reader tracking
    fence state. The tests below stamp the shape end to end and
    then attack the stamped packet in the old shapes, and the
    stamping test fails against the pre fix pair for that real
    reason.
    """

    def build_fence_repo(self):
        repo = Path(self.tmp.name) / "fencerepo"
        init_repo(repo)
        (repo / "a.md").write_text(
            "# Doc\n\n```\ncode line\n```\n\n"
            "tail line one\ntail line two\n",
            encoding="utf-8",
        )
        (repo / "b.md").write_text(
            "bravo one\nbravo two\n", encoding="utf-8"
        )
        (repo / "c.md").write_text(
            "charlie one\ncharlie two\n", encoding="utf-8"
        )
        commit_all(repo, "base")
        (repo / "a.md").write_text(
            "# Doc\n\n```\ncode line\n```\n\n"
            "tail line one EDITED\ntail line two\n",
            encoding="utf-8",
        )
        (repo / "b.md").write_text(
            "bravo one EDITED\nbravo two\n", encoding="utf-8"
        )
        (repo / "c.md").write_text(
            "charlie one EDITED\ncharlie two\n", encoding="utf-8"
        )
        commit_all(repo, "change")
        return repo

    def fence_packet(self):
        repo = self.build_fence_repo()
        out = extract_packet(
            repo, Path(self.tmp.name) / "fencepkt", "--commit", "HEAD"
        )
        return repo, out

    def check_against(self, repo, out):
        with redirect_stderr(io.StringIO()):
            return check_mod.main([str(out), "--repo", str(repo)])

    def test_a_markdown_fence_packet_stamps_end_to_end(self):
        repo, out = self.fence_packet()
        text = self.packet_text(out)
        self.assertIn("### b.md", text)
        self.assertEqual(self.check_against(repo, out), 0)
        self.assertIn("````diff", text)

    def test_a_hand_edit_inside_a_sized_fence_fails(self):
        repo, out = self.fence_packet()
        clone = self.clone("fenceedit", out)
        text = self.packet_text(clone)
        self.assertIn("+tail line one EDITED", text)
        self.save_packet(
            clone,
            text.replace(
                "+tail line one EDITED", "+tail line one FORGED"
            ),
        )
        self.assertEqual(self.check_against(repo, clone), 1)

    def test_a_removed_file_section_fails(self):
        repo, out = self.fence_packet()
        clone = self.clone("fenceremoved", out)
        text = self.packet_text(clone)
        start = text.index("### b.md")
        end = text.index("### c.md")
        self.save_packet(clone, text[:start] + text[end:])
        self.assertEqual(self.check_against(repo, clone), 1)

    def test_a_fence_shrunk_back_to_three_backticks_fails(self):
        repo, out = self.fence_packet()
        clone = self.clone("fenceshrunk", out)
        text = self.packet_text(clone)
        opened = text.replace("````diff", "```diff", 1)
        self.assertNotEqual(opened, text)
        shrunk = opened.replace("\n````\n", "\n```\n", 1)
        self.assertNotEqual(shrunk, opened)
        self.save_packet(clone, shrunk)
        self.assertEqual(self.check_against(repo, clone), 1)

    def test_a_fence_enlarged_at_both_ends_fails_on_the_change_tier(self):
        repo, out = self.fence_packet()
        clone = self.clone("fenceenlarged", out)
        text = self.packet_text(clone)
        opened = text.replace("````diff", "`````diff", 1)
        self.assertNotEqual(opened, text)
        enlarged = opened.replace("\n````\n", "\n`````\n", 1)
        self.assertNotEqual(enlarged, opened)
        self.save_packet(clone, enlarged)
        captured = io.StringIO()
        with redirect_stderr(captured):
            code = check_mod.main(
                [str(clone), "--repo", str(repo)]
            )
        self.assertEqual(code, 1)
        self.assertIn(
            "carries its diff block inside a 5 backtick fence, "
            "but the body it fences requires 4 backticks",
            captured.getvalue(),
        )

    def test_a_plain_packet_keeps_the_fixed_fence_and_passes(self):
        repo = Path(self.tmp.name) / "plainrepo"
        init_repo(repo)
        (repo / "plain.md").write_text(
            "alpha one\nalpha two\n", encoding="utf-8"
        )
        commit_all(repo, "base")
        (repo / "plain.md").write_text(
            "alpha one EDITED\nalpha two\n", encoding="utf-8"
        )
        commit_all(repo, "change")
        out = extract_packet(
            repo, Path(self.tmp.name) / "plainpkt", "--commit", "HEAD"
        )
        text = self.packet_text(out)
        self.assertIn("```diff", text)
        self.assertNotIn("````diff", text)
        self.assertEqual(self.check_against(repo, out), 0)


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


class TestDiffFenceAgreement(unittest.TestCase):
    """The two diff fence sizing copies must agree on every body.

    The extractor sizes each change tier fence with its copy
    and the checker judges the size it finds with its own, so
    a body the two size differently can never be stamped, or
    worse, can be stamped wrongly. This battery is the single
    behaviour the two copies are held to.
    """

    BODIES = (
        "",
        "no backticks at all",
        "(no textual diff)",
        "`",
        "``",
        "```",
        "a ``` b",
        "````diff",
        "code line\n ```\n\ntail line",
        "+" + "`" * 7 + " added run",
        "mixed ` and ```` and `` runs",
    )

    def test_the_two_copies_agree_on_the_battery(self):
        for body in self.BODIES:
            with self.subTest(body=body):
                self.assertEqual(
                    check_mod.diff_fence_for(body),
                    extract_mod.fence_for(body),
                )

    def test_the_floor_and_the_step_are_the_stated_sizes(self):
        self.assertEqual(check_mod.diff_fence_for("plain"), "```")
        self.assertEqual(check_mod.diff_fence_for("a ``` b"), "````")
        self.assertEqual(
            check_mod.diff_fence_for("`" * 7), "`" * 8
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



class Round27Fixture(VerifierFixture):
    """Shared helpers for the round 27 second pass battery."""

    def run_check_capture(self, out, repo=None, *extra):
        stream = io.StringIO()
        with redirect_stderr(stream):
            code = check_mod.main(
                [str(out), "--repo", str(repo or self.repo)] + list(extra)
            )
        return code, stream.getvalue()

    def fix_accounting(self, out):
        """Settle the token accounting after a packet body edit.

        The round recomputed the token accounting after every
        forgery, because an attacker with the shipped code can
        do that arithmetic. The packet estimate and the included
        tier receipts appear in the manifest and in the closing
        receipt, and all of them are settled together until the
        numbers measure the packet, so the only check that can
        still refuse the forged packet is the new rule the test
        is written for.
        """
        manifest = self.manifest(out)
        headings = {
            "T0": "## T0 Triage", "T1": "## T1 The change",
            "T2": "## T2 Companions", "T3": "## T3 History",
        }
        for _round in range(16):
            text = self.packet_text(out)
            changed = False
            for tier, heading in headings.items():
                info = manifest["tiers"][tier]
                if info["state"] != "included":
                    continue
                span = check_mod.section_span(text, heading)
                self.assertIsNotNone(span)
                body = span[:-1] if span.endswith("\n") else span
                estimate = extract_mod.estimate_tokens(body)
                if info["estimated_tokens"] != estimate or \
                        info["emitted_tokens"] != estimate:
                    info["estimated_tokens"] = estimate
                    info["emitted_tokens"] = estimate
                    changed = True
                new, count = re.subn(
                    r"%s included at about [0-9]+ tokens across "
                    r"%d files" % (tier, info["files"]),
                    "%s included at about %d tokens across %d "
                    "files" % (tier, estimate, info["files"]),
                    text,
                    count=1,
                )
                self.assertEqual(count, 1)
                if new != text:
                    text = new
                    changed = True
            estimate = extract_mod.estimate_tokens(text)
            new, count = re.subn(
                r"Packet estimate in tokens: [0-9]+",
                "Packet estimate in tokens: %d" % estimate,
                text,
                count=1,
            )
            self.assertEqual(count, 1)
            if new != text:
                text = new
                changed = True
            if manifest["budget"]["estimated_tokens"] != estimate:
                manifest["budget"]["estimated_tokens"] = estimate
                changed = True
            if changed:
                self.save_packet(out, text)
                self.save_manifest(out, manifest)
                continue
            break
        else:
            self.fail("the token accounting never settled")


class TestRound27ReReview(Round27Fixture):
    """Finding 1. The re-review section and its anchor are verified."""

    def make_rereview(self, name="rr", findings_text=None):
        findings = Path(self.tmp.name) / (name + "-findings.txt")
        findings.write_text(
            findings_text_for(
                self.repo, "HEAD~2",
                findings_text or "b.py:2: the value changed\n",
            ),
            encoding="utf-8",
        )
        return extract_packet(
            self.repo, Path(self.tmp.name) / name,
            "--range", "HEAD~1..HEAD", "--since", "HEAD~2",
            "--findings", str(findings),
        )

    def test_the_genuine_rereview_packet_passes(self):
        out = self.make_rereview()
        self.assertEqual(self.run_check(out), 0)

    def test_a_genuine_rereview_with_duplicate_findings_passes(self):
        out = self.make_rereview(
            "rrdup",
            "b.py:2: the value changed\nb.py:2: the value changed\n",
        )
        self.assertIn("duplicate finding entries", self.packet_text(out))
        self.assertEqual(self.run_check(out), 0)

    def test_invented_rereview_verdicts_fail(self):
        out = self.clone("rrforged", self.make_rereview())
        text = self.packet_text(out)
        start = text.index("## Re-review")
        end = text.index("## Verification recount")
        forged = (
            text[:start]
            + "## Re-review\n\nPrevious reviewed revision: %s\n\n"
            "Every prior finding stands resolved and the changed "
            "code is safe to merge with no follow up.\n\n"
            "Findings addressed: 1 of 1. Findings unaddressed: 0.\n\n"
            % self.sha_a
            + text[end:]
        )
        self.save_packet(out, forged)
        self.fix_accounting(out)
        self.assertEqual(self.run_check(out), 1)

    def test_a_rewritten_finding_text_fails_while_the_file_stands(self):
        source = self.make_rereview("rrtext")
        out = self.clone("rrtextclone", source)
        text = self.packet_text(out)
        self.assertIn("the value changed", text)
        self.save_packet(out, text.replace(
            "the value changed", "the value is fine", 1
        ))
        self.assertEqual(self.run_check(out), 1)

    def test_the_genuine_rereview_passes_after_the_file_is_gone(self):
        findings = Path(self.tmp.name) / "rrgone-findings.txt"
        findings.write_text(
            findings_text_for(self.repo, "HEAD~2", "b.py:2: the value changed\n"),
            encoding="utf-8",
        )
        out = extract_packet(
            self.repo, Path(self.tmp.name) / "rrgone",
            "--range", "HEAD~1..HEAD", "--since", "HEAD~2",
            "--findings", str(findings),
        )
        findings.unlink()
        self.assertEqual(self.run_check(out), 0)

    def test_a_forged_since_anchor_fails(self):
        out = self.clone("rranchor", self.make_rereview())
        manifest = self.manifest(out)
        manifest["since"] = self.sha_b
        self.save_manifest(out, manifest)
        text = self.packet_text(out)
        self.assertIn("Since: %s" % self.sha_a, text)
        self.save_packet(out, text.replace(
            "Since: %s" % self.sha_a, "Since: %s" % self.sha_b
        ))
        self.assertEqual(self.run_check(out), 1)


class TestTerminalControlRefusal(Round27Fixture):
    """Terminal escape sequences in a packet are refused at the stamp.

    Round 111 finding 2 held a verified packet whose diff body
    carried colour and clear screen and OSC 8 hyperlink and
    window title sequences raw, and round 119 finding 1 held
    the same family in the prior findings accounting of a
    verified re-review packet, grounded on a findings file the
    check itself reads back. The stamp now refuses both
    channels with the character named. Each forgery below is
    settled with the shipped token arithmetic, the way the
    round records settled theirs, so the control reading is
    the only reading that can refuse it, and each test fails
    against the pre fix checker, which stamped both packets.
    """

    def make_rereview(self, name):
        findings = Path(self.tmp.name) / (name + "-findings.txt")
        findings.write_text(
            findings_text_for(
                self.repo, "HEAD~2", "b.py:2: the value changed\n"
            ),
            encoding="utf-8",
        )
        return extract_packet(
            self.repo, Path(self.tmp.name) / name,
            "--range", "HEAD~1..HEAD", "--since", "HEAD~2",
            "--findings", str(findings),
        )

    def test_an_escape_sequence_in_a_diff_body_fails(self):
        out = self.clone("escbody")
        text = self.packet_text(out)
        self.assertIn("return 2", text)
        self.save_packet(out, text.replace(
            "return 2",
            "return 2 \x1b[31mREDALERTCANARY\x1b[0m",
            1,
        ))
        self.fix_accounting(out)
        code, output = self.run_check_capture(out)
        self.assertEqual(code, 1)
        self.assertIn(
            "the packet carries a terminal control character "
            "U+001B",
            output,
        )

    def test_a_hostile_findings_accounting_and_its_file_fail(self):
        source = self.make_rereview("escfind")
        out = self.clone("escfindclone", source)
        findings = Path(self.tmp.name) / "escfind-findings.txt"
        hostile = (
            "the value changed \x1b[31mFINDCANARY\x1b[0m "
            "\x1b]8;;https://example.invalid/findphish\x1b\\"
            "FINDCLICK\x1b]8;;\x1b\\"
        )
        findings.write_text(
            findings_text_for(
                self.repo, "HEAD~2", "b.py:2: " + hostile + "\n"
            ),
            encoding="utf-8",
        )
        text = self.packet_text(out)
        self.assertIn("the value changed", text)
        self.save_packet(
            out, text.replace("the value changed", hostile, 1)
        )
        manifest = self.manifest(out)
        manifest["findings_sha256"] = hashlib.sha256(
            findings.read_bytes()
        ).hexdigest()
        self.save_manifest(out, manifest)
        self.fix_accounting(out)
        code, output = self.run_check_capture(out)
        self.assertEqual(code, 1)
        self.assertIn(
            "the packet carries a terminal control character "
            "U+001B",
            output,
        )
        self.assertIn(
            "the findings file the manifest command records "
            "carries a terminal control character U+001B",
            output,
        )

    def test_a_genuine_rereview_packet_still_passes(self):
        out = self.make_rereview("escgenuine")
        manifest = self.manifest(out)
        findings = Path(self.tmp.name) / "escgenuine-findings.txt"
        self.assertEqual(
            manifest["findings_sha256"],
            hashlib.sha256(findings.read_bytes()).hexdigest(),
        )
        code, _output = self.run_check_capture(out)
        self.assertEqual(code, 0)


class TestTerminalControlAgreement(unittest.TestCase):
    """The two terminal control copies must agree on every text.

    The extractor refuses with its copy and the checker
    refuses with its own, so a character the two read
    differently could be built by one side and stamped by
    the other. This battery is the single behaviour the
    two copies are held to.
    """

    TEXTS = (
        "plain text",
        "a\tb",
        "a\nb",
        "a\r\nb",
        "\r\n",
        "a\rb",
        "a\r",
        "trail\r",
        "a\x1b[31mb",
        "a\x07b",
        "a\x0bb",
        "a\x0cb",
        "a\x7fb",
        "a\u0085b",
        "a\u009bb",
        "caf\u00e9",
        "emoji \U0001f600",
    )

    def test_the_two_copies_agree_on_the_battery(self):
        for text in self.TEXTS:
            with self.subTest(text=text):
                self.assertEqual(
                    check_mod.terminal_control_character(text),
                    extract_mod.terminal_control_character(text),
                )
        for code in range(256):
            with self.subTest(code=code):
                text = "a" + chr(code) + "b"
                self.assertEqual(
                    check_mod.terminal_control_character(text),
                    extract_mod.terminal_control_character(text),
                )

    def test_the_refused_set_is_the_stated_set(self):
        reading = check_mod.terminal_control_character
        self.assertEqual(reading("a\x1bb"), "\x1b")
        self.assertEqual(reading("a\rb"), "\r")
        self.assertIsNone(reading("a\u0085b"))
        self.assertIsNone(reading("a\u009bb"))
        self.assertIsNone(reading("a\tb"))
        self.assertIsNone(reading("a\r\nb"))
        self.assertIsNone(reading("plain text"))


class TestRound27PullRequest(Round27Fixture):
    """Finding 2. The PR preamble and the manifest PR record."""

    def setUp(self):
        super().setUp()
        repo = Path(self.tmp.name) / "prrepo27"
        init_repo(repo)
        (repo / "module.py").write_text(
            "def alpha():\n    return 1\n", encoding="utf-8"
        )
        base = commit_all(repo, "base")
        (repo / "module.py").write_text(
            "def alpha():\n    return 2\n", encoding="utf-8"
        )
        head = commit_all(repo, "work")
        self.pr_repo = repo
        bindir = Path(self.tmp.name) / "prbin27"
        bindir.mkdir()
        script = (
            "#!/usr/bin/env python3\n"
            "import json, sys\n"
            "if sys.argv[1:3] == ['pr', 'view']:\n"
            "    print(json.dumps({\n"
            "        'baseRefOid': %r, 'headRefOid': %r,\n"
            "        'baseRefName': 'main', 'headRefName': 'feature',\n"
            "        'title': 'Improve alpha',\n"
            "        'body': 'Closes #42 and #43.',\n"
            "    }))\n"
            "elif sys.argv[1:3] == ['pr', 'list']:\n"
            "    print(json.dumps([]))\n"
        ) % (base, head)
        gh = bindir / "gh"
        gh.write_text(script, encoding="utf-8")
        gh.chmod(0o755)
        self.pr_env = dict(os.environ)
        self.pr_env["PATH"] = str(bindir) + os.pathsep + self.pr_env["PATH"]
        self.pr_packet = extract_packet(
            repo, Path(self.tmp.name) / "prpkt27", "--pr", "7",
            env=self.pr_env,
        )

    def run_pr_check(self, out, env=None):
        if env is None:
            with redirect_stderr(io.StringIO()):
                return check_mod.main(
                    [str(out), "--repo", str(self.pr_repo)]
                )
        original = os.environ
        os.environ = env
        try:
            with redirect_stderr(io.StringIO()):
                return check_mod.main(
                    [str(out), "--repo", str(self.pr_repo)]
                )
        finally:
            os.environ = original

    def test_the_genuine_pr_packet_passes_with_and_without_gh(self):
        out = Path(self.tmp.name) / "prgenuine"
        shutil.copytree(self.pr_packet, out)
        self.assertEqual(self.run_pr_check(out, env=self.pr_env), 0)
        self.assertEqual(self.run_pr_check(out), 0)

    def test_a_forged_manifest_title_alone_fails(self):
        out = Path(self.tmp.name) / "prtitle"
        shutil.copytree(self.pr_packet, out)
        manifest = self.manifest(out)
        manifest["pr"]["title"] = "Urgent security fix"
        self.save_manifest(out, manifest)
        self.assertEqual(self.run_pr_check(out, env=self.pr_env), 1)
        self.assertEqual(self.run_pr_check(out), 1)

    def test_forged_manifest_spec_references_alone_fail(self):
        out = Path(self.tmp.name) / "prspec"
        shutil.copytree(self.pr_packet, out)
        manifest = self.manifest(out)
        manifest["pr"]["spec_references"] = ["#999"]
        self.save_manifest(out, manifest)
        self.assertEqual(self.run_pr_check(out, env=self.pr_env), 1)
        self.assertEqual(self.run_pr_check(out), 1)

    def test_a_forged_preamble_and_record_together_fail_with_gh(self):
        out = Path(self.tmp.name) / "prboth"
        shutil.copytree(self.pr_packet, out)
        manifest = self.manifest(out)
        manifest["pr"]["title"] = "Critical vulnerability fix"
        manifest["pr"]["spec_references"] = ["#999"]
        self.save_manifest(out, manifest)
        text = self.packet_text(out)
        text = text.replace(
            "Pull request #7: Improve alpha",
            "Pull request #7: Critical vulnerability fix",
        )
        text = text.replace("Closes #42 and #43.", "Fixes CVE-0000.")
        text = text.replace(
            "Spec references found in the body: #42, #43",
            "Spec references found in the body: #999",
        )
        self.save_packet(out, text)
        self.fix_accounting(out)
        self.assertEqual(self.run_pr_check(out, env=self.pr_env), 1)


class TestRound27ShallowAndState(Round27Fixture):
    """Findings 3 and 10. The checking environment is read."""

    def test_a_genuine_packet_in_a_shallow_clone_names_shallow(self):
        shallow = Path(self.tmp.name) / "shallowclone"
        subprocess.run(
            [
                "git", "clone", "-q", "--depth", "2",
                "file://" + str(self.repo), str(shallow),
            ],
            check=True,
        )
        git(shallow, "config", "user.email", "test@example.com")
        out = self.clone("shallowpkt", self.full)
        code, output = self.run_check_capture(out, repo=shallow)
        self.assertEqual(code, 1)
        self.assertIn("shallow", output)

    def test_a_packet_in_a_rebasing_repository_names_the_rebase(self):
        repo = Path(self.tmp.name) / "rebaserepo"
        init_repo(repo)
        (repo / "f.py").write_text("x = 1\n", encoding="utf-8")
        commit_all(repo, "one")
        git(repo, "checkout", "-q", "-b", "side")
        (repo / "f.py").write_text("x = 2\n", encoding="utf-8")
        side_head = commit_all(repo, "side change")
        git(repo, "checkout", "-q", "main")
        (repo / "f.py").write_text("x = 3\n", encoding="utf-8")
        main_head = commit_all(repo, "main change")
        clean = Path(self.tmp.name) / "cleanclone"
        subprocess.run(
            ["git", "clone", "-q", str(repo), str(clean)], check=True
        )
        git(clean, "checkout", "-q", main_head)
        out = extract_packet(
            clean, Path(self.tmp.name) / "rebasepkt",
            "--commit", main_head,
        )
        git(repo, "checkout", "-q", "side")
        result = subprocess.run(
            ["git", "-C", str(repo), "rebase", "main"],
            capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(git(repo, "rev-parse", "HEAD"), main_head)
        code, output = self.run_check_capture(out, repo=repo)
        self.assertEqual(code, 1)
        self.assertIn("rebase", output)
        self.assertEqual(side_head is not None, True)


class TestRound27CapNotes(Round27Fixture):
    """Finding 4. The manifest cap notes list is compared."""

    def make_capped(self):
        repo = Path(self.tmp.name) / "caprepo"
        init_repo(repo)
        (repo / "target.py").write_text(
            "def target():\n    return 1\n", encoding="utf-8"
        )
        for index in range(14):
            (repo / ("caller%02d.py" % index)).write_text(
                "value = target()\n",
                encoding="utf-8",
            )
        commit_all(repo, "one")
        (repo / "target.py").write_text(
            "def target():\n    return 2\n", encoding="utf-8"
        )
        commit_all(repo, "two")
        out = extract_packet(
            repo, Path(self.tmp.name) / "cappkt",
            "--range", "HEAD~1..HEAD",
        )
        self.capped_repo = repo
        return out

    def test_the_genuine_capped_packet_passes(self):
        out = self.make_capped()
        manifest = self.manifest(out)
        self.assertEqual(
            manifest["cap_notes"],
            ["call sites for target capped at 5 of 14"],
        )
        code, _output = self.run_check_capture(out, repo=self.capped_repo)
        self.assertEqual(code, 0)

    def test_an_emptied_cap_notes_list_fails(self):
        out = self.make_capped()
        manifest = self.manifest(out)
        manifest["cap_notes"] = []
        self.save_manifest(out, manifest)
        code, _output = self.run_check_capture(out, repo=self.capped_repo)
        self.assertEqual(code, 1)

    def test_invented_cap_notes_fail(self):
        out = self.clone("capinvent")
        manifest = self.manifest(out)
        self.assertEqual(manifest["cap_notes"], [])
        manifest["cap_notes"] = [
            "call sites capped at 5 of 999", "other capped at 3 of 400",
        ]
        self.save_manifest(out, manifest)
        self.assertEqual(self.run_check(out), 1)

    def test_a_duplicated_cap_note_fails(self):
        out = self.make_capped()
        manifest = self.manifest(out)
        manifest["cap_notes"] = manifest["cap_notes"] * 2
        self.save_manifest(out, manifest)
        code, _output = self.run_check_capture(out, repo=self.capped_repo)
        self.assertEqual(code, 1)


class TestRound27Budget(Round27Fixture):
    """Finding 5. The budget account is checked against the run."""

    def make_budgeted(self, name="budget27"):
        return extract_packet(
            self.repo, Path(self.tmp.name) / name,
            "--range", "HEAD~2..HEAD", "--budget", "1000",
        )

    def test_a_forged_budget_with_a_matching_receipt_line_fails(self):
        out = self.clone("budgetforge", self.make_budgeted())
        manifest = self.manifest(out)
        self.assertTrue(manifest["budget"]["dropped"])
        manifest["budget"]["budget_tokens"] = 31337
        self.save_manifest(out, manifest)
        text = self.packet_text(out)
        self.assertIn("Budget in tokens: 1000", text)
        self.save_packet(out, text.replace(
            "Budget in tokens: 1000", "Budget in tokens: 31337"
        ))
        self.fix_accounting(out)
        self.assertEqual(self.run_check(out), 1)

    def test_a_forged_drop_reason_fails(self):
        out = self.clone("reasonforge", self.make_budgeted())
        manifest = self.manifest(out)
        dropped = manifest["budget"]["dropped"]
        self.assertTrue(dropped)
        tier = dropped[0]["tier"]
        genuine_line = "Dropped %s because of the budget of 1000 tokens." % tier
        forged_line = "Dropped %s because of the a security redaction order." % tier
        dropped[0]["reason"] = "a security redaction order"
        self.save_manifest(out, manifest)
        text = self.packet_text(out)
        self.assertIn(genuine_line, text)
        self.save_packet(out, text.replace(genuine_line, forged_line))
        self.fix_accounting(out)
        self.assertEqual(self.run_check(out), 1)

    def test_a_forged_dropped_tier_size_fails(self):
        out = self.clone("sizeforge", self.make_budgeted())
        manifest = self.manifest(out)
        dropped = manifest["budget"]["dropped"]
        tier = dropped[0]["tier"]
        genuine = manifest["tiers"][tier]["estimated_tokens"]
        self.assertGreater(genuine, 7)
        manifest["tiers"][tier]["estimated_tokens"] = 7
        self.save_manifest(out, manifest)
        text = self.packet_text(out)
        new, count = re.subn(
            r"%s dropped under the token budget\. The full tier "
            r"runs about [0-9]+ tokens" % tier,
            "%s dropped under the token budget. The full tier "
            "runs about 7 tokens" % tier,
            text,
            count=1,
        )
        self.assertEqual(count, 1)
        self.save_packet(out, new)
        self.fix_accounting(out)
        self.assertEqual(self.run_check(out), 1)

    def test_a_duplicated_drop_entry_fails(self):
        out = self.clone("dupdrop", self.make_budgeted())
        manifest = self.manifest(out)
        dropped = manifest["budget"]["dropped"]
        self.assertTrue(dropped)
        dropped.append(dict(dropped[0]))
        self.save_manifest(out, manifest)
        self.assertEqual(self.run_check(out), 1)


class TestRound27Command(Round27Fixture):
    """Finding 6. The recorded command is read back whole."""

    def command_edit_fails(self, name, source, edit):
        out = self.clone(name, source)
        manifest = self.manifest(out)
        edit(manifest["command"])
        self.save_manifest(out, manifest)
        self.assertEqual(self.run_check(out), 1)

    def test_appended_budget_and_tiers_flags_fail(self):
        def edit(command):
            command.extend(["--budget", "999999", "--tiers", "0,1"])
        self.command_edit_fails("cmdappend", self.full, edit)

    def test_a_second_range_flag_is_read_at_its_last_value(self):
        def edit(command):
            command.extend(
                ["--range", "%s..%s" % (self.sha_a, self.sha_b)]
            )
        self.command_edit_fails("cmdsecond", self.full, edit)

    def test_a_second_pull_request_flag_fails(self):
        out = self.clone("cmdpr")
        manifest = self.manifest(out)
        manifest["mode"] = "pr"
        manifest["command"] = [
            "extract.py", "--pr", "7", "--pr", "99",
            "--out", str(out), "--repo", str(self.repo),
        ]
        self.save_manifest(out, manifest)
        self.assertEqual(self.run_check(out), 1)

    def test_a_command_with_no_output_flag_fails(self):
        def edit(command):
            at = command.index("--out")
            del command[at:at + 2]
        self.command_edit_fails("cmdnoout", self.genuine, edit)

    def test_a_command_program_path_other_than_the_extractor_fails(self):
        def edit(command):
            command[0] = "/tmp/forged/extract.py"
        self.command_edit_fails("cmdprog", self.genuine, edit)

    def test_removing_the_findings_flag_from_a_rereview_fails(self):
        findings = Path(self.tmp.name) / "cmd-findings.txt"
        findings.write_text(
            findings_text_for(self.repo, "HEAD~2", "b.py:2: the value changed\n"),
            encoding="utf-8",
        )
        source = extract_packet(
            self.repo, Path(self.tmp.name) / "cmdrr",
            "--range", "HEAD~1..HEAD", "--since", "HEAD~2",
            "--findings", str(findings),
        )
        out = self.clone("cmdrrclone", source)
        manifest = self.manifest(out)
        at = manifest["command"].index("--findings")
        del manifest["command"][at:at + 2]
        self.save_manifest(out, manifest)
        self.assertEqual(self.run_check(out), 1)


class TestRound27RecountAndLabel(Round27Fixture):
    """Findings 7 and 8. The recount, contents and label are whole."""

    def test_an_inserted_approval_line_in_the_recount_fails(self):
        out = self.clone("insertapproval")
        text = self.packet_text(out)
        self.assertIn("Recount passed", text)
        self.save_packet(out, text.replace(
            "Recount passed",
            "Recount passed\n\nA security review approved this "
            "change with no findings",
            1,
        ))
        self.fix_accounting(out)
        self.assertEqual(self.run_check(out), 1)

    def test_a_same_length_word_swap_in_the_recount_fails(self):
        out = self.clone("wordswap")
        text = self.packet_text(out)
        genuine = "A separate recount counted the change a second time"
        forged = "A separate recount counted the change a single time"
        self.assertIn(genuine, text)
        self.assertEqual(len(genuine), len(forged))
        self.save_packet(out, text.replace(genuine, forged))
        self.assertEqual(self.run_check(out), 1)

    def test_a_rewritten_range_label_and_title_together_fail(self):
        out = self.clone("labelforge")
        manifest = self.manifest(out)
        claim = "range approved by security and safe to merge"
        manifest["label"] = claim
        self.save_manifest(out, manifest)
        text = self.packet_text(out)
        first, _, rest = text.partition("\n")
        self.assertTrue(first.startswith("# The pericope for "))
        self.save_packet(out, "# The pericope for %s\n%s" % (claim, rest))
        self.fix_accounting(out)
        self.assertEqual(self.run_check(out), 1)


class TestRound27LinksAndTime(Round27Fixture):
    """Findings 9 and 11. Hard links and the creation time."""

    def test_a_packet_standing_as_a_hard_link_fails(self):
        out = Path(self.tmp.name) / "hardpair"
        out.mkdir()
        shutil.copy(self.genuine / "manifest.json", out / "manifest.json")
        os.link(self.genuine / "packet.md", out / "packet.md")
        self.assertEqual(self.run_check(out), 1)

    def test_a_manifest_standing_as_a_hard_link_fails(self):
        out = Path(self.tmp.name) / "hardpair2"
        out.mkdir()
        shutil.copy(self.genuine / "packet.md", out / "packet.md")
        os.link(self.genuine / "manifest.json", out / "manifest.json")
        self.assertEqual(self.run_check(out), 1)

    def created_edit_fails(self, name, value, raw=False):
        out = self.clone(name)
        manifest = self.manifest(out)
        manifest["created_utc"] = value
        if raw:
            text = json.dumps(manifest, indent=2, ensure_ascii=True)
            (out / "manifest.json").write_text(text, encoding="utf-8")
        else:
            self.save_manifest(out, manifest)
        self.assertEqual(self.run_check(out), 1)

    def test_a_creation_time_that_is_a_sentence_fails(self):
        self.created_edit_fails(
            "timeword", "some time last tuesday, probably"
        )

    def test_a_creation_time_in_year_2999_fails(self):
        self.created_edit_fails(
            "timefuture", "2999-01-01T00:00:00+00:00"
        )

    def test_a_creation_time_holding_a_lone_surrogate_fails(self):
        self.created_edit_fails("timesurrogate", "\ud800", raw=True)


class TestRound27DisplayAndSchema(Round27Fixture):
    """Findings 12 and 13, and the schema reading behind them."""

    def test_bidi_and_zero_width_names_print_escaped_and_pass(self):
        for label, char, spelling in (
            ("override", "\u202e", "\\u202e"),
            ("zerowidth", "\ufeff", "\\ufeff"),
        ):
            with self.subTest(kind=label):
                repo = Path(self.tmp.name) / ("disp-" + label)
                init_repo(repo)
                name = "disp" + char + "file.py"
                (repo / name).write_text("x = 1\n", encoding="utf-8")
                commit_all(repo, "one")
                (repo / name).write_text("x = 2\n", encoding="utf-8")
                commit_all(repo, "two")
                out = extract_packet(
                    repo, Path(self.tmp.name) / ("dispout-" + label),
                    "--range", "HEAD~1..HEAD",
                )
                text = self.packet_text(out)
                # The packet own voice, its headings and file
                # lists, must print the escaped spelling and
                # never the raw mark. The diff body is a verbatim
                # quote of the git output and stays byte true so
                # the recount can compare it, so the raw mark may
                # stand there and nowhere else.
                own_voice = [
                    line for line in text.split("\n")
                    if not line.startswith(
                        ("diff --git ", "--- ", "+++ ")
                    )
                ]
                self.assertNotIn(char, "\n".join(own_voice))
                self.assertIn(spelling, text)
                code, _output = self.run_check_capture(out, repo=repo)
                self.assertEqual(code, 0)
                self.assertEqual(
                    check_mod.display_path("a" + char + "b"),
                    extract_mod.display_path("a" + char + "b"),
                )

    def schema_mutation_is_refused(self, mutate):
        manifest = self.manifest(self.genuine)
        mutate(manifest)
        problems = check_mod.manifest_schema_problems(manifest)
        self.assertTrue(problems)

    def test_a_status_code_with_a_trailing_newline_fails_the_schema(self):
        self.schema_mutation_is_refused(
            lambda m: m["files"][0].update({"status_code": "M\n"})
        )

    def test_a_version_with_a_trailing_newline_fails_the_schema(self):
        self.schema_mutation_is_refused(
            lambda m: m.update({"version": "1.3.0\n"})
        )

    def test_a_head_with_a_trailing_newline_fails_the_schema(self):
        self.schema_mutation_is_refused(
            lambda m: m.update({"head": m["head"] + "\n"})
        )

    def test_a_label_reduced_to_a_newline_fails_the_schema(self):
        self.schema_mutation_is_refused(
            lambda m: m.update({"label": "\n"})
        )


class TestRound27Notes(Round27Fixture):
    """Findings 14, 15 and 16. Spellings, order and failure output."""

    def test_reversed_selected_tiers_fail(self):
        out = self.clone("tiersorder", self.full)
        manifest = self.manifest(out)
        manifest["selected_tiers"] = list(
            reversed(manifest["selected_tiers"])
        )
        self.save_manifest(out, manifest)
        self.assertEqual(self.run_check(out), 1)

    def test_a_moved_range_spelling_warns_and_still_stamps(self):
        repo = Path(self.tmp.name) / "spellrepo"
        init_repo(repo)
        (repo / "a.py").write_text("x = 1\n", encoding="utf-8")
        commit_all(repo, "one")
        git(repo, "branch", "feature")
        git(repo, "checkout", "-q", "feature")
        (repo / "a.py").write_text("x = 2\n", encoding="utf-8")
        commit_all(repo, "two")
        (repo / "a.py").write_text("x = 3\n", encoding="utf-8")
        head = commit_all(repo, "three")
        out = extract_packet(
            repo, Path(self.tmp.name) / "spellpkt",
            "--range", "main..feature",
        )
        clone = Path(self.tmp.name) / "spellclone"
        subprocess.run(
            ["git", "clone", "-q", str(repo), str(clone)], check=True
        )
        middle = git(clone, "rev-parse", "HEAD~1")
        git(clone, "checkout", "-q", "--detach", head)
        git(clone, "branch", "-f", "main", head)
        git(clone, "branch", "-f", "feature", middle)
        code, output = self.run_check_capture(out, repo=clone)
        self.assertEqual(code, 0)
        self.assertIn("warning", output)
        self.assertIn("now resolves", output)

    def test_a_false_verified_flag_names_the_skipped_checks(self):
        out = self.clone("skipnote")
        manifest = self.manifest(out)
        manifest["verified"] = False
        manifest["files"][0]["additions"] = 9999
        self.save_manifest(out, manifest)
        code, output = self.run_check_capture(out)
        self.assertEqual(code, 1)
        self.assertIn("were skipped because", output)

    def test_a_non_repository_path_is_named_as_the_cause(self):
        not_repo = Path(self.tmp.name) / "notrepo"
        not_repo.mkdir()
        out = self.clone("notrepocheck")
        code, output = self.run_check_capture(out, repo=not_repo)
        self.assertEqual(code, 1)
        self.assertIn("not a readable git repository", output)
        self.assertNotIn("is not a commit in the repository", output)

    def test_a_schema_anyof_refusal_names_the_value(self):
        out = self.clone("anyofvalue")
        manifest = self.manifest(out)
        manifest["pr"] = 7
        self.save_manifest(out, manifest)
        code, output = self.run_check_capture(out)
        self.assertEqual(code, 1)
        self.assertIn("matches none of the shapes", output)
        self.assertIn("7", output)

    def test_the_success_line_names_the_covered_range(self):
        out = self.clone("successline")
        stream_out = io.StringIO()
        stream_err = io.StringIO()
        with redirect_stderr(stream_err):
            from contextlib import redirect_stdout
            with redirect_stdout(stream_out):
                code = check_mod.main(
                    [str(out), "--repo", str(self.repo)]
                )
        self.assertEqual(code, 0)
        text = stream_out.getvalue()
        self.assertIn("covering base", text)
        self.assertIn("merge base", text)
        self.assertIn("the review named no expected range", text)


@unittest.skipUnless(hasattr(os, "mkfifo"), "no mkfifo on this host")
class TestCheckerInfoAttributesFifo(VerifierFixture):
    """Round 233. The checker clone attributes reading is guarded.

    The shipped FIFO test at this path exercised the extractor
    subprocess alone, so the checker reading stood untested while
    it read the same path with a plain read and no regular file
    test. A FIFO there blocked the checker without bound and
    without output. Every run below is a bounded subprocess, so a
    checker that still reads the pipe fails at the bound instead
    of hanging this suite.
    """

    def info_attributes(self):
        return self.repo / ".git" / "info" / "attributes"

    def clear_attributes(self):
        info = self.info_attributes()
        if info.is_symlink() or info.exists():
            info.unlink()
        return info

    def run_check_bounded(self, out):
        try:
            result = subprocess.run(
                [
                    sys.executable, str(CHECK_PATH),
                    str(out), "--repo", str(self.repo),
                ],
                capture_output=True, text=True, timeout=10,
            )
        except subprocess.TimeoutExpired:
            self.fail(
                "the checker did not finish inside ten seconds, "
                "so it blocked on the info attributes path"
            )
        return result.returncode, result.stderr

    def test_a_fifo_at_the_attributes_path_refuses_promptly(self):
        info = self.clear_attributes()
        os.mkfifo(info)
        code, output = self.run_check_bounded(self.genuine)
        self.assertEqual(code, 1)
        self.assertIn(
            "cannot be read, it is not a regular file", output
        )
        self.assertIn("attributes", output)

    def test_a_symlink_to_a_fifo_at_the_attributes_path_refuses(self):
        target = Path(self.tmp.name) / "attributes-pipe"
        os.mkfifo(target)
        info = self.clear_attributes()
        info.symlink_to(target)
        code, output = self.run_check_bounded(self.genuine)
        self.assertEqual(code, 1)
        self.assertIn(
            "cannot be read, it is not a regular file", output
        )

    def test_a_regular_effective_attributes_file_still_refuses(self):
        info = self.clear_attributes()
        info.write_text("b.py binary\n", encoding="utf-8")
        code, output = self.run_check_bounded(self.genuine)
        self.assertEqual(code, 1)
        self.assertIn("carries attributes in", output)
        self.assertIn("were skipped because", output)

    def test_a_comment_only_attributes_file_still_stamps(self):
        info = self.clear_attributes()
        info.write_text("# a local note\n\n", encoding="utf-8")
        code, output = self.run_check_bounded(self.genuine)
        self.assertEqual(code, 0, output)

    def test_absent_attributes_still_stamps(self):
        self.clear_attributes()
        code, output = self.run_check_bounded(self.genuine)
        self.assertEqual(code, 0, output)

    def test_a_dangling_attributes_symlink_still_stamps(self):
        info = self.clear_attributes()
        info.symlink_to(Path(self.tmp.name) / "no-such-target")
        code, output = self.run_check_bounded(self.genuine)
        self.assertEqual(code, 0, output)


class TestHeadConditionDisclosure(unittest.TestCase):
    """The current head condition stands on the surfaces that teach the check.

    The checker refuses a packet whose recorded head is not
    the current head of the repository it runs against and
    calls the packet stale, and for most of the programme no
    stranger facing surface stated that condition, so the
    packets the first hour teaches failed with a word no
    page explained. Dropping the statement from any of the
    three surfaces fails here.
    """

    CONDITION = (
        "must be the current head of the repository "
        "the check runs against"
    )

    def flat(self, rel):
        return " ".join(
            (ROOT / rel).read_text(encoding="utf-8").split()
        )

    def test_the_readme_usage_paragraph_states_the_condition(self):
        flat = self.flat("README.md")
        self.assertIn(
            "The head the manifest records " + self.CONDITION, flat
        )
        self.assertIn(
            "refused as stale, where stale names that "
            "condition alone and not any decay in the packet",
            flat,
        )

    def test_the_skill_stamping_section_states_the_condition(self):
        flat = self.flat(".agents/skills/recognitio/SKILL.md")
        self.assertIn(
            "The head the manifest records " + self.CONDITION, flat
        )
        self.assertIn(
            "A packet built for a named commit therefore "
            "stamps in a checkout standing at that commit",
            flat,
        )

    def test_the_examples_note_states_the_condition_and_the_route(self):
        flat = self.flat("examples/README.md")
        self.assertIn("## Stamping this packet", flat)
        self.assertIn(
            "refuses this packet as stale in a checkout "
            "standing at any later head",
            flat,
        )
        self.assertIn(
            "copy this folder into that checkout first", flat
        )


class TestSkillRestoredSentences(unittest.TestCase):
    """The two skill sentences the claims repair restored stand put.

    The re-review section names the re-review as the right
    tool after a rebase because the range diff shows whether
    hunks survived the move, and the findings accounting
    states that a finding whose path existed at the previous
    reviewed revision and whose file is gone at the head
    counts as addressed. The claims landing trimmed both
    for space and its repair restored both, so dropping
    either from any of the four skill copies fails here.
    """

    COPIES = (
        ".agents/skills/recognitio/SKILL.md",
        ".comate/skills/recognitio/SKILL.md",
        ".cursor-plugin/skills/recognitio/SKILL.md",
        "agent-plugins-package/skills/recognitio/SKILL.md",
    )

    def flat(self, rel):
        return " ".join(
            (ROOT / rel).read_text(encoding="utf-8").split()
        )

    def test_the_restored_sentences_stand_in_every_copy(self):
        for rel in self.COPIES:
            with self.subTest(copy=rel):
                flat = self.flat(rel)
                self.assertIn(
                    "This is also the right tool after a "
                    "rebase, because the range diff shows "
                    "whether hunks survived the move",
                    flat,
                )
                self.assertIn(
                    "A finding whose path existed at the "
                    "previous reviewed revision and whose "
                    "file is gone at the head counts as "
                    "addressed",
                    flat,
                )


if __name__ == "__main__":
    unittest.main()
