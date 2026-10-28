#!/usr/bin/env python3
"""Validate a recognitio packet directory before a review is stamped.

A gate report may only cite a packet that is whole. This script is the
mechanical form of that rule, and it verifies rather than trusts. The
manifest is read with a strict reader that refuses a repeated key and
is validated against the packet manifest schema that ships beside
this script, so a forged, stripped or extra key manifest fails before
anything else is read. A manifest that claims verified while carrying
a non empty discrepancies list fails on its own words. The recorded
refs are then checked against the repository itself. The head must
be the current head of the repository the review is being stamped
against, the recorded merge base must be the merge base git itself
computes for the recorded base and head, and a caller who names the
range under review with the expect flags gets a stamp for that range
and no other. The change is then recounted from the repository with
the extractor's own fetch and measurement code, loaded from the
canonical skill, and every manifest file record and exclusion
receipt must equal the recount field for field. The extractor's own
recount must also agree with the manifest it is handed. Last, the
packet body is read against the manifest. The header identity lines,
the contents totals, the triage file list and numstat block, the
change tier file sections with their status lines and diff bodies,
the tier receipts and token estimates, and the closing recount
receipt must all agree with the manifest and with the recount, and
the change tier must hold exactly one section per manifest file
record, no more and no fewer. The packet directory itself is read
as a sealed pair, so a packet or a manifest that arrives through a
symbolic link, and any further entry standing in the directory,
including a whole nested packet, fail the stamp, because the stamp
covers the pair that lives in the directory and nothing else. The
packet is decoded as strict UTF-8, because a packet holding bytes
no UTF-8 reader can open is not the document its consumers are
handed. The recorded extractor command is also read back, so its
mode flag must name the mode the manifest records and any full
hash it carries must name the refs the manifest records. The
second pass over this verifier widened that reading. The recorded
command is now read at the last value of every flag, the way the
extractor parser reads it, and its budget and tiers and findings
values are pinned against the manifest. The range label is pinned
against the recorded range spelling. The re-review section and
the pull request preamble are rebuilt from the repository and
from the records they stand on and compared whole, as the header
and the contents block and the closing recount now are. The
manifest cap notes list and the size of a dropped tier are
recounted in the rebuild, the budget account is checked against
its own rules, and the creation time must be a timestamp that
does not name a moment after the check. The repository itself is
read for state, so a shallow clone refuses the stamp in its own
words and a rebase in progress is named. A packet or a manifest
standing as a hard link fails for the reason a symbolic link
fails.

Exits nonzero and lists every problem when the packet cannot be used.
"""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# The same discipline the extractor runs under. Git location
# variables are scrubbed from the child environment, replace objects
# are refused twice over, and the child gets a timeout, because this
# script reads the head a review is being stamped against and a
# redirected or swapped read would stamp against the wrong head and
# still print verified.
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
# The same driver and configuration scrub the extractor runs under.
# Configuration supplied through the environment can define a driver
# program outright, and the remaining names hand a child process a
# program to run in place of its pager or its own subcommands.
GIT_DRIVER_ENV_VARS = (
    "GIT_EXTERNAL_DIFF",
    "GIT_DIFF_OPTS",
    "GIT_PAGER",
    "GIT_EXEC_PATH",
)
GIT_CONFIG_ENV_PREFIX = "GIT_CONFIG"
# The same attribute source and pathspec mode scrub the extractor
# runs under, so a recount in this script reads the reviewed tree
# and nothing the caller environment names beside it.
GIT_ATTR_ENV_VARS = (
    "GIT_ATTR_SOURCE",
    "GIT_ATTR_GLOBAL",
    "GIT_ATTR_SYSTEM",
)
GIT_PATHSPEC_ENV_VARS = (
    "GIT_LITERAL_PATHSPECS",
    "GIT_GLOB_PATHSPECS",
    "GIT_ICASE_PATHSPECS",
    "GIT_NOGLOB_PATHSPECS",
)
# The same output pins the extractor carries, so the small reads
# this script makes on its own run under the discipline its header
# claims for every invocation and not only through the recount
# the extractor code performs.
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
    "-c", "diff.renameLimit=0",
    "-c", "diff.algorithm=histogram",
    "-c", "diff.ignoreSubmodules=none",
    "-c", "diff.submodule=short",
    "-c", "core.abbrev=7",
    "-c", "i18n.logOutputEncoding=UTF-8",
    "-c", "core.attributesFile=",
    "-c", "attr.tree=",
]
PROCESS_TIMEOUT_SECONDS = 120
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
SCHEMA_PATH = Path(__file__).resolve().parent / "packet-manifest.schema.json"
EXTRACTOR_PATH = (
    Path(__file__).resolve().parents[1]
    / ".agents" / "skills" / "recognitio" / "scripts" / "extract.py"
)


def scrubbed_child_env():
    """The environment the git child process runs under."""
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in GIT_SCRUB_VARS
        and key not in GIT_DRIVER_ENV_VARS
        and key not in GIT_ATTR_ENV_VARS
        and key not in GIT_PATHSPEC_ENV_VARS
        and not key.startswith(GIT_CONFIG_ENV_PREFIX)
    }
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    env["GIT_ATTR_NOSYSTEM"] = "1"
    return env


def run_git(repo, args):
    """Run one pinned git read and return its stdout or None."""
    try:
        result = subprocess.run(
            ["git", "--no-pager", "--no-replace-objects",
             "--literal-pathspecs",
             "-C", str(repo)] + GIT_PIN + list(args),
            capture_output=True,
            text=True,
            env=scrubbed_child_env(),
            timeout=PROCESS_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def current_head(repo):
    out = run_git(repo, ["rev-parse", "HEAD"])
    return out.strip() if out is not None else None


class DuplicateKeyError(ValueError):
    """A JSON object that carries one key twice."""


def _reject_duplicate_keys(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise DuplicateKeyError("repeated key %r" % (key,))
        obj[key] = value
    return obj


def strict_json_loads(text):
    """Parse JSON while refusing a repeated key at any depth.

    A plain reader resolves a repeated key to its last value, so a
    manifest that carries verified twice, first false and then true,
    reads as verified. The fanout validator already refuses such a
    file, and the packet check now reads the manifest the same way,
    so one artefact cannot read verified here and corrupt there.
    """
    return json.loads(text, object_pairs_hook=_reject_duplicate_keys)


# ---------------------------------------------------------------------
# The manifest schema and a small validator for the subset it uses.
# The gate takes no third party dependencies, so the validator is a
# short walk over the schema rather than a library call. It covers
# the keywords the shipped schema uses and refuses anything else by
# ignoring nothing that could hide a bad manifest. Unknown keywords
# in the schema itself are a schema authoring error and are reported
# by the schema load check in the tests rather than at stamp time.
# ---------------------------------------------------------------------

_SCHEMA_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "null": type(None),
}


def _pattern_matches(pattern, value):
    """Match one schema pattern against one manifest string.

    A pattern the schema anchors at both ends is a claim about the
    whole value, so it is matched against the whole value. The end
    anchor alone accepts a trailing newline, because it also
    matches just before one, and a hash or a status code carrying
    a newline is not the shape the schema describes. A pattern
    anchored only at the start is a prefix claim and keeps the
    search reading the schema gives it.
    """
    if len(pattern) > 1 and pattern.startswith("^") \
            and pattern.endswith("$"):
        return re.fullmatch(pattern[1:-1], value) is not None
    return re.search(pattern, value) is not None


def _type_matches(value, name):
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, _SCHEMA_TYPES[name])


def _resolve_ref(schema, root_schema):
    ref = schema.get("$ref")
    if not ref:
        return schema
    if not ref.startswith("#/$defs/"):
        return schema
    target = root_schema.get("$defs", {}).get(ref[len("#/$defs/"):])
    merged = dict(target) if isinstance(target, dict) else {}
    for key, value in schema.items():
        if key != "$ref":
            merged[key] = value
    return merged


def schema_problems_at(value, schema, root_schema, where):
    """Validate one value against one schema node."""
    problems = []
    schema = _resolve_ref(schema, root_schema)
    if "anyOf" in schema:
        branches = schema["anyOf"]
        if not any(
            not schema_problems_at(value, branch, root_schema, where)
            for branch in branches
        ):
            problems.append(
                "the manifest value at %s matches none of the shapes "
                "its schema allows, and the value is %s"
                % (where, ascii(value)[:80])
            )
        return problems
    if "const" in schema and value != schema["const"]:
        problems.append(
            "the manifest value at %s is not the one value its "
            "schema allows" % where
        )
    if "enum" in schema and value not in schema["enum"]:
        problems.append(
            "the manifest value at %s is outside the set its schema "
            "allows" % where
        )
    declared = schema.get("type")
    if declared is not None and not _type_matches(value, declared):
        problems.append(
            "the manifest value at %s has the wrong type for its "
            "schema" % where
        )
        return problems
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            problems.append(
                "the manifest text at %s is shorter than its schema "
                "allows" % where
            )
        if "pattern" in schema and not _pattern_matches(
            schema["pattern"], value
        ):
            problems.append(
                "the manifest text at %s does not match the shape its "
                "schema requires" % where
            )
    if isinstance(value, int) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            problems.append(
                "the manifest number at %s is below the floor its "
                "schema sets" % where
            )
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            problems.append(
                "the manifest list at %s is shorter than its schema "
                "allows" % where
            )
        if schema.get("uniqueItems"):
            seen = []
            for item in value:
                if item in seen:
                    problems.append(
                        "the manifest list at %s repeats an entry "
                        "its schema requires to be unique" % where
                    )
                    break
                seen.append(item)
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                problems.extend(schema_problems_at(
                    item, item_schema, root_schema,
                    "%s[%d]" % (where, index),
                ))
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                problems.append(
                    "the manifest is missing a key its schema "
                    "requires, %s" % key
                )
        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, item in value.items():
            if key in properties:
                problems.extend(schema_problems_at(
                    item, properties[key], root_schema,
                    "%s.%s" % (where, key),
                ))
            elif additional is False:
                problems.append(
                    "the manifest carries a key its schema does not "
                    "allow, %s" % key
                )
            elif isinstance(additional, dict):
                problems.extend(schema_problems_at(
                    item, additional, root_schema, "%s.%s" % (where, key)
                ))
    return problems


def manifest_schema_problems(manifest):
    """Validate a manifest against the schema shipped in the tree."""
    try:
        schema = strict_json_loads(
            SCHEMA_PATH.read_text(encoding="utf-8")
        )
    except (OSError, ValueError) as exc:
        return [
            "the packet manifest schema cannot be read, so no "
            "manifest can be validated against it (%s)" % exc
        ]
    return schema_problems_at(manifest, schema, schema, "the manifest")


CREATED_ALLOWANCE_SECONDS = 3600


def parse_timestamp(value):
    """Parse one recorded timestamp, or return None."""
    if not isinstance(value, str) or "T" not in value:
        return None
    try:
        parsed = datetime.fromisoformat(
            value[:-1] + "+00:00" if value.endswith("Z") else value
        )
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed


def head_committer_time(repo, head):
    """The committer time of the recorded head, or None."""
    if repo is None or not isinstance(head, str):
        return None
    out = run_git(repo, ["show", "-s", "--format=%ct", head])
    if out is None:
        return None
    try:
        return datetime.fromtimestamp(int(out.strip()), timezone.utc)
    except (ValueError, OverflowError, OSError):
        return None


def created_problems(manifest, repo=None):
    """Check the recorded creation time against the repository.

    The true creation time cannot be verified against a
    repository, and the schema only types the field. The shapes
    a stamp must still refuse are the ones no clock reading can
    take and the ones the repository itself refutes. A value
    that is not an ISO timestamp, a value no UTF-8 reader can
    encode, and a value with no offset are none of them times a
    run could have recorded. A value that names a moment before
    the recorded head commit existed is a time the repository
    in the checker hands proves impossible, because a packet
    cannot have been extracted from a commit before that commit
    was committed. A value that names a moment after the check
    itself runs claims a creation that has not happened. Both
    bounds carry the same stated allowance of one hour for clock
    skew between the machine that committed the head, the
    machine that ran the extraction and the machine that runs
    this check, and that allowance replaces the earlier one day
    of silent grace. The pull request state fetch time recorded
    in the pull request record is held inside the same bounds,
    because that fetch happened inside the same run.
    """
    problems = []
    value = manifest.get("created_utc")
    if not isinstance(value, str):
        return problems
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        problems.append(
            "the manifest creation time cannot be encoded as "
            "UTF-8, so it is not a timestamp any consumer can read"
        )
        return problems
    parsed = None
    if "T" in value:
        try:
            parsed = datetime.fromisoformat(
                value[:-1] + "+00:00" if value.endswith("Z") else value
            )
        except ValueError:
            parsed = None
    if parsed is None:
        problems.append(
            "the manifest creation time %s is not an ISO timestamp, "
            "so the field records no time at all" % ascii(value)[:60]
        )
        return problems
    if parsed.tzinfo is None:
        problems.append(
            "the manifest creation time carries no offset, so it "
            "does not name one moment"
        )
        return problems
    now = datetime.now(timezone.utc)
    if (parsed - now).total_seconds() > CREATED_ALLOWANCE_SECONDS:
        problems.append(
            "the manifest creation time %s names a moment more "
            "than the stated allowance of one hour after this "
            "check runs, so the packet claims a creation that has "
            "not happened" % ascii(value)[:60]
        )
    head_time = head_committer_time(repo, manifest.get("head"))
    if head_time is not None and \
            (head_time - parsed).total_seconds() > \
            CREATED_ALLOWANCE_SECONDS:
        problems.append(
            "the manifest creation time %s names a moment more "
            "than the stated allowance of one hour before the "
            "recorded head commit was committed at %s, so the "
            "packet claims it was created before the change it "
            "holds existed"
            % (ascii(value)[:60], head_time.isoformat())
        )
    pr_record = manifest.get("pr")
    if isinstance(pr_record, dict) and \
            isinstance(pr_record.get("state_as_of"), str):
        fetched = parse_timestamp(pr_record["state_as_of"])
        if fetched is None:
            problems.append(
                "the manifest pull request state fetch time %s "
                "is not an ISO timestamp with an offset, so the "
                "state it carries records no fetch moment"
                % ascii(pr_record["state_as_of"])[:60]
            )
        else:
            if (fetched - parsed).total_seconds() > \
                    CREATED_ALLOWANCE_SECONDS:
                problems.append(
                    "the manifest pull request state fetch time "
                    "%s names a moment more than the stated "
                    "allowance of one hour after the manifest "
                    "creation time, so the state cannot have been "
                    "fetched inside the run that built the packet"
                    % ascii(pr_record["state_as_of"])[:60]
                )
            if head_time is not None and \
                    (head_time - fetched).total_seconds() > \
                    CREATED_ALLOWANCE_SECONDS:
                problems.append(
                    "the manifest pull request state fetch time "
                    "%s names a moment more than the stated "
                    "allowance of one hour before the recorded "
                    "head commit was committed at %s, so the "
                    "state cannot have been fetched for the "
                    "change this packet holds"
                    % (
                        ascii(pr_record["state_as_of"])[:60],
                        head_time.isoformat(),
                    )
                )
    return problems


def repo_state_problems(repo):
    """Read the state of the repository the stamp is asked against.

    Returns the problem list and whether the state is fatal to
    the deep checks. A path that is not a readable repository and
    a shallow clone are fatal, because every recount from them
    would blame the packet for the environment. A repository in
    the middle of a rebase is named without stopping the other
    checks, because its head is a transient position an abort
    will abandon and a continuation will move, and a stamp that
    says nothing about it invites a reviewer to treat that head
    as settled.
    """
    problems = []
    git_dir = run_git(repo, ["rev-parse", "--absolute-git-dir"])
    if git_dir is None:
        problems.append(
            "the path %s is not a readable git repository, so the "
            "recorded refs cannot be checked against it" % repo
        )
        return problems, True
    shallow = run_git(repo, ["rev-parse", "--is-shallow-repository"])
    if shallow is not None and shallow.strip() == "true":
        problems.append(
            "the repository at %s is a shallow clone, so its "
            "history is truncated and no packet can be verified "
            "against it. Fetch the full history first, for "
            "example with git fetch --unshallow, then run the "
            "check again" % repo
        )
        return problems, True
    common = run_git(repo, ["rev-parse", "--git-common-dir"])
    if common is not None and common.strip():
        common_path = Path(common.strip())
        if not common_path.is_absolute():
            common_path = Path(repo) / common_path
        info_attributes = common_path / "info" / "attributes"
        try:
            info_text = info_attributes.read_text(
                encoding="utf-8", errors="surrogateescape"
            )
        except OSError:
            info_text = ""
        if any(
            line.strip() and not line.lstrip().startswith("#")
            for line in info_text.splitlines()
        ):
            problems.append(
                "the repository at %s carries attributes in %s and "
                "those attributes sit outside the reviewed tree "
                "while git reads them ahead of the tree attributes "
                "themselves, so the recount cannot credit its "
                "markings to the tree under review and the packet "
                "cannot be stamped from this clone. Empty or "
                "remove that file, then run the check again"
                % (repo, info_attributes)
            )
            return problems, True
    git_dir_path = Path(git_dir.strip())
    if (git_dir_path / "rebase-merge").is_dir() or \
            (git_dir_path / "rebase-apply").is_dir():
        problems.append(
            "the repository at %s is in the middle of a rebase, "
            "so its head is a transient rebase position and the "
            "packet cannot be stamped as settled at that head "
            "until the rebase finishes or is aborted" % repo
        )
    return problems, False


# ---------------------------------------------------------------------
# Loading the extractor. The recount and the fresh diff bodies come
# from the extractor's own code, loaded from the canonical skill, so
# the check measures a change exactly the way the run that built the
# packet measured it and the two can never drift into rival counting
# rules. A tree without the extractor cannot recount, and the check
# fails closed there rather than stamping on trust.
# ---------------------------------------------------------------------

_EXTRACTOR_CACHE = {}


def load_extractor():
    if "module" in _EXTRACTOR_CACHE:
        return _EXTRACTOR_CACHE["module"]
    module = None
    if EXTRACTOR_PATH.is_file():
        try:
            spec = importlib.util.spec_from_file_location(
                "recognitio_extract_for_check", EXTRACTOR_PATH
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception:
            module = None
    _EXTRACTOR_CACHE["module"] = module
    return module


def outside_fence(lines):
    """Flag each line that stands outside every code fence.

    A fence opens on a run of three or more backticks with no
    backtick in the rest of the line and closes on a run at least
    as long standing alone. The rule the extractor writes its
    fences under, read back, so the two sides agree on what a
    heading is.
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


def packet_headings(packet_text):
    """The level two headings a packet carries, fences excluded.

    The same reading the extractor records its sections under, so
    the manifest section list can be compared against the packet
    itself as an ordered whole rather than as a subset.
    """
    lines = packet_text.split("\n")
    return [
        line for line, outside in zip(lines, outside_fence(lines))
        if outside and line.startswith("## ")
    ]


def section_problems(packet_text, recorded):
    """Check the packet carries the sections its manifest records.

    Every recorded heading must appear in the packet outside its
    fences, and each must hold at least one non blank line before
    the next heading, so a section that was promised and gutted is
    still caught. A heading inside a fence is quoted text the
    reviewed party wrote, and it satisfies nothing.
    """
    problems = []
    if not isinstance(recorded, list):
        return [
            "the manifest records its sections in a shape that "
            "cannot be checked"
        ]
    lines = packet_text.split("\n")
    outside = outside_fence(lines)
    positions = {}
    for index, line in enumerate(lines):
        if outside[index] and line.startswith("## ") \
                and line not in positions:
            positions[line] = index
    for heading in recorded:
        if not isinstance(heading, str):
            problems.append("a recorded section heading is not text")
            continue
        if heading not in positions:
            problems.append(
                "the manifest records a section the packet does not "
                "hold: %s" % heading
            )
            continue
        start = positions[heading] + 1
        filled = False
        for position in range(start, len(lines)):
            if outside[position] and lines[position].startswith("## "):
                break
            if lines[position].strip():
                filled = True
                break
        if not filled:
            problems.append(
                "the section %s stands in the packet with no content "
                "under it" % heading
            )
    return problems


TIER_HEADINGS = {
    "T2": "## T2 Companions",
    "T3": "## T3 History",
}

PLACEHOLDER_LINES = (
    "Not selected for this run. The change in T1 is complete.",
    "Dropped under the token budget. The change in T1 is complete.",
)


def section_body(packet_text, heading):
    """Return the lines under one section heading, outside fences.

    The body runs from the heading line to the next level two
    heading outside a fence, or to the end of the packet. A
    heading inside a fence is quoted text and opens nothing.
    """
    lines = packet_text.split("\n")
    outside = outside_fence(lines)
    start = None
    for index, line in enumerate(lines):
        if outside[index] and line == heading:
            start = index + 1
            break
    if start is None:
        return None
    body = []
    for position in range(start, len(lines)):
        if outside[position] and lines[position].startswith("## "):
            break
        body.append(lines[position])
    return body


def section_span(packet_text, heading):
    """Return one section as raw text, heading line included.

    The span runs to the next level two heading outside a fence or
    to the end of the packet. Lines are split on the newline
    character alone, here and everywhere this script reads the
    packet, because the Unicode line separators a filename can
    carry also split lines under the wider splitting rule, and a
    diff body line that names such a file would break in two. The
    extractor joins its sections with a single newline, so a span
    that is not the last section holds the section text plus that
    one joining newline, and the token accounting reads the span
    with the joining newline removed.
    """
    lines = packet_text.split("\n")
    outside = outside_fence(lines)
    start = None
    for index, line in enumerate(lines):
        if outside[index] and line == heading:
            start = index
            break
    if start is None:
        return None
    end = len(lines)
    for position in range(start + 1, len(lines)):
        if outside[position] and lines[position].startswith("## "):
            end = position
            break
    span = "\n".join(lines[start:end])
    if end < len(lines):
        span += "\n"
    return span


def tier_problems(packet_text, tiers):
    """Check the manifest tier receipt against the packet bodies.

    A tier the manifest records as included must carry real
    content in its packet section. A section whose whole body
    is the not selected or dropped placeholder is the thin
    packet shape, whatever the manifest receipt claims, so a
    thin packet cannot wear a full packet manifest even when
    both packets record the same section headings.
    """
    problems = []
    if not isinstance(tiers, dict):
        return ["the manifest records its tiers in a shape that "
                "cannot be checked"]
    for tier, heading in TIER_HEADINGS.items():
        info = tiers.get(tier)
        if not isinstance(info, dict):
            continue
        if info.get("included") is not True:
            continue
        body = section_body(packet_text, heading)
        if body is None:
            continue
        text = "\n".join(body).strip()
        if text in PLACEHOLDER_LINES:
            problems.append(
                "the manifest records %s as included but the packet "
                "carries only the placeholder for a tier that was "
                "not gathered" % tier
            )
    return problems


def display_path(path):
    """Render a manifest path the way the extractor prints it.

    The extractor escapes control characters, backslashes and the
    three Unicode line separators in a path before printing it as
    a packet heading, so the check applies the same escaping
    before comparing a manifest file record against the change
    tier headings. This copy and the extractor copy are held to
    one behaviour by the display path agreement test in the test
    suite, which runs both over an adversarial name battery, so
    the two sides cannot diverge again without a test failing.
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
            out.append("\\u%04x" % ord(char))
        elif char in (
            "\u202a", "\u202b", "\u202c", "\u202d", "\u202e",
            "\u2066", "\u2067", "\u2068", "\u2069",
            "\u200b", "\u200c", "\u200d", "\u200e", "\u200f",
            "\u2060", "\ufeff",
        ):
            out.append("\\u%04x" % ord(char))
        else:
            out.append(char)
    return "".join(out)


def file_problems(packet_text, files):
    """Check every manifest file record stands in the change tier.

    The extractor prints one level three heading per changed
    file inside the change tier. A packet that drops a changed
    file entry in full no longer shows the change the manifest
    receipts, and the stamp must fail even though every section
    heading still stands.
    """
    problems = []
    if not isinstance(files, list):
        return ["the manifest records its files in a shape that "
                "cannot be checked"]
    body = section_body(packet_text, "## T1 The change")
    if body is None:
        return problems
    lines = packet_text.split("\n")
    outside = outside_fence(lines)
    headings = set()
    in_t1 = False
    for index, line in enumerate(lines):
        if outside[index] and line.startswith("## "):
            in_t1 = line == "## T1 The change"
            continue
        if in_t1 and outside[index] and line.startswith("### "):
            headings.add(line[4:])
    for entry in files:
        if not isinstance(entry, dict) or "path" not in entry:
            problems.append("a manifest file record carries no path")
            continue
        if display_path(entry["path"]) not in headings:
            problems.append(
                "the manifest receipts a changed file the packet "
                "change tier does not hold: %s" % entry["path"]
            )
    return problems


# ---------------------------------------------------------------------
# Ref verification. The manifest names a base, a head and a merge
# base, and the stamp means the packet holds the change between the
# merge base and the head. Each recorded ref must name a commit in
# the repository, and the recorded merge base must be the merge base
# git itself computes, so a packet built for a narrower range cannot
# wear the refs of a wider one.
# ---------------------------------------------------------------------

HEX40 = re.compile(r"^[0-9a-f]{40}$")


def is_commit(repo, ref):
    if not isinstance(ref, str) or not HEX40.match(ref):
        return False
    return run_git(repo, ["cat-file", "-e", ref + "^{commit}"]) is not None


def git_merge_base(repo, base, head):
    out = run_git(repo, ["merge-base", base, head])
    return out.strip() if out is not None else None


def ref_problems(repo, manifest, expect_base, expect_merge_base):
    problems = []
    base = manifest.get("base")
    head = manifest.get("head")
    merge_base = manifest.get("merge_base")
    mode = manifest.get("mode")
    if not is_commit(repo, head):
        problems.append(
            "the manifest records head %s, which is not a commit in "
            "the repository" % head
        )
        return problems
    if base is None:
        if merge_base is not None:
            problems.append(
                "the manifest records no base but records a merge "
                "base, and the two cannot both be true"
            )
        if mode != "commit":
            problems.append(
                "the manifest records no base for a mode that "
                "always resolves one"
            )
        parent = run_git(repo, ["rev-parse", "--verify", head + "^"])
        if parent is not None:
            problems.append(
                "the manifest records the head as a root commit "
                "with no base, but the head has a parent in the "
                "repository"
            )
    else:
        if not is_commit(repo, base):
            problems.append(
                "the manifest records base %s, which is not a "
                "commit in the repository" % base
            )
            return problems
        computed = git_merge_base(repo, base, head)
        if computed is None:
            problems.append(
                "the recorded base and head share no merge base in "
                "the repository"
            )
        elif merge_base != computed:
            problems.append(
                "the manifest records merge base %s but the merge "
                "base of its recorded base and head is %s"
                % (merge_base, computed)
            )
        if mode == "commit" and merge_base != base:
            problems.append(
                "the manifest records a single commit packet whose "
                "merge base is not its base"
            )
    since = manifest.get("since")
    if since is not None and not is_commit(repo, since):
        problems.append(
            "the manifest records since %s, which is not a commit "
            "in the repository" % since
        )
    if expect_base is not None and base != expect_base:
        problems.append(
            "the manifest records base %s but the review names "
            "base %s, so this packet covers a different range than "
            "the one under review" % (base, expect_base)
        )
    if expect_merge_base is not None and merge_base != expect_merge_base:
        problems.append(
            "the manifest records merge base %s but the review "
            "names merge base %s, so this packet covers a "
            "different range than the one under review"
            % (merge_base, expect_merge_base)
        )
    return problems


# ---------------------------------------------------------------------
# The recount. The change is fetched and measured again from the
# repository, through the extractor's own code, and the manifest
# must equal the recount record for record. The extractor's own
# verification pass is then run against the manifest records, so
# the line counts are also confirmed by the second counting method
# that pass carries.
# ---------------------------------------------------------------------


def recount_problems(repo, manifest, extractor):
    """Recount the recorded change and compare it to the manifest.

    Returns the problem list and the fresh change mapping, which
    the body checks read the true diff bodies and commit log from.
    The fresh change is None when the recount could not run.
    """
    problems = []
    if extractor is None:
        return [
            "the extractor cannot be loaded from the canonical "
            "skill, so the change cannot be recounted and the "
            "packet cannot be verified"
        ], None
    head = manifest["head"]
    diff_base = manifest["merge_base"] or EMPTY_TREE
    try:
        change = extractor.fetch_change(repo, diff_base, head)
        exclusions = extractor.enrich_files(repo, diff_base, head, change)
        fresh_records = extractor.manifest_file_records(change["files"])
    except Exception as exc:
        return [
            "the recount of the recorded change could not run "
            "(%s)" % exc
        ], None
    recorded = manifest["files"]
    fresh_by_path = {entry["path"]: entry for entry in fresh_records}
    recorded_by_path = {entry["path"]: entry for entry in recorded}
    for path in sorted(set(recorded_by_path) - set(fresh_by_path)):
        problems.append(
            "the manifest receipts a file the recount of the "
            "recorded range does not hold: %s" % path
        )
    for path in sorted(set(fresh_by_path) - set(recorded_by_path)):
        problems.append(
            "the recount of the recorded range holds a file the "
            "manifest does not receipt: %s" % path
        )
    fields = (
        "old_path", "status", "status_code", "additions", "deletions",
        "hunks", "binary", "attribute_text", "binary_transition",
        "placeholder", "instruction_file",
    )
    for path in sorted(set(recorded_by_path) & set(fresh_by_path)):
        mine = recorded_by_path[path]
        theirs = fresh_by_path[path]
        for field in fields:
            if mine.get(field) != theirs.get(field):
                problems.append(
                    "the manifest record for %s disagrees with the "
                    "recount on %s" % (path, field)
                )
    if [entry["path"] for entry in recorded] != \
            [entry["path"] for entry in fresh_records]:
        if not problems:
            problems.append(
                "the manifest file records stand in a different "
                "order than the recount of the recorded range"
            )
    if manifest["exclusions"] != exclusions:
        problems.append(
            "the manifest exclusion receipts disagree with the "
            "recount of the recorded range"
        )
    try:
        discrepancies = extractor.verify_counts(
            repo, diff_base, head, recorded
        )
    except Exception as exc:
        problems.append(
            "the verification recount could not run (%s)" % exc
        )
    else:
        for item in discrepancies:
            problems.append("the recount disagrees: %s" % item)
    return problems, change


# ---------------------------------------------------------------------
# Body verification. The packet body is read against the manifest
# and against the recount, block by block, so an edit made to a
# packet after generation breaks the stamp wherever it lands.
# ---------------------------------------------------------------------

TIER_ORDER = ("T0", "T1", "T2", "T3")
TIER_SECTION = {
    "T0": "## T0 Triage",
    "T1": "## T1 The change",
    "T2": "## T2 Companions",
    "T3": "## T3 History",
}
STATUS_NAMES = (
    "added", "modified", "deleted", "renamed", "copied",
    "typechange", "unmerged", "unknown",
)


def manifest_totals(manifest):
    files = manifest["files"]
    return {
        "files": len(files),
        "hunks": sum(entry["hunks"] for entry in files),
        "additions": sum(entry["additions"] for entry in files),
        "deletions": sum(entry["deletions"] for entry in files),
    }


def counted_phrase(count, singular, plural):
    return "%d %s" % (count, singular if count == 1 else plural)


def header_problems(packet_text, manifest):
    problems = []
    lines = packet_text.split("\n")
    end = len(lines)
    for index, line in enumerate(lines):
        if line == "Contents":
            end = index
            break
    header = lines[:end]
    if not header or header[0] != "# The pericope for %s" % manifest["label"]:
        problems.append(
            "the packet title does not name the label the manifest "
            "records"
        )
    wanted = ["Mode: %s" % manifest["mode"]]
    if manifest["base"] is None:
        wanted.append(
            "Base: the empty tree, because the head is a root commit"
        )
    else:
        wanted.append("Base: %s" % manifest["base"])
    wanted.append("Head: %s" % manifest["head"])
    if manifest["merge_base"] is None:
        wanted.append(
            "Merge base: none, because the head is a root commit"
        )
    else:
        wanted.append("Merge base: %s" % manifest["merge_base"])
    if manifest["since"] is not None:
        wanted.append("Since: %s" % manifest["since"])
    wanted.append(
        "Verified: yes. The recount at the close of this packet "
        "carries the proof."
    )
    for line in wanted:
        if line not in header:
            problems.append(
                "the packet header does not carry the line its "
                "manifest requires: %s" % line
            )
    if manifest["since"] is None and any(
        line.startswith("Since: ") for line in header
    ):
        problems.append(
            "the packet header carries a since line its manifest "
            "does not record"
        )
    withheld = [
        item for item in manifest["exclusions"]
        if not item["shown_as_text"]
    ]
    shown = [
        item for item in manifest["exclusions"] if item["shown_as_text"]
    ]
    for title, group in (
        ("Files not shown in full:", withheld),
        ("Files shown in full:", shown),
    ):
        expected = [
            "- %s: %s" % (display_path(item["path"]), item["reason"])
            for item in group
        ]
        if title in header:
            start = header.index(title)
            found = []
            for line in header[start + 1:]:
                if line.startswith("- "):
                    found.append(line)
                elif found or line.strip():
                    break
            if found != expected:
                problems.append(
                    "the packet header list under %s disagrees "
                    "with the manifest exclusion receipts" % title
                )
        elif expected:
            problems.append(
                "the packet header carries no %s list, but the "
                "manifest receipts %d files there"
                % (title, len(expected))
            )
    return problems


def contents_problems(packet_text, manifest, totals):
    problems = []
    lines = packet_text.split("\n")
    sentence = (
        "This packet holds %s, %s, %s and %s"
        % (
            counted_phrase(totals["files"], "file", "files"),
            counted_phrase(totals["hunks"], "hunk", "hunks"),
            counted_phrase(totals["additions"], "added line", "added lines"),
            counted_phrase(totals["deletions"], "deleted line", "deleted lines"),
        )
    )
    if sentence not in lines:
        problems.append(
            "the packet contents block does not carry the totals "
            "sentence its manifest records add up to"
        )
    tiers = manifest["tiers"]
    standing = [
        tier for tier in TIER_ORDER if tiers[tier]["state"] == "included"
    ]
    placeholders = [
        tier for tier in TIER_ORDER if tiers[tier]["state"] != "included"
    ]
    if not placeholders:
        standing_line = "All four tiers stand in full"
    else:
        parts = []
        if standing:
            verb = "stands" if len(standing) == 1 else "stand"
            parts.append("%s %s in full" % (" and ".join(standing), verb))
        verb = "stands" if len(placeholders) == 1 else "stand"
        noun = "a placeholder" if len(placeholders) == 1 else "placeholders"
        parts.append(
            "%s %s as %s" % (" and ".join(placeholders), verb, noun)
        )
        joined = " and ".join(parts)
        standing_line = joined[:1].upper() + joined[1:]
    if standing_line not in lines:
        problems.append(
            "the packet contents block does not describe the tier "
            "states its manifest records"
        )
    return problems


def triage_problems(packet_text, manifest, fresh_change, extractor):
    problems = []
    body = section_body(packet_text, "## T0 Triage")
    if body is None:
        return problems
    count_line = "Files changed: %d" % len(manifest["files"])
    if count_line not in body:
        problems.append(
            "the triage tier does not carry the changed file count "
            "its manifest records"
        )
    outside = outside_fence(body)
    files_at = None
    numstat_at = None
    for index, line in enumerate(body):
        if not outside[index]:
            continue
        if line == "### Files" and files_at is None:
            files_at = index
        if line == "### Numstat" and numstat_at is None:
            numstat_at = index
    if files_at is None or numstat_at is None or numstat_at < files_at:
        problems.append(
            "the triage tier lacks its file list or its numstat "
            "block, so its file receipts cannot be checked"
        )
        return problems
    listed = []
    for line in body[files_at + 1:numstat_at]:
        if not line.startswith("- "):
            continue
        match = re.match(
            r"^- (.+) \((%s)(, instruction file)?"
            r"(, (renamed|copied) from (.+))?\)$" % "|".join(STATUS_NAMES),
            line,
        )
        if not match:
            problems.append(
                "a triage file list line cannot be read against "
                "the manifest: %s" % line
            )
            continue
        listed.append((
            match.group(1),
            match.group(2),
            bool(match.group(3)),
            match.group(5),
            match.group(6),
        ))
    expected = []
    for entry in manifest["files"]:
        expected.append((
            display_path(entry["path"]),
            entry["status"],
            entry["instruction_file"],
            (
                "copied" if entry["status"] == "copied" else "renamed"
            ) if entry["old_path"] else None,
            display_path(entry["old_path"]) if entry["old_path"] else None,
        ))
    if listed != expected:
        problems.append(
            "the triage file list disagrees with the manifest file "
            "records"
        )
    # The numstat block stands inside a fence after its heading.
    # Its lines are read raw, because the block is data the
    # manifest must match entry for entry.
    stats = []
    fence_open = None
    for index in range(numstat_at + 1, len(body)):
        stripped = body[index].strip()
        ticks = len(stripped) - len(stripped.lstrip("`"))
        if fence_open is None:
            if ticks >= 3:
                fence_open = ticks
            continue
        if ticks >= fence_open and stripped == "`" * ticks:
            fence_open = None
            break
        stats.append(body[index])
    if stats == ["(no changes)"]:
        stats = []
    parsed = []
    for line in stats:
        match = re.match(r"^(-|[0-9]+)\t(-|[0-9]+)\t(.*)$", line)
        if not match:
            problems.append(
                "a numstat line in the triage tier cannot be read "
                "against the manifest: %s" % line
            )
            continue
        parsed.append((match.group(1), match.group(2), match.group(3)))
    expected_stats = []
    for entry in manifest["files"]:
        if entry["binary"]:
            expected_stats.append(("-", "-", display_path(entry["path"])))
        else:
            expected_stats.append((
                str(entry["additions"]),
                str(entry["deletions"]),
                display_path(entry["path"]),
            ))
    if parsed != expected_stats:
        problems.append(
            "the triage numstat block disagrees with the manifest "
            "file records"
        )
    if fresh_change is not None and extractor is not None:
        commits_at = None
        for index, line in enumerate(body):
            if outside[index] and line == "### Commits":
                commits_at = index
                break
        if commits_at is not None:
            block = []
            fence_open = None
            for index in range(commits_at + 1, len(body)):
                stripped = body[index].strip()
                ticks = len(stripped) - len(stripped.lstrip("`"))
                if fence_open is None:
                    if ticks >= 3:
                        fence_open = ticks
                    continue
                if ticks >= fence_open and stripped == "`" * ticks:
                    break
                block.append(body[index])
            commit_text = fresh_change["commit_log"].rstrip()
            if not commit_text:
                commit_text = "(no commits)"
            if "\n".join(block) != commit_text:
                problems.append(
                    "the triage commit list disagrees with the "
                    "recount of the recorded range"
                )
    return problems


def diff_fence_for(text):
    """The diff fence the sizing rule gives for one diff body.

    A fence one backtick longer than the longest run of
    backticks inside the text, with a floor of three, which is
    the rule the extractor sizes every change tier fence
    under. This copy and the extractor copy are held to one
    behaviour by the diff fence agreement test in the test
    suite, which runs both over a battery of bodies, so the
    two sides cannot diverge again without a test failing.
    """
    longest = 0
    for match in re.finditer(r"`+", text):
        longest = max(longest, len(match.group(0)))
    return "`" * max(3, longest + 1)


def change_tier_problems(packet_text, manifest, fresh_change, extractor):
    problems = []
    span = section_span(packet_text, "## T1 The change")
    if span is None:
        return problems
    lines = span.split("\n")
    sections = []
    current = None
    for line in lines:
        if line.startswith("### "):
            current = (line[4:], [])
            sections.append(current)
        elif current is not None:
            current[1].append(line)
    recorded_paths = [entry["path"] for entry in manifest["files"]]
    found_paths = [name for name, _body in sections]
    expected_names = [display_path(path) for path in recorded_paths]
    if found_paths != expected_names:
        problems.append(
            "the change tier file sections do not stand one to one "
            "with the manifest file records, in the same order"
        )
        return problems
    by_path = {entry["path"]: entry for entry in manifest["files"]}
    for name, body_lines in sections:
        entry = by_path[recorded_paths[expected_names.index(name)]]
        status_line = "Status: %s" % entry["status"]
        if status_line not in body_lines:
            problems.append(
                "the change tier section for %s does not carry "
                "the status its manifest record names" % entry["path"]
            )
        sourced = [
            line for line in body_lines
            if line.startswith("Renamed from: ")
            or line.startswith("Copied from: ")
        ]
        if entry["old_path"]:
            verb = "Copied" if entry["status"] == "copied" else "Renamed"
            wanted = [
                "%s from: %s" % (verb, display_path(entry["old_path"]))
            ]
            if sourced != wanted:
                problems.append(
                    "the change tier section for %s does not carry "
                    "the source its manifest record names"
                    % entry["path"]
                )
        elif sourced:
            problems.append(
                "the change tier section for %s carries a source "
                "its manifest record does not" % entry["path"]
            )
        # The diff block opens on a run of three or more
        # backticks followed by the word diff and closes on the
        # same run standing alone. The extractor sizes the run
        # one backtick longer than the longest run inside the
        # diff body, so a bare fence line the body itself holds
        # as context cannot close the block early here either.
        # A packet written under the old fixed three backtick
        # fence reads under the same rule wherever its body
        # holds no run that could break that fence. The run is
        # also compared against the size the body requires, so
        # this reading on its own refuses a fence the extractor
        # would never write, at either end of the canonical
        # size, and never leans on the whole tier rebuild to
        # catch a non canonical fence for it.
        fence = None
        start = None
        for index, line in enumerate(body_lines):
            match = re.fullmatch(r"(`{3,})diff", line)
            if match:
                fence = match.group(1)
                start = index + 1
                break
        if fence is None:
            problems.append(
                "the change tier section for %s carries no diff "
                "block" % entry["path"]
            )
            continue
        inner = []
        closed = False
        for line in body_lines[start:]:
            if line == fence:
                closed = True
                break
            inner.append(line)
        if not closed:
            problems.append(
                "the change tier section for %s carries a diff "
                "block with no closing fence" % entry["path"]
            )
            continue
        inner_text = "\n".join(inner)
        required = diff_fence_for(inner_text)
        if fence != required:
            problems.append(
                "the change tier section for %s carries its "
                "diff block inside a %d backtick fence, but "
                "the body it fences requires %d backticks"
                % (entry["path"], len(fence), len(required))
            )
        if entry["placeholder"] is not None:
            if inner_text != entry["placeholder"]:
                problems.append(
                    "the change tier placeholder for %s disagrees "
                    "with its manifest record" % entry["path"]
                )
                continue
            match = re.search(
                r"its ([0-9]+) additions and ([0-9]+) deletions "
                r"across ([0-9]+) hunks",
                entry["placeholder"],
            )
            if match:
                claimed = tuple(int(match.group(i)) for i in (1, 2, 3))
                actual = (
                    entry["additions"], entry["deletions"], entry["hunks"]
                )
                if claimed != actual:
                    problems.append(
                        "the change tier placeholder for %s names "
                        "counts its manifest record does not"
                        % entry["path"]
                    )
            continue
        if "@@ " in inner_text or any(
            line.startswith("@@ ") for line in inner
        ):
            if extractor is not None:
                # The counting rule is the extractor's own, so a
                # merged typechange chunk, whose second section
                # opens a fresh file header, counts here exactly
                # as the recount counts it.
                adds, dels = extractor.count_chunk_lines(inner_text)
            else:
                adds = 0
                dels = 0
                in_hunks = False
                for line in inner:
                    if line.startswith("diff --git "):
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
            if (adds, dels) != (entry["additions"], entry["deletions"]):
                problems.append(
                    "the diff body for %s counts %d added and %d "
                    "deleted lines, but its manifest record names "
                    "%d and %d"
                    % (entry["path"], adds, dels,
                       entry["additions"], entry["deletions"])
                )
        if fresh_change is not None and extractor is not None:
            chunk = fresh_change["chunks"].get(entry["path"], "")
            expected_inner = (
                chunk.rstrip() if chunk.strip() else "(no textual diff)"
            )
            if inner_text != expected_inner:
                problems.append(
                    "the diff body for %s disagrees with the "
                    "recount of the recorded range" % entry["path"]
                )
    return problems


def span_text(packet_text, heading):
    """One section text with the joining newline removed."""
    span = section_span(packet_text, heading)
    if span is None:
        return None
    return span[:-1] if span.endswith("\n") else span


def tier_span_problems(packet_text, manifest, extractor):
    problems = []
    tiers = manifest["tiers"]
    for tier in TIER_ORDER:
        info = tiers[tier]
        span = section_span(packet_text, TIER_SECTION[tier])
        if span is None:
            continue
        text = span[:-1] if span.endswith("\n") else span
        if info["state"] == "included":
            estimate = (
                extractor.estimate_tokens(text)
                if extractor is not None else len(text) // 4
            )
            if estimate != info["estimated_tokens"] or \
                    estimate != info["emitted_tokens"]:
                problems.append(
                    "the %s section in the packet measures %d "
                    "tokens, but its manifest receipt names %d "
                    "estimated and %d emitted"
                    % (tier, estimate, info["estimated_tokens"],
                       info["emitted_tokens"])
                )
        else:
            if extractor is None:
                continue
            expected = extractor.tier_placeholder(tier, info["state"])
            if text != expected:
                problems.append(
                    "the %s section in the packet is not the "
                    "placeholder its manifest state requires" % tier
                )
            if extractor.estimate_tokens(expected) != info["emitted_tokens"]:
                problems.append(
                    "the %s placeholder in the packet measures "
                    "differently than its manifest receipt names"
                    % tier
                )
            if info["state"] == "not selected" and \
                    info["estimated_tokens"] != 0:
                problems.append(
                    "the manifest names an estimated size for %s, "
                    "a tier that was never built" % tier
                )
    return problems


def budget_problems(manifest):
    """Check the budget account against itself and its own rules.

    The receipt lines in the packet are printed from this
    account, so comparing the account only against those lines
    proves nothing about the account. What can be proven from
    the manifest alone is the account shape the extractor
    writes. A drop is recorded at most once per tier, the drops
    stand in the order the budget sheds them, T3 before T2, a
    drop with no budget is impossible, and every drop reason is
    the one wording the extractor writes, naming the budget the
    account itself records. The size of a dropped tier is
    recounted in the rebuild pass, which is the only place the
    tier text can be measured again.
    """
    problems = []
    budget = manifest["budget"]
    dropped = budget["dropped"]
    names = [item["tier"] for item in dropped]
    if len(set(names)) != len(names):
        problems.append(
            "the manifest budget account records the same tier "
            "drop more than once, and one receipt line in the "
            "packet cannot receipt two drops"
        )
    shed_order = [tier for tier in ("T3", "T2") if tier in names]
    if names != shed_order:
        problems.append(
            "the manifest budget account records its drops in "
            "the order %s, but the budget sheds T3 before T2"
            % ", ".join(names)
        )
    budget_tokens = budget["budget_tokens"]
    if dropped and budget_tokens is None:
        problems.append(
            "the manifest budget account records dropped tiers "
            "but no budget, and a tier drops only under a budget"
        )
    if budget_tokens is not None:
        wanted_reason = "budget of %d tokens" % budget_tokens
        for item in dropped:
            if item["reason"] != wanted_reason:
                problems.append(
                    "the manifest budget account records the drop "
                    "of %s with the reason %s, but the only reason "
                    "a run records is %s, naming the budget the "
                    "account itself records"
                    % (item["tier"], ascii(item["reason"])[:60],
                       wanted_reason)
                )
    return problems


def tier_receipt_problems(manifest):
    problems = []
    tiers = manifest["tiers"]
    selected = manifest["selected_tiers"]
    if selected != sorted(selected):
        problems.append(
            "the manifest records its selected tiers in the "
            "order %s, but a run writes that list in sorted order"
            % ", ".join(selected)
        )
    dropped = manifest["budget"]["dropped"]
    dropped_names = [item["tier"] for item in dropped]
    total = len(manifest["files"])
    for tier in TIER_ORDER:
        info = tiers[tier]
        if info["included"] != (info["state"] == "included"):
            problems.append(
                "the manifest tier receipt for %s carries an "
                "included flag that contradicts its state" % tier
            )
        if info["state"] == "included" and tier not in selected:
            problems.append(
                "the manifest records %s as included but does not "
                "list it among the selected tiers" % tier
            )
        if info["state"] == "not selected" and tier in selected:
            problems.append(
                "the manifest records %s as not selected but lists "
                "it among the selected tiers" % tier
            )
        if info["state"] == "dropped" and tier not in dropped_names:
            problems.append(
                "the manifest records %s as dropped but its "
                "budget account names no drop for it" % tier
            )
        if info["state"] != "dropped" and tier in dropped_names:
            problems.append(
                "the manifest budget account drops %s but its "
                "tier receipt does not record the drop" % tier
            )
    for tier in ("T0", "T1"):
        if tiers[tier]["state"] != "included":
            problems.append(
                "the manifest records %s as not included, and the "
                "core tiers are always included" % tier
            )
        if tiers[tier]["files"] != total:
            problems.append(
                "the manifest tier receipt for %s names %d files, "
                "but the manifest records %d changed files"
                % (tier, tiers[tier]["files"], total)
            )
    if tiers["T2"]["state"] == "not selected" and \
            tiers["T2"]["files"] != 0:
        problems.append(
            "the manifest tier receipt for T2 names files for a "
            "tier that was never built"
        )
    if tiers["T3"]["state"] == "not selected" and \
            tiers["T3"]["files"] != 0:
        problems.append(
            "the manifest tier receipt for T3 names files for a "
            "tier that was never built"
        )
    return problems


def receipt_problems(packet_text, manifest, totals, extractor=None):
    problems = []
    body = section_body(packet_text, "## Verification recount")
    if body is None:
        return problems
    budget = manifest["budget"]
    tiers = manifest["tiers"]
    wanted_budget = "Budget in tokens: %s" % (
        budget["budget_tokens"]
        if budget["budget_tokens"] is not None else "none set"
    )
    if wanted_budget not in body:
        problems.append(
            "the closing receipt does not carry the budget its "
            "manifest records"
        )
    estimate_line = "Packet estimate in tokens: %d" % budget["estimated_tokens"]
    if estimate_line not in body:
        problems.append(
            "the closing receipt does not carry the packet "
            "estimate its manifest records"
        )
    if extractor is None:
        extractor = load_extractor()
    packet_measure = (
        extractor.estimate_tokens(packet_text)
        if extractor is not None else len(packet_text) // 4
    )
    if budget["estimated_tokens"] != packet_measure:
        problems.append(
            "the manifest packet estimate of %d tokens does not "
            "measure the packet, which measures %d tokens"
            % (budget["estimated_tokens"], packet_measure)
        )
    for tier in TIER_ORDER:
        info = tiers[tier]
        if info["state"] == "included":
            line = (
                "%s included at about %d tokens across %d files"
                % (tier, info["estimated_tokens"], info["files"])
            )
        elif info["state"] == "dropped":
            line = (
                "%s dropped under the token budget. The full tier "
                "runs about %d tokens across %d files"
                % (tier, info["estimated_tokens"], info["files"])
            )
        else:
            line = "%s not selected for this run" % tier
        if line not in body:
            problems.append(
                "the closing receipt does not carry the %s line "
                "its manifest tier receipt requires" % tier
            )
    dropped = budget["dropped"]
    if dropped:
        for item in dropped:
            line = "Dropped %s because of the %s." % (
                item["tier"], item["reason"]
            )
            if line not in body:
                problems.append(
                    "the closing receipt does not carry the drop "
                    "line for %s its manifest budget records"
                    % item["tier"]
                )
    elif "No tier was dropped." not in body:
        problems.append(
            "the closing receipt does not carry the no drop line "
            "its manifest budget requires"
        )
    if "Recount passed" not in body:
        problems.append(
            "the closing receipt does not report that its recount "
            "passed"
        )
    covered = (
        "The recount covered %s with their statuses and old paths, "
        "%s, and %s and %s"
        % (
            counted_phrase(totals["files"], "file", "files"),
            counted_phrase(totals["hunks"], "hunk", "hunks"),
            counted_phrase(
                totals["additions"], "added line", "added lines"
            ),
            counted_phrase(
                totals["deletions"], "deleted line", "deleted lines"
            ),
        )
    )
    if covered not in body:
        problems.append(
            "the closing receipt recount sentence does not carry "
            "the totals its manifest records add up to"
        )
    if "The recount matches the manifest on every count" not in body:
        problems.append(
            "the closing receipt does not carry its agreement line"
        )
    if not dropped and all(
        tiers[tier]["state"] == "included" for tier in TIER_ORDER
    ):
        if "Every tier is included" not in body:
            problems.append(
                "the closing receipt does not carry the every tier "
                "line its manifest tier receipts require"
            )
    last = ""
    for line in packet_text.split("\n"):
        if line.strip():
            last = line
    if last != "Verified does not mean the change is correct or safe":
        problems.append(
            "the packet does not close on the limit sentence a "
            "verified packet ends with"
        )
    return problems


def section_sequence_problems(packet_text, manifest):
    problems = []
    recorded = manifest["sections"]
    actual = packet_headings(packet_text)
    if recorded != actual:
        problems.append(
            "the manifest section record does not match the "
            "sections the packet itself carries, in order"
        )
    expected = [
        "## T0 Triage", "## T1 The change", "## T2 Companions",
        "## T3 History",
    ]
    if manifest["since"] is not None:
        expected.append("## Re-review")
    expected.append("## Verification recount")
    if recorded != expected:
        problems.append(
            "the manifest section record is not the section "
            "sequence a packet for its recorded range carries"
        )
    return problems


COMMAND_VALUE_FLAGS = (
    "--pr", "--range", "--commit", "--since", "--tiers",
    "--findings", "--budget", "--out", "--repo",
)
COMMAND_MODE_FLAGS = {
    "range": "--range",
    "commit": "--commit",
    "pr": "--pr",
}
HEX_REF = re.compile(r"^[0-9a-f]{7,40}$")
HEX40_REF = re.compile(r"^[0-9a-f]{40}$")


def parse_command_flags(manifest):
    """Split the recorded command into its flags and their values.

    The extractor argument parser keeps the last value of a
    repeated flag, so every reading in this script takes the
    last value too. A check that read the first value would
    stamp a command the extractor itself would have run
    differently.
    """
    problems = []
    command = manifest.get("command")
    if not isinstance(command, list) or not command or \
            str(command[0]) != "extract.py":
        return None, [
            "the manifest command does not name the extractor "
            "that builds a packet"
        ]
    flags = {}
    tokens = [str(token) for token in command[1:]]
    index = 0
    while index < len(tokens):
        token = tokens[index]
        name, equals, value = token.partition("=")
        if name not in COMMAND_VALUE_FLAGS:
            problems.append(
                "the manifest command carries a flag the extractor "
                "does not take, %s" % token
            )
            index += 1
            continue
        if not equals:
            index += 1
            if index >= len(tokens):
                problems.append(
                    "the manifest command flag %s carries no value"
                    % name
                )
                break
            value = tokens[index]
        flags.setdefault(name, []).append(value)
        index += 1
    return flags, problems


def last_flag(flags, name):
    values = flags.get(name)
    return values[-1] if values else None


def resolve_ref(repo, value):
    if repo is None or value is None:
        return None
    out = run_git(repo, ["rev-parse", "--verify", value + "^{commit}"])
    return out.strip() if out is not None else None


def command_problems(manifest, repo, packet_text=None, extractor=None):
    """Read the recorded extractor command back against the manifest.

    The command is the record of how the packet claims it was
    built, and a forged record must not wear a genuine manifest.
    Every value the manifest also records is read back. The mode
    flag must be the flag for the mode the manifest records, the
    pull request flag must name the recorded pull request, the
    budget flag must name the recorded budget, the tiers flag
    must select the tiers the manifest records, and the findings
    flag must stand where the packet carries a findings
    accounting. A findings hash must stand only where the
    recorded command carries a findings flag, because the hash
    is the digest of the file that flag named and a run that
    named no such file used no findings file to digest.
    A range or commit or since value written as a full hash
    names an immutable commit, so a hash that names a different
    commit than the manifest records, or no commit at all,
    fails. A symbolic since spelling is resolved in the
    checking repository, because the since anchor is the ref
    the re-review section stands on and the manifest records
    the hash it resolved to. A symbolic range spelling is left
    to the warnings, because the range hashes are pinned in the
    manifest fields themselves and a branch spelling can
    honestly have moved since the run. The output flag the
    extractor requires must stand in the command. The output
    and repository values themselves name paths on the machine
    that ran the extraction, and a packet is portable across
    copies and clones, so those two values are read for
    presence and nothing more.
    """
    problems = []
    flags, parse_problems = parse_command_flags(manifest)
    problems.extend(parse_problems)
    if flags is None:
        return problems
    mode_flags = [
        flag for flag in COMMAND_MODE_FLAGS.values() if flag in flags
    ]
    wanted_flag = COMMAND_MODE_FLAGS.get(manifest.get("mode"))
    if len(mode_flags) != 1 or mode_flags[0] != wanted_flag:
        problems.append(
            "the manifest command does not carry the mode flag "
            "for the mode the manifest records"
        )
    if "--pr" in flags and isinstance(manifest.get("pr"), dict):
        if last_flag(flags, "--pr") != str(manifest["pr"].get("number")):
            problems.append(
                "the manifest command names a different pull "
                "request than the manifest records"
            )
    if "--commit" in flags:
        value = last_flag(flags, "--commit")
        if HEX_REF.match(value) and repo is not None:
            resolved = resolve_ref(repo, value)
            if resolved is None or resolved != manifest.get("head"):
                problems.append(
                    "the manifest command names a commit other "
                    "than the head the manifest records"
                )
    if "--range" in flags:
        value = last_flag(flags, "--range")
        if "..." in value:
            left, _, right = value.partition("...")
        elif ".." in value:
            left, _, right = value.partition("..")
        else:
            problems.append(
                "the manifest command range carries no range "
                "separator"
            )
            left = right = ""
        if HEX40_REF.match(left) and manifest.get("base") is not None \
                and left != manifest["base"]:
            problems.append(
                "the manifest command range starts at a different "
                "base than the manifest records"
            )
        if HEX40_REF.match(right) and right != manifest.get("head"):
            problems.append(
                "the manifest command range ends at a different "
                "head than the manifest records"
            )
    if manifest.get("since") is not None and "--since" not in flags:
        problems.append(
            "the manifest records a since ref its command does "
            "not carry"
        )
    if "--since" in flags:
        value = last_flag(flags, "--since")
        if manifest.get("since") is None:
            problems.append(
                "the manifest command carries a since flag the "
                "manifest does not record"
            )
        elif HEX40_REF.match(value):
            if value != manifest["since"]:
                problems.append(
                    "the manifest command names a different since "
                    "ref than the manifest records"
                )
        elif repo is not None:
            resolved = resolve_ref(repo, value)
            if resolved is not None and resolved != manifest["since"]:
                problems.append(
                    "the manifest command since spelling %s "
                    "resolves to %s in this repository, but the "
                    "manifest records since %s, so the re-review "
                    "anchor the command names is not the anchor "
                    "the manifest records"
                    % (value, resolved, manifest["since"])
                )
    budget = manifest.get("budget")
    recorded_budget = budget.get("budget_tokens") \
        if isinstance(budget, dict) else None
    if "--budget" in flags:
        raw = last_flag(flags, "--budget")
        try:
            named_budget = int(raw)
        except (TypeError, ValueError):
            named_budget = None
        if named_budget is None or named_budget != recorded_budget:
            problems.append(
                "the manifest command names budget %s but the "
                "manifest budget account records %s"
                % (raw, recorded_budget)
            )
    elif recorded_budget is not None:
        problems.append(
            "the manifest budget account records a budget of %s "
            "tokens but its command carries no budget flag"
            % recorded_budget
        )
    if "--tiers" in flags:
        if extractor is not None:
            try:
                selected = extractor.parse_tier_selection(
                    last_flag(flags, "--tiers")
                )
            except ValueError:
                problems.append(
                    "the manifest command tiers value %s is not a "
                    "tier selection the extractor accepts"
                    % last_flag(flags, "--tiers")
                )
            else:
                if sorted(selected) != manifest.get("selected_tiers"):
                    problems.append(
                        "the manifest command selects tiers %s but "
                        "the manifest records the selected tiers %s"
                        % (
                            ", ".join(sorted(selected)),
                            ", ".join(manifest.get("selected_tiers") or []),
                        )
                    )
    elif manifest.get("selected_tiers") not in (None, ["T0", "T1", "T2", "T3"]):
        problems.append(
            "the manifest records the selected tiers %s but its "
            "command carries no tiers flag, and a run with no "
            "tiers flag selects all four tiers"
            % ", ".join(manifest.get("selected_tiers") or [])
        )
    if "--findings" in flags and "--since" not in flags:
        problems.append(
            "the manifest command carries a findings flag with "
            "no since flag, and the extractor refuses that pairing"
        )
    if "--findings" not in flags and \
            manifest.get("findings_sha256") is not None:
        problems.append(
            "the manifest records a findings hash but its "
            "command carries no findings flag, so the hash "
            "claims a findings file the run of record never "
            "used"
        )
    if packet_text is not None and manifest.get("since") is not None:
        body = section_body(packet_text, "## Re-review")
        accounted = body is not None and any(
            line == "### Prior findings accounting" for line in body
        )
        if accounted and "--findings" not in flags:
            problems.append(
                "the packet carries a prior findings accounting "
                "but the manifest command carries no findings "
                "flag, so the command of record denies the input "
                "that produced the accounting"
            )
    if "--out" not in flags:
        problems.append(
            "the manifest command carries no output flag, and "
            "the extractor requires one on every run"
        )
    elif not last_flag(flags, "--out"):
        problems.append(
            "the manifest command output flag carries an empty "
            "value"
        )
    if "--repo" in flags and not last_flag(flags, "--repo"):
        problems.append(
            "the manifest command repository flag carries an "
            "empty value"
        )
    return problems


def command_warnings(manifest, repo):
    """The recorded spellings that moved and are worth a warning.

    A symbolic range spelling names whatever it resolves to in
    the checking repository, and it can honestly have moved
    since the run, so a moved spelling warns rather than
    refuses. The stamp covers the recorded hashes, and the
    warning tells the reader the names in the packet were not
    the names those hashes now travel under.
    """
    warnings = []
    flags, parse_problems = parse_command_flags(manifest)
    if flags is None or parse_problems or repo is None:
        return warnings
    if "--range" in flags:
        value = last_flag(flags, "--range")
        if "..." in value:
            left, _, right = value.partition("...")
        elif ".." in value:
            left, _, right = value.partition("..")
        else:
            left = right = ""
        for spelling, recorded, field in (
            (left, manifest.get("base"), "base"),
            (right, manifest.get("head"), "head"),
        ):
            if not spelling or HEX40_REF.match(spelling):
                continue
            resolved = resolve_ref(repo, spelling)
            if resolved is not None and recorded is not None \
                    and resolved != recorded:
                warnings.append(
                    "the recorded range spelling %s now resolves "
                    "to %s in this repository, while the packet "
                    "records %s %s, so the stamp covers the "
                    "recorded hashes and not the spelling as it "
                    "now reads"
                    % (spelling, resolved, field, recorded)
                )
    if "--since" in flags and manifest.get("since") is not None:
        value = last_flag(flags, "--since")
        if not HEX40_REF.match(value) \
                and resolve_ref(repo, value) is None:
            warnings.append(
                "the recorded since spelling %s cannot be "
                "resolved in this repository, so the re-review "
                "anchor was checked against the recorded hash "
                "alone" % value
            )
    return warnings


def identity_problems(manifest, extractor, repo=None, packet_text=None):
    problems = []
    problems.extend(
        command_problems(manifest, repo, packet_text, extractor)
    )
    if extractor is not None and \
            manifest["version"] != extractor.EXTRACTOR_VERSION:
        problems.append(
            "the manifest records extractor version %s, but the "
            "extractor in this tree is version %s"
            % (manifest["version"], extractor.EXTRACTOR_VERSION)
        )
    if manifest["mode"] == "pr":
        if not isinstance(manifest["pr"], dict):
            problems.append(
                "the manifest records a pull request packet but "
                "carries no pull request record"
            )
        elif manifest["label"] != "pull request %d" % manifest["pr"]["number"]:
            problems.append(
                "the manifest label does not name the pull request "
                "its record carries"
            )
    elif manifest["pr"] is not None:
        problems.append(
            "the manifest carries a pull request record for a "
            "packet that is not a pull request packet"
        )
    if manifest["mode"] == "commit":
        wanted = "commit %s" % manifest["head"][:12]
        if manifest["label"] != wanted:
            problems.append(
                "the manifest label does not name the commit its "
                "head records"
            )
    if manifest["mode"] == "range":
        flags, _parse = parse_command_flags(manifest)
        spec = last_flag(flags, "--range") if flags else None
        if spec is not None and manifest["label"] != "range %s" % spec:
            problems.append(
                "the manifest label %s does not name the range "
                "its command records, which is range %s"
                % (ascii(manifest["label"])[:60], spec)
            )
    return problems


PRIOR_PRS_HEADING = "### Prior pull requests touching these files"


def mask_prior_prs(text):
    """Mask the one tier passage a rebuild cannot reproduce.

    The prior pull requests passage reads the GitHub CLI when
    the environment carries it, so the checker environment and
    the generation environment can honestly produce different
    text there. The passage is masked in both the packet and
    the rebuild before they are compared, and its heading must
    still stand in both, because the mask only engages where
    the heading stands.
    """
    start = text.find(PRIOR_PRS_HEADING)
    if start == -1:
        return text
    end = text.find("\n### Cap notes", start)
    if end == -1:
        return text[:start] + "<prior pull requests passage>\n"
    return text[:start] + "<prior pull requests passage>" + text[end:]


FINDING_VERDICTS = (
    "unaddressed, the file never existed at the previous "
    "reviewed revision or at the head",
    "unaddressed, the file did not exist at the previous "
    "reviewed revision, so no anchored line was reviewed then",
    "addressed, the file is gone at the head",
    "addressed, the anchored lines changed",
    "unaddressed, the anchored lines are unchanged",
)

NO_FINDINGS_LINE = (
    "A findings file was given for this run and it contained "
    "no findings, so there is nothing to account for."
)


def unescape_display_path(text):
    """Reverse the display path escaping the extractor prints."""
    out = []
    index = 0
    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text):
            kind = text[index + 1]
            if kind == "\\":
                out.append("\\")
                index += 2
                continue
            if kind == "n":
                out.append("\n")
                index += 2
                continue
            if kind == "r":
                out.append("\r")
                index += 2
                continue
            if kind == "t":
                out.append("\t")
                index += 2
                continue
            if kind == "x":
                try:
                    out.append(chr(int(text[index + 2:index + 4], 16)))
                except ValueError:
                    out.append(char)
                    index += 1
                    continue
                index += 4
                continue
            if kind == "u":
                try:
                    out.append(chr(int(text[index + 2:index + 6], 16)))
                except ValueError:
                    out.append(char)
                    index += 1
                    continue
                index += 6
                continue
        out.append(char)
        index += 1
    return "".join(out)


def parse_packet_findings(span):
    """Read the findings a re-review section accounts for.

    Returns the findings list, whether a findings file was
    given, and the padding the rebuild needs. The packet lines
    are the only record of the findings file the checker is
    handed, so the findings are read back out of the lines
    themselves and the rebuild then recomputes every verdict
    from the repository. The duplicate and cap lines are read
    back as counts, and the rebuild input is padded with copies
    and with entries past the cap so those counts are recomputed
    rather than trusted.
    """
    lines = span.split("\n")
    if "### Prior findings accounting" not in lines:
        return [], False, []
    if NO_FINDINGS_LINE in lines:
        return [], True, []
    findings = []
    duplicates = 0
    capped_total = None
    in_accounting = False
    bad_lines = []
    for line in lines:
        if line == "### Prior findings accounting":
            in_accounting = True
            continue
        if not in_accounting:
            continue
        dup = re.match(
            r"^([0-9]+) duplicate finding entries were removed "
            r"before accounting",
            line,
        )
        if dup:
            duplicates = int(dup.group(1))
            continue
        cap = re.match(
            r"^Findings capped at ([0-9]+) of ([0-9]+)\.", line
        )
        if cap:
            capped_total = int(cap.group(2))
            continue
        if line.startswith("- "):
            verdict = None
            for candidate in FINDING_VERDICTS:
                if line.endswith(". " + candidate):
                    verdict = candidate
                    break
            if verdict is None:
                bad_lines.append(line)
                continue
            core = line[2:-(len(verdict) + 2)]
            match = re.match(r"^(.*?):([0-9]+) (.*)$", core)
            if not match:
                bad_lines.append(line)
                continue
            findings.append({
                "path": unescape_display_path(match.group(1)),
                "line": int(match.group(2)),
                "text": match.group(3),
            })
    padding = []
    if duplicates and findings:
        padding.extend([dict(findings[0])] * duplicates)
    if capped_total is not None and capped_total > len(findings):
        for index in range(capped_total - len(findings)):
            padding.append({
                "path": "cap padding %d.py" % index,
                "line": 1,
                "text": "padding past the accounting cap",
            })
    return findings, True, padding + bad_lines


def resolve_findings_file(findings_path, packet_dir):
    """Resolve the recorded findings path against its pinned base.

    An absolute spelling stands as it stands. A relative
    spelling resolves against the directory that holds the
    packet directory, never against the working directory the
    check itself was launched from, so the same packet and the
    same findings file give the same verdict from every
    directory. The packet directory itself is a sealed pair
    and a findings file cannot lawfully stand inside it, so a
    relative spelling names a file beside the pair, in the
    directory that holds it.
    """
    candidate = Path(findings_path)
    if candidate.is_absolute():
        return candidate
    if packet_dir is not None:
        return Path(packet_dir).resolve().parent / candidate
    return candidate


def rereview_problems(packet_text, manifest, repo, extractor,
                      packet_dir=None):
    """Rebuild the re-review section and compare it whole.

    The section rests on the since anchor and on a findings
    file. When the file the recorded command names is still
    where the run left it, its findings are read directly and
    the rebuild stands on them alone. A relative findings
    spelling is resolved against the pinned base the resolver
    above names, so a file that merely shares the spelling in
    the directory the check was launched from is never read
    and a genuine file beside the packet is never missed for
    that reason. When the file is not at the pinned path, the
    anchor, the commit list and the range diff are still
    readings of the repository, and the findings are read back
    out of the packet lines, so the whole section can be
    rebuilt and every verdict in it recomputed. A forged
    verdict, an invented accounting and a body written for a
    different anchor all disagree with the rebuild. In the
    fallback reading a finding invented whole, whose path and
    text no findings file ever carried, cannot be told from a
    real one, and that limit is recorded in the fix report
    rather than hidden.
    """
    problems = []
    span = span_text(packet_text, "## Re-review")
    if span is None:
        return [
            "the manifest records a since ref but the packet "
            "carries no re-review section"
        ]
    flags, _parse = parse_command_flags(manifest)
    findings_path = last_flag(flags, "--findings") if flags else None
    findings_file = None
    if findings_path:
        findings_file = resolve_findings_file(findings_path, packet_dir)
    if findings_file is not None and findings_file.is_file():
        # The findings file the command records is still where
        # the run left it, so its findings are the ground truth
        # and no reading of the packet lines is needed at all.
        try:
            findings_bytes = findings_file.read_bytes()
            findings_text = findings_bytes.decode(
                "utf-8", "surrogateescape"
            )
            recorded_findings = extractor.parse_findings(findings_text)
        except Exception as exc:
            return [
                "the findings file the manifest command records "
                "cannot be read back, so the re-review accounting "
                "cannot be verified (%s)" % exc
            ]
        recorded_hash = manifest.get("findings_sha256")
        if recorded_hash is not None:
            actual_hash = hashlib.sha256(findings_bytes).hexdigest()
            if actual_hash != recorded_hash:
                return [
                    "the findings file the manifest command "
                    "records hashes to %s, which is not the "
                    "findings hash %s the manifest records, so "
                    "the file the run used is not the file "
                    "standing there" % (actual_hash, recorded_hash)
                ]
        header_problems = extractor.findings_header_problems(
            findings_text, manifest["head"], manifest["since"]
        )
        if header_problems:
            return [
                "the findings file the manifest command records "
                "does not belong to this run: %s" % header_problems[0]
            ]
        diff_base = manifest["merge_base"] or EMPTY_TREE
        try:
            expected = extractor.build_rereview(
                repo, diff_base, manifest["head"], manifest["since"],
                recorded_findings, findings_given=True,
            )
        except Exception as exc:
            return [
                "the re-review rebuild could not run (%s)" % exc
            ]
        if span != expected:
            problems.append(
                "the re-review section disagrees with the "
                "re-review the recount rebuilds from the "
                "repository, its since anchor and the findings "
                "file the command records"
            )
        return problems
    findings, given, extra = parse_packet_findings(span)
    bad_lines = [item for item in extra if isinstance(item, str)]
    rebuild_input = findings + [
        item for item in extra if isinstance(item, dict)
    ]
    if bad_lines:
        problems.append(
            "a finding line in the re-review section carries no "
            "verdict the extractor writes, so the accounting "
            "cannot be read back"
        )
        return problems
    diff_base = manifest["merge_base"] or EMPTY_TREE
    try:
        expected = extractor.build_rereview(
            repo, diff_base, manifest["head"], manifest["since"],
            rebuild_input, findings_given=given,
        )
    except Exception as exc:
        problems.append(
            "the re-review rebuild could not run (%s)" % exc
        )
        return problems
    if span != expected:
        problems.append(
            "the re-review section disagrees with the re-review "
            "the recount rebuilds from the repository, its since "
            "anchor and the findings the section itself carries"
        )
    return problems


def fetch_pr_view(repo, number):
    """Read the pull request record from the GitHub CLI, or None.

    The extractor reads the same record the same way when it
    builds a pull request packet. A checker environment without
    a working CLI cannot reach that record, and the caller then
    falls back to the readings the packet itself carries.
    """
    try:
        result = subprocess.run(
            [
                "gh", "pr", "view", str(number), "--json",
                "baseRefOid,headRefOid,title,body",
            ],
            cwd=str(repo),
            capture_output=True,
            text=True,
            env=scrubbed_child_env(),
            timeout=PROCESS_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout)
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def parse_pr_body(packet_text):
    """Read the pull request body back out of the triage tier.

    Returns the body text, an empty string for a packet that
    records no body, and None when the body was capped in the
    packet, because a capped body cannot be read back whole.
    """
    body = section_body(packet_text, "## T0 Triage")
    if body is None:
        return None
    try:
        at = body.index("### Pull request body")
    except ValueError:
        return None
    rest = [line for line in body[at + 1:] if line.strip()]
    if not rest:
        return None
    if rest[0] == "The pull request has no body.":
        return ""
    fence = rest[0]
    ticks = len(fence) - len(fence.lstrip("`"))
    if ticks < 3 or fence.strip("`"):
        return None
    inner = []
    for line in body[at + 1:]:
        if not inner and line != fence:
            continue
        if inner and line == fence:
            tail = [
                item for item in body[at + 1:] if item.strip()
            ]
            capped = any(
                item.startswith("The body was capped at ")
                for item in tail
            )
            return None if capped else "\n".join(inner[1:])
        inner.append(line)
    return None


def pr_state_line(pr_record):
    """The triage line that presents the pull request state.

    The wording matches the line the extractor builder prints,
    because this reading is the presence form of that line for
    a packet whose body cannot be read back. The state is the
    state the extractor fetched when the packet was built and
    the line names its fetch moment, so the packet presents the
    state as the snapshot it is and never as a live claim.
    """
    if not isinstance(pr_record, dict) or not pr_record.get("state"):
        return None
    return (
        "Pull request state at fetch time: %s, recorded at %s. "
        "The state is a snapshot from that fetch and is not a "
        "live claim."
        % (pr_record["state"], pr_record.get("state_as_of", ""))
    )


def pr_triage_problems(packet_text, manifest, repo, fresh_change,
                       extractor):
    """Rebuild the pull request triage tier and compare it whole.

    A pull request packet skips the deterministic rebuild the
    other modes get, because its preamble rests on the pull
    request record. That record is read back here. When the
    GitHub CLI in the checking environment answers, its title
    and body are the ground truth, the spec references are
    recomputed from that body, the base and head identifiers
    in that same record are compared against the manifest base
    and head, and the manifest record must equal all of them.
    No identifier the view carries is fetched and left unread.
    The branch names the view also offers are no longer
    requested, because no surface in the pair records a branch
    name for them to be compared against. The live state of
    the pull request is not compared against the recorded
    state, because the recorded state is a snapshot from the
    fetch that built the packet and a state that has since
    moved does not falsify it. The rebuild carries the recorded
    state and its fetch moment from the manifest, so the
    packet line that presents them is compared whole. When the
    CLI does not answer, the body is read back out of the
    packet and the spec references are recomputed from it,
    which pins the manifest record and the preamble against
    each other and against the body the packet carries. A body
    that cannot be read back takes the presence only reading
    only where the packet carries the cap line the builder
    writes for a capped body. A body whose fence is damaged or
    missing, with no cap line standing, is refused, because a
    mutation of the packet alone must not convert the whole
    rebuild into a presence only reading in silence. A title
    forged in the manifest and the packet together, in an
    environment with no CLI, is the shape that still stands,
    and it is recorded in the fix report.
    """
    problems = []
    recorded = manifest["pr"]
    data = fetch_pr_view(repo, recorded["number"])
    if data is not None:
        title = data.get("title") or ""
        body_text = data.get("body") or ""
        spec = extractor.find_spec_references(body_text)
        if recorded["title"] != title:
            problems.append(
                "the manifest pull request title %s disagrees "
                "with the title the GitHub CLI reports, %s"
                % (ascii(recorded["title"])[:60], ascii(title)[:60])
            )
        if recorded["spec_references"] != spec:
            problems.append(
                "the manifest pull request spec references "
                "disagree with the references in the body the "
                "GitHub CLI reports"
            )
        for key, field in (
            ("baseRefOid", "base"), ("headRefOid", "head")
        ):
            reported = data.get(key)
            if not reported:
                problems.append(
                    "the pull request record the GitHub CLI "
                    "reports carries no %s, so the %s the packet "
                    "records cannot be checked against the pull "
                    "request as it stands" % (key, field)
                )
            elif reported != manifest.get(field):
                problems.append(
                    "the manifest records %s %s but the pull "
                    "request record the GitHub CLI reports names "
                    "%s %s, so the packet range no longer matches "
                    "the pull request it names"
                    % (
                        field, manifest.get(field), key, reported,
                    )
                )
        pr_info = {
            "number": recorded["number"], "title": title,
            "body": body_text, "spec_references": spec,
            "state": recorded.get("state"),
            "state_as_of": recorded.get("state_as_of"),
        }
    else:
        body_text = parse_pr_body(packet_text)
        if body_text is None:
            body = section_body(packet_text, "## T0 Triage") or []
            capped = any(
                line.startswith("The body was capped at ")
                for line in body
            )
            if not capped:
                problems.append(
                    "the pull request body in the triage tier "
                    "cannot be read back and the packet carries "
                    "no cap line for it, so its fence is damaged "
                    "or missing and the packet is refused rather "
                    "than checked on the presence of its title "
                    "and spec reference lines alone"
                )
                return problems
            line = "Pull request #%d: %s" % (
                recorded["number"], recorded["title"]
            )
            if line not in body:
                problems.append(
                    "the triage tier does not carry the pull "
                    "request title line its manifest records"
                )
            state_line = pr_state_line(recorded)
            if state_line is not None and state_line not in body:
                problems.append(
                    "the triage tier does not carry the pull "
                    "request state line its manifest records"
                )
            if recorded["spec_references"]:
                wanted = (
                    "Spec references found in the body: %s"
                    % ", ".join(recorded["spec_references"])
                )
            else:
                wanted = (
                    "No spec reference was found in the pull "
                    "request body."
                )
            if wanted not in body:
                problems.append(
                    "the triage tier does not carry the spec "
                    "reference line its manifest records"
                )
            return problems
        spec = extractor.find_spec_references(body_text)
        if recorded["spec_references"] != spec:
            problems.append(
                "the manifest pull request spec references "
                "disagree with the references in the body the "
                "packet itself carries"
            )
        pr_info = {
            "number": recorded["number"],
            "title": recorded["title"], "body": body_text,
            "spec_references": recorded["spec_references"],
            "state": recorded.get("state"),
            "state_as_of": recorded.get("state_as_of"),
        }
    expected = extractor.build_t0(
        fresh_change["files"], fresh_change["commit_log"], pr_info
    )
    if span_text(packet_text, "## T0 Triage") != expected:
        problems.append(
            "the triage tier disagrees with the tier the recount "
            "rebuilds from the pull request record"
        )
    return problems


def rebuild_problems(packet_text, manifest, repo, fresh_change, extractor,
                     packet_dir=None):
    """Rebuild the deterministic tiers and compare them whole.

    Token accounting catches a tier that shrinks or grows, but
    a same length edit inside a tier body keeps its measure.
    The triage, change, companion and history tiers are
    deterministic readings of the repository, so the checker
    rebuilds them with the extractor's own builders and
    compares the text, which catches an edit of any size. The
    change tier rebuild stands on the recount chunks and the
    recount file records, so every line of that tier, the tier
    introduction and the prose inside a file section outside
    its diff fence included, is compared against builder
    output and no free prose can stand there. The builders also hand
    back the cap notes and the tier sizes, and those readings
    pin the manifest cap notes list and the recorded size of a
    dropped tier, two accounts the packet receipt lines alone
    cannot pin because they are printed from the accounts
    themselves. The re-review section and the pull request
    preamble are rebuilt by their own passes above, from the
    repository and from the records those sections stand on.
    """
    problems = []
    if fresh_change is None or extractor is None:
        return problems
    files = fresh_change["files"]
    chunks = fresh_change["chunks"]
    functions = {
        entry["path"]: extractor.extract_function_names(
            chunks.get(entry["path"], "")
        )
        for entry in files
    }
    head = manifest["head"]
    tiers = manifest["tiers"]
    notes = []
    try:
        if manifest["mode"] == "pr":
            problems.extend(pr_triage_problems(
                packet_text, manifest, repo, fresh_change, extractor
            ))
        else:
            expected = extractor.build_t0(
                files, fresh_change["commit_log"], None
            )
            if span_text(packet_text, "## T0 Triage") != expected:
                problems.append(
                    "the triage tier disagrees with the tier the "
                    "recount rebuilds from the repository"
                )
        if tiers["T1"]["state"] == "included":
            expected_t1 = extractor.build_t1(files, chunks)
            if span_text(packet_text, "## T1 The change") != expected_t1:
                problems.append(
                    "the change tier disagrees with the change "
                    "tier the recount rebuilds from the repository, "
                    "so a line in it was inserted, removed or "
                    "rewritten after the run"
                )
        if tiers["T2"]["state"] != "not selected":
            text2, notes2, count2 = extractor.build_t2(
                repo, head, files, functions
            )
            notes.extend(notes2)
            if tiers["T2"]["state"] == "included":
                if span_text(packet_text, "## T2 Companions") != text2:
                    problems.append(
                        "the companion tier disagrees with the "
                        "tier the recount rebuilds from the "
                        "repository"
                    )
            else:
                if tiers["T2"]["estimated_tokens"] != \
                        extractor.estimate_tokens(text2):
                    problems.append(
                        "the manifest records the dropped T2 tier "
                        "at %d tokens, but the recount rebuilds "
                        "that tier at %d tokens"
                        % (tiers["T2"]["estimated_tokens"],
                           extractor.estimate_tokens(text2))
                    )
                if tiers["T2"]["files"] != count2:
                    problems.append(
                        "the manifest tier receipt for T2 names "
                        "%d files, but the recount finds %d "
                        "changed source files"
                        % (tiers["T2"]["files"], count2)
                    )
        if tiers["T3"]["state"] != "not selected":
            ranges = {
                entry["path"]: extractor.changed_ranges(
                    fresh_change["precise_chunks"].get(entry["path"], "")
                )
                for entry in files
            }
            text3, notes3, count3 = extractor.build_t3(
                repo, head, files, fresh_change["stats"], ranges,
                functions,
            )
            notes.extend(notes3)
            if tiers["T3"]["state"] == "included":
                actual = span_text(packet_text, "## T3 History")
                if actual is None or \
                        mask_prior_prs(actual) != mask_prior_prs(text3):
                    problems.append(
                        "the history tier disagrees with the tier "
                        "the recount rebuilds from the repository"
                    )
                recorded_passage = manifest.get(
                    "prior_pull_requests_passage"
                )
                if actual is not None and recorded_passage is not None and \
                        extractor.prior_prs_passage(actual) != \
                        recorded_passage:
                    problems.append(
                        "the manifest records a prior pull requests "
                        "passage that the packet history tier does "
                        "not carry"
                    )
            else:
                recorded_passage = manifest.get(
                    "prior_pull_requests_passage"
                )
                if recorded_passage is not None:
                    settled3 = extractor.settled_history_text(
                        text3, recorded_passage
                    )
                else:
                    settled3 = text3
                if tiers["T3"]["estimated_tokens"] != \
                        extractor.estimate_tokens(settled3):
                    problems.append(
                        "the manifest records the dropped T3 tier "
                        "at %d tokens, but the recount rebuilds "
                        "that tier at %d tokens against the prior "
                        "pull requests passage the manifest records"
                        % (tiers["T3"]["estimated_tokens"],
                           extractor.estimate_tokens(settled3))
                    )
                if tiers["T3"]["files"] != count3:
                    problems.append(
                        "the manifest tier receipt for T3 names "
                        "%d files, but the recount finds %d files "
                        "with history"
                        % (tiers["T3"]["files"], count3)
                    )
    except Exception as exc:
        problems.append(
            "the tier rebuild could not run (%s)" % exc
        )
        return problems
    if manifest.get("cap_notes") != notes:
        problems.append(
            "the manifest cap notes list %s disagrees with the "
            "cap notes the recount rebuilds from the repository, "
            "%s"
            % (
                ascii(manifest.get("cap_notes"))[:80],
                ascii(notes)[:80],
            )
        )
    if tiers["T2"]["state"] == "included":
        sources = len(extractor.source_entries(files))
        if tiers["T2"]["files"] != sources:
            problems.append(
                "the manifest tier receipt for T2 names %d "
                "files, but the recount finds %d changed source "
                "files" % (tiers["T2"]["files"], sources)
            )
    if tiers["T3"]["state"] == "included":
        top = len(extractor.top_history_files(
            files, fresh_change["stats"]
        ))
        if tiers["T3"]["files"] != top:
            problems.append(
                "the manifest tier receipt for T3 names %d "
                "files, but the recount finds %d files with "
                "history" % (tiers["T3"]["files"], top)
            )
    if manifest.get("since") is not None:
        problems.extend(rereview_problems(
            packet_text, manifest, repo, extractor,
            packet_dir=packet_dir,
        ))
    return problems


def whole_section_problems(packet_text, manifest, extractor):
    """Compare the framing sections whole against their rebuilds.

    The header, the contents block and the closing recount are
    generated from the manifest data and nothing else, so each
    can be rebuilt with the extractor builders and compared as
    a whole. The line by line readings elsewhere in this pass
    name the field that disagrees, and this reading catches
    what a presence reading cannot, a line inserted into a
    section, a sentence swapped inside a line nobody lists, and
    the descriptive sentence no other check reads back.
    """
    problems = []
    if extractor is None:
        return problems
    totals = manifest_totals(manifest)
    counts = {
        "files": totals["files"], "hunks": totals["hunks"],
        "additions": totals["additions"],
        "deletions": totals["deletions"],
    }
    diff_base = manifest["merge_base"] or EMPTY_TREE
    resolved = {
        "label": manifest["label"], "mode": manifest["mode"],
        "base": manifest["base"], "head": manifest["head"],
        "merge_base": manifest["merge_base"],
        "since": manifest["since"],
    }
    try:
        expected_header = extractor.build_header(
            resolved, diff_base, True, manifest["exclusions"]
        )
        lines = packet_text.split("\n")
        if "Contents" not in lines:
            problems.append(
                "the packet carries no Contents line, and that "
                "line is the marker the header and contents "
                "rebuilds stand on, so the packet is refused "
                "rather than stamped with those two rebuilds "
                "silently skipped"
            )
        if "Contents" in lines:
            actual_header = "\n".join(lines[:lines.index("Contents")])
            if actual_header.rstrip("\n") != \
                    expected_header.rstrip("\n"):
                problems.append(
                    "the packet header disagrees with the header "
                    "the recount rebuilds from the manifest"
                )
        expected_contents = extractor.build_contents(
            counts, manifest["tiers"], manifest["since"]
        )
        if "Contents" in lines:
            start = lines.index("Contents")
            block = []
            for line in lines[start:]:
                if line.startswith("## "):
                    break
                block.append(line)
            if "\n".join(block).rstrip("\n") != \
                    expected_contents.rstrip("\n"):
                problems.append(
                    "the packet contents block disagrees with "
                    "the contents the recount rebuilds from the "
                    "manifest"
                )
        expected_receipt = extractor.render_receipt(
            manifest["budget"]["budget_tokens"],
            manifest["budget"]["estimated_tokens"],
            manifest["tiers"],
            manifest["budget"]["dropped"],
            True, [], counts,
        )
        actual_receipt = span_text(
            packet_text, "## Verification recount"
        )
        if actual_receipt is None or \
                actual_receipt.rstrip("\n") != \
                expected_receipt.rstrip("\n"):
            problems.append(
                "the closing recount section disagrees with "
                "the recount the checker rebuilds from the "
                "manifest, so a line in it was inserted, removed "
                "or rewritten after the run"
            )
    except Exception as exc:
        problems.append(
            "the framing section rebuild could not run (%s)" % exc
        )
    return problems


def body_problems(packet_text, manifest, fresh_change, extractor,
                  repo=".", packet_dir=None):
    problems = []
    totals = manifest_totals(manifest)
    problems.extend(
        rebuild_problems(packet_text, manifest, repo, fresh_change,
                         extractor, packet_dir=packet_dir)
    )
    problems.extend(section_sequence_problems(packet_text, manifest))
    problems.extend(header_problems(packet_text, manifest))
    problems.extend(contents_problems(packet_text, manifest, totals))
    problems.extend(
        triage_problems(packet_text, manifest, fresh_change, extractor)
    )
    problems.extend(
        change_tier_problems(packet_text, manifest, fresh_change, extractor)
    )
    problems.extend(tier_span_problems(packet_text, manifest, extractor))
    problems.extend(receipt_problems(packet_text, manifest, totals, extractor))
    problems.extend(
        whole_section_problems(packet_text, manifest, extractor)
    )
    return problems


def packet_dir_problems(packet_dir):
    """Check the packet directory is the sealed pair the stamp covers.

    The extractor writes exactly two files into the packet
    directory. A further entry standing in the directory, even a
    whole nested packet, is content no manifest receipts, and a
    reader who copies or cites the directory as a whole inherits
    it unreceipted. A packet or a manifest that is a symbolic
    link is just as much a composition, because the bytes the
    check reads then live outside the directory it was handed
    and can be swapped without touching the directory at all.
    A packet directory reached through a linked directory is
    ordinary use and is not a problem, because the pair itself
    still lives together in the directory the link names.
    """
    problems = []
    if not packet_dir.is_dir():
        return problems
    try:
        entries = sorted(
            entry.name for entry in packet_dir.iterdir()
        )
    except OSError as exc:
        return [
            "the packet directory cannot be listed, so its "
            "contents cannot be checked (%s)" % exc
        ]
    for name in entries:
        if name not in ("packet.md", "manifest.json"):
            problems.append(
                "the packet directory holds an entry no manifest "
                "receipts, %s, so the directory is not the sealed "
                "pair the stamp covers" % name
            )
    for name in ("packet.md", "manifest.json"):
        target = packet_dir / name
        if target.is_symlink():
            problems.append(
                "%s in the packet directory is a symbolic link, "
                "so the bytes the check reads do not live in the "
                "directory it was handed" % name
            )
            continue
        try:
            link_count = target.stat().st_nlink
        except OSError:
            continue
        if link_count > 1:
            problems.append(
                "%s in the packet directory is a hard link with "
                "%d links, so the bytes the check reads can be "
                "rewritten through a name outside the directory "
                "it was handed, and the seal the symbolic link "
                "rule states covers that shape too" % (name, link_count)
            )
    return problems


class _VersionAction(argparse.Action):
    """Print the extractor version this check stamps against."""

    def __init__(self, option_strings, dest=None, **kwargs):
        super().__init__(
            option_strings=option_strings, dest=dest, nargs=0, **kwargs
        )

    def __call__(self, parser, namespace, values, option_string=None):
        extractor = load_extractor()
        version = extractor.EXTRACTOR_VERSION if extractor else "unknown"
        print("check_packet.py, extractor version %s" % version)
        parser.exit(0)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="check_packet.py",
        description="Validate a recognitio packet directory.",
    )
    parser.add_argument(
        "--version", action=_VersionAction,
        help="print the extractor version and exit",
    )
    parser.add_argument("packet_dir", help="directory holding the packet")
    parser.add_argument(
        "--repo", default=".",
        help="repository whose current head the packet must match",
    )
    parser.add_argument(
        "--expect-base", default=None,
        help="base the review under way names, as a full commit hash",
    )
    parser.add_argument(
        "--expect-merge-base", default=None,
        help="merge base the review under way names, as a full hash",
    )
    args = parser.parse_args(argv)

    packet_dir = Path(args.packet_dir)
    problems = []
    problems.extend(packet_dir_problems(packet_dir))

    packet_path = packet_dir / "packet.md"
    packet_text = None
    if not packet_path.is_file():
        problems.append("no packet.md in %s" % packet_dir)
    elif packet_path.stat().st_size == 0:
        problems.append(
            "packet.md in %s is empty. A packet with no content "
            "cannot carry a review" % packet_dir
        )
    else:
        try:
            # The packet is read as bytes and decoded directly,
            # because a text mode read translates line endings
            # and a packet holding CRLF content would then
            # measure and compare as a different document than
            # the one the extractor wrote. The decode is strict,
            # because a packet is a UTF-8 document and a packet
            # holding bytes no UTF-8 reader can open, as a packet
            # for a filename carrying a non UTF-8 byte does, is
            # not a document its consumers can be handed.
            packet_text = packet_path.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            problems.append(
                "packet.md is not valid UTF-8, so it is not the "
                "text document its consumers are handed"
            )
        except OSError as exc:
            problems.append("packet.md cannot be read: %s" % exc)

    manifest_path = packet_dir / "manifest.json"
    manifest = None
    manifest_parsed = False
    if not manifest_path.is_file():
        problems.append("no manifest.json in %s" % packet_dir)
    else:
        try:
            manifest_text = manifest_path.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            problems.append("manifest.json cannot be read: %s" % exc)
        else:
            try:
                manifest = strict_json_loads(manifest_text)
                manifest_parsed = True
            except DuplicateKeyError as exc:
                problems.append(
                    "manifest.json carries a repeated key and so "
                    "does not parse as one manifest: %s" % exc
                )
            except json.JSONDecodeError as exc:
                problems.append("manifest.json does not parse: %s" % exc)

    if manifest_parsed and not isinstance(manifest, dict):
        problems.append(
            "manifest.json does not hold a JSON object, so neither "
            "its verified flag nor its recorded head can be checked"
        )
        manifest = None

    if manifest is not None:
        schema_problem_list = manifest_schema_problems(manifest)
        problems.extend(schema_problem_list)
        problems.extend(created_problems(manifest, args.repo))
        if manifest.get("verified") is not True:
            problems.append(
                "the manifest does not report verified. A packet "
                "whose verified flag is false is not a packet"
            )
        schema_sound = not schema_problem_list
        discrepancies = manifest.get("discrepancies")
        if isinstance(discrepancies, list) and discrepancies:
            problems.append(
                "the manifest claims verified but its own "
                "discrepancies list is not empty, so the run that "
                "built it recorded a recount that failed"
            )
        recorded = manifest.get("head")
        state_problems, state_fatal = repo_state_problems(args.repo)
        problems.extend(state_problems)
        head = None
        if not state_fatal:
            head = current_head(args.repo)
            if head is None:
                problems.append(
                    "the repository at %s has no readable head "
                    "commit, so the recorded head cannot be "
                    "checked against it" % args.repo
                )
            elif recorded != head:
                problems.append(
                    "the manifest records head %s but the "
                    "repository head is %s. The packet is stale"
                    % (recorded, head)
                )
        extractor = load_extractor()
        # The deep checks need a schema sound manifest, because
        # they index the record fields directly. A manifest that
        # fails its schema has already failed the stamp, and
        # running the recount against a stripped record would only
        # add noise, or worse, an exception. When the deep checks
        # are skipped the output says so and says why, because a
        # reader who sees one fault named can otherwise take the
        # silence about the rest as a reading of the rest.
        skip_reason = None
        if not schema_sound:
            skip_reason = "the manifest failed its schema"
        elif manifest.get("verified") is not True:
            skip_reason = "the manifest does not report verified"
        elif state_fatal:
            skip_reason = "the repository cannot be recounted from"
        elif head is None:
            skip_reason = "the repository head cannot be read"
        elif not isinstance(recorded, str):
            skip_reason = "the manifest records no head"
        if skip_reason is None:
            problems.extend(
                identity_problems(
                    manifest, extractor, args.repo,
                    packet_text=packet_text,
                )
            )
            problems.extend(tier_receipt_problems(manifest))
            problems.extend(budget_problems(manifest))
            repo_problems = ref_problems(
                args.repo, manifest,
                args.expect_base, args.expect_merge_base,
            )
            problems.extend(repo_problems)
            fresh_change = None
            if not repo_problems:
                recount, fresh_change = recount_problems(
                    args.repo, manifest, extractor
                )
                problems.extend(recount)
            if packet_text is not None:
                if "sections" not in manifest:
                    problems.append(
                        "the manifest records no sections, so the packet "
                        "cannot be checked against it"
                    )
                else:
                    problems.extend(
                        section_problems(packet_text, manifest["sections"])
                    )
                    if "tiers" in manifest:
                        problems.extend(
                            tier_problems(packet_text, manifest["tiers"])
                        )
                    if "files" in manifest:
                        problems.extend(
                            file_problems(packet_text, manifest["files"])
                        )
                    problems.extend(
                        body_problems(
                            packet_text, manifest, fresh_change, extractor,
                            repo=args.repo, packet_dir=packet_dir,
                        )
                    )
        else:
            problems.append(
                "the identity, reference, recount and body checks "
                "were skipped because %s, so faults those checks "
                "would have caught are not named in this output"
                % skip_reason
            )

    if problems:
        for problem in problems:
            print("check_packet: %s" % problem, file=sys.stderr)
        return 1
    for warning in command_warnings(manifest, args.repo):
        print("check_packet: warning: %s" % warning, file=sys.stderr)
    if args.expect_base is None and args.expect_merge_base is None:
        expectation = (
            "the review named no expected range, so the stamp "
            "covers the range the packet records"
        )
    else:
        expectation = (
            "the stamp covers the range the review named with "
            "its expect flags"
        )
    print(
        "check_packet: packet in %s is verified for the current "
        "head %s, covering base %s and merge base %s, and %s"
        % (
            packet_dir, manifest["head"], manifest["base"],
            manifest["merge_base"], expectation,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
