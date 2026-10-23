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
is still caught. The span ends at the link boundary, so punctuation
sitting right after a link stays in the prose and is judged.

Four files are mostly code with prose living in their comments.
The workflow, the dependabot config, the Makefile and the
gitignore are scanned by comment span only, so their shell and
pattern lines are never judged as prose while every sentence a
contributor writes in them is.

The fence is discovered by rule rather than listed by hand, so a
new authored prose surface joins it by construction instead of
waiting for someone to remember the list. Every Markdown file in
the tree is prose, apart from the generated packets saved as eval
fixtures, which are extractor output and not authored text. The
description fields of the plugin manifests are prose a reader
meets in a listing, so they are scanned as values. The YAML files
whose values are prose are scanned as YAML, and the files whose
prose lives in hash comments are scanned by comment span.

Exits nonzero and lists every violation when the bar is broken.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def discover_prose_files(root=None):
    """Every authored prose file the bar reaches, found by rule.

    Local dependency and tool directories are not authored prose,
    so a Markdown file under a hidden directory other than the
    GitHub config directory, or under a node_modules directory,
    stays outside the fence, and so does a symlink whose target
    leaves the tree. The generated eval packets stay outside it
    for the reason the module docstring records.
    """
    root = ROOT if root is None else root
    found = []
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root)
        parts = rel.parts
        if any(
            part == "node_modules"
            or (part.startswith(".") and part != ".github")
            for part in parts[:-1]
        ):
            continue
        if len(parts) == 4 and parts[:2] == ("evals", "tasks") \
                and parts[3] == "packet.md":
            continue
        if path.is_symlink():
            try:
                path.resolve().relative_to(root.resolve())
            except ValueError:
                continue
        found.append(path)
    for extra in (
        root / ".github" / "ISSUE_TEMPLATE" / "config.yml",
        root / ".coderabbit.yaml",
    ):
        if extra.is_file():
            found.append(extra)
    return sorted(found)


def discover_comment_files(root=None):
    """Files whose prose lives in hash comments, found by rule."""
    root = ROOT if root is None else root
    found = []
    for path in (
        root / ".github" / "dependabot.yml",
        root / "Makefile",
        root / ".gitignore",
    ):
        if path.is_file():
            found.append(path)
    workflows = root / ".github" / "workflows"
    if workflows.is_dir():
        for path in sorted(workflows.iterdir()):
            if path.suffix in (".yml", ".yaml") and path.is_file():
                found.append(path)
    return sorted(found)


def discover_manifest_files(root=None):
    """Plugin manifests whose description fields are public prose.

    The two paths are fixed surfaces of the repo, so both are
    returned even when one is absent, and the caller reports the
    missing file instead of passing a scan that never ran.
    """
    root = ROOT if root is None else root
    return [
        root / ".claude-plugin" / "plugin.json",
        root / ".claude-plugin" / "marketplace.json",
    ]


PROSE_FILES = discover_prose_files()
COMMENT_FILES = discover_comment_files()
MANIFEST_FILES = discover_manifest_files()

EM_DASH = "\u2014"
FRONTMATTER_KEY = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*:(\s|$)")
LINK_REFERENCE = re.compile(r"^\s*\[[^\]]+\]:")
BARE_PATH = re.compile(r"^[\w.@~+-]+(/[\w.@~+-]+)+/?$")
INLINE_CODE = re.compile(r"`[^`]*`")
URL_SPAN = re.compile(r"https?://\S+")
YAML_KEY = re.compile(r"^\s*[A-Za-z_][A-Za-z0-9_-]*:(\s+(.*))?$")
YAML_BLOCK = re.compile(r":\s*[|>][+-]?\s*$")


def _url_replacement(match):
    """Blank a URL span but keep the punctuation that trails it.

    A Markdown link ends at its closing parenthesis, and a semicolon
    or a colon right after a link or a bare URL is prose punctuation,
    not part of the address. A port or path colon is never the last
    character of the span, so trimming these marks from the end of
    the span only ever exposes prose. Whatever trails the span stays
    in the line, so the bar still judges it.
    """
    span = match.group(0)
    core = span.rstrip(");:")
    return span[len(core):]


def clean(text):
    """Remove the spans of a line the bar does not reach."""
    text = URL_SPAN.sub(_url_replacement, text)
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


def comment_spans(path):
    """Yield (number, text) pairs for the comment spans of a file."""
    lines = path.read_text(encoding="utf-8").splitlines()
    for number, raw in enumerate(lines, start=1):
        for index, char in enumerate(raw):
            if char == "#" and (index == 0 or raw[index - 1] in " \t"):
                body = raw[index + 1:].strip()
                # Editor directives are machine syntax, not prose.
                if body.startswith("yaml-language-server"):
                    break
                if body:
                    yield number, clean(body)
                break


def display_name(path):
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def scan(violations, path, spans):
    for number, text in spans:
        where = "%s line %d" % (display_name(path), number)
        if EM_DASH in text:
            violations.append("%s has an em dash" % where)
        if ";" in text:
            violations.append("%s has a semicolon" % where)
        if ":" in text:
            violations.append("%s has a colon in prose" % where)


def description_values(data):
    """Every description string in a parsed manifest, at any depth."""
    values = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "description" and isinstance(value, str):
                values.append(value)
            else:
                values.extend(description_values(value))
    elif isinstance(data, list):
        for item in data:
            values.extend(description_values(item))
    return values


def scan_manifest(violations, path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        violations.append(
            "%s does not parse for the copy scan: %s"
            % (display_name(path), exc)
        )
        return
    for value in description_values(data):
        text = clean(value)
        where = "%s description field" % display_name(path)
        if EM_DASH in text:
            violations.append("%s has an em dash" % where)
        if ";" in text:
            violations.append("%s has a semicolon" % where)
        if ":" in text:
            violations.append("%s has a colon in prose" % where)


def main():
    violations = []
    for path in PROSE_FILES:
        if not path.is_file():
            violations.append("%s is missing" % display_name(path))
            continue
        scan(violations, path, prose_lines(path))
    for path in COMMENT_FILES:
        if not path.is_file():
            violations.append("%s is missing" % display_name(path))
            continue
        scan(violations, path, comment_spans(path))
    for path in MANIFEST_FILES:
        if not path.is_file():
            violations.append("%s is missing" % display_name(path))
            continue
        scan_manifest(violations, path)
    if violations:
        for violation in violations:
            print("check_copy: %s" % violation, file=sys.stderr)
        return 1
    print(
        "check_copy: copy bar holds on %d prose files, the "
        "description fields of %d plugin manifests and the "
        "comment prose of %d config files"
        % (len(PROSE_FILES), len(MANIFEST_FILES), len(COMMENT_FILES))
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
