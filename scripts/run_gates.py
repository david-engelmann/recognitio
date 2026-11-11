#!/usr/bin/env python3
"""Run the gate steps and key every verdict to the tree it ran on.

The Makefile wiring runs the steps and stops at the first
failure, and that wiring stays the gate. What the wiring
never produced is an artefact. A step printed a success
sentence to a terminal and left nothing behind, so a green
earned on one tree could not be told from a green earned on
another, a suite that lost test files printed the same
success at a lower count, and a green earned on a working
state carrying uncommitted edits certified a tree that was
never pushed. This runner is the shipped answer to that
family. It runs the same steps the Makefile check target
names, in the same order, and for each step it writes the
captured output to a log file named for the step and a meta
record beside it carrying the git tree hash of the tree
under test, the head, the step name, its exit code and its
count line where the step prints one. A run record names
the steps completed, the failing step where one failed,
and the steps never reached, so a stopped run names its
own frontier instead of leaving a reader to reconstruct it.

The tree identity is read from git before any step runs.
A working state that differs from its head is refused
unless the caller names the local mode with the allow
dirty flag, and a root that is not a git checkout at a
commit is refused outright, because a verdict that cannot
name its tree certifies nothing. The discover step count
is held against the pinned floor below, so the suite can
lose a test file in silence no longer. The floor moves
only in the same change that moves the census it pins.

One remainder stands named here rather than closed. The
submissions gate still measures its tree figures by
walking the working filesystem when it is run on its own,
outside this runner, so a standalone submissions verdict
is a working state verdict. Inside this runner the walk
runs on the state this runner just keyed, and the figures
the pack states are re-derived from the shipped tree by
the suite census beside it. The gate tests also still
assert most gate outcomes from in process summaries
rather than from artefacts like the ones this runner
writes, and that family stands as a named gap for a later
round to close with a subprocess smoke per gate script.

A second remainder stands named beside it. The vacuity
guard mirror of the discover set reads the top level of
the tests folder, so a vacuous test file standing in a
subdirectory of that folder draws no refusal from the
mirror and moves the discover count by nothing the floor
can see, and that blind spot stands open for the round
that next owns the guard. The runner own log folder
stands outside the dirtiness it judges, because a runner
that counted its own output as dirt could never key a
clean tree in its default shape, and the run record
names how many standing entries that exclusion covered.

Exits zero only when every step ran and passed on the
keyed tree at or above the pinned floor.
"""

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PINNED_TEST_FLOOR = 3039

RAN_RE = re.compile(r"^Ran (\d+) tests", re.M)

OWN_OUTPUT_ROOT = ".gate-logs"


def parse_makefile_steps(text):
    """The check target recipe as a list of command lists.

    The recipe lines under the check target are the wiring,
    so the runner reads its step list from the Makefile
    itself and the two can never drift apart. The Python
    variable the Makefile spells stands for the interpreter
    running this script.
    """
    steps = []
    in_check = False
    for line in text.splitlines():
        if line.startswith("check:"):
            in_check = True
            continue
        if in_check:
            if line.startswith("\t"):
                recipe = line.strip()
                recipe = recipe.replace(
                    "$(PYTHON)", sys.executable
                )
                steps.append(recipe.split())
            elif line.strip():
                break
    return steps


def step_name(argv):
    """A short stable name for one step command."""
    if "unittest" in argv:
        return "discover"
    for part in argv:
        if part.endswith(".py"):
            return Path(part).stem
    return "-".join(argv[1:]) or argv[0]


def _git(root, *args):
    try:
        out = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True, text=True, timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout


def _porcelain_paths(line):
    """The paths a porcelain status line names.

    The line carries a two letter state and a space before
    the path, and a rename or a copy spells its pair with an
    arrow between the old name and the new one, so the
    reading returns both names of the pair where an arrow
    stands and the one name otherwise.
    """
    text = line[3:] if len(line) > 3 else ""
    if " -> " in text:
        old, new = text.split(" -> ", 1)
        return [
            old.strip().strip('"'),
            new.strip().strip('"'),
        ]
    return [text.strip().strip('"')]


def _is_own_output(line):
    """Whether a status line names only the runner output.

    The runner output stands apart only while it is
    untracked, because an untracked entry under the log
    folder can only be the runner own writing. A tracked
    entry under that folder, and any rename or copy whose
    either name stands outside it, is a change to the tree
    under test and never the runner output.
    """
    if line[:2] != "??":
        return False
    paths = _porcelain_paths(line)
    return bool(paths) and all(
        path == OWN_OUTPUT_ROOT
        or path.startswith(OWN_OUTPUT_ROOT + "/")
        for path in paths
    )


def tree_identity(root):
    """The head, the tree hash and the dirty state of a root.

    Returns None when the root is not a git checkout at a
    commit, because no verdict can be keyed to such a root.
    Standing entries under the runner own log folder are
    counted apart, because that folder is the runner output
    and never part of the tree under test.
    """
    head = _git(root, "rev-parse", "HEAD")
    tree = _git(root, "rev-parse", "HEAD^{tree}")
    if head is None or tree is None:
        return None
    status = _git(root, "status", "--porcelain")
    if status is None:
        return None
    entries = [
        line for line in status.splitlines() if line.strip()
    ]
    own = [line for line in entries if _is_own_output(line)]
    foreign = [line for line in entries if line not in own]
    return {
        "head": head.strip(),
        "tree": tree.strip(),
        "dirty": bool(foreign),
        "dirty_entries": foreign,
        "own_output_entries": len(own),
    }


def count_line(output):
    """The count a step printed, and the line that carried it.

    Only the discover step prints a count in a stable form,
    so the reading names that form and returns no count
    anywhere else rather than inventing one. The last match
    in the output is the count, because a stray earlier line
    in the combined output can claim a count the step never
    printed as its verdict, and the first match reading let
    such a line overstate the count the floor arm reads.
    """
    matches = list(RAN_RE.finditer(output))
    if matches:
        match = matches[-1]
        return int(match.group(1)), match.group(0)
    return None, None


def run_gates(root, log_dir=None, allow_dirty=False, steps=None,
              floor=None):
    """Run the gate steps on one root and write their records.

    Returns the exit code and the run record. The record is
    also written to the log directory as it grows, so a run
    that stops early still leaves its frontier on disk.
    """
    root = Path(root)
    floor = PINNED_TEST_FLOOR if floor is None else floor
    if steps is None:
        makefile = root / "Makefile"
        steps = parse_makefile_steps(
            makefile.read_text(encoding="utf-8")
        )
    identity = tree_identity(root)
    if identity is None:
        record = {
            "verdict": "refused, the root is not a git checkout "
                       "at a commit, so no tree can be keyed",
            "tree": None,
            "head": None,
            "steps_completed": [],
            "failing_step": None,
            "steps_not_run": [step_name(s) for s in steps],
        }
        return 1, record
    if log_dir is None:
        log_dir = root / ".gate-logs"
    run_dir = Path(log_dir) / identity["tree"]
    run_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "verdict": "running",
        "tree": identity["tree"],
        "head": identity["head"],
        "dirty": identity["dirty"],
        "allow_dirty": bool(allow_dirty),
        "own_output_entries": identity["own_output_entries"],
        "pinned_test_floor": floor,
        "steps_completed": [],
        "failing_step": None,
        "steps_not_run": [step_name(s) for s in steps],
    }

    def write_record():
        (run_dir / "run.json").write_text(
            json.dumps(record, indent=1) + "\n", encoding="utf-8"
        )

    write_record()
    if identity["dirty"] and not allow_dirty:
        record["verdict"] = (
            "refused, the working state differs from its head "
            "and the allow dirty local mode was not named"
        )
        record["dirty_entries"] = identity["dirty_entries"]
        write_record()
        return 1, record
    names = [step_name(s) for s in steps]
    for index, argv in enumerate(steps):
        name = names[index]
        started = time.time()
        try:
            proc = subprocess.run(
                argv, cwd=str(root), capture_output=True,
                text=True, timeout=3600,
            )
            output = (proc.stdout or "") + (proc.stderr or "")
            code = proc.returncode
        except (OSError, subprocess.SubprocessError) as exc:
            output = "the step could not be run, %s" % exc
            code = 1
        (run_dir / ("%02d-%s.log" % (index + 1, name))).write_text(
            output, encoding="utf-8"
        )
        count, line = count_line(output)
        meta = {
            "step": name,
            "index": index + 1,
            "command": argv,
            "tree": identity["tree"],
            "head": identity["head"],
            "exit_code": code,
            "count": count,
            "count_line": line,
            "seconds": round(time.time() - started, 3),
            "log": "%02d-%s.log" % (index + 1, name),
        }
        (run_dir / ("%02d-%s.json" % (index + 1, name))).write_text(
            json.dumps(meta, indent=1) + "\n", encoding="utf-8"
        )
        failed = code != 0
        reason = None
        if name == "discover" and count is not None and count < floor:
            failed = True
            reason = (
                "the discover step counted %d tests, under the "
                "pinned floor of %d" % (count, floor)
            )
        if failed:
            record["failing_step"] = name
            if reason:
                record["failure_reason"] = reason
            record["steps_not_run"] = names[index + 1:]
            record["verdict"] = "failed at step %s" % name
            write_record()
            return 1, record
        record["steps_completed"].append(name)
        record["steps_not_run"] = names[index + 1:]
        write_record()
    missing = [
        name for index, name in enumerate(names)
        if not (run_dir / ("%02d-%s.json" % (index + 1, name))).is_file()
    ]
    if missing:
        record["verdict"] = (
            "failed, step meta records stand missing for %s"
            % ", ".join(missing)
        )
        write_record()
        return 1, record
    record["verdict"] = "pass"
    record["steps_not_run"] = []
    write_record()
    return 0, record


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run the gate steps with tree keyed records."
    )
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--log-dir", default=None)
    parser.add_argument("--allow-dirty", action="store_true")
    args = parser.parse_args(argv)
    code, record = run_gates(
        Path(args.root),
        log_dir=Path(args.log_dir) if args.log_dir else None,
        allow_dirty=args.allow_dirty,
    )
    print("run_gates: %s" % record["verdict"])
    if record.get("tree"):
        print(
            "run_gates: tree %s at head %s, %d steps completed"
            % (
                record["tree"], record["head"],
                len(record["steps_completed"]),
            )
        )
    return code


if __name__ == "__main__":
    sys.exit(main())
