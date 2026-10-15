#!/usr/bin/env python3
"""Recognitio extractor.

Assembles a verified review packet (the pericope) for a pull request, a
commit range, or a single commit, using only the local git clone. The
extractor never trusts a hosted API diff. It resolves refs locally, builds
tiered context, and recounts files and hunks with separate git invocations
before it will call a packet verified. Any disagreement fails closed.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
SOURCE_EXTS = {".py", ".js", ".jsx", ".ts", ".tsx", ".rs", ".go"}
MAX_CALL_SITES_PER_FUNCTION = 5
MAX_TEST_FILES = 10
MAX_MATCH_LINES_PER_TEST_FILE = 5
MAX_HISTORY_FILES = 3
MAX_BLAME_RANGES = 10
MAX_BLAME_SUMMARY_LINES = 10
MAX_LOG_L_FUNCTIONS = 3
MAX_LOG_L_CHARS = 4000
MAX_RANGE_DIFF_CHARS = 8000

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

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


class GitError(Exception):
    pass


def run_git(repo, args, check=True):
    result = subprocess.run(
        ["git", "-C", str(repo)] + list(args),
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        raise GitError(
            "git %s failed with exit %d: %s"
            % (" ".join(args), result.returncode, result.stderr.strip())
        )
    return result


def run_cmd(cwd, args, check=True):
    result = subprocess.run(list(args), cwd=str(cwd), capture_output=True, text=True)
    if check and result.returncode != 0:
        raise GitError(
            "%s failed with exit %d: %s"
            % (" ".join(args), result.returncode, result.stderr.strip())
        )
    return result


def rev_parse(repo, ref):
    return run_git(repo, ["rev-parse", "--verify", ref + "^{commit}"]).stdout.strip()


def merge_base(repo, left, right):
    return run_git(repo, ["merge-base", left, right]).stdout.strip()


def estimate_tokens(text):
    return len(text) // 4


def cap_text(text, limit, label):
    if len(text) <= limit:
        return text, False
    return text[:limit] + "\n[recognitio] %s capped at %d characters.\n" % (label, limit), True


def resolve_inputs(repo, args):
    """Return a dict with mode, base, head, merge_base, label, and since."""
    since_sha = rev_parse(repo, args.since) if args.since else None

    if args.pr is not None:
        view = run_cmd(
            repo,
            [
                "gh", "pr", "view", str(args.pr),
                "--json", "baseRefOid,headRefOid,baseRefName,headRefName,title",
            ],
        )
        try:
            data = json.loads(view.stdout)
        except json.JSONDecodeError as exc:
            raise GitError("gh pr view returned unparseable JSON: %s" % exc)
        base = None
        head = None
        for key, target in (("baseRefOid", "base"), ("headRefOid", "head")):
            oid = data.get(key)
            if oid:
                probe = run_git(repo, ["cat-file", "-e", oid + "^{commit}"], check=False)
                if probe.returncode == 0:
                    if target == "base":
                        base = oid
                    else:
                        head = oid
        if base is None and data.get("baseRefName"):
            base = rev_parse(repo, data["baseRefName"])
        if head is None and data.get("headRefName"):
            head = rev_parse(repo, data["headRefName"])
        if base is None or head is None:
            raise GitError(
                "could not resolve pull request %d refs in the local clone" % args.pr
            )
        base = rev_parse(repo, base)
        head = rev_parse(repo, head)
        mb = merge_base(repo, base, head)
        return {
            "mode": "pr",
            "label": "pull request %d" % args.pr,
            "base": base,
            "head": head,
            "merge_base": mb,
            "since": since_sha,
        }

    if args.range:
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
        mb = merge_base(repo, base, head)
        return {
            "mode": "range",
            "label": "range %s" % spec,
            "base": base,
            "head": head,
            "merge_base": mb,
            "since": since_sha,
        }

    if args.commit:
        head = rev_parse(repo, args.commit)
        parent = run_git(repo, ["rev-parse", "--verify", head + "^"], check=False)
        if parent.returncode == 0:
            base = parent.stdout.strip()
        else:
            base = EMPTY_TREE
        return {
            "mode": "commit",
            "label": "commit %s" % head[:12],
            "base": base,
            "head": head,
            "merge_base": base,
            "since": since_sha,
        }

    if since_sha is not None:
        head = rev_parse(repo, "HEAD")
        mb = merge_base(repo, since_sha, head)
        return {
            "mode": "since",
            "label": "changes since %s" % since_sha[:12],
            "base": since_sha,
            "head": head,
            "merge_base": mb,
            "since": since_sha,
        }

    raise GitError("one of --pr, --range, --commit, or --since is required")


def parse_name_status(text):
    files = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        code = parts[0].strip()
        letter = code[:1]
        entry = {
            "status_code": code,
            "status": STATUS_NAMES.get(letter, "unknown"),
            "old_path": None,
            "path": None,
        }
        if letter in ("R", "C"):
            entry["old_path"] = parts[1]
            entry["path"] = parts[2]
        else:
            entry["path"] = parts[1]
        files.append(entry)
    return files


def parse_numstat(text):
    stats = {}
    for line in text.splitlines():
        match = re.match(r"^(\S+)\t(\S+)\t(.*)$", line)
        if not match:
            continue
        adds_raw, dels_raw, path_field = match.groups()
        adds = int(adds_raw) if adds_raw.isdigit() else 0
        dels = int(dels_raw) if dels_raw.isdigit() else 0
        path = path_field
        if " => " in path_field:
            left, after = path_field.split(" => ", 1)
            if "{" in left:
                prefix = left.split("{", 1)[0]
                path = prefix + after.replace("}", "", 1)
            else:
                path = after
        stats[path] = (adds, dels)
    return stats


def split_diff(text):
    chunks = {}
    current_path = None
    current_lines = []
    header_re = re.compile(r"^diff --git a/(.*?) b/(.*)$")

    def flush():
        if current_path is not None:
            chunks[current_path] = "".join(current_lines)

    for line in text.splitlines(keepends=True):
        match = header_re.match(line.rstrip("\n"))
        if match:
            flush()
            current_path = match.group(2)
            current_lines = [line]
        elif current_path is not None:
            current_lines.append(line)
    flush()
    return chunks


def count_hunks(chunk):
    return sum(1 for line in chunk.splitlines() if line.startswith("@@ "))


def changed_ranges(chunk):
    ranges = []
    for line in chunk.splitlines():
        match = HUNK_RE.match(line)
        if match:
            start = int(match.group(3))
            count = int(match.group(4)) if match.group(4) else 1
            if count > 0:
                ranges.append((start, start + count - 1))
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


def show_file(repo, head, path):
    result = run_git(repo, ["show", "%s:%s" % (head, path)], check=False)
    if result.returncode != 0:
        return None
    return result.stdout


def build_t0(repo, mb, head, files, numstat_text, commit_log):
    lines = []
    lines.append("## T0 Triage")
    lines.append("")
    lines.append("Files changed: %d" % len(files))
    lines.append("")
    lines.append("### Numstat")
    lines.append("")
    lines.append("```")
    lines.append(numstat_text.rstrip() if numstat_text.strip() else "(no changes)")
    lines.append("```")
    lines.append("")
    lines.append("### Commits")
    lines.append("")
    lines.append("```")
    lines.append(commit_log.rstrip() if commit_log.strip() else "(no commits)")
    lines.append("```")
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
        lines.append("### %s" % path)
        lines.append("")
        lines.append("Status: %s" % entry["status"])
        if entry.get("old_path"):
            lines.append("Renamed from: %s" % entry["old_path"])
        lines.append("")
        lines.append("```diff")
        chunk = chunks.get(path, "")
        lines.append(chunk.rstrip() if chunk.strip() else "(no textual diff)")
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def git_grep_lines(repo, head, term):
    result = run_git(
        repo, ["grep", "-n", "-w", "-e", term, head], check=False
    )
    if result.returncode not in (0, 1):
        return []
    out = []
    for line in result.stdout.splitlines():
        parts = line.split(":", 3)
        if len(parts) == 4 and parts[2].isdigit():
            out.append((parts[1], int(parts[2]), parts[3]))
    return out


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


def build_t2(repo, head, files, functions_by_file):
    lines = []
    lines.append("## T2 Companions")
    lines.append("")
    lines.append(
        "Call sites and test files found by deterministic search at the head revision."
    )
    lines.append("")
    notes = []
    content_cache = {}

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
            block.append("%s:%d: %s" % (path, number, rows[number - 1]))
        return "\n".join(block)

    source_files = [
        entry for entry in files if Path(entry["path"]).suffix in SOURCE_EXTS
    ]
    if not source_files:
        lines.append("No changed source files, so no companions were gathered.")
        lines.append("")
        return "\n".join(lines), notes

    for entry in source_files:
        path = entry["path"]
        names = functions_by_file.get(path, [])
        for name in names:
            hits = [
                hit for hit in git_grep_lines(repo, head, name) if hit[0] != path
            ]
            lines.append("### Call sites for %s in %s" % (name, path))
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

    test_hits = {}
    all_names = []
    for entry in source_files:
        stem = Path(entry["path"]).stem
        terms = [stem] + functions_by_file.get(entry["path"], [])
        for term in terms:
            for hit_path, hit_line, content in git_grep_lines(repo, head, term):
                if is_test_path(hit_path) and hit_path not in [e["path"] for e in files]:
                    test_hits.setdefault(hit_path, []).append(
                        (hit_line, content)
                    )
    lines.append("### Test files that mention the changed code")
    lines.append("")
    if not test_hits:
        lines.append("No test files mention the changed modules or functions.")
        lines.append("")
    else:
        test_paths = sorted(test_hits)
        if len(test_paths) > MAX_TEST_FILES:
            notes.append(
                "test files capped at %d of %d" % (MAX_TEST_FILES, len(test_paths))
            )
            test_paths = test_paths[:MAX_TEST_FILES]
        for test_path in test_paths:
            hits = sorted(test_hits[test_path])
            lines.append("#### %s" % test_path)
            lines.append("")
            shown = hits[:MAX_MATCH_LINES_PER_TEST_FILE]
            if len(hits) > len(shown):
                notes.append(
                    "matches in %s capped at %d of %d"
                    % (test_path, len(shown), len(hits))
                )
            lines.append("```")
            for hit_line, content in shown:
                lines.append("%d: %s" % (hit_line, content))
            lines.append("```")
            lines.append("")
    for note in notes:
        lines.append("Cap note: %s." % note)
    if notes:
        lines.append("")
    return "\n".join(lines), notes


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


def build_t3(repo, head, files, stats, ranges_by_file, functions_by_file):
    lines = []
    lines.append("## T3 History")
    lines.append("")
    notes = []
    ranked = sorted(
        files,
        key=lambda e: stats.get(e["path"], (0, 0))[0] + stats.get(e["path"], (0, 0))[1],
        reverse=True,
    )
    top_files = [e for e in ranked if e["status"] != "deleted"][:MAX_HISTORY_FILES]
    if not top_files:
        lines.append("No files with history to summarise.")
        lines.append("")
        return "\n".join(lines), notes

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
                ["blame", "--porcelain", "-L", "%d,%d" % (start, end), head, "--", path],
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
        lines.append("#### %s" % path)
        lines.append("")
        if not tally:
            lines.append("No blame data for the changed ranges.")
            lines.append("")
            continue
        summary = sorted(tally.items(), key=lambda item: -item[1])
        if len(summary) > MAX_BLAME_SUMMARY_LINES:
            notes.append(
                "blame summary for %s capped at %d entries"
                % (path, MAX_BLAME_SUMMARY_LINES)
            )
            summary = summary[:MAX_BLAME_SUMMARY_LINES]
        lines.append("```")
        for (author, sha), count in summary:
            lines.append("%s %s lines %d" % (author, sha, count))
        lines.append("```")
        lines.append("")

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
            lines.append("#### %s in %s" % (name, path))
            lines.append("")
            if result.returncode != 0:
                lines.append("No history available for this function.")
                lines.append("")
                continue
            text, capped = cap_text(
                result.stdout.rstrip(), MAX_LOG_L_CHARS, "history for %s" % name
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
    for note in notes:
        lines.append("Cap note: %s." % note)
    if notes:
        lines.append("")
    return "\n".join(lines), notes


def build_rereview(repo, mb, head, since):
    lines = []
    lines.append("## Re-review")
    lines.append("")
    lines.append("Previous reviewed revision: %s" % since)
    lines.append("")
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
    result = run_git(
        repo,
        ["range-diff", "%s..%s" % (mb, since), "%s..%s" % (mb, head)],
        check=False,
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
            ["diff", "--stat", "%s...%s" % (since, head)],
        ).stdout
        lines.append("Range diff was not available. Diff stat since the previous review:")
        lines.append(delta.rstrip() if delta.strip() else "(no changes)")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def verify_counts(repo, mb, head, manifest_files):
    """Recount files and hunks with separate git invocations.

    Returns a list of discrepancy strings. An empty list means the manifest
    matches an independent recount.
    """
    discrepancies = []
    status_text = run_git(
        repo, ["diff", "--name-status", "-M", "-C", mb, head]
    ).stdout
    recounted_files = parse_name_status(status_text)
    manifest_by_path = {entry["path"]: entry for entry in manifest_files}
    recounted_by_path = {entry["path"]: entry for entry in recounted_files}
    for path in sorted(set(manifest_by_path) - set(recounted_by_path)):
        discrepancies.append("file in manifest but not in recount: %s" % path)
    for path in sorted(set(recounted_by_path) - set(manifest_by_path)):
        discrepancies.append("file in recount but not in manifest: %s" % path)
    for path in sorted(set(manifest_by_path) & set(recounted_by_path)):
        if manifest_by_path[path]["status"] != recounted_by_path[path]["status"]:
            discrepancies.append(
                "status mismatch for %s: manifest %s, recount %s"
                % (
                    path,
                    manifest_by_path[path]["status"],
                    recounted_by_path[path]["status"],
                )
            )
    full = run_git(
        repo,
        ["diff", "--histogram", "--find-renames", "--find-copies", "-W", mb, head],
    ).stdout
    recounted_chunks = split_diff(full)
    for path, entry in manifest_by_path.items():
        chunk = recounted_chunks.get(path)
        if chunk is None:
            if entry["hunks"] != 0:
                discrepancies.append(
                    "no diff chunk in recount for %s but manifest lists %d hunks"
                    % (path, entry["hunks"])
                )
            continue
        recounted_hunks = count_hunks(chunk)
        if recounted_hunks != entry["hunks"]:
            discrepancies.append(
                "hunk count mismatch for %s: manifest %d, recount %d"
                % (path, entry["hunks"], recounted_hunks)
            )
    for path in recounted_chunks:
        if path not in manifest_by_path:
            discrepancies.append("diff chunk in recount but not in manifest: %s" % path)
    return discrepancies


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="extract.py",
        description="Assemble a verified recognitio review packet from a local clone.",
    )
    parser.add_argument("--pr", type=int, default=None, help="pull request number")
    parser.add_argument("--range", dest="range", default=None, help="A..B or A...B")
    parser.add_argument("--commit", default=None, help="a single commit")
    parser.add_argument(
        "--since", default=None, help="previous reviewed revision for re-review"
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
    if sum(chosen) == 0 and not args.since:
        parser.error("one of --pr, --range, --commit, or --since is required")
    return args


def main(argv=None):
    args = parse_args(argv)
    repo = Path(args.repo).resolve()
    out_dir = Path(args.out)
    try:
        resolved = resolve_inputs(repo, args)
    except GitError as exc:
        print("recognitio: %s" % exc, file=sys.stderr)
        return 2

    mb = resolved["merge_base"]
    head = resolved["head"]

    try:
        status_text = run_git(
            repo, ["diff", "--name-status", "-M", "-C", mb, head]
        ).stdout
        numstat_text = run_git(
            repo, ["diff", "--numstat", "-M", "-C", mb, head]
        ).stdout
        commit_log = run_git(
            repo, ["log", "--oneline", "--reverse", "%s..%s" % (mb, head)]
        ).stdout
        full_diff = run_git(
            repo,
            ["diff", "--histogram", "--find-renames", "--find-copies", "-W", mb, head],
        ).stdout
        precise_diff = run_git(
            repo,
            ["diff", "--histogram", "--find-renames", "--find-copies", "-U0", mb, head],
        ).stdout
    except GitError as exc:
        print("recognitio: %s" % exc, file=sys.stderr)
        return 2

    files = parse_name_status(status_text)
    if not files:
        print(
            "recognitio: the resolved change is empty, no packet was built",
            file=sys.stderr,
        )
        return 2
    stats = parse_numstat(numstat_text)
    chunks = split_diff(full_diff)
    precise_chunks = split_diff(precise_diff)

    for entry in files:
        path = entry["path"]
        adds, dels = stats.get(path, (0, 0))
        entry["additions"] = adds
        entry["deletions"] = dels
        entry["hunks"] = count_hunks(chunks.get(path, ""))

    functions_by_file = {
        entry["path"]: extract_function_names(chunks.get(entry["path"], ""))
        for entry in files
    }
    ranges_by_file = {
        entry["path"]: changed_ranges(precise_chunks.get(entry["path"], ""))
        for entry in files
    }

    t0 = build_t0(repo, mb, head, files, numstat_text, commit_log)
    t1 = build_t1(files, chunks)
    t2, t2_notes = build_t2(repo, head, files, functions_by_file)
    t3, t3_notes = build_t3(repo, head, files, stats, ranges_by_file, functions_by_file)

    dropped = []
    included = {"T0": True, "T1": True, "T2": True, "T3": True}
    tier_texts = {"T0": t0, "T1": t1, "T2": t2, "T3": t3}

    if args.budget is not None:
        core_tokens = estimate_tokens(t0) + estimate_tokens(t1)
        if core_tokens > args.budget:
            print(
                "recognitio: T0 and T1 alone need about %d tokens, over the "
                "budget of %d. The change itself is never truncated. Raise "
                "the budget or split the change."
                % (core_tokens, args.budget),
                file=sys.stderr,
            )
            return 2
        total = core_tokens + estimate_tokens(t2) + estimate_tokens(t3)
        if total > args.budget:
            dropped.append(
                {"tier": "T3", "reason": "budget of %d tokens" % args.budget}
            )
            included["T3"] = False
            total -= estimate_tokens(t3)
        if total > args.budget:
            dropped.append(
                {"tier": "T2", "reason": "budget of %d tokens" % args.budget}
            )
            included["T2"] = False
            total -= estimate_tokens(t2)

    manifest_files = [
        {
            "path": entry["path"],
            "old_path": entry["old_path"],
            "status": entry["status"],
            "status_code": entry["status_code"],
            "additions": entry["additions"],
            "deletions": entry["deletions"],
            "hunks": entry["hunks"],
        }
        for entry in files
    ]

    try:
        discrepancies = verify_counts(repo, mb, head, manifest_files)
    except GitError as exc:
        discrepancies = ["verification could not run: %s" % exc]
    verified = not discrepancies

    header_lines = []
    header_lines.append("# The pericope for %s" % resolved["label"])
    header_lines.append("")
    header_lines.append(
        "A recognitio review packet. It holds the change and the context "
        "appointed to be read with it, and nothing else."
    )
    header_lines.append("")
    header_lines.append("Mode: %s" % resolved["mode"])
    header_lines.append("Base: %s" % resolved["base"])
    header_lines.append("Head: %s" % head)
    header_lines.append("Merge base: %s" % mb)
    if resolved["since"]:
        header_lines.append("Since: %s" % resolved["since"])
    header_lines.append(
        "Verified: %s" % ("yes" if verified else "NO, see the completeness section")
    )
    header_lines.append("")
    header = "\n".join(header_lines)

    sections = [header, t0, t1]
    if included["T2"]:
        sections.append(t2)
    else:
        sections.append(
            "## T2 Companions\n\nDropped under the token budget. "
            "The change in T1 is complete.\n"
        )
    if included["T3"]:
        sections.append(t3)
    else:
        sections.append(
            "## T3 History\n\nDropped under the token budget. "
            "The change in T1 is complete.\n"
        )
    if resolved["since"]:
        sections.append(build_rereview(repo, mb, head, resolved["since"]))

    tier_accounting = {}
    for tier in ("T0", "T1", "T2", "T3"):
        tier_accounting[tier] = {
            "included": included[tier],
            "estimated_tokens": estimate_tokens(tier_texts[tier]) if included[tier] else 0,
        }
    packet_estimate = estimate_tokens("\n".join(sections))

    completeness = []
    completeness.append("## Budget and completeness")
    completeness.append("")
    completeness.append("Budget in tokens: %s" % (args.budget if args.budget is not None else "none set"))
    completeness.append("Packet estimate in tokens: %d" % packet_estimate)
    for tier in ("T0", "T1", "T2", "T3"):
        completeness.append(
            "%s %s at about %d tokens"
            % (
                tier,
                "included" if included[tier] else "dropped",
                tier_accounting[tier]["estimated_tokens"],
            )
        )
    if dropped:
        for item in dropped:
            completeness.append(
                "Dropped %s because of the %s." % (item["tier"], item["reason"])
            )
    else:
        completeness.append("No tier was dropped.")
    completeness.append("")
    if verified:
        completeness.append(
            "Completeness check passed. A separate recount of files, "
            "statuses, and hunks matches the manifest."
        )
    else:
        completeness.append(
            "Completeness check FAILED. This packet must not be reviewed as "
            "if it were whole. Discrepancies follow."
        )
        for item in discrepancies:
            completeness.append("Missing or mismatched: %s" % item)
    completeness.append("")
    sections.append("\n".join(completeness))
    packet = "\n".join(sections)

    manifest = {
        "mode": resolved["mode"],
        "label": resolved["label"],
        "base": resolved["base"],
        "head": head,
        "merge_base": mb,
        "since": resolved["since"],
        "files": manifest_files,
        "tiers": tier_accounting,
        "budget": {
            "budget_tokens": args.budget,
            "estimated_tokens": packet_estimate,
            "dropped": dropped,
        },
        "cap_notes": t2_notes + t3_notes,
        "verified": verified,
        "discrepancies": discrepancies,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "packet.md").write_text(packet, encoding="utf-8")
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

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


if __name__ == "__main__":
    sys.exit(main())
