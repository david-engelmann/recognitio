"""Build 12, the Antigravity plugin alteration.

The brief at docs/antigravity-plugin-brief.md records the
Antigravity plugin format, the dated October 9 2026 sunset
evidence, the v0.65.0 stable pin with the docs lag caveat, and
the Antigravity native shapes as a second extensions namespace
beside the portable core, with a PreToolUse hook in the primary
hooks form carrying one command handler that runs the shipped
packet gate script, whose deny, force_ask, and auto_approve
decisions on the packet manifest are the build's declared
mapping, and a shipped plugin manifest carrying only the keys
its primary schema permits. These tests prove the pin fires
for a real reason on every load bearing claim the round 24
lanes named. A dropped sunset halt, a dropped named path, a
pinned page stamp reading, a dropped version pin, a dropped
docs lag caveat, a dropped extension boundary, a dropped
namespace placeholder, a dropped skills folder rule, a dropped
four keys sentence, a missing or unparseable hook file, a hook
without its PreToolUse entry, its matcher, or its command
handler, a hook script that misreads the packet manifest, a
manifest carrying a forbidden key, a missing Antigravity
namespace, a contract statement without a derivation note, a
passing prose derivation mention, a dropped harness mapping, a
dropped degraded state, a dropped Claude Code only negative, a
dropped honest limit, and a decision record without a decision
4 statement each fail the Antigravity gate.
"""

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HOOK_DRIVER = r"""
import importlib.util
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "hook_door", Path(sys.argv[1])
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
for problem in mod.antigravity_problems(Path(sys.argv[2])):
    print(problem)
"""


def load_script(name):
    path = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(
        "antigravity_" + name, path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestCheckAntigravity(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_antigravity")

    def make_layout(self, tmp):
        """A scratch tree with the brief, the record, and the shapes."""
        root = Path(tmp) / "root"
        for rel in (
            "docs/antigravity-plugin-brief.md",
            "docs/decisions.md",
            ".antigravity/plugin.json",
            ".antigravity/hooks.json",
            ".antigravity/scripts/packet_gate.py",
            "agent-plugins-package/plugin.json",
        ):
            source = ROOT / rel
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        return root

    def problems(self, root):
        return self.mod.antigravity_problems(root)

    def run_hook_door(self, root):
        # The FIFO doors run in a subprocess bounded at ten
        # seconds, so a door that reads its FIFO fails this
        # test at the bound instead of hanging the suite.
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    HOOK_DRIVER,
                    str(ROOT / "scripts" / "check_antigravity.py"),
                    str(root),
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except subprocess.TimeoutExpired:
            self.fail(
                "the hook wiring door did not finish within ten "
                "seconds"
            )
        return result.stdout + result.stderr

    def read_brief(self, root):
        return (root / "docs" / "antigravity-plugin-brief.md").read_text(
            encoding="utf-8"
        )

    def write_brief(self, root, text):
        (root / "docs" / "antigravity-plugin-brief.md").write_text(
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

    def read_hooks(self, root):
        path = root / ".antigravity" / "hooks.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def write_hooks(self, root, data):
        path = root / ".antigravity" / "hooks.json"
        path.write_text(json.dumps(data), encoding="utf-8")

    def read_manifest(self, root):
        path = root / "agent-plugins-package" / "plugin.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def write_manifest(self, root, data):
        path = root / "agent-plugins-package" / "plugin.json"
        path.write_text(json.dumps(data), encoding="utf-8")

    def read_plugin(self, root):
        path = root / ".antigravity" / "plugin.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def write_plugin(self, root, data):
        path = root / ".antigravity" / "plugin.json"
        path.write_text(json.dumps(data), encoding="utf-8")

    def test_the_shipped_tree_holds(self):
        self.assertEqual(self.mod.antigravity_problems(ROOT), [])

    def test_the_scratch_layout_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            self.assertEqual(self.problems(root), [])

    def test_a_dropped_sunset_halt_fails(self):
        # R24-RT-03. The October 9 2026 halt is the central dated
        # claim. Dropping it must fail the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "Starting October 9 2026, no new Gemini Code Assist "
                "Standard or Enterprise subscriptions can be purchased",
                "Google may one day change how it sells coding "
                "subscriptions",
            )
            self.assertTrue(
                any("sunset halt" in p for p in problems),
                problems,
            )

    def test_a_dropped_contract_terms_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "Existing subscriptions continue through their "
                "contract terms",
                "Existing subscriptions end at once",
            )
            self.assertTrue(
                any("contract terms" in p for p in problems),
                problems,
            )

    def test_a_dropped_github_split_status_fails(self):
        # Round 36 fold of the plan round 35 section 3 Gemini
        # correction. The GitHub service status stands in the
        # split form, and dropping either half of it fails.
        cases = (
            ("the consumer version deprecated on June 18 2026",
             "the consumer version deprecated at some point",
             "consumer deprecation"),
            ("the enterprise version not affected",
             "every version affected alike",
             "enterprise unaffected"),
        )
        for old, new, needle in cases:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                problems = self.break_brief(root, old, new)
                self.assertTrue(
                    any(needle in p for p in problems),
                    (old, problems),
                )

    def test_a_dropped_renewal_dates_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "License additions and annual renewals run to January "
                "31 2027",
                "Renewals run for a while",
            )
            self.assertTrue(
                any("renewal dates" in p for p in problems),
                problems,
            )

    def test_a_dropped_named_path_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "The page names Antigravity as the forward path for "
                "agentic coding assistance",
                "The page names some path forward",
            )
            self.assertTrue(
                any("named path" in p for p in problems),
                problems,
            )

    def test_a_pinned_page_stamp_reading_fails(self):
        # R24-RT-02. A page stamp is a moving target, so the brief
        # never pins one. An edit that states the stamp pin must
        # fail the gate through the discipline sentence.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "this brief never pins a page stamp, because a stamp "
                "is a moving target",
                "this brief pins the page stamp 2026-10-20 UTC",
            )
            self.assertTrue(
                any("no stamp discipline" in p for p in problems),
                problems,
            )

    def test_a_dropped_v0_65_0_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "v0.65.0 is the stable pin for the Gemini CLI "
                "extension bundle",
                "the newest tag is the pin",
            )
            self.assertTrue(
                any("v0.65.0 pin" in p for p in problems),
                problems,
            )

    def test_a_dropped_docs_lag_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "the brief trusts the releases page over the docs page",
                "the brief trusts whichever page is handy",
            )
            self.assertTrue(
                any("docs lag" in p for p in problems),
                problems,
            )

    def test_a_dropped_pre_release_fails(self):
        # R24-EX-01. The v0.66.0 pre-release is not stable, so the
        # v0.65.0 pin stands. Dropping the sentence must fail.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "it is not stable, so the v0.65.0 pin stands",
                "the pre-release is close enough to pin",
            )
            self.assertTrue(
                any("pre-release" in p for p in problems),
                problems,
            )

    def test_a_dropped_extension_boundary_fails(self):
        # R24-RT-01. The Antigravity native shapes live beside the
        # portable core, never blended into it.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "The Antigravity native shapes live as a second "
                "extensions namespace beside the portable core, never "
                "blended into it",
                "The Antigravity shapes live wherever is convenient",
            )
            self.assertTrue(
                any("extension boundary" in p for p in problems),
                problems,
            )

    def test_a_dropped_namespace_placeholder_fails(self):
        # R24-RT-01. No primary source names the reverse domain
        # namespace, so the brief must keep saying the key is a
        # documented placeholder and not primary.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "the portable manifest uses `com.google.antigravity` "
                "as a documented placeholder",
                "the portable manifest uses the primary Antigravity "
                "namespace",
            )
            self.assertTrue(
                any("namespace placeholder" in p for p in problems),
                problems,
            )

    def test_a_dropped_skills_folder_rule_fails(self):
        # R24-EX-03. Every skill lives inside the plugin's skills
        # folder, and this build ships no second skill copy.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "every skill lives inside the plugin's `skills` folder",
                "skills can live anywhere in the plugin",
            )
            self.assertTrue(
                any("skills folder rule" in p for p in problems),
                problems,
            )

    def test_a_dropped_four_keys_fails(self):
        # R24-SPEC-02. The canonical skill holds exactly four
        # frontmatter keys, never six.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "The canonical skill frontmatter holds exactly four "
                "keys, name, description, context, and background",
                "The canonical skill frontmatter holds six keys",
            )
            self.assertTrue(
                any("four frontmatter keys" in p for p in problems),
                problems,
            )

    def test_a_dropped_deny_mapping_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "`deny` refuses the tool call with a reason when the "
                "packet manifest is missing or not verified",
                "`deny` refuses the tool call sometimes",
            )
            self.assertTrue(
                any("deny mapping" in p for p in problems),
                problems,
            )

    def test_a_dropped_force_ask_mapping_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "`force_ask` holds the tool call for user confirmation "
                "when the packet manifest is unreadable or unparsable",
                "`force_ask` holds the tool call sometimes",
            )
            self.assertTrue(
                any("force_ask mapping" in p for p in problems),
                problems,
            )

    def test_a_dropped_auto_approve_mapping_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "`auto_approve` lets the tool call through without "
                "asking when the packet manifest reads verified",
                "`auto_approve` lets the tool call through sometimes",
            )
            self.assertTrue(
                any("auto_approve mapping" in p for p in problems),
                problems,
            )

    def test_a_dropped_degraded_state_fails(self):
        # R24-RT-03. A missing or unparseable hook file is a planned
        # degraded state, never a silent pass.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "A missing or unparseable hook file is a planned "
                "degraded state, never a silent pass",
                "A missing hook file is fine",
            )
            self.assertTrue(
                any("degraded state" in p for p in problems),
                problems,
            )

    def test_a_dropped_claude_code_only_negative_fails(self):
        # R24-RT-06. The Build 7 mod hooks are Claude Code only on
        # current evidence.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "The Build 7 mod hooks are Claude Code only on current "
                "evidence",
                "The Build 7 mod hooks work everywhere",
            )
            self.assertTrue(
                any("Claude Code only negative" in p for p in problems),
                problems,
            )

    def test_a_dropped_honest_limit_fails(self):
        # R24-RT-04. The harness contract is repo-documented, and
        # the brief claims no product behavior it cannot run.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "the brief claims no product enforcement behavior it "
                "cannot run",
                "the brief guarantees the host blocks every deny",
            )
            self.assertTrue(
                any("honest limit" in p for p in problems),
                problems,
            )

    def test_a_missing_hook_file_fails(self):
        # R24-RT-03. Removing the hook while the brief documents it
        # is the named adversarial angle for this round.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            (root / ".antigravity" / "hooks.json").unlink()
            problems = self.problems(root)
            self.assertTrue(
                any("hooks.json is missing" in p for p in problems),
                problems,
            )

    def test_an_unparseable_hook_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".antigravity" / "hooks.json"
            path.write_text("{not json", encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("does not parse" in p for p in problems),
                problems,
            )

    def hook_entry(self, data):
        return data["recognitio-packet-gate"]["PreToolUse"][0]

    def run_packet_gate(self, root, payload_text, env=None):
        # Run the shipped hook script the way the host runs
        # it, with the event JSON on stdin and no arguments,
        # and return the parsed decision object and the exit
        # code. An env mapping, when given, replaces the
        # inherited environment for that run.
        script = root / ".antigravity" / "scripts" / "packet_gate.py"
        proc = subprocess.run(
            [sys.executable, str(script)],
            input=payload_text,
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
        )
        return json.loads(proc.stdout), proc.returncode

    def gate_payload(self, packet):
        return json.dumps({
            "toolCall": {"name": "invoke_subagent", "args": {}},
            "workspacePaths": [str(packet)],
        })

    def test_a_hook_without_pretooluse_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_hooks(root)
            config = data["recognitio-packet-gate"]
            config["PostToolUse"] = config.pop("PreToolUse")
            self.write_hooks(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("no PreToolUse entry" in p for p in problems),
                problems,
            )

    def test_the_old_abstract_wiring_shape_fails(self):
        # The pre fix wiring stood as one abstract entry in a
        # hooks list with a decisions list and a mapping
        # object and no command anywhere. A host reading the
        # primary form finds no named hook in that shape, so
        # the whole shape must fail by name on its top level
        # keys.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".antigravity" / "hooks.json"
            path.write_text(
                json.dumps({
                    "hooks": [{
                        "decisions": ["deny", "force_ask",
                                      "auto_approve"],
                        "event": "PreToolUse",
                        "mapping": {"deny": "refused"},
                        "matcher": "invoke_subagent",
                    }],
                    "notes": "declared mapping",
                }),
                encoding="utf-8",
            )
            problems = self.problems(root)
            self.assertTrue(
                any("'hooks'" in p for p in problems),
                problems,
            )
            self.assertTrue(
                any("'notes'" in p for p in problems),
                problems,
            )

    def test_a_hook_with_an_extra_top_level_key_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_hooks(root)
            data["notes"] = "a second top level key"
            self.write_hooks(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("'notes'" in p for p in problems),
                problems,
            )

    def test_the_hook_script_denies_a_missing_manifest(self):
        # Statement S3. Deny refuses the tool call when the
        # packet manifest is missing.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            packet = Path(tmp) / "packet"
            packet.mkdir()
            out, code = self.run_packet_gate(
                root, self.gate_payload(packet)
            )
            self.assertEqual(code, 0)
            self.assertEqual(out["decision"], "deny")
            self.assertIn("missing", out["reason"])

    def test_the_hook_script_denies_an_unverified_manifest(self):
        # Statement S3. Deny refuses the tool call when the
        # packet manifest is not verified.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            packet = Path(tmp) / "packet"
            packet.mkdir()
            (packet / "manifest.json").write_text(
                json.dumps({"verified": False}), encoding="utf-8"
            )
            out, code = self.run_packet_gate(
                root, self.gate_payload(packet)
            )
            self.assertEqual(code, 0)
            self.assertEqual(out["decision"], "deny")
            self.assertIn("not verified", out["reason"])

    def test_the_hook_script_force_asks_on_an_unparsable_manifest(self):
        # Statement S4. Force ask holds the tool call when
        # the packet manifest is unreadable or unparsable.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            packet = Path(tmp) / "packet"
            packet.mkdir()
            (packet / "manifest.json").write_text(
                "{not json", encoding="utf-8"
            )
            out, code = self.run_packet_gate(
                root, self.gate_payload(packet)
            )
            self.assertEqual(code, 0)
            self.assertEqual(out["decision"], "force_ask")

    def test_the_hook_script_auto_approves_a_verified_manifest(self):
        # Statement S5. Auto approve lets the tool call
        # through when the packet manifest reads verified.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            packet = Path(tmp) / "packet"
            packet.mkdir()
            (packet / "manifest.json").write_text(
                json.dumps({"verified": True}), encoding="utf-8"
            )
            out, code = self.run_packet_gate(
                root, self.gate_payload(packet)
            )
            self.assertEqual(code, 0)
            self.assertEqual(out["decision"], "auto_approve")

    def test_the_hook_script_force_asks_on_a_malformed_event(self):
        # An event payload the script cannot parse leaves
        # the packet unprovable, so the call is held for
        # user confirmation and the script still exits 0.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            out, code = self.run_packet_gate(root, "not json")
            self.assertEqual(code, 0)
            self.assertEqual(out["decision"], "force_ask")

    def test_a_hook_matcher_drift_fails(self):
        # Round 254. Statement S1 states the entry matcher
        # names invoke_subagent. The exact plant the round
        # used must fail by name.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_hooks(root)
            self.hook_entry(data)["matcher"] = "some_other_tool"
            self.write_hooks(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "matcher" in p and "invoke_subagent" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_hook_without_a_matcher_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_hooks(root)
            del self.hook_entry(data)["matcher"]
            self.write_hooks(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "matcher" in p and "invoke_subagent" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_second_pretooluse_entry_fails(self):
        # Round 254. Statement S1 states the wiring declares
        # one PreToolUse entry, so a second identical entry
        # must fail by name.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_hooks(root)
            entries = data["recognitio-packet-gate"]["PreToolUse"]
            entries.append(dict(entries[0]))
            self.write_hooks(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("one PreToolUse entry" in p for p in problems),
                problems,
            )

    def test_a_hook_without_a_command_handler_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_hooks(root)
            self.hook_entry(data)["hooks"] = []
            self.write_hooks(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("no hooks array" in p for p in problems),
                problems,
            )

    def test_a_hook_with_a_non_command_handler_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_hooks(root)
            self.hook_entry(data)["hooks"][0]["type"] = "prompt"
            self.write_hooks(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("'prompt'" in p for p in problems),
                problems,
            )

    def test_a_hook_command_drift_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_hooks(root)
            self.hook_entry(data)["hooks"][0]["command"] = (
                "python3 ./scripts/other_gate.py"
            )
            self.write_hooks(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("packet_gate.py" in p for p in problems),
                problems,
            )

    def test_a_missing_hook_script_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            (root / ".antigravity" / "scripts"
             / "packet_gate.py").unlink()
            problems = self.problems(root)
            self.assertTrue(
                any("packet gate script" in p for p in problems),
                problems,
            )

    def test_a_manifest_with_a_version_key_fails(self):
        # The primary manifest schema permits the name and
        # the description beside the $schema key and no
        # further key, so a version field in the shipped
        # manifest is a forbidden field and must fail by
        # name at the value the tree once shipped.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_plugin(root)
            data["version"] = "1.3.0"
            self.write_plugin(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("'version'" in p for p in problems),
                problems,
            )

    def test_a_manifest_with_a_notes_key_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_plugin(root)
            data["notes"] = "a declared surface note"
            self.write_plugin(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("'notes'" in p for p in problems),
                problems,
            )

    def test_a_manifest_with_an_extra_key_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_plugin(root)
            data["displayName"] = "Recognitio"
            self.write_plugin(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("'displayName'" in p for p in problems),
                problems,
            )

    def test_a_manifest_without_a_description_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_plugin(root)
            del data["description"]
            self.write_plugin(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("'description'" in p for p in problems),
                problems,
            )

    def test_a_directory_at_the_hook_path_fails_by_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".antigravity" / "hooks.json"
            path.unlink()
            path.mkdir()
            problems = self.problems(root)
            self.assertTrue(
                any("not a regular file" in p for p in problems),
                problems,
            )

    @unittest.skipUnless(
        hasattr(os, "mkfifo"), "no mkfifo on this host"
    )
    def test_a_fifo_at_the_hook_path_refuses_promptly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".antigravity" / "hooks.json"
            path.unlink()
            os.mkfifo(path)
            output = self.run_hook_door(root)
            self.assertIn("not a regular file", output, output)

    @unittest.skipUnless(
        hasattr(os, "mkfifo"), "no mkfifo on this host"
    )
    def test_a_link_to_a_fifo_at_the_hook_path_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".antigravity" / "hooks.json"
            path.unlink()
            os.mkfifo(root / "hook-target")
            path.symlink_to(root / "hook-target")
            output = self.run_hook_door(root)
            self.assertIn("not a regular file", output, output)

    def test_a_dangling_link_at_the_hook_path_fails_by_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".antigravity" / "hooks.json"
            path.unlink()
            path.symlink_to(root / "no-such-hook-target")
            problems = self.problems(root)
            self.assertTrue(
                any("not a regular file" in p for p in problems),
                problems,
            )

    def test_a_hook_file_with_a_repeated_key_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".antigravity" / "hooks.json"
            text = path.read_text(encoding="utf-8")
            broken = text.replace(
                '"matcher"',
                '"matcher": "invoke_subagent", "matcher"',
                1,
            )
            self.assertNotEqual(broken, text)
            path.write_text(broken, encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("does not parse" in p for p in problems),
                problems,
            )

    def test_a_hook_file_with_non_utf8_bytes_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".antigravity" / "hooks.json"
            path.write_bytes(b"\xff\xfe not utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("does not parse" in p for p in problems),
                problems,
            )

    def test_a_disabled_hook_fails(self):
        # Burn-down repair. The gate once allowed an enabled
        # key and checked only that its value was a boolean,
        # so a wiring carrying enabled false passed while a
        # host reading that flag would run no hook at all.
        # The gate certified the wiring claim with the
        # wiring switched off, so the false state must fail
        # by name.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_hooks(root)
            data["recognitio-packet-gate"]["enabled"] = False
            self.write_hooks(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "enabled false" in p and "switched off" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_non_boolean_enabled_fails(self):
        # Burn-down repair. The enabled allowance branch
        # rejects a value that is not a boolean, and no test
        # planted one before this pass.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_hooks(root)
            data["recognitio-packet-gate"]["enabled"] = "yes"
            self.write_hooks(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "enabled value" in p and "not a boolean" in p
                    for p in problems
                ),
                problems,
            )

    def test_an_enabled_true_hook_passes(self):
        # Control. An enabled flag set to true states the
        # wiring stands on, so the shaped allowance keeps
        # passing in the other direction.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_hooks(root)
            data["recognitio-packet-gate"]["enabled"] = True
            self.write_hooks(root, data)
            self.assertEqual(self.problems(root), [])

    def test_an_invalid_timeout_fails(self):
        # Burn-down repair. The handler timeout branch
        # rejects a value that is not a positive integer,
        # and the only earlier timeout test was the passing
        # control, so each bad shape is planted here.
        for bad in (0, -5, True, "30"):
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                data = self.read_hooks(root)
                self.hook_entry(data)["hooks"][0]["timeout"] = bad
                self.write_hooks(root, data)
                problems = self.problems(root)
                self.assertTrue(
                    any(
                        "timeout" in p
                        and "not a positive integer" in p
                        for p in problems
                    ),
                    (bad, problems),
                )

    def test_the_hook_script_reads_the_env_var_manifest_path(self):
        # Burn-down repair. The packet gate script reads
        # the manifest path from the RECOGNITIO_PACKET_MANIFEST
        # environment variable before any workspace path,
        # and the brief documents that branch, but no test
        # set the variable before this pass. A dropped env
        # branch would read the empty workspace instead and
        # deny, so the verified manifest at the named path
        # must earn auto approve here.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            packet = Path(tmp) / "packet"
            packet.mkdir()
            named = Path(tmp) / "named-manifest.json"
            named.write_text(
                json.dumps({"verified": True}), encoding="utf-8"
            )
            env = dict(os.environ)
            env["RECOGNITIO_PACKET_MANIFEST"] = str(named)
            out, code = self.run_packet_gate(
                root, self.gate_payload(packet), env=env
            )
            self.assertEqual(code, 0)
            self.assertEqual(out["decision"], "auto_approve")

    def test_the_hook_script_env_var_manifest_decides_first(self):
        # The env var branch stands before the workspace
        # search, so an unverified manifest at the named
        # path decides even when a workspace path carries a
        # verified one.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            packet = Path(tmp) / "packet"
            packet.mkdir()
            (packet / "manifest.json").write_text(
                json.dumps({"verified": True}), encoding="utf-8"
            )
            named = Path(tmp) / "named-manifest.json"
            named.write_text(
                json.dumps({"verified": False}), encoding="utf-8"
            )
            env = dict(os.environ)
            env["RECOGNITIO_PACKET_MANIFEST"] = str(named)
            out, code = self.run_packet_gate(
                root, self.gate_payload(packet), env=env
            )
            self.assertEqual(code, 0)
            self.assertEqual(out["decision"], "deny")

    def test_the_hook_script_force_asks_on_a_duplicate_key_manifest(
        self,
    ):
        # Burn-down repair. The packet gate script once read
        # the packet manifest with a plain JSON load, so a
        # manifest naming verified twice, false and then
        # true, earned auto approve on the last value. The
        # repo refuses a repeated key in every trusted
        # reader, so that manifest is unparsable here and
        # statement S4 earns force ask.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            packet = Path(tmp) / "packet"
            packet.mkdir()
            (packet / "manifest.json").write_text(
                '{"verified": false, "verified": true}',
                encoding="utf-8",
            )
            out, code = self.run_packet_gate(
                root, self.gate_payload(packet)
            )
            self.assertEqual(code, 0)
            self.assertEqual(out["decision"], "force_ask")

    def test_a_hook_handler_timeout_passes(self):
        # Control. The primary handler form carries an
        # optional timeout in seconds beside the type and
        # the command, so a handler that sets one must keep
        # passing.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_hooks(root)
            self.hook_entry(data)["hooks"][0]["timeout"] = 10
            self.write_hooks(root, data)
            self.assertEqual(self.problems(root), [])

    def test_a_reformatted_hook_file_passes(self):
        # Control. A whitespace and key order rewrite that
        # keeps every pinned value must keep passing, in
        # both the fixed state and the state before the fix.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_hooks(root)
            path = root / ".antigravity" / "hooks.json"
            path.write_text(
                json.dumps(data, indent=4, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            self.assertEqual(self.problems(root), [])

    def test_a_link_to_a_regular_hook_file_passes(self):
        # Control. A link that names a regular file carrying
        # the pinned wiring must keep passing, in both the
        # fixed state and the state before the fix.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".antigravity" / "hooks.json"
            target = root / "hook-wiring-copy.json"
            target.write_bytes(path.read_bytes())
            path.unlink()
            path.symlink_to(target)
            self.assertEqual(self.problems(root), [])

    def test_a_missing_antigravity_namespace_fails(self):
        # R24-RT-01 and R24-RT-02. The Build 12 manifest must
        # declare the Antigravity shapes under the new namespace.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            del data["extensions"]["com.google.antigravity"]
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("com.google.antigravity" in p for p in problems),
                problems,
            )

    def test_a_statement_without_a_derivation_note_fails(self):
        # The second packet guard. Every contract statement
        # carries a derivation note naming its source.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            pattern = re.escape(
                "Derives from canonical skill, Stamping the gate "
                "report and Completeness discipline"
            ).replace("\\ ", "\\s+")
            broken, hits = re.subn(
                pattern, "Derives from nothing in particular", text
            )
            self.assertTrue(hits > 0)
            self.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "S3" in p and "derivation note" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_passing_prose_derivation_mention_fails(self):
        # R21-ST-01. A canonical section title mentioned in passing
        # prose does not count as a derivation source.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            old = (
                "Derives from canonical skill, Stamping the gate "
                "report and Completeness discipline, which read "
                "\"Never let a review begin on a packet whose verified "
                "flag is false.\""
            )
            new = (
                "Derives from the general idea that Stamping the gate "
                "report is a nice section title to mention in passing."
            )
            pattern = re.escape(old).replace("\\ ", "\\s+")
            broken, hits = re.subn(pattern, new, text)
            self.assertTrue(hits > 0)
            self.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "S3" in p and "derivation note" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_dropped_staging_copy_sentence_fails(self):
        # Burn-down repair, spec Minor 2. The round 39 rider
        # priced keeping the folder only with the brief
        # stating the pair is a staging copy a user places
        # into a plugin directory, with the copy step
        # written out. Dropping that statement must fail.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "The shipped pair is a staging copy a user "
                "places into a plugin directory",
                "The shipped pair is the installed plugin",
            )
            self.assertTrue(
                any("staging copy" in p for p in problems),
                problems,
            )

    def test_a_dropped_brief_enforcement_correction_fails(self):
        # Burn-down repair, spec Minor 1. The brief summary
        # carried the same never enforce sentence as the
        # record, so it carries the same dated correction.
        # Dropping the correction must fail.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "The hook wiring now enforces the contract "
                "through the shipped packet gate script",
                "The hook wiring documents the contract",
            )
            self.assertTrue(
                any(
                    "hook enforcement correction" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_missing_decision_22_correction_fails(self):
        # Burn-down repair, spec Minor 1. Decision 22 kept
        # stating in the present tense that the wiring
        # never enforces the contract while the shipped
        # wiring runs the packet gate script. The round 39
        # pricing ordered a dated correction appended with
        # the recorded text left standing, so removing the
        # correction from the record must fail by name.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / "docs" / "decisions.md"
            text = path.read_text(encoding="utf-8")
            start = text.find("## 22. Build 12")
            self.assertTrue(start >= 0)
            head, tail = text[:start], text[start:]
            tail = tail.replace(
                "now enforces the contract through the "
                "shipped\npacket gate script",
                "documents the contract",
            )
            self.assertNotEqual(tail, text[start:])
            path.write_text(head + tail, encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("dated correction" in p for p in problems),
                problems,
            )

    def test_a_missing_decision_22_record_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / "docs" / "decisions.md"
            text = path.read_text(encoding="utf-8")
            start = text.find("## 22. Build 12")
            self.assertTrue(start >= 0)
            match = re.search(r"(?m)^## ", text[start + 1:])
            end = start + 1 + match.start() if match else len(text)
            path.write_text(
                text[:start] + text[end:], encoding="utf-8"
            )
            problems = self.problems(root)
            self.assertTrue(
                any("Build 12 decision record" in p for p in problems),
                problems,
            )

    def test_a_decision_record_without_a_decision_4_statement_fails(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / "docs" / "decisions.md"
            text = path.read_text(encoding="utf-8")
            start = text.find("## 22. Build 12")
            self.assertTrue(start >= 0)
            head, tail = text[:start], text[start:]
            tail = tail.replace(
                "Decision 4 binds the build.", "The build is unbound."
            )
            self.assertNotEqual(tail, text[start:])
            path.write_text(head + tail, encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("decision 4 statement" in p for p in problems),
                problems,
            )
