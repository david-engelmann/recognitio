#!/usr/bin/env python3
"""Guard the eval artefacts the summaries ask a reader to trust.

The results and the per pass notes rest on the task fixtures under
evals/tasks and on the grading rules those fixtures carry. Before
this gate no step in the check compared any of those files against
anything, so a quiet edit to a transcript or a planted rule or a
recorded number left the gate green. This script closes that gap
with seven checks that run in one gate step.

The first check compares every eval artefact file under
evals/tasks plus the results file and the per pass notes and the
corpus index against the checksum record at evals/checksums.json
and names the first file whose bytes moved. The record loads
through a strict JSON reader that refuses a repeated key, so a
second entry for one path cannot override the pin. A deliberate
eval update refreshes the record with the write flag named in
AGENTS.md and then commits the record beside the artefacts it
covers.

The second check reads the results table back. The per task
planted and found counts must add up to the headline total row
the table prints, and the headline sentences in the prose under
the table must state the same totals, so a single cell edit is
caught even where a checksum refresh would hide it.

The third check re-derives the task-06 scores. Task-06 is the one
task with verbatim transcripts beside its summaries, so the gate
parses the planted grading rule, checks that each planted defect
still stands in the head rebuilt from the sources file, grades
each transcript fence under the rule, and compares the derived
raw and packet scores against the recorded sentences in the
results file and the per pass notes. A moved score distribution
over the earlier tasks that keeps every total true is the
deliberate residual of this check, recorded in the decisions
file, because those passes survive only as curated notes and a
parser over that prose would manufacture confidence the record
does not carry.

The fourth check rebuilds each task from its sources file. The
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
checksum record covers the saved packet instead. The sources
and manifest files the rebuild trusts load through the same
strict reader as the checksum record.

The fifth check compares the digest of each task sources file
against the source anchor record at evals/source-anchors.json,
which stands apart from the checksum refresh. Regenerating a
task from tampered sources and refreshing the checksums does not
move the anchor, so the tamper fails here. A deliberate sources
change moves the anchor first with the anchor write flag, as its
own committed step, and the checksum refresh refuses to run
while an anchor is stale.

The sixth check reads the corpus index. Every test name the
index cites must stand among the test functions under tests, so
renaming a cited test fails here instead of orphaning its rows
in silence. The corpus check shares this script because the
corpus is part of the same evidence layer and one gate step
keeps the layer under one name.

The seventh check compares the cited test names of each corpus
section against the corpus coverage record at
evals/corpus-coverage.json, which stands apart from the checksum
refresh like the source anchors. Dropping a row or a citation
fails here even after a checksum refresh, because the refresh
does not move the coverage record. A deliberate index change
moves the coverage first with the coverage write flag, as its
own committed step.

Record keys use the forward slash spelling on every host, so the
gate reads the same record on Windows and on POSIX.

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
SOURCE_ANCHORS_REL = "evals/source-anchors.json"
CORPUS_COVERAGE_REL = "evals/corpus-coverage.json"
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


class DuplicateKeyError(ValueError):
    """A JSON object holds the same key twice."""


def _reject_duplicate_keys(pairs):
    record = {}
    for key, value in pairs:
        if key in record:
            raise DuplicateKeyError("repeated key %r" % (key,))
        record[key] = value
    return record


def strict_json_loads(text):
    """Parse JSON refusing a repeated key in any object.

    A plain load keeps the last value of a repeated key in
    silence, which lets a second entry for one path override a
    pin with no refresh step at all. Every record this gate
    trusts loads through this reader instead.
    """
    return json.loads(text, object_pairs_hook=_reject_duplicate_keys)


def record_key(root, path):
    """Spell a record key with forward slashes on every host.

    The str of a relative path carries the host separator, so a
    record written on Windows would spell every key with
    backslashes while the shipped record carries forward
    slashes. The as_posix form keeps one spelling everywhere.
    """
    return path.relative_to(root).as_posix()


def artefact_paths(root):
    """List every file the checksum record covers in sorted order."""
    evals = root / "evals"
    paths = [
        evals / "RESULTS.md",
        evals / "PASS-NOTES.md",
        evals / "corpus.md",
        evals / "source-anchors.json",
        evals / "corpus-coverage.json",
    ]
    tasks = evals / "tasks"
    if tasks.is_dir():
        paths.extend(p for p in tasks.rglob("*") if p.is_file())
    return sorted(paths, key=lambda p: record_key(root, p))


def file_digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_record(root):
    record = {}
    for path in artefact_paths(root):
        record[record_key(root, path)] = file_digest(path)
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
        data = strict_json_loads(target.read_text(encoding="utf-8"))
        recorded = data["files"]
    except DuplicateKeyError:
        return [
            "the checksum record at %s holds a repeated key"
            % CHECKSUM_REL
        ]
    except (OSError, ValueError, KeyError, TypeError):
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


def task06_planted_rule(task_dir):
    """Parse the task-06 planted grading rule into checkable parts.

    Returns the D1 file name and the old module name. Fails
    closed. When the rule prose no longer parses, the caller
    reports a problem instead of grading against a guess.
    """
    try:
        text = (task_dir / "planted.md").read_text(encoding="utf-8")
    except OSError:
        return None, None, ["the task-06 planted file cannot be read"]
    rename = re.search(r"renames (\w+)\.py to (\w+)\.py", text)
    d1 = re.search(r"(\w+\.py) still imports", text)
    if rename is None or d1 is None:
        return None, None, ["the task-06 planted rule no longer parses"]
    return d1.group(1), rename.group(1), []


def transcript_fences(task_dir):
    """Split the task-06 transcripts into the raw and packet fences."""
    try:
        text = (task_dir / "transcripts.md").read_text(encoding="utf-8")
    except OSError:
        return None, ["the task-06 transcripts cannot be read"]
    fences = []
    for heading in (
        "## The raw pass transcript",
        "## The packet pass transcript",
    ):
        start = text.find(heading)
        if start < 0:
            return None, [
                "the task-06 transcripts hold no %s heading" % heading
            ]
        fence_open = text.find("```", start)
        fence_close = text.find("```", fence_open + 3)
        if fence_open < 0 or fence_close < 0:
            return None, [
                "the task-06 transcript under %s holds no fence" % heading
            ]
        fences.append(text[fence_open + 3:fence_close])
    return fences, []


def doubled_operand(diff):
    """Name the value the rebuilt diff adds to itself, if any."""
    for line in diff.split(b"\n"):
        if line.startswith(b"+") and not line.startswith(b"+++"):
            match = re.search(rb"\b(\w+) \+ \1\b", line)
            if match:
                return match.group(1).decode("ascii")
    return None


def task06_grade_fence(fence, d1_file, old_module, operand):
    """Grade one transcript fence under the planted rule.

    The D1 defect sits in an unchanged file, so the rule counts
    it only when the pass names the file and its import of the
    old module name. The D2 defect sits in the diff itself, so
    the rule counts it when the pass names the doubled return
    line.
    """
    d1 = (
        re.search(r"\b%s\b" % re.escape(d1_file), fence) is not None
        and re.search(r"\b%s\b" % re.escape(old_module), fence)
        is not None
    )
    doubled = (
        re.search(
            r"\b%s\b.*\b%s\b"
            % (re.escape(operand), re.escape(operand)),
            fence,
            re.DOTALL,
        )
        is not None
    )
    named = re.search(r"\b%s\b" % re.escape(operand), fence) is not None
    doubling = (
        re.search(r"\b(doubled|doubles|twice|itself|plus)\b", fence)
        is not None
    )
    d2 = doubled or (named and doubling)
    return (1 if d1 else 0, 1 if d2 else 0)


def recorded_task06_scores(root):
    """Read the recorded task-06 scores from both summaries.

    Returns the shared pair of (found, planted) scores for the
    raw and packet passes. Fails closed when a passage cannot be
    found, when a score cannot be parsed, or when the two
    summaries disagree with each other.
    """
    scores = {}
    for name, marker in (
        ("RESULTS.md", "task-06 is the replay task"),
        ("PASS-NOTES.md", "## The round 6 passes over the replay task-06"),
    ):
        try:
            text = (root / "evals" / name).read_text(encoding="utf-8")
        except OSError:
            return None, ["the %s file cannot be read" % name]
        start = text.find(marker)
        if start < 0:
            return None, [
                "the task-06 passage cannot be found in %s" % name
            ]
        window = text[start:]
        cut = window.find("\n## ", 1)
        if cut > 0:
            window = window[:cut]
        raw = re.search(r"raw pass reported (\d+) of (\d+)", window)
        packet = re.search(r"packet pass reported (\d+) of (\d+)", window)
        if raw is None or packet is None:
            return None, [
                "the task-06 recorded scores cannot be parsed in %s"
                % name
            ]
        scores[name] = (
            (int(raw.group(1)), int(raw.group(2))),
            (int(packet.group(1)), int(packet.group(2))),
        )
    if scores["RESULTS.md"] != scores["PASS-NOTES.md"]:
        return None, [
            "the task-06 recorded scores in RESULTS.md and "
            "PASS-NOTES.md disagree"
        ]
    return scores["RESULTS.md"], []


def task06_anchor_problems(repo, rebuilt_diff, d1_file, old_module):
    """Check the planted defects still stand in the rebuilt artefacts.

    Returns the doubled operand the D2 grading needs. A tampered
    sources file that drops a planted defect fails here even when
    every artefact was regenerated from it and every refreshable
    record was refreshed, because the transcripts and the planted
    rule still describe the defect the head no longer carries.
    """
    operand = doubled_operand(rebuilt_diff)
    if operand is None:
        return None, [
            "the planted D2 defect of task-06 no longer stands in "
            "the rebuilt diff"
        ]
    try:
        first_line = (
            (repo / d1_file)
            .read_text(encoding="utf-8", errors="replace")
            .splitlines()[0]
        )
    except (OSError, IndexError):
        first_line = ""
    problems = []
    if not re.match(
        r"\s*from %s import\b" % re.escape(old_module), first_line
    ):
        problems.append(
            "the planted D1 defect of task-06 no longer stands in "
            "the rebuilt head"
        )
    return operand, problems


def task06_problems(root):
    """Derive the task-06 scores from its transcripts and its rule.

    The derivation ties the diff, the packet, the transcripts and
    both summaries together leg by leg. The planted grading rule
    parses into the D1 file and the old module name, the rebuilt
    head must still carry the stale import and the rebuilt diff
    must still carry the doubled return line, each transcript
    fence grades under the rule, and the derived scores must
    match the recorded sentences in both summaries. Any leg that
    moves without the others fails here.
    """
    task_dir = root / "evals" / "tasks" / "task-06"
    problems = []
    d1_file, old_module, parse_problems = task06_planted_rule(task_dir)
    problems.extend(parse_problems)
    fences, fence_problems = transcript_fences(task_dir)
    problems.extend(fence_problems)
    if problems:
        return problems
    try:
        sources = strict_json_loads(
            (task_dir / "sources.json").read_text(encoding="utf-8")
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return ["the task-06 sources cannot be read with %s" % exc]
    try:
        with tempfile.TemporaryDirectory() as tmp:
            repo, _base, _head, rebuilt_diff = build_fixture_repo(
                tmp, sources
            )
            operand, anchor_problems = task06_anchor_problems(
                repo, rebuilt_diff, d1_file, old_module
            )
            problems.extend(anchor_problems)
    except (
        OSError,
        ValueError,
        KeyError,
        AssertionError,
        subprocess.SubprocessError,
    ) as exc:
        return ["the task-06 rebuild failed with %s" % exc]
    if operand is None:
        return problems
    raw_d1, raw_d2 = task06_grade_fence(
        fences[0], d1_file, old_module, operand
    )
    packet_d1, packet_d2 = task06_grade_fence(
        fences[1], d1_file, old_module, operand
    )
    recorded, recorded_problems = recorded_task06_scores(root)
    problems.extend(recorded_problems)
    if recorded is None:
        return problems
    (raw_found, raw_planted), (packet_found, packet_planted) = recorded
    if raw_planted != 2 or packet_planted != 2:
        problems.append(
            "the task-06 recorded scores plant a count other than 2"
        )
    if raw_d1 + raw_d2 != raw_found:
        problems.append(
            "the task-06 raw pass derives as %d of 2 and the "
            "summaries record %d of 2" % (raw_d1 + raw_d2, raw_found)
        )
    if packet_d1 + packet_d2 != packet_found:
        problems.append(
            "the task-06 packet pass derives as %d of 2 and the "
            "summaries record %d of 2"
            % (packet_d1 + packet_d2, packet_found)
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


def corpus_sections(text):
    """Map each incidents section title to its cited test names."""
    sections = {}
    pattern = re.compile(r"^## (.+?) incidents\s*$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    for index, match in enumerate(matches):
        start = match.end()
        if index + 1 < len(matches):
            end = matches[index + 1].start()
        else:
            end = len(text)
        sections[match.group(1)] = cited_test_names(text[start:end])
    return sections


def corpus_coverage_problems(root):
    """Check the corpus index against its per section coverage record.

    The coverage record pins the cited test names of each
    incidents section, so a dropped row or a dropped citation
    fails here even after a checksum refresh, because the
    refresh does not move this record. A deliberate index change
    moves the record first with the coverage write flag, as its
    own committed step.
    """
    target = root / CORPUS_COVERAGE_REL
    if not target.is_file():
        return [
            "no corpus coverage record stands at %s" % CORPUS_COVERAGE_REL
        ]
    try:
        data = strict_json_loads(target.read_text(encoding="utf-8"))
        recorded = data["sections"]
    except DuplicateKeyError:
        return [
            "the corpus coverage record at %s holds a repeated key"
            % CORPUS_COVERAGE_REL
        ]
    except (OSError, ValueError, KeyError, TypeError):
        return [
            "the corpus coverage record at %s does not parse"
            % CORPUS_COVERAGE_REL
        ]
    if not isinstance(recorded, dict):
        return [
            "the corpus coverage record at %s holds no sections map"
            % CORPUS_COVERAGE_REL
        ]
    try:
        text = (root / "evals" / "corpus.md").read_text(encoding="utf-8")
    except OSError:
        return ["the corpus index cannot be read"]
    current = corpus_sections(text)
    for title in sorted(current):
        if title not in recorded:
            return [
                "the corpus section %s stands with no coverage "
                "record" % title
            ]
    for title in sorted(recorded):
        if title not in current:
            return [
                "the corpus coverage record names section %s with "
                "no section in the index" % title
            ]
    for title in sorted(current):
        want = recorded[title]
        if not isinstance(want, list):
            return [
                "the corpus coverage record holds no name list for "
                "section %s" % title
            ]
        if set(want) != current[title]:
            lost = sorted(set(want) - current[title])
            gained = sorted(current[title] - set(want))
            detail = []
            if lost:
                detail.append("lost " + ", ".join(lost))
            if gained:
                detail.append("gained " + ", ".join(gained))
            return [
                "the corpus section %s changed its cited names, %s"
                % (title, " and ".join(detail))
            ]
    return []


def write_corpus_coverage(root):
    text = (root / "evals" / "corpus.md").read_text(encoding="utf-8")
    sections = {
        title: sorted(names)
        for title, names in sorted(corpus_sections(text).items())
    }
    target = root / CORPUS_COVERAGE_REL
    target.write_text(
        json.dumps({"sections": sections}, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return len(sections)


def source_anchor_problems(root):
    """Check each task sources file against its recorded digest.

    The anchor record stands apart from the checksum refresh, so
    regenerating a task from tampered sources and refreshing the
    checksums does not move the anchor and the tamper fails
    here. A deliberate sources change moves the anchor first
    with the anchor write flag, as its own committed step.
    """
    target = root / SOURCE_ANCHORS_REL
    if not target.is_file():
        return [
            "no source anchor record stands at %s" % SOURCE_ANCHORS_REL
        ]
    try:
        data = strict_json_loads(target.read_text(encoding="utf-8"))
        anchored = data["sources"]
    except DuplicateKeyError:
        return [
            "the source anchor record at %s holds a repeated key"
            % SOURCE_ANCHORS_REL
        ]
    except (OSError, ValueError, KeyError, TypeError):
        return [
            "the source anchor record at %s does not parse"
            % SOURCE_ANCHORS_REL
        ]
    if not isinstance(anchored, dict):
        return [
            "the source anchor record at %s holds no sources map"
            % SOURCE_ANCHORS_REL
        ]
    tasks = root / "evals" / "tasks"
    if not tasks.is_dir():
        return ["no eval tasks stand under evals/tasks"]
    names = sorted(d.name for d in tasks.iterdir() if d.is_dir())
    for name in names:
        if name not in anchored:
            return ["eval task %s stands with no source anchor" % name]
    for name in sorted(anchored):
        if name not in names:
            return [
                "the source anchor record names %s with no task in "
                "the tree" % name
            ]
    for name in names:
        try:
            digest = file_digest(tasks / name / "sources.json")
        except OSError:
            return ["the sources file of %s cannot be read" % name]
        if anchored[name] != digest:
            return [
                "the sources of %s no longer match the source "
                "anchor record" % name
            ]
    return []


def write_source_anchors(root):
    tasks = root / "evals" / "tasks"
    anchored = {}
    for task_dir in sorted(tasks.iterdir()):
        if task_dir.is_dir():
            anchored[task_dir.name] = file_digest(
                task_dir / "sources.json"
            )
    target = root / SOURCE_ANCHORS_REL
    target.write_text(
        json.dumps({"sources": anchored}, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return len(anchored)


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


def build_fixture_repo(tmp, sources):
    """Build the two commit fixture history for a task.

    Returns the repository path and the rebuilt diff bytes. The
    same pins stand here as in the extractor, so a host line
    ending setting cannot drift the byte comparison.
    """
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
    rebuilt_diff = git(
        repo, *(DIFF_FLAGS + ["%s..%s" % (base, head)]), raw=True
    )
    return repo, base, head, rebuilt_diff


def load_packet_checker(root):
    path = root / "scripts" / "check_packet.py"
    spec = importlib.util.spec_from_file_location("gate_check_packet", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def shipped_packet_problems(root, task_dir, checker):
    problems = []
    try:
        manifest = strict_json_loads(
            (task_dir / "manifest.json").read_text(encoding="utf-8")
        )
        packet_text = (task_dir / "packet.md").read_text(
            encoding="utf-8", errors="surrogateescape"
        )
    except DuplicateKeyError:
        return [
            "the saved manifest of %s holds a repeated key"
            % task_dir.name
        ]
    except (OSError, ValueError) as exc:
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
    sources = strict_json_loads(
        (task_dir / "sources.json").read_text(encoding="utf-8")
    )
    repo, base, head, rebuilt_diff = build_fixture_repo(tmp, sources)
    problems = []
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
         "--range", "%s..%s" % (base, head),
         "--out", str(out)],
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
    rebuilt = strict_json_loads(
        (out / "manifest.json").read_text(encoding="utf-8")
    )
    saved = strict_json_loads(
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
    problems.extend(task06_problems(root))
    problems.extend(source_anchor_problems(root))
    problems.extend(corpus_problems(root))
    problems.extend(corpus_coverage_problems(root))
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
    parser.add_argument(
        "--write-source-anchors",
        action="store_true",
        help="refresh the source anchor digests from the current sources",
    )
    parser.add_argument(
        "--write-corpus-coverage",
        action="store_true",
        help="refresh the corpus coverage record from the current index",
    )
    args = parser.parse_args(argv)
    if args.write_source_anchors:
        count = write_source_anchors(ROOT)
        print(
            "check_evals: source anchors refreshed over %d tasks"
            % count
        )
        return 0
    if args.write_corpus_coverage:
        count = write_corpus_coverage(ROOT)
        print(
            "check_evals: corpus coverage refreshed over %d sections"
            % count
        )
        return 0
    if args.write_checksums:
        guard = source_anchor_problems(ROOT)
        guard.extend(corpus_coverage_problems(ROOT))
        if guard:
            for problem in guard:
                print("check_evals: %s" % problem, file=sys.stderr)
            print(
                "check_evals: refresh the source anchors or the "
                "corpus coverage first with --write-source-anchors "
                "or --write-corpus-coverage, each as its own "
                "committed step",
                file=sys.stderr,
            )
            return 2
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
        "and the results totals add up and the task-06 scores "
        "re-derive from its transcripts and every task rebuilds "
        "from its sources and every task sources file matches its "
        "anchor and every corpus name stands in the suite and the "
        "corpus coverage record matches the index"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
