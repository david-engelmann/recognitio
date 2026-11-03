"""Top 20 item 19, the submission packs gate script.

The script at scripts/check_submissions.py pins the three
submission packs and the manifest facts their evidence checks
rest on. These tests prove the pin fires for a real reason on
the claims the packs rest on. A pack that drops its
unsubmitted sentence, its read date, its route, its owner act
section, or one of its pinned figures, a pack that claims a
filed or live listing in any case or ordinary wording, a pack
that promises a review timeline, a manifest that loses or
drifts a fact a pack asserts, a manifest path in a forbidden
shape, a portable manifest that leaves the closed field set
of its specification, and a version bump the packs do not
follow each fail the gate.
"""

import importlib.util
import json
import os
import re
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FILES = (
    "docs/submission-cursor.md",
    "docs/submission-claude.md",
    "docs/submission-agent-plugins.md",
    ".agents/skills/recognitio/SKILL.md",
    "agents/reviewer.md",
    "output-styles/packet.md",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    ".cursor-plugin/plugin.json",
    ".cursor-plugin/marketplace.json",
    ".cursor-plugin/skills/recognitio/SKILL.md",
    ".cursor-plugin/rules/recognitio.mdc",
    "agent-plugins-package/plugin.json",
    "agent-plugins-package/skills/recognitio/SKILL.md",
    "docs/brand/recognitio-icon.svg",
    "docs/brand/recognitio-icon-512.png",
    "LICENSE",
)

CURSOR_PACK = "docs/submission-cursor.md"
CLAUDE_PACK = "docs/submission-claude.md"
PORTABLE_PACK = "docs/submission-agent-plugins.md"
CLAUDE_PLUGIN = ".claude-plugin/plugin.json"
CLAUDE_MARKET = ".claude-plugin/marketplace.json"
CURSOR_PLUGIN = ".cursor-plugin/plugin.json"
CURSOR_MARKET = ".cursor-plugin/marketplace.json"
PORTABLE = "agent-plugins-package/plugin.json"


GIT_LOCATION_VARS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_NAMESPACE",
)


def scrubbed_git_env():
    """The caller environment with the git location names removed."""
    return {
        key: value
        for key, value in os.environ.items()
        if key not in GIT_LOCATION_VARS
    }


def load_script(name):
    path = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(
        "submissions_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestCheckSubmissions(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_submissions")

    def make_layout(self, tmp):
        root = Path(tmp) / "root"
        for rel in FILES:
            source = ROOT / rel
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        return root

    def problems(self, root):
        return self.mod.submissions_problems(root)

    def read_json(self, root, rel):
        return json.loads((root / rel).read_text(encoding="utf-8"))

    def write_json(self, root, rel, data):
        (root / rel).write_text(json.dumps(data), encoding="utf-8")

    def mutate_json(self, rel, change):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_json(root, rel)
            change(data)
            self.write_json(root, rel, data)
            return self.problems(root)

    def mutate_text(self, rel, change):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / rel
            path.write_text(
                change(path.read_text(encoding="utf-8")),
                encoding="utf-8")
            return self.problems(root)

    def mutate_raw(self, rel, text):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            (root / rel).write_text(text, encoding="utf-8")
            return self.problems(root)

    def test_the_shipped_tree_holds(self):
        self.assertEqual(self.mod.submissions_problems(ROOT), [])

    def figure_layout(self, tmp):
        """A layout whose pack figures are restated to its own tree.

        The figure check measures a whole tree, so the scratch
        layout gains the demo recording the largest file figure
        names and its pack figures are rewritten to the figures
        the gate itself measures on that layout. What remains
        under test is the comparison, which is the gate.
        """
        root = self.make_layout(tmp)
        target = root / "docs" / "images"
        target.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(
            ROOT / "docs" / "images"
            / "recognitio-cursor-agent-demo.gif",
            target / "recognitio-cursor-agent-demo.gif")
        measured = self.mod.tree_measurements(root)
        self.assertIsNotNone(measured)
        pack = root / CLAUDE_PACK
        text = re.sub(
            r"\s+", " ", pack.read_text(encoding="utf-8"))

        def fmt(value):
            return format(value, ",")

        text = re.sub(
            r"The repo holds [0-9]+ files",
            "The repo holds %d files" % measured["count"], text)
        text = re.sub(
            r"held [0-9]+ files",
            "held %d files" % measured["count"], text)
        text = re.sub(
            r"at [0-9]+ files against a cap",
            "at %d files against a cap" % measured["count"], text)
        text = re.sub(
            r"demo recording at [0-9,]+ bytes",
            "demo recording at %s bytes"
            % fmt(measured["largest_size"]), text)
        text = re.sub(
            r"largest file that is not an image or a font is "
            r"\S+ at [0-9,]+ bytes",
            "largest file that is not an image or a font is "
            "%s at %s bytes" % (
                measured["largest_plain_path"],
                fmt(measured["largest_plain_size"])), text)
        text = re.sub(
            r"over all [0-9]+ files in the tree",
            "over all %d files in the tree" % measured["scan_files"],
            text)
        pack.write_text(text, encoding="utf-8")
        return root

    def test_the_figure_check_holds_on_a_measured_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            problems = []
            self.mod.figure_problems(root, problems)
            self.assertEqual(problems, [])

    def test_a_falsified_largest_file_figure_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            measured = self.mod.tree_measurements(root)
            pack = root / CLAUDE_PACK
            text = pack.read_text(encoding="utf-8")
            claimed = format(measured["largest_size"], ",")
            falsified = format(measured["largest_size"] + 1, ",")
            pack.write_text(
                text.replace(
                    "at %s bytes" % claimed,
                    "at %s bytes" % falsified),
                encoding="utf-8")
            problems = []
            self.mod.figure_problems(root, problems)
            self.assertTrue(
                any("largest file" in p for p in problems),
                problems)

    def test_a_falsified_file_count_figure_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            measured = self.mod.tree_measurements(root)
            pack = root / CLAUDE_PACK
            text = pack.read_text(encoding="utf-8")
            pack.write_text(
                text.replace(
                    "The repo holds %d files" % measured["count"],
                    "The repo holds %d files"
                    % (measured["count"] + 1)),
                encoding="utf-8")
            problems = []
            self.mod.figure_problems(root, problems)
            self.assertTrue(
                any("holds" in p for p in problems), problems)

    def test_a_falsified_description_length_figure_fails(self):
        problems = self.mutate_text(
            CLAUDE_PACK,
            lambda t: t.replace(
                "the skill at 548 characters",
                "the skill at 549 characters"))
        self.assertTrue(
            any("description lengths" in p for p in problems),
            problems)

    def test_a_duplicated_falsified_figure_pair_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            text = pack.read_text(encoding="utf-8")
            pack.write_text(
                text + "\nThe repo holds 999 files. Its largest "
                "file is the demo recording at 1 bytes.\n",
                encoding="utf-8")
            problems = []
            self.mod.figure_problems(root, problems)
            self.assertTrue(
                any("holds 999 files" in p for p in problems),
                problems)
            self.assertTrue(
                any("largest file is the demo" in p
                    for p in problems), problems)

    def test_a_reworded_file_count_statement_fails_as_unverifiable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            measured = self.mod.tree_measurements(root)
            pack = root / CLAUDE_PACK
            text = pack.read_text(encoding="utf-8")
            pack.write_text(
                text.replace(
                    "The repo holds %d files" % measured["count"],
                    "The repository contains 999 files"),
                encoding="utf-8")
            problems = []
            self.mod.figure_problems(root, problems)
            self.assertTrue(
                any("file count figure" in p
                    and "unverifiable" in p for p in problems),
                problems)

    def test_a_duplicated_falsified_scan_result_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            text = pack.read_text(encoding="utf-8")
            pack.write_text(
                text + "\nThe credential pattern scan returned "
                "999 hits.\n",
                encoding="utf-8")
            problems = []
            self.mod.figure_problems(root, problems)
            self.assertTrue(
                any("returned 999 hits" in p for p in problems),
                problems)

    def test_a_comma_grouped_file_count_figure_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            text = pack.read_text(encoding="utf-8")
            pack.write_text(
                text + "\nThe repo holds 9,999 files.\n",
                encoding="utf-8")
            problems = []
            self.mod.figure_problems(root, problems)
            self.assertTrue(
                any("holds 9,999 files" in p for p in problems),
                problems)

    def test_a_lowercase_file_count_figure_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            text = pack.read_text(encoding="utf-8")
            pack.write_text(
                text + "\nthe repo holds 999 files.\n",
                encoding="utf-8")
            problems = []
            self.mod.figure_problems(root, problems)
            self.assertTrue(
                any("holds 999 files" in p for p in problems),
                problems)

    def test_a_comma_grouped_scan_count_figure_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            text = pack.read_text(encoding="utf-8")
            pack.write_text(
                text + "\nA credential pattern scan over all "
                "9,999 files in the tree returned zero hits.\n",
                encoding="utf-8")
            problems = []
            self.mod.figure_problems(root, problems)
            self.assertTrue(
                any("ran over 9,999 files" in p for p in problems),
                problems)

    def test_true_restated_figures_in_sibling_phrasings_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            measured = self.mod.tree_measurements(root)
            pack = root / CLAUDE_PACK
            text = pack.read_text(encoding="utf-8")
            pack.write_text(
                text + "\nthe repo holds %d files. The credential "
                "pattern scan returned zero hits.\n"
                % measured["count"],
                encoding="utf-8")
            problems = []
            self.mod.figure_problems(root, problems)
            self.assertEqual(problems, [])

    def falsified_restatements(self, measured):
        """Falsified figures in the sibling phrasings a restatement chooses.

        The corpus is the final red team shapes beside the
        lane 1 and lane 2 shapes. Each sentence states one
        priced figure in words a writer restating the figure
        for a summary would plausibly choose, with a verb,
        tense, connective or ordering outside the canonical
        sentence, beside the true canonical statements of the
        measured layout.
        """
        plain = measured["largest_plain_path"]
        return (
            "The repo holds a total of 9,999 files.",
            "The repo holds 9,999 tracked files.",
            "The repo held 9,999 files.",
            "There are 9,999 files in the repo.",
            "The file count of the repo is 9,999.",
            "The repo stands at 9,999 files against the cap "
            "of 512 files.",
            "The repository contains 999 files.",
            "The credential pattern scan returned 999 "
            "credential hits.",
            "The credential pattern scan returned 999 total "
            "hits.",
            "The credential pattern scan returned a total of "
            "999 hits.",
            "The credential pattern scan returned: 999 hits.",
            "The credential pattern scan returned nine hits.",
            "The credential pattern scan yielded 999 hits.",
            "The credential pattern scan covered all 9,999 "
            "files in the tree and returned zero hits.",
            "A credential pattern scan of all 9,999 files in "
            "the tree returned zero hits.",
            "The demo recording is the largest file at "
            "1 bytes.",
            "The largest file is the demo recording, at "
            "1 bytes.",
            "Its largest file that is not an image or font is "
            "%s at 1 bytes." % plain,
            "The largest plain file is %s at 1 bytes." % plain,
            "The skill description runs to 9,999 characters.",
            "The output style at 9,999 characters and the "
            "reviewer agent at 9,998 characters and the skill "
            "at 9,997 characters.",
            "The three component files carry descriptions, "
            "the skill at roughly 9,999 characters and the "
            "reviewer agent at 122 characters and the output "
            "style at 172 characters.",
        )

    def test_falsified_restatements_in_sibling_phrasings_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            measured = self.mod.tree_measurements(root)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            for shape in self.falsified_restatements(measured):
                pack.write_text(
                    base + "\n" + shape + "\n", encoding="utf-8")
                problems = []
                self.mod.figure_problems(root, problems)
                self.assertTrue(problems, shape)

    def test_true_restatements_in_sibling_phrasings_fail_as_unpriced(self):
        # The inverted reading. A true value stated outside
        # the canonical form is still refused, by name as an
        # unpriced figure statement, because the gate judges
        # the canonical forms on value and does not judge the
        # value of arbitrary prose at all.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            measured = self.mod.tree_measurements(root)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            plain = measured["largest_plain_path"]
            true_shapes = (
                "The repo holds a total of %d files."
                % measured["count"],
                "The repo held %d files." % measured["count"],
                "There are %d files in the repo."
                % measured["count"],
                "The file count of the repo is %d."
                % measured["count"],
                "The credential pattern scan returned a total "
                "of zero hits.",
                "The credential pattern scan yielded zero hits.",
                "The demo recording is the largest file at %s "
                "bytes." % format(measured["largest_size"], ","),
                "The largest plain file is %s at %s bytes."
                % (plain, format(
                    measured["largest_plain_size"], ",")),
                "The skill description runs to 548 characters.",
                "The output style at 172 characters and the "
                "reviewer agent at 122 characters and the "
                "skill at 548 characters.",
            )
            for shape in true_shapes:
                pack.write_text(
                    base + "\n" + shape + "\n", encoding="utf-8")
                problems = []
                self.mod.figure_problems(root, problems)
                self.assertTrue(
                    any("unpriced figure statement" in p
                        for p in problems),
                    (shape, problems))

    def falsified_next_phrasings(self, measured):
        """Falsified figures in the phrasings the next round out chose.

        The corpus is the lane 3 red team shapes beside the
        spec seat shapes. Each statement restates one priced
        figure in ordinary pack prose one step past the
        grammar the earlier rounds priced, by an article
        form of a spelled number, a count noun the earlier
        reading did not anchor on, a distance or a sentence
        split, a binary unit, a synonym, or a summary noun
        phrase with no files noun beside its number.
        """
        return (
            "The repo holds a hundred files.",
            "The repo holds a thousand files.",
            "The repo holds over a thousand files.",
            "The credential pattern scan returned a hundred "
            "hits.",
            "The credential pattern scan returned a dozen "
            "hits.",
            "The skill description runs to a hundred "
            "characters.",
            "The repo comprises 9,999 entries.",
            "The tree totals 9,999 items.",
            "The scan covered 9,999 file entries in the tree.",
            "The repo holds 9,999.",
            "The repo holds files numbering 9,999.",
            "The repo holds 9,999 of the many tracked files "
            "in total.",
            "The repo holds many files. The count stands at "
            "9,999.",
            "The repo file count stands revealed. It comes "
            "to 9,999.",
            "The scan covered the whole tree. All 9,999 files "
            "were in scope and it returned zero hits.",
            "| Files in the repo | 9,999 |",
            "- Files in the repo: 9,999",
            "The scan returned 999 results in the full report "
            "that the reviewers later recorded as hits.",
            "The demo recording is the largest file. It "
            "stands at 1 bytes.",
            "The largest file is the demo recording at "
            "593 KiB.",
            "The largest file is the demo recording at "
            "1 byte.",
            "The biggest file is the demo recording at "
            "1 bytes.",
            "The largest file is the poster image at %s "
            "bytes." % format(measured["largest_size"], ","),
            "The skill description runs long, at 9,999 "
            "characters.",
            "The skill description is 9,999 chars long.",
            "The agent description runs to 9,999 characters.",
            "The skill/reviewer descriptions run to 9,999 "
            "characters in total.",
            "The hits from the scan total 999.",
            "The total number of hits from the scan is 999.",
            "The repo file total is 9,999.",
            "The number of files in the repo comes to 9,999.",
        )

    def test_falsified_restatements_in_the_next_phrasings_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            measured = self.mod.tree_measurements(root)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            for shape in self.falsified_next_phrasings(measured):
                pack.write_text(
                    base + "\n" + shape + "\n", encoding="utf-8")
                problems = []
                self.mod.figure_problems(root, problems)
                self.assertTrue(problems, shape)

    def test_true_bound_cap_and_dated_restatements_pass(self):
        # The broadening has a second direction. A gate that
        # reds on the truthful forms of its own figures, the
        # bounds and caps and dated restatements the pack
        # itself writes in, teaches the next writer to stop
        # restating figures at all. Each statement below is
        # true of the measured layout it stands beside.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            measured = self.mod.tree_measurements(root)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            plain = measured["largest_plain_path"]
            true_shapes = (
                "The repo holds over %d files."
                % (measured["count"] - 1),
                "The repo holds between %d and %d files."
                % (measured["count"] - 1,
                   measured["count"] + 1),
                "The credential pattern scan returned fewer "
                "than five hits.",
                "The credential pattern scan returned between "
                "zero and five hits.",
                "The repo is capped at 512 files.",
                "The repo must stay under a maximum of 512 "
                "files.",
                "On 2026-10-01 the repo held 999 files, "
                "before pruning brought it to %d files."
                % measured["count"],
                "The bundled linter reported 42 hits on its "
                "own test corpus, while the credential scan "
                "returned zero hits.",
                "The second largest file is %s at %s bytes."
                % (plain, format(
                    measured["largest_plain_size"], ",")),
                "The largest file is the demo recording at "
                "%s bytes, beside the pack at "
                "docs/submission-claude.md."
                % format(measured["largest_size"], ","),
                "Its largest file that is not an image or a "
                "font is %s at %s bytes, under the 256 KiB "
                "capped at 262,144 bytes by the checklist."
                % (plain, format(
                    measured["largest_plain_size"], ",")),
                "The 2026 scan returned zero hits.",
                "The repo holds %d files across 3 top level "
                "folders." % measured["count"],
                "The credential pattern scan returned no more "
                "than five hits.",
                "The repo holds no fewer than %d files."
                % measured["count"],
                "The repo holds no more than %d files."
                % (measured["count"] + 1),
                "The skill allows 1,024 characters in a "
                "prompt.",
            )
            for shape in true_shapes:
                pack.write_text(
                    base + "\n" + shape + "\n", encoding="utf-8")
                problems = []
                self.mod.figure_problems(root, problems)
                self.assertEqual(problems, [], shape)

    def test_the_lane5_next_shapes_fail_by_name(self):
        # The lane 4 red team shapes under the inverted
        # reading. An abbreviation must not split a figure
        # sentence away from judgement, a decimal with a unit
        # states a figure, the scan result stands under its
        # whole noun family, a vague magnitude word states a
        # value, a negated bound is judged as the bound it
        # states, and the next unit and anchor synonyms of
        # the priced quantities are refused outside the
        # canonical form.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            measured = self.mod.tree_measurements(root)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            shapes = (
                "The repo holds approx. 9,999 files.",
                "The count stands at approx. 9,999.",
                "The repo holds ca. 9,999 files.",
                "The repo holds c. 9,999 files in total.",
                "The largest file is the demo recording at "
                "0.5 MiB.",
                "The largest file is the demo recording at "
                "607.3 KiB.",
                "The largest plain file stands at 15.97 KiB.",
                "The skill description runs to 0.548 thousand "
                "characters.",
                "The credential pattern scan returned 999 "
                "results.",
                "The scan found 999 matches.",
                "The scan yielded 999 findings.",
                "The credential check flagged 999 positives.",
                "The credential scan flagged 999 issues.",
                "The repo holds thousands of files.",
                "The repo holds hundreds of files.",
                "The repo holds a few thousand files.",
                "The repo holds several thousand files.",
                "The credential pattern scan returned dozens "
                "of hits.",
                "The repo holds a billion files.",
                "The descriptions together run to 9,999 "
                "characters.",
                "The repo holds no fewer than 9,999 files.",
                "The repo holds no less than 9,999 files.",
                "The scan returned no fewer than 999 hits.",
                "The largest file is the demo recording at "
                "1 B.",
                "The largest file is the demo recording at "
                "607,308 octets.",
                "The heaviest file is the demo recording at "
                "1 bytes.",
                "The most sizeable file is the demo recording "
                "at 1 bytes.",
                "The top file by size is the demo recording "
                "at 1 bytes.",
                "The skill description runs to 9,999 glyphs.",
                "The repo tracks 9,999 paths.",
                "The skill has a description. Its length is "
                "9,999 characters.",
                "The file count amounts to 9,999.",
                "| Figure | Value |\n| Files | 9,999 |",
                "The file count of the repo is %d, spread "
                "over 3 top level folders." % measured["count"],
                "The skill description for version 2 runs to "
                "548 characters.",
                "The skill allows 1,024 characters in a "
                "prompt, and its description runs to 548 "
                "characters.",
            )
            for shape in shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertTrue(problems, shape)

    def test_the_lane6_next_shapes_fail_by_name(self):
        # The lane 5 review shapes. The scan carryover is
        # consumed like the other quantities, a priced
        # subject named outright asserts its size with no
        # superlative, a sentence dated with the pack its own
        # measurement date is judged, a false file count cap
        # is judged against the stated cap, and the next
        # anchor, noun, subject and value forms of the priced
        # quantities are refused outside the canonical form.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            measured = self.mod.tree_measurements(root)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            plain = measured["largest_plain_path"]
            shapes = (
                "The credential scan has its results. The "
                "total came to 999.",
                "The demo recording weighs in at 999,999 "
                "bytes.",
                "The demo recording runs to 999,999 bytes.",
                "The demo recording is 999,999 bytes long.",
                "The demo recording takes up 999,999 bytes.",
                "%s runs to 1 bytes." % plain,
                "| Demo recording | 999,999 bytes |",
                "On 2026-10-27 the tree contained 9,999 "
                "files.",
                "As of 2026-10-27, the archive of the tree "
                "totals 9,999 files.",
                "The tree contained 9,999 files on 2026-10-27.",
                "Dated 2026-10-27, the demo recording stands "
                "at 1 bytes as the largest file.",
                "The repo is capped at 9,999 files.",
                "The cap stands at 9,999 files for the repo.",
                "The count stands at est. 9,999.",
                "The weightiest file is the demo recording "
                "at 1 bytes.",
                "The scan returned 999 outcomes.",
                "The bundle holds 9,999 entries.",
                "The package contains 9,999 items.",
                "The archive totals 9,999 entries.",
                "The sweep returned 999 results.",
                "The audit found 999 findings.",
                "The frontmatter summary runs to 9,999 "
                "characters.",
                "| Entries | 9,999 |",
                "| Summary length | 9,999 characters |",
                "The repository was counted. It holds 9,999.",
                "The tree was counted yesterday. The census "
                "recorded 9,999.",
                "The largest file is half a MiB.",
                "The largest file is three quarters of a MiB.",
                "The demo recording is half a MiB in size.",
                "The largest file is between 1 and 2 bytes.",
            )
            for shape in shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertTrue(problems, shape)

    def test_the_lane7_mixed_date_shapes_fail_by_name(self):
        # The lane 6 red team Major and the lane 6 spec
        # Minor on the same root. The dating rule is clause
        # level, so a date in a clause carrying no figure
        # assertion does not exempt an assertion dated with
        # the pack its own measurement date in another
        # clause, and an assertion whose own clause carries
        # no date is governed by the dating of the sentence
        # as a whole, which carries the measurement date in
        # every shape below.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            shapes = (
                "On 2026-10-27 the tree contained 9,999 "
                "files, a figure first drafted on 2025-01-01.",
                "On 2026-10-27 the tree contained 9,999 "
                "files and the 2025-01-01 draft said nothing "
                "of it.",
                "The tree contained 9,999 files on 2026-10-27, "
                "the anniversary of the 2025-01-01 start.",
                "On 2026-10-27 the demo recording weighs in "
                "at 999,999 bytes, a size unchanged since "
                "2025-01-01.",
                "Dated 2026-10-27, the demo recording stands "
                "at 1 bytes as the largest file, as it did on "
                "2025-01-01.",
                "On 2026-10-27, as on 2025-01-01, the tree "
                "contained 9,999 files.",
                "On 2026-10-27 the tree contained 9,999 "
                "files, a change from 2025.",
            )
            for shape in shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertTrue(problems, shape)

    def test_the_lane7_next_shapes_fail_by_name(self):
        # The lane 6 red team Minors on their next shapes.
        # The scan carryover is consumed for a bare valued
        # sentence of ordinary length and across one
        # intervening sentence that states no value, the
        # verification and census names anchor the scan
        # result, the priced subjects assert their sizes
        # under their other names and by a partial path, and
        # the fraction forms past the halves, quarters and
        # thirds, and the priced fractions in their next
        # spellings, state falsified sizes inside anchored
        # sentences.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            shapes = (
                "The credential scan has its results. The "
                "recorded figure for the run came to 999.",
                "The credential scan has its results. The run "
                "recorded a figure of 999 for the tree.",
                "The credential scan has its findings. It "
                "found 999 in the tree as a whole.",
                "The credential scan has its results. All "
                "told, the run came back with 999 for the "
                "tree as a whole.",
                "The repository was counted. The recorded "
                "figure for the run came to 999.",
                "The credential scan has its results. The run "
                "is complete. The total came to 999.",
                "The repo was counted. The run is complete. "
                "It holds 9,999.",
                "The largest file stands unnamed. The run is "
                "complete. It weighs 999,999 bytes.",
                "The verification returned 999 results.",
                "The census returned 999 outcomes.",
                "The hero recording weighs in at 999,999 "
                "bytes.",
                "The demo weighs in at 999,999 bytes.",
                "The recording weighs in at 999,999 bytes.",
                "The demo GIF weighs in at 999,999 bytes.",
                "The gif weighs in at 999,999 bytes.",
                "The cursor agent demo weighs in at 999,999 "
                "bytes.",
                "recognitio/SKILL.md runs to 1 bytes.",
                "SKILL.md runs to 1 bytes.",
                "The skill file runs to 1 bytes.",
                "The SKILL.md file runs to 1 bytes.",
                "The skill runs to 1 bytes.",
                "The largest file is a fifth of a MiB.",
                "The largest file is one fifth of a MiB.",
                "The largest file is two fifths of a MiB.",
                "The largest file is an eighth of a MiB.",
                "The largest file is three eighths of a MiB.",
                "The largest file is a sixth of a MiB.",
                "The largest file is five sixths of a MiB.",
                "The demo recording is a fifth of a MiB in "
                "size.",
                "The largest file is three-quarters of a "
                "MiB.",
                "The largest file is a half MiB.",
                "The largest file is one and a half MiB.",
                "The largest file is quarter of a MiB.",
                "The largest file is 3/4 of a MiB.",
            )
            for shape in shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertTrue(problems, shape)

    def test_the_lane7_docstring_restatements_stand(self):
        # The lane 6 standards Minor on its six instances and
        # the lane 6 spec Minor on the word loads. The
        # restated passages name the postfix bound pairs, the
        # largest plain file among the range quantities, the
        # byte factor units and the refusal a named subject
        # statement meets at any value, the part reading of a
        # spelled number past billions and of an ordinal in a
        # value position, and the class of indeterminate
        # magnitude phrases that state no number, so a
        # restatement that drops any of them fails here.
        figure_doc = " ".join(self.mod.figure_problems.__doc__.split())
        bound_doc = " ".join(self.mod.bound_relation.__doc__.split())
        for phrase in (
            "the largest file size, the largest plain file "
            "size and a description length",
            "verification or census words",
            "together with a size in any byte factor unit",
            "refused as unpriced whatever value it states",
            "Indeterminate magnitude phrases that state no "
            "number, myriad, countless and loads of among "
            "them and their kin",
            "A spelled number past billions that carries a "
            "readable cardinal, as five trillion, is read as "
            "that cardinal and refused as unpriced for it",
            "An ordinal form in a value position is "
            "likewise read as the cardinal or the digits "
            "it carries",
            "fraction denominators past tenths state no "
            "fraction the gate reads",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, figure_doc)
        self.assertIn(
            "or the pairs or more, or fewer or or less "
            "standing after the number and its unit",
            bound_doc)

    def test_the_lane7_restated_readings_behave_as_stated(self):
        # The probed behaviour behind the restatements. The
        # postfix bound pairs judge the largest file as the
        # bound they state in both directions, a largest
        # plain file range is judged on value, a named
        # subject size in a byte factor unit and a true size
        # stated outright are both refused as unpriced, and
        # the two part read forms past the boundary are
        # refused for the cardinal they carry, beside the
        # boundary forms that pass whole.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            measured = self.mod.tree_measurements(root)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            plain = measured["largest_plain_path"]
            fail_shapes = (
                "The largest file is 999,999 bytes or more.",
                "The largest file is 100 bytes or fewer.",
                "The largest file is 100 bytes or less.",
                "%s is between 1 and 2 bytes." % plain,
                "The demo recording weighs 600 KiB.",
                "The demo recording is %s bytes."
                % format(measured["largest_size"], ","),
                "The repo holds five trillion files.",
                "The repo holds the nine thousand nine "
                "hundred and ninety ninth files.",
            )
            for shape in fail_shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertTrue(problems, shape)
            pass_shapes = (
                "The largest file is 100 bytes or more.",
                "The largest file is 999,999 bytes or fewer.",
                "%s is between 1 and 99,999 bytes." % plain,
                "The repo holds a trillion files.",
                "The repo holds a myriad of files.",
                "The repo holds countless files.",
                "The repo holds loads of files.",
            )
            for shape in pass_shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertEqual(problems, [], shape)

    def test_the_lane7_historical_mixed_date_shape_passes(self):
        # The declared historical boundary under the clause
        # rule. The figure is stated of a genuinely
        # historical date in its own clause, and the
        # measurement date in the second clause carries no
        # figure, so the assertion stands exempt and the
        # sentence passes.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            shape = (
                "On 2025-01-01 the tree contained 9,999 "
                "files and on 2026-10-27 it was rechecked.")
            pack.write_text(
                base + "\n" + shape + "\n", encoding="utf-8")
            problems = []
            self.mod.figure_problems(root, problems)
            self.assertEqual(problems, [], shape)

    def test_the_lane8_dating_shapes_fail_by_name(self):
        # The lane 7 red team Major on its three roots and
        # the lane 7 spec Minor on the spelled month forms.
        # The governing dating rule of this lane stands in
        # the figure docstring, a preamble dating governs
        # every assertion in the sentence except an
        # assertion inside a subordinate clause carrying
        # its own complete date and figure, month and year
        # and year alone dating count at their granularity,
        # and any measurement dating in a governing
        # position or any ambiguity judges the assertion.
        # Every shape below states its priced figure of the
        # measurement dating and must fail.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            shapes = (
                "On 2026-10-27, the tree contained 9,999 "
                "files in the folder created on 2025-01-01.",
                "Dated 2026-10-27, the demo recording made "
                "on 2025-01-01 weighs in at 999,999 bytes.",
                "Dated 2026-10-27, the tree that held 12 "
                "files on 2025-01-01 contained 9,999 files.",
                "Measured on 2026-10-27, the folder created "
                "on 2025-01-01 held a tree of 9,999 files.",
                "Read on 2026-10-27, the pack describing "
                "the 2025-01-01 tree of 12 files states the "
                "tree contained 9,999 files.",
                "In October 2026 the tree contained 9,999 "
                "files, a figure first drafted on 2025-01-01.",
                "The tree contained 9,999 files during "
                "October 2026, a count first taken on "
                "2025-01-01.",
                "As of October 2026 the tree contained 9,999 "
                "files and the 2025-01-01 draft said nothing "
                "of it.",
                "Measured over October 2026, the tree "
                "contained 9,999 files, after the 2025-01-01 "
                "draft.",
                "The tree contained 9,999 files in October "
                "2026, the anniversary of the 2025-01-01 "
                "start.",
                "In 2026, the tree contained 9,999 files "
                "first drafted on 2025-01-01.",
                "Dated 2026-10-27, the tree contained 9,999 "
                "files in 2025.",
                "The tree contained 9,999 files, measured "
                "in 2026 and drafted on 2025-01-01.",
                "The tree contained 9,999 files since the "
                "2025-01-01 draft while measured on "
                "2026-10-27.",
            )
            for shape in shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertTrue(problems, shape)

    def test_the_lane8_historical_dating_shapes_pass(self):
        # The other limb of the lane 8 dating rule. The
        # historical control passes because its preamble
        # is the historical date and the measurement date
        # in it governs no figure, the spelled month and
        # month and year historical forms pass again, and
        # a historical range split by its own and stands
        # exempt whole under its historical preamble.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            shapes = (
                "On 2025-01-01 the tree contained 9,999 "
                "files and on 2026-10-27 it was rechecked.",
                "On 27 October 2025 the tree contained "
                "9,999 files.",
                "The tree contained 9,999 files in October "
                "2025.",
                "In October 2025 the tree contained 12 "
                "files.",
                "On 27 October 2025 the tree contained 12 "
                "files, and on 2026-10-27 it was rechecked.",
                "The tree contained 12 files in October "
                "2025 and on 2026-10-27 it was rechecked.",
                "On 2025-01-01 the tree held between 5 and "
                "20 files, and on 2026-10-27 it was "
                "rechecked.",
                "On 2026-10-27 the tree held between 15 "
                "and 20 files, and on 2025-01-01 it held "
                "12 files.",
                "In 2025 the tree contained 9,999 files, a "
                "change noted in 2026.",
            )
            for shape in shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertEqual(problems, [], shape)
            figure_doc = " ".join(
                self.mod.figure_problems.__doc__.split())
            for phrase in (
                "stands exempt if and only if it passes "
                "the exemption test in the order stated "
                "here",
                "read at every grain present",
                "a date standing attributive before a noun "
                "counting as dating in the clause, there "
                "being no skip set",
                "a label fragment glued from the line above "
                "in the flattened text",
                "whatever opener it stands under, on, in, "
                "from or since among them",
                "October 2026 is the measurement month and "
                "2026 alone is the measurement year",
                "The false failure cost of this rule is "
                "declared beside it",
            ):
                with self.subTest(phrase=phrase):
                    self.assertIn(phrase, figure_doc)

    def test_the_lane9_next_shapes_fail_by_name(self):
        # The lane 8 red team Minors on their next shapes.
        # The carryover tally set in its next words and the
        # scan anchors in their next names carry falsified
        # figures, the demo recording asserts its size as
        # the clip and the footage, and the proportion
        # forms past the priced percent and decimal of
        # forms state falsified sizes inside anchored
        # sentences.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            shapes = (
                "The credential scan has its results. The "
                "recorded sum for the whole run across the "
                "tree was 999.",
                "The repository was counted. The recorded "
                "sum for the whole run across the tree was "
                "9,999.",
                "The credential scan has its results. The "
                "run came out to 999 for the whole tree "
                "today.",
                "The repository was counted. The run came "
                "out to 9,999 for the whole tree today.",
                "The credential scan has its results. The "
                "run yielded 999 across the whole tree in "
                "the end.",
                "The credential scan has its results. "
                "Overall the run recorded 999 across the "
                "whole tree.",
                "The credential scan has its results. In "
                "all the run recorded 999 across the whole "
                "tree.",
                "The probe returned 999 results.",
                "The examination returned 999 results.",
                "The clip weighs in at 999,999 bytes.",
                "The footage weighs in at 999,999 bytes.",
                "The largest file is fifty percent of a "
                "MiB.",
                "The demo recording is fifty percent of a "
                "MiB in size.",
                "The largest file is 50 per cent of a MiB.",
                "The largest file is 50% of the MiB.",
                "The largest file is .5 of a MiB.",
            )
            for shape in shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertTrue(problems, shape)

    def test_the_lane9_dating_escapes_fail_by_name(self):
        # The lane 8 red team Major on its six roots and
        # the lane 8 standards Major on its tail preamble
        # shape. The exemption test of this lane stands in
        # the figure docstring in the order the reading
        # holds, a clause carrying a complete dating of
        # its own at every grain, every dating in the
        # clause a dating other than the measurement
        # dating, and no measurement dating in a governing
        # position before it, with a measurement phrase
        # judging every main assertion in its sentence.
        # Every shape below states its priced figure of
        # the measurement dating and must fail.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            shapes = (
                "On 2025-01-01, the tree contained 9,999 "
                "files on 2026-10-27.",
                "On 2025-01-01, the tree contained 9,999 "
                "files in October 2026.",
                "In 2025, the tree contained 9,999 files on "
                "2026-10-27.",
                "The tree was archived, which held 9,999 "
                "files in October 2026 beside the folder "
                "created on 2025-01-01.",
                "The tree was archived, which held 9,999 "
                "files in 2026 beside the folder created on "
                "2025-01-01.",
                "Dated 2025-01-01 to 2026-10-27, the tree "
                "contained 9,999 files in the folder created "
                "on 2025-06-01.",
                "The archive was opened, from 2025-01-01 to "
                "2026-10-27 the tree contained 9,999 files.",
                "Evidence From 2026-10-27, the tree "
                "contained 9,999 files in the folder created "
                "on 2025-01-01.",
                "Evidence Since 2026-10-27, the tree "
                "contained 9,999 files in the folder created "
                "on 2025-01-01.",
                "Evidence on 2026-10-27; the tree contained "
                "9,999 files in the folder created on "
                "2025-01-01.",
                "The 2026-10-27 count of 9,999 files is "
                "recorded beside the folder created on "
                "2025-01-01.",
                "The 2026-10-27 figure of 9,999 files is "
                "recorded beside the folder created on "
                "2025-01-01.",
                "The folder created on 2025-01-01 held 12 "
                "files beside the 2026-10-27 count of 9,999 "
                "files.",
                "The tree that held 12 files on 2025-01-01 "
                "had 9,999 files, as measured on "
                "2026-10-27.",
                "The tree that held 12 files on 2025-01-01 "
                "counted 9,999 files, as measured on "
                "2026-10-27.",
                "The recording that held 12 files on "
                "2025-01-01 weighed in at 999,999 bytes, as "
                "measured on 2026-10-27.",
                "On 2025-01-01, the folder that contained "
                "9,999 files on 2026-10-27 was empty.",
                "On 2026-10-27, the report was read on "
                "2025-01-01, the tree contained 9,999 "
                "files.",
            )
            for shape in shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertTrue(problems, shape)

    def test_the_lane9_dating_controls_pass(self):
        # The controls in the other direction under the
        # exemption test. The historical control passes,
        # its figure exempt under the test and the
        # measurement date behind it governing no figure.
        # A historically dated subordinate figure at the
        # end of its sentence is exempt under its own
        # dating, a comma preamble supplies its clause its
        # dating, a subordinate figure under a measurement
        # preamble takes its own dating, and a historical
        # date at the tail of a preceding clause governs a
        # figure clause carrying no dating of its own.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            shapes = (
                "On 2025-01-01 the tree contained 9,999 "
                "files and on 2026-10-27 it was rechecked.",
                "On 2026-10-27, the folder that contained "
                "9,999 files on 2025-01-01 was empty.",
                "On 2025-01-01, the tree contained 9,999 "
                "files.",
                "In October 2025, the tree contained 12 "
                "files.",
                "On 2026-10-27 the pack was read, which "
                "held 12 files on 2025-01-01.",
                "The report was read on 2025-01-01, the "
                "tree contained 9,999 files.",
                "On 2026-10-27 the tree held between 15 "
                "and 20 files, and on 2025-01-01 it held "
                "12 files.",
            )
            for shape in shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertEqual(problems, [], shape)
            figure_doc = " ".join(
                self.mod.figure_problems.__doc__.split())
            for phrase in (
                "A measurement phrase anywhere in the "
                "sentence",
                "a subordinate historical figure inside a "
                "measurement phrased sentence whose clause "
                "the splitter cannot separate is judged "
                "with the sentence",
            ):
                with self.subTest(phrase=phrase):
                    self.assertIn(phrase, figure_doc)

    def test_the_lane10_next_shapes_fail_by_name(self):
        # The lane 9 red team Minors on their next shapes.
        # The carryover tally set in its next words, stood
        # at, came in at and in the end, carries falsified
        # figures in both carryovers, the scan anchors in
        # their next names, survey and analysis, carry one
        # inside a single sentence, the demo recording
        # asserts its size as the film and the reel, and
        # the proportion forms past the priced forms, the
        # spelled number with the percent sign and the
        # hyphenated per-cent, state falsified sizes
        # inside anchored sentences.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            shapes = (
                "The credential scan has its results. The "
                "run stood at 999 for the whole tree.",
                "The repository was counted. The run stood "
                "at 9,999 for the whole tree today.",
                "The credential scan has its results. The "
                "run came in at 999 for the whole tree "
                "today.",
                "The repository was counted. The run came "
                "in at 9,999 for the whole tree today.",
                "The credential scan has its results. The "
                "run recorded 999 in the end for the whole "
                "tree today.",
                "The repository was counted. The run "
                "recorded 9,999 in the end for the whole "
                "tree today.",
                "The survey returned 999 results.",
                "The analysis returned 999 results.",
                "The film weighs in at 999,999 bytes.",
                "The reel weighs in at 999,999 bytes.",
                "The largest file is fifty % of a MiB.",
                "The largest file is 50 per-cent of a MiB.",
            )
            for shape in shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertTrue(problems, shape)

    def test_the_lane11_next_shapes_fail_by_name(self):
        # The lane 10 red team Minors 3, 4 and 5 on
        # their next shapes. The carryover tally set in
        # its next words, added up to, ran to, worked
        # out at and closed at, carries falsified
        # figures in both carryovers, the scan anchors
        # in their next names, inventory, count and
        # tally, carry one inside a single sentence, the
        # demo recording asserts its size as the
        # trailer, the videotape and the showreel, and
        # the proportion forms past the priced forms,
        # the pct abbreviation, the percent stated
        # against the size of the unit and the per
        # mille register, state falsified sizes inside
        # anchored sentences. A marker or a name past
        # these enumerations stands under the declared
        # boundary of its family in the figure passage.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            shapes = (
                "The repository was counted. The run "
                "added up to 9,999 for the whole tree "
                "today.",
                "The repository was counted. The run "
                "ran to 9,999 for the whole tree today.",
                "The repository was counted. The run "
                "worked out at 9,999 for the whole tree "
                "today.",
                "The repository was counted. The run "
                "closed at 9,999 for the whole tree "
                "today.",
                "The credential scan has its results. "
                "The run added up to 999 for the whole "
                "tree.",
                "The credential scan has its results. "
                "The run worked out at 999 for the whole "
                "tree.",
                "The inventory returned 999 results.",
                "The count returned 999 results.",
                "The tally returned 999 results.",
                "The trailer weighs in at 999,999 bytes.",
                "The videotape weighs in at 999,999 "
                "bytes.",
                "The showreel weighs in at 999,999 "
                "bytes.",
                "The largest file is 50 pct of a MiB.",
                "The largest file is 50% the size of a "
                "MiB.",
                "The largest file is 500 per mille of a "
                "MiB.",
            )
            for shape in shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertTrue(problems, shape)

    def test_the_lane10_dating_escapes_fail_by_name(self):
        # The lane 9 red team Major on its five roots.
        # The sentence level backstop of this lane stands
        # in the figure docstring as the fourth step of
        # the exemption test. A between range is read by
        # both its ends wherever its ends stand, a
        # trailing bare dating fragment defeats the
        # exemption of the clause before it, a subordinate
        # figure under a measurement preamble is judged
        # on the folder date standing in its clause
        # notwithstanding, and a participial measurement
        # phrase in any preposition judges in the same
        # way. Every shape below states its priced figure
        # of the measurement dating and must fail.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            shapes = (
                "The tree contained 9,999 files between "
                "October 2025 and October 2026.",
                "The tree contained 9,999 files between "
                "October 2025 and October 27, 2026.",
                "The tree contained 9,999 files between "
                "September 2026 and November 2026.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, on "
                "2026-10-27.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, in October "
                "2026.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01 and on "
                "2026-10-27.",
                "In October 2026, the tree was archived, "
                "which held 9,999 files beside the folder "
                "created on 2025-01-01.",
                "In October 2026, the tree was archived, "
                "which held 9,999 files beside the folder "
                "created in January 2025.",
                "The tree that held 12 files in October "
                "2025 had 9,999 files, on 2026-10-27.",
                "The tree that held 12 files on 1 October "
                "2025 had 9,999 files, on 2026-10-27.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, measured "
                "at 2026-10-27.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, measured "
                "during October 2026.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, as measured "
                "at 2026-10-27.",
            )
            for shape in shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertTrue(problems, shape)

    def test_the_lane10_dating_controls_and_residual_pass(self):
        # The controls in the other direction under the
        # backstop. The historical control passes on its
        # stated ground, the measurement date behind its
        # figure standing in a full independent clause
        # carrying its own subject and verb and no figure
        # and governing no figure. The closing residual
        # of the dating family stands beside it, a
        # measurement event narrated as a full independent
        # clause standing beside a historically dated
        # figure read as the rechecked form, a figureless
        # event clause, the figure exempt on its own
        # dating.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            shapes = (
                "On 2025-01-01 the tree contained 9,999 "
                "files and on 2026-10-27 it was rechecked.",
                "The tree contained 9,999 files on "
                "2025-01-01 and the count was taken on "
                "2026-10-27.",
                "On 2025-01-01 the tree contained 9,999 "
                "files, and on 2026-10-27 the count was "
                "taken.",
            )
            for shape in shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertEqual(problems, [], shape)
            figure_doc = " ".join(
                self.mod.figure_problems.__doc__.split())
            for phrase in (
                "Fourth, the backstop at sentence level",
                "a trailing bare dating fragment among "
                "its forms",
                "A participial measurement phrase in one "
                "of the twelve prepositions named above",
                "does not reach the other assertions of "
                "the sentence",
                "the closing residual of the dating "
                "family",
                "a figureless event clause",
                "telling that narration from a recheck is "
                "a judgement the prose does not settle",
            ):
                with self.subTest(phrase=phrase):
                    self.assertIn(phrase, figure_doc)

    def test_the_lane11_trailing_range_shapes_fail_by_name(self):
        # The lane 10 standards Major on its one reading.
        # A trailing clause that is nothing but a date
        # range never defeated the exemption in its ISO
        # form, because the fragment reading read a range
        # clause by its glued end alone and that reading
        # fired only for capitalised openers. The backstop
        # now reads a range clause standing after the
        # assertion by both its ends, in ISO and spelled
        # forms, capitalised and lower case, and in the
        # and between form. The spelled twin and the
        # priced in clause and before clause ranges hold
        # their verdicts beside the three probed
        # spellings.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            shapes = (
                "The tree contained 9,999 files on "
                "2025-01-01, between 2024-01-01 and "
                "2026-10-27.",
                "The tree contained 9,999 files on "
                "2025-01-01, Between 2024-01-01 and "
                "2026-10-27.",
                "The tree contained 9,999 files on "
                "2025-01-01, and between 2024-01-01 and "
                "2026-10-27.",
                "The tree contained 9,999 files on "
                "2025-01-01, between 2026-10-27 and "
                "2025-01-01.",
                "The tree contained 9,999 files on "
                "2025-01-01, between October 2025 and "
                "October 2026.",
                "The tree contained 9,999 files between "
                "October 2025 and October 2026.",
                "Between 2024-01-01 and 2026-10-27, the "
                "tree contained 9,999 files in the folder "
                "created on 2025-01-01.",
            )
            for shape in shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertTrue(problems, shape)

    def test_the_lane11_backstop_fragment_shapes_fail_by_name(self):
        # The lane 10 spec Minor on the exception wider
        # in code than worded, its two members, and the
        # lane 10 red team Minor 1 on its remaining
        # roots. A trailing verbless fragment carrying a
        # figure noun and a date is a pure dating clause
        # for the backstop on the root B folder date
        # base, the subjectless participial counted form
        # joins the measurement phrase family beside
        # measured, and the ordinary fragment shapes
        # past the priced forms, the taken, measuring,
        # nominal, glued position, as at, glued range
        # and directly before shapes among them, are
        # enumerated into the fragment reading in the
        # same way.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            shapes = (
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, the count "
                "on 2026-10-27.",
                "The tree contained 9,999 files on "
                "2025-01-01 and the count on 2026-10-27.",
                "The tree contained 9,999 files on "
                "2025-01-01, counted on 2026-10-27.",
                "The tree contained 9,999 files on "
                "2025-01-01, measured on 2026-10-27.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, counted "
                "on 2026-10-27.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, with the "
                "count taken on 2026-10-27.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, the count "
                "having been taken on 2026-10-27.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, measuring "
                "the tree on 2026-10-27.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, a "
                "measurement on 2026-10-27.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, taken in "
                "2026.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, on "
                "2026-10-27 at noon.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, in "
                "October 2026 alone.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, on "
                "2026-10-27 at the recount.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, the "
                "2026-10-27 recount.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, Recount "
                "2026-10-27.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, recount "
                "27 October 2026.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, as at "
                "2026-10-27.",
                "The tree contained 9,999 files in "
                "November 2026, the count ran October "
                "2026 to November 2026.",
                "The pack was read, on 2026-10-27, which "
                "held 9,999 files beside the folder "
                "created on 2025-01-01.",
                "The report was read, on 2026-10-27, on "
                "2025-01-01 the tree contained 9,999 "
                "files.",
                "Recount 2026-10-27, the pack was read, "
                "which held 9,999 files beside the "
                "folder created on 2025-01-01.",
                "The pack stands as written. Recount "
                "2026-10-27, the pack was read, "
                "which held 9,999 files beside the "
                "folder created on 2025-01-01.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, the count "
                "on 2025-06-01.",
            )
            for shape in shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertTrue(problems, shape)

    def test_the_finisher_backstop_next_shapes_fail_by_name(self):
        # The lane 11 red team Minor 1 on its roots B
        # and C. A verbless fragment carrying a figure
        # noun one step past the four names, the result,
        # the number and the sum, and a participial
        # fragment of a count verb one step past
        # counted, tallied, totalled, totaled,
        # enumerated and inventoried, each left a
        # falsified figure exempt beside the same
        # dating. The widened noun set and participle
        # family now read them, and the as tallied and
        # as totaled forms stand in the phrase family
        # beside as counted. The measurement
        # phrase in a preposition past the twelve named
        # stands under the declared boundary of the
        # passage and is pinned passing here in that
        # form, under, upon and via among them.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            shapes = (
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, the "
                "result on 2026-10-27.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, the "
                "number on 2026-10-27.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, the sum "
                "on 2026-10-27.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, tallied "
                "on 2026-10-27.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, totalled "
                "on 2026-10-27.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, "
                "enumerated on 2026-10-27.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, "
                "inventoried on 2026-10-27.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, as "
                "tallied on 2026-10-27.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, totaled "
                "on 2026-10-27.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, as "
                "totaled on 2026-10-27.",
            )
            for shape in shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertTrue(problems, shape)
            boundary = (
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, measured "
                "under 2026-10-27.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, measured "
                "upon 2026-10-27.",
                "The tree contained 9,999 files in the "
                "folder created on 2025-01-01, measured "
                "via 2026-10-27.",
            )
            for shape in boundary:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertEqual(problems, [], shape)

    def test_the_lane11_backstop_controls_pass(self):
        # The controls in the other direction under the
        # widened backstop. The standards Minor on the
        # spelled month grain holds in its first and
        # third shapes here, a full independent clause
        # carrying its dating in its content standing
        # outside the fragment reading whole where no
        # finite verb reading reaches it. The historical
        # control, the closing residual pair and a full
        # independent clause carrying a figure noun but
        # no figure value hold their verdicts in the
        # same way, so the exception for a clause with
        # its own subject and verb and no figure still
        # does not reach the other assertions, and the
        # named closing residual still stands as
        # recorded.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            shapes = (
                "The tree contained 9,999 files in "
                "October 2025 and the count was taken in "
                "October 2026.",
                "The tree contained 9,999 files in "
                "October 2025 and the folder was "
                "archived in October 2026.",
                "On 2025-01-01 the tree contained 9,999 "
                "files and on 2026-10-27 it was "
                "rechecked.",
                "The tree contained 9,999 files on "
                "2025-01-01 and the count was taken on "
                "2026-10-27.",
                "On 2025-01-01 the tree contained 9,999 "
                "files, and on 2026-10-27 the count was "
                "taken.",
                "The tree contained 9,999 files on "
                "2025-01-01 and the file count was "
                "recorded on 2026-10-27.",
            )
            for shape in shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertEqual(problems, [], shape)
            figure_doc = " ".join(
                self.mod.figure_problems.__doc__.split())
            for phrase in (
                "one of the twelve prepositions on, in, "
                "over, at, during, by, before, after, "
                "since, from, through or within",
                "A range clause standing after the "
                "assertion is read by both its ends",
                "in the and between form",
                "A trailing verbless fragment carrying "
                "a figure noun",
                "is a pure dating clause for this "
                "backstop",
                "where no finite verb stands before it "
                "in its clause",
                "standing directly before a subordinate "
                "clause or a clause opening with its own "
                "date phrase, after another clause of "
                "the sentence, is read here in the same "
                "way",
                "A participial measurement phrase in one "
                "of the twelve prepositions named above",
            ):
                with self.subTest(phrase=phrase):
                    self.assertIn(phrase, figure_doc)

    def test_the_lane10_relative_clause_grains_fail_by_name(self):
        # The lane 9 spec Minor and the other half of the
        # lane 9 red team root D. The splitter its
        # relative clause expansion searched for an ISO
        # full date alone, so a relative clause dated at
        # month grain, at year grain or by a spelled full
        # date was never separated and a resumed main
        # figure stood exempt on the relative dating. The
        # expansion now takes every date form the reading
        # holds, so each shape below is judged in the
        # same way as its ISO dated twin.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            shapes = (
                "The tree that held 12 files in October "
                "2025 contained 9,999 files, and on "
                "2026-10-27 it was rechecked.",
                "The tree that held 12 files in 2025 "
                "contained 9,999 files, and on 2026-10-27 "
                "it was rechecked.",
                "The tree that held 12 files on 1 October "
                "2025 contained 9,999 files, and on "
                "2026-10-27 it was rechecked.",
                "The tree that held 12 files on October "
                "1, 2025 contained 9,999 files, and on "
                "2026-10-27 it was rechecked.",
            )
            for shape in shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertTrue(problems, shape)

    def test_the_lane10_relative_clause_grain_controls_pass(self):
        # The lane 9 standards Minor in the other
        # direction. An embedded relative figure dated at
        # a spelled grain, at month grain or at year
        # grain under a measurement preamble takes its
        # own dating in the same way as its ISO dated
        # twin, because the splitter now separates its
        # clause at every grain. The declared cost
        # stands beside them in its remaining form, a
        # relative clause resuming in a verb past the
        # splitter its list is not separated, so its
        # historical figure is judged with its sentence
        # under a plain preamble, a false failure and
        # not an escape.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            shapes = (
                "On 2026-10-27, the folder that contained "
                "9,999 files on 27 October 2025 was empty.",
                "On 2026-10-27, the folder that contained "
                "9,999 files in October 2025 was empty.",
                "On 2026-10-27, the folder that contained "
                "9,999 files in 2025 was empty.",
            )
            for shape in shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertEqual(problems, [], shape)
            cost_shape = (
                "On 2026-10-27, the folder that contained "
                "9,999 files on 2025-01-01 seemed empty.")
            pack.write_text(
                base + "\n" + cost_shape + "\n",
                encoding="utf-8")
            problems = []
            self.mod.figure_problems(root, problems)
            self.assertTrue(problems, cost_shape)
            figure_doc = " ".join(
                self.mod.figure_problems.__doc__.split())
            for phrase in (
                "The subordinate limb holds where the "
                "splitter separates the clause",
                "at every grain the reading holds",
                "the remaining effect of that limit is "
                "the false failure cost declared below "
                "and not an escape",
                "is judged with its sentence under a "
                "plain preamble in the same way",
            ):
                with self.subTest(phrase=phrase):
                    self.assertIn(phrase, figure_doc)

    def test_the_lane11_relative_clause_shapes_fail_by_name(self):
        # The lane 10 red team Minor 2 on its three
        # roots and the lane 10 standards Minor 3. The
        # separation read every dating grain and still
        # separated only where a listed main verb stood
        # directly after the relative dating, and a
        # relative clause dated by a spelled full date
        # in the US order was never separated at all,
        # because the comma inside the date cut it
        # across two segments below the widened search.
        # An adverb in the resumption, a verb one step
        # past the list and the ISO month form at the
        # edge of the shared alternation are enumerated
        # into the reading in the same way, a verb past
        # the widened list standing under the declared
        # cost of the family in its judged direction.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            shapes = (
                "The tree that held 12 files in October "
                "2025 still contained 9,999 files, and "
                "on 2026-10-27 it was rechecked.",
                "The tree that held 12 files in October "
                "2025 then contained 9,999 files, and on "
                "2026-10-27 it was rechecked.",
                "The tree that held 12 files in October "
                "2025 numbered 9,999 files, and on "
                "2026-10-27 it was rechecked.",
                "The tree that held 12 files in 2025-10 "
                "contained 9,999 files, and on "
                "2026-10-27 it was rechecked.",
            )
            for shape in shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertTrue(problems, shape)

    def test_the_lane11_relative_clause_controls_pass(self):
        # The controls in the other direction. A
        # relative clause dated by a spelled full date
        # in the US order is separated in the same way
        # as its day first twin, so its historical
        # figure takes its own dating and passes, the
        # second shape of the standards spelled month
        # Minor passes with it once its date stands
        # whole in one clause, and a relative clause
        # dated at ISO month grain takes its own dating
        # in the same way.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            shapes = (
                "On 2026-10-27, the folder that "
                "contained 9,999 files on October 1, "
                "2025 was empty.",
                "The tree contained 9,999 files on "
                "2025-01-01 and the count was taken on "
                "October 27, 2026.",
                "On 2026-10-27, the folder that "
                "contained 9,999 files in 2025-10 was "
                "empty.",
            )
            for shape in shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertEqual(problems, [], shape)
            figure_doc = " ".join(
                self.mod.figure_problems.__doc__.split())
            for phrase in (
                "The comma inside a spelled full date "
                "in the US order is part of the date "
                "and not a clause separator",
                "a resumption adverb standing between "
                "the relative dating and a listed verb",
                "the ISO full date, the ISO month, the "
                "spelled full date",
            ):
                with self.subTest(phrase=phrase):
                    self.assertIn(phrase, figure_doc)

    def test_the_finisher_relative_clause_adverbs_fail_by_name(self):
        # The lane 11 relative clause Minor past the
        # lane 11 repair. The separation read a
        # resumption adverb from a set of five, so a
        # resumption carrying an adverb past the set
        # escaped whole, and two adverbs from inside
        # the set standing together escaped with it.
        # The set now holds twelve adverbs and the
        # reading allows one of them or two of them
        # standing together before the listed verb.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            shapes = (
                "The tree that held 12 files in October "
                "2025 already contained 9,999 files, and "
                "on 2026-10-27 it was rechecked.",
                "The tree that held 12 files in October "
                "2025 just contained 9,999 files, and on "
                "2026-10-27 it was rechecked.",
                "The tree that held 12 files in October "
                "2025 soon contained 9,999 files, and on "
                "2026-10-27 it was rechecked.",
                "The tree that held 12 files in October "
                "2025 later contained 9,999 files, and "
                "on 2026-10-27 it was rechecked.",
                "The tree that held 12 files in October "
                "2025 finally contained 9,999 files, and "
                "on 2026-10-27 it was rechecked.",
                "The tree that held 12 files in October "
                "2025 subsequently contained 9,999 files, "
                "and on 2026-10-27 it was rechecked.",
                "The tree that held 12 files in October "
                "2025 reportedly contained 9,999 files, "
                "and on 2026-10-27 it was rechecked.",
                "The tree that held 12 files in October "
                "2025 still then contained 9,999 files, "
                "and on 2026-10-27 it was rechecked.",
            )
            for shape in shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertTrue(problems, shape)
            figure_doc = " ".join(
                self.mod.figure_problems.__doc__.split())
            self.assertIn(
                "one adverb or two of them standing "
                "together", figure_doc)

    def test_the_finisher_carryover_anchor_subject_and_proportion_shapes_fail_by_name(self):
        # Three lane 11 Minors standing past the lane
        # 11 repairs on neighbouring enumerations. The
        # carryover tally sets in both carryovers named
        # no totalled or totaled word and no amounted
        # to pair, so a count or a scan carried by one
        # of those markers escaped. The scan anchor set
        # named no listing, register, catalogue or
        # catalog word, so a scan result anchored by
        # one of them escaped. The named subject set
        # named no screencapture or playback, so a size
        # stated for one of them escaped. And the
        # proportion reading held no decimal stated
        # against the size of a unit and no per
        # thousand form, so both shapes crossed it.
        # Each enumeration now holds the priced words,
        # restated in the docstring and in the comments
        # that enumerate the sets in the same words.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            shapes = (
                "The repository was counted. The run "
                "totalled 9,999 for the whole tree today.",
                "The repository was counted. The run "
                "totaled 9,999 for the whole tree today.",
                "The repository was counted. The run "
                "amounted to 9,999 for the whole tree "
                "today.",
                "The credential scan was run. The run "
                "totalled 999 before the morning review "
                "meeting.",
                "The listing returned 999 results.",
                "The register returned 999 results.",
                "The catalogue returned 999 results.",
                "The catalog returned 999 results.",
                "The screencapture weighs in at 999,999 "
                "bytes.",
                "The playback weighs in at 999,999 bytes.",
                "The largest file is 0.5 the size of a "
                "MiB.",
                "The largest file is 500 per thousand of "
                "a MiB.",
            )
            for shape in shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertTrue(problems, shape)
            figure_doc = " ".join(
                self.mod.figure_problems.__doc__.split())
            for phrase in (
                "and by the listing, register, catalogue "
                "or catalog words in the same way",
                "the showreel, the screencapture or the "
                "playback",
                "or as pct, per mille or per thousand",
                "a decimal stated against the size of a "
                "unit counting in the same way",
            ):
                with self.subTest(phrase=phrase):
                    self.assertIn(phrase, figure_doc)

    def test_the_lane8_digit_fraction_denominators_stop_at_tenths(self):
        # The lane 7 spec Minor on the fraction root and
        # the lane 7 standards instance on the same
        # sentence. The declared boundary, fraction
        # denominators past tenths state no fraction the
        # gate reads, now holds for the digit forms as it
        # already held for the spelled ones, so a digit
        # fraction inside the boundary is refused and one
        # past it passes unjudged in both forms.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            fail_shapes = (
                "The largest file is 3/4 of a MiB.",
                "The largest file is 7/10 of a MiB.",
                "The largest file is 1/10 of a MiB.",
            )
            for shape in fail_shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertTrue(problems, shape)
            pass_shapes = (
                "The largest file is 3/12 of a MiB.",
                "The largest file is 7/20 of a MiB.",
                "The largest file is 3/11 of a MiB.",
                "The largest file is 1/100 of a MiB.",
                "The largest file is a twelfth of a MiB.",
            )
            for shape in pass_shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertEqual(problems, [], shape)

    def test_the_lane8_restated_passages_match_the_reading(self):
        # The lane 7 standards Minor on its four passages.
        # The named subject units are the abbreviated
        # factors the code holds, so a spelled factor unit
        # states no size the reading takes while the
        # abbreviated form is refused. The scan carryover
        # comment now names the came back pair its code
        # reads. And the count carryover now consumes the
        # long bare tally shapes the lane 7 commit body
        # claimed for it, all told, found and came back
        # beside the figure and came to forms it already
        # held, so the claim the body made stands true in
        # the code from this lane on.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            fail_shapes = (
                "The repository was counted. All told, the "
                "run recorded 9,999 for the whole set here "
                "today now.",
                "The repository was counted. The run found "
                "9,999 for the whole set here today now.",
                "The repository was counted. The run came "
                "back with 9,999 for the whole set here "
                "today now.",
                "The demo recording weighs 600 KiB.",
            )
            for shape in fail_shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertTrue(problems, shape)
            pass_shapes = (
                "The demo recording weighs 1 kibibytes.",
                "The demo recording weighs 1 kilobytes.",
                "The demo recording weighs 1 mebibytes.",
                "The demo recording weighs 1 megabytes.",
                "The demo recording weighs 1 gibibytes.",
            )
            for shape in pass_shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertEqual(problems, [], shape)
            figure_doc = " ".join(
                self.mod.figure_problems.__doc__.split())
            self.assertIn(
                "the abbreviated factors kib, kb, mib, mb "
                "or gib in any case", figure_doc)
            self.assertNotIn("kibibytes", figure_doc)

    def test_the_lane8_next_shapes_fail_by_name(self):
        # The lane 7 red team Minors on their next shapes.
        # A dated intervening sentence that states no value
        # does not discharge the carry, the tally markers
        # in their next words and the scan anchors in their
        # next names carry falsified figures, the priced
        # subjects assert their sizes under the capture
        # record its own other names and the plain file
        # under its role name, and the percent and decimal
        # of forms state falsified sizes inside anchored
        # sentences.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            shapes = (
                "The credential scan has its results. The "
                "2026 run is complete. The total came to "
                "999.",
                "The credential scan has its results. The "
                "recorded tally for the whole run across "
                "the tree was 999.",
                "The credential scan has its results. "
                "Altogether the run recorded 999 across the "
                "whole tree.",
                "The credential scan has its results. The "
                "bottom line for the whole run across the "
                "tree was 999.",
                "The screening returned 999 results.",
                "The inspection returned 999 outcomes.",
                "The review returned 999 results.",
                "The search returned 999 results.",
                "The pattern match returned 999 results.",
                "The capture weighs in at 999,999 bytes.",
                "The video weighs in at 999,999 bytes.",
                "The walkthrough weighs in at 999,999 "
                "bytes.",
                "The screencast weighs in at 999,999 bytes.",
                "The animation weighs in at 999,999 bytes.",
                "The movie weighs in at 999,999 bytes.",
                "The instructions file runs to 1 bytes.",
                "The largest file comes to 50% of a MiB.",
                "The largest file is 58 percent of a MiB.",
                "The demo recording is 0.5 of a MiB in "
                "size.",
                "The largest file is 0.5 of a MiB.",
            )
            for shape in shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertTrue(problems, shape)

    def test_true_lane6_bound_cap_and_dated_forms_pass(self):
        # The other limb of the lane 5 false failure Minor.
        # The verb form caps, the postfix bound, the year
        # dated history and a true largest range are true of
        # the measured layout and pass, beside a genuinely
        # historical full date carrying a figure the gate
        # cannot measure.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            measured = self.mod.tree_measurements(root)
            pack = root / CLAUDE_PACK
            base = pack.read_text(encoding="utf-8")
            true_shapes = (
                "The checklist caps the tree at 512 files.",
                "The tree is limited to 512 files.",
                "The tree holds 512 files at most under the "
                "checklist cap.",
                "In 2025 the repo held 12 files.",
                "The 2025 tree held 12 files.",
                "The repo held 12 files in 2025.",
                "On 2025-01-01 the tree contained 9,999 "
                "files.",
                "The largest file is between 600,000 and "
                "610,000 bytes.",
                "The repo is capped at 512 files.",
            )
            for shape in true_shapes:
                with self.subTest(shape=shape):
                    pack.write_text(
                        base + "\n" + shape + "\n",
                        encoding="utf-8")
                    problems = []
                    self.mod.figure_problems(root, problems)
                    self.assertEqual(problems, [], shape)

    def test_a_deleted_credential_scan_sentence_fails_as_unverifiable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            pack = root / CLAUDE_PACK
            text = pack.read_text(encoding="utf-8")
            text = re.sub(
                r"A credential pattern scan.*?returned zero "
                r"hits, ", "A credential check was run and "
                "looked fine. ", text)
            self.assertNotIn("credential pattern scan", text)
            pack.write_text(text, encoding="utf-8")
            problems = []
            self.mod.figure_problems(root, problems)
            self.assertTrue(
                any("credential scan" in p
                    and "unverifiable" in p for p in problems),
                problems)

    def test_a_planted_pgp_header_counts_as_a_scan_hit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.figure_layout(tmp)
            (root / "planted.txt").write_text(
                "-----BEGIN PGP PRIVATE " + "KEY BLOCK-----\n"
                "planted body\n"
                "-----END PGP PRIVATE " + "KEY BLOCK-----\n",
                encoding="utf-8")
            problems = []
            self.mod.figure_problems(root, problems)
            self.assertTrue(
                any("scan over this tree returns 1" in p
                    for p in problems), problems)

    def test_a_dropped_mod_entry_fails(self):
        def change(d):
            d["plugins"] = [
                e for e in d["plugins"]
                if e["name"] != "recognitio-mod"]
        problems = self.mutate_json(CLAUDE_MARKET, change)
        self.assertTrue(
            any("exactly two" in p for p in problems), problems)

    def test_a_renamed_mod_entry_fails(self):
        def change(d):
            for entry in d["plugins"]:
                if entry["name"] == "recognitio-mod":
                    entry["name"] = "spawn-gate"
        problems = self.mutate_json(CLAUDE_MARKET, change)
        self.assertTrue(
            any("recognitio-mod" in p for p in problems), problems)

    def test_a_drifted_mod_entry_source_fails(self):
        def change(d):
            for entry in d["plugins"]:
                if entry["name"] == "recognitio-mod":
                    entry["source"] = "./plugins/other"
        problems = self.mutate_json(CLAUDE_MARKET, change)
        self.assertTrue(any(
            "recognitio-mod" in p and "source" in p
            for p in problems), problems)

    def test_a_non_strict_mod_entry_fails(self):
        def change(d):
            for entry in d["plugins"]:
                if entry["name"] == "recognitio-mod":
                    entry["strict"] = False
        problems = self.mutate_json(CLAUDE_MARKET, change)
        self.assertTrue(any(
            "recognitio-mod" in p and "strict" in p
            for p in problems), problems)

    def test_the_scratch_layout_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            self.assertEqual(self.problems(root), [])

    def test_a_missing_pack_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            (root / CURSOR_PACK).unlink()
            problems = self.problems(root)
            self.assertTrue(
                any("missing" in p for p in problems), problems)

    def test_a_dropped_unsubmitted_sentence_fails(self):
        problems = self.mutate_text(
            CURSOR_PACK,
            lambda t: t.replace(
                "Nothing in this pack has been submitted.", ""))
        self.assertTrue(
            any("has been submitted" in p for p in problems),
            problems)

    def test_a_dropped_read_date_fails(self):
        problems = self.mutate_text(
            CLAUDE_PACK,
            lambda t: t.replace("on 2026-10-27.", "recently."))
        self.assertTrue(
            any("2026-10-27" in p for p in problems), problems)

    def test_a_dropped_route_fails(self):
        problems = self.mutate_text(
            CLAUDE_PACK,
            lambda t: t.replace(
                "claude.ai/directory/manage", "the portal"))
        self.assertTrue(
            any("directory/manage" in p for p in problems),
            problems)

    def test_a_dropped_owner_act_section_fails(self):
        problems = self.mutate_text(
            PORTABLE_PACK,
            lambda t: t.replace(
                "## What remains David's act",
                "## What remains"))
        self.assertTrue(
            any("David's act" in p for p in problems), problems)

    def test_a_dropped_no_directory_sentence_fails(self):
        problems = self.mutate_text(
            PORTABLE_PACK,
            lambda t: t.replace(
                "The Agent Plugins project runs no directory "
                "of packages.",
                "The project directory question is open."))
        self.assertTrue(
            any("no directory" in p for p in problems), problems)

    def test_a_filed_listing_claim_fails(self):
        problems = self.mutate_text(
            CURSOR_PACK,
            lambda t: t + "\nThe listing is live.\n")
        self.assertTrue(
            any("listing is live" in p for p in problems),
            problems)

    def test_a_version_bump_the_packs_do_not_follow_fails(self):
        def change(d):
            d["version"] = "1.4.0"
        problems = self.mutate_json(CLAUDE_PLUGIN, change)
        self.assertTrue(
            any("1.4.0" in p for p in problems), problems)

    def test_a_cursor_owner_loss_fails(self):
        def change(d):
            d.pop("owner")
        problems = self.mutate_json(CURSOR_MARKET, change)
        self.assertTrue(
            any("owner" in p for p in problems), problems)

    def test_a_second_cursor_entry_fails(self):
        def change(d):
            extra = dict(d["plugins"][0])
            extra["name"] = "recognitio-copy"
            d["plugins"] = d["plugins"] + [extra]
        problems = self.mutate_json(CURSOR_MARKET, change)
        self.assertTrue(
            any("exactly one" in p for p in problems), problems)

    def test_a_cursor_entry_source_drift_fails(self):
        # Burn-down repair. The submissions gate once read
        # only the entry count and name, so an entry source
        # drifted off the plugin root passed it while the
        # Cursor gate failed the same plant. The entry
        # paths the pack states must fail here by name too.
        def change(d):
            d["plugins"][0]["source"] = "./.cursor-plugin"
        problems = self.mutate_json(CURSOR_MARKET, change)
        self.assertTrue(
            any("source" in p for p in problems), problems)

    def test_a_cursor_entry_skills_drift_fails(self):
        # Burn-down repair. The old entry skills value,
        # written from the manifest folder, resolves
        # nowhere under the entry source at the root, and
        # the submissions gate never opened it.
        def change(d):
            d["plugins"][0]["skills"] = ["./skills/recognitio/"]
        problems = self.mutate_json(CURSOR_MARKET, change)
        self.assertTrue(
            any("skills" in p for p in problems), problems)

    def test_a_cursor_entry_logo_drift_fails(self):
        # Burn-down repair. An entry logo drifted from the
        # manifest value passed the submissions gate for
        # the same reason, so it fails here by name now.
        def change(d):
            d["plugins"][0]["logo"] = "docs/brand/other.svg"
        problems = self.mutate_json(CURSOR_MARKET, change)
        self.assertTrue(
            any("logo" in p for p in problems), problems)

    def test_a_claude_author_loss_fails(self):
        def change(d):
            d.pop("author")
        problems = self.mutate_json(CLAUDE_PLUGIN, change)
        self.assertTrue(
            any("author" in p for p in problems), problems)

    def test_a_claude_entry_name_drift_fails(self):
        def change(d):
            d["plugins"][0]["name"] = "recognitio-copy"
        problems = self.mutate_json(CLAUDE_MARKET, change)
        self.assertTrue(
            any("does not match" in p for p in problems),
            problems)

    def test_a_license_file_loss_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            (root / "LICENSE").unlink()
            problems = self.problems(root)
            self.assertTrue(
                any("LICENSE" in p for p in problems), problems)

    def test_an_eleventh_portable_field_fails(self):
        def change(d):
            d["displayName"] = "Recognitio"
        problems = self.mutate_json(PORTABLE, change)
        self.assertTrue(
            any("closed" in p for p in problems), problems)

    def test_an_uppercase_portable_keyword_fails(self):
        def change(d):
            d["keywords"] = ["Review-Packet"]
        problems = self.mutate_json(PORTABLE, change)
        self.assertTrue(
            any("keyword" in p for p in problems), problems)

    def test_a_portable_name_outside_the_pattern_fails(self):
        # The value isolates the pattern guard. It carries no
        # doubled hyphen and no other defect, so only the
        # pattern reading can refuse it.
        def change(d):
            d["name"] = "Recognitio"
        problems = self.mutate_json(PORTABLE, change)
        self.assertTrue(
            any("pattern" in p for p in problems), problems)

    def test_a_capitalised_filed_claim_fails(self):
        problems = self.mutate_text(
            CURSOR_PACK, lambda t: t + "\nListing is live now.\n")
        self.assertTrue(
            any("listing is live" in p for p in problems),
            problems)

    def test_a_submitted_claim_beside_the_honest_sentence_fails(self):
        problems = self.mutate_text(
            CLAUDE_PACK,
            lambda t: t + "\nThe pack has been submitted.\n")
        self.assertTrue(
            any("pack has been submitted" in p for p in problems),
            problems)

    def test_a_listed_in_claim_fails(self):
        problems = self.mutate_text(
            CURSOR_PACK,
            lambda t: t
            + "\nRecognitio is listed in the marketplace.\n")
        self.assertTrue(
            any("is listed in" in p for p in problems), problems)

    def test_a_we_filed_claim_fails(self):
        problems = self.mutate_text(
            PORTABLE_PACK,
            lambda t: t + "\nWe filed the submission yesterday.\n")
        self.assertTrue(
            any("we filed" in p for p in problems), problems)

    def test_a_promised_timeline_fails(self):
        problems = self.mutate_text(
            CURSOR_PACK,
            lambda t: t + "\nCursor reviews every submission "
            "within 2 business days.\n")
        self.assertTrue(
            any("timeline" in p for p in problems), problems)

    def test_a_spelled_out_timeline_fails(self):
        problems = self.mutate_text(
            CURSOR_PACK,
            lambda t: t + "\nCursor reviews every submission "
            "within two business days.\n")
        self.assertTrue(
            any("timeline" in p for p in problems), problems)

    def test_a_cursor_figure_drift_fails(self):
        problems = self.mutate_text(
            CURSOR_PACK,
            lambda t: t.replace("10 MB", "10 GB"))
        self.assertTrue(
            any("10 MB" in p for p in problems), problems)

    def test_a_claude_figure_drift_fails(self):
        problems = self.mutate_text(
            CLAUDE_PACK,
            lambda t: t.replace(
                "at least 40 words", "at least 4 words"))
        self.assertTrue(
            any("40 words" in p for p in problems), problems)

    def test_a_claude_count_drift_fails(self):
        problems = self.mutate_text(
            CLAUDE_PACK,
            lambda t: t.replace(
                "holds 254 files", "holds 236 files"))
        self.assertTrue(
            any("254 files" in p for p in problems), problems)

    def test_the_pack_figures_match_the_measured_tree(self):
        # SC3. The Claude pack states its tree figures in the
        # present tense, and they went stale three times while
        # every pin held, because no check measured them
        # against the tree. This test measures the tracked
        # tree and holds every stated figure against the
        # measurement, so a file added or removed, or the
        # largest files growing, fails here until the pack is
        # restated.
        import re
        import subprocess

        listed = subprocess.check_output(
            ["git", "ls-files"], cwd=ROOT, text=True,
            env=scrubbed_git_env(),
        ).splitlines()
        sizes = []
        for rel in listed:
            path = ROOT / rel
            size = (
                path.lstat().st_size if path.is_symlink()
                else path.stat().st_size
            )
            sizes.append((size, rel))
        sizes.sort(reverse=True)
        image_or_font = {
            ".gif", ".png", ".svg", ".jpg", ".jpeg", ".webp",
            ".ico", ".ttf", ".otf", ".woff", ".woff2",
        }
        largest = sizes[0]
        largest_plain = next(
            entry for entry in sizes
            if Path(entry[1]).suffix.lower() not in image_or_font
        )
        text = re.sub(
            r"\s+", " ",
            (ROOT / CLAUDE_PACK).read_text(encoding="utf-8"),
        )

        def stated(pattern):
            match = re.search(pattern, text)
            self.assertIsNotNone(match, pattern)
            return match.group(1)

        self.assertEqual(
            int(stated(r"holds (\d+) files")), len(listed))
        self.assertEqual(
            int(stated(r"held (\d+) files")), len(listed))
        self.assertEqual(
            int(stated(r"at (\d+) files against a cap")),
            len(listed))
        self.assertEqual(
            stated(r"demo recording at ([\d,]+) bytes"),
            format(largest[0], ","))
        self.assertTrue(
            largest[1].endswith("demo.gif")
            or "demo" in largest[1], largest)
        self.assertEqual(
            stated(
                r"scripts/check_mod\.py at ([\d,]+) bytes"),
            format(largest_plain[0], ","))
        self.assertEqual(largest_plain[1],
                         "scripts/check_mod.py")
        self.assertEqual(
            int(stated(r"scan over all (\d+) files in the tree")),
            len(listed))

    def test_a_portable_figure_drift_fails(self):
        problems = self.mutate_text(
            PORTABLE_PACK,
            lambda t: t.replace("six month", "six week"))
        self.assertTrue(
            any("six month" in p for p in problems), problems)

    def test_an_invented_registry_fails(self):
        problems = self.mutate_text(
            PORTABLE_PACK,
            lambda t: t + "\nThe project also runs a package "
            "registry of its own.\n")
        self.assertTrue(
            any("registry" in p for p in problems), problems)

    def test_a_name_availability_claim_fails(self):
        problems = self.mutate_text(
            CLAUDE_PACK,
            lambda t: t + "\nThe name recognitio is available "
            "in the directory.\n")
        self.assertTrue(
            any("available in the directory" in p
                for p in problems),
            problems)

    def test_a_claude_skills_path_drift_fails(self):
        def change(d):
            d["skills"] = ["./nonexistent/"]
        problems = self.mutate_json(CLAUDE_PLUGIN, change)
        self.assertTrue(
            any("skills path" in p for p in problems), problems)

    def test_a_claude_display_name_loss_fails(self):
        def change(d):
            d.pop("displayName")
        problems = self.mutate_json(CLAUDE_PLUGIN, change)
        self.assertTrue(
            any("displayName" in p for p in problems), problems)

    def test_a_claude_version_loss_fails(self):
        def change(d):
            d.pop("version")
        problems = self.mutate_json(CLAUDE_PLUGIN, change)
        self.assertTrue(
            any("no version" in p for p in problems), problems)

    def test_a_claude_strict_off_entry_fails(self):
        def change(d):
            d["plugins"][0]["strict"] = False
        problems = self.mutate_json(CLAUDE_MARKET, change)
        self.assertTrue(
            any("strict" in p for p in problems), problems)

    def test_a_claude_entry_source_drift_fails(self):
        def change(d):
            d["plugins"][0]["source"] = "./elsewhere"
        problems = self.mutate_json(CLAUDE_MARKET, change)
        self.assertTrue(
            any("source" in p for p in problems), problems)

    def test_a_portable_license_drift_fails(self):
        def change(d):
            d["license"] = "Apache-2.0"
        problems = self.mutate_json(PORTABLE, change)
        self.assertTrue(
            any("license" in p for p in problems), problems)

    def test_a_portable_repository_drift_fails(self):
        def change(d):
            d["repository"] = (
                "https://github.com/someone-else/other")
        problems = self.mutate_json(PORTABLE, change)
        self.assertTrue(
            any("repository" in p for p in problems), problems)

    def test_a_portable_keyword_content_drift_fails(self):
        def change(d):
            d["keywords"] = ["zzz", "yyy"]
        problems = self.mutate_json(PORTABLE, change)
        self.assertTrue(
            any("keywords" in p for p in problems), problems)

    def test_a_portable_schema_drift_fails(self):
        def change(d):
            d["$schema"] = "https://example.com/schema.json"
        problems = self.mutate_json(PORTABLE, change)
        self.assertTrue(
            any("$schema" in p for p in problems), problems)

    def test_a_portable_author_loss_fails(self):
        def change(d):
            d.pop("author")
        problems = self.mutate_json(PORTABLE, change)
        self.assertTrue(
            any("author" in p for p in problems), problems)

    def test_a_portable_non_semver_version_fails(self):
        def change(d):
            d["version"] = "1.3"
        problems = self.mutate_json(PORTABLE, change)
        self.assertTrue(
            any("semantic version" in p for p in problems),
            problems)

    def test_an_absolute_cursor_logo_path_fails(self):
        def change(d):
            d["logo"] = "/docs/brand/recognitio-icon.svg"
        problems = self.mutate_json(CURSOR_PLUGIN, change)
        self.assertTrue(
            any("logo" in p for p in problems), problems)

    def test_a_parent_reference_icon_path_fails(self):
        def change(d):
            d["icon"] = "../../docs/brand/recognitio-icon-512.png"
        problems = self.mutate_json(CLAUDE_PLUGIN, change)
        self.assertTrue(
            any("icon" in p for p in problems), problems)

    def test_a_cursor_description_loss_fails(self):
        def change(d):
            d.pop("description")
        problems = self.mutate_json(CURSOR_PLUGIN, change)
        self.assertTrue(
            any("description" in p for p in problems), problems)

    def test_a_cursor_marketplace_name_loss_fails(self):
        def change(d):
            d.pop("name")
        problems = self.mutate_json(CURSOR_MARKET, change)
        self.assertTrue(
            any("no name" in p for p in problems), problems)

    def test_a_loose_json_constant_fails(self):
        problems = self.mutate_raw(
            CURSOR_PLUGIN, '{"name": "recognitio", "x": NaN}')
        self.assertTrue(
            any("does not parse" in p for p in problems),
            problems)

    def test_a_repeated_key_fails(self):
        problems = self.mutate_raw(
            CURSOR_MARKET,
            '{"name": "a", "name": "b", "plugins": []}')
        self.assertTrue(
            any("does not parse" in p for p in problems),
            problems)

    def test_a_non_object_manifest_fails(self):
        problems = self.mutate_raw(PORTABLE, "[]")
        self.assertTrue(
            any("not an object" in p for p in problems),
            problems)

    def test_a_missing_portable_skill_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            (root / "agent-plugins-package" / "skills"
             / "recognitio" / "SKILL.md").unlink()
            problems = self.problems(root)
            self.assertTrue(
                any("fixed location" in p for p in problems),
                problems)


class TestPackPinWidth(unittest.TestCase):
    """The packs state the pin width the gate actually holds.

    Each pack once stated that the gate pins the facts the
    check rests on, so drift in a manifest or in the pack
    fails the gate, while the gate holds no file counting
    reading and the pack figures outside its pin list drift
    under a green gate. Restoring the unqualified sentence
    in any pack, or dropping the scoped sentence from one,
    fails here.
    """

    PACKS = (
        "docs/submission-claude.md",
        "docs/submission-cursor.md",
        "docs/submission-agent-plugins.md",
    )

    def test_each_pack_states_the_scoped_pin_width(self):
        for rel in self.PACKS:
            with self.subTest(pack=rel):
                flat = " ".join(
                    (ROOT / rel).read_text(encoding="utf-8").split()
                )
                self.assertNotIn(
                    "pins the facts the check rests on", flat
                )
                self.assertIn(
                    "pins the manifest facts the check rests on "
                    "and the few figures in this pack its pin "
                    "list names",
                    flat,
                )
                self.assertIn(
                    "The remaining figures in this pack stand "
                    "as measurements taken on the date this "
                    "pack states, and no gate recounts them.",
                    flat,
                )


if __name__ == "__main__":
    unittest.main()
