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
    "Qwen fields agents working side by side, 16 of them on a large review",
    "Qwen runs 16 agents working concurrently on a large review",
    "Qwen runs 16 agents simultaneously on a large review",
    "Qwen runs 16 agents in tandem on a large review",
    "Qwen runs 16 agents at the same time on a large review",
    "Qwen runs 18 agents at once on a large review",
    "Qwen runs 16 agents, each reviewing a different file in the same repository under the same deadline, working side by side",
    "The outer shell exits with code 4 on refusal",
    "The outer layer exits with code 4 on refusal",
    "Qwen enables hooks for the recognitio plugin",
    "Qwen turns on hooks for the recognitio plugin",
    "Qwen activates hooks for the recognitio plugin, provenance unverified",
    "Qwen activates, for the recognitio plugin and its companion tools in the same review, the hooks",
    "Qwen discovers skills at .agents/skills automatically across repositories",
    "The winning copy on collision is the .agents/skills copy",
    "Qwen prefers the .agents/skills copy on collision",
    "The .qwen/skills copy loses on collision",
    "Qwen runs 16 agents side-by-side on a large review",
    "Qwen runs 16 side-by-side agents on a large review",
    "Qwen runs 16 agents shoulder to shoulder on a large review",
    "The shell exits with code 4 on refusal",
    "Qwen switches hooks on for the recognitio plugin",
    "Qwen powers up hooks for the recognitio plugin",
    "Qwen picks up skills at .agents/skills automatically across repositories",
    "The .agents/skills copy outranks the .qwen/skills copy on collision",
    "Qwen runs 16 agents\nworking side by side on a large review",
    "Qwen runs 16 agents alongside each other on a large review",
    "Qwen brings hooks online for the recognitio plugin",
    "Qwen finds skills at .agents/skills automatically across repositories",
    "The .qwen/skills copy is beaten on collision",
    "Qwen runs twenty parallel agents on a large review",
    "Qwen runs two parallel agents on a large review",
    "Qwen runs 16 reviewers spread across the whole set of "
    "files in the review packet for this change, with each "
    "one checking a different part of the diff in full, "
    "together",
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

    def test_the_shipped_qoder_unverified_sentence_passes(self):
        self.assertEqual(self.mod.negative_problems(
            "Activation of preserved Qoder commands and agents "
            "in Qwen stays UNVERIFIED."), [])

    def test_the_wrapped_qoder_unverified_sentence_passes(self):
        self.assertEqual(self.mod.negative_problems(
            "Activation of preserved Qoder commands and agents\n"
            "in Qwen stays UNVERIFIED."), [])

    def test_false_positive_probes_pass(self):
        probes = (
            "Qwen runs 5 reviewers on a small review.",
            "The wrapper supports 4 tools.",
        )
        for probe in probes:
            self.assertEqual(self.mod.negative_problems(probe), [], probe)

    def test_gate_review_split_figure_plants_fail(self):
        # Gate review repair. The figure family read one
        # sentence at a time, so the review split the agent
        # count and the simultaneity word across a sentence
        # boundary in both orders and each half passed. The
        # family now reads the pairs of prose sentences
        # that stand next to each other beside the singles.
        for plant in (
            "Qwen runs 16 agents. They work together on a "
            "large review.",
            "Together, they check the whole review. Qwen "
            "runs 16 agents on it.",
        ):
            problems = self.mod.negative_problems(plant)
            self.assertTrue(
                any("figure plant" in p for p in problems),
                (plant, problems),
            )

    def test_gate_review_unbound_figure_sentence_passes(self):
        # Gate review repair. The sentence scope span fired
        # on any number in a sentence with a simultaneity
        # word, including a true record sentence whose
        # number counted source pages far from the word
        # together. A figure now has to bind to a generic
        # agent noun before the sentence can state one.
        problems = self.mod.negative_problems(
            "Qwen lists 4 source pages in the basis and "
            "scope table at the head of this brief, and each "
            "page was read on its own date and is cited for "
            "a different claim in a different section of the "
            "record that follows, and the basis table and "
            "the scope table are presented together in that "
            "record."
        )
        self.assertFalse(
            any("figure plant" in p for p in problems),
            problems,
        )

    def test_passive_beaten_fails_and_active_beats_passes(self):
        # S2. Only the passive beaten form states losing, so
        # the active beats form that states the shipped
        # precedence must pass while every passive form fails.
        self.assertEqual(self.mod.negative_problems(
            "The .qwen/skills copy beats the .agents/skills "
            "copy on collision."), [])
        for plant in (
            "The .qwen/skills copy is beaten on collision.",
            "The .qwen/skills copy was beaten on collision.",
            "The .qwen/skills copy will be beaten on collision.",
        ):
            self.assertTrue(self.mod.negative_problems(plant), plant)

    def test_negated_bring_online_passes(self):
        # S3. The negation guard must cover bring just as it
        # covers turn, while the positive bring form still fails.
        self.assertEqual(self.mod.negative_problems(
            "Qwen does not bring hooks online for the "
            "recognitio plugin."), [])
        self.assertEqual(self.mod.negative_problems(
            "Qwen does not turn hooks on for the "
            "recognitio plugin."), [])
        self.assertTrue(self.mod.negative_problems(
            "Qwen brings hooks online for the "
            "recognitio plugin."))

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

    def test_round37_figure_split_across_three_sentences_fails(self):
        # R37-RT-10. The count and the simultaneity word
        # stand two sentences apart with a filler between
        # them, and the three sentence window must catch
        # the figure claim.
        problems = self.mod.negative_problems(
            "Qwen runs 16 agents for this change. The "
            "packet lists each file in the change beside "
            "its diff. They work together on the review."
        )
        self.assertTrue(problems)

    def test_round37_guard_word_no_longer_shelters_a_figure(self):
        # R37-RT-10. A basis label on the neighbouring
        # sentence exempts only its own sentence now, so a
        # planted figure beside it still fails.
        problems = self.mod.negative_problems(
            "Qwen runs 16 agents for this change. They work "
            "together on the review, as the roster "
            "narrative records."
        )
        self.assertTrue(problems)

    def test_round37_full_conversion_byte_fidelity_claim_fails(self):
        # R37-RT-01. Byte fidelity holds for the round 33
        # skill tree installs only, so a byte identical
        # claim for a full conversion must fail.
        problems = self.mod.negative_problems(
            "The full bundle conversion output is byte "
            "identical to the canonical tree."
        )
        self.assertTrue(problems)

    def test_round37_fidelity_record_pins_hold(self):
        # R37-RT-01. Dropping any of the six round 37
        # record sentences from the brief fails the gate,
        # so the conversion account cannot quietly lose
        # one of its named differences or its install
        # record sentence.
        fragments = (
            "The installed SKILL.md differs from the "
            "canonical file in exactly one line",
            "read as a Claude rules file under a "
            ".qwen/rules folder",
            "the author and license fields the input "
            "manifest carried are absent from the "
            "converted file",
            "losing only its trailing newline",
            "Skill file byte fidelity does not hold for a "
            "Qoder install of the current canonical skill "
            "text",
            "an install record file that has no canonical "
            "counterpart",
        )
        for fragment in fragments:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                problems = self.break_brief(
                    root, fragment, "the record omits this"
                )
                self.assertTrue(problems, fragment)

    def test_round37_fixreview_figure_split_across_four_fails(self):
        # R37F-RT-15. The windows run to four neighbouring
        # sentences, because the fix review split the count
        # and the simultaneity word three sentences apart
        # with two fillers between them.
        problems = self.mod.negative_problems(
            "Qwen runs 16 agents for this change. The "
            "packet lists each file beside its diff. The "
            "roster records each file in the change. They "
            "work together on the review."
        )
        self.assertTrue(problems)

    def test_round37_fixreview_contrast_clause_guard_no_shelter(self):
        # R37F-RT-16. A guard phrase in a contrast clause
        # names a basis the claim separates itself from, so
        # it exempts nothing and the own voice figure
        # claim fails.
        problems = self.mod.negative_problems(
            "Qwen runs 16 agents together on this review, "
            "separate from the roster narrative table."
        )
        self.assertTrue(problems)

    def test_round37_confirm_figure_split_across_five_fails(self):
        # R37C-RT-01. The windows run to five neighbouring
        # sentences, because the confirmation review split
        # the count and the simultaneity word four
        # sentences apart with three fillers between them.
        problems = self.mod.negative_problems(
            "Qwen runs 16 agents for this change. The "
            "packet lists each file beside its diff. The "
            "roster records each file in the change. The "
            "summary notes the packet shape. They work "
            "together on the review."
        )
        self.assertTrue(problems)

    def test_round37_fixreview_window_with_own_count_passes(self):
        # R37F-RT-17. A simultaneity sentence carrying its
        # own different count heads its own claim, so the
        # window joins no figure claim and must pass.
        problems = self.mod.negative_problems(
            "The roster lists 16 agents for this change. "
            "The packet lists each file beside its diff. "
            "The two editors work together on the packet "
            "format."
        )
        self.assertEqual(problems, [])

