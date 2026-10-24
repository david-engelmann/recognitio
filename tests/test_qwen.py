"""Build 15, the Qwen Code marketplace presence build.

The brief at docs/qwen-code-brief.md records the Qwen
figure basis and scope table with no single figure as
the Qwen figure, the wrapper exits 0 1 and 3 kept
separate from the internal verify exit 4, the Agent
Plugins v1 matrix in full, the Qoder and scoped npm
routes, the prefixed naming rule with its cancellation
exception, the shared skills alias with its precedence,
the conversion fidelity record with runtime invocation
left UNVERIFIED, the bundled CLI version from the
primary releases listing, and the conditional
publication draft with no listing file shipped, all
with derivation notes pinned by the gate at
scripts/check_qwen.py. These tests prove the pin fires
for a real reason on every load bearing claim the build
names. A dropped pin, a dropped derivation note, a
plant sentence that passes, and a correct control
sentence that fails each fail the Qwen gate.
"""

import importlib.util
import re
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    path = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(
        "qwen_" + name, path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PLANTS = (
    "a dozen concurrent reviewers at top effort",
    "nineteen parallel workers in practice",
    "sixteen simultaneous review bots run every high effort review",
    "the headless wrapper returns four when the verification budget runs out",
    "wrapper exit table: 0, 1, 3, and also 4 for blocking review",
    "skills.enabled turns the skill on under the bare name",
    "skills.disabled blocks only the prefixed spelling",
    "on native load, commands, agents and hooks all light up, and legacy SSE servers activate",
    "the .agents/skills copy may drift from the package copy",
    "any npm package installs, unscoped names work too",
    "the converted bundle is proven to run the full packet workflow in Qwen",
    "sixteen agents working side by side",
    "a dozen agents running together",
    "16 agents at once on a large review",
    "the outer gate exits with code 4 on refusal",
    "internal verify exit 4 is listed as a wrapper exit",
    "Qwen activates hooks for the recognitio plugin",
    "Qwen activates commands for the recognitio plugin",
    "Qwen activates agents for the recognitio plugin",
    "Qwen activates client namespaces for the recognitio plugin",
    "Qwen activates legacy SSE MCP for the recognitio plugin",
    "in Qwen, skills at .agents/skills are automatically discovered across repositories",
    "Qwen loads the .agents/skills copy as the winning copy on collision",
)

CONTROL = (
    "Wrapper exits are 0, 1, and 3. "
    "Exit 4 is internal verify only. "
    "skills.disabled blocks either spelling, "
    "skills.enabled opts in under the prefixed name only."
)


class TestCheckQwen(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_qwen")

    def make_layout(self, tmp):
        """A scratch tree with the brief and the record."""
        root = Path(tmp) / "root"
        for rel in (
            "docs/qwen-code-brief.md",
            "docs/decisions.md",
            "CHANGELOG.md",
            "README.md",
        ):
            source = ROOT / rel
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        return root

    def problems(self, root):
        return self.mod.qwen_problems(root)

    def read_brief(self, root):
        return (root / "docs" / "qwen-code-brief.md").read_text(
            encoding="utf-8"
        )

    def write_brief(self, root, text):
        (root / "docs" / "qwen-code-brief.md").write_text(
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

    def test_the_shipped_tree_holds(self):
        self.assertEqual(self.mod.qwen_problems(ROOT), [])

    def test_the_scratch_layout_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            self.assertEqual(self.problems(root), [])

    def test_every_plant_fails(self):
        for plant in PLANTS:
            problems = self.mod.negative_problems(plant)
            self.assertTrue(problems, plant)

    def test_the_control_passes(self):
        self.assertEqual(self.mod.negative_problems(CONTROL), [])

    def test_the_number_normalisation_fires(self):
        problems = self.mod.negative_problems(
            "twelve parallel agents at high effort"
        )
        self.assertTrue(problems)

    def test_a_dropped_figure_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "conflicting summary and is not used",
                "conflicting summary and is used",
            )
            self.assertTrue(
                any("figure" in p or "commands page" in p for p in problems),
                problems,
            )

    def test_a_dropped_wrapper_exit_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "It completed with REQUEST_CHANGES and fail-on request-changes set",
                "It completed with REQUEST_CHANGES and no fail-on set",
            )
            self.assertTrue(
                any("wrapper exit 3" in p for p in problems),
                problems,
            )

    def test_a_dropped_internal_verify_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "default 1200 and 0 disabling the gate",
                "default 900 and never disabling the gate",
            )
            self.assertTrue(
                any("compose floor" in p for p in problems),
                problems,
            )

    def test_a_dropped_not_activated_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "Commands, agents, hooks, client namespaces, and legacy SSE MCP are not activated",
                "Commands, agents, hooks, client namespaces, and legacy SSE MCP are activated",
            )
            self.assertTrue(
                any("not activated" in p for p in problems),
                problems,
            )

    def test_a_dropped_cancellation_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "The cancellation exception holds for one bare pair",
                "No cancellation exception holds for any bare pair",
            )
            self.assertTrue(
                any("cancellation" in p for p in problems),
                problems,
            )

    def test_a_dropped_precedence_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "the one in `.qwen/skills/` wins",
                "the one in `.agents/skills/` wins",
            )
            self.assertTrue(
                any("precedence" in p or "Qwen skills wins" in p for p in problems),
                problems,
            )

    def test_a_dropped_runtime_unverified_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "Runtime invocation stays UNVERIFIED",
                "Runtime invocation is fully verified",
            )
            self.assertTrue(
                any("runtime UNVERIFIED" in p for p in problems),
                problems,
            )

    def test_a_dropped_no_listing_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "No Qwen listing file ships in this round",
                "A Qwen listing file ships in this round",
                count=0,
            )
            self.assertTrue(
                any("no listing file" in p for p in problems),
                problems,
            )

    def test_a_dropped_derivation_note_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            first = text.find("Derives from")
            self.assertTrue(first > 0)
            broken = text[:first] + text[first:].replace(
                "Derives from", "Noted from", 1
            )
            self.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("derivation" in p for p in problems),
                problems,
            )

    def test_a_dropped_r4_qoder_path_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "qwen extensions install ./recognitio-qwen/qoder-input",
                "qwen extensions install ./recognitio-qwen/agent-plugins-package",
            )
            self.assertTrue(
                any("R4 Qoder install path" in p for p in problems),
                problems,
            )

    def test_a_dropped_qoder_activation_unverified_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "Activation of preserved Qoder commands and agents in Qwen stays UNVERIFIED",
                "Activation of preserved Qoder commands and agents in Qwen is verified",
            )
            self.assertTrue(
                any("Qoder activation UNVERIFIED" in p for p in problems),
                problems,
            )

    def test_a_merged_exit_table_fails(self):
        problems = self.mod.negative_problems(
            "wrapper exit table: 0, 1, 3, and also 4 for blocking review"
        )
        self.assertTrue(problems)

    def test_the_three_naming_cases(self):
        self.assertTrue(self.mod.negative_problems(
            "skills.disabled blocks only the prefixed spelling"))
        self.assertTrue(self.mod.negative_problems(
            "skills.enabled turns the skill on under the bare name"))
        self.assertEqual(self.mod.negative_problems(
            "skills.disabled blocks either spelling, "
            "skills.enabled opts in under the prefixed name only."), [])

    def test_a_publication_promise_fails(self):
        problems = self.mod.negative_problems(
            "submit the skill through the central Qwen marketplace approval queue"
        )
        self.assertTrue(problems)
