"""Build 14, the Kimi managed plugin.

The brief at docs/kimi-plugin-brief.md records the Kimi
managed plugin surface as primary, the agents manifest field
with auto discovery, the explicit collision precedence, the
qualified names rule, the hook working directory in both
scopes, the four hook events with a blocking check on each,
the 32KB per systemPrompt field and 64KB total limits, the
unsupported runtime field diagnostics, and the print mode CI
persona, all with derivation notes pinned by the gate at
scripts/check_kimi.py. These tests prove the pin fires for a
real reason on every load bearing claim the round 27 lanes
named. A notification only hook sentence, a plugin wins
collision sentence, a bare name invocation sentence, a server
start directory sentence, an inflated size limit, a dropped
persona, a dropped derivation note, a dropped pin, and a
decision record without a decision 4 statement each fail the
Kimi gate, and the live hook test proves a failed check
stops the turn it gates for each of the four events.
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
        "kimi_" + name, path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestCheckKimi(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_kimi")

    def make_layout(self, tmp):
        """A scratch tree with the brief, the record, and the
        committed fixtures."""
        root = Path(tmp) / "root"
        for rel in (
            "docs/kimi-plugin-brief.md",
            "docs/decisions.md",
        ):
            source = ROOT / rel
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        for rel in (
            "tests/fixtures/kimi-hooks",
            "tests/fixtures/kimi-collision",
        ):
            source = ROOT / rel
            target = root / rel
            shutil.copytree(source, target)
        return root

    def problems(self, root):
        return self.mod.kimi_problems(root)

    def read_brief(self, root):
        return (root / "docs" / "kimi-plugin-brief.md").read_text(
            encoding="utf-8"
        )

    def write_brief(self, root, text):
        (root / "docs" / "kimi-plugin-brief.md").write_text(
            text, encoding="utf-8"
        )

    def break_brief(self, root, old, new, count=1):
        # The gate pins sentences on whitespace normalized text, so
        # the old string names words in order and any run of
        # whitespace in the brief matches. The rest of the brief
        # keeps its line breaks, so the section parsers still see
        # their headings. A test that names an old string the gate
        # cannot see is not a test.
        text = self.read_brief(root)
        pattern = re.escape(old).replace("\\ ", "\\s+")
        broken, hits = re.subn(
            pattern, lambda _match: new, text, count=count
        )
        self.assertNotEqual(broken, text)
        self.assertTrue(hits > 0)
        self.write_brief(root, broken)
        return self.problems(root)

    def plant_sentence(self, root, anchor, sentence):
        # Insert a violating sentence before a rule heading and
        # return the gate problems on the planted brief.
        text = self.read_brief(root)
        self.assertIn(anchor, text)
        self.write_brief(
            root, text.replace(anchor, sentence + "\n\n" + anchor, 1)
        )
        return self.problems(root)

    def test_the_shipped_tree_holds(self):
        self.assertEqual(self.mod.kimi_problems(ROOT), [])

    def test_the_scratch_layout_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            self.assertEqual(self.problems(root), [])

    def test_each_hook_event_carries_a_blocking_check(self):
        # R27-RT-01. The managed plugin wires every hook event
        # through a blocking check. A check that fails must stop
        # the turn it gates, for each of the four events. The
        # fixture check runs live and echoes the event it ran.
        for event in self.mod.HOOK_EVENTS:
            self.assertEqual(
                self.mod.hook_turn_verdict(event, "fail"),
                "blocked",
                event,
            )
            self.assertEqual(
                self.mod.hook_turn_verdict(event, "pass"),
                "proceeds",
                event,
            )

    def test_a_notification_only_sentence_fails(self):
        # R27-RT-01. The four hook events are not notification
        # only. A later edit that says they never block must
        # fail the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.plant_sentence(
                root,
                "### R7. The size limits",
                "The four hook events are notification only and "
                "never block the session.",
            )
            self.assertTrue(
                any("notification only" in p for p in problems),
                problems,
            )

    def test_the_user_agent_wins_the_collision_fixture(self):
        # R27-RT-02. The committed fixture pair carries a user
        # level reviewer and a plugin provided reviewer of the
        # same name. The precedence order must resolve the pair
        # to the user level agent, which loses nothing.
        winner, found = self.mod.fixture_collision_winner(ROOT)
        self.assertIn("user", found)
        self.assertIn("plugin", found)
        self.assertEqual(winner, "user")
        self.assertEqual(self.mod.collision_problems(ROOT), [])

    def test_a_plugin_wins_sentence_fails(self):
        # R27-RT-02. User level, extra, project level, and
        # --agent-file agents win over the plugin provided
        # one. A later edit that grants the plugin agent the
        # win must fail the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.plant_sentence(
                root,
                "### R3. The qualified names rule",
                "A plugin provided agent named reviewer wins over "
                "a user level agent of the same name.",
            )
            self.assertTrue(
                any(
                    "plugin provided agent win" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_bare_name_sentence_fails(self):
        # R27-RT-03. Plugin skills are invoked under their
        # qualified name and the bare name no longer works. A
        # later edit that lets the bare name resolve must fail
        # the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.plant_sentence(
                root,
                "### R4. The hook working directory, kept in two scopes",
                "The reviewer runs when the user invokes review by "
                "its bare skill name.",
            )
            self.assertTrue(
                any("bare name" in p for p in problems),
                problems,
            )

    def test_a_server_start_directory_sentence_fails(self):
        # R27-RT-04. Hooks run in the session's project
        # directory. A later edit that puts them in the server
        # start directory must fail the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.plant_sentence(
                root,
                "### R5. The four hook events",
                "Hooks run in the directory the server was started "
                "from.",
            )
            self.assertTrue(
                any("server start directory" in p for p in problems),
                problems,
            )

    def test_an_inflated_limit_fails(self):
        # R27-RT-05. The limits are 32KB per systemPrompt field
        # and 64KB total. A later edit that inflates them must
        # fail the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            planted = text.replace(
                "limited to 32 KB of UTF-8 bytes",
                "accepts up to 128KB",
                1,
            ).replace(
                "injects at most 64 KB of instructions",
                "injects up to 256KB",
                1,
            )
            self.assertNotEqual(planted, text)
            self.write_brief(root, planted)
            problems = self.problems(root)
            self.assertTrue(
                any("32KB" in p or "64KB" in p for p in problems),
                problems,
            )

    def test_a_dropped_persona_fails(self):
        # R27-RT-06. Print mode CI runs under the reviewer
        # persona. A later edit that drops the persona must
        # fail the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "Print mode CI runs under the reviewer persona "
                "through `kimi -p --agent reviewer`, which selects "
                "the named agent as the main agent for a new "
                "session in print mode.",
                "Print mode CI runs somehow.",
            )
            self.assertTrue(
                any("print mode persona" in p for p in problems),
                problems,
            )

    def test_a_rule_without_a_derivation_note_fails(self):
        # The second packet guard. A rule with no derivation
        # note is a rival instruction source and must fail the
        # gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            anchor = "### R7. The size limits"
            plant = (
                "### R0. A rule with no note\n\n"
                "This rule states something with no derivation.\n\n"
                + anchor
            )
            self.assertIn(anchor, text)
            self.write_brief(root, text.replace(anchor, plant, 1))
            problems = self.problems(root)
            self.assertTrue(
                any("no derivation note" in p for p in problems),
                problems,
            )

    def test_a_markerless_derivation_note_fails(self):
        # R21-ST-01. A note that merely mentions a canonical
        # section title in passing prose, without the
        # deliberate attribution marker, derives from nothing
        # and must fail the gate. A naive substring check would
        # pass this plant, so the test proves the deliberate
        # regex is the one doing the work.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "Derives from canonical skill, Trust and limits, "
                "which fails closed, so a failed hook check stops "
                "the turn. Decision 4 binds this build like every "
                "other build.",
                "Derives from a passing mention of Trust and limits "
                "and nothing at all.",
            )
            self.assertTrue(
                any(
                    "names no canonical skill section" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_dropped_pin_fails(self):
        # A later edit that drops a stated pin must fail the
        # gate instead of drifting in silence.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "an `agents/` directory at the plugin root is auto "
                "discovered",
                "an `agents/` directory may appear somewhere",
            )
            self.assertTrue(
                any("agents field auto discovery" in p
                    for p in problems),
                problems,
            )

    def test_a_decision_record_without_a_statement_fails(self):
        # Every landed build records a decision 4 statement. A
        # decision record without one must fail the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            record = root / "docs" / "decisions.md"
            text = record.read_text(encoding="utf-8")
            self.assertIn("## 24. Build 14", text)
            pattern = re.escape(
                "Decision 4 binds this build like every other build."
            ).replace("\\ ", "\\s+")
            broken, hits = re.subn(
                pattern, "Some other sentence stands here.", text
            )
            self.assertTrue(hits > 0)
            self.assertNotEqual(broken, text)
            record.write_text(broken, encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("decision 4 statement" in p for p in problems),
                problems,
            )


if __name__ == "__main__":
    unittest.main()
