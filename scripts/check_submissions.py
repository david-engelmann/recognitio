#!/usr/bin/env python3
"""Pin the submission packs and the facts their evidence checks rest on.

The top 20 program prepared one submission pack per directory
for the Cursor Marketplace, the Claude plugin directory, and
the Agent Plugins portable package. Nothing in any pack has
been submitted, and each pack says so in a pinned sentence, so
a later edit cannot quietly turn a prepared pack into a
claimed listing. Each pack also states the version it was
written against and the date its requirements were read, and
this gate holds both against the shipped manifests, so a
version bump or a stale pack fails here instead of reaching
a filing.

The evidence half pins the manifest facts the packs assert.
The Cursor marketplace file carries its required name and
owner and one entry, and the Cursor manifest carries the
description, author, and license the checklist asks about,
with the logo, skill, and rule paths resolving in the tree.
The Claude manifest carries the author and license its
directory validation warns or blocks on, its marketplace
file carries the required owner, and its one entry name
matches the manifest name. The portable manifest stays
inside the closed ten field set of the Agent Plugins
specification, with a name inside the pattern the
specification names, a semantic version, lowercase
hyphenated keywords, and an HTTPS GitHub repository value.
A license file stands at the root the Claude pack names as
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

PACK_ROUTES = {
    CURSOR_PACK: ("cursor.com/marketplace/publish",),
    CLAUDE_PACK: ("claude.ai/directory/manage",),
    PORTABLE_PACK: (
        "The Agent Plugins project runs no directory of packages.",
        "github/awesome-copilot",
        "plugins/external.json",
    ),
}

COMMON_FRAGMENTS = (
    "Nothing in this pack has been submitted.",
    "Requirements were read from the primary sources named "
    "in this pack on 2026-10-27.",
    "## What remains David's act",
)

# Claims of a filed or live listing. A prepared pack must
# never carry one, in the same spirit as the stale wording
# refusals the other gates hold.
BANNED_CLAIMS = (
    "is now listed",
    "listing is live",
    "submission was filed",
    "has been filed",
    "was approved for listing",
)

CLOSED_FIELDS = {
    "$schema", "name", "version", "description", "author",
    "homepage", "repository", "license", "keywords",
    "extensions",
}

NAME_PATTERN = re.compile(r"^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$")
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
KEYWORD_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class DuplicateKeyError(ValueError):
    """A JSON object names one key twice."""


def strict_json_loads(text):
    """Parse JSON refusing a repeated key, like the other gates."""
    def reject(pairs):
        seen = {}
        for key, value in pairs:
            if key in seen:
                raise DuplicateKeyError("repeated key %r" % (key,))
            seen[key] = value
        return seen
    return json.loads(text, object_pairs_hook=reject)


def load_manifest(root, rel, problems):
    path = root / rel
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


def single_entry(rel, data, problems):
    entries = data.get("plugins")
    if not isinstance(entries, list) or len(entries) != 1:
        problems.append(
            "%s must list exactly one plugin entry" % rel)
        return None
    entry = entries[0]
    if not isinstance(entry, dict):
        problems.append("%s carries an entry that is not an object" % rel)
        return None
    return entry


def pack_problems(root, version, problems):
    for rel, routes in PACK_ROUTES.items():
        path = root / rel
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
        for claim in BANNED_CLAIMS:
            if claim in text:
                problems.append(
                    "%s carries the filed listing claim %r and "
                    "nothing in the pack has been submitted"
                    % (rel, claim))


def shipped_path(root, value):
    if not isinstance(value, str):
        return None
    return root / value.lstrip("./")


def cursor_problems(root, problems):
    plugin = load_manifest(root, CURSOR_PLUGIN, problems)
    market = load_manifest(root, CURSOR_MARKET, problems)
    if plugin is not None:
        if not plugin.get("description"):
            problems.append(
                "%s carries no description and the submission "
                "checklist asks for one that states the purpose"
                % CURSOR_PLUGIN)
        if not author_name(plugin):
            problems.append(
                "%s carries no author name" % CURSOR_PLUGIN)
        if plugin.get("license") != "MIT":
            problems.append(
                "%s carries license %r and the pack states MIT"
                % (CURSOR_PLUGIN, plugin.get("license")))
        logo = shipped_path(root, plugin.get("logo"))
        if logo is None or not logo.is_file():
            problems.append(
                "%s names a logo path that does not resolve in "
                "the tree" % CURSOR_PLUGIN)
        # Component paths in the Cursor manifest resolve from
        # the plugin dir that holds the manifest, as the
        # Cursor gate reads them. The logo value resolves
        # from the repo root, as the reference states.
        plugin_dir = root / ".cursor-plugin"
        skills = plugin.get("skills") or []
        for value in skills:
            target = shipped_path(plugin_dir, value)
            if target is None or not (target / "SKILL.md").is_file():
                problems.append(
                    "%s names a skills path with no SKILL.md "
                    "inside it" % CURSOR_PLUGIN)
        for value in plugin.get("rules") or []:
            target = shipped_path(plugin_dir, value)
            if target is None or not target.is_file():
                problems.append(
                    "%s names a rule path that does not resolve "
                    "in the tree" % CURSOR_PLUGIN)
    if market is not None:
        if not market.get("name"):
            problems.append(
                "%s carries no name and the reference marks it "
                "required" % CURSOR_MARKET)
        owner = market.get("owner")
        if not isinstance(owner, dict) or not owner.get("name"):
            problems.append(
                "%s carries no owner name and the reference "
                "marks it required" % CURSOR_MARKET)
        entry = single_entry(CURSOR_MARKET, market, problems)
        if entry is not None and plugin is not None:
            if entry.get("name") != plugin.get("name"):
                problems.append(
                    "%s entry name %r does not match the "
                    "manifest name %r"
                    % (CURSOR_MARKET, entry.get("name"),
                       plugin.get("name")))


def claude_problems(root, problems):
    plugin = load_manifest(root, CLAUDE_PLUGIN, problems)
    market = load_manifest(root, CLAUDE_MARKET, problems)
    version = None
    if plugin is not None:
        version = plugin.get("version")
        if not author_name(plugin):
            problems.append(
                "%s carries no author name and the directory "
                "checklist warns on its absence" % CLAUDE_PLUGIN)
        if plugin.get("license") != "MIT":
            problems.append(
                "%s carries license %r and the pack states MIT"
                % (CLAUDE_PLUGIN, plugin.get("license")))
        icon = shipped_path(root, plugin.get("icon"))
        if icon is None or not icon.is_file():
            problems.append(
                "%s names an icon path that does not resolve "
                "in the tree" % CLAUDE_PLUGIN)
    if market is not None:
        owner = market.get("owner")
        if not isinstance(owner, dict) or not owner.get("name"):
            problems.append(
                "%s carries no owner name and the marketplace "
                "reference marks it required" % CLAUDE_MARKET)
        entry = single_entry(CLAUDE_MARKET, market, problems)
        if entry is not None and plugin is not None:
            if entry.get("name") != plugin.get("name"):
                problems.append(
                    "%s entry name %r does not match the "
                    "manifest name %r"
                    % (CLAUDE_MARKET, entry.get("name"),
                       plugin.get("name")))
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
    name = data.get("name")
    if not isinstance(name, str) or not NAME_PATTERN.match(name) \
            or "--" in name or ".." in name or len(name) > 64:
        problems.append(
            "%s carries name %r outside the pattern the "
            "specification names" % (PORTABLE, name))
    version = data.get("version")
    if not isinstance(version, str) \
            or not SEMVER_PATTERN.match(version):
        problems.append(
            "%s carries version %r and the host listing asks "
            "for a semantic version" % (PORTABLE, version))
    keywords = data.get("keywords")
    if not isinstance(keywords, list) or not keywords:
        problems.append("%s carries no keyword set" % PORTABLE)
    else:
        for word in keywords:
            if not isinstance(word, str) \
                    or not KEYWORD_PATTERN.match(word):
                problems.append(
                    "%s carries keyword %r outside the lowercase "
                    "hyphenated form the host listing asks for"
                    % (PORTABLE, word))
    repository = data.get("repository")
    if not isinstance(repository, str) \
            or not repository.startswith("https://github.com/"):
        problems.append(
            "%s carries repository %r and the host listing "
            "asks for an HTTPS GitHub URL" % (PORTABLE, repository))
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
