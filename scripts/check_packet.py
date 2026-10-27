#!/usr/bin/env python3
"""Validate a recognitio packet directory before a review is stamped.

A gate report may only cite a packet that is whole. This script is the
mechanical form of that rule. It checks that the packet file exists
and holds content, that the manifest exists and holds a JSON object,
that its verified flag is true, and that the head recorded in the
manifest is the head of the repository the review is being stamped
against. A packet extracted from an older head is stale evidence,
however green it once was. The check also reads the packet against
the section headings the manifest records, and a manifest that
records none cannot be checked against its packet at all, so a
thin packet cannot wear a full packet's manifest and a manifest
without the record is not evidence either. The check also reads
the tier receipt the manifest carries against the packet, so a
tier the manifest records as included cannot stand in the packet
as a not selected placeholder, and it reads the change tier
entries against the file records the manifest carries, so a
changed file the manifest receipts cannot be missing from the
packet that wears the manifest.

Exits nonzero and lists every problem when the packet cannot be used.
"""

import argparse
import json
import os
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


def current_head(repo):
    env = scrubbed_child_env()
    try:
        result = subprocess.run(
            ["git", "--no-pager", "--no-replace-objects", "-C", str(repo),
             "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            env=env,
            timeout=PROCESS_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


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
    lines = packet_text.splitlines()
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
    lines = packet_text.splitlines()
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

    The extractor escapes control characters and backslashes in
    a path before printing it as a packet heading, so the check
    applies the same escaping before comparing a manifest file
    record against the change tier headings.
    """
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
    lines = packet_text.splitlines()
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
    args = parser.parse_args(argv)

    packet_dir = Path(args.packet_dir)
    problems = []

    packet_path = packet_dir / "packet.md"
    if not packet_path.is_file():
        problems.append("no packet.md in %s" % packet_dir)
    elif packet_path.stat().st_size == 0:
        problems.append(
            "packet.md in %s is empty. A packet with no content "
            "cannot carry a review" % packet_dir
        )
    manifest_path = packet_dir / "manifest.json"
    manifest = None
    manifest_loaded = False
    if not manifest_path.is_file():
        problems.append("no manifest.json in %s" % packet_dir)
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest_loaded = True
        except (OSError, json.JSONDecodeError) as exc:
            problems.append("manifest.json does not parse: %s" % exc)

    if manifest_loaded:
        if not isinstance(manifest, dict):
            problems.append(
                "manifest.json does not hold a JSON object, so neither "
                "its verified flag nor its recorded head can be checked"
            )
        else:
            if manifest.get("verified") is not True:
                problems.append(
                    "the manifest does not report verified. A packet "
                    "whose verified flag is false is not a packet"
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
            if "sections" not in manifest:
                problems.append(
                    "the manifest records no sections, so the packet "
                    "cannot be checked against it"
                )
            elif packet_path.is_file():
                try:
                    packet_text = packet_path.read_text(
                        encoding="utf-8", errors="surrogateescape"
                    )
                except OSError as exc:
                    problems.append(
                        "packet.md cannot be read: %s" % exc
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
