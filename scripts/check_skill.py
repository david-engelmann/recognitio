#!/usr/bin/env python3
"""Validate the recognitio skill package.

Checks that the SKILL file exists where the skill format expects it,
that its frontmatter names the skill after its directory, that the
description is present and within the length limit the skill loaders
enforce, and that the bundled extractor script exists and compiles.

Exits nonzero with one line per problem when anything fails.
"""

import py_compile
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "recognitio"
SKILL_MD = SKILL_DIR / "SKILL.md"
EXTRACT = SKILL_DIR / "scripts" / "extract.py"
DESCRIPTION_LIMIT = 1024


def parse_frontmatter(text):
    """Return the frontmatter mapping of a skill file, or None."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    fields = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return None


def main():
    problems = []

    if not SKILL_MD.is_file():
        problems.append("missing skill file at %s" % SKILL_MD.relative_to(ROOT))
        fields = None
    else:
        fields = parse_frontmatter(SKILL_MD.read_text(encoding="utf-8"))
        if fields is None:
            problems.append("SKILL.md has no readable frontmatter block")

    if fields is not None:
        name = fields.get("name", "")
        if not name:
            problems.append("frontmatter has no name field")
        else:
            if name != SKILL_DIR.name:
                problems.append(
                    "frontmatter name %r does not match the skill directory %r"
                    % (name, SKILL_DIR.name)
                )
            if name != "recognitio":
                problems.append("frontmatter name %r is not 'recognitio'" % name)
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
