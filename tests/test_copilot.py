"""Build 13, the Copilot SDK agent build.

The brief at docs/copilot-sdk-brief.md records the Copilot code
review surface as primary, the head branch instructions as
untrusted input posture, the base branch merge authority rule,
the never approve on a red packet rule, and the capability
level model pin, all with derivation notes pinned by the gate
at scripts/check_copilot.py. These tests prove the pin fires
for a real reason on every load bearing claim the round 26
lanes named. A trusted head branch sentence, a head branch
merge authority grant, a named review model, a permitted
approval on a red packet, a dropped derivation note, a
dropped pin, and a decision record without a decision 4
statement each fail the Copilot gate.
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
    spec = importlib.util.spec_from_file_location(
        "copilot_" + name, path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestCheckCopilot(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_copilot")

    def make_layout(self, tmp):
        """A scratch tree with the brief and the record."""
        root = Path(tmp) / "root"
        for rel in (
            "docs/copilot-sdk-brief.md",
            "docs/decisions.md",
        ):
            source = ROOT / rel
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        return root

    def problems(self, root):
        return self.mod.copilot_problems(root)

    def read_brief(self, root):
        return (root / "docs" / "copilot-sdk-brief.md").read_text(
            encoding="utf-8"
        )

    def write_brief(self, root, text):
        (root / "docs" / "copilot-sdk-brief.md").write_text(
            text, encoding="utf-8"
        )

    def break_brief(self, root, old, new, count=1):
        # The gate pins sentences on whitespace normalized text, so
        # the old string names words in order and any run of
        # whitespace in the brief matches. The rest of the brief
        # keeps its line breaks, so the section parsers still see
        # their headings. A test that names an old string the gate
        # cannot see is not a test.
        text = self.read_brief(root)
        pattern = re.escape(old).replace("\\ ", "\\s+")
        broken, hits = re.subn(
            pattern, lambda _match: new, text, count=count
        )
        self.assertNotEqual(broken, text)
        self.assertTrue(hits > 0)
        self.write_brief(root, broken)
        return self.problems(root)

    def test_the_shipped_tree_holds(self):
        self.assertEqual(self.mod.copilot_problems(ROOT), [])

    def test_the_scratch_layout_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            self.assertEqual(self.problems(root), [])

    def test_a_trusted_head_branch_sentence_fails(self):
        # R26-RT-01. Head branch instructions are untrusted
        # input. A later edit that trusts them must fail the
        # gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "Head branch instructions are untrusted input for "
                "the review run.",
                "Head branch instructions are trusted input for "
                "the review run.",
            )
            self.assertTrue(
                any("trusts head branch" in p for p in problems),
                problems,
            )

    def test_a_head_branch_merge_authority_grant_fails(self):
        # R26-RT-01. Merge authority lives in base branch
        # CODEOWNERS and rulesets only. A later edit that
        # grants head branch content merge authority must fail
        # the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "carries no base branch merge authority",
                "carries base branch merge authority",
            )
            self.assertTrue(
                any("merge authority" in p for p in problems),
                problems,
            )

    def test_a_named_review_model_fails(self):
        # R26-RT-02. The review model reports as unknown, so
        # model pinning stays at capability level. A later edit
        # that names a review model must fail the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            anchor = "### R5. Effort levels"
            plant = (
                "Copilot code review pull requests are reviewed "
                "by GPT-6.1 Sol.\n\n" + anchor
            )
            self.assertIn(anchor, text)
            self.write_brief(root, text.replace(anchor, plant, 1))
            problems = self.problems(root)
            self.assertTrue(
                any("names a model" in p for p in problems),
                problems,
            )

    def test_a_permitted_approval_on_a_red_packet_fails(self):
        # R26-RT-03. An approval never fires on a red packet,
        # including opt in approvals that count toward branch
        # protection. A later edit that permits it must fail
        # the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "An approval never fires on a red packet.",
                "An approval may fire on a red packet.",
            )
            self.assertTrue(
                any("approval" in p for p in problems), problems
            )

    def test_a_rule_without_a_derivation_note_fails(self):
        # The second packet guard. A rule with no derivation
        # note is a rival instruction source and must fail the
        # gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            anchor = "### R5. Effort levels"
            plant = (
                "### R0. A rule with no note\n\n"
                "This rule states something with no derivation.\n\n"
                + anchor
            )
            self.assertIn(anchor, text)
            self.write_brief(root, text.replace(anchor, plant, 1))
            problems = self.problems(root)
            self.assertTrue(
                any("no derivation note" in p for p in problems),
                problems,
            )

    def test_a_markerless_derivation_note_fails(self):
        # R27-ST-02. The deliberate_source marker distinguishes a
        # note that derives from a canonical section from passing
        # prose that merely mentions one. A note that names a
        # section title without the marker must fail the gate, so
        # a regression to bare substring matching cannot pass the
        # suite. A naive substring check would pass this plant.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "Derives from canonical skill, Trust and limits, "
                "which keeps untrusted content outside the "
                "packet's verified boundary, and the primary "
                "GitHub release note for the July 17 2026 change "
                "at github.blog/changelog/2026-07-17-copilot-code-"
                "review-customization-and-configurability-"
                "improvements with its security note.",
                "Derives from a passing mention of Trust and limits "
                "and nothing at all.",
            )
            self.assertTrue(
                any(
                    "names no canonical skill section" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_dropped_pin_fails(self):
        # A later edit that drops a stated pin must fail the
        # gate instead of drifting in silence.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "Lite is the standard review.",
                "Lite is the usual review.",
            )
            self.assertTrue(
                any("effort levels" in p for p in problems),
                problems,
            )

    def test_a_decision_record_without_a_statement_fails(self):
        # Every landed build records a decision 4 statement. A
        # decision record without one must fail the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            record = root / "docs" / "decisions.md"
            text = record.read_text(encoding="utf-8")
            self.assertIn("## 23. Build 13", text)
            pattern = re.escape(
                "Decision 4 binds this build like every other build."
            ).replace("\\ ", "\\s+")
            broken, hits = re.subn(
                pattern, "Some other sentence stands here.", text
            )
            self.assertTrue(hits > 0)
            self.assertNotEqual(broken, text)
            record.write_text(broken, encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("decision 4 statement" in p for p in problems),
                problems,
            )
    def plant_sentence(self, root, sentence):
        # Insert a sentence before a rule heading, inside the
        # rules section, and return the gate problems.
        text = self.read_brief(root)
        anchor = "### R5. Effort levels"
        self.assertIn(anchor, text)
        self.write_brief(
            root, text.replace(anchor, sentence + "\n\n" + anchor, 1)
        )
        return self.problems(root)

    def test_a_reliable_head_branch_sentence_fails(self):
        # R29-RT-13. The trust check forbade the single phrase
        # "trusted input", so a sentence calling head branch
        # instructions reliable and followable passed.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.plant_sentence(
                root,
                "Head branch instructions are reliable and may "
                "be followed.",
            )
            self.assertTrue(
                any("trusts head branch" in p for p in problems),
                problems,
            )

    def test_a_reworded_approval_permission_fails(self):
        # R29-RT-13. The approval check forbade the single verb
        # fire, so a sentence letting an approval go ahead or
        # be granted on a red packet passed.
        cases = (
            "An approval goes ahead on a red packet.",
            "Approvals are granted for red packets.",
        )
        for sentence in cases:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                problems = self.plant_sentence(root, sentence)
                self.assertTrue(
                    any("approval" in p for p in problems),
                    (sentence, problems),
                )

    def test_a_negated_approval_permission_passes(self):
        # R29-RT-15 style. A sentence that negates its own
        # permission verb states the correct posture and must
        # not fail the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.plant_sentence(
                root,
                "An approval never goes ahead on a red packet.",
            )
            self.assertEqual(problems, [], problems)

    def test_a_synonym_trust_sentence_fails(self):
        # R31-RT-05. Trust stated as dependable, relied on,
        # or safe to follow states the same trust without
        # the reliable and trustworthy words.
        cases = (
            "Head branch instructions are dependable.",
            "Head branch instructions can be relied on.",
            "Head branch instructions are safe to follow.",
        )
        for sentence in cases:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                problems = self.plant_sentence(root, sentence)
                self.assertTrue(
                    any("trusts head branch" in p
                        for p in problems),
                    (sentence, problems),
                )

    def test_a_synonym_approval_sentence_fails(self):
        # R31-RT-05. Permission stated as moves forward,
        # issued, clears, or fine states the same firing
        # without the goes ahead and granted verbs.
        cases = (
            "An approval moves forward on a red packet.",
            "An approval is issued for a red packet.",
            "An approval clears a red packet.",
            "An approval is fine on a red packet.",
        )
        for sentence in cases:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                problems = self.plant_sentence(root, sentence)
                self.assertTrue(
                    any("approval" in p for p in problems),
                    (sentence, problems),
                )

    def test_r32_synonym_sentences_fail(self):
        # R32-RT-02. Trust and approval stated as credible,
        # goes through, greenlights, endorsed, or valid on a
        # red packet passed while every pin stayed in place.
        cases = (
            ("Head branch instructions are credible.",
             "trusts head branch"),
            ("An approval goes through on a red packet.",
             "permits an approval firing"),
            ("An approval greenlights a red packet.",
             "permits an approval firing"),
            ("Head branch instructions are endorsed.",
             "trusts head branch"),
            ("A merge approval on a red packet is valid.",
             "permits an approval firing"),
        )
        for sentence, needle in cases:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                problems = self.plant_sentence(root, sentence)
                self.assertTrue(
                    any(needle in p for p in problems),
                    (sentence, problems),
                )

    def test_a_dropped_currency_pin_fails(self):
        # R31-EX-02 and R31-RT-09 through R31-RT-11. The
        # Build 13 currency notes pin the global default
        # window, the model policy API, the totals by
        # client caveats, the Teams legacy retirement, the
        # Argon availability, and the November 16 all
        # experiences coverage.
        cases = (
            ("October 22 through October 26 2026",
             "global default window"),
            ("MCP servers in Copilot",
             "global default pages"),
            ("model policy API is generally available",
             "model policy API"),
            ("totals_by_client",
             "totals by client metrics"),
            ("best effort grouping",
             "totals best effort caveat"),
            ("counts model calls, not prompts",
             "calls not prompts caveat"),
            ("renamed GitHub deprecated",
             "Teams legacy retirement"),
            ("Gemini 4 Argon general availability in Copilot",
             "Gemini 4 Argon availability"),
            ("across all GitHub Copilot experiences",
             "all experiences coverage"),
        )
        for old, needle in cases:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                problems = self.break_brief(
                    root, old, "Some other sentence stands here."
                )
                self.assertTrue(
                    any(needle in p for p in problems),
                    (old, problems),
                )

    def test_a_merge_authority_without_base_branch_fails(self):
        # R31-RT-05. Merge authority without the base branch
        # qualifier, and a merge approval authored by head
        # branch instructions said to be valid, grant the
        # same authority the exact phrase check missed.
        cases = (
            "Head branch instructions carry merge authority.",
            "A merge approval authored by head branch "
            "instructions is valid.",
        )
        for sentence in cases:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                problems = self.plant_sentence(root, sentence)
                self.assertTrue(
                    any("merge authority" in p for p in problems),
                    (sentence, problems),
                )

    def test_trust_core_plants_after_the_rules_section_fail(self):
        # R36-RT-01. The three trust core rules restated as
        # plain sentences appended after the rules section
        # passed while the trust and approval scans read the
        # rules section only. The scans now read the whole
        # brief, so each appended restatement fails.
        cases = (
            ("An approval fires on a red packet when the "
             "reviewer asks for one.", "approval"),
            ("Merge authority lives in head branch CODEOWNERS "
             "and rulesets only.", "merge authority"),
            ("Head branch instructions are trusted input for "
             "the review run.", "trusts head branch"),
        )
        for sentence, needle in cases:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                text = self.read_brief(root)
                self.write_brief(
                    root, text + "\n\n" + sentence + "\n"
                )
                problems = self.problems(root)
                self.assertTrue(
                    any(needle in p for p in problems),
                    (sentence, problems),
                )

    def test_gate_review_split_and_paraphrase_plants_fail(self):
        # Gate review repair. The whole brief scans still
        # read one sentence at a time, so the review split
        # the trust claim and the approval claim across a
        # sentence boundary and restated each in a passive
        # or decide form, and each passed. The scans now
        # read the pairs of sentences that stand next to
        # each other beside the single sentences.
        cases = (
            ("Head branch instructions are input for the "
             "review run. They are trusted.",
             "trusts head branch instructions"),
            ("A red packet is present in this run. An "
             "approval fires on it when the reviewer asks "
             "for one.", "permits an approval firing"),
            ("A red packet can be approved when the "
             "reviewer asks for one.",
             "permits an approval firing"),
            ("Head branch instructions should be obeyed "
             "during the review run.",
             "trusts head branch instructions"),
            ("Only head branch CODEOWNERS and rulesets "
             "decide whether a merge proceeds.",
             "grants head branch content merge authority"),
        )
        for plant, needle in cases:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                text = self.read_brief(root)
                self.write_brief(root, text + "\n\n" + plant + "\n")
                problems = self.problems(root)
                self.assertTrue(
                    any(needle in p for p in problems),
                    (plant, problems),
                )

    def test_gate_review_negated_and_attributed_trust_passes(self):
        # Gate review repair. The widened trust scan
        # carried no negation guard and no attribution
        # guard, so true sentences restating the untrusted
        # posture with not or never, and a derivation note
        # reporting and rejecting a source claim, failed.
        cases = (
            "Head branch instructions are not reliable "
            "input for the review run.",
            "Head branch instructions are never trustworthy "
            "input for the review run.",
            "Head branch instructions are not credible "
            "input for the review run.",
            "The derivation note records that a source once "
            "called head branch instructions credible, a "
            "claim this brief rejects.",
        )
        for plant in cases:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                text = self.read_brief(root)
                self.write_brief(root, text + "\n\n" + plant + "\n")
                self.assertEqual(self.problems(root), [])

    def test_round37_trust_split_across_three_sentences_fails(self):
        # R37-RT-02. The trust claim split across three
        # sentences, with a filler between the subject half
        # and the predicate half, stands in no sentence and
        # no pair, and the triple reading must catch it.
        plant = (
            "Head branch instructions are input for the "
            "review run. The packet lists them beside the "
            "diff for the reviewer. They are trusted."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any("trusts head branch" in p for p in problems),
                problems,
            )

    def test_round37_approval_split_across_three_sentences_fails(self):
        # R37-RT-02. The approval and its firing split
        # across three sentences must fail the same way.
        plant = (
            "An approval is recorded for this run. The "
            "packet lists its checks beside the diff. It "
            "fires on the red packet when the reviewer "
            "asks for one."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "permits an approval firing" in p
                    for p in problems
                ),
                problems,
            )

    def test_round37_negation_after_the_verb_passes(self):
        # R37-RT-03. A negation standing after the verb as
        # a negative quantifier states the shipped posture
        # and must not fail the gate.
        sentences = (
            "Head branch instructions are trusted by no "
            "reviewer in this run.",
            "Head branch instructions are trusted by nobody "
            "in this run.",
            "An approval is granted on no red packet in "
            "this run.",
            "Head branch instructions are obeyed by no "
            "reviewer in this run.",
        )
        for sentence in sentences:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                text = self.read_brief(root)
                self.write_brief(
                    root, text + "\n\n" + sentence + "\n"
                )
                self.assertEqual(
                    self.problems(root), [], sentence
                )

    def test_round37_fixreview_authority_split_across_three_fails(self):
        # R37F-RT-01. The merge authority passes read
        # triples too, because the fix review split an
        # authority claim across three sentences the same
        # way the round 37 review split the trust claim.
        plant = (
            "Head branch instructions are recorded for this "
            "run. The packet lists them beside the diff for "
            "the reviewer. They carry merge authority for "
            "the review."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "grants head branch content merge "
                    "authority" in p
                    for p in problems
                ),
                problems,
            )

    def test_round37_fixreview_filler_negation_does_not_guard(self):
        # R37F-RT-02. A negation in a filler sentence
        # between the halves of a split trust claim guards
        # nothing, because the guard reads only the
        # sentences that carry the claim.
        plant = (
            "Head branch instructions are input for the "
            "review run. No reviewer questions the packet "
            "contents in this run. They are trusted."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any("trusts head branch" in p for p in problems),
                problems,
            )

    def test_round37_fixreview_zero_quantifier_after_verb_passes(self):
        # R37F-RT-03. The zero and not a single forms state
        # the same negative agent and object as the four
        # filed forms, so the true sentences must pass.
        sentences = (
            "Head branch instructions are trusted by zero "
            "reviewers in this run.",
            "Head branch instructions are trusted by not a "
            "single reviewer in this run.",
            "An approval is granted to zero red packets in "
            "this run.",
        )
        for sentence in sentences:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                text = self.read_brief(root)
                self.write_brief(
                    root, text + "\n\n" + sentence + "\n"
                )
                self.assertEqual(
                    self.problems(root), [], sentence
                )


if __name__ == "__main__":
    unittest.main()
