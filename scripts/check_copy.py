#!/usr/bin/env python3
"""Enforce the copy bar on the public prose files.

The bar bans three marks from prose sentences. Em dashes, semicolons
and colons all push a writer toward compressed clauses, and the house
style is short plain sentences instead. The em dash is matched by
codepoint because a shell grep for the character once reported zero
hits on a tree full of them.

Code is exempt. Fenced code blocks and inline code spans are skipped,
as are YAML frontmatter keys, lines that carry a URL, link reference
definitions and lines that hold nothing but a file path.

Exits nonzero and lists every violation when the bar is broken.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROSE_FILES = [
    ROOT / "README.md",
    ROOT / "AGENTS.md",
    ROOT / "CHANGELOG.md",
    ROOT / "skills" / "recognitio" / "SKILL.md",
]

EM_DASH = "\u2014"
FRONTMATTER_KEY = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*:(\s|$)")
LINK_REFERENCE = re.compile(r"^\s*\[[^\]]+\]:")
BARE_PATH = re.compile(r"^[\w.@~+-]+(/[\w.@~+-]+)+/?$")
INLINE_CODE = re.compile(r"`[^`]*`")


def prose_lines(path):
    """Yield (number, text) pairs for the lines the bar applies to."""
    lines = path.read_text(encoding="utf-8").splitlines()
    in_fence = False
    in_frontmatter = False
    for number, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if number == 1 and stripped == "---":
            in_frontmatter = True
            continue
        if in_frontmatter:
            if stripped == "---":
                in_frontmatter = False
            elif FRONTMATTER_KEY.match(raw):
                # The key is syntax. The value after it stays prose.
                yield number, raw.split(":", 1)[1]
            else:
                yield number, raw
            continue
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if "://" in raw:
            continue
        if LINK_REFERENCE.match(raw):
            continue
        if BARE_PATH.match(stripped):
            continue
        yield number, INLINE_CODE.sub("", raw)


def main():
    violations = []
    for path in PROSE_FILES:
        if not path.is_file():
            violations.append("%s is missing" % path.relative_to(ROOT))
            continue
        for number, text in prose_lines(path):
            where = "%s line %d" % (path.relative_to(ROOT), number)
            if EM_DASH in text:
                violations.append("%s has an em dash" % where)
            if ";" in text:
                violations.append("%s has a semicolon" % where)
            if ":" in text:
                violations.append("%s has a colon in prose" % where)
    if violations:
        for violation in violations:
            print("check_copy: %s" % violation, file=sys.stderr)
        return 1
    print("check_copy: copy bar holds on %d prose files" % len(PROSE_FILES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
