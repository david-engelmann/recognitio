#!/usr/bin/env python3
"""Recognitio extractor.

Assembles a verified review packet (the pericope) for a pull request, a
commit range, or a single commit, using only the local git clone. The
extractor never trusts a hosted API diff. It resolves refs locally, builds
tiered context, and recounts files, statuses, hunks and lines with
separate git invocations before it will call a packet verified. Any
disagreement fails closed.

Every git invocation runs with its output format pinned, so ambient
configuration in the clone or in the user's global config cannot reshape
the diff under the packet. Every invocation also refuses replace
objects, so a replace ref planted in the clone cannot swap the objects
the packet is built from while the packet keeps the real head's name.
File paths reach git as literal pathspecs, never as patterns. Path data
moves through NUL delimited output, so quoted, spaced and Unicode
paths survive end to end. All subprocess output is handled as bytes
first, so binary files and non UTF-8 content cannot crash the run.
"""

import argparse
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
EXTRACTOR_VERSION = "1.3.0"
SOURCE_EXTS = {".py", ".js", ".jsx", ".ts", ".tsx", ".rs", ".go"}
MAX_CALL_SITES_PER_FUNCTION = 5
MAX_TEST_FILES = 10
MAX_MATCH_LINES_PER_TEST_FILE = 5
MAX_IMPORT_LINES_PER_FILE = 20
MAX_DEFINITIONS_PER_NAME = 3
MAX_HISTORY_FILES = 3
MAX_BLAME_RANGES = 10
MAX_BLAME_SUMMARY_LINES = 10
MAX_LOG_L_FUNCTIONS = 3
MAX_LOG_L_CHARS = 4000
MAX_RANGE_DIFF_CHARS = 8000
MAX_PR_BODY_CHARS = 4000
MAX_PRIOR_PRS = 5
MAX_PRIOR_PR_LIST = 30
MAX_SPEC_REFERENCES = 5
MAX_FINDINGS_ACCOUNTED = 100

STATUS_NAMES = {
    "A": "added",
    "M": "modified",
    "D": "deleted",
    "R": "renamed",
    "C": "copied",
    "T": "typechange",
    "U": "unmerged",
    "X": "unknown",
}

FUNC_PATTERNS = [
    re.compile(r"(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)"),
    re.compile(r"(?:pub(?:\([^)]*\))?\s+)?fn\s+([A-Za-z_][A-Za-z0-9_]*)"),
    re.compile(r"func\s+(?:\([^)]*\)\s*)?([A-Za-z_][A-Za-z0-9_]*)"),
    re.compile(r"function\s+([A-Za-z_][A-Za-z0-9_]*)"),
    re.compile(r"(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:async\s*)?(?:\(|function)"),
]

CLASS_PATTERN = re.compile(r"class\s+([A-Za-z_][A-Za-z0-9_]*)")

IMPORT_PATTERNS = {
    ".py": re.compile(r"^\s*(import\s+\S|from\s+\S+\s+import)"),
    ".js": re.compile(r"^\s*(import\s|const\s+.*=\s*require\(|let\s+.*=\s*require\(|var\s+.*=\s*require\()"),
    ".jsx": re.compile(r"^\s*(import\s|const\s+.*=\s*require\(|let\s+.*=\s*require\(|var\s+.*=\s*require\()"),
    ".ts": re.compile(r"^\s*(import\s|const\s+.*=\s*require\()"),
    ".tsx": re.compile(r"^\s*(import\s|const\s+.*=\s*require\()"),
    ".rs": re.compile(r"^\s*(pub\s+)?use\s"),
    ".go": re.compile(r"^\s*(import\s|\"[^\"]+\")"),
}

# Files whose diff is replaced by a named placeholder in the packet.
# The manifest still counts their lines and hunks in full, and the
# packet header names every one of them with its reason.
LOCKFILE_NAMES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Cargo.lock",
    "poetry.lock",
    "Pipfile.lock",
    "Gemfile.lock",
    "composer.lock",
    "go.sum",
    "flake.lock",
    "packages.lock.json",
}
# Files whose whole purpose is to steer the agent that loads the
# tree. A change to one changes agent behaviour rather than merely
# describing code, so the packet flags it in the triage list and in
# the manifest instead of listing it exactly like ordinary code.
# The set is name based and deterministic. It covers the agent
# guidance names hosts load at any depth, the Copilot instructions
# file name, the path specific Copilot instructions files under
# .github/instructions, the Cursor rules names, the Claude
# rules files under .claude/rules, and the plugin surfaces
# below in is_instruction_path, the output styles and the
# plugin agent files at the plugin root.
INSTRUCTION_BASENAMES = {
    "AGENTS.md",
    "CLAUDE.md",
    "SKILL.md",
    "GEMINI.md",
    "copilot-instructions.md",
    ".cursorrules",
}
GENERATED_SUFFIXES = (
    ".pb.go",
    "_pb2.py",
    "_pb2_grpc.py",
    ".min.js",
    ".min.css",
    ".generated.ts",
    ".generated.tsx",
)

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
URL_RE = re.compile(r"https?://[^\s<>\"')\]]+")
ISSUE_REF_RE = re.compile(r"#(\d+)\b")
FINDING_RE = re.compile(r"^(.*?):(\d+):\s?(.*)$")

# Pin the output format of every git invocation. Ambient configuration,
# whether it sits in the clone under review or in the user's global
# config, must not be able to reshape the data the packet is built from
# or the data the recount reads.
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
# Diff invocations also refuse external diff drivers and textconv
# filters, both of which can rewrite the text of a change.
DIFF_FLAGS = ["--no-ext-diff", "--no-textconv"]


class GitError(Exception):
    pass


class Proc:
    """A finished subprocess with text output decoded byte safely."""

    def __init__(self, returncode, stdout, stderr):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def display_path(path):
    """Render a path as one safe line of packet text.

    A path is data the reviewed party controls and it can carry a
    newline. Written raw into a heading or a list it would print
    forged packet sections in the packet's own voice and it would
    split one record across lines. Control characters are escaped
    instead, so a crafted name stays one inert line everywhere the
    packet names a file. The manifest keeps the true path as data.
    """
    if path is None:
        return ""
    out = []
    for char in str(path):
        if char == "\\":
            out.append("\\\\")
        elif char == "\n":
            out.append("\\n")
        elif char == "\r":
            out.append("\\r")
        elif char == "\t":
            out.append("\\t")
        elif ord(char) < 32 or ord(char) == 127:
            out.append("\\x%02x" % ord(char))
        elif char in ("\u0085", "\u2028", "\u2029"):
            # Unicode line separators split lines for many readers
            # even though they are not newline characters, so a
            # name carrying one would print a second line that
            # looks like packet structure to those readers.
            out.append("\\u%04x" % ord(char))
        else:
            out.append(char)
    return "".join(out)


def sanitize_packet_text(text):
    """Keep raw NUL bytes out of packet text.

    A blob that turns from binary to text is shown through a text
    diff, and the old side of that diff can carry raw NUL bytes
    into a document every downstream tool reads as Markdown text.
    The byte is named instead of carried, which changes no line
    count because the replacement holds no newline.
    """
    if not text:
        return text
    return text.replace("\x00", "[NUL]")


def decode_bytes(data):
    """Decode subprocess bytes without ever failing.

    Surrogate escapes carry undecodable bytes through as data, so CRLF
    endings and legacy encodings survive into the packet unchanged.
    """
    return data.decode("utf-8", "surrogateescape")


# Git location variables are scrubbed from the child environment. An
# exported GIT_DIR defeats git -C, so an extractor launched from a git
# hook or a configured shell would silently read a different
# repository, and the recount would read that same repository and
# still agree with the packet. The replace object controls are
# scrubbed for the same reason and then pinned off outright in
# run_process. A replace ref in the clone under review redirects
# every object read to a different object, so assembly and recount
# would agree perfectly about the wrong tree under the real head's
# name, and no output pin can see it.
GIT_LOCATION_VARS = (
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

# Every child process gets a timeout, the network calls to the GitHub
# CLI included. A stalled call must fail the run, never hang it.
PROCESS_TIMEOUT_SECONDS = 120


def run_process(argv, cwd=None):
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in GIT_LOCATION_VARS
    }
    # The second belt behind the --no-replace-objects flag every git
    # invocation carries. Whichever layer a future call site forgets,
    # the other still refuses replacement objects.
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    try:
        return subprocess.run(
            list(argv), cwd=str(cwd) if cwd is not None else None,
            capture_output=True, env=env,
            timeout=PROCESS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise GitError(
            "command timed out after %d seconds: %s"
            % (
                PROCESS_TIMEOUT_SECONDS,
                " ".join(str(part) for part in argv),
            )
        ) from exc
    except OSError as exc:
        # A missing executable, the GitHub CLI most often, is a run
        # failure in the tool's own voice, never a raw traceback. The
        # caller routes GitError to the failure receipt and exit 2.
        raise GitError(
            "could not run %s: %s" % (argv[0], exc)
        ) from exc


def run_argv(argv, cwd, check, label):
    result = run_process(argv, cwd=cwd)
    proc = Proc(
        result.returncode,
        decode_bytes(result.stdout),
        decode_bytes(result.stderr),
    )
    if check and proc.returncode != 0:
        raise GitError(
            "%s failed with exit %d: %s"
            % (label, proc.returncode, proc.stderr.strip())
        )
    return proc


def run_git(repo, args, check=True, global_flags=()):
    # --no-replace-objects refuses replace refs, so the objects read
    # are the objects the recorded refs name. --literal-pathspecs
    # makes every pathspec in the invocation a literal path, so a
    # file named with glob characters is measured as itself and never
    # as a pattern that borrows a neighbour's diff.
    argv = (
        ["git", "--no-replace-objects", "--literal-pathspecs"]
        + list(global_flags)
        + ["-C", str(repo)] + GIT_PIN + list(args)
    )
    return run_argv(argv, None, check, "git " + " ".join(args))


def run_cmd(cwd, args, check=True):
    return run_argv(list(args), cwd, check, " ".join(args))


def rev_parse(repo, ref):
    return run_git(repo, ["rev-parse", "--verify", ref + "^{commit}"]).stdout.strip()


def merge_base(repo, left, right):
    return run_git(repo, ["merge-base", left, right]).stdout.strip()


def is_shallow(repo):
    out = run_git(repo, ["rev-parse", "--is-shallow-repository"]).stdout.strip()
    return out == "true"


def estimate_tokens(text):
    return len(text) // 4


def cap_text(text, limit, label, mark=True):
    if len(text) <= limit:
        return text, False
    if not mark:
        # The cap is stated once, in the cap notes block of the
        # tier that owns the text, so the text itself carries no
        # second wording of the same event inside its fence.
        return text[:limit], True
    return text[:limit] + "\n[recognitio] %s capped at %d characters.\n" % (label, limit), True


def render_notes(notes):
    """The cap notes of one tier, grouped under one labelled block.

    Every note carries the one wording, and a note the tier
    recorded more than once stands once in the packet. The
    manifest keeps the recorded list as it stands.
    """
    lines = []
    seen = []
    for note in notes:
        if note not in seen:
            seen.append(note)
    if not seen:
        return lines
    lines.append("### Cap notes")
    lines.append("")
    for note in seen:
        lines.append("Cap note: %s." % note)
        lines.append("")
    return lines


def refuse_shallow(repo):
    if is_shallow(repo):
        raise GitError(
            "the local clone is shallow, so its history is truncated and no "
            "packet built from it can be trusted. Fetch the full history "
            "first, for example with git fetch --unshallow, then run again"
        )


def resolve_pr(repo, args, since_sha):
    view = run_cmd(
        repo,
        [
            "gh", "pr", "view", str(args.pr),
            "--json",
            "baseRefOid,headRefOid,baseRefName,headRefName,title,body",
        ],
    )
    try:
        data = json.loads(view.stdout)
    except json.JSONDecodeError as exc:
        raise GitError("gh pr view returned unparseable JSON: %s" % exc)
    if not isinstance(data, dict):
        raise GitError(
            "gh pr view returned JSON that is not an object, so pull "
            "request %d cannot be resolved from it" % args.pr
        )
    resolved_refs = {}
    for key, target in (("baseRefOid", "base"), ("headRefOid", "head")):
        oid = data.get(key)
        if not oid:
            raise GitError(
                "gh did not return a %s for pull request %d" % (key, args.pr)
            )
        probe = run_git(repo, ["cat-file", "-e", oid + "^{commit}"], check=False)
        if probe.returncode != 0:
            raise GitError(
                "the %s %s of pull request %d is not in the local clone. "
                "Fetch it first, for example with gh pr checkout %d or git "
                "fetch, then run again" % (target, oid, args.pr, args.pr)
            )
        resolved_refs[target] = rev_parse(repo, oid)
    base = resolved_refs["base"]
    head = resolved_refs["head"]
    body = data.get("body") or ""
    pr_info = {
        "number": args.pr,
        "title": data.get("title") or "",
        "body": body,
        "spec_references": find_spec_references(body),
    }
    return {
        "mode": "pr",
        "label": "pull request %d" % args.pr,
        "base": base,
        "head": head,
        "merge_base": merge_base(repo, base, head),
        "since": since_sha,
        "pr": pr_info,
    }


def find_spec_references(body):
    """Collect the links and issue references a PR body carries."""
    refs = []
    for match in URL_RE.finditer(body):
        ref = match.group(0).rstrip(".,;")
        if ref not in refs:
            refs.append(ref)
    for match in ISSUE_REF_RE.finditer(body):
        ref = "#" + match.group(1)
        if ref not in refs:
            refs.append(ref)
    return refs[:MAX_SPEC_REFERENCES]


def resolve_range(repo, args, since_sha):
    spec = args.range
    if "..." in spec:
        left, right = spec.split("...", 1)
    elif ".." in spec:
        left, right = spec.split("..", 1)
    else:
        raise GitError("range must look like A..B or A...B, got %r" % spec)
    if not left or not right:
        raise GitError("range must name both ends, got %r" % spec)
    base = rev_parse(repo, left)
    head = rev_parse(repo, right)
    return {
        "mode": "range",
        "label": "range %s" % spec,
        "base": base,
        "head": head,
        "merge_base": merge_base(repo, base, head),
        "since": since_sha,
        "pr": None,
    }


def resolve_commit(repo, args, since_sha):
    head = rev_parse(repo, args.commit)
    parent = run_git(repo, ["rev-parse", "--verify", head + "^"], check=False)
    if parent.returncode == 0:
        base = parent.stdout.strip()
        return {
            "mode": "commit",
            "label": "commit %s" % head[:12],
            "base": base,
            "head": head,
            "merge_base": base,
            "since": since_sha,
            "pr": None,
        }
    # A root commit has no parent and no merge base. The diff runs
    # against the empty tree, and the manifest records the merge base
    # as absent rather than mislabelling a tree as a commit.
    return {
        "mode": "commit",
        "label": "commit %s" % head[:12],
        "base": None,
        "head": head,
        "merge_base": None,
        "since": since_sha,
        "pr": None,
    }


def resolve_inputs(repo, args):
    """Return a dict with mode, refs, merge base, label, since and pr."""
    refuse_shallow(repo)
    since_sha = rev_parse(repo, args.since) if args.since else None
    if args.pr is not None:
        return resolve_pr(repo, args, since_sha)
    if args.range:
        return resolve_range(repo, args, since_sha)
    if args.commit:
        return resolve_commit(repo, args, since_sha)
    raise GitError("one of --pr, --range, or --commit is required")


def parse_name_status_z(text):
    """Parse NUL delimited name-status output into file entries."""
    fields = text.split("\0")
    while fields and fields[-1] == "":
        fields.pop()
    files = []
    index = 0
    while index < len(fields):
        code = fields[index]
        index += 1
        letter = code[:1]
        entry = {
            "status_code": code,
            "status": STATUS_NAMES.get(letter, "unknown"),
            "old_path": None,
            "path": None,
        }
        if letter in ("R", "C"):
            entry["old_path"] = fields[index]
            entry["path"] = fields[index + 1]
            index += 2
        else:
            entry["path"] = fields[index]
            index += 1
        files.append(entry)
    return files


def parse_numstat_z(text):
    """Parse NUL delimited numstat output.

    Returns a mapping of path to (additions, deletions) plus the set of
    paths git reported with the binary marker instead of line counts.
    """
    fields = text.split("\0")
    while fields and fields[-1] == "":
        fields.pop()
    stats = {}
    binary_paths = set()
    index = 0
    # The path field runs to the end of the NUL delimited record
    # and it may itself carry a newline, so the pattern must match
    # across lines and anchor at the true end of the record. A
    # pattern that stops at a newline truncates the record and
    # reads a crafted name at zero counts.
    record_re = re.compile(r"^([^\t]+)\t([^\t]+)\t([\s\S]*)\Z")
    while index < len(fields):
        match = record_re.match(fields[index])
        index += 1
        if not match:
            continue
        adds_raw, dels_raw, path_field = match.groups()
        if path_field == "":
            # A rename carries an empty path field, then the old and
            # new paths as their own NUL terminated fields.
            index += 1  # the old path
            path = fields[index]
            index += 1
        else:
            path = path_field
        if adds_raw == "-" or dels_raw == "-":
            stats[path] = (0, 0)
            binary_paths.add(path)
        else:
            stats[path] = (int(adds_raw), int(dels_raw))
    return stats, binary_paths


def split_diff(text):
    """Split a full diff into per file chunks, in emission order.

    The chunk order of a git diff matches the order of the matching
    name-status output, so callers pair chunks with file entries by
    position. No path is ever parsed out of a diff header, which keeps
    paths containing spaces or the text b/ intact.
    """
    chunks = []
    current = None
    for line in text.splitlines(keepends=True):
        if line.startswith("diff --git "):
            if current is not None:
                chunks.append("".join(current))
            current = [line]
        elif current is not None:
            current.append(line)
    if current is not None:
        chunks.append("".join(current))
    return chunks


def count_hunks(chunk):
    return sum(1 for line in chunk.splitlines() if line.startswith("@@ "))


def count_chunk_lines(chunk):
    """Count added and deleted lines in a zero context diff chunk.

    The chunk is parsed structurally. Lines count only inside a hunk,
    so the +++ and --- file headers, which stand before the first hunk
    header, are never mistaken for content, and a content line whose
    own text begins with ++ or --, a SQL comment or a TOML delimiter,
    counts as the content it is.
    """
    adds = 0
    dels = 0
    in_hunks = False
    for line in chunk.splitlines():
        if line.startswith("@@ "):
            in_hunks = True
            continue
        if not in_hunks:
            continue
        if line.startswith("+"):
            adds += 1
        elif line.startswith("-"):
            dels += 1
    return adds, dels


def changed_ranges(chunk):
    """New side line ranges touched by a zero context diff chunk."""
    ranges = []
    for line in chunk.splitlines():
        match = HUNK_RE.match(line)
        if match:
            start = int(match.group(3))
            count = int(match.group(4)) if match.group(4) else 1
            if count > 0:
                ranges.append((start, start + count - 1))
    return ranges


def old_side_ranges(chunk):
    """Old side line ranges touched by a zero context diff chunk."""
    ranges = []
    for line in chunk.splitlines():
        match = HUNK_RE.match(line)
        if match:
            start = int(match.group(1))
            count = int(match.group(2)) if match.group(2) else 1
            ranges.append((start, count))
    return ranges


def extract_function_names(chunk):
    names = []
    for line in chunk.splitlines():
        if line.startswith("@@"):
            probe = line.split("@@", 2)[-1].strip()
        elif line[:1] in ("+", "-", " "):
            # Changed lines and context lines both count. With whole
            # function context the enclosing definition usually arrives
            # as a context line, and a function that starts on line 1 of
            # its file produces no hunk header context at all.
            probe = line[1:].strip()
        else:
            continue
        for pattern in FUNC_PATTERNS:
            match = pattern.match(probe)
            if match:
                name = match.group(1)
                if name not in names:
                    names.append(name)
    return names



def file_bytes(repo, ref, path):
    """Return the raw bytes of a file at a ref, or None when absent."""
    if ref is None or path is None:
        return None
    result = run_process(
        ["git", "--no-replace-objects", "--literal-pathspecs",
         "-C", str(repo)] + GIT_PIN
        + ["show", "%s:%s" % (ref, path)]
    )
    if result.returncode != 0:
        return None
    return result.stdout


def looks_textual(data):
    """True when bytes read as UTF-8 text with no NUL bytes early on."""
    if data is None:
        return False
    if b"\0" in data[:8192]:
        return False
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def decode_text(data):
    """Decode bytes as strict UTF-8, or return None when they are not."""
    if data is None:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def show_file(repo, head, path):
    return decode_text(file_bytes(repo, head, path))


def fetch_change(repo, diff_base, head):
    """Fetch the change channels between a diff base and a head.

    Path data comes back NUL delimited. The returned file entries are
    in git's emission order, and the chunk lists pair with them by
    position.
    """
    status_text = run_git(
        repo, ["diff", "--name-status", "-z", "-M", "-C"] + DIFF_FLAGS
        + [diff_base, head]
    ).stdout
    numstat_text = run_git(
        repo, ["diff", "--numstat", "-z", "-M", "-C"] + DIFF_FLAGS
        + [diff_base, head]
    ).stdout
    commit_log = run_git(
        repo, ["log", "--oneline", "--reverse", "%s..%s" % (diff_base, head)]
    ).stdout
    full_diff = run_git(
        repo,
        ["diff", "--histogram", "--find-renames", "--find-copies", "-W"]
        + DIFF_FLAGS + [diff_base, head],
    ).stdout
    precise_diff = run_git(
        repo,
        ["diff", "--histogram", "--find-renames", "--find-copies", "-U0"]
        + DIFF_FLAGS + [diff_base, head],
    ).stdout
    files = parse_name_status_z(status_text)
    stats, binary_paths = parse_numstat_z(numstat_text)
    full_chunks = split_diff(full_diff)
    precise_chunks = split_diff(precise_diff)
    chunks = {}
    precise = {}
    for position, entry in enumerate(files):
        chunks[entry["path"]] = (
            full_chunks[position] if position < len(full_chunks) else ""
        )
        precise[entry["path"]] = (
            precise_chunks[position] if position < len(precise_chunks) else ""
        )
    return {
        "files": files,
        "stats": stats,
        "binary_paths": binary_paths,
        "chunks": chunks,
        "precise_chunks": precise,
        "commit_log": commit_log,
    }


def entry_paths(entry):
    """Every path an entry answers to, oldest first."""
    paths = []
    if entry.get("old_path"):
        paths.append(entry["old_path"])
    paths.append(entry["path"])
    return paths


def per_file_text_diff(repo, diff_base, head, entry, context_flag):
    """Diff one file with the text flag, for attribute marked files.

    The diff runs over every path the file answers to, under literal
    pathspecs, so rename detection pairs the two sides of a rename
    and the chunk is the file's real delta rather than its whole new
    size, and a path carrying glob characters names itself alone.
    """
    result = run_git(
        repo,
        ["diff", "--text", "--histogram", "--find-renames",
         "--find-copies", context_flag] + DIFF_FLAGS
        + [diff_base, head, "--"] + entry_paths(entry),
    )
    chunks = split_diff(result.stdout)
    return chunks[0] if chunks else ""


def per_file_text_numstat(repo, diff_base, head, entry):
    """Git's own line counts for one file, read with the text flag.

    Returns the (additions, deletions) pair numstat reports for the
    entry's path, or None when git still reports the file as binary.
    This is the independent second count for attribute marked files,
    the same numstat source ordinary files are measured from.
    """
    result = run_git(
        repo,
        ["diff", "--text", "--numstat", "-z", "-M", "-C"] + DIFF_FLAGS
        + [diff_base, head, "--"] + entry_paths(entry),
    )
    stats, binary_paths = parse_numstat_z(result.stdout)
    if entry["path"] in binary_paths:
        return None
    return stats.get(entry["path"])


def has_generated_marker(content):
    """True when a file's first lines carry the do not edit marker."""
    if content is None:
        return False
    for line in content.splitlines()[:5]:
        lowered = line.lower()
        if "code generated" in lowered and "do not edit" in lowered:
            return True
    return False


def generated_reason(repo, diff_base, head, entry):
    """Name the placeholder reason for generated files and lockfiles.

    Returns the reason, the string "marker arrived" when the head
    version carries a generated marker the base version did not, or
    None. A name based reason, a lockfile name or a generated suffix,
    never depends on file content and always applies. The content
    marker is different. It is asserted by the file itself, so it
    withholds the diff only when the marker already stood at the
    base revision. A marker that arrives in the very change under
    review exempts nothing, and the caller flags its arrival while
    showing the change in full.
    """
    path = entry["path"]
    name = Path(path).name
    if name in LOCKFILE_NAMES:
        return "lockfile"
    if path.endswith(GENERATED_SUFFIXES):
        return "generated file"
    if Path(path).suffix not in SOURCE_EXTS:
        return None
    ref = head if entry["status"] != "deleted" else diff_base
    # A deletion carries its path in path alone. old_path is set only
    # for renames and copies, so reading through it loses the file.
    content = show_file(repo, ref, path)
    if not has_generated_marker(content):
        return None
    if entry["status"] == "deleted":
        # The content just read is the base revision's own, so the
        # marker predates the change by construction.
        return "generated file"
    base_path = entry["old_path"] or path
    base_content = show_file(repo, diff_base, base_path)
    if has_generated_marker(base_content):
        return "generated file"
    return "marker arrived"


def measure_binary_entry(repo, diff_base, head, entry, chunks, precise):
    """Measure one entry git reported with the binary marker.

    Returns the counts to record and the receipt entry for the
    file, or the incoming counts and no receipt when no bytes exist
    on either side, where the entry is a gitlink or similar and the
    diff chunk already speaks for itself. Two very different cases
    sit behind the marker and the receipt must not confuse them.
    When the old side holds real binary content and the head side
    is plain text, the file changed from binary to text in this
    change and no attributes file need exist. When both sides are
    plain text, git only calls the file binary because the tree
    marks it so through its attributes file. Count and show both
    as text, and name each one in the receipt by its real reason.
    """
    path = entry["path"]
    side_ref = head if entry["status"] != "deleted" else diff_base
    # The entry path names the file on both sides of a deletion.
    data = file_bytes(repo, side_ref, path)
    if data is None:
        return None, None
    if not looks_textual(data):
        entry["binary"] = True
        entry["head_bytes"] = len(data)
        entry["placeholder"] = (
            "(binary file of %d bytes at the %s revision. No "
            "textual diff is shown.)"
            % (len(data), "head" if entry["status"] != "deleted"
               else "base")
        )
        receipt = {
            "path": path,
            "reason": "binary file of %d bytes" % len(data),
            "shown_as_text": False,
        }
        return (0, 0), receipt
    text_chunk = sanitize_packet_text(
        per_file_text_diff(repo, diff_base, head, entry, "-W")
    )
    zero_chunk = sanitize_packet_text(
        per_file_text_diff(repo, diff_base, head, entry, "-U0")
    )
    chunks[path] = text_chunk
    precise[path] = zero_chunk
    # Git's own count, read with the text flag, is the
    # primary measure, and the recount cross checks it
    # against the diff body like any other text file.
    measured = per_file_text_numstat(repo, diff_base, head, entry)
    if measured is not None:
        counts = measured
    else:
        counts = count_chunk_lines(zero_chunk)
    base_path = entry["old_path"] or path
    base_data = None
    if entry["status"] not in ("added", "deleted"):
        base_data = file_bytes(repo, diff_base, base_path)
    if base_data is not None and not looks_textual(base_data):
        entry["binary_transition"] = True
        receipt = {
            "path": path,
            "reason": "changed from binary content to text "
                      "in this change, counted and shown "
                      "as text",
            "shown_as_text": True,
        }
    else:
        entry["attribute_text"] = True
        receipt = {
            "path": path,
            "reason": "marked binary by repository attributes, "
                      "counted and shown as text",
            "shown_as_text": True,
        }
    return counts, receipt


def generated_placeholder(repo, diff_base, head, entry, adds, dels):
    """The placeholder and receipt for a generated or lockfile entry.

    A marker that is new in this change exempts nothing. The change
    is shown in full and the receipt flags the arrival where a
    reviewer reads the exclusions. A marker that already stood at
    the base withholds the diff behind a named placeholder whose
    counts stay in the manifest.
    """
    path = entry["path"]
    reason = generated_reason(repo, diff_base, head, entry)
    if reason is None:
        return None
    if reason == "marker arrived":
        return {
            "path": path,
            "reason": "carries a generated file marker that "
                      "arrived in this change, counted and "
                      "shown in full",
            "shown_as_text": True,
        }
    entry["placeholder"] = (
        "(%s. The diff is withheld from the packet and its "
        "%d additions and %d deletions across %d hunks are "
        "counted in the manifest)"
        % (reason, adds, dels, entry["hunks"])
    )
    return {
        "path": path,
        "reason": reason,
        "shown_as_text": False,
    }


def enrich_files(repo, diff_base, head, change):
    """Fill in counts and placeholder state for every file entry.

    Returns the exclusion receipt, one entry per file that is binary,
    attribute marked, generated or a lockfile.
    """
    files = change["files"]
    stats = change["stats"]
    binary_paths = change["binary_paths"]
    chunks = change["chunks"]
    precise = change["precise_chunks"]
    exclusions = []
    for entry in files:
        path = entry["path"]
        adds, dels = stats.get(path, (0, 0))
        entry["binary"] = False
        entry["attribute_text"] = False
        entry["binary_transition"] = False
        entry["placeholder"] = None
        entry["head_bytes"] = None
        # One receipt entry per file, decided last. An attribute
        # marked lockfile is a lockfile in the packet, not a file
        # shown as text, and the receipt must say what the packet
        # does, once, in one voice.
        receipt = None
        if path in binary_paths:
            counts, receipt = measure_binary_entry(
                repo, diff_base, head, entry, chunks, precise
            )
            if counts is not None:
                adds, dels = counts
        entry["additions"] = adds
        entry["deletions"] = dels
        entry["hunks"] = count_hunks(chunks.get(path, ""))
        if not entry["binary"] and entry["placeholder"] is None:
            found = generated_placeholder(
                repo, diff_base, head, entry, adds, dels
            )
            if found is not None:
                receipt = found
        if receipt is not None:
            exclusions.append(receipt)
    return exclusions


def build_header(resolved, diff_base, verified, exclusions):
    """The packet header, one field per line block.

    Consecutive raw lines with no blank line between them render
    as one wrapped paragraph, so every field stands in its own
    block and the verified marker is never the last field of a
    hash paragraph. The marker points at the closing recount
    where its proof stands.
    """
    lines = []
    lines.append("# The pericope for %s" % resolved["label"])
    lines.append("")
    lines.append(
        "A recognitio review packet. The pericope named in the "
        "title is this packet, holding the change and the context "
        "a reviewer needs to read it, and nothing else."
    )
    lines.append("")
    lines.append("Mode: %s" % resolved["mode"])
    lines.append("")
    if resolved["base"] is None:
        lines.append("Base: the empty tree, because the head is a root commit")
    else:
        lines.append("Base: %s" % resolved["base"])
    lines.append("")
    lines.append("Head: %s" % resolved["head"])
    lines.append("")
    if resolved["merge_base"] is None:
        lines.append("Merge base: none, because the head is a root commit")
    else:
        lines.append("Merge base: %s" % resolved["merge_base"])
    if resolved["since"]:
        lines.append("")
        lines.append("Since: %s" % resolved["since"])
    lines.append("")
    if verified:
        lines.append(
            "Verified: yes. The recount at the close of this "
            "packet carries the proof."
        )
    else:
        lines.append(
            "Verified: NO. See the verification recount at the "
            "close of this packet."
        )
    shown = [item for item in exclusions if item["shown_as_text"]]
    withheld = [item for item in exclusions if not item["shown_as_text"]]
    if withheld:
        lines.append("")
        lines.append("Files not shown in full:")
        for item in withheld:
            lines.append("- %s: %s" % (display_path(item["path"]), item["reason"]))
    if shown:
        lines.append("")
        lines.append("Files shown in full:")
        for item in shown:
            lines.append("- %s: %s" % (display_path(item["path"]), item["reason"]))
    lines.append("")
    return "\n".join(lines)


def packet_counts(manifest_files):
    """The manifest totals the contents block and the receipt print."""
    return {
        "files": len(manifest_files),
        "hunks": sum(entry["hunks"] for entry in manifest_files),
        "additions": sum(entry["additions"] for entry in manifest_files),
        "deletions": sum(entry["deletions"] for entry in manifest_files),
    }


def _counted(count, singular, plural):
    return "%d %s" % (count, singular if count == 1 else plural)


def build_contents(counts, tier_info, rereview):
    """The contents block at the packet head.

    A one line summary from the manifest totals above a grouped
    index of the packet sections in order. Every word of it is
    generated from the manifest data the run already computed,
    so the block can name nothing the run did not count.
    """
    lines = []
    lines.append("Contents")
    lines.append("")
    lines.append(
        "This packet holds %s, %s, %s and %s"
        % (
            _counted(counts["files"], "file", "files"),
            _counted(counts["hunks"], "hunk", "hunks"),
            _counted(counts["additions"], "added line", "added lines"),
            _counted(counts["deletions"], "deleted line", "deleted lines"),
        )
    )
    lines.append("")
    standing = [
        tier for tier in ("T0", "T1", "T2", "T3")
        if tier_info[tier]["state"] == "included"
    ]
    placeholders = [
        tier for tier in ("T0", "T1", "T2", "T3")
        if tier_info[tier]["state"] != "included"
    ]
    if not placeholders:
        lines.append("All four tiers stand in full")
    else:
        parts = []
        if standing:
            verb = "stands" if len(standing) == 1 else "stand"
            parts.append(
                "%s %s in full" % (" and ".join(standing), verb)
            )
        if placeholders:
            verb = "stands" if len(placeholders) == 1 else "stand"
            noun = "a placeholder" if len(placeholders) == 1 else "placeholders"
            parts.append(
                "%s %s as %s"
                % (" and ".join(placeholders), verb, noun)
            )
        joined = " and ".join(parts)
        lines.append(joined[:1].upper() + joined[1:])
    lines.append("")
    lines.append("The tiers, in order")
    lines.append("")
    lines.append("- T0 Triage")
    lines.append("- T1 The change")
    lines.append("- T2 Companions")
    lines.append("- T3 History")
    lines.append("")
    lines.append("The close")
    lines.append("")
    if rereview is not None:
        lines.append("- Re-review")
    lines.append("- Verification recount")
    lines.append("")
    return "\n".join(lines)


def fence_for(text):
    """A fence longer than any run of backticks inside the text.

    Untrusted text, a pull request body above all, is written by the
    author of the change under review. Inside a plain fence it can
    close the fence early and print forged packet sections in its
    own voice. A fence one backtick longer than the longest run
    inside the text cannot be closed from inside, so the text stays
    text and the packet's own headings stay the only headings.
    """
    longest = 0
    for match in re.finditer(r"`+", text):
        longest = max(longest, len(match.group(0)))
    return "`" * max(3, longest + 1)


def outside_fence(lines):
    """Flag each line that stands outside every code fence.

    A fence opens on a run of three or more backticks with no
    backtick in the rest of the line and closes on a run at least
    as long standing alone. The rule the packet's own fences are
    written under, read back.
    """
    flags = []
    open_len = None
    for line in lines:
        stripped = line.strip()
        ticks = len(stripped) - len(stripped.lstrip("`"))
        rest = stripped[ticks:]
        if open_len is None:
            flags.append(True)
            if ticks >= 3 and "`" not in rest:
                open_len = ticks
        else:
            flags.append(False)
            if ticks >= open_len and rest == "":
                open_len = None
    return flags


def packet_headings(packet):
    """The level two headings a packet carries, fences excluded.

    Text the reviewed party wrote stands inside fences, the pull
    request body above all, and a heading inside a fence is quoted
    text, not a section of the packet. Recording it as one would
    let quoted text stand in the manifest as packet structure,
    and checking against it would let quoted text satisfy a
    section the packet itself does not hold.
    """
    lines = packet.splitlines()
    return [
        line for line, outside in zip(lines, outside_fence(lines))
        if outside and line.startswith("## ")
    ]


def is_instruction_path(path):
    """Whether one path names an instruction bearing file."""
    if not path:
        return False
    parts = Path(path).parts
    name = parts[-1] if parts else ""
    if name in INSTRUCTION_BASENAMES:
        return True
    if name.endswith(".mdc") and ".cursor" in parts:
        return True
    if len(parts) >= 3 and parts[-3] == ".github" \
            and parts[-2] == "instructions" \
            and name.endswith(".instructions.md"):
        return True
    if name.endswith(".md") and any(
        parts[index] == ".claude" and parts[index + 1] == "rules"
        for index in range(len(parts) - 2)
    ):
        return True
    # A review packet output style under the plugin root's
    # output-styles folder steers the next agent that loads the
    # tree exactly the way the flagged names do, so a change to
    # it is flagged like a change to any instruction file. The
    # legacy spelling under .claude-plugin/ stays flagged too,
    # because a rename is judged from either name.
    if len(parts) >= 2 and parts[0] == "output-styles" \
            and name.endswith(".md"):
        return True
    if (
        len(parts) >= 3
        and parts[0] == ".claude-plugin"
        and parts[1] == "output-styles"
        and name.endswith(".md")
    ):
        return True
    # A plugin agent file under the plugin root's agents folder
    # steers the session agent's system prompt exactly the way
    # the flagged names steer the next agent that loads the
    # tree, so a change to it is flagged like a change to any
    # instruction file. The rule mirrors the output-styles rule
    # above, root level and Markdown only, because no primary
    # source covers a deeper agents folder as a plugin surface.
    if len(parts) >= 2 and parts[0] == "agents" \
            and name.endswith(".md"):
        return True
    # R29-RT-10, R29-SP-02, and R29-EX-02. The precedence
    # manifest location is the plugin root kimi.plugin.json,
    # which sits outside any .kimi-plugin directory, so it
    # flags by basename wherever it sits, the way SKILL.md
    # does. A change to it steers the next agent that loads
    # the tree, and the nested manifest alone cannot carry
    # the precedence claim.
    if name == "kimi.plugin.json":
        return True
    # A Kimi plugin surface under a .kimi-plugin directory
    # steers the session agent and executes in the session
    # exactly the way the flagged names do, so a change to
    # it is flagged like a change to any instruction file.
    # Agent files steer the session, hook scripts execute in
    # it, and a plugin manifest can carry a systemPrompt.
    if ".kimi-plugin" in parts:
        if name in ("plugin.json", "kimi.plugin.json"):
            return True
        if "agents" in parts and name.endswith(".md"):
            return True
        if "hooks" in parts:
            return True
    return False


def entry_is_instruction(entry):
    """Whether a changed file is an instruction bearing file.

    A rename is judged from either name, so renaming a file into
    an instruction name or out of one flags the entry either way.
    """
    return is_instruction_path(entry.get("path")) or \
        is_instruction_path(entry.get("old_path"))


def build_t0(files, commit_log, pr_info):
    lines = []
    lines.append("## T0 Triage")
    lines.append("")
    if pr_info is not None:
        lines.append("Pull request #%d: %s" % (pr_info["number"], pr_info["title"]))
        lines.append("")
        lines.append("### Pull request body")
        lines.append("")
        body = pr_info["body"].strip()
        if body:
            shown, capped = cap_text(body, MAX_PR_BODY_CHARS, "pull request body")
            fence = fence_for(shown)
            lines.append(fence)
            lines.append(shown)
            lines.append(fence)
            if capped:
                lines.append("")
                lines.append(
                    "The body was capped at %d characters." % MAX_PR_BODY_CHARS
                )
        else:
            lines.append("The pull request has no body.")
        lines.append("")
        if pr_info["spec_references"]:
            lines.append(
                "Spec references found in the body: %s"
                % ", ".join(pr_info["spec_references"])
            )
        else:
            lines.append("No spec reference was found in the pull request body.")
        lines.append("")
    lines.append("Files changed: %d" % len(files))
    lines.append("")
    lines.append("### Files")
    lines.append("")
    for entry in files:
        marker = ", instruction file" if entry_is_instruction(entry) else ""
        if entry.get("old_path"):
            lines.append(
                "- %s (%s%s, renamed from %s)"
                % (display_path(entry["path"]), entry["status"], marker,
                   display_path(entry["old_path"]))
            )
        else:
            lines.append(
                "- %s (%s%s)"
                % (display_path(entry["path"]), entry["status"], marker)
            )
    lines.append("")
    lines.append("### Numstat")
    lines.append("")
    numstat_lines = []
    for entry in files:
        if entry["binary"]:
            numstat_lines.append("-\t-\t%s" % display_path(entry["path"]))
        else:
            numstat_lines.append(
                "%d\t%d\t%s"
                % (entry["additions"], entry["deletions"],
                   display_path(entry["path"]))
            )
    numstat_text = "\n".join(numstat_lines) if numstat_lines else "(no changes)"
    fence = fence_for(numstat_text)
    lines.append(fence)
    lines.append(numstat_text)
    lines.append(fence)
    lines.append("")
    lines.append("### Commits")
    lines.append("")
    commit_text = commit_log.rstrip() if commit_log.strip() else "(no commits)"
    fence = fence_for(commit_text)
    lines.append(fence)
    lines.append(commit_text)
    lines.append(fence)
    lines.append("")
    return "\n".join(lines)


def build_t1(files, chunks):
    lines = []
    lines.append("## T1 The change")
    lines.append("")
    lines.append(
        "Each file shows its diff with whole enclosing function context."
    )
    lines.append("")
    for entry in files:
        path = entry["path"]
        lines.append("### %s" % display_path(path))
        lines.append("")
        lines.append("Status: %s" % entry["status"])
        if entry.get("old_path"):
            lines.append("Renamed from: %s" % display_path(entry["old_path"]))
        lines.append("")
        lines.append("```diff")
        if entry["placeholder"] is not None:
            lines.append(entry["placeholder"])
        else:
            chunk = chunks.get(path, "")
            lines.append(chunk.rstrip() if chunk.strip() else "(no textual diff)")
        lines.append("```")
        lines.append("")
    return "\n".join(lines)



def parse_grep_z(stdout, rev):
    """Parse NUL delimited grep output into (path, line, content) hits.

    Each record is the revision and path, a NUL, the line number, a
    NUL, and the line content ending in a newline. The path field
    itself may carry a newline, so records are read by scanning for
    the NUL fields in order, never by splitting the output into
    lines. Splitting on lines first truncates a crafted path at its
    newline and hands every hit in that file to the fragment that
    follows the newline, which is a different file or no file at all.
    """
    out = []
    prefix = rev + ":"
    pos = 0
    total = len(stdout)
    while pos < total:
        if not stdout.startswith(prefix, pos):
            nxt = stdout.find("\n", pos)
            if nxt == -1:
                break
            pos = nxt + 1
            continue
        pos += len(prefix)
        end = stdout.find("\0", pos)
        if end == -1:
            break
        path = stdout[pos:end]
        pos = end + 1
        end = stdout.find("\0", pos)
        if end == -1:
            break
        lineno = stdout[pos:end]
        pos = end + 1
        end = stdout.find("\n", pos)
        if end == -1:
            content = stdout[pos:]
            pos = total
        else:
            content = stdout[pos:end]
            pos = end + 1
        if lineno.isdigit():
            out.append((path, int(lineno), content))
    return out


def git_grep_lines(repo, head, term, fixed=True):
    """Return (path, line number, content) hits for a term at a head.

    Output is NUL delimited, so paths containing colons or spaces parse
    exactly. Terms are fixed strings by default, never patterns. The
    text flag makes the search read files the tree marks binary as
    text, so an attributes line cannot hide a caller from this tier
    and leave the section reporting that no call sites exist.
    """
    args = ["grep", "--text", "-n", "-z", "-w", "-e", term, head]
    if fixed:
        args = ["grep", "--text", "-n", "-z", "-w", "-F", "-e", term, head]
    result = run_git(repo, args, check=False)
    if result.returncode not in (0, 1):
        # A search that failed is not a search that found nothing.
        # Returning no hits would let the tier report an absence
        # the run never established, inside a verified packet.
        raise GitError(
            "git grep failed with exit %d: %s"
            % (result.returncode, result.stderr.strip())
        )
    return parse_grep_z(result.stdout, head)


_WORD_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
)


def term_matches_line(term, content):
    """Whether a fixed term word matches inside one line of content.

    This mirrors the word match the grep flags ask git for, so a
    bulk search can hand each candidate line to the terms it truly
    matches. The grep word rule checks both ends of every match,
    whatever characters the term itself begins or ends with. The
    character before the match and the character after it must
    each be a non word character or the edge of the line, so a
    term that begins with a dot or ends with a hyphen is held to
    the same boundaries as a plain name.
    """
    if not term:
        return False
    start = 0
    while True:
        index = content.find(term, start)
        if index == -1:
            return False
        before_ok = index == 0 or content[index - 1] not in _WORD_CHARS
        after = index + len(term)
        after_ok = after == len(content) or content[after] not in _WORD_CHARS
        if before_ok and after_ok:
            return True
        start = index + 1


def git_grep_bulk(repo, head, terms):
    """Return hits per term from one search over the whole tree.

    The companion tier once ran one whole tree search per changed
    function and per changed file stem, so its work grew with the
    product of the change size and the tree size. One search that
    carries every term at once, with each returned line handed to
    the terms it word matches, keeps the same hits in an order
    that matches the per term searches while the search count
    stays at one however large the change grows.
    """
    unique = sorted(set(terms))
    if not unique:
        return {}
    if len(unique) == 1:
        return {unique[0]: git_grep_lines(repo, head, unique[0])}
    args = ["grep", "--text", "-n", "-z", "-w", "-F"]
    for term in unique:
        args.extend(["-e", term])
    args.append(head)
    result = run_git(repo, args, check=False)
    if result.returncode not in (0, 1):
        raise GitError(
            "git grep failed with exit %d: %s"
            % (result.returncode, result.stderr.strip())
        )
    hits = {term: [] for term in unique}
    for path, lineno, content in parse_grep_z(result.stdout, head):
        for term in unique:
            if term_matches_line(term, content):
                hits[term].append((path, lineno, content))
    return hits


def is_test_path(path):
    name = Path(path).name
    parts = Path(path).parts
    return (
        name.startswith("test_")
        or name.endswith("_test.go")
        or ".test." in name
        or ".spec." in name
        or "tests" in parts
        or "test" in parts
    )


def source_entries(files):
    return [entry for entry in files if Path(entry["path"]).suffix in SOURCE_EXTS]


def companion_terms(files, functions_by_file):
    """Every search term the companion tier needs, gathered once."""
    terms = []
    for entry in source_entries(files):
        terms.append(Path(entry["path"]).stem)
        if entry.get("old_path") and entry.get("status") == "renamed":
            # A paired rename carries its old name only in the old
            # path field of its single entry. The old stem is a
            # search term beside the new stem, in the same way the
            # findings accounting keys its ranges by the old side,
            # or a test file that still mentions the module under
            # its old name is never found and the test files section
            # can print a false absence over it. A copied entry
            # carries an old path too, and its old module still
            # exists under that name, so its mentions are not
            # evidence about the copy and no old stem is searched.
            terms.append(Path(entry["old_path"]).stem)
        terms.extend(functions_by_file.get(entry["path"], []))
    return terms


def call_sites_section(repo, head, files, functions_by_file, notes,
                       hits_by_term=None):
    lines = []
    content_cache = {}
    if hits_by_term is None:
        hits_by_term = git_grep_bulk(
            repo, head, companion_terms(files, functions_by_file)
        )

    def context_block(path, lineno):
        if path not in content_cache:
            content_cache[path] = show_file(repo, head, path)
        content = content_cache[path]
        if content is None:
            return None
        rows = content.splitlines()
        start = max(1, lineno - 1)
        end = min(len(rows), lineno + 1)
        block = []
        for number in range(start, end + 1):
            block.append("%s:%d: %s" % (display_path(path), number, rows[number - 1]))
        return "\n".join(block)

    for entry in source_entries(files):
        path = entry["path"]
        for name in functions_by_file.get(path, []):
            hits = [
                hit for hit in hits_by_term.get(name, []) if hit[0] != path
            ]
            lines.append("### Call sites for %s in %s" % (name, display_path(path)))
            lines.append("")
            if not hits:
                lines.append("No call sites found outside the changed file.")
                lines.append("")
                continue
            shown = hits[:MAX_CALL_SITES_PER_FUNCTION]
            if len(hits) > len(shown):
                notes.append(
                    "call sites for %s capped at %d of %d"
                    % (name, len(shown), len(hits))
                )
            lines.append("```")
            for hit_path, hit_line, _content in shown:
                block = context_block(hit_path, hit_line)
                if block:
                    lines.append(block)
                    lines.append("")
            lines.append("```")
            lines.append("")
    return lines


def imports_section(repo, head, files, notes):
    lines = []
    lines.append("### Imports of the changed files")
    lines.append("")
    any_imports = False
    for entry in source_entries(files):
        path = entry["path"]
        if entry["status"] == "deleted":
            continue
        pattern = IMPORT_PATTERNS.get(Path(path).suffix)
        if pattern is None:
            continue
        content = show_file(repo, head, path)
        if content is None:
            continue
        in_go_block = False
        found = []
        for number, row in enumerate(content.splitlines(), start=1):
            stripped = row.strip()
            if Path(path).suffix == ".go":
                if stripped.startswith("import ("):
                    in_go_block = True
                    continue
                if in_go_block and stripped == ")":
                    in_go_block = False
                    continue
                if in_go_block or pattern.match(row):
                    found.append((number, stripped))
            elif pattern.match(row):
                found.append((number, stripped))
        if not found:
            continue
        any_imports = True
        shown = found[:MAX_IMPORT_LINES_PER_FILE]
        if len(found) > len(shown):
            notes.append(
                "imports of %s capped at %d of %d"
                % (display_path(path), len(shown), len(found))
            )
        lines.append("#### %s" % display_path(path))
        lines.append("")
        lines.append("```")
        for number, row in shown:
            lines.append("%d: %s" % (number, row))
        lines.append("```")
        lines.append("")
    if not any_imports:
        lines.append("No import lines were found in the changed source files.")
        lines.append("")
    return lines


def line_defines(line, name):
    for pattern in FUNC_PATTERNS:
        match = pattern.match(line.strip())
        if match and match.group(1) == name:
            return True
    match = CLASS_PATTERN.match(line.strip())
    return bool(match and match.group(1) == name)


def definitions_section(repo, head, files, functions_by_file, notes,
                        hits_by_term=None):
    lines = []
    lines.append("### Definitions of changed names elsewhere")
    lines.append("")
    changed_paths = {entry["path"] for entry in files}
    if hits_by_term is None:
        hits_by_term = git_grep_bulk(
            repo, head, companion_terms(files, functions_by_file)
        )
    any_found = False
    for entry in source_entries(files):
        for name in functions_by_file.get(entry["path"], []):
            # One search per name replaces the five prefix searches
            # this section once ran. A line that defines the name
            # carries the name as a word, so the name search returns
            # every candidate the prefix searches could return, and
            # the definition check below keeps the same lines.
            hits = []
            for hit in hits_by_term.get(name, []):
                if hit[0] not in changed_paths and line_defines(hit[2], name):
                    hits.append(hit)
            hits = sorted(set(hits))
            if not hits:
                continue
            any_found = True
            shown = hits[:MAX_DEFINITIONS_PER_NAME]
            if len(hits) > len(shown):
                notes.append(
                    "definitions of %s capped at %d of %d"
                    % (name, len(shown), len(hits))
                )
            lines.append("#### %s" % name)
            lines.append("")
            lines.append("```")
            for hit_path, hit_line, content in shown:
                lines.append("%s:%d: %s" % (display_path(hit_path), hit_line, content.strip()))
            lines.append("```")
            lines.append("")
    if not any_found:
        lines.append(
            "No definitions of the changed names were found outside the "
            "changed files."
        )
        lines.append("")
    return lines


def test_files_section(repo, head, files, functions_by_file, notes,
                       hits_by_term=None):
    lines = []
    test_hits = {}
    changed_paths = [entry["path"] for entry in files]
    if hits_by_term is None:
        hits_by_term = git_grep_bulk(
            repo, head, companion_terms(files, functions_by_file)
        )
    for entry in source_entries(files):
        stem = Path(entry["path"]).stem
        terms = [stem]
        if entry.get("old_path") and entry.get("status") == "renamed":
            terms.append(Path(entry["old_path"]).stem)
        terms.extend(functions_by_file.get(entry["path"], []))
        for term in terms:
            for hit_path, hit_line, content in hits_by_term.get(term, []):
                if is_test_path(hit_path) and hit_path not in changed_paths:
                    # One line is one piece of evidence however many
                    # of the terms match it. Hits are deduped by path
                    # and line here, before the cap below applies, so
                    # the cap and its note count distinct lines and a
                    # line that matches several terms cannot crowd
                    # distinct lines out of the section. The section
                    # sorts each file's hits before display, so a set
                    # per file loses no ordering and membership stays
                    # constant time however many lines match.
                    test_hits.setdefault(hit_path, set()).add(
                        (hit_line, content)
                    )
    lines.append("### Test files that mention the changed code")
    lines.append("")
    if not test_hits:
        lines.append("No test files mention the changed modules or functions.")
        lines.append("")
        return lines
    test_paths = sorted(test_hits)
    if len(test_paths) > MAX_TEST_FILES:
        notes.append(
            "test files capped at %d of %d" % (MAX_TEST_FILES, len(test_paths))
        )
        test_paths = test_paths[:MAX_TEST_FILES]
    for test_path in test_paths:
        hits = sorted(test_hits[test_path])
        lines.append("#### %s" % display_path(test_path))
        lines.append("")
        shown = hits[:MAX_MATCH_LINES_PER_TEST_FILE]
        if len(hits) > len(shown):
            notes.append(
                "matches in %s capped at %d of %d"
                % (display_path(test_path), len(shown), len(hits))
            )
        lines.append("```")
        for hit_line, content in shown:
            lines.append("%d: %s" % (hit_line, content))
        lines.append("```")
        lines.append("")
    return lines


def build_t2(repo, head, files, functions_by_file):
    """Return the T2 text, its cap notes, and its source file count."""
    lines = []
    lines.append("## T2 Companions")
    lines.append("")
    lines.append(
        "Call sites, imports, definitions and test files found by "
        "deterministic search at the head revision."
    )
    lines.append("")
    notes = []
    sources = source_entries(files)
    if not sources:
        lines.append("No changed source files, so no companions were gathered.")
        lines.append("")
        return "\n".join(lines), notes, 0
    hits_by_term = git_grep_bulk(
        repo, head, companion_terms(files, functions_by_file)
    )
    lines.extend(call_sites_section(
        repo, head, files, functions_by_file, notes, hits_by_term
    ))
    lines.extend(imports_section(repo, head, files, notes))
    lines.extend(
        definitions_section(
            repo, head, files, functions_by_file, notes, hits_by_term
        )
    )
    lines.extend(test_files_section(
        repo, head, files, functions_by_file, notes, hits_by_term
    ))
    lines.extend(render_notes(notes))
    return "\n".join(lines), notes, len(sources)


def find_function_span(content_lines, name, path):
    start = None
    for index, line in enumerate(content_lines):
        for pattern in FUNC_PATTERNS:
            match = pattern.search(line)
            if match and match.group(1) == name:
                start = index
                break
        if start is not None:
            break
    if start is None:
        return None
    suffix = Path(path).suffix
    if suffix == ".py":
        indent = len(content_lines[start]) - len(content_lines[start].lstrip())
        end = len(content_lines)
        for index in range(start + 1, len(content_lines)):
            line = content_lines[index]
            if line.strip() and (len(line) - len(line.lstrip())) <= indent and \
                    (line.lstrip().startswith("def ") or line.lstrip().startswith("class ")):
                end = index
                break
        return (start + 1, end)
    depth = 0
    seen_brace = False
    for index in range(start, len(content_lines)):
        depth += content_lines[index].count("{") - content_lines[index].count("}")
        if "{" in content_lines[index]:
            seen_brace = True
        if seen_brace and depth <= 0:
            return (start + 1, index + 1)
    return (start + 1, min(len(content_lines), start + 40))


def top_history_files(files, stats):
    ranked = sorted(
        files,
        key=lambda e: stats.get(e["path"], (0, 0))[0]
        + stats.get(e["path"], (0, 0))[1],
        reverse=True,
    )
    return [e for e in ranked if e["status"] != "deleted"][:MAX_HISTORY_FILES]


def blame_section(repo, head, top_files, ranges_by_file, notes):
    lines = []
    lines.append("### Blame summary for changed ranges")
    lines.append("")
    range_count = 0
    for entry in top_files:
        path = entry["path"]
        ranges = ranges_by_file.get(path, [])
        if not ranges:
            continue
        tally = {}
        for start, end in ranges:
            if range_count >= MAX_BLAME_RANGES:
                notes.append("blame ranges capped at %d" % MAX_BLAME_RANGES)
                break
            range_count += 1
            result = run_git(
                repo,
                ["blame", "--porcelain", "-L", "%d,%d" % (start, end),
                 head, "--", path],
                check=False,
            )
            if result.returncode != 0:
                continue
            pending_sha = None
            pending_count = 0
            for row in result.stdout.splitlines():
                header = re.match(r"^([0-9a-f]{40}) \d+ \d+ (\d+)$", row)
                if header:
                    pending_sha = header.group(1)[:8]
                    pending_count = int(header.group(2))
                elif row.startswith("author ") and pending_sha is not None:
                    key = (row[len("author "):], pending_sha)
                    tally[key] = tally.get(key, 0) + pending_count
                    pending_sha = None
        lines.append("#### %s" % display_path(path))
        lines.append("")
        if not tally:
            lines.append("No blame data for the changed ranges.")
            lines.append("")
            continue
        summary = sorted(tally.items(), key=lambda item: -item[1])
        if len(summary) > MAX_BLAME_SUMMARY_LINES:
            notes.append(
                "blame summary for %s capped at %d entries"
                % (display_path(path), MAX_BLAME_SUMMARY_LINES)
            )
            summary = summary[:MAX_BLAME_SUMMARY_LINES]
        lines.append("```")
        for (author, sha), count in summary:
            lines.append("%s %s lines %d" % (author, sha, count))
        lines.append("```")
        lines.append("")
    return lines


def evolution_section(repo, head, top_files, functions_by_file, notes):
    lines = []
    lines.append("### Recent evolution of changed functions")
    lines.append("")
    log_count = 0
    for entry in top_files:
        if log_count >= MAX_LOG_L_FUNCTIONS:
            break
        path = entry["path"]
        content = show_file(repo, head, path)
        if content is None:
            continue
        content_lines = content.splitlines()
        for name in functions_by_file.get(path, []):
            if log_count >= MAX_LOG_L_FUNCTIONS:
                break
            span = find_function_span(content_lines, name, path)
            if span is None:
                continue
            log_count += 1
            result = run_git(
                repo,
                ["log", "-L", "%d,%d:%s" % (span[0], span[1], path),
                 "--format=commit %h %s", head],
                check=False,
            )
            lines.append("#### %s in %s" % (name, display_path(path)))
            lines.append("")
            if result.returncode != 0:
                lines.append("No history available for this function.")
                lines.append("")
                continue
            text, capped = cap_text(
                result.stdout.rstrip(), MAX_LOG_L_CHARS,
                "history for %s" % name, mark=False,
            )
            if capped:
                notes.append("history for %s capped" % name)
            lines.append("```")
            lines.append(text)
            lines.append("```")
            lines.append("")
    if log_count == 0:
        lines.append("No changed functions had traceable history.")
        lines.append("")
    return lines


def prior_prs(repo, paths):
    """List recent PRs touching the given paths, or None when unknown.

    Uses the GitHub CLI as metadata only. Any failure returns None and
    the caller degrades honestly instead of inventing history.
    """
    if shutil.which("gh") is None:
        return None
    try:
        view = run_cmd(
            repo,
            [
                "gh", "pr", "list", "--state", "all",
                "--limit", str(MAX_PRIOR_PR_LIST),
                "--json", "number,title,state,files",
            ],
        )
        data = json.loads(view.stdout)
        if not isinstance(data, list):
            return None
        wanted = set(paths)
        found = []
        for pr in data:
            if not isinstance(pr, dict):
                continue
            pr_files = {
                item.get("path")
                for item in pr.get("files") or []
                if isinstance(item, dict)
            }
            if pr_files & wanted:
                found.append({
                    "number": pr.get("number"),
                    "title": pr.get("title") or "",
                    "state": pr.get("state") or "",
                })
    except (GitError, json.JSONDecodeError, AttributeError, TypeError):
        # Metadata from the GitHub CLI is a convenience, never a
        # load bearing input. Any shape it arrives in that the code
        # cannot read degrades to the honest unavailable answer.
        return None
    return found


def prior_prs_section(repo, top_files):
    lines = []
    lines.append("### Prior pull requests touching these files")
    lines.append("")
    lines.append(
        "Scope of the lookup: the %d most changed files, checked "
        "against the %d most recent pull requests, with at most %d "
        "matches shown. A pull request outside that window is not "
        "reported here."
        % (MAX_HISTORY_FILES, MAX_PRIOR_PR_LIST, MAX_PRIOR_PRS)
    )
    lines.append("")
    paths = [entry["path"] for entry in top_files]
    found = prior_prs(repo, paths) if paths else []
    if found is None:
        lines.append(
            "Prior pull requests are unavailable in this environment. The "
            "GitHub CLI is missing or this clone is not a GitHub checkout, "
            "so no pull request history was gathered."
        )
        lines.append("")
        return lines
    if not found:
        lines.append(
            "No earlier pull requests in the recent list touch these files."
        )
        lines.append("")
        return lines
    shown = found[:MAX_PRIOR_PRS]
    for pr in shown:
        lines.append(
            "- #%s %s (%s)" % (pr["number"], pr["title"], pr["state"].lower())
        )
    if len(found) > len(shown):
        lines.append(
            "Showing %d of %d matching pull requests."
            % (len(shown), len(found))
        )
    lines.append("")
    return lines


def build_t3(repo, head, files, stats, ranges_by_file, functions_by_file):
    """Return the T3 text, its cap notes, and its history file count."""
    lines = []
    lines.append("## T3 History")
    lines.append("")
    notes = []
    top_files = top_history_files(files, stats)
    if not top_files:
        lines.append("No files with history to summarise.")
        lines.append("")
        return "\n".join(lines), notes, 0
    lines.extend(blame_section(repo, head, top_files, ranges_by_file, notes))
    lines.extend(
        evolution_section(repo, head, top_files, functions_by_file, notes)
    )
    lines.extend(prior_prs_section(repo, top_files))
    lines.extend(render_notes(notes))
    return "\n".join(lines), notes, len(top_files)


def normalize_finding_path(path):
    """The one spelling a findings path is accounted under.

    Many spellings name the same file as the plain spelling, so
    identity and verdicts share the plain spelling and one worry
    written in any of them counts once with one verdict. A leading
    or mid path dot segment names nothing, a doubled separator
    separates nothing extra, a backslash separates on the systems
    that write paths that way, and stray space around the path is
    not part of a file name. Case is left untouched, because two
    spellings that differ only in case can name two different
    files in one tree. The path is also folded to composed
    Unicode form, so a name written with combining marks counts
    as the file the tree holds in composed form. That fold can
    merge two files whose names differ only in normalisation
    form. Such a pair can coexist on a byte exact filesystem and
    a reviewer can barely tell the two apart, so the fold is the
    right trade and it is recorded here as a choice.
    """
    path = unicodedata.normalize("NFC", path)
    path = path.strip()
    path = path.replace("\\", "/")
    parts = [
        part for part in path.split("/")
        if part not in ("", ".")
    ]
    return "/".join(parts)


def parse_findings(text):
    """Parse a findings file of one finding per line, anchored path:line."""
    findings = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = FINDING_RE.match(line)
        if not match:
            raise GitError(
                "findings line does not carry a path:line anchor: %r" % raw
            )
        findings.append({
            "path": normalize_finding_path(match.group(1)),
            "line": int(match.group(2)),
            "text": match.group(3),
        })
    return findings


def dedupe_findings(findings):
    """Drop repeated copies of one finding, keeping the first.

    A findings file is reviewer supplied input, and the same line
    can stand in it many times by accident or by padding. Counting
    each copy as its own finding inflates the summary, and a run of
    copies ahead of a distinct finding can push that finding past
    the accounting cap and out of the packet. Identity is the whole
    anchored entry, its path and line and text together.
    """
    seen = set()
    unique = []
    duplicates = 0
    for finding in findings:
        path = normalize_finding_path(finding["path"])
        if path != finding["path"]:
            # Keep the first object untouched when its spelling is
            # already plain, and account a dotted spelling under
            # the plain one so its verdict lookup shares it too.
            finding = dict(finding, path=path)
        key = (path, finding["line"], finding["text"])
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        unique.append(finding)
    return unique, duplicates


def _content_lines(data):
    """The lines of one file revision with line endings normalised.

    The bytes are decoded the way the packet decodes file text,
    split on line feeds, and a carriage return closing a line is
    dropped, so a line that only changed its ending compares
    equal to itself.
    """
    text = data.decode("utf-8", "surrogateescape")
    return [
        line[:-1] if line.endswith("\r") else line
        for line in text.split("\n")
    ]


def _unchanged_old_lines(old_lines, new_lines):
    """Old line numbers whose content survives in the new revision.

    The two revisions are matched line by line in order, so an
    old line counts as unchanged only when the same words stand
    at the matched position in the new revision.
    """
    matcher = difflib.SequenceMatcher(
        None, old_lines, new_lines, autojunk=False
    )
    unchanged = set()
    for tag, i1, i2, _j1, _j2 in matcher.get_opcodes():
        if tag == "equal":
            unchanged.update(range(i1 + 1, i2 + 1))
    return unchanged


def _content_changed_ranges(repo, since, head, entry, git_ranges):
    """Filter diff ranges to the lines whose content really changed.

    Hunk membership alone would mark a line changed when the
    interval only re-terminated it, as a rename that flips every
    line ending of a file does. The old side and the new side of
    the file are compared with line endings normalised away,
    and a range keeps only the old lines that no matching line
    survives for. When either side of the file cannot be read,
    the diff ranges stand as they are.
    """
    if entry["status"] == "deleted":
        return git_ranges
    old_data = file_bytes(
        repo, since, entry["old_path"] or entry["path"]
    )
    new_data = file_bytes(repo, head, entry["path"])
    if old_data is None or new_data is None:
        return git_ranges
    unchanged = _unchanged_old_lines(
        _content_lines(old_data), _content_lines(new_data)
    )
    in_hunks = set()
    for start, count in git_ranges:
        in_hunks.update(range(start, start + count))
    ranges = []
    for number in sorted(in_hunks - unchanged):
        if ranges and ranges[-1][0] + ranges[-1][1] == number:
            ranges[-1] = (ranges[-1][0], ranges[-1][1] + 1)
        else:
            ranges.append((number, 1))
    return ranges


def rereview_ranges(repo, since, head):
    """The diff ranges and tree listings one accounting runs over.

    Existence at either revision is read once, from a single
    listing of each tree, however many findings there are.
    Findings anchor at the since revision, so their paths are the
    paths the files carried there. The ranges are keyed by that
    side and the rename map remembers where each file moved, or
    every finding on a renamed file reads addressed because its
    old path is gone.
    """
    precise = run_git(
        repo,
        ["diff", "--histogram", "--find-renames", "--find-copies", "-U0"]
        + DIFF_FLAGS + [since, head],
    ).stdout
    status_text = run_git(
        repo, ["diff", "--name-status", "-z", "-M", "-C"] + DIFF_FLAGS
        + [since, head]
    ).stdout
    tree_text = run_git(
        repo, ["ls-tree", "-r", "-z", "--name-only", head]
    ).stdout
    head_paths = {
        normalize_finding_path(field)
        for field in tree_text.split("\0") if field
    }
    since_text = run_git(
        repo, ["ls-tree", "-r", "-z", "--name-only", since]
    ).stdout
    since_paths = {
        normalize_finding_path(field)
        for field in since_text.split("\0") if field
    }
    since_files = parse_name_status_z(status_text)
    chunks = split_diff(precise)
    ranges_by_path = {}
    moved_to = {}
    for position, entry in enumerate(since_files):
        if entry["status"] == "copied":
            # A copied entry carries its source as its old path and
            # its chunk describes the delta between the source at
            # the previous revision and the copy at the head. Those
            # ranges are not edits to the source file, so a copy
            # writes no ranges under its source path and it never
            # overwrites the ranges the source file its own
            # modification wrote there.
            continue
        chunk = chunks[position] if position < len(chunks) else ""
        since_path = normalize_finding_path(
            entry["old_path"] or entry["path"]
        )
        ranges_by_path[since_path] = _content_changed_ranges(
            repo, since, head, entry, old_side_ranges(chunk)
        )
        if entry["status"] == "renamed":
            moved_to[since_path] = normalize_finding_path(entry["path"])
    return ranges_by_path, moved_to, head_paths, since_paths


def finding_verdict(finding, ranges_by_path, moved_to, head_paths,
                    since_paths):
    """The verdict for one finding and whether it counts addressed."""
    path = finding["path"]
    anchor = finding["line"]
    target = moved_to.get(path, path)
    if path not in since_paths and target not in head_paths \
            and path not in head_paths:
        # The path never existed at the previous reviewed
        # revision and it does not exist at the head either. A
        # mistyped or crafted path, a traversal path above
        # all, is not a file that went away. Counting it as
        # addressed would inflate the summary with work that
        # was never done, so it reads unaddressed in plain
        # words.
        return (
            "unaddressed, the file never existed at the previous "
            "reviewed revision or at the head"
        ), False
    if path not in since_paths:
        return (
            "unaddressed, the file did not exist at the previous "
            "reviewed revision, so no anchored line was reviewed then"
        ), False
    if target not in head_paths:
        return "addressed, the file is gone at the head", True
    for start, count in ranges_by_path.get(path, []):
        if count == 0:
            # A pure insertion touches no old side line. Its
            # start names the line before the inserted text.
            continue
        if start <= anchor <= start + count - 1:
            return "addressed, the anchored lines changed", True
    return "unaddressed, the anchored lines are unchanged", False


def findings_accounting(repo, diff_base, since, head, findings):
    """Mark each prior finding addressed or unaddressed.

    A finding counts as addressed when the file is gone at the head or
    when the content of the lines it anchors to changed between the
    previous reviewed head and this head. A change of line endings
    alone does not change the content of a line, so a finding on a
    line that was only re-terminated reads unaddressed. When the
    anchored lines survive that interval untouched, the finding is
    unaddressed.

    Repeated copies of one finding are removed before the cap is
    applied, so the summary counts unique findings and duplicates
    can never crowd a distinct finding out of the accounting. The
    accounting itself is capped like every other surface in the
    tool, and the section states both the dedupe and the cap.
    """
    findings, duplicates = dedupe_findings(findings)
    total_findings = len(findings)
    findings = findings[:MAX_FINDINGS_ACCOUNTED]
    ranges_by_path, moved_to, head_paths, since_paths = rereview_ranges(
        repo, since, head
    )
    lines = []
    lines.append("### Prior findings accounting")
    lines.append("")
    if duplicates:
        lines.append(
            "%d duplicate finding entries were removed before "
            "accounting, so every finding below is one unique "
            "anchored finding." % duplicates
        )
        lines.append("")
    addressed = 0
    for finding in findings:
        verdict, counted = finding_verdict(
            finding, ranges_by_path, moved_to, head_paths, since_paths
        )
        if counted:
            addressed += 1
        lines.append(
            "- %s:%d %s. %s"
            % (
                display_path(finding["path"]), finding["line"],
                finding["text"], verdict,
            )
        )
    lines.append("")
    lines.append(
        "Findings addressed: %d of %d. Findings unaddressed: %d."
        % (addressed, len(findings), len(findings) - addressed)
    )
    if total_findings > len(findings):
        lines.append(
            "Findings capped at %d of %d. The remaining findings were "
            "not accounted."
            % (MAX_FINDINGS_ACCOUNTED, total_findings)
        )
    lines.append("")
    return lines


def build_rereview(repo, diff_base, head, since, findings,
                   findings_given=False):
    lines = []
    lines.append("## Re-review")
    lines.append("")
    lines.append("Previous reviewed revision: %s" % since)
    lines.append("")
    shared = run_git(repo, ["merge-base", since, head], check=False)
    if shared.returncode != 0 or not shared.stdout.strip():
        # The since ref shares no history with this change, so a
        # re-review against it would be fiction. Say so and stop. A
        # shared merge base is the test, not ancestry, because a
        # rebase or a force push leaves the previous reviewed head a
        # non ancestor while the two still share their history.
        lines.append(
            "The since ref %s is not an ancestor of the head and shares no "
            "usable history with this change, so no re-review accounting "
            "is possible against it. The tiers above cover the whole "
            "change, and nothing here claims otherwise." % since
        )
        lines.append("")
        return "\n".join(lines)
    commits = run_git(
        repo, ["log", "--oneline", "--reverse", "%s..%s" % (since, head)]
    ).stdout
    lines.append("### Commits since the previous review")
    lines.append("")
    lines.append("```")
    lines.append(commits.rstrip() if commits.strip() else "(none)")
    lines.append("```")
    lines.append("")
    lines.append("### Range diff against the previous review")
    lines.append("")
    # The range diff carries the same pins as every other diff. Its
    # inner diffs do not take the flags in every git version, so the
    # attributes are also read from the empty tree for this one
    # invocation. No attribute in the reviewed tree can then assign
    # a text conversion or an external driver to the inner diffs,
    # and the reviewed tree cannot rewrite its own re-review. The
    # creation factor is set to its maximum because pairing is the
    # point of the section. At the default factor a small commit,
    # a one line change above all, pairs with nothing and its inner
    # diff vanishes from the re-review entirely.
    result = run_git(
        repo,
        ["range-diff", "--creation-factor=100"] + DIFF_FLAGS
        + ["%s..%s" % (diff_base, since),
           "%s..%s" % (diff_base, head)],
        check=False,
        global_flags=["--attr-source=" + EMPTY_TREE],
    )
    lines.append("```")
    if result.returncode == 0 and result.stdout.strip():
        text, _capped = cap_text(
            result.stdout.rstrip(), MAX_RANGE_DIFF_CHARS, "range diff"
        )
        lines.append(text)
    else:
        delta = run_git(
            repo,
            ["diff", "--stat"] + DIFF_FLAGS + ["%s...%s" % (since, head)],
        ).stdout
        lines.append(
            "Range diff was not available. Diff stat since the previous review:"
        )
        lines.append(delta.rstrip() if delta.strip() else "(no changes)")
    lines.append("```")
    lines.append("")
    if findings:
        lines.extend(
            findings_accounting(repo, diff_base, since, head, findings)
        )
    elif findings_given:
        # A findings file was supplied and held nothing. Say so, so
        # a reader can tell that case apart from no file at all.
        lines.append("### Prior findings accounting")
        lines.append("")
        lines.append(
            "A findings file was given for this run and it contained "
            "no findings, so there is nothing to account for."
        )
        lines.append("")
    return "\n".join(lines)


def verify_counts(repo, diff_base, head, manifest_files):
    """Recount the change with separate git invocations.

    The recount repeats the fetch and the measurement, then also
    recounts added and deleted lines straight from the recount's own
    zero context diff. Returns a list of discrepancy strings. An empty
    list means the manifest matches the recount in files, statuses,
    old paths, hunks and lines.
    """
    discrepancies = []
    change = fetch_change(repo, diff_base, head)
    enrich_files(repo, diff_base, head, change)
    recounted = change["files"]
    manifest_by_path = {entry["path"]: entry for entry in manifest_files}
    recounted_by_path = {entry["path"]: entry for entry in recounted}
    for path in sorted(set(manifest_by_path) - set(recounted_by_path)):
        discrepancies.append("file in manifest but not in recount: %s" % path)
    for path in sorted(set(recounted_by_path) - set(manifest_by_path)):
        discrepancies.append("file in recount but not in manifest: %s" % path)
    for path in sorted(set(manifest_by_path) & set(recounted_by_path)):
        mine = manifest_by_path[path]
        theirs = recounted_by_path[path]
        if mine["status"] != theirs["status"]:
            discrepancies.append(
                "status mismatch for %s: manifest %s, recount %s"
                % (path, mine["status"], theirs["status"])
            )
        if mine.get("old_path") != theirs.get("old_path"):
            discrepancies.append(
                "old path mismatch for %s: manifest %s, recount %s"
                % (path, mine.get("old_path"), theirs.get("old_path"))
            )
        if mine["hunks"] != theirs["hunks"]:
            discrepancies.append(
                "hunk count mismatch for %s: manifest %d, recount %d"
                % (path, mine["hunks"], theirs["hunks"])
            )
        if mine["additions"] != theirs["additions"] or \
                mine["deletions"] != theirs["deletions"]:
            discrepancies.append(
                "line count mismatch for %s: manifest +%d -%d, recount "
                "+%d -%d"
                % (
                    path,
                    mine["additions"],
                    mine["deletions"],
                    theirs["additions"],
                    theirs["deletions"],
                )
            )
        if not theirs["binary"]:
            # Attribute marked files take part like any other text
            # file. Their manifest counts come from numstat read with
            # the text flag, and this recount of the diff body is the
            # independent second way that must agree with them.
            counted = count_chunk_lines(
                change["precise_chunks"].get(path, "")
            )
            if counted != (mine["additions"], mine["deletions"]):
                discrepancies.append(
                    "recounted lines for %s disagree: manifest +%d -%d, "
                    "counted from the recount diff +%d -%d"
                    % (
                        path,
                        mine["additions"],
                        mine["deletions"],
                        counted[0],
                        counted[1],
                    )
                )
    manifest_adds = sum(e["additions"] for e in manifest_files)
    manifest_dels = sum(e["deletions"] for e in manifest_files)
    recount_adds = sum(e["additions"] for e in recounted)
    recount_dels = sum(e["deletions"] for e in recounted)
    if (manifest_adds, manifest_dels) != (recount_adds, recount_dels):
        discrepancies.append(
            "total line counts disagree: manifest +%d -%d, recount +%d -%d"
            % (manifest_adds, manifest_dels, recount_adds, recount_dels)
        )
    return discrepancies



def parse_tier_selection(text):
    """Parse a tier selector such as 0-3 or 0,1 into tier names."""
    if text is None:
        return {"T0", "T1", "T2", "T3"}
    selected = set()
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            low_raw, high_raw = part.split("-", 1)
            if not (low_raw.isdigit() and high_raw.isdigit()):
                raise ValueError("tier range %r is not two numbers" % part)
            low, high = int(low_raw), int(high_raw)
            if low > high or low < 0 or high > 3:
                raise ValueError("tier range %r is outside 0-3" % part)
            for number in range(low, high + 1):
                selected.add("T%d" % number)
        elif part.isdigit() and 0 <= int(part) <= 3:
            selected.add("T%d" % int(part))
        else:
            raise ValueError("tier %r is not one of 0, 1, 2, 3" % part)
    if "T0" not in selected or "T1" not in selected:
        raise ValueError("T0 and T1 are always included in a packet")
    return selected


def tier_placeholder(tier, state):
    title = "## T2 Companions" if tier == "T2" else "## T3 History"
    if state == "dropped":
        body = (
            "Dropped under the token budget. The change in T1 is complete."
        )
    else:
        body = "Not selected for this run. The change in T1 is complete."
    return "%s\n\n%s\n" % (title, body)


def render_receipt(budget, packet_estimate, tier_info, dropped,
                   verified, discrepancies, counts):
    """The closing receipt of the packet.

    The budget account stands under its own subheading as facts,
    then the recount prints the manifest counts it covered, the
    agreement, and the limit sentence last, so the final line of
    the packet states what verified does not mean.
    """
    lines = []
    lines.append("## Verification recount")
    lines.append("")
    lines.append("### Budget")
    lines.append("")
    lines.append(
        "Budget in tokens: %s"
        % (budget if budget is not None else "none set")
    )
    lines.append("")
    lines.append("Packet estimate in tokens: %d" % packet_estimate)
    lines.append("")
    for tier in ("T0", "T1", "T2", "T3"):
        info = tier_info[tier]
        if info["state"] == "included":
            lines.append(
                "%s included at about %d tokens across %d files"
                % (tier, info["estimated_tokens"], info["files"])
            )
        elif info["state"] == "dropped":
            lines.append(
                "%s dropped under the token budget. The full tier runs "
                "about %d tokens across %d files"
                % (tier, info["estimated_tokens"], info["files"])
            )
        else:
            lines.append("%s not selected for this run" % tier)
        lines.append("")
    if dropped:
        for item in dropped:
            lines.append(
                "Dropped %s because of the %s." % (item["tier"], item["reason"])
            )
            lines.append("")
    else:
        lines.append("No tier was dropped.")
        lines.append("")
    lines.append("### Recount")
    lines.append("")
    covered = (
        "The recount covered %s with their statuses and old paths, "
        "%s, and %s and %s"
        % (
            _counted(counts["files"], "file", "files"),
            _counted(counts["hunks"], "hunk", "hunks"),
            _counted(counts["additions"], "added line", "added lines"),
            _counted(counts["deletions"], "deleted line", "deleted lines"),
        )
    )
    if verified:
        lines.append("Recount passed")
        lines.append("")
        lines.append("A separate recount counted the change a second time")
        lines.append("")
        lines.append(covered)
        lines.append("")
        lines.append("The recount matches the manifest on every count")
        lines.append("")
        if not dropped and all(
            tier_info[tier]["state"] == "included"
            for tier in ("T0", "T1", "T2", "T3")
        ):
            lines.append("Every tier is included")
            lines.append("")
        lines.append(
            "Verified means this packet holds the whole change it names"
        )
        lines.append("")
    else:
        lines.append("Recount FAILED")
        lines.append("")
        lines.append(
            "This packet must not be reviewed as if it were whole"
        )
        lines.append("")
        lines.append(covered)
        lines.append("")
        lines.append("Discrepancies follow")
        lines.append("")
        for item in discrepancies:
            lines.append(
                "Missing or mismatched: %s"
                % item.replace("\n", "\\n").replace("\r", "\\r")
            )
            lines.append("")
    lines.append(
        "Verified does not mean the change is correct or safe"
    )
    lines.append("")
    return "\n".join(lines)


def base_manifest(argv):
    return {
        "extractor": "recognitio extract.py",
        "version": EXTRACTOR_VERSION,
        "command": ["extract.py"] + list(argv),
        "created_utc": datetime.now(timezone.utc).isoformat(),
    }


def write_manifest(out_dir, manifest):
    text = json.dumps(manifest, indent=2) + "\n"
    (out_dir / "manifest.json").write_bytes(text.encode("utf-8"))


def write_failure_manifest(out_dir, argv, message, resolved=None):
    """Leave a receipt that cannot be mistaken for a verified packet."""
    manifest = base_manifest(argv)
    manifest.update({
        "mode": resolved["mode"] if resolved else None,
        "label": resolved["label"] if resolved else None,
        "base": resolved["base"] if resolved else None,
        "head": resolved["head"] if resolved else None,
        "merge_base": resolved["merge_base"] if resolved else None,
        "since": resolved["since"] if resolved else None,
        "files": [],
        "tiers": {},
        "budget": {"budget_tokens": None, "estimated_tokens": 0,
                   "dropped": []},
        "cap_notes": [],
        "exclusions": [],
        "verified": False,
        "error": message,
        "discrepancies": [message],
    })
    try:
        write_manifest(out_dir, manifest)
    except OSError:
        pass


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="extract.py",
        description="Assemble a verified recognitio review packet from a local clone.",
    )
    parser.add_argument("--pr", type=int, default=None, help="pull request number")
    parser.add_argument("--range", dest="range", default=None, help="A..B or A...B")
    parser.add_argument("--commit", default=None, help="a single commit")
    parser.add_argument(
        "--since", default=None,
        help="previous reviewed revision, a re-review input to any mode",
    )
    parser.add_argument(
        "--tiers", default=None,
        help="tier selection such as 0-3 or 0,1. T0 and T1 always included",
    )
    parser.add_argument(
        "--findings", default=None,
        help="file of prior findings, one per line anchored as path:line: text",
    )
    parser.add_argument(
        "--budget", type=int, default=None,
        help="approximate token budget, counted as characters divided by 4",
    )
    parser.add_argument("--out", required=True, help="output directory")
    parser.add_argument("--repo", default=".", help="path to the local clone")
    args = parser.parse_args(argv)
    chosen = [args.pr is not None, bool(args.range), bool(args.commit)]
    if sum(chosen) > 1:
        parser.error("choose exactly one of --pr, --range, or --commit")
    if sum(chosen) == 0:
        parser.error(
            "one of --pr, --range, or --commit is required. --since is a "
            "re-review input and cannot stand alone"
        )
    if args.findings and not args.since:
        parser.error("--findings needs --since, the previous reviewed revision")
    try:
        args.tiers_selected = parse_tier_selection(args.tiers)
    except ValueError as exc:
        parser.error(str(exc))
    return args


def load_findings(args):
    """Read and parse the findings file, or an empty list without one."""
    if not args.findings:
        return []
    try:
        findings_text = Path(args.findings).read_text(
            encoding="utf-8", errors="surrogateescape"
        )
    except OSError as exc:
        raise GitError("cannot read the findings file: %s" % exc)
    return parse_findings(findings_text)


def assemble_tiers(args, repo, resolved, diff_base, change, files,
                   findings):
    """Build the tier texts for one run.

    Returns the tier texts keyed by tier, the files each tier worked
    over, the cap notes in tier order, and the re-review text, which
    is None when the run carries no since ref.
    """
    head = resolved["head"]
    chunks = change["chunks"]
    functions_by_file = {
        entry["path"]: extract_function_names(chunks.get(entry["path"], ""))
        for entry in files
    }
    ranges_by_file = {
        entry["path"]: changed_ranges(change["precise_chunks"].get(
            entry["path"], ""))
        for entry in files
    }
    selected = args.tiers_selected
    tier_texts = {
        "T0": build_t0(files, change["commit_log"], resolved["pr"]),
        "T1": build_t1(files, chunks),
        "T2": "",
        "T3": "",
    }
    tier_files = {"T0": len(files), "T1": len(files), "T2": 0, "T3": 0}
    t2_notes, t3_notes = [], []
    if "T2" in selected:
        tier_texts["T2"], t2_notes, tier_files["T2"] = build_t2(
            repo, head, files, functions_by_file
        )
    if "T3" in selected:
        tier_texts["T3"], t3_notes, tier_files["T3"] = build_t3(
            repo, head, files, change["stats"], ranges_by_file,
            functions_by_file,
        )
    rereview = None
    if resolved["since"]:
        rereview = build_rereview(
            repo, diff_base, head, resolved["since"], findings,
            findings_given=args.findings is not None,
        )
    return tier_texts, tier_files, t2_notes + t3_notes, rereview


def apply_budget(args, selected, tier_texts, tier_files, rereview,
                 header_provisional, counts):
    """Decide which optional tiers the budget sheds.

    Returns the drop list and, when T0 and T1 alone exceed the
    budget, the failure message instead. T3 sheds before T2, and
    the change itself is never truncated.

    Each candidate drop set is measured by assembling the packet
    it would emit and settling its token estimate, the same fixed
    point the shipped packet is measured at, so a packet the
    budget accepts is a packet that measures inside the budget.
    A fixed allowance for the closing receipt undercounted
    it whenever the section grew, drop lines and all, and let
    emitted packets land over the budget they were accepted
    under. The measurement reads the verified form of the packet.
    A packet that goes on to fail verification is a failure
    artifact at exit 3, not a packet presented as ready, and its
    discrepancy list can carry it past the budget.
    """
    dropped = []
    if args.budget is None:
        return dropped, None

    def measure(candidate):
        info = tier_accounting(
            selected,
            {item["tier"] for item in candidate},
            tier_texts,
            tier_files,
        )
        _packet, estimate = build_packet_text(
            header_provisional, tier_texts, rereview, info,
            candidate, args.budget, True, [], counts,
        )
        return estimate

    optional = [tier for tier in ("T3", "T2") if tier in selected]
    reason = "budget of %d tokens" % args.budget
    core = measure([{"tier": tier, "reason": reason} for tier in optional])
    if core > args.budget:
        message = (
            "T0 and T1 alone need about %d tokens, over the budget of "
            "%d. The change itself is never truncated. Raise the budget "
            "or split the change." % (core, args.budget)
        )
        return dropped, message
    for tier in optional:
        if measure(dropped) > args.budget:
            dropped.append({"tier": tier, "reason": reason})
    return dropped, None


def tier_accounting(selected, dropped_names, tier_texts, tier_files):
    """The per tier receipt the manifest and the packet both carry."""
    tier_info = {}
    for tier in ("T0", "T1", "T2", "T3"):
        if tier in dropped_names:
            state = "dropped"
        elif tier not in selected:
            state = "not selected"
        else:
            state = "included"
        if state == "included":
            emitted = estimate_tokens(tier_texts[tier])
        elif state == "dropped":
            emitted = estimate_tokens(tier_placeholder(tier, "dropped"))
        elif tier in ("T2", "T3"):
            emitted = estimate_tokens(tier_placeholder(tier, "not selected"))
        else:
            emitted = estimate_tokens(tier_texts[tier])
        tier_info[tier] = {
            "state": state,
            "included": state == "included",
            "estimated_tokens": estimate_tokens(tier_texts[tier]),
            "emitted_tokens": emitted,
            "files": tier_files[tier],
        }
    return tier_info


def build_packet_text(header, tier_texts, rereview, tier_info, dropped,
                      budget, verified, discrepancies, counts):
    """Join the sections and settle the completeness fixed point.

    Returns the packet text and its settled token estimate.
    """
    contents = build_contents(counts, tier_info, rereview)
    sections = [header, contents, tier_texts["T0"], tier_texts["T1"]]
    for tier in ("T2", "T3"):
        if tier_info[tier]["state"] == "included":
            sections.append(tier_texts[tier])
        else:
            sections.append(
                tier_placeholder(tier, tier_info[tier]["state"])
            )
    if rereview is not None:
        sections.append(rereview)
    packet_estimate = 0
    packet = ""
    for _round in range(5):
        completeness = render_receipt(
            budget, packet_estimate, tier_info, dropped,
            verified, discrepancies, counts,
        )
        packet = sanitize_packet_text("\n".join(sections + [completeness]))
        new_estimate = estimate_tokens(packet)
        if new_estimate == packet_estimate:
            break
        packet_estimate = new_estimate
    return packet, packet_estimate


def manifest_file_records(files):
    return [
        {
            "path": entry["path"],
            "old_path": entry["old_path"],
            "status": entry["status"],
            "status_code": entry["status_code"],
            "additions": entry["additions"],
            "deletions": entry["deletions"],
            "hunks": entry["hunks"],
            "binary": entry["binary"],
            "attribute_text": entry["attribute_text"],
            "binary_transition": entry["binary_transition"],
            "placeholder": entry["placeholder"],
            "instruction_file": entry_is_instruction(entry),
        }
        for entry in files
    ]


def assemble_manifest(argv, args, resolved, head, manifest_files,
                      exclusions, selected, tier_info, packet,
                      packet_estimate, dropped, cap_notes, verified,
                      discrepancies):
    """The manifest receipt for a built packet."""
    manifest = base_manifest(argv)
    manifest.update({
        "mode": resolved["mode"],
        "label": resolved["label"],
        "base": resolved["base"],
        "head": head,
        "merge_base": resolved["merge_base"],
        "since": resolved["since"],
        "pr": (
            {
                "number": resolved["pr"]["number"],
                "title": resolved["pr"]["title"],
                "spec_references": resolved["pr"]["spec_references"],
            }
            if resolved["pr"] else None
        ),
        "files": manifest_files,
        "exclusions": exclusions,
        "selected_tiers": sorted(selected),
        "tiers": tier_info,
        # The section headings this packet carries, in order,
        # counted outside its fences. The packet check compares
        # them against the packet itself under the same rule, so
        # a thin packet cannot wear a full packet's manifest and
        # quoted text cannot stand in for a missing section.
        "sections": packet_headings(packet),
        "budget": {
            "budget_tokens": args.budget,
            "estimated_tokens": packet_estimate,
            "dropped": dropped,
        },
        "cap_notes": cap_notes,
        "verified": verified,
        "discrepancies": discrepancies,
    })
    return manifest


def run_pipeline(args, repo, out_dir, argv):
    resolved = resolve_inputs(repo, args)
    diff_base = resolved["merge_base"]
    if diff_base is None:
        diff_base = EMPTY_TREE
    head = resolved["head"]

    findings = load_findings(args)

    change = fetch_change(repo, diff_base, head)
    files = change["files"]
    if not files:
        message = "the resolved change is empty, no packet was built"
        write_failure_manifest(out_dir, argv, message, resolved)
        print("recognitio: %s" % message, file=sys.stderr)
        return 2
    exclusions = enrich_files(repo, diff_base, head, change)

    tier_texts, tier_files, cap_notes, rereview = assemble_tiers(
        args, repo, resolved, diff_base, change, files, findings
    )
    selected = args.tiers_selected
    manifest_files = manifest_file_records(files)
    counts = packet_counts(manifest_files)
    header_provisional = build_header(resolved, diff_base, True, exclusions)
    dropped, failure = apply_budget(
        args, selected, tier_texts, tier_files, rereview,
        header_provisional, counts
    )
    if failure is not None:
        write_failure_manifest(out_dir, argv, failure, resolved)
        print("recognitio: %s" % failure, file=sys.stderr)
        return 2
    dropped_names = {item["tier"] for item in dropped}

    try:
        discrepancies = verify_counts(repo, diff_base, head, manifest_files)
    except GitError as exc:
        discrepancies = ["verification could not run: %s" % exc]
    verified = not discrepancies

    tier_info = tier_accounting(
        selected, dropped_names, tier_texts, tier_files
    )
    header = build_header(resolved, diff_base, verified, exclusions)
    packet, packet_estimate = build_packet_text(
        header, tier_texts, rereview, tier_info, dropped,
        args.budget, verified, discrepancies, counts,
    )
    manifest = assemble_manifest(
        argv, args, resolved, head, manifest_files, exclusions,
        selected, tier_info, packet, packet_estimate, dropped,
        cap_notes, verified, discrepancies,
    )

    try:
        (out_dir / "packet.md").write_bytes(
            packet.encode("utf-8", "surrogateescape")
        )
        write_manifest(out_dir, manifest)
    except OSError as exc:
        # A failed write is a run failure in the same voice as every
        # other one, so main can leave the failure receipt.
        raise GitError("cannot write the packet files: %s" % exc) from exc

    if not verified:
        for item in discrepancies:
            print("recognitio: discrepancy: %s" % item, file=sys.stderr)
        print(
            "recognitio: packet failed verification and must not be treated "
            "as complete",
            file=sys.stderr,
        )
        return 3
    print(
        "recognitio: packet written to %s with %d files, verified"
        % (out_dir, len(files))
    )
    return 0


def prepare_out_dir(out_dir):
    """Create the output directory and clear any earlier packet."""
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        for name in ("packet.md", "manifest.json"):
            stale = out_dir / name
            if stale.exists():
                stale.unlink()
    except OSError:
        return False
    return True


def find_out_dir(raw_argv):
    """The --out value in a raw argument list, or None when absent."""
    for index, token in enumerate(raw_argv):
        if token == "--out" and index + 1 < len(raw_argv):
            return Path(raw_argv[index + 1])
        if token.startswith("--out="):
            return Path(token[len("--out="):])
    return None


def main(argv=None):
    raw_argv = list(sys.argv[1:]) if argv is None else list(argv)
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        # Argument checking rejects the run before the pipeline ever
        # starts, and it still named an output directory. No earlier
        # verified packet may stand as the apparent result of this
        # run, so the directory is cleared and the failure receipt is
        # written here too, and the exit code passes through.
        code = exc.code if isinstance(exc.code, int) else 2
        if code != 0:
            out_dir = find_out_dir(raw_argv)
            if out_dir is not None and prepare_out_dir(out_dir):
                write_failure_manifest(
                    out_dir, raw_argv,
                    "the run was rejected while its arguments were "
                    "checked, and no packet was built",
                )
                return code
        raise
    repo = Path(args.repo).resolve()
    out_dir = Path(args.out)
    if not prepare_out_dir(out_dir):
        print(
            "recognitio: cannot prepare the output directory %s" % out_dir,
            file=sys.stderr,
        )
        return 2
    try:
        return run_pipeline(args, repo, out_dir, raw_argv)
    except GitError as exc:
        write_failure_manifest(out_dir, raw_argv, str(exc))
        print("recognitio: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
