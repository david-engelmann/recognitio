"""Build 7, the Claude Code mod with in process hooks.

The mod's agent.spawn hook gates the reviewer fan out on the review
packet manifest named by RECOGNITIO_PACKET_DIR. These tests execute
the real hooks module under node with stub arguments, the way the
host drives events through hooks, and prove the dispatch contract.
The hook denies an unverified packet, lets a verified packet
through, stays inert with no packet configured, and fails closed
through its .catch handler when the hook crashes. The host side
semantic for a crashed catch handler is pinned as a recorded
limit in the brief. The disabled mods degradation is proved by
running the shipped deterministic scripts with no mod loaded.
"""

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOKS_DIR = ROOT / "hooks"
MODULE = HOOKS_DIR / "register.js"
BRIEF = ROOT / "docs" / "mod-build7.md"


def load_script(name):
    path = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location("mod_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_extractor():
    path = ROOT / ".agents" / "skills" / "recognitio" / "scripts" / "extract.py"
    spec = importlib.util.spec_from_file_location("mod_extract", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HARNESS = r"""
import { register } from "./register.js";

const mode = process.argv[2];
const manifestKind = process.env.MANIFEST_KIND || "verified";
const packetDir = process.env.RECOGNITIO_PACKET_DIR || "";

const manifests = {
  verified: JSON.stringify({ verified: true, files: [] }),
  unverified: JSON.stringify({ verified: false, files: [] }),
};

const $ = {
  env: {
    get: async (name) =>
      name === "RECOGNITIO_PACKET_DIR" ? packetDir || undefined : undefined,
  },
  fs: {
    read: async ({ path }) => {
      if (manifestKind === "unreadable") throw new Error("EACCES: no entry");
      if (manifestKind === "corrupt") return "not json{{{";
      return manifests[manifestKind] ?? manifests.verified;
    },
  },
};
const e = { agentId: "reviewer-1" };
const next = async (ev) => ({ passedThrough: true });

let hooked = null;
const fakeOn = (name, handler) => {
  hooked = { name, handler };
  return { catch: (h) => { hooked.catchHandler = h; } };
};
register(fakeOn, {});

const out = {};
if (mode === "describe") {
  out.event = hooked.name;
  out.hasCatch = typeof hooked.catchHandler === "function";
} else if (mode === "fire") {
  try {
    out.result = await hooked.handler($, e, next);
    out.crashed = false;
  } catch (err) {
    out.result = await hooked.catchHandler($, e, next);
    out.crashed = true;
  }
}
console.log(JSON.stringify(out));
"""


def git(repo, *args):
    result = subprocess.run(
        ["git", "-C", str(repo)] + list(args),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(
            "git %s failed: %s" % (" ".join(args), result.stderr)
        )
    return result.stdout.strip()


class ModDispatchTestCase(unittest.TestCase):
    """The dispatch contract, proved against the real hooks module."""

    def run_harness(self, mode, env=None, module_text=None):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "package.json").write_text('{"type": "module"}')
            (tmp / "register.js").write_text(
                module_text
                if module_text is not None
                else MODULE.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (tmp / "harness.mjs").write_text(HARNESS, encoding="utf-8")
            full_env = dict(os.environ)
            full_env.pop("RECOGNITIO_PACKET_DIR", None)
            full_env.update(env or {})
            result = subprocess.run(
                ["node", "harness.mjs", mode],
                cwd=str(tmp),
                env=full_env,
                capture_output=True,
                text=True,
                timeout=60,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def fire(self, env=None, module_text=None):
        return self.run_harness("fire", env, module_text)

    def test_the_hook_registers_agent_spawn_with_a_catch_handler(self):
        out = self.run_harness("describe")
        self.assertEqual(out["event"], "agent.spawn")
        self.assertTrue(out["hasCatch"])

    def test_a_verified_packet_lets_the_spawn_through(self):
        out = self.fire(
            {"RECOGNITIO_PACKET_DIR": "/packet", "MANIFEST_KIND": "verified"}
        )
        self.assertFalse(out["crashed"])
        self.assertEqual(out["result"], {"passedThrough": True})

    def test_an_unverified_packet_denies_the_spawn(self):
        out = self.fire(
            {"RECOGNITIO_PACKET_DIR": "/packet", "MANIFEST_KIND": "unverified"}
        )
        self.assertFalse(out["crashed"])
        self.assertIn("not verified", out["result"]["deny"])

    def test_no_packet_configured_leaves_the_spawn_alone(self):
        out = self.fire({"MANIFEST_KIND": "verified"})
        self.assertFalse(out["crashed"])
        self.assertEqual(out["result"], {"passedThrough": True})

    def test_an_unreadable_manifest_fails_closed(self):
        out = self.fire(
            {"RECOGNITIO_PACKET_DIR": "/packet", "MANIFEST_KIND": "unreadable"}
        )
        self.assertTrue(out["crashed"])
        self.assertIn("denied rather than let through", out["result"]["deny"])

    def test_a_corrupt_manifest_fails_closed(self):
        out = self.fire(
            {"RECOGNITIO_PACKET_DIR": "/packet", "MANIFEST_KIND": "corrupt"}
        )
        self.assertTrue(out["crashed"])
        self.assertIn("denied rather than let through", out["result"]["deny"])

    def test_a_catch_handler_without_deny_breaks_fail_closed(self):
        # The revert that must fail. A catch handler that answers
        # anything but deny lets a crashed hook through.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'deny: "recognitio: the packet gate hook failed, '
            'so this review spawn is denied rather than let through"',
            'passed: true',
        )
        self.assertNotEqual(broken, text)
        out = self.fire(
            {"RECOGNITIO_PACKET_DIR": "/packet", "MANIFEST_KIND": "unreadable"},
            module_text=broken,
        )
        self.assertTrue(out["crashed"])
        self.assertNotIn("deny", out["result"])

    def test_the_second_layer_fail_open_is_a_recorded_limit(self):
        # The host skips the hook when the catch handler itself
        # throws or times out, and the spawn proceeds. That semantic
        # belongs to the host, so the deterministic proof is that
        # the shipped brief records it as a limit, pinned here and
        # by the gate script.
        import re

        mod = load_script("check_mod")
        text = re.sub(r"\s+", " ", BRIEF.read_text(encoding="utf-8"))
        self.assertIn(mod.LIMIT_SENTENCE, text)


class ModDegradationTestCase(unittest.TestCase):
    """Disabled mods degrade to the deterministic scripts."""

    def test_the_scripts_gate_with_no_mod_loaded(self):
        # No mod is loaded in this test at all. The packet scripts
        # must still gate the review, which is the degradation the
        # brief promises when mods are disabled or unavailable.
        extract = load_extractor()
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            repo = tmp / "repo"
            repo.mkdir()
            (repo / "main.py").write_text("print(1)\n", encoding="utf-8")
            git(repo, "init", "-q")
            git(repo, "config", "user.email", "t@t.t")
            git(repo, "config", "user.name", "t")
            git(repo, "add", "-A")
            git(repo, "commit", "-qm", "base")
            (repo / "main.py").write_text("print(2)\n", encoding="utf-8")
            git(repo, "add", "-A")
            git(repo, "commit", "-qm", "change")
            packet = tmp / "packet"
            code = extract.main(
                [
                    "--range",
                    "HEAD~1..HEAD",
                    "--repo",
                    str(repo),
                    "--out",
                    str(packet),
                ]
            )
            self.assertEqual(code, 0)
            good = subprocess.run(
                [os.environ.get("PYTHON", "python3"),
                 str(ROOT / "scripts" / "check_packet.py"),
                 "--repo", str(repo), str(packet)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(good.returncode, 0, good.stderr)
            manifest = json.loads(
                (packet / "manifest.json").read_text(encoding="utf-8")
            )
            manifest["verified"] = False
            (packet / "manifest.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            bad = subprocess.run(
                [os.environ.get("PYTHON", "python3"),
                 str(ROOT / "scripts" / "check_packet.py"),
                 "--repo", str(repo), str(packet)],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(bad.returncode, 0)


class ModContractTestCase(unittest.TestCase):
    """The structural contract, pinned by the gate script."""

    def setUp(self):
        self.mod = load_script("check_mod")

    def test_the_shipped_mod_holds_its_contract(self):
        self.assertEqual(self.mod.mod_problems(), [])

    def test_the_marketplace_entry_sentence_stands_in_the_brief(self):
        # The gate requires the brief to state the marketplace
        # entry, and this test holds the same sentence the way
        # the limit sentence is held, so a brief that drops the
        # entry fails here in words, not only in the gate.
        import re

        text = re.sub(r"\s+", " ", BRIEF.read_text(encoding="utf-8"))
        self.assertIn(
            "offers the mod as its own marketplace entry, named "
            "recognitio-mod",
            text,
        )

    def test_a_hook_without_catch_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(".catch(catchSpawnFailure)", "")
        self.assertNotEqual(broken, text)
        with tempfile.TemporaryDirectory() as tmp:
            module = Path(tmp) / "register.js"
            module.write_text(broken, encoding="utf-8")
            problems = self.mod.module_problems(module)
        self.assertTrue(
            any("no .catch handler" in p for p in problems), problems
        )

    def test_a_model_call_in_the_hook_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read({ path: manifestPath });",
            "const text = await $.model.complete({ prompt: 'judge' });",
        )
        self.assertNotEqual(broken, text)
        with tempfile.TemporaryDirectory() as tmp:
            module = Path(tmp) / "register.js"
            module.write_text(broken, encoding="utf-8")
            problems = self.mod.module_problems(module)
        self.assertTrue(
            any("$.model.complete" in p for p in problems), problems
        )

    def make_copy_layout(self, tmp):
        root = Path(tmp) / "root"
        hooks = root / "hooks"
        plugin_dir = root / "plugins" / "recognitio-mod"
        copy_hooks = plugin_dir / "hooks"
        hooks.mkdir(parents=True)
        copy_hooks.mkdir(parents=True)
        for name in ("hooks.json", "register.js", "register.test.ts"):
            text = (HOOKS_DIR / name).read_text(encoding="utf-8")
            (hooks / name).write_text(text, encoding="utf-8")
            (copy_hooks / name).write_text(text, encoding="utf-8")
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        (root / "LICENSE").write_text(license_text, encoding="utf-8")
        (plugin_dir / "LICENSE").write_text(
            license_text, encoding="utf-8")
        self.mod.ROOT = root
        self.mod.MOD_PLUGIN_DIR = plugin_dir
        self.mod.MOD_PLUGIN_HOOKS = copy_hooks
        return copy_hooks

    def test_the_marketplace_copy_holds_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.make_copy_layout(tmp)
            self.assertEqual(self.mod.plugin_copy_problems(), [])

    def test_a_drifted_marketplace_copy_fails_the_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy_hooks = self.make_copy_layout(tmp)
            target = copy_hooks / "register.js"
            target.write_text(
                target.read_text(encoding="utf-8") + "\n// drift\n",
                encoding="utf-8",
            )
            problems = self.mod.plugin_copy_problems()
        self.assertTrue(
            any("drifted" in p for p in problems), problems
        )

    def test_a_missing_marketplace_copy_fails_the_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy_hooks = self.make_copy_layout(tmp)
            (copy_hooks / "hooks.json").unlink()
            problems = self.mod.plugin_copy_problems()
        self.assertTrue(
            any("does not mirror" in p for p in problems), problems
        )

    def test_an_extra_file_in_the_copy_fails_the_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy_hooks = self.make_copy_layout(tmp)
            (copy_hooks / "extra.js").write_text(
                "// uncertified\n", encoding="utf-8")
            problems = self.mod.plugin_copy_problems()
        self.assertTrue(
            any("does not mirror" in p for p in problems), problems
        )

    def test_an_uncopied_hooks_file_fails_the_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy_hooks = self.make_copy_layout(tmp)
            originals = copy_hooks.parent.parent.parent / "hooks"
            (originals / "second.js").write_text(
                "// new module\n", encoding="utf-8")
            problems = self.mod.plugin_copy_problems()
        self.assertTrue(
            any("does not mirror" in p for p in problems), problems
        )

    def test_a_missing_mod_license_fails_the_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy_hooks = self.make_copy_layout(tmp)
            (copy_hooks.parent / "LICENSE").unlink()
            problems = self.mod.plugin_copy_problems()
        self.assertTrue(
            any("missing" in p for p in problems), problems
        )

    def test_a_drifted_mod_license_fails_the_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy_hooks = self.make_copy_layout(tmp)
            target = copy_hooks.parent / "LICENSE"
            target.write_text(
                target.read_text(encoding="utf-8") + "\nExtra.\n",
                encoding="utf-8",
            )
            problems = self.mod.plugin_copy_problems()
        self.assertTrue(
            any("different terms" in p for p in problems), problems
        )

    def test_the_struck_onfailure_language_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "return {",
            "const onFailure = 'block'; return {",
            1,
        )
        self.assertNotEqual(broken, text)
        with tempfile.TemporaryDirectory() as tmp:
            module = Path(tmp) / "register.js"
            module.write_text(broken, encoding="utf-8")
            problems = self.mod.module_problems(module)
        self.assertTrue(
            any("onFailure" in p for p in problems), problems
        )


if __name__ == "__main__":
    unittest.main()
