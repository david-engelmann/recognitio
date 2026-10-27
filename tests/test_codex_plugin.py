"""Build 19, the Codex plugin build.

The build ships the com.openai extension object in the portable
manifest, the repo marketplace that offers the package, and the
agents/openai.yaml file inside the skill folder. These tests
prove the gate at scripts/check_codex_plugin.py fires for a
real reason on every stated failure. A dropped namespace, a
drifted discovery value, a brand colour off the palette, an
icon that drifts from the brand master, a stray asset, a
compatibility overlay beside the extension, a marketplace that
points nowhere, a policy or category drift, an openai.yaml
that turns implicit invocation off or drifts between skill
spellings, a brief that drops the probe result or the
unverified remainder, and a decision record without its
decision 4 statement each fail the Codex plugin gate.
"""

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FILES = (
    "agent-plugins-package/plugin.json",
    "agent-plugins-package/assets/icon-512.png",
    "docs/brand/recognitio-icon-512.png",
    "docs/brand/palette.json",
    ".agents/plugins/marketplace.json",
    ".agents/skills/recognitio/agents/openai.yaml",
    "agent-plugins-package/skills/recognitio/agents/openai.yaml",
    ".cursor-plugin/skills/recognitio/agents/openai.yaml",
    "docs/codex-plugin-brief.md",
    "docs/decisions.md",
    "docs/README.md",
    "README.md",
    "CHANGELOG.md",
    "AGENTS.md",
)


def load_script(name):
    path = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(
        "codex_plugin_" + name, path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestCheckCodexPlugin(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_codex_plugin")

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

    def manifest(self, root):
        return json.loads(
            self.read(root, "agent-plugins-package/plugin.json")
        )

    def write_manifest(self, root, data):
        self.write(
            root,
            "agent-plugins-package/plugin.json",
            json.dumps(data, indent=2, sort_keys=True),
        )

    def problems(self, root):
        return self.mod.codex_plugin_problems(root)

    def test_the_shipped_tree_holds(self):
        self.assertEqual(self.mod.codex_plugin_problems(ROOT), [])

    def test_the_scratch_layout_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            self.assertEqual(self.problems(root), [])

    def test_a_dropped_openai_namespace_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.manifest(root)
            del data["extensions"]["com.openai"]
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("com.openai" in p for p in problems), problems
            )

    def test_an_apps_mapping_in_the_extension_fails(self):
        # Recognitio registers no MCP server apps, so an apps key
        # in the extension declares a surface the build does not
        # ship.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.manifest(root)
            data["extensions"]["com.openai"]["apps"] = "./.app.json"
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("single interface object" in p for p in problems),
                problems,
            )

    def test_a_drifted_display_name_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.manifest(root)
            data["extensions"]["com.openai"]["interface"][
                "displayName"
            ] = "Recognitio Pro"
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("displayName" in p for p in problems), problems
            )

    def test_a_brand_colour_off_the_palette_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.manifest(root)
            data["extensions"]["com.openai"]["interface"][
                "brandColor"
            ] = "#000000"
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("brandColor" in p for p in problems), problems
            )

    def test_an_icon_drifted_from_the_brand_master_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            icon = root / "agent-plugins-package/assets/icon-512.png"
            icon.write_bytes(icon.read_bytes() + b"drift")
            problems = self.problems(root)
            self.assertTrue(
                any("byte identical" in p for p in problems), problems
            )

    def test_a_stray_asset_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            stray = root / "agent-plugins-package/assets/stray.png"
            stray.write_bytes(b"stray")
            problems = self.problems(root)
            self.assertTrue(
                any("single icon-512.png" in p for p in problems),
                problems,
            )

    def test_a_codex_plugin_overlay_beside_the_extension_fails(self):
        # The extension replaces the overlay whole, so an overlay
        # directory is dead configuration and fails.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            overlay = root / ".codex-plugin"
            overlay.mkdir()
            (overlay / "plugin.json").write_text(
                "{}", encoding="utf-8"
            )
            problems = self.problems(root)
            self.assertTrue(
                any(".codex-plugin" in p for p in problems), problems
            )

    def test_a_marketplace_pointing_nowhere_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read(root, ".agents/plugins/marketplace.json")
            broken = text.replace(
                "./agent-plugins-package", "./no-such-package"
            )
            self.assertNotEqual(broken, text)
            self.write(root, ".agents/plugins/marketplace.json", broken)
            problems = self.problems(root)
            self.assertTrue(
                any("marketplace source" in p for p in problems),
                problems,
            )

    def test_a_marketplace_policy_drift_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read(root, ".agents/plugins/marketplace.json")
            broken = text.replace(
                '"AVAILABLE"', '"INSTALLED_BY_DEFAULT"'
            )
            self.assertNotEqual(broken, text)
            self.write(root, ".agents/plugins/marketplace.json", broken)
            problems = self.problems(root)
            self.assertTrue(
                any("marketplace policy" in p for p in problems),
                problems,
            )

    def test_a_marketplace_category_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read(root, ".agents/plugins/marketplace.json")
            broken = text.replace(
                '"Productivity"', '"Developer Tools"'
            )
            self.assertNotEqual(broken, text)
            self.write(root, ".agents/plugins/marketplace.json", broken)
            problems = self.problems(root)
            self.assertTrue(
                any("marketplace category" in p for p in problems),
                problems,
            )

    def test_implicit_invocation_switched_off_fails(self):
        # The skill is meant to trigger on a matching request, so
        # a policy that waits for an explicit call only fails.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = ".agents/skills/recognitio/agents/openai.yaml"
            text = self.read(root, rel)
            broken = text.replace(
                "allow_implicit_invocation: true",
                "allow_implicit_invocation: false",
            )
            self.assertNotEqual(broken, text)
            for tree in (
                ".agents/skills/recognitio",
                "agent-plugins-package/skills/recognitio",
                ".cursor-plugin/skills/recognitio",
            ):
                self.write(
                    root, tree + "/agents/openai.yaml", broken
                )
            problems = self.problems(root)
            self.assertTrue(
                any("allow_implicit_invocation" in p for p in problems),
                problems,
            )

    def test_a_drifted_openai_yaml_copy_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = ".cursor-plugin/skills/recognitio/agents/openai.yaml"
            text = self.read(root, rel)
            broken = text.replace("Recognitio", "Recognitio Two")
            self.assertNotEqual(broken, text)
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("byte identical" in p for p in problems), problems
            )

    def test_a_dependencies_block_in_openai_yaml_fails(self):
        # The workflow needs no MCP tool, so a dependencies block
        # declares a surface the build does not ship.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = ".agents/skills/recognitio/agents/openai.yaml"
            text = self.read(root, rel)
            broken = text + "dependencies:\n  tools: []\n"
            for tree in (
                ".agents/skills/recognitio",
                "agent-plugins-package/skills/recognitio",
                ".cursor-plugin/skills/recognitio",
            ):
                self.write(
                    root, tree + "/agents/openai.yaml", broken
                )
            problems = self.problems(root)
            self.assertTrue(
                any("interface and policy" in p for p in problems),
                problems,
            )

    def test_a_brief_without_the_probe_result_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "docs/codex-plugin-brief.md"
            text = self.read(root, rel)
            broken = text.replace(
                "registered the repo marketplace and listed",
                "was pointed at the repo marketplace beside",
            )
            self.assertNotEqual(broken, text)
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("CLI probe result" in p for p in problems),
                problems,
            )

    def test_a_brief_without_the_unverified_remainder_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "docs/codex-plugin-brief.md"
            text = self.read(root, rel)
            # The sentence stands twice in the brief, once in
            # the glance and once wrapped across a line break in
            # the probe section, so the mutation breaks the shared
            # span both copies carry.
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

    def test_a_rule_without_a_derivation_note_fails(self):
        # The second packet guard. A rule that names no canonical
        # section or primary citation is a rival instruction
        # source, and the gate must catch the note going missing.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "docs/codex-plugin-brief.md"
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
        # A derivation note that names nothing the gate can check
        # is the same failure wearing a label. Stripping the
        # packaging page stem leaves four rules with no source.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "docs/codex-plugin-brief.md"
            text = self.read(root, rel)
            broken = text.replace(
                "developers.openai.com/plugins/build/plugins",
                "a secondary writeup",
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
        # place and the appended sentences claim the opposite, so
        # only a negative pin can catch them.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "docs/codex-plugin-brief.md"
            text = self.read(root, rel)
            broken = text + (
                "\nInstallation through the desktop app stands "
                "verified and a universal plugin directory listing "
                "has been submitted for recognitio. The plugin was "
                "invoked inside a live Codex session.\n"
            )
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("listing has been submitted" in p for p in problems),
                problems,
            )
            self.assertTrue(
                any("desktop app" in p for p in problems), problems
            )
            self.assertTrue(
                any("invoked inside" in p for p in problems), problems
            )

    def test_a_contradiction_in_decision_29_fails(self):
        # The decision record carries the same honesty claims,
        # so a contradicting sentence appended inside it fails
        # on the same stems.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "docs/decisions.md"
            text = self.read(root, rel)
            broken = text + (
                "\nInstallation through the desktop app stands "
                "verified.\n"
            )
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("decision 29" in p for p in problems), problems
            )

    def test_a_quoted_policy_value_fails(self):
        # A quoted true is a string to a YAML reader, not the
        # boolean the invocation policy declares.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = ".agents/skills/recognitio/agents/openai.yaml"
            text = self.read(root, rel)
            broken = text.replace(
                "allow_implicit_invocation: true",
                'allow_implicit_invocation: "true"',
            )
            self.assertNotEqual(broken, text)
            for tree in (
                ".agents/skills/recognitio",
                "agent-plugins-package/skills/recognitio",
                ".cursor-plugin/skills/recognitio",
            ):
                self.write(root, tree + "/agents/openai.yaml", broken)
            problems = self.problems(root)
            self.assertTrue(
                any("quoted" in p for p in problems), problems
            )

    def test_a_repeated_policy_key_fails(self):
        # The strict reading refuses a repeated key, so a false
        # line cannot hide above the true one.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = ".agents/skills/recognitio/agents/openai.yaml"
            text = self.read(root, rel)
            broken = text.replace(
                "  allow_implicit_invocation: true",
                "  allow_implicit_invocation: false\n"
                "  allow_implicit_invocation: true",
            )
            self.assertNotEqual(broken, text)
            for tree in (
                ".agents/skills/recognitio",
                "agent-plugins-package/skills/recognitio",
                ".cursor-plugin/skills/recognitio",
            ):
                self.write(root, tree + "/agents/openai.yaml", broken)
            problems = self.problems(root)
            self.assertTrue(
                any("repeats a key" in p for p in problems), problems
            )

    def test_a_capitalised_contradiction_fails(self):
        # A claim that opens a sentence capitalises its first
        # word, so the stem refusal folds case or the most
        # natural form of the false claim walks past it.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "docs/codex-plugin-brief.md"
            text = self.read(root, rel)
            broken = text + (
                "\nInvoked inside a live Codex session, the "
                "plugin produced a packet. A universal plugin "
                "directory listing exists for recognitio.\n"
            )
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("invoked inside" in p for p in problems),
                problems,
            )
            self.assertTrue(
                any("listing exists for recognitio" in p
                    for p in problems),
                problems,
            )

    def test_a_symlinked_assets_directory_fails(self):
        # The leaf checks alone let a linked parent directory
        # carry the icon outside the tree, and the installer
        # drops a linked directory, so the refusal walks every
        # component of the pinned paths.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            package = root / "agent-plugins-package"
            outside = root / "outside-assets"
            outside.mkdir()
            shutil.copyfile(
                package / "assets" / "icon-512.png",
                outside / "icon-512.png",
            )
            shutil.rmtree(package / "assets")
            (package / "assets").symlink_to(
                outside, target_is_directory=True
            )
            problems = self.problems(root)
            self.assertTrue(
                any("symlink" in p for p in problems), problems
            )

    def test_an_empty_assets_subdirectory_fails(self):
        # The assets listing counts directories as well as
        # files, so an empty folder cannot ride the single
        # icon pin in silence.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            (root / "agent-plugins-package/assets/sub").mkdir()
            problems = self.problems(root)
            self.assertTrue(
                any("single icon-512.png" in p for p in problems),
                problems,
            )

    def test_an_unquoted_hash_brand_colour_fails(self):
        # YAML reads an unquoted hash as a comment, so the
        # colour a real reader sees is null and not the accent
        # the literal text suggests.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = ".agents/skills/recognitio/agents/openai.yaml"
            text = self.read(root, rel)
            broken = text.replace(
                'brand_color: "#D97757"', "brand_color: #D97757"
            )
            self.assertNotEqual(broken, text)
            for tree in (
                ".agents/skills/recognitio",
                "agent-plugins-package/skills/recognitio",
                ".cursor-plugin/skills/recognitio",
            ):
                self.write(root, tree + "/agents/openai.yaml", broken)
            problems = self.problems(root)
            self.assertTrue(
                any("does not parse" in p for p in problems),
                problems,
            )

    def test_a_dropped_readme_command_fails(self):
        # The install commands are the one actionable sentence
        # in the route, so they carry pins like the scoped
        # desktop sentence beside them.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "README.md"
            text = self.read(root, rel)
            broken = text.replace(
                "codex plugin add", "codex plugin fetch"
            )
            self.assertNotEqual(broken, text)
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("plugin add command" in p for p in problems),
                problems,
            )

    def test_a_wrong_readme_plugin_address_fails(self):
        # The address pin is anchored to the Codex subsection
        # with a boundary, because other sections carry
        # recognitio@recognitio-marketplace and an unanchored
        # substring stays satisfied by that prefix while the
        # Codex route prints a wrong address.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "README.md"
            text = self.read(root, rel)
            broken = text.replace(
                "recognitio@recognitio\n```",
                "recognitio@recognitio-wrong\n```",
            )
            self.assertNotEqual(broken, text)
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("Codex plugin address" in p for p in problems),
                problems,
            )

    def test_a_contradiction_in_agents_md_fails(self):
        # AGENTS.md is the surface agents read as guidance in
        # this repo, so the stems scan it with the other claim
        # surfaces.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "AGENTS.md"
            text = self.read(root, rel)
            broken = text + (
                "\nThe plugin was invoked inside a live Codex "
                "session.\n"
            )
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("AGENTS.md" in p for p in problems), problems
            )

    def test_a_symlinked_icon_fails(self):
        # The byte pin certifies content, not containment, so a
        # symlink to the brand master needs its own refusal.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            icon = root / "agent-plugins-package/assets/icon-512.png"
            icon.unlink()
            icon.symlink_to(
                root / "docs" / "brand" / "recognitio-icon-512.png"
            )
            problems = self.problems(root)
            self.assertTrue(
                any("symlink" in p for p in problems), problems
            )

    def test_a_dropped_probe_version_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "docs/codex-plugin-brief.md"
            text = self.read(root, rel)
            broken = text.replace("0.164.0-alpha.9", "0.160.0")
            self.assertNotEqual(broken, text)
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("CLI probe version" in p for p in problems),
                problems,
            )

    def test_a_marketplace_repeated_key_fails(self):
        # The strict reader refuses a repeated key, so a second
        # name entry cannot hide beside the one the gate reads.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = ".agents/plugins/marketplace.json"
            text = self.read(root, rel)
            broken = text.replace(
                '"name": "recognitio",',
                '"name": "recognitio", "name": "recognitio",',
                1,
            )
            self.assertNotEqual(broken, text)
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("does not parse" in p for p in problems),
                problems,
            )

    def test_an_unscoped_readme_install_route_fails(self):
        # The README route must scope the install to the desktop
        # app surface, so the stale wording that promises an
        # install the CLI performs fails twice over.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            rel = "README.md"
            text = self.read(root, rel)
            broken = text.replace(
                "or install recognitio from that marketplace in "
                "the Plugins Directory of the ChatGPT desktop app",
                "and install the recognitio plugin it offers",
            )
            self.assertNotEqual(broken, text)
            self.write(root, rel, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("Plugins Directory" in p for p in problems),
                problems,
            )
            self.assertTrue(
                any("stale" in p for p in problems), problems
            )

    def test_a_decision_record_without_decision_4_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / "docs" / "decisions.md"
            text = path.read_text(encoding="utf-8")
            start = text.find("## 29. Build 19")
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


if __name__ == "__main__":
    unittest.main()
