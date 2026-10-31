"""The regeneration gate at scripts/check_regeneration.py.

The gate regenerates the shipped artefacts that claim a
provenance and compares each regeneration against the
shipped copy under a stated normalisation.
These tests pin the makefile step by name and position,
unit test the three normalisation functions on the hash
and subject and token and blame shapes the shipped packets
carry, and plant tamper shapes against every checker class
on prepared roots, a hand edit inside the shipped example
packet, a stale printed command, a printed command carrying
extra flags, a printed command missing one continuation
backslash, a printed command carrying a duplicated out
flag, a printed command carrying a shortened out flag
beside a valid decoy out flag, a printed command carrying
an out flag joined to its target by a shell expansion, a
printed command carrying a shell metacharacter token, a
printed command carrying a second command, a committed
symlink standing in place of the examples folder in the
scratch source, a symlink standing in place of the shipped
example folder in the checked tree, a symlink standing in
place of the shipped packet file pointing at a byte
identical external target, a symlink standing in place of
the shipped manifest file pointing at a byte identical
external target, a committed symlink standing in place of
the packet file in the scratch source, a printed command
carrying an absolute out target,
a printed command carrying an out target that escapes by
dotdot, a printed command carrying an out target that
names a different folder, a forged example manifest hash
set, a hand
edit inside a shipped eval packet, a symlink standing in
place of a shipped eval packet file pointing at a byte
identical external target, a symlink standing in place
of a shipped eval manifest file pointing at a byte
identical external target, a symlink standing in place
of a shipped eval diff file pointing at a byte identical
external target, a symlink standing in place of a
shipped eval sources file pointing at a byte identical
external target, a subject edit inside
the shipped proof packet, a symlink standing in place
of the shipped proof packet file pointing at a byte
identical external target, a symlink standing in place
of the shipped proof manifest file pointing at a byte
identical external target, a symlink standing in place
of the shipped proof sources file pointing at a byte
identical external target, a symlink standing in place
of the shipped proof sources file pointing at a target
whose bytes are not JSON, a symlink standing in place of
a shipped builder output file pointing at a byte
identical external target, a symlink standing in place
of the declared builder palette input pointing at a byte
identical external target, a builder writing an unshipped
name, a builder dropping a shipped output, a builder that
only reads a dropped output, a builder that only touches a
dropped output, a builder dropping a generated Python file,
a builder dropping a file in a subfolder, and a builder
deleting a shipped output, so each check fails for a real
reason. Malformed and repeated key records plant against
the example and eval and proof readers as well. A full
subprocess run of the gate inside the suite is deliberately
absent, because make check runs the gate itself one step
after the suite.
"""

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_gate():
    path = ROOT / "scripts" / "check_regeneration.py"
    spec = importlib.util.spec_from_file_location(
        "regen_check_regeneration", path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GATE = load_gate()

HASH_A = "4bb4094c1b4586cca433e8c1b7b32e4b0bec35b4"
HASH_B = "46b418895ebd14a4bfe863d20154bbca0cb25e6d"


def clone_tree(tmp):
    dest = Path(tmp) / "tree"
    result = subprocess.run(
        ["git", "clone", "-q", str(ROOT), str(dest)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError("git clone failed: %s" % result.stderr)
    return dest


class MakefileStepTest(unittest.TestCase):
    def test_the_step_stands_between_evals_and_persona(self):
        lines = (ROOT / "Makefile").read_text(
            encoding="utf-8"
        ).splitlines()
        steps = [
            line.strip() for line in lines if "scripts/check_" in line
        ]
        regen = "$(PYTHON) scripts/check_regeneration.py"
        self.assertEqual(steps.count(regen), 1)
        position = steps.index(regen)
        self.assertEqual(
            steps[position - 1], "$(PYTHON) scripts/check_evals.py"
        )
        self.assertEqual(
            steps[position + 1], "$(PYTHON) scripts/check_persona.py"
        )


class NormEvalPacketTest(unittest.TestCase):
    def test_hash_subject_token_and_blame_shapes_normalise(self):
        text = "\n".join(
            [
                "# The pericope for range %s..%s" % (HASH_A, HASH_B),
                "commit 46b4188 head",
                "46b4188 head",
                "Eval Fixture 46b41889 lines 2",
                "Packet estimate in tokens: 1284",
                "T0 included at about 65 tokens across 1 files",
                "## T1 The change",
            ]
        )
        normed = GATE.norm_eval_packet(text).splitlines()
        self.assertEqual(normed[0], "# The pericope for range @range@")
        self.assertEqual(normed[1], "commit @hash@ head")
        self.assertEqual(normed[2], "@hash@ head")
        self.assertEqual(normed[3], "Eval Fixture @hash@ lines 2")
        self.assertEqual(normed[4], "Packet estimate in tokens: @tokens@")
        self.assertEqual(
            normed[5], "T0 included at about @tokens@ tokens across 1 files"
        )
        self.assertEqual(normed[6], "## T1 The change")

    def test_a_rebuilt_history_normalises_equal(self):
        shipped = "\n".join(
            [
                "# The pericope for range %s..%s" % (HASH_A, HASH_B),
                "commit 46b4188 head",
                "Packet estimate in tokens: 1284",
            ]
        )
        rebuilt = "\n".join(
            [
                "# The pericope for range %s..%s" % (HASH_B, HASH_A),
                "commit 4bb4094 head",
                "Packet estimate in tokens: 999",
            ]
        )
        self.assertEqual(
            GATE.norm_eval_packet(shipped), GATE.norm_eval_packet(rebuilt)
        )

    def test_a_subject_or_blame_author_change_survives(self):
        shipped = "\n".join(
            [
                "commit 46b4188 head",
                "Eval Fixture 46b41889 lines 2",
            ]
        )
        forged_subject = "\n".join(
            [
                "commit 46b4188 forged",
                "Eval Fixture 46b41889 lines 2",
            ]
        )
        forged_author = "\n".join(
            [
                "commit 46b4188 head",
                "Forged Author 46b41889 lines 2",
            ]
        )
        self.assertNotEqual(
            GATE.norm_eval_packet(shipped),
            GATE.norm_eval_packet(forged_subject),
        )
        self.assertNotEqual(
            GATE.norm_eval_packet(shipped),
            GATE.norm_eval_packet(forged_author),
        )

    def test_a_framing_change_survives_the_normalisation(self):
        shipped = "## T1 The change"
        rebuilt = "## T1 The changes"
        self.assertNotEqual(
            GATE.norm_eval_packet(shipped), GATE.norm_eval_packet(rebuilt)
        )


class NormProofPacketTest(unittest.TestCase):
    def test_hashes_normalise_and_subjects_and_tokens_stay(self):
        text = "\n".join(
            [
                "# The pericope for range %s..%s" % (HASH_A, HASH_B),
                "commit 46b4188 head change",
                "46b4188 head change",
                "Eval Fixture 46b41889 lines 2",
                "Packet estimate in tokens: 2118",
            ]
        )
        normed = GATE.norm_proof_packet(text).splitlines()
        self.assertEqual(normed[0], "# The pericope for range @hash@..@hash@")
        self.assertEqual(normed[1], "commit @hash@ head change")
        self.assertEqual(normed[2], "@hash@ head change")
        self.assertEqual(normed[3], "Eval Fixture @hash@ lines 2")
        self.assertEqual(normed[4], "Packet estimate in tokens: 2118")

    def test_a_subject_change_survives_the_normalisation(self):
        shipped = "commit 46b4188 head change"
        rebuilt = "commit 46b4188 head changes"
        self.assertNotEqual(
            GATE.norm_proof_packet(shipped), GATE.norm_proof_packet(rebuilt)
        )


class ManifestCopyTest(unittest.TestCase):
    def manifest(self):
        return {
            "created_utc": "2026-10-27T12:07:00+00:00",
            "command": ["extract.py", "--range", "a..b"],
            "base": HASH_A,
            "head": HASH_B,
            "merge_base": HASH_A,
            "label": "range %s..%s" % (HASH_A, HASH_B),
            "prior_pull_requests_passage": "passage %s end" % HASH_A,
            "budget": {"estimated_tokens": 1284},
            "tiers": {"T0": {"estimated_tokens": 65, "files": 1}},
            "verified": True,
        }

    def test_run_record_fields_and_hashes_are_set_aside(self):
        copied = GATE.manifest_copy(self.manifest(), keep_tokens=True)
        self.assertNotIn("created_utc", copied)
        self.assertNotIn("command", copied)
        self.assertEqual(copied["base"], "@hash@")
        self.assertEqual(copied["head"], "@hash@")
        self.assertEqual(copied["merge_base"], "@hash@")
        self.assertEqual(copied["label"], "range @hash@..@hash@")
        self.assertEqual(
            copied["prior_pull_requests_passage"], "passage @hash@ end"
        )
        self.assertIs(copied["verified"], True)

    def test_hashes_compare_exactly_over_real_history(self):
        copied = GATE.manifest_copy(
            self.manifest(), keep_tokens=True, exact_hashes=True
        )
        self.assertEqual(copied["base"], HASH_A)
        self.assertEqual(copied["head"], HASH_B)
        self.assertEqual(copied["merge_base"], HASH_A)
        self.assertEqual(
            copied["label"], "range %s..%s" % (HASH_A, HASH_B)
        )
        self.assertEqual(
            copied["prior_pull_requests_passage"],
            "passage %s end" % HASH_A,
        )
        moved = self.manifest()
        moved["base"] = "a" * 40
        problems = GATE.manifest_problems(
            "example packet", self.manifest(), moved,
            keep_tokens=True, exact_hashes=True,
        )
        self.assertEqual(len(problems), 1)
        self.assertIn("base", problems[0])
        self.assertEqual(
            GATE.manifest_problems(
                "proof run packet", self.manifest(), moved,
                keep_tokens=True,
            ),
            [],
        )

    def test_tokens_stay_when_the_caller_keeps_them(self):
        copied = GATE.manifest_copy(self.manifest(), keep_tokens=True)
        self.assertEqual(copied["budget"]["estimated_tokens"], 1284)
        moved = self.manifest()
        moved["budget"] = {"estimated_tokens": 1300}
        problems = GATE.manifest_problems(
            "example packet", self.manifest(), moved, keep_tokens=True
        )
        self.assertEqual(len(problems), 1)
        self.assertIn("budget", problems[0])

    def test_tokens_and_label_are_set_aside_for_eval_manifests(self):
        copied = GATE.manifest_copy(self.manifest(), keep_tokens=False)
        self.assertEqual(copied["budget"]["estimated_tokens"], "@tokens@")
        self.assertEqual(
            copied["tiers"]["T0"]["estimated_tokens"], "@tokens@"
        )
        self.assertEqual(copied["label"], "@label@")
        moved = self.manifest()
        moved["budget"] = {"estimated_tokens": 1300}
        self.assertEqual(
            GATE.manifest_problems(
                "task", self.manifest(), moved, keep_tokens=False
            ),
            [],
        )


class ExampleTamperTest(unittest.TestCase):
    def test_a_hand_edit_inside_the_shipped_packet_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = clone_tree(tmp)
            packet = (
                tree
                / "examples"
                / "example-packet-991ac6a"
                / "packet.md"
            )
            text = packet.read_text(encoding="utf-8")
            self.assertIn("## T1", text)
            packet.write_text(
                text.replace("## T1", "## T1x", 1), encoding="utf-8"
            )
            problems = GATE.example_problems(tree)
            self.assertTrue(
                any("example packet differs" in p for p in problems),
                problems,
            )

    def test_a_stale_printed_command_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = clone_tree(tmp)
            index = tree / "examples" / "README.md"
            text = index.read_text(encoding="utf-8")
            self.assertIn("991ac6a", text)
            index.write_text(
                text.replace("991ac6a", "004283d"), encoding="utf-8"
            )
            problems = GATE.example_problems(tree)
            self.assertEqual(len(problems), 1)
            self.assertIn("004283d", problems[0])

    def test_a_printed_command_with_extra_flags_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = clone_tree(tmp)
            index = tree / "examples" / "README.md"
            text = index.read_text(encoding="utf-8")
            self.assertIn("--repo .", text)
            index.write_text(
                text.replace(
                    "--repo .", "--repo ./docs \\\n  --budget 5 ."
                ),
                encoding="utf-8",
            )
            problems = GATE.example_problems(tree)
            self.assertTrue(
                any(
                    "printed example command" in p for p in problems
                ),
                problems,
            )

    def test_a_printed_command_missing_a_continuation_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = clone_tree(tmp)
            index = tree / "examples" / "README.md"
            text = index.read_text(encoding="utf-8")
            self.assertIn("extract.py \\\n", text)
            index.write_text(
                text.replace("extract.py \\\n", "extract.py\n", 1),
                encoding="utf-8",
            )
            packet = (
                tree
                / "examples"
                / "example-packet-991ac6a"
                / "packet.md"
            )
            before = hashlib.sha256(packet.read_bytes()).hexdigest()
            problems = GATE.example_problems(tree)
            self.assertEqual(len(problems), 1)
            self.assertTrue(
                any(
                    "no continuation backslash" in p
                    for p in problems
                ),
                problems,
            )
            self.assertTrue(
                any("block is not run" in p for p in problems),
                problems,
            )
            self.assertEqual(
                hashlib.sha256(packet.read_bytes()).hexdigest(), before
            )

    def test_a_duplicated_out_flag_stays_out_of_the_checked_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = clone_tree(tmp)
            index = tree / "examples" / "README.md"
            text = index.read_text(encoding="utf-8")
            self.assertIn("  --repo .", text)
            index.write_text(
                text.replace(
                    "  --repo .",
                    "  --out examples/example-packet-991ac6a \\\n"
                    "  --repo .",
                    1,
                ),
                encoding="utf-8",
            )
            packet = (
                tree
                / "examples"
                / "example-packet-991ac6a"
                / "packet.md"
            )
            edited = packet.read_text(encoding="utf-8")
            self.assertIn("## T1", edited)
            packet.write_text(
                edited.replace("## T1", "## T1x", 1), encoding="utf-8"
            )
            before = hashlib.sha256(packet.read_bytes()).hexdigest()
            problems = GATE.example_problems(tree)
            self.assertEqual(len(problems), 1)
            self.assertTrue(
                any("block is not run" in p for p in problems),
                problems,
            )
            self.assertFalse(
                any("example packet differs" in p for p in problems),
                problems,
            )
            self.assertEqual(
                hashlib.sha256(packet.read_bytes()).hexdigest(), before
            )
            self.assertIn(
                "## T1x", packet.read_text(encoding="utf-8")
            )

    def test_a_shortened_out_flag_beside_a_decoy_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = clone_tree(tmp)
            index = tree / "examples" / "README.md"
            text = index.read_text(encoding="utf-8")
            self.assertIn("  --repo .", text)
            target = str(
                tree / "examples" / "example-packet-991ac6a"
            )
            index.write_text(
                text.replace(
                    "  --repo .",
                    "  --ou %s --repo ." % target,
                    1,
                ),
                encoding="utf-8",
            )
            packet = (
                tree
                / "examples"
                / "example-packet-991ac6a"
                / "packet.md"
            )
            edited = packet.read_text(encoding="utf-8")
            self.assertIn("## T1", edited)
            packet.write_text(
                edited.replace("## T1", "## T1x", 1),
                encoding="utf-8",
            )
            before = hashlib.sha256(packet.read_bytes()).hexdigest()
            problems = GATE.example_problems(tree)
            self.assertEqual(len(problems), 1)
            self.assertIn("--ou", problems[0])
            self.assertIn("block is not run", problems[0])
            self.assertEqual(
                hashlib.sha256(packet.read_bytes()).hexdigest(),
                before,
            )
            self.assertIn(
                "## T1x", packet.read_text(encoding="utf-8")
            )

    def test_an_expansion_joined_out_flag_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = clone_tree(tmp)
            index = tree / "examples" / "README.md"
            text = index.read_text(encoding="utf-8")
            self.assertIn("  --repo .", text)
            target = str(
                tree / "examples" / "example-packet-991ac6a"
            )
            index.write_text(
                text.replace(
                    "  --repo .",
                    "  --out${IFS}%s --repo ." % target,
                    1,
                ),
                encoding="utf-8",
            )
            packet = (
                tree
                / "examples"
                / "example-packet-991ac6a"
                / "packet.md"
            )
            edited = packet.read_text(encoding="utf-8")
            self.assertIn("## T1", edited)
            packet.write_text(
                edited.replace("## T1", "## T1x", 1),
                encoding="utf-8",
            )
            before = hashlib.sha256(packet.read_bytes()).hexdigest()
            problems = GATE.example_problems(tree)
            self.assertEqual(len(problems), 1)
            self.assertIn("$", problems[0])
            self.assertIn("block is not run", problems[0])
            self.assertEqual(
                hashlib.sha256(packet.read_bytes()).hexdigest(),
                before,
            )
            self.assertIn(
                "## T1x", packet.read_text(encoding="utf-8")
            )

    def test_a_metacharacter_token_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = clone_tree(tmp)
            index = tree / "examples" / "README.md"
            text = index.read_text(encoding="utf-8")
            self.assertIn("  --repo .", text)
            index.write_text(
                text.replace(
                    "  --repo .",
                    "  --repo .; echo planted",
                    1,
                ),
                encoding="utf-8",
            )
            packet = (
                tree
                / "examples"
                / "example-packet-991ac6a"
                / "packet.md"
            )
            before = hashlib.sha256(packet.read_bytes()).hexdigest()
            problems = GATE.example_problems(tree)
            self.assertEqual(len(problems), 1)
            self.assertIn(";", problems[0])
            self.assertIn("block is not run", problems[0])
            self.assertEqual(
                hashlib.sha256(packet.read_bytes()).hexdigest(),
                before,
            )

    def test_a_second_command_in_the_block_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = clone_tree(tmp)
            index = tree / "examples" / "README.md"
            text = index.read_text(encoding="utf-8")
            self.assertIn("  --repo .\n```", text)
            index.write_text(
                text.replace(
                    "  --repo .\n```",
                    "  --repo .\npython3 --version\n```",
                    1,
                ),
                encoding="utf-8",
            )
            packet = (
                tree
                / "examples"
                / "example-packet-991ac6a"
                / "packet.md"
            )
            before = hashlib.sha256(packet.read_bytes()).hexdigest()
            problems = GATE.example_problems(tree)
            self.assertEqual(len(problems), 1)
            self.assertIn("block is not run", problems[0])
            self.assertTrue(
                any(
                    "continuation backslash" in p
                    for p in problems
                ),
                problems,
            )
            self.assertEqual(
                hashlib.sha256(packet.read_bytes()).hexdigest(),
                before,
            )

    def test_a_committed_parent_symlink_in_the_scratch_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = clone_tree(tmp)
            external = Path(tmp) / "external-examples"
            shutil.copytree(tree / "examples", external)
            sentinel = (
                external
                / "example-packet-991ac6a"
                / "sentinel.txt"
            )
            sentinel.write_text("sentinel\n", encoding="utf-8")
            shutil.rmtree(tree / "examples")
            os.symlink(external, tree / "examples")
            for args in (
                ("config", "user.name", "Gate Test"),
                ("config", "user.email", "gate@example.invalid"),
                ("add", "-A"),
                ("commit", "-q", "-m", "plant the parent symlink"),
            ):
                result = subprocess.run(
                    ["git", "-C", str(tree)] + list(args),
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
            block, parse_problems = GATE.printed_example_block(tree)
            self.assertEqual(parse_problems, [])
            folder = (
                tree / "examples" / "example-packet-991ac6a"
            )
            shipped = (folder / "packet.md").read_text(
                encoding="utf-8"
            )
            direct = GATE.example_regeneration_problems(
                block, tree, folder, shipped
            )
            self.assertTrue(
                any("symlink" in p for p in direct), direct
            )
            self.assertTrue(
                any("nothing is deleted" in p for p in direct),
                direct,
            )
            problems = GATE.example_problems(tree)
            self.assertTrue(
                any("symlink" in p for p in problems), problems
            )
            self.assertTrue(sentinel.is_file())
            self.assertEqual(
                sentinel.read_text(encoding="utf-8"), "sentinel\n"
            )
            self.assertEqual(
                (external / "example-packet-991ac6a" / "packet.md")
                .read_text(encoding="utf-8"),
                shipped,
            )

    def test_a_symlink_at_the_shipped_folder_is_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = clone_tree(tmp)
            folder = (
                tree / "examples" / "example-packet-991ac6a"
            )
            external = Path(tmp) / "external-packet"
            shutil.copytree(folder, external)
            external_packet = external / "packet.md"
            text = external_packet.read_text(encoding="utf-8")
            self.assertIn("## T1", text)
            external_packet.write_text(
                text.replace("## T1", "## T1x", 1),
                encoding="utf-8",
            )
            before = hashlib.sha256(
                external_packet.read_bytes()
            ).hexdigest()
            shutil.rmtree(folder)
            os.symlink(external, folder)
            problems = GATE.example_problems(tree)
            self.assertEqual(len(problems), 1)
            self.assertIn("symlink", problems[0])
            self.assertIn("real file in a real folder", problems[0])
            self.assertEqual(
                hashlib.sha256(
                    external_packet.read_bytes()
                ).hexdigest(),
                before,
            )
            self.assertIn(
                "## T1x",
                external_packet.read_text(encoding="utf-8"),
            )

    def test_a_packet_file_symlink_to_an_identical_target_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = clone_tree(tmp)
            packet = (
                tree
                / "examples"
                / "example-packet-991ac6a"
                / "packet.md"
            )
            external = Path(tmp) / "external-packet-target.md"
            external.write_bytes(packet.read_bytes())
            before = hashlib.sha256(
                external.read_bytes()
            ).hexdigest()
            self.assertEqual(
                before,
                hashlib.sha256(packet.read_bytes()).hexdigest(),
            )
            packet.unlink()
            os.symlink(external, packet)
            self.assertTrue(packet.is_symlink())
            problems = GATE.example_problems(tree)
            self.assertEqual(len(problems), 1)
            self.assertIn("packet.md", problems[0])
            self.assertIn("symlink", problems[0])
            self.assertEqual(
                hashlib.sha256(
                    external.read_bytes()
                ).hexdigest(),
                before,
            )

    def test_a_manifest_file_symlink_to_an_identical_target_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = clone_tree(tmp)
            manifest = (
                tree
                / "examples"
                / "example-packet-991ac6a"
                / "manifest.json"
            )
            external = Path(tmp) / "external-manifest-target.json"
            external.write_bytes(manifest.read_bytes())
            before = hashlib.sha256(
                external.read_bytes()
            ).hexdigest()
            self.assertEqual(
                before,
                hashlib.sha256(manifest.read_bytes()).hexdigest(),
            )
            manifest.unlink()
            os.symlink(external, manifest)
            self.assertTrue(manifest.is_symlink())
            problems = GATE.example_problems(tree)
            self.assertEqual(len(problems), 1)
            self.assertIn("manifest.json", problems[0])
            self.assertIn("symlink", problems[0])
            self.assertEqual(
                hashlib.sha256(
                    external.read_bytes()
                ).hexdigest(),
                before,
            )

    def test_a_committed_packet_symlink_in_the_scratch_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = clone_tree(tmp)
            packet = (
                tree
                / "examples"
                / "example-packet-991ac6a"
                / "packet.md"
            )
            external = Path(tmp) / "external-scratch-packet.md"
            external.write_bytes(packet.read_bytes())
            before = hashlib.sha256(
                external.read_bytes()
            ).hexdigest()
            self.assertEqual(
                before,
                hashlib.sha256(packet.read_bytes()).hexdigest(),
            )
            packet.unlink()
            os.symlink(external, packet)
            for args in (
                ("config", "user.name", "Gate Test"),
                ("config", "user.email", "gate@example.invalid"),
                ("add", "-A"),
                ("commit", "-q", "-m", "plant the packet symlink"),
            ):
                result = subprocess.run(
                    ["git", "-C", str(tree)] + list(args),
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
            block, parse_problems = GATE.printed_example_block(tree)
            self.assertEqual(parse_problems, [])
            folder = (
                tree / "examples" / "example-packet-991ac6a"
            )
            shipped = (folder / "packet.md").read_text(
                encoding="utf-8"
            )
            direct = GATE.example_regeneration_problems(
                block, tree, folder, shipped
            )
            self.assertEqual(len(direct), 1)
            self.assertTrue(
                any("symlink" in p for p in direct), direct
            )
            self.assertTrue(
                any("nothing is deleted" in p for p in direct),
                direct,
            )
            self.assertEqual(
                hashlib.sha256(
                    external.read_bytes()
                ).hexdigest(),
                before,
            )
            self.assertEqual(
                external.read_text(encoding="utf-8"), shipped
            )

    def test_an_absolute_out_target_is_refused_and_not_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = clone_tree(tmp)
            index = tree / "examples" / "README.md"
            text = index.read_text(encoding="utf-8")
            self.assertIn(
                "  --out examples/\\\nexample-packet-991ac6a \\\n",
                text,
            )
            target = str(
                tree
                / "examples"
                / "example-packet-991ac6a"
            )
            index.write_text(
                text.replace(
                    "  --out examples/\\\n"
                    "example-packet-991ac6a \\\n",
                    "  --out %s \\\n" % target,
                    1,
                ),
                encoding="utf-8",
            )
            packet = (
                tree
                / "examples"
                / "example-packet-991ac6a"
                / "packet.md"
            )
            edited = packet.read_text(encoding="utf-8")
            self.assertIn("## T1", edited)
            packet.write_text(
                edited.replace("## T1", "## T1x", 1),
                encoding="utf-8",
            )
            before = hashlib.sha256(packet.read_bytes()).hexdigest()
            problems = GATE.example_problems(tree)
            self.assertEqual(len(problems), 1)
            self.assertIn("absolute out target", problems[0])
            self.assertIn(target, problems[0])
            self.assertIn("block is not run", problems[0])
            self.assertEqual(
                hashlib.sha256(packet.read_bytes()).hexdigest(),
                before,
            )
            self.assertIn(
                "## T1x", packet.read_text(encoding="utf-8")
            )

    def test_a_dotdot_escape_out_target_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = clone_tree(tmp)
            index = tree / "examples" / "README.md"
            text = index.read_text(encoding="utf-8")
            self.assertIn(
                "  --out examples/\\\nexample-packet-991ac6a \\\n",
                text,
            )
            index.write_text(
                text.replace(
                    "  --out examples/\\\n"
                    "example-packet-991ac6a \\\n",
                    "  --out examples/../../outside-packet \\\n",
                    1,
                ),
                encoding="utf-8",
            )
            packet = (
                tree
                / "examples"
                / "example-packet-991ac6a"
                / "packet.md"
            )
            before = hashlib.sha256(packet.read_bytes()).hexdigest()
            problems = GATE.example_problems(tree)
            self.assertEqual(len(problems), 1)
            self.assertIn(
                "examples/../../outside-packet", problems[0]
            )
            self.assertIn("escapes the scratch", problems[0])
            self.assertIn("block is not run", problems[0])
            self.assertEqual(
                hashlib.sha256(packet.read_bytes()).hexdigest(),
                before,
            )

    def test_a_different_folder_out_target_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = clone_tree(tmp)
            index = tree / "examples" / "README.md"
            text = index.read_text(encoding="utf-8")
            self.assertIn(
                "  --out examples/\\\nexample-packet-991ac6a \\\n",
                text,
            )
            index.write_text(
                text.replace(
                    "  --out examples/\\\n"
                    "example-packet-991ac6a \\\n",
                    "  --out examples/other-folder \\\n",
                    1,
                ),
                encoding="utf-8",
            )
            packet = (
                tree
                / "examples"
                / "example-packet-991ac6a"
                / "packet.md"
            )
            before = hashlib.sha256(packet.read_bytes()).hexdigest()
            problems = GATE.example_problems(tree)
            self.assertEqual(len(problems), 1)
            self.assertIn("examples/other-folder", problems[0])
            self.assertIn(
                "not to the shipped example folder", problems[0]
            )
            self.assertIn("block is not run", problems[0])
            self.assertEqual(
                hashlib.sha256(packet.read_bytes()).hexdigest(),
                before,
            )

    def test_a_forged_example_manifest_hash_set_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = clone_tree(tmp)
            manifest = (
                tree
                / "examples"
                / "example-packet-991ac6a"
                / "manifest.json"
            )
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["base"] = "a" * 40
            data["head"] = "b" * 40
            data["merge_base"] = "c" * 40
            data["created_utc"] = "not-a-date"
            data["command"] = ["extract.py", "--repo", "/elsewhere"]
            manifest.write_text(
                json.dumps(data, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            problems = GATE.example_problems(tree)
            self.assertTrue(
                any(
                    "manifest" in p and "base" in p for p in problems
                ),
                problems,
            )

    def test_a_repeated_key_in_the_example_manifest_is_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = clone_tree(tmp)
            manifest = (
                tree
                / "examples"
                / "example-packet-991ac6a"
                / "manifest.json"
            )
            text = manifest.read_text(encoding="utf-8")
            self.assertIn('"verified"', text)
            manifest.write_text(
                text.replace(
                    "{\n", '{\n  "verified": true,\n', 1
                ),
                encoding="utf-8",
            )
            problems = GATE.example_problems(tree)
            self.assertTrue(
                any("repeated key" in p for p in problems), problems
            )

    def test_a_wrong_typed_example_manifest_is_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = clone_tree(tmp)
            manifest = (
                tree
                / "examples"
                / "example-packet-991ac6a"
                / "manifest.json"
            )
            manifest.write_text("[]\n", encoding="utf-8")
            problems = GATE.example_problems(tree)
            self.assertTrue(
                any(
                    "does not hold a JSON object" in p
                    for p in problems
                ),
                problems,
            )


def copy_fixture(tmp, source_rel, names, dest_rel=None):
    root = Path(tmp) / "root"
    source = ROOT / source_rel
    dest = root / (dest_rel or source_rel)
    dest.mkdir(parents=True, exist_ok=True)
    for name in names:
        shutil.copyfile(source / name, dest / name)
    return root


def fixture_root(tmp, layout):
    root = Path(tmp) / "root"
    for rel, content in layout.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8")
    return root


class EvalTamperTest(unittest.TestCase):
    TASK_FILES = (
        "sources.json",
        "diff.patch",
        "packet.md",
        "manifest.json",
        "planted.md",
    )

    def test_a_hand_edit_inside_a_shipped_eval_packet_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_fixture(
                tmp, "evals/tasks/task-01", self.TASK_FILES
            )
            packet = (
                root / "evals" / "tasks" / "task-01" / "packet.md"
            )
            text = packet.read_text(encoding="utf-8")
            self.assertIn("## T1 The change", text)
            packet.write_text(
                text.replace(
                    "## T1 The change", "## T1 The changes", 1
                ),
                encoding="utf-8",
            )
            problems = GATE.eval_problems(root)
            self.assertTrue(
                any("task-01" in p for p in problems), problems
            )

    def test_an_eval_packet_file_symlink_to_an_identical_target_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_fixture(
                tmp, "evals/tasks/task-01", self.TASK_FILES
            )
            packet = (
                root / "evals" / "tasks" / "task-01" / "packet.md"
            )
            external = Path(tmp) / "external-eval-packet-target.md"
            external.write_bytes(packet.read_bytes())
            before = hashlib.sha256(
                external.read_bytes()
            ).hexdigest()
            self.assertEqual(
                before,
                hashlib.sha256(packet.read_bytes()).hexdigest(),
            )
            packet.unlink()
            os.symlink(external, packet)
            self.assertTrue(packet.is_symlink())
            problems = GATE.eval_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("eval task", problems[0])
            self.assertIn("packet.md", problems[0])
            self.assertIn("symlink", problems[0])
            self.assertEqual(
                hashlib.sha256(
                    external.read_bytes()
                ).hexdigest(),
                before,
            )

    def test_an_eval_manifest_file_symlink_to_an_identical_target_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_fixture(
                tmp, "evals/tasks/task-01", self.TASK_FILES
            )
            manifest = (
                root / "evals" / "tasks" / "task-01" / "manifest.json"
            )
            external = Path(tmp) / "external-eval-manifest-target.json"
            external.write_bytes(manifest.read_bytes())
            before = hashlib.sha256(
                external.read_bytes()
            ).hexdigest()
            self.assertEqual(
                before,
                hashlib.sha256(manifest.read_bytes()).hexdigest(),
            )
            manifest.unlink()
            os.symlink(external, manifest)
            self.assertTrue(manifest.is_symlink())
            problems = GATE.eval_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("eval task", problems[0])
            self.assertIn("manifest.json", problems[0])
            self.assertIn("symlink", problems[0])
            self.assertEqual(
                hashlib.sha256(
                    external.read_bytes()
                ).hexdigest(),
                before,
            )

    def test_an_eval_diff_file_symlink_to_an_identical_target_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_fixture(
                tmp, "evals/tasks/task-01", self.TASK_FILES
            )
            diff = (
                root / "evals" / "tasks" / "task-01" / "diff.patch"
            )
            external = Path(tmp) / "external-eval-diff-target.patch"
            external.write_bytes(diff.read_bytes())
            before = hashlib.sha256(
                external.read_bytes()
            ).hexdigest()
            self.assertEqual(
                before,
                hashlib.sha256(diff.read_bytes()).hexdigest(),
            )
            diff.unlink()
            os.symlink(external, diff)
            self.assertTrue(diff.is_symlink())
            problems = GATE.eval_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("eval task", problems[0])
            self.assertIn("diff.patch", problems[0])
            self.assertIn("symlink", problems[0])
            self.assertEqual(
                hashlib.sha256(
                    external.read_bytes()
                ).hexdigest(),
                before,
            )

    def test_an_eval_sources_file_symlink_to_an_identical_target_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_fixture(
                tmp, "evals/tasks/task-01", self.TASK_FILES
            )
            sources = (
                root / "evals" / "tasks" / "task-01" / "sources.json"
            )
            external = Path(tmp) / "external-eval-sources-target.json"
            external.write_bytes(sources.read_bytes())
            before = hashlib.sha256(
                external.read_bytes()
            ).hexdigest()
            self.assertEqual(
                before,
                hashlib.sha256(sources.read_bytes()).hexdigest(),
            )
            sources.unlink()
            os.symlink(external, sources)
            self.assertTrue(sources.is_symlink())
            problems = GATE.eval_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("eval task", problems[0])
            self.assertIn("sources.json", problems[0])
            self.assertIn("symlink", problems[0])
            self.assertEqual(
                hashlib.sha256(
                    external.read_bytes()
                ).hexdigest(),
                before,
            )

    def test_a_repeated_key_in_an_eval_manifest_is_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_fixture(
                tmp, "evals/tasks/task-01", self.TASK_FILES
            )
            manifest = (
                root / "evals" / "tasks" / "task-01" / "manifest.json"
            )
            text = manifest.read_text(encoding="utf-8")
            self.assertIn('"verified"', text)
            manifest.write_text(
                text.replace(
                    "{\n", '{\n  "verified": true,\n', 1
                ),
                encoding="utf-8",
            )
            problems = GATE.eval_problems(root)
            self.assertTrue(
                any("repeated key" in p for p in problems), problems
            )

    def test_a_wrong_typed_eval_manifest_is_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_fixture(
                tmp, "evals/tasks/task-01", self.TASK_FILES
            )
            manifest = (
                root / "evals" / "tasks" / "task-01" / "manifest.json"
            )
            manifest.write_text(
                '"a string"\n', encoding="utf-8"
            )
            problems = GATE.eval_problems(root)
            self.assertTrue(
                any(
                    "does not hold a JSON object" in p
                    for p in problems
                ),
                problems,
            )


class ProofTamperTest(unittest.TestCase):
    PROOF_FILES = ("sources.json", "packet.md", "manifest.json")

    def test_a_subject_edit_inside_the_proof_packet_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_fixture(
                tmp, "workflows/proof-run", self.PROOF_FILES
            )
            packet = root / "workflows" / "proof-run" / "packet.md"
            text = packet.read_text(encoding="utf-8")
            self.assertIn("head change", text)
            packet.write_text(
                text.replace("head change", "head changes"),
                encoding="utf-8",
            )
            problems = GATE.proof_problems(root)
            self.assertTrue(
                any("proof run packet" in p for p in problems),
                problems,
            )

    def test_a_proof_packet_file_symlink_to_an_identical_target_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_fixture(
                tmp, "workflows/proof-run", self.PROOF_FILES
            )
            packet = root / "workflows" / "proof-run" / "packet.md"
            external = Path(tmp) / "external-proof-packet-target.md"
            external.write_bytes(packet.read_bytes())
            before = hashlib.sha256(
                external.read_bytes()
            ).hexdigest()
            self.assertEqual(
                before,
                hashlib.sha256(packet.read_bytes()).hexdigest(),
            )
            packet.unlink()
            os.symlink(external, packet)
            self.assertTrue(packet.is_symlink())
            problems = GATE.proof_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("proof run", problems[0])
            self.assertIn("packet.md", problems[0])
            self.assertIn("symlink", problems[0])
            self.assertEqual(
                hashlib.sha256(
                    external.read_bytes()
                ).hexdigest(),
                before,
            )

    def test_a_proof_manifest_file_symlink_to_an_identical_target_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_fixture(
                tmp, "workflows/proof-run", self.PROOF_FILES
            )
            manifest = (
                root / "workflows" / "proof-run" / "manifest.json"
            )
            external = Path(tmp) / "external-proof-manifest-target.json"
            external.write_bytes(manifest.read_bytes())
            before = hashlib.sha256(
                external.read_bytes()
            ).hexdigest()
            self.assertEqual(
                before,
                hashlib.sha256(manifest.read_bytes()).hexdigest(),
            )
            manifest.unlink()
            os.symlink(external, manifest)
            self.assertTrue(manifest.is_symlink())
            problems = GATE.proof_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("proof run", problems[0])
            self.assertIn("manifest.json", problems[0])
            self.assertIn("symlink", problems[0])
            self.assertEqual(
                hashlib.sha256(
                    external.read_bytes()
                ).hexdigest(),
                before,
            )

    def test_a_proof_sources_file_symlink_to_an_identical_target_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_fixture(
                tmp, "workflows/proof-run", self.PROOF_FILES
            )
            sources = (
                root / "workflows" / "proof-run" / "sources.json"
            )
            external = Path(tmp) / "external-proof-sources-target.json"
            external.write_bytes(sources.read_bytes())
            before = hashlib.sha256(
                external.read_bytes()
            ).hexdigest()
            self.assertEqual(
                before,
                hashlib.sha256(sources.read_bytes()).hexdigest(),
            )
            sources.unlink()
            os.symlink(external, sources)
            self.assertTrue(sources.is_symlink())
            problems = GATE.proof_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("proof run", problems[0])
            self.assertIn("sources.json", problems[0])
            self.assertIn("symlink", problems[0])
            self.assertEqual(
                hashlib.sha256(
                    external.read_bytes()
                ).hexdigest(),
                before,
            )

    def test_a_proof_sources_symlink_with_non_json_content_is_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_fixture(
                tmp, "workflows/proof-run", self.PROOF_FILES
            )
            sources = (
                root / "workflows" / "proof-run" / "sources.json"
            )
            external = Path(tmp) / "external-proof-sources-nonjson.txt"
            external.write_text("not json\n", encoding="utf-8")
            before = hashlib.sha256(
                external.read_bytes()
            ).hexdigest()
            sources.unlink()
            os.symlink(external, sources)
            self.assertTrue(sources.is_symlink())
            problems = GATE.proof_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("proof run", problems[0])
            self.assertIn("sources.json", problems[0])
            self.assertIn("symlink", problems[0])
            self.assertFalse(
                any(
                    "cannot be rebuilt or read" in p
                    for p in problems
                ),
                problems,
            )
            self.assertEqual(
                hashlib.sha256(
                    external.read_bytes()
                ).hexdigest(),
                before,
            )

    def test_a_malformed_proof_sources_file_is_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture_root(
                tmp,
                {"workflows/proof-run/sources.json": "{ not json\n"},
            )
            problems = GATE.proof_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("proof run", problems[0])

    def test_a_wrong_typed_proof_manifest_is_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_fixture(
                tmp, "workflows/proof-run", self.PROOF_FILES
            )
            manifest = (
                root / "workflows" / "proof-run" / "manifest.json"
            )
            manifest.write_text("42\n", encoding="utf-8")
            problems = GATE.proof_problems(root)
            self.assertTrue(
                any(
                    "does not hold a JSON object" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_repeated_key_in_the_proof_sources_is_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture_root(
                tmp,
                {
                    "workflows/proof-run/sources.json": (
                        '{"author_name": "a", '
                        '"author_name": "b"}\n'
                    )
                },
            )
            problems = GATE.proof_problems(root)
            self.assertTrue(
                any("repeated key" in p for p in problems), problems
            )


WRITE_ROGUE = (
    "from pathlib import Path\n"
    "(Path(__file__).parent / \"%s\").write_text(\"rogue\\n\")\n"
)


class BuilderTamperTest(unittest.TestCase):
    def test_a_builder_writing_an_unshipped_name_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture_root(
                tmp,
                {"docs/x/build_fake.py": WRITE_ROGUE % "rogue.txt"},
            )
            problems = GATE.builder_problems(root)
            self.assertTrue(
                any("rogue.txt" in p for p in problems), problems
            )

    def test_a_builder_dropping_a_shipped_output_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture_root(
                tmp,
                {
                    "docs/x/build_fake.py": (
                        WRITE_ROGUE % "kept.txt"
                    ).replace("rogue", "kept"),
                    "docs/x/kept.txt": "kept\n",
                    "docs/x/dropped.txt": "dropped\n",
                },
            )
            problems = GATE.builder_problems(root)
            self.assertTrue(
                any("dropped.txt" in p for p in problems), problems
            )
            self.assertFalse(
                any("kept.txt" in p for p in problems), problems
            )

    def test_a_builder_that_only_reads_a_dropped_output_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture_root(
                tmp,
                {
                    "docs/x/build_fake.py": (
                        "from pathlib import Path\n"
                        "here = Path(__file__).parent\n"
                        "(here / \"kept.txt\").write_text(\"kept\\n\")\n"
                        "(here / \"dropped.txt\").read_bytes()\n"
                    ),
                    "docs/x/kept.txt": "kept\n",
                    "docs/x/dropped.txt": "dropped\n",
                },
            )
            problems = GATE.builder_problems(root)
            self.assertTrue(
                any("dropped.txt" in p for p in problems), problems
            )
            self.assertFalse(
                any("kept.txt" in p for p in problems), problems
            )

    def test_a_builder_that_only_touches_a_dropped_output_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture_root(
                tmp,
                {
                    "docs/x/build_fake.py": (
                        "import os\n"
                        "from pathlib import Path\n"
                        "here = Path(__file__).parent\n"
                        "(here / \"kept.txt\").write_text(\"kept\\n\")\n"
                        "os.utime(here / \"dropped.txt\")\n"
                    ),
                    "docs/x/kept.txt": "kept\n",
                    "docs/x/dropped.txt": "dropped\n",
                },
            )
            problems = GATE.builder_problems(root)
            self.assertTrue(
                any("dropped.txt" in p for p in problems), problems
            )
            self.assertFalse(
                any("kept.txt" in p for p in problems), problems
            )

    def test_a_builder_dropping_a_generated_python_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture_root(
                tmp,
                {
                    "docs/x/build_fake.py": (
                        "import helper\n"
                        "from pathlib import Path\n"
                        "here = Path(__file__).parent\n"
                        "(here / \"kept.txt\").write_text(\n"
                        "    \"kept %s\\n\" % helper.VALUE\n"
                        ")\n"
                    ),
                    "docs/x/helper.py": "VALUE = 7\n",
                    "docs/x/kept.txt": "kept 7\n",
                    "docs/x/generated_data.py": "DATA = 1\n",
                },
            )
            problems = GATE.builder_problems(root)
            self.assertTrue(
                any("generated_data.py" in p for p in problems),
                problems,
            )
            self.assertFalse(
                any("helper.py" in p for p in problems), problems
            )

    def test_a_builder_dropping_a_subfolder_output_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture_root(
                tmp,
                {
                    "docs/x/build_fake.py": (
                        WRITE_ROGUE % "kept.txt"
                    ).replace("rogue", "kept"),
                    "docs/x/kept.txt": "kept\n",
                    "docs/x/exports/dropped.png": b"dropped",
                },
            )
            problems = GATE.builder_problems(root)
            self.assertTrue(
                any(
                    "exports/dropped.png" in p for p in problems
                ),
                problems,
            )

    def test_a_file_under_another_builder_folder_is_left_to_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture_root(
                tmp,
                {
                    "docs/x/build_fake.py": (
                        WRITE_ROGUE % "kept.txt"
                    ).replace("rogue", "kept"),
                    "docs/x/kept.txt": "kept\n",
                    "docs/x/nested/build_nested.py": (
                        WRITE_ROGUE % "foreign.txt"
                    ).replace("rogue", "foreign"),
                    "docs/x/nested/foreign.txt": "foreign\n",
                },
            )
            problems = GATE.builder_problems(root)
            self.assertEqual(problems, [])

    def test_the_declared_palette_input_is_not_a_dropped_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture_root(
                tmp,
                {
                    "docs/brand/build_palette.py": (
                        "import json\n"
                        "from pathlib import Path\n"
                        "here = Path(__file__).parent\n"
                        "palette = json.loads(\n"
                        "    (here / \"palette.json\").read_text(\n"
                        "        encoding=\"utf-8\"\n"
                        "    )\n"
                        ")\n"
                        "(here / \"kept.txt\").write_text(\n"
                        "    palette[\"ink\"] + \"\\n\"\n"
                        ")\n"
                    ),
                    "docs/brand/palette.json": '{"ink": "kept"}\n',
                    "docs/brand/kept.txt": "kept\n",
                },
            )
            problems = GATE.builder_problems(root)
            self.assertEqual(problems, [])

    def test_a_builder_output_symlink_to_an_identical_target_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture_root(
                tmp,
                {
                    "docs/brand/build_fake.py": (
                        WRITE_ROGUE % "wordmark-dark.svg"
                    ).replace("rogue", "wordmark"),
                    "docs/brand/wordmark-dark.svg": "wordmark\n",
                },
            )
            output = root / "docs" / "brand" / "wordmark-dark.svg"
            external = Path(tmp) / "external-wordmark-target.svg"
            external.write_bytes(output.read_bytes())
            before = hashlib.sha256(
                external.read_bytes()
            ).hexdigest()
            self.assertEqual(
                before,
                hashlib.sha256(output.read_bytes()).hexdigest(),
            )
            output.unlink()
            os.symlink(external, output)
            self.assertTrue(output.is_symlink())
            problems = GATE.builder_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("builder", problems[0])
            self.assertIn("wordmark-dark.svg", problems[0])
            self.assertIn("symlink", problems[0])
            self.assertEqual(
                hashlib.sha256(
                    external.read_bytes()
                ).hexdigest(),
                before,
            )

    def test_a_builder_palette_input_symlink_to_an_identical_target_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture_root(
                tmp,
                {
                    "docs/brand/build_palette.py": (
                        "import json\n"
                        "from pathlib import Path\n"
                        "here = Path(__file__).parent\n"
                        "palette = json.loads(\n"
                        "    (here / \"palette.json\").read_text(\n"
                        "        encoding=\"utf-8\"\n"
                        "    )\n"
                        ")\n"
                        "(here / \"kept.txt\").write_text(\n"
                        "    palette[\"ink\"] + \"\\n\"\n"
                        ")\n"
                    ),
                    "docs/brand/palette.json": '{"ink": "kept"}\n',
                    "docs/brand/kept.txt": "kept\n",
                },
            )
            palette = root / "docs" / "brand" / "palette.json"
            external = Path(tmp) / "external-palette-target.json"
            external.write_bytes(palette.read_bytes())
            before = hashlib.sha256(
                external.read_bytes()
            ).hexdigest()
            self.assertEqual(
                before,
                hashlib.sha256(palette.read_bytes()).hexdigest(),
            )
            palette.unlink()
            os.symlink(external, palette)
            self.assertTrue(palette.is_symlink())
            problems = GATE.builder_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("builder", problems[0])
            self.assertIn("palette.json", problems[0])
            self.assertIn("symlink", problems[0])
            self.assertEqual(
                hashlib.sha256(
                    external.read_bytes()
                ).hexdigest(),
                before,
            )

    def test_a_child_rewrite_with_identical_bytes_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture_root(
                tmp,
                {
                    "docs/x/build_fake.py": (
                        "import subprocess\n"
                        "import sys\n"
                        "from pathlib import Path\n"
                        "here = Path(__file__).parent\n"
                        "(here / \"kept.txt\").write_text(\"kept\\n\")\n"
                        "code = (\n"
                        "    \"from pathlib import Path\\n\"\n"
                        "    \"import sys\\n\"\n"
                        "    \"Path(sys.argv[1]).write_text(\"\n"
                        "    \"'dropped\\\\n')\\n\"\n"
                        ")\n"
                        "subprocess.run(\n"
                        "    [sys.executable, \"-c\", code,\n"
                        "     str(here / \"dropped.txt\")],\n"
                        "    check=True,\n"
                        ")\n"
                    ),
                    "docs/x/kept.txt": "kept\n",
                    "docs/x/dropped.txt": "dropped\n",
                },
            )
            problems = GATE.builder_problems(root)
            self.assertEqual(problems, [])

    def test_a_builder_deleting_a_shipped_output_is_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture_root(
                tmp,
                {
                    "docs/x/build_del.py": (
                        "from pathlib import Path\n"
                        "(Path(__file__).parent / \"gone.png\")"
                        ".unlink()\n"
                    ),
                    "docs/x/gone.png": b"gone",
                },
            )
            problems = GATE.builder_problems(root)
            self.assertTrue(
                any(
                    "deletes" in p and "gone.png" in p
                    for p in problems
                ),
                problems,
            )

    def test_builders_at_the_top_and_nested_depths_are_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture_root(
                tmp,
                {
                    "docs/build_top.py": WRITE_ROGUE % "top-rogue.txt",
                    "docs/brand/nested/build_nested.py": (
                        WRITE_ROGUE % "nested-rogue.txt"
                    ),
                },
            )
            problems = GATE.builder_problems(root)
            self.assertTrue(
                any("top-rogue.txt" in p for p in problems), problems
            )
            self.assertTrue(
                any("nested-rogue.txt" in p for p in problems),
                problems,
            )


class ChangelogReachTest(unittest.TestCase):
    """The changelog entry states the reach the gate docstring states.

    The Added entry once claimed the gate and the sources file
    rerun every gated provenance claim in the tree on every
    check, while the gate docstring states that commit hashes
    are set aside and that a token only change inside the eval
    class is drift the gate cannot see. Restoring the absolute
    claim, or dropping either stated limit from the entry,
    fails here.
    """

    def test_the_entry_states_the_scoped_reach_and_its_limits(self):
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        flat = " ".join(text.split())
        self.assertNotIn(
            "rerun every gated provenance claim in the tree "
            "on every check",
            flat,
        )
        marker = "- The regeneration gate at"
        start = flat.find(marker)
        self.assertNotEqual(start, -1)
        bullet = flat[start:flat.find("- The phone hero", start)]
        self.assertIn(
            "regenerate the shipped artefacts that claim "
            "a provenance",
            bullet,
        )
        self.assertIn(
            "The comparison sets commit hashes aside, because "
            "the fixture builder sets no date",
            bullet,
        )
        self.assertIn(
            "a token only change inside the eval class is "
            "drift the gate cannot see",
            bullet,
        )


if __name__ == "__main__":
    unittest.main()
