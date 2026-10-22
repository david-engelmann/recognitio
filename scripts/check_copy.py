#!/usr/bin/env python3
"""Enforce the copy bar on the public prose files.

The bar bans three marks from prose sentences. Em dashes, semicolons
and colons all push a writer toward compressed clauses, and the house
style is short plain sentences instead. The em dash is matched by
codepoint because a shell grep for the character once reported zero
hits on a tree full of them.

Code is exempt. Fenced code blocks and inline code spans are skipped,
as are YAML frontmatter keys, link reference definitions and lines
that hold nothing but a file path. A URL exempts only its own span of
a line, never the whole line, so a banned mark hiding beside a link
is still caught.

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
    ROOT / "CLAUDE.md",
    ROOT / "docs" / "decisions.md",
    ROOT / "skills" / "recognitio" / "SKILL.md",
    ROOT / ".github" / "pull_request_template.md",
    ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.md",
    ROOT / ".github" / "ISSUE_TEMPLATE" / "feature_request.md",
    ROOT / ".coderabbit.yaml",
]

EM_DASH = "\u2014"
FRONTMATTER_KEY = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*:(\s|$)")
LINK_REFERENCE = re.compile(r"^\s*\[[^\]]+\]:")
BARE_PATH = re.compile(r"^[\w.@~+-]+(/[\w.@~+-]+)+/?$")
INLINE_CODE = re.compile(r"`[^`]*`")
URL_SPAN = re.compile(r"https?://\S+")
YAML_KEY = re.compile(r"^\s*[A-Za-z_][A-Za-z0-9_-]*:(\s+(.*))?$")
YAML_BLOCK = re.compile(r":\s*[|>][+-]?\s*$")


def clean(text):
    """Remove the spans of a line the bar does not reach."""
    text = URL_SPAN.sub("", text)
    text = INLINE_CODE.sub("", text)
    return text


def prose_lines(path):
    """Yield (number, text) pairs for the lines the bar applies to."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if path.suffix in (".yaml", ".yml"):
        yield from yaml_prose_lines(lines)
        return
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
                yield number, clean(raw.split(":", 1)[1])
            else:
                yield number, clean(raw)
            continue
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if LINK_REFERENCE.match(raw):
            continue
        if BARE_PATH.match(stripped):
            continue
        yield number, clean(raw)


def yaml_prose_lines(lines):
    """Yield the prose of a YAML file.

    Comments are prose. So are block scalar bodies and the plain or
    quoted values on key lines. Keys and structure are syntax.
    """
    block_indent = None
    for number, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        indent = len(raw) - len(raw.lstrip())
        if block_indent is not None:
            if stripped and indent <= block_indent:
                block_indent = None
            else:
                if stripped:
                    yield number, clean(raw)
                continue
        if not stripped:
            continue
        if stripped.startswith("#"):
            body = stripped.lstrip("#").strip()
            # Editor directives are machine syntax, not prose.
            if body.startswith("yaml-language-server"):
                continue
            yield number, clean(body)
            continue
        if YAML_BLOCK.search(raw):
            block_indent = indent
            continue
        candidate = stripped[2:] if stripped.startswith("- ") else stripped
        match = YAML_KEY.match(candidate)
        if match:
            value = match.group(2)
            if value:
                yield number, clean(value)
            continue
        yield number, clean(raw)


def display_name(path):
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def main():
    violations = []
    for path in PROSE_FILES:
        if not path.is_file():
            violations.append("%s is missing" % display_name(path))
            continue
        for number, text in prose_lines(path):
            where = "%s line %d" % (display_name(path), number)
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
