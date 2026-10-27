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
hash it carries must name the refs the manifest records.

Exits nonzero and lists every problem when the packet cannot be used.
"""

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
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
        and not key.startswith(GIT_CONFIG_ENV_PREFIX)
    }
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    return env


def run_git(repo, args):
    """Run one pinned git read and return its stdout or None."""
    try:
        result = subprocess.run(
            ["git", "--no-pager", "--no-replace-objects",
             "-C", str(repo)] + list(args),
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
                "its schema allows" % where
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
        if "pattern" in schema and not re.search(schema["pattern"], value):
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
            r"(, renamed from (.+))?\)$" % "|".join(STATUS_NAMES),
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
        ))
    expected = []
    for entry in manifest["files"]:
        expected.append((
            display_path(entry["path"]),
            entry["status"],
            entry["instruction_file"],
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
        renamed = [
            line for line in body_lines if line.startswith("Renamed from: ")
        ]
        if entry["old_path"]:
            wanted = ["Renamed from: %s" % display_path(entry["old_path"])]
            if renamed != wanted:
                problems.append(
                    "the change tier section for %s does not carry "
                    "the rename source its manifest record names"
                    % entry["path"]
                )
        elif renamed:
            problems.append(
                "the change tier section for %s carries a rename "
                "source its manifest record does not" % entry["path"]
            )
        if "```diff" not in body_lines:
            problems.append(
                "the change tier section for %s carries no diff "
                "block" % entry["path"]
            )
            continue
        start = body_lines.index("```diff") + 1
        inner = []
        for line in body_lines[start:]:
            if line == "```":
                break
            inner.append(line)
        inner_text = "\n".join(inner)
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
            estimate = len(text) // 4
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
            if len(expected) // 4 != info["emitted_tokens"]:
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


def tier_receipt_problems(manifest):
    problems = []
    tiers = manifest["tiers"]
    selected = manifest["selected_tiers"]
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


def receipt_problems(packet_text, manifest, totals):
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
    if budget["estimated_tokens"] != len(packet_text) // 4:
        problems.append(
            "the manifest packet estimate of %d tokens does not "
            "measure the packet, which measures %d tokens"
            % (budget["estimated_tokens"], len(packet_text) // 4)
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


def command_problems(manifest, repo):
    """Read the recorded extractor command back against the manifest.

    The command is the record of how the packet claims it was
    built, and a forged record must not wear a genuine manifest.
    The mode flag in the command must be the flag for the mode the
    manifest records, and the pull request flag must name the pull
    request the manifest records. A range or commit or since value
    written as a full hash names an immutable commit, so a hash
    that names a different commit than the manifest records, or
    no commit at all, fails. A symbolic spelling names whatever
    it resolves to when the check runs and can honestly have
    moved since the run, so symbolic values are left to the ref
    checks that read the manifest fields themselves.
    """
    problems = []
    command = manifest.get("command")
    if not isinstance(command, list) or not command or \
            Path(str(command[0])).name != "extract.py":
        return [
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
    if problems:
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
        if flags["--pr"][0] != str(manifest["pr"].get("number")):
            problems.append(
                "the manifest command names a different pull "
                "request than the manifest records"
            )
    if "--commit" in flags:
        value = flags["--commit"][0]
        if HEX_REF.match(value) and repo is not None:
            resolved = run_git(
                repo, ["rev-parse", "--verify", value + "^{commit}"]
            )
            if resolved is None or \
                    resolved.strip() != manifest.get("head"):
                problems.append(
                    "the manifest command names a commit other "
                    "than the head the manifest records"
                )
    if "--range" in flags:
        value = flags["--range"][0]
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
        if manifest.get("since") is None:
            problems.append(
                "the manifest command carries a since flag the "
                "manifest does not record"
            )
        elif HEX40_REF.match(flags["--since"][0]) and \
                flags["--since"][0] != manifest["since"]:
            problems.append(
                "the manifest command names a different since ref "
                "than the manifest records"
            )
    return problems


def identity_problems(manifest, extractor, repo=None):
    problems = []
    problems.extend(command_problems(manifest, repo))
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


def rebuild_problems(packet_text, manifest, repo, fresh_change, extractor):
    """Rebuild the deterministic tiers and compare them whole.

    Token accounting catches a tier that shrinks or grows, but
    a same length edit inside a tier body keeps its measure.
    The triage, companion and history tiers are deterministic
    readings of the repository, so the checker rebuilds them
    with the extractor's own builders and compares the text,
    which catches an edit of any size. The pull request tier
    text of a pull request packet and the re-review section
    are not rebuilt, because both rest on inputs the checker
    is not handed, the pull request body and the findings file.
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
    try:
        if manifest["mode"] != "pr":
            expected = extractor.build_t0(
                files, fresh_change["commit_log"], None
            )
            if span_text(packet_text, "## T0 Triage") != expected:
                problems.append(
                    "the triage tier disagrees with the tier the "
                    "recount rebuilds from the repository"
                )
        if tiers["T2"]["state"] == "included":
            expected = extractor.build_t2(repo, head, files, functions)[0]
            if span_text(packet_text, "## T2 Companions") != expected:
                problems.append(
                    "the companion tier disagrees with the tier "
                    "the recount rebuilds from the repository"
                )
        if tiers["T3"]["state"] == "included":
            ranges = {
                entry["path"]: extractor.changed_ranges(
                    fresh_change["precise_chunks"].get(entry["path"], "")
                )
                for entry in files
            }
            expected = extractor.build_t3(
                repo, head, files, fresh_change["stats"], ranges,
                functions,
            )[0]
            actual = span_text(packet_text, "## T3 History")
            if actual is None or \
                    mask_prior_prs(actual) != mask_prior_prs(expected):
                problems.append(
                    "the history tier disagrees with the tier "
                    "the recount rebuilds from the repository"
                )
    except Exception as exc:
        problems.append(
            "the tier rebuild could not run (%s)" % exc
        )
        return problems
    if tiers["T2"]["state"] != "not selected":
        sources = len(extractor.source_entries(files))
        if tiers["T2"]["files"] != sources:
            problems.append(
                "the manifest tier receipt for T2 names %d "
                "files, but the recount finds %d changed source "
                "files" % (tiers["T2"]["files"], sources)
            )
    if tiers["T3"]["state"] != "not selected":
        top = len(extractor.top_history_files(
            files, fresh_change["stats"]
        ))
        if tiers["T3"]["files"] != top:
            problems.append(
                "the manifest tier receipt for T3 names %d "
                "files, but the recount finds %d files with "
                "history" % (tiers["T3"]["files"], top)
            )
    return problems


def body_problems(packet_text, manifest, fresh_change, extractor,
                  repo="."):
    problems = []
    totals = manifest_totals(manifest)
    problems.extend(
        rebuild_problems(packet_text, manifest, repo, fresh_change,
                         extractor)
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
    problems.extend(receipt_problems(packet_text, manifest, totals))
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
        if (packet_dir / name).is_symlink():
            problems.append(
                "%s in the packet directory is a symbolic link, "
                "so the bytes the check reads do not live in the "
                "directory it was handed" % name
            )
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="check_packet.py",
        description="Validate a recognitio packet directory.",
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
        head = current_head(args.repo)
        if head is None:
            problems.append(
                "cannot read the current head of %s" % args.repo
            )
        elif recorded != head:
            problems.append(
                "the manifest records head %s but the repository "
                "head is %s. The packet is stale" % (recorded, head)
            )
        extractor = load_extractor()
        # The deep checks need a schema sound manifest, because
        # they index the record fields directly. A manifest that
        # fails its schema has already failed the stamp, and
        # running the recount against a stripped record would only
        # add noise, or worse, an exception.
        if schema_sound and manifest.get("verified") is True \
                and isinstance(recorded, str):
            problems.extend(
                identity_problems(manifest, extractor, args.repo)
            )
            problems.extend(tier_receipt_problems(manifest))
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
                            repo=args.repo,
                        )
                    )

    if problems:
        for problem in problems:
            print("check_packet: %s" % problem, file=sys.stderr)
        return 1
    print(
        "check_packet: packet in %s is verified for the current head"
        % packet_dir
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
