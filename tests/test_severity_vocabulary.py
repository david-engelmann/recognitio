"""The severity vocabulary pin.

One vocabulary stands on every shipped surface, P0 and P1
and P2 and P3, the set the shipped gates already enforce.
The skill copies and the output style and the reviewer
persona state it in one shared sentence, the findings
template carries a heading for every grade, the fan out
and headless runbooks and schemas state it, and both
validator messages name the allowed values when they
refuse one. This file is the single pin. Its classified
surface list is itself under test, so a new surface that
names a severity joins the tree only by being classified
here in the open. The skill copies and the extractor
copies are found by census rather than listed by hand, so
a copy at a new placement joins those checks by
construction instead of escaping them in silence. The
census walks through directory symlinks under a cycle
guard and matches the copy shape in any letter case, so
a seat reached only through a link and a copy whose name
drifts in case join as well. In both scans a link free
spelling of a file displaces an alias spelling of the
same file, so which spelling stands never depends on
the order the walk reaches them. The classification and the
census are tied in both directions for skill copies, so
a classified copy the census cannot hold is caught by
the tie, and the known placements stand as a floor under
the census, so a deleted copy fails instead of shrinking
the pin in silence.
"""

import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

VOCABULARY = ["P0", "P1", "P2", "P3"]
SENTENCE = (
    "Findings from a packet carry the fixed severity "
    "vocabulary, P0 and P1 and P2 and P3."
)
OLD_SENTENCE = (
    "Findings written from a packet carry one fixed "
    "severity vocabulary, P1 and P2 and P3."
)


# Pockets that stand outside the shipped tree in both
# scans, so the census and the surface scan agree about
# what stands in the tree.
EXCLUDED_PARTS = {".git", "__pycache__", ".pytest_cache"}


def walk_files(root):
    """Every file under a root, following directory links safely.

    A directory symlink is descended like a real directory,
    so a seat reached only through a link is walked beside
    a seat at a plain path. A directory whose resolved
    target already stands among its own ancestors is not
    descended again, so a link cycle ends instead of
    looping. A file reached under two spellings is yielded
    under each spelling, and the caller decides how the
    spellings count.
    """

    def descend(directory, ancestors):
        try:
            entries = sorted(directory.iterdir())
        except OSError:
            return
        for entry in entries:
            if entry.is_dir():
                resolved = entry.resolve()
                if resolved in ancestors:
                    continue
                yield from descend(entry, ancestors | {resolved})
            elif entry.is_file():
                yield entry

    yield from descend(root, {root.resolve()})


def spelling_is_link(root, path):
    """Whether any part of a spelling below the root is a link.

    The final part can be a link itself, and a seat part
    above it can be a link that carries the whole folder,
    so every part of the spelling is checked in turn.
    """
    current = root
    for part in path.relative_to(root).parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def copy_paths(root, tail):
    """Every copy of one skill file, found by census.

    A copy stands anywhere in the scanned tree at a path
    ending in the tail, matched in any letter case, so a
    placement the pin has never named joins the census by
    construction. A file at a copy shaped path counts as
    a copy even when it was meant as an excerpt, because
    the path alone cannot tell the two apart and a host
    that discovers the skill by folder shape could load
    either one. Two spellings that resolve to one file
    count once, because they are one copy, and the
    spelling that survives is a spelling that passes
    through no link when one stands, so an alias cannot
    displace the seat it points at by sorting ahead of
    it in the walk.
    """
    lowered = tuple(part.lower() for part in tail)
    best = {}
    for path in walk_files(root):
        rel = path.relative_to(root)
        if set(rel.parts) & EXCLUDED_PARTS:
            continue
        parts = tuple(part.lower() for part in rel.parts)
        if parts[-len(lowered):] != lowered:
            continue
        resolved = path.resolve()
        link = spelling_is_link(root, path)
        held = best.get(resolved)
        if held is None or (held[1] and not link):
            best[resolved] = (rel.as_posix(), link)
    return sorted(spelling for spelling, _ in best.values())


def skill_copies(root=ROOT):
    """Every SKILL.md copy of the skill in the tree."""
    return copy_paths(root, ("skills", "recognitio", "SKILL.md"))


def extractor_copies(root=ROOT):
    """Every extractor copy of the skill in the tree."""
    return copy_paths(
        root, ("skills", "recognitio", "scripts", "extract.py")
    )


SKILL_COPIES = skill_copies()
EXTRACTOR_COPIES = extractor_copies()

# The placements the tree is known to ship, held as a
# floor under the census. The census finds the copies the
# checks read, and this floor fails when a known copy is
# deleted, so the pin cannot shrink in silence.
KNOWN_SKILL_COPIES = [
    ".agents/skills/recognitio/SKILL.md",
    ".comate/skills/recognitio/SKILL.md",
    ".cursor-plugin/skills/recognitio/SKILL.md",
    "agent-plugins-package/skills/recognitio/SKILL.md",
]
KNOWN_EXTRACTOR_COPIES = [
    ".agents/skills/recognitio/scripts/extract.py",
    ".comate/skills/recognitio/scripts/extract.py",
    ".cursor-plugin/skills/recognitio/scripts/extract.py",
    "agent-plugins-package/skills/recognitio/scripts/extract.py",
]


def unreconciled_skill_copies(classified, copies):
    """Skill copies the classification and the census disagree on.

    A classified entry shaped like a skill copy, in any
    letter case, that the census does not hold is pinned
    by nothing, and a censused copy with no states entry
    in the classification stands outside the tie from the
    other side. Both directions stand in the returned
    list, so the two nets can never drift apart quietly.
    """
    shaped = {
        rel
        for rel, kind in classified.items()
        if kind == "states"
        and tuple(part.lower() for part in rel.split("/"))[-3:]
        == ("skills", "recognitio", "skill.md")
    }
    return sorted(shaped.symmetric_difference(copies))


# Every file in the tree that names a severity, classified.
# A surface states the vocabulary, validates it, carries a
# validated value across a seam, records a historical
# grading, names a foreign platform and its own severities,
# or tests the vocabulary. This test file itself is the pin
# and stands outside the list it keeps.
CLASSIFIED = {
    ".agents/skills/recognitio/SKILL.md": "states",
    ".comate/skills/recognitio/SKILL.md": "states",
    ".cursor-plugin/skills/recognitio/SKILL.md": "states",
    "agent-plugins-package/skills/recognitio/SKILL.md": "states",
    "output-styles/packet.md": "states",
    "agents/reviewer.md": "states",
    "REVIEW.md": "states",
    "docs/headless-review.md": "states",
    "workflows/review-fanout.md": "states",
    "workflows/findings.schema.json": "states",
    "workflows/headless-findings.schema.json": "states",
    "scripts/check_fanout.py": "validates",
    "scripts/check_headless.py": "validates",
    "scripts/merge_to_headless.py": "carries validated values only",
    "AGENTS.md": "chronicle record",
    "CHANGELOG.md": "chronicle record",
    "docs/reviews/round11-fix-review.md": "report record",
    "docs/reviews/round12-fix-review.md": "report record",
    "docs/reviews/round13-fix-review.md": "report record",
    "docs/reviews/round14-fix-review.md": "report record",
    "docs/reviews/round4-fix-review.md": "report record",
    "docs/reviews/round6-fix-review.md": "report record",
    "docs/reviews/round7-fix-review.md": "report record",
    "docs/reviews/round8-fix-review.md": "report record",
    "docs/reviews/round9-fix-review.md": "report record",
    "evals/TRIGGER-RESULTS.md": "eval record",
    "evals/trigger-set.md": "eval prompt under checksum",
    "workflows/proof-run/run-record.json": "proof record",
    "docs/coderabbit-review-brief.md": "foreign platform",
    "docs/codex-review-brief.md": "foreign platform",
    "docs/cursor-plugin-brief.md": "foreign platform",
    "docs/devin-playbook-brief.md": "foreign platform",
    "docs/submission-claude.md": "foreign platform",
    "tests/test_fanout.py": "tests",
    "tests/test_headless.py": "tests",
    "tests/test_review_chain.py": "tests",
}

# Lines that enumerate P tokens without stating a severity
# vocabulary. The two chronicle lines are historical entries
# that describe a past landing in the vocabulary of its day
# and stand unedited as record. The two brand lines number
# brand gate pins, a different token family that shares the
# shape. Any other partial enumeration in the tree fails.
RECORD_LINES = {
    "and carries the fixed P1 and P2 and P3 severity",
    "and gains the fixed P1 and P2 and P3 severity",
    "gate pins P1 and P2 and P3 and P9 and P10 and P11 and P16.",
    '"""Problems under pins P1 and P2 and P3 and P16."""',
}

# Severity literals the test suites may plant. Every value
# stands inside the vocabulary, apart from the two named
# plants the suites use to prove a gate refuses a value
# outside it. A new literal joins only by being named here.
TEST_SEVERITY_LITERALS = set(VOCABULARY) | {"P9", "P999-banana"}

ENUMERATION_RE = re.compile(r"P[0-3](?:\s+and\s+P[0-3])+")
P_TOKEN_RE = re.compile(r"P[0-3]\b")


def partial_enumeration_offenders():
    """Lines enumerating a partial vocabulary outside the records."""
    offenders = []
    for rel, text in tree_text_files():
        for line in text.splitlines():
            match = ENUMERATION_RE.search(line)
            if not match:
                continue
            named = set(P_TOKEN_RE.findall(match.group(0)))
            if named == set(VOCABULARY):
                continue
            if line.strip() in RECORD_LINES:
                continue
            offenders.append("%s: %s" % (rel, line.strip()))
    return offenders


def p_token_enum_offenders():
    """JSON enums holding a P token that are not the vocabulary."""
    offenders = []
    for rel, text in tree_text_files():
        if not rel.endswith(".json"):
            continue
        for match in re.finditer(r'"enum":\s*\[([^\]]*)\]', text):
            values = re.findall(r'"([^"]+)"', match.group(1))
            if any(P_TOKEN_RE.fullmatch(v) for v in values):
                if values != VOCABULARY:
                    offenders.append("%s: %s" % (rel, values))
    return offenders


def load_script(name):
    path = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(
        "severity_" + name, path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def decode_utf16_surface(data):
    """The text of a byte string that carries a UTF-16 mark.

    A severity surface written in UTF-16 with its byte
    order mark decodes here instead of skipping in
    silence. A byte string with no mark is left alone,
    because without the mark it cannot be told apart
    from the binary files the scan skips by design.
    """
    if not data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return None
    try:
        return data.decode("utf-16")
    except UnicodeDecodeError:
        return None


def tree_text_files(root=ROOT):
    """Every text file in the tree under one spelling per file.

    Two spellings that resolve to one file yield once,
    under a spelling that passes through no link when
    one stands, so an alias cannot displace the seat it
    points at by sorting ahead of it in the walk. The
    spellings are gathered before any is yielded because
    a link free spelling can stand later in the walk
    than the alias it must displace.
    """
    best = {}
    for path in walk_files(root):
        rel = path.relative_to(root).as_posix()
        parts = set(rel.split("/"))
        if parts & EXCLUDED_PARTS:
            continue
        if rel == "tests/test_severity_vocabulary.py":
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = decode_utf16_surface(data)
            if text is None:
                continue
        resolved = path.resolve()
        link = spelling_is_link(root, path)
        held = best.get(resolved)
        if held is None or (held[2] and not link):
            best[resolved] = (rel, text, link)
    for rel, text, _ in sorted(
        best.values(), key=lambda held: held[0]
    ):
        yield rel, text


def severity_surfaces(root=ROOT):
    """Every file under a root that names a severity."""
    return {
        rel
        for rel, text in tree_text_files(root)
        if "severit" in text.lower()
    }


class TestSeverityVocabulary(unittest.TestCase):
    """One severity vocabulary, everywhere, pinned."""

    def test_the_skill_copies_carry_the_unified_sentence(self):
        texts = []
        for rel in SKILL_COPIES:
            text = read(rel)
            texts.append(text)
            self.assertIn(SENTENCE, text, rel)
            self.assertNotIn(OLD_SENTENCE, text, rel)
            self.assertLessEqual(
                len(text.encode("utf-8")), 16000, rel
            )
        self.assertEqual(len(set(texts)), 1, "skill copies drifted")

    def test_the_output_style_carries_the_unified_sentence(self):
        text = read("output-styles/packet.md")
        self.assertIn(SENTENCE, text)
        self.assertNotIn(OLD_SENTENCE, text)

    def test_the_persona_carries_the_severity_sentence(self):
        text = read("agents/reviewer.md")
        self.assertIn(SENTENCE, text)

    def test_the_template_carries_a_heading_for_every_grade(self):
        text = read("REVIEW.md")
        template = text.split("```", 2)[1]
        headings = re.findall(r"^### (P[0-3])$", template, re.M)
        self.assertEqual(headings, VOCABULARY)
        self.assertIn(
            "The P0 heading entered this template on 2026-10-27",
            text,
        )

    def test_the_fanout_surfaces_state_the_vocabulary(self):
        schema = json.loads(read("workflows/findings.schema.json"))
        severity = schema["properties"]["findings"]["items"][
            "properties"
        ]["severity"]
        self.assertEqual(severity["enum"], VOCABULARY)
        runbook = read("workflows/review-fanout.md")
        self.assertIn("P0 and P1 and P2 and P3", runbook)
        fanout = load_script("check_fanout")
        problems = fanout.schema_problems(
            severity, "P9", "finding.severity"
        )
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("outside the allowed values", problems[0])
        for value in VOCABULARY:
            self.assertIn(value, problems[0])

    def test_the_headless_surfaces_state_the_vocabulary(self):
        shipped = json.loads(
            read("workflows/headless-findings.schema.json")
        )
        severity = shipped["properties"]["findings"]["items"][
            "properties"
        ]["severity"]
        self.assertEqual(severity["enum"], VOCABULARY)
        doc = read("docs/headless-review.md")
        printed = json.loads(
            re.search(r"```json\n(.*?)```", doc, re.DOTALL).group(1)
        )
        printed_severity = printed["properties"]["findings"][
            "items"
        ]["properties"]["severity"]
        self.assertEqual(printed_severity["enum"], VOCABULARY)
        prose = doc.split("```json", 1)[0]
        self.assertIn("P0 and P1 and P2 and P3", prose)
        headless = load_script("check_headless")
        self.assertEqual(list(headless.SEVERITIES), VOCABULARY)
        problems = headless.findings_problems(
            {
                "verdict": "fail",
                "findings": [
                    {
                        "severity": "banana",
                        "location": "src/app.py:1",
                        "evidence": ["src/app.py"],
                    }
                ],
            },
            ["src/app.py"],
        )
        named = [
            p for p in problems if "outside the shipped" in p
        ]
        self.assertEqual(len(named), 1, problems)
        for value in VOCABULARY:
            self.assertIn(value, named[0])

    def test_the_proof_run_keeps_its_p0_grade_and_reads_green(self):
        record = json.loads(
            read("workflows/proof-run/run-record.json")
        )
        severities = []

        def collect(node):
            if isinstance(node, dict):
                if isinstance(node.get("severity"), str):
                    severities.append(node["severity"])
                for value in node.values():
                    collect(value)
            elif isinstance(node, list):
                for value in node:
                    collect(value)

        collect(record)
        self.assertIn("P0", severities)
        for value in severities:
            self.assertIn(value, VOCABULARY)
        fanout = load_script("check_fanout")
        problems = fanout.run_problems(
            ROOT / "workflows" / "proof-run" / "run-record.json"
        )
        self.assertEqual(problems, [])

    def test_the_extractor_copies_name_no_severity_vocabulary(self):
        texts = []
        for rel in EXTRACTOR_COPIES:
            text = read(rel)
            texts.append(text)
            self.assertNotIn("severit", text.lower(), rel)
        self.assertEqual(len(set(texts)), 1, "extractor copies drifted")

    def test_every_severity_surface_in_the_tree_is_classified(self):
        self.assertEqual(severity_surfaces(), set(CLASSIFIED))

    def test_a_copy_at_a_novel_path_is_caught_by_the_census(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seat = root / ".novel" / "skills" / "recognitio"
            (seat / "scripts").mkdir(parents=True)
            (seat / "SKILL.md").write_text(
                read(".agents/skills/recognitio/SKILL.md"),
                encoding="utf-8",
            )
            (seat / "scripts" / "extract.py").write_text(
                read(
                    ".agents/skills/recognitio/scripts/extract.py"
                ),
                encoding="utf-8",
            )
            skill_rel = ".novel/skills/recognitio/SKILL.md"
            extractor_rel = (
                ".novel/skills/recognitio/scripts/extract.py"
            )
            self.assertIn(skill_rel, skill_copies(root))
            self.assertIn(extractor_rel, extractor_copies(root))
            self.assertEqual(severity_surfaces(root), {skill_rel})
            self.assertNotIn(skill_rel, CLASSIFIED)

    def test_a_seat_behind_a_directory_symlink_is_censused(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "tree"
            outside = base / "outside"
            (outside / "scripts").mkdir(parents=True)
            (outside / "SKILL.md").write_text(
                read(".agents/skills/recognitio/SKILL.md")
                + "\nA rogue extra line.\n",
                encoding="utf-8",
            )
            (outside / "scripts" / "extract.py").write_text(
                read(
                    ".agents/skills/recognitio/scripts/extract.py"
                )
                + "\n# a rogue extra line\n",
                encoding="utf-8",
            )
            seat = root / ".newseat" / "skills"
            seat.mkdir(parents=True)
            (seat / "recognitio").symlink_to(
                outside, target_is_directory=True
            )
            (outside / "loop").symlink_to(
                root, target_is_directory=True
            )
            skill_rel = ".newseat/skills/recognitio/SKILL.md"
            extractor_rel = (
                ".newseat/skills/recognitio/scripts/extract.py"
            )
            self.assertIn(skill_rel, skill_copies(root))
            self.assertIn(extractor_rel, extractor_copies(root))
            self.assertIn(skill_rel, severity_surfaces(root))

    def test_a_file_symlink_alias_counts_once_in_both_nets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seat = root / ".agents" / "skills" / "recognitio"
            seat.mkdir(parents=True)
            skill_rel = ".agents/skills/recognitio/SKILL.md"
            (seat / "SKILL.md").write_text(
                read(".agents/skills/recognitio/SKILL.md"),
                encoding="utf-8",
            )
            alias = root / ".alias" / "skills" / "recognitio"
            alias.mkdir(parents=True)
            (alias / "SKILL.md").symlink_to(seat / "SKILL.md")
            self.assertEqual(skill_copies(root), [skill_rel])
            self.assertEqual(severity_surfaces(root), {skill_rel})

    def test_an_alias_sorting_before_the_seat_displaces_nothing(self):
        for form in ("file", "directory"):
            with self.subTest(form=form):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    seat = (
                        root / ".agents" / "skills" / "recognitio"
                    )
                    seat.mkdir(parents=True)
                    skill_rel = (
                        ".agents/skills/recognitio/SKILL.md"
                    )
                    (seat / "SKILL.md").write_text(
                        read(
                            ".agents/skills/recognitio/SKILL.md"
                        ),
                        encoding="utf-8",
                    )
                    alias_parent = root / ".aaa" / "skills"
                    if form == "file":
                        alias = alias_parent / "recognitio"
                        alias.mkdir(parents=True)
                        (alias / "SKILL.md").symlink_to(
                            seat / "SKILL.md"
                        )
                    else:
                        alias_parent.mkdir(parents=True)
                        (alias_parent / "recognitio").symlink_to(
                            seat, target_is_directory=True
                        )
                    self.assertEqual(
                        skill_copies(root), [skill_rel]
                    )
                    self.assertEqual(
                        severity_surfaces(root), {skill_rel}
                    )
                    self.assertEqual(
                        [
                            rel
                            for rel, _ in tree_text_files(root)
                        ],
                        [skill_rel],
                    )
                    self.assertEqual(
                        unreconciled_skill_copies(
                            {skill_rel: "states"},
                            skill_copies(root),
                        ),
                        [],
                    )

    def test_the_census_skips_the_pockets_the_scan_skips(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for pocket in (".git", "__pycache__"):
                seat = (
                    root / pocket / "skills" / "recognitio"
                )
                (seat / "scripts").mkdir(parents=True)
                (seat / "SKILL.md").write_text(
                    read(".agents/skills/recognitio/SKILL.md"),
                    encoding="utf-8",
                )
                (seat / "scripts" / "extract.py").write_text(
                    read(
                        ".agents/skills/recognitio/"
                        "scripts/extract.py"
                    ),
                    encoding="utf-8",
                )
            self.assertEqual(skill_copies(root), [])
            self.assertEqual(extractor_copies(root), [])
            self.assertEqual(severity_surfaces(root), set())

    def test_classified_skill_copies_and_the_census_agree(self):
        self.assertEqual(
            unreconciled_skill_copies(CLASSIFIED, SKILL_COPIES),
            [],
        )

    def test_a_case_variant_skill_copy_stands_inside_the_tie(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seat = root / ".case" / "skills" / "recognitio"
            seat.mkdir(parents=True)
            variant_rel = ".case/skills/recognitio/skill.md"
            (seat / "skill.md").write_text(
                read(".agents/skills/recognitio/SKILL.md"),
                encoding="utf-8",
            )
            self.assertIn(variant_rel, skill_copies(root))
            classified = {variant_rel: "states"}
            self.assertEqual(
                unreconciled_skill_copies(
                    classified, skill_copies(root)
                ),
                [],
            )
            classified[".caps/Skills/Recognitio/SKILL.md"] = (
                "states"
            )
            self.assertEqual(
                unreconciled_skill_copies(
                    classified, skill_copies(root)
                ),
                [".caps/Skills/Recognitio/SKILL.md"],
            )
            self.assertEqual(
                unreconciled_skill_copies(
                    {}, skill_copies(root)
                ),
                [variant_rel],
            )

    def test_the_census_keeps_every_known_placement(self):
        for rel in KNOWN_SKILL_COPIES:
            self.assertIn(rel, SKILL_COPIES)
        for rel in KNOWN_EXTRACTOR_COPIES:
            self.assertIn(rel, EXTRACTOR_COPIES)

    def test_deleting_an_extractor_copy_breaks_the_floor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seat = root / ".agents" / "skills" / "recognitio"
            (seat / "scripts").mkdir(parents=True)
            extractor_rel = (
                ".agents/skills/recognitio/scripts/extract.py"
            )
            planted = seat / "scripts" / "extract.py"
            planted.write_text(
                read(
                    ".agents/skills/recognitio/scripts/extract.py"
                ),
                encoding="utf-8",
            )
            floor = {extractor_rel}
            self.assertLessEqual(
                floor, set(extractor_copies(root))
            )
            planted.unlink()
            self.assertFalse(
                floor <= set(extractor_copies(root))
            )

    def test_a_utf16_severity_surface_is_seen_by_the_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir(parents=True)
            (root / "docs" / "utf16-surface.md").write_text(
                "This page names the severity grades in full.\n",
                encoding="utf-16",
            )
            self.assertEqual(
                severity_surfaces(root),
                {"docs/utf16-surface.md"},
            )

    def test_no_partial_vocabulary_enumeration_stands_unrecorded(self):
        self.assertEqual(partial_enumeration_offenders(), [])

    def test_every_p_token_enum_is_the_vocabulary(self):
        self.assertEqual(p_token_enum_offenders(), [])

    def test_test_suite_severity_literals_stay_classified(self):
        literals = set()
        patterns = (
            r'"severity":\s*"([^"]+)"',
            r'\["severity"\]\s*=\s*"([^"]+)"',
        )
        for path in sorted((ROOT / "tests").glob("test_*.py")):
            if path.name == "test_severity_vocabulary.py":
                continue
            text = path.read_text(encoding="utf-8")
            for pattern in patterns:
                literals.update(re.findall(pattern, text))
        self.assertEqual(literals, TEST_SEVERITY_LITERALS)


if __name__ == "__main__":
    unittest.main()
