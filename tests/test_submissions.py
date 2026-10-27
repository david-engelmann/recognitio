"""Top 20 item 19, the submission packs gate script.

The script at scripts/check_submissions.py pins the three
submission packs and the manifest facts their evidence checks
rest on. These tests prove the pin fires for a real reason on
every load bearing claim. A pack that drops its unsubmitted
sentence, its read date, its route, or its owner act section,
a pack that claims a filed listing, a manifest that loses a
fact a pack asserts, a portable manifest that leaves the
closed field set of its specification, and a version bump the
packs do not follow each fail the gate.
"""

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FILES = (
    "docs/submission-cursor.md",
    "docs/submission-claude.md",
    "docs/submission-agent-plugins.md",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    ".cursor-plugin/plugin.json",
    ".cursor-plugin/marketplace.json",
    ".cursor-plugin/skills/recognitio/SKILL.md",
    ".cursor-plugin/rules/recognitio.mdc",
    "agent-plugins-package/plugin.json",
    "agent-plugins-package/skills/recognitio/SKILL.md",
    "docs/brand/recognitio-icon.svg",
    "docs/brand/recognitio-icon-512.png",
    "LICENSE",
)

CURSOR_PACK = "docs/submission-cursor.md"
CLAUDE_PACK = "docs/submission-claude.md"
PORTABLE_PACK = "docs/submission-agent-plugins.md"
CLAUDE_PLUGIN = ".claude-plugin/plugin.json"
CLAUDE_MARKET = ".claude-plugin/marketplace.json"
CURSOR_MARKET = ".cursor-plugin/marketplace.json"
PORTABLE = "agent-plugins-package/plugin.json"


def load_script(name):
    path = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(
        "submissions_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestCheckSubmissions(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_submissions")

    def make_layout(self, tmp):
        root = Path(tmp) / "root"
        for rel in FILES:
            source = ROOT / rel
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        return root

    def problems(self, root):
        return self.mod.submissions_problems(root)

    def read_json(self, root, rel):
        return json.loads((root / rel).read_text(encoding="utf-8"))

    def write_json(self, root, rel, data):
        (root / rel).write_text(json.dumps(data), encoding="utf-8")

    def mutate_json(self, rel, change):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_json(root, rel)
            change(data)
            self.write_json(root, rel, data)
            return self.problems(root)

    def mutate_text(self, rel, change):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / rel
            path.write_text(
                change(path.read_text(encoding="utf-8")),
                encoding="utf-8")
            return self.problems(root)

    def test_the_shipped_tree_holds(self):
        self.assertEqual(self.mod.submissions_problems(ROOT), [])

    def test_the_scratch_layout_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            self.assertEqual(self.problems(root), [])

    def test_a_missing_pack_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            (root / CURSOR_PACK).unlink()
            problems = self.problems(root)
            self.assertTrue(
                any("missing" in p for p in problems), problems)

    def test_a_dropped_unsubmitted_sentence_fails(self):
        problems = self.mutate_text(
            CURSOR_PACK,
            lambda t: t.replace(
                "Nothing in this pack has been submitted.", ""))
        self.assertTrue(
            any("has been submitted" in p for p in problems),
            problems)

    def test_a_dropped_read_date_fails(self):
        problems = self.mutate_text(
            CLAUDE_PACK,
            lambda t: t.replace("on 2026-10-27.", "recently."))
        self.assertTrue(
            any("2026-10-27" in p for p in problems), problems)

    def test_a_dropped_route_fails(self):
        problems = self.mutate_text(
            CLAUDE_PACK,
            lambda t: t.replace(
                "claude.ai/directory/manage", "the portal"))
        self.assertTrue(
            any("directory/manage" in p for p in problems),
            problems)

    def test_a_dropped_owner_act_section_fails(self):
        problems = self.mutate_text(
            PORTABLE_PACK,
            lambda t: t.replace(
                "## What remains David's act",
                "## What remains"))
        self.assertTrue(
            any("David's act" in p for p in problems), problems)

    def test_a_dropped_no_directory_sentence_fails(self):
        problems = self.mutate_text(
            PORTABLE_PACK,
            lambda t: t.replace(
                "The Agent Plugins project runs no directory "
                "of packages.",
                "The project directory question is open."))
        self.assertTrue(
            any("no directory" in p for p in problems), problems)

    def test_a_filed_listing_claim_fails(self):
        problems = self.mutate_text(
            CURSOR_PACK,
            lambda t: t + "\nThe listing is live.\n")
        self.assertTrue(
            any("listing is live" in p for p in problems),
            problems)

    def test_a_version_bump_the_packs_do_not_follow_fails(self):
        def change(d):
            d["version"] = "1.4.0"
        problems = self.mutate_json(CLAUDE_PLUGIN, change)
        self.assertTrue(
            any("1.4.0" in p for p in problems), problems)

    def test_a_cursor_owner_loss_fails(self):
        def change(d):
            d.pop("owner")
        problems = self.mutate_json(CURSOR_MARKET, change)
        self.assertTrue(
            any("owner" in p for p in problems), problems)

    def test_a_second_cursor_entry_fails(self):
        def change(d):
            extra = dict(d["plugins"][0])
            extra["name"] = "recognitio-copy"
            d["plugins"] = d["plugins"] + [extra]
        problems = self.mutate_json(CURSOR_MARKET, change)
        self.assertTrue(
            any("exactly one" in p for p in problems), problems)

    def test_a_claude_author_loss_fails(self):
        def change(d):
            d.pop("author")
        problems = self.mutate_json(CLAUDE_PLUGIN, change)
        self.assertTrue(
            any("author" in p for p in problems), problems)

    def test_a_claude_entry_name_drift_fails(self):
        def change(d):
            d["plugins"][0]["name"] = "recognitio-copy"
        problems = self.mutate_json(CLAUDE_MARKET, change)
        self.assertTrue(
            any("does not match" in p for p in problems),
            problems)

    def test_a_license_file_loss_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            (root / "LICENSE").unlink()
            problems = self.problems(root)
            self.assertTrue(
                any("LICENSE" in p for p in problems), problems)

    def test_an_eleventh_portable_field_fails(self):
        def change(d):
            d["displayName"] = "Recognitio"
        problems = self.mutate_json(PORTABLE, change)
        self.assertTrue(
            any("closed" in p for p in problems), problems)

    def test_an_uppercase_portable_keyword_fails(self):
        def change(d):
            d["keywords"] = ["Review-Packet"]
        problems = self.mutate_json(PORTABLE, change)
        self.assertTrue(
            any("keyword" in p for p in problems), problems)

    def test_a_portable_name_outside_the_pattern_fails(self):
        def change(d):
            d["name"] = "Recognitio--Pack"
        problems = self.mutate_json(PORTABLE, change)
        self.assertTrue(
            any("pattern" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
