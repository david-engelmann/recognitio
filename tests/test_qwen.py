"""Build 15, the Qwen Code marketplace presence build.

The brief at docs/qwen-code-brief.md records the Qwen
figure basis and scope table with no single figure as
the Qwen figure, the wrapper exits 0 1 and 3 kept
separate from the internal verify exit 4, the Agent
Plugins v1 matrix in full, the Qoder and scoped npm
routes, the prefixed naming rule with its cancellation
exception, the shared skills alias with its precedence,
the conversion fidelity record with runtime invocation
verified for one scoped OpenRouter shape, the bundled
CLI version from the
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
import io
import re
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
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

    def assert_plant_kind(self, problems, kind):
        self.assertTrue(
            any(
                ("carries a %s plant in the sentence" % kind) in p
                for p in problems
            ),
            problems,
        )

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

    def run_main_on(self, root):
        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out):
            with redirect_stderr(err):
                code = self.mod.main(root)
        return code, out.getvalue(), err.getvalue()

    def test_problems_print_to_the_error_stream_naming_the_brief(self):
        # Round 4 audit Major 3. The gate once printed its
        # problems to the output stream as fragments, so a
        # failing run read as ordinary output and named no
        # surface. Problems now land on the error stream as
        # sentences naming the brief.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            (root / "docs" / "qwen-code-brief.md").unlink()
            code, out, err = self.run_main_on(root)
            self.assertEqual(code, 1)
            self.assertIn("check_qwen", err)
            self.assertIn("docs/qwen-code-brief.md", err)
            self.assertIn("is missing", err)
            self.assertNotIn("is missing", out)

    def test_the_success_line_stays_on_the_output_stream(self):
        code, out, err = self.run_main_on(ROOT)
        self.assertEqual(code, 0)
        self.assertIn(
            "check_qwen: the Build 15 Qwen Code marketplace "
            "presence contract holds", out)
        self.assertEqual(err, "")

    def test_an_undecodable_brief_is_named_not_raised(self):
        # Round 4 standards Minor 3, repaired at the fix
        # review. The brief reading once let the decode
        # error escape as a traceback. A standing file with
        # damaged bytes is not a missing file, so the
        # problem names the UTF-8 defect and never the
        # missing wording.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            (root / "docs" / "qwen-code-brief.md").write_bytes(
                b"\xff\xfe\x00bad"
            )
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "qwen-code-brief.md" in p
                    and "cannot be read as UTF-8 text" in p
                    for p in problems
                ),
                problems,
            )
            self.assertFalse(
                any(
                    "qwen-code-brief.md is missing" in p
                    or (
                        "qwen-code-brief.md" in p
                        and "is missing" in p
                    )
                    for p in problems
                ),
                problems,
            )

    def test_a_missing_brief_keeps_the_missing_wording(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            (root / "docs" / "qwen-code-brief.md").unlink()
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "qwen-code-brief.md" in p
                    and "is missing" in p
                    for p in problems
                ),
                problems,
            )
            self.assertFalse(
                any(
                    "cannot be read as UTF-8 text" in p
                    for p in problems
                ),
                problems,
            )

    def test_the_readme_scoped_npm_form_fails(self):
        # Visual round 1. The copyable scoped npm test
        # form belongs in this brief only, so restoring
        # it in the README Qwen section fails the gate.
        # The README rebuild after the visual program
        # gave the pin block its own heading, which now
        # bounds the Qwen section the gate reads, so the
        # plant lands inside the section in front of its
        # closing placeholder sentence instead of in
        # front of the pin block.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / "README.md"
            text = path.read_text(encoding="utf-8")
            plant = (
                "The scoped npm form below is an unpinned "
                "test form in shape only.\n\n"
                "```bash\n"
                "qwen extensions install "
                "@scope/my-extension@1.2.0\n"
                "```\n\n"
            )
            anchor = (
                "Replace COMMIT_SHA with the commit SHA "
                "you reviewed."
            )
            broken = text.replace(
                anchor,
                plant + anchor,
                1,
            )
            self.assertNotEqual(broken, text)
            path.write_text(broken, encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("scoped npm test form" in p for p in problems),
                problems,
            )

    def test_every_plant_fails(self):
        for plant in PLANTS:
            problems = self.mod.negative_problems(plant)
            norm = re.sub(r"\s+", " ", self.mod.normalise(plant))
            self.assertTrue(
                any(
                    " plant in the sentence " in p
                    and norm[:60] in p
                    for p in problems
                ),
                (plant, problems),
            )

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
            self.assert_plant_kind(
                self.mod.negative_problems(plant),
                "alias precedence")

    def test_negated_bring_online_passes(self):
        # S3. The negation guard must cover bring just as it
        # covers turn, while the positive bring form still fails.
        self.assertEqual(self.mod.negative_problems(
            "Qwen does not bring hooks online for the "
            "recognitio plugin."), [])
        self.assertEqual(self.mod.negative_problems(
            "Qwen does not turn hooks on for the "
            "recognitio plugin."), [])
        self.assert_plant_kind(
            self.mod.negative_problems(
                "Qwen brings hooks online for the "
                "recognitio plugin."),
            "activation")

    def test_the_number_normalisation_fires(self):
        problems = self.mod.negative_problems(
            "twelve parallel agents at high effort"
        )
        self.assert_plant_kind(problems, "figure")

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

    def test_a_dropped_runtime_proof_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "Runtime invocation stands verified for one "
                "scoped shape",
                "Runtime invocation is fully verified",
            )
            self.assertTrue(
                any("runtime scoped proof" in p for p in problems),
                problems,
            )

    def test_the_stale_runtime_unverified_wording_fails(self):
        # The live run of 2026-10-29 falsified the blanket
        # UNVERIFIED wording for the one scoped shape it ran.
        # Restoring that wording must fail by name even where
        # the scoped proof sentences stand beside it.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "No wider claim is made.",
                "Runtime invocation stays UNVERIFIED.",
            )
            self.assertTrue(
                any("stale runtime UNVERIFIED" in p
                    for p in problems),
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

    def test_a_negative_family_plant_speaks_in_the_sentence_form(self):
        # Round 4 fix review, standards Minor 5. The
        # negative family problems are rewritten into full
        # sentences naming the brief, and this pin holds
        # that form, so reverting the rewriting to a pass
        # through that returns the old labels fails here.
        problems = self.mod.negative_problems(
            "Qwen runs 16 agents working side by side on a "
            "large review"
        )
        self.assert_plant_kind(problems, "figure")
        self.assertTrue(
            any(
                p.startswith(
                    "the Qwen brief at "
                    "docs/qwen-code-brief.md carries a "
                    "figure plant in the sentence "
                )
                and "16 agents" in p
                for p in problems
            ),
            problems,
        )
        self.assertFalse(
            any(p.startswith("figure plant:") for p in problems),
            problems,
        )

    def test_a_derivation_plant_speaks_in_the_sentence_form(self):
        # The derivation reading was rewritten the same
        # way, and its sentence form is pinned the same
        # way, naming the brief and the rule head and the
        # defect in one sentence.
        raw = (
            "## The Qwen rules\n"
            "\n"
            "### R1. A planted rule head\n"
            "\n"
            "A rule body with no derivation note at all.\n"
        )
        problems = self.mod.derivation_problems(raw)
        self.assertTrue(
            any(
                p.startswith(
                    "the Qwen brief at "
                    "docs/qwen-code-brief.md carries a rule "
                    "without derivation note, the rule "
                    "headed A planted rule head, so the "
                    "rule names no source a reader can check"
                )
                for p in problems
            ),
            problems,
        )
        self.assertFalse(
            any(
                p.startswith("rule without derivation note:")
                for p in problems
            ),
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
        self.assert_plant_kind(problems, "wrapper exit")

    def test_the_three_naming_cases(self):
        self.assert_plant_kind(
            self.mod.negative_problems(
                "skills.disabled blocks only the prefixed spelling"),
            "disabled naming")
        self.assert_plant_kind(
            self.mod.negative_problems(
                "skills.enabled turns the skill on under the bare name"),
            "enabled naming")
        self.assertEqual(self.mod.negative_problems(
            "skills.disabled blocks either spelling, "
            "skills.enabled opts in under the prefixed name only."), [])

    def test_a_publication_promise_fails(self):
        problems = self.mod.negative_problems(
            "submit the skill through the central Qwen marketplace approval queue"
        )
        self.assert_plant_kind(problems, "publication")

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
        self.assert_plant_kind(problems, "figure")

    def test_round37_guard_word_no_longer_shelters_a_figure(self):
        # R37-RT-10. A basis label on the neighbouring
        # sentence exempts only its own sentence now, so a
        # planted figure beside it still fails.
        problems = self.mod.negative_problems(
            "Qwen runs 16 agents for this change. They work "
            "together on the review, as the roster "
            "narrative records."
        )
        self.assert_plant_kind(problems, "figure")

    def test_round37_full_conversion_byte_fidelity_claim_fails(self):
        # R37-RT-01. Byte fidelity holds for the round 33
        # skill tree installs only, so a byte identical
        # claim for a full conversion must fail.
        problems = self.mod.negative_problems(
            "The full bundle conversion output is byte "
            "identical to the canonical tree."
        )
        self.assert_plant_kind(problems, "conversion fidelity")

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
                name = {
                    frag: lab for lab, frag in self.mod.PINNED
                }[fragment]
                self.assertTrue(
                    any(name in p for p in problems),
                    (fragment, problems),
                )

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
        self.assert_plant_kind(problems, "figure")

    def test_round37_fixreview_contrast_clause_guard_no_shelter(self):
        # R37F-RT-16. A guard phrase in a contrast clause
        # names a basis the claim separates itself from, so
        # it exempts nothing and the own voice figure
        # claim fails.
        problems = self.mod.negative_problems(
            "Qwen runs 16 agents together on this review, "
            "separate from the roster narrative table."
        )
        self.assert_plant_kind(problems, "figure")

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
        self.assert_plant_kind(problems, "figure")

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

    def test_round37_confirm2_figure_guard_as_clause_fails(self):
        # R37C-RT-11. A basis clause appended with as and
        # no comma stands outside the clause that holds
        # the figure, so its guard phrase does not exempt
        # the claim.
        problems = self.mod.negative_problems(
            "Qwen runs 16 agents together on this review "
            "as the roster narrative records."
        )
        self.assert_plant_kind(problems, "figure")

    def test_round38_figure_split_across_six_sentences_fails(self):
        # R38-RT-13. The count and the simultaneity word
        # stand five sentences apart with four fillers
        # between them, and the paragraph scope reading
        # must catch the figure claim.
        problems = self.mod.negative_problems(
            "Qwen runs 16 agents for this change. The "
            "packet lists each file beside its diff. The "
            "roster records each file in the change. The "
            "summary lists each file in the packet. The "
            "index names each file in the review. They "
            "work together on the review."
        )
        self.assert_plant_kind(problems, "figure")

    def test_round38_figure_guard_while_clause_fails(self):
        # R38-RT-14. A basis clause appended with while
        # and no comma stands outside the clause that
        # holds the figure, so its guard phrase does not
        # exempt the claim.
        problems = self.mod.negative_problems(
            "Qwen runs 16 agents together on this review "
            "while the roster narrative records the count."
        )
        self.assert_plant_kind(problems, "figure")

    def test_round38_window_with_unnumbered_other_subject_passes(self):
        # R38-RT-15. A simultaneity sentence whose subject
        # is an explicit noun phrase other than the
        # figure agents heads its own claim even with no
        # number of its own, so the window joins no figure
        # claim and must pass.
        problems = self.mod.negative_problems(
            "The roster lists 16 agents for this change. "
            "The packet lists each file beside its diff. "
            "The editors work together on the packet "
            "format."
        )
        self.assertEqual(problems, [])

    def test_gate_round38_figure_split_across_paragraphs_fails(self):
        # R38G-RT-03. The count and the simultaneity word
        # split across a paragraph break stand in no
        # paragraph window, and the claim scope reading
        # over consecutive prose paragraphs must catch
        # the figure claim.
        problems = self.mod.negative_problems(
            "Qwen runs 16 agents for this change. The "
            "packet lists each file beside its diff. The "
            "roster records each file in the change. The "
            "summary lists each file in the packet. The "
            "index names each file in the review.\n\n"
            "They work together on the review."
        )
        self.assert_plant_kind(problems, "figure")

    def test_gate_round38_decoy_member_does_not_shelter_window(self):
        # R38G-RT-05. A simultaneity member headed by an
        # explicit subject other than the figure agents
        # heads its own claim and does not join, and it
        # no longer exempts the whole window either, so a
        # decoy member standing between the figure and a
        # member that does join shelters nothing, in the
        # unnumbered and the numbered decoy forms alike.
        plants = (
            "Qwen runs 16 agents for this change. The "
            "editors work together on the packet format. "
            "The agents work together on the review.",
            "Qwen runs 16 agents for this change. The "
            "two editors work together on the packet "
            "format. The agents work together on the "
            "review.",
            "Qwen runs 16 agents for this change. The "
            "editors work together on the packet format. "
            "They work together on the review.",
        )
        for plant in plants:
            problems = self.mod.negative_problems(plant)
            self.assert_plant_kind(problems, "figure")

    def test_gate_round38_figure_guard_with_appendage_fails(self):
        # R38G-RT-09. A basis appendage joined by the
        # word with and no comma is a clause edge, so
        # its guard phrase stands outside the figure
        # clause and does not exempt the claim.
        problems = self.mod.negative_problems(
            "Qwen runs 16 agents together on this review "
            "with the roster narrative recording the "
            "count."
        )
        self.assert_plant_kind(problems, "figure")

    def test_gate_round38_guard_paragraph_shelters_nothing(self):
        # R38G-RT-03 control. A guard phrase standing in
        # a neighbouring paragraph before a figure claim
        # shelters nothing, because the guard stays
        # scoped to the clause of the sentence that
        # carries the figure, and the claim must fail.
        problems = self.mod.negative_problems(
            "The roster narrative records the count.\n\n"
            "Qwen runs 16 agents together on this review."
        )
        self.assert_plant_kind(problems, "figure")

    def test_round38_side_shape_record_pins_hold(self):
        # R38-EX-01 and R38-EX-02. Dropping any of the
        # rescoped side shape or mirror sentences from the
        # brief fails the gate, so the conversion account
        # cannot quietly return to its unscoped form.
        fragments = (
            "Side shape files ride in as files in the "
            "round 37",
            "The round 33 installs carried the skill tree "
            "only",
            "No activation of the preserved shapes inside "
            "a Qwen session is shown",
            "an installer mirror of the input manifest",
            "three in the round 33 input",
        )
        for fragment in fragments:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                problems = self.break_brief(
                    root, fragment, "the record omits this"
                )
                name = {
                    frag: lab for lab, frag in self.mod.PINNED
                }[fragment]
                self.assertTrue(
                    any(name in p for p in problems),
                    (fragment, problems),
                )

    def test_round38_unscoped_side_shape_denial_fails(self):
        # R38-EX-01. The old unscoped denial states the
        # opposite of the round 37 full bundle record, so
        # the negative reading rejects it on its own.
        for plant in (
            "Side shapes do not ride in.",
            "The installed bundles contain only the skill "
            "tree.",
        ):
            problems = self.mod.negative_problems(plant)
            self.assert_plant_kind(problems, "conversion")

    def test_a_listing_file_at_the_root_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            (root / "qwen-extension.json").write_text(
                "{}", encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("a Qwen listing file ships at" in p
                    for p in problems), problems)

    def test_a_listing_file_inside_a_scratch_named_folder_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            folder = root / "scratch-notes"
            folder.mkdir(parents=True)
            (folder / "qwen-extension.json").write_text(
                "{}", encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("a Qwen listing file ships at" in p
                    for p in problems), problems)

    def test_a_listing_under_a_scratch_named_ancestor_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "scratch-ancestor"
            base.mkdir(parents=True)
            root = self.make_layout(str(base))
            (root / "qwen-extension.json").write_text(
                "{}", encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("a Qwen listing file ships at" in p
                    for p in problems), problems)

    def test_a_clean_control_under_a_scratch_named_ancestor_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "scratch-ancestor"
            base.mkdir(parents=True)
            root = self.make_layout(str(base))
            self.assertEqual(self.problems(root), [])

    def test_a_publication_claim_in_three_placements_fails(self):
        plant = (
            "A listing file ships in this repo and the "
            "marketplace presence is published."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            self.assert_plant_kind(
                self.mod.negative_problems(
                    self.read_brief(root)), "publication")
            problems = self.problems(root)
            self.assertTrue(
                any("publication plant" in p for p in problems),
                problems)
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            anchor = "## Summary\n"
            self.assertIn(anchor, text)
            self.write_brief(
                root, text.replace(anchor, anchor + "\n" + plant + "\n", 1))
            problems = self.problems(root)
            self.assertTrue(
                any("publication plant" in p for p in problems),
                problems)
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            anchor = "## The Qwen rules"
            self.assertIn(anchor, text)
            self.write_brief(
                root, text.replace(
                    anchor, plant + "\n\n" + anchor, 1))
            problems = self.problems(root)
            self.assertTrue(
                any("publication plant" in p for p in problems),
                problems)

    def test_a_restated_live_session_date_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "A second live session on 2026-11-03",
                "A second live session on 2026-12-03")
            self.assertTrue(
                any("second live session date" in p
                    and "2026-12-03" in p for p in problems),
                problems)

    def test_a_derivation_marker_in_navigation_is_not_a_rule(self):
        # Standards Note 2. A derivation marker standing in
        # the navigation section must not be judged as part
        # of the last rule, so dropping the last rule note
        # fails even while the marker stands in navigation.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            anchor = "## Navigation"
            self.assertIn(anchor, text)
            nav = text.find(anchor)
            last = text.rfind("Derives from", 0, nav)
            self.assertTrue(last > 0)
            broken = text[:last] + "Source note" + text[last + len("Derives from"):]
            broken = broken.replace(
                anchor,
                anchor + "\n\nDerives from canonical skill, "
                "The tier model, standing in navigation.\n", 1)
            self.assertNotEqual(broken, text)
            self.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("without derivation note" in p
                    for p in problems), problems)

    def test_publication_past_tense_listing_form_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root, text + "\n\nA listing file has shipped "
                "in this repo.\n")
            self.assert_plant_kind(
                self.problems(root), "publication")

    def test_publication_past_tense_build_form_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root, text + "\n\nBuild 15 was published.\n")
            self.assert_plant_kind(
                self.problems(root), "publication")

    def test_publication_claim_with_guard_word_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root, text + "\n\nThe marketplace presence is "
                "listed, as the effort table records.\n")
            self.assert_plant_kind(
                self.problems(root), "publication")

    def test_publication_listing_present_form_alone_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root, text + "\n\nA listing file ships in "
                "this repo.\n")
            self.assert_plant_kind(
                self.problems(root), "publication")

    def test_publication_listing_past_form_alone_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root, text + "\n\nA listing file shipped in "
                "this repo.\n")
            self.assert_plant_kind(
                self.problems(root), "publication")

    def test_publication_guard_in_given_that_clause_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root, text + "\n\nThe brief never claims a "
                "listing given that the marketplace presence "
                "was published.\n")
            self.assert_plant_kind(
                self.problems(root), "publication")

    def test_publication_guard_covering_given_that_claim_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root, text + "\n\nThe brief states given that "
                "no claim stands and a listing file ships in "
                "this repo.\n")
            problems = self.problems(root)
            self.assertFalse(any(
                "publication plant" in p for p in problems),
                problems)

    def test_publication_guard_in_while_clause_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root, text + "\n\nThe brief never claims a "
                "listing while the marketplace presence was "
                "published.\n")
            self.assert_plant_kind(
                self.problems(root), "publication")

    def test_publication_guard_covering_while_claim_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root, text + "\n\nThe brief states while no "
                "claim stands and a listing file ships in "
                "this repo.\n")
            problems = self.problems(root)
            self.assertFalse(any(
                "publication plant" in p for p in problems),
                problems)

    def test_publication_claim_in_a_table_cell_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root, text + "\n| Qwen marketplace | "
                "Published |\n")
            self.assert_plant_kind(
                self.problems(root), "publication")

    def test_publication_claim_in_a_table_cell_emphasis_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root, text + "\n| Qwen marketplace | "
                "**Published** |\n")
            self.assert_plant_kind(
                self.problems(root), "publication")

    def test_publication_claim_split_cell_and_caption_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root, text + "\n| Qwen marketplace | See "
                "caption |\n\nTable caption. The status "
                "stands published.\n")
            self.assert_plant_kind(
                self.problems(root), "publication")

    def test_publication_caption_without_status_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root, text + "\n| Qwen marketplace | See "
                "caption |\n\nTable caption. The status "
                "stands open.\n")
            problems = self.problems(root)
            self.assertFalse(any(
                "publication plant" in p for p in problems),
                problems)

    def test_publication_honest_status_in_a_table_cell_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root, text + "\n| Qwen marketplace | Not "
                "published |\n")
            problems = self.problems(root)
            self.assertFalse(any(
                "publication plant" in p for p in problems),
                problems)

    def test_publication_claim_in_a_heading_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            anchor = "## Summary\n"
            self.assertIn(anchor, text)
            self.write_brief(
                root, text.replace(
                    anchor,
                    anchor + "\n## Published in the Qwen "
                    "marketplace\n", 1))
            self.assert_plant_kind(
                self.problems(root), "publication")

    def test_live_presence_claim_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root, text + "\n\nBuild 15 stands live in "
                "the Qwen marketplace.\n")
            self.assert_plant_kind(
                self.problems(root), "live presence")

    def test_live_presence_bounded_form_alone_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root, text + "\n\nBuild 15 is live on the "
                "Qwen marketplace.\n")
            self.assert_plant_kind(
                self.problems(root), "live presence")

    def test_publication_claim_inside_r9_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            self.break_brief(
                root,
                "### R9. The conditional publication draft",
                "### R9. The conditional publication draft\n\n"
                "Build 15 is published in the Qwen marketplace.")
            self.assert_plant_kind(
                self.problems(root), "publication")

    def test_r1_scope_table_figures_exchanged_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            self.break_brief(
                root,
                "| Code review page | Step 3A small diff roster | Up to 16 parallel agents | Effort table |",
                "| Code review page | Step 3A small diff roster | Up to 17 parallel tasks | Effort table |")
            self.break_brief(
                root,
                "| Code review page | Same repo PR reviews | Up to 17 parallel tasks | Roster narrative |",
                "| Code review page | Same repo PR reviews | Up to 16 parallel agents | Roster narrative |")
            problems = self.problems(root)
            self.assertTrue(
                any("R1 scope table does not carry the pinned "
                    "row" in p for p in problems), problems)


class TestRepairPassFourQwen(unittest.TestCase):
    def setUp(self):
        self.inner = TestCheckQwen()
        self.inner.setUp()
        self.mod = self.inner.mod

    def assert_plant_kind(self, problems, kind):
        self.assertTrue(
            any(
                ("carries a %s plant in the sentence" % kind) in p
                for p in problems
            ),
            problems,
        )

    def plant_brief(self, root, suffix):
        text = self.inner.read_brief(root)
        self.inner.write_brief(root, text + suffix)

    def test_r1_census_added_row_inside_table_fails(self):
        # Repair pass four. The R1 reading was presence
        # based, so a thirteenth row binding Step 3A to 19
        # parallel agents passed beside the pinned 16. The
        # closed census refuses a row outside the pinned
        # set standing inside the table.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.read_brief(root)
            anchor = (
                "| Code review page | Same repo PR reviews "
                "| Up to 17 parallel tasks | Roster narrative |"
            )
            self.assertIn(anchor, text)
            planted = text.replace(
                anchor,
                "| Code review page | Step 3A small diff "
                "roster | Up to 19 parallel agents | Effort "
                "table |\n" + anchor,
                1,
            )
            self.assertNotEqual(planted, text)
            self.inner.write_brief(root, planted)
            problems = self.inner.problems(root)
            self.assertTrue(
                any(
                    "R1 scope table carries a row outside "
                    "the pinned census" in p
                    and "Up to 19 parallel agents" in p
                    for p in problems
                ),
                problems,
            )

    def test_r1_census_added_row_appended_fails(self):
        # Repair pass four. The record plant appends the
        # same row at the end of the brief, outside the
        # table block, and the census reads a row in the
        # R1 form wherever it stands.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            self.plant_brief(
                root,
                "\n| Code review page | Step 3A small diff "
                "roster | Up to 19 parallel agents | Effort "
                "table |\n",
            )
            problems = self.inner.problems(root)
            self.assertTrue(
                any(
                    "R1 scope table carries a row outside "
                    "the pinned census" in p
                    and "Up to 19 parallel agents" in p
                    for p in problems
                ),
                problems,
            )

    def test_r1_census_dropped_row_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.read_brief(root)
            row = (
                "| Code review page | Local and file reviews "
                "| 15 | Token efficiency table |\n"
            )
            self.assertIn(row, text)
            self.inner.write_brief(root, text.replace(row, "", 1))
            problems = self.inner.problems(root)
            self.assertTrue(
                any(
                    "R1 scope table does not carry the "
                    "pinned row" in p
                    and "Local and file reviews" in p
                    for p in problems
                ),
                problems,
            )

    def test_r1_census_restated_figure_in_row_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.read_brief(root)
            planted = text.replace(
                "Up to 16 parallel agents",
                "Up to 19 parallel agents",
                1,
            )
            self.assertNotEqual(planted, text)
            self.inner.write_brief(root, planted)
            problems = self.inner.problems(root)
            self.assertTrue(
                any(
                    "R1 scope table carries a row outside "
                    "the pinned census" in p
                    for p in problems
                ),
                problems,
            )
            self.assertTrue(
                any(
                    "R1 scope table does not carry the "
                    "pinned row" in p
                    and "Step 3A small diff roster" in p
                    for p in problems
                ),
                problems,
            )

    def test_wrapper_census_added_row_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.read_brief(root)
            anchor = (
                "| 3 | It completed with REQUEST_CHANGES "
                "and fail-on request-changes set |"
            )
            self.assertIn(anchor, text)
            planted = text.replace(
                anchor,
                anchor + "\n| 4 | It completed with "
                "REQUEST_CHANGES and fail-on "
                "request-changes set |",
                1,
            )
            self.assertNotEqual(planted, text)
            self.inner.write_brief(root, planted)
            problems = self.inner.problems(root)
            self.assertTrue(
                any(
                    "wrapper exit table carries a row "
                    "outside the pinned census" in p
                    for p in problems
                ),
                problems,
            )

    def test_wrapper_census_dropped_row_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.read_brief(root)
            row = (
                "| 1 | It never reached a verdict because "
                "a child failed or timed out or left no "
                "composed artifact |\n"
            )
            self.assertIn(row, text)
            self.inner.write_brief(root, text.replace(row, "", 1))
            problems = self.inner.problems(root)
            self.assertTrue(
                any("wrapper exit 1" in p for p in problems),
                problems,
            )

    def test_internal_census_added_row_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.read_brief(root)
            anchor = (
                "| 4 | Internal verify refusal at the "
                "compose floor |"
            )
            self.assertIn(anchor, text)
            planted = text.replace(
                anchor,
                anchor + "\n| 5 | Internal verify refusal "
                "at the compose floor |",
                1,
            )
            self.assertNotEqual(planted, text)
            self.inner.write_brief(root, planted)
            problems = self.inner.problems(root)
            self.assertTrue(
                any(
                    "internal verify exit table carries a "
                    "row outside the pinned census" in p
                    for p in problems
                ),
                problems,
            )

    def test_internal_census_restated_row_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.read_brief(root)
            planted = text.replace(
                "| 4 | Internal verify refusal at the "
                "compose floor |",
                "| 3 | Internal verify refusal at the "
                "compose floor |",
                1,
            )
            self.assertNotEqual(planted, text)
            self.inner.write_brief(root, planted)
            problems = self.inner.problems(root)
            self.assertTrue(
                any(
                    "internal verify exit table carries a "
                    "row outside the pinned census" in p
                    for p in problems
                ),
                problems,
            )

    def test_internal_verify_exit_restated_in_prose_fails(self):
        problems = self.mod.negative_problems(
            "The internal verify exit is 5."
        )
        self.assert_plant_kind(
            problems, "internal verify exit")

    def test_wrapper_exit_outside_set_in_prose_fails(self):
        problems = self.mod.negative_problems(
            "The wrapper exit 2 covers a broken tool."
        )
        self.assert_plant_kind(problems, "wrapper exit")

    def test_wrapper_exit_list_with_outside_figure_fails(self):
        problems = self.mod.negative_problems(
            "Wrapper exits are 0, 1, 3, and 5."
        )
        self.assert_plant_kind(problems, "wrapper exit")

    def test_wrapper_exit_list_true_form_holds(self):
        self.assertEqual(
            self.mod.negative_problems(
                "Wrapper exits are 0, 1, and 3."),
            [],
        )

    def test_wrapper_meaning_swapped_in_prose_fails(self):
        problems = self.mod.negative_problems(
            "The wrapper exit 0 means it never reached "
            "a verdict."
        )
        self.assert_plant_kind(problems, "wrapper exit")

    def test_internal_meaning_swapped_in_prose_fails(self):
        problems = self.mod.negative_problems(
            "The internal verify exit means the review "
            "completed whatever it decided."
        )
        self.assert_plant_kind(
            problems, "internal verify exit")

    def test_exit_pairings_own_meanings_hold(self):
        for sentence in (
            "The wrapper exit 0 means the review completed "
            "whatever it decided.",
            "The wrapper exit 3 means it completed with "
            "REQUEST_CHANGES and fail-on request-changes set.",
            "The internal verify exit is 4, an internal "
            "verify refusal at the compose floor.",
            "The internal verify exit is not 5.",
        ):
            self.assertEqual(
                self.mod.negative_problems(sentence),
                [],
                sentence,
            )

    def test_publication_caption_with_caption_lead_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            self.plant_brief(
                root,
                "\n| Qwen marketplace | See caption |\n\n"
                "Caption. The status stands published.\n",
            )
            self.assert_plant_kind(
                self.inner.problems(root), "publication")

    def test_publication_caption_with_bare_status_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            self.plant_brief(
                root,
                "\n| Qwen marketplace | See caption |\n\n"
                "Table caption. Published.\n",
            )
            self.assert_plant_kind(
                self.inner.problems(root), "publication")

    def test_publication_standalone_status_line_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            self.plant_brief(
                root,
                "\n| Qwen marketplace | Open |\n\n"
                "Published.\n",
            )
            self.assert_plant_kind(
                self.inner.problems(root), "publication")

    def test_publication_standalone_stands_line_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            self.plant_brief(
                root,
                "\n| Qwen marketplace | Open |\n\n"
                "The status stands published.\n",
            )
            self.assert_plant_kind(
                self.inner.problems(root), "publication")

    def test_publication_caption_after_prose_paragraph_holds(self):
        # Repair pass four. A caption standing after an
        # intervening prose paragraph stands outside the
        # reading, and the scoping texts name it outside,
        # so this form passes on purpose.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            self.plant_brief(
                root,
                "\n| Qwen marketplace | See caption |\n\n"
                "Some prose paragraph.\n\n"
                "Table caption. The status stands "
                "published.\n",
            )
            problems = self.inner.problems(root)
            self.assertFalse(
                any(
                    "publication plant" in p for p in problems
                ),
                problems,
            )

    def test_publication_caption_honest_controls_hold(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            self.plant_brief(
                root,
                "\n| Qwen marketplace | See caption |\n\n"
                "Caption. The status stands open.\n",
            )
            problems = self.inner.problems(root)
            self.assertFalse(
                any(
                    "publication plant" in p for p in problems
                ),
                problems,
            )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            self.plant_brief(
                root,
                "\n| Qwen marketplace | Open |\n\n"
                "Not published.\n",
            )
            problems = self.inner.problems(root)
            self.assertFalse(
                any(
                    "publication plant" in p for p in problems
                ),
                problems,
            )


class TestRepairPassFiveQwen(unittest.TestCase):
    def setUp(self):
        self.inner = TestCheckQwen()
        self.inner.setUp()
        self.mod = self.inner.mod

    def assert_plant_kind(self, problems, kind):
        self.assertTrue(
            any(
                ("carries a %s plant in the sentence" % kind) in p
                for p in problems
            ),
            problems,
        )

    def test_wrapper_exit_of_form_in_prose_fails(self):
        # Repair pass five. The wrapper exit figure
        # readings admitted the plain form only, so a
        # figure standing after the word of in the exit
        # of form stated a false membership no reading
        # refused. The of form is an exit figure position
        # in the wrapper reading now.
        problems = self.mod.negative_problems(
            "The wrapper exit of 2 covers a broken tool."
        )
        self.assert_plant_kind(problems, "wrapper exit")

    def test_internal_verify_exit_of_form_in_prose_fails(self):
        # Repair pass five. The internal verify reading
        # admitted the plain form only, so its exit of
        # form passed the same way. The of form is an
        # exit figure position in that reading now.
        problems = self.mod.negative_problems(
            "The internal verify exit of 5 stands in "
            "the record."
        )
        self.assert_plant_kind(
            problems, "internal verify exit")
