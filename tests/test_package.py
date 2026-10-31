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
pin. A native manifest that cannot be read or does not parse
or is not an object or carries no version or carries a
version that is not a string fails the gate by name, while a
genuinely absent native manifest keeps the single extension
path problem it has always carried. A manifest standing as a
FIFO at either manifest path fails promptly with the cannot
be read problem instead of blocking on the read, and a link
to a regular file still reads through while a dangling link
keeps the absent reading at both paths.
"""

import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
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

    def read_native(self, root):
        path = root / ".claude-plugin" / "plugin.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def write_native(self, root, data):
        path = root / ".claude-plugin" / "plugin.json"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def write_manifest(self, root, data):
        path = root / "agent-plugins-package" / "plugin.json"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def problems(self, root):
        return self.mod.package_problems(root)

    def run_gate(self, root):
        # The FIFO shapes can only be graded in a subprocess
        # with a bound, because a gate that still reads the
        # FIFO would block this test process itself and hang
        # the whole suite instead of failing one test. The
        # driver loads the shipped gate script and runs its
        # main entry against the scratch root.
        driver = (
            "import importlib.util, sys\n"
            "from pathlib import Path\n"
            "spec = importlib.util.spec_from_file_location(\n"
            "    'gate_under_test', sys.argv[1])\n"
            "module = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(module)\n"
            "sys.exit(module.main(Path(sys.argv[2])))\n"
        )
        try:
            return subprocess.run(
                [
                    sys.executable,
                    "-c",
                    driver,
                    str(ROOT / "scripts" / "check_package.py"),
                    str(root),
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except subprocess.TimeoutExpired:
            self.fail(
                "the package gate did not finish within ten "
                "seconds against the scratch root"
            )

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

    def test_a_corrupt_native_manifest_fails(self):
        # Round 115 Finding 1. The version agreement reading
        # once skipped in silence when the native manifest did
        # not parse, so the gate printed its holds line over a
        # manifest it never read. The parse failure must surface
        # as a named problem.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".claude-plugin" / "plugin.json"
            path.write_text("{not json\n", encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "native manifest does not parse" in problem
                    for problem in problems
                ),
                problems,
            )

    def test_a_native_manifest_without_a_version_fails(self):
        # Round 115 Finding 1. A native manifest carrying no
        # version leaves nothing for the portable version to
        # agree with, and that absence must fail the gate instead
        # of skipping the agreement reading in silence.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_native(root)
            del data["version"]
            self.write_native(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "native manifest carries no version" in problem
                    for problem in problems
                ),
                problems,
            )

    def test_a_native_manifest_that_is_a_directory_fails(self):
        # Round 115 Finding 1. A directory standing where the
        # native manifest stands cannot be read, and the gate
        # must name that instead of skipping the agreement
        # reading in silence.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".claude-plugin" / "plugin.json"
            path.unlink()
            path.mkdir()
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "native manifest" in problem
                    and "cannot be read" in problem
                    for problem in problems
                ),
                problems,
            )

    @unittest.skipUnless(hasattr(os, "mkfifo"), "no mkfifo on this host")
    def test_a_native_manifest_standing_as_a_fifo_fails_promptly(self):
        # Round 159 Finding 1. Opening a FIFO for reading
        # blocks until a writer opens the other end, so a
        # plain read of a native manifest standing as a FIFO
        # hangs the gate in silence. The gate must refuse it
        # by name without reading it.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".claude-plugin" / "plugin.json"
            path.unlink()
            os.mkfifo(path)
            result = self.run_gate(root)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("native manifest", result.stderr)
            self.assertIn("cannot be read", result.stderr)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "no mkfifo on this host")
    def test_a_portable_manifest_standing_as_a_fifo_fails_promptly(self):
        # Round 159 Finding 1. The portable manifest reading
        # carries the same plain read as the native one, so a
        # FIFO at the portable path hangs the gate the same
        # way and must draw the same cannot be read problem.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / "agent-plugins-package" / "plugin.json"
            path.unlink()
            os.mkfifo(path)
            result = self.run_gate(root)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("portable manifest", result.stderr)
            self.assertIn("cannot be read", result.stderr)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "no mkfifo on this host")
    def test_a_native_manifest_linking_to_a_fifo_fails_promptly(self):
        # Round 159 Finding 1. The regular file test follows
        # links, so a link whose target is a FIFO refuses
        # exactly as a FIFO standing at the path itself does.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            target = Path(tmp) / "native-fifo"
            os.mkfifo(target)
            path = root / ".claude-plugin" / "plugin.json"
            path.unlink()
            path.symlink_to(target)
            result = self.run_gate(root)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("native manifest", result.stderr)
            self.assertIn("cannot be read", result.stderr)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "no mkfifo on this host")
    def test_a_portable_manifest_linking_to_a_fifo_fails_promptly(self):
        # Round 159 Finding 1. A link to a FIFO at the
        # portable path refuses the same way as at the
        # native path.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            target = Path(tmp) / "portable-fifo"
            os.mkfifo(target)
            path = root / "agent-plugins-package" / "plugin.json"
            path.unlink()
            path.symlink_to(target)
            result = self.run_gate(root)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("portable manifest", result.stderr)
            self.assertIn("cannot be read", result.stderr)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "no mkfifo on this host")
    def test_a_brief_standing_as_a_fifo_fails_promptly(self):
        # Round 183 New Minor 3. The brief reading kept the
        # plain read the manifest fix did not cover, so a
        # FIFO at the brief path blocks the gate in silence
        # after its earlier readings have passed. The gate
        # must refuse it by name without reading it.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / "docs" / "agent-plugins-brief.md"
            path.unlink()
            os.mkfifo(path)
            result = self.run_gate(root)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn(
                "cannot read docs/agent-plugins-brief.md",
                result.stderr,
            )
            self.assertIn("not a regular file", result.stderr)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "no mkfifo on this host")
    def test_a_brief_linking_to_a_fifo_fails_promptly(self):
        # Round 183 New Minor 3. The regular file test
        # follows links, so a brief linking to a FIFO refuses
        # exactly as a FIFO standing at the path itself does.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            target = Path(tmp) / "brief-fifo"
            os.mkfifo(target)
            path = root / "docs" / "agent-plugins-brief.md"
            path.unlink()
            path.symlink_to(target)
            result = self.run_gate(root)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn(
                "cannot read docs/agent-plugins-brief.md",
                result.stderr,
            )
            self.assertIn("not a regular file", result.stderr)

    def test_a_brief_linking_to_a_regular_file_reads_through(self):
        # Round 183 New Minor 3. A brief that is a link to a
        # regular file still reads through, so the scratch
        # layout holds exactly as it does with a plain brief.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            target = Path(tmp) / "brief-regular.md"
            shutil.copyfile(
                ROOT / "docs" / "agent-plugins-brief.md", target)
            path = root / "docs" / "agent-plugins-brief.md"
            path.unlink()
            path.symlink_to(target)
            self.assertEqual(self.problems(root), [])

    def test_a_brief_standing_as_a_directory_fails(self):
        # Round 183 New Minor 3. A directory is not a
        # regular file either, so the brief path draws the
        # cannot be read problem instead of the operating
        # system error text its plain read produced.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / "docs" / "agent-plugins-brief.md"
            path.unlink()
            path.mkdir()
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "cannot read docs/agent-plugins-brief.md"
                    in problem
                    and "not a regular file" in problem
                    for problem in problems
                ),
                problems,
            )

    def test_a_portable_manifest_that_is_a_directory_fails(self):
        # Round 159 Finding 1. A directory is not a regular
        # file either, so the portable path draws the cannot
        # be read problem the native directory shape already
        # drew instead of the missing reading.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / "agent-plugins-package" / "plugin.json"
            path.unlink()
            path.mkdir()
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "portable manifest" in problem
                    and "cannot be read" in problem
                    for problem in problems
                ),
                problems,
            )

    def test_a_native_manifest_linking_to_a_regular_file_holds(self):
        # The regular file test follows links, so a native
        # manifest standing as a link to a regular file with
        # the genuine content still reads through and the
        # scratch layout still holds.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".claude-plugin" / "plugin.json"
            target = Path(tmp) / "native-copy.json"
            shutil.copyfile(path, target)
            path.unlink()
            path.symlink_to(target)
            self.assertEqual(self.problems(root), [])

    def test_a_portable_manifest_linking_to_a_regular_file_holds(self):
        # A portable manifest standing as a link to a regular
        # file with the genuine content reads through the
        # same way and the scratch layout still holds.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / "agent-plugins-package" / "plugin.json"
            target = Path(tmp) / "portable-copy.json"
            shutil.copyfile(path, target)
            path.unlink()
            path.symlink_to(target)
            self.assertEqual(self.problems(root), [])

    def test_a_dangling_native_manifest_link_reads_as_absent(self):
        # A dangling link keeps the absent reading the plain
        # missing shape carries, namely the single extension
        # path problem and no added version problem.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".claude-plugin" / "plugin.json"
            path.unlink()
            path.symlink_to(Path(tmp) / "no-native-manifest.json")
            problems = self.problems(root)
            self.assertEqual(len(problems), 1, problems)
            self.assertIn(".claude-plugin/plugin.json", problems[0])
            self.assertIn("does not resolve", problems[0])

    def test_a_dangling_portable_manifest_link_reads_as_missing(self):
        # A dangling link at the portable path keeps the
        # missing reading a genuinely absent portable
        # manifest carries.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / "agent-plugins-package" / "plugin.json"
            path.unlink()
            path.symlink_to(Path(tmp) / "no-portable-manifest.json")
            problems = self.problems(root)
            self.assertEqual(len(problems), 1, problems)
            self.assertIn("portable manifest", problems[0])
            self.assertIn("is missing", problems[0])

    def test_a_missing_portable_manifest_reads_as_missing(self):
        # A genuinely absent portable manifest keeps its
        # exact current behaviour, namely the single missing
        # problem and nothing else.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            (root / "agent-plugins-package" / "plugin.json").unlink()
            problems = self.problems(root)
            self.assertEqual(len(problems), 1, problems)
            self.assertIn("portable manifest", problems[0])
            self.assertIn("is missing", problems[0])

    def test_a_native_manifest_that_is_not_an_object_fails(self):
        # Round 115 Finding 1. A native manifest that parses to
        # something other than an object carries no version the
        # agreement reading can use, so it must fail by name.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".claude-plugin" / "plugin.json"
            path.write_text('["recognitio"]\n', encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "native manifest is not a JSON object" in problem
                    for problem in problems
                ),
                problems,
            )

    def test_a_native_manifest_with_a_non_string_version_fails(self):
        # Round 115 Finding 1. A version of the wrong type is
        # not a version the portable manifest can be checked
        # against, so the gate names the type instead of
        # comparing across types.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_native(root)
            data["version"] = 130
            self.write_native(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "which is not a string" in problem
                    for problem in problems
                ),
                problems,
            )

    def test_a_missing_native_manifest_reads_as_before(self):
        # A genuinely absent native manifest keeps the verdict
        # the extension path reading already gives it, with no
        # added version problem, because that reading names the
        # absence in its own terms.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            (root / ".claude-plugin" / "plugin.json").unlink()
            problems = self.problems(root)
            self.assertEqual(len(problems), 1, problems)
            self.assertIn(".claude-plugin/plugin.json", problems[0])
            self.assertIn("does not resolve", problems[0])

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
        # agent-plugins-package/ are plugin.json, the skills/
        # tree, and the assets/icon-512.png file. A native
        # platform file placed inside the portable core must
        # fail the gate instead of blending in silence.
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

    def test_a_manifest_inside_a_cache_folder_at_the_root_fails(self):
        # Rounds 286 and 294. A manifest wearing a cache folder
        # name at the package root must stand in the tree census,
        # so the gate names it inside the portable core instead
        # of skipping the folder whole.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            cache = root / "agent-plugins-package" / "__pycache__"
            cache.mkdir(parents=True)
            (cache / "manifest.json").write_text(
                "{}\n", encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("manifest.json" in problem
                    and "portable core" in problem
                    for problem in problems),
                problems,
            )

    def test_a_manifest_inside_a_cache_folder_in_the_skill_fails(self):
        # Rounds 286 and 294. The same shape inside the package
        # skill copy breaks the byte identical file set reading.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            cache = (root / "agent-plugins-package" / "skills"
                     / "recognitio" / "__pycache__")
            cache.mkdir(parents=True)
            (cache / "manifest.json").write_text(
                "{}\n", encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("file set" in problem for problem in problems),
                problems,
            )

    def test_a_bytecode_cache_file_in_a_cache_folder_passes(self):
        # Control. A genuine bytecode cache file, a .pyc file
        # inside a cache folder, stays excluded as build state
        # in both the fixed state and the state before the fix.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            cache = (root / "agent-plugins-package" / "skills"
                     / "recognitio" / "scripts" / "__pycache__")
            cache.mkdir(parents=True)
            (cache / "extract.cpython-311.pyc").write_bytes(
                b"\x42\x0d\x0d\x0a cache bytes")
            self.assertEqual(self.problems(root), [])

    def test_an_inverted_antigravity_extension_note_fails(self):
        # Round 270. The Antigravity extension note states that
        # no primary source names a namespace for the platform.
        # Inverting that account must fail the package gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["extensions"]["com.google.antigravity"]["note"] = (
                "A primary source names a reverse domain "
                "namespace for an Antigravity plugin and the "
                "key is primary."
            )
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("com.google.antigravity" in problem
                    and "note" in problem for problem in problems),
                problems,
            )

    def test_an_inverted_claude_extension_note_fails(self):
        # Round 270. The Claude Code extension note states that
        # the native shapes live at the repo root. Inverting
        # that account must fail the package gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["extensions"]["com.anthropic.claude-code"]["note"] = (
                "The native shapes live in the portable core "
                "itself and replace the repo root shapes."
            )
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("com.anthropic.claude-code" in problem
                    and "note" in problem for problem in problems),
                problems,
            )

    def test_a_deleted_antigravity_extension_namespace_fails(self):
        # Round 270, the deletion shape. The Antigravity
        # extension namespace carries a pinned note, so
        # deleting the namespace whole must fail the package
        # gate by name, not pass in silence as it did while
        # the pin read only a present namespace object.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            del data["extensions"]["com.google.antigravity"]
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("com.google.antigravity" in problem
                    and "note" in problem for problem in problems),
                problems,
            )

    def test_a_non_object_antigravity_extension_namespace_fails(self):
        # Round 270, the wrong type shape. A namespace that
        # stands in the extensions object but is not an object
        # carries no note, so the pin must fail it by name too.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["extensions"]["com.google.antigravity"] = "native"
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("com.google.antigravity" in problem
                    and "note" in problem for problem in problems),
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

    def test_a_brief_without_the_live_install_record_fails(self):
        # The blocker audit of 2026-10-29. The glance card
        # stated that no live install stood in the brief, a
        # wording that predated the Codex probe proof and the
        # Qwen Code run proof. Dropping the record of the two
        # installs must fail the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            brief = root / "docs" / "agent-plugins-brief.md"
            text = brief.read_text(encoding="utf-8")
            brief.write_text(
                text.replace(
                    "stand proven on two hosts",
                    "stand unproven in this brief",
                ),
                encoding="utf-8",
            )
            problems = self.problems(root)
            self.assertTrue(
                any("live installs" in problem
                    for problem in problems),
                problems,
            )

    def test_a_brief_with_the_stale_no_live_install_wording_fails(self):
        # The stale card wording must fail by name even where
        # the live install record stands beside it.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            brief = root / "docs" / "agent-plugins-brief.md"
            text = brief.read_text(encoding="utf-8")
            brief.write_text(
                text + "\nNo live install of the portable "
                "package stands proven.\n",
                encoding="utf-8",
            )
            problems = self.problems(root)
            self.assertTrue(
                any("no live install" in problem
                    for problem in problems),
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

    def test_a_stray_asset_inside_the_portable_core_fails(self):
        # The tree pin admits the one asset the Codex interface
        # names and no other, so a second file under assets/
        # fails instead of riding the admission in silence.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            stray = (
                root / "agent-plugins-package" / "assets" / "stray.png"
            )
            stray.parent.mkdir(parents=True, exist_ok=True)
            stray.write_bytes(b"stray")
            problems = self.problems(root)
            self.assertTrue(
                any("assets/stray.png" in p for p in problems),
                problems,
            )

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
