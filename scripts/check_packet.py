#!/usr/bin/env python3
"""Validate a recognitio packet directory before a review is stamped.

A gate report may only cite a packet that is whole. This script is the
mechanical form of that rule. It checks that the packet file and the
manifest both exist, that the manifest parses, that its verified flag
is true, and that the head recorded in the manifest is the head of the
repository the review is being stamped against. A packet extracted
from an older head is stale evidence, however green it once was.

Exits nonzero and lists every problem when the packet cannot be used.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def current_head(repo):
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


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
    manifest_path = packet_dir / "manifest.json"
    manifest = None
    if not manifest_path.is_file():
        problems.append("no manifest.json in %s" % packet_dir)
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            problems.append("manifest.json does not parse: %s" % exc)

    if manifest is not None:
        if manifest.get("verified") is not True:
            problems.append(
                "the manifest does not report verified. A packet whose "
                "verified flag is false is not a packet"
            )
        recorded = manifest.get("head")
        head = current_head(args.repo)
        if head is None:
            problems.append(
                "cannot read the current head of %s" % args.repo
            )
        elif recorded != head:
            problems.append(
                "the manifest records head %s but the repository head "
                "is %s. The packet is stale" % (recorded, head)
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
