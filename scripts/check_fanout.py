#!/usr/bin/env python3
"""Fail closed validation of a Build 6 review fan-out run record.

The script reads one run record JSON object, the findings schema
at workflows/findings.schema.json, and the packet manifest the
record names, and reports every problem that stops the run from
reading green. A run reads green only when the packet it ran on
is verified, the groups cover the manifest file list exactly,
every group review validates against the findings schema, the
merged findings carry each raised identity exactly once with
its raising groups, every merged finding carries one second
pass verdict with cited evidence inside the packet, and the
declared concurrency caps sit at or under the primary numbers.
Anything else fails the run, because a fan out must never read
green on a shape the gate cannot verify. See
workflows/review-fanout.md for the full contract and the
primary sources behind each rule.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "workflows" / "findings.schema.json"
PROOF_RUN = ROOT / "workflows" / "proof-run" / "run-record.json"

# The concurrency ceilings the round 15 research closed on
# primary. Local dynamic workflows run 16 agents concurrently
# and Managed Agents runs 64, each with 1000 agents started
# per run as the lifetime cap. A run may use fewer agents.
# It may never declare more.
LOCAL_MAX_CONCURRENT = 16
MANAGED_MAX_CONCURRENT = 64
MAX_AGENTS_PER_RUN = 1000

VERDICTS = ("confirm", "contest", "new")
MODES = ("local", "managed")
RUN_KEYS = (
    "packet_manifest",
    "groups",
    "reviews",
    "merged_findings",
    "second_pass",
    "concurrency",
)


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


def schema_problems(schema, value, where):
    """Problems validating a value against the schema subset.

    The subset covers what the findings schema uses. Type,
    required, properties, enum, items, minItems, minimum, and
    additionalProperties false. Anything outside the subset
    fails closed as an unknown schema shape.
    """
    problems = []
    known = (
        "type",
        "required",
        "properties",
        "enum",
        "items",
        "minItems",
        "minimum",
        "additionalProperties",
        "description",
        "$schema",
        "$id",
        "title",
    )
    for key in schema:
        if key not in known:
            return ["%s uses an unsupported schema keyword %r" % (where, key)]
    stype = schema.get("type")
    if stype == "object":
        if not isinstance(value, dict):
            return ["%s is not an object" % where]
        for key in schema.get("required", []):
            if key not in value:
                problems.append("%s is missing %r" % (where, key))
        props = schema.get("properties", {})
        for key, sub in value.items():
            if key in props:
                problems.extend(
                    schema_problems(props[key], sub, "%s.%s" % (where, key))
                )
            elif schema.get("additionalProperties") is False:
                problems.append(
                    "%s carries an unknown key %r" % (where, key)
                )
    elif stype == "array":
        if not isinstance(value, list):
            return ["%s is not an array" % where]
        minimum_items = schema.get("minItems")
        if minimum_items is not None and len(value) < minimum_items:
            problems.append(
                "%s has %d items, fewer than %d"
                % (where, len(value), minimum_items)
            )
        items = schema.get("items")
        if items is not None:
            for index, entry in enumerate(value):
                problems.extend(
                    schema_problems(items, entry, "%s[%d]" % (where, index))
                )
    elif stype == "string":
        if not isinstance(value, str):
            problems.append("%s is not a string" % where)
    elif stype == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            problems.append("%s is not an integer" % where)
        elif "minimum" in schema and value < schema["minimum"]:
            problems.append(
                "%s is %d, below the minimum %d"
                % (where, value, schema["minimum"])
            )
    elif stype is not None:
        return ["%s uses an unsupported type %r" % (where, stype)]
    if "enum" in schema and value not in schema["enum"]:
        problems.append(
            "%s is %r, outside the allowed values" % (where, value)
        )
    return problems


def finding_identity(finding):
    """The dedupe identity of one finding."""
    location = finding["location"]
    return (location["file"], location["line"], finding["rule"])


def manifest_file_set(manifest):
    """The packet file list from a manifest object."""
    entries = manifest.get("entries", manifest.get("files", []))
    return {entry["path"] for entry in entries}


def check_manifest(record, base):
    """Problems with the packet manifest the run names."""
    problems = []
    rel = record.get("packet_manifest")
    if not isinstance(rel, str) or not rel:
        return ["the run names no packet manifest"], set()
    path = (base / rel).resolve()
    try:
        manifest = strict_json_loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return ["cannot read the packet manifest: %s" % exc], set()
    except (json.JSONDecodeError, DuplicateKeyError) as exc:
        return ["the packet manifest does not parse: %s" % exc], set()
    if not isinstance(manifest, dict):
        return ["the packet manifest is not an object"], set()
    if manifest.get("verified") is not True:
        problems.append("the packet manifest is not verified")
    try:
        files = manifest_file_set(manifest)
    except (KeyError, TypeError):
        problems.append("the packet manifest carries no file list")
        files = set()
    return problems, files


def check_groups(record, files):
    """Problems with the group partition against the packet."""
    problems = []
    groups = record.get("groups")
    if not isinstance(groups, list) or not groups:
        return ["the run lists no groups"], {}
    seen = {}
    union = set()
    for index, group in enumerate(groups):
        where = "group %d" % index
        if not isinstance(group, dict):
            problems.append("%s is not an object" % where)
            continue
        gid = group.get("id")
        gfiles = group.get("files")
        if not isinstance(gid, str) or not gid:
            problems.append("%s carries no id" % where)
        elif gid in seen:
            problems.append("group id %r is used twice" % gid)
        else:
            seen[gid] = group
        if not isinstance(gfiles, list) or not gfiles or not all(
            isinstance(entry, str) for entry in gfiles
        ):
            problems.append("%s carries no file list" % where)
            continue
        union.update(gfiles)
    if union != files:
        missing = sorted(files - union)
        extra = sorted(union - files)
        if missing:
            problems.append(
                "the groups drop packet files: %s" % ", ".join(missing)
            )
        if extra:
            problems.append(
                "the groups add files outside the packet: %s"
                % ", ".join(extra)
            )
    return problems, seen


def check_reviews(record, groups, files, finding_schema):
    """Problems with the group reviews against the schema."""
    problems = []
    reviews = record.get("reviews")
    if not isinstance(reviews, list):
        return ["the run carries no reviews list"], {}
    by_group = {}
    for index, review in enumerate(reviews):
        where = "review %d" % index
        if not isinstance(review, dict):
            problems.append("%s is not an object" % where)
            continue
        problems.extend(schema_problems(finding_schema, review, where))
        gid = review.get("group")
        if gid in groups:
            if gid in by_group:
                problems.append(
                    "group %r carries two reviews" % gid
                )
            by_group[gid] = review
        findings = review.get("findings")
        if isinstance(findings, list):
            for finding in findings:
                if not isinstance(finding, dict):
                    continue
                location = finding.get("location")
                if isinstance(location, dict):
                    if location.get("file") not in files:
                        problems.append(
                            "%s cites a location outside the packet" % where
                        )
                evidence = finding.get("evidence")
                if isinstance(evidence, list):
                    for path in evidence:
                        if path not in files:
                            problems.append(
                                "%s cites evidence outside the packet: %s"
                                % (where, path)
                            )
            verdict = review.get("verdict")
            if verdict == "pass" and findings:
                problems.append(
                    "%s reads pass while listing findings" % where
                )
            if verdict == "fail" and not findings:
                problems.append(
                    "%s reads fail while listing no findings" % where
                )
    for gid in groups:
        if gid not in by_group:
            problems.append("group %r carries no review" % gid)
    return problems, by_group


def check_merged(record, by_group, finding_schema):
    """Problems with the merged findings and their dedupe."""
    problems = []
    merged = record.get("merged_findings")
    if not isinstance(merged, list):
        return ["the run carries no merged findings list"], {}
    item_schema = finding_schema["properties"]["findings"]["items"]
    seen_identities = {}
    seen_ids = set()
    raised_identities = {}
    for review in by_group.values():
        findings = review.get("findings")
        if not isinstance(findings, list):
            continue
        for finding in findings:
            if isinstance(finding, dict) and "location" in finding:
                try:
                    raised_identities.setdefault(
                        finding_identity(finding), set()
                    ).add(review.get("group"))
                except (KeyError, TypeError):
                    pass
    for index, finding in enumerate(merged):
        where = "merged finding %d" % index
        if not isinstance(finding, dict):
            problems.append("%s is not an object" % where)
            continue
        bare = {
            key: value for key, value in finding.items() if key != "raised_by"
        }
        problems.extend(schema_problems(item_schema, bare, where))
        raised_by = finding.get("raised_by")
        if not isinstance(raised_by, list) or not raised_by or not all(
            isinstance(entry, str) for entry in raised_by
        ):
            problems.append("%s names no raising groups" % where)
            continue
        fid = finding.get("id")
        if fid in seen_ids:
            problems.append("merged finding id %r is used twice" % fid)
        seen_ids.add(fid)
        try:
            identity = finding_identity(finding)
        except (KeyError, TypeError):
            continue
        if identity in seen_identities:
            problems.append(
                "%s shares an identity with %s, so the merge "
                "did not dedupe" % (where, seen_identities[identity])
            )
        else:
            seen_identities[identity] = where
        for gid in raised_by:
            if gid not in by_group:
                problems.append(
                    "%s names an unknown group %r" % (where, gid)
                )
            elif identity not in raised_identities or gid not in (
                raised_identities[identity]
            ):
                problems.append(
                    "%s names group %r, which raised no finding "
                    "with that identity" % (where, gid)
                )
    for identity, groups in raised_identities.items():
        if identity not in seen_identities:
            problems.append(
                "a raised finding %r never reached the merged set, "
                "so the merge dropped it" % (identity,)
            )
    return problems, seen_ids


def check_second_pass(record, merged_ids, files, finding_schema):
    """Problems with the adversarial second pass verdicts."""
    problems = []
    verdicts = record.get("second_pass")
    if not isinstance(verdicts, list):
        return ["the run carries no second pass verdicts"]
    item_schema = finding_schema["properties"]["findings"]["items"]
    seen = set()
    for index, entry in enumerate(verdicts):
        where = "second pass verdict %d" % index
        if not isinstance(entry, dict):
            problems.append("%s is not an object" % where)
            continue
        fid = entry.get("finding")
        verdict = entry.get("verdict")
        evidence = entry.get("evidence")
        note = entry.get("note")
        if verdict not in VERDICTS:
            problems.append(
                "%s carries verdict %r, not confirm, contest, or new"
                % (where, verdict)
            )
        if verdict in ("confirm", "contest") and fid not in merged_ids:
            problems.append(
                "%s judges %r, which is not a merged finding"
                % (where, fid)
            )
        if fid in seen:
            problems.append(
                "%s judges finding %r twice" % (where, fid)
            )
        seen.add(fid)
        if not isinstance(evidence, list) or not evidence or not all(
            isinstance(path, str) for path in evidence
        ):
            problems.append(
                "%s cites no evidence, which is the rubber stamp "
                "the second pass must never be" % where
            )
        else:
            for path in evidence:
                if path not in files:
                    problems.append(
                        "%s cites evidence outside the packet: %s"
                        % (where, path)
                    )
        if not isinstance(note, str) or not note.strip():
            problems.append("%s carries no note" % where)
        if verdict == "new":
            raised = entry.get("raised")
            if not isinstance(raised, dict):
                problems.append(
                    "%s raises nothing for its new verdict" % where
                )
            else:
                problems.extend(
                    schema_problems(item_schema, raised, "%s.raised" % where)
                )
                if raised.get("id") != fid:
                    problems.append(
                        "%s raises a finding with a different id" % where
                    )
        elif "raised" in entry:
            problems.append(
                "%s carries a raised finding beside a %r verdict"
                % (where, verdict)
            )
    for fid in merged_ids:
        if fid not in seen:
            problems.append(
                "merged finding %r carries no second pass verdict" % fid
            )
    return problems


def check_concurrency(record):
    """Problems with the declared concurrency caps."""
    problems = []
    concurrency = record.get("concurrency")
    if not isinstance(concurrency, dict):
        return ["the run declares no concurrency caps"]
    mode = concurrency.get("mode")
    concurrent = concurrency.get("max_concurrent")
    per_run = concurrency.get("max_agents_per_run")
    if mode not in MODES:
        problems.append(
            "the concurrency mode is %r, not local or managed" % (mode,)
        )
    ceiling = (
        LOCAL_MAX_CONCURRENT if mode == "local"
        else MANAGED_MAX_CONCURRENT if mode == "managed"
        else None
    )
    if not isinstance(concurrent, int) or isinstance(concurrent, bool) \
            or concurrent < 1:
        problems.append("the max concurrent figure is not a positive integer")
    elif ceiling is not None and concurrent > ceiling:
        problems.append(
            "the run declares %d concurrent agents, past the "
            "primary cap of %d" % (concurrent, ceiling)
        )
    if not isinstance(per_run, int) or isinstance(per_run, bool) \
            or per_run < 1:
        problems.append(
            "the max agents per run figure is not a positive integer"
        )
    elif per_run > MAX_AGENTS_PER_RUN:
        problems.append(
            "the run declares %d agents per run, past the primary "
            "cap of %d" % (per_run, MAX_AGENTS_PER_RUN)
        )
    return problems


def run_problems(record_path):
    """Every fan-out problem in one run record."""
    problems = []
    try:
        text = record_path.read_text(encoding="utf-8")
    except OSError as exc:
        return ["cannot read the run record: %s" % exc]
    try:
        record = strict_json_loads(text)
    except (json.JSONDecodeError, DuplicateKeyError) as exc:
        return ["the run record does not parse: %s" % exc]
    if not isinstance(record, dict):
        return ["the run record is not an object"]
    for key in record:
        if key not in RUN_KEYS:
            problems.append("the run record carries an unknown key %r" % key)
    for key in RUN_KEYS:
        if key not in record:
            problems.append("the run record is missing %r" % key)
    if problems:
        return problems
    try:
        schema = strict_json_loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, DuplicateKeyError) as exc:
        return ["cannot read the findings schema: %s" % exc]
    base = record_path.parent
    manifest_problems, files = check_manifest(record, base)
    problems.extend(manifest_problems)
    group_problems, groups = check_groups(record, files)
    problems.extend(group_problems)
    review_problems, by_group = check_reviews(
        record, groups, files, schema
    )
    problems.extend(review_problems)
    merged_problems, merged_ids = check_merged(
        record, by_group, schema
    )
    problems.extend(merged_problems)
    problems.extend(
        check_second_pass(record, merged_ids, files, schema)
    )
    problems.extend(check_concurrency(record))
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate a Build 6 review fan-out run record."
    )
    parser.add_argument(
        "--run",
        default=str(PROOF_RUN),
        help="the run record to validate, defaulting to the shipped proof",
    )
    args = parser.parse_args(argv)
    problems = run_problems(Path(args.run))
    if problems:
        for problem in problems:
            print("check_fanout: %s" % problem, file=sys.stderr)
        return 1
    print("check_fanout: the fan-out run record reads green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
