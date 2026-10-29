"""The residual FIFO doors of the eval and regeneration gates.

The round 183 sweep recorded two gates as a residual for a
follow up lane, the eval gate reading its shipped packet
manifest at an artefact path enumerated inside the shipped
eval tree and the regeneration gate reading its examples
index at a fixed artefact path inside the shipped tree.
Both gates take no caller named path, their mains read only
the shipped tree under their own root, and their readings
stand scattered across many sites with no shared helper.
Every reading site in both scripts was swept with a planted
FIFO for this lane, and every site that hung now reads
through one guarded helper per script that tests existence
first and the regular file shape second and only then
reads, raising the OSError shape an unreadable file raises
so each site keeps its own problem wording. Every shape
runs in a subprocess with a ten second bound, so a door
that still reads its FIFO fails one test at the bound
instead of hanging the suite.
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DRIVER = r"""
import importlib.util
import json
import os
import shutil
import socket
import sys
import tempfile
from pathlib import Path

script = Path(sys.argv[1])
case = sys.argv[2]
work = Path(sys.argv[3])
repo = Path(sys.argv[4])
spec = importlib.util.spec_from_file_location("door_under_test", script)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def fifo(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    os.mkfifo(path)
    return path


def copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return dst


def show(problems):
    if isinstance(problems, (list, tuple)):
        for p in problems:
            print(p)
    else:
        print(repr(problems))


def sock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    s = socket.socket(socket.AF_UNIX)
    s.bind(str(path))
    return path


try:
    if case.startswith("evals_results_"):
        kind = case[len("evals_results_"):]
        p = work / "evals/RESULTS.md"
        if kind == "fifo":
            fifo(p)
        elif kind == "linkfifo":
            fifo(work / "target")
            p.parent.mkdir(parents=True, exist_ok=True)
            p.symlink_to(work / "target")
        elif kind == "regular":
            copy(repo / "evals/RESULTS.md", p)
        elif kind == "linkregular":
            copy(repo / "evals/RESULTS.md", work / "target")
            p.parent.mkdir(parents=True, exist_ok=True)
            p.symlink_to(work / "target")
        elif kind == "socket":
            sock(p)
        elif kind == "dir":
            p.mkdir(parents=True)
        elif kind == "dangling":
            p.parent.mkdir(parents=True, exist_ok=True)
            p.symlink_to(work / "nope")
        show(mod.results_problems(work))
    elif case == "evals_build_record_fifo":
        for rel in ("evals/PASS-NOTES.md", "evals/corpus.md",
                    "evals/source-anchors.json",
                    "evals/corpus-coverage.json"):
            copy(repo / rel, work / rel)
        fifo(work / "evals/RESULTS.md")
        try:
            mod.build_record(work)
            print("built")
        except OSError as exc:
            print("OSError %s" % exc)
    elif case == "evals_checksum_record_fifo":
        fifo(work / "evals/checksums.json")
        show(mod.checksum_problems(work))
    elif case == "evals_readme_fifo":
        fifo(work / "README.md")
        show(mod.readme_eval_claim_problems(work))
    elif case == "evals_planted_fifo":
        fifo(work / "evals/tasks/task-06/planted.md")
        print(repr(mod.task06_planted_rule(work / "evals/tasks/task-06")))
    elif case == "evals_transcripts_fifo":
        fifo(work / "evals/tasks/task-06/transcripts.md")
        print(repr(mod.transcript_fences(work / "evals/tasks/task-06")))
    elif case in ("evals_recorded_results_fifo",
                  "evals_recorded_pass_fifo"):
        name = ("RESULTS.md" if case.endswith("results_fifo")
                else "PASS-NOTES.md")
        other = ("PASS-NOTES.md" if name == "RESULTS.md"
                 else "RESULTS.md")
        copy(repo / "evals" / other, work / "evals" / other)
        fifo(work / "evals" / name)
        print(repr(mod.recorded_task06_scores(work)))
    elif case == "evals_task06_sources_fifo":
        td = work / "evals/tasks/task-06"
        copy(repo / "evals/tasks/task-06/planted.md", td / "planted.md")
        copy(repo / "evals/tasks/task-06/transcripts.md",
             td / "transcripts.md")
        fifo(td / "sources.json")
        show(mod.task06_problems(work))
    elif case == "evals_anchor_sources_fifo":
        fifo(work / "evals/tasks/task-01/sources.json")
        show(mod.task_anchor_problems(work, "task-01"))
    elif case == "evals_suite_fifo":
        fifo(work / "tests/test_planted.py")
        print("names %d" % len(mod.suite_test_names(work)))
    elif case in ("evals_corpus_fifo", "evals_scope_fifo"):
        fifo(work / "evals/corpus.md")
        if case == "evals_corpus_fifo":
            show(mod.corpus_problems(work))
        else:
            show(mod.corpus_scope_problems(work))
    elif case == "evals_coverage_record_fifo":
        fifo(work / "evals/corpus-coverage.json")
        show(mod.corpus_coverage_problems(work))
    elif case == "evals_coverage_corpus_fifo":
        copy(repo / "evals/corpus-coverage.json",
             work / "evals/corpus-coverage.json")
        fifo(work / "evals/corpus.md")
        show(mod.corpus_coverage_problems(work))
    elif case == "evals_write_coverage_fifo":
        fifo(work / "evals/corpus.md")
        try:
            print("wrote %d" % mod.write_corpus_coverage(work))
        except OSError as exc:
            print("OSError %s" % exc)
    elif case == "evals_anchor_record_fifo":
        fifo(work / "evals/source-anchors.json")
        show(mod.source_anchor_problems(work))
    elif case in ("evals_anchor_digest_fifo",
                  "evals_write_anchors_fifo"):
        copy(repo / "evals/source-anchors.json",
             work / "evals/source-anchors.json")
        data = json.loads(
            (repo / "evals/source-anchors.json").read_text(
                encoding="utf-8"))
        names = sorted(data["sources"])
        for name in names:
            d = work / "evals/tasks" / name
            d.mkdir(parents=True, exist_ok=True)
            if name == names[0]:
                fifo(d / "sources.json")
            else:
                copy(repo / "evals/tasks" / name / "sources.json",
                     d / "sources.json")
        if case == "evals_anchor_digest_fifo":
            show(mod.source_anchor_problems(work))
        else:
            try:
                print("wrote %d" % mod.write_source_anchors(work))
            except OSError as exc:
                print("OSError %s" % exc)
    elif case.startswith("evals_shipped_"):
        kind = case[len("evals_shipped_"):]
        td = work / "evals/tasks/task-01"
        checker = mod.load_packet_checker(repo)
        if kind == "manifest_fifo":
            fifo(td / "manifest.json")
        elif kind == "packet_fifo":
            copy(repo / "evals/tasks/task-01/manifest.json",
                 td / "manifest.json")
            fifo(td / "packet.md")
        elif kind == "manifest_linkfifo":
            fifo(work / "target")
            td.mkdir(parents=True, exist_ok=True)
            (td / "manifest.json").symlink_to(work / "target")
        elif kind == "manifest_socket":
            sock(td / "manifest.json")
        elif kind == "manifest_dir":
            (td / "manifest.json").mkdir(parents=True)
        elif kind == "manifest_dangling":
            td.mkdir(parents=True, exist_ok=True)
            (td / "manifest.json").symlink_to(work / "nope")
        elif kind == "manifest_regular":
            copy(repo / "evals/tasks/task-01/manifest.json",
                 td / "manifest.json")
            copy(repo / "evals/tasks/task-01/packet.md",
                 td / "packet.md")
        elif kind == "manifest_linkregular":
            copy(repo / "evals/tasks/task-01/manifest.json",
                 work / "target")
            copy(repo / "evals/tasks/task-01/packet.md",
                 td / "packet.md")
            (td / "manifest.json").symlink_to(work / "target")
        show(mod.shipped_packet_problems(work, td, checker))
    elif case == "evals_rebuild_sources_fifo":
        fifo(work / "evals/tasks/task-01/sources.json")
        with tempfile.TemporaryDirectory() as tmp:
            show(mod.rebuild_problems(
                work, work / "evals/tasks/task-01", tmp))
    elif case == "evals_rebuild_diff_fifo":
        td = work / "evals/tasks/task-01"
        copy(repo / "evals/tasks/task-01/sources.json",
             td / "sources.json")
        fifo(td / "diff.patch")
        with tempfile.TemporaryDirectory() as tmp:
            show(mod.rebuild_problems(work, td, tmp))
    elif case == "evals_rebuild_manifest_fifo":
        td = work / "evals/tasks/task-01"
        copy(repo / "evals/tasks/task-01/sources.json",
             td / "sources.json")
        copy(repo / "evals/tasks/task-01/diff.patch",
             td / "diff.patch")
        shutil.copytree(repo / ".agents", work / ".agents",
                        symlinks=True)
        copy(repo / "scripts/check_packet.py",
             work / "scripts/check_packet.py")
        copy(repo / "scripts/packet-manifest.schema.json",
             work / "scripts/packet-manifest.schema.json")
        fifo(td / "manifest.json")
        with tempfile.TemporaryDirectory() as tmp:
            show(mod.rebuild_problems(work, td, tmp))
    elif case == "evals_anchor_doubled_fifo":
        r = work / "repo"
        r.mkdir(parents=True)
        fifo(r / "calc.py")
        print(repr(mod._anchor_doubled_result(r, "calc", "total")))
    elif case == "evals_anchor_firstline_fifo":
        r = work / "repo"
        r.mkdir(parents=True)
        fifo(r / "report.py")
        out = mod.task06_anchor_problems(
            r, b"+ total + total\n", "report.py", "oldmod", "newmod")
        print(repr(out))
    elif case == "evals_load_packet_fifo":
        fifo(work / "scripts/check_packet.py")
        try:
            mod.load_packet_checker(work)
            print("loaded")
        except OSError as exc:
            print("OSError %s" % exc)
    elif case.startswith("regen_index_"):
        kind = case[len("regen_index_"):]
        p = work / "examples/README.md"
        if kind == "fifo":
            fifo(p)
        elif kind == "linkfifo":
            fifo(work / "target")
            p.parent.mkdir(parents=True, exist_ok=True)
            p.symlink_to(work / "target")
        elif kind == "regular":
            copy(repo / "examples/README.md", p)
        elif kind == "linkregular":
            copy(repo / "examples/README.md", work / "target")
            p.parent.mkdir(parents=True, exist_ok=True)
            p.symlink_to(work / "target")
        elif kind == "socket":
            sock(p)
        elif kind == "dir":
            p.mkdir(parents=True)
        elif kind == "dangling":
            p.parent.mkdir(parents=True, exist_ok=True)
            p.symlink_to(work / "nope")
        try:
            block, probs = mod.printed_example_block(work)
            print("probs %r block %s" % (
                probs, None if block is None else len(block)))
        except OSError as exc:
            print("OSError %s" % exc)
    elif case == "regen_example_fifo":
        fifo(work / "examples/README.md")
        show(mod.example_problems(work))
    elif case == "regen_length_index_fifo":
        fifo(work / "examples/README.md")
        try:
            show(mod.printed_length_problems(work, 3))
        except OSError as exc:
            print("OSError %s" % exc)
    elif case == "regen_length_readme_fifo":
        idx = work / "examples/README.md"
        idx.parent.mkdir(parents=True, exist_ok=True)
        idx.write_text("Packet length 3 lines\n", encoding="utf-8")
        fifo(work / "README.md")
        try:
            show(mod.printed_length_problems(work, 3))
        except OSError as exc:
            print("OSError %s" % exc)
    elif case == "regen_length_regular":
        idx = work / "examples/README.md"
        idx.parent.mkdir(parents=True, exist_ok=True)
        idx.write_text("Packet length 3 lines\n", encoding="utf-8")
        (work / "README.md").write_text(
            "full packet for this commit runs 3 lines\n",
            encoding="utf-8")
        show(mod.printed_length_problems(work, 3))
    elif case.startswith("regen_eval_"):
        rel = case[len("regen_eval_"):]
        td = work / "evals/tasks/task-01"
        files = {"sources": "sources.json", "diff": "diff.patch",
                 "packet": "packet.md", "manifest": "manifest.json"}
        for key, name in files.items():
            if key == rel:
                fifo(td / name)
            else:
                copy(repo / "evals/tasks/task-01" / name, td / name)
        eg_spec = importlib.util.spec_from_file_location(
            "eg", repo / "scripts/check_evals.py")
        eg = importlib.util.module_from_spec(eg_spec)
        eg_spec.loader.exec_module(eg)
        show(mod.eval_task_problems(work, eg, td))
    elif case == "regen_proof_sources_fifo":
        fifo(work / "workflows/proof-run/sources.json")
        show(mod.proof_problems(work))
    elif case in ("regen_proof_packet_fifo",
                  "regen_proof_manifest_fifo"):
        folder = work / "workflows/proof-run"
        copy(repo / "workflows/proof-run/sources.json",
             folder / "sources.json")
        if case == "regen_proof_packet_fifo":
            fifo(folder / "packet.md")
            copy(repo / "workflows/proof-run/manifest.json",
                 folder / "manifest.json")
        else:
            copy(repo / "workflows/proof-run/packet.md",
                 folder / "packet.md")
            fifo(folder / "manifest.json")
        show(mod.proof_problems(work))
    elif case == "regen_snapshot_fifo":
        folder = work / "folder"
        folder.mkdir(parents=True)
        (folder / "a.txt").write_text("x", encoding="utf-8")
        fifo(folder / "b.txt")
        print("snap %r" % mod.folder_snapshot(folder))
    elif case == "regen_traced_fifo":
        fifo(work / "trace.log")
        print(repr(mod.traced_opens(work / "trace.log")))
    elif case == "regen_builder_fifo":
        builder = work / "docs/x/build_x.py"
        builder.parent.mkdir(parents=True, exist_ok=True)
        builder.write_text("# builder\n", encoding="utf-8")
        fifo(work / "docs/x/out.txt")
        show(mod.builder_symlink_problems(work, builder))
    elif case == "regen_checked_example_fifo":
        folder = work / "examples/example-packet-abc"
        folder.mkdir(parents=True, exist_ok=True)
        fifo(folder / "packet.md")
        show(mod.checked_symlink_problems(
            work, "examples/example-packet-abc"))
    elif case == "regen_load_sibling_fifo":
        sib = work / "copy/scripts/check_regeneration.py"
        copy(repo / "scripts/check_regeneration.py", sib)
        fifo(work / "copy/scripts/check_evals.py")
        spec2 = importlib.util.spec_from_file_location(
            "regen_copy", sib)
        m2 = importlib.util.module_from_spec(spec2)
        spec2.loader.exec_module(m2)
        try:
            m2.load_sibling("check_evals")
            print("loaded")
        except OSError as exc:
            print("OSError %s" % exc)
    else:
        raise SystemExit("unknown case " + case)
except OSError as exc:
    print("UNCAUGHT OSError %s" % exc)
"""


@unittest.skipUnless(hasattr(os, "mkfifo"), "no mkfifo on this host")
class ResidualFifoDoorTestCase(unittest.TestCase):
    """One bounded subprocess per planted FIFO door."""

    def run_door(self, script, case):
        with tempfile.TemporaryDirectory() as tmp:
            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        DRIVER,
                        str(ROOT / "scripts" / (script + ".py")),
                        case,
                        tmp,
                        str(ROOT),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
            except subprocess.TimeoutExpired:
                self.fail(
                    "the %s door %s still hangs on a FIFO"
                    % (script, case)
                )
            self.assertEqual(result.returncode, 0, result.stderr)
            return result.stdout

    # The eval gate doors

    def test_evals_results_shapes(self):
        for kind, want in (
            ("fifo", "the results file cannot be read"),
            ("linkfifo", "the results file cannot be read"),
            ("socket", "the results file cannot be read"),
            ("dir", "the results file cannot be read"),
            ("dangling", "the results file cannot be read"),
            ("absent", "the results file cannot be read"),
        ):
            with self.subTest(kind=kind):
                out = self.run_door(
                    "check_evals", "evals_results_" + kind
                )
                self.assertIn(want, out)
        for kind in ("regular", "linkregular"):
            with self.subTest(kind=kind):
                out = self.run_door(
                    "check_evals", "evals_results_" + kind
                )
                self.assertNotIn("cannot be read", out)

    def test_evals_build_record_fifo_refuses(self):
        out = self.run_door(
            "check_evals", "evals_build_record_fifo"
        )
        self.assertIn("is not a regular file", out)

    def test_evals_checksum_record_fifo_control(self):
        out = self.run_door(
            "check_evals", "evals_checksum_record_fifo"
        )
        self.assertIn("no checksum record stands", out)

    def test_evals_readme_fifo_refuses(self):
        out = self.run_door("check_evals", "evals_readme_fifo")
        self.assertIn(
            "the README cannot be read for the eval claim", out
        )

    def test_evals_task06_text_fifo_refuses(self):
        out = self.run_door("check_evals", "evals_planted_fifo")
        self.assertIn(
            "the task-06 planted file cannot be read", out
        )
        out = self.run_door(
            "check_evals", "evals_transcripts_fifo"
        )
        self.assertIn(
            "the task-06 transcripts cannot be read", out
        )

    def test_evals_recorded_scores_fifo_refuses(self):
        for case in (
            "evals_recorded_results_fifo",
            "evals_recorded_pass_fifo",
        ):
            with self.subTest(case=case):
                out = self.run_door("check_evals", case)
                self.assertIn("file cannot be read", out)

    def test_evals_sources_fifo_refuses(self):
        out = self.run_door(
            "check_evals", "evals_task06_sources_fifo"
        )
        self.assertIn("the task-06 sources cannot be read", out)
        out = self.run_door(
            "check_evals", "evals_anchor_sources_fifo"
        )
        self.assertIn(
            "the task-01 sources cannot be read", out
        )

    def test_evals_suite_fifo_refuses(self):
        out = self.run_door("check_evals", "evals_suite_fifo")
        self.assertIn("names 0", out)

    def test_evals_corpus_fifo_refuses(self):
        out = self.run_door("check_evals", "evals_corpus_fifo")
        self.assertIn("the corpus index cannot be read", out)
        out = self.run_door("check_evals", "evals_scope_fifo")
        self.assertIn("the corpus index cannot be read", out)
        out = self.run_door(
            "check_evals", "evals_coverage_corpus_fifo"
        )
        self.assertIn("the corpus index cannot be read", out)

    def test_evals_coverage_record_fifo_control(self):
        out = self.run_door(
            "check_evals", "evals_coverage_record_fifo"
        )
        self.assertIn("no corpus coverage record stands", out)

    def test_evals_write_coverage_fifo_refuses(self):
        out = self.run_door(
            "check_evals", "evals_write_coverage_fifo"
        )
        self.assertIn("is not a regular file", out)

    def test_evals_anchor_fifo_refuses(self):
        out = self.run_door(
            "check_evals", "evals_anchor_record_fifo"
        )
        self.assertIn("no source anchor record stands", out)
        out = self.run_door(
            "check_evals", "evals_anchor_digest_fifo"
        )
        self.assertIn("cannot be read", out)
        out = self.run_door(
            "check_evals", "evals_write_anchors_fifo"
        )
        self.assertIn("is not a regular file", out)

    def test_evals_shipped_packet_shapes(self):
        for kind, want in (
            ("manifest_fifo", "cannot be read"),
            ("packet_fifo", "cannot be read"),
            ("manifest_linkfifo", "cannot be read"),
            ("manifest_socket", "cannot be read"),
            ("manifest_dir", "cannot be read"),
            ("manifest_dangling", "cannot be read"),
        ):
            with self.subTest(kind=kind):
                out = self.run_door(
                    "check_evals", "evals_shipped_" + kind
                )
                self.assertIn(want, out)
        for kind in ("manifest_regular", "manifest_linkregular"):
            with self.subTest(kind=kind):
                out = self.run_door(
                    "check_evals", "evals_shipped_" + kind
                )
                self.assertNotIn("cannot be read", out)

    def test_evals_rebuild_fifo_refuses(self):
        for case in (
            "evals_rebuild_sources_fifo",
            "evals_rebuild_diff_fifo",
            "evals_rebuild_manifest_fifo",
        ):
            with self.subTest(case=case):
                out = self.run_door("check_evals", case)
                self.assertIn("is not a regular file", out)

    def test_evals_anchor_probe_fifo_refuses(self):
        out = self.run_door(
            "check_evals", "evals_anchor_doubled_fifo"
        )
        self.assertIn("cannot read", out)
        out = self.run_door(
            "check_evals", "evals_anchor_firstline_fifo"
        )
        self.assertIn("no longer stands", out)

    def test_evals_load_packet_fifo_refuses(self):
        out = self.run_door(
            "check_evals", "evals_load_packet_fifo"
        )
        self.assertIn("is not a regular file", out)

    # The regeneration gate doors

    def test_regen_index_shapes(self):
        for kind in ("fifo", "linkfifo", "socket", "dir",
                     "dangling"):
            with self.subTest(kind=kind):
                out = self.run_door(
                    "check_regeneration", "regen_index_" + kind
                )
                self.assertIn("OSError", out)
        for kind in ("regular", "linkregular"):
            with self.subTest(kind=kind):
                out = self.run_door(
                    "check_regeneration", "regen_index_" + kind
                )
                self.assertIn("probs []", out)

    def test_regen_example_fifo_refuses(self):
        out = self.run_door(
            "check_regeneration", "regen_example_fifo"
        )
        self.assertIn("cannot be read", out)

    def test_regen_length_fifo_refuses(self):
        out = self.run_door(
            "check_regeneration", "regen_length_index_fifo"
        )
        self.assertIn("is not a regular file", out)
        out = self.run_door(
            "check_regeneration", "regen_length_readme_fifo"
        )
        self.assertIn("is not a regular file", out)
        out = self.run_door(
            "check_regeneration", "regen_length_regular"
        )
        self.assertNotIn("packet length", out)

    def test_regen_eval_task_fifo_controls(self):
        for rel in ("sources", "diff", "packet", "manifest"):
            with self.subTest(rel=rel):
                out = self.run_door(
                    "check_regeneration", "regen_eval_" + rel
                )
                self.assertIn(
                    "does not stand as a regular file", out
                )

    def test_regen_proof_fifo_controls(self):
        out = self.run_door(
            "check_regeneration", "regen_proof_sources_fifo"
        )
        self.assertIn("no sources file stands", out)
        for case in (
            "regen_proof_packet_fifo",
            "regen_proof_manifest_fifo",
        ):
            with self.subTest(case=case):
                out = self.run_door("check_regeneration", case)
                self.assertIn(
                    "does not stand as a regular file", out
                )

    def test_regen_snapshot_and_trace_fifo_controls(self):
        out = self.run_door(
            "check_regeneration", "regen_snapshot_fifo"
        )
        self.assertIn("a.txt", out)
        self.assertNotIn("b.txt", out)
        out = self.run_door(
            "check_regeneration", "regen_traced_fifo"
        )
        self.assertIn("(set(), set())", out)

    def test_regen_builder_and_checked_fifo_controls(self):
        out = self.run_door(
            "check_regeneration", "regen_builder_fifo"
        )
        self.assertIn("does not stand as a regular file", out)
        out = self.run_door(
            "check_regeneration", "regen_checked_example_fifo"
        )
        self.assertIn("does not stand as a regular file", out)

    def test_regen_load_sibling_fifo_refuses(self):
        out = self.run_door(
            "check_regeneration", "regen_load_sibling_fifo"
        )
        self.assertIn("is not a regular file", out)


if __name__ == "__main__":
    unittest.main()
