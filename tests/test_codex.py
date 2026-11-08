"""Build 9, the Codex review rules package.

The brief at docs/codex-review-brief.md is scoped Codex guidance
beside the canonical packet, and the second packet guard says
every rule it states must carry a derivation note naming the
canonical skill section or gate it restates or the primary
OpenAI citation it reports. These tests prove the pin fires for
a real reason on every stated negative and limit the round 21
lanes named. A rule without a derivation note, a rule with an
uncheckable derivation, a dropped no calendar negative, a
conflated pause, an unqualified model pin, a dropped coverage
limit, a dropped default branch limit, a dropped Legacy watch
discipline, unflagged vendor figures, a dropped SECURITY.md
policy note, and a decision record without a decision 4
statement each fail the Codex gate.
"""

import importlib.util
import re
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    path = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location("codex_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestCheckCodex(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_codex")

    def make_layout(self, tmp):
        """A scratch tree with the brief and the decision record."""
        root = Path(tmp) / "root"
        docs = root / "docs"
        docs.mkdir(parents=True)
        shutil.copyfile(
            ROOT / "docs" / "codex-review-brief.md",
            docs / "codex-review-brief.md",
        )
        shutil.copyfile(
            ROOT / "docs" / "decisions.md", docs / "decisions.md"
        )
        return root

    def brief_text(self, root):
        return (root / "docs" / "codex-review-brief.md").read_text(
            encoding="utf-8"
        )

    def write_brief(self, root, text):
        (root / "docs" / "codex-review-brief.md").write_text(
            text, encoding="utf-8"
        )

    def problems(self, root):
        return self.mod.codex_problems(root)

    def test_the_shipped_brief_holds(self):
        self.assertEqual(self.mod.codex_problems(ROOT), [])

    def test_the_scratch_layout_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            self.assertEqual(self.problems(root), [])

    def test_a_rule_without_a_derivation_note_fails(self):
        # The second packet guard. A rule that names no canonical
        # section or primary citation is a rival instruction source.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.brief_text(root)
            broken = text.replace(
                "Derives from canonical skill, The tier model, the T0\n"
                "instruction file flag.",
                "No derivation is offered for this rule.",
                1,
            )
            self.assertNotEqual(broken, text)
            self.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("no derivation note" in p for p in problems),
                problems,
            )

    def test_a_rule_with_an_uncheckable_derivation_fails(self):
        # A derivation note that names nothing the gate can check
        # is the same failure wearing a label.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.brief_text(root)
            broken = text.replace(
                "Derives from canonical skill, The tier model, the T0\n"
                "instruction file flag.",
                "Derives from: general engineering experience.",
                1,
            )
            self.assertNotEqual(broken, text)
            self.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("no canonical skill section" in p for p in problems),
                problems,
            )

    def test_a_dropped_0_164_0_pin_fails(self):
        # R31-EX-10. The Codex brief carries the CLI 0.164.0
        # promotion as the later primary pin, with presets
        # as TUI slots only and no skill format claim.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.brief_text(root)
            broken = text.replace(
                "CLI 0.164.0 is the later primary pin",
                "CLI 0.161.0 is the later primary pin",
                1,
            )
            self.assertNotEqual(broken, text)
            self.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("0.164.0 promotion" in p for p in problems),
                problems,
            )

    def test_a_dropped_no_calendar_negative_fails(self):
        # The negative pin. Without the sentence, a later edit
        # could claim a product native calendar schedule.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.brief_text(root)
            broken = text.replace(
                "There is no product native calendar schedule on any "
                "primary\nsurface.",
                "Scans run on a schedule the product provides.",
                1,
            )
            self.assertNotEqual(broken, text)
            self.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("no calendar negative" in p for p in problems),
                problems,
            )

    def test_a_conflated_pause_fails(self):
        # R21-RT-03. The two pauses are different mechanisms with
        # different owners, and the brief must name both separately.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.brief_text(root)
            broken = text.replace(
                "scanning pauses when funding is unavailable.",
                "scanning pauses on the same toggle.",
                1,
            )
            self.assertNotEqual(broken, text)
            self.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("automatic funding pause" in p for p in problems),
                problems,
            )

    def test_an_unqualified_model_pin_fails(self):
        # R21-RT-01. A model name without its surface will be caught
        # by its own citations, so the pin requires the qualifier.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.brief_text(root)
            broken = text.replace(
                "The Actions example defaults to\ngpt-6-sol at "
                "action-v0.3.0,",
                "The model defaults to gpt-6-sol at action-v0.3.0,",
                1,
            )
            self.assertNotEqual(broken, text)
            self.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("Actions surface model pin" in p for p in problems),
                problems,
            )

    def test_a_dropped_coverage_limit_fails(self):
        # R21-RT-02. Exit 0 does not mean every file was reviewed,
        # and the brief must carry that limit.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.brief_text(root)
            broken = text.replace(
                "A completed scan and complete coverage are separate "
                "claims.",
                "A completed scan means the tree was fully reviewed.",
                1,
            )
            self.assertNotEqual(broken, text)
            self.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("complete coverage limit" in p for p in problems),
                problems,
            )

    def test_a_dropped_default_branch_limit_fails(self):
        # R21-RT-02. Continuous monitoring covers the default branch
        # only, so a wider claim fails the pin.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.brief_text(root)
            broken = text.replace(
                "Continuous scanning monitors new commits on the "
                "repository's\ndefault branch.",
                "Continuous scanning monitors new commits on every "
                "branch.",
                1,
            )
            self.assertNotEqual(broken, text)
            self.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("default branch only" in p for p in problems),
                problems,
            )

    def test_a_dropped_legacy_watch_discipline_fails(self):
        # The watch item. Legacy is under active restriction and
        # the brief must promise no retirement date.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.brief_text(root)
            broken = text.replace(
                "no\nretirement date is promised.",
                "retirement is expected soon.",
                1,
            )
            self.assertNotEqual(broken, text)
            self.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("no promised retirement date" in p for p in problems),
                problems,
            )

    def test_unflagged_vendor_figures_fail(self):
        # The honesty constraint. The 98 percent against 58.3
        # percent figures stay flagged as OpenAI's on OpenAI's
        # tasks.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.brief_text(root)
            broken = text.replace(
                "The figures are OpenAI's\non OpenAI's tasks.",
                "The figures prove the approach.",
                1,
            )
            self.assertNotEqual(broken, text)
            self.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("OpenAI owned figures" in p for p in problems),
                problems,
            )

    def test_a_dropped_security_md_note_fails(self):
        # The live trap. SECURITY.md is policy context, not
        # executable instructions, and the pin holds the sentence.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.brief_text(root)
            broken = text.replace(
                "SECURITY.md is policy context, not executable "
                "instructions.",
                "SECURITY.md carries the review instructions.",
                1,
            )
            self.assertNotEqual(broken, text)
            self.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("policy context note" in p for p in problems),
                problems,
            )

    def test_a_dropped_fails_closed_lifecycle_fails(self):
        # R27-SP-01. Automatic review fails closed on prompt
        # build, review session, and parse failures, per the
        # primary agent approvals page. A later edit that drops
        # the lifecycle sentence must fail the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.brief_text(root)
            broken = text.replace(
                "fails closed on\nprompt build, review session, and "
                "parse failures",
                "fails open on prompt build, review session, and "
                "parse failures",
                1,
            )
            self.assertNotEqual(broken, text)
            self.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("fails closed lifecycle" in p for p in problems),
                problems,
            )

    def test_a_decision_record_without_decision_4_fails(self):
        # Every landed build records a decision 4 statement. A
        # Build 9 record without one fails the pin.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / "docs" / "decisions.md"
            text = path.read_text(encoding="utf-8")
            start = text.find("## 18. Build 9")
            self.assertNotEqual(start, -1)
            record = text[start:]
            broken = record.replace(
                "Decision 4 binds the build.",
                "Decision 4 is noted elsewhere.",
                1,
            )
            self.assertNotEqual(broken, record)
            path.write_text(text[:start] + broken, encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("decision 4" in p for p in problems), problems
            )

    def test_a_passing_prose_title_mention_fails(self):
        # R21-ST-01. A note that names a canonical section title
        # in passing prose without deriving from it must fail.
        # The old substring check would pass on the bare title.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.brief_text(root)
            broken = text.replace(
                "Derives from canonical skill, The tier model, the T0\n"
                "instruction file flag.",
                "Derives from the primary blog post. It shapes the\n"
                "Workflow of the review and nothing else.",
                1,
            )
            self.assertNotEqual(broken, text)
            self.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "no canonical skill section" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_deliberate_title_naming_still_passes(self):
        # The hardening must not reject a note that names its
        # source deliberately through the attribution marker.
        note = (
            "canonical skill, The tier model, the T0 instruction "
            "file flag"
        )
        self.assertTrue(self.mod.deliberate_source(note))

    def test_a_title_after_a_sentence_break_is_passing_prose(self):
        # A title appearing after a sentence break is passing
        # prose, not a derivation, and must not satisfy the
        # check on its own.
        bare = "The rule keeps the Workflow readable for reviewers"
        self.assertFalse(self.mod.deliberate_source(bare))


class TestRound5Codex(unittest.TestCase):
    def setUp(self):
        self.inner = TestCheckCodex()
        self.inner.setUp()
        self.mod = self.inner.mod

    def problems(self, root):
        return self.mod.codex_problems(root)

    def test_t0_kimi_member_removed_from_r4_fails_by_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.brief_text(root)
            pattern = re.escape(
                "A Kimi plugin manifest named kimi.plugin.json "
                "at any depth and a Kimi plugin agent, hook "
                "script or manifest under a .kimi-plugin folder "
                "are flagged too. "
            ).replace("\\ ", "\\s+")
            broken, hits = re.subn(
                pattern, lambda _match: "", text, count=1)
            self.assertTrue(hits > 0)
            self.assertNotEqual(broken, text)
            self.inner.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(any(
                "canonical T0 member" in p
                and "kimi.plugin.json" in p for p in problems), problems)

    def test_packet_gating_exercised_glance_claim_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.brief_text(root)
            self.inner.write_brief(
                root, text + "\n\nThe packet gating rule was "
                "exercised in the paired run.\n")
            problems = self.problems(root)
            self.assertTrue(any(
                "packet gating rule was exercised" in p
                for p in problems), problems)

    def test_packet_gating_claim_reworded_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.brief_text(root)
            self.inner.write_brief(
                root, text + "\n\nThe paired run exercised the "
                "packet gating rule.\n")
            problems = self.problems(root)
            self.assertTrue(any(
                "packet gating rule was exercised" in p
                for p in problems), problems)

    def test_evidence_figures_exchanged_additive_in_worked_example_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.brief_text(root)
            plant = (
                "The baseline control recovered 98 percent."
            )
            pattern = re.escape(
                "58.3 percent for the baseline control."
            ).replace("\\ ", "\\s+")
            broken, hits = re.subn(
                pattern,
                lambda match: match.group(0) + " " + plant,
                text, count=1)
            self.assertTrue(hits > 0)
            self.assertNotEqual(broken, text)
            self.inner.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(any(
                "binds the recovery figures to the wrong subjects"
                in p for p in problems), problems)

    def test_evidence_figures_exchanged_additive_inside_r6_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.brief_text(root)
            plant = (
                "The rule guided variants recovered "
                "58.3 percent."
            )
            pattern = re.escape(
                "that SECURITY.md is policy context, not "
                "executable instructions."
            ).replace("\\ ", "\\s+")
            broken, hits = re.subn(
                pattern,
                lambda match: match.group(0) + " " + plant,
                text, count=1)
            self.assertTrue(hits > 0)
            self.assertNotEqual(broken, text)
            self.inner.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(any(
                "binds the recovery figures to the wrong subjects"
                in p for p in problems), problems)

    def test_evidence_figures_exchanged_additive_literal_baseline_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.brief_text(root)
            self.inner.write_brief(
                root, text + "\n\nThe record gives 98 "
                "percent for the baseline.\n")
            problems = self.problems(root)
            self.assertTrue(any(
                "binds the recovery figures to the wrong subjects"
                in p for p in problems), problems)

    def test_evidence_figures_exchanged_additive_literal_rule_guided_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.brief_text(root)
            self.inner.write_brief(
                root, text + "\n\nThe record gives 58.3 "
                "percent for the rule guided.\n")
            problems = self.problems(root)
            self.assertTrue(any(
                "binds the recovery figures to the wrong subjects"
                in p for p in problems), problems)

    def test_packet_gating_guard_in_once_clause_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.brief_text(root)
            self.inner.write_brief(
                root, text + "\n\nThe brief never claims a "
                "run once the packet gating rule was "
                "exercised in the paired run.\n")
            problems = self.problems(root)
            self.assertTrue(any(
                "packet gating rule was exercised" in p
                for p in problems), problems)

    def test_packet_gating_guard_in_while_clause_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.brief_text(root)
            self.inner.write_brief(
                root, text + "\n\nThe brief never claims a "
                "run while the packet gating rule was "
                "exercised in the paired run.\n")
            problems = self.problems(root)
            self.assertTrue(any(
                "packet gating rule was exercised" in p
                for p in problems), problems)

    def test_an_undecodable_brief_is_named_not_raised(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            path = root / "docs" / "codex-review-brief.md"
            path.write_bytes(
                (ROOT / "docs" / "brand" / "recognitio-icon-512.png"
                 ).read_bytes())
            problems = self.problems(root)
            self.assertTrue(any(
                "cannot read docs/codex-review-brief.md" in p
                for p in problems), problems)

    def test_an_undecodable_decision_record_is_named_not_raised(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            path = root / "docs" / "decisions.md"
            path.write_bytes(
                (ROOT / "docs" / "brand" / "recognitio-icon-512.png"
                 ).read_bytes())
            problems = self.mod.decision_problems(root)
            self.assertTrue(any(
                "cannot read docs/decisions.md" in p
                for p in problems), problems)


class TestRound5SecondSeatCodex(unittest.TestCase):
    def setUp(self):
        self.inner = TestCheckCodex()
        self.inner.setUp()
        self.mod = self.inner.mod

    def problems(self, root):
        return self.mod.codex_problems(root)

    def test_calendar_schedule_claim_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.brief_text(root)
            self.inner.write_brief(
                root, text + "\n\nScans can be scheduled on a "
                "product native calendar inside the Codex "
                "Security console.\n")
            problems = self.problems(root)
            self.assertTrue(any(
                "calendar schedule" in p for p in problems),
                problems)

    def test_security_md_executable_claim_inside_r6_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.brief_text(root)
            anchor = "that SECURITY.md is policy context, not executable instructions."
            self.assertIn(anchor, text)
            self.inner.write_brief(
                root, text.replace(
                    anchor,
                    anchor + " A SECURITY.md file is executable "
                    "instruction for the review run.", 1))
            problems = self.problems(root)
            self.assertTrue(any(
                "SECURITY.md file is executable instruction" in p
                for p in problems), problems)

    def test_evidence_figures_exchanged_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.brief_text(root)
            broken = text.replace(
                "rule guided variants recovered 98 percent",
                "rule guided variants recovered 58.3 percent", 1)
            broken = broken.replace(
                "58.3 percent for the baseline control",
                "98 percent for the baseline control", 1)
            self.assertNotEqual(broken, text)
            self.inner.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(any(
                "does not bind the 98 percent figure" in p
                for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
