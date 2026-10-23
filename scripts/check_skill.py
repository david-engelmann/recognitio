#!/usr/bin/env python3
"""Validate the recognitio skill package.

Checks that the SKILL file exists where the skill format expects it,
that its frontmatter names the skill after its directory, that the
name follows the character rules of the skill specification, that
the description is present and within the length limit the skill
loaders enforce, that the whole skill file stays under the size
limit that guards it against host truncation, and that the
bundled extractor script exists and compiles.

The name rules come from the specification. A name runs at most 64
characters, uses lowercase letters and numbers and hyphens only,
never starts or ends with a hyphen, and never holds two hyphens in
a row. A future rename or a second skill could break those rules
without any other check noticing, so the gate carries them.

Exits nonzero with one line per problem when anything fails.
"""

import py_compile
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "recognitio"
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


def main():
    problems = []

    if not SKILL_MD.is_file():
        problems.append("missing skill file at %s" % SKILL_MD.relative_to(ROOT))
        fields = None
    else:
        skill_text = SKILL_MD.read_text(encoding="utf-8")
        if len(skill_text) > SKILL_TEXT_LIMIT:
            problems.append(
                "SKILL.md runs %d characters, over the %d limit. "
                "Move detail into a references file the skill "
                "points at" % (len(skill_text), SKILL_TEXT_LIMIT)
            )
        byte_count = len(skill_text.encode("utf-8"))
        if byte_count > SKILL_TEXT_LIMIT:
            problems.append(
                "SKILL.md runs %d bytes, over the %d limit. "
                "Move detail into a references file the skill "
                "points at" % (byte_count, SKILL_TEXT_LIMIT)
            )
        fields = parse_frontmatter(skill_text)
        if fields is None:
            problems.append("SKILL.md has no readable frontmatter block")

    if fields is not None:
        name = fields.get("name", "")
        if not name:
            problems.append("frontmatter has no name field")
        else:
            problems.extend(name_problems(name))
        if name and name != SKILL_DIR.name:
            # The directory is named recognitio by construction, so
            # this one check also keeps the skill from ever taking
            # the bundled code-review name.
            problems.append(
                "frontmatter name %r does not match the skill directory %r"
                % (name, SKILL_DIR.name)
            )
        description = fields.get("description", "")
        if not description:
            problems.append("frontmatter has no description field")
        elif len(description) > DESCRIPTION_LIMIT:
            problems.append(
                "description runs %d characters, over the %d limit"
                % (len(description), DESCRIPTION_LIMIT)
            )

    if not EXTRACT.is_file():
        problems.append("missing extractor script at %s" % EXTRACT.relative_to(ROOT))
    else:
        with tempfile.TemporaryDirectory() as tmp:
            try:
                py_compile.compile(
                    str(EXTRACT), cfile=str(Path(tmp) / "extract.pyc"), doraise=True
                )
            except py_compile.PyCompileError as exc:
                problems.append("extract.py does not compile: %s" % exc)

    if problems:
        for problem in problems:
            print("check_skill: %s" % problem, file=sys.stderr)
        return 1
    print("check_skill: skill package is valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
