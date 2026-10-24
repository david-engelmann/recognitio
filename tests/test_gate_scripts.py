import ast
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr
from pathlib import Path, PureWindowsPath
from unittest import mock

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


class RetryingTemporaryDirectory(tempfile.TemporaryDirectory):
    # A fixture repository can gain a file while its temporary
    # directory is being removed. CI job 120492623700 on Python
    # 3.10 failed in teardown with OSError Errno 39 Directory not
    # empty on the pack folder inside a fixture repository after
    # every assertion in the test had passed, and a rerun passed.
    # The cleanup shipped with Python 3.12 tolerates that race
    # and the one shipped with Python 3.10 does not. Removal here
    # retries a bounded number of times with a short pause and
    # then raises, so a tree that truly cannot be removed still
    # fails loudly instead of passing in silence.

    cleanup_attempts = 5
    cleanup_delay_seconds = 0.1

    def cleanup(self):
        last_error = None
        for attempt in range(self.cleanup_attempts):
            try:
                shutil.rmtree(self.name)
            except FileNotFoundError as error:
                if not os.path.exists(self.name):
                    last_error = None
                    break
                last_error = error
            except OSError as error:
                last_error = error
            else:
                last_error = None
                break
            if attempt + 1 < self.cleanup_attempts:
                time.sleep(self.cleanup_delay_seconds)
        if last_error is not None:
            raise last_error
        self._finalizer.detach()


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
            ".agents/skills/recognitio/SKILL.md",
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
        with RetryingTemporaryDirectory() as tmp:
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
        with RetryingTemporaryDirectory() as tmp:
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
        with RetryingTemporaryDirectory() as tmp:
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
        with RetryingTemporaryDirectory() as tmp:
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
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, ".gitignore",
                "# Extractor output %s working papers.\n"
                "packet/\n" % EM_DASH,
            )
            self.assertEqual(self.run_main_on([], [path]), 1)

    def test_em_dash_in_a_dependabot_comment_is_caught(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "dependabot.yml",
                "# Keep the pinned actions current %s weekly.\n"
                "version: 2\n"
                "updates:\n"
                "  - package-ecosystem: \"github-actions\"\n" % EM_DASH,
            )
            self.assertEqual(self.run_main_on([], [path]), 1)

    def test_em_dash_beside_a_url_is_still_caught(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "page.md",
                "See https://example.com/spec for the plan %s truly.\n"
                % EM_DASH,
            )
            self.assertEqual(self.run_main_on([path]), 1)

    def test_semicolon_right_after_a_markdown_link_is_caught(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "page.md",
                "See [guide](https://example.com/spec); then continue.\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)

    def test_colon_right_after_a_markdown_link_is_caught(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "page.md",
                "See [guide](https://example.com/spec): then continue.\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)

    def test_a_markdown_link_with_clean_prose_passes(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "page.md",
                "See [guide](https://example.com/spec) before continuing.\n",
            )
            self.assertEqual(self.run_main_on([path]), 0)

    def test_a_bare_url_line_passes(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "page.md",
                "The plan lives at https://example.com/spec today.\n",
            )
            self.assertEqual(self.run_main_on([path]), 0)

    def test_em_dash_in_a_template_shaped_file_is_caught(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "CLAUDE.md",
                "All guidance lives elsewhere %s read it first.\n" % EM_DASH,
            )
            self.assertEqual(self.run_main_on([path]), 1)

    def test_yaml_block_scalar_prose_is_scanned(self):
        with RetryingTemporaryDirectory() as tmp:
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
        for pattern in ("*.md", "*.mdc", "*.yml", "*.yaml"):
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
             ".claude-plugin/marketplace.json",
             ".cursor-plugin/plugin.json",
             ".cursor-plugin/marketplace.json",
             "agent-plugins-package/plugin.json"},
        )

    def test_discovery_extends_to_a_new_markdown_file_by_rule(self):
        with RetryingTemporaryDirectory() as tmp:
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
        with RetryingTemporaryDirectory() as tmp:
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
        with RetryingTemporaryDirectory() as tmp:
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
        with RetryingTemporaryDirectory() as tmp:
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
        with RetryingTemporaryDirectory() as tmp:
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
        with RetryingTemporaryDirectory() as tmp:
            found = self.mod.discover_manifest_files(Path(tmp))
            self.assertEqual(len(found), 2)
            self.assertTrue(all(not p.exists() for p in found))

    def test_manifest_discovery_extends_to_a_new_manifest_by_rule(self):
        # R19-ST-01. The portable package manifest joins the fence
        # by rule rather than by a third fixed path, so the next
        # manifest joins the same way.
        with RetryingTemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "agent-plugins-package"
            package.mkdir()
            manifest = package / "plugin.json"
            manifest.write_text("{}\n", encoding="utf-8")
            listing = root / "other" / "marketplace.json"
            listing.parent.mkdir()
            listing.write_text("{}\n", encoding="utf-8")
            hidden = root / ".tool" / "plugin.json"
            hidden.parent.mkdir()
            hidden.write_text("{}\n", encoding="utf-8")
            found = {
                str(p.relative_to(root))
                for p in self.mod.discover_manifest_files(root)
            }
            self.assertIn("agent-plugins-package/plugin.json", found)
            self.assertIn("other/marketplace.json", found)
            self.assertNotIn(".tool/plugin.json", found)

    def test_em_dash_in_a_manifest_description_is_caught(self):
        with RetryingTemporaryDirectory() as tmp:
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

    def test_em_dash_in_cursor_plugin_readme_is_caught(self):
        # R23-ST-01. The Cursor plugin README is public prose, so
        # an em dash in it fails the gate. Reverting the fence
        # change leaves the file outside the fence and this test
        # fails.
        with RetryingTemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = self.write_tmp(
                root,
                ".cursor-plugin/README.md",
                "The plugin ships the skill %s the rules.\n"
                % EM_DASH,
            )
            files = self.mod.discover_prose_files(root)
            self.assertIn(readme, files)
            self.assertEqual(self.run_main_on(files), 1)

    def test_em_dash_in_cursor_plugin_rule_file_is_caught(self):
        # R23-ST-01. The Cursor rule file is public prose, so an
        # em dash in it fails the gate. The fence discovers rule
        # files by rule, not by listing.
        with RetryingTemporaryDirectory() as tmp:
            root = Path(tmp)
            rule = self.write_tmp(
                root,
                ".cursor-plugin/rules/recognitio.mdc",
                "---\n"
                "description: Test rule.\n"
                "---\n"
                "\n"
                "The rule restates the packet discipline %s plainly.\n"
                % EM_DASH,
            )
            files = self.mod.discover_prose_files(root)
            self.assertIn(rule, files)
            self.assertEqual(self.run_main_on(files), 1)

    def test_em_dash_in_cursor_plugin_manifest_is_caught(self):
        # R23-ST-01. The Cursor plugin manifest descriptions are
        # public prose. A manifest under the plugin directory
        # joins the fence by rule.
        with RetryingTemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self.write_tmp(
                root,
                ".cursor-plugin/plugin.json",
                '{"name": "x", "description": "Does a thing %s '
                'in plain words."}\n' % EM_DASH,
            )
            found = self.mod.discover_manifest_files(root)
            self.assertIn(manifest, found)
            original = (
                self.mod.PROSE_FILES, self.mod.COMMENT_FILES,
                self.mod.MANIFEST_FILES,
            )
            self.mod.PROSE_FILES = []
            self.mod.COMMENT_FILES = []
            self.mod.MANIFEST_FILES = [manifest]
            try:
                with redirect_stderr(io.StringIO()):
                    code = self.mod.main()
            finally:
                (
                    self.mod.PROSE_FILES, self.mod.COMMENT_FILES,
                    self.mod.MANIFEST_FILES,
                ) = original
            self.assertEqual(code, 1)

    def test_discovery_keeps_the_plugin_skill_copy_out(self):
        # R23-ST-01. The plugin skill copy is pinned byte identical
        # to the canonical skill by scripts/check_cursor.py, and
        # the canonical skill is already inside the fence, so the
        # copy stays out by rule the way the generated eval
        # packets do.
        with RetryingTemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = self.write_tmp(
                root,
                ".cursor-plugin/skills/recognitio/SKILL.md",
                "The copied skill.\n",
            )
            found = self.mod.discover_prose_files(root)
            self.assertNotIn(skill, found)

    def test_a_flow_mapping_value_is_structure_not_prose(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "point: {x: 1, y: 2}\n",
            )
            self.assertEqual(self.run_main_on([path]), 0)

    def test_a_nested_sequence_of_mappings_is_structure_not_prose(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "items:\n"
                "  - - name: alpha\n"
                "    - name: beta\n",
            )
            self.assertEqual(self.run_main_on([path]), 0)

    def test_a_colon_inside_a_flow_mapping_value_still_flags(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "point: {label: \"Read: now\"}\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)

    def test_a_colon_inside_a_list_item_flow_mapping_still_flags(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "items:\n"
                "  - {label: \"Read: now\"}\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)

    def test_a_prose_mapping_value_with_a_colon_still_flags(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "note: see the guide for details: the long version\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)

    def test_a_prose_value_in_a_nested_sequence_still_flags(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "items:\n"
                "  - - name: alpha: the first one\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)

    def test_wide_key_shapes_are_structure_not_prose(self):
        shapes = (
            "app.name: myapp\n",
            "404: missing page\n",
            "my key: some value\n",
            "\"my key\": some value\n",
            "'my key': some value\n",
            "a/b: some value\n",
            "2fa: enabled\n",
        )
        for text in shapes:
            with RetryingTemporaryDirectory() as tmp:
                path = self.write_tmp(tmp, "config.yaml", text)
                self.assertEqual(self.run_main_on([path]), 0, text)

    def test_a_prose_value_after_a_wide_key_still_flags(self):
        shapes = (
            "app.name: see the guide: the long version\n",
            "404: see the guide: the long version\n",
            "\"my key\": see the guide: the long version\n",
        )
        for text in shapes:
            with RetryingTemporaryDirectory() as tmp:
                path = self.write_tmp(tmp, "config.yaml", text)
                self.assertEqual(self.run_main_on([path]), 1, text)

    def test_flow_collections_after_anchors_and_tags_are_structure(self):
        shapes = (
            "point: &anchor {x: 1, y: 2}\n",
            "point: !!str {x: 1, y: 2}\n",
            "items:\n  - &anchor {x: 1, y: 2}\n",
            "point: &anchor\n  x: 1\n  y: 2\n",
        )
        for text in shapes:
            with RetryingTemporaryDirectory() as tmp:
                path = self.write_tmp(tmp, "config.yaml", text)
                self.assertEqual(self.run_main_on([path]), 0, text)

    def test_a_flow_sequence_of_mappings_is_structure_not_prose(self):
        shapes = (
            "points: [{x: 1, y: 2}, {x: 3, y: 4}]\n",
            "items: [{name: alpha}, {name: beta}]\n",
            "items:\n  - [{x: 1, y: 2}]\n",
            "- [{x: 1, y: 2}]\n",
            "names: [alpha, beta]\n",
            "point: {inner: {x: 1}}\n",
        )
        for text in shapes:
            with RetryingTemporaryDirectory() as tmp:
                path = self.write_tmp(tmp, "config.yaml", text)
                self.assertEqual(self.run_main_on([path]), 0, text)

    def test_a_prose_value_inside_a_flow_sequence_still_flags(self):
        shapes = (
            "points: [{label: \"Read: now\"}]\n",
            "items:\n  - [{label: \"Read: now\"}]\n",
            "point: &anchor {label: \"Read: now\"}\n",
            "point: {\"label\":\"Read: now\"}\n",
        )
        for text in shapes:
            with RetryingTemporaryDirectory() as tmp:
                path = self.write_tmp(tmp, "config.yaml", text)
                self.assertEqual(self.run_main_on([path]), 1, text)

    def test_an_apostrophe_in_a_plain_flow_scalar_is_not_a_quote(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "tags: [don't, ok]\n"
                "next: value\n",
            )
            self.assertEqual(self.run_main_on([path]), 0)
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "tags: [don't, \"Read: now\"]\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)

    def test_text_after_a_flow_collection_still_flags(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "ports: [80, 443] # Open: web\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "ports: [80, 443] # Open web\n",
            )
            self.assertEqual(self.run_main_on([path]), 0)

    def test_a_key_shaped_continuation_of_a_quoted_scalar_still_flags(self):
        shapes = (
            "description: \"Long prose starts here\n"
            "  continues: with words after a key shaped colon\"\n",
            "description: \"Long prose starts\n"
            "  Summary: only colon is here\"\n",
        )
        for text in shapes:
            with RetryingTemporaryDirectory() as tmp:
                path = self.write_tmp(tmp, "config.yaml", text)
                self.assertEqual(self.run_main_on([path]), 1, text)

    def test_a_key_shaped_continuation_of_a_plain_scalar_still_flags(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "description: Long prose starts\n"
                "  Summary: only colon is here\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)

    def test_a_key_shaped_line_inside_a_flow_quoted_scalar_still_flags(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "point: {label: \"Read\n"
                "  now: the sequel\"}\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)

    def test_ordinary_keys_after_a_plain_value_still_parse(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "name: Readme\n"
                "url: https://example.com/readme\n"
                "about: What the skill does in plain words.\n"
                "other: true\n",
            )
            self.assertEqual(self.run_main_on([path]), 0)

    def test_a_multiline_flow_mapping_with_prose_values_still_flags(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "point: {\n"
                "  label: \"Read: now\",\n"
                "  other: \"See: this\"\n"
                "}\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)

    def test_yaml_keys_and_directives_are_syntax(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "# yaml-language-server: $schema=https://example.com/s.json\n"
                "language: \"en-US\"\n"
                "tone: \"Be direct and plain.\"\n",
            )
            self.assertEqual(self.run_main_on([path]), 0)

    def test_no_function_in_check_copy_passes_the_length_ceiling(self):
        source = (ROOT / "scripts" / "check_copy.py").read_text(
            encoding="utf-8"
        )
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = node.end_lineno - node.lineno + 1
                self.assertLessEqual(
                    length, 86,
                    "function %s runs %d lines, over the 86 line "
                    "ceiling the gate scripts record"
                    % (node.name, length),
                )


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
        with RetryingTemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "recognitio"
            skill_dir.mkdir()
            long_half = "x" * 600
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                "---\nname: recognitio\ndescription: %s\n  %s\n---\n\n# X\n"
                % (long_half, long_half),
                encoding="utf-8",
            )
            original = (
                self.mod.SKILL_DIR,
                self.mod.SKILL_MD,
                self.mod.EXTRACT,
                self.mod.HOME_SKILL_DIR,
            )
            self.mod.SKILL_DIR = skill_dir
            self.mod.SKILL_MD = skill_md
            self.mod.EXTRACT = ROOT / ".agents" / "skills" / "recognitio" / "scripts" / "extract.py"
            # The home spelling follows the overridden canonical, so
            # the layout check reads the fixture and not the tree.
            self.mod.HOME_SKILL_DIR = skill_dir
            try:
                with redirect_stderr(io.StringIO()) as captured:
                    code = self.mod.main()
            finally:
                (
                    self.mod.SKILL_DIR,
                    self.mod.SKILL_MD,
                    self.mod.EXTRACT,
                    self.mod.HOME_SKILL_DIR,
                ) = original
            self.assertEqual(code, 1)
            self.assertIn("over the 1024 limit", captured.getvalue())

    def run_main_on_skill_text(self, text):
        with RetryingTemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "recognitio"
            skill_dir.mkdir()
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(text, encoding="utf-8")
            original = (
                self.mod.SKILL_DIR,
                self.mod.SKILL_MD,
                self.mod.EXTRACT,
                self.mod.HOME_SKILL_DIR,
            )
            self.mod.SKILL_DIR = skill_dir
            self.mod.SKILL_MD = skill_md
            self.mod.EXTRACT = ROOT / ".agents" / "skills" / "recognitio" / "scripts" / "extract.py"
            # The home spelling follows the overridden canonical, so
            # the layout check reads the fixture and not the tree.
            self.mod.HOME_SKILL_DIR = skill_dir
            try:
                with redirect_stderr(io.StringIO()) as captured:
                    code = self.mod.main()
            finally:
                (
                    self.mod.SKILL_DIR,
                    self.mod.SKILL_MD,
                    self.mod.EXTRACT,
                    self.mod.HOME_SKILL_DIR,
                ) = original
            return code, captured.getvalue()

    def test_a_skill_file_past_the_size_limit_fails(self):
        head = "---\nname: recognitio\ndescription: a packet\n---\n\n"
        text = head + "x" * (self.mod.SKILL_TEXT_LIMIT + 1 - len(head))
        self.assertEqual(len(text), self.mod.SKILL_TEXT_LIMIT + 1)
        code, err = self.run_main_on_skill_text(text)
        self.assertEqual(code, 1)
        self.assertIn("over the %d limit" % self.mod.SKILL_TEXT_LIMIT, err)
        self.assertIn("references file", err)

    def test_a_multibyte_skill_file_past_the_byte_limit_fails(self):
        head = "---\nname: recognitio\ndescription: a packet\n---\n\n"
        text = head + "世" * 7000
        self.assertEqual(len(text), 7048)
        self.assertLess(len(text), self.mod.SKILL_TEXT_LIMIT)
        self.assertEqual(len(text.encode("utf-8")), 21048)
        self.assertGreater(
            len(text.encode("utf-8")), self.mod.SKILL_TEXT_LIMIT
        )
        code, err = self.run_main_on_skill_text(text)
        self.assertEqual(code, 1)
        self.assertIn(
            "bytes, over the %d limit" % self.mod.SKILL_TEXT_LIMIT,
            err,
        )
        self.assertIn("references file", err)

    def test_a_skill_file_at_the_size_limit_passes(self):
        head = "---\nname: recognitio\ndescription: a packet\n---\n\n"
        text = head + "x" * (self.mod.SKILL_TEXT_LIMIT - len(head))
        self.assertEqual(len(text), self.mod.SKILL_TEXT_LIMIT)
        code, err = self.run_main_on_skill_text(text)
        self.assertEqual(code, 0, err)

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
        with RetryingTemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "recognitio"
            skill_dir.mkdir()
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                "---\nname: recog--nitio\ndescription: a packet\n---\n\n# X\n",
                encoding="utf-8",
            )
            original = (
                self.mod.SKILL_DIR,
                self.mod.SKILL_MD,
                self.mod.EXTRACT,
                self.mod.HOME_SKILL_DIR,
            )
            self.mod.SKILL_DIR = skill_dir
            self.mod.SKILL_MD = skill_md
            self.mod.EXTRACT = ROOT / ".agents" / "skills" / "recognitio" / "scripts" / "extract.py"
            # The home spelling follows the overridden canonical, so
            # the layout check reads the fixture and not the tree.
            self.mod.HOME_SKILL_DIR = skill_dir
            try:
                with redirect_stderr(io.StringIO()) as captured:
                    code = self.mod.main()
            finally:
                (
                    self.mod.SKILL_DIR,
                    self.mod.SKILL_MD,
                    self.mod.EXTRACT,
                    self.mod.HOME_SKILL_DIR,
                ) = original
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
        with RetryingTemporaryDirectory() as tmp:
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

    def test_manifest_conflict_problems_names_the_broken_pair(self):
        plugin = '{"name": "x", "skills": ["./skills/x/"]}'
        broken = (
            '{"plugins": [{"name": "x", "strict": false, '
            '"skills": ["./skills/x/"]}]}'
        )
        problems = self.mod.manifest_conflict_problems(plugin, broken)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("strict", problems[0])
        # A plugin manifest that declares no components at all
        # still conflicts, because the host treats the entry
        # components under strict false as a conflict whenever a
        # plugin manifest stands beside the entry at all. A live
        # install probe in the round 6 fix lane confirmed the
        # metadata only pair fails to load with the same error.
        entry_only = (
            '{"plugins": [{"name": "x", "strict": false, '
            '"skills": ["./skills/x/"]}]}'
        )
        problems = self.mod.manifest_conflict_problems(
            '{"name": "x"}', entry_only
        )
        self.assertEqual(len(problems), 1, problems)
        # The host conflict set is the six component fields the
        # host names, so a themes pair conflicts in the same way.
        themes = (
            '{"plugins": [{"name": "x", "strict": false, '
            '"themes": ["./themes/"]}]}'
        )
        problems = self.mod.manifest_conflict_problems(
            '{"name": "x", "themes": ["./themes/"]}', themes
        )
        self.assertEqual(len(problems), 1, problems)

    def test_manifest_conflict_problems_accept_the_loadable_pairs(self):
        plugin = '{"name": "x", "skills": ["./skills/x/"]}'
        strict_true = (
            '{"plugins": [{"name": "x", "strict": true, '
            '"skills": ["./skills/x/"]}]}'
        )
        self.assertEqual(
            self.mod.manifest_conflict_problems(plugin, strict_true), []
        )
        manifest_only = '{"plugins": [{"name": "x", "strict": false}]}'
        self.assertEqual(
            self.mod.manifest_conflict_problems(plugin, manifest_only),
            [],
        )
        # The server fields stand outside the host conflict set,
        # and a live install probe in the round 6 fix lane
        # confirmed an mcpServers pair loads under strict false.
        mcp = (
            '{"plugins": [{"name": "x", "strict": false, '
            '"mcpServers": {}}]}'
        )
        self.assertEqual(
            self.mod.manifest_conflict_problems(
                '{"name": "x", "mcpServers": {}}', mcp
            ),
            [],
        )

    def test_manifest_conflict_problems_follow_the_strict_states(self):
        plugin = '{"name": "x", "skills": ["./skills/x/"]}'
        # A missing strict key reads as true on the host, so an
        # entry that names components and omits the key loads.
        absent = (
            '{"plugins": [{"name": "x", '
            '"skills": ["./skills/x/"]}]}'
        )
        self.assertEqual(
            self.mod.manifest_conflict_problems(plugin, absent), []
        )
        # An entry that sets strict to false beside a plugin
        # manifest is the conflict the host refuses.
        present_false = (
            '{"plugins": [{"name": "x", "strict": false, '
            '"skills": ["./skills/x/"]}]}'
        )
        problems = self.mod.manifest_conflict_problems(
            plugin, present_false
        )
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("strict to false", problems[0])
        # An entry that sets strict to true loads with the
        # manifest as its definition.
        present_true = (
            '{"plugins": [{"name": "x", "strict": true, '
            '"skills": ["./skills/x/"]}]}'
        )
        self.assertEqual(
            self.mod.manifest_conflict_problems(plugin, present_true),
            [],
        )

    def test_manifest_conflict_problems_cover_the_experimental_home(self):
        # The pure experimental pair, with themes declared
        # under the experimental object on both sides, is the
        # pair the round 7 audit watched the host refuse.
        pure_plugin = (
            '{"name": "x", "experimental": '
            '{"themes": ["./themes/"]}}'
        )
        pure_entry = (
            '{"plugins": [{"name": "x", "strict": false, '
            '"experimental": {"themes": ["./themes/"]}}]}'
        )
        problems = self.mod.manifest_conflict_problems(
            pure_plugin, pure_entry
        )
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("themes", problems[0])
        # The mixed pair, with the plugin manifest declaring
        # themes at the top level and the entry declaring them
        # under its experimental object, refuses in the same
        # way.
        mixed_entry = pure_entry
        problems = self.mod.manifest_conflict_problems(
            '{"name": "x", "themes": ["./themes/"]}', mixed_entry
        )
        self.assertEqual(len(problems), 1, problems)
        # The scan covers the whole conflict set in that home
        # and not themes alone.
        skills_entry = (
            '{"plugins": [{"name": "x", "strict": false, '
            '"experimental": {"skills": ["./skills/x/"]}}]}'
        )
        problems = self.mod.manifest_conflict_problems(
            '{"name": "x"}', skills_entry
        )
        self.assertEqual(len(problems), 1, problems)
        # An experimental object carrying no conflict field is
        # a control that passes, because the monitors field in
        # that home stands outside the conflict set.
        monitors_entry = (
            '{"plugins": [{"name": "x", "strict": false, '
            '"experimental": {"monitors": []}}]}'
        )
        self.assertEqual(
            self.mod.manifest_conflict_problems(
                '{"name": "x"}', monitors_entry
            ),
            [],
        )
        # An experimental conflict with no strict key still
        # loads, because the missing key reads as true.
        absent_entry = (
            '{"plugins": [{"name": "x", '
            '"experimental": {"themes": ["./themes/"]}}]}'
        )
        self.assertEqual(
            self.mod.manifest_conflict_problems(
                pure_plugin, absent_entry
            ),
            [],
        )

    def test_the_real_manifest_pair_has_no_conflict(self):
        problems = self.mod.manifest_conflict_problems(
            (ROOT / ".claude-plugin" / "plugin.json").read_text(
                encoding="utf-8"
            ),
            (ROOT / ".claude-plugin" / "marketplace.json").read_text(
                encoding="utf-8"
            ),
        )
        self.assertEqual(problems, [])

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
    def setUp(self):
        self.mod = load_script("check_version")

    def load_manifest(self, name):
        # The pinning tests read through the strict reader, so a
        # manifest with a repeated key fails here the same way it
        # fails the version gate.
        return self.mod.strict_json_loads(
            (ROOT / ".claude-plugin" / name).read_text(encoding="utf-8")
        )

    def test_plugin_manifest_names_the_skill_and_its_path(self):
        data = self.load_manifest("plugin.json")
        self.assertEqual(data["name"], "recognitio")
        self.assertEqual(data["skills"], ["./.agents/skills/recognitio/"])
        self.assertTrue(data["version"])

    def test_plugin_manifest_carries_the_owner_email(self):
        data = self.load_manifest("plugin.json")
        self.assertEqual(
            data["author"]["email"],
            "81196676+david-engelmann@users.noreply.github.com",
        )

    def test_marketplace_lists_the_plugin_with_its_skill_path(self):
        data = self.load_manifest("marketplace.json")
        # The listing carries exactly one plugin entry. A second
        # entry naming the same skill under another name is the
        # identity family in its purest form, so the gate pins
        # the count, not just the recognitio entry.
        self.assertEqual(len(data["plugins"]), 1, data["plugins"])
        entries = [p for p in data["plugins"] if p["name"] == "recognitio"]
        self.assertEqual(len(entries), 1, data["plugins"])
        self.assertEqual(entries[0]["source"], "./")
        # The entry sets strict to true, so the plugin manifest is
        # the definition the host loads and the pair may both name
        # the skill without conflicting. Under strict false the
        # host refused to load this pair at all, as the round 6
        # marketplace install run showed. The strict value is
        # pinned as a real boolean, because a wrong typed strict
        # such as the string "false" must fail loudly instead of
        # reading as strict true in silence.
        self.assertIsInstance(entries[0]["strict"], bool)
        self.assertTrue(entries[0]["strict"])
        # The entry carries the skills list of the researched
        # official shape, naming the same path the plugin manifest
        # names, so a marketplace reader sees the skill the entry
        # installs without opening the manifest first. The two
        # spellings are asserted coherent with each other, not
        # just pinned to two literals that could drift apart in
        # a later edit.
        self.assertEqual(entries[0]["skills"], ["./.agents/skills/recognitio/"])
        plugin = self.load_manifest("plugin.json")
        self.assertEqual(entries[0]["skills"], plugin["skills"])

    def test_a_repeated_key_in_plugin_json_fails(self):
        text = (
            (ROOT / ".claude-plugin" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )
        evil = text.replace(
            '"version":"1.3.0"', '"version":"9.9.9","version":"1.3.0"', 1
        )
        self.assertNotEqual(evil, text)
        with self.assertRaises(self.mod.DuplicateKeyError):
            self.mod.strict_json_loads(evil)

    def test_a_repeated_key_in_marketplace_json_fails(self):
        text = (
            (ROOT / ".claude-plugin" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        evil = text.replace('"version": "1.3.0"', '"version": "9.9.9", "version": "1.3.0"', 1)
        self.assertNotEqual(evil, text)
        with self.assertRaises(self.mod.DuplicateKeyError):
            self.mod.strict_json_loads(evil)

    def test_a_wrong_typed_strict_key_is_a_problem(self):
        plugin_text = (
            (ROOT / ".claude-plugin" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )
        market_text = (
            (ROOT / ".claude-plugin" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        data = json.loads(market_text)
        data["plugins"][0]["strict"] = "false"
        problems = self.mod.manifest_conflict_problems(
            plugin_text, json.dumps(data)
        )
        self.assertTrue(
            any("not a boolean" in problem for problem in problems),
            problems,
        )

    def test_a_missing_strict_key_stays_silent(self):
        # A missing strict key reads as true on the host, so it is
        # not a wrong typed key and must not be named.
        plugin_text = (
            (ROOT / ".claude-plugin" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )
        market_text = (
            (ROOT / ".claude-plugin" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        data = json.loads(market_text)
        del data["plugins"][0]["strict"]
        problems = self.mod.manifest_conflict_problems(
            plugin_text, json.dumps(data)
        )
        self.assertEqual(problems, [])


class TestDescriptionPins(unittest.TestCase):
    """The three spellings of the skill description are pinned.

    The frontmatter description is the trigger identity the
    TRIGGER-RESULTS.md winner discipline protects. No description
    change ships without a winning scored run. The manifest
    descriptions are the listing blurbs. A copy bar clean rewrite
    of any of the three spellings must fail the gate, so each
    text is pinned here. A deliberate change updates the
    spelling, this pin, the trigger record and the changelog in
    the same change, and the change notes say the description
    change is a spec change and why.
    """

    FRONTMATTER_DESCRIPTION = (
        "Extracts the changes from a pull request, a commit range, or a single "
        "commit and assembles them with their surrounding context into one "
        "verified packet, so a review can start from evidence instead of a bare "
        "diff. Use it when someone asks to extract changes, pull a diff for "
        "review, prepare a review packet, re-review a change after new commits, "
        "or confirm that everything in a change is present before review "
        "begins. The skill assembles evidence only. It does not conduct the "
        "review itself, judge whether a change is safe to merge, or fix "
        "findings."
    )
    MANIFEST_DESCRIPTION = (
        "Assembles a pull request or a commit range from a local clone into one "
        "verified review packet, so a review starts from evidence instead of a "
        "bare diff."
    )

    def setUp(self):
        self.skill_mod = load_script("check_skill")
        self.version_mod = load_script("check_version")

    def frontmatter_description(self):
        text = (
            ROOT / ".agents" / "skills" / "recognitio" / "SKILL.md"
        ).read_text(encoding="utf-8")
        fields = self.skill_mod.parse_frontmatter(text)
        self.assertIsNotNone(fields)
        return fields["description"]

    def manifest_description(self, name):
        data = self.version_mod.strict_json_loads(
            (ROOT / ".claude-plugin" / name).read_text(encoding="utf-8")
        )
        return data["description"]

    def marketplace_entry_description(self):
        data = self.version_mod.strict_json_loads(
            (ROOT / ".claude-plugin" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        return data["plugins"][0]["description"]

    def test_frontmatter_description_is_pinned(self):
        self.assertEqual(
            self.frontmatter_description(), self.FRONTMATTER_DESCRIPTION
        )

    def test_plugin_manifest_description_is_pinned(self):
        self.assertEqual(
            self.manifest_description("plugin.json"),
            self.MANIFEST_DESCRIPTION,
        )

    def test_marketplace_entry_description_is_pinned(self):
        self.assertEqual(
            self.marketplace_entry_description(),
            self.MANIFEST_DESCRIPTION,
        )


class TestCanonicalSkillLayout(unittest.TestCase):
    """Build 2, the canonical skill at .agents/skills/recognitio.

    The home platform spelling at .claude/skills/recognitio is a
    symlink to the canonical. These tests run the red team's T1
    to T10 adversarial plan against the build. Drift between the
    spellings, version drift on each spelling, the pinned copy
    direction, the symlink shape, the fence coverage of the new
    location, both spellings through the skill validator, the
    moved manifest pins, resolving command examples, slash
    spellings of the packaged path, and the install route naming
    the canonical source.
    """

    def setUp(self):
        self.skill_mod = load_script("check_skill")
        self.copy_mod = load_script("check_copy")
        self.version_mod = load_script("check_version")

    def make_layout(self, tmp, home_shape="symlink"):
        root = Path(tmp) / "root"
        canonical = root / ".agents" / "skills" / "recognitio"
        home = root / ".claude" / "skills" / "recognitio"
        shutil.copytree(
            ROOT / ".agents" / "skills" / "recognitio", canonical
        )
        if home_shape == "symlink":
            home.parent.mkdir(parents=True)
            home.symlink_to(Path("../../.agents/skills/recognitio"))
        else:
            shutil.copytree(canonical, home)
        return root

    def layout_problems(self, root):
        canonical = root / ".agents" / "skills" / "recognitio"
        home = root / ".claude" / "skills" / "recognitio"
        return self.skill_mod.layout_problems(canonical, home, root=root)

    def run_main_on(self, root):
        canonical = root / ".agents" / "skills" / "recognitio"
        home = root / ".claude" / "skills" / "recognitio"
        mod = self.skill_mod
        original = (
            mod.SKILL_DIR,
            mod.SKILL_MD,
            mod.EXTRACT,
            mod.HOME_SKILL_DIR,
        )
        mod.SKILL_DIR = canonical
        mod.SKILL_MD = canonical / "SKILL.md"
        mod.EXTRACT = canonical / "scripts" / "extract.py"
        mod.HOME_SKILL_DIR = home
        try:
            with redirect_stderr(io.StringIO()) as captured:
                code = mod.main(root=root)
        finally:
            (
                mod.SKILL_DIR,
                mod.SKILL_MD,
                mod.EXTRACT,
                mod.HOME_SKILL_DIR,
            ) = original
        return code, captured.getvalue()

    def test_the_shipped_home_spelling_is_a_symlink_to_canonical(self):
        # T3. The copy direction is pinned structurally. The home
        # spelling is a link, so it cannot drift and there is no
        # sync step that could copy the wrong way.
        home = ROOT / ".claude" / "skills" / "recognitio"
        canonical = ROOT / ".agents" / "skills" / "recognitio"
        self.assertTrue(home.is_symlink())
        self.assertTrue(
            os.path.samefile(home.resolve(), canonical.resolve())
        )

    def test_a_symlink_home_spelling_passes_the_layout(self):
        # T1, T4. The symlink shape the build ships.
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_layout(tmp, home_shape="symlink")
            self.assertEqual(self.layout_problems(root), [])

    def test_a_byte_identical_home_copy_passes_the_layout(self):
        # T1, T4. The copy shape the build also accepts.
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_layout(tmp, home_shape="copy")
            self.assertEqual(self.layout_problems(root), [])

    def test_a_symlink_pointing_elsewhere_fails(self):
        # T1. A home spelling that resolves to another directory
        # is a second instruction source.
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_layout(tmp, home_shape="symlink")
            other = root / "other"
            other.mkdir()
            (other / "SKILL.md").write_text(
                "---\nname: recognitio\ndescription: other\n---\n",
                encoding="utf-8",
            )
            home = root / ".claude" / "skills" / "recognitio"
            home.unlink()
            home.symlink_to(Path("../../other"))
            problems = self.layout_problems(root)
            self.assertTrue(problems, "expected a layout problem")
            self.assertTrue(
                any(".claude/skills/recognitio" in p for p in problems),
                problems,
            )

    def test_a_symlink_leaving_the_tree_fails(self):
        # T4. A home spelling that points outside the tree is a
        # pointer at an uncontrolled skill.
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_layout(tmp, home_shape="symlink")
            outside = Path(tmp) / "outside"
            outside.mkdir()
            home = root / ".claude" / "skills" / "recognitio"
            home.unlink()
            home.symlink_to(outside)
            problems = self.layout_problems(root)
            self.assertTrue(
                any("outside the tree" in p for p in problems), problems
            )

    def test_a_drifted_home_copy_fails_naming_the_file(self):
        # T1. Plant A of the red team plan, drift in the home
        # spelling only.
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_layout(tmp, home_shape="copy")
            home_md = root / ".claude" / "skills" / "recognitio" / "SKILL.md"
            text = home_md.read_text(encoding="utf-8")
            home_md.write_text(
                text.replace("Judgement belongs", "Judgement stays"),
                encoding="utf-8",
            )
            problems = self.layout_problems(root)
            self.assertTrue(problems, "expected a layout problem")
            self.assertTrue(
                any("SKILL.md" in p and "drifted" in p for p in problems),
                problems,
            )

    def test_an_extra_file_in_the_home_copy_fails(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_layout(tmp, home_shape="copy")
            (root / ".claude" / "skills" / "recognitio" / "EXTRA.md").write_text(
                "# extra\n", encoding="utf-8"
            )
            problems = self.layout_problems(root)
            self.assertTrue(
                any("extra file" in p for p in problems), problems
            )

    def test_a_missing_home_spelling_fails(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_layout(tmp, home_shape="symlink")
            home = root / ".claude" / "skills" / "recognitio"
            home.unlink()
            problems = self.layout_problems(root)
            self.assertTrue(
                any("missing" in p for p in problems), problems
            )

    def test_drift_in_the_home_copy_fails_the_full_skill_gate(self):
        # T1 against the real gate entry point, not just the
        # layout function.
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_layout(tmp, home_shape="copy")
            home_md = root / ".claude" / "skills" / "recognitio" / "SKILL.md"
            text = home_md.read_text(encoding="utf-8")
            home_md.write_text(
                text.replace("Judgement belongs", "Judgement stays"),
                encoding="utf-8",
            )
            code, output = self.run_main_on(root)
            self.assertEqual(code, 1)
            self.assertIn(".claude/skills/recognitio", output)

    def test_drift_in_the_canonical_copy_fails_the_full_skill_gate(self):
        # T1 plant B, drift in the canonical spelling only.
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_layout(tmp, home_shape="copy")
            canonical_md = (
                root / ".agents" / "skills" / "recognitio" / "SKILL.md"
            )
            text = canonical_md.read_text(encoding="utf-8")
            canonical_md.write_text(
                text.replace("Judgement belongs", "Judgement stays"),
                encoding="utf-8",
            )
            code, output = self.run_main_on(root)
            self.assertEqual(code, 1)
            self.assertIn(".agents/skills/recognitio", output)

    def test_drift_never_flows_from_home_to_canonical(self):
        # T3. After a failed gate on a drifted home copy, the
        # canonical bytes are untouched. There is no sync step
        # that could copy the drift the wrong way.
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_layout(tmp, home_shape="copy")
            canonical_md = (
                root / ".agents" / "skills" / "recognitio" / "SKILL.md"
            )
            before = canonical_md.read_bytes()
            home_md = root / ".claude" / "skills" / "recognitio" / "SKILL.md"
            home_md.write_text(
                home_md.read_text(encoding="utf-8").replace(
                    "Judgement belongs", "Judgement stays"
                ),
                encoding="utf-8",
            )
            code, _output = self.run_main_on(root)
            self.assertEqual(code, 1)
            self.assertEqual(canonical_md.read_bytes(), before)

    def test_extractor_version_drift_in_canonical_fails_coherence(self):
        # T2. A version bearing drift on the canonical spelling.
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_layout(tmp, home_shape="copy")
            extract = (
                root / ".agents" / "skills" / "recognitio"
                / "scripts" / "extract.py"
            )
            text = extract.read_text(encoding="utf-8")
            self.assertIn('EXTRACTOR_VERSION = "1.3.0"', text)
            planted = text.replace(
                'EXTRACTOR_VERSION = "1.3.0"',
                'EXTRACTOR_VERSION = "1.3.1"',
                1,
            )
            version = self.version_mod.extractor_version(planted)
            self.assertEqual(version, "1.3.1")
            problems = self.version_mod.coherence_problems(
                {"EXTRACTOR_VERSION": version, "plugin.json": "1.3.0"}
            )
            self.assertTrue(
                any("disagree" in p for p in problems), problems
            )

    def test_extractor_version_drift_in_home_copy_fails_layout(self):
        # T2. The same plant on a real directory home spelling is
        # caught by the layout check, because the copy is no longer
        # byte identical to the canonical.
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_layout(tmp, home_shape="copy")
            extract = (
                root / ".claude" / "skills" / "recognitio"
                / "scripts" / "extract.py"
            )
            text = extract.read_text(encoding="utf-8")
            extract.write_text(
                text.replace(
                    'EXTRACTOR_VERSION = "1.3.0"',
                    'EXTRACTOR_VERSION = "1.3.1"',
                    1,
                ),
                encoding="utf-8",
            )
            problems = self.layout_problems(root)
            self.assertTrue(
                any("drifted" in p for p in problems), problems
            )

    def test_canonical_skill_md_is_discovered_exactly_once(self):
        # T4, T5. The copy bar scans the canonical skill prose
        # through the canonical path only. The home spelling is a
        # symlink the discovery walk does not descend into, so no
        # file is scanned twice and the canonical is not silently
        # excluded by the dot directory rule.
        names = [
            str(p.relative_to(ROOT))
            for p in self.copy_mod.discover_prose_files()
        ]
        self.assertIn(".agents/skills/recognitio/SKILL.md", names)
        self.assertEqual(
            names.count(".agents/skills/recognitio/SKILL.md"), 1
        )
        self.assertEqual(
            [n for n in names if n.startswith(".claude/skills/")], []
        )

    def test_dot_directories_without_skill_prose_stay_excluded(self):
        # T5. The exclusion fix is surgical. Tool directories are
        # still outside the fence.
        self.assertTrue(
            self.copy_mod.is_fence_excluded(
                ROOT, ROOT / ".venv" / "lib" / "x.md"
            )
        )
        self.assertFalse(
            self.copy_mod.is_fence_excluded(
                ROOT, ROOT / ".agents" / "skills" / "recognitio" / "SKILL.md"
            )
        )
        self.assertFalse(
            self.copy_mod.is_fence_excluded(
                ROOT, ROOT / ".github" / "workflows" / "ci.yml"
            )
        )

    def test_a_broken_name_in_home_spelling_fails_naming_it(self):
        # T6. Each spelling goes through the validator on its own.
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_layout(tmp, home_shape="copy")
            home_md = root / ".claude" / "skills" / "recognitio" / "SKILL.md"
            home_md.write_text(
                "---\nname: recog--nitio\ndescription: a packet\n---\n\n# X\n",
                encoding="utf-8",
            )
            code, output = self.run_main_on(root)
            self.assertEqual(code, 1)
            self.assertIn(".claude/skills/recognitio", output)
            self.assertIn("consecutive hyphens", output)

    def test_a_broken_name_in_canonical_spelling_fails_naming_it(self):
        # T6. The canonical spelling gets the same treatment.
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_layout(tmp, home_shape="copy")
            canonical_md = (
                root / ".agents" / "skills" / "recognitio" / "SKILL.md"
            )
            canonical_md.write_text(
                "---\nname: recog--nitio\ndescription: a packet\n---\n\n# X\n",
                encoding="utf-8",
            )
            code, output = self.run_main_on(root)
            self.assertEqual(code, 1)
            self.assertIn(".agents/skills/recognitio", output)
            self.assertIn("consecutive hyphens", output)

    def test_skill_command_examples_resolve_at_both_spellings(self):
        # T8. Every example path in the shipped SKILL.md resolves
        # to a file at the canonical spelling and through the home
        # spelling, so the move cannot leave stale paths the copy
        # scan never checks.
        text = (
            ROOT / ".agents" / "skills" / "recognitio" / "SKILL.md"
        ).read_text(encoding="utf-8")
        paths = re.findall(r"python3 (\S+)", text)
        self.assertTrue(paths, "expected command examples in SKILL.md")
        for path in paths:
            self.assertTrue(
                (ROOT / path).is_file(), "example path missing: %s" % path
            )
            self.assertTrue(
                path.startswith(".agents/skills/recognitio/"),
                "example path outside the canonical skill: %s" % path,
            )
            home_path = path.replace(
                ".agents/skills/recognitio/",
                ".claude/skills/recognitio/",
                1,
            )
            self.assertTrue(
                (ROOT / home_path).is_file(),
                "example path missing at home spelling: %s" % home_path,
            )

    def test_a_backslash_skills_path_fails_the_manifest_pin(self):
        # T9. A backslash spelling of the packaged path is a
        # different string and must fail the pin, never read as
        # the same pointer.
        data = self.version_mod.strict_json_loads(
            (ROOT / ".claude-plugin" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )
        data["skills"] = [".\\.agents\\skills\\recognitio\\"]
        with self.assertRaises(AssertionError):
            self.assertEqual(
                data["skills"], ["./.agents/skills/recognitio/"]
            )

    def test_a_no_dot_slash_skills_path_fails_the_manifest_pin(self):
        # T9. The plant H restyle, accepted silently before the
        # pins.
        data = self.version_mod.strict_json_loads(
            (ROOT / ".claude-plugin" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        data["plugins"][0]["skills"] = [".agents/skills/recognitio"]
        with self.assertRaises(AssertionError):
            self.assertEqual(
                data["plugins"][0]["skills"],
                ["./.agents/skills/recognitio/"],
            )

    def test_readme_install_route_names_the_canonical_source(self):
        # T10. The folder copy route installs from the canonical
        # skill, not from the old location.
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("cp -r .agents/skills/recognitio", text)
        self.assertNotIn("cp -r skills/recognitio", text)


class TestCheckPacket(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_packet")
        self.tmp = RetryingTemporaryDirectory()
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
        self.tmp = RetryingTemporaryDirectory()
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


class TestCheckEvals(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_evals")

    def copy_fixture(self, tmp):
        root = Path(tmp) / "root"
        shutil.copytree(ROOT / "evals", root / "evals")
        shutil.copytree(ROOT / "tests", root / "tests")
        shutil.copytree(ROOT / "scripts", root / "scripts")
        skill_scripts = (
            root / ".agents" / "skills" / "recognitio" / "scripts"
        )
        skill_scripts.mkdir(parents=True)
        shutil.copy2(
            ROOT / ".agents" / "skills" / "recognitio" / "scripts" / "extract.py",
            skill_scripts / "extract.py",
        )
        return root

    def test_the_real_eval_artefacts_pass(self):
        self.assertEqual(self.mod.all_problems(ROOT), [])

    def test_a_transcript_edit_fails_naming_its_file(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = root / "evals" / "tasks" / "task-06" / "transcripts.md"
            text = target.read_text(encoding="utf-8")
            text = text.replace(
                "Finding 2. The file is renamed from ledger.py to "
                "book.py, so anything importing the old module name "
                "will break. I cannot name an importer, because the "
                "diff shows no other file. This is a warning, not a "
                "placed finding.",
                "Finding 2. report.py line 1 reads from ledger "
                "import total, so that import names a module that "
                "no longer exists and report.py breaks.",
            )
            self.assertIn("report.py line 1 reads", text)
            target.write_text(text, encoding="utf-8")
            problems = self.mod.checksum_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn(
                "evals/tasks/task-06/transcripts.md", problems[0]
            )

    def test_a_planted_rule_edit_fails_naming_its_file(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = root / "evals" / "tasks" / "task-02" / "planted.md"
            text = target.read_text(encoding="utf-8")
            text = text.replace(
                "A pass finds this only when it names the test "
                "expectation or the unchecked caller in server.py.",
                "A pass finds this when it notes the behaviour "
                "change in general words.",
            )
            self.assertIn("in general words", text)
            target.write_text(text, encoding="utf-8")
            problems = self.mod.checksum_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn(
                "evals/tasks/task-02/planted.md", problems[0]
            )

    def test_a_results_cell_edit_fails_the_totals_check(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = root / "evals" / "RESULTS.md"
            text = target.read_text(encoding="utf-8")
            text = text.replace(
                "| task-01 | 2 | 1 | 2 |",
                "| task-01 | 2 | 2 | 2 |",
            )
            self.assertIn("| task-01 | 2 | 2 | 2 |", text)
            target.write_text(text, encoding="utf-8")
            problems = self.mod.results_problems(root)
            self.assertTrue(problems)
            self.assertIn("total row states 4", problems[0])
            named = self.mod.checksum_problems(root)
            self.assertEqual(len(named), 1)
            self.assertIn("evals/RESULTS.md", named[0])

    def test_a_tampered_diff_fails_the_rebuild(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = root / "evals" / "tasks" / "task-01" / "diff.patch"
            data = target.read_bytes()
            target.write_bytes(data.replace(b"tax + tax", b"tax + fee"))
            problems = self.mod.packet_problems(root)
            self.assertTrue(
                any(
                    "task-01" in problem and "byte for byte" in problem
                    for problem in problems
                ),
                problems,
            )

    def test_the_checksum_record_regenerates_and_then_passes(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = root / "evals" / "tasks" / "task-03" / "planted.md"
            text = target.read_text(encoding="utf-8")
            target.write_text(text + "\nA deliberate note.\n",
                              encoding="utf-8")
            self.assertEqual(len(self.mod.checksum_problems(root)), 1)
            original = self.mod.ROOT
            self.mod.ROOT = root
            try:
                with redirect_stderr(io.StringIO()):
                    code = self.mod.main(["--write-checksums"])
            finally:
                self.mod.ROOT = original
            self.assertEqual(code, 0)
            self.assertEqual(self.mod.checksum_problems(root), [])

    def test_a_manifest_entry_missing_a_key_fails_the_rebuild(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = (
                root / "evals" / "tasks" / "task-03" / "manifest.json"
            )
            manifest = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["files"]), 2)
            del manifest["files"][0]["hunks"]
            target.write_text(json.dumps(manifest), encoding="utf-8")
            problems = self.mod.packet_problems(root)
            self.assertTrue(
                any(
                    "task-03" in problem and "entries" in problem
                    for problem in problems
                ),
                problems,
            )

    def test_a_non_object_manifest_is_a_problem_not_a_crash(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = (
                root / "evals" / "tasks" / "task-02" / "manifest.json"
            )
            target.write_text("[1, 2]\n", encoding="utf-8")
            problems = self.mod.packet_problems(root)
            self.assertTrue(
                any(
                    "task-02" in problem
                    and "does not hold a JSON object" in problem
                    for problem in problems
                ),
                problems,
            )

    def test_a_manifest_entry_key_missing_from_every_entry_fails(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = (
                root / "evals" / "tasks" / "task-03" / "manifest.json"
            )
            manifest = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["files"]), 2)
            for entry in manifest["files"]:
                del entry["hunks"]
            target.write_text(json.dumps(manifest), encoding="utf-8")
            problems = self.mod.packet_problems(root)
            self.assertTrue(
                any(
                    "task-03" in problem and "entries" in problem
                    for problem in problems
                ),
                problems,
            )

    def test_a_task_with_crlf_sources_rebuilds_byte_for_byte(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            task = root / "evals" / "tasks" / "task-07"
            task.mkdir()
            base = {"crlf.py": "one = 1\r\ntwo = 2\r\n"}
            head = {"crlf.py": "one = 1\r\ntwo = 22\r\n"}
            (task / "sources.json").write_text(
                json.dumps({"base": base, "head": head}),
                encoding="utf-8",
            )
            (task / "planted.md").write_text(
                "# Planted defects for task-07\n\nNone.\n",
                encoding="utf-8",
            )
            work = Path(tmp) / "build"
            repo = work / "repo"
            repo.mkdir(parents=True)
            self.mod.git(repo, "init", "-b", "main")
            self.mod.git(repo, "config", "user.email", "eval@example.com")
            self.mod.git(repo, "config", "user.name", "Eval Fixture")
            self.mod.git(repo, "config", "core.autocrlf", "false")
            self.mod.git(repo, "config", "commit.gpgsign", "false")
            self.mod.write_fixture(repo, base)
            self.mod.git(repo, "add", "-A")
            self.mod.git(repo, "commit", "-m", "base")
            base_sha = self.mod.git(repo, "rev-parse", "HEAD").strip()
            self.mod.write_fixture(repo, head)
            self.mod.git(repo, "add", "-A")
            self.mod.git(repo, "commit", "-m", "head")
            head_sha = self.mod.git(repo, "rev-parse", "HEAD").strip()
            diff = self.mod.git(
                repo,
                *(self.mod.DIFF_FLAGS
                  + ["%s..%s" % (base_sha, head_sha)]),
                raw=True,
            )
            self.assertIn(b"\r\n", diff)
            (task / "diff.patch").write_bytes(diff)
            out = work / "out"
            extract = (
                root / ".agents" / "skills" / "recognitio" / "scripts" / "extract.py"
            )
            run = subprocess.run(
                [sys.executable, str(extract), "--repo", str(repo),
                 "--range", "%s..%s" % (base_sha, head_sha),
                 "--out", str(out)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            shutil.copy2(out / "packet.md", task / "packet.md")
            shutil.copy2(out / "manifest.json", task / "manifest.json")
            problems = self.mod.packet_problems(root)
            self.assertFalse(
                any("task-07" in problem for problem in problems),
                problems,
            )

    def test_a_renamed_cited_test_fails_the_corpus_check(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = root / "tests" / "test_gate_scripts.py"
            text = target.read_text(encoding="utf-8")
            text = text.replace(
                "def test_the_real_skill_package_is_valid",
                "def test_the_real_skill_package_stays_valid",
            )
            self.assertIn(
                "test_the_real_skill_package_stays_valid", text
            )
            target.write_text(text, encoding="utf-8")
            problems = self.mod.corpus_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn(
                "test_the_real_skill_package_is_valid", problems[0]
            )

    def test_a_corpus_name_that_never_existed_fails(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = root / "evals" / "corpus.md"
            text = target.read_text(encoding="utf-8")
            target.write_text(
                text + "\nA row citing "
                "`test_a_name_that_never_existed` in the gate "
                "script suite.\n",
                encoding="utf-8",
            )
            problems = self.mod.corpus_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn(
                "test_a_name_that_never_existed", problems[0]
            )

    def test_a_duplicate_key_in_the_checksum_record_fails(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = root / "evals" / "tasks" / "task-06" / "transcripts.md"
            text = target.read_text(encoding="utf-8")
            target.write_text(text + "\nTampered line.\n", encoding="utf-8")
            tampered = hashlib.sha256(target.read_bytes()).hexdigest()
            record_path = root / "evals" / "checksums.json"
            lines = record_path.read_text(encoding="utf-8").splitlines(
                keepends=True
            )
            key = '"evals/tasks/task-06/transcripts.md"'
            out = []
            inserted = False
            for line in lines:
                if key in line and not inserted:
                    out.append('    %s: "%s",\n' % (key, tampered))
                    inserted = True
                out.append(line)
            self.assertTrue(inserted)
            record_path.write_text("".join(out), encoding="utf-8")
            problems = self.mod.checksum_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("repeated key", problems[0])

    def test_a_duplicate_key_in_a_sources_file_fails_the_rebuild(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = root / "evals" / "tasks" / "task-01" / "sources.json"
            text = target.read_text(encoding="utf-8")
            data = json.loads(text)
            stripped = text.rstrip()
            self.assertTrue(stripped.endswith("}"))
            target.write_text(
                stripped[:-1]
                + ', "head": '
                + json.dumps(data["head"])
                + "}\n",
                encoding="utf-8",
            )
            problems = self.mod.packet_problems(root)
            self.assertTrue(
                any(
                    "task-01" in problem and "repeated key" in problem
                    for problem in problems
                ),
                problems,
            )

    def test_a_duplicate_key_in_a_saved_manifest_fails(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = root / "evals" / "tasks" / "task-01" / "manifest.json"
            text = target.read_text(encoding="utf-8")
            self.assertIn('"verified": true', text)
            target.write_text(
                text.replace(
                    '"verified": true',
                    '"verified": true, "verified": true',
                    1,
                ),
                encoding="utf-8",
            )
            problems = self.mod.packet_problems(root)
            self.assertTrue(
                any(
                    "task-01" in problem and "repeated key" in problem
                    for problem in problems
                ),
                problems,
            )

    def test_record_keys_use_posix_spelling(self):
        root = PureWindowsPath("C:/repo")
        path = PureWindowsPath(
            "C:/repo/evals/tasks/task-01/diff.patch"
        )
        self.assertEqual(
            self.mod.record_key(root, path),
            "evals/tasks/task-01/diff.patch",
        )

    def test_task06_scores_rederive_from_its_transcripts(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            self.assertEqual(self.mod.task06_problems(root), [])

    def test_an_upgraded_task06_transcript_fails_the_derivation(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = root / "evals" / "tasks" / "task-06" / "transcripts.md"
            text = target.read_text(encoding="utf-8")
            text = text.replace(
                "Finding 2. The file is renamed from ledger.py to "
                "book.py, so anything importing the old module name "
                "will break. I cannot name an importer, because the "
                "diff shows no other file. This is a warning, not a "
                "placed finding.",
                "Finding 2. report.py line 1 reads from ledger "
                "import total, so that import names a module that "
                "no longer exists and report.py breaks.",
            )
            self.assertIn("report.py line 1 reads", text)
            target.write_text(text, encoding="utf-8")
            self.mod.write_checksums(root)
            self.assertEqual(self.mod.checksum_problems(root), [])
            problems = self.mod.task06_problems(root)
            self.assertTrue(problems)
            self.assertTrue(
                any("derives as 2 of 2" in problem for problem in problems),
                problems,
            )

    def test_a_moved_task06_results_cell_fails_the_derivation(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = root / "evals" / "RESULTS.md"
            text = target.read_text(encoding="utf-8")
            text = re.sub(
                r"The raw pass reported 1 of 2 on this\s+task",
                "The raw pass reported 2 of 2 on this task",
                text,
                count=1,
            )
            self.assertIn(
                "The raw pass reported 2 of 2 on this task", text
            )
            target.write_text(text, encoding="utf-8")
            notes = root / "evals" / "PASS-NOTES.md"
            notes_text = notes.read_text(encoding="utf-8")
            notes_text = re.sub(
                r"The raw pass reported 1 of 2 planted",
                "The raw pass reported 2 of 2 planted",
                notes_text,
                count=1,
            )
            self.assertIn(
                "The raw pass reported 2 of 2 planted", notes_text
            )
            notes.write_text(notes_text, encoding="utf-8")
            self.mod.write_checksums(root)
            self.assertEqual(self.mod.checksum_problems(root), [])
            problems = self.mod.task06_problems(root)
            self.assertTrue(problems)
            self.assertTrue(
                any("record 2 of 2" in problem for problem in problems),
                problems,
            )

    def test_an_unparseable_task06_planted_rule_fails_closed(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = root / "evals" / "tasks" / "task-06" / "planted.md"
            text = target.read_text(encoding="utf-8")
            text = text.replace(
                "renames ledger.py to book.py", "renames one module"
            )
            self.assertNotIn("renames ledger.py", text)
            target.write_text(text, encoding="utf-8")
            problems = self.mod.task06_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("no longer parses", problems[0])

    def test_tampered_sources_regeneration_fails_the_anchor(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            task = root / "evals" / "tasks" / "task-06"
            sources_path = task / "sources.json"
            sources = json.loads(sources_path.read_text(encoding="utf-8"))
            sources["head"]["report.py"] = (
                "from book import total\n\n\n"
                "def grand(items):\n"
                "    return total(items)\n"
            )
            sources_path.write_text(json.dumps(sources), encoding="utf-8")
            work = Path(tmp) / "regen"
            repo, base, head, diff = self.mod.build_fixture_repo(
                str(work), sources
            )
            (task / "diff.patch").write_bytes(diff)
            out = work / "out"
            extract = (
                root / ".agents" / "skills" / "recognitio" / "scripts" / "extract.py"
            )
            run = subprocess.run(
                [sys.executable, str(extract), "--repo", str(repo),
                 "--range", "%s..%s" % (base, head),
                 "--out", str(out)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            shutil.copy2(out / "packet.md", task / "packet.md")
            shutil.copy2(out / "manifest.json", task / "manifest.json")
            original = self.mod.ROOT
            self.mod.ROOT = root
            try:
                with redirect_stderr(io.StringIO()):
                    self.assertEqual(
                        self.mod.main(["--write-source-anchors"]), 0
                    )
                    self.assertEqual(
                        self.mod.main(["--write-checksums"]), 0
                    )
            finally:
                self.mod.ROOT = original
            self.assertEqual(self.mod.checksum_problems(root), [])
            self.assertEqual(self.mod.source_anchor_problems(root), [])
            problems = self.mod.task06_problems(root)
            self.assertTrue(problems)
            self.assertTrue(
                any("D1 defect" in problem for problem in problems),
                problems,
            )
            self.assertTrue(self.mod.all_problems(root))

    def test_source_anchors_regenerate_and_then_pass(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = root / "evals" / "tasks" / "task-01" / "sources.json"
            text = target.read_text(encoding="utf-8")
            target.write_text(text + "\n", encoding="utf-8")
            problems = self.mod.source_anchor_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("task-01", problems[0])
            original = self.mod.ROOT
            self.mod.ROOT = root
            try:
                with redirect_stderr(io.StringIO()):
                    code = self.mod.main(["--write-source-anchors"])
            finally:
                self.mod.ROOT = original
            self.assertEqual(code, 0)
            self.assertEqual(self.mod.source_anchor_problems(root), [])

    def test_the_checksum_refresh_refuses_while_source_anchors_are_stale(
        self,
    ):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = root / "evals" / "tasks" / "task-01" / "sources.json"
            text = target.read_text(encoding="utf-8")
            target.write_text(text + "\n", encoding="utf-8")
            original = self.mod.ROOT
            self.mod.ROOT = root
            try:
                with redirect_stderr(io.StringIO()):
                    code = self.mod.main(["--write-checksums"])
            finally:
                self.mod.ROOT = original
            self.assertEqual(code, 2)

    def test_a_dropped_corpus_row_fails_the_coverage_floor(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = root / "evals" / "corpus.md"
            lines = target.read_text(encoding="utf-8").splitlines(
                keepends=True
            )
            start = next(
                i
                for i, line in enumerate(lines)
                if line.startswith("## Round 1 incidents")
            )
            dropped = False
            kept = []
            for i, line in enumerate(lines):
                if (
                    not dropped
                    and i > start
                    and line.startswith("|")
                    and not line.startswith("| Incident")
                    and not line.startswith("| ---")
                ):
                    dropped = True
                    continue
                kept.append(line)
            self.assertTrue(dropped)
            target.write_text("".join(kept), encoding="utf-8")
            self.mod.write_checksums(root)
            self.assertEqual(self.mod.checksum_problems(root), [])
            problems = self.mod.corpus_coverage_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("Round 1", problems[0])
            self.assertIn("lost", problems[0])

    def test_a_dropped_corpus_citation_fails_the_coverage_floor(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = root / "evals" / "corpus.md"
            text = target.read_text(encoding="utf-8")
            text = text.replace(
                " and `test_modify_without_a_copy_control_is_unchanged`",
                "",
                1,
            )
            self.assertNotIn(
                "test_modify_without_a_copy_control_is_unchanged", text
            )
            target.write_text(text, encoding="utf-8")
            self.mod.write_checksums(root)
            self.assertEqual(self.mod.checksum_problems(root), [])
            problems = self.mod.corpus_coverage_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("Round 6", problems[0])
            self.assertIn(
                "test_modify_without_a_copy_control_is_unchanged",
                problems[0],
            )

    def test_corpus_md_stands_in_the_checksum_record(self):
        self.assertIn("evals/corpus.md", self.mod.build_record(ROOT))
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = root / "evals" / "corpus.md"
            text = target.read_text(encoding="utf-8")
            target.write_text(
                text + "\nA dropped row hides here.\n", encoding="utf-8"
            )
            problems = self.mod.checksum_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("evals/corpus.md", problems[0])

    def test_corpus_coverage_regenerates_and_then_passes(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = root / "evals" / "corpus.md"
            text = target.read_text(encoding="utf-8")
            text = text.replace(
                " and `test_modify_without_a_copy_control_is_unchanged`",
                "",
                1,
            )
            target.write_text(text, encoding="utf-8")
            self.assertEqual(
                len(self.mod.corpus_coverage_problems(root)), 1
            )
            original = self.mod.ROOT
            self.mod.ROOT = root
            try:
                with redirect_stderr(io.StringIO()):
                    code = self.mod.main(["--write-corpus-coverage"])
            finally:
                self.mod.ROOT = original
            self.assertEqual(code, 0)
            self.assertEqual(
                self.mod.corpus_coverage_problems(root), []
            )

    def test_scope_cap_names_the_highest_round_section(self):
        self.assertEqual(self.mod.corpus_scope_problems(ROOT), [])

    def test_a_stale_scope_sentence_fails_the_scope_check(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = root / "evals" / "corpus.md"
            text = target.read_text(encoding="utf-8")
            stale = text.replace("through round 14", "through round 11", 1)
            self.assertNotEqual(stale, text)
            target.write_text(stale, encoding="utf-8")
            problems = self.mod.corpus_scope_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("round 11", problems[0])
            self.assertIn("round 14", problems[0])

    def test_a_section_past_the_scope_cap_fails_the_scope_check(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = root / "evals" / "corpus.md"
            text = target.read_text(encoding="utf-8")
            target.write_text(
                text + "\n## Round 15 incidents\n\nNothing yet.\n",
                encoding="utf-8",
            )
            problems = self.mod.corpus_scope_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("round 14", problems[0])
            self.assertIn("round 15", problems[0])

    def test_a_skipped_round_fails_the_scope_check(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = root / "evals" / "corpus.md"
            text = target.read_text(encoding="utf-8")
            skipped = text.replace(
                "## Round 11 incidents", "## Round eleven incidents", 1
            )
            self.assertNotEqual(skipped, text)
            target.write_text(skipped, encoding="utf-8")
            problems = self.mod.corpus_scope_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("round 11", problems[0])

    def test_help_output_carries_no_banned_marks(self):
        scripts = [
            ROOT / ".agents" / "skills" / "recognitio" / "scripts" / "extract.py",
            ROOT / "scripts" / "check_evals.py",
            ROOT / "scripts" / "check_packet.py",
        ]
        for script in scripts:
            run = subprocess.run(
                [sys.executable, str(script), "--help"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(run.returncode, 0, script.name)
            for mark, name in (("\u2014", "em dash"), (";", "semicolon")):
                self.assertNotIn(
                    mark,
                    run.stdout,
                    "%s in the help output of %s" % (name, script.name),
                )


class TestRetryingTemporaryDirectory(unittest.TestCase):
    def test_cleanup_retries_a_removal_that_fails_once(self):
        holder = RetryingTemporaryDirectory()
        Path(holder.name, "kept.txt").write_text("x", encoding="utf-8")
        real_rmtree = shutil.rmtree
        calls = []

        def flaky(path, *args, **kwargs):
            calls.append(path)
            if len(calls) == 1:
                raise OSError("directory not empty")
            return real_rmtree(path, *args, **kwargs)

        with mock.patch.object(shutil, "rmtree", flaky):
            with mock.patch.object(time, "sleep", lambda seconds: None):
                holder.cleanup()
        self.assertEqual(len(calls), 2)
        self.assertFalse(Path(holder.name).exists())

    def test_cleanup_retries_when_a_child_path_vanishes_mid_removal(self):
        holder = RetryingTemporaryDirectory()
        Path(holder.name, "kept.txt").write_text("x", encoding="utf-8")
        real_rmtree = shutil.rmtree
        calls = []

        def vanishing(path, *args, **kwargs):
            calls.append(path)
            if len(calls) == 1:
                raise FileNotFoundError("a child path vanished")
            return real_rmtree(path, *args, **kwargs)

        with mock.patch.object(shutil, "rmtree", vanishing):
            with mock.patch.object(time, "sleep", lambda seconds: None):
                holder.cleanup()
        self.assertEqual(len(calls), 2)
        self.assertFalse(Path(holder.name).exists())

    def test_cleanup_raises_after_the_bound_when_removal_always_fails(self):
        holder = RetryingTemporaryDirectory()
        calls = []

        def always_fails(path, *args, **kwargs):
            calls.append(path)
            raise OSError("directory not empty")

        try:
            with mock.patch.object(shutil, "rmtree", always_fails):
                with mock.patch.object(time, "sleep", lambda seconds: None):
                    with self.assertRaises(OSError):
                        holder.cleanup()
            self.assertEqual(len(calls), holder.cleanup_attempts)
        finally:
            holder.cleanup()
        self.assertFalse(Path(holder.name).exists())


def resolve_plugin_component_path(plugin_root, declared):
    """Resolve a manifest component path the way the host does.

    The vendor manifest reference says every component path in a
    manifest is relative to the plugin root, must start with ./,
    must resolve inside the plugin root, and must exist, with a
    missing path reported as path not found and the component not
    loading. Returns the resolved Path, or None when the declared
    value breaks the rule, so the gate fails instead of reading
    a path the host will never load.
    """
    if not isinstance(declared, str) or not declared.startswith("./"):
        return None
    candidate = (plugin_root / declared[2:]).resolve()
    try:
        candidate.relative_to(plugin_root.resolve())
    except ValueError:
        return None
    return candidate


def style_frontmatter_problems(text):
    """Problems a host YAML reader would hit in the style frontmatter.

    The spelling pin beside this check guards the exact field name
    and its true value. This check guards that the block parses at
    all. A duplicate top level key, an unbalanced bracket, or a
    line that is not a key value pair means the host loads the
    style with no fields set, which silently switches force off,
    so each shape is named as its own problem.
    """
    problems = []
    if not text.startswith("---"):
        return ["the style has no frontmatter block"]
    try:
        end = text.index("---", 3)
    except ValueError:
        return ["the frontmatter block never closes"]
    front = text[3:end]
    seen = {}
    depth = {"[": 0, "{": 0, "(": 0}
    closers = {"]": "[", "}": "{", ")": "("}
    in_single = False
    in_double = False
    for lineno, line in enumerate(front.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line[0] not in (" ", "\t"):
            match = re.match(r"^([A-Za-z0-9_][A-Za-z0-9_.-]*)\s*:", line)
            if not match:
                problems.append(
                    "frontmatter line %d is not a key value pair"
                    % lineno
                )
            else:
                key = match.group(1)
                if key in seen:
                    problems.append(
                        "duplicate frontmatter key %r" % key
                    )
                seen[key] = lineno
        for char in line:
            if char == "'" and not in_double:
                in_single = not in_single
            elif char == '"' and not in_single:
                in_double = not in_double
            elif not in_single and not in_double:
                if char in depth:
                    depth[char] += 1
                elif char in closers:
                    opener = closers[char]
                    if depth[opener] == 0:
                        problems.append(
                            "unbalanced %r on frontmatter line %d"
                            % (char, lineno)
                        )
                    else:
                        depth[opener] -= 1
    for opener, count in depth.items():
        if count:
            problems.append(
                "unbalanced %r in the frontmatter block" % opener
            )
    return problems


def split_sentences(text):
    """Segment prose the way the style sentence check does."""
    pieces = []
    for piece in re.split(r"\.\s+|\n", text):
        cleaned = piece.lstrip("- ").strip()
        # A sentence at the very end of the text keeps its final
        # period, because no whitespace follows it for the split
        # to consume, so the one trailing period is normalized
        # away on both sides of the comparison.
        if cleaned.endswith("."):
            cleaned = cleaned[:-1].strip()
        if cleaned:
            pieces.append(re.sub(r"\s+", " ", cleaned))
    return pieces


class TestOutputStyle(unittest.TestCase):
    """The packet output style, Build 3 of the adaptation plan.

    The style is a second spelling of the packet the extractor
    writes. The gate pins its force field, its guarantee
    sentences, its heading list, and its manifest pointers, and
    fails any style sentence that is not a whole sentence the
    canonical skill text carries or a pinned derivation meta
    sentence. Manifest component paths are resolved the way the
    host resolves them, against the plugin root, never against
    a hardcoded directory prefix.
    """

    STYLE_REL = Path("output-styles") / "packet.md"

    # The derivation prose, pinned word for word. The derivation
    # is the one place the style may speak about enforcement, so
    # its prose is fixed and the sentence check lets these
    # sentences stand beside the canonical skill sentences.
    DERIVATION_PROSE = (
        "This style is a second spelling of the packet the extractor writes. "
        "Its only source is the tier model, workflow, completeness, trust, "
        "and stamping sections of `.agents/skills/recognitio/SKILL.md`. "
        "It adds no instruction the canonical text does not carry and moves "
        "no guarantee. Packet enforcement stays where decision 4 of "
        "`docs/decisions.md` puts it, in the shipped scripts and the skill "
        "workflow steps. When this style is inert, the prose packet enforces "
        "every guarantee unchanged."
    )

    def setUp(self):
        self.version = load_script("check_version")
        self.copy = load_script("check_copy")
        self.style_path = ROOT / self.STYLE_REL
        self.style_text = self.style_path.read_text(encoding="utf-8")
        self.skill_text = (
            ROOT / ".agents" / "skills" / "recognitio" / "SKILL.md"
        ).read_text(encoding="utf-8")

    def style_body(self):
        """The style without frontmatter, derivation, headings, or fences.

        The derivation prose is pinned word for word by its own
        test, because the no new instruction check must reach the
        one section the style is allowed to speak about
        enforcement in, and a prose pin is the strongest form of
        that reach.
        """
        text = self.style_text
        if text.startswith("---"):
            end = text.index("---", 3)
            text = text[end + 3 :]
        lines = text.splitlines()
        kept = []
        in_fence = False
        in_derivation = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            if stripped.startswith("## "):
                in_derivation = stripped == "## Derivation"
                continue
            if in_derivation or stripped.startswith("#"):
                continue
            kept.append(line)
        return "\n".join(kept)

    def derivation_body(self):
        """The derivation section prose, without its heading.

        The region runs to the next top level heading, matched
        at the line start, so a ### subheading planted inside
        the region cannot end the region early.
        """
        match = re.search(
            r"## Derivation\n(.*?)(?=\n## )", self.style_text, re.DOTALL
        )
        self.assertIsNotNone(match, "the style carries a Derivation section")
        lines = []
        in_fence = False
        for line in match.group(1).splitlines():
            stripped = line.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence or stripped.startswith("#"):
                continue
            lines.append(line)
        return "\n".join(lines)

    def canonical_sentences(self):
        """The canonical skill text segmented like the style."""
        lines = []
        in_fence = False
        for line in self.skill_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence or stripped.startswith("#"):
                continue
            lines.append(line)
        return set(split_sentences("\n".join(lines)))

    def _read_style_pointer_pair(self, root):
        plugin = self.version.strict_json_loads(
            (root / ".claude-plugin" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )
        market = self.version.strict_json_loads(
            (root / ".claude-plugin" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        entries = [
            p for p in market["plugins"] if p["name"] == "recognitio"
        ]
        self.assertEqual(len(entries), 1)
        return plugin, entries[0]

    def _assert_style_pointer_pin(self, root):
        plugin, entry = self._read_style_pointer_pair(root)
        self.assertEqual(
            plugin.get("outputStyles"), ["./output-styles/packet.md"]
        )
        self.assertEqual(
            entry.get("outputStyles"), ["./output-styles/packet.md"]
        )
        self.assertEqual(
            entry.get("outputStyles"), plugin.get("outputStyles")
        )
        resolved = resolve_plugin_component_path(
            root, entry.get("outputStyles")[0]
        )
        self.assertIsNotNone(
            resolved, "the declared style path resolves under the plugin root"
        )
        self.assertTrue(resolved.is_file(), resolved)

    def test_style_file_exists_where_the_manifests_declare_it(self):
        self._assert_style_pointer_pin(ROOT)

    def test_style_path_resolves_against_the_plugin_root(self):
        # The vendor manifest reference resolves every component
        # path against the plugin root. The declared value must
        # name the shipped file through that resolution, not
        # through a hardcoded directory prefix in the test.
        plugin, _ = self._read_style_pointer_pair(ROOT)
        declared = plugin["outputStyles"][0]
        resolved = resolve_plugin_component_path(ROOT, declared)
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved, self.style_path.resolve())
        # A declaration without the ./ prefix never resolves.
        self.assertIsNone(
            resolve_plugin_component_path(ROOT, "output-styles/packet.md")
        )
        # A declaration that escapes the plugin root never resolves.
        self.assertIsNone(
            resolve_plugin_component_path(ROOT, "./../outside/packet.md")
        )

    def test_an_entry_missing_the_style_pointer_fails_the_pin(self):
        # The defect is planted in real files on a scratch tree
        # and the real pin runs against them. An entry that drops
        # the outputStyles pointer must fail the pointer pin,
        # which is what the vacuous in memory test it replaces
        # never proved.
        with RetryingTemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin_dir = root / ".claude-plugin"
            plugin_dir.mkdir()
            (plugin_dir / "plugin.json").write_text(
                (ROOT / ".claude-plugin" / "plugin.json").read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8",
            )
            market = json.loads(
                (ROOT / ".claude-plugin" / "marketplace.json").read_text(
                    encoding="utf-8"
                )
            )
            del market["plugins"][0]["outputStyles"]
            (plugin_dir / "marketplace.json").write_text(
                json.dumps(market), encoding="utf-8"
            )
            with self.assertRaises(AssertionError):
                self._assert_style_pointer_pin(root)

    def test_the_old_layout_fails_the_vendor_resolution(self):
        # The R14-RT-05 shape, planted in a scratch tree. The
        # manifests declare ./output-styles/packet.md while the
        # file sits only under .claude-plugin/, so the vendor
        # resolution misses and the pin must fail. This is the
        # plant the old hardcoded test stayed green on.
        with RetryingTemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin_dir = root / ".claude-plugin"
            legacy = plugin_dir / "output-styles"
            legacy.mkdir(parents=True)
            (plugin_dir / "plugin.json").write_text(
                (ROOT / ".claude-plugin" / "plugin.json").read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8",
            )
            (plugin_dir / "marketplace.json").write_text(
                (ROOT / ".claude-plugin" / "marketplace.json").read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8",
            )
            (legacy / "packet.md").write_text(
                self.style_text, encoding="utf-8"
            )
            with self.assertRaises(AssertionError):
                self._assert_style_pointer_pin(root)

    def test_style_frontmatter_pins_force_for_plugin(self):
        text = self.style_text
        self.assertTrue(text.startswith("---"))
        front = text[3 : text.index("---", 3)]
        fields = {}
        for line in front.splitlines():
            line = line.strip()
            if line and ":" in line:
                key, value = line.split(":", 1)
                fields[key.strip()] = value.strip()
        # The host ignores a misspelled field in silence, so the
        # exact hyphenated spelling and its true value are pinned.
        self.assertEqual(fields.get("force-for-plugin"), "true")
        self.assertNotIn("force_for_plugin", fields)

    def test_style_frontmatter_is_host_readable(self):
        self.assertEqual(style_frontmatter_problems(self.style_text), [])

    def test_a_duplicate_frontmatter_key_is_a_readability_problem(self):
        planted = self.style_text.replace(
            "force-for-plugin: true",
            "force-for-plugin: false\nforce-for-plugin: true",
            1,
        )
        problems = style_frontmatter_problems(planted)
        self.assertTrue(
            any("duplicate" in problem for problem in problems), problems
        )

    def test_an_unbalanced_bracket_is_a_readability_problem(self):
        planted = self.style_text.replace(
            "A format only.", "A format only [draft.", 1
        )
        problems = style_frontmatter_problems(planted)
        self.assertTrue(
            any("unbalanced" in problem for problem in problems), problems
        )

    def test_style_guarantee_sentences_match_the_canonical_text(self):
        guarantees = [
            "Read the manifest the script writes and check that "
            "its verified flag is true before anything else happens.",
            "A review is stamped only on a verified packet.",
            "Never present a partial packet as a complete one.",
            "Never let a review begin on a packet whose verified "
            "flag is false.",
            "When verification fails, stop and say what is missing "
            "in plain words, naming the files or hunks that "
            "disagree.",
            "A verified packet proves the packet is complete.",
            "It does not prove the change is correct or safe.",
        ]
        for sentence in guarantees:
            self.assertIn(
                sentence, self.skill_text, sentence[:40]
            )
            self.assertIn(
                sentence, self.style_text, sentence[:40]
            )

    def test_style_headings_match_the_extractor(self):
        source = (
            ROOT
            / ".agents"
            / "skills"
            / "recognitio"
            / "scripts"
            / "extract.py"
        ).read_text(encoding="utf-8")
        shipped = re.findall(r'lines\.append\("## ([^"]+)"\)', source)
        self.assertTrue(shipped)
        fenced = re.search(
            r"```text\n(.*?)```", self.style_text, re.DOTALL
        )
        self.assertIsNotNone(fenced)
        declared = [
            line[3:]
            for line in fenced.group(1).splitlines()
            if line.startswith("## ")
        ]
        self.assertEqual(declared, shipped)

    def test_style_sentences_stand_in_the_canonical_text(self):
        sentences = split_sentences(self.style_body())
        self.assertTrue(sentences)
        canonical = self.canonical_sentences()
        for sentence in sentences:
            self.assertIn(sentence, canonical, sentence[:60])

    def test_style_derivation_is_the_pinned_prose(self):
        self.assertEqual(
            re.sub(r"\s+", " ", self.derivation_body()).strip(),
            self.DERIVATION_PROSE,
        )

    def test_style_references_no_external_urls(self):
        self.assertNotRegex(self.style_text, r"https?://")

    def test_style_claims_no_enforcement(self):
        # Enforcement lives in the scripts and the skill
        # workflow. The style may name that fact in its
        # derivation section and nowhere else. The region runs
        # to the next top level heading at the line start, so a
        # subheading planted inside it cannot end it early.
        derivation = re.search(
            r"## Derivation\n(.*?)(?=\n## )", self.style_text, re.DOTALL
        )
        self.assertIsNotNone(derivation)
        rest = self.style_text.replace(derivation.group(0), "")
        self.assertNotRegex(rest, r"(?i)enforce")

    def test_copy_fence_scans_the_style_file(self):
        found = self.copy.discover_prose_files(ROOT)
        self.assertIn(self.style_path, found)

    def test_a_banned_mark_in_the_style_fails_the_fence(self):
        with RetryingTemporaryDirectory() as tmp:
            path = Path(tmp) / "packet.md"
            path.write_text(
                self.style_text.replace(
                    "A format only.", "A format only \u2014 truly.", 1
                ),
                encoding="utf-8",
            )
            violations = []
            self.copy.scan(violations, path, self.copy.prose_lines(path))
            self.assertTrue(
                any("packet.md" in violation for violation in violations),
                violations,
            )

    def test_a_style_pointer_with_strict_false_is_a_conflict(self):
        plugin_text = (
            ROOT / ".claude-plugin" / "plugin.json"
        ).read_text(encoding="utf-8")
        market = json.loads(
            (ROOT / ".claude-plugin" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        market["plugins"][0]["strict"] = False
        problems = self.version.manifest_conflict_problems(
            plugin_text, json.dumps(market)
        )
        self.assertTrue(
            any("outputStyles" in problem for problem in problems),
            problems,
        )

    def test_split_sentences_pins_a_known_fixture(self):
        # R16-ST-01. The style sentence check runs both sides of
        # its comparison through this one helper, so a bug in the
        # helper would shift both sides together and stay
        # invisible to the check. This test pins the helper
        # itself against a fixture whose sentence boundaries were
        # read by a human, so a segmentation bug fails here even
        # when the comparison check stays green. The
        # counterweight the round 16 standards lane recorded
        # stands beside it. The round 14 adversarial pass planted
        # real defects against the check, so the check is
        # exercised by plants rather than trusted by
        # construction.
        fixture = (
            "First sentence. Second sentence.\n"
            "- A bullet sentence.\n"
            "A sentence  with   wide spacing.\n"
            "A sentence at the very end."
        )
        self.assertEqual(
            split_sentences(fixture),
            [
                "First sentence",
                "Second sentence",
                "A bullet sentence",
                "A sentence with wide spacing",
                "A sentence at the very end",
            ],
        )


class TestPersonaBuild(unittest.TestCase):
    """Build 5, the plugin reviewer persona as the main thread.

    The plugin ships the reviewer agent file at
    agents/reviewer.md, declares it under the `agents` key of
    the plugin manifest, and names it as the session agent
    under the manifest `settings` key. The gate script pins
    the manifest keys and the agent frontmatter field by
    field, and the sentence discipline that guards the output
    style prose reaches the persona prose. These tests run
    the round 16 red team plant against the pins. A widened
    `tools` allowlist beside prose claiming free push rights
    stayed green at 308 tests, and it must fail here.
    """

    PERSONA_REL = Path("agents") / "reviewer.md"

    # The persona prose, pinned word for word. The persona
    # carries no instruction the canonical skill text does not
    # carry, apart from this block, which states the persona
    # side bound of R16-SF-01. The precedence rules stay out
    # of the persona prose and live in docs/reviewer-persona.md
    # as host behavior.
    PERSONA_PROSE = (
        "This persona changes the voice and posture of the session, "
        "not its tool access. It declares no tool allowlist and no "
        "permission mode, so it cannot widen what the session may do."
    )

    def setUp(self):
        self.persona = load_script("check_persona")
        self.agent_text = (
            ROOT / self.PERSONA_REL
        ).read_text(encoding="utf-8")
        self.skill_text = (
            ROOT / ".agents" / "skills" / "recognitio" / "SKILL.md"
        ).read_text(encoding="utf-8")

    def make_tree(self, tmp, agent_text=None, manifest=None):
        root = Path(tmp) / "root"
        plugin_dir = root / ".claude-plugin"
        plugin_dir.mkdir(parents=True)
        agent_dir = root / "agents"
        agent_dir.mkdir(parents=True)
        (agent_dir / "reviewer.md").write_text(
            self.agent_text if agent_text is None else agent_text,
            encoding="utf-8",
        )
        if manifest is None:
            manifest = {
                "name": "recognitio",
                "agents": ["./agents/reviewer.md"],
                "settings": {"agent": "reviewer"},
                "version": "1.3.0",
            }
        (plugin_dir / "plugin.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        return root

    def frontmatter_insert(self, text, line):
        head, _, rest = text.partition("---\n")
        front, sep, body = rest.partition("---")
        self.assertTrue(sep, "the agent text carries frontmatter")
        return head + "---\n" + front + line + "\n" + sep + body

    def persona_body(self, text):
        """The persona without frontmatter, headings, or fences."""
        if text.startswith("---"):
            end = text.index("---", 3)
            text = text[end + 3 :]
        kept = []
        in_fence = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence or stripped.startswith("#"):
                continue
            kept.append(line)
        return "\n".join(kept)

    def canonical_sentences(self):
        """The canonical skill text segmented like the persona."""
        lines = []
        in_fence = False
        for line in self.skill_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence or stripped.startswith("#"):
                continue
            lines.append(line)
        return set(split_sentences("\n".join(lines)))

    def foreign_sentences(self, agent_text):
        """Persona sentences outside the canonical set and the pin."""
        sentences = split_sentences(self.persona_body(agent_text))
        canonical = self.canonical_sentences()
        pinned = set(split_sentences(self.PERSONA_PROSE))
        return [
            sentence
            for sentence in sentences
            if sentence not in canonical and sentence not in pinned
        ]

    def test_the_shipped_persona_passes_the_gate_script(self):
        self.assertEqual(self.persona.persona_problems(ROOT), [])

    def test_a_widened_tools_allowlist_fails_the_pin(self):
        # R16-RT-01, the script half of the red team plant. The
        # plant declared a tools allowlist of Bash, Write, Edit,
        # WebFetch and Task beside prose claiming free push
        # rights, and the full gate stayed green. The pin must
        # name the widening.
        planted = self.frontmatter_insert(
            self.agent_text, "tools: Bash, Write, Edit, WebFetch, Task"
        )
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp, agent_text=planted)
            problems = self.persona.persona_problems(root)
        self.assertTrue(
            any(
                "tools" in problem and "must never carry" in problem
                for problem in problems
            ),
            problems,
        )

    def test_free_push_prose_fails_the_sentence_discipline(self):
        # R16-RT-01, the prose half of the red team plant. The
        # persona may carry no sentence the canonical skill text
        # does not carry beside the pinned persona prose, so the
        # planted claim fails the discipline.
        planted = self.agent_text + (
            "\nYou may push fixes freely whenever the review asks.\n"
        )
        foreign = self.foreign_sentences(planted)
        self.assertEqual(len(foreign), 1, foreign)
        self.assertIn("push fixes freely", foreign[0])

    def test_the_shipped_persona_prose_passes_the_discipline(self):
        self.assertEqual(self.foreign_sentences(self.agent_text), [])

    def test_the_pinned_persona_prose_is_word_for_word(self):
        normalized = re.sub(r"\s+", " ", self.agent_text)
        self.assertIn(self.PERSONA_PROSE, normalized)

    def test_a_bypass_permission_mode_is_forbidden(self):
        # Defense in depth. The host ignores permissionMode on
        # plugin agents, but a shipped bypass declaration must
        # still fail, because a host that honored it would hand
        # the persona the widest tool access.
        planted = self.frontmatter_insert(
            self.agent_text, "permissionMode: bypassPermissions"
        )
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp, agent_text=planted)
            problems = self.persona.persona_problems(root)
        self.assertTrue(
            any("permissionMode" in problem for problem in problems),
            problems,
        )

    def test_each_ignored_host_field_is_forbidden(self):
        for key in ("hooks", "mcpServers", "initialPrompt"):
            planted = self.frontmatter_insert(
                self.agent_text, "%s: {}" % key
            )
            with RetryingTemporaryDirectory() as tmp:
                root = self.make_tree(tmp, agent_text=planted)
                problems = self.persona.persona_problems(root)
            self.assertTrue(
                any(key in problem for problem in problems),
                (key, problems),
            )

    def test_an_unknown_frontmatter_key_fails(self):
        planted = self.frontmatter_insert(
            self.agent_text, "systemPrompt: be nice"
        )
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp, agent_text=planted)
            problems = self.persona.persona_problems(root)
        self.assertTrue(
            any("systemPrompt" in problem for problem in problems),
            problems,
        )

    def test_a_non_worktree_isolation_fails(self):
        planted = self.frontmatter_insert(
            self.agent_text, "isolation: container"
        )
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp, agent_text=planted)
            problems = self.persona.persona_problems(root)
        self.assertTrue(
            any("isolation" in problem for problem in problems),
            problems,
        )

    def test_a_worktree_isolation_passes(self):
        planted = self.frontmatter_insert(
            self.agent_text, "isolation: worktree"
        )
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp, agent_text=planted)
            problems = self.persona.persona_problems(root)
        self.assertEqual(problems, [], problems)

    def test_a_bad_effort_fails(self):
        planted = self.frontmatter_insert(
            self.agent_text, "effort: extreme"
        )
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp, agent_text=planted)
            problems = self.persona.persona_problems(root)
        self.assertTrue(
            any("effort" in problem for problem in problems), problems
        )

    def test_a_non_positive_max_turns_fails(self):
        for value in ("0", "-3", "many"):
            planted = self.frontmatter_insert(
                self.agent_text, "maxTurns: %s" % value
            )
            with RetryingTemporaryDirectory() as tmp:
                root = self.make_tree(tmp, agent_text=planted)
                problems = self.persona.persona_problems(root)
            self.assertTrue(
                any("maxTurns" in problem for problem in problems),
                (value, problems),
            )

    def test_a_malformed_disallowed_tools_fails(self):
        planted = self.frontmatter_insert(
            self.agent_text, "disallowedTools: Bash"
        )
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp, agent_text=planted)
            problems = self.persona.persona_problems(root)
        self.assertTrue(
            any("disallowedTools" in problem for problem in problems),
            problems,
        )

    def test_a_well_formed_disallowed_tools_passes(self):
        planted = self.frontmatter_insert(
            self.agent_text, 'disallowedTools: ["Bash", "Write"]'
        )
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp, agent_text=planted)
            problems = self.persona.persona_problems(root)
        self.assertEqual(problems, [], problems)

    def test_a_duplicate_frontmatter_key_fails(self):
        planted = self.agent_text.replace(
            "name: reviewer",
            "name: reviewer\nname: reviewer",
            1,
        )
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp, agent_text=planted)
            problems = self.persona.persona_problems(root)
        self.assertTrue(
            any("duplicate" in problem for problem in problems),
            problems,
        )

    def test_an_unclosed_frontmatter_fails(self):
        planted = self.agent_text.replace("---\n", "", 1)
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp, agent_text=planted)
            problems = self.persona.persona_problems(root)
        self.assertTrue(problems, "expected a frontmatter problem")

    def test_a_renamed_agent_fails_the_pin(self):
        planted = self.agent_text.replace(
            "name: reviewer", "name: auditor", 1
        )
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp, agent_text=planted)
            problems = self.persona.persona_problems(root)
        self.assertTrue(
            any("reviewer" in problem for problem in problems),
            problems,
        )

    def test_settings_with_an_extra_key_fails(self):
        manifest = {
            "name": "recognitio",
            "agents": ["./agents/reviewer.md"],
            "settings": {"agent": "reviewer", "theme": "dark"},
            "version": "1.3.0",
        }
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp, manifest=manifest)
            problems = self.persona.persona_problems(root)
        self.assertTrue(
            any("theme" in problem for problem in problems), problems
        )

    def test_settings_naming_another_agent_fails(self):
        manifest = {
            "name": "recognitio",
            "agents": ["./agents/reviewer.md"],
            "settings": {"agent": "auditor"},
            "version": "1.3.0",
        }
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp, manifest=manifest)
            problems = self.persona.persona_problems(root)
        self.assertTrue(
            any("auditor" in problem for problem in problems), problems
        )

    def test_a_missing_agents_key_fails(self):
        manifest = {
            "name": "recognitio",
            "settings": {"agent": "reviewer"},
            "version": "1.3.0",
        }
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp, manifest=manifest)
            problems = self.persona.persona_problems(root)
        self.assertTrue(
            any("agents" in problem for problem in problems), problems
        )

    def test_an_agent_path_pointing_at_a_missing_file_fails(self):
        manifest = {
            "name": "recognitio",
            "agents": ["./agents/missing.md"],
            "settings": {"agent": "reviewer"},
            "version": "1.3.0",
        }
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp, manifest=manifest)
            problems = self.persona.persona_problems(root)
        self.assertTrue(problems, "expected a resolution problem")

    def test_an_agent_path_escaping_the_plugin_root_fails(self):
        manifest = {
            "name": "recognitio",
            "agents": ["./../outside/reviewer.md"],
            "settings": {"agent": "reviewer"},
            "version": "1.3.0",
        }
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp, manifest=manifest)
            problems = self.persona.persona_problems(root)
        self.assertTrue(problems, "expected a resolution problem")

    def test_persona_frontmatter_is_host_readable(self):
        self.assertEqual(
            style_frontmatter_problems(self.agent_text), []
        )

    def test_the_copy_fence_scans_the_persona_file(self):
        copy_mod = load_script("check_copy")
        found = copy_mod.discover_prose_files(ROOT)
        self.assertIn(ROOT / self.PERSONA_REL, found)
        self.assertIn(ROOT / "docs" / "reviewer-persona.md", found)


if __name__ == "__main__":
    unittest.main()
