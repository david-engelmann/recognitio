"""Build 11, the CodeRabbit guidelines build.

The brief at docs/coderabbit-review-brief.md records the rename
direction, the focus toggle table as a constraint, the Quiet
Chill and Assertive profiles, the pre merge checks with Error
mode merge blocking, the October 2026 entries, and the guideline
file provenance now shown in review summaries, all from the
primary CodeRabbit docs. These tests prove the pin fires for a
real reason on every load bearing claim the round 23 lanes
named. A deeper reading of high, a dropped rename direction, a
softened focus constraint, a dropped summary fold, a dropped
axis naming, a dropped Quiet launch, a dropped Error mode pin,
a dropped Automatic Approvals pin, a dropped Deep Scan pin, a
dropped provenance pin, a dropped .claude/rules/ pin, a dropped
pairing guard, a claimed calendar, a guideline without a
derivation note, a passing prose title mention, and a decision
record without a decision 4 statement each fail the CodeRabbit
gate. The shipped config at the repo root stands under the
same gate, and a planted change to a setting the brief states
for that file, a deleted config, and a FIFO at the config
path each fail it as well. A planted change to the config
path filters, to the path instruction paths, or to the
Markdown path instruction wording, and the deletion of
either path block whole, each fail it as well.
"""

import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CONFIG_DRIVER = r"""
import importlib.util
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "config_door", Path(sys.argv[1])
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
for problem in mod.coderabbit_problems(Path(sys.argv[2])):
    print(problem)
"""


def load_script(name):
    path = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(
        "coderabbit_" + name, path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestCheckCoderabbit(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_coderabbit")

    def make_layout(self, tmp):
        """A scratch tree with the brief and the record."""
        root = Path(tmp) / "root"
        for rel in (
            "docs/coderabbit-review-brief.md",
            "docs/decisions.md",
            ".coderabbit.yaml",
        ):
            source = ROOT / rel
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        return root

    def problems(self, root):
        return self.mod.coderabbit_problems(root)

    def read_brief(self, root):
        return (root / "docs" / "coderabbit-review-brief.md").read_text(
            encoding="utf-8"
        )

    def write_brief(self, root, text):
        (root / "docs" / "coderabbit-review-brief.md").write_text(
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

    def read_config(self, root):
        return (root / ".coderabbit.yaml").read_text(
            encoding="utf-8"
        )

    def write_config(self, root, text):
        (root / ".coderabbit.yaml").write_text(
            text, encoding="utf-8"
        )

    def break_config(self, root, old, new):
        # The config is read as shipped text, so the old
        # string names the exact lines the plant moves and
        # the rest of the file stands untouched. A plant
        # that names a string the file does not carry is
        # not a test.
        text = self.read_config(root)
        broken = text.replace(old, new, 1)
        self.assertNotEqual(broken, text)
        self.write_config(root, broken)
        return self.problems(root)

    def run_config_door(self, root):
        # The FIFO doors run in a subprocess bounded at ten
        # seconds, so a door that reads its FIFO fails this
        # test at the bound instead of hanging the suite.
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    CONFIG_DRIVER,
                    str(ROOT / "scripts" / "check_coderabbit.py"),
                    str(root),
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except subprocess.TimeoutExpired:
            self.fail(
                "the config door did not finish within ten "
                "seconds"
            )
        return result.stdout + result.stderr

    def test_the_shipped_tree_holds(self):
        self.assertEqual(self.mod.coderabbit_problems(ROOT), [])

    def test_the_scratch_layout_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            self.assertEqual(self.problems(root), [])

    def test_a_deeper_reading_of_high_fails(self):
        # R23-RT-03. High trims verbosity and never reads as deeper
        # review. A later edit that treats high as deeper analysis
        # must fail the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "It does not deepen analysis, and the brief must "
                "never treat it as deeper review.",
                "It deepens analysis for reviewers who want more "
                "depth.",
            )
            self.assertTrue(
                any("never deeper reading" in p for p in problems),
                problems,
            )

    def test_a_softened_focus_constraint_fails(self):
        # R23-RT-03. The focus table constrains the brief. Softening
        # the trims claim lets the deeper reading drift back in.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "High trims verbosity.",
                "High adjusts verbosity.",
            )
            self.assertTrue(
                any("high trims" in p for p in problems), problems
            )

    def test_a_dropped_rename_direction_fails(self):
        # R23-RT-03. The primary direction is Fix comments was
        # Autofix and Autofix was Autopilot. Reversing either half
        # must fail the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "Fix comments (formerly Autofix) fixes the review comments you select",
                "Autofix (formerly Fix comments) fixes the review "
                "comments you select",
            )
            self.assertTrue(
                any("Fix comments was Autofix" in p for p in problems),
                problems,
            )

    def test_a_dropped_alias_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "keep working as aliases for a limited time for "
                "backward compatibility.",
                "keep working forever with no sunset.",
            )
            self.assertTrue(
                any("compat aliases" in p for p in problems), problems
            )

    def test_a_dropped_high_row_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "reviews down to essential content only",
                "reviews down to whatever feels right",
            )
            self.assertTrue(
                any("high table row" in p for p in problems), problems
            )

    def test_a_dropped_summary_fold_pin_fails(self):
        # R23-SP-A2. The fold of the summary into the walkthrough
        # at high is pinned explicitly, so no reader counts it as
        # added analysis.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "moves from off to on at high and folds the summary into the walkthrough.",
                "stays off at high like every other setting.",
            )
            self.assertTrue(
                any("summary fold" in p for p in problems), problems
            )

    def test_a_dropped_axis_naming_fails(self):
        # R23-SP-A1. Every focus and profile sentence names its
        # axis, so a reader cannot mix high with assertive.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "On the focus axis, `reviews.focus` takes casual, "
                "balanced, or high",
                "`reviews.focus` takes casual, balanced, or high",
            )
            self.assertTrue(
                any("focus axis named" in p for p in problems),
                problems,
            )

    def test_a_dropped_quiet_launch_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "July 2 2026",
                "a recent date",
                count=0,
            )
            self.assertTrue(
                any("Quiet launch" in p for p in problems), problems
            )

    def test_a_dropped_error_blocking_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "requires resolution before merging.",
                "asks nicely for resolution before merging.",
            )
            self.assertTrue(
                any("Error mode merge blocking" in p for p in problems),
                problems,
            )

    def test_a_dropped_security_merge_blocking_pin_fails(self):
        # R27-SP-02. The October 5 2026 changelog entry says
        # publishing the CodeRabbit Security check alone does
        # not block. A later edit that drops the entry must fail
        # the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "publishing alone does not block.",
                "publishing alone blocks every merge.",
            )
            self.assertTrue(
                any("security merge blocking entry" in p
                    for p in problems),
                problems,
            )

    def test_a_dropped_auto_approvals_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "Optional risk limits keep pull requests above a "
                "chosen Merge Risk for human approval.",
                "Optional risk limits exist somewhere in the "
                "settings.",
            )
            self.assertTrue(
                any("approval risk limits" in p for p in problems),
                problems,
            )

    def test_a_dropped_deep_scan_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "prevent pull request authors from using "
                "`@coderabbitai approve` and `@coderabbitai resolve` "
                "on their own pull requests.",
                "lets pull request authors approve their own pull "
                "requests.",
            )
            self.assertTrue(
                any("author approval key" in p for p in problems),
                problems,
            )

    def test_a_dropped_deep_scan_limit_pin_fails(self):
        # R31-EX-04. The Build 11 brief pins the Deep Scan
        # linked repository limits, the manual versus
        # automatic linking distinction, the findings
        # attachment rule, and the CLI v0.9.0 cloud task
        # surface with its signed Linux release
        # verification.
        cases = (
            ("up to 20 linked repositories",
             "20 linked repositories limit"),
            ("subject to the plan linked repository limit",
             "plan linked repository limit"),
            ("Essentials supports manual links",
             "manual versus automatic linking"),
            ("remain attached to the primary repository",
             "findings attached to primary"),
            ("CLI v0.9.0 for cloud task work",
             "CLI v0.9.0 cloud tasks"),
            ("verifies signed Linux releases",
             "signed Linux release verification"),
        )
        for old, needle in cases:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                problems = self.break_brief(
                    root, old, "Some other sentence stands here."
                )
                self.assertTrue(
                    any(needle in p for p in problems),
                    (old, problems),
                )

    def test_a_dropped_provenance_pin_fails(self):
        # R23-RT-03. The guideline file provenance now shown in
        # review summaries is a pinned sentence.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "configured, auto-discovered, or an Agent Skill.",
                "configured or discovered somehow.",
                count=0,
            )
            self.assertTrue(
                any("guideline provenance" in p for p in problems),
                problems,
            )

    def test_a_dropped_claude_rules_pin_fails(self):
        # R23-EX-01. `.claude/rules/` is the fourth guideline
        # source, with `paths` frontmatter scoping.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "adds `.claude/rules/` as a fourth guideline source",
                "adds another guideline source",
            )
            self.assertTrue(
                any("fourth guideline source" in p for p in problems),
                problems,
            )

    def test_a_dropped_pairing_guard_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "Guideline files are a review pairing source, never "
                "a second packet.",
                "Guideline files are a handy second packet.",
            )
            self.assertTrue(
                any("pairing not a packet" in p for p in problems),
                problems,
            )

    def test_a_claimed_calendar_fails(self):
        # The brief states the no calendar negative plainly.
        # Dropping it lets a schedule claim drift in unpinned.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "There is no product native calendar schedule on any "
                "primary CodeRabbit surface, and the brief claims "
                "none.",
                "CodeRabbit runs reviews on a nightly calendar "
                "schedule.",
            )
            self.assertTrue(
                any("no calendar negative" in p for p in problems),
                problems,
            )

    def test_a_guideline_without_a_derivation_note_fails(self):
        # The second packet guard, carried over from Builds 9 and
        # 10. A guideline with no derivation note is a rival
        # instruction source.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "Derives from canonical skill, The tier model, the T0 instruction file flag.",
                "No derivation is offered for this guideline.",
            )
            self.assertTrue(
                any("no derivation note" in p for p in problems),
                problems,
            )

    def test_a_passing_prose_guideline_note_fails(self):
        # R21-ST-01, applied to the CodeRabbit guidelines. A note
        # that names a canonical section title in passing prose
        # without deriving from it must fail.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "Derives from canonical skill, The tier model, the T0 instruction file flag.",
                "Derives from the primary blog post. It shapes the\n"
                "Workflow of the review and nothing else.",
            )
            self.assertTrue(
                any(
                    "no canonical skill section" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_decision_record_without_decision_4_fails(self):
        # Every landed build records a decision 4 statement. A
        # Build 11 record without one fails the pin.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / "docs" / "decisions.md"
            text = path.read_text(encoding="utf-8")
            start = text.find("## 20. Build 11")
            self.assertNotEqual(start, -1)
            record = text[start:]
            broken = record.replace(
                "Decision 4 binds the build.",
                "Decision 4 is noted elsewhere.",
                1,
            )
            self.assertNotEqual(broken, record)
            path.write_text(text[:start] + broken, encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("decision 4" in p for p in problems), problems
            )


    def test_the_unmutated_config_holds(self):
        # Round 230 control. The shipped config in a scratch
        # layout passes the config reading whole.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            self.assertEqual(self.problems(root), [])

    def test_a_config_profile_plant_fails(self):
        # Round 230. The profile moved from chill to
        # assertive returned zero problems at the base.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_config(
                root,
                'profile: "chill"',
                'profile: "assertive"',
            )
            self.assertTrue(
                any(
                    "reviews profile to chill" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_config_title_check_plant_fails(self):
        # Round 230. The pre merge title check moved from
        # warning to error returned zero problems.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_config(
                root,
                'title:\n      mode: "warning"',
                'title:\n      mode: "error"',
            )
            self.assertTrue(
                any(
                    "pre merge title check to warning" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_config_description_check_plant_fails(self):
        # Round 230. The pre merge description check moved
        # from warning to error returned zero problems.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_config(
                root,
                'description:\n      mode: "warning"',
                'description:\n      mode: "error"',
            )
            self.assertTrue(
                any(
                    "pre merge description check to warning"
                    in p
                    for p in problems
                ),
                problems,
            )

    def test_a_config_guideline_patterns_plant_fails(self):
        # Round 230. The guideline file patterns replaced
        # whole returned zero problems.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_config(
                root,
                '      - "**/AGENTS.md"\n'
                '      - "README.md"',
                '      - "**/CHANGELOG.md"',
            )
            self.assertTrue(
                any("file patterns on" in p for p in problems),
                problems,
            )

    def test_a_config_request_changes_plant_fails(self):
        # Round 230. The request changes workflow switched
        # on returned zero problems.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_config(
                root,
                "request_changes_workflow: false",
                "request_changes_workflow: true",
            )
            self.assertTrue(
                any(
                    "request changes workflow to false" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_config_auto_review_plant_fails(self):
        # Round 230. Automatic review switched off returned
        # zero problems.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_config(
                root,
                "  auto_review:\n    enabled: true",
                "  auto_review:\n    enabled: false",
            )
            self.assertTrue(
                any(
                    "automatic review to enabled" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_config_issue_assessment_plant_fails(self):
        # The brief sets the pre merge checks to warning
        # mode, and the issue assessment check is one of
        # them beside the title and description checks.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_config(
                root,
                'issue_assessment:\n      mode: "warning"',
                'issue_assessment:\n      mode: "error"',
            )
            self.assertTrue(
                any(
                    "pre merge issue assessment check to "
                    "warning" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_config_docstrings_plant_fails(self):
        # The shipped shape the round 230 reading recorded
        # holds docstrings off beside the warning checks.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_config(
                root,
                'docstrings:\n      mode: "off"',
                'docstrings:\n      mode: "warning"',
            )
            self.assertTrue(
                any(
                    "pre merge docstrings check to off" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_config_guidelines_disabled_plant_fails(self):
        # The brief pairs the config through the knowledge
        # base code guidelines, so the enabled flag is part
        # of the pairing claim and not only its patterns.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_config(
                root,
                "code_guidelines:\n    enabled: true",
                "code_guidelines:\n    enabled: false",
            )
            self.assertTrue(
                any(
                    "does not enable the knowledge base "
                    "code guidelines" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_config_advisory_comment_plant_fails(self):
        # The brief states the file own comment records
        # CodeRabbit as advisory step 0 in this repo.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_config(
                root,
                "CodeRabbit is advisory step 0 in this repo.",
                "CodeRabbit is a review tool in this repo.",
            )
            self.assertTrue(
                any("advisory step 0" in p for p in problems),
                problems,
            )

    def test_a_config_markdown_path_wording_plant_fails(self):
        # Round 236. The wording flipped in the Markdown
        # path passage returned zero problems at the base.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_config(
                root,
                "No em dashes in prose",
                "Em dashes are welcome in prose",
            )
            self.assertTrue(
                any(
                    "copy bar path instructions for **/*.md"
                    in p
                    for p in problems
                ),
                problems,
            )

    def test_a_config_path_instructions_block_deleted_fails(
        self,
    ):
        # Round 236. The path instructions block deleted
        # whole returned zero problems at the base.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_config(root)
            start = text.index("  path_instructions:")
            end = text.index("  pre_merge_checks:")
            self.write_config(root, text[:start] + text[end:])
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "does not carry path instructions for"
                    in p
                    for p in problems
                ),
                problems,
            )

    def test_a_config_path_filters_block_deleted_fails(self):
        # Round 236. The path filters block deleted whole
        # returned zero problems at the base.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_config(root)
            start = text.index("  path_filters:")
            end = text.index("  path_instructions:")
            self.write_config(root, text[:start] + text[end:])
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "does not carry the reviews path filters"
                    in p
                    for p in problems
                ),
                problems,
            )

    def test_a_config_path_instruction_path_plant_fails(self):
        # Round 236 scope. The path instruction paths are
        # pinned as a set, so a moved path fails by name.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_config(
                root,
                '- path: "tests/**"',
                '- path: "test/**"',
            )
            self.assertTrue(
                any(
                    "does not carry path instructions for"
                    in p
                    for p in problems
                ),
                problems,
            )

    def test_a_config_path_filter_entry_plant_fails(self):
        # Round 236 scope. The path filter entries are
        # pinned as a set, so a weakened entry fails by
        # name.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_config(
                root,
                '- "!packet/**"',
                '- "!packet/"',
            )
            self.assertTrue(
                any(
                    "does not carry the reviews path filters"
                    in p
                    for p in problems
                ),
                problems,
            )

    def test_a_config_extra_path_instruction_entry_fails(
        self,
    ):
        # Round 236 scope. An added path instruction entry
        # moves the pinned path set and fails by name.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_config(
                root,
                "\n  pre_merge_checks:",
                '\n    - path: "docs/**"\n'
                "      instructions: |\n"
                "        Extra guidance.\n"
                "\n  pre_merge_checks:",
            )
            self.assertTrue(
                any(
                    "does not carry path instructions for"
                    in p
                    for p in problems
                ),
                problems,
            )

    def test_a_config_extra_path_filter_entry_fails(self):
        # Round 236 scope. An added path filter entry
        # moves the pinned filter set and fails by name.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_config(
                root,
                '- "!packets/**"',
                '- "!packets/**"\n    - "!docs/**"',
            )
            self.assertTrue(
                any(
                    "does not carry the reviews path filters"
                    in p
                    for p in problems
                ),
                problems,
            )

    def test_a_config_other_path_wording_change_holds(self):
        # Control. The instruction wording of the non
        # Markdown path entries is not pinned under the
        # round 236 scope, so a wording change there passes
        # in both states while its path stays pinned.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_config(
                root,
                "The extractor reads local git only",
                "The extractor reads hosted diffs only",
            )
            self.assertEqual(problems, [])

    def test_a_config_markdown_block_deeper_indent_holds(
        self,
    ):
        # Control. The Markdown block scalar carried at a
        # deeper indentation holds the same words, and the
        # pin reads wording rather than indentation.
        old = (
            "      instructions: |\n"
            "        Public prose here follows a copy bar. "
            "No em dashes in prose,\n"
            "        and no colons or semicolons in prose "
            "sentences either. When\n"
            "        flagging one of these marks, never "
            "suggest another banned\n"
            "        mark as the replacement. Suggest short "
            "plain sentences\n"
            "        instead. Flag claims about what the "
            "skill does that the\n"
            "        README and SKILL files do not back.\n"
        )
        new = (
            "      instructions: |\n"
            "          Public prose here follows a copy "
            "bar. No em dashes in prose,\n"
            "          and no colons or semicolons in prose "
            "sentences either. When\n"
            "          flagging one of these marks, never "
            "suggest another banned\n"
            "          mark as the replacement. Suggest "
            "short plain sentences\n"
            "          instead. Flag claims about what the "
            "skill does that the\n"
            "          README and SKILL files do not back.\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_config(root, old, new)
            self.assertEqual(problems, [])

    def test_a_config_markdown_wording_rewrapped_holds(self):
        # Control. The Markdown passage rewrapped onto
        # different lines holds the same words in order,
        # and the pin reads wording rather than wrapping.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_config(
                root,
                "No em dashes in prose,\n"
                "        and no colons",
                "No em dashes\n"
                "        in prose, and no colons",
            )
            self.assertEqual(problems, [])

    def test_a_deleted_config_fails(self):
        # Round 230. Deleting the config whole returned
        # zero problems at the base.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            (root / ".coderabbit.yaml").unlink()
            problems = self.problems(root)
            self.assertTrue(
                any(
                    ".coderabbit.yaml is missing" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_directory_at_the_config_path_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            (root / ".coderabbit.yaml").unlink()
            (root / ".coderabbit.yaml").mkdir()
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "is not a regular file" in p
                    for p in problems
                ),
                problems,
            )

    @unittest.skipUnless(
        hasattr(os, "mkfifo"), "no mkfifo on this host"
    )
    def test_a_fifo_at_the_config_path_refuses_promptly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            (root / ".coderabbit.yaml").unlink()
            os.mkfifo(root / ".coderabbit.yaml")
            output = self.run_config_door(root)
            self.assertIn("not a regular file", output, output)

    @unittest.skipUnless(
        hasattr(os, "mkfifo"), "no mkfifo on this host"
    )
    def test_a_link_to_a_fifo_at_the_config_path_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            (root / ".coderabbit.yaml").unlink()
            os.mkfifo(root / "config-target")
            (root / ".coderabbit.yaml").symlink_to(
                root / "config-target"
            )
            output = self.run_config_door(root)
            self.assertIn("not a regular file", output, output)

    def test_a_planted_claude_rules_directory_fails(self):
        # The brief states the repo ships no .claude/rules
        # directory today, in the same passage that states
        # the guideline file patterns.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            (root / ".claude" / "rules").mkdir(parents=True)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    ".claude/rules stands in the tree" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_reordered_config_holds(self):
        # Control. The pinned settings in a different key
        # order, with the file patterns in the other order,
        # hold in substance and must pass.
        text = (
            "# CodeRabbit is advisory step 0 in this repo.\n"
            "knowledge_base:\n"
            "  code_guidelines:\n"
            "    filePatterns:\n"
            '      - "README.md"\n'
            '      - "**/AGENTS.md"\n'
            "    enabled: true\n"
            "reviews:\n"
            "  pre_merge_checks:\n"
            "    issue_assessment:\n"
            '      mode: "warning"\n'
            "    description:\n"
            '      mode: "warning"\n'
            "    title:\n"
            '      mode: "warning"\n'
            "    docstrings:\n"
            '      mode: "off"\n'
            "  auto_review:\n"
            "    enabled: true\n"
            "  request_changes_workflow: false\n"
            '  profile: "chill"\n'
            "  path_filters:\n"
            '    - "!packets/**"\n'
            '    - "!packet/**"\n'
            '    - "!**/*.pyc"\n'
            '    - "!**/__pycache__/**"\n'
            "  path_instructions:\n"
            '    - path: "scripts/**"\n'
            "      instructions: |\n"
            "        Gate scripts are stdlib only.\n"
            '    - path: "**/*.md"\n'
            "      instructions: |\n"
            "        Public prose here follows a copy bar. "
            "No em dashes in prose, and\n"
            "        no colons or semicolons in prose "
            "sentences either. When flagging\n"
            "        one of these marks, never suggest "
            "another banned mark as the\n"
            "        replacement. Suggest short plain "
            "sentences instead. Flag claims\n"
            "        about what the skill does that the "
            "README and SKILL files do\n"
            "        not back.\n"
            '    - path: "tests/**"\n'
            "      instructions: |\n"
            "        Every test must be able to fail.\n"
            '    - path: ".agents/skills/recognitio/**"\n'
            "      instructions: |\n"
            "        The extractor reads local git only.\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            self.write_config(root, text)
            self.assertEqual(self.problems(root), [])

    def test_a_config_with_unknown_keys_holds(self):
        # Control. Keys the brief makes no claim about are
        # not policed, at the top level or inside a section.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_config(root)
            text = text.replace(
                '  profile: "chill"',
                '  profile: "chill"\n'
                "  extra_review_key: true",
                1,
            )
            text += "\nextra_top_level:\n  extra_key: true\n"
            self.write_config(root, text)
            self.assertEqual(self.problems(root), [])

    def test_a_config_with_crlf_endings_holds(self):
        # Control. The shipped settings with CRLF line
        # endings hold in substance and must pass.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_config(root).replace(
                "\n", "\r\n"
            )
            (root / ".coderabbit.yaml").write_bytes(
                data.encode("utf-8")
            )
            self.assertEqual(self.problems(root), [])

    def test_linked_source_plants_fail(self):
        # R36-RT-04. Linked source promised on an excluded
        # platform, and a linked repository limit above 20,
        # each passed while the pins stayed in place.
        cases = (
            ("Deep Scan linked source is available in the "
             "scan trigger flow for self hosted GitLab and "
             "Azure DevOps and Bitbucket.",
             "promises Deep Scan linked source"),
            ("A Deep Scan can read up to 50 linked "
             "repositories on any plan.",
             "other than the pinned limit of 20"),
        )
        for plant, needle in cases:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                text = self.read_brief(root)
                self.write_brief(root, text + "\n\n" + plant + "\n")
                problems = self.problems(root)
                self.assertTrue(
                    any(needle in p for p in problems),
                    (plant, problems),
                )

    def test_a_dropped_platform_limit_pin_fails(self):
        # R36-RT-04. The platform limit sentence folded
        # beside the linked context sentence is pinned, so
        # dropping it fails.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            problems = self.break_brief(
                root,
                "not available in that flow for self hosted "
                "GitLab or Azure DevOps or Bitbucket",
                "available on every platform",
            )
            self.assertTrue(
                any("platform limit" in p for p in problems),
                problems,
            )

    def test_gate_review_linked_source_restated_plants_fail(self):
        # Gate review repair. The first platform branch
        # required the word available as a substring and
        # the figure branch read digits only, so the
        # review restated the promise with works and
        # offered and supported, raised the limit in
        # words, and hid the figure behind the verb link,
        # and each passed.
        cases = (
            ("Deep Scan linked source works in the scan "
             "trigger flow for self hosted GitLab.",
             "promises Deep Scan linked source"),
            ("Deep Scan linked source is offered in the "
             "scan trigger flow on Bitbucket.",
             "promises Deep Scan linked source"),
            ("Linked repositories are supported in the "
             "scan trigger flow on Azure DevOps.",
             "promises Deep Scan linked source"),
            ("A Deep Scan can read up to fifty linked "
             "repositories on any plan.",
             "linked repositories, other than the pinned limit"),
            ("A Deep Scan can read up to twenty one linked "
             "repositories on any plan.",
             "linked repositories, other than the pinned limit"),
            ("A Deep Scan can link 50 repositories to a "
             "primary repository on any plan.",
             "linked repositories, other than the pinned limit"),
        )
        for plant, needle in cases:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                text = self.read_brief(root)
                self.write_brief(root, text + "\n\n" + plant + "\n")
                problems = self.problems(root)
                self.assertTrue(
                    any(needle in p for p in problems),
                    (plant, problems),
                )

    def test_gate_review_linked_source_true_sentences_pass(self):
        # Gate review repair. The substring read of the
        # word available fired on unavailable, and the
        # sentence level read fired where an included
        # platform carried the offer and an excluded
        # platform stood under its own negation.
        cases = (
            "Linked source is unavailable in the scan "
            "trigger flow for self hosted GitLab.",
            "Linked source is available on GitHub Cloud, "
            "and self hosted GitLab is not among the "
            "supported platforms.",
        )
        for plant in cases:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                text = self.read_brief(root)
                self.write_brief(root, text + "\n\n" + plant + "\n")
                self.assertEqual(self.problems(root), [])

    def test_round37_platform_split_across_sentences_fails(self):
        # R37-RT-07. The offer and the excluded platform
        # split across two sentences, and the pair reading
        # must catch the promise.
        plant = (
            "Deep Scan linked source runs in the scan "
            "trigger flow. It also runs on self hosted "
            "GitLab."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "promises Deep Scan linked source" in p
                    for p in problems
                ),
                problems,
            )

    def test_round37_figure_in_partner_sentence_fails(self):
        # R37-RT-07. The raised figure stands in a partner
        # sentence holding no repository word, bound to
        # the linked repositories through its cap frame.
        plant = (
            "A Deep Scan can read linked repositories "
            "across a workspace. The cap for that reading "
            "is 50 on any plan."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "linked repository cap of 50" in p
                    for p in problems
                ),
                problems,
            )

    def test_round37_platform_past_the_span_fails(self):
        # R37-RT-07. The offer and the platform stand past
        # the old span inside one long sentence, and the
        # unit scope binding must catch the promise.
        plant = (
            "Linked source is available in the scan trigger "
            "flow, after the scan reads the primary "
            "repository and every linked repository in the "
            "workspace in full, on self hosted GitLab."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "promises Deep Scan linked source" in p
                    for p in problems
                ),
                problems,
            )

    def test_round37_negation_before_the_offer_passes(self):
        # R37-RT-08. The negation stands ahead of a
        # subordinate clause, far before the offer word,
        # and the true platform limit sentence must pass.
        sentence = (
            "Linked source is not, in the scan trigger flow "
            "as the security page states the platform "
            "limit, available for self hosted GitLab."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root, text + "\n\n" + sentence + "\n"
            )
            self.assertEqual(self.problems(root), [])

    def test_round37_below_limit_figure_fails_as_other_than(self):
        # R37-ST-01. The figure rule tests inequality, so
        # a figure below the pinned limit fails too, and
        # the problem states the rule as other than.
        plant = (
            "A Deep Scan can read up to 10 linked "
            "repositories on any plan."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "other than the pinned limit of 20" in p
                    for p in problems
                ),
                problems,
            )


    def test_round37_neighbouring_limit_on_another_surface_passes(self):
        # Gate review repair. A limit on another surface in
        # the partner sentence states no linked repository
        # cap, so the pair must pass.
        sentence = (
            "A Deep Scan can read linked repositories "
            "across a workspace. The message size limit is "
            "40 on this surface."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root, text + "\n\n" + sentence + "\n"
            )
            self.assertEqual(self.problems(root), [])

    def test_round37_self_corrected_cap_figure_passes(self):
        # Gate review repair. A figure the same sentence
        # corrects to the pinned figure across a correction
        # word states the pinned cap in the end and must
        # pass.
        sentence = (
            "A Deep Scan can read linked repositories "
            "across a workspace. The cap for that reading "
            "is 50, no, it is 20 on any plan."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root, text + "\n\n" + sentence + "\n"
            )
            self.assertEqual(self.problems(root), [])

    def test_round37_fixreview_first_clause_negation_no_guard(self):
        # R37F-RT-10. A comma and clause opening on a
        # pronoun subject resets the claim stretch, so a
        # negation in the first clause no longer guards
        # the availability the second clause asserts.
        plant = (
            "Linked source is not a separate product in "
            "the scan trigger flow, and it is available "
            "on self hosted GitLab."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "promises Deep Scan linked source" in p
                    for p in problems
                ),
                problems,
            )

    def test_round37_fixreview_cap_split_across_three_fails(self):
        # R37F-RT-11. The cap frame rule judges every
        # ordered pair inside a triple window, so a cap
        # stated two sentences after the linked reading
        # still binds to it.
        plant = (
            "A Deep Scan can read linked repositories "
            "across a workspace. The scan trigger flow "
            "records that reading in its summary. The cap "
            "for that reading is 50 on any plan."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "linked repository cap of 50" in p
                    for p in problems
                ),
                problems,
            )

    def test_round37_fixreview_platform_split_across_three_fails(self):
        # R37F-RT-11. The platform branch reads triples,
        # so a platform offer two sentences after the
        # linked sentence still binds to it.
        plant = (
            "Deep Scan linked source runs in the scan "
            "trigger flow. The packet lists each repository "
            "beside its diff. It also runs on self hosted "
            "GitLab."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "promises Deep Scan linked source" in p
                    for p in problems
                ),
                problems,
            )

    def test_round37_confirm_second_bare_figure_in_frame_fails(self):
        # R37C-RT-06. A tied frame sentence can state a
        # second repository figure with no frame of its
        # own beside the pinned figure, and the bare
        # figure is judged under the same guards.
        plant = (
            "Deep Scan can read linked repositories across "
            "a workspace. The cap for that reading is 20 "
            "repositories in the trigger flow and 50 "
            "repositories in the summary report."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "linked repository cap of 50" in p
                    for p in problems
                ),
                problems,
            )

    def test_round37_fixreview_platform_negated_in_own_sentence(self):
        # R37F-RT-12. A platform negated inside its own
        # sentence states the limit itself, so an offer in
        # the partner sentence must not bind to it.
        pair_text = (
            "Linked source is available on GitHub Cloud. "
            "For self hosted GitLab it remains unavailable."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root, text + "\n\n" + pair_text + "\n"
            )
            self.assertEqual(self.problems(root), [])

    def test_round37_fixreview_report_cap_in_partner_passes(self):
        # R37F-RT-12. A cap frame whose sentence names no
        # reading and no linked repositories caps its own
        # subject, report entries here, and must not bind
        # to the linked reading beside it.
        pair_text = (
            "Deep Scan can read up to 20 linked "
            "repositories across a workspace. The summary "
            "cap for that report is 50 entries."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root, text + "\n\n" + pair_text + "\n"
            )
            self.assertEqual(self.problems(root), [])

    def test_round37_confirm2_platform_across_four_fails(self):
        # R37C-RT-06. The platform claim split across four
        # sentences with two fillers between the halves
        # stands in no window of three, and the four
        # sentence reading must catch it.
        plant = (
            "Deep Scan linked source runs in the scan "
            "trigger flow. The packet lists each repository "
            "beside its diff. The summary records that "
            "reading in full. It also runs on self hosted "
            "GitLab."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "promises Deep Scan linked source" in p
                    for p in problems
                ), problems
            )

    def test_round37_confirm2_prefix_noun_subject_reset_fails(self):
        # R37C-RT-07. A comma and clause opening on the
        # claim noun subject restated is the same reset as
        # the pronoun form, so the first clause negation
        # does not guard the offer in the second.
        plant = (
            "Linked source is not a separate product in "
            "the scan trigger flow, and linked source is "
            "available on self hosted GitLab."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "promises Deep Scan linked source" in p
                    for p in problems
                ), problems
            )


    def test_round38_platform_across_five_sentences_fails(self):
        # R38-RT-08. The platform claim split across five
        # sentences with three fillers between the halves
        # stands in no window of four, and the paragraph
        # scope reading must catch it.
        plant = (
            "Deep Scan linked source runs in the scan "
            "trigger flow. The packet lists each repository "
            "beside its diff. The summary records that "
            "reading in full. The roster lists each file "
            "in the change beside its diff. It also runs "
            "on self hosted GitLab."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "promises Deep Scan linked source" in p
                    for p in problems
                ), problems
            )

    def test_round38_cap_across_five_sentences_fails(self):
        # R38-RT-08. The linked figure claim split across
        # five sentences must fail the same way.
        plant = (
            "A Deep Scan can read linked repositories "
            "across a workspace. The packet lists each "
            "repository beside its diff. The summary "
            "records that reading in full. The roster lists "
            "each file in the change beside its diff. The "
            "cap for that reading is 50 on any plan."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(problems, problems)

    def test_gate_round38_platform_across_paragraphs_fails(self):
        # R38G-RT-02. The platform claim split across a
        # paragraph break inside one block stands in no
        # paragraph window, and the claim scope reading
        # must catch it.
        plant = (
            "Deep Scan linked source runs in the scan "
            "trigger flow. The packet lists each repository "
            "beside its diff. The summary records that "
            "reading in full. The roster lists each file "
            "in the change beside its diff.\n\n"
            "It also runs on self hosted GitLab."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "promises Deep Scan linked source" in p
                    for p in problems
                ), problems
            )

    def test_gate_round38_prefix_reset_on_a_possessive_subject(self):
        # R38G-RT-06. A comma and clause opening on a
        # possessive led subject restatement, our summary,
        # is the same reset as the article led form, so
        # the first clause negation does not guard the
        # offer in the second.
        plant = (
            "Linked source is not a separate product in "
            "the scan trigger flow, and our summary is "
            "available on self hosted GitLab."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "promises Deep Scan linked source" in p
                    for p in problems
                ), problems
            )

    def test_round38_prefix_reset_on_an_unlisted_noun_subject(self):
        # R38-RT-09. A comma and clause opening on a noun
        # subject the earlier reset list never named, the
        # summary, is the same reset, so the first clause
        # negation does not guard the offer in the second.
        plant = (
            "Linked source is not a separate product in "
            "the scan trigger flow, and the summary is "
            "available on self hosted GitLab."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "promises Deep Scan linked source" in p
                    for p in problems
                ), problems
            )


if __name__ == "__main__":
    unittest.main()
