"""Build 20, the Comate adaptation.

The build ships a byte identical copy of the canonical skill
at .comate/skills/recognitio for the native Comate project
path, the brief at docs/comate-brief.md, and no manifest or
registration artifact. These tests prove the gate at
scripts/check_comate.py fires for a real reason on every
stated failure. A drifted, missing, or extra file in the
copy, a manifest planted beside the copy, a symlinked seat,
a brief that drops the sign in wall or the unverified
remainder, a rule without a checkable derivation, an
appended contradiction, and a decision record without its
decision 4 statement each fail the Comate gate. The
contradiction cases include the natural phrasings and the
placements a slice based reader would miss, a sentence
that withdraws a pinned claim while quoting it, a swapped
derivation note, a negated citation, and the deletion of
rule C8.
"""

import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SKILL_FILES = (
    "SKILL.md",
    "agents/openai.yaml",
    "references/budget-system.md",
    "references/verifier-completeness.md",
    "scripts/extract.py",
)

FILES = tuple(
    ".agents/skills/recognitio/" + name for name in SKILL_FILES
) + tuple(
    ".comate/skills/recognitio/" + name for name in SKILL_FILES
) + (
    "docs/comate-brief.md",
    "docs/decisions.md",
    "docs/README.md",
    "README.md",
    "CHANGELOG.md",
    "AGENTS.md",
)


def load_script(name):
    path = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(
        "comate_" + name, path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestCheckComate(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_comate")

    def make_layout(self, tmp):
        """A scratch tree with every file the gate reads."""
        root = Path(tmp) / "root"
        for rel in FILES:
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / rel, target)
        return root

    def read(self, root, rel):
        return (root / rel).read_text(encoding="utf-8")

    def write(self, root, rel, text):
        (root / rel).write_text(text, encoding="utf-8")

    def problems(self, root):
        return self.mod.comate_problems(root)

    def test_the_shipped_tree_holds(self):
        self.assertEqual(self.mod.comate_problems(ROOT), [])

    def test_the_scratch_layout_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            self.assertEqual(self.problems(root), [])

    def test_a_drifted_copy_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = ".comate/skills/recognitio/SKILL.md"
            text = self.read(root, rel)
            broken = text + "\nA drifted line.\n"
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("drifts from the canonical skill" in p
                    for p in problems),
                problems,
            )

    def test_a_missing_copy_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            (root / ".comate/skills/recognitio/scripts"
             / "extract.py").unlink()
            problems = self.problems(root)
            self.assertTrue(
                any("missing the file" in p for p in problems),
                problems,
            )

    def test_an_extra_copy_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            stray = (root / ".comate/skills/recognitio"
                     / "references" / "stray.md")
            stray.write_text("stray", encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("extra file" in p for p in problems), problems
            )

    def test_a_manifest_beside_the_copy_fails(self):
        # No manifest is evidenced for Comate, so one planted
        # beside the copy reads as a registration the record
        # never evidenced and fails the census.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            (root / ".comate" / "plugin.json").write_text(
                "{}", encoding="utf-8"
            )
            problems = self.problems(root)
            self.assertTrue(
                any("not the skill copy alone" in p
                    for p in problems),
                problems,
            )

    def test_a_missing_comate_tree_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            shutil.rmtree(root / ".comate")
            problems = self.problems(root)
            self.assertTrue(
                any("carries no skill copy" in p for p in problems),
                problems,
            )

    def test_a_symlinked_copy_fails(self):
        # The byte pin certifies content, not containment, so a
        # symlinked seat needs its own refusal.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            copy_dir = root / ".comate" / "skills" / "recognitio"
            shutil.rmtree(copy_dir)
            copy_dir.symlink_to(
                root / ".agents" / "skills" / "recognitio",
                target_is_directory=True,
            )
            problems = self.problems(root)
            self.assertTrue(
                any("symlink" in p for p in problems), problems
            )

    def test_a_brief_without_the_unverified_remainder_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "docs/comate-brief.md"
            text = self.read(root, rel)
            broken = text.replace(
                "session stays unverified",
                "session stands verified",
            )
            self.assertNotEqual(broken, text)
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("unverified remainder" in p for p in problems),
                problems,
            )

    def test_a_brief_without_the_sign_in_wall_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "docs/comate-brief.md"
            text = self.read(root, rel)
            broken = text.replace(
                "presents a log in button and no task surface",
                "opens the agent workspace at once",
            )
            self.assertNotEqual(broken, text)
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("sign in wall" in p for p in problems),
                problems,
            )

    def test_a_brief_without_the_no_listing_sentence_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "docs/comate-brief.md"
            text = self.read(root, rel)
            broken = text.replace(
                "ships no submission",
                "ships a submission",
            )
            self.assertNotEqual(broken, text)
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("no listing honesty sentence" in p
                    for p in problems),
                problems,
            )

    def test_a_rule_without_a_derivation_note_fails(self):
        # The second packet guard. A rule that names no
        # canonical section or checkable citation is a rival
        # instruction source, and the gate must catch the note
        # going missing.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "docs/comate-brief.md"
            text = self.read(root, rel)
            broken = text.replace("Derives from", "Restates", 1)
            self.assertNotEqual(broken, text)
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("no derivation note" in p for p in problems),
                problems,
            )

    def test_a_rule_with_an_uncheckable_derivation_fails(self):
        # A derivation note that names nothing the gate can
        # check is the same failure wearing a label. Stripping
        # the Microi stem leaves the path rule with no source.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "docs/comate-brief.md"
            text = self.read(root, rel)
            broken = text.replace(
                "Microi.v8-engine", "a secondary writeup"
            )
            self.assertNotEqual(broken, text)
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("derivation note" in p for p in problems),
                problems,
            )

    def test_an_appended_contradiction_fails(self):
        # The honesty negatives. The pinned sentences stay in
        # place and the appended sentences claim the opposite,
        # so only a negative pin can catch them.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "docs/comate-brief.md"
            text = self.read(root, rel)
            broken = text + (
                "\nThe skill was invoked in a live Comate "
                "session and Comate runs the bundled extractor "
                "on every review. The pack has been submitted "
                "to a Comate marketplace.\n"
            )
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("invoked in a live Comate session" in p
                    for p in problems),
                problems,
            )
            self.assertTrue(
                any("bundled extractor" in p for p in problems),
                problems,
            )
            self.assertTrue(
                any("submitted to a Comate marketplace" in p
                    for p in problems),
                problems,
            )

    def test_a_capitalised_contradiction_fails(self):
        # A claim that opens a sentence capitalises its first
        # word, so the stem refusal folds case or the most
        # natural form of the false claim walks past it.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "docs/comate-brief.md"
            text = self.read(root, rel)
            broken = text + (
                "\nInvoked in a live Comate session, the skill "
                "produced a verified packet.\n"
            )
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("invoked in a live Comate session" in p
                    for p in problems),
                problems,
            )

    def test_a_contradiction_in_decision_32_fails(self):
        # The decision record carries the same honesty claims,
        # so a contradicting sentence appended inside it fails
        # on the same stems.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "docs/decisions.md"
            text = self.read(root, rel)
            broken = text + (
                "\nThe skill stands verified in a live Comate "
                "session.\n"
            )
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("decision 32" in p for p in problems),
                problems,
            )

    def test_a_decision_record_without_decision_4_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / "docs" / "decisions.md"
            text = path.read_text(encoding="utf-8")
            start = text.find("## 32. Build 20")
            self.assertNotEqual(start, -1)
            record = text[start:]
            broken = record.replace(
                "Decision 4 binds", "Decision 4 is noted", 1
            )
            self.assertNotEqual(broken, record)
            path.write_text(
                text[:start] + broken, encoding="utf-8"
            )
            problems = self.problems(root)
            self.assertTrue(
                any("decision 4" in p for p in problems), problems
            )

    def test_a_dropped_readme_link_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "README.md"
            text = self.read(root, rel)
            broken = text.replace(
                "[the Comate brief](docs/comate-brief.md)",
                "the Comate brief",
            )
            self.assertNotEqual(broken, text)
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("does not link the Comate brief" in p
                    for p in problems),
                problems,
            )

    def test_a_hardened_readme_marketplace_claim_fails(self):
        # The scoping record grades the marketplace negative
        # unverified with a negative lean, so the README must
        # keep the evidenced scoping. Hardening it into an
        # existence claim drops the pinned sentence and fails.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "README.md"
            text = self.read(root, rel)
            broken = text.replace(
                "no Comate skill marketplace or submission "
                "route is evidenced",
                "no Comate skill marketplace listing exists",
            )
            self.assertNotEqual(broken, text)
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("marketplace position" in p for p in problems),
                problems,
            )

    def test_a_dropped_index_entry_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "docs/README.md"
            text = self.read(root, rel)
            broken = text.replace("(comate-brief.md)", "(comate.md)")
            self.assertNotEqual(broken, text)
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("does not list the Comate brief" in p
                    for p in problems),
                problems,
            )

    def test_a_dropped_changelog_entry_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "CHANGELOG.md"
            text = self.read(root, rel)
            broken = text.replace(
                "- The Comate adaptation.", "- The Comate build."
            )
            self.assertNotEqual(broken, text)
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("no Comate adaptation entry" in p
                    for p in problems),
                problems,
            )

    def test_a_live_session_claim_in_natural_phrasing_fails(self):
        # The red team plants. The appended block claims the
        # session result, the store listing, and the accepted
        # submission in ordinary phrasing, none of it in the
        # builder's own wording, and the family reader has to
        # refuse it anyway.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "docs/comate-brief.md"
            text = self.read(root, rel)
            broken = text + (
                "\nRecognitio ran in a signed in Comate "
                "session. The client loaded the skill and ran "
                "extract.py to produce a packet. The skill is "
                "listed in the Comate skill store, and a "
                "submission pack was accepted.\n"
            )
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("invoked in a live Comate session" in p
                    for p in problems),
                problems,
            )
            self.assertTrue(
                any("submitted to a Comate marketplace" in p
                    for p in problems),
                problems,
            )
            self.assertTrue(
                any("submission stands accepted" in p
                    for p in problems),
                problems,
            )

    def test_an_extractor_claim_in_past_tense_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "docs/comate-brief.md"
            text = self.read(root, rel)
            broken = text + (
                "\nComate executed the bundled extractor "
                "script on the test range and stamped the "
                "packet.\n"
            )
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("bundled extractor" in p for p in problems),
                problems,
            )

    def test_a_settled_open_question_claim_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "docs/comate-brief.md"
            text = self.read(root, rel)
            broken = text + (
                "\nFrontmatter is settled. Comate ignores the "
                "fields beyond name and description, and the "
                "native copy takes precedence over the "
                "canonical one.\n"
            )
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("stands settled" in p for p in problems),
                problems,
            )

    def test_a_reordered_live_session_claim_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "docs/comate-brief.md"
            text = self.read(root, rel)
            broken = text + (
                "\nThe skill was verified in a live session "
                "with Comate after it was invoked in a live "
                "session inside the client.\n"
            )
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("invoked in a live Comate session" in p
                    for p in problems),
                problems,
            )

    def test_a_contradiction_in_the_docs_index_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "docs/README.md"
            text = self.read(root, rel)
            broken = text + (
                "\nThe pack has been submitted to a Comate "
                "marketplace and the skill stands verified "
                "in a live Comate session.\n"
            )
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("docs/README.md" in p for p in problems),
                problems,
            )

    def test_a_contradiction_after_the_changelog_entry_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "CHANGELOG.md"
            text = self.read(root, rel)
            broken = text + (
                "\n- The pack has been submitted to a Comate "
                "marketplace.\n"
            )
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("CHANGELOG.md" in p for p in problems),
                problems,
            )

    def test_a_contradiction_before_decision_32_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "docs/decisions.md"
            text = self.read(root, rel)
            marker = "## 32. Build 20"
            self.assertIn(marker, text)
            broken = text.replace(
                marker,
                "The skill was invoked in a live Comate "
                "session.\n\n" + marker,
                1,
            )
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("invoked in a live Comate session" in p
                    for p in problems),
                problems,
            )

    def test_a_contradiction_in_the_readme_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "README.md"
            text = self.read(root, rel)
            broken = text + (
                "\nRecognitio ran in a signed in Comate "
                "session.\n"
            )
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("README.md" in p for p in problems),
                problems,
            )

    def test_a_contradiction_in_agents_md_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "AGENTS.md"
            text = self.read(root, rel)
            broken = text + (
                "\nComate executed the bundled extractor on "
                "the test range.\n"
            )
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("AGENTS.md" in p for p in problems),
                problems,
            )

    def test_a_withdrawal_sentence_in_the_brief_fails(self):
        # A presence pin cannot tell an assertion from a
        # quotation that withdraws it, so the withdrawal
        # phrasing itself is refused.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "docs/comate-brief.md"
            text = self.read(root, rel)
            broken = text + (
                "\nIt is no longer true that invocation "
                "inside a live Comate session stays "
                "unverified.\n"
            )
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("withdraws a pinned claim" in p
                    for p in problems),
                problems,
            )

    def test_a_withdrawn_decision_4_statement_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / "docs" / "decisions.md"
            text = path.read_text(encoding="utf-8")
            start = text.find("## 32. Build 20")
            self.assertNotEqual(start, -1)
            record = text[start:]
            broken = record.replace(
                "Decision 4 binds",
                "It is false that Decision 4 binds",
                1,
            )
            self.assertNotEqual(broken, record)
            path.write_text(
                text[:start] + broken, encoding="utf-8"
            )
            problems = self.problems(root)
            self.assertTrue(
                any("withdraws a pinned claim" in p
                    for p in problems),
                problems,
            )

    def test_the_readme_copy_sentence_dropped_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "README.md"
            text = self.read(root, rel)
            broken = text.replace(
                "a byte identical copy at "
                "`.comate/skills/recognitio/`",
                "a copy at `.comate/skills/recognitio/`",
            )
            self.assertNotEqual(broken, text)
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("byte identical" in p for p in problems),
                problems,
            )

    def test_the_readme_comate_subsection_dropped_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "README.md"
            text = self.read(root, rel)
            broken = text.replace("### Comate", "### Comate route")
            self.assertNotEqual(broken, text)
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("no Comate install subsection" in p
                    for p in problems),
                problems,
            )

    def test_rule_c8_deleted_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "docs/comate-brief.md"
            text = self.read(root, rel)
            start = text.find("### C8.")
            self.assertNotEqual(start, -1)
            end = text.find("\n## ", start)
            self.assertNotEqual(end, -1)
            broken = text[:start] + text[end + 1:]
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("C1 to C8" in p for p in problems),
                problems,
            )

    def test_a_swapped_derivation_note_fails(self):
        # Rule C8's note names real sources, so only a per
        # rule citation set catches it standing under C3.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "docs/comate-brief.md"
            text = self.read(root, rel)
            c3 = text.find("### C3.")
            c8 = text.find("### C8.")
            self.assertTrue(-1 < c3 < c8)
            note3_start = text.find("Derives from", c3)
            note3_end = text.find("\n\n", note3_start)
            note8_start = text.find("Derives from", c8)
            note8_end = text.find("\n\n", note8_start)
            note8 = text[note8_start:note8_end]
            broken = (
                text[:note3_start] + note8 + text[note3_end:]
            )
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("expected" in p and "C3" in p
                    for p in problems),
                problems,
            )

    def test_a_negated_citation_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "docs/comate-brief.md"
            text = self.read(root, rel)
            broken = text.replace(
                "Microi.v8-engine", "not Microi.v8-engine", 1
            )
            self.assertNotEqual(broken, text)
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("negates the citation" in p
                    for p in problems),
                problems,
            )

    def test_a_symlinked_seat_is_not_misdiagnosed(self):
        # With the seat linked, the census walk cannot see
        # inside it, so the gate must name the symlink and
        # must not claim a stray file stands beside the copy.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            copy_dir = root / ".comate" / "skills" / "recognitio"
            shutil.rmtree(copy_dir)
            copy_dir.symlink_to(
                root / ".agents" / "skills" / "recognitio",
                target_is_directory=True,
            )
            problems = self.problems(root)
            self.assertTrue(
                any("symlink" in p for p in problems), problems
            )
            self.assertFalse(
                any("not the skill copy alone" in p
                    for p in problems),
                problems,
            )


if __name__ == "__main__":
    unittest.main()

