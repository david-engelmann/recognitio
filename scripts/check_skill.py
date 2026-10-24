#!/usr/bin/env python3
"""Validate the recognitio skill package.

The canonical skill lives at .agents/skills/recognitio and the home
platform spelling at .claude/skills/recognitio holds a symlink to
the canonical or a byte identical copy of it, so the two spellings
are one skill, never two instruction sources. The gate checks the
layout first, then validates the skill text at each spelling that
does not resolve to the canonical file.

The content checks are that the SKILL file exists where the skill
format expects it, that its frontmatter names the skill after its
directory, that the name follows the character rules of the skill
specification, that the description is present and within the
length limit the skill loaders enforce, that the whole skill file
stays under the size limit that guards it against host truncation,
and that the bundled extractor script exists and compiles.

The name rules come from the specification. A name runs at most 64
characters, uses lowercase letters and numbers and hyphens only,
never starts or ends with a hyphen, and never holds two hyphens in
a row. A future rename or a second skill could break those rules
without any other check noticing, so the gate carries them.

Exits nonzero with one line per problem when anything fails.
"""

import os
import py_compile
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SKILL_DIR = ROOT / ".agents" / "skills" / "recognitio"
HOME_SKILL_DIR = ROOT / ".claude" / "skills" / "recognitio"
# The trio below names the canonical spelling. The gate tests
# override them against scratch fixtures, so the names stay.
SKILL_DIR = CANONICAL_SKILL_DIR
SKILL_MD = SKILL_DIR / "SKILL.md"
EXTRACT = SKILL_DIR / "scripts" / "extract.py"
DESCRIPTION_LIMIT = 1024
NAME_LIMIT = 64
# The host reattaches each skill after a compaction cut at 20000
# characters, so a skill that grows past that cut loses its tail
# instructions for the rest of a session with no other signal.
# The evidence behind the cut speaks in both units, because the
# release notes that report the cut report it in characters
# while the guard test in the same project fails at a byte
# count, and no primary host source settles which unit the
# host applies. The gate therefore guards both units at the
# same limit, so the file stays safe under either reading. The
# gate trips at 16000, a 20 percent buffer under the cut, while
# a move into a references file is still a small edit rather
# than an emergency rewrite at the cliff edge.
SKILL_TEXT_LIMIT = 16000
NAME_CHARS = re.compile(r"^[a-z0-9-]+$")


def describe(path, root=ROOT):
    """The root relative spelling of a path, or the path itself."""
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def name_problems(name):
    """The specification character problems a skill name carries."""
    problems = []
    if len(name) > NAME_LIMIT:
        problems.append(
            "frontmatter name runs %d characters, over the %d limit"
            % (len(name), NAME_LIMIT)
        )
    if not NAME_CHARS.match(name):
        problems.append(
            "frontmatter name %r uses characters outside lowercase "
            "letters, numbers and hyphens" % name
        )
    if name.startswith("-") or name.endswith("-"):
        problems.append(
            "frontmatter name %r starts or ends with a hyphen" % name
        )
    if "--" in name:
        problems.append(
            "frontmatter name %r holds consecutive hyphens" % name
        )
    return problems


def parse_frontmatter(text):
    """Return the frontmatter mapping of a skill file, or None.

    Indented continuation lines belong to the value above them, as
    YAML folding reads them, so a wrapped description is measured at
    its full length and not at the length of its first line.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    fields = {}
    current_key = None
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        if line[:1] in (" ", "\t") and current_key is not None:
            fields[current_key] = (
                fields[current_key] + " " + line.strip()
            ).strip()
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            current_key = key.strip()
            fields[current_key] = value.strip()
    return None


def _tree_bytes(directory):
    """Map every file under a directory to its bytes."""
    found = {}
    for path in sorted(directory.rglob("*")):
        if path.is_file() and not path.is_symlink():
            found[str(path.relative_to(directory))] = path.read_bytes()
    return found


def layout_problems(canonical_dir, home_dir, root=ROOT):
    """The two spellings hold one skill and point the right way.

    The canonical spelling is the real directory. The home
    platform spelling is either a symlink that resolves inside
    the tree to the canonical directory, which pins the copy
    direction structurally because a link has no drift of its
    own, or a real directory whose files are byte identical to
    the canonical files. Anything else is a second instruction
    source or a pointer at one, and the gate fails it.
    """
    problems = []
    canonical_name = describe(canonical_dir, root)
    home_name = describe(home_dir, root)
    if not canonical_dir.is_dir() or canonical_dir.is_symlink():
        problems.append(
            "canonical skill at %s is not a directory" % canonical_name
        )
        return problems
    if not home_dir.is_symlink() and not home_dir.exists():
        problems.append(
            "home platform skill at %s is missing" % home_name
        )
        return problems
    if home_dir.is_symlink():
        try:
            target = home_dir.resolve()
        except OSError as exc:
            problems.append(
                "home platform skill at %s does not resolve with %s"
                % (home_name, exc)
            )
            return problems
        try:
            target.relative_to(root.resolve())
        except ValueError:
            problems.append(
                "home platform skill at %s resolves outside the tree"
                % home_name
            )
            return problems
        try:
            same = os.path.samefile(target, canonical_dir)
        except OSError:
            same = target == canonical_dir.resolve()
        if not same:
            problems.append(
                "home platform skill at %s resolves to %s instead of "
                "the canonical skill at %s, so the copy direction "
                "is ambiguous" % (
                    home_name, describe(target, root), canonical_name,
                )
            )
        return problems
    if not home_dir.is_dir():
        problems.append(
            "home platform skill at %s is neither a directory nor "
            "a symlink" % home_name
        )
        return problems
    canonical_files = _tree_bytes(canonical_dir)
    home_files = _tree_bytes(home_dir)
    for name in sorted(set(canonical_files) | set(home_files)):
        if name not in canonical_files:
            problems.append(
                "home platform skill at %s carries an extra file %s "
                "the canonical skill at %s does not hold"
                % (home_name, name, canonical_name)
            )
        elif name not in home_files:
            problems.append(
                "home platform skill at %s is missing the file %s "
                "the canonical skill at %s holds"
                % (home_name, name, canonical_name)
            )
        elif home_files[name] != canonical_files[name]:
            problems.append(
                "home platform skill at %s carries a drifted copy of "
                "%s, and the canonical skill at %s is the only "
                "spelling that may change"
                % (home_name, name, canonical_name)
            )
    return problems


def content_problems(skill_dir, skill_md, extract, tag):
    """The skill text checks for one spelling.

    The tag prefixes every message so a failure names the
    spelling it was found at. The canonical spelling passes an
    empty tag and its messages read exactly as before.
    """
    problems = []

    if not skill_md.is_file():
        problems.append(
            "%smissing skill file at %s" % (tag, describe(skill_md))
        )
        fields = None
    else:
        skill_text = skill_md.read_text(encoding="utf-8")
        if len(skill_text) > SKILL_TEXT_LIMIT:
            problems.append(
                "%sSKILL.md runs %d characters, over the %d limit. "
                "Move detail into a references file the skill "
                "points at" % (tag, len(skill_text), SKILL_TEXT_LIMIT)
            )
        byte_count = len(skill_text.encode("utf-8"))
        if byte_count > SKILL_TEXT_LIMIT:
            problems.append(
                "%sSKILL.md runs %d bytes, over the %d limit. "
                "Move detail into a references file the skill "
                "points at" % (tag, byte_count, SKILL_TEXT_LIMIT)
            )
        fields = parse_frontmatter(skill_text)
        if fields is None:
            problems.append(
                "%sSKILL.md has no readable frontmatter block" % tag
            )

    if fields is not None:
        name = fields.get("name", "")
        if not name:
            problems.append("%sfrontmatter has no name field" % tag)
        else:
            problems.extend(
                tag + problem for problem in name_problems(name)
            )
        if name and name != skill_dir.name:
            # The directory is named recognitio by construction, so
            # this one check also keeps the skill from ever taking
            # the bundled code-review name.
            problems.append(
                "%sfrontmatter name %r does not match the skill "
                "directory %r" % (tag, name, skill_dir.name)
            )
        description = fields.get("description", "")
        if not description:
            problems.append(
                "%sfrontmatter has no description field" % tag
            )
        elif len(description) > DESCRIPTION_LIMIT:
            problems.append(
                "%sdescription runs %d characters, over the %d limit"
                % (tag, len(description), DESCRIPTION_LIMIT)
            )

    if not extract.is_file():
        problems.append(
            "%smissing extractor script at %s" % (
                tag, describe(extract),
            )
        )
    else:
        with tempfile.TemporaryDirectory() as tmp:
            try:
                py_compile.compile(
                    str(extract), cfile=str(Path(tmp) / "extract.pyc"), doraise=True
                )
            except py_compile.PyCompileError as exc:
                problems.append(
                    "%sextract.py does not compile: %s" % (tag, exc)
                )
    return problems


def _same_file(first, second):
    try:
        return os.path.samefile(first, second)
    except OSError:
        return False


def main(root=None):
    root = ROOT if root is None else root
    problems = []
    problems.extend(layout_problems(SKILL_DIR, HOME_SKILL_DIR, root))
    problems.extend(content_problems(SKILL_DIR, SKILL_MD, EXTRACT, ""))
    home_md = HOME_SKILL_DIR / "SKILL.md"
    # When the home spelling is a symlink to the canonical, its
    # SKILL.md is the same file the canonical check just read,
    # so a second content pass would only repeat its messages.
    # A real directory spelling that survived the layout check
    # is byte identical, but its messages still name the
    # spelling, because a byte identical copy can still be
    # pointed at a broken file on a fixture.
    if home_md.is_file() and not _same_file(home_md, SKILL_MD):
        problems.extend(
            content_problems(
                HOME_SKILL_DIR,
                home_md,
                HOME_SKILL_DIR / "scripts" / "extract.py",
                "%s: " % describe(HOME_SKILL_DIR, root),
            )
        )

    if problems:
        for problem in problems:
            print("check_skill: %s" % problem, file=sys.stderr)
        return 1
    print("check_skill: skill package is valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
