import importlib.util
import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    path = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location("gate_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(repo, *args):
    result = subprocess.run(
        ["git", "-C", str(repo)] + list(args),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError("git %s failed: %s" % (" ".join(args), result.stderr))
    return result.stdout.strip()


EM_DASH = "\u2014"


class TestCheckCopy(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_copy")

    def write_tmp(self, tmp, name, text):
        path = Path(tmp) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def run_main_on(self, files, comment_files=()):
        original = self.mod.PROSE_FILES
        original_comments = self.mod.COMMENT_FILES
        self.mod.PROSE_FILES = files
        self.mod.COMMENT_FILES = list(comment_files)
        try:
            with redirect_stderr(io.StringIO()):
                return self.mod.main()
        finally:
            self.mod.PROSE_FILES = original
            self.mod.COMMENT_FILES = original_comments

    def test_every_public_prose_surface_is_scanned(self):
        names = {str(path.relative_to(ROOT)) for path in self.mod.PROSE_FILES}
        for expected in (
            "README.md",
            "REVIEW.md",
            "AGENTS.md",
            "CHANGELOG.md",
            "CLAUDE.md",
            "docs/decisions.md",
            "skills/recognitio/SKILL.md",
            ".github/pull_request_template.md",
            ".github/ISSUE_TEMPLATE/bug_report.md",
            ".github/ISSUE_TEMPLATE/feature_request.md",
            ".github/ISSUE_TEMPLATE/config.yml",
            ".coderabbit.yaml",
        ):
            self.assertIn(expected, names)
        comment_names = {
            str(path.relative_to(ROOT)) for path in self.mod.COMMENT_FILES
        }
        for expected in (
            ".github/workflows/ci.yml",
            ".github/dependabot.yml",
            "Makefile",
            ".gitignore",
        ):
            self.assertIn(expected, comment_names)

    def test_em_dash_in_issue_template_config_is_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yml",
                "blank_issues_enabled: true\n"
                "contact_links:\n"
                "  - name: Readme\n"
                "    url: https://example.com/readme\n"
                "    about: What the skill does %s in plain words.\n"
                % EM_DASH,
            )
            self.assertEqual(self.run_main_on([path]), 1)

    def test_em_dash_in_a_workflow_comment_is_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "ci.yml",
                "name: ci\n"
                "\n"
                "# The gate runs first %s always.\n"
                "jobs:\n"
                "  check:\n"
                "    steps:\n"
                "      - run: |\n"
                "          echo one; echo two\n" % EM_DASH,
            )
            self.assertEqual(self.run_main_on([], [path]), 1)

    def test_shell_code_in_a_run_block_is_not_prose(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "ci.yml",
                "name: ci\n"
                "\n"
                "# The gate runs first.\n"
                "jobs:\n"
                "  check:\n"
                "    steps:\n"
                "      - run: |\n"
                "          echo \"needs: this; that\"; exit 1\n",
            )
            self.assertEqual(self.run_main_on([], [path]), 0)

    def test_em_dash_in_a_makefile_comment_is_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "Makefile",
                "# The gate for this repo %s run it first.\n"
                "\n"
                "PYTHON ?= python3\n"
                "\n"
                "check:\n"
                "\tpython3 -m unittest discover -s tests\n" % EM_DASH,
            )
            self.assertEqual(self.run_main_on([], [path]), 1)

    def test_em_dash_in_a_gitignore_comment_is_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, ".gitignore",
                "# Extractor output %s working papers.\n"
                "packet/\n" % EM_DASH,
            )
            self.assertEqual(self.run_main_on([], [path]), 1)

    def test_em_dash_in_a_dependabot_comment_is_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "dependabot.yml",
                "# Keep the pinned actions current %s weekly.\n"
                "version: 2\n"
                "updates:\n"
                "  - package-ecosystem: \"github-actions\"\n" % EM_DASH,
            )
            self.assertEqual(self.run_main_on([], [path]), 1)

    def test_em_dash_beside_a_url_is_still_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "page.md",
                "See https://example.com/spec for the plan %s truly.\n"
                % EM_DASH,
            )
            self.assertEqual(self.run_main_on([path]), 1)

    def test_semicolon_right_after_a_markdown_link_is_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "page.md",
                "See [guide](https://example.com/spec); then continue.\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)

    def test_colon_right_after_a_markdown_link_is_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "page.md",
                "See [guide](https://example.com/spec): then continue.\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)

    def test_a_markdown_link_with_clean_prose_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "page.md",
                "See [guide](https://example.com/spec) before continuing.\n",
            )
            self.assertEqual(self.run_main_on([path]), 0)

    def test_a_bare_url_line_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "page.md",
                "The plan lives at https://example.com/spec today.\n",
            )
            self.assertEqual(self.run_main_on([path]), 0)

    def test_em_dash_in_a_template_shaped_file_is_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "CLAUDE.md",
                "All guidance lives elsewhere %s read it first.\n" % EM_DASH,
            )
            self.assertEqual(self.run_main_on([path]), 1)

    def test_yaml_block_scalar_prose_is_scanned(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "reviews:\n  instructions: |\n"
                "    Be direct %s always.\n" % EM_DASH,
            )
            self.assertEqual(self.run_main_on([path]), 1)

    def test_fence_covers_every_authored_prose_file_in_the_tree(self):
        covered = {str(p.relative_to(ROOT)) for p in self.mod.PROSE_FILES}
        authored = set()
        authored_yaml = set()
        # The walk shares the one exclusion predicate the discovery
        # function uses, so a file under a hidden directory or a
        # node_modules directory is outside both or inside both and
        # the two rules can never contradict each other again.
        for pattern in ("*.md", "*.yml", "*.yaml"):
            for path in ROOT.rglob(pattern):
                if self.mod.is_fence_excluded(ROOT, path):
                    continue
                if path.suffix in (".yml", ".yaml") \
                        and self.mod.is_comment_span_file(ROOT, path):
                    continue
                rel = str(path.relative_to(ROOT))
                authored.add(rel)
                if path.suffix in (".yml", ".yaml"):
                    authored_yaml.add(rel)
        self.assertTrue(authored)
        self.assertTrue(authored_yaml)
        self.assertEqual(authored - covered, set())
        comment_covered = {
            str(p.relative_to(ROOT)) for p in self.mod.COMMENT_FILES
        }
        for pattern in ("*.yml", "*.yaml"):
            for path in ROOT.rglob(pattern):
                if self.mod.is_fence_excluded(ROOT, path):
                    continue
                if self.mod.is_comment_span_file(ROOT, path):
                    self.assertIn(
                        str(path.relative_to(ROOT)), comment_covered
                    )
        manifests = {
            str(p.relative_to(ROOT)) for p in self.mod.MANIFEST_FILES
        }
        self.assertEqual(
            manifests,
            {".claude-plugin/plugin.json",
             ".claude-plugin/marketplace.json"},
        )

    def test_discovery_extends_to_a_new_markdown_file_by_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            note = root / "docs" / "new-note.md"
            note.write_text("A new note.\n", encoding="utf-8")
            tasks = root / "evals" / "tasks" / "task-99"
            tasks.mkdir(parents=True)
            (tasks / "packet.md").write_text(
                "Generated output.\n", encoding="utf-8"
            )
            (tasks / "planted.md").write_text(
                "Authored grading notes.\n", encoding="utf-8"
            )
            found = {
                str(p.relative_to(root))
                for p in self.mod.discover_prose_files(root)
            }
            self.assertIn("docs/new-note.md", found)
            self.assertIn("evals/tasks/task-99/planted.md", found)
            self.assertNotIn("evals/tasks/task-99/packet.md", found)

    def test_discovery_skips_dependency_dirs_and_outside_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "note.md").write_text(
                "A note.\n", encoding="utf-8"
            )
            venv = root / ".venv" / "lib"
            venv.mkdir(parents=True)
            (venv / "README.md").write_text(
                "Third party docs.\n", encoding="utf-8"
            )
            modules = root / "node_modules" / "pkg"
            modules.mkdir(parents=True)
            (modules / "README.md").write_text(
                "Third party docs.\n", encoding="utf-8"
            )
            outside = root.parent / "outside-the-tree.md"
            outside.write_text("Outside the tree.\n", encoding="utf-8")
            try:
                (root / "docs" / "linked.md").symlink_to(outside)
            except OSError:
                linked = False
            else:
                linked = True
            found = {
                str(p.relative_to(root))
                for p in self.mod.discover_prose_files(root)
            }
            self.assertIn("docs/note.md", found)
            self.assertNotIn(".venv/lib/README.md", found)
            self.assertNotIn("node_modules/pkg/README.md", found)
            if linked:
                self.assertNotIn("docs/linked.md", found)

    def test_discovery_extends_to_new_yaml_files_by_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            form = root / ".github" / "ISSUE_TEMPLATE" / "feature_form.yml"
            form.parent.mkdir(parents=True)
            form.write_text("name: Feature\n", encoding="utf-8")
            settings = root / "docs" / "settings.yml"
            settings.parent.mkdir(parents=True)
            settings.write_text("title: Settings\n", encoding="utf-8")
            notes = root / "notes.yaml"
            notes.write_text("title: Notes\n", encoding="utf-8")
            workflow = root / ".github" / "workflows" / "ci.yml"
            workflow.parent.mkdir(parents=True)
            workflow.write_text("name: ci\n", encoding="utf-8")
            dependabot = root / ".github" / "dependabot.yml"
            dependabot.write_text("version: 2\n", encoding="utf-8")
            hidden = root / ".notes" / "secret.yml"
            hidden.parent.mkdir(parents=True)
            hidden.write_text("title: Secret\n", encoding="utf-8")
            modules = root / "node_modules" / "pkg" / "conf.yml"
            modules.parent.mkdir(parents=True)
            modules.write_text("title: Package\n", encoding="utf-8")
            found = {
                str(p.relative_to(root))
                for p in self.mod.discover_prose_files(root)
            }
            self.assertIn(".github/ISSUE_TEMPLATE/feature_form.yml", found)
            self.assertIn("docs/settings.yml", found)
            self.assertIn("notes.yaml", found)
            self.assertNotIn(".github/workflows/ci.yml", found)
            self.assertNotIn(".github/dependabot.yml", found)
            self.assertNotIn(".notes/secret.yml", found)
            self.assertNotIn("node_modules/pkg/conf.yml", found)
            comments = {
                str(p.relative_to(root))
                for p in self.mod.discover_comment_files(root)
            }
            self.assertIn(".github/workflows/ci.yml", comments)
            self.assertIn(".github/dependabot.yml", comments)

    def test_a_new_yaml_issue_form_joins_the_fence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            form = root / ".github" / "ISSUE_TEMPLATE" / "feature_form.yml"
            form.parent.mkdir(parents=True)
            form.write_text(
                "name: Feature\n"
                "description: Ask for a thing %s in plain words.\n"
                % EM_DASH,
                encoding="utf-8",
            )
            found = self.mod.discover_prose_files(root)
            self.assertIn(form, found)
            self.assertEqual(self.run_main_on(found), 1)

    def test_the_walk_and_discovery_share_one_exclusion_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "note.md").write_text(
                "A note.\n", encoding="utf-8"
            )
            (root / "docs" / "settings.yml").write_text(
                "title: Settings\n", encoding="utf-8"
            )
            hidden = root / ".notes"
            hidden.mkdir()
            (hidden / "draft.md").write_text("A draft.\n", encoding="utf-8")
            (hidden / "secret.yml").write_text(
                "title: Secret\n", encoding="utf-8"
            )
            modules = root / "node_modules" / "pkg"
            modules.mkdir(parents=True)
            (modules / "README.md").write_text(
                "Package docs.\n", encoding="utf-8"
            )
            walked = set()
            for pattern in ("*.md", "*.yml", "*.yaml"):
                for path in root.rglob(pattern):
                    if self.mod.is_fence_excluded(root, path):
                        continue
                    if path.suffix in (".yml", ".yaml") \
                            and self.mod.is_comment_span_file(root, path):
                        continue
                    walked.add(str(path.relative_to(root)))
            discovered = {
                str(p.relative_to(root))
                for p in self.mod.discover_prose_files(root)
            }
            self.assertEqual(walked, discovered)
            self.assertEqual(
                walked, {"docs/note.md", "docs/settings.yml"}
            )

    def test_manifest_discovery_returns_missing_paths_for_the_caller(self):
        with tempfile.TemporaryDirectory() as tmp:
            found = self.mod.discover_manifest_files(Path(tmp))
            self.assertEqual(len(found), 2)
            self.assertTrue(all(not p.exists() for p in found))

    def test_em_dash_in_a_manifest_description_is_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "plugin.json",
                '{"name": "x", "description": "Does a thing %s '
                'in plain words."}\n' % EM_DASH,
            )
            original = (
                self.mod.PROSE_FILES, self.mod.COMMENT_FILES,
                self.mod.MANIFEST_FILES,
            )
            self.mod.PROSE_FILES = []
            self.mod.COMMENT_FILES = []
            self.mod.MANIFEST_FILES = [path]
            try:
                with redirect_stderr(io.StringIO()):
                    code = self.mod.main()
            finally:
                (
                    self.mod.PROSE_FILES, self.mod.COMMENT_FILES,
                    self.mod.MANIFEST_FILES,
                ) = original
            self.assertEqual(code, 1)

    def test_a_flow_mapping_value_is_structure_not_prose(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "point: {x: 1, y: 2}\n",
            )
            self.assertEqual(self.run_main_on([path]), 0)

    def test_a_nested_sequence_of_mappings_is_structure_not_prose(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "items:\n"
                "  - - name: alpha\n"
                "    - name: beta\n",
            )
            self.assertEqual(self.run_main_on([path]), 0)

    def test_a_colon_inside_a_flow_mapping_value_still_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "point: {label: \"Read: now\"}\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)

    def test_a_colon_inside_a_list_item_flow_mapping_still_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "items:\n"
                "  - {label: \"Read: now\"}\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)

    def test_a_prose_mapping_value_with_a_colon_still_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "note: see the guide for details: the long version\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)

    def test_a_prose_value_in_a_nested_sequence_still_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "items:\n"
                "  - - name: alpha: the first one\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)

    def test_yaml_keys_and_directives_are_syntax(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "# yaml-language-server: $schema=https://example.com/s.json\n"
                "language: \"en-US\"\n"
                "tone: \"Be direct and plain.\"\n",
            )
            self.assertEqual(self.run_main_on([path]), 0)


class TestEvalDocs(unittest.TestCase):
    def test_the_runner_note_describes_the_current_method(self):
        text = (ROOT / "evals" / "README.md").read_text(encoding="utf-8")
        self.assertIn("Run the three passes in a fixed order", text)
        self.assertIn("fair raw pass", text)
        self.assertIn("clean control", text)
        self.assertNotIn("Run the two passes", text)


class TestCheckSkill(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_skill")

    def test_folded_description_is_measured_whole(self):
        text = (
            "---\nname: recognitio\n"
            "description: first part\n  second part\n---\n"
        )
        fields = self.mod.parse_frontmatter(text)
        self.assertEqual(fields["description"], "first part second part")

    def test_over_limit_folded_description_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "recognitio"
            skill_dir.mkdir()
            long_half = "x" * 600
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                "---\nname: recognitio\ndescription: %s\n  %s\n---\n\n# X\n"
                % (long_half, long_half),
                encoding="utf-8",
            )
            original = (self.mod.SKILL_DIR, self.mod.SKILL_MD, self.mod.EXTRACT)
            self.mod.SKILL_DIR = skill_dir
            self.mod.SKILL_MD = skill_md
            self.mod.EXTRACT = ROOT / "skills" / "recognitio" / "scripts" / "extract.py"
            try:
                with redirect_stderr(io.StringIO()) as captured:
                    code = self.mod.main()
            finally:
                self.mod.SKILL_DIR, self.mod.SKILL_MD, self.mod.EXTRACT = original
            self.assertEqual(code, 1)
            self.assertIn("over the 1024 limit", captured.getvalue())

    def test_the_real_skill_package_is_valid(self):
        self.assertEqual(self.mod.main(), 0)

    def test_name_character_rules_accept_the_shipped_name(self):
        self.assertEqual(self.mod.name_problems("recognitio"), [])

    def test_name_character_rules_reject_each_break(self):
        for bad in (
            "Recognitio",
            "recog_nitio",
            "-recognitio",
            "recognitio-",
            "recog--nitio",
            "r" * 65,
        ):
            self.assertTrue(
                self.mod.name_problems(bad),
                "name %r must fail the character rules" % bad,
            )

    def test_a_name_with_consecutive_hyphens_fails_the_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "recognitio"
            skill_dir.mkdir()
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                "---\nname: recog--nitio\ndescription: a packet\n---\n\n# X\n",
                encoding="utf-8",
            )
            original = (self.mod.SKILL_DIR, self.mod.SKILL_MD, self.mod.EXTRACT)
            self.mod.SKILL_DIR = skill_dir
            self.mod.SKILL_MD = skill_md
            self.mod.EXTRACT = ROOT / "skills" / "recognitio" / "scripts" / "extract.py"
            try:
                with redirect_stderr(io.StringIO()) as captured:
                    code = self.mod.main()
            finally:
                self.mod.SKILL_DIR, self.mod.SKILL_MD, self.mod.EXTRACT = original
            self.assertEqual(code, 1)
            self.assertIn("consecutive hyphens", captured.getvalue())


class TestCheckVersion(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_version")

    def test_the_real_versions_agree(self):
        self.assertEqual(self.mod.main(), 0)

    def test_each_version_source_is_read(self):
        self.assertEqual(
            self.mod.extractor_version('EXTRACTOR_VERSION = "1.3.0"\n'),
            "1.3.0",
        )
        self.assertEqual(
            self.mod.changelog_version("## [Unreleased]\n\nThis work "
                                        "carries version 1.3.0.\n"),
            "1.3.0",
        )
        self.assertEqual(
            self.mod.changelog_version("## [2.0.0] - 2026-01-01\n"),
            "2.0.0",
        )
        self.assertEqual(
            self.mod.plugin_version('{"version": "1.3.0"}'), "1.3.0"
        )

    def test_disagreement_is_a_problem(self):
        problems = self.mod.coherence_problems({
            "plugin.json": "1.3.0",
            "EXTRACTOR_VERSION": "1.2.0",
            "CHANGELOG.md": "1.3.0",
        })
        self.assertTrue(any("disagree" in p for p in problems), problems)

    def test_a_missing_version_is_a_problem(self):
        problems = self.mod.coherence_problems({
            "plugin.json": None,
            "EXTRACTOR_VERSION": "1.3.0",
        })
        self.assertTrue(any("no version" in p for p in problems), problems)

    def test_a_missing_marketplace_version_is_recorded(self):
        found = self.mod.marketplace_versions(
            '{"metadata": {}, "plugins": [{"name": "x", "version": "1.3.0"}]}'
        )
        self.assertEqual(found, [None, "1.3.0"])
        problems = self.mod.coherence_problems({
            "marketplace.json entry 1": found[0],
            "EXTRACTOR_VERSION": "1.3.0",
        })
        self.assertTrue(any("no version" in p for p in problems), problems)

    def test_an_unreleased_declaration_wins_over_a_release(self):
        text = (
            "## [Unreleased]\n\nThis work carries version 1.4.0.\n\n"
            "## [1.3.0] - 2026-01-01\n"
        )
        self.assertEqual(self.mod.changelog_version(text), "1.4.0")

    def test_a_malformed_version_is_a_problem(self):
        problems = self.mod.coherence_problems({
            "plugin.json": "1.3",
            "EXTRACTOR_VERSION": "1.3",
        })
        self.assertTrue(
            any("not a version" in p for p in problems), problems
        )

    def test_wrong_typed_versions_are_problems_not_crashes(self):
        self.assertIsNone(self.mod.plugin_version("[1, 2]"))
        self.assertEqual(self.mod.plugin_version('{"version": 1.3}'), 1.3)
        problems = self.mod.coherence_problems({
            "plugin.json": 1.3,
            "EXTRACTOR_VERSION": "1.3.0",
        })
        self.assertTrue(
            any("not a version" in p for p in problems), problems
        )
        found = self.mod.marketplace_versions(
            '{"metadata": "oops", "plugins": [{"version": "1.3.0"}]}'
        )
        self.assertEqual(found, [None, "1.3.0"])
        self.assertEqual(self.mod.marketplace_versions("[1, 2]"), [None])
        found = self.mod.marketplace_versions(
            '{"metadata": {"version": 130}, '
            '"plugins": [{"version": "1.3.0"}]}'
        )
        self.assertEqual(found, [130, "1.3.0"])

    def test_an_empty_or_missing_plugins_list_is_a_problem(self):
        for text in (
            '{"metadata": {"version": "1.3.0"}, "plugins": []}',
            '{"metadata": {"version": "1.3.0"}}',
        ):
            with self.assertRaises(ValueError) as caught:
                self.mod.marketplace_versions(text)
            self.assertIn("no plugins", str(caught.exception))

    def test_a_unicode_digit_version_is_not_a_version(self):
        mixed = "1\u0663.3.0"
        self.assertFalse(self.mod.VERSION_RE.fullmatch(mixed))
        problems = self.mod.coherence_problems({
            "plugin.json": mixed,
            "EXTRACTOR_VERSION": mixed,
        })
        self.assertTrue(
            any("not a version" in p for p in problems), problems
        )
        text = (
            "## [Unreleased]\n\nThis work carries version %s.\n" % mixed
        )
        self.assertIsNone(self.mod.changelog_version(text))
        released = "## [%s] - 2026-01-01\n" % mixed
        self.assertIsNone(self.mod.changelog_version(released))

    def test_a_leading_zero_version_is_not_a_version(self):
        problems = self.mod.coherence_problems({
            "plugin.json": "01.3.0",
            "EXTRACTOR_VERSION": "01.3.0",
        })
        self.assertTrue(
            any("not a version" in p for p in problems), problems
        )

    def test_a_malformed_unreleased_declaration_governs(self):
        text = (
            "## [Unreleased]\n\nThis work carries version 01.3.0.\n\n"
            "## [1.3.0] - 2026-01-01\n"
        )
        self.assertIsNone(self.mod.changelog_version(text))
        problems = self.mod.coherence_problems({
            "CHANGELOG.md": self.mod.changelog_version(text),
            "EXTRACTOR_VERSION": "1.3.0",
        })
        self.assertTrue(
            any("no version" in p for p in problems), problems
        )

    def test_a_decoy_carries_phrase_in_a_release_note_loses(self):
        text = (
            "## [Unreleased]\n\nWork in progress.\n\n"
            "## [1.3.0] - 2026-01-01\n\n"
            "This release carries version 9.9.9 in its notes.\n"
        )
        self.assertEqual(self.mod.changelog_version(text), "1.3.0")

    def run_main_on_texts(self, plugin_text, marketplace_text,
                          changelog_text):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin = root / "plugin.json"
            plugin.write_text(plugin_text, encoding="utf-8")
            market = root / "marketplace.json"
            market.write_text(marketplace_text, encoding="utf-8")
            extract = root / "extract.py"
            extract.write_text(
                'EXTRACTOR_VERSION = "1.3.0"\n', encoding="utf-8"
            )
            log = root / "CHANGELOG.md"
            log.write_text(changelog_text, encoding="utf-8")
            original = (
                self.mod.PLUGIN_JSON, self.mod.MARKETPLACE_JSON,
                self.mod.EXTRACT_PY, self.mod.CHANGELOG_MD,
            )
            self.mod.PLUGIN_JSON = plugin
            self.mod.MARKETPLACE_JSON = market
            self.mod.EXTRACT_PY = extract
            self.mod.CHANGELOG_MD = log
            try:
                with redirect_stderr(io.StringIO()) as captured:
                    code = self.mod.main()
            finally:
                (
                    self.mod.PLUGIN_JSON, self.mod.MARKETPLACE_JSON,
                    self.mod.EXTRACT_PY, self.mod.CHANGELOG_MD,
                ) = original
            return code, captured.getvalue()

    def test_main_reports_wrong_typed_shapes_without_a_traceback(self):
        good_market = (
            '{"metadata": {"version": "1.3.0"}, "plugins": '
            '[{"name": "recognitio", "version": "1.3.0"}]}'
        )
        good_log = "## [Unreleased]\n\nThis work carries version 1.3.0.\n"
        cases = (
            ('{"version": 1.3}', good_market, good_log),
            ("[1, 2]", good_market, good_log),
            (
                '{"version": "1.3.0"}',
                '{"metadata": "oops", "plugins": '
                '[{"version": "1.3.0"}]}',
                good_log,
            ),
            (
                '{"version": "1.3.0"}',
                '{"metadata": {"version": 130}, "plugins": '
                '[{"version": "1.3.0"}]}',
                good_log,
            ),
            (
                '{"version": "1.3.0"}',
                '{"metadata": {"version": "1.3.0"}, "plugins": []}',
                good_log,
            ),
        )
        for plugin_text, market_text, log_text in cases:
            code, err = self.run_main_on_texts(
                plugin_text, market_text, log_text
            )
            self.assertEqual(code, 1, (plugin_text, err))
            self.assertIn("check_version:", err)
            self.assertNotIn("Traceback", err)


class TestPluginPackaging(unittest.TestCase):
    def test_plugin_manifest_names_the_skill_and_its_path(self):
        data = json.loads(
            (ROOT / ".claude-plugin" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(data["name"], "recognitio")
        self.assertEqual(data["skills"], ["./skills/recognitio/"])
        self.assertTrue(data["version"])

    def test_plugin_manifest_carries_the_owner_email(self):
        data = json.loads(
            (ROOT / ".claude-plugin" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            data["author"]["email"],
            "81196676+david-engelmann@users.noreply.github.com",
        )

    def test_marketplace_lists_the_plugin_with_its_skill_path(self):
        data = json.loads(
            (ROOT / ".claude-plugin" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        entries = [p for p in data["plugins"] if p["name"] == "recognitio"]
        self.assertEqual(len(entries), 1, data["plugins"])
        self.assertEqual(entries[0]["source"], "./")
        self.assertFalse(entries[0]["strict"])
        # The entry carries the skills list of the researched
        # official shape, naming the same path the plugin manifest
        # names, so a marketplace reader sees the skill the entry
        # installs without opening the manifest first.
        self.assertEqual(entries[0]["skills"], ["./skills/recognitio/"])


class TestCheckPacket(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_packet")
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.email", "test@example.com")
        git(self.repo, "config", "user.name", "Test User")
        git(self.repo, "config", "commit.gpgsign", "false")
        (self.repo / "a.py").write_text("x = 1\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-m", "one")
        self.head = git(self.repo, "rev-parse", "HEAD")

    def tearDown(self):
        self.tmp.cleanup()

    def write_packet(self, name, manifest):
        out = Path(self.tmp.name) / name
        out.mkdir()
        (out / "packet.md").write_text("# packet\n", encoding="utf-8")
        if manifest is not None:
            (out / "manifest.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
        return out

    def run_check(self, out):
        with redirect_stderr(io.StringIO()):
            return self.mod.main([str(out), "--repo", str(self.repo)])

    def test_verified_packet_for_the_current_head_passes(self):
        out = self.write_sections_packet(
            "good",
            ["## T0 Triage"],
            "# packet\n\n## T0 Triage\n\nThe triage.\n",
        )
        self.assertEqual(self.run_check(out), 0)

    def test_a_manifest_without_sections_fails(self):
        out = self.write_packet(
            "nosections", {"verified": True, "head": self.head}
        )
        self.assertEqual(self.run_check(out), 1)

    def test_unverified_packet_fails(self):
        out = self.write_packet(
            "bad", {"verified": False, "head": self.head}
        )
        self.assertEqual(self.run_check(out), 1)

    def test_packet_for_a_stale_head_fails(self):
        out = self.write_sections_packet(
            "stale",
            ["## T0 Triage"],
            "# packet\n\n## T0 Triage\n\nThe triage.\n",
            head="0" * 40,
        )
        self.assertEqual(self.run_check(out), 1)

    def test_missing_manifest_fails(self):
        out = self.write_packet("empty", None)
        self.assertEqual(self.run_check(out), 1)

    def test_empty_packet_file_fails(self):
        out = self.write_packet(
            "hollow", {"verified": True, "head": self.head}
        )
        (out / "packet.md").write_text("", encoding="utf-8")
        self.assertEqual(self.run_check(out), 1)

    def test_null_manifest_fails(self):
        out = self.write_packet(
            "nullman", {"verified": True, "head": self.head}
        )
        (out / "manifest.json").write_text("null", encoding="utf-8")
        self.assertEqual(self.run_check(out), 1)

    def test_non_object_manifest_fails(self):
        out = self.write_packet(
            "listman", {"verified": True, "head": self.head}
        )
        (out / "manifest.json").write_text('["verified"]', encoding="utf-8")
        self.assertEqual(self.run_check(out), 1)

    def write_sections_packet(self, name, sections, packet_text,
                              head=None):
        out = Path(self.tmp.name) / name
        out.mkdir()
        (out / "packet.md").write_text(packet_text, encoding="utf-8")
        (out / "manifest.json").write_text(
            json.dumps({
                "verified": True,
                "head": self.head if head is None else head,
                "sections": sections,
            }),
            encoding="utf-8",
        )
        return out

    def test_recorded_sections_present_and_filled_pass(self):
        out = self.write_sections_packet(
            "whole",
            ["## T0 Triage", "## T2 Companions"],
            "# packet\n\n## T0 Triage\n\nThe triage.\n\n"
            "## T2 Companions\n\nThe companions.\n",
        )
        self.assertEqual(self.run_check(out), 0)

    def test_a_thin_packet_wearing_a_full_manifest_fails(self):
        out = self.write_sections_packet(
            "thin",
            ["## T0 Triage", "## T2 Companions", "## T3 History"],
            "# packet\n\n## T0 Triage\n\nThe triage.\n\n"
            "## T2 Companions\n\nNot selected for this run.\n",
        )
        self.assertEqual(self.run_check(out), 1)

    def test_a_recorded_section_with_no_content_fails(self):
        out = self.write_sections_packet(
            "gutted",
            ["## T0 Triage", "## T2 Companions"],
            "# packet\n\n## T0 Triage\n\n"
            "## T2 Companions\n\nThe companions.\n",
        )
        self.assertEqual(self.run_check(out), 1)

    def test_a_heading_inside_a_fence_satisfies_nothing(self):
        out = self.write_sections_packet(
            "fenced",
            ["## T0 Triage", "## T3 History"],
            "# packet\n\n## T0 Triage\n\nThe triage.\n\n"
            "````\n## T3 History\n\nQuoted text, not a section.\n````\n",
        )
        self.assertEqual(self.run_check(out), 1)

    def test_exported_git_dir_does_not_redirect_the_packet_check(self):
        decoy = Path(self.tmp.name) / "decoy"
        decoy.mkdir()
        git(decoy, "init", "-b", "main")
        git(decoy, "config", "user.email", "test@example.com")
        git(decoy, "config", "user.name", "Test User")
        git(decoy, "config", "commit.gpgsign", "false")
        (decoy / "z.py").write_text("z = 1\n")
        git(decoy, "add", "-A")
        git(decoy, "commit", "-m", "decoy")
        out = self.write_sections_packet(
            "good",
            ["## T0 Triage"],
            "# packet\n\n## T0 Triage\n\nThe triage.\n",
        )
        env = dict(os.environ)
        env["GIT_DIR"] = str(decoy / ".git")
        env["GIT_WORK_TREE"] = str(decoy)
        original = os.environ
        os.environ = env
        try:
            code = self.run_check(out)
        finally:
            os.environ = original
        self.assertEqual(code, 0)


SIGN_OFF = (
    "Signed-off-by: David Engelmann "
    "<81196676+david-engelmann@users.noreply.github.com>"
)


class TestDcoWorkflow(unittest.TestCase):
    """The DCO job must read the trailer block, not the whole message.

    The check line is taken from the workflow itself and run against
    real commits, so reverting the workflow to a whole message grep
    makes the buried trailer case pass and this test fail.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.email", "test@example.com")
        git(self.repo, "config", "user.name", "Test User")
        git(self.repo, "config", "commit.gpgsign", "false")
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        self.pipeline = None
        for line in workflow.splitlines():
            stripped = line.strip()
            if (
                stripped.startswith("if ")
                and "git log -1" in stripped
                and "Signed-off-by" in stripped
            ):
                self.assertTrue(stripped.startswith("if ! "))
                self.assertTrue(stripped.endswith("; then"))
                self.pipeline = stripped[len("if ! "):-len("; then")]
        self.assertIsNotNone(self.pipeline)

    def tearDown(self):
        self.tmp.cleanup()

    def commit_message(self, name, message):
        msg = Path(self.tmp.name) / name
        msg.write_text(message, encoding="utf-8")
        git(self.repo, "commit", "--allow-empty", "-F", str(msg))
        return git(self.repo, "rev-parse", "HEAD")

    def check(self, sha):
        env = dict(os.environ)
        env["sha"] = sha
        result = subprocess.run(
            ["bash", "-c", self.pipeline],
            cwd=str(self.repo), env=env,
            capture_output=True, text=True,
        )
        return result.returncode

    def test_a_proper_trailer_passes(self):
        sha = self.commit_message(
            "good.txt", "A change\n\n%s\n" % SIGN_OFF
        )
        self.assertEqual(self.check(sha), 0)

    def test_a_buried_sign_off_is_not_a_trailer(self):
        sha = self.commit_message(
            "buried.txt",
            "A change\n\n%s\n\nA closing paragraph follows it.\n"
            % SIGN_OFF,
        )
        self.assertNotEqual(self.check(sha), 0)

    def test_a_wrong_sign_off_identity_fails(self):
        sha = self.commit_message(
            "wrong.txt",
            "A change\n\nSigned-off-by: Someone Else "
            "<someone@example.invalid>\n",
        )
        self.assertNotEqual(self.check(sha), 0)

    def test_the_workflow_exempts_dependabot_by_actor(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "if: github.event_name == 'pull_request' && "
            "github.actor != 'dependabot[bot]'",
            workflow,
        )


if __name__ == "__main__":
    unittest.main()
