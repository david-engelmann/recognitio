#!/usr/bin/env python3
"""Pin the submission packs and the facts their evidence checks rest on.

The top 20 program prepared one submission pack per directory
for the Cursor Marketplace, the Claude plugin directory, and
the Agent Plugins portable package. Nothing in any pack has
been submitted, and each pack says so in a pinned sentence.
The claim check reads the packs the way the later build gates
read their briefs, on flattened lower case text with the
honest sentence lifted out first, so a filed or live listing
claim fails here in any case and in the ordinary wordings of
such a claim, and a promised review timeline fails with it,
since no primary source states one. Each pack also states the
version it was written against and the date its requirements
were read, and this gate holds both against the shipped
manifests, so a version bump or a stale pack fails here
instead of reaching a filing. The load bearing figures in
the pack prose stand pinned beside the sentences. The
Claude pack tree figures, its file count and its largest
file sizes and its credential scan count, stand pinned in
that same style, and the gate test suite measures them
against the tracked tree, so a tree that grows or shrinks
past the stated figures fails instead of drifting in
silence the way SC3 kept doing.

The evidence half pins the manifest facts the packs assert.
The Cursor marketplace file carries its required name and
owner and one entry, and the Cursor manifest carries the
description, author, and license the checklist asks about,
with the logo, skill, and rule paths resolving in the tree.
The Claude manifest carries the fields its evidence check
names, with its component paths resolving inside the folder,
its marketplace file carries the required name and owner,
and its recognitio entry matches the manifest in name,
source, and strict mode, beside the recognitio-mod entry
the same pack names with its own folder source and strict
mode. The portable manifest stays inside the closed
ten field set of the Agent Plugins specification and carries
the exact values the host listing would read from it. A
license file stands at the root the Claude pack names as
the plugin folder.

Exits nonzero with one line per problem when anything fails.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CURSOR_PACK = "docs/submission-cursor.md"
CLAUDE_PACK = "docs/submission-claude.md"
PORTABLE_PACK = "docs/submission-agent-plugins.md"
CLAUDE_PLUGIN = ".claude-plugin/plugin.json"
CLAUDE_MARKET = ".claude-plugin/marketplace.json"
CURSOR_PLUGIN = ".cursor-plugin/plugin.json"
CURSOR_MARKET = ".cursor-plugin/marketplace.json"
PORTABLE = "agent-plugins-package/plugin.json"

REPO_URL = "https://github.com/david-engelmann/recognitio"
SCHEMA_URL = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
HONEST_SENTENCE = "nothing in this pack has been submitted."

PACK_ROUTES = {
    CURSOR_PACK: ("cursor.com/marketplace/publish",),
    CLAUDE_PACK: ("claude.ai/directory/manage",),
    PORTABLE_PACK: (
        "The Agent Plugins project runs no directory of packages.",
        "github/awesome-copilot",
        "plugins/external.json",
    ),
}

# Load bearing figures and promises in the pack prose. A
# drift in any of them is a falsified pack under a green
# gate, so each stands pinned word for word.
PACK_PINS = {
    CURSOR_PACK: (
        "must stay at or under 10 MB",
        "Every plugin is manually reviewed before it is listed",
    ),
    CLAUDE_PACK: (
        "at least 40 words",
        "must stay under 5 MiB",
        "holds 238 files",
        "held 238 files",
        "at 238 files against a cap of 512 files",
        "demo recording at 607,309 bytes",
        "tests/test_gate_scripts.py at 263,066 bytes",
        "scan over all 238 tracked files",
    ),
    PORTABLE_PACK: (
        "six month cycle",
    ),
}

COMMON_FRAGMENTS = (
    "Nothing in this pack has been submitted.",
    "Requirements were read from the primary sources named "
    "in this pack on 2026-10-27.",
    "## What remains David's act",
)

# Claims of a filed or live listing, read on the flattened
# lower case text with the honest sentence lifted out. A
# prepared pack must never carry one, in the same spirit as
# the stale wording refusals the other gates hold.
BANNED_CLAIMS = (
    "listing is live",
    "is now listed",
    "is listed in",
    "is listed on",
    "listed in the marketplace",
    "pack has been submitted",
    "was approved and listed",
    "approved for listing",
    "we filed",
    "filed the submission",
    "submission was filed",
    "has been filed",
    "is now live",
)

PACK_BANNED_CLAIMS = {
    CLAUDE_PACK: ("is available in the directory",),
    PORTABLE_PACK: (
        "runs a package registry",
        "runs a registry",
        "operates a directory",
    ),
}

# No primary source states a review timeline for any of the
# three routes, so a promised one fails in any pack, in
# digits or in number words.
TIMELINE_CLAIM = re.compile(
    r"within ([0-9]+|one|two|three|four|five|six|seven|"
    r"eight|nine|ten|fourteen|thirty|sixty|ninety) "
    r"(business )?(day|days|week|weeks)")

CLOSED_FIELDS = {
    "$schema", "name", "version", "description", "author",
    "homepage", "repository", "license", "keywords",
    "extensions",
}

NAME_PATTERN = re.compile(r"[a-z0-9]([a-z0-9.-]*[a-z0-9])?")
KEYWORD_PATTERN = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")


def semver_ok(value):
    """The house version shape, ASCII digits, no leading zeros."""
    if not isinstance(value, str):
        return False
    parts = value.split(".")
    if len(parts) != 3:
        return False
    for part in parts:
        if not part or not part.isascii() or not part.isdigit():
            return False
        if len(part) > 1 and part.startswith("0"):
            return False
    return True


class DuplicateKeyError(ValueError):
    """A JSON object names one key twice."""


def strict_json_loads(text):
    """Parse JSON refusing a repeated key and the loose constants."""
    def reject(pairs):
        seen = {}
        for key, value in pairs:
            if key in seen:
                raise DuplicateKeyError("repeated key %r" % (key,))
            seen[key] = value
        return seen

    def reject_constant(value):
        raise ValueError("loose JSON constant %r" % (value,))
    return json.loads(
        text, object_pairs_hook=reject,
        parse_constant=reject_constant)


def load_manifest(root, rel, problems):
    path = root / rel
    if path.exists() and not path.is_file():
        problems.append(
            "%s cannot be read, it is not a regular file" % rel)
        return None
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        problems.append("%s is missing" % rel)
        return None
    try:
        data = strict_json_loads(raw)
    except (ValueError, DuplicateKeyError) as exc:
        problems.append("%s does not parse, %s" % (rel, exc))
        return None
    if not isinstance(data, dict):
        problems.append("%s is not an object" % rel)
        return None
    return data


def author_name(data):
    author = data.get("author")
    if isinstance(author, dict):
        return author.get("name")
    return None


def field_problems(rel, data, field, problems, why):
    if not data.get(field):
        problems.append("%s carries no %s, %s" % (rel, field, why))


def license_problems(rel, data, problems):
    if data.get("license") != "MIT":
        problems.append(
            "%s carries license %r and the pack states MIT"
            % (rel, data.get("license")))


def owner_problems(rel, market, problems, why):
    owner = market.get("owner")
    if not isinstance(owner, dict) or not owner.get("name"):
        problems.append(
            "%s carries no owner name, %s" % (rel, why))


def entry_problems(rel, market, plugin, problems):
    entries = market.get("plugins")
    if not isinstance(entries, list) or len(entries) != 1:
        problems.append(
            "%s must list exactly one plugin entry" % rel)
        return None
    entry = entries[0]
    if not isinstance(entry, dict):
        problems.append("%s carries an entry that is not an object" % rel)
        return None
    if plugin is not None and entry.get("name") != plugin.get("name"):
        problems.append(
            "%s entry name %r does not match the manifest "
            "name %r" % (rel, entry.get("name"), plugin.get("name")))
    if plugin is not None:
        # The Cursor pack states the entry paths resolve
        # from the one plugin root, so this gate reads the
        # entry source, skills, and logo the way the Cursor
        # gate does and pins them to the manifest values.
        # An entry path written from another base resolves
        # nowhere under its own source, and a gate that
        # never opened those values would certify the pack
        # sentence in silence.
        if entry.get("source") != "./":
            problems.append(
                "%s entry carries source %r and the pack "
                "states the plugin root the manifest stands "
                "at" % (rel, entry.get("source")))
        if entry.get("skills") != plugin.get("skills"):
            problems.append(
                "%s entry carries skills %r and the manifest "
                "carries %r, so the entry paths do not "
                "resolve from the entry source"
                % (rel, entry.get("skills"), plugin.get("skills")))
        if entry.get("logo") != plugin.get("logo"):
            problems.append(
                "%s entry carries logo %r and the manifest "
                "carries %r"
                % (rel, entry.get("logo"), plugin.get("logo")))
    return entry


def claude_entry_problems(rel, market, plugin, problems):
    """The Claude listing holds the recognitio and mod entries.

    The recognitio entry comes back for the source and strict
    checks the caller runs, and the recognitio-mod entry is
    named here so a listing that lost it, or renamed it, or
    grew a third entry fails in this gate as well.
    """
    entries = market.get("plugins")
    if not isinstance(entries, list) or len(entries) != 2:
        problems.append(
            "%s must list exactly two plugin entries, the "
            "recognitio plugin and the recognitio-mod plugin"
            % rel)
        return None
    by_name = {}
    for entry in entries:
        if not isinstance(entry, dict):
            problems.append(
                "%s carries an entry that is not an object" % rel)
            return None
        by_name[entry.get("name")] = entry
    entry = by_name.get("recognitio")
    if entry is None:
        if plugin is not None:
            problems.append(
                "%s entry name %r does not match the manifest "
                "name %r"
                % (rel, entries[0].get("name"),
                   plugin.get("name")))
        else:
            problems.append(
                "%s lists no recognitio entry" % rel)
        return None
    if plugin is not None and entry.get("name") != plugin.get("name"):
        problems.append(
            "%s entry name %r does not match the manifest "
            "name %r" % (rel, entry.get("name"), plugin.get("name")))
    mod = by_name.get("recognitio-mod")
    if mod is None:
        problems.append(
            "%s lists no recognitio-mod entry, and the Claude "
            "pack names the mod entry beside the plugin entry"
            % rel)
    else:
        if mod.get("source") != "./plugins/recognitio-mod":
            problems.append(
                "%s recognitio-mod entry carries source %r and "
                "the pack states the mod plugin folder"
                % (rel, mod.get("source")))
        if mod.get("strict") is not True:
            problems.append(
                "%s recognitio-mod entry carries strict %r and "
                "the pack states strict mode on"
                % (rel, mod.get("strict")))
    return entry


def shipped_path(root, value):
    """Resolve a manifest path, refusing the forbidden shapes.

    An absolute value, a parent reference, and an empty value
    resolve to nothing here rather than being normalised into
    the tree, because both platforms forbid those shapes and
    a gate that rewrites them before judging them cannot
    fail for the reason it exists.
    """
    if not isinstance(value, str) or not value:
        return None
    if value.startswith("/") or value.startswith("\\"):
        return None
    parts = value.split("/")
    if ".." in parts:
        return None
    if value.startswith("./"):
        value = value[2:]
    return root / value


def pack_problems(root, version, problems):
    for rel, routes in PACK_ROUTES.items():
        path = root / rel
        if path.exists() and not path.is_file():
            problems.append(
                "%s cannot be read, it is not a regular file" % rel)
            continue
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError:
            problems.append("%s is missing" % rel)
            continue
        # The packs wrap their prose across lines, so the
        # pinned sentences are read on the flattened text.
        text = re.sub(r"\s+", " ", raw)
        for fragment in COMMON_FRAGMENTS:
            if fragment not in text:
                problems.append(
                    "%s no longer states %r" % (rel, fragment))
        if version is not None:
            sentence = "written against version %s of recognitio" % version
            if sentence not in text:
                problems.append(
                    "%s no longer states the version sentence for "
                    "%s" % (rel, version))
        for route in routes:
            if route not in text:
                problems.append(
                    "%s no longer names %r" % (rel, route))
        for pin in PACK_PINS[rel]:
            if pin not in text:
                problems.append(
                    "%s no longer states %r" % (rel, pin))
        lowered = text.lower().replace(HONEST_SENTENCE, "")
        claims = BANNED_CLAIMS + PACK_BANNED_CLAIMS.get(rel, ())
        for claim in claims:
            if claim in lowered:
                problems.append(
                    "%s carries the filed listing claim %r and "
                    "nothing in the pack has been submitted"
                    % (rel, claim))
        if TIMELINE_CLAIM.search(lowered):
            problems.append(
                "%s promises a review timeline and no primary "
                "source states one" % rel)


def cursor_problems(root, problems):
    plugin = load_manifest(root, CURSOR_PLUGIN, problems)
    market = load_manifest(root, CURSOR_MARKET, problems)
    if plugin is not None:
        field_problems(
            CURSOR_PLUGIN, plugin, "description", problems,
            "and the submission checklist asks for one that "
            "states the purpose")
        if not author_name(plugin):
            problems.append(
                "%s carries no author name" % CURSOR_PLUGIN)
        license_problems(CURSOR_PLUGIN, plugin, problems)
        logo = shipped_path(root, plugin.get("logo"))
        if logo is None or not logo.is_file():
            problems.append(
                "%s names a logo path that does not resolve in "
                "the tree" % CURSOR_PLUGIN)
        # Every path in the Cursor manifest resolves from
        # the one plugin root, which is the repo root in
        # this tree, as the Cursor gate reads them. A path
        # written from the manifest folder resolves nowhere
        # under that base.
        for value in plugin.get("skills") or []:
            target = shipped_path(root, value)
            if target is None or not (target / "SKILL.md").is_file():
                problems.append(
                    "%s names a skills path with no SKILL.md "
                    "inside it" % CURSOR_PLUGIN)
        for value in plugin.get("rules") or []:
            target = shipped_path(root, value)
            if target is None or not target.is_file():
                problems.append(
                    "%s names a rule path that does not resolve "
                    "in the tree" % CURSOR_PLUGIN)
    if market is not None:
        field_problems(
            CURSOR_MARKET, market, "name", problems,
            "and the reference marks it required")
        owner_problems(
            CURSOR_MARKET, market, problems,
            "and the reference marks it required")
        entry_problems(CURSOR_MARKET, market, plugin, problems)


def claude_problems(root, problems):
    plugin = load_manifest(root, CLAUDE_PLUGIN, problems)
    market = load_manifest(root, CLAUDE_MARKET, problems)
    version = None
    if plugin is not None:
        version = plugin.get("version")
        if not version:
            problems.append(
                "%s carries no version and the packs state the "
                "version they were written against" % CLAUDE_PLUGIN)
        for field in ("displayName", "description", "keywords",
                      "homepage"):
            field_problems(
                CLAUDE_PLUGIN, plugin, field, problems,
                "and the pack evidence check names it as carried")
        if plugin.get("repository") != REPO_URL:
            problems.append(
                "%s carries repository %r and the pack states "
                "the public repo"
                % (CLAUDE_PLUGIN, plugin.get("repository")))
        if not author_name(plugin):
            problems.append(
                "%s carries no author name and the directory "
                "checklist warns on its absence" % CLAUDE_PLUGIN)
        license_problems(CLAUDE_PLUGIN, plugin, problems)
        icon = shipped_path(root, plugin.get("icon"))
        if icon is None or not icon.is_file():
            problems.append(
                "%s names an icon path that does not resolve "
                "in the tree" % CLAUDE_PLUGIN)
        for value in plugin.get("skills") or []:
            target = shipped_path(root, value)
            if target is None or not target.is_dir():
                problems.append(
                    "%s names a skills path that does not "
                    "resolve inside the folder" % CLAUDE_PLUGIN)
        for field in ("agents", "outputStyles"):
            for value in plugin.get(field) or []:
                target = shipped_path(root, value)
                if target is None or not target.is_file():
                    problems.append(
                        "%s names a %s path that does not "
                        "resolve inside the folder"
                        % (CLAUDE_PLUGIN, field))
    if market is not None:
        field_problems(
            CLAUDE_MARKET, market, "name", problems,
            "and the marketplace reference marks it required")
        owner_problems(
            CLAUDE_MARKET, market, problems,
            "and the marketplace reference marks it required")
        entry = claude_entry_problems(
            CLAUDE_MARKET, market, plugin, problems)
        if entry is not None:
            if entry.get("source") != "./":
                problems.append(
                    "%s entry carries source %r and the pack "
                    "states the root"
                    % (CLAUDE_MARKET, entry.get("source")))
            if entry.get("strict") is not True:
                problems.append(
                    "%s entry carries strict %r and the pack "
                    "states strict mode on"
                    % (CLAUDE_MARKET, entry.get("strict")))
    if not (root / "LICENSE").is_file():
        problems.append(
            "LICENSE is missing from the plugin folder the "
            "Claude pack names")
    return version


def portable_problems(root, problems):
    data = load_manifest(root, PORTABLE, problems)
    if data is None:
        return
    extra = sorted(set(data) - CLOSED_FIELDS)
    if extra:
        problems.append(
            "%s carries top level fields outside the closed "
            "set of the specification, %s"
            % (PORTABLE, ", ".join(extra)))
    if data.get("$schema") != SCHEMA_URL:
        problems.append(
            "%s carries $schema %r and the pack states the "
            "canonical 1.0.0 schema"
            % (PORTABLE, data.get("$schema")))
    name = data.get("name")
    if name != "recognitio":
        problems.append(
            "%s carries name %r and the pack states the "
            "shipped package name" % (PORTABLE, name))
    if not isinstance(name, str) \
            or not NAME_PATTERN.fullmatch(name) \
            or "--" in name or ".." in name or len(name) > 64:
        problems.append(
            "%s carries name %r outside the pattern the "
            "specification names" % (PORTABLE, name))
    if not semver_ok(data.get("version")):
        problems.append(
            "%s carries version %r and the host listing asks "
            "for a semantic version" % (PORTABLE, data.get("version")))
    field_problems(
        PORTABLE, data, "description", problems,
        "and the host listing asks for one")
    if not author_name(data):
        problems.append(
            "%s carries no author name and the host listing "
            "asks for one" % PORTABLE)
    license_problems(PORTABLE, data, problems)
    if data.get("homepage") != REPO_URL:
        problems.append(
            "%s carries homepage %r and the pack states the "
            "public repo" % (PORTABLE, data.get("homepage")))
    if data.get("repository") != REPO_URL:
        problems.append(
            "%s carries repository %r and the host listing "
            "files against the public repo"
            % (PORTABLE, data.get("repository")))
    expected_keywords = ["review-packet", "agent-skill",
                         "pull-request"]
    if data.get("keywords") != expected_keywords:
        problems.append(
            "%s carries keywords %r and the pack states the "
            "set the host listing would read"
            % (PORTABLE, data.get("keywords")))
    keywords = data.get("keywords")
    if isinstance(keywords, list):
        for word in keywords:
            if not isinstance(word, str) \
                    or not KEYWORD_PATTERN.fullmatch(word):
                problems.append(
                    "%s carries keyword %r outside the lowercase "
                    "hyphenated form the host listing asks for"
                    % (PORTABLE, word))
    extensions = data.get("extensions")
    if not isinstance(extensions, dict) or not extensions:
        problems.append(
            "%s carries no extension declarations and the "
            "package exists to carry them" % PORTABLE)
    skill = root / "agent-plugins-package" / "skills" \
        / "recognitio" / "SKILL.md"
    if not skill.is_file():
        problems.append(
            "the portable package skill is missing from its "
            "fixed location")


def submissions_problems(root=None):
    """Problems with the submission packs or their facts."""
    root = ROOT if root is None else root
    problems = []
    cursor_problems(root, problems)
    version = claude_problems(root, problems)
    portable_problems(root, problems)
    pack_problems(root, version, problems)
    return problems


def main():
    problems = submissions_problems()
    if problems:
        for problem in problems:
            print("check_submissions: %s" % problem, file=sys.stderr)
        return 1
    print(
        "check_submissions: the three submission packs stand "
        "unsubmitted at the shipped version, and every manifest "
        "fact their evidence checks rest on holds in the tree"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
