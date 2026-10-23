#!/usr/bin/env python3
"""Validate a recognitio packet directory before a review is stamped.

A gate report may only cite a packet that is whole. This script is the
mechanical form of that rule. It checks that the packet file exists
and holds content, that the manifest exists and holds a JSON object,
that its verified flag is true, and that the head recorded in the
manifest is the head of the repository the review is being stamped
against. A packet extracted from an older head is stale evidence,
however green it once was. When the manifest records the section
headings it emitted, the check also reads the packet against that
record, so a thin packet cannot wear a full packet's manifest.

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
PROCESS_TIMEOUT_SECONDS = 120


def current_head(repo):
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in GIT_SCRUB_VARS
    }
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    try:
        result = subprocess.run(
            ["git", "--no-replace-objects", "-C", str(repo),
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


def section_problems(packet_text, recorded):
    """Check the packet carries the sections its manifest records.

    Every recorded heading must appear in the packet, and each must
    hold at least one non blank line before the next heading, so a
    section that was promised and gutted is still caught.
    """
    problems = []
    if not isinstance(recorded, list):
        return [
            "the manifest records its sections in a shape that "
            "cannot be checked"
        ]
    lines = packet_text.splitlines()
    positions = {}
    for index, line in enumerate(lines):
        if line.startswith("## ") and line not in positions:
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
        for line in lines[start:]:
            if line.startswith("## "):
                break
            if line.strip():
                filled = True
                break
        if not filled:
            problems.append(
                "the section %s stands in the packet with no content "
                "under it" % heading
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
            if "sections" in manifest and packet_path.is_file():
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
