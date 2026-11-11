import ast
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import unittest
import zlib
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


def load_script_at(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# The git location variables are scrubbed from the environment
# every fixture command runs under. An exported GIT_DIR defeats
# git -C, so a suite launched with the variables set would run
# its fixture work in the repository they name instead of in
# the fixture, writing real commits there under passing tests.
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

def git(repo, *args):
    result = subprocess.run(
        ["git", "-C", str(repo)] + list(args),
        env=scrubbed_git_env(),
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

    def run_main_on(self, files, comment_files=(), manifest_files=None):
        # The error stream is kept on self.last_stderr rather
        # than discarded, so a test that plants a defect can
        # assert the failure names the planted surface instead
        # of holding only the exit code. The three surface
        # lists are handed to the gate main explicitly, the
        # injection shape the Round 14 repair gave it, and no
        # module level list is patched. A caller that names
        # no manifest list hands an empty one, because the
        # shipped manifests are not the surface under test
        # in the tests that use this helper.
        if manifest_files is None:
            manifest_files = []
        err = io.StringIO()
        with redirect_stderr(err):
            code = self.mod.main(
                prose_files=list(files),
                comment_files=list(comment_files),
                manifest_files=list(manifest_files),
            )
        self.last_stderr = err.getvalue()
        return code

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
            self.assertIn("has an em dash", self.last_stderr)
            self.assertIn("config.yml", self.last_stderr)

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
            self.assertIn("has an em dash", self.last_stderr)
            self.assertIn("ci.yml", self.last_stderr)

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
            self.assertIn("has an em dash", self.last_stderr)
            self.assertIn("Makefile", self.last_stderr)

    def test_em_dash_in_a_gitignore_comment_is_caught(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, ".gitignore",
                "# Extractor output %s working papers.\n"
                "packet/\n" % EM_DASH,
            )
            self.assertEqual(self.run_main_on([], [path]), 1)
            self.assertIn("has an em dash", self.last_stderr)
            self.assertIn(".gitignore", self.last_stderr)

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
            self.assertIn("has an em dash", self.last_stderr)
            self.assertIn("dependabot.yml", self.last_stderr)

    def test_em_dash_beside_a_url_is_still_caught(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "page.md",
                "See https://example.com/spec for the plan %s truly.\n"
                % EM_DASH,
            )
            self.assertEqual(self.run_main_on([path]), 1)
            self.assertIn("has an em dash", self.last_stderr)

    def test_semicolon_right_after_a_markdown_link_is_caught(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "page.md",
                "See [guide](https://example.com/spec); then continue.\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)
            self.assertIn("has a semicolon", self.last_stderr)

    def test_colon_right_after_a_markdown_link_is_caught(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "page.md",
                "See [guide](https://example.com/spec): then continue.\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)
            self.assertIn("has a colon in prose", self.last_stderr)

    def test_a_picture_tag_line_is_markup_not_prose(self):
        # Visual round 8. The README wordmark stood in a
        # picture element whose source lines carry a media
        # attribute value with a colon inside it, and the
        # fence learned from that landing to read a line
        # holding one HTML tag and nothing else as markup,
        # so the attribute syntax is not judged as prose.
        # The wordmark has since moved to the theme fragment
        # pair and the tag lines of both hero shapes stand
        # in the same class.
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "page.md",
                "<p align=\"center\">\n"
                "  <picture>\n"
                "    <source media=\"(prefers-color-scheme: dark)\" "
                "srcset=\"docs/brand/wordmark-dark.svg\">\n"
                "    <img alt=\"recognitio\" "
                "src=\"docs/brand/wordmark-light.svg\" width=\"300\">\n"
                "  </picture>\n"
                "</p>\n"
                "\n"
                "Clean prose stands under the markup.\n",
            )
            self.assertEqual(self.run_main_on([path]), 0)

    def test_prose_beside_a_tag_on_one_line_still_fails(self):
        # The tag line exemption is narrow. Prose sharing
        # a line with a tag is still prose and a banned
        # mark inside it still fails the bar.
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "page.md",
                "<p>Words in prose: with a colon beside a tag.</p>\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)
            self.assertIn("has a colon in prose", self.last_stderr)

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
            self.assertIn("has an em dash", self.last_stderr)
            self.assertIn("CLAUDE.md", self.last_stderr)

    def test_yaml_block_scalar_prose_is_scanned(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "reviews:\n  instructions: |\n"
                "    Be direct %s always.\n" % EM_DASH,
            )
            self.assertEqual(self.run_main_on([path]), 1)
            self.assertIn("has an em dash", self.last_stderr)

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
        # Round 9 spec Minor 1. The completeness reading above
        # shares the exclusion predicate with the discovery it
        # measures, so a file the predicate wrongly excludes is
        # invisible on both sides and this pair can stand while
        # a prose file escapes the fence. The public directory
        # set the predicate is built on is pinned here as a
        # literal, and the covered count stands under a floor
        # counted on the Round 9 tree, so dropping an entry
        # from the set or silently excluding a covered file
        # breaks one of these two pins by name.
        self.assertEqual(
            self.mod._PUBLIC_DOT_DIRS,
            (".github", ".agents", ".claude", ".claude-plugin",
             ".cursor", ".cursor-plugin", ".antigravity",
             ".zcode-plugin"),
        )
        self.assertGreaterEqual(
            len(covered), 77,
            "the copy fence covers fewer prose files than the "
            "77 the Round 9 tree holds, so a covered file left "
            "the fence silently",
        )
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
             "plugins/recognitio-mod/.claude-plugin/plugin.json",
             ".cursor-plugin/plugin.json",
             ".cursor-plugin/marketplace.json",
             ".antigravity/plugin.json",
             ".zcode-plugin/plugin.json",
             ".agents/plugins/marketplace.json",
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

    def test_discovery_keeps_the_example_packet_out_only(self):
        # WP2. The packet saved under examples is extractor
        # output shipped for reading without an install, so it
        # stays out by the generated packet rule, while the
        # authored note in the same folder stays inside.
        with RetryingTemporaryDirectory() as tmp:
            root = Path(tmp)
            packet_dir = root / "examples" / "example-packet-991ac6a"
            packet_dir.mkdir(parents=True)
            (packet_dir / "packet.md").write_text(
                "Mode: commit\n", encoding="utf-8"
            )
            note = root / "examples" / "README.md"
            note.write_text("An authored note.\n", encoding="utf-8")
            found = {
                str(p.relative_to(root))
                for p in self.mod.discover_prose_files(root)
            }
            self.assertNotIn(
                "examples/example-packet-991ac6a/packet.md", found
            )
            self.assertIn("examples/README.md", found)

    def test_discovery_keeps_the_proof_run_packet_out_only(self):
        # The proof run packet is extractor output shipped as
        # the record a fan out run stands on, so it stays out by
        # the generated packet rule, while the authored readme in
        # the same folder stays inside the fence.
        with RetryingTemporaryDirectory() as tmp:
            root = Path(tmp)
            proof = root / "workflows" / "proof-run"
            proof.mkdir(parents=True)
            (proof / "packet.md").write_text(
                "Mode: range\n", encoding="utf-8"
            )
            (proof / "README.md").write_text(
                "An authored note.\n", encoding="utf-8"
            )
            found = {
                str(p.relative_to(root))
                for p in self.mod.discover_prose_files(root)
            }
            self.assertNotIn("workflows/proof-run/packet.md", found)
            self.assertIn("workflows/proof-run/README.md", found)

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
            self.assertIn("has an em dash", self.last_stderr)
            self.assertIn("feature_form.yml", self.last_stderr)

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
            code = self.run_main_on(
                [], manifest_files=[path]
            )
            self.assertEqual(code, 1)
            self.assertIn(
                "description field has an em dash", self.last_stderr
            )

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
            self.assertIn("has an em dash", self.last_stderr)
            self.assertIn("README.md", self.last_stderr)

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
            self.assertIn("has an em dash", self.last_stderr)
            self.assertIn("recognitio.mdc", self.last_stderr)

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
            code = self.run_main_on(
                [], manifest_files=[manifest]
            )
            self.assertEqual(code, 1)
            self.assertIn(
                "description field has an em dash", self.last_stderr
            )

    def test_em_dash_in_antigravity_plugin_manifest_is_caught(self):
        # R38-ST-01. The Antigravity plugin manifest
        # description is public prose, so an em dash in it
        # fails the gate. The manifest joins the fence
        # through the public directory list the shared
        # exclusion rule reads.
        with RetryingTemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self.write_tmp(
                root,
                ".antigravity/plugin.json",
                '{"name": "x", "description": "Does a thing %s '
                'in plain words."}\n' % EM_DASH,
            )
            found = self.mod.discover_manifest_files(root)
            self.assertIn(manifest, found)
            code = self.run_main_on(
                [], manifest_files=[manifest]
            )
            self.assertEqual(code, 1)
            self.assertIn(
                "description field has an em dash", self.last_stderr
            )

    def test_em_dash_in_zcode_plugin_manifest_is_caught(self):
        # R38-ST-01. The ZCode plugin manifest description
        # is public prose of the same kind, so an em dash
        # in it fails the gate the same way.
        with RetryingTemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self.write_tmp(
                root,
                ".zcode-plugin/plugin.json",
                '{"name": "x", "description": "Does a thing %s '
                'in plain words."}\n' % EM_DASH,
            )
            found = self.mod.discover_manifest_files(root)
            self.assertIn(manifest, found)
            code = self.run_main_on(
                [], manifest_files=[manifest]
            )
            self.assertEqual(code, 1)
            self.assertIn(
                "description field has an em dash", self.last_stderr
            )

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
            self.assertIn("has a colon in prose", self.last_stderr)

    def test_a_colon_inside_a_list_item_flow_mapping_still_flags(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "items:\n"
                "  - {label: \"Read: now\"}\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)
            self.assertIn("has a colon in prose", self.last_stderr)

    def test_a_prose_mapping_value_with_a_colon_still_flags(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "note: see the guide for details: the long version\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)
            self.assertIn("has a colon in prose", self.last_stderr)

    def test_a_prose_value_in_a_nested_sequence_still_flags(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "items:\n"
                "  - - name: alpha: the first one\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)
            self.assertIn("has a colon in prose", self.last_stderr)

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
                self.assertIn(
                    "has a colon in prose", self.last_stderr, text
                )

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
                self.assertIn(
                    "has a colon in prose", self.last_stderr, text
                )

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
            self.assertIn("has a colon in prose", self.last_stderr)

    def test_text_after_a_flow_collection_still_flags(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "ports: [80, 443] # Open: web\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)
            self.assertIn("has a colon in prose", self.last_stderr)
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
                self.assertIn(
                    "has a colon in prose", self.last_stderr, text
                )

    def test_a_key_shaped_continuation_of_a_plain_scalar_still_flags(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "description: Long prose starts\n"
                "  Summary: only colon is here\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)
            self.assertIn("has a colon in prose", self.last_stderr)

    def test_a_key_shaped_line_inside_a_flow_quoted_scalar_still_flags(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "point: {label: \"Read\n"
                "  now: the sequel\"}\n",
            )
            self.assertEqual(self.run_main_on([path]), 1)
            self.assertIn("has a colon in prose", self.last_stderr)

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
            self.assertIn("has a colon in prose", self.last_stderr)

    def test_yaml_keys_and_directives_are_syntax(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "config.yaml",
                "# yaml-language-server: $schema=https://example.com/s.json\n"
                "language: \"en-US\"\n"
                "tone: \"Be direct and plain.\"\n",
            )
            self.assertEqual(self.run_main_on([path]), 0)

    def test_a_banned_mark_in_a_long_description_is_caught(self):
        # Round 4 spec Major 1, in the seat probe shape. The
        # portable manifest carries its prose under keys the
        # scan once never read, so a banned mark there passed
        # the whole gate unseen.
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "plugin.json",
                '{"name": "x", "longDescription": "Does a thing '
                '%s in plain words."}\n' % EM_DASH,
            )
            code = self.run_main_on([], manifest_files=[path])
            self.assertEqual(code, 1)
            self.assertIn(
                "longDescription field has an em dash",
                self.last_stderr,
            )

    def test_a_banned_mark_in_a_short_description_is_caught(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "plugin.json",
                '{"name": "x", "shortDescription": "Does a thing; '
                'in plain words."}\n',
            )
            code = self.run_main_on([], manifest_files=[path])
            self.assertEqual(code, 1)
            self.assertIn(
                "shortDescription field has a semicolon",
                self.last_stderr,
            )

    def test_a_banned_mark_in_a_note_field_is_caught(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "plugin.json",
                '{"name": "x", "note": "Does a thing: in plain '
                'words."}\n',
            )
            code = self.run_main_on([], manifest_files=[path])
            self.assertEqual(code, 1)
            self.assertIn(
                "note field has a colon in prose", self.last_stderr
            )

    def test_a_banned_mark_in_a_list_valued_description_is_caught(self):
        # The storefront finalization repair. A prose key
        # holding a list of strings once escaped collection
        # whole, because collection required a string value
        # and the recursion dropped the bare strings inside
        # the list, so a description carried as a list passed
        # the gate unseen.
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "plugin.json",
                '{"name": "x", "description": ["Does a thing in '
                'plain words.", "And a second part; in plain '
                'words."]}\n',
            )
            code = self.run_main_on([], manifest_files=[path])
            self.assertEqual(code, 1)
            self.assertIn(
                "description field has a semicolon",
                self.last_stderr,
            )

    def test_a_banned_mark_in_a_list_valued_note_is_caught(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "plugin.json",
                '{"name": "x", "note": ["Does a thing %s in '
                'plain words."]}\n' % EM_DASH,
            )
            code = self.run_main_on([], manifest_files=[path])
            self.assertEqual(code, 1)
            self.assertIn(
                "note field has an em dash", self.last_stderr
            )

    def test_a_clean_list_valued_description_passes(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "plugin.json",
                '{"name": "x", "description": ["Does a thing in '
                'plain words.", "And a second part in plain '
                'words."]}\n',
            )
            code = self.run_main_on([], manifest_files=[path])
            self.assertEqual(code, 0, self.last_stderr)

    def test_a_banned_mark_in_a_nested_list_is_caught(self):
        # The repair review's plant. A list inside the list
        # a prose key holds once escaped the list repair one
        # level down, because the items of the outer list
        # were passed back through a reading that returns
        # nothing for a bare string, so the strings inside
        # the inner list fell out of the collection unseen.
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "plugin.json",
                '{"name": "x", "description": [["Does a thing; '
                'in plain words."]]}\n',
            )
            code = self.run_main_on([], manifest_files=[path])
            self.assertEqual(code, 1)
            self.assertIn(
                "description field has a semicolon",
                self.last_stderr,
            )

    def test_nested_frontmatter_keys_are_syntax(self):
        # The storefront finalization repair. The DESIGN.md
        # format nests its front matter keys one and two
        # levels down, and the key pattern once anchored at
        # column zero, so every nested key line was judged
        # as prose and its key colon flagged, 52 violations
        # on the adopted file and every one a key colon.
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "DESIGN.md",
                "---\n"
                "version: alpha\n"
                "name: Product storefront\n"
                "colors:\n"
                "  ground: \"#ffffff\"\n"
                "  panel: \"#f6f8fa\"\n"
                "typography:\n"
                "  display:\n"
                "    fontSize: \"2rem\"\n"
                "---\n"
                "\n"
                "# Product storefront\n"
                "\n"
                "Clean prose stands here.\n",
            )
            code = self.run_main_on([path])
            self.assertEqual(code, 0, self.last_stderr)

    def test_a_banned_mark_in_a_nested_frontmatter_value_is_caught(self):
        # The other direction of the same repair. A nested
        # key is syntax at any depth, and its value stays
        # prose under the bar.
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "DESIGN.md",
                "---\n"
                "version: alpha\n"
                "colors:\n"
                "  ground: \"a bad; ground\"\n"
                "---\n"
                "\n"
                "Clean prose stands here.\n",
            )
            code = self.run_main_on([path])
            self.assertEqual(code, 1)
            self.assertIn("has a semicolon", self.last_stderr)

    def test_a_missing_readme_fails_the_gate_itself(self):
        # Round 4 audit Minor 4 and red team Minor 3. Deleting
        # README.md once left the gate green over the prose
        # that remained. The gate now refuses by name when a
        # required surface is absent, run here as the gate
        # itself inside a scratch tree rather than through
        # the suite helpers.
        with RetryingTemporaryDirectory() as tmp:
            root = Path(tmp) / "tree"
            script_dir = root / "scripts"
            script_dir.mkdir(parents=True)
            shutil.copyfile(
                ROOT / "scripts" / "check_copy.py",
                script_dir / "check_copy.py",
            )
            (root / "docs").mkdir()
            (root / "docs" / "page.md").write_text(
                "Clean prose stands here.\n", encoding="utf-8"
            )
            mod = load_script_at(
                script_dir / "check_copy.py", "copy_gate_no_readme"
            )
            err = io.StringIO()
            with redirect_stderr(err):
                code = mod.main()
            self.assertEqual(code, 1)
            self.assertIn("README.md is missing", err.getvalue())

    def test_an_empty_census_fails_the_gate_itself(self):
        with RetryingTemporaryDirectory() as tmp:
            root = Path(tmp) / "tree"
            script_dir = root / "scripts"
            script_dir.mkdir(parents=True)
            shutil.copyfile(
                ROOT / "scripts" / "check_copy.py",
                script_dir / "check_copy.py",
            )
            mod = load_script_at(
                script_dir / "check_copy.py", "copy_gate_empty"
            )
            err = io.StringIO()
            with redirect_stderr(err):
                code = mod.main()
            self.assertEqual(code, 1)
            self.assertIn("census stands at zero", err.getvalue())

    def test_a_broken_relative_link_is_caught(self):
        # Round 4 red team Minor 2, in the seat plant shape.
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "page.md",
                "Clean words stand here.\n"
                "\n"
                "See [the missing guide](missing-guide-zzz.md) "
                "for the rest.\n",
            )
            code = self.run_main_on([path])
            self.assertEqual(code, 1)
            self.assertIn("missing-guide-zzz.md", self.last_stderr)
            self.assertIn("does not stand in the tree", self.last_stderr)

    def test_a_relative_link_to_a_standing_file_passes(self):
        with RetryingTemporaryDirectory() as tmp:
            target = self.write_tmp(
                tmp, "other.md", "The other page.\n"
            )
            path = self.write_tmp(
                tmp, "page.md",
                "See [the other page](other.md) for the rest.\n",
            )
            code = self.run_main_on([path, target])
            self.assertEqual(code, 0, self.last_stderr)

    def test_a_split_link_to_a_missing_file_is_caught(self):
        # Round 4 red team Minor 2, second shape. The
        # destination stands on the line after the opening
        # bracket, and the grammar reads it as one link, so
        # the gate reads it as one link and reports the
        # line where the link opens.
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "page.md",
                "Clean words stand here.\n"
                "\n"
                "See [the missing guide](\n"
                "missing-split-zzz.md) for the rest.\n",
            )
            code = self.run_main_on([path])
            self.assertEqual(code, 1)
            self.assertIn("missing-split-zzz.md", self.last_stderr)
            self.assertIn(
                "does not stand in the tree", self.last_stderr
            )
            self.assertIn("line 3", self.last_stderr)

    def test_a_split_link_to_a_standing_file_passes(self):
        with RetryingTemporaryDirectory() as tmp:
            target = self.write_tmp(
                tmp, "other.md", "The other page.\n"
            )
            path = self.write_tmp(
                tmp, "page.md",
                "See [the other page](\n"
                "other.md) for the rest.\n",
            )
            code = self.run_main_on([path, target])
            self.assertEqual(code, 0, self.last_stderr)

    def test_an_html_href_to_a_missing_file_is_caught(self):
        # Round 4 red team Minor 2, third shape. An anchor
        # element href is the HTML form of the same reader
        # facing reference inside a prose page.
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "page.md",
                "Clean words stand here.\n"
                "\n"
                '<a href="missing-html-zzz.md">A guide</a>\n',
            )
            code = self.run_main_on([path])
            self.assertEqual(code, 1)
            self.assertIn("missing-html-zzz.md", self.last_stderr)
            self.assertIn(
                "does not stand in the tree", self.last_stderr
            )
            self.assertIn("line 3", self.last_stderr)

    def test_an_external_html_href_passes(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "page.md",
                '<a href="https://example.com/guide">A guide</a>\n',
            )
            code = self.run_main_on([path])
            self.assertEqual(code, 0, self.last_stderr)

    def test_a_banned_mark_in_a_default_prompt_is_caught(self):
        # Round 4 red team Note 4. The default prompt list
        # of the OpenAI interface object is prose a listing
        # reader meets, in a list of strings rather than
        # one string.
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "plugin.json",
                '{"name": "x", "interface": {"defaultPrompt": '
                '["Does a thing %s in plain words.", '
                '"A clean prompt."]}}\n' % EM_DASH,
            )
            code = self.run_main_on([], manifest_files=[path])
            self.assertEqual(code, 1)
            self.assertIn(
                "defaultPrompt field has an em dash",
                self.last_stderr,
            )

    def test_a_clean_default_prompt_list_passes(self):
        with RetryingTemporaryDirectory() as tmp:
            path = self.write_tmp(
                tmp, "plugin.json",
                '{"name": "x", "interface": {"defaultPrompt": '
                '["Does a thing in plain words."]}}\n',
            )
            code = self.run_main_on([], manifest_files=[path])
            self.assertEqual(code, 0, self.last_stderr)

    def test_an_undecodable_prose_file_is_named(self):
        with RetryingTemporaryDirectory() as tmp:
            path = Path(tmp) / "page.md"
            path.write_bytes(b"\xff\xfe\x00bad")
            code = self.run_main_on([path])
            self.assertEqual(code, 1)
            self.assertIn(
                "cannot be read as UTF-8 text", self.last_stderr
            )

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
                    "ceiling this test records for the functions "
                    "of scripts/check_copy.py alone"
                    % (node.name, length),
                )


class TestUndecodableGateInputs(unittest.TestCase):
    """Undecodable files draw a named problem, never a traceback.

    Round 4 standards Minor 3. The read_text copies across
    the gates caught the OS error and let the decode error
    escape, so one byte damaged input file crashed the gate
    that read it instead of failing in the family voice.
    Every copy now behaves the same way over the same bytes.
    """

    SINGLE_PATH_GATES = (
        "check_antigravity",
        "check_brand",
        "check_coderabbit",
        "check_copilot",
        "check_cursor",
        "check_devin",
        "check_kimi",
        "check_qwen",
        "check_zcode",
    )

    def test_every_read_text_copy_returns_none_on_bad_bytes(self):
        with RetryingTemporaryDirectory() as tmp:
            path = Path(tmp) / "damaged.md"
            path.write_bytes(b"\xff\xfe\x00bad")
            for name in self.SINGLE_PATH_GATES:
                mod = load_script(name)
                self.assertIsNone(mod.read_text(path), name)
                self.assertTrue(
                    any(
                        "damaged.md" in p
                        and "cannot be read as UTF-8 text" in p
                        for p in mod.utf8_problems()
                    ),
                    (name, mod.utf8_problems()),
                )
            version = load_script("check_version")
            self.assertIsNone(version.read(path))
            self.assertTrue(
                any(
                    "damaged.md" in p
                    and "cannot be read as UTF-8 text" in p
                    for p in version.utf8_problems()
                ),
                version.utf8_problems(),
            )

    def test_every_read_text_copy_records_nothing_on_absent(self):
        # An absent file keeps the missing wording at the
        # caller, so the helper records no UTF-8 problem
        # for it and still returns no text.
        with RetryingTemporaryDirectory() as tmp:
            absent = Path(tmp) / "absent.md"
            for name in self.SINGLE_PATH_GATES:
                mod = load_script(name)
                self.assertIsNone(mod.read_text(absent), name)
                self.assertEqual(mod.utf8_problems(), [], name)
            version = load_script("check_version")
            self.assertIsNone(version.read(absent))
            self.assertEqual(version.utf8_problems(), [])

    def test_the_comate_copy_records_the_problem(self):
        mod = load_script("check_comate")
        with RetryingTemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "damaged.md").write_bytes(b"\xff\xfe\x00bad")
            problems = []
            result = mod.read_text(
                root, "damaged.md", problems, "the damaged file"
            )
            self.assertIsNone(result)
            self.assertTrue(
                any("cannot be read as UTF-8 text" in p
                    for p in problems),
                problems,
            )


class TestUndecodableProblemLevelPlants(unittest.TestCase):
    """Problem level plants for the seven remaining gates.

    Round 4 fix review, standards Minor 3. The kimi and
    qwen and zcode plants pin the decode repair wiring at
    problem level, and the helper level battery above pins
    the read copies, but the other seven gates carried the
    same repair wiring with no plant at the level a
    contributor meets. Each plant below stands a damaged
    file at the path its gate reads first and calls the
    gate problems entry, so reverting the repair call or
    the entry clearing in any one of the seven leaves that
    gate calling a standing damaged file missing and turns
    its plant red.
    """

    def gate_problems(self, script, entry, rel):
        mod = load_script(script)
        with RetryingTemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"\xff\xfe\x00bad")
            return getattr(mod, entry)(root)

    def assert_utf8_named_not_missing(self, problems, name,
                                      missing_wording):
        self.assertTrue(
            any(
                name in p and "cannot be read as UTF-8 text" in p
                for p in problems
            ),
            problems,
        )
        self.assertFalse(
            any(missing_wording in p for p in problems),
            problems,
        )

    def test_antigravity_problems_name_utf8_not_missing(self):
        problems = self.gate_problems(
            "check_antigravity", "antigravity_problems",
            "docs/antigravity-plugin-brief.md",
        )
        self.assert_utf8_named_not_missing(
            problems, "antigravity-plugin-brief.md",
            "docs/antigravity-plugin-brief.md is missing",
        )

    def test_brand_problems_name_utf8_not_missing(self):
        problems = self.gate_problems(
            "check_brand", "brand_problems",
            ".claude-plugin/plugin.json",
        )
        self.assert_utf8_named_not_missing(
            problems, "plugin.json",
            "missing manifest at .claude-plugin/plugin.json",
        )

    def test_coderabbit_problems_name_utf8_not_missing(self):
        problems = self.gate_problems(
            "check_coderabbit", "coderabbit_problems",
            "docs/coderabbit-review-brief.md",
        )
        self.assert_utf8_named_not_missing(
            problems, "coderabbit-review-brief.md",
            "docs/coderabbit-review-brief.md is missing",
        )

    def test_copilot_problems_name_utf8_not_missing(self):
        problems = self.gate_problems(
            "check_copilot", "copilot_problems",
            "docs/copilot-sdk-brief.md",
        )
        self.assert_utf8_named_not_missing(
            problems, "copilot-sdk-brief.md",
            "docs/copilot-sdk-brief.md is missing",
        )

    def test_cursor_problems_name_utf8_not_missing(self):
        problems = self.gate_problems(
            "check_cursor", "cursor_problems",
            ".cursor-plugin/plugin.json",
        )
        self.assert_utf8_named_not_missing(
            problems, "plugin.json",
            ".cursor-plugin/plugin.json is missing",
        )

    def test_devin_problems_name_utf8_not_missing(self):
        problems = self.gate_problems(
            "check_devin", "devin_problems",
            "docs/devin-playbook-brief.md",
        )
        self.assert_utf8_named_not_missing(
            problems, "devin-playbook-brief.md",
            "docs/devin-playbook-brief.md is missing",
        )

    def test_version_main_names_utf8_not_missing(self):
        mod = load_script("check_version")
        with RetryingTemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin = root / ".claude-plugin" / "plugin.json"
            plugin.parent.mkdir(parents=True)
            plugin.write_bytes(b"\xff\xfe\x00bad")
            mod_plugin = root / "mod-plugin.json"
            mod_plugin.write_text(
                '{"version": "1.3.0"}', encoding="utf-8"
            )
            antigravity_plugin = root / "antigravity-plugin.json"
            antigravity_plugin.write_text(
                '{"name": "recognitio", '
                '"description": "A plugin."}',
                encoding="utf-8",
            )
            market = root / "marketplace.json"
            market.write_text(
                '{"metadata": {"version": "1.3.0"}, "plugins": '
                '[{"name": "recognitio", "version": "1.3.0"}]}',
                encoding="utf-8",
            )
            extract = root / "extract.py"
            extract.write_text(
                'EXTRACTOR_VERSION = "1.3.0"\n', encoding="utf-8"
            )
            log = root / "CHANGELOG.md"
            log.write_text(
                "## [Unreleased]\n\n"
                "This work carries version 1.3.0.\n",
                encoding="utf-8",
            )
            original = (
                mod.PLUGIN_JSON, mod.MOD_PLUGIN_JSON,
                mod.MARKETPLACE_JSON, mod.EXTRACT_PY,
                mod.CHANGELOG_MD, mod.ANTIGRAVITY_PLUGIN_JSON,
            )
            mod.PLUGIN_JSON = plugin
            mod.MOD_PLUGIN_JSON = mod_plugin
            mod.MARKETPLACE_JSON = market
            mod.EXTRACT_PY = extract
            mod.CHANGELOG_MD = log
            mod.ANTIGRAVITY_PLUGIN_JSON = antigravity_plugin
            try:
                with redirect_stderr(io.StringIO()) as captured:
                    code = mod.main()
            finally:
                (
                    mod.PLUGIN_JSON, mod.MOD_PLUGIN_JSON,
                    mod.MARKETPLACE_JSON, mod.EXTRACT_PY,
                    mod.CHANGELOG_MD, mod.ANTIGRAVITY_PLUGIN_JSON,
                ) = original
            err = captured.getvalue()
        self.assertEqual(code, 1, err)
        self.assertIn(
            "plugin.json cannot be read as UTF-8 text", err
        )
        self.assertNotIn("missing plugin manifest", err)
        self.assertNotIn("Traceback", err)


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

    def test_the_skill_text_limit_stands_at_sixteen_thousand(self):
        # Round 9 spec Minor 2. The boundary tests in this class
        # build every plant from the module constant, so raising
        # the constant moves the plants and the expectations
        # with it and the class stays green while the shipped
        # skill drifts toward the host reattachment cut the
        # check_skill comment names. The value stands pinned
        # here as a literal, and one plant built from the same
        # literal fails at one character past it, so the check
        # that enforces the buffer is itself held to it.
        self.assertEqual(self.mod.SKILL_TEXT_LIMIT, 16000)
        head = "---\nname: recognitio\ndescription: a packet\n---\n\n"
        text = head + "x" * (16001 - len(head))
        self.assertEqual(len(text), 16001)
        code, err = self.run_main_on_skill_text(text)
        self.assertEqual(code, 1)
        self.assertIn("over the 16000 limit", err)

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

    def test_a_stale_marketplace_entry_is_a_problem(self):
        problems = self.mod.coherence_problems({
            "plugin.json": "1.3.0",
            "EXTRACTOR_VERSION": "1.3.0",
            "marketplace.json entry 1": "1.2.0",
        })
        self.assertTrue(any("disagree" in p for p in problems), problems)
        problems = self.mod.coherence_problems({
            "plugin.json": "1.3.0",
            "marketplace.json entry 1": None,
        })
        self.assertTrue(any("no version" in p for p in problems), problems)

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
                          changelog_text, readme_text=None,
                          mod_text=None, antigravity_text="default",
                          package_text='{"version": "1.3.0"}',
                          cursor_plugin_text='{"version": "1.3.0"}',
                          cursor_market_text=None,
                          zcode_text='{"version": "1.3.0"}'):
        if readme_text is None:
            readme_text = "# Recognitio\n"
        if mod_text is None:
            mod_text = plugin_text
        if antigravity_text == "default":
            antigravity_text = (
                '{"name": "recognitio", '
                '"description": "A plugin."}'
            )
        if cursor_market_text is None:
            cursor_market_text = (
                '{"metadata": {"version": "1.3.0"}, "plugins": '
                '[{"version": "1.3.0"}]}'
            )
        with RetryingTemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin = root / "plugin.json"
            plugin.write_text(plugin_text, encoding="utf-8")
            mod_plugin = root / "mod-plugin.json"
            mod_plugin.write_text(mod_text, encoding="utf-8")
            antigravity_plugin = root / "antigravity-plugin.json"
            if antigravity_text is not None:
                antigravity_plugin.write_text(
                    antigravity_text, encoding="utf-8"
                )
            market = root / "marketplace.json"
            market.write_text(marketplace_text, encoding="utf-8")
            package = root / "package.json"
            package.write_text(package_text, encoding="utf-8")
            cursor_plugin = root / "cursor-plugin.json"
            cursor_plugin.write_text(
                cursor_plugin_text, encoding="utf-8"
            )
            cursor_market = root / "cursor-marketplace.json"
            cursor_market.write_text(
                cursor_market_text, encoding="utf-8"
            )
            zcode_plugin = root / "zcode-plugin.json"
            zcode_plugin.write_text(zcode_text, encoding="utf-8")
            extract = root / "extract.py"
            extract.write_text(
                'EXTRACTOR_VERSION = "1.3.0"\n', encoding="utf-8"
            )
            log = root / "CHANGELOG.md"
            log.write_text(changelog_text, encoding="utf-8")
            readme = root / "README.md"
            readme.write_text(readme_text, encoding="utf-8")
            original = (
                self.mod.PLUGIN_JSON, self.mod.MOD_PLUGIN_JSON,
                self.mod.MARKETPLACE_JSON,
                self.mod.EXTRACT_PY, self.mod.CHANGELOG_MD,
                getattr(self.mod, "ANTIGRAVITY_PLUGIN_JSON", None),
                self.mod.PACKAGE_JSON, self.mod.CURSOR_PLUGIN_JSON,
                self.mod.CURSOR_MARKETPLACE_JSON,
                self.mod.ZCODE_PLUGIN_JSON,
            )
            self.mod.PLUGIN_JSON = plugin
            self.mod.MOD_PLUGIN_JSON = mod_plugin
            self.mod.MARKETPLACE_JSON = market
            self.mod.EXTRACT_PY = extract
            self.mod.CHANGELOG_MD = log
            self.mod.PACKAGE_JSON = package
            self.mod.CURSOR_PLUGIN_JSON = cursor_plugin
            self.mod.CURSOR_MARKETPLACE_JSON = cursor_market
            self.mod.ZCODE_PLUGIN_JSON = zcode_plugin
            self.mod.ANTIGRAVITY_PLUGIN_JSON = antigravity_plugin
            try:
                with redirect_stderr(io.StringIO()) as captured:
                    code = self.mod.main()
            finally:
                (
                    self.mod.PLUGIN_JSON, self.mod.MOD_PLUGIN_JSON,
                    self.mod.MARKETPLACE_JSON,
                    self.mod.EXTRACT_PY, self.mod.CHANGELOG_MD,
                    self.mod.ANTIGRAVITY_PLUGIN_JSON,
                    self.mod.PACKAGE_JSON,
                    self.mod.CURSOR_PLUGIN_JSON,
                    self.mod.CURSOR_MARKETPLACE_JSON,
                    self.mod.ZCODE_PLUGIN_JSON,
                ) = original
            return code, captured.getvalue()

    def test_a_drifted_mod_manifest_version_fails(self):
        # The recognitio-mod manifest is a version surface like
        # the root manifest, because under strict mode it is
        # the definition the host loads for its entry. A bump
        # that moved every other surface and left it behind
        # must fail here.
        good_log = (
            "# Changelog\n\n## [Unreleased]\n\n"
            "This work carries version 1.3.0.\n"
        )
        code, err = self.run_main_on_texts(
            '{"version": "1.3.0"}',
            '{"metadata": {"version": "1.3.0"}, "plugins": '
            '[{"version": "1.3.0"}, {"version": "1.3.0"}]}',
            good_log,
            mod_text='{"version": "9.9.9"}',
        )
        self.assertEqual(code, 1, err)
        self.assertIn("recognitio-mod", err)

    def test_a_drifted_portable_package_version_fails(self):
        # Round 14. The portable package manifest carries the
        # release version and the gate never read it, so a bump
        # that left it behind passed. The drift plant fails
        # here and names the surface.
        code, err = self.run_main_on_texts(
            '{"version": "1.3.0"}', self.GOOD_MARKET, self.GOOD_LOG,
            package_text='{"version": "9.9.9"}',
        )
        self.assertEqual(code, 1, err)
        self.assertIn("portable package plugin.json", err)

    def test_a_drifted_cursor_plugin_version_fails(self):
        # Round 14. The Cursor plugin manifest is a version
        # surface of the same kind.
        code, err = self.run_main_on_texts(
            '{"version": "1.3.0"}', self.GOOD_MARKET, self.GOOD_LOG,
            cursor_plugin_text='{"version": "9.9.9"}',
        )
        self.assertEqual(code, 1, err)
        self.assertIn("Cursor plugin.json", err)

    def test_a_drifted_cursor_marketplace_version_fails(self):
        # Round 14. The Cursor marketplace listing carries a
        # version on its metadata and on each entry.
        code, err = self.run_main_on_texts(
            '{"version": "1.3.0"}', self.GOOD_MARKET, self.GOOD_LOG,
            cursor_market_text=(
                '{"metadata": {"version": "1.3.0"}, "plugins": '
                '[{"version": "9.9.9"}]}'
            ),
        )
        self.assertEqual(code, 1, err)
        self.assertIn("Cursor marketplace.json entry 2", err)

    def test_a_drifted_zcode_plugin_version_fails(self):
        # Round 14. The ZCode plugin manifest is a version
        # surface of the same kind.
        code, err = self.run_main_on_texts(
            '{"version": "1.3.0"}', self.GOOD_MARKET, self.GOOD_LOG,
            zcode_text='{"version": "9.9.9"}',
        )
        self.assertEqual(code, 1, err)
        self.assertIn("ZCode plugin.json", err)

    GOOD_LOG = (
        "# Changelog\n\n## [Unreleased]\n\n"
        "This work carries version 1.3.0.\n"
    )
    GOOD_MARKET = (
        '{"metadata": {"version": "1.3.0"}, "plugins": '
        '[{"version": "1.3.0"}, {"version": "1.3.0"}]}'
    )

    def test_a_version_field_on_the_antigravity_manifest_fails(self):
        # The schema the Antigravity manifest names through
        # its $schema key permits the name and the description
        # beside that key and no further key, so the manifest
        # is not a version surface at all. A version field
        # standing there is a forbidden field and must fail
        # here by name.
        code, err = self.run_main_on_texts(
            '{"version": "1.3.0"}',
            self.GOOD_MARKET,
            self.GOOD_LOG,
            antigravity_text='{"version": "9.9.9"}',
        )
        self.assertEqual(code, 1, err)
        self.assertIn("Antigravity", err)
        self.assertIn("forbidden", err)

    def test_a_missing_antigravity_manifest_fails_by_name(self):
        # The manifest ships in the tree, so an absent one is
        # a named problem and not a silent pass.
        code, err = self.run_main_on_texts(
            '{"version": "1.3.0"}',
            self.GOOD_MARKET,
            self.GOOD_LOG,
            antigravity_text=None,
        )
        self.assertEqual(code, 1, err)
        self.assertIn("Antigravity", err)
        self.assertIn("missing", err)

    def test_a_non_string_version_field_on_the_manifest_fails(self):
        # The forbidden field fails at any value type, so a
        # numeric version field is the same problem as a
        # string one.
        code, err = self.run_main_on_texts(
            '{"version": "1.3.0"}',
            self.GOOD_MARKET,
            self.GOOD_LOG,
            antigravity_text='{"version": 130}',
        )
        self.assertEqual(code, 1, err)
        self.assertIn("Antigravity", err)
        self.assertIn("forbidden", err)

    def test_an_unparsable_antigravity_manifest_fails_by_name(self):
        code, err = self.run_main_on_texts(
            '{"version": "1.3.0"}',
            self.GOOD_MARKET,
            self.GOOD_LOG,
            antigravity_text="{ not json",
        )
        self.assertEqual(code, 1, err)
        self.assertIn("Antigravity", err)
        self.assertIn("does not parse", err)

    def test_an_antigravity_manifest_directory_fails_by_name(self):
        with RetryingTemporaryDirectory() as tmp:
            root = Path(tmp)
            code, err = self.run_main_with_antigravity_shape(
                root, "directory"
            )
        self.assertEqual(code, 1, err)
        self.assertIn("Antigravity", err)
        self.assertIn("not a regular file", err)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "no mkfifo on this host")
    def test_an_antigravity_manifest_fifo_refuses_promptly_by_name(self):
        with RetryingTemporaryDirectory() as tmp:
            root = Path(tmp)
            code, err = self.run_main_with_antigravity_shape(
                root, "fifo"
            )
        self.assertEqual(code, 1, err)
        self.assertIn("Antigravity", err)
        self.assertIn("not a regular file", err)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "no mkfifo on this host")
    def test_an_antigravity_link_to_a_fifo_refuses_promptly(self):
        with RetryingTemporaryDirectory() as tmp:
            root = Path(tmp)
            code, err = self.run_main_with_antigravity_shape(
                root, "link-to-fifo"
            )
        self.assertEqual(code, 1, err)
        self.assertIn("Antigravity", err)
        self.assertIn("not a regular file", err)

    def test_an_agreeing_version_field_on_the_manifest_fails(self):
        # The forbidden field fails even at the value every
        # real version surface agrees on, because the field
        # itself is what the schema forbids. Before the fix
        # this exact text passed as an agreeing surface.
        code, err = self.run_main_on_texts(
            '{"version": "1.3.0"}',
            self.GOOD_MARKET,
            self.GOOD_LOG,
            antigravity_text='{"version": "1.3.0"}',
        )
        self.assertEqual(code, 1, err)
        self.assertIn("Antigravity", err)
        self.assertIn("forbidden", err)

    def test_a_schema_clean_antigravity_manifest_passes(self):
        # Control. A manifest carrying only the keys its
        # schema permits is the shape that must keep passing.
        code, err = self.run_main_on_texts(
            '{"version": "1.3.0"}',
            self.GOOD_MARKET,
            self.GOOD_LOG,
            antigravity_text=(
                '{"name": "recognitio", '
                '"description": "A plugin."}'
            ),
        )
        self.assertEqual(code, 0, err)

    def test_a_reformatted_antigravity_manifest_passes(self):
        # Control. A whitespace and key order rewrite of the
        # schema clean manifest must keep passing.
        code, err = self.run_main_on_texts(
            '{"version": "1.3.0"}',
            self.GOOD_MARKET,
            self.GOOD_LOG,
            antigravity_text=(
                '{\n  "description": "A plugin.",\n'
                '  "name": "recognitio"\n}\n'
            ),
        )
        self.assertEqual(code, 0, err)

    def run_main_with_antigravity_shape(self, root, shape):
        # Build a whole gate tree in root with the Antigravity
        # path standing in the named shape, then run the gate
        # main in a subprocess bounded at ten seconds, so a
        # door that read its FIFO would fail at the bound
        # instead of hanging the suite.
        (root / "plugin.json").write_text(
            '{"version": "1.3.0"}', encoding="utf-8"
        )
        (root / "mod-plugin.json").write_text(
            '{"version": "1.3.0"}', encoding="utf-8"
        )
        (root / "marketplace.json").write_text(
            self.GOOD_MARKET, encoding="utf-8"
        )
        (root / "extract.py").write_text(
            'EXTRACTOR_VERSION = "1.3.0"\n', encoding="utf-8"
        )
        (root / "CHANGELOG.md").write_text(
            self.GOOD_LOG, encoding="utf-8"
        )
        antigravity = root / "antigravity-plugin.json"
        if shape == "directory":
            antigravity.mkdir()
        elif shape == "fifo":
            os.mkfifo(antigravity)
        elif shape == "link-to-fifo":
            os.mkfifo(root / "antigravity-target")
            antigravity.symlink_to(root / "antigravity-target")
        else:  # pragma: no cover, a test authoring error
            raise AssertionError("unknown shape %r" % shape)
        driver = (
            "import importlib.util, sys\n"
            "spec = importlib.util.spec_from_file_location("
            "'gate_under_test', sys.argv[1])\n"
            "mod = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(mod)\n"
            "from pathlib import Path\n"
            "root = Path(sys.argv[2])\n"
            "mod.PLUGIN_JSON = root / 'plugin.json'\n"
            "mod.MOD_PLUGIN_JSON = root / 'mod-plugin.json'\n"
            "mod.MARKETPLACE_JSON = root / 'marketplace.json'\n"
            "mod.EXTRACT_PY = root / 'extract.py'\n"
            "mod.CHANGELOG_MD = root / 'CHANGELOG.md'\n"
            "if hasattr(mod, 'ANTIGRAVITY_PLUGIN_JSON'):\n"
            "    mod.ANTIGRAVITY_PLUGIN_JSON = (\n"
            "        root / 'antigravity-plugin.json')\n"
            "sys.exit(mod.main())\n"
        )
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    driver,
                    str(ROOT / "scripts" / "check_version.py"),
                    str(root),
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except subprocess.TimeoutExpired:
            self.fail("the version gate did not finish within ten seconds")
        return result.returncode, result.stdout + result.stderr

    def test_main_no_longer_reads_a_readme_version_badge(self):
        # The README version badge retired in the visual round 2
        # storefront rebuild, and the gate repinned to the
        # manifests and the changelog. A README that still carried
        # a stale badge, or no badge at all, is no longer a
        # version surface, so both forms pass while the manifests
        # and the changelog agree.
        plugin = '{"version": "1.3.0"}'
        market = (
            '{"metadata": {"version": "1.3.0"}, "plugins": '
            '[{"name": "x", "version": "1.3.0"}]}'
        )
        log = (
            "## [Unreleased]\n\nThis work carries version 1.3.0.\n"
        )
        stale = (
            "[![Version](https://img.shields.io/badge/"
            "version-1.2.0-blue.svg)](CHANGELOG.md)\n"
        )
        code, err = self.run_main_on_texts(
            plugin, market, log, readme_text=stale
        )
        self.assertEqual(code, 0, err)
        missing = "a README with no badge at all\n"
        code, err = self.run_main_on_texts(
            plugin, market, log, readme_text=missing
        )
        self.assertEqual(code, 0, err)

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
        # The listing carries exactly two plugin entries, the
        # recognitio plugin and the recognitio-mod plugin, and
        # the gate pins the set by name. A further entry naming
        # the same skill under another name is the identity
        # family in its purest form, so the pin holds the set,
        # not just the recognitio entry, and only the
        # recognitio entry may name the skill.
        self.assertEqual(
            sorted(p["name"] for p in data["plugins"]),
            ["recognitio", "recognitio-mod"],
            data["plugins"],
        )
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
        # The mod entry names the mod plugin folder as its
        # source and sets strict to true as a real boolean for
        # the same reason the recognitio entry does. It names
        # no component, because the mod manifest in that
        # folder is the whole definition of the plugin.
        mod_entries = [
            p for p in data["plugins"] if p["name"] == "recognitio-mod"
        ]
        self.assertEqual(len(mod_entries), 1, data["plugins"])
        self.assertEqual(
            mod_entries[0]["source"], "./plugins/recognitio-mod")
        self.assertIsInstance(mod_entries[0]["strict"], bool)
        self.assertTrue(mod_entries[0]["strict"])
        self.assertNotIn("skills", mod_entries[0])

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
    """The description spellings are pinned.

    The frontmatter description is the trigger identity the
    TRIGGER-RESULTS.md winner discipline protects. No description
    change ships without a winning scored run, so the frontmatter
    stands as the named exception to the description unification.
    Every display description carries the one canonical sentence
    from the visual round 2 storefront rebuild, and each spelling
    is pinned here so a copy bar clean rewrite of any of them
    fails the gate. A deliberate change updates the spelling,
    this pin and the changelog in the same change, and a change
    to the frontmatter spelling also updates the trigger record
    and says in the change notes that the change is a spec change
    and why.
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
        "Pulls the relevant changes from a pull request or a commit range, "
        "with the context a reviewer needs, into one verified review packet."
    )
    # The storefront repair round once let the two Claude
    # listing surfaces and the portable manifest carry one
    # further sentence each, on the ground that the never
    # install both rule belonged to the listing a reader
    # chooses between. The storefront finalization retired
    # both exceptions under the listing standard, which sets
    # one short description identical on every face, and
    # the never both guidance stands in the portable long
    # description at the place the standard reserves for
    # how the software is used. Every short description
    # below therefore pins to the canonical sentence alone.
    # The Antigravity face carried one platform sentence of
    # its own beside the canonical sentence until this
    # stack, and it standardizes with the rest, so its pin
    # below is the canonical sentence as well.
    ANTIGRAVITY_DESCRIPTION = MANIFEST_DESCRIPTION

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

    def json_description(self, *parts):
        data = self.version_mod.strict_json_loads(
            (ROOT.joinpath(*parts)).read_text(encoding="utf-8")
        )
        return data["description"]

    def json_entry_description(self, *parts):
        data = self.version_mod.strict_json_loads(
            (ROOT.joinpath(*parts)).read_text(encoding="utf-8")
        )
        return data["plugins"][0]["description"]

    def json_metadata_description(self, *parts):
        data = self.version_mod.strict_json_loads(
            (ROOT.joinpath(*parts)).read_text(encoding="utf-8")
        )
        return data["metadata"]["description"]

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

    def test_marketplace_metadata_description_is_pinned(self):
        self.assertEqual(
            self.json_metadata_description(
                ".claude-plugin", "marketplace.json"
            ),
            self.MANIFEST_DESCRIPTION,
        )

    def test_cursor_manifest_description_is_pinned(self):
        self.assertEqual(
            self.json_description(".cursor-plugin", "plugin.json"),
            self.MANIFEST_DESCRIPTION,
        )

    def test_cursor_marketplace_entry_description_is_pinned(self):
        self.assertEqual(
            self.json_entry_description(
                ".cursor-plugin", "marketplace.json"
            ),
            self.MANIFEST_DESCRIPTION,
        )

    def test_cursor_marketplace_metadata_description_is_pinned(self):
        self.assertEqual(
            self.json_metadata_description(
                ".cursor-plugin", "marketplace.json"
            ),
            self.MANIFEST_DESCRIPTION,
        )

    def test_zcode_manifest_description_is_pinned(self):
        self.assertEqual(
            self.json_description(".zcode-plugin", "plugin.json"),
            self.MANIFEST_DESCRIPTION,
        )

    def test_antigravity_manifest_description_is_pinned(self):
        self.assertEqual(
            self.json_description(".antigravity", "plugin.json"),
            self.ANTIGRAVITY_DESCRIPTION,
        )

    def test_package_manifest_description_is_pinned(self):
        self.assertEqual(
            self.json_description("agent-plugins-package", "plugin.json"),
            self.MANIFEST_DESCRIPTION,
        )


class TestReadmeStorefront(unittest.TestCase):
    """The visual round 2 storefront elements are pinned.

    The first screen carries the headline, the canonical
    description, the navigation row, the CI and license badges,
    the hero, the paired eval proof and the install pointer, in
    that order. The static version badge retired from the README,
    so its badge form must not return. The adaptations table
    names each platform brief as a clickable relative link.
    """

    CANONICAL = (
        "Pulls the relevant changes from a pull request or a commit "
        "range, with the context a reviewer needs, into one verified "
        "review packet."
    )
    HEADLINE = "**A review starts from evidence instead of a bare diff.**"
    BRIEF_LINKS = (
        "[the Codex review brief](docs/codex-review-brief.md)",
        "[the Codex plugin brief](docs/codex-plugin-brief.md)",
        "[the Cursor plugin brief](docs/cursor-plugin-brief.md)",
        "[the Copilot SDK brief](docs/copilot-sdk-brief.md)",
        "[the CodeRabbit review brief](docs/coderabbit-review-brief.md)",
        "[the Kimi plugin brief](docs/kimi-plugin-brief.md)",
        "[the ZCode plugin brief](docs/zcode-plugin-brief.md)",
        "[the Devin playbook brief](docs/devin-playbook-brief.md)",
        "[the Qwen Code brief](docs/qwen-code-brief.md)",
        "[the Antigravity plugin brief](docs/antigravity-plugin-brief.md)",
    )

    def setUp(self):
        self.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.flat = " ".join(self.readme.split())

    def test_the_first_screen_order_is_pinned(self):
        # The README rebuild after visual round 10. The hero
        # is one lockup, the wordmark pair alone, and the
        # heading that once repeated the wordmark under it
        # stays out, so the first marker is the wordmark
        # itself and the headline follows it.
        self.assertNotIn("# Recognitio", self.readme)
        markers = (
            "docs/brand/wordmark-dark.svg",
            self.HEADLINE,
            self.CANONICAL,
            "For reviewers and the agents who assist them",
            "[What it does](#what-it-does)",
            "[![CI passing]",
            "docs/images/recognitio-claude-code-demo.gif",
            "docs/images/recognitio-session-claude-code-denial.png",
            "docs/images/recognitio-session-codex-verified.png",
            "docs/images/recognitio-cursor-agent-poster.png",
            "docs/images/recognitio-session-qwen-summary.png",
            "docs/images/eval-chart.svg",
            "Eight planted defects across four fixture tasks",
            "New here. Start with the sixty second quickstart",
            "**Sixty second quickstart**",
            "--commit 991ac6a",
            "## What it does",
        )
        positions = []
        for marker in markers:
            self.assertIn(marker, self.flat)
            positions.append(self.flat.index(marker))
        self.assertEqual(positions, sorted(positions))

    def test_the_version_badge_stays_out_of_the_readme(self):
        self.assertNotIn("badge/version-", self.readme)
        self.assertNotIn("[![Version]", self.readme)

    def test_the_badge_row_is_ci_and_license_only(self):
        badge_lines = [
            line for line in self.readme.splitlines()
            if line.startswith("[![")
        ]
        self.assertEqual(len(badge_lines), 1)
        self.assertIn("[![CI passing]", badge_lines[0])
        self.assertIn("[![License MIT]", badge_lines[0])

    def test_the_canonical_sentence_opens_agents_and_the_cursor_readme(self):
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn(self.CANONICAL, " ".join(agents.split()))
        cursor_readme = (
            ROOT / ".cursor-plugin" / "README.md"
        ).read_text(encoding="utf-8")
        self.assertIn(self.CANONICAL, " ".join(cursor_readme.split()))

    def test_the_adaptations_briefs_are_clickable_links(self):
        for link in self.BRIEF_LINKS:
            self.assertIn(link, self.readme)
        self.assertNotIn("`docs/codex-review-brief.md`", self.readme)
        self.assertNotIn("`docs/qwen-code-brief.md`", self.readme)

    def test_the_serving_paragraph_lives_in_the_why_section(self):
        why = self.readme.split("## Why", 1)[1].split("## Install", 1)[0]
        self.assertIn(
            "Recognitio serves the pull request review workflow.", why
        )
        first_screen = self.readme.split("## What it does", 1)[0]
        self.assertNotIn(
            "Recognitio serves the pull request review workflow.",
            first_screen,
        )


class TestReadmeRebuild(unittest.TestCase):
    """The README rebuild after the visual program is pinned.

    The rebuild moved the tier model, the completeness
    discipline and trust and limits behind a closing Going
    deeper section, gave every install route its own
    subheading, explained pinning in one place and wrapped
    the Usage commands so every command line fits its
    block. These pins hold that structure in place, in the
    same way the storefront pins hold the first screen.
    """

    GOING_DEEPER_LINKS = (
        "[The tier model](.agents/skills/recognitio/SKILL.md"
        "#the-tier-model)",
        "[The completeness discipline](.agents/skills/recognitio"
        "/SKILL.md#completeness-discipline)",
        "[Trust and limits](.agents/skills/recognitio/SKILL.md"
        "#trust-and-limits)",
        "[Principles](docs/principles.md)",
    )
    INSTALL_SUBHEADINGS = (
        "### Claude Code plugin",
        "### Cursor",
        "### Any agent",
        "### Folder copy",
        "### Qwen Code",
        "### Pinning the install",
        "### The packet output style",
        "### The reviewer persona",
    )

    def setUp(self):
        self.readme = (ROOT / "README.md").read_text(encoding="utf-8")

    def test_the_going_deeper_links_close_the_page(self):
        for link in self.GOING_DEEPER_LINKS:
            self.assertIn(link, self.readme)
        headings = [
            line for line in self.readme.splitlines()
            if line.startswith("## ")
        ]
        self.assertEqual(headings[-1], "## Going deeper")

    def test_each_install_route_carries_its_own_subheading(self):
        install = self.readme.split("## Install", 1)[1].split(
            "## Platform adaptations", 1
        )[0]
        positions = []
        for heading in self.INSTALL_SUBHEADINGS:
            self.assertIn(heading, install)
            positions.append(install.index(heading))
        self.assertEqual(positions, sorted(positions))

    def test_pinning_is_explained_exactly_once(self):
        self.assertEqual(
            self.readme.count("### Pinning the install"), 1
        )
        self.assertEqual(
            self.readme.count(
                "Before running any route above, pin the install "
                "to a commit SHA and read the commands and files "
                "the route will run"
            ),
            1,
        )
        self.assertEqual(
            self.readme.count(
                "A copied or installed skill does not inherit "
                "later upstream fixes."
            ),
            1,
        )

    def test_usage_command_lines_fit_their_blocks(self):
        usage = self.readme.split("## Usage", 1)[1].split(
            "## Going deeper", 1
        )[0]
        in_fence = False
        command_lines = []
        for line in usage.splitlines():
            if line.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                command_lines.append(line)
        self.assertGreaterEqual(
            sum("extract.py" in line for line in command_lines), 4
        )
        for line in command_lines:
            self.assertLessEqual(len(line), 80, line)


class TestReadmePhoneWidth(unittest.TestCase):
    """The WP1 phone width fixes are pinned.

    The hero recording carries a max width picture source
    for its phone crop, the worked example fences and the
    shell command blocks keep every physical line inside
    the phone visible width, the flow diagram runs wide,
    the platform table carries no long inline code path,
    and every README image alt sits inside the 125
    character guideline with declared dimensions.
    """

    def setUp(self):
        self.readme = (ROOT / "README.md").read_text(encoding="utf-8")

    def fences(self, section_start, section_end=None):
        part = self.readme.split(section_start, 1)[1]
        if section_end:
            part = part.split(section_end, 1)[0]
        found = []
        current = None
        for line in part.splitlines():
            if line.startswith("```"):
                if current is None:
                    current = []
                else:
                    found.append(current)
                    current = None
                continue
            if current is not None:
                current.append(line)
        return found

    def test_the_hero_picture_serves_the_phone_crop(self):
        # The hero picture is the first picture element in
        # the README since the wordmark theme fix landing
        # moved the wordmark to the theme fragment pair, so
        # the block stands after the first picture opening.
        block = self.readme.split("<picture>", 1)[1].split(
            "</picture>", 1
        )[0]
        self.assertIn(
            '<source media="(max-width: 480px)" '
            'srcset="docs/images/'
            'recognitio-claude-code-verified-crop.png">',
            block,
        )
        self.assertIn(
            'src="docs/images/recognitio-claude-code-demo.gif" '
            'width="792">',
            block,
        )
        # The shared alt names the denial as well as the
        # verified packet and the verdict, because the phone
        # crop shows the verified moment and the desktop
        # recording carries the denial during its play and
        # ends on the verdict. The alt stood unpinned before
        # this pin, and a tree with the alt reverted to its
        # earlier wording passed every gate test, so the pin
        # stands here beside the source and fallback pins.
        self.assertIn(
            'alt="A Claude Code session denied a reviewer '
            "spawn, then verified its packet and ended on a "
            'verdict of Not blocking."',
            block,
        )
        # The hero image declares its width and no height.
        # GitHub honours a height attribute as a fixed CSS
        # height, and the WP1 rendered pass caught it
        # stretching the phone crop into a 608 tall box.
        # With the width alone declared, both sources
        # render at their natural aspect on the live page.

    def test_every_readme_image_alt_and_dimensions(self):
        alts = re.findall(r'alt="([^"]+)"', self.readme)
        alts += re.findall(r"!\[([^\]]*)\]\(", self.readme)
        self.assertTrue(alts)
        for alt in alts:
            self.assertLessEqual(len(alt), 125, alt)
        for tag in re.findall(r"<img [^>]+>", self.readme):
            self.assertIn('width="', tag)
            if "wordmark" in tag:
                self.assertIn('height="', tag)
            if "claude-code-demo" in tag:
                self.assertNotIn('height="', tag)

    def test_the_worked_example_lines_fit_phone_width(self):
        for fence in self.fences(
            "## See it on a real change", "## How it works"
        ):
            for line in fence:
                self.assertLessEqual(len(line), 30, line)

    def test_shell_command_lines_fit_phone_width(self):
        # The plugin chat lines are the named residue. They
        # are chat input rather than shell, they cannot take
        # a backslash continuation, and they stand at their
        # shortest true lengths of 50 and 49 characters in
        # the first block and 61 and 49 in the pin block.
        for start, end in (
            ("## Install", "## Platform adaptations"),
            ("## Usage", "## Going deeper"),
        ):
            for fence in self.fences(start, end):
                for line in fence:
                    if line.startswith("/plugin"):
                        continue
                    self.assertLessEqual(len(line), 30, line)

    def test_usage_commands_join_back_to_the_exact_paths(self):
        usage = self.readme.split("## Usage", 1)[1]
        joined = usage.replace("\\\n", "")
        self.assertEqual(
            joined.count(
                "python3 .agents/skills/recognitio/"
                "scripts/extract.py"
            ),
            5,
        )

    def test_the_flow_diagram_runs_wide_with_its_nodes(self):
        # The diagram keeps its tall form. The WP1 rendered
        # pass tried the wide single row and the paired
        # subgraph rows on the live page. The wide row
        # failed phone legibility and the subgraph rows
        # failed to render at all, so the tall form is the
        # compact arrangement that passes both widths.
        self.assertIn("flowchart TB", self.readme)
        # The subgraph form is the form that failed to
        # render, so it stays out by name, and the tall
        # edges stand in their exact single column form.
        # Without these two pins the label checks above
        # pass on the subgraph form as well, which the
        # WP1 completion mutation run proved.
        self.assertNotIn("subgraph", self.readme)
        self.assertNotIn("direction LR", self.readme)
        for edge in (
            "A([Pull request or commit range]) --> "
            "B[Extract from the local clone]",
            "B --> C[Assemble the packet in four tiers]",
            "C --> D{Recount the change}",
            "D -->|Counts agree| E([Verified packet])",
            "E --> G[The review reads the packet]",
        ):
            self.assertIn(edge, self.readme)
        for label in (
            "Pull request or commit range",
            "Extract from the local clone",
            "Assemble the packet in four tiers",
            "Recount the change",
            "Verified packet",
            "A failed run leaves a standing verified packet untouched",
            "The review reads the packet",
        ):
            self.assertIn(label, self.readme)
        self.assertIn("D -->|Counts agree|", self.readme)
        self.assertIn("D -->|Counts disagree|", self.readme)

    def test_the_platform_table_carries_no_long_code_path(self):
        table = self.readme.split("## Platform adaptations", 1)[1]
        self.assertNotIn("`.zcode-plugin/plugin.json`", table)
        self.assertNotIn("`.antigravity/plugin.json`", table)
        self.assertIn(
            "in the .zcode-plugin directory as `plugin.json`", table
        )
        self.assertIn(
            "in the .antigravity directory as `plugin.json`", table
        )


class TestReadmeRound9(unittest.TestCase):
    """The visual round 9 cold eyes fixes are pinned.

    The Install section opens with a heads up that states the
    requirements and the two plugin session effects before any
    route, the Qwen subsection names the maintainer and carries
    no round language, the pin block names the commands and
    files a route will run, the tier model names the five
    languages the definition patterns cover, the demo lead in
    carries its receipt, the pericope is glossed at first use,
    the eval paragraph states the tied result beside the
    constructed one, the hosted diff claim carries the research
    attribution, and the worked example states the true
    relationship of its two function names.
    """

    def setUp(self):
        self.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.flat = " ".join(self.readme.split())

    def test_the_qwen_subsection_names_the_maintainer(self):
        self.assertIn(
            "the conditional publication decision stays with "
            "the maintainer",
            self.flat,
        )
        self.assertIn("No Qwen listing file ships.", self.flat)
        self.assertNotIn("stays with David", self.flat)
        self.assertNotIn("ships in this round", self.flat)

    def test_the_install_heads_up_states_requirements_and_effects(self):
        for fragment in (
            "Before any route, know what installing means.",
            "Every route needs Python 3.10 or newer and git, "
            "pull request mode also needs the GitHub CLI, and "
            "there are no third party dependencies.",
            "Its output style applies to every response in the "
            "session while the plugin is enabled and overrides "
            "the style chosen in your own settings",
            "its reviewer persona runs as the session main thread",
            "Pin the install to a commit SHA before running any "
            "route, as the pin block below sets out.",
        ):
            self.assertIn(fragment, self.flat)
        heads_up = self.flat.index("Before any route, know what")
        self.assertLess(
            self.flat.index("Take one install route only"), heads_up
        )
        self.assertLess(heads_up, self.flat.index("The plugin route comes first"))

    def test_the_pin_block_names_what_the_route_will_run(self):
        self.assertIn(
            "read the commands and files the route will run", self.flat
        )
        self.assertNotIn("read the install script", self.flat)

    def test_the_tier_model_names_the_five_languages(self):
        # The README rebuild after the visual program moved
        # the tier model summary into How it works, so the
        # sentence is pinned inside that section, not
        # anywhere on the page.
        how_it_works = self.readme.split("## How it works", 1)[1].split(
            "## Why", 1
        )[0]
        self.assertIn(
            "The definition patterns the companion search uses "
            "cover five languages, Python and Rust and Go and "
            "JavaScript and TypeScript, and a definition written "
            "in a language outside those five will not be found.",
            " ".join(how_it_works.split()),
        )

    def test_the_demo_lead_in_carries_its_receipt(self):
        # The storefront WP3 landing. The hero recording
        # changed from the Cursor money shot to a live Claude
        # Code session with the mod installed over the same
        # change, so the receipt sentences name the new
        # session, its deny then proceed arc and its capture
        # record in place of the old ones. The Cursor session
        # stands in the proof strip below the hero.
        # The storefront repair round then moved the receipt
        # paragraph below the hero and restated the arc, after
        # the red team found the landing wording credited the
        # second spawn itself with the 15 findings its session
        # only reached through a provider failure, parallel
        # partial reports and a third targeted pass. The pins
        # below hold the restated arc.
        first_screen = self.flat.split("## What it does", 1)[0]
        self.assertIn(
            "A session in Claude Code 2.1.314 with the "
            "recognitio mod installed reviews the change from "
            "`365da81e` to `ecdda4c8` in this repository, 28 "
            "files and 3,233 lines of diff.",
            first_screen,
        )
        self.assertIn(
            "Its first reviewer spawn is denied because no "
            "verified packet stands, and the packet is then "
            "built and its manifest verified flag confirmed "
            "true.",
            first_screen,
        )
        self.assertIn(
            "The second spawn proceeds against the verified "
            "packet and its first completion fails on a "
            "provider credit error, two reviewer reports come "
            "back in parallel over part of the range, and a "
            "third targeted reviewer pass fills the gap they "
            "left.",
            first_screen,
        )
        self.assertIn(
            "The session ends on a consolidated presentation "
            "of 15 findings with a verdict of Not blocking.",
            first_screen,
        )
        self.assertIn(
            "over OpenRouter with the model "
            "anthropic/claude-sonnet-5",
            first_screen,
        )
        self.assertIn(
            "Its capture record stands at "
            "[docs/images/capture-record.md]"
            "(docs/images/capture-record.md).",
            first_screen,
        )

    def test_the_pericope_is_glossed_at_first_use(self):
        self.assertIn(
            "The pericope is the packet itself, holding the "
            "change and the context a reviewer needs to read it, "
            "and nothing else.",
            self.flat,
        )

    def test_the_eval_paragraph_states_the_tied_result(self):
        self.assertIn(
            "On the defects inside the diff itself the two "
            "passes tied at 4 of 4 each.",
            self.flat,
        )

    def test_the_hosted_claim_carries_the_research_attribution(self):
        self.assertIn(
            "The research this project grew out of found hosted "
            "diffs capping the file counts they return and "
            "dropping oversized patches entirely, with no flag "
            "on either",
            self.flat,
        )
        self.assertNotIn(
            "Hosted diff endpoints cap their file counts", self.flat
        )

    def test_the_worked_example_states_the_function_relationship(self):
        self.assertIn(
            "Both excerpts show the same edit inside "
            "semantic_problems, and the packet header names "
            "naming_problems because git labels a hunk with the "
            "nearest function line above its opening line, and "
            "this hunk opens on the def line of "
            "semantic_problems itself.",
            self.flat,
        )


class TestReadmeWp2(unittest.TestCase):
    """The WP2 proof and story landing is pinned.

    The paired eval paragraph of numbers became a chart with
    a caption that keeps its pinned claims, the examples
    folder holds the complete packet for commit 991ac6a with
    its entry note, the who this is for line and the sixty
    second quickstart stand in the first screen, and the
    objections section answers its three questions between
    the Why section and the Install section.
    """

    def setUp(self):
        self.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.flat = " ".join(self.readme.split())

    def test_the_eval_chart_stands_in_the_first_screen(self):
        first_screen = self.readme.split("## What it does", 1)[0]
        self.assertIn("docs/images/eval-chart.svg", first_screen)
        chart = ROOT / "docs" / "images" / "eval-chart.svg"
        self.assertTrue(chart.is_file())
        self.assertIn("8 of 8", chart.read_text(encoding="utf-8"))

    def test_the_eval_chart_keeps_its_paired_eval_content(self):
        chart = (ROOT / "docs" / "images" / "eval-chart.svg").read_text(
            encoding="utf-8"
        )
        for fragment in (
            "Paired eval results",
            "Planted defects found across four fixture tasks",
            "Packet pass",
            "Raw diff pass",
            "4 of 8",
            "On defects inside the diff the passes tied at 4 of 4 each.",
            "In unchanged files the packet found 4 of 4 and the raw "
            "pass found 0 of 4.",
            "Every defect the raw pass missed lived in a file the "
            "diff never showed.",
            "evals/RESULTS.md",
        ):
            self.assertIn(fragment, chart, fragment)
        self.assertNotIn("hosted", chart)

    def test_the_eval_caption_keeps_its_pinned_claims(self):
        for fragment in (
            "Eight planted defects across four fixture tasks.",
            "The packet pass found 8 of 8 and the raw diff "
            "pass found 4 of 8.",
            "A defect in an unchanged file is unreachable by "
            "a raw diff pass by construction, because the pass "
            "holds no content from any unchanged file.",
            "On the defects inside the diff itself the two "
            "passes tied at 4 of 4 each.",
            "[the paired eval results](evals/RESULTS.md)",
        ):
            self.assertIn(fragment, self.flat)

    def test_the_example_packet_is_complete_and_verified(self):
        folder = ROOT / "examples" / "example-packet-991ac6a"
        packet = (folder / "packet.md").read_text(encoding="utf-8")
        self.assertEqual(len(packet.splitlines()), 626)
        manifest = json.loads(
            (folder / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertIs(manifest["verified"], True)
        self.assertEqual(manifest["discrepancies"], [])
        self.assertEqual(
            manifest["head"],
            "991ac6ae80d3c00c0b6c7fc06a4a35bdafb2d965",
        )
        self.assertEqual(
            manifest["base"],
            "eba549658f9c21e78115f6caf96034dd142af4e6",
        )

    def test_the_examples_entry_note_and_readme_link_resolve(self):
        entry = (ROOT / "examples" / "README.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "one complete real packet a visitor can open "
            "without installing anything",
            " ".join(entry.split()),
        )
        self.assertIn(
            "example-packet-991ac6a/packet.md", entry
        )
        self.assertIn(
            "example-packet-991ac6a/manifest.json", entry
        )
        self.assertIn(
            "[the examples folder](examples/README.md)", self.readme
        )

    def test_the_quickstart_names_the_verified_commit(self):
        first_screen = self.readme.split("## What it does", 1)[0]
        self.assertIn("**Sixty second quickstart**", first_screen)
        self.assertIn("--commit 991ac6a", first_screen)
        self.assertIn(
            "For reviewers and the agents who assist them, "
            "judging a pull request or a commit range they did "
            "not write",
            self.flat,
        )
        for step in ("1. Clone this repo", "2. Build a packet",
                     "3. Read the verdict", "4. Open `packet.md`"):
            self.assertIn(step, first_screen)

    def test_the_objections_answer_their_three_questions(self):
        objections = self.readme.split("## Objections", 1)[1].split(
            "## Install", 1
        )[0]
        positions = []
        for heading in (
            "### Why not just run gh pr diff",
            "### Why does it run locally",
            "### What verified does not mean",
        ):
            self.assertIn(heading, objections)
            positions.append(objections.index(heading))
        self.assertEqual(positions, sorted(positions))
        self.assertIn(
            "Verified does not prove the change is correct "
            "or safe",
            " ".join(objections.split()),
        )
        self.assertLess(
            self.readme.index("## Objections"),
            self.readme.index("## Install"),
        )


def _gif_lzw_decode(data, min_code_size):
    """Decode one GIF LZW stream with the standard library only."""
    out = bytearray()
    clear = 1 << min_code_size
    eoi = clear + 1
    code_size = min_code_size + 1
    table = None

    def reset():
        return {i: bytes([i]) for i in range(clear)}

    table = reset()
    next_code = eoi + 1
    bitpos = 0
    prev = None

    def read_code():
        nonlocal bitpos
        byte_i = bitpos // 8
        shift = bitpos % 8
        chunk = int.from_bytes(data[byte_i:byte_i + 4].ljust(4, b"\x00"), "little")
        code = (chunk >> shift) & ((1 << code_size) - 1)
        bitpos += code_size
        return code

    while True:
        code = read_code()
        if code == clear:
            table = reset()
            code_size = min_code_size + 1
            next_code = eoi + 1
            prev = None
            continue
        if code == eoi:
            break
        if prev is None:
            entry = table[code]
            out += entry
            prev = entry
            continue
        if code in table:
            entry = table[code]
        else:
            entry = prev + prev[:1]
        out += entry
        table[next_code] = prev + entry[:1]
        next_code += 1
        if next_code == (1 << code_size) and code_size < 12:
            code_size += 1
        prev = entry
    return bytes(out)


def _gif_frames(path):
    """Return (width, height, frames, delays_ms) for one GIF.

    Each frame is the composited full canvas as flat RGB
    bytes after that frame is applied, decoded with the
    standard library only. The WP1 encode carries local
    palettes and a transparency index for unchanged pixels,
    so compositing is the only honest read of a frame. The
    palette argument the older form returned is gone, and
    _bright_fraction reads the RGB bytes directly.
    """
    raw = path.read_bytes()
    assert raw[:6] in (b"GIF89a", b"GIF87a"), "not a GIF file"
    width = int.from_bytes(raw[6:8], "little")
    height = int.from_bytes(raw[8:10], "little")
    packed = raw[10]
    pos = 13
    global_palette = []
    if packed & 0x80:
        count = 2 ** ((packed & 0x07) + 1)
        for i in range(count):
            global_palette.append(
                tuple(raw[13 + 3 * i:16 + 3 * i])
            )
        pos += 3 * count
    canvas = bytearray(width * height * 3)
    frames = []
    delays = []
    delay = 0
    transparent = None
    while pos < len(raw):
        marker = raw[pos]
        if marker == 0x3B:
            break
        if marker == 0x21:
            label = raw[pos + 1]
            if label == 0xF9:
                delay = int.from_bytes(
                    raw[pos + 4:pos + 6], "little"
                ) * 10
                if raw[pos + 3] & 0x01:
                    transparent = raw[pos + 6]
                else:
                    transparent = None
                pos += 8
            else:
                pos += 2
                while raw[pos]:
                    pos += raw[pos] + 1
                pos += 1
        elif marker == 0x2C:
            left = int.from_bytes(raw[pos + 1:pos + 3], "little")
            top = int.from_bytes(raw[pos + 3:pos + 5], "little")
            fw = int.from_bytes(raw[pos + 5:pos + 7], "little")
            fh = int.from_bytes(raw[pos + 7:pos + 9], "little")
            fpacked = raw[pos + 9]
            pos += 10
            palette = global_palette
            if fpacked & 0x80:
                count = 2 ** ((fpacked & 0x07) + 1)
                palette = [
                    tuple(raw[pos + 3 * i:pos + 3 * i + 3])
                    for i in range(count)
                ]
                pos += 3 * count
            min_code = raw[pos]
            pos += 1
            chunks = bytearray()
            while raw[pos]:
                chunks += raw[pos + 1:pos + 1 + raw[pos]]
                pos += raw[pos] + 1
            pos += 1
            indices = _gif_lzw_decode(bytes(chunks), min_code)
            for y in range(fh):
                for x in range(fw):
                    idx = indices[y * fw + x]
                    if idx == transparent or idx >= len(palette):
                        continue
                    r, g, b = palette[idx]
                    off = ((top + y) * width + (left + x)) * 3
                    canvas[off:off + 3] = bytes((r, g, b))
            frames.append(bytes(canvas))
            delays.append(delay)
            delay = 0
            transparent = None
        else:
            raise AssertionError("unexpected GIF block %r" % marker)
    return width, height, frames, delays


def _bright_fraction(rgb_bytes):
    """Share of pixels whose channel sum clears the floor."""
    if not rgb_bytes:
        return 0.0
    bright = 0
    pixels = len(rgb_bytes) // 3
    for i in range(0, len(rgb_bytes), 3):
        if rgb_bytes[i] + rgb_bytes[i + 1] + rgb_bytes[i + 2] > 90:
            bright += 1
    return bright / pixels


def _png_pixels(path):
    """Return (width, height, rows) for an RGB PNG file.

    Each row is a list of (red, green, blue) tuples, decoded
    with the standard library only. The shipped demo stills
    are 8 bit RGB files with no interlace, and anything else
    fails here rather than passing unexamined.
    """
    raw = path.read_bytes()
    assert raw[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG file"
    width, height, depth, color = struct.unpack(">IIBB", raw[16:26])
    assert (depth, color, raw[28]) == (8, 2, 0), "unexpected PNG form"
    idat = bytearray()
    pos = 8
    while pos < len(raw):
        size = int.from_bytes(raw[pos:pos + 4], "big")
        kind = raw[pos + 4:pos + 8]
        if kind == b"IDAT":
            idat += raw[pos + 8:pos + 8 + size]
        pos += size + 12
    data = zlib.decompress(bytes(idat))
    stride = width * 3
    rows = []
    prev = bytearray(stride)
    pos = 0
    for _y in range(height):
        filt = data[pos]
        line = bytearray(data[pos + 1:pos + 1 + stride])
        pos += stride + 1
        for x in range(stride):
            left = line[x - 3] if x >= 3 else 0
            up = prev[x]
            corner = prev[x - 3] if x >= 3 else 0
            if filt == 1:
                line[x] = (line[x] + left) & 0xFF
            elif filt == 2:
                line[x] = (line[x] + up) & 0xFF
            elif filt == 3:
                line[x] = (line[x] + (left + up) // 2) & 0xFF
            elif filt == 4:
                guess = left + up - corner
                pick_a = abs(guess - left)
                pick_b = abs(guess - up)
                pick_c = abs(guess - corner)
                if pick_a <= pick_b and pick_a <= pick_c:
                    pred = left
                elif pick_b <= pick_c:
                    pred = up
                else:
                    pred = corner
                line[x] = (line[x] + pred) & 0xFF
            elif filt != 0:
                raise AssertionError("unexpected PNG filter %r" % filt)
        rows.append(
            [tuple(line[i:i + 3]) for i in range(0, stride, 3)]
        )
        prev = line
    return width, height, rows


class TestRound6PublicClaims(unittest.TestCase):
    """Round 6 pins on public claims the gates used to leave free.

    The round 6 audit plants renamed a capability in the
    README plugin table, softened the shallow clone limit in
    README prose, renamed a tier in the README naming
    sentence and set a contradictory figure into the eval
    chart title, and every gate read green on each plant.
    These tests pin the README tier names against the
    example packet, the spawn gate name against the plugin
    manifest that carries it, the shallow clone limit
    against the skill text, the chart title and description
    as exact text, and the release file against naming a
    standing tag candidate in the present tense.
    """

    def setUp(self):
        self.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.flat = " ".join(self.readme.split())

    def test_readme_tier_names_match_the_example_packet(self):
        sentence = (
            "The four tiers are T0 Triage, T1 The change, "
            "T2 Companions and T3 History."
        )
        self.assertIn(sentence, self.flat)
        packet = (
            ROOT / "examples" / "example-packet-991ac6a" / "packet.md"
        ).read_text(encoding="utf-8")
        listed = re.findall(
            r"^- (T[0-3] (?:Triage|The change|Companions|History))$",
            packet,
            flags=re.M,
        )
        self.assertEqual(
            listed,
            [
                "T0 Triage",
                "T1 The change",
                "T2 Companions",
                "T3 History",
            ],
        )
        for name in listed:
            self.assertIn("## " + name, packet)

    def test_readme_spawn_gate_name_matches_the_manifest(self):
        self.assertIn(
            "recognitio-mod | The spawn gate on its own", self.flat
        )
        self.assertIn(
            "with the spawn gate mod included", self.flat
        )
        self.assertIn(
            "brings the spawn gate the Claude Code plugin "
            "subsection describes",
            self.flat,
        )
        package = json.loads(
            (ROOT / "agent-plugins-package" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )
        long_description = package["extensions"]["com.openai"][
            "interface"
        ]["longDescription"]
        self.assertIn(
            "the spawn gate on its own", long_description
        )
        release = (ROOT / "docs" / "release-1.3.0.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "the Build 7 spawn gate mod",
            " ".join(release.split()),
        )

    def test_readme_shallow_clone_limit_matches_the_skill(self):
        fragment = "A shallow clone is refused outright"
        self.assertIn(fragment, self.flat)
        skill = (
            ROOT / ".agents" / "skills" / "recognitio" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn(fragment, skill)
        persona = (ROOT / "agents" / "reviewer.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(fragment, persona)

    def test_eval_chart_title_and_description_are_exact(self):
        chart = (ROOT / "docs" / "images" / "eval-chart.svg").read_text(
            encoding="utf-8"
        )
        title = re.search(
            r'<title id="chartTitle">([^<]+)</title>', chart
        )
        desc = re.search(r'<desc id="chartDesc">([^<]+)</desc>', chart)
        self.assertIsNotNone(title)
        self.assertIsNotNone(desc)
        self.assertEqual(
            title.group(1),
            "Paired eval results. The packet pass found 8 of 8 "
            "planted defects and the raw diff pass found 4 of 8.",
        )
        self.assertEqual(
            desc.group(1),
            "Two bars on a scale of eight. On the defects inside "
            "the diff the two passes tied at 4 of 4 each. In "
            "unchanged files the packet pass found 4 of 4 and "
            "the raw diff pass found 0 of 4.",
        )
        # The visible labels carry the same figures, and the
        # README alt text restates them, so each figure stands
        # in the chart exactly twice and the alt sentence is
        # pinned word for word.
        self.assertEqual(chart.count("8 of 8"), 2)
        self.assertEqual(chart.count("4 of 8"), 2)
        self.assertEqual(chart.count("4 of 4"), 4)
        self.assertEqual(chart.count("0 of 4"), 2)
        self.assertIn(
            "Paired eval chart. The packet pass found 8 of 8 "
            "planted defects and the raw diff pass found 4 of 8.",
            self.readme,
        )

    def test_release_file_names_no_standing_tag_candidate(self):
        release = (ROOT / "docs" / "release-1.3.0.md").read_text(
            encoding="utf-8"
        )
        flat = " ".join(release.split())
        self.assertIn(
            "No tag candidate stands named on the face of this "
            "file while the tag stays held.",
            flat,
        )
        self.assertNotIn(
            "The tag candidate head for this release is", flat
        )
        # The claim must not survive in another word order or
        # in another section of the same file. The release
        # notes name no candidate at all, and the checklist
        # holds exactly the three standing mentions of the
        # candidate head its items carry, so a claim added to
        # either section in any wording raises one of these
        # readings.
        self.assertNotIn("tag candidate head", flat)
        self.assertNotIn("as the tag candidate", flat)
        self.assertNotIn("current head of main", flat)
        notes = release.split("## Release notes", 1)[1].split(
            "## The tag checklist", 1
        )[0]
        self.assertNotIn("candidate", notes.lower())
        checklist = release.split("## The tag checklist", 1)[1]
        self.assertEqual(checklist.lower().count("candidate"), 3)


class TestDocsIndex(unittest.TestCase):
    """The visual round 7 docs index and navigation pins.

    The docs index at `docs/README.md` lists every document
    in the docs set exactly once with a relative link that
    resolves, every document opens with a back link to the
    index, and every brief closes with the navigation block
    after its final section, so the set cannot quietly return
    to a pile of unlinked pages.
    """

    DOCS = (
        "agent-plugins-brief.md",
        "antigravity-plugin-brief.md",
        "coderabbit-review-brief.md",
        "comate-brief.md",
        "codex-plugin-brief.md",
        "codex-review-brief.md",
        "copilot-sdk-brief.md",
        "cursor-plugin-brief.md",
        "decisions.md",
        "devin-playbook-brief.md",
        "headless-review.md",
        "kimi-plugin-brief.md",
        "mod-build7.md",
        "principles.md",
        "qwen-code-brief.md",
        "release-1.3.0.md",
        "reviewer-persona.md",
        "submission-agent-plugins.md",
        "submission-claude.md",
        "submission-cursor.md",
        "zcode-plugin-brief.md",
    )
    BRIEFS = (
        "agent-plugins-brief.md",
        "antigravity-plugin-brief.md",
        "coderabbit-review-brief.md",
        "comate-brief.md",
        "codex-plugin-brief.md",
        "codex-review-brief.md",
        "copilot-sdk-brief.md",
        "cursor-plugin-brief.md",
        "devin-playbook-brief.md",
        "kimi-plugin-brief.md",
        "mod-build7.md",
        "qwen-code-brief.md",
        "zcode-plugin-brief.md",
    )
    BACK_LINK = "[Back to the documentation index](README.md)"
    NAV_BLOCK = (
        "- [Documentation index](README.md)\n"
        "- [Decisions](decisions.md)\n"
        "- [Principles](principles.md)"
    )

    # WP4. The filed records under docs join the index, so the
    # listing pin grows from the top level set to every Markdown
    # document under docs. The back link pin below stays scoped
    # to the top level set, because the filed records are dated
    # reports that keep the heads they were filed with.
    FILED = (
        "images/capture-record.md",
        "reviews/round4-fix-review.md",
        "reviews/round6-fix-review.md",
        "reviews/round7-fix-review.md",
        "reviews/round8-fix-review.md",
        "reviews/round9-fix-review.md",
        "reviews/round11-fix-review.md",
        "reviews/round12-fix-review.md",
        "reviews/round13-fix-review.md",
        "reviews/round14-fix-review.md",
    )

    def test_the_index_lists_every_document_once_and_links_resolve(self):
        index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
        targets = re.findall(r"\]\(([^)]+\.md)\)", index)
        self.assertEqual(sorted(targets), sorted(self.DOCS + self.FILED))
        for target in targets:
            self.assertTrue((ROOT / "docs" / target).is_file(), target)

    def test_every_document_opens_with_the_back_link(self):
        for name in self.DOCS:
            text = (ROOT / "docs" / name).read_text(encoding="utf-8")
            self.assertEqual(text.splitlines()[0], self.BACK_LINK, name)

    # WP7. The submission packs adopt the brief furniture, the
    # summary card and the closing navigation block, without
    # joining the briefs list, whose anchor rule names a
    # section the packs do not carry. Their furniture stands
    # pinned here instead, so a pack cannot drop its card or
    # its closing block in silence either.
    PACKS = (
        "submission-agent-plugins.md",
        "submission-claude.md",
        "submission-cursor.md",
    )

    def test_the_packs_carry_the_card_and_the_navigation(self):
        labels = (
            "**What ships**",
            "**What was proven**",
            "**What is unverified**",
        )
        for name in self.PACKS:
            text = (ROOT / "docs" / name).read_text(encoding="utf-8")
            positions = []
            for label in labels:
                self.assertEqual(text.count(label), 1, (name, label))
                positions.append(text.index(label))
            self.assertEqual(positions, sorted(positions), name)
            self.assertLess(
                text.index("## At a glance"),
                text.index("## Summary"),
                name,
            )
            self.assertIn(self.NAV_BLOCK, text, name)
            self.assertGreater(
                text.index(self.NAV_BLOCK),
                text.index("## Sources"),
                name,
            )

    def test_every_brief_closes_with_the_navigation_block(self):
        for name in self.BRIEFS:
            text = (ROOT / "docs" / name).read_text(encoding="utf-8")
            self.assertIn(self.NAV_BLOCK, text, name)
            # The Qwen brief carries no Skill tightness section,
            # so its rules heading is the anchor there instead.
            anchor = (
                "## The Qwen rules"
                if name == "qwen-code-brief.md"
                else "## Skill tightness"
            )
            self.assertGreater(
                text.index(self.NAV_BLOCK),
                text.index(anchor),
                name,
            )


class TestWp4Docs(unittest.TestCase):
    """The WP4 docs depth pins.

    Every platform brief opens with the same three field summary
    card between its title and its summary section, the principles
    page carries its failure to packet graphic with the palette
    values and the story strings the page itself proves, and the
    headless runbook carries its denial rule in one place only
    after its lean pass, so a later edit cannot drop the card,
    hollow the graphic, or redouble the runbook claim in silence.
    """

    CARD_LABELS = (
        "**What ships**",
        "**What was proven**",
        "**What is unverified**",
    )

    def test_every_brief_opens_with_the_summary_card(self):
        for name in TestDocsIndex.BRIEFS:
            text = (ROOT / "docs" / name).read_text(encoding="utf-8")
            self.assertIn("## At a glance", text, name)
            positions = []
            for label in self.CARD_LABELS:
                self.assertEqual(text.count(label), 1, (name, label))
                positions.append(text.index(label))
            self.assertEqual(positions, sorted(positions), name)
            self.assertLess(text.index("# "), text.index("## At a glance"), name)
            self.assertLess(
                text.index("## At a glance"), text.index("## Summary"), name
            )
            self.assertLess(
                text.index("**What is unverified**"),
                text.index("## Summary"),
                name,
            )

    def test_the_principles_graphic_carries_the_page_story(self):
        page = (ROOT / "docs" / "principles.md").read_text(encoding="utf-8")
        self.assertIn("images/principles-packet-story.svg", page)
        svg = (
            ROOT / "docs" / "images" / "principles-packet-story.svg"
        ).read_text(encoding="utf-8")
        for fragment in (
            ">The hosted diff<",
            ">The packet from the local clone<",
            "The failure to packet story.",
            "From a silent summary to a counted packet",
            "The failure behind the first principle on this page, "
            "in one frame",
            "File counts capped by the service",
            "Oversized patches dropped whole",
            "No flag on either loss",
            "Success reported over the top",
            "Each silence passes downstream unseen",
            "Extraction reads git objects on disk",
            "The packet lists the whole range",
            "An unaccounted file fails the run",
            "Nothing passes unnoticed",
            "The packet list is the range list",
            "No check downstream can restore a file the source "
            "never mentioned.",
            "Source. The failure record stated in the first "
            "section of this page.",
        ):
            self.assertEqual(svg.count(fragment), 1, fragment)
        for invented in (
            "Patch text cut past a size ceiling",
            "Every file from git itself",
            "Full patch text at any size",
            "The packet is built from the local clone",
        ):
            self.assertNotIn(invented, svg, invented)
        for value in ("#13151B", "#181B23", "#343842", "#D97757", "#4AC76A"):
            self.assertIn(value, svg, value)

    def test_the_headless_runbook_carries_the_denial_rule_once(self):
        text = (ROOT / "docs" / "headless-review.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual(text.count("permission_denials"), 1)
        self.assertIn(
            "when any permission denied system message stands anywhere",
            text,
        )
        self.assertIn(
            "when the field is missing from the result altogether",
            text,
        )
        self.assertNotIn("the authoritative", text)


class TestDemoAssets(unittest.TestCase):
    """The demo asset gate, rebuilt for the money shot landing.

    The visual round 3 gate pinned the chat capture and its
    stills gallery, and round 6 grew it over the border ring
    and the detail crop. The money shot landing after the
    visual program retires that whole asset set, because the
    pixel inspection condemned the stills as dark fields and
    the crop as a cut off strip, and replaces it with one
    recording of a live Cursor agent session over the same
    change and one poster frame from it. The pins below hold
    the new set. The ring pins retire with the assets they
    described, because the recorded frames carry the terminal
    ground to the canvas edge and no builder ring was applied
    to this capture, and re-encoding a verified capture to
    paint one on would alter the record the capture stands
    as. The clipped band check retires for the same reason,
    because the band geometry belonged to the retired chat
    card header and this recording has no such header.
    The storefront WP3 landing then moves the hero slot to
    the Claude Code session with the mod installed, filmed
    over the same range, and the pins below move to that
    set in the same change. The Cursor set stays in the
    tree, and its poster stands in the proof strip under
    the pins of TestProofStrip.
    """

    IMAGES = ROOT / "docs" / "images"
    HERO = IMAGES / "recognitio-claude-code-demo.gif"
    POSTER = "recognitio-claude-code-poster.png"
    RETIRED = (
        "recognitio-demo-chat.gif",
        "recognitio-demo-poster.png",
        "recognitio-demo-poster-detail.png",
        "recognitio-demo-still-diff.png",
        "recognitio-demo-still-verified.png",
        "recognitio-demo-still-verdict.png",
        "recognitio-cursor-agent-demo-short.gif",
        "recognitio-cursor-agent-verified-crop.png",
    )
    POSTER_GEOMETRY = (792, 570)
    POSTER_SHA256 = (
        "be23a2ef5dd00540ba12670db155da81fdd25acb2f2fcb0842f7c00ada691935"
    )
    # The byte budget moved down for WP1 in the open. The
    # work order set a 700,000 byte target for the captioned
    # re-encode, and the budget now stands at that target
    # rather than the 1,400,000 the first money shot landing
    # set. The Claude Code hero that WP3 moves into the
    # hero slot weighs 546,582 bytes, under the same budget,
    # so the budget does not move.
    BYTE_BUDGET = 700000

    def test_the_hero_dimensions_and_byte_budget_are_pinned(self):
        width, height, _frames, _delays = _gif_frames(self.HERO)
        self.assertEqual((width, height), (792, 608))
        self.assertLessEqual(self.HERO.stat().st_size, self.BYTE_BUDGET)

    def test_frame_zero_carries_content(self):
        _w, _h, frames, _delays = _gif_frames(self.HERO)
        # The WP1 hero opens on the Claude Code welcome
        # screen, sparse bright text on the dark terminal
        # ground. The repair round re-encode opens on the
        # same screen with the prompt standing in it, whose
        # composited bright share measures 0.0498. The floor
        # stands at 0.04, four fifths of that measure and
        # well above a blank frame.
        self.assertGreater(_bright_fraction(frames[0]), 0.04)

    def test_the_verdict_rest_frame_is_present_and_clean(self):
        _w, _h, frames, delays = _gif_frames(self.HERO)
        # The hero encode pins, re-derived from the shipped
        # file after the repair round re-encode. It carries
        # 21 frames over 28,770 ms in total, with the
        # closing verdict frame held for 2,400 ms.
        self.assertEqual(len(frames), 21)
        self.assertEqual(sum(delays), 28770)
        self.assertEqual(delays[-1], 2400)
        last = frames[-1]
        # The brightness floor is re-derived from this last
        # frame, whose composited bright share measures
        # 0.1238. The floor stands at 0.08, under that
        # measure and well above a dark field.
        self.assertGreater(_bright_fraction(last), 0.08)

    def test_the_short_cut_geometry_and_timing_are_pinned(self):
        path = self.IMAGES / "recognitio-claude-code-demo-short.gif"
        self.assertTrue(path.is_file())
        width, height, frames, delays = _gif_frames(path)
        self.assertEqual((width, height), (792, 608))
        self.assertEqual(len(frames), 10)
        self.assertEqual(sum(delays), 4600)
        self.assertEqual(path.stat().st_size, 187062)

    def test_the_phone_crop_geometry_and_hash_are_pinned(self):
        path = (
            self.IMAGES
            / "recognitio-claude-code-verified-crop.png"
        )
        self.assertTrue(path.is_file())
        width, height, _rows = _png_pixels_any(path)
        self.assertEqual((width, height), (544, 95))
        found = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(
            found,
            "82d3a849233b8ac0af3d0c1ee35d2ebd3"
            "eeff21fe89c09305082984ebb12edb6",
        )

    def test_the_poster_exists_as_a_png_frame(self):
        path = self.IMAGES / self.POSTER
        self.assertTrue(path.is_file(), self.POSTER)
        self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        self.assertGreater(path.stat().st_size, 5000)

    def test_the_poster_geometry_and_hash_are_pinned(self):
        path = self.IMAGES / self.POSTER
        width, height, _rows = _png_pixels(path)
        self.assertEqual((width, height), self.POSTER_GEOMETRY)
        found = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(found, self.POSTER_SHA256)

    def test_the_retired_assets_stay_out_of_the_tree(self):
        for name in self.RETIRED:
            self.assertFalse((self.IMAGES / name).is_file(), name)

    def test_every_readme_image_reference_resolves(self):
        # The page names the poster still as a link inside
        # the demo lead in and embeds the recording itself,
        # and the lead in also links the capture record and
        # the short cut of the same session as plain links,
        # and every reference it carries resolves. The top 20
        # program added the session stills of item 18 and the
        # link to their capture record, and the list below is
        # the page order the two finds return, links first
        # and then embeds. The visual fix pass added a phone
        # width source in front of each output style still,
        # and each source stands in the list ahead of the
        # still it replaces on a narrow screen. The links
        # and the embeds are collected as two passes, every
        # bracketed link in page order and then every src and
        # srcset in page order. The video standard programme
        # wrapped the hero preview and each proof frame in a
        # link to its film or clip. Those wrapped anchors are
        # HTML hrefs, which the bracketed link pass never
        # collects, so they stand in no list here and
        # TestVideoForms pins them instead. The bracketed
        # film links the lead in and the Cursor caption carry
        # stand in the link pass at their page positions
        # below. No retired asset name may return to the page.
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        refs = re.findall(r"\]\((docs/images/[^)]+)\)", readme)
        refs += re.findall(
            r"(?:src|srcset)=\"(docs/images/[^\"]+)\"", readme
        )
        self.assertEqual(
            refs,
            [
                "docs/images/capture-record.md",
                "docs/images/recognitio-claude-code-poster.png",
                "docs/images/recognitio-claude-code-demo-short.gif",
                "docs/images/recognitio-claude-code-demo.mp4",
                "docs/images/recognitio-claude-code-demo.webm",
                "docs/images/capture-record.md",
                "docs/images/capture-record.md",
                "docs/images/recognitio-cursor-agent-demo.mp4",
                "docs/images/recognitio-cursor-agent-demo.webm",
                "docs/images/capture-record.md",
                "docs/images/capture-record.md",
                "docs/images/capture-record.md",
                "docs/images/recognitio-claude-code-verified-crop.png",
                "docs/images/recognitio-claude-code-demo.gif",
                "docs/images/recognitio-session-claude-code-denial-phone.png",
                "docs/images/recognitio-session-claude-code-denial.png",
                "docs/images/recognitio-session-codex-verified-phone.png",
                "docs/images/recognitio-session-codex-verified.png",
                "docs/images/recognitio-cursor-agent-poster-phone.png",
                "docs/images/recognitio-cursor-agent-poster.png",
                "docs/images/recognitio-session-qwen-summary-phone.png",
                "docs/images/recognitio-session-qwen-summary.png",
                "docs/images/eval-chart.svg",
                "docs/images/recognitio-session-style-tiers-phone.png",
                "docs/images/recognitio-session-style-tiers.png",
                "docs/images/recognitio-session-style-change-phone.png",
                "docs/images/recognitio-session-style-change.png",
                "docs/images/recognitio-session-style-recount-phone.png",
                "docs/images/recognitio-session-style-recount.png",
            ],
        )
        for ref in refs:
            self.assertTrue((ROOT / ref).is_file(), ref)
        for name in self.RETIRED:
            self.assertNotIn(name, readme)
        self.assertNotIn("recognitio-demo-terminal", readme)


def _mp4_facts(path):
    """Return video facts for one MP4 file.

    The probe reads the ISO box structure with the standard
    library only and returns width and height and duration
    in seconds and the video sample count and the total
    video sample bytes the sample size table names. It
    walks the boxes to the moov box, reads the movie header
    timescale and duration, and walks to the first video
    track's sample entry for its width and height. The
    sample entry must carry a codec record the probe
    parses in full, holding a version and a sequence
    parameter set and a picture parameter set, and the
    timing and size tables must name samples and bytes.
    The probe then lays every sample out through the
    chunk tables and requires each one to stand inside
    a media data box, so a file whose tables claim bytes
    its media boxes do not hold cannot pass either. The
    probe then reads the head of every placed sample as
    a coded unit, holding each unit length inside its
    sample and each unit header inside the coded unit
    types, and requires the first sample to tile into
    units whole and to hold a picture unit, so a media
    box of unwritten bytes cannot pass however honest
    its tables stand. A header shell with no frames
    cannot pass. Every box on every walk must end inside the bytes the
    walk reads, so a file cut short fails here rather than
    passing on its surviving header. A file that does not
    carry this structure is not an MP4 the gate can
    certify, and the probe fails here rather than passing
    it unexamined. Malformed input fails as an
    AssertionError, because the probe's verdict is the only
    thing its callers read.
    """
    raw = path.read_bytes()
    try:
        return _mp4_facts_inner(raw)
    except (IndexError, struct.error):
        raise AssertionError("the MP4 structure is truncated")


def _mp4_facts_inner(raw):
    assert raw[4:8] == b"ftyp", "not an MP4 file"

    def boxes(start, end):
        pos = start
        while pos + 8 <= end:
            size = int.from_bytes(raw[pos:pos + 4], "big")
            kind = raw[pos + 4:pos + 8]
            header = 8
            if size == 1:
                size = int.from_bytes(
                    raw[pos + 8:pos + 16], "big"
                )
                header = 16
            elif size == 0:
                size = end - pos
            assert size >= header, "a box shorter than its header"
            assert pos + size <= end, (
                "a box ends past the bytes under it"
            )
            yield kind, pos + header, pos + size
            pos += size

    def find(start, end, kind):
        for found, body, stop in boxes(start, end):
            if found == kind:
                return body, stop
        raise AssertionError("no %s box in the MP4" % kind)

    # The walk above never steps into the media data box,
    # so this pass drives the top level walk to completion
    # over it. The point of the pass is the driving, because
    # a media box that ends past the file is a cut the
    # header facts alone would never show. The pass also
    # keeps the span of every media box, because the sample
    # placement check below reads them.
    media_spans = []
    for _kind, _body, stop in boxes(0, len(raw)):
        assert stop <= len(raw), "a top level box ends past the file"
        if _kind == b"mdat":
            media_spans.append((_body, stop))

    moov_body, moov_end = find(0, len(raw), b"moov")
    mvhd_body, _ = find(moov_body, moov_end, b"mvhd")
    version = raw[mvhd_body]
    if version == 1:
        timescale = int.from_bytes(
            raw[mvhd_body + 20:mvhd_body + 24], "big"
        )
        duration = int.from_bytes(
            raw[mvhd_body + 24:mvhd_body + 32], "big"
        )
    else:
        timescale = int.from_bytes(
            raw[mvhd_body + 12:mvhd_body + 16], "big"
        )
        duration = int.from_bytes(
            raw[mvhd_body + 16:mvhd_body + 20], "big"
        )
    assert timescale > 0, "the MP4 movie header names no timescale"
    width = height = None
    samples = 0
    config = False
    payload = 0
    placed = 0
    nal_size = 4
    for kind, body, stop in boxes(moov_body, moov_end):
        if kind != b"trak":
            continue
        try:
            mdia_body, mdia_end = find(body, stop, b"mdia")
            minf_body, minf_end = find(mdia_body, mdia_end, b"minf")
            stbl_body, stbl_end = find(minf_body, minf_end, b"stbl")
            stsd_body, _ = find(stbl_body, stbl_end, b"stsd")
        except AssertionError:
            continue
        entry = stsd_body + 8
        if raw[entry + 4:entry + 8] not in (b"avc1", b"avc3"):
            continue
        width = int.from_bytes(raw[entry + 32:entry + 34], "big")
        height = int.from_bytes(raw[entry + 34:entry + 36], "big")
        size_field = int.from_bytes(raw[entry:entry + 4], "big")
        record = raw[entry + 8 + 78:entry + size_field]
        assert record[4:8] == b"avcC", (
            "the video sample entry carries no codec record"
        )
        rec_size = int.from_bytes(record[0:4], "big")
        assert 8 < rec_size <= len(record), (
            "the codec record is cut inside the sample entry"
        )
        avcc = record[8:rec_size]
        assert avcc[0] == 1, "the codec record names no version"
        sps_count = avcc[5] & 0x1F
        assert sps_count >= 1, (
            "the codec record names no sequence parameter set"
        )
        at = 6
        for _ in range(sps_count):
            assert at + 2 <= len(avcc), (
                "the codec record sequence parameter set is cut"
            )
            sps_len = int.from_bytes(avcc[at:at + 2], "big")
            at += 2
            assert 1 <= sps_len and at + sps_len <= len(avcc), (
                "the codec record sequence parameter set is cut"
            )
            at += sps_len
        assert at < len(avcc), (
            "the codec record names no picture parameter set"
        )
        pps_count = avcc[at]
        assert pps_count >= 1, (
            "the codec record names no picture parameter set"
        )
        at += 1
        for _ in range(pps_count):
            assert at + 2 <= len(avcc), (
                "the codec record picture parameter set is cut"
            )
            pps_len = int.from_bytes(avcc[at:at + 2], "big")
            at += 2
            assert 1 <= pps_len and at + pps_len <= len(avcc), (
                "the codec record picture parameter set is cut"
            )
            at += pps_len
        nal_size = (avcc[4] & 0x03) + 1
        config = True
        sizes = []
        runs = []
        offsets = []
        try:
            stts_body, _ = find(stbl_body, stbl_end, b"stts")
            count = int.from_bytes(
                raw[stts_body + 4:stts_body + 8], "big"
            )
            for i in range(count):
                samples += int.from_bytes(
                    raw[stts_body + 8 + i * 8:
                        stts_body + 12 + i * 8], "big"
                )
            stsz_body, _ = find(stbl_body, stbl_end, b"stsz")
            unit = int.from_bytes(
                raw[stsz_body + 4:stsz_body + 8], "big"
            )
            total = int.from_bytes(
                raw[stsz_body + 8:stsz_body + 12], "big"
            )
            if unit:
                payload = unit * total
                sizes = [unit] * total
            else:
                sizes = [
                    int.from_bytes(
                        raw[stsz_body + 12 + i * 4:
                            stsz_body + 16 + i * 4], "big"
                    )
                    for i in range(total)
                ]
                payload = sum(sizes)
        except AssertionError:
            samples = 0
            payload = 0
        try:
            stsc_body, _ = find(stbl_body, stbl_end, b"stsc")
            run_total = int.from_bytes(
                raw[stsc_body + 4:stsc_body + 8], "big"
            )
            for i in range(run_total):
                at = stsc_body + 8 + i * 12
                runs.append((
                    int.from_bytes(raw[at:at + 4], "big"),
                    int.from_bytes(raw[at + 4:at + 8], "big"),
                ))
            for name, wide in ((b"stco", 4), (b"co64", 8)):
                try:
                    off_body, _ = find(stbl_body, stbl_end, name)
                except AssertionError:
                    continue
                off_total = int.from_bytes(
                    raw[off_body + 4:off_body + 8], "big"
                )
                offsets = [
                    int.from_bytes(
                        raw[off_body + 8 + i * wide:
                            off_body + 8 + (i + 1) * wide], "big"
                    )
                    for i in range(off_total)
                ]
                break
        except AssertionError:
            pass
        if samples > 0:
            assert len(sizes) == samples, (
                "the size table names a sample count the "
                "timing table does not"
            )
            assert runs and offsets, (
                "the MP4 video samples name no chunk tables"
            )
            run_at = 0
            at_size = 0
            for chunk_at, chunk_off in enumerate(offsets, 1):
                while (
                    run_at + 1 < len(runs)
                    and runs[run_at + 1][0] <= chunk_at
                ):
                    run_at += 1
                pos = chunk_off
                for _ in range(runs[run_at][1]):
                    end = pos + sizes[at_size]
                    assert any(
                        start <= pos and end <= stop
                        for start, stop in media_spans
                    ), "a video sample stands outside the media data"
                    head = raw[pos:pos + nal_size]
                    assert len(head) == nal_size, (
                        "a video sample is cut at its head"
                    )
                    first_len = int.from_bytes(head, "big")
                    assert 1 <= first_len <= (
                        sizes[at_size] - nal_size
                    ), "a video sample opens on a unit past its end"
                    header = raw[pos + nal_size]
                    assert header >> 7 == 0 and (
                        header & 0x1F
                    ) in (
                        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12
                    ), "a video sample opens on no coded unit"
                    if at_size == 0:
                        types = []
                        cursor = pos
                        while cursor < end:
                            step = int.from_bytes(
                                raw[cursor:cursor + nal_size],
                                "big",
                            )
                            assert 1 <= step <= (
                                end - cursor - nal_size
                            ), (
                                "the first sample does not "
                                "tile into units"
                            )
                            types.append(
                                raw[cursor + nal_size] & 0x1F
                            )
                            cursor += nal_size + step
                        assert 1 in types or 5 in types, (
                            "the first sample holds "
                            "no picture unit"
                        )
                    pos = end
                    at_size += 1
                    placed += 1
            assert placed == samples, (
                "the chunk tables place fewer samples than "
                "the timing table names"
            )
        break
    assert width and height, "no video track sample entry in the MP4"
    assert samples > 0, "the MP4 video track names no samples"
    assert payload > 0, "the MP4 video samples name no bytes"
    assert placed == samples, (
        "the MP4 video samples do not stand inside the media data"
    )
    return width, height, duration / timescale, samples, payload


def _mp4_shell():
    """Build a header only MP4 shell with planted facts.

    The plant for the video gate. The shell carries an
    ftyp box, a movie header claiming a duration of 171.7
    seconds at a timescale of 1000, and one video track
    whose sample entry claims 1584 by 1216 over one media
    box of zero padding. It holds no codec record, no
    sample timing table, and no sample sizes, so a probe
    that reads frame evidence refuses it while a probe
    that reads only header claims passes it.
    """
    def box(kind, body):
        return (
            (len(body) + 8).to_bytes(4, "big") + kind + body
        )

    mvhd = (
        b"\x00\x00\x00\x00" + b"\x00" * 8
        + (1000).to_bytes(4, "big") + (171700).to_bytes(4, "big")
        + b"\x00" * 80
    )
    entry = (
        (86).to_bytes(4, "big") + b"avc1" + b"\x00" * 24
        + (1584).to_bytes(2, "big") + (1216).to_bytes(2, "big")
        + b"\x00" * 48
    )
    stsd = b"\x00" * 4 + (1).to_bytes(4, "big") + entry
    stbl = box(b"stbl", box(b"stsd", stsd))
    minf = box(b"minf", stbl)
    mdia = box(b"mdia", minf)
    trak = box(b"trak", mdia)
    moov = box(b"moov", box(b"mvhd", mvhd) + trak)
    ftyp = box(b"ftyp", b"isom" + b"\x00" * 12)
    mdat = box(b"mdat", b"\x00" * 105000)
    return ftyp + moov + mdat


def _mp4_table_shell(valid_record):
    """Build an MP4 whose tables claim frames it lacks.

    The second plant family for the video gate. The shell
    carries the planted movie header and sample entry of
    the header shell and adds a timing table claiming
    1717 samples and a size table claiming bytes for
    every one of them over the same media box of zero
    padding, and it names no chunk tables at all, so the
    claimed samples stand nowhere in the file. In the
    letters form the sample entry record holds the bare
    letters of a codec record at no box boundary. In the
    valid form the record parses in full, so only the
    sample placement check can refuse the shell.
    """
    def box(kind, body):
        return (
            (len(body) + 8).to_bytes(4, "big") + kind + body
        )

    mvhd = (
        b"\x00\x00\x00\x00" + b"\x00" * 8
        + (1000).to_bytes(4, "big") + (171700).to_bytes(4, "big")
        + b"\x00" * 80
    )
    if valid_record:
        avcc = (
            b"\x01\x64\x00\x28\xff\xe1"
            + (4).to_bytes(2, "big") + b"\x67\x64\x00\x28"
            + b"\x01" + (2).to_bytes(2, "big") + b"\x68\xee"
        )
        record = (
            (len(avcc) + 8).to_bytes(4, "big") + b"avcC" + avcc
        )
    else:
        record = b"\x00" * 14 + b"avcC" + b"\x00" * 8
    entry = (
        (86 + len(record)).to_bytes(4, "big") + b"avc1"
        + b"\x00" * 24
        + (1584).to_bytes(2, "big") + (1216).to_bytes(2, "big")
        + b"\x00" * 50
        + record
    )
    stsd = b"\x00" * 4 + (1).to_bytes(4, "big") + entry
    stts = (
        b"\x00" * 4 + (1).to_bytes(4, "big")
        + (1717).to_bytes(4, "big") + (1001).to_bytes(4, "big")
    )
    stsz = (
        b"\x00" * 4 + (5100).to_bytes(4, "big")
        + (1717).to_bytes(4, "big")
    )
    stbl = box(
        b"stbl",
        box(b"stsd", stsd) + box(b"stts", stts)
        + box(b"stsz", stsz),
    )
    minf = box(b"minf", stbl)
    mdia = box(b"mdia", minf)
    trak = box(b"trak", mdia)
    moov = box(b"moov", box(b"mvhd", mvhd) + trak)
    ftyp = box(b"ftyp", b"isom" + b"\x00" * 12)
    mdat = box(b"mdat", b"\x00" * 105000)
    return ftyp + moov + mdat


def _mp4_stream_shell(valid_record=True):
    """Build an MP4 whose placed samples hold no units.

    The third plant family for the video gate. The shell
    carries the codec record and adds the chunk tables
    the table shell lacks, with one chunk standing
    inside a media box of zero bytes sized to the size
    table claims, so the sample placement check stands
    satisfied and only the coded unit check on the
    sample bytes themselves can refuse it. In the
    letters form the record holds the bare letters of a
    codec record at no box boundary while every check
    before the record stands satisfied, so only the
    structural record parse can refuse that form, and
    the plant test reads its refusal message to prove
    the parse is the check that fired.
    """
    def box(kind, body):
        return (
            (len(body) + 8).to_bytes(4, "big") + kind + body
        )

    mvhd = (
        b"\x00\x00\x00\x00" + b"\x00" * 8
        + (1000).to_bytes(4, "big") + (171700).to_bytes(4, "big")
        + b"\x00" * 80
    )
    if valid_record:
        avcc = (
            b"\x01\x64\x00\x28\xff\xe1"
            + (4).to_bytes(2, "big") + b"\x67\x64\x00\x28"
            + b"\x01" + (2).to_bytes(2, "big") + b"\x68\xee"
        )
        record = (
            (len(avcc) + 8).to_bytes(4, "big") + b"avcC" + avcc
        )
    else:
        record = b"\x00" * 14 + b"avcC" + b"\x00" * 8
    entry = (
        (86 + len(record)).to_bytes(4, "big") + b"avc1"
        + b"\x00" * 24
        + (1584).to_bytes(2, "big") + (1216).to_bytes(2, "big")
        + b"\x00" * 50
        + record
    )
    stsd = b"\x00" * 4 + (1).to_bytes(4, "big") + entry
    stts = (
        b"\x00" * 4 + (1).to_bytes(4, "big")
        + (1717).to_bytes(4, "big") + (1001).to_bytes(4, "big")
    )
    stsz = (
        b"\x00" * 4 + (5100).to_bytes(4, "big")
        + (1717).to_bytes(4, "big")
    )
    stsc = (
        b"\x00" * 4 + (1).to_bytes(4, "big")
        + (1).to_bytes(4, "big") + (1717).to_bytes(4, "big")
        + (1).to_bytes(4, "big")
    )

    def build(offset):
        stco = (
            b"\x00" * 4 + (1).to_bytes(4, "big")
            + offset.to_bytes(4, "big")
        )
        stbl = box(
            b"stbl",
            box(b"stsd", stsd) + box(b"stts", stts)
            + box(b"stsz", stsz) + box(b"stsc", stsc)
            + box(b"stco", stco),
        )
        minf = box(b"minf", stbl)
        mdia = box(b"mdia", minf)
        trak = box(b"trak", mdia)
        return box(b"moov", box(b"mvhd", mvhd) + trak)

    ftyp = box(b"ftyp", b"isom" + b"\x00" * 12)
    moov = build(0)
    moov = build(len(ftyp) + len(moov) + 8)
    mdat = box(b"mdat", b"\x00" * (5100 * 1717))
    return ftyp + moov + mdat


def _webm_shell():
    """Build a header only WebM shell with planted facts.

    The plant for the video gate. The shell carries an
    EBML header naming webm, an Info element claiming a
    16.9 second duration, and one video track claiming
    VP8 at 1584 by 1140, over one Void element of zero
    padding. It holds no cluster and no frame block, so a
    probe that reads frame evidence refuses it while a
    probe that reads only header claims passes it.
    """
    def size(value):
        if value < 127:
            return bytes([0x80 | value])
        if value < 16383:
            return bytes([0x40 | (value >> 8), value & 0xFF])
        if value < 2097151:
            return bytes([
                0x20 | (value >> 16),
                (value >> 8) & 0xFF,
                value & 0xFF,
            ])
        return bytes([
            0x10 | (value >> 24),
            (value >> 16) & 0xFF,
            (value >> 8) & 0xFF,
            value & 0xFF,
        ])

    def element(kind, body):
        return kind + size(len(body)) + body

    header = element(
        b"\x1a\x45\xdf\xa3",
        element(b"\x42\x86", b"\x01")
        + element(b"\x42\x82", b"webm"),
    )
    info = element(
        b"\x15\x49\xa9\x66",
        element(b"\x2a\xd7\xb1", (1000000).to_bytes(3, "big"))
        + element(
            b"\x44\x89", struct.pack(">d", 16900.0)
        ),
    )
    video = element(
        b"\xe0",
        element(b"\xb0", (1584).to_bytes(2, "big"))
        + element(b"\xba", (1140).to_bytes(2, "big")),
    )
    track = element(
        b"\xae",
        element(b"\xd7", b"\x01")
        + element(b"\x83", b"\x01")
        + element(b"\x86", b"V_VP8")
        + video,
    )
    tracks = element(b"\x16\x54\xae\x6b", track)
    void = element(b"\xec", b"\x00" * 100500)
    segment = element(
        b"\x18\x53\x80\x67", info + tracks + void
    )
    return header + segment


def _webm_block_shell():
    """Build a WebM whose frame blocks hold no frame.

    The second plant family for the video gate. The shell
    carries the planted Info and track elements of the
    header shell and adds one cluster holding three frame
    blocks whose payloads are single zero bytes under
    timecodes that reach the planted duration, so every
    header and table claim stands satisfied and only a
    probe that reads the frame bytes themselves can
    refuse it.
    """
    def size(value):
        if value < 127:
            return bytes([0x80 | value])
        if value < 16383:
            return bytes([0x40 | (value >> 8), value & 0xFF])
        if value < 2097151:
            return bytes([
                0x20 | (value >> 16),
                (value >> 8) & 0xFF,
                value & 0xFF,
            ])
        return bytes([
            0x10 | (value >> 24),
            (value >> 16) & 0xFF,
            (value >> 8) & 0xFF,
            value & 0xFF,
        ])

    def element(kind, body):
        return kind + size(len(body)) + body

    header = element(
        b"\x1a\x45\xdf\xa3",
        element(b"\x42\x86", b"\x01")
        + element(b"\x42\x82", b"webm"),
    )
    info = element(
        b"\x15\x49\xa9\x66",
        element(b"\x2a\xd7\xb1", (1000000).to_bytes(3, "big"))
        + element(
            b"\x44\x89", struct.pack(">d", 200.0)
        ),
    )
    video = element(
        b"\xe0",
        element(b"\xb0", (1584).to_bytes(2, "big"))
        + element(b"\xba", (1140).to_bytes(2, "big")),
    )
    track = element(
        b"\xae",
        element(b"\xd7", b"\x01")
        + element(b"\x83", b"\x01")
        + element(b"\x86", b"V_VP8")
        + video,
    )
    tracks = element(b"\x16\x54\xae\x6b", track)

    def block(delta):
        return element(
            b"\xa3",
            b"\x81"
            + delta.to_bytes(2, "big", signed=True)
            + b"\x00" + b"\x00",
        )

    cluster = element(
        b"\x1f\x43\xb6\x75",
        element(b"\xe7", b"\x00")
        + block(0) + block(100) + block(200),
    )
    segment = element(
        b"\x18\x53\x80\x67", info + tracks + cluster
    )
    return header + segment


def _webm_facts(path):
    """Return video facts for one WebM file.

    The probe reads the EBML structure with the standard
    library only and returns width and height and duration
    in seconds and the frame block count. It confirms the
    DocType names webm, walks the Segment children to the
    Info element for the TimestampScale and Duration and
    to the first video track for its codec and its
    PixelWidth and PixelHeight, and then reads the frame
    blocks standing in the clusters, whose latest timecode
    must stand at the stated duration rather than far
    short of it, so a header shell with no frames cannot
    pass. The probe then reads the frame tag at the head
    of every block payload and holds each first partition
    inside its own block, and every keyframe must carry
    the VP8 signature and name the frame size the track
    names, so blocks holding no decodable frame cannot
    pass either. A file that does not carry this structure is not
    a WebM the gate can certify, and the probe fails here
    rather than passing it unexamined. Malformed input
    fails as an AssertionError, because the probe's verdict
    is the only thing its callers read.
    """
    raw = path.read_bytes()
    try:
        return _webm_facts_inner(raw)
    except (IndexError, KeyError, struct.error):
        raise AssertionError("the WebM structure is malformed")


def _webm_facts_inner(raw):
    assert raw[:4] == b"\x1a\x45\xdf\xa3", "not an EBML file"

    def read_id(pos):
        first = raw[pos]
        assert first != 0, "an element id with no marker bit"
        length = 1
        mask = 0x80
        while not first & mask:
            mask >>= 1
            length += 1
        return raw[pos:pos + length], pos + length

    def read_size(pos):
        first = raw[pos]
        assert first != 0, "a size with no marker bit"
        length = 1
        mask = 0x80
        while not first & mask:
            mask >>= 1
            length += 1
        value = first & (mask - 1)
        for i in range(1, length):
            value = (value << 8) | raw[pos + i]
        unknown = value == (1 << (7 * length)) - 1
        return (None if unknown else value), pos + length

    def children(start, end):
        pos = start
        while pos < end:
            kind, after = read_id(pos)
            size, after = read_size(after)
            stop = end if size is None else after + size
            assert stop <= end, (
                "an element ends past the bytes under it"
            )
            yield kind, after, stop
            pos = stop

    segment = None
    for kind, body, stop in children(0, len(raw)):
        if kind == b"\x1a\x45\xdf\xa3":
            for sub, sub_body, sub_stop in children(body, stop):
                if sub == b"\x42\x82":
                    assert raw[sub_body:sub_stop] == b"webm", (
                        "the EBML DocType does not name webm"
                    )
        elif kind == b"\x18\x53\x80\x67":
            segment = (body, stop)
            break
    assert segment is not None, "no Segment in the WebM"
    seg_body, seg_end = segment
    # The muxer writes a SeekHead ahead of the Info and
    # Tracks elements. The walk steps over it by its size,
    # like every other child, so the ids inside its entries
    # are never mistaken for the elements themselves.
    scale = 1000000
    duration_units = None
    width = height = None
    codec = None
    video_track = None
    found_frames = []
    blocks = 0
    max_timecode = None
    base = 0
    for kind, body, stop in children(seg_body, seg_end):
        if kind == b"\x15\x49\xa9\x66":
            for sub, sub_body, sub_stop in children(body, stop):
                if sub == b"\x2a\xd7\xb1":
                    scale = int.from_bytes(
                        raw[sub_body:sub_stop], "big"
                    )
                elif sub == b"\x44\x89":
                    duration_units = struct.unpack(
                        ">f" if sub_stop - sub_body == 4 else ">d",
                        raw[sub_body:sub_stop],
                    )[0]
        elif kind == b"\x1f\x43\xb6\x75":
            for sub, sub_body, sub_stop in children(body, stop):
                if sub == b"\xe7":
                    base = int.from_bytes(
                        raw[sub_body:sub_stop], "big"
                    )
                elif sub == b"\xa3":
                    blocks += 1
                    first = raw[sub_body]
                    marker = 0x80
                    tlen = 1
                    while not first & marker:
                        marker >>= 1
                        tlen += 1
                    track_no = first & (marker - 1)
                    for i in range(1, tlen):
                        track_no = (track_no << 8) | raw[
                            sub_body + i
                        ]
                    head = sub_body + tlen
                    delta = int.from_bytes(
                        raw[head:head + 2], "big",
                        signed=True,
                    )
                    stamp = base + delta
                    if max_timecode is None or stamp > max_timecode:
                        max_timecode = stamp
                    found_frames.append(
                        (track_no, raw[head + 2],
                         head + 3, sub_stop)
                    )
        elif kind == b"\x16\x54\xae\x6b":
            for track, t_body, t_stop in children(body, stop):
                if track != b"\xae":
                    continue
                fields = {}
                for sub, sub_body, sub_stop in children(
                    t_body, t_stop
                ):
                    fields[sub] = (sub_body, sub_stop)
                if b"\x83" not in fields:
                    continue
                s, e = fields[b"\x83"]
                if raw[s:e] != b"\x01":
                    continue
                if b"\xd7" in fields:
                    ns, ne = fields[b"\xd7"]
                    video_track = int.from_bytes(raw[ns:ne], "big")
                s, e = fields[b"\xe0"]
                if b"\x86" in fields:
                    cs, ce = fields[b"\x86"]
                    codec = raw[cs:ce]
                for sub, sub_body, sub_stop in children(s, e):
                    if sub == b"\xb0":
                        width = int.from_bytes(
                            raw[sub_body:sub_stop], "big"
                        )
                    elif sub == b"\xba":
                        height = int.from_bytes(
                            raw[sub_body:sub_stop], "big"
                        )
    assert codec == b"V_VP8", "the WebM video track is not VP8"
    assert width and height, "no video track in the WebM"
    assert duration_units, "no duration in the WebM Info element"
    seconds = duration_units * scale / 1e9
    assert blocks > 0, "the WebM segment holds no frame blocks"
    assert max_timecode is not None, (
        "the WebM clusters name no frame timecodes"
    )
    tail = seconds - max_timecode * scale / 1e9
    assert -0.5 <= tail <= 5.0, (
        "the last frame timecode stands off the stated duration"
    )
    frames = [
        frame for frame in found_frames
        if video_track is None or frame[0] == video_track
    ]
    assert len(frames) == blocks, (
        "a frame block stands on a track the gate does not read"
    )
    keyframes = 0
    for _track, flags, start, stop in frames:
        assert flags & 0x06 == 0, "a frame block is laced"
        payload = raw[start:stop]
        assert len(payload) >= 3, (
            "a frame block is too small to hold a frame"
        )
        tag = payload[0] | (payload[1] << 8) | (payload[2] << 16)
        part0 = tag >> 5
        if tag & 1:
            assert 1 <= part0 <= len(payload) - 3, (
                "a frame block names a first partition "
                "past its own bytes"
            )
        else:
            keyframes += 1
            assert len(payload) >= 10, (
                "a keyframe block is too small to hold "
                "its header"
            )
            assert payload[3:6] == b"\x9d\x01\x2a", (
                "a keyframe block carries no VP8 signature"
            )
            assert part0 <= len(payload) - 10, (
                "a keyframe block names a first partition "
                "past its own bytes"
            )
            frame_width = (
                int.from_bytes(payload[6:8], "little") & 0x3FFF
            )
            frame_height = (
                int.from_bytes(payload[8:10], "little") & 0x3FFF
            )
            assert (frame_width, frame_height) == (width, height), (
                "a keyframe names a frame size the track "
                "does not"
            )
    assert keyframes > 0, "the WebM holds no keyframe"
    return width, height, seconds, blocks


class TestVideoForms(unittest.TestCase):
    """The money shot video standard gate.

    The video standard programme gave every money shot a
    full video form beside its preview and its stills. Each
    hero session and each proof strip moment stands in the
    tree as an MP4 and a WebM rendered from the recorded
    cast of its own session, and the capture record names
    every file with its geometry and duration and play
    length. The pins below hold the recorded facts, read
    through the suite's own stdlib probes, so a money shot
    whose video form is removed, truncated, or replaced by
    a dummy file fails this gate by name. The gate certifies each video by its container structure, its sample placement, its coded unit framing, its frame tags, and its exact recorded size. It does not decode the encoded picture data, so a file fabricated to the recorded shape at the recorded size with framed but undecodable picture data is not refused by the gate. The provenance of the shipped films rests on the frame checks recorded in this section. The video files
    stand outside the weighed page set under the ruling
    pinned in TestBrandAssets, because a linked video is
    click to play and no page load pulls it.
    """

    IMAGES = ROOT / "docs" / "images"
    # The recorded play length of each film and clip in
    # seconds. The duration a probe may read stands
    # within 1.5 seconds of the figure named here. The
    # third element of each row holds the frame evidence
    # for the MP4 form, its sample count and its total
    # sample bytes, and the WebM frame block counts stand
    # in their own table below.
    VIDEOS = {
        "recognitio-claude-code-demo": (
            (1584, 1216), 171.7, (1717, 8751129),
        ),
        "recognitio-cursor-agent-demo": (
            (1584, 1216), 150.5, (1505, 3218173),
        ),
        "recognitio-session-claude-code-denial-video": (
            (1584, 1140), 30.0, (300, 938817),
        ),
        "recognitio-session-codex-verified-video": (
            (1584, 1456), 39.8, (398, 2180392),
        ),
        "recognitio-session-cursor-packet-check-video": (
            (1584, 1140), 36.0, (360, 718566),
        ),
        "recognitio-session-qwen-summary-video": (
            (1584, 1140), 16.9, (169, 2448593),
        ),
    }
    WEBM_BLOCKS = {
        "recognitio-claude-code-demo": 1717,
        "recognitio-cursor-agent-demo": 1505,
        "recognitio-session-claude-code-denial-video": 300,
        "recognitio-session-codex-verified-video": 398,
        "recognitio-session-cursor-packet-check-video": 360,
        "recognitio-session-qwen-summary-video": 169,
    }
    # The byte size the capture record states for each
    # video file, held here so the record test below can
    # hold the record to its own figures and the forms
    # test can hold each shipped file to its exact
    # recorded size, so a dummy built to the recorded
    # shape at the wrong size fails on the figure as
    # well as on the probes that read its frames.
    SIZES = {
        "recognitio-claude-code-demo.mp4": 8772651,
        "recognitio-claude-code-demo.webm": 24222065,
        "recognitio-cursor-agent-demo.mp4": 3237111,
        "recognitio-cursor-agent-demo.webm": 15813785,
        "recognitio-session-claude-code-denial-video.mp4": 943256,
        "recognitio-session-claude-code-denial-video.webm": 3103914,
        "recognitio-session-codex-verified-video.mp4": 2186026,
        "recognitio-session-codex-verified-video.webm": 4586737,
        "recognitio-session-cursor-packet-check-video.mp4": 723749,
        "recognitio-session-cursor-packet-check-video.webm": 2560181,
        "recognitio-session-qwen-summary-video.mp4": 2451448,
        "recognitio-session-qwen-summary-video.webm": 3353603,
    }

    def test_every_money_shot_carries_both_video_forms(self):
        for stem, (geometry, seconds, evidence) in (
            self.VIDEOS.items()
        ):
            samples, payload = evidence
            path = self.IMAGES / (stem + ".mp4")
            self.assertTrue(path.is_file(), stem + ".mp4")
            width, height, duration, found, named = _mp4_facts(path)
            self.assertEqual(
                (width, height), geometry, stem + ".mp4"
            )
            self.assertAlmostEqual(
                duration, seconds, delta=1.5, msg=stem + ".mp4"
            )
            self.assertEqual(found, samples, stem + ".mp4")
            self.assertEqual(named, payload, stem + ".mp4")
            self.assertEqual(
                path.stat().st_size,
                self.SIZES[stem + ".mp4"],
                stem + ".mp4",
            )
            path = self.IMAGES / (stem + ".webm")
            self.assertTrue(path.is_file(), stem + ".webm")
            width, height, duration, blocks = _webm_facts(path)
            self.assertEqual(
                (width, height), geometry, stem + ".webm"
            )
            self.assertAlmostEqual(
                duration, seconds, delta=1.5, msg=stem + ".webm"
            )
            self.assertEqual(
                blocks, self.WEBM_BLOCKS[stem], stem + ".webm"
            )
            self.assertEqual(
                path.stat().st_size,
                self.SIZES[stem + ".webm"],
                stem + ".webm",
            )

    def test_the_capture_record_names_every_video(self):
        record = (
            self.IMAGES / "capture-record.md"
        ).read_text(encoding="utf-8")
        section = record.split("## The video forms", 1)[1]
        for stem in self.VIDEOS:
            self.assertIn(stem + ".mp4", section, stem)
            self.assertIn(stem + ".webm", section, stem)
        for name, size in self.SIZES.items():
            stated = (
                "%s, %d bytes" % (name, size) in section
                or "%s at %d bytes" % (name, size) in section
            )
            self.assertTrue(stated, name)
        # The record also states each play length in the
        # entry that names the film or clip, and the test
        # holds that figure to the recorded duration, so a
        # restated record cannot drift from the gate table.
        lines = section.splitlines()
        for stem, (_geometry, seconds, _evidence) in (
            self.VIDEOS.items()
        ):
            entries = [
                line for line in lines if stem + ".mp4" in line
            ]
            self.assertTrue(entries, stem)
            self.assertTrue(
                any(
                    "play %.1f seconds" % seconds in line
                    for line in entries
                ),
                stem,
            )

    def test_the_readme_links_the_films_and_clips(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        hero = readme.split("**Four harnesses, one range**", 1)[0]
        self.assertIn(
            '<a href="docs/images/'
            'recognitio-claude-code-demo.mp4">',
            hero,
        )
        strip = readme.split(
            "**Four harnesses, one range**", 1
        )[1].split("eval-chart.svg", 1)[0]
        for stem in (
            "recognitio-session-claude-code-denial-video",
            "recognitio-session-codex-verified-video",
            "recognitio-session-cursor-packet-check-video",
            "recognitio-session-qwen-summary-video",
        ):
            self.assertIn(
                '<a href="docs/images/%s.mp4">' % stem, strip, stem
            )

    def test_a_removed_or_truncated_video_fails_the_probe(self):
        # The regression plant for the gate itself. A video
        # file replaced by a short dummy or cut in half must
        # fail the probe by assertion, never pass as a video.
        source = (
            self.IMAGES / "recognitio-claude-code-demo.mp4"
        ).read_bytes()
        with RetryingTemporaryDirectory() as tmp:
            dummy = Path(tmp) / "dummy.mp4"
            dummy.write_bytes(source[:64])
            with self.assertRaises(AssertionError):
                _mp4_facts(dummy)
            halved = Path(tmp) / "halved.mp4"
            halved.write_bytes(source[: len(source) // 2])
            with self.assertRaises(AssertionError):
                _mp4_facts(halved)
            webm = (
                self.IMAGES
                / "recognitio-session-qwen-summary-video.webm"
            ).read_bytes()
            dummy = Path(tmp) / "dummy.webm"
            dummy.write_bytes(webm[:64])
            with self.assertRaises(AssertionError):
                _webm_facts(dummy)
            halved = Path(tmp) / "halved.webm"
            halved.write_bytes(webm[: len(webm) // 2])
            with self.assertRaises(AssertionError):
                _webm_facts(halved)
            # A forged WebM whose Info element carries a
            # duration but whose Tracks element holds no
            # video track must also fail, because the probe
            # reads the track rather than trusting the
            # container. The forgery is the Qwen file cut
            # just past its Info element with a fresh empty
            # Tracks element appended.
            raw = webm
            tracks_at = raw.find(b"\x16\x54\xae\x6b")
            forged = Path(tmp) / "forged.webm"
            forged.write_bytes(
                raw[:tracks_at] + b"\x16\x54\xae\x6b\x80"
            )
            with self.assertRaises(AssertionError):
                _webm_facts(forged)
            # Hand built shells with planted header facts
            # and no frames must also fail, because the
            # probes read frame evidence and not only the
            # values a header can claim. The MP4 shell
            # carries a planted movie header and sample
            # entry over one media box of zero padding. The
            # WebM shell carries a planted duration and
            # track over one Void of zero padding.
            shell = Path(tmp) / "shell.mp4"
            shell.write_bytes(_mp4_shell())
            with self.assertRaises(AssertionError):
                _mp4_facts(shell)
            shellw = Path(tmp) / "shell.webm"
            shellw.write_bytes(_webm_shell())
            with self.assertRaises(AssertionError):
                _webm_facts(shellw)
            # The upgraded plants from the red team delta
            # audit. An MP4 whose tables claim samples its
            # chunk tables never place, in the bare letters
            # record form and in a record form that parses
            # in full, and a WebM whose frame blocks hold
            # single zero bytes under honest timecodes must
            # also fail, because the probes now read the
            # frame data the tables describe.
            for form in (False, True):
                forged_mp4 = Path(tmp) / "table.mp4"
                forged_mp4.write_bytes(_mp4_table_shell(form))
                with self.assertRaises(AssertionError):
                    _mp4_facts(forged_mp4)
            forged_webm = Path(tmp) / "blocks.webm"
            forged_webm.write_bytes(_webm_block_shell())
            with self.assertRaises(AssertionError):
                _webm_facts(forged_webm)
            # The stream plant from the second red team
            # delta. Its chunk tables place every claimed
            # sample inside its media box, so only the
            # coded unit check on the sample bytes can
            # refuse it, and the media box holds zero
            # bytes throughout.
            stream = Path(tmp) / "stream.mp4"
            stream.write_bytes(_mp4_stream_shell())
            with self.assertRaises(AssertionError):
                _mp4_facts(stream)
            # The letters form of the stream shell holds
            # every other check satisfied as far as the
            # record, so the refusal must name the codec
            # record. Reading the message is what proves
            # the structural parse fired, because a probe
            # that degraded the parse to a substring
            # search would pass this record and refuse
            # the file later on its unit bytes instead.
            letters = Path(tmp) / "letters.mp4"
            letters.write_bytes(_mp4_stream_shell(False))
            with self.assertRaises(AssertionError) as caught:
                _mp4_facts(letters)
            self.assertIn("codec record", str(caught.exception))

    def test_a_removed_video_fails_the_gate(self):
        # The removal half of the regression clause. The
        # plant copies the shipped files into a scratch
        # images folder, proves the gate method passes on
        # the copy, then removes one file and one whole
        # stem and pads two files past their recorded
        # sizes and proves the same method fails each
        # time.
        with RetryingTemporaryDirectory() as tmp:
            root = Path(tmp)
            images = root / "docs" / "images"
            images.mkdir(parents=True)
            for name in self.SIZES:
                shutil.copy(self.IMAGES / name, images / name)
            case = TestVideoForms(
                "test_every_money_shot_carries_both_video_forms"
            )
            real = TestVideoForms.IMAGES
            TestVideoForms.IMAGES = images
            try:
                case.test_every_money_shot_carries_both_video_forms()
                (images / "recognitio-claude-code-demo.webm").unlink()
                with self.assertRaises(AssertionError):
                    case.test_every_money_shot_carries_both_video_forms()
                shutil.copy(
                    real / "recognitio-claude-code-demo.webm",
                    images / "recognitio-claude-code-demo.webm",
                )
                (images / "recognitio-cursor-agent-demo.mp4").unlink()
                (images / "recognitio-cursor-agent-demo.webm").unlink()
                with self.assertRaises(AssertionError):
                    case.test_every_money_shot_carries_both_video_forms()
                shutil.copy(
                    real / "recognitio-cursor-agent-demo.mp4",
                    images / "recognitio-cursor-agent-demo.mp4",
                )
                shutil.copy(
                    real / "recognitio-cursor-agent-demo.webm",
                    images / "recognitio-cursor-agent-demo.webm",
                )
                # A shipped file padded past its recorded
                # size must fail on the figure even when
                # its frames still read as a video, because
                # the forms test holds every file to the
                # exact size the capture record states.
                qwen = images / (
                    "recognitio-session-qwen-summary-video.webm"
                )
                qwen.write_bytes(
                    qwen.read_bytes() + b"\x00" * 16
                )
                with self.assertRaises(AssertionError):
                    case.test_every_money_shot_carries_both_video_forms()
                shutil.copy(
                    real
                    / "recognitio-session-qwen-summary-video.webm",
                    qwen,
                )
                hero = images / "recognitio-claude-code-demo.mp4"
                hero.write_bytes(
                    hero.read_bytes()
                    + (8).to_bytes(4, "big") + b"free"
                )
                with self.assertRaises(AssertionError):
                    case.test_every_money_shot_carries_both_video_forms()
            finally:
                TestVideoForms.IMAGES = real

    def test_linked_videos_stand_outside_the_weighed_set(self):
        # The page weight ruling, pinned in both directions.
        # A linked video file is click to play, so the
        # weighing never collects it, while the inline
        # preview the page does pull keeps its weight.
        with RetryingTemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "images").mkdir(parents=True)
            film = root / "docs" / "images" / "film.mp4"
            film.write_bytes(b"x" * 5000)
            still = root / "docs" / "images" / "still.png"
            still.write_bytes(b"x" * 700)
            readme = "\n".join([
                '<a href="docs/images/film.mp4">',
                '<img src="docs/images/still.png">',
                "",
                "[the film](docs/images/film.mp4)",
            ])
            self.assertEqual(
                readme_page_weight(root, readme), 700
            )
            refs = readme_page_weight_refs(readme)
            self.assertIn("docs/images/still.png", refs)
            self.assertNotIn("docs/images/film.mp4", refs)


class TestProofStrip(unittest.TestCase):
    """The storefront WP3 proof strip gate.

    Four frames stand under the hero, one per harness over
    the same range, each under its harness name with a line
    tying it to its capture record section. The repair
    round rebuilt the strip on uniform 792 by 570 frames.
    The Claude Code frame is the denial moment of the WP1
    cast, the Qwen frame is the summary screen of its WP2
    session, and the Codex still and the Cursor money shot
    poster stand as they were. Each frame also carries a
    phone band cut from the same frame as its narrow
    screen source. The mod denial still rendered from the
    same cast stands in the mod plugin assets folder.

    The hash is the single strong pin for each still, so
    the byte size pins the first form carried stand
    retired, because a hash over the bytes already fails
    on any size or content change. The geometry pin stays,
    read through the suite PNG decoder, because the
    uniform strip geometry is a claim of the rebuild
    itself and not a restatement of the bytes.
    """

    IMAGES = ROOT / "docs" / "images"
    STILLS = {
        "recognitio-session-claude-code-denial.png": (
            (792, 570),
            "e55d704ab35e1dbbb1f6c98614c94c3c61973c64965a6f96b5c969fdc55cfd54",
        ),
        "recognitio-session-codex-verified.png": (
            (792, 728),
            "56374c93662a6e662bcdbb3ff691470261a8866e75bef7fbf8fac8c7d002f7fd",
        ),
        "recognitio-cursor-agent-poster.png": (
            (792, 570),
            "b63dd2f84835319d71ad13d4ab91860b3bb807e8a013c3632406bb954e9c684d",
        ),
        "recognitio-session-qwen-summary.png": (
            (792, 570),
            "5bc379354fe3fadd8adb0f904c0ee0f3177edeb0b9cb75ba8c44d61a049b1bc4",
        ),
    }
    BANDS = {
        "recognitio-session-claude-code-denial-phone.png":
            "a8e7252fa4b882bf2cd0fbe2b5fd0fe4d9cdd237ba9bc2d0b5bb03590f58ad50",
        "recognitio-session-codex-verified-phone.png":
            "d3f56411bbfcef4b26abc57d149dc479fc04573641f071499328f9da06600891",
        "recognitio-cursor-agent-poster-phone.png":
            "4c38aab3db340513060b483e81169fbab4f0ac80759cec62f815df88f0ccdcd6",
        "recognitio-session-qwen-summary-phone.png":
            "26f9eba0ec31707a9072c6dcc80531207f4b307f0f3226f01a180c317561ad21",
    }
    ORDER = (
        ("**Claude Code**",
         "recognitio-session-claude-code-denial.png",
         "under the Claude Code hero session"),
        ("**Codex**",
         "recognitio-session-codex-verified.png",
         "under the Codex proof strip session"),
        ("**Cursor**",
         "recognitio-cursor-agent-poster.png",
         "under the Cursor agent money shot"),
        ("**Qwen Code**",
         "recognitio-session-qwen-summary.png",
         "under the Qwen proof strip session"),
    )
    # The capture record section each still stands behind,
    # named by a fragment of its heading. The tie is
    # structural, because a still named in the wrong
    # section of the record is a broken tie even when the
    # name stands somewhere in the file.
    RECORD_SECTIONS = {
        "recognitio-session-claude-code-denial.png":
            "The Claude Code proof strip still",
        "recognitio-session-codex-verified.png":
            "Capture record for the Codex proof strip session",
        "recognitio-cursor-agent-poster.png":
            "Capture record for the Cursor agent money shot",
        "recognitio-session-qwen-summary.png":
            "Capture record for the Qwen proof strip session",
    }

    def test_the_strip_stills_are_pinned(self):
        for name, (geometry, digest) in self.STILLS.items():
            path = self.IMAGES / name
            self.assertTrue(path.is_file(), name)
            width, height, _rows = _png_pixels_any(path)
            self.assertEqual((width, height), geometry, name)
            found = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(found, digest, name)

    def test_the_strip_bands_are_pinned(self):
        for name, digest in self.BANDS.items():
            path = self.IMAGES / name
            self.assertTrue(path.is_file(), name)
            width, height, _rows = _png_pixels_any(path)
            self.assertEqual((width, height), (544, 95), name)
            found = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(found, digest, name)

    def test_the_strip_order_and_record_ties_are_pinned(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        strip = readme.split("**Four harnesses, one range**", 1)[1]
        strip = strip.split("eval-chart.svg", 1)[0]
        positions = []
        for heading, name, record_name in self.ORDER:
            self.assertIn(heading, strip)
            self.assertIn("docs/images/" + name, strip)
            self.assertIn(record_name, strip)
            positions.append(strip.index(heading))
            positions.append(strip.index("docs/images/" + name))
        self.assertEqual(positions, sorted(positions))

    def test_the_capture_record_names_every_strip_still(self):
        record = (
            self.IMAGES / "capture-record.md"
        ).read_text(encoding="utf-8")
        headings = [
            "Capture record for the Cursor agent money shot",
            "Capture record for the Claude Code hero session",
            "Capture record for the Codex proof strip session",
            "Capture record for the Qwen proof strip session",
            "The Claude Code proof strip still",
        ]
        starts = []
        for heading in headings:
            self.assertIn(heading, record, heading)
            starts.append(record.index(heading))
        self.assertEqual(starts, sorted(starts))
        spans = {}
        for i, heading in enumerate(headings):
            end = (
                starts[i + 1] if i + 1 < len(starts)
                else len(record)
            )
            spans[heading] = record[starts[i]:end]
        for name, heading in self.RECORD_SECTIONS.items():
            self.assertIn(name, spans[heading], name)

    def test_the_mod_denial_still_is_pinned(self):
        path = (
            ROOT / "plugins" / "recognitio-mod" / "assets"
            / "recognitio-mod-denial.png"
        )
        self.assertTrue(path.is_file())
        found = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(
            found,
            "e55d704ab35e1dbbb1f6c98614c94c3c61973c64965a6f96b5c969f"
            "dc55cfd54",
        )
        mod_readme = (
            ROOT / "plugins" / "recognitio-mod" / "README.md"
        ).read_text(encoding="utf-8")
        self.assertIn("assets/recognitio-mod-denial.png", mod_readme)


def _png_pixels_any(path):
    """Return width and height and RGB rows for one PNG file.

    The decoder uses the standard library only and supports
    the 8 bit RGB and RGBA forms the brand exports ship in
    and the 8 bit palette form the quantized session stills
    ship in, with no interlace and anything else fails here
    rather than passing unexamined. The repair round grew
    the palette arm so the proof strip pins could read
    their stills through this helper instead of a raw
    header unpack.
    """
    raw = path.read_bytes()
    assert raw[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG file"
    width, height, depth, color = struct.unpack(">IIBB", raw[16:26])
    assert depth == 8 and color in (2, 3, 6) and raw[28] == 0, (
        "unexpected PNG form"
    )
    channels = {2: 3, 3: 1, 6: 4}[color]
    idat = bytearray()
    palette = []
    pos = 8
    while pos < len(raw):
        size = int.from_bytes(raw[pos:pos + 4], "big")
        kind = raw[pos + 4:pos + 8]
        if kind == b"IDAT":
            idat += raw[pos + 8:pos + 8 + size]
        elif kind == b"PLTE":
            palette = [
                tuple(raw[pos + 8 + 3 * i:pos + 11 + 3 * i])
                for i in range(size // 3)
            ]
        pos += size + 12
    if color == 3:
        assert palette, "palette PNG without a PLTE chunk"
    data = zlib.decompress(bytes(idat))
    stride = width * channels
    rows = []
    prev = bytearray(stride)
    pos = 0
    for _y in range(height):
        filt = data[pos]
        line = bytearray(data[pos + 1:pos + 1 + stride])
        pos += stride + 1
        for x in range(stride):
            left = line[x - channels] if x >= channels else 0
            up = prev[x]
            corner = prev[x - channels] if x >= channels else 0
            if filt == 1:
                line[x] = (line[x] + left) & 0xFF
            elif filt == 2:
                line[x] = (line[x] + up) & 0xFF
            elif filt == 3:
                line[x] = (line[x] + (left + up) // 2) & 0xFF
            elif filt == 4:
                guess = left + up - corner
                pick_a = abs(guess - left)
                pick_b = abs(guess - up)
                pick_c = abs(guess - corner)
                if pick_a <= pick_b and pick_a <= pick_c:
                    pred = left
                elif pick_b <= pick_c:
                    pred = up
                else:
                    pred = corner
                line[x] = (line[x] + pred) & 0xFF
            elif filt != 0:
                raise AssertionError("unexpected PNG filter %r" % filt)
        if color == 3:
            rows.append([palette[idx] for idx in line])
        else:
            rows.append(
                [tuple(line[i:i + 3])
                 for i in range(0, stride, channels)]
            )
        prev = line
    return width, height, rows


class TestWp5SessionScreenshots(unittest.TestCase):
    """Top 20 item 18, the session screenshot sets.

    Two real Cursor agent sessions over the docs depth range
    stand behind the six stills, one for the packet output
    style and one for the reviewer persona, with the record
    filed in the demo capture record. The pins hold the
    geometry and the hashes and the byte sizes of every
    still, the references from the README output style
    section and the persona brief, the alt text guideline
    the WP1 pass set, and the capture record naming every
    file it stands behind.

    The visual fix pass re-rendered the output style set
    through the renderer with the spinner fallback, which
    left the recount still byte identical, and recaptured
    the persona set in a fresh session whose prompt was
    pasted and verified before it was submitted. Every set
    also gained a phone width variant from a session run
    in a 48 column terminal, and the phone pins hold the
    same facts for the narrow frames.
    """

    IMAGES = ROOT / "docs" / "images"
    STYLE = (
        "recognitio-session-style-tiers.png",
        "recognitio-session-style-change.png",
        "recognitio-session-style-recount.png",
    )
    PERSONA = (
        "recognitio-session-persona-opening.png",
        "recognitio-session-persona-packet.png",
        "recognitio-session-persona-refusal.png",
    )
    STYLE_PHONE = (
        "recognitio-session-style-tiers-phone.png",
        "recognitio-session-style-change-phone.png",
        "recognitio-session-style-recount-phone.png",
    )
    PERSONA_PHONE = (
        "recognitio-session-persona-opening-phone.png",
        "recognitio-session-persona-packet-phone.png",
        "recognitio-session-persona-refusal-phone.png",
    )
    SIZES = {
        "recognitio-session-style-tiers.png": 18972,
        "recognitio-session-style-change.png": 29838,
        "recognitio-session-style-recount.png": 22297,
        "recognitio-session-persona-opening.png": 20056,
        "recognitio-session-persona-packet.png": 19809,
        "recognitio-session-persona-refusal.png": 18640,
        "recognitio-session-style-tiers-phone.png": 14455,
        "recognitio-session-style-change-phone.png": 13487,
        "recognitio-session-style-recount-phone.png": 11575,
        "recognitio-session-persona-opening-phone.png": 15436,
        "recognitio-session-persona-packet-phone.png": 14718,
        "recognitio-session-persona-refusal-phone.png": 12637,
    }
    SHA256 = {
        "recognitio-session-style-tiers.png":
            "150f764eae551801f1681a441809aa86da4f4a5aba827f42d6eb6411071"
            "cfdde",
        "recognitio-session-style-change.png":
            "7733b9a5eb4d861f16087c5309a1533c3ce3721a76a7a4c6936bc5531e7"
            "c8d00",
        "recognitio-session-style-recount.png":
            "f1732118c3742a3e9f6420379a89d203afbba215ecfa348386c1a1564"
            "e7322c3",
        "recognitio-session-persona-opening.png":
            "a883139e957eaca75518ed8d41832bcb97726c2a643e141149ff5785"
            "52e6ae32",
        "recognitio-session-persona-packet.png":
            "a4408475a9db79d3931fd9ee1f6fbd38797aba76a0e500195066eb7d"
            "05d8638a",
        "recognitio-session-persona-refusal.png":
            "6e78d9e3702e47a6f3077e2e737eb35c085198d019e4df5c76f05f8b"
            "1ed4f953",
        "recognitio-session-style-tiers-phone.png":
            "0d74782ad3c87c2b8747e734636d2d14ebfa861a59088ab83e21c209"
            "cfe55296",
        "recognitio-session-style-change-phone.png":
            "923a293e572da79f490bc27f4494827b1438a81579716a2d31673a99"
            "9c72b09a",
        "recognitio-session-style-recount-phone.png":
            "97a4958dfd33b60cff47da05423f166452fb721870b821f4d8609727"
            "81dbf251",
        "recognitio-session-persona-opening-phone.png":
            "0d7a13247c67c104dd1c5cc465e99b393273dddaa33a9ab6918531bd"
            "1ba0e426",
        "recognitio-session-persona-packet-phone.png":
            "7089540a13bb2a3145c116805d373590fc1050ac3f28d80303a90e3d"
            "8f251866",
        "recognitio-session-persona-refusal-phone.png":
            "2654c4eb710aeb36c28f749ccd135ea330abdc615f1feebf226e86d0"
            "e98c6a64",
    }

    def test_the_stills_exist_at_the_pinned_geometry(self):
        for name in self.STYLE + self.PERSONA:
            path = self.IMAGES / name
            self.assertTrue(path.is_file(), name)
            raw = path.read_bytes()
            self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n", name)
            width, height = struct.unpack(">II", raw[16:24])
            self.assertEqual((width, height), (792, 570), name)

    def test_the_phone_stills_exist_at_the_pinned_geometry(self):
        for name in self.STYLE_PHONE + self.PERSONA_PHONE:
            path = self.IMAGES / name
            self.assertTrue(path.is_file(), name)
            raw = path.read_bytes()
            self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n", name)
            width, height = struct.unpack(">II", raw[16:24])
            self.assertEqual((width, height), (432, 570), name)

    def test_the_still_sizes_and_hashes_are_pinned(self):
        for name, size in self.SIZES.items():
            path = self.IMAGES / name
            self.assertEqual(path.stat().st_size, size, name)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(digest, self.SHA256[name], name)

    def test_the_docs_reference_their_sets(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        style_section = readme.split(
            "### The packet output style", 1
        )[1].split("### The reviewer persona", 1)[0]
        for name in self.STYLE + self.STYLE_PHONE:
            self.assertIn("docs/images/" + name, style_section)
        persona = (
            ROOT / "docs" / "reviewer-persona.md"
        ).read_text(encoding="utf-8")
        session_section = persona.split(
            "## The persona in a session", 1
        )[1].split("## Limits", 1)[0]
        for name in self.PERSONA + self.PERSONA_PHONE:
            self.assertIn("images/" + name, session_section)

    def test_the_alt_texts_meet_the_guideline(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        persona = (
            ROOT / "docs" / "reviewer-persona.md"
        ).read_text(encoding="utf-8")
        for name in self.STYLE:
            match = re.search(
                r'<img alt="([^"]+)" src="docs/images/%s"' % name,
                readme,
            )
            self.assertIsNotNone(match, name)
            self.assertLessEqual(len(match.group(1)), 125, name)
        for name in self.PERSONA:
            match = re.search(
                r'<img alt="([^"]+)" src="images/%s"' % name,
                persona,
            )
            self.assertIsNotNone(match, name)
            self.assertLessEqual(len(match.group(1)), 125, name)

    def test_the_capture_record_names_every_still(self):
        record = (
            self.IMAGES / "capture-record.md"
        ).read_text(encoding="utf-8")
        for name in (
            self.STYLE + self.PERSONA + self.STYLE_PHONE + self.PERSONA_PHONE
        ):
            self.assertIn(name, record)


def readme_page_weight_refs(readme):
    """Every local image reference a README page carries.

    The weighed forms are the inline Markdown image, the
    reference style Markdown image whose target stands in a
    definition line, and the HTML image attributes in either
    quote spelling. A srcset contributes every one of its
    candidates, not only the first, because the browser may
    fetch any of them. External targets stand outside the
    weighing, as they always have.
    """
    refs = []
    refs += re.findall(r"!\[[^\]]*\]\((docs/[^)\s]+)[^)]*\)", readme)
    definitions = {}
    for match in re.finditer(
        r"^\s{0,3}\[([^\]]+)\]:\s*<?(docs/[^\s>]+)>?",
        readme, re.M,
    ):
        label = " ".join(match.group(1).split()).lower()
        definitions[label] = match.group(2)
    for match in re.finditer(r"!\[([^\]]*)\]\[([^\]]*)\]", readme):
        label = match.group(2) or match.group(1)
        label = " ".join(label.split()).lower()
        if label in definitions:
            refs.append(definitions[label])
    for match in re.finditer(r"!\[([^\]]+)\](?![\[(])", readme):
        label = " ".join(match.group(1).split()).lower()
        if label in definitions:
            refs.append(definitions[label])
    for match in re.finditer(
        r"\bsrc\s*=\s*(?:\"([^\"]+)\"|'([^']+)')", readme, re.I
    ):
        value = match.group(1) or match.group(2)
        if value.startswith("docs/"):
            refs.append(value)
    for match in re.finditer(
        r"\bsrcset\s*=\s*(?:\"([^\"]+)\"|'([^']+)')", readme, re.I
    ):
        value = match.group(1) or match.group(2)
        for candidate in value.split(","):
            fields = candidate.split()
            if fields and fields[0].startswith("docs/"):
                refs.append(fields[0])
    return refs


def readme_page_weight(root, readme):
    """The weighed total of one README text against one root.

    A src may carry a fragment, as the two wordmark images
    carry their GitHub theme fragments. A fragment is a
    rendering instruction and not part of the file path, so
    it is stripped before the file is weighed. Each local
    asset is weighed once however many forms carry it. A
    reference naming a file that does not stand under the
    root fails by name here, so a weighing can never surface
    as a bare file error from the stat call.
    """
    unique = list(
        dict.fromkeys(
            ref.split("#", 1)[0]
            for ref in readme_page_weight_refs(readme)
        )
    )
    total = 0
    for ref in unique:
        if not (root / ref).is_file():
            raise AssertionError(
                "the README page weight reference %s names no "
                "file under the weighed root" % ref
            )
        total += (root / ref).stat().st_size
    return total


class TestBrandAssets(unittest.TestCase):
    """The visual round 8 brand asset gate.

    The brand masters and exports stand under geometry and
    weight and hash pins and the README wordmark theme
    fragment pair stands under form pins and the page
    weight ledger stands under its ceiling. The manifest
    and palette pins live in scripts/check_brand.py and its
    own test file drives that script against scratch trees.
    """

    BRAND = ROOT / "docs" / "brand"
    GROUND = (19, 21, 27)
    GEOMETRY = {
        "recognitio-icon-512.png": (512, 512),
        "recognitio-icon-256.png": (256, 256),
        "recognitio-social-preview.png": (1280, 640),
        "recognitio-wordmark-1600.png": (1600, 384),
    }
    BUDGETS = {
        "recognitio-social-preview.png": 750000,
        "wordmark-light.svg": 25000,
        "wordmark-dark.svg": 25000,
        "recognitio-wordmark-1600.png": 200000,
        "recognitio-icon.svg": 25000,
        "recognitio-icon-512.png": 100000,
        "recognitio-icon-256.png": 50000,
    }
    SHA256 = {
        "wordmark-light.svg":
            "bc1a1e19e94380504ba3e541a7c877723bbf3aa1d8d30c2097262fba619f90df",
        "wordmark-dark.svg":
            "f237e5bc8358f75a453fc1e3b2147a502fe319e0f915e17eabc5c077fade3401",
        "recognitio-icon.svg":
            "5541cda96a1e985d1ee8b78670ce24fd879fa177743e74da36a22190d2850ddf",
        "recognitio-social-preview.svg":
            "5fc46199cc1e8c099f002950da2399de28214e08953ba08b38a6eca38db3419e",
        "recognitio-wordmark-1600.png":
            "1d786eff35455d9cea3f250519b18755be0a75e6a90aa5d03580043676bfb52c",
        "recognitio-icon-512.png":
            "76f8aa0c297165fd71a9d6a53df16f64c5bb3865a45cecd5878007a5da4a9111",
        "recognitio-icon-256.png":
            "e0fd6c02c638b50256b23ae7087950ebf3fcccc5c12442d83d78097784e33145",
        "recognitio-social-preview.png":
            "85c3155015b1cfe77ec8082f8a0d381be379fd543748e88fb72a2fcd09e69f3d",
    }
    # The ceiling moved down for WP1, and the move is
    # recorded here rather than absorbed in silence. The
    # ledger under it is 3,556 for the dark wordmark plus
    # 3,556 for the light wordmark plus 18,094 for the
    # phone crop plus 646,314 for the captioned hero
    # recording, which sums to 671,520. The old ceiling
    # of 1,300,000 held the 1,274,392 byte first encode.
    # The new ceiling of 700,000 is the work order hero
    # target and holds 28,480 of headroom over the ledger.
    # WP2 adds the eval chart at 2,914 bytes to the ledger,
    # which moves the total to 674,434 in the open. The
    # ceiling does not move, because 700,000 still holds
    # the new ledger with 25,566 of headroom over it.
    # WP5 adds the three output style session stills at
    # 18,961 plus 29,843 plus 22,297, which moves the total
    # to 745,535 in the open. The ceiling moves to 750,000
    # to hold the new ledger with 4,465 of headroom over
    # it, because the work order screenshot item puts real
    # session stills on the page the ceiling guards.
    # The visual fix pass then rebuilds the hero
    # recording at 607,309 with its captions set on
    # landmark boundaries, re-renders the three style
    # stills at 18,972 plus 29,838 plus 22,297 with the
    # spinner glyph drawn by fallback, adds the three
    # phone width style stills at 14,455 plus 13,487
    # plus 11,575 from a session run at phone width, and
    # redraws the eval chart at 2,999 with its text
    # raised, which moves the total to 740,901 in the
    # open. The ceiling does not move, because 750,000
    # still holds the new ledger with 9,099 of headroom
    # over it.
    # The storefront WP3 landing then moves the hero
    # slot to the Claude Code recording at 546,582 with
    # its phone crop at 11,580, replacing the Cursor
    # recording at 607,309 and its crop at 12,857, and
    # adds the four proof strip stills at 21,878 for
    # Claude Code plus 36,754 for Codex plus 44,889 for
    # Cursor plus 32,418 for Qwen, which moves the total
    # from 740,901 to 814,836 in the open. The ceiling
    # moves once, from 750,000 to 850,000, to hold the
    # new ledger with 35,164 of headroom over it,
    # because real session frames from four harnesses
    # stand on the page the ceiling guards. The full
    # ledger stands at 3,556 for the dark wordmark plus
    # 3,556 for the light wordmark plus 546,582 for the
    # hero recording plus 11,580 for its phone crop plus
    # 21,878 plus 36,754 plus 44,889 plus 32,418 for the
    # four strip stills plus 2,999 for the eval chart
    # plus 18,972 plus 29,838 plus 22,297 for the three
    # style stills plus 14,455 plus 13,487 plus 11,575
    # for their phone width variants.
    # The storefront repair round then re-encodes the
    # hero recording at 549,840, replaces the Claude
    # Code strip still with the denial frame at 20,342
    # and the Qwen strip still with the summary frame
    # at 20,157, and adds one phone band per strip
    # frame at 4,134 plus 3,838 plus 3,568 plus 4,285,
    # which moves the total from 814,836 to 820,122 in
    # the open. The ceiling does not move, because
    # 850,000 still holds the new ledger with 29,878
    # of headroom over it.
    PAGE_CEILING = 850000

    def test_the_brand_files_exist(self):
        for name in list(self.SHA256) + ["palette.json", "build_brand.py"]:
            self.assertTrue((self.BRAND / name).is_file(), name)

    def test_the_export_geometry_is_pinned(self):
        for name, size in self.GEOMETRY.items():
            width, height, _rows = _png_pixels_any(self.BRAND / name)
            self.assertEqual((width, height), size, name)

    def test_the_asset_weights_sit_under_their_budgets(self):
        for name, budget in self.BUDGETS.items():
            self.assertLessEqual(
                (self.BRAND / name).stat().st_size, budget, name
            )

    def test_the_asset_hashes_are_pinned(self):
        for name, digest in self.SHA256.items():
            found = hashlib.sha256(
                (self.BRAND / name).read_bytes()
            ).hexdigest()
            self.assertEqual(found, digest, name)

    def test_no_master_carries_live_text_or_a_font_reference(self):
        for name in (
            "wordmark-light.svg",
            "wordmark-dark.svg",
            "recognitio-icon.svg",
            "recognitio-social-preview.svg",
        ):
            text = (self.BRAND / name).read_text(encoding="utf-8")
            self.assertNotIn("<text", text, name)
            self.assertNotIn("font-family", text, name)
            self.assertIn('aria-label="recognitio"', text, name)

    def test_the_wordmark_variants_share_one_geometry(self):
        def geometry(name):
            text = (self.BRAND / name).read_text(encoding="utf-8")
            return re.sub(r'(fill|stroke)="[^"]*"', r'\1=""', text)

        self.assertEqual(
            geometry("wordmark-light.svg"), geometry("wordmark-dark.svg")
        )

    def test_no_brand_asset_uses_a_green(self):
        for name in self.SHA256:
            if name.endswith(".svg"):
                text = (self.BRAND / name).read_text(encoding="utf-8")
                self.assertNotIn("#4AC76A", text, name)
                self.assertNotIn("#3FB950", text, name)
        palette = json.loads(
            (self.BRAND / "palette.json").read_text(encoding="utf-8")
        )
        self.assertEqual(palette["reserved_verified_green"], "#4AC76A")
        self.assertEqual(palette["accent"], "#D97757")

    def test_the_wordmark_theme_fragment_form_is_pinned(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        # The wordmark lockup stands on the GitHub theme
        # fragments since the theme fix landing. Eight
        # picture elements stand in the README, the hero
        # recording picture, pinned in TestReadmePhoneWidth,
        # one picture per output style still from the
        # visual fix pass, and one picture per proof strip
        # frame from the storefront repair round, each
        # carrying a phone width source. The picture form keyed to
        # prefers-color-scheme is refused, because the
        # media feature follows the system scheme and a
        # reader who forces a GitHub theme against their
        # system scheme was served the master drawn for
        # the other ground.
        self.assertEqual(readme.count("<picture>"), 8)
        self.assertNotIn("prefers-color-scheme", readme)
        dark = '<img alt="recognitio" src="docs/brand/wordmark-dark.svg#gh-dark-mode-only" width="300" height="72">'
        light = '<img alt="recognitio" src="docs/brand/wordmark-light.svg#gh-light-mode-only" width="300" height="72">'
        for fragment in (dark, light):
            self.assertIn(fragment, readme)
        positions = [readme.index(item) for item in (dark, light)]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(readme.count("#gh-dark-mode-only"), 1)
        self.assertEqual(readme.count("#gh-light-mode-only"), 1)
        # The pair is also counted, in the hero block and
        # across the page. The picture era pin counted one
        # image and two sources inside its block, and the
        # count is the part of that pin this form keeps, so
        # an added master that stands visible in every theme
        # cannot ride beside the correct pair uncounted, and
        # no second reference to either master can stand
        # anywhere else in the README.
        hero = readme.split('<p align="center">', 1)[1].split(
            "</p>", 1
        )[0]
        self.assertEqual(hero.count("<img"), 2)
        self.assertEqual(readme.count("docs/brand/wordmark-dark.svg"), 1)
        self.assertEqual(
            readme.count("docs/brand/wordmark-light.svg"), 1
        )
        # The crossed pairings stay out. A dark master under
        # the light fragment is the defect in another dress.
        self.assertNotIn("wordmark-dark.svg#gh-light-mode-only", readme)
        self.assertNotIn("wordmark-light.svg#gh-dark-mode-only", readme)
        centred = '<p align="center">'
        self.assertIn(centred, readme)
        self.assertLess(readme.index(centred), readme.index(dark))
        # The wordmark pair is the whole hero lockup and no
        # heading repeats it, so the pair stands before the
        # headline and the old heading stays out.
        self.assertLess(
            readme.index(light),
            readme.index(
                "**A review starts from evidence instead "
                "of a bare diff.**"
            ),
        )
        self.assertNotIn("# Recognitio", readme)

    def test_the_icon_safe_area_is_pinned(self):
        width, height, rows = _png_pixels_any(
            self.BRAND / "recognitio-icon-512.png"
        )
        self.assertEqual((width, height), (512, 512))
        filled = [
            (x, y)
            for y, row in enumerate(rows)
            for x, pixel in enumerate(row)
            if pixel == (217, 119, 87)
        ]
        self.assertTrue(filled)
        xs = [point[0] for point in filled]
        ys = [point[1] for point in filled]
        span_x = max(xs) - min(xs) + 1
        span_y = max(ys) - min(ys) + 1
        self.assertLessEqual(span_x, int(512 * 0.72) + 2)
        self.assertLessEqual(span_y, int(512 * 0.72) + 2)
        self.assertGreaterEqual(span_x, int(512 * 0.65))
        self.assertGreaterEqual(span_y, int(512 * 0.65))

    def test_the_social_preview_safe_area_and_ground_are_pinned(self):
        width, height, rows = _png_pixels_any(
            self.BRAND / "recognitio-social-preview.png"
        )
        self.assertEqual((width, height), (1280, 640))
        for corner in (
            rows[0][0], rows[0][-1], rows[-1][0], rows[-1][-1]
        ):
            self.assertEqual(corner, self.GROUND)
        inset_x = int(width * 0.08)
        inset_y = int(height * 0.12)
        for row in rows[:inset_y] + rows[height - inset_y:]:
            for pixel in row[:inset_x] + row[width - inset_x:]:
                self.assertEqual(pixel, self.GROUND)
        lockup = [
            (x, y)
            for y in range(140, 300)
            for x in range(320, 960)
            if rows[y][x] != self.GROUND
        ]
        self.assertTrue(lockup)
        outside = [
            (x, y)
            for y in range(140, 300)
            for x in list(range(0, 320)) + list(range(960, 1280))
            if rows[y][x] != self.GROUND
        ]
        self.assertEqual(outside, [])

    def test_the_icon_registers_at_the_floor_size(self):
        _w, _h, rows = _png_pixels_any(
            self.BRAND / "recognitio-icon-512.png"
        )
        block = 512 // 16
        filled_cells = 0
        for cell_y in range(16):
            for cell_x in range(16):
                coral = 0
                for y in range(cell_y * block, (cell_y + 1) * block):
                    for x in range(cell_x * block, (cell_x + 1) * block):
                        if rows[y][x] == (217, 119, 87):
                            coral += 1
                if coral > (block * block) // 4:
                    filled_cells += 1
        self.assertGreaterEqual(filled_cells, 100)

    def test_the_readme_page_weight_sits_under_its_ceiling(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        total = readme_page_weight(ROOT, readme)
        self.assertLessEqual(total, self.PAGE_CEILING)
        self.assertEqual(total, 820122)

    def test_the_page_weight_weighs_every_carried_form(self):
        # Round 10 red team Major 3 and Minor 7. The weighing
        # once read only double quoted attributes and inline
        # Markdown images, and it read a whole srcset value as
        # one path, so a single quoted src, a reference style
        # image and the later candidates of a srcset carried
        # weight the gate never counted, and a multi candidate
        # srcset opening on a docs path died as an uncaught
        # file error instead of rendering a verdict.
        with RetryingTemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            sizes = {
                "docs/a.png": 100,
                "docs/b.png": 200,
                "docs/c.png": 400,
                "docs/d.png": 800,
                "docs/e.png": 1600,
            }
            for name, size in sizes.items():
                (root / name).write_bytes(b"x" * size)
            readme = "\n".join([
                "<img src='docs/a.png'>",
                "![the b picture][bref]",
                "",
                "[bref]: docs/b.png",
                "",
                '<source srcset="docs/c.png 1x, docs/d.png 2x">',
                "",
                "![the a picture again](docs/a.png)",
                "",
                '<img src="https://example.com/outside.png">',
                "",
                '<IMG SRC="docs/e.png">',
            ])
            # The a picture stands under two forms and weighs
            # once. The external target weighs nothing. The e
            # picture stands behind an uppercase attribute
            # name, which HTML reads the same as its lowercase
            # spelling, and the weighing reads it the same way.
            self.assertEqual(
                readme_page_weight(root, readme),
                100 + 200 + 400 + 800 + 1600,
            )

    def test_a_srcset_naming_a_missing_file_fails_by_name(self):
        with RetryingTemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "here.png").write_bytes(b"x" * 10)
            readme = (
                '<source srcset="docs/here.png 1x, '
                'docs/gone.png 2x">'
            )
            with self.assertRaises(AssertionError) as caught:
                readme_page_weight(root, readme)
            self.assertIn("docs/gone.png", str(caught.exception))


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

    def test_the_tree_records_every_gate_script_as_executable(self):
        # The full gate invokes every script through the Python
        # interpreter, so a script that lost its executable bit
        # in the tree would pass the gate and ship in a tag
        # archive without the bit. The recorded modes are read
        # from the git index, where a mode drift is visible.
        result = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "-s"],
            capture_output=True, text=True, env=scrubbed_git_env(),
        )
        if result.returncode != 0:
            self.skipTest("no git index stands over this tree")
        modes = {}
        for line in result.stdout.splitlines():
            meta, _, path = line.partition("\t")
            modes[path] = meta.split(" ", 1)[0]
        scripts = [
            path for path in modes
            if path.startswith("scripts/") and path.endswith(".py")
        ]
        self.assertTrue(scripts)
        for path in scripts:
            self.assertEqual(modes[path], "100755", path)
        self.assertEqual(
            modes[".agents/skills/recognitio/scripts/extract.py"],
            "100755",
        )
        self.assertEqual(modes[".claude/skills/recognitio"], "120000")

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

    def test_a_symlinked_entry_inside_the_home_copy_fails(self):
        # Round 14. The tree map once admitted a path only
        # when it was a regular file and not a symlink, so an
        # extra symlinked file inside a real directory copy
        # appeared in neither map and the layout comparison
        # passed over it in silence.
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_layout(tmp, home_shape="copy")
            link = (
                root / ".claude" / "skills" / "recognitio"
                / "references" / "linked-note.md"
            )
            link.symlink_to(Path("../SKILL.md"))
            problems = self.layout_problems(root)
            self.assertTrue(
                any(
                    "linked-note.md" in p and "as a symlink" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_symlinked_entry_inside_the_canonical_fails(self):
        # Round 14. The same silent spot on the canonical
        # side, where a file replaced by a symlink to another
        # skill file read as no file at all in both maps.
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_layout(tmp, home_shape="copy")
            entry = (
                root / ".agents" / "skills" / "recognitio"
                / "references" / "budget-system.md"
            )
            target_bytes = entry.read_bytes()
            entry.unlink()
            entry.symlink_to(Path("../SKILL.md"))
            home_entry = (
                root / ".claude" / "skills" / "recognitio"
                / "references" / "budget-system.md"
            )
            home_entry.write_bytes(target_bytes)
            problems = self.layout_problems(root)
            self.assertTrue(
                any(
                    "budget-system.md" in p and "as a symlink" in p
                    for p in problems
                ),
                problems,
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
        # skill, not from the old location. The WP1 phone wrap
        # splits the source path over a backslash continuation,
        # so the pin reads the command as the shell joins it,
        # with the continuation removed.
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        joined = text.replace("\\\n", "")
        self.assertIn("cp -r .agents/skills/recognitio", joined)
        self.assertNotIn("cp -r skills/recognitio", joined)


class TestCheckPacket(unittest.TestCase):
    """The packet check as a verifier, over genuine packets.

    The fixture packet is built by the shipped extractor over a
    real two commit repository, because the check now recounts the
    change it stamps and a hand written manifest is exactly the
    fabrication the check exists to refuse. Tamper tests copy the
    genuine packet and edit the copy.
    """

    CALC_V1 = (
        "def total(values):\n    result = 0\n"
        "    for value in values:\n        result += value\n"
        "    return result\n"
    )
    CALC_V2 = CALC_V1.replace("result = 0", "result = 1")
    CALLER = (
        "from calc import total\n\n\ndef run():\n"
        "    return total([1, 2])\n"
    )

    def setUp(self):
        self.mod = load_script("check_packet")
        self.tmp = RetryingTemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.email", "test@example.com")
        git(self.repo, "config", "user.name", "Test User")
        git(self.repo, "config", "commit.gpgsign", "false")
        (self.repo / "calc.py").write_text(self.CALC_V1, encoding="utf-8")
        (self.repo / "caller.py").write_text(self.CALLER, encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-m", "one")
        (self.repo / "calc.py").write_text(self.CALC_V2, encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-m", "two")
        self.head = git(self.repo, "rev-parse", "HEAD")
        extract = load_script_at(
            ROOT / ".agents" / "skills" / "recognitio" / "scripts"
            / "extract.py", "gate_extract_for_check_packet",
        )
        self.genuine = Path(self.tmp.name) / "genuine"
        with redirect_stderr(io.StringIO()):
            code = extract.main([
                "--range", "HEAD~1..HEAD",
                "--repo", str(self.repo),
                "--out", str(self.genuine),
            ])
        self.assertEqual(code, 0)

    def test_child_env_scrubs_config_and_driver_variables(self):
        # Round 7 F4 in the 300 round program. The head read this
        # script stamps against must run under the same scrub as the
        # extractor, so configuration or a driver program supplied
        # through the environment never reaches its git child.
        poisoned = {
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "diff.drv.textconv",
            "GIT_CONFIG_VALUE_0": "/tmp/forge.sh",
            "GIT_CONFIG_PARAMETERS": "'diff.drv.textconv=/tmp/forge.sh'",
            "GIT_EXTERNAL_DIFF": "/tmp/forge.sh",
            "GIT_DIFF_OPTS": "--ext-diff",
            "GIT_PAGER": "/tmp/forge.sh",
            "GIT_EXEC_PATH": "/tmp",
        }
        with mock.patch.dict(os.environ, poisoned):
            env = self.mod.scrubbed_child_env()
        for name in poisoned:
            self.assertNotIn(name, env)
        self.assertEqual(env["GIT_NO_REPLACE_OBJECTS"], "1")
        self.assertIn("PATH", env)

    def clone_packet(self, name):
        out = Path(self.tmp.name) / name
        shutil.copytree(self.genuine, out)
        return out

    def read_manifest(self, out):
        return json.loads(
            (out / "manifest.json").read_text(encoding="utf-8")
        )

    def write_manifest(self, out, manifest):
        (out / "manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )

    def read_packet(self, out):
        return (out / "packet.md").read_text(encoding="utf-8")

    def write_packet_text(self, out, text):
        (out / "packet.md").write_text(text, encoding="utf-8")

    def run_check(self, out, *extra):
        # The error stream is kept on self.last_stderr rather
        # than discarded, so a tamper test can assert the
        # failure names the tampered surface instead of
        # holding only the exit code.
        err = io.StringIO()
        with redirect_stderr(err):
            code = self.mod.main(
                [str(out), "--repo", str(self.repo)] + list(extra)
            )
        self.last_stderr = err.getvalue()
        return code

    def test_verified_packet_for_the_current_head_passes(self):
        out = self.clone_packet("good")
        self.assertEqual(self.run_check(out), 0)

    def test_a_manifest_without_sections_fails(self):
        out = self.clone_packet("nosections")
        manifest = self.read_manifest(out)
        del manifest["sections"]
        self.write_manifest(out, manifest)
        self.assertEqual(self.run_check(out), 1)
        self.assertIn(
            "missing a key its schema requires, sections",
            self.last_stderr,
        )

    def test_unverified_packet_fails(self):
        out = self.clone_packet("bad")
        manifest = self.read_manifest(out)
        manifest["verified"] = False
        self.write_manifest(out, manifest)
        self.assertEqual(self.run_check(out), 1)
        self.assertIn("does not report verified", self.last_stderr)

    def test_packet_for_a_stale_head_fails(self):
        out = self.clone_packet("stale")
        (self.repo / "later.py").write_text("x = 3\n", encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-m", "three")
        self.assertEqual(self.run_check(out), 1)
        self.assertIn("The packet is stale", self.last_stderr)

    def test_missing_manifest_fails(self):
        out = Path(self.tmp.name) / "empty"
        out.mkdir()
        (out / "packet.md").write_text("# packet\n", encoding="utf-8")
        self.assertEqual(self.run_check(out), 1)
        self.assertIn("there is no manifest.json in", self.last_stderr)

    def test_empty_packet_file_fails(self):
        out = self.clone_packet("hollow")
        (out / "packet.md").write_text("", encoding="utf-8")
        self.assertEqual(self.run_check(out), 1)
        self.assertIn("is empty", self.last_stderr)
        self.assertIn("packet.md", self.last_stderr)

    def test_null_manifest_fails(self):
        out = self.clone_packet("nullman")
        (out / "manifest.json").write_text("null", encoding="utf-8")
        self.assertEqual(self.run_check(out), 1)
        self.assertIn(
            "manifest.json does not hold a JSON object",
            self.last_stderr,
        )

    def test_non_object_manifest_fails(self):
        out = self.clone_packet("listman")
        (out / "manifest.json").write_text(
            '["verified"]', encoding="utf-8"
        )
        self.assertEqual(self.run_check(out), 1)
        self.assertIn(
            "manifest.json does not hold a JSON object",
            self.last_stderr,
        )

    def test_recorded_sections_present_and_filled_pass(self):
        out = self.clone_packet("whole")
        manifest = self.read_manifest(out)
        self.assertEqual(
            manifest["sections"],
            [
                "## T0 Triage", "## T1 The change",
                "## T2 Companions", "## T3 History",
                "## Verification recount",
            ],
        )
        self.assertEqual(self.run_check(out), 0)

    def test_a_thin_packet_wearing_a_full_manifest_fails(self):
        out = self.clone_packet("thin")
        text = self.read_packet(out)
        start = text.index("## T2 Companions")
        end = text.index("## T3 History")
        text = (
            text[:start]
            + "## T2 Companions\n\n"
            + "Not selected for this run. "
            + "The change in T1 is complete.\n\n"
            + text[end:]
        )
        self.write_packet_text(out, text)
        self.assertEqual(self.run_check(out), 1)
        self.assertIn(
            "carries only the placeholder for a tier",
            self.last_stderr,
        )

    def test_a_dropped_section_wearing_a_full_manifest_fails(self):
        out = self.clone_packet("dropppedsection")
        text = self.read_packet(out)
        start = text.index("## T3 History")
        end = text.index("## Verification recount")
        text = text[:start] + text[end:]
        self.write_packet_text(out, text)
        self.assertEqual(self.run_check(out), 1)
        self.assertIn(
            "records a section the packet does not hold",
            self.last_stderr,
        )
        self.assertIn("## T3 History", self.last_stderr)

    def test_an_included_tier_with_real_content_passes(self):
        out = self.clone_packet("fullreceipt")
        manifest = self.read_manifest(out)
        self.assertTrue(manifest["tiers"]["T2"]["included"])
        self.assertIn("## T2 Companions", self.read_packet(out))
        self.assertEqual(self.run_check(out), 0)

    def test_a_manifest_file_missing_from_the_change_tier_fails(self):
        out = self.clone_packet("droppedfile")
        text = self.read_packet(out)
        start = text.index("### calc.py")
        end = text.index("## T2 Companions")
        text = text[:start] + text[end:]
        self.write_packet_text(out, text)
        self.assertEqual(self.run_check(out), 1)
        self.assertIn(
            "receipts a changed file the packet change tier "
            "does not hold",
            self.last_stderr,
        )
        self.assertIn("calc.py", self.last_stderr)

    def test_manifest_files_present_in_the_change_tier_pass(self):
        out = self.clone_packet("wholefiles")
        text = self.read_packet(out)
        self.assertIn("### calc.py", text)
        self.assertEqual(self.run_check(out), 0)

    def test_a_recorded_section_with_no_content_fails(self):
        out = self.clone_packet("gutted")
        text = self.read_packet(out)
        start = text.index("## T3 History")
        end = text.index("## Verification recount")
        text = text[:start] + "## T3 History\n\n" + text[end:]
        self.write_packet_text(out, text)
        self.assertEqual(self.run_check(out), 1)
        self.assertIn(
            "stands in the packet with no content under it",
            self.last_stderr,
        )
        self.assertIn("## T3 History", self.last_stderr)

    def test_a_heading_inside_a_fence_satisfies_nothing(self):
        packet = (
            "# packet\n\n## T0 Triage\n\nThe triage.\n\n"
            "````\n## T3 History\n\nQuoted text, not a section.\n````\n"
        )
        problems = self.mod.section_problems(
            packet, ["## T0 Triage", "## T3 History"]
        )
        self.assertTrue(
            any(
                "records a section the packet does not hold" in p
                and "## T3 History" in p
                for p in problems
            ),
            problems,
        )

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
        out = self.clone_packet("goodenv")
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


class TestCheckEvals(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_evals")

    def test_child_env_scrubs_config_and_driver_variables(self):
        # Round 7 F4 in the 300 round program. The fixture rebuild
        # diff in this gate runs under the same scrub as the
        # extractor, so configuration or a driver program supplied
        # through the environment never reaches its git children.
        poisoned = {
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "diff.drv.textconv",
            "GIT_CONFIG_VALUE_0": "/tmp/forge.sh",
            "GIT_CONFIG_PARAMETERS": "'diff.drv.textconv=/tmp/forge.sh'",
            "GIT_EXTERNAL_DIFF": "/tmp/forge.sh",
            "GIT_DIFF_OPTS": "--ext-diff",
            "GIT_PAGER": "/tmp/forge.sh",
            "GIT_EXEC_PATH": "/tmp",
        }
        with mock.patch.dict(os.environ, poisoned):
            env = self.mod.scrubbed_child_env()
            anchor_env = self.mod._anchor_env()
        for name in poisoned:
            self.assertNotIn(name, env)
            self.assertNotIn(name, anchor_env)
        self.assertEqual(env["GIT_NO_REPLACE_OBJECTS"], "1")
        self.assertNotIn("PYTHONPATH", anchor_env)

    def copy_fixture(self, tmp):
        root = Path(tmp) / "root"
        shutil.copytree(ROOT / "evals", root / "evals")
        shutil.copytree(ROOT / "tests", root / "tests")
        shutil.copytree(ROOT / "scripts", root / "scripts")
        shutil.copy2(ROOT / "README.md", root / "README.md")
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

    def test_a_readme_eval_claim_without_the_caveat_fails(self):
        # Visual round 1. The README paired eval claim
        # must carry the construction caveat the results
        # file states, so a claim restored without it
        # fails the eval gate.
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = root / "README.md"
            text = target.read_text(encoding="utf-8")
            broken = text.replace(
                "A defect in an unchanged file is "
                "unreachable by a raw diff pass by "
                "construction, because the pass holds no "
                "content from any unchanged file. ",
                "",
                1,
            )
            self.assertNotEqual(broken, text)
            target.write_text(broken, encoding="utf-8")
            problems = self.mod.readme_eval_claim_problems(root)
            self.assertTrue(
                any("construction caveat" in p for p in problems),
                problems,
            )

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

    def test_an_unrecorded_eval_artefact_fails_naming_its_file(self):
        # Round 9 red team Major G8. The checksum tests above
        # plant edits to files the record already names, so a
        # gate that iterated only over the recorded names would
        # pass them all while a covered artefact added to the
        # tree with no record entry walked out unseen. The
        # shipped gate walks the union of the record and the
        # tree, and this plant holds the direction.
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = (
                root / "evals" / "tasks" / "task-01" / "extra-note.md"
            )
            target.write_text("an unrecorded note\n", encoding="utf-8")
            problems = self.mod.checksum_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn(
                "evals/tasks/task-01/extra-note.md", problems[0]
            )
            self.assertIn("no entry in the checksum record", problems[0])

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
            stale = text.replace("through round 37", "through round 11", 1)
            self.assertNotEqual(stale, text)
            target.write_text(stale, encoding="utf-8")
            problems = self.mod.corpus_scope_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("round 11", problems[0])
            self.assertIn("round 37", problems[0])

    def test_a_section_past_the_scope_cap_fails_the_scope_check(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.copy_fixture(tmp)
            target = root / "evals" / "corpus.md"
            text = target.read_text(encoding="utf-8")
            target.write_text(
                text + "\n## Round 38 incidents\n\nNothing yet.\n",
                encoding="utf-8",
            )
            problems = self.mod.corpus_scope_problems(root)
            self.assertEqual(len(problems), 1)
            self.assertIn("round 37", problems[0])
            self.assertIn("round 38", problems[0])

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
        "stamping, and re-review sections of `.agents/skills/recognitio/SKILL.md`. "
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

    def write_settings_file(self, root, payload):
        (root / "settings.json").write_text(
            payload if isinstance(payload, str) else json.dumps(payload),
            encoding="utf-8",
        )

    def test_a_root_settings_file_naming_another_agent_fails(self):
        # Round 238 hunt. The brief states the settings object
        # may ship as settings.json at the plugin root, and a
        # plant naming another agent returned zero problems
        # while the gate printed its pinned line, because no
        # shipped check read that path at all. The pin must
        # name the override.
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp)
            self.write_settings_file(root, {"agent": "not-the-reviewer"})
            problems = self.persona.persona_problems(root)
        self.assertTrue(
            any(
                "settings file" in problem
                and "not-the-reviewer" in problem
                for problem in problems
            ),
            problems,
        )

    def test_a_root_settings_file_agreeing_with_the_pin_passes(self):
        # The control beside the plant above. A settings file
        # carrying only the pinned agent value is the benign
        # shape the brief allows, so it passes whole. This
        # test also passed against the blind gate by design,
        # because a gate that never reads the file passes
        # every shape it carries.
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp)
            self.write_settings_file(root, {"agent": "reviewer"})
            problems = self.persona.persona_problems(root)
        self.assertEqual(problems, [], problems)

    def test_the_settings_file_wins_over_a_disagreeing_manifest_key(self):
        # The brief states the precedence in plain words.
        # When both shapes exist the file wins and the
        # manifest key is ignored, so a manifest key naming
        # another agent draws no problem beside a file that
        # carries the pinned value, while the reverse plant
        # above fails on the file value alone.
        manifest = {
            "name": "recognitio",
            "agents": ["./agents/reviewer.md"],
            "settings": {"agent": "auditor"},
            "version": "1.3.0",
        }
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp, manifest=manifest)
            self.write_settings_file(root, {"agent": "reviewer"})
            problems = self.persona.persona_problems(root)
        self.assertEqual(problems, [], problems)

    def test_a_settings_file_with_an_extra_key_fails(self):
        # Only agent and subagentStatusLine take effect in
        # plugin settings and every other key is dropped at
        # load, the same claim the manifest key pin rests on,
        # so the file shape is held to the same allowed set.
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp)
            self.write_settings_file(
                root, {"agent": "reviewer", "theme": "dark"}
            )
            problems = self.persona.persona_problems(root)
        self.assertTrue(
            any("theme" in problem for problem in problems), problems
        )

    def test_a_missing_manifest_settings_key_passes_beside_the_file(self):
        # The manifest key is ignored when the file stands,
        # so its absence beside a file carrying the pinned
        # value is no problem. The file is the whole settings
        # surface in that shape.
        manifest = {
            "name": "recognitio",
            "agents": ["./agents/reviewer.md"],
            "version": "1.3.0",
        }
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp, manifest=manifest)
            self.write_settings_file(root, {"agent": "reviewer"})
            problems = self.persona.persona_problems(root)
        self.assertEqual(problems, [], problems)

    def test_a_malformed_settings_file_fails_by_name(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp)
            self.write_settings_file(root, "{ not json")
            problems = self.persona.persona_problems(root)
        self.assertTrue(
            any(
                "settings file" in problem
                and "does not parse" in problem
                for problem in problems
            ),
            problems,
        )

    def test_a_non_utf8_settings_file_fails_by_name(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp)
            (root / "settings.json").write_bytes(b"\xff\xfe{")
            problems = self.persona.persona_problems(root)
        self.assertTrue(
            any(
                "settings file" in problem
                and "does not parse" in problem
                for problem in problems
            ),
            problems,
        )

    def test_a_settings_file_that_is_a_directory_fails_by_name(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp)
            (root / "settings.json").mkdir()
            problems = self.persona.persona_problems(root)
        self.assertTrue(
            any(
                "settings file" in problem
                and "not a regular file" in problem
                for problem in problems
            ),
            problems,
        )

    def test_a_dangling_settings_file_link_keeps_the_absent_reading(self):
        # A dangling link names no file, so it keeps the
        # absent reading the guarded read pattern gives an
        # absent path, and the manifest key stays the pinned
        # surface. This test also passed against the blind
        # gate by design.
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp)
            (root / "settings.json").symlink_to(root / "missing.json")
            problems = self.persona.persona_problems(root)
        self.assertEqual(problems, [], problems)

    def run_persona_problems_bounded(self, root):
        driver = (
            "import importlib.util, sys\n"
            "spec = importlib.util.spec_from_file_location("
            "'gate_under_test', sys.argv[1])\n"
            "mod = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(mod)\n"
            "from pathlib import Path\n"
            "for problem in mod.persona_problems(Path(sys.argv[2])):\n"
            "    print(problem)\n"
        )
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    driver,
                    str(ROOT / "scripts" / "check_persona.py"),
                    str(root),
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except subprocess.TimeoutExpired:
            self.fail("the persona gate did not finish within ten seconds")
        return result.stdout + result.stderr

    @unittest.skipUnless(hasattr(os, "mkfifo"), "no mkfifo on this host")
    def test_a_settings_file_fifo_refuses_promptly_by_name(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp)
            os.mkfifo(root / "settings.json")
            output = self.run_persona_problems_bounded(root)
        self.assertIn("settings file", output, output)
        self.assertIn("not a regular file", output, output)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "no mkfifo on this host")
    def test_a_settings_file_link_to_a_fifo_refuses_promptly_by_name(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp)
            os.mkfifo(root / "settings-target")
            (root / "settings.json").symlink_to(root / "settings-target")
            output = self.run_persona_problems_bounded(root)
        self.assertIn("settings file", output, output)
        self.assertIn("not a regular file", output, output)

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


class TestCapstoneSupersessionPin(unittest.TestCase):
    # Capstone Round 11. The closing documents of the three
    # finished programmes each stated the closing state of
    # their own moment in the present tense, and the capstone
    # answered with one dated supersession line per document.
    # The three lines stand in the programme records outside
    # the tree and carry no gate pin. This pin holds the
    # fourth statement of the set, the dated scoping sentence
    # the round added to the Claude submission pack, which
    # names the three lines and the records that carry them,
    # so the pack cannot claim the scoping in silence once
    # the scoping itself is gone or reworded.
    PACK = ROOT / "docs" / "submission-claude.md"
    SCOPING = (
        "The closing statements this pack rests on stand "
        "scoped by the supersession lines recorded in "
        "capstone Round 11 in the final certification of "
        "the 300 round programme, in the burn down addendum "
        "to that certification, and in the storefront "
        "certification summary, each line scoping its own "
        "closing figures to the head they were earned on."
    )

    def test_the_supersession_scoping_sentence_stands_pinned(self):
        text = self.PACK.read_text(encoding="utf-8")
        flat = " ".join(text.split())
        self.assertEqual(flat.count(self.SCOPING), 1)


class TestTreeFigureCensus(unittest.TestCase):
    # Capstone Round 11. The Claude pack states the tree
    # figures in its size paragraph, the repo file count and
    # the cap the count holds under and the largest file and
    # the largest file that is not an image or a font, and
    # the submissions gate re-derives those figures from the
    # tree it is given and judges the pack sentences against
    # them. That gate reads a synthetic layout in its own
    # tests and the shipped tree in its shipped tree run, so
    # no test read the measured figures off the shipped tree
    # and set them beside the pack sentences as the gate
    # derives them. This census closes that gap, so a tree
    # the gate reads green in its layout form cannot carry a
    # pack whose stated figures disagree with the shipped
    # tree the pack describes.
    PACK = ROOT / "docs" / "submission-claude.md"
    COUNT = (
        "The repo holds 273 files and tens of megabytes in "
        "total, as restated on 2026-11-10 against the tree "
        "that now holds that count."
    )
    CAP = (
        "at 273 files against a cap of 512 files"
    )
    LARGEST = (
        "Its largest file is the demo recording at "
        "24,222,065 bytes"
    )

    def test_the_pack_tree_figures_match_the_measured_tree(self):
        mod = load_script("check_submissions")
        measured = mod.tree_measurements(ROOT)
        self.assertIsNotNone(measured)
        self.assertEqual(measured["count"], 273)
        self.assertEqual(measured["scan_files"], 273)
        self.assertEqual(measured["largest_size"], 24222065)
        self.assertEqual(
            measured["largest_plain_path"],
            "tests/test_gate_scripts.py",
        )
        text = self.PACK.read_text(encoding="utf-8")
        flat = " ".join(text.split())
        for sentence in (self.COUNT, self.CAP, self.LARGEST):
            self.assertEqual(flat.count(sentence), 1, sentence)
        plain = (
            "Its largest file that is not an image or a font "
            "or a video is tests/test_gate_scripts.py at %s bytes"
            % format(measured["largest_plain_size"], ",")
        )
        self.assertEqual(flat.count(plain), 1)


class TestRound15SkillMainRoot(unittest.TestCase):
    """Round 15. The skill gate main entry judges a handed root."""

    def setUp(self):
        self.mod = load_script("check_skill")

    def make_root(self, tmp):
        root = Path(tmp) / "root"
        shutil.copytree(
            ROOT / ".agents" / "skills" / "recognitio",
            root / ".agents" / "skills" / "recognitio",
        )
        home = root / ".claude" / "skills"
        home.mkdir(parents=True)
        (home / "recognitio").symlink_to(
            root / ".agents" / "skills" / "recognitio"
        )
        return root

    def run_main(self, root):
        err = io.StringIO()
        with redirect_stderr(err):
            code = self.mod.main(root=root)
        return code, err.getvalue()

    def test_a_clean_handed_root_passes(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_root(tmp)
            code, err = self.run_main(root)
            self.assertEqual(code, 0, err)

    def test_a_broken_handed_root_fails(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_root(tmp)
            md = root / ".agents" / "skills" / "recognitio" / "SKILL.md"
            lines = md.read_text(encoding="utf-8").split("\n")
            for i, line in enumerate(lines):
                if line.startswith("description:"):
                    lines[i] = line + " " + ("x" * 600) + " " + ("y" * 600)
                    break
            else:
                self.fail("the skill file carries no description line")
            md.write_text("\n".join(lines), encoding="utf-8")
            code, err = self.run_main(root)
            self.assertEqual(code, 1)
            self.assertIn("over the 1024 limit", err)


if __name__ == "__main__":
    unittest.main()
