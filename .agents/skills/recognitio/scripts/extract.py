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
No invocation runs a driver program a repository or the caller's
environment defines. The diff family, blame, the line history reader,
the blob reader and the companion search all refuse text conversion,
the diff family also refuses external diff drivers, and configuration
the caller supplies through the environment never reaches a child
process at all.
File paths reach git as literal pathspecs, never as patterns. Path data
moves through NUL delimited output, so quoted, spaced and Unicode
paths survive end to end. All subprocess output is handled as bytes
first, so binary files and non UTF-8 content cannot crash the run.

The output directory is written only by a finished run. Arguments are
checked before any output path is touched, and the inputs are resolved
and read before the directory is opened. The output location is
resolved once and pinned for the whole run, the pair is staged beside
its final names inside that directory and moved into place with
renames under an exclusive lock, and a second run naming the same
directory is refused while the first is working. A run that fails
after its inputs were read leaves a failure receipt in place of the
old packet, and a run that is refused or interrupted leaves whatever
already stood in the directory untouched.
"""

import argparse
import difflib
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover, the shipped hosts carry fcntl
    fcntl = None

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
    # A rename limit of zero is no limit in git, so inexact rename
    # and copy detection always runs in full. Pinning it here, on
    # the command line, overrides any diff.renameLimit a clone or
    # a global config carries, which would otherwise switch the
    # inexact pass off in silence and read copies as additions and
    # renames as a deletion beside an addition.
    "-c", "diff.renameLimit=0",
    # The diff algorithm is histogram on every reader, not only on
    # the body diffs that carry the flag in their argument list.
    # The numstat family, the name status family, the stat
    # fallback and the line history reader obey this pin, so the
    # counts the manifest is built from and the bodies the packet
    # shows are one reading of the change under one algorithm,
    # whatever algorithm a clone or a global config prefers.
    "-c", "diff.algorithm=histogram",
    # A submodule pointer move is a change in the packet. An
    # ambient ignore setting at all would delete it in silence
    # from every diff the fetch reads, and a display setting of
    # diff or log would rewrite its body with content from inside
    # the submodule or break the run outright, so the ignore
    # behaviour is pinned to the value that reports pointer moves
    # and the display is pinned to the short form.
    "-c", "diff.ignoreSubmodules=none",
    "-c", "diff.submodule=short",
    # Shortened hashes stand at seven characters on every surface
    # that prints one, the oneline commit lists, the index lines
    # inside diff bodies and the range diff output alike, so a
    # packet stamped in one clone is not refused in another over
    # display width alone.
    "-c", "core.abbrev=7",
    # Commit subjects are recoded to UTF-8 on every log reading.
    # A commit that declares a legacy encoding otherwise hands the
    # packet raw legacy bytes under an ambient log output
    # encoding, and the shipped packet is then not a valid UTF-8
    # document at all.
    "-c", "i18n.logOutputEncoding=UTF-8",
    # Attributes come from the tree under review alone. The user
    # attributes file, named by configuration or standing at its
    # default location, is switched off by the empty value, the
    # attribute tree configuration is switched off the same way,
    # and every diff reading invocation also carries an attribute
    # source pin naming the reviewed tree, which overrides the
    # attribute source variable in the caller environment. The
    # clone info attributes file is the one source no pin can
    # confine, because git gives it the highest precedence of any
    # attribute source, so a clone carrying one is refused where
    # the inputs are resolved rather than read under it.
    "-c", "core.attributesFile=",
    "-c", "attr.tree=",
]
# Every invocation that can produce or read diff text also refuses
# external diff drivers and textconv filters, both of which can
# rewrite the text of a change. A textconv driver is named by the
# attributes of the tree under review and defined in configuration,
# so an unpinned reader would run a program the reviewed party or
# the caller's environment chose and would read its output as
# evidence. Blame applies a textconv filter by default, so it
# carries these flags beside the diff family, the line history
# reader and the blob reader. The companion search takes the
# textconv refusal alone, because it has no external diff form.
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
        elif char in (
            "\u202a", "\u202b", "\u202c", "\u202d", "\u202e",
            "\u2066", "\u2067", "\u2068", "\u2069",
            "\u200b", "\u200c", "\u200d", "\u200e", "\u200f",
            "\u2060", "\ufeff",
        ):
            # Bidirectional controls reorder the text that follows
            # them in any ordinary renderer, and zero width marks
            # hide inside a name, so a name carrying one would
            # display as a different name than the file the packet
            # names. They are escaped like the separators above.
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

# Driver and configuration variables are scrubbed beside the location
# variables. Configuration supplied through the environment can define
# a textconv or external diff driver outright, with no entry in any
# config file a reviewer could read first, and the remaining names hand
# a child process a program to run in place of its pager, its diff
# renderer or its own subcommands. None of them may reach a child.
GIT_DRIVER_ENV_VARS = (
    "GIT_EXTERNAL_DIFF",
    "GIT_DIFF_OPTS",
    "GIT_PAGER",
    "GIT_EXEC_PATH",
)
GIT_CONFIG_ENV_PREFIX = "GIT_CONFIG"

# Attribute source variables are scrubbed beside the driver family.
# The attribute source variable names a tree whose attributes every
# child would read in place of the reviewed tree, and the global
# and system attribute variables name files outside the reviewed
# tree that would reshape its markings the same way. The diff
# readings carry an attribute source pin of their own as well, so
# either layer alone confines the markings to the reviewed tree.
GIT_ATTR_ENV_VARS = (
    "GIT_ATTR_SOURCE",
    "GIT_ATTR_GLOBAL",
    "GIT_ATTR_SYSTEM",
)

# Pathspec mode variables are scrubbed for the same reason. The
# wrapper hands every pathspec to git under the literal pathspecs
# flag, and a caller shell that exports the case insensitive or
# glob pathspec mode for its own work makes git refuse that
# combination outright, which fails extraction closed on exactly
# the attribute marked files whose per file readings carry a
# pathspec. No pathspec mode from the caller may reach a child.
GIT_PATHSPEC_ENV_VARS = (
    "GIT_LITERAL_PATHSPECS",
    "GIT_GLOB_PATHSPECS",
    "GIT_ICASE_PATHSPECS",
    "GIT_NOGLOB_PATHSPECS",
)


def scrubbed_child_env():
    """The environment every child process runs under."""
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in GIT_LOCATION_VARS
        and key not in GIT_DRIVER_ENV_VARS
        and key not in GIT_ATTR_ENV_VARS
        and key not in GIT_PATHSPEC_ENV_VARS
        and not key.startswith(GIT_CONFIG_ENV_PREFIX)
    }
    # The second belt behind the --no-replace-objects flag every git
    # invocation carries. Whichever layer a future call site forgets,
    # the other still refuses replacement objects.
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    # The system attributes file stands outside the reviewed tree
    # beside the user attributes file the pin list switches off,
    # so its readings are refused here as well.
    env["GIT_ATTR_NOSYSTEM"] = "1"
    return env


# Every child process gets a timeout, the network calls to the GitHub
# CLI included. A stalled call must fail the run, never hang it.
PROCESS_TIMEOUT_SECONDS = 120


def run_process(argv, cwd=None):
    env = scrubbed_child_env()
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
    # --no-pager stands beside the replace and pathspec refusals, so
    # a pager program named by clone config, global config or the
    # environment can never run for an invocation whose output the
    # packet reads as data.
    argv = (
        ["git", "--no-pager", "--no-replace-objects",
         "--literal-pathspecs"]
        + list(global_flags)
        + ["-C", str(repo)] + GIT_PIN + list(args)
    )
    proc = run_argv(argv, None, check, "git " + " ".join(args))
    # Git reports a skipped rename detection pass on standard error
    # while still exiting zero, so checking the exit code alone
    # discards the one warning that says the diff under the packet
    # was degraded. Surface it as a run failure instead, so it
    # reaches the failure receipt and no stamped packet can rest on
    # a detection pass that never ran.
    lowered = proc.stderr.lower()
    if "rename detection was skipped" in lowered or \
            "exhaustive rename detection" in lowered:
        raise GitError(
            "git reported that rename detection was skipped, so the "
            "diff cannot be trusted as a complete reading of the "
            "change: %s" % proc.stderr.strip()
        )
    return proc


def run_cmd(cwd, args, check=True):
    return run_argv(list(args), cwd, check, " ".join(args))


def rev_parse(repo, ref):
    return run_git(repo, ["rev-parse", "--verify", ref + "^{commit}"]).stdout.strip()


def merge_base(repo, left, right):
    return run_git(repo, ["merge-base", left, right]).stdout.strip()


def is_shallow(repo):
    out = run_git(repo, ["rev-parse", "--is-shallow-repository"]).stdout.strip()
    return out == "true"


ESTIMATE_METHOD = (
    "per shape token estimate, priced by character class"
)


def estimate_tokens(text):
    """The per shape token estimate of one text, in whole tokens.

    The old rule counted characters and divided by four, and it
    mispriced whole shape families by multiples. CJK text carries
    about one real token per character and was priced at a quarter
    of one, base64 and hex text carry about seven real tokens per
    ten characters and were priced at two and a half, and a run of
    spaces carries almost no real tokens and was priced at full
    character rate. This estimate prices each character class at
    the rate that class carries in a real tokenizer, in thousandths
    of a token, and states its shape rates here so the number a
    budget spends can be read against them. A digit bearing run of
    characters is priced at 600 thousandths per character, at 800
    when it stands alone, and at 1500 in all when it runs to two
    characters, because a real tokenizer splits short hex and
    number pairs finer than long ones. A run of hex letters is
    priced at 700 per character. A plain letter run is priced at a
    base of 600 plus 120 per character and 200 more per character
    past eight, because a real tokenizer splits long runs finer
    than short words. A run of eight or more copies of one
    character is priced at 100 per character, because a real
    tokenizer merges repeats. A character outside ASCII is priced
    by its encoded length, one whole token at two bytes or fewer,
    1200 thousandths at three bytes and 2400 thousandths at four
    bytes, because a tokenizer works on the encoded bytes and the
    widest characters carry the most tokens. A newline is priced
    at one whole token, blank space at 20 per character with a
    short blank run carrying a tab priced at 300 in all, and any
    other ASCII mark at 800. On the
    shape families the audit measured, prose, code, CJK, base64,
    hex in both its forms, identifier heavy text, punctuation
    dense text, short lines, space runs and repeated character
    runs, a fresh measurement with the cl100k tokenizer put the
    real count between 0.49 and 1.35 times this estimate, so
    the estimate never underprices a measured family by a
    multiple and never overprices one by more than about twice.
    It is still an estimate and not a tokenizer, and every surface
    that names a budget names this method beside it.
    """
    total = 0
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char == "\n":
            total += 1000
            index += 1
            continue
        if char in " \t\r":
            end = index
            while end < length and text[end] in " \t\r":
                end += 1
            run = text[index:end]
            cost = 20 * len(run)
            if "\t" in run and len(run) <= 8:
                cost = max(cost, 300)
            total += cost
            index = end
            continue
        if ord(char) >= 128:
            encoded = len(char.encode("utf-8", "surrogateescape"))
            total += {1: 1000, 2: 1000, 3: 1200, 4: 2400}.get(
                encoded, 2400
            )
            index += 1
            continue
        if char.isalnum() or char == "_":
            end = index
            while end < length:
                nxt = text[end]
                if not (nxt.isalnum() or nxt == "_") or ord(nxt) >= 128:
                    break
                end += 1
            run = text[index:end]
            size = len(run)
            if len(set(run)) == 1 and size >= 8:
                total += 100 * size
            elif any(item.isdigit() for item in run):
                if size == 1:
                    total += 800
                elif size == 2:
                    total += 1500
                else:
                    total += 600 * size
            elif size >= 2 and all(
                item in "abcdefABCDEF" for item in run
            ):
                total += 700 * size
            else:
                total += 600 + 120 * size + 200 * max(0, size - 8)
            index = end
            continue
        total += 800
        index += 1
    return total // 1000


PRIOR_PRS_HEADING = "### Prior pull requests touching these files"


def prior_prs_passage(text):
    """The prior pull requests passage of a history tier text.

    The passage is the one part of the tier whose words come from
    the live GitHub state of the environment that built the
    packet, so the extractor records it in the manifest and the
    packet check settles a dropped history tier against that
    record instead of against the checking environment. The
    passage runs from its heading to the cap notes block that
    follows it, or to the end of the tier when no cap notes stand.
    """
    start = text.find(PRIOR_PRS_HEADING)
    if start == -1:
        return None
    end = text.find("\n### Cap notes", start)
    if end == -1:
        return text[start:]
    return text[start:end]


def settled_history_text(text, passage):
    """A rebuilt history tier with its passage settled from a record.

    The rebuilt tier is measured with the recorded passage standing
    where the rebuild put its own live passage, so the measure
    cannot move with the checking environment its GitHub state.
    """
    if passage is None:
        return text
    start = text.find(PRIOR_PRS_HEADING)
    if start == -1:
        return text
    end = text.find("\n### Cap notes", start)
    if end == -1:
        return text[:start] + passage
    return text[:start] + passage + text[end:]


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


def refuse_info_attributes(repo):
    """Refuse a clone whose info attributes would reshape the packet.

    Git gives the attributes file inside the clone git directory
    the highest precedence of any attribute source, above the
    attributes of the tree under review itself, and no command
    line pin, configuration pin or environment scrub on this git
    can confine or disable that reading. A clone carrying an
    effective line in that file would hand the packet markings
    the reviewed tree never made while the packet credits the
    tree, so the run refuses in its own words instead. A file
    holding only comments and blank lines assigns nothing and
    does not refuse the run.
    """
    common = run_git(
        repo, ["rev-parse", "--git-common-dir"], check=False
    )
    if common.returncode != 0 or not common.stdout.strip():
        return
    common_path = Path(common.stdout.strip())
    if not common_path.is_absolute():
        common_path = Path(repo) / common_path
    info_attributes = common_path / "info" / "attributes"
    try:
        text = info_attributes.read_text(
            encoding="utf-8", errors="surrogateescape"
        )
    except OSError:
        return
    effective = [
        line for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if effective:
        raise GitError(
            "the clone carries attributes in %s and those attributes "
            "sit outside the reviewed tree while git reads them ahead "
            "of the tree attributes themselves, so no packet built in "
            "this clone can credit its markings to the tree under "
            "review. Empty or remove that file, then run again"
            % info_attributes
        )


def resolve_pr(repo, args, since_sha):
    view = run_cmd(
        repo,
        [
            "gh", "pr", "view", str(args.pr),
            "--json",
            "baseRefOid,headRefOid,title,body,state",
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
        # The state of the pull request under review, recorded
        # with the moment this fetch read it. The state is a
        # snapshot from this fetch and is never presented as a
        # live claim, and a record that carries no state names
        # it unknown rather than inventing one.
        "state": str(data.get("state") or "unknown").lower(),
        "state_as_of": datetime.now(timezone.utc).isoformat(),
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
    refuse_info_attributes(repo)
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
    """Split a full diff into its emitted sections, in emission order.

    One file entry can own more than one section. A typechange is
    emitted as two sections under one header, the old form deleted
    and the new form created, so a section list is not a file list
    and no caller may pair the two by position. Grouping by header
    identity, in group_diff_chunks below, is how sections are
    reunited with the entry that owns them. No path is ever parsed
    out of a diff header, which keeps paths containing spaces or
    the text b/ intact.
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


def group_diff_chunks(chunks):
    """Group emitted diff sections by header identity.

    Consecutive sections that carry the exact same header line are
    the two halves of one typechange entry, the deletion of the old
    form and the creation of the new form under the same path. They
    merge, in emission order, into the one chunk that entry owns.
    Every other entry emits exactly one section, so grouping leaves
    it untouched. The header line is compared whole and never
    parsed, so a path carrying spaces, quotes or the text b/ groups
    exactly as safely as a plain path.
    """
    grouped = []
    headers = []
    for chunk in chunks:
        header = chunk.split("\n", 1)[0] if chunk else ""
        if grouped and header and headers[-1] == header:
            grouped[-1] += chunk
        else:
            grouped.append(chunk)
            headers.append(header)
    return grouped


def pair_diff_chunks(files, raw_chunks):
    """Pair diff chunks with file entries by identity, never position.

    The grouped chunks stand in the same order as the name status
    entries, and grouping has already reunited the two sections a
    typechange emits, so the pairing is one grouped chunk per entry
    in that shared order, each chunk carrying the header of the file
    it is paired with. A count that still disagrees after grouping
    means the diff and the name status output describe different
    changes, and the run fails closed instead of handing any file
    a neighbouring file's diff body.
    """
    grouped = group_diff_chunks(raw_chunks)
    if len(grouped) != len(files):
        raise GitError(
            "the diff holds %d file chunks against %d name status "
            "entries, so no chunk can be paired with its file by "
            "identity and no packet can be built from it"
            % (len(grouped), len(files))
        )
    return {
        entry["path"]: grouped[position]
        for position, entry in enumerate(files)
    }


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
        if line.startswith("diff --git "):
            # A merged typechange chunk holds two sections. The
            # second section opens a fresh file header, so the
            # hunk state resets here or its --- and +++ header
            # lines would count as content lines of the first
            # section.
            in_hunks = False
            continue
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
        ["git", "--no-pager", "--no-replace-objects",
         "--literal-pathspecs",
         "-C", str(repo)] + GIT_PIN
        + ["show"] + DIFF_FLAGS + ["%s:%s" % (ref, path)]
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
    in git's emission order, and the chunks pair with them by header
    identity through pair_diff_chunks, so the two sections a
    typechange emits land on the typechanged file itself and never
    shift a later file onto the wrong diff body.

    Copy detection runs under the harder rule on every call, so a
    file the change itself does not modify can still stand as the
    source of a copy. Without that rule such a copy reads as a
    plain addition and its lines count as new to the tree when
    they already stood in it.
    """
    # Every diff reading in the fetch takes its attributes from
    # the head tree alone, under the attribute source pin the
    # range diff reading already carried in its own form. Markings
    # planted in the working tree, in a user attributes file or
    # through the caller environment then cannot reach the packet,
    # and a marking the head tree itself carries still can.
    attr_flags = ["--attr-source=" + head]
    status_text = run_git(
        repo, ["diff", "--name-status", "-z", "-M", "-C", "--find-copies-harder"] + DIFF_FLAGS
        + [diff_base, head], global_flags=attr_flags
    ).stdout
    # The counts are read under the histogram algorithm, the same
    # algorithm both diff bodies in this fetch are produced under.
    # Git's default algorithm pairs repeated lines differently, so
    # on a file whose lines repeat its numstat can stand one pair
    # of lines away from any count of the diff body, and the
    # recount then reports a disagreement that is not there.
    numstat_text = run_git(
        repo, ["diff", "--histogram", "--numstat", "-z", "-M", "-C",
               "--find-copies-harder"] + DIFF_FLAGS
        + [diff_base, head], global_flags=attr_flags
    ).stdout
    commit_log = run_git(
        repo, ["log", "--oneline", "--reverse", "%s..%s" % (diff_base, head)]
    ).stdout
    full_diff = run_git(
        repo,
        ["diff", "--histogram", "--find-renames", "--find-copies", "--find-copies-harder", "-W"]
        + DIFF_FLAGS + [diff_base, head], global_flags=attr_flags
    ).stdout
    precise_diff = run_git(
        repo,
        ["diff", "--histogram", "--find-renames", "--find-copies", "--find-copies-harder", "-U0"]
        + DIFF_FLAGS + [diff_base, head], global_flags=attr_flags
    ).stdout
    files = parse_name_status_z(status_text)
    stats, binary_paths = parse_numstat_z(numstat_text)
    chunks = pair_diff_chunks(files, split_diff(full_diff))
    precise = pair_diff_chunks(files, split_diff(precise_diff))
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

    The pathspec can pull a second file into the run. When the
    source of a copy stands in the pathspec beside its copy and
    the source itself changed in the range, git emits the source
    change as its own section, and that section is not the copy's
    delta. The run therefore pairs its sections with its own name
    status output, under the same detection flags, and keeps only
    the section the entry itself owns. A typechange entry still
    emits its two sections inside that one pairing, and grouping
    has already reunited them, so the entry is measured and shown
    whole instead of by its deletion half alone.
    """
    paths = entry_paths(entry)
    result = run_git(
        repo,
        ["diff", "--text", "--histogram", "--find-renames",
         "--find-copies", "--find-copies-harder", context_flag] + DIFF_FLAGS
        + [diff_base, head, "--"] + paths,
        global_flags=["--attr-source=" + head],
    )
    status_text = run_git(
        repo, ["diff", "--name-status", "-z", "-M", "-C",
               "--find-copies-harder"] + DIFF_FLAGS
        + [diff_base, head, "--"] + paths,
        global_flags=["--attr-source=" + head],
    ).stdout
    paired = pair_diff_chunks(
        parse_name_status_z(status_text), split_diff(result.stdout)
    )
    if entry["path"] not in paired:
        raise GitError(
            "the per file diff for %s holds no section the entry "
            "owns, so it cannot be measured as text" % entry["path"]
        )
    return paired[entry["path"]]


def per_file_text_numstat(repo, diff_base, head, entry):
    """Git's own line counts for one file, read with the text flag.

    Returns the (additions, deletions) pair numstat reports for the
    entry's path, or None when git still reports the file as binary.
    This is the independent second count for attribute marked files,
    the same numstat source ordinary files are measured from. It is
    read under the histogram algorithm, like the per file text diff
    it is cross checked against, for the reason fetch_change gives.
    """
    result = run_git(
        repo,
        ["diff", "--text", "--histogram", "--numstat", "-z", "-M", "-C",
         "--find-copies-harder"] + DIFF_FLAGS
        + [diff_base, head, "--"] + entry_paths(entry),
        global_flags=["--attr-source=" + head],
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
            "reason": "marked binary by the attributes of the "
                      "tree under review, counted and shown as text",
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


def identical_blob_typechange_counts(repo, diff_base, head, entry,
                                       precise_chunk):
    """The body counts for a typechange whose blob never changed.

    Plain numstat reports no added and no deleted lines for such
    an entry because the bytes on the two sides are the same
    bytes. The diff body still shows the change as a deletion
    of the old form and a creation of the new form, so the
    lines that body carries are the count a reader of the
    packet can recount for themselves. A mode only change
    carries no such body lines and keeps its zero counts, and
    a gitlink carries its pointer as its one body line in the
    same way. This helper returns the body count for the one
    shape whose blob is identical on both sides and returns
    None for every other entry, so a typechange whose bytes
    differ in any way at all keeps the count numstat gave it.
    """
    if entry["status"] != "typechange":
        return None
    base_data = file_bytes(
        repo, diff_base, entry["old_path"] or entry["path"]
    )
    head_data = file_bytes(repo, head, entry["path"])
    if base_data is None or head_data != base_data:
        return None
    return count_chunk_lines(precise_chunk)


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
        if not entry["binary"]:
            body_counts = identical_blob_typechange_counts(
                repo, diff_base, head, entry, precise.get(path, "")
            )
            if body_counts is not None and body_counts != (adds, dels):
                # The corrected count is the measure every later
                # reading of this change must stand on, so the
                # stats reading moves with the entry it names.
                adds, dels = body_counts
                stats[path] = body_counts
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
    A copy is judged from its destination alone. Its old path is
    not a former name of the copy at all. It is a different file
    that still stands in the tree under that name, with its own
    entry in the same packet, so a copy taken from an instruction
    file under a plain name is not itself an instruction file,
    while a copy taken to an instruction name is flagged on the
    strength of its own destination path.
    """
    if entry.get("status") == "copied":
        return is_instruction_path(entry.get("path"))
    return is_instruction_path(entry.get("path")) or \
        is_instruction_path(entry.get("old_path"))


def source_verb(entry):
    """The verb that names where an entry with an old path came from.

    A copied entry was copied from its source, which still stands
    in the tree. A renamed entry was renamed from its old name,
    which no longer stands. The two verbs are not interchangeable,
    so every surface that names a source takes the verb from the
    entry status rather than printing the rename wording for both.
    """
    return "copied" if entry.get("status") == "copied" else "renamed"


def source_line(entry):
    """The change tier source line for an entry with an old path."""
    return "%s from: %s" % (
        source_verb(entry).capitalize(),
        display_path(entry["old_path"]),
    )


def build_t0(files, commit_log, pr_info):
    lines = []
    lines.append("## T0 Triage")
    lines.append("")
    if pr_info is not None:
        lines.append("Pull request #%d: %s" % (pr_info["number"], pr_info["title"]))
        lines.append("")
        if pr_info.get("state"):
            lines.append(
                "Pull request state at fetch time: %s, recorded at %s. "
                "The state is a snapshot from that fetch and is not a "
                "live claim."
                % (pr_info["state"], pr_info.get("state_as_of", ""))
            )
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
                "- %s (%s%s, %s from %s)"
                % (display_path(entry["path"]), entry["status"], marker,
                   source_verb(entry),
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
            lines.append(source_line(entry))
        lines.append("")
        if entry["placeholder"] is not None:
            shown = entry["placeholder"]
        else:
            chunk = chunks.get(path, "")
            shown = chunk.rstrip() if chunk.strip() else "(no textual diff)"
        # The fence is sized by fence_for over the exact text it
        # fences, the same rule the triage tier fences stand
        # under. A diff body can itself hold a bare fence line,
        # as a context line of a Markdown file that holds a code
        # block, and a fixed three backtick fence would close
        # early on that line and desynchronise every reader that
        # tracks fence state, the packet check above all. A fence
        # one backtick longer than the longest run inside the
        # body cannot be closed from inside the body.
        fence = fence_for(shown)
        lines.append(fence + "diff")
        lines.append(shown)
        lines.append(fence)
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
    and leave the section reporting that no call sites exist. The
    textconv refusal stands on the call as well, so the search reads
    the bytes the tree holds and never a driver rewriting of them.
    """
    args = ["grep", "--no-textconv", "--text", "-n", "-z", "-w",
            "-e", term, head]
    if fixed:
        args = ["grep", "--no-textconv", "--text", "-n", "-z", "-w",
                "-F", "-e", term, head]
    result = run_git(
        repo, args, check=False, global_flags=["--attr-source=" + head]
    )
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
    args = ["grep", "--no-textconv", "--text", "-n", "-z", "-w", "-F"]
    for term in unique:
        args.extend(["-e", term])
    args.append(head)
    result = run_git(
        repo, args, check=False, global_flags=["--attr-source=" + head]
    )
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


def blame_git_dir(repo):
    """The absolute git directory of the repo, or None when unread.

    The blame reader runs against the git directory directly, so
    it needs the directory as a path of its own rather than as a
    working tree spelling.
    """
    result = run_git(
        repo, ["rev-parse", "--absolute-git-dir"], check=False
    )
    if result.returncode != 0:
        return None
    text = result.stdout.strip()
    return text or None


def run_blame(repo, git_dir, head, start, end, path):
    """One blame reading with its attribution sources confined.

    Blame applies a mailmap and an ignore revs file by default,
    and both can sit outside the change under review. A mailmap
    file named by clone configuration and a mailmap file standing
    untracked in the working tree rewrite the credited author,
    and a clone configuration ignore revs file moves the credit
    to a different commit, all with no trace in the packet. The
    reading therefore runs against the git directory from outside
    the working tree, where no untracked working tree mailmap is
    read, with the configuration mailmap file switched off, with
    the mailmap blob pinned to the mailmap file the reviewed
    head itself carries, which is reviewed content and stays in
    force, and with the ignore revs list cleared by the empty
    file name the blame flag provides for that clearing. When
    the git directory cannot be resolved the reading falls back
    to the ordinary wrapper with the same flag and file pins the
    wrapper can carry.
    """
    args = (
        ["blame", "--porcelain"] + DIFF_FLAGS
        + ["--ignore-revs-file", "",
           "-L", "%d,%d" % (start, end), head, "--", path]
    )
    if git_dir is None:
        return run_git(
            repo, args, check=False,
            global_flags=["-c", "mailmap.file="],
        )
    argv = (
        ["git", "--no-pager", "--no-replace-objects",
         "--literal-pathspecs", "--git-dir", git_dir,
         "--attr-source=" + head]
        + GIT_PIN
        + ["-c", "mailmap.file=",
           "-c", "mailmap.blob=" + head + ":.mailmap"]
        + args
    )
    return run_argv(argv, git_dir, False, "git blame")


def blame_section(repo, head, top_files, ranges_by_file, notes):
    lines = []
    lines.append("### Blame summary for changed ranges")
    lines.append("")
    range_count = 0
    git_dir = blame_git_dir(repo)
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
            result = run_blame(repo, git_dir, head, start, end, path)
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
                ["log"] + DIFF_FLAGS
                + ["-L", "%d,%d:%s" % (span[0], span[1], path),
                   "--format=commit %h %s", head],
                check=False,
                global_flags=["--attr-source=" + head],
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
    lines.append(
        "The states in this list are a snapshot from the fetch "
        "that built this packet. They are not refreshed after "
        "that fetch and they are not a live claim about any "
        "pull request."
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


FINDINGS_FORMAT_VERSION = "1"


def split_findings_header(text):
    """The header a findings file opens with, as a dict.

    The header stands in comment lines above the findings and
    names the format version, the head of the packet the file
    was written for, and the since anchor of that run, in this
    shape.

        # recognitio-findings 1
        # packet-head: <full commit hash>
        # since: <full commit hash, or none>

    A file with no such lines returns an empty dict. The lines
    are comments to the line parser below, so a file carrying a
    header still parses as findings, and the header is the only
    place the references live.
    """
    header = {}
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("# recognitio-findings"):
            header["version"] = line[len("# recognitio-findings"):].strip()
        elif line.startswith("# packet-head:"):
            header["packet_head"] = line[len("# packet-head:"):].strip()
        elif line.startswith("# since:"):
            header["since"] = line[len("# since:"):].strip()
        elif line.startswith("#") or not line:
            continue
        else:
            break
    return header


def findings_header_problems(text, head, since):
    """Problems with a findings file header against one run.

    A findings file that carries findings must open with a
    header naming the packet head and the since anchor it was
    written for, and both must name this run. A file written
    for another packet, another head, or another anchor is a
    foreign file here, however plausible its lines look, and a
    file with no header at all names no run, so its findings
    cannot be told apart from a foreign file either. A file
    that carries a header is judged by it even when it carries
    no findings. A file with neither a header nor findings is
    an empty findings file and stands as one.
    """
    header = split_findings_header(text)
    findings = parse_findings(text)
    if not header:
        if findings:
            return [
                "the findings file carries no header naming the "
                "packet head and since anchor it was written for, "
                "so its findings cannot be tied to this run"
            ]
        return []
    problems = []
    if header.get("version") != FINDINGS_FORMAT_VERSION:
        problems.append(
            "the findings file header names format version %r, "
            "which this extractor does not read"
            % header.get("version")
        )
    if header.get("packet_head") != head:
        problems.append(
            "the findings file was written for packet head %s, "
            "which is not the head of this run %s"
            % (header.get("packet_head"), head)
        )
    wanted_since = since if since is not None else "none"
    if header.get("since") != wanted_since:
        problems.append(
            "the findings file was written for since anchor %s, "
            "which is not the since anchor of this run %s"
            % (header.get("since"), wanted_since)
        )
    return problems


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
        ["diff", "--histogram", "--find-renames", "--find-copies", "--find-copies-harder", "-U0"]
        + DIFF_FLAGS + [since, head],
        global_flags=["--attr-source=" + head],
    ).stdout
    status_text = run_git(
        repo, ["diff", "--name-status", "-z", "-M", "-C", "--find-copies-harder"] + DIFF_FLAGS
        + [since, head], global_flags=["--attr-source=" + head]
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
    chunks = pair_diff_chunks(since_files, split_diff(precise))
    ranges_by_path = {}
    moved_to = {}
    for entry in since_files:
        if entry["status"] == "copied":
            # A copied entry carries its source as its old path and
            # its chunk describes the delta between the source at
            # the previous revision and the copy at the head. Those
            # ranges are not edits to the source file, so a copy
            # writes no ranges under its source path and it never
            # overwrites the ranges the source file its own
            # modification wrote there.
            continue
        chunk = chunks.get(entry["path"], "")
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
        # The fallback stat stands under the same pins as every
        # other diff reading, and its widths are pinned in its
        # argument list, because the width family has no working
        # config form a pin list could carry on the measured git.
        # The widths are the values
        # git itself defaults to away from a terminal, so a clean
        # reading is unchanged and a configured width in the
        # checking clone cannot reshape the fallback text.
        delta = run_git(
            repo,
            ["diff", "--histogram", "--stat", "--stat-width=80",
             "--stat-name-width=50", "--stat-graph-width=30"]
            + DIFF_FLAGS + ["%s...%s" % (since, head)],
            global_flags=["--attr-source=" + head],
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


def manifest_bytes(manifest):
    text = json.dumps(manifest, indent=2) + "\n"
    return text.encode("utf-8")


def budget_from_argv(argv):
    """The budget a run was given, read back from its own arguments.

    The last budget flag wins, the way the argument parser reads
    it. A value that is not an integer, or no flag at all, records
    as no budget, because a failure receipt must not invent the
    number it receipts.
    """
    budget = None
    items = list(argv)
    for index, item in enumerate(items):
        if item == "--budget" and index + 1 < len(items):
            try:
                budget = int(items[index + 1])
            except ValueError:
                budget = None
        elif item.startswith("--budget="):
            try:
                budget = int(item.split("=", 1)[1])
            except ValueError:
                budget = None
    return budget


def build_failure_manifest(argv, message, resolved=None, tiers=None,
                           budget_block=None):
    """The receipt a failed run leaves, specific about its own cause.

    The budget block records the budget the run was given, in the
    shape the manifest schema allows, and never the fixed none and
    zero the writer once hardcoded for every failure. When the
    caller measured the tiers before the run failed, the tier
    account it measured stands in the receipt as well, so a reader
    who keeps only the receipt can see what each tier would have
    cost. A caller that failed before any tier was measured leaves
    the tier account empty, because those costs were never known.
    """
    if budget_block is None:
        budget_block = {
            "budget_tokens": budget_from_argv(argv),
            "estimated_tokens": 0,
            "dropped": [],
        }
    manifest = base_manifest(argv)
    manifest.update({
        "mode": resolved["mode"] if resolved else None,
        "label": resolved["label"] if resolved else None,
        "base": resolved["base"] if resolved else None,
        "head": resolved["head"] if resolved else None,
        "merge_base": resolved["merge_base"] if resolved else None,
        "since": resolved["since"] if resolved else None,
        "files": [],
        "tiers": tiers if tiers is not None else {},
        "budget": budget_block,
        "cap_notes": [],
        "exclusions": [],
        "verified": False,
        "error": message,
        "discrepancies": [message],
    })
    return manifest


class OutputRefusal(Exception):
    """The output location cannot be written, with the reason named."""


class OutputTarget:
    """One output directory, pinned once and written under a lock.

    The path is resolved a single time, before any input is read, so a
    link swapped while the run builds cannot redirect the writes to a
    different directory. The directory itself is opened once the run
    is ready to build and the descriptor is held for the rest of the
    run, so the writes land in the directory the run opened even if a
    path component above it is renamed afterwards. The finished pair
    is staged under temporary names inside that directory and renamed
    over the final names, so no reader can meet a torn file, and a
    link standing at a final name is replaced as a link rather than
    followed to a file outside the directory. An exclusive lock keyed
    on the pinned path is held from the build to the publish, so a
    second run naming the same directory is refused instead of
    interleaving its writes with the first.
    """

    def __init__(self, pinned):
        self.path = pinned
        self.lock_fd = None
        self.dir_fd = None

    def acquire_lock(self):
        if fcntl is None or self.lock_fd is not None:
            return
        digest = hashlib.sha256(
            str(self.path).encode("utf-8")
        ).hexdigest()
        lock_path = Path(tempfile.gettempdir()) / (
            "recognitio-out-%s.lock" % digest[:32]
        )
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
        except OSError as exc:
            raise OutputRefusal(
                "cannot take the output lock for %s because %s"
                % (self.path, exc.strerror or exc)
            ) from exc
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(fd)
            raise OutputRefusal(
                "another recognitio run is already writing to the "
                "output directory %s. Wait for it to finish or pick "
                "another output directory" % self.path
            )
        except OSError as exc:
            os.close(fd)
            raise OutputRefusal(
                "cannot take the output lock for %s because %s"
                % (self.path, exc.strerror or exc)
            ) from exc
        self.lock_fd = fd

    def open_dir(self):
        if self.dir_fd is not None:
            return
        try:
            self.path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise OutputRefusal(
                "cannot prepare the output directory %s because %s. "
                "Fix the path or pick another output directory"
                % (self.path, exc.strerror or exc)
            ) from exc
        try:
            info = os.lstat(self.path)
        except OSError as exc:
            raise OutputRefusal(
                "cannot prepare the output directory %s because %s. "
                "Fix the path or pick another output directory"
                % (self.path, exc.strerror or exc)
            ) from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise OutputRefusal(
                "cannot prepare the output directory %s because it is "
                "not a directory. Fix the path or pick another output "
                "directory" % self.path
            )
        try:
            self.dir_fd = os.open(
                self.path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            )
        except OSError as exc:
            raise OutputRefusal(
                "cannot open the output directory %s because %s. "
                "Fix the path or pick another output directory"
                % (self.path, exc.strerror or exc)
            ) from exc

    def close(self):
        for attr in ("dir_fd", "lock_fd"):
            fd = getattr(self, attr)
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
                setattr(self, attr, None)

    def _verify_still_pinned(self):
        """Refuse a publish if the pinned path stopped naming this dir.

        The descriptor pins the writes, but a directory renamed aside
        and replaced at its path during the build would leave the
        success line naming a path that no longer holds the packet.
        Comparing the path identity with the descriptor identity at
        publish time turns that swap into a refusal instead.
        """
        try:
            current = os.stat(self.path)
            opened = os.fstat(self.dir_fd)
        except OSError as exc:
            raise OutputRefusal(
                "the output directory %s could not be rechecked "
                "because %s, so nothing was published"
                % (self.path, exc.strerror or exc)
            ) from exc
        if (current.st_dev, current.st_ino) != (
                opened.st_dev, opened.st_ino):
            raise OutputRefusal(
                "the output directory %s was moved or replaced "
                "while the run was building, so nothing was "
                "published at that path" % self.path
            )

    def _check_names(self, names):
        """Refuse before any mutation when a final name cannot move."""
        for name in names:
            try:
                info = os.stat(
                    name, dir_fd=self.dir_fd, follow_symlinks=False
                )
            except FileNotFoundError:
                continue
            except OSError as exc:
                raise OutputRefusal(
                    "cannot replace %s in the output directory %s "
                    "because %s. Move it aside or pick another output "
                    "directory"
                    % (name, self.path, exc.strerror or exc)
                ) from exc
            if not (stat.S_ISREG(info.st_mode)
                    or stat.S_ISLNK(info.st_mode)):
                raise OutputRefusal(
                    "cannot replace %s in the output directory %s "
                    "because it is not a regular file. Move it aside "
                    "or pick another output directory"
                    % (name, self.path)
                )

    def _stage(self, hint, data):
        """Write one finished file under a temporary name in place."""
        temp_name = ".recognitio-tmp-%d-%s" % (os.getpid(), hint)
        try:
            fd = os.open(
                temp_name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL
                | getattr(os, "O_NOFOLLOW", 0),
                0o644,
                dir_fd=self.dir_fd,
            )
        except OSError as exc:
            raise OutputRefusal(
                "cannot stage the %s in the output directory %s "
                "because %s" % (hint, self.path, exc.strerror or exc)
            ) from exc
        try:
            view = memoryview(data)
            while view:
                written = os.write(fd, view)
                view = view[written:]
            os.fsync(fd)
        except OSError as exc:
            raise OutputRefusal(
                "cannot stage the %s in the output directory %s "
                "because %s" % (hint, self.path, exc.strerror or exc)
            ) from exc
        finally:
            os.close(fd)
        return temp_name

    def _discard(self, temp_name):
        try:
            os.unlink(temp_name, dir_fd=self.dir_fd)
        except OSError:
            pass

    def _discard_stale_temps(self):
        """Drop staging files a killed run left in the directory.

        The publish lock is held here, so a staging file can only
        belong to a run that died between staging and renaming.
        Leaving one behind would make the packet directory carry an
        entry no manifest receipts.
        """
        try:
            entries = os.listdir(self.dir_fd)
        except OSError:
            return
        for entry in entries:
            if entry.startswith(".recognitio-tmp-"):
                self._discard(entry)

    def _replace(self, temp_name, final_name):
        try:
            os.replace(
                temp_name, final_name,
                src_dir_fd=self.dir_fd, dst_dir_fd=self.dir_fd,
            )
        except OSError as exc:
            raise OutputRefusal(
                "cannot move the finished %s into place in the output "
                "directory %s because %s"
                % (final_name, self.path, exc.strerror or exc)
            ) from exc

    def publish_pair(self, packet_data, manifest):
        """Move a finished packet and manifest into place together."""
        self.open_dir()
        self._verify_still_pinned()
        self._check_names(("packet.md", "manifest.json"))
        self._discard_stale_temps()
        temp_packet = self._stage("packet.md", packet_data)
        try:
            temp_manifest = self._stage(
                "manifest.json", manifest_bytes(manifest)
            )
        except OutputRefusal:
            self._discard(temp_packet)
            raise
        try:
            self._replace(temp_packet, "packet.md")
            self._replace(temp_manifest, "manifest.json")
        finally:
            self._discard(temp_packet)
            self._discard(temp_manifest)
        os.fsync(self.dir_fd)

    def _standing_verified(self):
        """Whether the directory holds a standing verified packet.

        A standing packet is a packet file beside a manifest file
        whose own verified flag reads true. Anything else standing
        there, a torn pair, an unreadable manifest or a manifest
        that claims no verification, is not a packet a later run
        must preserve.
        """
        try:
            packet_info = os.stat(
                "packet.md", dir_fd=self.dir_fd, follow_symlinks=False
            )
            if not stat.S_ISREG(packet_info.st_mode):
                return False
            fd = os.open(
                "manifest.json", os.O_RDONLY, dir_fd=self.dir_fd
            )
        except OSError:
            return False
        try:
            with os.fdopen(fd, "rb") as handle:
                data = handle.read()
        except OSError:
            return False
        try:
            manifest = json.loads(data.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return False
        return isinstance(manifest, dict) and manifest.get(
            "verified"
        ) is True

    def publish_failure(self, argv, message, resolved=None, tiers=None,
                        budget_block=None, preserve_verified=False):
        """Replace the old packet with a failure receipt, or nothing.

        Both final names are checked before either is touched, so a
        blocked name leaves the directory exactly as it stood instead
        of half cleared. A caller that passes preserve_verified, as
        the budget refusal path does, never replaces a standing
        verified packet with a failure receipt, and the directory
        is left exactly as it stood while the refusal itself is
        still printed by the caller. The method returns True when
        a receipt was published and False when a standing packet
        was preserved.
        """
        self.open_dir()
        self._verify_still_pinned()
        if preserve_verified and self._standing_verified():
            return False
        self._check_names(("packet.md", "manifest.json"))
        self._discard_stale_temps()
        manifest = build_failure_manifest(
            argv, message, resolved, tiers=tiers,
            budget_block=budget_block,
        )
        temp_manifest = self._stage(
            "manifest.json", manifest_bytes(manifest)
        )
        try:
            try:
                os.unlink("packet.md", dir_fd=self.dir_fd)
            except FileNotFoundError:
                pass
            except OSError as exc:
                raise OutputRefusal(
                    "cannot clear the old packet in the output "
                    "directory %s because %s"
                    % (self.path, exc.strerror or exc)
                ) from exc
            self._replace(temp_manifest, "manifest.json")
        finally:
            self._discard(temp_manifest)
        os.fsync(self.dir_fd)
        return True


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="extract.py",
        description="Assemble a verified recognitio review packet from a local clone.",
    )
    parser.add_argument(
        "--version", action="version",
        version="recognitio extract.py %s" % EXTRACTOR_VERSION,
        help="print the extractor version and exit",
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
        help="file of prior findings with its format header, one finding per line anchored as path:line: text",
    )
    parser.add_argument(
        "--budget", type=int, default=None,
        help=(
            "approximate token budget, counted with the per shape "
            "token estimate priced by character class"
        ),
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
    if args.budget is not None and args.budget < 1:
        parser.error(
            "--budget must be at least 1, the minimum a manifest "
            "can record"
        )
    try:
        args.tiers_selected = parse_tier_selection(args.tiers)
    except ValueError as exc:
        parser.error(str(exc))
    return args


def load_findings(args, resolved=None):
    """Read and parse the findings file, or an empty list without one.

    When the run it feeds is resolved, the file header is read
    against that run and a file written for another packet
    head or another since anchor is refused before any packet
    is built, and the hash of the file bytes is recorded on
    the args for the manifest, so the packet check can judge
    the file the run actually used.
    """
    if not args.findings:
        # A run with no findings file records no findings hash,
        # even where a reused args object still carries the hash
        # an earlier findings run set on it.
        args.findings_sha256 = None
        return []
    try:
        findings_bytes = Path(args.findings).read_bytes()
    except OSError as exc:
        raise GitError("cannot read the findings file: %s" % exc)
    args.findings_sha256 = hashlib.sha256(findings_bytes).hexdigest()
    findings_text = findings_bytes.decode(
        encoding="utf-8", errors="surrogateescape"
    )
    if resolved is not None:
        problems = findings_header_problems(
            findings_text, resolved["head"], resolved["since"]
        )
        if problems:
            raise GitError(problems[0])
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

    Returns the drop list, a failure message when no drop set
    fits, and a failure account naming the measured core size and
    the tier account and budget block a failure receipt must
    carry. The change itself is never truncated.

    The choice among drop sets is cost aware. Every candidate
    drop set is measured by assembling the packet it would emit
    and settling its token estimate, the same fixed point the
    shipped packet is measured at, so a packet the budget accepts
    is a packet that measures inside the budget. Among the drop
    sets that fit, the run keeps the set whose kept optional
    tiers carry the most estimated tokens, so a budget that fits
    the small tier whole never sheds it just because the fixed
    order reached it first. At equal kept size the documented
    order breaks the tie, history before companions, which keeps
    the equal cost behaviour the old fixed order produced. The
    one limit that remains is tier granularity, because a tier is
    kept whole or dropped whole, so the unspent remainder of an
    accepted packet is always smaller than the smallest marginal
    cost of restoring one dropped tier on its own. A fixed
    allowance for the closing receipt undercounted it whenever
    the section grew, drop lines and all, and let emitted packets
    land over the budget they were accepted under. The
    measurement reads the verified form of the packet. A packet
    that goes on to fail verification is a failure artifact at
    exit 3, not a packet presented as ready, and its discrepancy
    list can carry it past the budget.
    """
    dropped = []
    if args.budget is None:
        return dropped, None, None

    def candidate_drops(names):
        return [
            {"tier": tier, "reason": reason}
            for tier in ("T3", "T2") if tier in names
        ]

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
    sizes = {
        tier: estimate_tokens(tier_texts[tier])
        for tier in ("T0", "T1", "T2", "T3")
    }
    core_candidate = candidate_drops(set(optional))
    core = measure(core_candidate)
    if core > args.budget:
        rest = core - sizes["T0"] - sizes["T1"]
        message = (
            "The smallest packet this selection can emit measures "
            "about %d tokens, over the budget of %d. That packet "
            "carries T0 at about %d tokens and T1 at about %d "
            "tokens, with the header and the contents and the "
            "receipts and any re-review section making up the "
            "remaining about %d tokens, and it has already shed "
            "every optional tier the selection gathered. The "
            "change itself is never truncated. Raise the budget "
            "or split the change."
            % (core, args.budget, sizes["T0"], sizes["T1"], rest)
        )
        failure_tiers = tier_accounting(
            selected, set(optional), tier_texts, tier_files
        )
        failure_block = {
            "budget_tokens": args.budget,
            "estimated_tokens": core,
            "dropped": core_candidate,
        }
        return dropped, message, (failure_tiers, failure_block)
    candidates = []
    for names in (
        set(),
        {"T3"},
        {"T2"},
        {"T3", "T2"},
    ):
        names = names & set(optional)
        candidate = candidate_drops(names)
        if any(
            [item["tier"] for item in candidate]
            == [item["tier"] for item in kept]
            for kept in candidates
        ):
            continue
        if measure(candidate) <= args.budget:
            candidates.append(candidate)
    def kept_tokens(candidate):
        dropped_names = {item["tier"] for item in candidate}
        return sum(
            sizes[tier] for tier in optional if tier not in dropped_names
        )

    def tie_rank(candidate):
        dropped_names = {item["tier"] for item in candidate}
        if dropped_names == {"T3"}:
            return 0
        if dropped_names == {"T2"}:
            return 1
        if not dropped_names:
            return 0
        return 2

    best = min(
        candidates,
        key=lambda candidate: (
            -kept_tokens(candidate), tie_rank(candidate),
        ),
    )
    return best, None, None


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
                      discrepancies, prior_passage=None):
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
                "state": resolved["pr"].get("state", "unknown"),
                "state_as_of": resolved["pr"].get("state_as_of", ""),
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
        "findings_sha256": getattr(args, "findings_sha256", None),
        "prior_pull_requests_passage": prior_passage,
    })
    return manifest


def run_pipeline(args, repo, target, argv, prepared=None):
    if prepared is not None:
        resolved, findings, change = prepared
    else:
        resolved = resolve_inputs(repo, args)
        findings = load_findings(args, resolved)
        change = None
    diff_base = resolved["merge_base"]
    if diff_base is None:
        diff_base = EMPTY_TREE
    head = resolved["head"]

    if change is None:
        change = fetch_change(repo, diff_base, head)
    files = change["files"]
    if not files:
        message = "the resolved change is empty, no packet was built"
        target.publish_failure(argv, message, resolved)
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
    dropped, failure, failure_account = apply_budget(
        args, selected, tier_texts, tier_files, rereview,
        header_provisional, counts
    )
    if failure is not None:
        failure_tiers, failure_block = failure_account
        target.publish_failure(
            argv, failure, resolved, tiers=failure_tiers,
            budget_block=failure_block, preserve_verified=True,
        )
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
        prior_passage=(
            prior_prs_passage(tier_texts["T3"])
            if "T3" in selected else None
        ),
    )

    target.publish_pair(
        packet.encode("utf-8", "surrogateescape"), manifest
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
        % (target.path, len(files))
    )
    return 0


def _git_read(path, *args):
    """One pinned git read against a path, or None when it fails.

    The reader carries the same pin list and the same literal
    pathspecs flag as every other invocation, so the written
    claim that every invocation runs pinned holds for this
    helper as well and not only for the main wrapper.
    """
    try:
        result = run_process(
            ["git", "--no-pager", "--no-replace-objects",
             "--literal-pathspecs",
             "-C", str(path)] + GIT_PIN + list(args)
        )
    except GitError:
        # A read that cannot run proves nothing about the path, and
        # the input resolution that follows reports the same failure
        # in the run voice. This probe must never be the traceback.
        return None
    if result.returncode != 0:
        return None
    return decode_bytes(result.stdout).strip()


def refuse_tracked_output_root(target):
    """Refuse an output directory that is a working tree root.

    A run pointed at the root of a working tree would replace files
    named packet.md and manifest.json that the tree tracks as its own
    content, and deleting tracked work is never a packet operation.
    The check reads only, so a refused run leaves the tree untouched.
    A directory that is not the root of a working tree, including a
    bare repository root, is not refused by this rule.
    """
    pinned = target.path
    if not pinned.is_dir():
        return
    toplevel = _git_read(pinned, "rev-parse", "--show-toplevel")
    if toplevel is None:
        return
    if Path(toplevel).resolve() != pinned:
        return
    tracked = _git_read(
        pinned, "ls-files", "--", "packet.md", "manifest.json"
    )
    if not tracked:
        return
    names = ", ".join(sorted(tracked.splitlines()))
    raise OutputRefusal(
        "the output directory %s is the root of a git working tree "
        "and the tracked files %s stand there. A packet run must not "
        "replace tracked files, so pick another output directory "
        "and nothing was written" % (pinned, names)
    )


def publish_failure_quietly(target, argv, message, resolved=None):
    """Leave a failure receipt where one can be left, else say why."""
    try:
        target.publish_failure(argv, message, resolved)
    except OutputRefusal as exc:
        print("recognitio: %s" % exc, file=sys.stderr)


def main(argv=None):
    raw_argv = list(sys.argv[1:]) if argv is None else list(argv)
    # Argument checking completes before any output path is touched.
    # A rejection, a help print and a version print all leave every
    # named output directory exactly as it stood, so the specific
    # message argparse prints is the whole record of an argument
    # failure and no generic receipt overwrites it or the packet.
    args = parse_args(argv)
    repo = Path(args.repo).resolve()
    target = OutputTarget(Path(args.out).resolve())
    try:
        refuse_tracked_output_root(target)
        # The inputs are resolved and read before the output
        # directory is opened or locked. Only a run whose arguments
        # and inputs stood up reaches the build, and only the build
        # and its publish ever write into the directory.
        try:
            resolved = resolve_inputs(repo, args)
            findings = load_findings(args, resolved)
            diff_base = resolved["merge_base"]
            if diff_base is None:
                diff_base = EMPTY_TREE
            change = fetch_change(repo, diff_base, resolved["head"])
        except GitError as exc:
            try:
                target.acquire_lock()
            except OutputRefusal as lock_exc:
                print("recognitio: %s" % lock_exc, file=sys.stderr)
            else:
                publish_failure_quietly(target, raw_argv, str(exc))
            print("recognitio: %s" % exc, file=sys.stderr)
            return 2
        try:
            target.acquire_lock()
            target.open_dir()
        except OutputRefusal as exc:
            print("recognitio: %s" % exc, file=sys.stderr)
            return 2
        try:
            return run_pipeline(
                args, repo, target, raw_argv,
                prepared=(resolved, findings, change),
            )
        except GitError as exc:
            publish_failure_quietly(target, raw_argv, str(exc))
            print("recognitio: %s" % exc, file=sys.stderr)
            return 2
        except OutputRefusal as exc:
            print("recognitio: %s" % exc, file=sys.stderr)
            return 2
    except OutputRefusal as exc:
        print("recognitio: %s" % exc, file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print(
            "recognitio: the run was interrupted and no packet was "
            "published, so whatever already stood in the output "
            "directory %s was left untouched" % target.path,
            file=sys.stderr,
        )
        return 130
    finally:
        target.close()


if __name__ == "__main__":
    sys.exit(main())
