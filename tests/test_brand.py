"""Visual round 8, the brand asset gate script.

The script at scripts/check_brand.py carries the manifest
and palette logic of the brand gate. These tests prove the
pin fires for a real reason on every load bearing claim the
round 8 consistency lane named. A deleted manifest value, an
image field on a surface that documents none, a logo path
that resolves nowhere, an unrecorded colour in a master, a
palette pair under its contrast floor, live text in a
master, moved wordmark geometry and a wrong conditional
brand colour each fail the brand gate.
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
    ".cursor-plugin/plugin.json",
    ".cursor-plugin/marketplace.json",
    "agent-plugins-package/plugin.json",
    ".zcode-plugin/plugin.json",
    ".antigravity/plugin.json",
    "README.md",
)
BRAND_FILES = (
    "wordmark-light.svg",
    "wordmark-dark.svg",
    "recognitio-wordmark-1600.png",
    "recognitio-icon.svg",
    "recognitio-icon-512.png",
    "recognitio-icon-256.png",
    "recognitio-social-preview.svg",
    "recognitio-social-preview.png",
    "palette.json",
    "build_brand.py",
)


def load_script(name):
    path = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location("brand_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestCheckBrand(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_brand")

    def make_layout(self, tmp):
        root = Path(tmp) / "root"
        for rel in FILES:
            source = ROOT / rel
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        for name in BRAND_FILES:
            source = ROOT / "docs" / "brand" / name
            target = root / "docs" / "brand" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        asset = ROOT / "agent-plugins-package" / "assets" / "icon-512.png"
        if asset.is_file():
            target = root / "agent-plugins-package" / "assets" / "icon-512.png"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(asset, target)
        return root

    def problems(self, root):
        return self.mod.brand_problems(root)

    def read_json(self, root, rel):
        return json.loads((root / rel).read_text(encoding="utf-8"))

    def write_json(self, root, rel, data):
        (root / rel).write_text(json.dumps(data), encoding="utf-8")

    def test_the_shipped_tree_holds(self):
        self.assertEqual(self.mod.brand_problems(ROOT), [])

    def test_the_scratch_layout_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            self.assertEqual(self.problems(root), [])

    def test_p1_a_deleted_claude_icon_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_json(root, ".claude-plugin/plugin.json")
            del data["icon"]
            self.write_json(root, ".claude-plugin/plugin.json", data)
            problems = self.problems(root)
            self.assertTrue(
                any("icon field" in p for p in problems), problems
            )

    def test_p1_a_deleted_cursor_logo_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_json(root, ".cursor-plugin/plugin.json")
            del data["logo"]
            self.write_json(root, ".cursor-plugin/plugin.json", data)
            problems = self.problems(root)
            self.assertTrue(
                any("logo field" in p for p in problems), problems
            )

    def test_p1_a_changed_marketplace_logo_value_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_json(root, ".cursor-plugin/marketplace.json")
            data["plugins"][0]["logo"] = "docs/brand/wordmark-light.svg"
            self.write_json(root, ".cursor-plugin/marketplace.json", data)
            problems = self.problems(root)
            self.assertTrue(
                any("logo field" in p for p in problems), problems
            )

    def test_p2_an_icon_on_the_claude_marketplace_entry_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_json(root, ".claude-plugin/marketplace.json")
            data["plugins"][0]["icon"] = "./docs/brand/recognitio-icon-512.png"
            self.write_json(root, ".claude-plugin/marketplace.json", data)
            problems = self.problems(root)
            self.assertTrue(
                any("marketplace" in p and "image field" in p
                    for p in problems),
                problems,
            )

    def test_p2_a_logo_on_the_portable_manifest_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_json(root, "agent-plugins-package/plugin.json")
            data["logo"] = "docs/brand/recognitio-icon.svg"
            self.write_json(root, "agent-plugins-package/plugin.json", data)
            problems = self.problems(root)
            self.assertTrue(
                any("top level" in p for p in problems), problems
            )

    def test_p2_an_image_field_on_the_zcode_manifest_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_json(root, ".zcode-plugin/plugin.json")
            data["icon"] = "docs/brand/recognitio-icon-512.png"
            self.write_json(root, ".zcode-plugin/plugin.json", data)
            problems = self.problems(root)
            self.assertTrue(
                any("zcode" in p for p in problems), problems
            )

    def test_p2_an_image_field_on_the_antigravity_manifest_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_json(root, ".antigravity/plugin.json")
            data["logo"] = "docs/brand/recognitio-icon.svg"
            self.write_json(root, ".antigravity/plugin.json", data)
            problems = self.problems(root)
            self.assertTrue(
                any("antigravity" in p for p in problems), problems
            )

    def test_p3_a_logo_path_that_resolves_nowhere_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            target = root / "docs" / "brand" / "recognitio-icon.svg"
            target.unlink()
            problems = self.problems(root)
            self.assertTrue(
                any("resolves to no file" in p for p in problems),
                problems,
            )

    def test_p3_a_marketplace_logo_naming_another_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            other = root / "docs" / "brand" / "other-icon.svg"
            text = (
                root / "docs" / "brand" / "recognitio-icon.svg"
            ).read_text(encoding="utf-8")
            other.write_text(
                text.replace("#D97757", "#D97758"), encoding="utf-8"
            )
            data = self.read_json(root, ".cursor-plugin/marketplace.json")
            data["plugins"][0]["logo"] = "docs/brand/other-icon.svg"
            self.write_json(root, ".cursor-plugin/marketplace.json", data)
            problems = self.problems(root)
            self.assertTrue(
                any("different files" in p for p in problems), problems
            )

    def test_p9_an_unrecorded_colour_in_a_master_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / "docs" / "brand" / "recognitio-icon.svg"
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace("#D97757", "#D97758"), encoding="utf-8"
            )
            problems = self.problems(root)
            self.assertTrue(
                any("palette record names no such value" in p
                    for p in problems),
                problems,
            )

    def test_p9_the_reserved_green_in_a_master_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / "docs" / "brand" / "recognitio-icon.svg"
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace("#D97757", "#4AC76A"), encoding="utf-8"
            )
            problems = self.problems(root)
            self.assertTrue(
                any("reserved green" in p for p in problems), problems
            )

    def test_p9_a_moved_palette_value_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_json(root, "docs/brand/palette.json")
            data["accent"] = "#D97758"
            self.write_json(root, "docs/brand/palette.json", data)
            problems = self.problems(root)
            self.assertTrue(
                any("frozen palette value" in p for p in problems),
                problems,
            )

    def test_p10_a_lightened_ink_fails_the_contrast_floor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_json(root, "docs/brand/palette.json")
            data["ink_on_dark"] = "#777777"
            self.write_json(root, "docs/brand/palette.json", data)
            problems = self.problems(root)
            self.assertTrue(
                any("floor" in p for p in problems), problems
            )

    def test_p11_live_text_in_a_master_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / "docs" / "brand" / "wordmark-light.svg"
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace("</svg>", "<text>recognitio</text></svg>"),
                encoding="utf-8",
            )
            problems = self.problems(root)
            self.assertTrue(
                any("text element" in p for p in problems), problems
            )

    def test_p11_moved_dark_geometry_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / "docs" / "brand" / "wordmark-dark.svg"
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace(
                    "translate(106.00 71.70)", "translate(107.00 71.70)", 1
                ),
                encoding="utf-8",
            )
            problems = self.problems(root)
            self.assertTrue(
                any("differ in geometry" in p for p in problems),
                problems,
            )

    def test_p13_an_animation_chunk_in_the_preview_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = (
                root / "docs" / "brand" / "recognitio-social-preview.png"
            )
            raw = path.read_bytes()
            chunk = b"\x00\x00\x00\x00acTL\x00\x00\x00\x00"
            path.write_bytes(raw[:33] + chunk + raw[33:])
            problems = self.problems(root)
            self.assertTrue(
                any("still image" in p for p in problems), problems
            )

    def test_p16_a_wrong_openai_brand_colour_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_json(root, "agent-plugins-package/plugin.json")
            data["extensions"]["com.openai"] = {
                "interface": {
                    "brandColor": "#D97758",
                    "composerIcon": "./assets/icon-512.png",
                    "logo": "./assets/icon-512.png",
                }
            }
            self.write_json(root, "agent-plugins-package/plugin.json", data)
            problems = self.problems(root)
            self.assertTrue(
                any("brandColor" in p for p in problems), problems
            )

    def test_p16_a_matching_openai_namespace_holds(self):
        # The fixture carries the shipped values, with the icon
        # paths in the ./assets form the primary path rules
        # resolve against the plugin root, and the layout
        # builder places the package asset beside the manifest.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_json(root, "agent-plugins-package/plugin.json")
            data["extensions"]["com.openai"] = {
                "interface": {
                    "brandColor": "#D97757",
                    "composerIcon": "./assets/icon-512.png",
                    "logo": "./assets/icon-512.png",
                }
            }
            self.write_json(root, "agent-plugins-package/plugin.json", data)
            self.assertEqual(self.problems(root), [])


if __name__ == "__main__":
    unittest.main()
