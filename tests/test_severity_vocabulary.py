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
here in the open.
"""

import importlib.util
import json
import re
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

SKILL_COPIES = [
    ".agents/skills/recognitio/SKILL.md",
    ".cursor-plugin/skills/recognitio/SKILL.md",
    "agent-plugins-package/skills/recognitio/SKILL.md",
]
EXTRACTOR_COPIES = [
    ".agents/skills/recognitio/scripts/extract.py",
    ".cursor-plugin/skills/recognitio/scripts/extract.py",
    "agent-plugins-package/skills/recognitio/scripts/extract.py",
]

# Every file in the tree that names a severity, classified.
# A surface states the vocabulary, validates it, carries a
# validated value across a seam, records a historical
# grading, names a foreign platform and its own severities,
# or tests the vocabulary. This test file itself is the pin
# and stands outside the list it keeps.
CLASSIFIED = {
    ".agents/skills/recognitio/SKILL.md": "states",
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
    "docs/images/capture.json": "capture record",
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


def tree_text_files():
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        parts = set(rel.split("/"))
        if parts & {".git", "__pycache__", ".pytest_cache"}:
            continue
        if rel == "tests/test_severity_vocabulary.py":
            continue
        try:
            yield rel, path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue


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
        found = {
            rel
            for rel, text in tree_text_files()
            if "severit" in text.lower()
        }
        self.assertEqual(found, set(CLASSIFIED))

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
