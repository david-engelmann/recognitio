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


if __name__ == "__main__":
    unittest.main()
