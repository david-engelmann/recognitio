"""Top 20 item 16, the discovery metadata gate script.

The script at scripts/check_discovery.py pins the discovery
fields the top 20 program filled on the Claude manifest, the
Claude marketplace entry and the Cursor manifest. These
tests prove the pin fires for a real reason on every load
bearing claim. A deleted or drifted value on any surface, a
category or tags key on the Claude manifest where its schema
names none, a directory listing field or a duplicated
display field on the marketplace entry, and a Cursor value
that disagrees with the Claude surface each fail the gate.
The marketplace polish pass added the recognitio-mod entry
and its manifest to the pinned surfaces, and the entry set
itself is pinned by name, so a dropped, renamed or added
entry fails beside the field pins.
"""

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FILES = (
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    "plugins/recognitio-mod/.claude-plugin/plugin.json",
    ".cursor-plugin/plugin.json",
    ".cursor-plugin/marketplace.json",
)

CLAUDE_PLUGIN = ".claude-plugin/plugin.json"
CLAUDE_MARKET = ".claude-plugin/marketplace.json"
MOD_PLUGIN = "plugins/recognitio-mod/.claude-plugin/plugin.json"
CURSOR_PLUGIN = ".cursor-plugin/plugin.json"
CURSOR_MARKET = ".cursor-plugin/marketplace.json"


def load_script(name):
    path = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(
        "discovery_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestCheckDiscovery(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_discovery")

    def make_layout(self, tmp):
        root = Path(tmp) / "root"
        for rel in FILES:
            source = ROOT / rel
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        return root

    def problems(self, root):
        return self.mod.discovery_problems(root)

    def read_json(self, root, rel):
        return json.loads((root / rel).read_text(encoding="utf-8"))

    def write_json(self, root, rel, data):
        (root / rel).write_text(json.dumps(data), encoding="utf-8")

    def mutate(self, rel, change):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_json(root, rel)
            change(data)
            self.write_json(root, rel, data)
            return self.problems(root)

    def test_the_shipped_tree_holds(self):
        self.assertEqual(self.mod.discovery_problems(ROOT), [])

    def test_the_scratch_layout_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            self.assertEqual(self.problems(root), [])

    def test_a_deleted_claude_display_name_fails(self):
        problems = self.mutate(
            CLAUDE_PLUGIN, lambda d: d.pop("displayName"))
        self.assertTrue(
            any("displayName" in p for p in problems), problems)

    def test_a_drifted_claude_homepage_fails(self):
        def change(d):
            d["homepage"] = "https://example.com/recognitio"
        problems = self.mutate(CLAUDE_PLUGIN, change)
        self.assertTrue(
            any("homepage" in p for p in problems), problems)

    def test_a_dropped_claude_keyword_fails(self):
        def change(d):
            d["keywords"] = d["keywords"][:-1]
        problems = self.mutate(CLAUDE_PLUGIN, change)
        self.assertTrue(
            any("keywords" in p for p in problems), problems)

    def test_a_category_on_the_claude_manifest_fails(self):
        # The manifest reference names no category field for
        # plugin.json and the host strips an unrecognized key
        # at load, so the field belongs on the entry only,
        # and even the pinned entry value fails here.
        def change(d):
            d["category"] = "developer-tools"
        problems = self.mutate(CLAUDE_PLUGIN, change)
        self.assertTrue(
            any("category" in p for p in problems), problems)

    def test_tags_on_the_claude_manifest_fail(self):
        def change(d):
            d["tags"] = list(d["keywords"])
        problems = self.mutate(CLAUDE_PLUGIN, change)
        self.assertTrue(
            any("tags" in p for p in problems), problems)

    def test_a_changed_entry_category_fails(self):
        def change(d):
            d["plugins"][0]["category"] = "Utilities"
        problems = self.mutate(CLAUDE_MARKET, change)
        self.assertTrue(
            any("category" in p for p in problems), problems)

    def test_a_dropped_entry_tag_fails(self):
        def change(d):
            entry = d["plugins"][0]
            entry["tags"] = entry["tags"][:-1]
        problems = self.mutate(CLAUDE_MARKET, change)
        self.assertTrue(
            any("tags" in p for p in problems), problems)

    def test_a_directory_field_on_the_entry_fails(self):
        # The directory listing fields live in plugin.json
        # only, and the validator reports each one in a
        # marketplace entry as an unknown field.
        def change(d):
            d["plugins"][0]["documentationUrl"] = (
                "https://github.com/david-engelmann/recognitio")
        problems = self.mutate(CLAUDE_MARKET, change)
        self.assertTrue(
            any("documentationUrl" in p for p in problems),
            problems)

    def test_a_duplicated_display_field_on_the_entry_fails(self):
        # An entry display name would override the manifest
        # value wherever the two drifted, so the manifest
        # stays the single source.
        def change(d):
            d["plugins"][0]["displayName"] = "Recognitio"
        problems = self.mutate(CLAUDE_MARKET, change)
        self.assertTrue(
            any("displayName" in p for p in problems), problems)

    def test_a_cursor_value_that_disagrees_fails(self):
        def change(d):
            d["category"] = "Utilities"
        problems = self.mutate(CURSOR_PLUGIN, change)
        self.assertTrue(
            any("category" in p for p in problems), problems)

    def test_a_cursor_tag_that_disagrees_fails(self):
        def change(d):
            d["tags"] = d["tags"] + ["extra"]
        problems = self.mutate(CURSOR_PLUGIN, change)
        self.assertTrue(
            any("tags" in p for p in problems), problems)

    def test_a_cursor_keyword_that_disagrees_fails(self):
        def change(d):
            d["keywords"] = d["keywords"] + ["extra"]
        problems = self.mutate(CURSOR_PLUGIN, change)
        self.assertTrue(
            any("keywords" in p for p in problems), problems)

    def test_an_unlisted_claude_entry_fails(self):
        # The entry set is pinned by name, so a third entry
        # fails even when it copies a listed one, and the
        # skill plugin can never stand under a second name.
        def change(d):
            extra = dict(d["plugins"][0])
            extra["name"] = "recognitio-copy"
            d["plugins"] = d["plugins"] + [extra]
        problems = self.mutate(CLAUDE_MARKET, change)
        self.assertTrue(
            any("plugin entries" in p for p in problems), problems)

    def test_a_dropped_mod_entry_fails(self):
        def change(d):
            d["plugins"] = [
                e for e in d["plugins"]
                if e["name"] != "recognitio-mod"
            ]
        problems = self.mutate(CLAUDE_MARKET, change)
        self.assertTrue(
            any("plugin entries" in p for p in problems), problems)

    def test_a_renamed_mod_entry_fails(self):
        def change(d):
            for entry in d["plugins"]:
                if entry["name"] == "recognitio-mod":
                    entry["name"] = "spawn-gate"
        problems = self.mutate(CLAUDE_MARKET, change)
        self.assertTrue(
            any("plugin entries" in p for p in problems), problems)

    def test_a_drifted_mod_entry_source_fails(self):
        def change(d):
            for entry in d["plugins"]:
                if entry["name"] == "recognitio-mod":
                    entry["source"] = "./plugins/other"
        problems = self.mutate(CLAUDE_MARKET, change)
        self.assertTrue(
            any("source" in p for p in problems), problems)

    def test_a_component_on_the_mod_entry_fails(self):
        # The mod manifest is the whole definition of the
        # mod plugin, so its entry names no component, and
        # a skills list there would shadow the manifest.
        def change(d):
            for entry in d["plugins"]:
                if entry["name"] == "recognitio-mod":
                    entry["skills"] = ["./hooks/"]
        problems = self.mutate(CLAUDE_MARKET, change)
        self.assertTrue(
            any("skills" in p for p in problems), problems)

    def test_a_deleted_mod_display_name_fails(self):
        problems = self.mutate(
            MOD_PLUGIN, lambda d: d.pop("displayName"))
        self.assertTrue(
            any("displayName" in p for p in problems), problems)

    def test_a_drifted_mod_keyword_fails(self):
        def change(d):
            d["keywords"] = d["keywords"][:-1]
        problems = self.mutate(MOD_PLUGIN, change)
        self.assertTrue(
            any("keywords" in p for p in problems), problems)

    def test_a_category_on_the_mod_manifest_fails(self):
        def change(d):
            d["category"] = "developer-tools"
        problems = self.mutate(MOD_PLUGIN, change)
        self.assertTrue(
            any("category" in p for p in problems), problems)

    def test_a_drifted_mod_entry_tag_fails(self):
        # Each entry carries the tags of its own manifest,
        # so the mod entry is pinned to the mod keyword set
        # and not to the skill plugin set.
        def change(d):
            for entry in d["plugins"]:
                if entry["name"] == "recognitio-mod":
                    entry["tags"] = entry["tags"] + ["diff"]
        problems = self.mutate(CLAUDE_MARKET, change)
        self.assertTrue(
            any("tags" in p for p in problems), problems)

    def test_a_drifted_mod_entry_description_fails(self):
        def change(d):
            for entry in d["plugins"]:
                if entry["name"] == "recognitio-mod":
                    entry["description"] = "A spawn gate."
        problems = self.mutate(CLAUDE_MARKET, change)
        self.assertTrue(
            any("description" in p for p in problems), problems)

    def test_a_drifted_mod_description_fails(self):
        def change(d):
            d["description"] = "A spawn gate."
        problems = self.mutate(MOD_PLUGIN, change)
        self.assertTrue(
            any("description" in p for p in problems), problems)

    def test_a_drifted_mod_homepage_fails(self):
        def change(d):
            d["homepage"] = "https://example.com/recognitio"
        problems = self.mutate(MOD_PLUGIN, change)
        self.assertTrue(
            any("homepage" in p for p in problems), problems)

    def test_a_drifted_mod_manifest_name_fails(self):
        def change(d):
            d["name"] = "spawn-gate"
        problems = self.mutate(MOD_PLUGIN, change)
        self.assertTrue(
            any("name" in p for p in problems), problems)

    def test_a_component_on_the_mod_manifest_fails(self):
        # The mod plugin ships the hooks module alone, so a
        # component field in its manifest would ship the
        # skill under a second name, the hazard the entry
        # set pin exists to close.
        def change(d):
            d["skills"] = ["./.agents/skills/recognitio/"]
        problems = self.mutate(MOD_PLUGIN, change)
        self.assertTrue(
            any("skills" in p for p in problems), problems)

    def test_a_server_on_the_mod_manifest_fails(self):
        def change(d):
            d["mcpServers"] = {"x": {"command": "x"}}
        problems = self.mutate(MOD_PLUGIN, change)
        self.assertTrue(
            any("mcpServers" in p for p in problems), problems)

    def test_a_component_under_experimental_on_the_mod_entry_fails(self):
        def change(d):
            for entry in d["plugins"]:
                if entry["name"] == "recognitio-mod":
                    entry["experimental"] = {"skills": ["./x/"]}
        problems = self.mutate(CLAUDE_MARKET, change)
        self.assertTrue(
            any("skills" in p for p in problems), problems)

    def test_a_wrong_typed_entry_name_fails(self):
        # A wrong typed name is named as its own problem in
        # the gate voice, never a crash on the sort.
        def change(d):
            for entry in d["plugins"]:
                if entry["name"] == "recognitio-mod":
                    entry["name"] = 123
        problems = self.mutate(CLAUDE_MARKET, change)
        self.assertTrue(
            any("not a string" in p for p in problems), problems)

    def test_a_discovery_field_on_the_cursor_entry_fails(self):
        def change(d):
            d["plugins"][0]["category"] = "developer-tools"
        problems = self.mutate(CURSOR_MARKET, change)
        self.assertTrue(
            any(
                "category" in p and "Cursor" in p for p in problems
            ),
            problems,
        )

    def test_a_missing_marketplace_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            (root / CLAUDE_MARKET).unlink()
            problems = self.problems(root)
            self.assertTrue(
                any("missing" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
