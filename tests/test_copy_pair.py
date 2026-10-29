"""Regression tests for the copy labelling pair.

Rounds 26 and 34 of the 300 round audit program showed every
detected copy labelled as a rename in the triage list and in its
change tier section inside a stamped packet, with the packet check
refusing the corrected wording. The same rounds showed a copy from
an instruction file inheriting the instruction flag under a plain
destination name, an ambient diff.renameLimit switching inexact
detection off in silence, and copies from sources the range never
touched reading as plain additions. Every test here fails against
the pre fix extractor and checker pair and passes against the
fixed pair.

Round 161 of the same program showed one narrower labelling
failure standing after that pair landed. A copied entry measured
as text through the binary measurement path, because the tree
attributes mark it binary or because its source held binary
content at the base, carried rename header lines inside its own
diff body when its source was renamed away in the same range,
while its manifest and its packet prose correctly said copied.
The packet check stamped that packet, because no rule read the
git header lines inside a diff body against the manifest status.
The header wording tests below pin the graded shape beside its
two controls and beside the partial copy and binary to text
forms the same mechanism covers, and beside the mixed shape
round 185 widened it with, two copies of one source in a single
range where only the first copy carries the attributes mark, so
the correction stands per entry on the marked path alone and
the unmarked sibling wording stands untouched. The checker
tests pin the
new rule on its own through a direct call with no recount, so
each test fails when its own side of the fix is reverted.
"""

import importlib.util
import io
import json
import os
import shutil
import subprocess
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


def load_at(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


extract_mod = load_at(EXTRACT_PATH, "extract_for_copy_pair_tests")
check_mod = load_at(CHECK_PATH, "check_packet_for_copy_pair_tests")


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


def lines(prefix, count=100):
    return "".join("%s line %d\n" % (prefix, i) for i in range(count))


def edited(text, count, prefix):
    rows = text.splitlines(True)
    for index in range(count):
        rows[index] = "%s new %d\n" % (prefix, index)
    return "".join(rows)


def build_copy_repo(repo):
    """One base commit and one head commit holding every copy shape."""
    init_repo(repo)
    src = lines("src")
    (repo / "src.py").write_text(src)
    (repo / "bin.dat").write_bytes(bytes(range(256)) * 2)
    os.symlink("target-a", repo / "oldlink")
    (repo / "mode.py").write_text(lines("mode"))
    (repo / "package-lock.json").write_text(lines("lock"))
    (repo / "AGENTS.md").write_text(lines("guide", 20))
    (repo / "guide-src.txt").write_text(lines("plain", 20))
    (repo / "oldname.py").write_text(lines("oldname", 20))
    (repo / "untouched.py").write_text(lines("untouched", 40))
    commit_all(repo, "base")

    (repo / "src.py").write_text(edited(src, 1, "src"))
    (repo / "copy.py").write_text(src)
    (repo / "copy2.py").write_text(src)
    (repo / "partial.py").write_text(edited(src, 18, "partial"))
    old_bin = bytes(range(256)) * 2
    (repo / "bin.dat").write_bytes(b"\xff" * 16 + old_bin[16:])
    (repo / "bincopy.dat").write_bytes(old_bin)
    (repo / "oldlink").unlink()
    os.symlink("target-b", repo / "oldlink")
    os.symlink("target-a", repo / "newlink")
    (repo / "mode.py").write_text(edited(lines("mode"), 1, "mode"))
    exec_copy = repo / "execcopy.py"
    exec_copy.write_text(lines("mode"))
    exec_copy.chmod(0o755)
    (repo / "package-lock.json").write_text(
        edited(lines("lock"), 1, "lock")
    )
    (repo / "yarn.lock").write_text(lines("lock"))
    guide = lines("guide", 20)
    (repo / "AGENTS.md").write_text(edited(guide, 1, "guide"))
    (repo / "notes.txt").write_text(guide)
    plain = lines("plain", 20)
    (repo / "guide-src.txt").write_text(edited(plain, 1, "plain"))
    (repo / "CLAUDE.md").write_text(plain)
    (repo / "oldname.py").rename(repo / "newname.py")
    (repo / "ucopy.py").write_text(lines("untouched", 40))
    return commit_all(repo, "copies")


class CopyPairFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = RetryingTemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.head = build_copy_repo(self.repo)
        self.out = Path(self.tmp.name) / "packet"
        with redirect_stderr(io.StringIO()):
            code = extract_mod.main([
                "--repo", str(self.repo), "--out", str(self.out),
                "--range", "HEAD~1..HEAD", "--tiers", "0,1",
            ])
        self.assertEqual(code, 0)
        self.manifest = json.loads(
            (self.out / "manifest.json").read_text(encoding="utf-8")
        )
        self.packet = (self.out / "packet.md").read_text(encoding="utf-8")
        self.by_path = {
            entry["path"]: entry for entry in self.manifest["files"]
        }

    def run_check(self, out=None):
        with redirect_stderr(io.StringIO()):
            return check_mod.main(
                [str(out or self.out), "--repo", str(self.repo)]
            )


class TestCopyLabelling(CopyPairFixture):
    COPY_PATHS = (
        "copy.py", "copy2.py", "partial.py", "bincopy.dat",
        "newlink", "execcopy.py", "yarn.lock", "notes.txt",
        "CLAUDE.md", "ucopy.py",
    )

    def test_every_copy_shape_is_a_copy_in_the_manifest(self):
        for path in self.COPY_PATHS:
            entry = self.by_path[path]
            self.assertEqual(entry["status"], "copied", entry)
            self.assertTrue(
                entry["status_code"].startswith("C"), entry
            )
            self.assertIsNotNone(entry["old_path"], entry)

    def test_copies_are_labelled_copied_in_triage_and_change_tier(self):
        for path in self.COPY_PATHS:
            entry = self.by_path[path]
            marker = ", instruction file" if entry[
                "instruction_file"
            ] else ""
            self.assertIn(
                "- %s (copied%s, copied from %s)"
                % (path, marker, entry["old_path"]),
                self.packet,
            )
            self.assertIn(
                "Copied from: %s" % entry["old_path"], self.packet
            )
        self.assertNotIn("renamed from src.py", self.packet)
        self.assertNotIn("Renamed from: src.py", self.packet)
        self.assertNotIn("renamed from AGENTS.md", self.packet)
        self.assertNotIn("Renamed from: AGENTS.md", self.packet)

    def test_a_rename_is_still_labelled_renamed(self):
        entry = self.by_path["newname.py"]
        self.assertEqual(entry["status"], "renamed", entry)
        self.assertIn(
            "- newname.py (renamed, renamed from oldname.py)",
            self.packet,
        )
        self.assertIn("Renamed from: oldname.py", self.packet)

    def test_partial_copy_carries_its_similarity_code(self):
        entry = self.by_path["partial.py"]
        self.assertEqual(entry["status"], "copied", entry)
        self.assertNotEqual(entry["status_code"], "C100", entry)
        self.assertGreater(entry["additions"], 0, entry)

    def test_copy_from_an_untouched_source_reads_as_a_copy(self):
        entry = self.by_path["ucopy.py"]
        self.assertEqual(entry["status"], "copied", entry)
        self.assertEqual(entry["old_path"], "untouched.py", entry)
        self.assertEqual(entry["additions"], 0, entry)
        self.assertEqual(entry["deletions"], 0, entry)


class TestInstructionFlagFromDestination(CopyPairFixture):
    def test_copy_from_an_instruction_source_is_not_flagged(self):
        entry = self.by_path["notes.txt"]
        self.assertEqual(entry["status"], "copied", entry)
        self.assertEqual(entry["old_path"], "AGENTS.md", entry)
        self.assertFalse(entry["instruction_file"], entry)
        self.assertIn("- notes.txt (copied, copied from AGENTS.md)",
                      self.packet)

    def test_copy_to_an_instruction_name_is_flagged_on_its_own_path(self):
        entry = self.by_path["CLAUDE.md"]
        self.assertEqual(entry["status"], "copied", entry)
        self.assertTrue(entry["instruction_file"], entry)
        self.assertTrue(self.by_path["AGENTS.md"]["instruction_file"])


class TestExtractorVerifierPair(CopyPairFixture):
    def test_the_genuine_copy_packet_stamps(self):
        self.assertEqual(self.run_check(), 0)

    def test_the_old_mislabel_is_refused(self):
        out = Path(self.tmp.name) / "mislabelled"
        shutil.copytree(self.out, out)
        text = (out / "packet.md").read_text(encoding="utf-8")
        text = text.replace("copied from", "renamed from")
        text = text.replace("Copied from:", "Renamed from:")
        (out / "packet.md").write_text(text, encoding="utf-8")
        self.assertEqual(self.run_check(out), 1)

    def test_the_old_inherited_instruction_flag_is_refused(self):
        out = Path(self.tmp.name) / "wrongflag"
        shutil.copytree(self.out, out)
        manifest = json.loads(
            (out / "manifest.json").read_text(encoding="utf-8")
        )
        for entry in manifest["files"]:
            if entry["path"] == "notes.txt":
                entry["instruction_file"] = True
        (out / "manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
        text = (out / "packet.md").read_text(encoding="utf-8")
        text = text.replace(
            "- notes.txt (copied, copied from AGENTS.md)",
            "- notes.txt (copied, instruction file, "
            "copied from AGENTS.md)",
        )
        (out / "packet.md").write_text(text, encoding="utf-8")
        self.assertEqual(self.run_check(out), 1)


ORIG20 = "".join("line %d\n" % index for index in range(20))


def build_header_repo(repo, marked, standing, partial=False):
    """One range holding a copy and, unless standing, its rename.

    The copy source is renamed away to an exact destination in
    the same range, beside one ordinary edit, in the shape round
    161 graded. The standing control keeps the source in the
    tree under its own name with one line changed instead.
    """
    init_repo(repo)
    (repo / "orig.py").write_text(ORIG20)
    if marked:
        (repo / ".gitattributes").write_text("copy.py binary\n")
    (repo / "plain.py").write_text("p = 1\n")
    commit_all(repo, "base")
    if standing:
        rows = ORIG20.splitlines(True)
        rows[0] = "orig new 0\n"
        (repo / "orig.py").write_text("".join(rows))
    else:
        (repo / "moved.py").write_text(ORIG20)
        (repo / "orig.py").unlink()
    copy_text = ORIG20
    if partial:
        rows = ORIG20.splitlines(True)
        rows[0] = "copy new 0\n"
        rows[1] = "copy new 1\n"
        copy_text = "".join(rows)
    (repo / "copy.py").write_text(copy_text)
    (repo / "plain.py").write_text("p = 2\n")
    commit_all(repo, "head")


def build_transition_repo(repo):
    """One range whose copy source held binary content at base.

    The source bytes are the copy text with a NUL byte standing
    in its first line, so the copy destination is plain text at
    the head while its source side is binary content, and the
    entry travels the binary measurement path by its binary to
    text transition receipt rather than by an attributes mark.
    """
    init_repo(repo)
    base_bytes = ORIG20.encode().replace(
        b"line 0\n", b"line \x00 0\n"
    )
    (repo / "orig.py").write_bytes(base_bytes)
    (repo / "plain.py").write_text("p = 1\n")
    commit_all(repo, "base")
    (repo / "moved.py").write_bytes(base_bytes)
    (repo / "orig.py").unlink()
    (repo / "copy.py").write_bytes(ORIG20.encode())
    (repo / "plain.py").write_text("p = 2\n")
    commit_all(repo, "head")


def build_mixed_repo(repo):
    """One range holding two copies of one source, one marked.

    The attributes file marks the first copy binary alone, and
    the source is renamed away in the same range, in the shape
    round 185 widened round 161 with. The marked copy travels
    the binary measurement path while its unmarked sibling
    travels the ordinary path, so the wording split between
    their sections isolates the marked per file reading.
    """
    init_repo(repo)
    (repo / "orig.py").write_text(ORIG20)
    (repo / ".gitattributes").write_text("copy1.py binary\n")
    (repo / "plain.py").write_text("p = 1\n")
    commit_all(repo, "base")
    (repo / "moved.py").write_text(ORIG20)
    (repo / "orig.py").unlink()
    (repo / "copy1.py").write_text(ORIG20)
    (repo / "copy2.py").write_text(ORIG20)
    (repo / "plain.py").write_text("p = 2\n")
    commit_all(repo, "head")


def extract_header_case(tmp, label, builder, *builder_args):
    repo = Path(tmp) / (label + "-repo")
    builder(repo, *builder_args)
    out = Path(tmp) / (label + "-out")
    with redirect_stderr(io.StringIO()):
        code = extract_mod.main([
            "--repo", str(repo), "--out", str(out),
            "--range", "HEAD~1..HEAD", "--tiers", "0,1",
        ])
    if code != 0:
        raise AssertionError("extractor exited %d for %s" % (code, label))
    manifest = json.loads(
        (out / "manifest.json").read_text(encoding="utf-8")
    )
    packet = (out / "packet.md").read_text(encoding="utf-8")
    return repo, out, manifest, packet


def section_of(packet, name):
    tier = packet.split("## T1 The change", 1)[1]
    for part in tier.split("\n### ")[1:]:
        if part.split("\n", 1)[0].strip() == name:
            return part
    raise AssertionError("no change tier section for %s" % name)


def header_lines(section):
    return [
        line for line in section.splitlines()
        if line.startswith((
            "copy from ", "copy to ", "rename from ", "rename to ",
            "similarity index",
        ))
    ]


class TestCopyRenameHeaderWording(unittest.TestCase):
    """Round 161. The diff body header must say what the manifest says."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = RetryingTemporaryDirectory()
        root = cls.tmp.name
        cls.cases = {
            "graded": extract_header_case(
                root, "graded", build_header_repo, True, False
            ),
            "standing": extract_header_case(
                root, "standing", build_header_repo, True, True
            ),
            "unmarked": extract_header_case(
                root, "unmarked", build_header_repo, False, False
            ),
            "partial": extract_header_case(
                root, "partial", build_header_repo, True, False, True
            ),
            "transition": extract_header_case(
                root, "transition", build_transition_repo
            ),
            "mixed": extract_header_case(
                root, "mixed", build_mixed_repo
            ),
        }

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def entry_of(self, label, path):
        _repo, _out, manifest, _packet = self.cases[label]
        for entry in manifest["files"]:
            if entry["path"] == path:
                return entry
        self.fail("no manifest entry for %s in %s" % (path, label))

    def totals_of(self, label):
        _repo, _out, manifest, _packet = self.cases[label]
        return (
            sum(entry["additions"] for entry in manifest["files"]),
            sum(entry["deletions"] for entry in manifest["files"]),
        )

    def test_graded_marked_copy_source_renamed_away_says_copy(self):
        entry = self.entry_of("graded", "copy.py")
        self.assertEqual(entry["status"], "copied", entry)
        self.assertEqual(entry["status_code"], "C100", entry)
        self.assertEqual(entry["old_path"], "orig.py", entry)
        self.assertTrue(entry["attribute_text"], entry)
        self.assertEqual(
            (entry["additions"], entry["deletions"]), (0, 0), entry
        )
        packet = self.cases["graded"][3]
        self.assertEqual(
            header_lines(section_of(packet, "copy.py")),
            [
                "similarity index 100%",
                "copy from orig.py",
                "copy to copy.py",
            ],
        )
        self.assertEqual(
            header_lines(section_of(packet, "moved.py")),
            [
                "similarity index 100%",
                "rename from orig.py",
                "rename to moved.py",
            ],
        )
        self.assertEqual(self.totals_of("graded"), (1, 1))

    def test_graded_copy_headers_stand_in_both_stored_chunk_forms(self):
        repo, _out, _manifest, _packet = self.cases["graded"]
        base = git(repo, "rev-parse", "HEAD~1")
        head = git(repo, "rev-parse", "HEAD")
        change = extract_mod.fetch_change(repo, base, head)
        entry = [
            item for item in change["files"]
            if item["path"] == "copy.py"
        ][0]
        self.assertEqual(entry["status"], "copied", entry)
        for flag in ("-W", "-U0"):
            chunk = extract_mod.per_file_text_diff(
                repo, base, head, entry, flag
            )
            self.assertIn("copy from orig.py", chunk)
            self.assertIn("copy to copy.py", chunk)
            self.assertNotIn("rename from orig.py", chunk)
            self.assertNotIn("rename to copy.py", chunk)

    def test_marked_copy_with_source_standing_keeps_copy_headers(self):
        entry = self.entry_of("standing", "copy.py")
        self.assertEqual(entry["status"], "copied", entry)
        self.assertTrue(entry["attribute_text"], entry)
        packet = self.cases["standing"][3]
        self.assertEqual(
            header_lines(section_of(packet, "copy.py")),
            [
                "similarity index 100%",
                "copy from orig.py",
                "copy to copy.py",
            ],
        )
        self.assertEqual(self.totals_of("standing"), (2, 2))

    def test_unmarked_copy_with_source_renamed_away_keeps_copy(self):
        entry = self.entry_of("unmarked", "copy.py")
        self.assertEqual(entry["status"], "copied", entry)
        self.assertFalse(entry["attribute_text"], entry)
        packet = self.cases["unmarked"][3]
        self.assertEqual(
            header_lines(section_of(packet, "copy.py")),
            [
                "similarity index 100%",
                "copy from orig.py",
                "copy to copy.py",
            ],
        )
        moved = self.entry_of("unmarked", "moved.py")
        self.assertEqual(moved["status"], "renamed", moved)
        self.assertEqual(self.totals_of("unmarked"), (1, 1))

    def test_partial_marked_copy_source_renamed_away_says_copy(self):
        entry = self.entry_of("partial", "copy.py")
        self.assertEqual(entry["status"], "copied", entry)
        self.assertTrue(entry["status_code"].startswith("C"), entry)
        self.assertNotEqual(entry["status_code"], "C100", entry)
        self.assertTrue(entry["attribute_text"], entry)
        self.assertEqual(
            (entry["additions"], entry["deletions"]), (2, 2), entry
        )
        packet = self.cases["partial"][3]
        found = header_lines(section_of(packet, "copy.py"))
        self.assertIn("copy from orig.py", found)
        self.assertIn("copy to copy.py", found)
        self.assertNotIn("rename from orig.py", found)
        self.assertNotIn("rename to copy.py", found)
        self.assertEqual(self.totals_of("partial"), (3, 3))

    def test_binary_to_text_copy_source_renamed_away_says_copy(self):
        entry = self.entry_of("transition", "copy.py")
        self.assertEqual(entry["status"], "copied", entry)
        self.assertTrue(entry["status_code"].startswith("C"), entry)
        self.assertTrue(entry["binary_transition"], entry)
        self.assertFalse(entry["attribute_text"], entry)
        self.assertEqual(
            (entry["additions"], entry["deletions"]), (1, 1), entry
        )
        packet = self.cases["transition"][3]
        found = header_lines(section_of(packet, "copy.py"))
        self.assertIn("copy from orig.py", found)
        self.assertIn("copy to copy.py", found)
        self.assertNotIn("rename from orig.py", found)
        self.assertNotIn("rename to copy.py", found)

    def test_mixed_two_copies_one_marked_source_renamed_away(self):
        marked = self.entry_of("mixed", "copy1.py")
        self.assertEqual(marked["status"], "copied", marked)
        self.assertEqual(marked["status_code"], "C100", marked)
        self.assertEqual(marked["old_path"], "orig.py", marked)
        self.assertTrue(marked["attribute_text"], marked)
        self.assertEqual(
            (marked["additions"], marked["deletions"]), (0, 0), marked
        )
        unmarked = self.entry_of("mixed", "copy2.py")
        self.assertEqual(unmarked["status"], "copied", unmarked)
        self.assertEqual(unmarked["status_code"], "C100", unmarked)
        self.assertEqual(unmarked["old_path"], "orig.py", unmarked)
        self.assertFalse(unmarked["attribute_text"], unmarked)
        self.assertEqual(
            (unmarked["additions"], unmarked["deletions"]), (0, 0),
            unmarked,
        )
        packet = self.cases["mixed"][3]
        self.assertEqual(
            header_lines(section_of(packet, "copy1.py")),
            [
                "similarity index 100%",
                "copy from orig.py",
                "copy to copy1.py",
            ],
        )
        self.assertEqual(
            header_lines(section_of(packet, "copy2.py")),
            [
                "similarity index 100%",
                "copy from orig.py",
                "copy to copy2.py",
            ],
        )
        self.assertEqual(
            header_lines(section_of(packet, "moved.py")),
            [
                "similarity index 100%",
                "rename from orig.py",
                "rename to moved.py",
            ],
        )
        self.assertIn(
            "copy1.py (copied, copied from orig.py)", packet
        )
        self.assertIn(
            "copy2.py (copied, copied from orig.py)", packet
        )
        self.assertEqual(self.totals_of("mixed"), (1, 1))

    def test_the_genuine_graded_packet_stamps(self):
        repo, out, _manifest, _packet = self.cases["graded"]
        with redirect_stderr(io.StringIO()):
            code = check_mod.main([str(out), "--repo", str(repo)])
        self.assertEqual(code, 0)

    def test_checker_accepts_the_genuine_graded_headers(self):
        _repo, _out, manifest, packet = self.cases["graded"]
        problems = check_mod.change_tier_problems(
            packet, manifest, None, None
        )
        self.assertEqual(problems, [])

    def test_checker_refuses_rename_headers_in_a_copied_section(self):
        _repo, _out, manifest, packet = self.cases["graded"]
        doctored = packet.replace(
            "copy from orig.py", "rename from orig.py"
        ).replace("copy to copy.py", "rename to copy.py")
        self.assertNotEqual(doctored, packet)
        problems = check_mod.change_tier_problems(
            doctored, manifest, None, None
        )
        self.assertTrue(
            any(
                "rename header lines" in problem
                and "copy.py" in problem
                for problem in problems
            ),
            problems,
        )

    def test_checker_refuses_copy_headers_in_a_renamed_section(self):
        _repo, _out, manifest, packet = self.cases["graded"]
        doctored = packet.replace(
            "rename from orig.py", "copy from orig.py"
        ).replace("rename to moved.py", "copy to moved.py")
        self.assertNotEqual(doctored, packet)
        problems = check_mod.change_tier_problems(
            doctored, manifest, None, None
        )
        self.assertTrue(
            any(
                "copy header lines" in problem
                and "moved.py" in problem
                for problem in problems
            ),
            problems,
        )


class TestRenameLimitPin(unittest.TestCase):
    def test_an_ambient_rename_limit_does_not_degrade_detection(self):
        tmp = RetryingTemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        repo = Path(tmp.name) / "repo"
        init_repo(repo)
        for index in range(6):
            (repo / ("s%d.py" % index)).write_text(
                lines("s%d" % index)
            )
        commit_all(repo, "base")
        for index in range(6):
            original = lines("s%d" % index)
            (repo / ("s%d.py" % index)).write_text(
                edited(original, 18, "s%d" % index)
            )
            (repo / ("c%d.py" % index)).write_text(
                edited(original, 18, "copy")
            )
        git(repo, "config", "diff.renameLimit", "5")
        commit_all(repo, "copies")
        out = Path(tmp.name) / "packet"
        with redirect_stderr(io.StringIO()):
            code = extract_mod.main([
                "--repo", str(repo), "--out", str(out),
                "--range", "HEAD~1..HEAD", "--tiers", "0,1",
            ])
        self.assertEqual(code, 0)
        manifest = json.loads(
            (out / "manifest.json").read_text(encoding="utf-8")
        )
        copies = [
            entry for entry in manifest["files"]
            if entry["path"].startswith("c")
        ]
        self.assertEqual(len(copies), 6, manifest["files"])
        for entry in copies:
            self.assertEqual(entry["status"], "copied", entry)
        with redirect_stderr(io.StringIO()):
            self.assertEqual(
                check_mod.main([str(out), "--repo", str(repo)]), 0
            )

    def test_a_skipped_detection_warning_fails_the_run(self):
        fake = extract_mod.Proc(
            0, "",
            "warning: exhaustive rename detection was skipped due "
            "to too many files.\n",
        )
        with mock.patch.object(
            extract_mod, "run_argv", return_value=fake
        ):
            with self.assertRaises(extract_mod.GitError):
                extract_mod.run_git(
                    Path("."), ["diff", "--name-status", "-z"]
                )

    def test_the_rename_limit_pin_is_on_every_git_invocation(self):
        self.assertIn("diff.renameLimit=0", extract_mod.GIT_PIN)


if __name__ == "__main__":
    unittest.main()
