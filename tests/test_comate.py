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
import re
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

    def test_a_manifest_inside_a_cache_folder_in_the_copy_fails(self):
        # Rounds 286 and 294. A manifest wearing a cache folder
        # name inside the copy must stand in the census, so the
        # gate names it instead of certifying the copy alone.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            cache = (root / ".comate/skills/recognitio"
                     / "__pycache__")
            cache.mkdir(parents=True)
            (cache / "manifest.json").write_text(
                "{}\n", encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("not the skill copy alone" in p
                    or "extra file" in p for p in problems),
                problems,
            )

    def test_a_manifest_wearing_a_cache_suffix_beside_the_copy_fails(self):
        # Rounds 286 and 294. A cache suffix alone excludes
        # nothing, so a manifest named with one is counted.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            (root / ".comate/skills/recognitio"
             / "manifest.pyc").write_text(
                "{}\n", encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("not the skill copy alone" in p
                    or "extra file" in p for p in problems),
                problems,
            )

    def test_a_plugin_file_inside_a_cache_folder_at_the_root_fails(self):
        # Rounds 286 and 294. The cache folder at the .comate
        # root is inside the census on the same rule.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            cache = root / ".comate" / "__pycache__"
            cache.mkdir(parents=True)
            (cache / "plugin.json").write_text(
                "{}\n", encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("not the skill copy alone" in p
                    or "beside" in p for p in problems),
                problems,
            )

    def test_a_bytecode_cache_file_in_a_cache_folder_passes(self):
        # Control. A genuine bytecode cache file, a .pyc file
        # inside a cache folder, stays excluded as build state
        # in both the fixed state and the state before the fix.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            cache = (root / ".comate/skills/recognitio/scripts"
                     / "__pycache__")
            cache.mkdir(parents=True)
            (cache / "extract.cpython-311.pyc").write_bytes(
                b"\x42\x0d\x0d\x0a cache bytes")
            self.assertEqual(self.problems(root), [])

    def test_a_bytecode_file_nested_below_a_cache_folder_fails(self):
        # Red team re-review of the burndown stack. A bytecode
        # file nested one folder below a cache folder is not
        # the shape an interpreter writes, so it stands in the
        # census like any other file and the gate names it.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            nested = (root / ".comate/skills/recognitio/scripts"
                      / "__pycache__" / "nested")
            nested.mkdir(parents=True)
            (nested / "payload.pyc").write_bytes(
                b"\x42\x0d\x0d\x0a payload bytes")
            problems = self.problems(root)
            self.assertTrue(
                any("not the skill copy alone" in p
                    or "extra file" in p for p in problems),
                problems,
            )

    def test_the_comate_bullet_under_removed_fails(self):
        # Round 288. The Comate bullet narrates an addition.
        # Moving it under the Removed subsection, where it
        # stood at the finding, must fail the gate on its
        # placement alone.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "CHANGELOG.md"
            text = self.read(root, rel)
            start = text.find("\n- The Comate adaptation.")
            self.assertTrue(start != -1)
            end = text.find("\n### Fixed", start)
            self.assertTrue(end != -1)
            bullet = text[start:end]
            moved = text[:start] + text[end:] + bullet + "\n"
            self.write(root, rel, moved)
            problems = self.problems(root)
            self.assertTrue(
                any("outside the Added subsection" in p
                    for p in problems),
                problems,
            )

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

    def test_a_comate_heading_inside_a_code_fence_does_not_stand(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "README.md"
            text = self.read(root, rel)
            broken = text.replace("### Comate", "### Comate route")
            broken += "\n```\n### Comate\n```\n"
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("no Comate install subsection" in p
                    for p in problems),
                problems,
            )

    def test_a_comate_heading_inside_an_html_comment_does_not_stand(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "README.md"
            text = self.read(root, rel)
            broken = text.replace("### Comate", "### Comate route")
            broken += "\n<!--\n### Comate\n-->\n"
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("no Comate install subsection" in p
                    for p in problems),
                problems,
            )

    def test_a_comate_heading_in_an_indented_code_block_does_not_stand(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "README.md"
            text = self.read(root, rel)
            broken = text.replace("### Comate", "### Comate route")
            broken += "\n\n    ### Comate\n"
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("no Comate install subsection" in p
                    for p in problems),
                problems,
            )

    def test_a_comate_heading_after_an_info_string_fence_does_not_stand(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "README.md"
            text = self.read(root, rel)
            broken = text.replace("### Comate", "### Comate route")
            broken += "\n```\ncode\n``` python\n### Comate\n```\n"
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("no Comate install subsection" in p
                    for p in problems),
                problems,
            )

    def test_a_comate_heading_inside_an_html_pre_block_does_not_stand(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "README.md"
            text = self.read(root, rel)
            broken = text.replace("### Comate", "### Comate route")
            broken += "\n<pre>\n### Comate\n</pre>\n"
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("no Comate install subsection" in p
                    for p in problems),
                problems,
            )

    def test_a_comate_heading_inside_an_html_block_does_not_stand(self):
        # The rendered HTML block family beyond pre. A heading
        # line inside a div, a details element or a raw text
        # element is block content or literal text in the
        # rendered document, never a heading.
        for plant in (
            "\n<div>\n### Comate\n</div>\n",
            "\n<details>\n### Comate\n</details>\n",
            "\n<script>\n### Comate\n</script>\n",
            "\n<style>\n### Comate\n</style>\n",
            "\n<textarea>\n### Comate\n</textarea>\n",
        ):
            with self.subTest(plant=plant):
                with tempfile.TemporaryDirectory() as tmp:
                    root = self.make_layout(tmp)
                    rel = "README.md"
                    text = self.read(root, rel)
                    broken = text.replace(
                        "### Comate", "### Comate route")
                    broken += plant
                    self.write(root, rel, broken)
                    problems = self.problems(root)
                    self.assertTrue(
                        any("no Comate install subsection" in p
                            for p in problems),
                        problems,
                    )

    def test_a_comate_heading_inside_the_remaining_block_shapes_does_not_stand(self):
        # The rendered block family beyond the block level
        # tags. A lone tag line of any other element, a
        # processing instruction, a declaration and a CDATA
        # block each open a block in the rendering, and a
        # block or a fence standing inside a list item opens
        # after its list marker, so a heading inside any of
        # them stands in no rendered subsection.
        for plant in (
            "\n<span>\n### Comate\n",
            "\n<br>\n### Comate\n",
            '\n<a name="comate">\n### Comate\n',
            "\n<search>\n### Comate\n</search>\n",
            "\n<?pi\n### Comate\n?>\n",
            "\n<![CDATA[\n### Comate\n]]>\n",
            "\n<!FOO\n### Comate\n>\n",
            "\n- <div>\n  ### Comate\n",
            "\n- ```\n  ### Comate\n  ```\n",
        ):
            with self.subTest(plant=plant):
                with tempfile.TemporaryDirectory() as tmp:
                    root = self.make_layout(tmp)
                    rel = "README.md"
                    text = self.read(root, rel)
                    broken = text.replace(
                        "### Comate", "### Comate route")
                    broken += plant
                    self.write(root, rel, broken)
                    problems = self.problems(root)
                    self.assertTrue(
                        any("no Comate install subsection" in p
                            for p in problems),
                        problems,
                    )

    def test_a_comate_heading_inside_blocks_after_any_line_does_not_stand(self):
        # The rendered start conditions past the blank line
        # proxy. The instruction, declaration and CDATA
        # blocks and a closing block tag can interrupt a
        # paragraph and open after a heading, a thematic
        # break or a fence close, a lone tag opens wherever
        # no paragraph stands open, including as a list item
        # its first content, and a block tag split across two
        # lines opens on its first line. Each plant below was
        # checked against the CommonMark reference renderer,
        # and none of them renders a Comate heading.
        for plant in (
            "\nSome closing paragraph text\n<?pi\n"
            "### Comate\n?>\n",
            "\nSome closing paragraph text\n<![CDATA[\n"
            "### Comate\n]]>\n",
            "\nSome closing paragraph text\n<!FOO\n"
            "### Comate\n>\n",
            "\n## A heading above\n<?pi\n### Comate\n?>\n",
            "\n---\n<?pi\n### Comate\n?>\n",
            "\n```\ncode\n```\n<?pi\n### Comate\n?>\n",
            "\n## A heading above\n<![CDATA[\n"
            "### Comate\n]]>\n",
            "\n## A heading above\n<!FOO\n### Comate\n>\n",
            "\n- item one\n  <?pi\n  ### Comate\n  ?>\n",
            "\n## A heading above\n<span>\n### Comate\n",
            '\n## A heading above\n<a name="comate">\n'
            "### Comate\n",
            "\n---\n<span>\n### Comate\n",
            "\n```\ncode\n```\n<span>\n### Comate\n",
            "\nSome closing paragraph text\n</div>\n"
            "### Comate\n",
            "\n## A heading above\n</div>\n### Comate\n",
            "\n- item one\n- <span>\n  ### Comate\n",
            "\n1. item one\n2. <span>\n   ### Comate\n",
            '\n<div\nclass="x">\n### Comate\n',
        ):
            with self.subTest(plant=plant):
                with tempfile.TemporaryDirectory() as tmp:
                    root = self.make_layout(tmp)
                    rel = "README.md"
                    text = self.read(root, rel)
                    broken = text.replace(
                        "### Comate", "### Comate route")
                    broken += plant
                    self.write(root, rel, broken)
                    problems = self.problems(root)
                    self.assertTrue(
                        any("no Comate install subsection" in p
                            for p in problems),
                        problems,
                    )

    def test_a_comate_heading_after_a_lone_tag_in_a_paragraph_stands(self):
        # The discharged shapes in the other direction. A
        # lone tag block cannot interrupt a paragraph, a lone
        # tag on a list continuation line stands inside the
        # item its paragraph, and a tag standing after a
        # comment closed on the same line opens nothing, so
        # the heading after each of them renders and stands,
        # as the reference renderer shows for all three.
        for plant in (
            "\nSome closing paragraph text\n<span>\n"
            "### Comate\n",
            "\n- item one\n  <span>\n  ### Comate\n",
            "\n<!-- x --> <span>\n### Comate\n",
        ):
            with self.subTest(plant=plant):
                with tempfile.TemporaryDirectory() as tmp:
                    root = self.make_layout(tmp)
                    rel = "README.md"
                    text = self.read(root, rel)
                    broken = text.replace(
                        "### Comate", "### Comate route")
                    broken += plant
                    self.write(root, rel, broken)
                    problems = self.problems(root)
                    self.assertFalse(
                        any("no Comate install subsection" in p
                            for p in problems),
                        problems,
                    )

    def test_a_comate_heading_after_a_lone_tag_past_a_closed_block_does_not_stand(self):
        # The lane 5 start condition shapes. A setext heading
        # underline of equals signs, a comment only line, a
        # blockquote line and the last item of a list on an
        # unindented line are each closed blocks in the
        # rendering, so a lone tag after any of them opens
        # its block and the heading inside it renders
        # nowhere. Each plant was checked against the
        # CommonMark reference renderer, and none of them
        # renders a Comate heading.
        for plant in (
            "\nA title\n===\n<span>\n### Comate\n",
            "\n<!-- a comment -->\n<span>\n### Comate\n",
            "\n> quoted text\n<span>\n### Comate\n",
            "\n> quoted text\n> more quoted\n<span>\n"
            "### Comate\n",
            "\n- item one\n- item two\n<span>\n### Comate\n",
            "\n1. item one\n2. item two\n<span>\n"
            "### Comate\n",
        ):
            with self.subTest(plant=plant):
                with tempfile.TemporaryDirectory() as tmp:
                    root = self.make_layout(tmp)
                    rel = "README.md"
                    text = self.read(root, rel)
                    broken = text.replace(
                        "### Comate", "### Comate route")
                    broken += plant
                    self.write(root, rel, broken)
                    problems = self.problems(root)
                    self.assertTrue(
                        any("no Comate install subsection" in p
                            for p in problems),
                        problems,
                    )

    def test_a_comate_heading_after_a_lone_tag_past_the_lane6_blocks_does_not_stand(self):
        # The lane 6 red team shapes on their next roots. A
        # comment block spanning lines, a blockquote its
        # lazy continuation line and a list item its
        # paragraph after a blank line are each closed
        # blocks or no paragraph of the outer document in
        # the rendering, so a lone tag after any of them
        # opens its block and the heading inside it renders
        # nowhere. Each plant was checked against the
        # CommonMark reference renderer, and none of them
        # renders a Comate heading.
        for plant in (
            "\n<!-- start\nend -->\n<span>\n### Comate\n",
            "\n<!-- start\nend --> tail\n<span>\n"
            "### Comate\n",
            "\n<!-- start\na middle line\nend -->\n<span>\n"
            "### Comate\n",
            "\nSome closing paragraph text\n<!-- start\n"
            "end -->\n<span>\n### Comate\n",
            "\n> quoted text\nlazy line\n<span>\n"
            "### Comate\n",
            "\n- item one\n\n  para in item\n<span>\n"
            "### Comate\n",
        ):
            with self.subTest(plant=plant):
                with tempfile.TemporaryDirectory() as tmp:
                    root = self.make_layout(tmp)
                    rel = "README.md"
                    text = self.read(root, rel)
                    broken = text.replace(
                        "### Comate", "### Comate route")
                    broken += plant
                    self.write(root, rel, broken)
                    problems = self.problems(root)
                    self.assertTrue(
                        any("no Comate install subsection" in p
                            for p in problems),
                        problems,
                    )

    def test_a_comate_heading_after_a_lone_tag_past_a_list_lazy_line_does_not_stand(self):
        # The lane 7 red team Minor on its new root. A
        # list item its lazy continuation line is the item
        # its own paragraph continuing in the rendering,
        # so the item closes after it and a lone tag after
        # it opens its block, with the heading inside the
        # block. Each plant was checked against the
        # CommonMark reference renderer, and none of them
        # renders a Comate heading.
        for plant in (
            "\n- item one\nlazy line\n<span>\n### Comate\n",
            "\n- item one\nlazy line\nsecond lazy line\n"
            "<span>\n### Comate\n",
            "\n1. item one\nlazy line\n<span>\n"
            "### Comate\n",
            "\n* item one\nlazy line\n<span>\n### Comate\n",
            "\n- one\n- two\nlazy line\n<span>\n"
            "### Comate\n",
            "\n- item one\n lazy line\n<span>\n"
            "### Comate\n",
            "\n- item one\n\n  para in item\nlazy line\n"
            "<span>\n### Comate\n",
        ):
            with self.subTest(plant=plant):
                with tempfile.TemporaryDirectory() as tmp:
                    root = self.make_layout(tmp)
                    rel = "README.md"
                    text = self.read(root, rel)
                    broken = text.replace(
                        "### Comate", "### Comate route")
                    broken += plant
                    self.write(root, rel, broken)
                    problems = self.problems(root)
                    self.assertTrue(
                        any("no Comate install subsection" in p
                            for p in problems),
                        problems,
                    )

    def test_a_comate_heading_after_a_lone_tag_past_the_lane9_item_shapes_does_not_stand(self):
        # The lane 8 red team Minor on its new roots and
        # the fence standing beside them. A list item its
        # paragraph whose first line is a backtick fence
        # line carrying a backtick in its info string is
        # no fence in the rendering, so its lazy line is
        # the item its continuation and the tag after it
        # opens its block. An item opened by a bare marker
        # holds its indented paragraph in the same way. A
        # fence standing in an item with its content lines
        # unindented ends at the first unindented line in
        # the rendering and a new fence opens at the
        # closing line, swallowing the tag and the
        # heading. Each plant was checked against the
        # CommonMark reference renderer, and none of them
        # renders a Comate heading.
        for plant in (
            "\n- ```a`b\nlazy line\n<span>\n### Comate\n",
            "\n- item one\n\n  ```a`b\nlazy line\n"
            "<span>\n### Comate\n",
            "\n-\n  para in item\n<span>\n### Comate\n",
            "\n-\n  para in item\nlazy line\n<span>\n"
            "### Comate\n",
            "\n- ```\ncode\n```\nlazy line\n<span>\n"
            "### Comate\n",
        ):
            with self.subTest(plant=plant):
                with tempfile.TemporaryDirectory() as tmp:
                    root = self.make_layout(tmp)
                    rel = "README.md"
                    text = self.read(root, rel)
                    broken = text.replace(
                        "### Comate", "### Comate route")
                    broken += plant
                    self.write(root, rel, broken)
                    problems = self.problems(root)
                    self.assertTrue(
                        any("no Comate install subsection" in p
                            for p in problems),
                        problems,
                    )

    def test_a_comate_heading_after_a_lone_tag_past_the_lane10_item_shapes_does_not_stand(self):
        # The lane 9 red team Minor standing on its new
        # root. A line at the fourth column inside an
        # open list item, short of four columns past the
        # item its content indent, is the item its
        # content in the rendering and not an indented
        # code block, so a paragraph standing there arms
        # the item its paragraph fact, the lazy line
        # after it is the item its continuation, and the
        # lone tag after that stands inside the item.
        # Each plant was checked against the CommonMark
        # reference renderer, and none of them renders a
        # Comate heading.
        for plant in (
            "\n-\n    para in item\nlazy line\n<span>\n"
            "### Comate\n",
            "\n- item one\n\n    code block\npara line\n"
            "<span>\n### Comate\n",
            "\n- item one\n    para line\nlazy line\n"
            "<span>\n### Comate\n",
        ):
            with self.subTest(plant=plant):
                with tempfile.TemporaryDirectory() as tmp:
                    root = self.make_layout(tmp)
                    rel = "README.md"
                    text = self.read(root, rel)
                    broken = text.replace(
                        "### Comate", "### Comate route")
                    broken += plant
                    self.write(root, rel, broken)
                    problems = self.problems(root)
                    self.assertTrue(
                        any("no Comate install subsection" in p
                            for p in problems),
                        problems,
                    )

    def test_a_comate_heading_after_the_lane10_item_controls_stands(self):
        # The controls in the other direction, checked
        # against the same renderer. A line at four
        # columns past the item its content indent inside
        # the item is a true indented code block of the
        # item, so the paragraph after it is a paragraph
        # of the outer document and the heading after the
        # tag stands. An item opened by a marker carrying
        # a trailing space and no content is an empty
        # item in the rendering, the lane 9 red team Note
        # shape, so no item paragraph stands open for the
        # lazy line and the heading stands.
        for plant in (
            "\n- item one\n\n      code block\npara line\n"
            "<span>\n### Comate\n",
            "\n- item one\n- \nlazy line\n<span>\n"
            "### Comate\n",
        ):
            with self.subTest(plant=plant):
                with tempfile.TemporaryDirectory() as tmp:
                    root = self.make_layout(tmp)
                    rel = "README.md"
                    text = self.read(root, rel)
                    broken = text.replace(
                        "### Comate", "### Comate route")
                    broken += plant
                    self.write(root, rel, broken)
                    problems = self.problems(root)
                    self.assertFalse(
                        any("no Comate install subsection" in p
                            for p in problems),
                        problems,
                    )
        comate_doc = " ".join(
            self.mod.comate_subsection_stands.__doc__.split())
        for phrase in (
            "short of four columns past the item its "
            "content indent",
            "a marker carrying a trailing space and no "
            "content opens an empty item",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, comate_doc)

    def test_a_comate_heading_after_a_lone_tag_past_the_lane11_tab_gap_items_does_not_stand(self):
        # The lane 10 red team Minor 6 standing on its
        # new root. A marker whose gap carries a tab
        # gave the reader a content indent in characters
        # where the renderer gives it in columns, so an
        # item paragraph standing in the window between
        # the two indents was skipped whole as an
        # indented code block and the item its paragraph
        # fact was never armed. The content indent is
        # now counted in columns, a tab counting to the
        # next multiple of four, on the three marker
        # gaps that carry a tab, beside the discharged
        # sibling whose renewal line stands inside both
        # windows. Each plant was checked against the
        # CommonMark reference renderer, and none of
        # them renders a Comate heading.
        for plant in (
            "\n-\titem one\n\n      para in item\n"
            "lazy line\n<span>\n### Comate\n",
            "\n1.\titem one\n\n       para in item\n"
            "lazy line\n<span>\n### Comate\n",
            "\n- \titem one\n\n       para in item\n"
            "lazy line\n<span>\n### Comate\n",
            "\n-\titem one\n\n    para in item\n"
            "lazy line\n<span>\n### Comate\n",
        ):
            with self.subTest(plant=plant):
                with tempfile.TemporaryDirectory() as tmp:
                    root = self.make_layout(tmp)
                    rel = "README.md"
                    text = self.read(root, rel)
                    broken = text.replace(
                        "### Comate", "### Comate route")
                    broken += plant
                    self.write(root, rel, broken)
                    problems = self.problems(root)
                    self.assertTrue(
                        any("no Comate install subsection" in p
                            for p in problems),
                        problems,
                    )

    def test_a_comate_heading_after_the_lane11_tab_gap_code_block_stands(self):
        # The control in the other direction, checked
        # against the same renderer. With a tab in the
        # marker gap the item its content indent stands
        # at four columns in the rendering, so a line at
        # eight columns, four columns past that indent,
        # is an indented code block of the item, the
        # paragraph after it is a paragraph of the outer
        # document, and the heading after the tag
        # stands.
        for plant in (
            "\n-\titem one\n\n        para in item\n"
            "lazy line\n<span>\n### Comate\n",
        ):
            with self.subTest(plant=plant):
                with tempfile.TemporaryDirectory() as tmp:
                    root = self.make_layout(tmp)
                    rel = "README.md"
                    text = self.read(root, rel)
                    broken = text.replace(
                        "### Comate", "### Comate route")
                    broken += plant
                    self.write(root, rel, broken)
                    problems = self.problems(root)
                    self.assertFalse(
                        any("no Comate install subsection" in p
                            for p in problems),
                        problems,
                    )
        comate_doc = " ".join(
            self.mod.comate_subsection_stands.__doc__.split())
        for phrase in (
            "a tab in the gap after a marker counting "
            "to the next multiple of four columns and "
            "not as one character",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, comate_doc)

    def test_a_comate_heading_after_a_lone_tag_past_the_finisher_wide_gap_items_does_not_stand(self):
        # The lane 11 Comate Minor standing on its new
        # root. Two tabs in the gap after a marker count
        # to eight columns in the reader its column walk,
        # while the renderer gives a gap of five columns
        # or more as one space and stands the content
        # one column past the marker end, so renewals at
        # two to five columns are item paragraphs in the
        # rendering and renewals at four and at two
        # columns escaped the reader whole as indented
        # code. The reader now counts a wide gap the
        # rendered way. Each plant was checked against
        # the CommonMark reference renderer across the
        # renewal band, renewals at two to five columns
        # rendering no heading and renewals at six
        # columns and past it rendering the heading, and
        # the six column renewal stands below as the
        # control in the other direction.
        for plant in (
            "\n-\t\titem one\n\n    para in item\n"
            "lazy line\n<span>\n### Comate\n",
            "\n-\t\titem one\n\n  para in item\n"
            "lazy line\n<span>\n### Comate\n",
        ):
            with self.subTest(plant=plant):
                with tempfile.TemporaryDirectory() as tmp:
                    root = self.make_layout(tmp)
                    rel = "README.md"
                    text = self.read(root, rel)
                    broken = text.replace(
                        "### Comate", "### Comate route")
                    broken += plant
                    self.write(root, rel, broken)
                    problems = self.problems(root)
                    self.assertTrue(
                        any("no Comate install subsection" in p
                            for p in problems),
                        problems,
                    )
        for plant in (
            "\n-\t\titem one\n\n      para in item\n"
            "lazy line\n<span>\n### Comate\n",
        ):
            with self.subTest(plant=plant):
                with tempfile.TemporaryDirectory() as tmp:
                    root = self.make_layout(tmp)
                    rel = "README.md"
                    text = self.read(root, rel)
                    broken = text.replace(
                        "### Comate", "### Comate route")
                    broken += plant
                    self.write(root, rel, broken)
                    problems = self.problems(root)
                    self.assertFalse(
                        any("no Comate install subsection" in p
                            for p in problems),
                        problems,
                    )
        comate_doc = " ".join(
            self.mod.comate_subsection_stands.__doc__.split())
        for phrase in (
            "a gap of five columns or more after a "
            "marker counting as one space",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, comate_doc)

    def test_a_comate_heading_after_a_lone_tag_past_a_closed_block_stands(self):
        # The lane 8 standards Note on the stale lazy fact,
        # renderer proven in that seat. A comment block in
        # its one line and multiline forms and a fenced
        # block standing outside the item close the item
        # in the rendering, so the paragraph line after
        # one is a paragraph of the outer document, the
        # lone tag cannot interrupt it, and the heading
        # after it renders and stands, beside the priced
        # lazy shape in the other direction in the lane 8
        # list lazy test.
        for plant in (
            "\n- item one\n<!-- c -->\npara line\n"
            "<span>\n### Comate\n",
            "\n- item one\n<!-- start\nend -->\n"
            "para line\n<span>\n### Comate\n",
            "\n- item one\n```\ncode\n```\npara line\n"
            "<span>\n### Comate\n",
        ):
            with self.subTest(plant=plant):
                with tempfile.TemporaryDirectory() as tmp:
                    root = self.make_layout(tmp)
                    rel = "README.md"
                    text = self.read(root, rel)
                    broken = text.replace(
                        "### Comate", "### Comate route")
                    broken += plant
                    self.write(root, rel, broken)
                    problems = self.problems(root)
                    self.assertFalse(
                        any("no Comate install subsection" in p
                            for p in problems),
                        problems,
                    )
        comate_doc = " ".join(
            self.mod.comate_subsection_stands.__doc__.split())
        self.assertIn(
            "whether a list item paragraph stands open "
            "for a lazy continuation", comate_doc)

    def test_a_comate_heading_after_the_lane6_block_controls_stands(self):
        # The controls in the other direction, checked
        # against the same renderer. A paragraph standing
        # outside the list after the item its paragraph
        # reopens the paragraph the lone tag cannot
        # interrupt, and a heading line standing after a
        # blockquote line is a heading of the document and
        # not a lazy continuation, so the heading after
        # each of them renders and stands.
        for plant in (
            "\n- item one\n\n  para in item\n\n"
            "outside para\n<span>\n### Comate\n",
            "\n> quoted text\n### Comate\n",
        ):
            with self.subTest(plant=plant):
                with tempfile.TemporaryDirectory() as tmp:
                    root = self.make_layout(tmp)
                    rel = "README.md"
                    text = self.read(root, rel)
                    broken = text.replace(
                        "### Comate", "### Comate route")
                    broken += plant
                    self.write(root, rel, broken)
                    problems = self.problems(root)
                    self.assertFalse(
                        any("no Comate install subsection" in p
                            for p in problems),
                        problems,
                    )

    def test_a_comate_heading_after_the_discharged_lone_tag_shapes_stands(self):
        # The discharged shapes in the other direction,
        # beside the lane 4 controls. A split lone tag is
        # inline text in a paragraph in the rendering, and a
        # lone tag after a table line or a link reference
        # definition stands inside a paragraph the tag
        # cannot interrupt, so the heading after each of
        # them renders and stands, as the reference renderer
        # shows for all three.
        for plant in (
            "\n<span\n>\n### Comate\n",
            "\n| a | b |\n<span>\n### Comate\n",
            "\n[ref]: /docs\n<span>\n### Comate\n",
        ):
            with self.subTest(plant=plant):
                with tempfile.TemporaryDirectory() as tmp:
                    root = self.make_layout(tmp)
                    rel = "README.md"
                    text = self.read(root, rel)
                    broken = text.replace(
                        "### Comate", "### Comate route")
                    broken += plant
                    self.write(root, rel, broken)
                    problems = self.problems(root)
                    self.assertFalse(
                        any("no Comate install subsection" in p
                            for p in problems),
                        problems,
                    )

    def test_a_comate_heading_after_a_lone_tag_block_stands(self):
        # The block a lone tag opens runs to a blank line, so
        # a real heading after the blank line renders and
        # stands, and a heading standing as a list item its
        # own content renders and stands beside it.
        for plant in (
            '\n<a name="comate">\n\n### Comate\n',
            "\n<?pi ?>\n\n### Comate\n",
            "\n- ### Comate\n",
        ):
            with self.subTest(plant=plant):
                with tempfile.TemporaryDirectory() as tmp:
                    root = self.make_layout(tmp)
                    rel = "README.md"
                    text = self.read(root, rel)
                    broken = text.replace(
                        "### Comate", "### Comate route")
                    broken += plant
                    self.write(root, rel, broken)
                    problems = self.problems(root)
                    self.assertFalse(
                        any("no Comate install subsection" in p
                            for p in problems),
                        problems,
                    )

    def test_a_comate_heading_after_an_indented_closing_fence_does_not_stand(self):
        # A rendered fence closes on at most three spaces of
        # indent, so a closing line indented four spaces
        # leaves the heading inside the fence.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "README.md"
            text = self.read(root, rel)
            broken = text.replace("### Comate", "### Comate route")
            broken += "\n```\ncode\n    ```\n### Comate\n```\n"
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("no Comate install subsection" in p
                    for p in problems),
                problems,
            )

    def test_a_comate_heading_indented_by_a_space_and_a_tab_does_not_stand(self):
        # The tab carries the indent to the fourth column, so
        # the rendered line is an indented code block even
        # though only one space stands before the tab.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "README.md"
            text = self.read(root, rel)
            broken = text.replace("### Comate", "### Comate route")
            broken += "\n\n \t### Comate\n"
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("no Comate install subsection" in p
                    for p in problems),
                problems,
            )

    def test_a_comate_heading_with_a_wide_separator_stands(self):
        # The conservative sibling shapes. A rendered heading
        # allows more than one space after the hash marks and
        # a tab as the separator, so both spellings stand.
        for heading in ("###  Comate\n", "###\tComate\n"):
            with self.subTest(heading=heading):
                with tempfile.TemporaryDirectory() as tmp:
                    root = self.make_layout(tmp)
                    rel = "README.md"
                    text = self.read(root, rel)
                    broken = text.replace("### Comate\n", heading)
                    self.assertNotEqual(broken, text)
                    self.write(root, rel, broken)
                    problems = self.problems(root)
                    self.assertFalse(
                        any("no Comate install subsection" in p
                            for p in problems),
                        problems,
                    )

    def test_a_comate_heading_after_a_backtick_info_line_stands(self):
        # A backtick fence line whose info string carries a
        # backtick is no fence at all, so the heading after
        # one stands in the rendered document.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "README.md"
            text = self.read(root, rel)
            broken = text.replace("### Comate", "### Comate route")
            broken += "\n```foo`bar\n### Comate\n"
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertFalse(
                any("no Comate install subsection" in p
                    for p in problems),
                problems,
            )

    def test_a_closed_atx_comate_heading_stands(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "README.md"
            text = self.read(root, rel)
            broken = text.replace("### Comate\n", "### Comate ##\n")
            self.assertNotEqual(broken, text)
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertFalse(
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


class TestRound5Comate(unittest.TestCase):
    def setUp(self):
        self.inner = TestCheckComate()
        self.inner.setUp()
        self.mod = self.inner.mod

    def test_a_restated_tool_figure_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.read(root, "docs/comate-brief.md")
            broken = text.replace(
                "recognition of over 20 tools including",
                "recognition of over 30 tools including", 1)
            self.assertNotEqual(broken, text)
            self.inner.write(root, "docs/comate-brief.md", broken)
            problems = self.inner.problems(root)
            self.assertTrue(any(
                "over 30 tools" in p and "over 20 tools" in p
                for p in problems), problems)


class TestRound5SecondSeatComate(unittest.TestCase):
    def setUp(self):
        self.inner = TestCheckComate()
        self.inner.setUp()
        self.mod = self.inner.mod

    def test_glance_client_version_moved_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            rel = "docs/comate-brief.md"
            text = self.inner.read(root, rel)
            broken = text.replace(
                "at version 3.11.5 downloaded", "at version "
                "3.11.6 downloaded", 1)
            self.assertNotEqual(broken, text)
            self.inner.write(root, rel, broken)
            problems = self.inner.problems(root)
            self.assertTrue(any(
                "At a glance restates the client version as "
                "3.11.6" in p for p in problems), problems)


class TestRepairPassFourComate(unittest.TestCase):
    def setUp(self):
        self.inner = TestCheckComate()
        self.inner.setUp()
        self.mod = self.inner.mod

    def test_glance_client_version_in_digit_form_fails(self):
        # Repair pass four. The glance reading checked
        # only the at version form, so the same restated
        # version standing in the glance as a bare digit
        # form passed beside the pinned statement. Every
        # version token in the glance is now value checked.
        # Repair pass five. The plant lands through a
        # whitespace normalised pattern in the form the
        # sibling break helpers use, so a pure rewrap of
        # the shipped paragraph leaves the plant landing
        # instead of leaving it nothing to land on.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            rel = "docs/comate-brief.md"
            text = self.inner.read(root, rel)
            pattern = re.escape(
                "The editor command line in the client "
                "bundle reports the same version."
            ).replace("\\ ", "\\s+")
            broken, hits = re.subn(
                pattern,
                lambda _match: (
                    "The editor command line in the client "
                    "bundle reports 3.12.0."
                ),
                text, count=1)
            self.assertTrue(hits > 0)
            self.assertNotEqual(broken, text)
            self.inner.write(root, rel, broken)
            problems = self.inner.problems(root)
            self.assertTrue(any(
                "At a glance restates the client version "
                "as 3.12.0" in p for p in problems), problems)

    def test_installer_record_version_restated_fails(self):
        # Repair pass four. The installer record form of
        # the client version is value checked over the
        # whole brief, so an added statement restating it
        # with a moved version refuses beside the pin.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            rel = "docs/comate-brief.md"
            text = self.inner.read(root, rel)
            planted = text + (
                "\n\nThe official Linux installer record "
                "names Comate AI IDE 3.12.0 for linux x64.\n")
            self.inner.write(root, rel, planted)
            problems = self.inner.problems(root)
            self.assertTrue(any(
                "client version as 3.12.0" in p
                and "installer record form" in p
                for p in problems), problems)

    def test_command_line_version_restated_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            rel = "docs/comate-brief.md"
            text = self.inner.read(root, rel)
            planted = text + (
                "\n\nThe editor command line reports "
                "3.12.0.\n")
            self.inner.write(root, rel, planted)
            problems = self.inner.problems(root)
            self.assertTrue(any(
                "client version as 3.12.0" in p
                and "command line form" in p
                for p in problems), problems)

    def test_client_version_true_forms_hold(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            rel = "docs/comate-brief.md"
            text = self.inner.read(root, rel)
            planted = text + (
                "\n\nThe official Linux installer record "
                "names Comate AI IDE 3.11.5 for linux x64. "
                "The editor command line reports 3.11.5.\n")
            self.inner.write(root, rel, planted)
            problems = self.inner.problems(root)
            self.assertFalse(any(
                "client version" in p for p in problems),
                problems)


class TestRepairPassFiveComate(unittest.TestCase):
    def setUp(self):
        self.inner = TestCheckComate()
        self.inner.setUp()
        self.mod = self.inner.mod

    def plant_brief(self, root, suffix):
        rel = "docs/comate-brief.md"
        text = self.inner.read(root, rel)
        self.inner.write(root, rel, text + suffix)
        return self.inner.problems(root)

    def test_command_line_bundle_version_restated_fails(self):
        # Repair pass five. The command line form read
        # the contiguous form only, so the shipped glance
        # sentence shape with the client bundle words
        # standing before its reports word passed outside
        # the glance with a moved figure in place of its
        # same version words. That shape is a command line
        # form in the whole brief check now.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            problems = self.plant_brief(
                root,
                "\n\nThe editor command line in the client "
                "bundle reports 3.12.0.\n")
            self.assertTrue(any(
                "client version as 3.12.0" in p
                and "command line form" in p
                for p in problems), problems)

    def test_installer_record_version_word_form_fails(self):
        # Repair pass five. The installer record form
        # read the figure standing straight after the IDE
        # name only, so a statement carrying the word
        # version inside the installer sentence passed.
        # That carrying word stands in the form now.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            problems = self.plant_brief(
                root,
                "\n\nThe official Linux installer record "
                "names Comate AI IDE version 3.12.0 for "
                "linux x64.\n")
            self.assertTrue(any(
                "client version as 3.12.0" in p
                and "installer record form" in p
                for p in problems), problems)

    def test_at_version_form_outside_glance_fails(self):
        # Repair pass five. The at version form was value
        # checked inside the glance alone, so the same
        # client version statement standing at the end of
        # the brief passed beside the pinned statement.
        # The form is value checked over the whole brief
        # now.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            problems = self.plant_brief(
                root,
                "\n\nThe official Linux client at version "
                "3.12.0 downloaded from the installer "
                "record.\n")
            self.assertTrue(any(
                "client version as 3.12.0" in p
                and "at version form" in p
                for p in problems), problems)


if __name__ == "__main__":
    unittest.main()

