#!/usr/bin/env python3
"""Check that every version string in the repo agrees.

The extractor stamps each manifest with its version, the plugin
manifest carries a version, the marketplace listing carries one in
its metadata and one on its plugin entry, the changelog names
the version its unreleased work carries or the newest released
version it records, and the README carries the version on its
badge. A reader who installs through any surface
should meet the same version on every one, so the gate fails when
any of them drifts from the others.

Exits nonzero with one line per problem when anything disagrees.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_JSON = ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE_JSON = ROOT / ".claude-plugin" / "marketplace.json"
EXTRACT_PY = ROOT / ".agents" / "skills" / "recognitio" / "scripts" / "extract.py"
CHANGELOG_MD = ROOT / "CHANGELOG.md"
README_MD = ROOT / "README.md"


class DuplicateKeyError(ValueError):
    """A JSON object holds the same key twice."""


def _reject_duplicate_keys(pairs):
    record = {}
    for key, value in pairs:
        if key in record:
            raise DuplicateKeyError("repeated key %r" % (key,))
        record[key] = value
    return record


def strict_json_loads(text):
    """Parse JSON refusing a repeated key in any object.

    A plain load keeps the last value of a repeated key in
    silence, which lets a second version entry hide beside the
    one the gate certifies. This is the same reader the eval
    records load through in scripts/check_evals.py, kept as a
    second copy because the gate scripts never import each
    other. Every manifest this gate trusts loads through it.
    """
    return json.loads(text, object_pairs_hook=_reject_duplicate_keys)

# The digit classes are written as ASCII ranges on purpose. A
# backslash d class in a Python pattern also matches Unicode
# decimal digits, so a version written with Arabic Indic digits
# would pass the shape and agree across surfaces while not being
# a version any tool can read.
VERSION_SHAPE = r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
VERSION_RE = re.compile(VERSION_SHAPE)
EXTRACTOR_RE = re.compile(r'^EXTRACTOR_VERSION\s*=\s*"([^"]+)"', re.M)
RELEASED_RE = re.compile(r"^## \[(%s)\]" % VERSION_SHAPE, re.M)
CARRIES_DECLARATION_RE = re.compile(r"carries version\s+(\S+)")
UNRELEASED_RE = re.compile(r"^## \[Unreleased\]", re.M)
SECTION_RE = re.compile(r"^## \[", re.M)
BADGE_RE = re.compile(r"badge/version-(%s)-" % VERSION_SHAPE)


def plugin_version(text):
    data = strict_json_loads(text)
    if not isinstance(data, dict):
        return None
    return data.get("version")


def marketplace_versions(text):
    """Every version the listing is required to carry.

    The metadata version and one version per plugin entry are
    required fields of this listing, so a missing one is recorded
    as None rather than silently dropped. Dropping it would let
    the remaining values agree and pass a listing that lost a
    version it must carry. A listing that carries no plugin entry
    at all certifies nothing, so that shape raises instead and
    the caller records it as a problem in the gate voice.
    """
    data = strict_json_loads(text)
    if not isinstance(data, dict):
        return [None]
    versions = []
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    versions.append(metadata.get("version"))
    plugins = data.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        raise ValueError("marketplace.json lists no plugins")
    for entry in plugins:
        if isinstance(entry, dict):
            versions.append(entry.get("version"))
        else:
            versions.append(None)
    return versions


COMPONENT_KEYS = (
    "skills", "commands", "agents", "hooks", "outputStyles",
    "themes",
)


def manifest_conflict_problems(plugin_text, marketplace_text):
    """Problems in the manifest pair that stop the plugin loading.

    The host refuses to load a plugin when its marketplace
    entry specifies components while the entry sets strict to
    false and a plugin manifest stands beside the entry,
    because under a strict false entry the entry itself is the
    plugin definition and the manifest beside it is a second
    definition. The manifest does not have to specify any
    component itself for the conflict to fire, and a live
    install probe in the round 6 fix lane confirmed that a
    metadata only manifest fails to load in this shape with
    the same error the shipped pair once drew. An entry that
    omits the strict key loads as if strict were true, because
    the host treats a missing strict key as true, and a live
    probe in the round 7 audit confirmed that a pair whose
    entry names components with no strict key at all loads
    with status enabled. Setting strict to true makes the
    manifest the definition the host loads, so the pair can
    both name the components and the manifest stays self
    describing. The conflict set is the six component fields
    the host names for this rule, and a field counts wherever
    the entry declares it, at the top level of the entry or
    under the experimental object of the entry, which is the
    current home of themes. The server fields stand outside
    the set, and the round 6 probe confirmed an mcpServers
    pair loads under strict false. A strict key with the wrong
    type is named as its own problem below, because the gate
    cannot verify what the host does with a strict that is
    neither true nor false nor absent.
    """
    try:
        plugin = strict_json_loads(plugin_text)
        market = strict_json_loads(marketplace_text)
    except (json.JSONDecodeError, ValueError, TypeError):
        # A repeated key is named by the version readers below,
        # so this function stays silent on unparsable input and
        # never escapes as a traceback.
        return []
    if not isinstance(plugin, dict) or not isinstance(market, dict):
        return []
    plugins = market.get("plugins")
    if not isinstance(plugins, list):
        return []
    problems = []
    for entry in plugins:
        if not isinstance(entry, dict):
            continue
        # The conflict fires only when strict stands present
        # and false. A missing strict key reads as true on the
        # host, so an entry that omits it appends its components
        # to the manifest and loads.
        if "strict" not in entry:
            continue
        strict = entry["strict"]
        if not isinstance(strict, bool):
            # A wrong typed strict, such as the string "false",
            # is not a false the host honors and not a true
            # either. The gate cannot verify what the host does
            # with it, so it fails loudly instead of silently
            # reading it as strict true.
            problems.append(
                "marketplace entry %r sets strict to %r, which is "
                "not a boolean, so the gate cannot tell how the "
                "host reads it" % (entry.get("name"), strict)
            )
            continue
        if strict is not False:
            continue
        experimental = entry.get("experimental")
        if not isinstance(experimental, dict):
            experimental = {}
        shared = [
            key for key in COMPONENT_KEYS
            if key in entry or key in experimental
        ]
        if shared:
            problems.append(
                "marketplace entry %r specifies components (%s) "
                "while a plugin.json stands beside it and the "
                "entry sets strict to false, so the host "
                "refuses to load the plugin for conflicting "
                "manifests"
                % (
                    entry.get("name"),
                    ", ".join(shared),
                )
            )
    return problems


def extractor_version(text):
    match = EXTRACTOR_RE.search(text)
    return match.group(1) if match else None


def readme_badge_version(text):
    """The version the README badge carries, or None when absent.

    The badge is a static image URL, so nothing updates it when
    the version moves. Reading it here keeps the badge inside
    the coherence check instead of letting it drift stale on
    the next bump.
    """
    match = BADGE_RE.search(text)
    return match.group(1) if match else None


def changelog_version(text):
    """The version the changelog speaks for.

    The version the unreleased work declares wins when it
    declares one, because after the first release the changelog
    holds a released heading and a newer unreleased declaration
    at once, and the unreleased work is what the other surfaces
    are being checked against. The declaration search is scoped
    to the unreleased section, so a carries phrase inside an old
    release note can never hijack the compared version. The
    newest released heading is the fallback when the unreleased
    section declares nothing.
    """
    unreleased = UNRELEASED_RE.search(text)
    if unreleased:
        rest = text[unreleased.end():]
        following = SECTION_RE.search(rest)
        section = rest[:following.start()] if following else rest
        declaration = CARRIES_DECLARATION_RE.search(section)
        if declaration:
            # A declaration stands in the unreleased section, so
            # its word governs. A value that is not a strict
            # version is a broken declaration, not an absence, and
            # it must never fall back to a released heading and
            # pass beside surfaces that carry the real version.
            candidate = declaration.group(1).rstrip(".,;:!?)]}")
            return candidate if VERSION_RE.fullmatch(candidate) else None
    match = RELEASED_RE.search(text)
    return match.group(1) if match else None


def coherence_problems(versions):
    """One problem per surface that disagrees with the rest.

    The versions argument maps a surface name to the version it
    carries, or to None when the surface carries none at all.
    """
    problems = []
    present = {}
    for surface, version in versions.items():
        if version is None:
            problems.append("%s carries no version" % surface)
        elif not isinstance(version, str) or not VERSION_RE.fullmatch(version):
            problems.append(
                "%s carries %r, which is not a version of the form "
                "major.minor.patch" % (surface, version)
            )
        else:
            present[surface] = version
    distinct = sorted(set(present.values()))
    if len(distinct) > 1:
        detail = ", ".join(
            "%s at %s" % (surface, present[surface])
            for surface in sorted(present)
        )
        problems.append("version strings disagree: %s" % detail)
    return problems


def read(path):
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def main():
    versions = {}
    problems = []
    plugin_text = read(PLUGIN_JSON)
    marketplace_text = read(MARKETPLACE_JSON)
    if plugin_text is not None and marketplace_text is not None:
        problems.extend(
            manifest_conflict_problems(plugin_text, marketplace_text)
        )

    text = read(PLUGIN_JSON)
    if text is None:
        problems.append("missing plugin manifest at .claude-plugin/plugin.json")
        versions["plugin.json"] = None
    else:
        try:
            versions["plugin.json"] = plugin_version(text)
        except (json.JSONDecodeError, ValueError, TypeError, AttributeError) as exc:
            problems.append("plugin.json does not parse: %s" % exc)
            versions["plugin.json"] = None

    text = read(MARKETPLACE_JSON)
    if text is None:
        problems.append(
            "missing marketplace listing at .claude-plugin/marketplace.json"
        )
    else:
        try:
            found = marketplace_versions(text)
        except (json.JSONDecodeError, ValueError, TypeError, AttributeError) as exc:
            problems.append("marketplace.json problem: %s" % exc)
            found = None
        if found is not None:
            if not found:
                problems.append("marketplace.json carries no version")
            for index, version in enumerate(found):
                versions["marketplace.json entry %d" % (index + 1)] = version

    text = read(EXTRACT_PY)
    versions["EXTRACTOR_VERSION"] = (
        extractor_version(text) if text is not None else None
    )

    text = read(CHANGELOG_MD)
    versions["CHANGELOG.md"] = (
        changelog_version(text) if text is not None else None
    )

    text = read(README_MD)
    versions["README.md version badge"] = (
        readme_badge_version(text) if text is not None else None
    )

    problems.extend(coherence_problems(versions))
    if problems:
        for problem in problems:
            print("check_version: %s" % problem, file=sys.stderr)
        return 1
    print(
        "check_version: version %s agrees across the plugin manifest, "
        "the marketplace listing, the extractor, the changelog and "
        "the README version badge"
        % versions["EXTRACTOR_VERSION"]
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
