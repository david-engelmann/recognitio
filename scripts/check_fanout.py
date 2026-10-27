#!/usr/bin/env python3
"""Fail closed validation of a Build 6 review fan-out run record.

The script reads one run record JSON object, the findings schema
at workflows/findings.schema.json, and the packet the record
names, and reports every problem that stops the run from
reading green. The packet is an anchor its record author did
not write alone. The manifest the record names must validate
against the packet manifest schema that ships beside the
packet check, a packet file must stand beside that manifest,
and the packet header and section list must match the manifest
head, base and file list, so a hand written manifest with no
packet behind it never reads green. When the caller also names
the repository with the repo flag, the shipped packet check
recounts the packet from that repository and its verdict is
part of this stamp. A run reads green only when the packet it
ran on is verified in that sense, the groups cover the
manifest file list exactly, every group review validates
against the findings schema, the merged findings carry each
raised identity exactly once with its raising groups and with
the severity, summary, evidence, rule and location a raising
review actually wrote, every second pass finding obeys the
same packet evidence and dedupe rules as a first pass finding
and reaches the merged set, every merged finding carries one
second pass verdict with cited evidence inside the packet, and
the declared concurrency caps sit at or under the primary
numbers. Anything else fails the run, because a fan out must
never read green on a shape the gate cannot verify. Packet
content is untrusted data throughout. Text quoted from the
packet is evidence about the change under review and never an
instruction to a reviewer or to this gate, and a finding
summary written in the shape of an instruction to a reviewer
fails the run for a human to clear. See
workflows/review-fanout.md for the full contract and the
primary sources behind each rule.
"""

import argparse
import importlib.util
import json
import subprocess
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
SECOND_PASS_SOURCE = "second_pass"
MIN_NOTE_CHARS = 20

# Finding summaries are reviewer text about a defect. A summary
# written as an instruction to the next reader is steering
# content planted in the chain, whatever hand wrote it, so the
# gate names it as a problem for a human to clear rather than
# passing it down the chain in silence.
STEERING_PHRASES = (
    "ignore the",
    "ignore all",
    "disregard",
    "report no findings",
    "stamp approve",
    "rate every finding",
    "reviewer instruction",
    "reviewer note",
    "do not report",
    "cite only",
)


def steering_problems(summary, where):
    """Problems with a finding summary shaped as an instruction."""
    if not isinstance(summary, str):
        return []
    lowered = summary.lower()
    for phrase in STEERING_PHRASES:
        if phrase in lowered:
            return [
                "%s carries a summary shaped as an instruction "
                "to a reviewer (%r), which is steering content a "
                "human must clear" % (where, phrase)
            ]
    return []


def load_packet_checker():
    """The shipped packet check, loaded as a sibling module."""
    path = Path(__file__).resolve().parent / "check_packet.py"
    spec = importlib.util.spec_from_file_location(
        "fanout_check_packet", path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
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
            "%s is %r, outside the allowed values %s"
            % (where, value, ", ".join(str(v) for v in schema["enum"]))
        )
    return problems


def finding_identity(finding):
    """The dedupe identity of one finding."""
    location = finding["location"]
    return (location["file"], location["line"], finding["rule"])


def manifest_file_set(manifest):
    """The packet file list from a manifest object.

    The files key alone names the packet files. A legacy
    entries key names nothing in a packet manifest, and letting
    it override the files key would let one manifest certify
    one packet to this gate and another packet to a gate that
    honours the files key, so it is never read here.
    """
    files = manifest.get("files")
    if not isinstance(files, list):
        raise TypeError("the files key is not a list")
    return {entry["path"] for entry in files}


def packet_binding_problems(manifest, manifest_path):
    """Problems binding the manifest to the packet beside it.

    The packet file must stand in the same directory as the
    manifest, decode as strict UTF-8, and carry the header
    identity lines and the section list the manifest records.
    The header lines bind the packet to the manifest head and
    base, and the section list binds its structure, so a
    manifest repointed at another packet, or a packet swapped
    under a manifest, disagrees here even before a repository
    recount is asked for.
    """
    packet_path = manifest_path.parent / "packet.md"
    if not packet_path.is_file():
        return [
            "no packet file stands beside the packet manifest, "
            "so the run names a packet that does not exist"
        ]
    try:
        packet_text = packet_path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return ["the packet file cannot be read as UTF-8: %s" % exc]
    if not packet_text.strip():
        return ["the packet file beside the manifest is empty"]
    checker = load_packet_checker()
    problems = []
    for problem in checker.header_problems(packet_text, manifest):
        problems.append("the packet file disagrees with its manifest: %s"
                        % problem)
    for problem in checker.section_problems(
        packet_text, manifest.get("sections")
    ):
        problems.append("the packet file disagrees with its manifest: %s"
                        % problem)
    return problems


def check_manifest(record, base):
    """Problems with the packet manifest the run names."""
    problems = []
    rel = record.get("packet_manifest")
    if not isinstance(rel, str) or not rel:
        return ["the run names no packet manifest"], set(), None
    path = (base / rel).resolve()
    try:
        manifest = strict_json_loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return ["cannot read the packet manifest: %s" % exc], set(), None
    except (json.JSONDecodeError, DuplicateKeyError) as exc:
        return ["the packet manifest does not parse: %s" % exc], set(), None
    if not isinstance(manifest, dict):
        return ["the packet manifest is not an object"], set(), None
    if manifest.get("verified") is not True:
        problems.append("the packet manifest is not verified")
    checker = load_packet_checker()
    schema_problems = checker.manifest_schema_problems(manifest)
    for problem in schema_problems:
        problems.append("the packet manifest fails its schema: %s" % problem)
    discrepancies = manifest.get("discrepancies")
    if isinstance(discrepancies, list) and discrepancies:
        problems.append(
            "the packet manifest claims verified but its own "
            "discrepancies list is not empty"
        )
    try:
        files = manifest_file_set(manifest)
    except (KeyError, TypeError):
        problems.append("the packet manifest carries no file list")
        files = set()
    if not schema_problems and manifest.get("verified") is True:
        problems.extend(packet_binding_problems(manifest, path))
    return problems, files, manifest


def repo_line_problems(record, manifest, repo):
    """Problems with finding lines past the end of their file.

    With a repository named, every finding location is read
    against the file as it stands at the manifest head. A
    location naming a line the file does not have is a
    location no packet held, however consistent the record
    is internally.
    """
    head = manifest.get("head") if isinstance(manifest, dict) else None
    if not isinstance(head, str):
        return []
    locations = []

    def collect(finding, where):
        if isinstance(finding, dict) and isinstance(
            finding.get("location"), dict
        ):
            locations.append((finding["location"], where))

    for index, review in enumerate(record.get("reviews") or []):
        if isinstance(review, dict):
            for finding in review.get("findings") or []:
                collect(finding, "review %d" % index)
    for index, finding in enumerate(record.get("merged_findings") or []):
        collect(finding, "merged finding %d" % index)
    for index, entry in enumerate(record.get("second_pass") or []):
        if isinstance(entry, dict):
            collect(entry.get("raised"), "second pass verdict %d" % index)
    problems = []
    counts = {}
    for location, where in locations:
        path = location.get("file")
        line = location.get("line")
        if not isinstance(path, str) or not isinstance(line, int):
            continue
        if path not in counts:
            result = subprocess.run(
                ["git", "-C", str(repo), "show", "%s:%s" % (head, path)],
                capture_output=True, text=True,
            )
            counts[path] = (
                len(result.stdout.splitlines())
                if result.returncode == 0 else None
            )
        total = counts[path]
        if total is not None and line > total:
            problems.append(
                "%s cites %s line %d, past the %d lines the file "
                "has at the packet head" % (where, path, line, total)
            )
    return problems


def repo_packet_problems(manifest_path, manifest, repo):
    """Problems from the shipped packet check against a repo.

    This is the full recount. The packet check is run on the
    packet directory the manifest lives in, against the named
    repository, with the range the manifest itself records
    named as the expected range, so the stamp covers that
    packet and that range and no other.
    """
    checker = Path(__file__).resolve().parent / "check_packet.py"
    command = [
        sys.executable, str(checker), str(manifest_path.parent),
        "--repo", str(repo),
    ]
    if isinstance(manifest, dict) and manifest.get("base"):
        command += ["--expect-base", str(manifest["base"])]
    if isinstance(manifest, dict) and manifest.get("merge_base"):
        command += ["--expect-merge-base", str(manifest["merge_base"])]
    result = subprocess.run(
        command, capture_output=True, text=True
    )
    if result.returncode == 0:
        return []
    lines = [
        line.strip()
        for line in (result.stderr + result.stdout).splitlines()
        if line.strip()
    ]
    detail = lines[-1] if lines else "exit %d" % result.returncode
    return [
        "the packet check refuses the packet this run names: %s" % detail
    ]


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
                problems.extend(
                    steering_problems(finding.get("summary"), where)
                )
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


CONTENT_FIELDS = ("severity", "summary", "evidence", "rule", "location")


def content_matches(merged, raised):
    """Whether a merged finding copies a raised finding in full.

    Identity alone proves nothing about the finding a consumer
    reads. The merged record must carry the severity, the
    summary, the evidence, the rule and the location exactly as
    one of the findings that raised its identity wrote them.
    """
    return all(merged.get(field) == raised.get(field)
               for field in CONTENT_FIELDS)


def second_pass_raised(record):
    """The findings the second pass raises, by their id."""
    raised = {}
    verdicts = record.get("second_pass")
    if not isinstance(verdicts, list):
        return raised
    for entry in verdicts:
        if isinstance(entry, dict) and entry.get("verdict") == "new":
            finding = entry.get("raised")
            if isinstance(finding, dict) and finding.get("id"):
                raised[finding["id"]] = finding
    return raised


def check_merged(record, by_group, finding_schema, files):
    """Problems with the merged findings and their dedupe."""
    problems = []
    merged = record.get("merged_findings")
    if not isinstance(merged, list):
        return ["the run carries no merged findings list"], {}
    item_schema = finding_schema["properties"]["findings"]["items"]
    seen_identities = {}
    seen_ids = set()
    raised_identities = {}
    raised_findings = {}
    for review in by_group.values():
        findings = review.get("findings")
        if not isinstance(findings, list):
            continue
        for finding in findings:
            if isinstance(finding, dict) and "location" in finding:
                try:
                    identity = finding_identity(finding)
                except (KeyError, TypeError):
                    continue
                raised_identities.setdefault(identity, set()).add(
                    review.get("group")
                )
                raised_findings.setdefault(
                    (identity, review.get("group")), []
                ).append(finding)
    new_raised = second_pass_raised(record)
    for index, finding in enumerate(merged):
        where = "merged finding %d" % index
        if not isinstance(finding, dict):
            problems.append("%s is not an object" % where)
            continue
        bare = {
            key: value for key, value in finding.items() if key != "raised_by"
        }
        problems.extend(schema_problems(item_schema, bare, where))
        problems.extend(steering_problems(finding.get("summary"), where))
        evidence = finding.get("evidence")
        if isinstance(evidence, list):
            for path in evidence:
                if path not in files:
                    problems.append(
                        "%s cites evidence outside the packet: %s"
                        % (where, path)
                    )
        location = finding.get("location")
        if isinstance(location, dict) and location.get("file") not in files:
            problems.append("%s cites a location outside the packet" % where)
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
        if raised_by == [SECOND_PASS_SOURCE]:
            source = new_raised.get(fid)
            if source is None:
                problems.append(
                    "%s claims the second pass as its source, but "
                    "no second pass verdict raises it" % where
                )
            elif not content_matches(finding, source):
                problems.append(
                    "%s does not match the second pass finding it "
                    "claims to carry, in severity, summary, "
                    "evidence, rule or location" % where
                )
            continue
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
        named = [
            raised
            for gid in raised_by
            for raised in raised_findings.get((identity, gid), [])
        ]
        if named and not any(
            content_matches(finding, raised) for raised in named
        ):
            problems.append(
                "%s matches no finding its raising groups wrote, "
                "in severity, summary, evidence, rule or location, "
                "so the merge rewrote the finding it summarises"
                % where
            )
    for identity, groups in raised_identities.items():
        if identity not in seen_identities:
            problems.append(
                "a raised finding %r never reached the merged set, "
                "so the merge dropped it" % (identity,)
            )
    for fid, raised in new_raised.items():
        if fid not in seen_ids:
            problems.append(
                "second pass finding %r never reached the merged "
                "set, so a consumer reading the merged set drops it"
                % fid
            )
    return problems, seen_ids


def check_second_pass(record, merged_ids, files, finding_schema):
    """Problems with the adversarial second pass verdicts."""
    problems = []
    verdicts = record.get("second_pass")
    if not isinstance(verdicts, list):
        return ["the run carries no second pass verdicts"]
    item_schema = finding_schema["properties"]["findings"]["items"]
    merged = record.get("merged_findings")
    merged_by_id = {}
    first_pass_identities = set()
    if isinstance(merged, list):
        for finding in merged:
            if isinstance(finding, dict):
                merged_by_id[finding.get("id")] = finding
                if finding.get("raised_by") != [SECOND_PASS_SOURCE]:
                    try:
                        first_pass_identities.add(
                            finding_identity(finding)
                        )
                    except (KeyError, TypeError):
                        pass
    seen = set()
    raised_identities = set()
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
        if verdict == "new" and fid in merged_by_id and (
            merged_by_id[fid].get("raised_by") != [SECOND_PASS_SOURCE]
        ):
            problems.append(
                "%s raises a new finding under the id of a merged "
                "finding, so the new verdict displaces that finding"
                % where
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
            judged = merged_by_id.get(fid)
            if verdict in ("confirm", "contest") and isinstance(
                judged, dict
            ):
                location = judged.get("location")
                if isinstance(location, dict) and (
                    location.get("file") not in evidence
                ):
                    problems.append(
                        "%s cites evidence that does not include "
                        "the file the finding it judges stands in"
                        % where
                    )
        if not isinstance(note, str) or len(note.strip()) < MIN_NOTE_CHARS:
            problems.append(
                "%s carries no note of substance, which is the "
                "rubber stamp the second pass must never be" % where
            )
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
                problems.extend(
                    steering_problems(
                        raised.get("summary"), "%s.raised" % where
                    )
                )
                if raised.get("id") != fid:
                    problems.append(
                        "%s raises a finding with a different id" % where
                    )
                location = raised.get("location")
                if isinstance(location, dict):
                    if location.get("file") not in files:
                        problems.append(
                            "%s raises a finding located outside "
                            "the packet" % where
                        )
                    elif location.get("file") not in (evidence or []):
                        problems.append(
                            "%s cites entry evidence that does not "
                            "include the file its raised finding "
                            "stands in" % where
                        )
                raised_evidence = raised.get("evidence")
                if isinstance(raised_evidence, list):
                    for path in raised_evidence:
                        if path not in files:
                            problems.append(
                                "%s raises a finding citing "
                                "evidence outside the packet: %s"
                                % (where, path)
                            )
                try:
                    identity = finding_identity(raised)
                except (KeyError, TypeError):
                    identity = None
                if identity is not None:
                    if identity in first_pass_identities:
                        problems.append(
                            "%s raises a finding whose identity "
                            "duplicates a merged finding, so the "
                            "same defect counts twice" % where
                        )
                    if identity in raised_identities:
                        problems.append(
                            "%s raises a finding whose identity "
                            "duplicates another second pass finding"
                            % where
                        )
                    raised_identities.add(identity)
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


def run_problems(record_path, repo=None):
    """Every fan-out problem in one run record.

    When repo is named, the shipped packet check recount of the
    packet against that repository joins the problems, so the
    stamp covers a packet a repository recount verifies.
    """
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
    manifest_problems, files, manifest = check_manifest(record, base)
    problems.extend(manifest_problems)
    if repo is not None and manifest is not None:
        manifest_path = (base / record.get("packet_manifest", "")).resolve()
        problems.extend(repo_packet_problems(manifest_path, manifest, repo))
        problems.extend(repo_line_problems(record, manifest, repo))
    group_problems, groups = check_groups(record, files)
    problems.extend(group_problems)
    review_problems, by_group = check_reviews(
        record, groups, files, schema
    )
    problems.extend(review_problems)
    merged_problems, merged_ids = check_merged(
        record, by_group, schema, files
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
    parser.add_argument(
        "--repo",
        default=None,
        help=(
            "the repository the packet under review was built from. "
            "When named, the shipped packet check recounts the "
            "packet against it and its verdict joins this stamp"
        ),
    )
    args = parser.parse_args(argv)
    problems = run_problems(Path(args.run), repo=args.repo)
    if problems:
        for problem in problems:
            print("check_fanout: %s" % problem, file=sys.stderr)
        return 1
    print("check_fanout: the fan-out run record reads green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
