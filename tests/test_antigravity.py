"""Build 12, the Antigravity plugin alteration.

The brief at docs/antigravity-plugin-brief.md records the
Antigravity plugin format, the dated October 9 2026 sunset
evidence, the v0.65.0 stable pin with the docs lag caveat, and
the Antigravity native shapes as a second extensions namespace
beside the portable core, with a PreToolUse hook carrying the
deny, force_ask, and auto_approve decisions as the build's
declared mapping. These tests prove the pin fires for a real
reason on every load bearing claim the round 24 lanes named. A
dropped sunset halt, a dropped named path, a pinned page stamp
reading, a dropped version pin, a dropped docs lag caveat, a
dropped extension boundary, a dropped namespace placeholder, a
dropped skills folder rule, a dropped four keys sentence, a
missing or unparseable hook file, a hook without its PreToolUse
entry or one of its three decisions, a missing Antigravity
namespace, a contract statement without a derivation note, a
passing prose derivation mention, a dropped harness mapping, a
dropped degraded state, a dropped Claude Code only negative, a
dropped honest limit, and a decision record without a decision
4 statement each fail the Antigravity gate.
"""

import importlib.util
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
            "agent-plugins-package/plugin.json",
        ):
            source = ROOT / rel
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        return root

    def problems(self, root):
        return self.mod.antigravity_problems(root)

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

    def test_a_hook_without_pretooluse_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_hooks(root)
            data["hooks"][0]["event"] = "SessionStart"
            self.write_hooks(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("no PreToolUse entry" in p for p in problems),
                problems,
            )

    def test_a_hook_without_deny_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_hooks(root)
            decisions = data["hooks"][0]["decisions"]
            decisions.remove("deny")
            self.write_hooks(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("'deny'" in p for p in problems),
                problems,
            )

    def test_a_hook_without_force_ask_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_hooks(root)
            decisions = data["hooks"][0]["decisions"]
            decisions.remove("force_ask")
            self.write_hooks(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("'force_ask'" in p for p in problems),
                problems,
            )

    def test_a_hook_without_auto_approve_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_hooks(root)
            decisions = data["hooks"][0]["decisions"]
            decisions.remove("auto_approve")
            self.write_hooks(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("'auto_approve'" in p for p in problems),
                problems,
            )

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
