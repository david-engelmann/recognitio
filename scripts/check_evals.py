#!/usr/bin/env python3
"""Guard the eval artefacts the summaries ask a reader to trust.

The results and the per pass notes rest on the task fixtures under
evals/tasks and on the grading rules those fixtures carry. Before
this gate no step in the check compared any of those files against
anything, so a quiet edit to a transcript or a planted rule or a
recorded number left the gate green. This script closes that gap
with four checks that run in one gate step.

The first check compares every eval artefact file under
evals/tasks plus the results file and the per pass notes against
the checksum record at evals/checksums.json and names the first
file whose bytes moved. A deliberate eval update refreshes the
record with the write flag named in AGENTS.md and then commits
the record beside the artefacts it covers.

The second check reads the results table back. The per task
planted and found counts must add up to the headline total row
the table prints, and the headline sentences in the prose under
the table must state the same totals, so a single cell edit is
caught even where a checksum refresh would hide it.

The third check rebuilds each task from its sources file. The
rebuilt diff must match the saved diff byte for byte and the
rebuilt manifest entries must match the saved entries, and the
rebuilt packet must pass the shipped packet checker against the
rebuilt repository. The saved packet itself must carry a
verified manifest whose recorded sections stand in the packet
under the same section check the packet checker runs. The
packet text itself is not rebuilt line for line, because the
commit subjects and authors of the original fixture commits
stand in no sources file, so no rebuild can reproduce the
history lines or the token estimates that rest on them. The
checksum record covers the saved packet instead.

The fourth check reads the corpus index. Every test name the
index cites must stand among the test functions under tests, so
renaming a cited test fails here instead of orphaning its rows
in silence. The corpus check shares this script because the
corpus is part of the same evidence layer and one gate step
keeps the layer under one name.

Exits nonzero and lists every problem when a check fails.
"""

import argparse
import ast
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKSUM_REL = "evals/checksums.json"
GIT_SCRUB_VARS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_NAMESPACE",
    "GIT_NO_REPLACE_OBJECTS",
    "GIT_REPLACE_REF_BASE",
)
GIT_PIN = [
    "-c", "core.quotepath=false",
    "-c", "diff.noprefix=false",
    "-c", "diff.mnemonicPrefix=false",
    "-c", "color.ui=false",
    "-c", "color.diff=false",
    "-c", "color.grep=false",
    "-c", "color.status=false",
    "-c", "grep.column=false",
    "-c", "diff.interHunkContext=0",
]
DIFF_FLAGS = [
    "diff", "--histogram", "--find-renames", "--find-copies",
    "-W", "--no-ext-diff", "--no-textconv",
]
LEGACY_ENTRY_KEYS = {"instruction_file"}


def artefact_paths(root):
    """List every file the checksum record covers in sorted order."""
    evals = root / "evals"
    paths = [evals / "RESULTS.md", evals / "PASS-NOTES.md"]
    tasks = evals / "tasks"
    if tasks.is_dir():
        paths.extend(p for p in tasks.rglob("*") if p.is_file())
    return sorted(paths, key=lambda p: str(p.relative_to(root)))


def file_digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_record(root):
    record = {}
    for path in artefact_paths(root):
        rel = str(path.relative_to(root))
        record[rel] = file_digest(path)
    return record


def write_checksums(root):
    record = build_record(root)
    target = root / CHECKSUM_REL
    target.write_text(
        json.dumps({"files": record}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return len(record)


def checksum_problems(root):
    """Name the first artefact whose bytes moved off the record."""
    target = root / CHECKSUM_REL
    if not target.is_file():
        return ["no checksum record stands at %s" % CHECKSUM_REL]
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
        recorded = data["files"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        return ["the checksum record at %s does not parse" % CHECKSUM_REL]
    current = build_record(root)
    for rel in sorted(set(recorded) | set(current)):
        if rel not in recorded:
            return [
                "eval artefact %s stands in the tree with no entry "
                "in the checksum record" % rel
            ]
        if rel not in current:
            return [
                "eval artefact %s stands in the checksum record "
                "with no file in the tree" % rel
            ]
        if recorded[rel] != current[rel]:
            return [
                "eval artefact %s no longer matches the checksum "
                "record" % rel
            ]
    return []


def table_rows(text):
    rows = {}
    pattern = re.compile(
        r"^\| (task-\d+|Total) \| (\d+) \| (\d+) \| (\d+) \|$",
        re.MULTILINE,
    )
    for match in pattern.finditer(text):
        rows[match.group(1)] = tuple(
            int(match.group(i)) for i in (2, 3, 4)
        )
    return rows


def results_problems(root):
    """Check the results totals against the per task entries."""
    path = root / "evals" / "RESULTS.md"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ["the results file cannot be read"]
    rows = table_rows(text)
    problems = []
    tasks = sorted(name for name in rows if name != "Total")
    if not tasks or "Total" not in rows:
        return ["the results table cannot be parsed"]
    total = rows["Total"]
    for column, label in (
        (0, "planted"),
        (1, "raw diff pass"),
        (2, "packet pass"),
    ):
        summed = sum(rows[name][column] for name in tasks)
        if summed != total[column]:
            problems.append(
                "the results table %s entries add to %d and its "
                "total row states %d" % (label, summed, total[column])
            )
    headlines = (
        (r"raw diff pass found (\d+) of (\d+)", 1),
        (r"packet pass found (\d+) of (\d+)", 2),
        (r"fair raw pass found the same (\d+) of (\d+)", 1),
    )
    for pattern, column in headlines:
        match = re.search(pattern, text)
        if match is None:
            problems.append(
                "the results prose holds no sentence matching %s"
                % pattern
            )
            continue
        found, planted = int(match.group(1)), int(match.group(2))
        if found != total[column] or planted != total[0]:
            problems.append(
                "the results prose states %d of %d and its total "
                "row states %d of %d"
                % (found, planted, total[column], total[0])
            )
    return problems


def cited_test_names(text):
    return set(re.findall(r"`(test_[a-z0-9_]+)`", text))


def suite_test_names(root):
    names = set()
    tests = root / "tests"
    if not tests.is_dir():
        return names
    for path in sorted(tests.glob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("test_"):
                    names.add(node.name)
    return names


def corpus_problems(root):
    """Name every test the corpus cites that the suite lacks."""
    path = root / "evals" / "corpus.md"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ["the corpus index cannot be read"]
    missing = sorted(cited_test_names(text) - suite_test_names(root))
    if missing:
        return [
            "the corpus index cites test names the suite does not "
            "hold, namely %s" % " and ".join(missing)
        ]
    return []


def git(repo, *args, raw=False):
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in GIT_SCRUB_VARS
    }
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    argv = (
        ["git", "--no-replace-objects", "--literal-pathspecs"]
        + ["-C", str(repo)] + GIT_PIN + list(args)
    )
    result = subprocess.run(
        argv,
        capture_output=True,
        text=not raw,
        env=env,
        timeout=120,
    )
    if result.returncode != 0:
        stderr = result.stderr
        if raw:
            stderr = stderr.decode("utf-8", errors="replace")
        raise AssertionError(
            "git %s failed with %s" % (" ".join(args), stderr)
        )
    return result.stdout


def write_fixture(repo, mapping):
    for child in list(repo.iterdir()):
        if child.name == ".git":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    for name, content in mapping.items():
        target = repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def load_packet_checker(root):
    path = root / "scripts" / "check_packet.py"
    spec = importlib.util.spec_from_file_location("gate_check_packet", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def shipped_packet_problems(root, task_dir, checker):
    problems = []
    try:
        manifest = json.loads(
            (task_dir / "manifest.json").read_text(encoding="utf-8")
        )
        packet_text = (task_dir / "packet.md").read_text(
            encoding="utf-8", errors="surrogateescape"
        )
    except (OSError, json.JSONDecodeError) as exc:
        return ["the saved packet of %s cannot be read with %s"
                % (task_dir.name, exc)]
    if not isinstance(manifest, dict):
        return [
            "the saved manifest of %s does not hold a JSON object"
            % task_dir.name
        ]
    if manifest.get("verified") is not True:
        problems.append(
            "the saved manifest of %s does not report verified"
            % task_dir.name
        )
    sections = manifest.get("sections")
    if not isinstance(sections, list):
        problems.append(
            "the saved manifest of %s records no sections"
            % task_dir.name
        )
    else:
        for problem in checker.section_problems(packet_text, sections):
            problems.append("%s with %s" % (task_dir.name, problem))
    return problems


def rebuild_problems(root, task_dir, tmp):
    sources = json.loads(
        (task_dir / "sources.json").read_text(encoding="utf-8")
    )
    repo = Path(tmp) / "repo"
    repo.mkdir(parents=True)
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "eval@example.com")
    git(repo, "config", "user.name", "Eval Fixture")
    git(repo, "config", "core.autocrlf", "false")
    git(repo, "config", "commit.gpgsign", "false")
    write_fixture(repo, sources["base"])
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "base")
    base = git(repo, "rev-parse", "HEAD").strip()
    write_fixture(repo, sources["head"])
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "head")
    head = git(repo, "rev-parse", "HEAD").strip()
    problems = []
    rebuilt_diff = git(
        repo, *(DIFF_FLAGS + ["%s..%s" % (base, head)]), raw=True
    )
    saved_diff = (task_dir / "diff.patch").read_bytes()
    if rebuilt_diff != saved_diff:
        problems.append(
            "the diff of %s does not rebuild byte for byte from "
            "its sources" % task_dir.name
        )
    out = Path(tmp) / "out"
    extract = root / "skills" / "recognitio" / "scripts" / "extract.py"
    run = subprocess.run(
        [sys.executable, str(extract), "--repo", str(repo),
         "--range", "%s..%s" % (base, head), "--out", str(out)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if run.returncode != 0:
        problems.append(
            "the extractor failed on the rebuilt history of %s "
            "with %s" % (task_dir.name, run.stderr.strip())
        )
        return problems
    rebuilt = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    saved = json.loads(
        (task_dir / "manifest.json").read_text(encoding="utf-8")
    )
    if rebuilt.get("verified") is not True:
        problems.append(
            "the rebuilt packet of %s does not report verified"
            % task_dir.name
        )
    problems.extend(entry_problems(task_dir.name, saved, rebuilt))
    check = subprocess.run(
        [sys.executable, str(root / "scripts" / "check_packet.py"),
         str(out), "--repo", str(repo)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if check.returncode != 0:
        problems.append(
            "the packet checker refuses the rebuilt packet of %s "
            "with %s" % (task_dir.name, check.stderr.strip())
        )
    return problems


def entry_problems(task_name, saved, rebuilt):
    """Compare the saved manifest entries against the rebuilt ones.

    The rebuilt manifest sets the entry format, because the
    current extractor writes it. One key stands exempt from
    that rule. The instruction file key arrived after the
    first tasks were recorded, so a task whose saved entries
    carry it nowhere has that key set aside. Any other key
    missing from the saved entries is drift and the
    comparison catches it, whether the key is missing from
    every entry or only some, because the saved side reads
    the missing key as no value against the rebuilt value.
    """
    saved_files = saved.get("files") if isinstance(saved, dict) else None
    rebuilt_files = (
        rebuilt.get("files") if isinstance(rebuilt, dict) else None
    )
    if not isinstance(saved_files, list) or not saved_files:
        return [
            "the saved manifest of %s records no file entries"
            % task_name
        ]
    if not isinstance(rebuilt_files, list) or not rebuilt_files:
        return [
            "the rebuilt manifest of %s records no file entries"
            % task_name
        ]
    keys = list(rebuilt_files[0].keys())
    dated = {
        key
        for key in keys
        if key in LEGACY_ENTRY_KEYS
        and all(
            not isinstance(entry, dict) or key not in entry
            for entry in saved_files
        )
    }
    keys = [key for key in keys if key not in dated]
    rebuilt_entries = [
        {key: entry.get(key) for key in keys}
        for entry in rebuilt_files
        if isinstance(entry, dict)
    ]
    saved_entries = [
        {key: entry.get(key) for key in keys}
        if isinstance(entry, dict)
        else {}
        for entry in saved_files
    ]
    if rebuilt_entries != saved_entries:
        return [
            "the manifest entries of %s do not rebuild from its "
            "sources" % task_name
        ]
    return []


def packet_problems(root):
    """Rebuild every task and verify its packet and its diff."""
    problems = []
    tasks = root / "evals" / "tasks"
    if not tasks.is_dir():
        return ["no eval tasks stand under evals/tasks"]
    checker = load_packet_checker(root)
    for task_dir in sorted(tasks.iterdir()):
        if not task_dir.is_dir():
            continue
        with tempfile.TemporaryDirectory() as tmp:
            try:
                problems.extend(
                    shipped_packet_problems(root, task_dir, checker)
                )
                problems.extend(rebuild_problems(root, task_dir, tmp))
            except (
                OSError,
                ValueError,
                KeyError,
                IndexError,
                TypeError,
                AttributeError,
                subprocess.SubprocessError,
                AssertionError,
            ) as exc:
                problems.append(
                    "the rebuild of %s failed with %s"
                    % (task_dir.name, exc)
                )
    return problems


def all_problems(root):
    problems = []
    problems.extend(checksum_problems(root))
    problems.extend(results_problems(root))
    problems.extend(corpus_problems(root))
    problems.extend(packet_problems(root))
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="check_evals.py",
        description="Guard the eval artefacts and the corpus index.",
    )
    parser.add_argument(
        "--write-checksums",
        action="store_true",
        help="refresh the checksum record from the current tree",
    )
    args = parser.parse_args(argv)
    if args.write_checksums:
        count = write_checksums(ROOT)
        print(
            "check_evals: checksum record refreshed over %d files"
            % count
        )
        return 0
    problems = all_problems(ROOT)
    if problems:
        for problem in problems:
            print("check_evals: %s" % problem, file=sys.stderr)
        return 1
    print(
        "check_evals: eval artefacts match their checksum record "
        "and the results totals add up and every task rebuilds "
        "from its sources and every corpus name stands in the suite"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
