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
                "holds 239 files", "holds 236 files"))
        self.assertTrue(
            any("239 files" in p for p in problems), problems)

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
                r"tests/test_gate_scripts\.py at ([\d,]+) bytes"),
            format(largest_plain[0], ","))
        self.assertEqual(largest_plain[1],
                         "tests/test_gate_scripts.py")
        self.assertEqual(
            int(stated(r"scan over all (\d+) tracked files")),
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
