#!/usr/bin/env python3
"""Pin the discovery metadata on the Claude and Cursor surfaces.

The top 20 program filled the discovery fields each manifest
schema allows, and this gate pins the filled values so a later
edit cannot quietly empty or drift them. The primary sources
are the Claude Code plugin manifest reference and marketplace
reference at code.claude.com, read on 2026-10-26, and the
Cursor plugin manifest schema the Cursor project ships, read
the same day.

The manifest reference names displayName and homepage and
repository and keywords as plugin.json fields. It names no
category or tags field for plugin.json, and an unrecognized
top level key is stripped at load with a validator warning,
so this gate fails a plugin.json that carries either one.
The marketplace reference names category and tags as plugin
entry fields, and the manifest reference states that the
directory listing fields belong in plugin.json only and are
reported as unknown fields in a marketplace entry. The
display fields live in plugin.json as the single source, and
an entry value would override the manifest value wherever
the two drifted, so the entry carries none of them.

The Cursor manifest schema names displayName and homepage
and repository and keywords and category and tags as
plugin.json fields, and its marketplace entry schema names
none of them, so on that surface every discovery field lives
in the manifest. The Cursor gate at scripts/check_cursor.py
pins the Cursor manifest values to its own constants, and
this gate pins the agreement of the two surfaces, so the
display name and the homepage and the repository and the
keyword set and the category a searcher meets are the same
on both.

Two listing shapes carry the filled fields and are pinned
with them. The Claude listing holds exactly one plugin
entry, and the Cursor marketplace entry carries no
discovery field, since its entry schema names none and a
field placed there would contradict the manifest only fill.

Exits nonzero with one line per problem when anything fails.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAUDE_PLUGIN = ".claude-plugin/plugin.json"
CLAUDE_MARKET = ".claude-plugin/marketplace.json"
CURSOR_PLUGIN = ".cursor-plugin/plugin.json"
CURSOR_MARKET = ".cursor-plugin/marketplace.json"

DISPLAY_NAME = "Recognitio"
HOMEPAGE = "https://github.com/david-engelmann/recognitio"
REPOSITORY = "https://github.com/david-engelmann/recognitio"
KEYWORDS = [
    "agent-skills",
    "code-review",
    "diff",
    "git",
    "pull-request",
    "review-packet",
]
CATEGORY = "developer-tools"

# The directory listing fields the manifest reference reads
# from plugin.json only. In a marketplace entry the validator
# reports each one as an unknown field.
DIRECTORY_FIELDS = (
    "icon",
    "documentationUrl",
    "supportUrl",
    "privacyPolicyUrl",
    "termsOfServiceUrl",
)

# The display fields plugin.json carries as the single
# source. An entry that sets one overrides the manifest
# value a reader sees, so the entry carries none of them.
ENTRY_DISPLAY_FIELDS = (
    "displayName",
    "homepage",
    "repository",
    "keywords",
)


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


def value_problems(rel, data, field, expected, problems):
    found = data.get(field)
    if found != expected:
        problems.append(
            "%s carries %s %r and the pinned value is %r"
            % (rel, field, found, expected)
        )


def discovery_problems(root=None):
    """Problems with the discovery metadata across the surfaces."""
    root = ROOT if root is None else root
    problems = []
    claude = load_manifest(root, CLAUDE_PLUGIN, problems)
    market = load_manifest(root, CLAUDE_MARKET, problems)
    cursor = load_manifest(root, CURSOR_PLUGIN, problems)
    cursor_market = load_manifest(root, CURSOR_MARKET, problems)

    if claude is not None:
        value_problems(
            CLAUDE_PLUGIN, claude, "displayName", DISPLAY_NAME, problems)
        value_problems(
            CLAUDE_PLUGIN, claude, "homepage", HOMEPAGE, problems)
        value_problems(
            CLAUDE_PLUGIN, claude, "repository", REPOSITORY, problems)
        value_problems(
            CLAUDE_PLUGIN, claude, "keywords", KEYWORDS, problems)
        for field in ("category", "tags"):
            if field in claude:
                problems.append(
                    "%s carries %s and the manifest reference names "
                    "no such plugin.json field, so the host strips "
                    "it at load" % (CLAUDE_PLUGIN, field)
                )

    if market is not None:
        entries = market.get("plugins")
        if not isinstance(entries, list) or not entries:
            problems.append(
                "%s lists no plugin entry" % CLAUDE_MARKET)
            entries = []
        elif len(entries) != 1:
            problems.append(
                "%s lists %d plugin entries and the listing "
                "holds one plugin entry"
                % (CLAUDE_MARKET, len(entries)))
        for entry in entries:
            if not isinstance(entry, dict):
                problems.append(
                    "%s carries a plugin entry that is not an "
                    "object" % CLAUDE_MARKET)
                continue
            value_problems(
                CLAUDE_MARKET + " entry", entry, "category",
                CATEGORY, problems)
            value_problems(
                CLAUDE_MARKET + " entry", entry, "tags",
                KEYWORDS, problems)
            for field in DIRECTORY_FIELDS:
                if field in entry:
                    problems.append(
                        "%s entry carries %s and the directory "
                        "listing fields live in plugin.json only"
                        % (CLAUDE_MARKET, field)
                    )
            for field in ENTRY_DISPLAY_FIELDS:
                if field in entry:
                    problems.append(
                        "%s entry carries %s and the display "
                        "fields live in plugin.json as the single "
                        "source" % (CLAUDE_MARKET, field)
                    )

    if cursor is not None:
        for field, expected in (
            ("displayName", DISPLAY_NAME),
            ("homepage", HOMEPAGE),
            ("repository", REPOSITORY),
            ("keywords", KEYWORDS),
            ("category", CATEGORY),
            ("tags", KEYWORDS),
        ):
            found = cursor.get(field)
            if found != expected:
                problems.append(
                    "%s carries %s %r and the value the Claude "
                    "surface pins is %r, so the surfaces disagree"
                    % (CURSOR_PLUGIN, field, found, expected)
                )

    if cursor_market is not None:
        cursor_entries = cursor_market.get("plugins")
        if isinstance(cursor_entries, list):
            for entry in cursor_entries:
                if not isinstance(entry, dict):
                    continue
                for field in (
                    "displayName", "homepage", "repository",
                    "keywords", "category", "tags",
                ):
                    if field in entry:
                        problems.append(
                            "%s entry carries %s and the Cursor "
                            "entry schema names no discovery "
                            "field, so the discovery fields live "
                            "in the Cursor manifest only"
                            % (CURSOR_MARKET, field)
                        )
    return problems


def main():
    problems = discovery_problems()
    if problems:
        for problem in problems:
            print("check_discovery: %s" % problem, file=sys.stderr)
        return 1
    print(
        "check_discovery: the discovery fields agree across the "
        "Claude manifest, the Claude marketplace entry and the "
        "Cursor manifest, and no discovery field stands on the "
        "Cursor marketplace entry"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
