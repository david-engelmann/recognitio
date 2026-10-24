"""Build 8, the Agent Plugins 1.0.0 portable package.

The package at agent-plugins-package/ carries only the portable
core beside the Claude Code native shapes, which ride as per
platform extensions declared in the manifest under the reverse
domain namespace the spec section 8 defines. These tests prove
the pin fires for a real reason on every inversion the round 19
lanes named. A Claude Code native key at the top level of the
portable manifest, a drifted or reshaped package skill copy, a
present mcp.json, a dangling extension path, a brief without
the honesty sentence, a brief without the primary AAIF sentence,
and a brief with the stale AAIF wording each fail the package
gate, and an em dash in the portable description fails the copy
gate. A second extensions namespace with a dangling shape path
fails the generalized path resolution, a dangling Antigravity
shape path fails the same way, and a native platform file
placed inside the portable core fails the package root tree
pin.
"""

import importlib.util
import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "agent-plugins-package"
NAMESPACE = "com.anthropic.claude-code"
HONESTY_SENTENCE = (
    "The package does not install natively in Claude Code on "
    "current evidence"
)


def load_script(name):
    path = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location("package_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Every repo relative path the portable manifest declares under
# the extension namespace. The scratch layout creates each one
# as a file so the extension path resolution has something to
# resolve, the same way the real tree does.
EXTENSION_PATHS = (
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    "agents/reviewer.md",
    "output-styles/packet.md",
    "hooks/hooks.json",
    "hooks/register.js",
    "docs/headless-review.md",
    "scripts/check_headless.py",
    "workflows/review-fanout.md",
    "workflows/findings.schema.json",
    ".antigravity/plugin.json",
    ".antigravity/hooks.json",
)


class TestCheckPackage(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_package")

    def make_layout(self, tmp):
        """A scratch tree mirroring the package layout."""
        root = Path(tmp) / "root"
        shutil.copytree(PACKAGE, root / "agent-plugins-package")
        shutil.copytree(
            ROOT / ".agents" / "skills" / "recognitio",
            root / ".agents" / "skills" / "recognitio",
        )
        for entry in EXTENSION_PATHS:
            path = root / entry
            path.parent.mkdir(parents=True, exist_ok=True)
            if entry == ".claude-plugin/plugin.json":
                shutil.copyfile(ROOT / entry, path)
            else:
                path.write_text("shape\n", encoding="utf-8")
        brief = root / "docs" / "agent-plugins-brief.md"
        shutil.copyfile(ROOT / "docs" / "agent-plugins-brief.md", brief)
        return root

    def read_manifest(self, root):
        path = root / "agent-plugins-package" / "plugin.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def write_manifest(self, root, data):
        path = root / "agent-plugins-package" / "plugin.json"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def problems(self, root):
        return self.mod.package_problems(root)

    def test_the_shipped_package_holds(self):
        self.assertEqual(self.mod.package_problems(ROOT), [])

    def test_the_scratch_layout_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            self.assertEqual(self.problems(root), [])

    def test_a_claude_code_key_at_the_top_level_fails(self):
        # R19-SP-01. The agents key off the native manifest would
        # be silently ignored by a conformant client, dropping
        # the persona with no error. The closed schema pin names
        # the key.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["agents"] = ["./agents/reviewer.md"]
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("'agents'" in problem for problem in problems),
                problems,
            )

    def test_an_unknown_top_level_field_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["customField"] = "custom value"
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("'customField'" in problem for problem in problems),
                problems,
            )

    def test_a_wrong_schema_value_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["$schema"] = (
                "https://agent-plugins.org/schemas/0.9.0/plugin.schema.json"
            )
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("$schema" in problem for problem in problems),
                problems,
            )

    def test_a_repeated_key_in_the_manifest_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / "agent-plugins-package" / "plugin.json"
            text = path.read_text(encoding="utf-8")
            text = text.replace(
                '"version":"1.3.0"',
                '"version":"1.3.0","version":"9.9.9"',
            )
            path.write_text(text, encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("repeated key" in problem for problem in problems),
                problems,
            )

    def test_a_version_disagreement_with_the_native_manifest_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["version"] = "9.9.9"
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("disagrees" in problem for problem in problems),
                problems,
            )

    def test_a_missing_namespace_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            del data["extensions"][NAMESPACE]
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any(NAMESPACE in problem for problem in problems),
                problems,
            )

    def test_a_dangling_extension_path_fails(self):
        # Proof 6 of the second leg. A renamed native shape must
        # break the gate instead of dangling in the manifest.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            shapes = data["extensions"][NAMESPACE]["shapes"]
            shapes["modHooks"] = ["hooks/register-missing.js"]
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("does not resolve" in problem for problem in problems),
                problems,
            )

    def test_a_second_namespace_with_a_dangling_path_fails(self):
        # R24-RT-01 and R24-RT-02. Path resolution covers every
        # namespace in the extensions object, not just the pinned
        # Claude Code one. A fixture namespace whose shape path
        # dangles must fail the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["extensions"]["com.example.fixture"] = {
                "shapes": {"fixtureShape": ["fixture/missing.md"]}
            }
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "fixture/missing.md" in problem
                    and "does not resolve" in problem
                    for problem in problems
                ),
                problems,
            )

    def test_a_dangling_antigravity_path_fails(self):
        # R24-RT-01 and R24-RT-02. The Build 12 namespace rides
        # the same generalized resolution as every other
        # namespace, so a renamed Antigravity shape dangles
        # loudly instead of in silence.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            shapes = data["extensions"]["com.google.antigravity"]["shapes"]
            shapes["hookWiring"] = [".antigravity/hooks-missing.json"]
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("does not resolve" in problem for problem in problems),
                problems,
            )

    def test_a_native_file_inside_the_portable_core_fails(self):
        # R24-RT-01. The allowed contents of
        # agent-plugins-package/ are plugin.json and the skills/
        # tree. A native platform file placed inside the portable
        # core must fail the gate instead of blending in silence.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            package = root / "agent-plugins-package"
            (package / "hooks.json").write_text(
                '{"hooks": []}\n', encoding="utf-8"
            )
            agents = package / "agents"
            agents.mkdir()
            (agents / "reviewer.md").write_text(
                "Native.\n", encoding="utf-8"
            )
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "agent-plugins-package/hooks.json" in problem
                    for problem in problems
                ),
                problems,
            )
            self.assertTrue(
                any(
                    "agent-plugins-package/agents/reviewer.md" in problem
                    for problem in problems
                ),
                problems,
            )

    def test_a_drifted_skill_copy_fails(self):
        # R19-RT-03. The package skill is a second spelling of the
        # canonical skill by construction, and the canonical is
        # the only spelling that ever changes.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            skill = root / "agent-plugins-package" / "skills" / "recognitio"
            path = skill / "SKILL.md"
            path.write_text(
                path.read_text(encoding="utf-8") + "\nDrifted.\n",
                encoding="utf-8",
            )
            problems = self.problems(root)
            self.assertTrue(
                any("byte identical" in problem for problem in problems),
                problems,
            )

    def test_an_extra_file_in_the_package_skill_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            skill = root / "agent-plugins-package" / "skills" / "recognitio"
            (skill / "extra.md").write_text("Extra.\n", encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("file set" in problem for problem in problems),
                problems,
            )

    def test_a_missing_file_in_the_package_skill_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            skill = root / "agent-plugins-package" / "skills" / "recognitio"
            (skill / "scripts" / "extract.py").unlink()
            problems = self.problems(root)
            self.assertTrue(
                any("file set" in problem for problem in problems),
                problems,
            )

    def test_a_second_skill_directory_in_package_skills_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            other = root / "agent-plugins-package" / "skills" / "other"
            other.mkdir()
            (other / "SKILL.md").write_text("Other.\n", encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("single recognitio" in problem for problem in problems),
                problems,
            )

    def test_a_present_mcp_json_fails(self):
        # R19-RT-02. The recorded disposition is omission, so a
        # present mcp.json is a drifted choice, not a quiet one.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / "agent-plugins-package" / "mcp.json"
            path.write_text('{"mcpServers": {}}\n', encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("mcp.json is present" in problem for problem in problems),
                problems,
            )

    def test_a_brief_without_the_honesty_sentence_fails(self):
        # Proof 5 of the second leg. The brief must keep stating
        # the negative, so a later edit cannot quietly claim the
        # native install.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            brief = root / "docs" / "agent-plugins-brief.md"
            text = brief.read_text(encoding="utf-8")
            self.assertIn(HONESTY_SENTENCE, text)
            brief.write_text(
                text.replace(HONESTY_SENTENCE, "The package installs well."),
                encoding="utf-8",
            )
            problems = self.problems(root)
            self.assertTrue(
                any("honesty sentence" in problem for problem in problems),
                problems,
            )

    def test_a_brief_without_the_primary_aaif_sentence_fails(self):
        # R21-ST-01. Round 20 closed the Agent Skills donation to
        # primary on both halves, so the brief must keep recording
        # the transfer as primary.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            brief = root / "docs" / "agent-plugins-brief.md"
            text = brief.read_text(encoding="utf-8")
            sentence = (
                "the transfer is now recorded\nas primary on both halves"
            )
            self.assertIn(sentence, text)
            brief.write_text(
                text.replace(sentence, "the transfer is recorded"),
                encoding="utf-8",
            )
            problems = self.problems(root)
            self.assertTrue(
                any("primary on both halves" in problem for problem in problems),
                problems,
            )

    def test_a_brief_with_the_stale_aaif_wording_fails(self):
        # R21-ST-01. The secondary corroborated wording is stale by
        # timing, and planting it back must fail the pin.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            brief = root / "docs" / "agent-plugins-brief.md"
            text = brief.read_text(encoding="utf-8")
            self.assertNotIn("secondary corroborated", text)
            broken = text.replace(
                "the transfer is now recorded\nas primary on both halves",
                "the transfer is recorded as secondary corroborated",
                1,
            )
            self.assertNotEqual(broken, text)
            brief.write_text(broken, encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("stale" in problem for problem in problems),
                problems,
            )

    def test_bytecode_caches_do_not_break_the_pin(self):
        # Importing the extractor during the test run writes a
        # __pycache__ beside it. The cache is build state, not
        # skill content, so it is skipped on both sides of the
        # comparison instead of failing the pin.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            cache = (
                root / ".agents" / "skills" / "recognitio"
                / "scripts" / "__pycache__"
            )
            cache.mkdir(exist_ok=True)
            (cache / "extract.cpython-312.pyc").write_bytes(b"cache")
            self.assertEqual(self.problems(root), [])

    def test_an_em_dash_in_the_portable_description_fails_the_copy_gate(
        self,
    ):
        # R19-ST-01. The manifest discovery reaches the portable
        # manifest by rule, so its description joins the bar with
        # every other public description in the repo.
        copy_mod = load_script("check_copy")
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["description"] = "A skill for review packets \u2014 fast."
            self.write_manifest(root, data)
            path = root / "agent-plugins-package" / "plugin.json"
            found = [
                str(p.relative_to(root))
                for p in copy_mod.discover_manifest_files(root)
            ]
            self.assertIn("agent-plugins-package/plugin.json", found)
            original = copy_mod.MANIFEST_FILES
            copy_mod.MANIFEST_FILES = [path]
            try:
                with redirect_stderr(io.StringIO()):
                    code = copy_mod.main()
            finally:
                copy_mod.MANIFEST_FILES = original
            self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
