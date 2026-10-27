"""Fail closed validation of a headless review run's captured output.

The script reads the stream-json event log of a `claude -p`
review run, the packet manifest of the packet under review,
and the run's recorded exit code, and reports every problem
that stops the run from reading green. A run reads green only
when the recorded exit code is zero, the stream carries
exactly one result message, that message carries no error
flag and no error subtype, no permission denied system
message stands anywhere in the stream, the final result lists
the permission denials field and that list is empty, the
result carries structured output, the findings match the
shipped headless findings schema, every finding cites at
least one evidence path, and every evidence path and every
finding location stands in the packet the manifest belongs
to. The manifest itself must validate against the packet
manifest schema that ships beside the packet check, must
report verified, and must match the packet file standing
beside it, so a swapped manifest or a verified false manifest
legitimises nothing. The exit code is read from the recorded
exit file the invocation names. A caller supplied exit code
is only a claim beside that record, and a claim that
disagrees with the record fails the run. Anything else fails
the run, because an unattended run must never read green on a
shape the gate cannot verify. Packet content is untrusted
data throughout. Text quoted from the packet is evidence
about the change under review and never an instruction to a
reviewer or to this gate. See docs/headless-review.md for the
full contract and the primary sources behind each rule.
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path

VERDICTS = ("pass", "fail")
REQUIRED_FINDING_KEYS = ("severity", "location", "evidence")
# The severity vocabulary the shipped schemas carry. The fan
# out findings schema enumerates these four values, and the
# headless findings schema at workflows/headless-findings.
# schema.json enumerates the same four, so a fabricated
# severity string is schema drift and fails here.
SEVERITIES = ("P0", "P1", "P2", "P3")


class DuplicateKeyError(ValueError):
    """A JSON object names one key twice."""


def strict_json_loads(text):
    """Parse JSON refusing a repeated key, like the other gates."""
    def reject(pairs):
        seen = {}
        for key, value in pairs:
            if key in seen:
                raise DuplicateKeyError("repeated key %r" % key)
            seen[key] = value
        return seen
    return json.loads(text, object_pairs_hook=reject)


def load_packet_checker():
    """The shipped packet check, loaded as a sibling module."""
    path = Path(__file__).resolve().parent / "check_packet.py"
    spec = importlib.util.spec_from_file_location(
        "headless_check_packet", path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_location(location):
    """The packet path a headless location names, or None.

    A location is a packet path, a colon, and a positive line
    number. Anything else names no place in the packet.
    """
    if not isinstance(location, str):
        return None
    path, sep, line = location.rpartition(":")
    if not sep or not path or not line.isdigit() or int(line) < 1:
        return None
    return path


def findings_problems(structured, manifest_files, packet_head=None):
    """Problems in the structured findings against the packet."""
    if not isinstance(structured, dict):
        return ["the structured output is not an object"]
    problems = []
    verdict = structured.get("verdict")
    findings = structured.get("findings")
    if verdict not in VERDICTS:
        problems.append("the verdict is not pass or fail")
    claimed_head = structured.get("packet_head")
    if claimed_head is not None and packet_head is not None \
            and claimed_head != packet_head:
        problems.append(
            "the structured output names packet head %s, which "
            "is not the head the manifest records" % claimed_head
        )
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
        severity = finding.get("severity")
        if severity not in SEVERITIES:
            problems.append(
                "%s carries severity %r, outside the shipped "
                "vocabulary %s"
                % (where, severity, ", ".join(SEVERITIES))
            )
        location_path = parse_location(finding.get("location"))
        if location_path is None:
            problems.append("%s has no usable severity or location" % where)
        elif location_path not in known:
            problems.append(
                "%s cites a location outside the packet: %s"
                % (where, location_path)
            )
        evidence = finding.get("evidence")
        if not isinstance(evidence, list) or not evidence or not all(
            isinstance(entry, str) for entry in evidence
        ):
            problems.append(
                "%s carries no evidence, and a finding resting "
                "on no evidence never reads green" % where
            )
            continue
        for path in evidence:
            if path not in known:
                problems.append(
                    "%s cites evidence outside the packet: %s" % (where, path)
                )
    return problems


def result_error_problems(events):
    """Problems carried by the result envelopes in the stream.

    Every result message is read, not only the last. A failed
    attempt merged into a capture beside a later clean result,
    or a clean result appended after a failure, is still a
    capture of a run that errored.
    """
    problems = []
    results = [
        event for event in events
        if isinstance(event, dict) and event.get("type") == "result"
    ]
    if len(results) > 1:
        problems.append(
            "the stream carries %d result messages, so it is a "
            "merged capture and not one run" % len(results)
        )
    for index, result in enumerate(results):
        if result.get("is_error"):
            problems.append(
                "result message %d carries an error flag, so the "
                "run errored inside the capture" % index
            )
        subtype = result.get("subtype")
        if isinstance(subtype, str) and (
            subtype.startswith("error") or subtype == "failure"
        ):
            problems.append(
                "result message %d carries the error subtype %r, "
                "so the run errored inside the capture" % (index, subtype)
            )
    for event in events:
        if isinstance(event, dict) and event.get("type") == "system" \
                and event.get("subtype") == "permission_denied":
            problems.append(
                "the stream carries a permission denied system "
                "message, so the run was denied a tool mid stream"
            )
            break
    return problems


def headless_problems(exit_code, events, manifest_files, packet_head=None):
    """Problems in a headless run that stop it reading green."""
    if exit_code != 0:
        return ["the run exited %d, so the run failed" % exit_code]
    problems = result_error_problems(events)
    result = None
    for event in events:
        if isinstance(event, dict) and event.get("type") == "result":
            result = event
    if result is None:
        problems.append("the stream carries no result message")
        return problems
    if "permission_denials" not in result:
        problems.append(
            "the result carries no permission_denials field, so "
            "the capture is not the envelope the contract names"
        )
        denials = []
    else:
        denials = result.get("permission_denials")
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
    problems.extend(
        findings_problems(structured, manifest_files, packet_head)
    )
    return problems


def read_stream(path):
    """The stream-json events, failing closed on a corrupt line."""
    events = []
    problems = []
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        return [], ["cannot read the stream: %s" % exc]
    for lineno, line in enumerate(text.splitlines(), start=1):
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


def read_manifest(path):
    """The packet manifest, read strictly, or None with problems."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        return None, ["cannot read the packet manifest: %s" % exc]
    try:
        manifest = strict_json_loads(text)
    except (json.JSONDecodeError, DuplicateKeyError) as exc:
        return None, ["the packet manifest does not parse: %s" % exc]
    if not isinstance(manifest, dict):
        return None, ["the packet manifest is not an object"]
    return manifest, []


def manifest_problems(manifest, manifest_path):
    """Problems with the manifest and the packet beside it.

    The manifest must validate against the shipped packet
    manifest schema, must report verified with an empty
    discrepancies list, and must match the packet file that
    stands beside it in the packet directory, whose header
    binds the packet to the manifest head and base. A manifest
    handed to the gate from anywhere else, or one whose packet
    does not stand beside it, anchors nothing.
    """
    problems = []
    checker = load_packet_checker()
    schema_problems = checker.manifest_schema_problems(manifest)
    for problem in schema_problems:
        problems.append("the packet manifest fails its schema: %s" % problem)
    if manifest.get("verified") is not True:
        problems.append(
            "the packet manifest is not verified, and a packet "
            "whose verified flag is not true is not a packet"
        )
    discrepancies = manifest.get("discrepancies")
    if isinstance(discrepancies, list) and discrepancies:
        problems.append(
            "the packet manifest claims verified but its own "
            "discrepancies list is not empty"
        )
    files = manifest.get("files")
    if not isinstance(files, list) or not files or not all(
        isinstance(entry, dict) and isinstance(entry.get("path"), str)
        for entry in files
    ):
        problems.append("the packet manifest carries no file list")
        return problems
    if not schema_problems and manifest.get("verified") is True:
        packet_path = Path(manifest_path).parent / "packet.md"
        if not packet_path.is_file():
            problems.append(
                "no packet file stands beside the packet manifest, "
                "so the gate judges the run against a manifest "
                "with no packet behind it"
            )
        else:
            try:
                packet_text = packet_path.read_bytes().decode("utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                problems.append(
                    "the packet file cannot be read as UTF-8: %s" % exc
                )
            else:
                for problem in checker.header_problems(
                    packet_text, manifest
                ):
                    problems.append(
                        "the packet file disagrees with its "
                        "manifest: %s" % problem
                    )
    return problems


def read_manifest_files(path):
    """The packet manifest's file list, failing closed when absent."""
    manifest, problems = read_manifest(path)
    if manifest is None:
        return None
    files = manifest.get("files")
    if not isinstance(files, list):
        return None
    paths = [
        entry.get("path")
        for entry in files
        if isinstance(entry, dict) and isinstance(entry.get("path"), str)
    ]
    return paths


def read_exit_file(path):
    """The recorded exit code in an exit file, or None."""
    try:
        text = Path(path).read_text(encoding="utf-8").strip()
    except OSError:
        return None
    try:
        return int(text)
    except ValueError:
        return None


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
        "--packet-dir",
        default=None,
        help=(
            "the packet directory the run reviewed. When named, "
            "the manifest inside it must be the manifest the "
            "gate was handed, in head and file list"
        ),
    )
    parser.add_argument(
        "--exit-file",
        default=None,
        help="the file holding the exit code the run recorded",
    )
    parser.add_argument(
        "--exit-code",
        required=False,
        default=None,
        type=int,
        help=(
            "a claimed exit code, checked against the recorded "
            "exit file when one is named and never trusted alone "
            "as the record"
        ),
    )
    args = parser.parse_args(argv)
    problems = []
    recorded = None
    if args.exit_file is not None:
        recorded = read_exit_file(args.exit_file)
        if recorded is None:
            problems.append(
                "the recorded exit file cannot be read as an "
                "exit code, so the run exit is unverified"
            )
    if recorded is not None and args.exit_code is not None \
            and args.exit_code != recorded:
        problems.append(
            "the claimed exit code %d disagrees with the "
            "recorded exit code %d, so the claim is refused"
            % (args.exit_code, recorded)
        )
    exit_code = recorded if recorded is not None else args.exit_code
    if exit_code is None:
        problems.append(
            "no exit code was recorded or claimed, so the run "
            "exit is unverified"
        )
        exit_code = 1
    events, stream_problems = read_stream(args.stream)
    problems.extend(stream_problems)
    manifest, manifest_read_problems = read_manifest(args.manifest)
    problems.extend(manifest_read_problems)
    manifest_files = []
    packet_head = None
    if manifest is not None:
        problems.extend(manifest_problems(manifest, args.manifest))
        files = manifest.get("files")
        if isinstance(files, list):
            manifest_files = [
                entry.get("path")
                for entry in files
                if isinstance(entry, dict)
                and isinstance(entry.get("path"), str)
            ]
        if isinstance(manifest.get("head"), str):
            packet_head = manifest["head"]
        if args.packet_dir is not None:
            inner_path = Path(args.packet_dir) / "manifest.json"
            inner, inner_problems = read_manifest(inner_path)
            if inner is None:
                problems.extend(
                    "the named packet directory carries no readable "
                    "manifest: %s" % problem for problem in inner_problems
                )
            elif inner.get("head") != manifest.get("head") or (
                read_manifest_files(inner_path) != manifest_files
            ):
                problems.append(
                    "the manifest the gate was handed is not the "
                    "manifest of the named packet directory, in "
                    "head or in file list"
                )
    problems.extend(
        headless_problems(exit_code, events, manifest_files, packet_head)
    )
    if problems:
        for problem in problems:
            print(problem)
        return 1
    print("the headless run reads green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
