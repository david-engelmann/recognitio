"""Round 183 sweep, the sibling FIFO doors of the gate scripts.

Round 183 graded the fan-out, headless and package brief
doors, and recorded that the sibling gates share the same
plain read shape at fixed paths under a root. Every door
in this file was executed with a planted FIFO before the
fix and hung, and each one now refuses promptly behind a
regular file test. Every shape runs in a subprocess with
a ten second bound, so a door that still reads its FIFO
fails one test at the bound instead of hanging the suite.
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DRIVER = r"""
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

script = Path(sys.argv[1])
case = sys.argv[2]
work = Path(sys.argv[3])
repo = Path(sys.argv[4])
spec = importlib.util.spec_from_file_location("door_under_test", script)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def fifo(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    os.mkfifo(path)
    return path


def copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return dst


def show(problems):
    for problem in problems:
        print(problem)


if case == "helper":
    mode = sys.argv[5]
    door = work / "door.txt"
    if mode == "fifo":
        fifo(door)
    elif mode == "regular":
        door.write_text("content\n", encoding="utf-8")
    elif mode == "linkfifo":
        fifo(work / "target")
        door.symlink_to(work / "target")
    elif mode == "linkregular":
        (work / "target").write_text("content\n", encoding="utf-8")
        door.symlink_to(work / "target")
    print(repr(mod.read_text(door)))
elif case == "version_read":
    print(repr(mod.read(fifo(work / "door.txt"))))
elif case == "codex_brief":
    fifo(work / "docs/codex-review-brief.md")
    show(mod.brief_problems(work))
elif case == "codex_decisions":
    fifo(work / "docs/decisions.md")
    show(mod.decision_problems(work))
elif case == "cp_load_json":
    fifo(work / "x.json")
    problems = []
    mod.load_json(work, "x.json", problems, "thing")
    show(problems)
elif case.startswith("cp_brief_"):
    rel = {
        "brief": "docs/codex-plugin-brief.md",
        "decisions": "docs/decisions.md",
        "changelog": "CHANGELOG.md",
        "docsreadme": "docs/README.md",
        "readme": "README.md",
        "agents": "AGENTS.md",
    }[case[len("cp_brief_"):]]
    for other in ("docs/codex-plugin-brief.md", "docs/decisions.md",
                  "CHANGELOG.md", "docs/README.md", "README.md",
                  "AGENTS.md"):
        if other != rel:
            copy(repo / other, work / other)
    fifo(work / rel)
    problems = []
    mod.brief_problems(work, problems)
    show(problems)
elif case == "cp_asset_brand":
    assets = work / "agent-plugins-package/assets"
    assets.mkdir(parents=True)
    (assets / "icon-512.png").write_bytes(b"x")
    fifo(work / "docs/brand/recognitio-icon-512.png")
    problems = []
    mod.asset_problems(work, problems)
    show(problems)
elif case == "cp_asset_icon":
    fifo(work / "agent-plugins-package/assets/icon-512.png")
    copy(repo / "docs/brand/recognitio-icon-512.png",
         work / "docs/brand/recognitio-icon-512.png")
    problems = []
    mod.asset_problems(work, problems)
    show(problems)
elif case == "cp_yaml_canonical":
    fifo(work / ".agents/skills/recognitio/agents/openai.yaml")
    problems = []
    mod.openai_yaml_problems(work, "accent", problems)
    show(problems)
elif case == "cp_yaml_copy":
    copy(repo / ".agents/skills/recognitio/agents/openai.yaml",
         work / ".agents/skills/recognitio/agents/openai.yaml")
    fifo(work / "agent-plugins-package/skills/recognitio"
         "/agents/openai.yaml")
    problems = []
    mod.openai_yaml_problems(work, "accent", problems)
    show(problems)
elif case == "discovery_load":
    fifo(work / "x.json")
    problems = []
    mod.load_manifest(work, "x.json", problems)
    show(problems)
elif case == "submissions_load":
    fifo(work / "x.json")
    problems = []
    mod.load_manifest(work, "x.json", problems)
    show(problems)
elif case == "submissions_pack":
    fifo(work / "docs/submission-cursor.md")
    problems = []
    mod.pack_problems(work, "1.0", problems)
    show(problems)
elif case == "persona_manifest":
    fifo(work / ".claude-plugin/plugin.json")
    show(mod.manifest_problems(work))
elif case == "persona_agent":
    copy(repo / ".claude-plugin/plugin.json",
         work / ".claude-plugin/plugin.json")
    shutil.copytree(repo / "agents", work / "agents", symlinks=True)
    target = work / "agents/reviewer.md"
    if target.exists() or target.is_symlink():
        target.unlink()
    fifo(target)
    show(mod.persona_problems(work))
elif case == "vacuity":
    fifo(work / "tests/test_planted.py")
    show(mod.vacuity_problems(work))
elif case == "mod_hooks":
    mod.HOOKS_JSON = fifo(work / "hooks.json")
    path, problem = mod.module_path()
    print(problem)
elif case == "mod_brief":
    mod.BRIEF = fifo(work / "brief.md")
    show(mod.brief_problems())
elif case == "mod_module":
    show(mod.module_problems(fifo(work / "register.js")))
else:
    raise SystemExit("unknown case " + case)
"""

HELPER_SCRIPTS = (
    "check_antigravity",
    "check_brand",
    "check_coderabbit",
    "check_copilot",
    "check_cursor",
    "check_devin",
    "check_kimi",
    "check_qwen",
    "check_zcode",
)


@unittest.skipUnless(hasattr(os, "mkfifo"), "no mkfifo on this host")
class FifoDoorTestCase(unittest.TestCase):
    """One bounded subprocess per planted FIFO door."""

    def run_door(self, script, case, *extra):
        with tempfile.TemporaryDirectory() as tmp:
            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        DRIVER,
                        str(ROOT / "scripts" / (script + ".py")),
                        case,
                        tmp,
                        str(ROOT),
                        *extra,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
            except subprocess.TimeoutExpired:
                self.fail(
                    "the %s door %s did not finish within ten "
                    "seconds" % (script, case)
                )
            return result.stdout + result.stderr

    def assert_cannot_read(self, script, case, *extra):
        output = self.run_door(script, case, *extra)
        self.assertTrue(
            "cannot read" in output or "cannot be read" in output,
            output,
        )
        self.assertIn("not a regular file", output, output)

    def test_the_shared_read_helpers_refuse_a_fifo(self):
        # The brief gates read their fixed paths through one
        # read_text helper each, so the helper is the door
        # every one of those readings stands behind. A FIFO
        # draws the helper its unreadable shape, which the
        # callers already turn into named problems.
        for script in HELPER_SCRIPTS:
            with self.subTest(script=script):
                output = self.run_door(script, "helper", "fifo")
                self.assertIn("None", output, output)

    def test_the_shared_read_helpers_refuse_a_link_to_a_fifo(self):
        for script in HELPER_SCRIPTS:
            with self.subTest(script=script):
                output = self.run_door(
                    script, "helper", "linkfifo")
                self.assertIn("None", output, output)

    def test_the_shared_read_helpers_read_a_regular_file(self):
        for script in HELPER_SCRIPTS:
            with self.subTest(script=script):
                output = self.run_door(
                    script, "helper", "regular")
                self.assertIn("content", output, output)

    def test_the_shared_read_helpers_read_through_a_link(self):
        for script in HELPER_SCRIPTS:
            with self.subTest(script=script):
                output = self.run_door(
                    script, "helper", "linkregular")
                self.assertIn("content", output, output)

    def test_the_version_read_helper_refuses_a_fifo(self):
        output = self.run_door("check_version", "version_read")
        self.assertIn("None", output, output)

    def test_the_codex_brief_door_refuses_a_fifo(self):
        self.assert_cannot_read("check_codex", "codex_brief")

    def test_the_codex_decisions_door_refuses_a_fifo(self):
        self.assert_cannot_read("check_codex", "codex_decisions")

    def test_the_codex_plugin_json_door_refuses_a_fifo(self):
        self.assert_cannot_read("check_codex_plugin", "cp_load_json")

    def test_the_codex_plugin_record_doors_refuse_a_fifo(self):
        for key in ("brief", "decisions", "changelog",
                    "docsreadme", "readme", "agents"):
            with self.subTest(door=key):
                self.assert_cannot_read(
                    "check_codex_plugin", "cp_brief_" + key)

    def test_the_codex_plugin_asset_doors_refuse_a_fifo(self):
        self.assert_cannot_read(
            "check_codex_plugin", "cp_asset_brand")
        self.assert_cannot_read(
            "check_codex_plugin", "cp_asset_icon")

    def test_the_codex_plugin_yaml_doors_refuse_a_fifo(self):
        self.assert_cannot_read(
            "check_codex_plugin", "cp_yaml_canonical")
        self.assert_cannot_read(
            "check_codex_plugin", "cp_yaml_copy")

    def test_the_discovery_manifest_door_refuses_a_fifo(self):
        self.assert_cannot_read("check_discovery", "discovery_load")

    def test_the_submissions_manifest_door_refuses_a_fifo(self):
        self.assert_cannot_read(
            "check_submissions", "submissions_load")

    def test_the_submissions_pack_door_refuses_a_fifo(self):
        self.assert_cannot_read(
            "check_submissions", "submissions_pack")

    def test_the_persona_manifest_door_refuses_a_fifo(self):
        self.assert_cannot_read("check_persona", "persona_manifest")

    def test_the_persona_agent_door_refuses_a_fifo(self):
        output = self.run_door("check_persona", "persona_agent")
        self.assertIn("cannot read it", output, output)
        self.assertIn("not a regular file", output, output)

    def test_the_vacuity_door_refuses_a_fifo(self):
        output = self.run_door("check_test_vacuity", "vacuity")
        self.assertIn("does not parse", output, output)
        self.assertIn("not a regular file", output, output)

    def test_the_mod_hooks_door_refuses_a_fifo(self):
        output = self.run_door("check_mod", "mod_hooks")
        self.assertIn("cannot read hooks/hooks.json", output,
                      output)
        self.assertIn("not a regular file", output, output)

    def test_the_mod_brief_door_refuses_a_fifo(self):
        output = self.run_door("check_mod", "mod_brief")
        self.assertIn("cannot read docs/mod-build7.md", output,
                      output)
        self.assertIn("not a regular file", output, output)

    def test_the_mod_module_door_refuses_a_fifo(self):
        self.assert_cannot_read("check_mod", "mod_module")


if __name__ == "__main__":
    unittest.main()
