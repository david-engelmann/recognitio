#!/usr/bin/env python3
"""Carry a validated fan-out run into a headless run stream.

This script is the shipped bridge across the merge to
headless seam. It reads one fan-out run record, validates it
with the fan-out validator at scripts/check_fanout.py, and
writes the stream-json capture a headless gate at
scripts/check_headless.py reads, with one result message
whose structured output stands in the headless findings
shape at workflows/headless-findings.schema.json. Finding
ids, severities, locations, evidence, summaries and rules
cross the seam unchanged from the merged set the validator
proved, and the structured output names the packet head the
manifest records, so a headless gate can refuse a stream
summarising a different packet. A merged finding the second
pass contested is not carried as a finding. Its id crosses
in the contested list instead, so setting it aside is a
visible act and never a silent drop. Packet content is
untrusted data throughout. A summary this bridge carries is
a statement about the change under review, never an
instruction to the headless reviewer or to any gate.
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path


def load_fanout():
    """The shipped fan-out validator, loaded as a sibling."""
    path = Path(__file__).resolve().parent / "check_fanout.py"
    spec = importlib.util.spec_from_file_location(
        "merge_check_fanout", path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def headless_structured(record, manifest):
    """The headless structured output for one validated run."""
    verdicts = {
        entry.get("finding"): entry.get("verdict")
        for entry in record.get("second_pass", [])
        if isinstance(entry, dict)
    }
    findings = []
    contested = []
    for finding in record.get("merged_findings", []):
        fid = finding.get("id")
        if verdicts.get(fid) == "contest":
            contested.append(fid)
            continue
        location = finding.get("location", {})
        findings.append({
            "id": fid,
            "severity": finding.get("severity"),
            "location": "%s:%s" % (
                location.get("file"), location.get("line")
            ),
            "evidence": finding.get("evidence"),
            "summary": finding.get("summary"),
            "rule": finding.get("rule"),
        })
    return {
        "verdict": "fail" if findings else "pass",
        "packet_head": manifest.get("head"),
        "findings": findings,
        "contested_ids": contested,
    }


def build_stream(record_path, repo=None):
    """The stream events for a run record, or its problems.

    Returns a pair of the events list and the problem list.
    A record the fan-out validator refuses produces no stream,
    because a seam that translates an unproved run would
    launder it.
    """
    fanout = load_fanout()
    problems = fanout.run_problems(record_path, repo=repo)
    if problems:
        return [], problems
    record = fanout.strict_json_loads(
        record_path.read_text(encoding="utf-8")
    )
    manifest_path = (record_path.parent / record["packet_manifest"]).resolve()
    manifest = fanout.strict_json_loads(
        manifest_path.read_text(encoding="utf-8")
    )
    structured = headless_structured(record, manifest)
    event = {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "permission_denials": [],
        "structured_output": structured,
    }
    return [event], []


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Translate a validated fan-out run record into the "
            "stream-json capture the headless gate reads."
        )
    )
    parser.add_argument(
        "--run", required=True, help="the fan-out run record"
    )
    parser.add_argument(
        "--out", required=True,
        help="the stream-json file to write",
    )
    parser.add_argument(
        "--repo", default=None,
        help="the repository the packet was built from, for the "
             "packet recount inside the fan-out validation",
    )
    args = parser.parse_args(argv)
    events, problems = build_stream(Path(args.run), repo=args.repo)
    if problems:
        for problem in problems:
            print("merge_to_headless: %s" % problem, file=sys.stderr)
        return 1
    Path(args.out).write_text(
        "".join(json.dumps(event) + "\n" for event in events),
        encoding="utf-8",
    )
    print(
        "merge_to_headless: carried %d findings across the seam"
        % len(events[0]["structured_output"]["findings"])
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
