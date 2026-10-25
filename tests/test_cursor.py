"""Build 10, the Cursor plugin.

The brief at docs/cursor-plugin-brief.md exploits the Cursor
Plugin manifest, the six component packaging rules, the Bugbot
rules in .cursor/BUGBOT.md, and the .cursor/config/bugbot.yaml
repo config. These tests prove the pin fires for a real reason
on every load bearing claim the round 22 lanes named. A
symlinked skill copy, a drifted skill copy, an unknown
bugbot.yaml field, a bad autofix mode, a variables schema
violation on the platform root, a dropped symlink pin, a
dropped neutral default, a dropped fail on unresolved, a
dropped effort split, a Bugbot rule without a derivation note,
a passing prose title mention, a version drift, an absolute
manifest path, and a decision record without a decision 4
statement each fail the Cursor gate.
"""

import importlib.util
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    path = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location("cursor_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestCheckCursor(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_cursor")

    def make_layout(self, tmp):
        """A scratch tree with the plugin, the brief, and the record."""
        root = Path(tmp) / "root"
        for rel in (
            "docs/cursor-plugin-brief.md",
            "docs/decisions.md",
            ".cursor-plugin/plugin.json",
            ".cursor-plugin/marketplace.json",
            ".cursor-plugin/rules/recognitio.mdc",
            ".cursor/BUGBOT.md",
            ".cursor/config/bugbot.yaml",
            ".claude-plugin/plugin.json",
        ):
            source = ROOT / rel
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        shutil.copytree(
            ROOT / ".cursor-plugin" / "skills" / "recognitio",
            root / ".cursor-plugin" / "skills" / "recognitio",
        )
        shutil.copytree(
            ROOT / ".agents" / "skills" / "recognitio",
            root / ".agents" / "skills" / "recognitio",
        )
        return root

    def problems(self, root):
        return self.mod.cursor_problems(root)

    def read_brief(self, root):
        return (root / "docs" / "cursor-plugin-brief.md").read_text(
            encoding="utf-8"
        )

    def write_brief(self, root, text):
        (root / "docs" / "cursor-plugin-brief.md").write_text(
            text, encoding="utf-8"
        )

    def break_brief(self, root, old, new, count=1):
        text = self.read_brief(root)
        pattern = re.escape(old).replace("\\ ", "\\s+")
        broken, hits = re.subn(
            pattern, lambda _match: new, text, count=count
        )
        self.assertNotEqual(broken, text)
        self.assertTrue(hits > 0)
        self.write_brief(root, broken)
        return self.problems(root)

    def read_manifest(self, root):
        return json.loads(
            (root / ".cursor-plugin" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )

    def write_manifest(self, root, data):
        (root / ".cursor-plugin" / "plugin.json").write_text(
            json.dumps(data), encoding="utf-8"
        )

    def test_the_shipped_tree_holds(self):
        self.assertEqual(self.mod.cursor_problems(ROOT), [])

    def test_the_scratch_layout_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            self.assertEqual(self.problems(root), [])

    def test_a_symlinked_skill_copy_fails(self):
        # R22-RT-01. The host skips a symlink that points at a
        # plugin repository elsewhere on disk, so the skill copy
        # must be real files.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            copy_dir = root / ".cursor-plugin" / "skills" / "recognitio"
            shutil.rmtree(copy_dir)
            copy_dir.symlink_to(
                root / ".agents" / "skills" / "recognitio",
                target_is_directory=True,
            )
            problems = self.problems(root)
            self.assertTrue(
                any("is a symlink" in p for p in problems), problems
            )

    def test_a_drifted_skill_copy_fails(self):
        # The standing guidance is never ship two separate copies
        # of the same skill. The plugin copy stays byte identical
        # to the canonical skill, and a drift fails the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            skill = (
                root
                / ".cursor-plugin"
                / "skills"
                / "recognitio"
                / "SKILL.md"
            )
            before = skill.read_bytes()
            skill.write_bytes(before + b"\nExtra line.\n")
            problems = self.problems(root)
            self.assertTrue(
                any("drifts from" in p for p in problems), problems
            )

    def test_an_unknown_bugbot_yaml_field_fails(self):
        # R22-RT-05. An unknown field falls back silently down the
        # precedence order, so the gate rejects it outright. The
        # effort field is the adversarial case, because a
        # secondary analysis claims it works while the primary
        # page documents no such field.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".cursor" / "config" / "bugbot.yaml"
            text = path.read_text(encoding="utf-8")
            broken = text + "effort: high\n"
            self.assertNotEqual(broken, text)
            path.write_text(broken, encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("unknown fields" in p for p in problems),
                problems,
            )

    def test_a_bad_autofix_mode_fails(self):
        # Only the autofix.mode values the primary page names are
        # allowed. An invented mode fails the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".cursor" / "config" / "bugbot.yaml"
            text = path.read_text(encoding="utf-8")
            broken = text.replace("mode: disabled", "mode: turbo", 1)
            self.assertNotEqual(broken, text)
            path.write_text(broken, encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("not a mode" in p for p in problems), problems
            )

    def test_a_dropped_symlink_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            broken = text.replace(
                "Cursor skips a\nsymlink that points to a plugin repository "
                "elsewhere on disk.",
                "Cursor handles symlinks however it likes.",
                1,
            )
            self.assertNotEqual(broken, text)
            self.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("symlink skip" in p for p in problems), problems
            )

    def test_a_dropped_neutral_pin_fails(self):
        # R22-RT-03. Without the neutral default sentence, a
        # later edit could read neutral as a pass.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            broken = text.replace(
                "this is\nthe default conclusion when Bugbot reports findings.",
                "this is one possible conclusion.",
                1,
            )
            self.assertNotEqual(broken, text)
            self.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("neutral default" in p for p in problems),
                problems,
            )

    def test_a_dropped_fail_on_unresolved_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            broken = text.replace(
                "enable it to\nmake unresolved findings produce a failing "
                "status.",
                "enable it to make findings nicer.",
                1,
            )
            self.assertNotEqual(broken, text)
            self.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("fail on unresolved" in p for p in problems),
                problems,
            )

    def test_a_dropped_effort_split_pin_fails(self):
        # R22-RT-02. Without the dashboard setting sentence, a
        # later edit could claim bugbot.yaml pins effort.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            broken = text.replace(
                "Bugbot Teams includes the ability to set the "
                "effort level Bugbot\nuses for reviews.",
                "Bugbot effort is configured wherever is handy.",
                1,
            )
            self.assertNotEqual(broken, text)
            self.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("effort dashboard setting" in p for p in problems),
                problems,
            )

    def test_a_variables_schema_violation_fails(self):
        # R22-RT-04. The platform provided root is exempt from
        # the variables schema checklist item, so declaring it
        # there fails the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["variables"] = {
                "CURSOR_PLUGIN_ROOT": {"type": "string"}
            }
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("exempt" in p for p in problems), problems
            )

    def test_a_bugbot_rule_without_a_derivation_note_fails(self):
        # The second packet guard, carried over from Build 9. A
        # Bugbot rule with no derivation note is a rival
        # instruction source.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".cursor" / "BUGBOT.md"
            text = path.read_text(encoding="utf-8")
            broken = text.replace(
                "Derives from canonical skill, The tier model, the T0 instruction\n"
                "file flag.",
                "No derivation is offered for this rule.",
                1,
            )
            self.assertNotEqual(broken, text)
            path.write_text(broken, encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("no derivation note" in p for p in problems),
                problems,
            )

    def test_a_passing_prose_title_mention_fails(self):
        # R21-ST-01, applied to the Bugbot rules. A note that
        # names a canonical section title in passing prose
        # without deriving from it must fail.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".cursor" / "BUGBOT.md"
            text = path.read_text(encoding="utf-8")
            broken = text.replace(
                "Derives from canonical skill, The tier model, the T0 instruction\n"
                "file flag.",
                "Derives from the primary blog post. It shapes the\n"
                "Workflow of the review and nothing else.",
                1,
            )
            self.assertNotEqual(broken, text)
            path.write_text(broken, encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "no canonical skill section" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_version_drift_fails(self):
        # Every surface that carries a version agrees, so a
        # Cursor manifest that drifted from the Claude manifest
        # fails the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["version"] = "9.9.9"
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("disagree" in p for p in problems), problems
            )

    def test_a_marketplace_only_version_drift_fails(self):
        # R23-ST-02. No committed test broke only the marketplace
        # listing. A marketplace entry that drifted from the
        # manifest must fail the gate through the marketplace
        # check alone, so deleting the marketplace version
        # comparison fails this test.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".cursor-plugin" / "marketplace.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["plugins"][0]["version"] = "9.9.9"
            path.write_text(json.dumps(data), encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "marketplace.json is at version" in p
                    for p in problems
                ),
                problems,
            )

    def test_an_absolute_manifest_path_fails(self):
        # All manifest paths must be relative with no parent
        # traversal and no absolute paths.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["skills"] = ["/etc/recognitio"]
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("not a relative path" in p for p in problems),
                problems,
            )

    def test_a_dropped_security_review_pin_fails(self):
        # R31-EX-03. The Build 10 brief pins the Security
        # Review separation, scope, team rules, draft skip,
        # and plan gate, plus the Origin launch path beside
        # the Cursor plugin path.
        cases = (
            ("Security Review is a separate bot from Bugbot",
             "Security Review separation"),
            ("injection across SQL, command, and template surfaces",
             "Security Review scope"),
            ("enforces them on every pull request",
             "Security Review team rules"),
            ("Draft pull requests are skipped",
             "Security Review draft skip"),
            ("gated to Teams and Enterprise plans",
             "Security Review plan gate"),
            ("built in review-security skill",
             "review-security skill"),
            ("Origin App Marketplace launched October 13 2026",
             "Origin launch path"),
            ("not the only CodeRabbit in Cursor path",
             "Origin not only plugin path"),
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

    def test_a_decision_record_without_decision_4_fails(self):
        # Every landed build records a decision 4 statement. A
        # Build 10 record without one fails the pin.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / "docs" / "decisions.md"
            text = path.read_text(encoding="utf-8")
            start = text.find("## 19. Build 10")
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


    def test_cap_figure_and_bugbot_control_plants_fail(self):
        # R36-RT-03. A repository cap figure stated alone,
        # a bugbot.yaml effort pin, and a merge blocking
        # neutral conclusion each passed while the pins
        # stayed in place, because no check read a
        # contradicting brief sentence.
        cases = (
            ("A cloud agent environment supports up to 500 "
             "repositories.", "cap figure of 500"),
            ("A cloud agent environment supports up to 300 "
             "repositories.", "cap figure of 300"),
            ("Bugbot effort can be pinned at High in "
             "bugbot.yaml for this repository.",
             "pins Bugbot effort"),
            ("A neutral Bugbot conclusion blocks merges on "
             "findings.", "neutral Bugbot conclusion"),
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

    def test_a_cap_figure_with_the_conflict_note_passes(self):
        # R36-RT-03. A cap figure stated with the R35-C-01
        # conflict named beside it in the same sentence is
        # the one allowed form, so it passes.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root,
                text + "\n\nOne primary page supports up to "
                "500 repositories and another states 300, "
                "and the conflict stands unresolved.\n",
            )
            self.assertEqual(self.problems(root), [])

    def test_gate_review_cursor_restated_plants_fail(self):
        # Gate review repair. The first cap branch needed a
        # bounding verb and exempted a sentence naming both
        # figures, the effort branch read a 50 character
        # window and three pin verbs, and the neutral branch
        # read one verb form, so the review restated every
        # plant just outside those shapes and each passed.
        cases = (
            ("A cloud agent environment has 500 "
             "repositories.", "cap figure of 500"),
            ("Cloud agent environments get 500 repositories "
             "each.", "cap figure of 500"),
            ("A cloud agent environment supports up to five "
             "hundred repositories.",
             "cap figure of five hundred"),
            ("A cloud agent environment supports up to 500 "
             "repositories, while another page says 300 "
             "repositories.", "cap figure of 500"),
            ("The bugbot.yaml file controls Bugbot effort "
             "for this repository.", "pins Bugbot effort"),
            ("Bugbot effort for this repository, across all "
             "reviews and all teams in the organization, can "
             "be pinned in bugbot.yaml.",
             "pins Bugbot effort"),
            ("A neutral Bugbot conclusion stops merges on "
             "findings.", "neutral Bugbot conclusion"),
            ("A neutral Bugbot conclusion blocked merges on "
             "findings.", "neutral Bugbot conclusion"),
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

    def test_gate_review_cursor_cannot_control_passes(self):
        # Gate review repair. The effort guard read the
        # words not and never, so the same true sentence
        # with cannot in place of never failed the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root,
                text + "\n\nEffort cannot be pinned in "
                "bugbot.yaml, because effort is a dashboard "
                "setting only.\n",
            )
            self.assertEqual(self.problems(root), [])

    def test_round37_neutral_conclusion_split_across_sentences_fails(self):
        # R37-RT-06. The pronoun carries the neutral
        # conclusion into a second sentence that holds the
        # blocking verb, and the pair reading must catch it.
        plant = (
            "Bugbot findings default to a neutral "
            "conclusion. That conclusion blocks merges in "
            "this repository."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "neutral Bugbot conclusion blocking" in p
                    for p in problems
                ),
                problems,
            )

    def test_round37_cap_figure_past_the_reach_fails(self):
        # R37-RT-06 and R35-C-01. Filler between the figure
        # and the word repositories no longer shelters a
        # cap figure stated without the conflict note.
        plant = (
            "A cloud agent environment supports up to 500 "
            "carefully counted and individually tracked "
            "repositories in this workspace."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "repository cap figure of 500" in p
                    for p in problems
                ),
                problems,
            )

    def test_round37_effort_pin_past_the_reach_fails(self):
        # R37-RT-06. The effort pin stated across a long
        # dashboard filler must fail at sentence scope.
        plant = (
            "Bugbot effort, as a dashboard value that the "
            "workspace admin reviews each quarter alongside "
            "the other review choices for this repository "
            "and its sibling projects in the same "
            "organisation and its partner teams abroad, is "
            "pinned in bugbot.yaml."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "pins Bugbot effort in bugbot.yaml" in p
                    for p in problems
                ),
                problems,
            )


    def test_round37_grouped_cap_figure_is_named_in_full(self):
        # Gate review repair. A comma grouped figure binds
        # as one figure, so the problem names 100,000 and
        # not the truncated 100 the digit run alone reads.
        plant = (
            "A cloud agent environment supports up to "
            "100,000 repositories in this workspace."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "repository cap figure of 100,000" in p
                    for p in problems
                ),
                problems,
            )

    def test_round37_fixreview_unit_word_in_parenthetical_fails(self):
        # R37F-RT-07. A unit word inside a parenthetical
        # after the figure does not rebind it, because the
        # figure's unit position stands empty, so the cap
        # figure still binds to repositories.
        plant = (
            "A cloud agent environment supports up to 500, "
            "counting files separately, repositories in "
            "this workspace."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "repository cap figure of 500" in p
                    for p in problems
                ),
                problems,
            )

    def test_round37_fixreview_idle_negation_does_not_guard(self):
        # R37F-RT-08. A negation joined to the blocking
        # verb by a coordinating and modifies the earlier
        # verb, so the neutral conclusion blocking merges
        # still fails.
        plant = (
            "Bugbot findings default to a neutral "
            "conclusion. That conclusion never sits idle "
            "and blocks merges in this repository."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "conclusion blocking merges" in p
                    for p in problems
                ),
                problems,
            )

    def test_round37_fixreview_effort_in_another_clause_passes(self):
        # R37F-RT-09. Effort in one coordinating unit and
        # a pin verb in the next state no pin, so the true
        # sentence must pass.
        sentence = (
            "Bugbot effort is a dashboard setting, and the "
            "autofix mode is pinned in bugbot.yaml."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root, text + "\n\n" + sentence + "\n"
            )
            self.assertEqual(self.problems(root), [])

    def test_round37_fixreview_count_of_another_noun_passes(self):
        # R37F-RT-09. A figure followed directly by its own
        # count noun binds to that noun, so a workspace
        # listing 500 issues across its repositories
        # states no repository cap figure and must pass.
        sentence = (
            "The workspace lists 500 issues across its "
            "repositories."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root, text + "\n\n" + sentence + "\n"
            )
            self.assertEqual(self.problems(root), [])

    def test_round37_confirm2_neutral_comma_splice_fails(self):
        # R37C-RT-04. A comma splice joins the verbs the
        # same way a coordinating and does, so a negation
        # before the comma modifies the earlier verb and
        # does not guard the blocking verb.
        plant = (
            "Bugbot findings default to a neutral "
            "conclusion. That conclusion never sits idle, "
            "blocks merges in this repository."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any("neutral" in p for p in problems), problems
            )

    def test_round37_confirm2_effort_plain_and_units_pass(self):
        # R37C-RT-05. A comma free sentence joins its
        # units with the plain joint alone, so effort in
        # one unit and a pin verb in the next state no pin
        # and the true sentence passes.
        plant = (
            "Bugbot effort is a dashboard setting and the "
            "autofix mode is pinned in bugbot.yaml."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertFalse(
                any("effort" in p for p in problems), problems
            )

    def test_round37_confirm2_cap_parenthetical_behind_fails(self):
        # Unnumbered confirmation shape. A unit word in a
        # parenthetical between the target and its figure
        # is not in the figure unit position behind the
        # target either, so the cap figure still binds.
        plant = (
            "Repositories in this workspace, counting files "
            "separately, number 500 in this environment."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "repository cap figure of 500" in p
                    for p in problems
                ),
                problems,
            )


    def test_round38_neutral_split_across_three_sentences_fails(self):
        # R38-RT-05. The neutral claim split across three
        # sentences with a filler between the halves stands
        # in no pair, and the paragraph scope reading must
        # catch it.
        plant = (
            "Bugbot findings default to a neutral "
            "conclusion. The packet lists each finding "
            "beside its diff. That conclusion blocks "
            "merges in this repository."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "neutral Bugbot conclusion blocking" in p
                    for p in problems
                ),
                problems,
            )

    def test_round38_neutral_semicolon_negation_does_not_guard(self):
        # R38-RT-06. A negation before a semicolon modifies
        # the earlier verb alone, so the blocking claim
        # after the semicolon still fails.
        plant = (
            "Bugbot findings default to a neutral "
            "conclusion. That conclusion never sits idle; "
            "blocks merges in this repository."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "neutral Bugbot conclusion blocking" in p
                    for p in problems
                ),
                problems,
            )

    def test_gate_round38_cli_attempt_note_pins_hold(self):
        # Round 38 CLI attempt note. Dropping any of the
        # amended note sentences fails the gate, so the
        # CLI surface record cannot quietly soften back
        # into the blocked API attempt wording or grow a
        # desktop claim the attempt never observed.
        fragments = (
            "no session included a recognitio plugin manifest",
            "the entry pointed at the .claude/skills spelling "
            "of the canonical skill",
            "the plugin tree copy never appeared as a skill "
            "entry in any session",
            "no claim in this note rests on a skill count",
            "no session named the plugin rule file or "
            "BUGBOT.md as in effect on that surface",
        )
        for fragment in fragments:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                problems = self.break_brief(
                    root, fragment, "the record omits this"
                )
                self.assertTrue(problems, fragment)

    def test_desktop_verification_pins_hold(self):
        # Desktop verification of 2026-10-25. Dropping any
        # of the settled desktop sentences fails the gate,
        # so the brief cannot drift back to carrying the
        # desktop questions as open once the real client
        # run answered them. The precedence fragment that
        # stood here moved to the CLI precedence pins,
        # because the CLI run settled that question on its
        # surface later the same day.
        fragments = (
            "The duplicate skill residual is settled at the "
            "level of desktop registration",
            "the official Cursor desktop build 3.27.12 for "
            "Linux ran here under a virtual display",
            "recorded the recognitio plugin loaded with zero "
            "failures five times in the first launch",
            "every recorded load happened before any "
            "sign-in",
            "the Customize backing records, which list a "
            "skill entry and a rule entry pointing at the "
            "local plugin copies",
            "the Customize backing records held two "
            "recognitio skill entries side by side",
            "the desktop deduped neither entry",
            "Marketplace installation from a listing and "
            "Bugbot behaviour on a real pull request stay "
            "UNVERIFIED",
        )
        for fragment in fragments:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                problems = self.break_brief(
                    root, fragment, "the record omits this"
                )
                self.assertTrue(problems, fragment)

    def test_the_superseded_desktop_sentences_fail(self):
        # Desktop verification of 2026-10-25. Each pre run
        # sentence the desktop evidence falsified or
        # discharged fails the gate when planted back,
        # because the positive pins alone would let a
        # restored stale sentence ride beside them.
        plants = (
            "This box has no Cursor client, so the real "
            "client run is owed.",
            "The local simulation of the documented rule in "
            "this round's gate is the evidence that stands "
            "in until that run happens.",
            "Cursor plugin load behaviour in the desktop "
            "client stays UNVERIFIED.",
            "Duplicate skill behaviour on the Cursor agent "
            "CLI surface was observed in round 38 and stays "
            "UNVERIFIED for the desktop client.",
            "The duplicate skill residual stays UNVERIFIED "
            "at primary, and the standing guidance is "
            "unchanged.",
            "The real desktop client run remains owed under "
            "the protocol in this brief.",
        )
        for plant in plants:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                text = self.read_brief(root)
                self.write_brief(root, text + "\n\n" + plant + "\n")
                problems = self.problems(root)
                self.assertTrue(
                    any("stale" in p for p in problems),
                    (plant, problems),
                )

    def test_cli_precedence_pins_hold(self):
        # CLI precedence run of 2026-10-25. Dropping any
        # of the settled precedence sentences fails the
        # gate, so the brief cannot drift back to carrying
        # invocation precedence as open on every surface
        # once the live CLI sessions answered it.
        fragments = (
            "Invocation precedence is settled on the agent "
            "CLI surface",
            "stays open on the desktop client alone",
            "two in the shipped state and two in the "
            "duplicate state",
            "a distinct marker line appended to each copy "
            "of the skill",
            "installed at .cursor/plugins/local/recognitio "
            "in the session home",
            "each session invoked the workspace copy at "
            "the .claude/skills/recognitio/SKILL.md "
            "spelling",
            "registered as a second entry and was never "
            "invoked",
            "each session invoked the added copy at "
            ".cursor/skills/recognitio/SKILL.md",
            "took the workspace seat outright while the "
            ".claude spelling entry left the catalog",
            "The repo root plugin tree at .cursor-plugin "
            "appeared as an entry in no session",
            "no signed-in desktop session could be landed "
            "on this box",
            "login-session poll never received a completed "
            "sign-in across the original run and the "
            "repaired relaunch",
            "the evidence stands in the desktop "
            "precedence report and the sign-in repair "
            "report",
        )
        for fragment in fragments:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                problems = self.break_brief(
                    root, fragment, "the record omits this"
                )
                self.assertTrue(problems, fragment)

    def test_the_superseded_precedence_sentence_fails(self):
        # CLI precedence run of 2026-10-25. The open
        # precedence sentence the run superseded fails the
        # gate when planted back, because the positive
        # pins alone would let a restored stale sentence
        # ride beside them.
        plant = (
            "Invocation precedence stays open, because both "
            "copies register with no precedence field in "
            "the Customize data and a live agent session "
            "requires a sign-in the run did not perform."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any("stale" in p for p in problems),
                (plant, problems),
            )

    def test_gate_round38_neutral_split_across_paragraphs_fails(self):
        # R38G-RT-04. The neutral claim split across a
        # paragraph break inside one block stands in no
        # paragraph window, and the claim scope reading
        # must catch it.
        plant = (
            "Bugbot findings default to a neutral "
            "conclusion. The packet lists each finding "
            "beside its diff.\n\n"
            "That conclusion blocks merges in this "
            "repository."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "neutral Bugbot conclusion blocking" in p
                    for p in problems
                ),
                problems,
            )

    def test_gate_round38_cap_split_across_paragraphs_fails(self):
        # R38G-RT-04. The cap figure and the repositories
        # it counts split across a paragraph break inside
        # one block state one cap claim, and the claim
        # scope pair reading must catch it.
        plant = (
            "A cloud agent environment supports up to 500 "
            "in this workspace.\n\n"
            "Those are repositories counted across every "
            "team in the organisation."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "repository cap figure of 500" in p
                    for p in problems
                ),
                problems,
            )

    def test_round38_cap_split_across_two_sentences_fails(self):
        # R38-RT-07. The cap figure in one sentence and the
        # repositories it counts named in the next, carried
        # by a deictic opening, state one cap claim with no
        # conflict note beside it.
        plant = (
            "A cloud agent environment supports up to 500 "
            "in this workspace. Those are repositories "
            "counted across every team in the organisation."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "repository cap figure of 500" in p
                    for p in problems
                ),
                problems,
            )


if __name__ == "__main__":
    unittest.main()
