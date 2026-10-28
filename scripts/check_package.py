#!/usr/bin/env python3
"""Pin the Build 8 Agent Plugins 1.0.0 portable package.

The portable package lives at agent-plugins-package/ and carries
only the portable core, the closed schema manifest and the
skills/ tree. The Claude Code native shapes ride beside the
portable core at the repo root as per platform extensions, named
in the manifest under the reverse domain namespace the spec
section 8 defines. This script pins that arrangement without a
portable host. The manifest must carry only the ten top level
fields the spec section 5 permits, with the canonical 1.0.0
$schema value, so a Claude Code native key can never slip in
and be silently ignored by a conformant client. The package
skill must stay byte identical to the canonical skill at
.agents/skills/recognitio/, which is the only spelling that
ever changes. Recognitio ships no MCP servers, so mcp.json is
omitted and its absence is pinned. Every repo relative path
the extensions object names must resolve in the repo, across
every namespace in the extensions object and not just the
pinned Claude Code one, and the
brief at docs/agent-plugins-brief.md must state the honesty
sentence, so the package cannot drift into claiming a native
Claude Code install it does not have, and must record the Agent
Skills donation transfer as primary on both halves, so the round
21 one sentence correction cannot quietly revert. The tree shape
of agent-plugins-package/ itself is pinned to plugin.json, the
skills/ tree, and the one asset file the builds name inside
the portable core, so a native platform shape placed inside
the portable core fails the gate instead of blending in
silence.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "agent-plugins-package"
MANIFEST = PACKAGE / "plugin.json"
SKILLS = PACKAGE / "skills"
CANONICAL_SKILL = ROOT / ".agents" / "skills" / "recognitio"
NATIVE_MANIFEST = ROOT / ".claude-plugin" / "plugin.json"
BRIEF = ROOT / "docs" / "agent-plugins-brief.md"

SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
PERMITTED_FIELDS = {
    "$schema",
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
    "extensions",
}
# Claude Code native manifest keys that must never appear at the
# top level of the portable manifest. A conformant client must
# ignore unknown top level fields without assigning them
# semantics, so these keys would silently drop the persona, the
# session agent setting, the forced output style and the skill
# path they carry on the native manifest.
NATIVE_KEYS = {"agents", "settings", "outputStyles", "skills"}
NAMESPACE = "com.anthropic.claude-code"

HONESTY_SENTENCE = (
    "The package does not install natively in Claude Code on "
    "current evidence"
)

# The round 20 research closed the Agent Skills donation to
# primary on both halves, so the brief records the transfer as
# primary. The older secondary corroborated wording is stale and
# must not come back.
AAIF_SENTENCE = (
    "the transfer is now recorded as primary on both halves"
)
STALE_AAIF = "secondary corroborated"

# The digit classes are ASCII ranges on purpose, the same reason
# scripts/check_version.py records. A backslash d class also
# matches Unicode decimal digits, so a version written with
# Arabic Indic digits would pass the shape while not being a
# version any tool can read.
VERSION_RE = re.compile(
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
)


class DuplicateKeyError(ValueError):
    """A JSON object names one key twice."""


def strict_json_loads(text):
    """Parse JSON refusing a repeated key, like the other gates.

    A plain load keeps the last value of a repeated key in
    silence, which would let a second extensions entry hide
    beside the one the gate certifies. This is the same reader
    the other gate scripts carry, kept as a second copy because
    the gate scripts never import each other.
    """
    def reject(pairs):
        seen = {}
        for key, value in pairs:
            if key in seen:
                raise DuplicateKeyError("repeated key %r" % key)
            seen[key] = value
        return seen
    return json.loads(text, object_pairs_hook=reject)


def describe(path, root=ROOT):
    """The root relative spelling of a path, or the path itself."""
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def load_manifest(root):
    """The parsed portable manifest, or a problem."""
    path = root / "agent-plugins-package" / "plugin.json"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None, "the portable manifest at %s is missing" % describe(
            path, root
        )
    try:
        data = strict_json_loads(text)
    except (json.JSONDecodeError, DuplicateKeyError) as exc:
        return None, "the portable manifest does not parse, %s" % exc
    if not isinstance(data, dict):
        return None, "the portable manifest is not a JSON object"
    return data, None


def native_version(root):
    """The native plugin manifest version and any problem reading it.

    A manifest that stands in the tree but cannot be read or
    does not parse or is not an object or carries no version or
    carries a version that is not a string yields a problem
    beside no version, so the agreement reading fails closed
    instead of skipping in silence over a manifest it never
    read. A manifest that does not stand in the tree yields
    neither a version nor a problem, because the extension path
    reading already names that absence in its own terms.
    """
    path = root / ".claude-plugin" / "plugin.json"
    if not path.exists():
        return None, None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return None, "the native manifest at %s cannot be read, %s" % (
            describe(path, root),
            exc,
        )
    try:
        data = strict_json_loads(text)
    except (json.JSONDecodeError, DuplicateKeyError) as exc:
        return None, "the native manifest does not parse, %s" % exc
    if not isinstance(data, dict):
        return None, "the native manifest is not a JSON object"
    version = data.get("version")
    if version is None:
        return None, (
            "the native manifest carries no version, so the "
            "portable manifest version cannot be checked against it"
        )
    if not isinstance(version, str):
        return None, (
            "the native manifest carries version %r, which is not "
            "a string, so the portable manifest version cannot be "
            "checked against it" % (version,)
        )
    return version, None


def extension_paths(data):
    """Every repo relative path the extensions object declares.

    R24-RT-01 and R24-RT-02. Every namespace object under
    extensions is resolved, not just the pinned Claude Code one.
    A second namespace carrying a dangling shape path passed in
    silence before this change, because the old helper read the
    shapes object of the pinned namespace only and never looked
    at a sibling namespace.
    """
    paths = []
    extensions = data.get("extensions")
    if not isinstance(extensions, dict):
        return paths
    for namespace in extensions.values():
        if not isinstance(namespace, dict):
            continue
        for key in ("nativeManifest", "nativeMarketplace"):
            value = namespace.get(key)
            if isinstance(value, str):
                paths.append(value)
        shapes = namespace.get("shapes")
        if isinstance(shapes, dict):
            for entries in shapes.values():
                if isinstance(entries, list):
                    paths.extend(
                        entry for entry in entries if isinstance(entry, str)
                    )
    return paths


def manifest_problems(data, root):
    """Problems with the portable manifest itself."""
    problems = []
    for field in sorted(data):
        if field not in PERMITTED_FIELDS:
            if field in NATIVE_KEYS:
                problems.append(
                    "the portable manifest carries the Claude Code "
                    "native key %r at the top level, where a "
                    "conformant client must ignore it and drop the "
                    "native wiring it names" % field
                )
            else:
                problems.append(
                    "the portable manifest carries top level field "
                    "%r, outside the closed schema of section 5"
                    % field
                )
    if data.get("$schema") != SCHEMA:
        problems.append(
            "the portable manifest $schema is %r, not the 1.0.0 "
            "canonical value" % (data.get("$schema"),)
        )
    version = data.get("version")
    if not isinstance(version, str) or not VERSION_RE.fullmatch(version):
        problems.append(
            "the portable manifest carries version %r, which is not "
            "a version of the form major.minor.patch" % (version,)
        )
    else:
        expected, native_problem = native_version(root)
        if native_problem is not None:
            problems.append(native_problem)
        elif expected is not None and version != expected:
            problems.append(
                "the portable manifest version %r disagrees with the "
                "native manifest version %r" % (version, expected)
            )
    extensions = data.get("extensions")
    if not isinstance(extensions, dict):
        problems.append(
            "the portable manifest carries no extensions object for "
            "the per platform native shapes"
        )
        return problems
    namespace = extensions.get(NAMESPACE)
    if not isinstance(namespace, dict):
        problems.append(
            "the extensions object names no %r namespace for the "
            "Claude Code native shapes" % NAMESPACE
        )
        return problems
    for entry in extension_paths(data):
        if not (root / entry).exists():
            problems.append(
                "the extension path %r does not resolve in the repo, "
                "so the portable manifest names a native shape that "
                "is not there" % entry
            )
    return problems


def tree_bytes(directory):
    """Map every file under a directory to its bytes.

    Compiled bytecode caches are build state, not skill content,
    so a __pycache__ directory on either side is skipped. Without
    the skip, importing the extractor during the test run would
    put a cache on the canonical side only and fail the pin for
    no authored reason.
    """
    found = {}
    for path in sorted(directory.rglob("*")):
        if "__pycache__" in path.parts:
            continue
        if path.is_file() and not path.is_symlink():
            found[str(path.relative_to(directory))] = path.read_bytes()
    return found


def skills_problems(root):
    """Problems with the package skill against the canonical one."""
    problems = []
    skills = root / "agent-plugins-package" / "skills"
    canonical = root / ".agents" / "skills" / "recognitio"
    if not skills.is_dir():
        return ["the package carries no skills/ directory"]
    children = sorted(
        path.name for path in skills.iterdir() if path.is_dir()
    )
    if children != ["recognitio"]:
        problems.append(
            "the package skills/ holds %r, not the single recognitio "
            "skill directory the spec section 6 fixes" % (children,)
        )
        return problems
    if not canonical.is_dir():
        return ["the canonical skill at %s is missing" % describe(
            canonical, root
        )]
    package_files = tree_bytes(skills / "recognitio")
    canonical_files = tree_bytes(canonical)
    if set(package_files) != set(canonical_files):
        problems.append(
            "the package skill file set %r differs from the canonical "
            "skill file set %r"
            % (sorted(package_files), sorted(canonical_files))
        )
        return problems
    for name in sorted(package_files):
        if package_files[name] != canonical_files[name]:
            problems.append(
                "agent-plugins-package/skills/recognitio/%s is not "
                "byte identical to the canonical skill, so the "
                "package carries a second spelling that can drift"
                % name
            )
    return problems


def mcp_problems(root):
    """Problems with the mcp.json disposition, which is omission."""
    if (root / "agent-plugins-package" / "mcp.json").exists():
        return [
            "agent-plugins-package/mcp.json is present, but the "
            "recorded disposition is omission because recognitio "
            "ships no MCP servers"
        ]
    return []


def tree_problems(root):
    """Problems with the package root tree shape.

    R24-RT-01. The allowed contents of agent-plugins-package/
    are plugin.json, the skills/ tree, and the
    assets/icon-512.png the Codex interface names, and
    anything else fails the gate. The manifest
    schema pin cannot catch a native platform file placed
    inside the portable core, because these are files and not
    manifest keys, and the skills pin only walks
    skills/recognitio, so the tree shape needs its own pin.
    """
    problems = []
    package = root / "agent-plugins-package"
    if not package.is_dir():
        return ["agent-plugins-package/ is missing"]
    for path in sorted(package.rglob("*")):
        if "__pycache__" in path.parts:
            continue
        if path.is_dir():
            continue
        rel = path.relative_to(package)
        if len(rel.parts) == 1 and rel.parts[0] == "plugin.json":
            continue
        if rel.parts[0] == "skills":
            continue
        if str(rel) == "assets/icon-512.png":
            # The one asset a build names inside the portable
            # core, the Codex interface icon whose bytes the
            # Build 19 gate pins against the brand master.
            continue
        problems.append(
            "agent-plugins-package/%s sits inside the portable core, "
            "but only plugin.json, the skills/ tree, and the "
            "assets/icon-512.png the Codex interface names may "
            "live there"
            % rel
        )
    return problems


def brief_problems(root):
    """Problems with the Build 8 brief's stated contract."""
    problems = []
    path = root / "docs" / "agent-plugins-brief.md"
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return ["cannot read docs/agent-plugins-brief.md, %s" % exc]
    text = re.sub(r"\s+", " ", raw)
    if HONESTY_SENTENCE not in text:
        problems.append(
            "docs/agent-plugins-brief.md does not state the honesty "
            "sentence, so the brief could drift into claiming a "
            "native Claude Code install"
        )
    if AAIF_SENTENCE not in text:
        problems.append(
            "docs/agent-plugins-brief.md does not record the Agent "
            "Skills donation transfer as primary on both halves"
        )
    if STALE_AAIF in text:
        problems.append(
            "docs/agent-plugins-brief.md still carries the stale "
            "secondary corroborated wording for the donation transfer"
        )
    return problems


def package_problems(root=None):
    """Every Build 8 portable package problem."""
    root = ROOT if root is None else root
    problems = []
    data, problem = load_manifest(root)
    if problem:
        return [problem]
    problems.extend(manifest_problems(data, root))
    problems.extend(skills_problems(root))
    problems.extend(mcp_problems(root))
    problems.extend(tree_problems(root))
    problems.extend(brief_problems(root))
    return problems


def main(root=None):
    problems = package_problems(root)
    if problems:
        for problem in problems:
            print("check_package: %s" % problem, file=sys.stderr)
        return 1
    print("check_package: the Build 8 portable package holds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
