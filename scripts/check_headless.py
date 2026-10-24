"""Fail closed validation of a headless review run's captured output.

The script reads the stream-json event log of a `claude -p`
review run, the packet manifest of the packet under review,
and the run's exit code, and reports every problem that stops
the run from reading green. A run reads green only when the
exit code is zero, the stream carries a final result message,
that message lists no permission denials, the result carries
structured output, the findings match the expected schema, and
every evidence path a finding cites stands in the packet
manifest's file list. Anything else fails the run, because an
unattended run must never read green on a shape the gate
cannot verify. See docs/headless-review.md for the full
contract and the primary sources behind each rule.
"""

import argparse
import json
import sys
from pathlib import Path

VERDICTS = ("pass", "fail")
REQUIRED_FINDING_KEYS = ("severity", "location", "evidence")


def findings_problems(structured, manifest_files):
    """Problems in the structured findings against the packet."""
    if not isinstance(structured, dict):
        return ["the structured output is not an object"]
    problems = []
    verdict = structured.get("verdict")
    findings = structured.get("findings")
    if verdict not in VERDICTS:
        problems.append("the verdict is not pass or fail")
    if not isinstance(findings, list):
        problems.append("the findings are not a list")
        return problems
    if verdict == "pass" and findings:
        problems.append(
            "the verdict is pass while the run lists findings"
        )
    known = set(manifest_files)
    for index, finding in enumerate(findings):
        where = "finding %d" % index
        if not isinstance(finding, dict):
            problems.append("%s is not an object" % where)
            continue
        for key in REQUIRED_FINDING_KEYS:
            if key not in finding:
                problems.append("%s is missing %r" % (where, key))
        if not isinstance(finding.get("severity"), str) or not isinstance(
            finding.get("location"), str
        ):
            problems.append("%s has no usable severity or location" % where)
        evidence = finding.get("evidence")
        if not isinstance(evidence, list) or not all(
            isinstance(entry, str) for entry in evidence
        ):
            problems.append("%s carries no evidence list" % where)
            continue
        for path in evidence:
            if path not in known:
                problems.append(
                    "%s cites evidence outside the packet: %s" % (where, path)
                )
    return problems


def headless_problems(exit_code, events, manifest_files):
    """Problems in a headless run that stop it reading green."""
    if exit_code != 0:
        return ["the run exited %d, so the run failed" % exit_code]
    result = None
    for event in events:
        if isinstance(event, dict) and event.get("type") == "result":
            result = event
    if result is None:
        return ["the stream carries no result message"]
    denials = result.get("permission_denials") or []
    problems = []
    if not isinstance(denials, list):
        problems.append("the permission_denials field is not a list")
    elif denials:
        problems.append(
            "the run lists %d permission denials" % len(denials)
        )
    structured = result.get("structured_output")
    if structured is None:
        problems.append("the result carries no structured output")
        return problems
    problems.extend(findings_problems(structured, manifest_files))
    return problems


def read_stream(path):
    """The stream-json events, failing closed on a corrupt line."""
    events = []
    problems = []
    for lineno, line in enumerate(
        Path(path).read_text(encoding="utf-8").splitlines(), start=1
    ):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            events.append(json.loads(stripped))
        except json.JSONDecodeError:
            problems.append(
                "stream line %d is not JSON, so the capture is corrupt"
                % lineno
            )
    return events, problems


def read_manifest_files(path):
    """The packet manifest's file list, failing closed when absent."""
    try:
        manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    files = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(files, list):
        return None
    paths = [
        entry.get("path")
        for entry in files
        if isinstance(entry, dict) and isinstance(entry.get("path"), str)
    ]
    return paths


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Fail a headless review run closed when its captured "
            "output cannot prove a clean review."
        )
    )
    parser.add_argument(
        "--stream",
        required=True,
        help="the stream-json event log the run wrote",
    )
    parser.add_argument(
        "--manifest",
        required=True,
        help="the packet manifest of the packet under review",
    )
    parser.add_argument(
        "--exit-code",
        required=True,
        type=int,
        help="the exit code the run exited with",
    )
    args = parser.parse_args(argv)
    events, problems = read_stream(args.stream)
    manifest_files = read_manifest_files(args.manifest)
    if manifest_files is None:
        problems.append("the packet manifest carries no file list")
        manifest_files = []
    problems.extend(headless_problems(args.exit_code, events, manifest_files))
    if problems:
        for problem in problems:
            print(problem)
        return 1
    print("the headless run reads green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
