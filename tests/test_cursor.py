"""Build 10, the Cursor plugin.

The brief at docs/cursor-plugin-brief.md exploits the Cursor
Plugin manifest, the six component packaging rules, the Bugbot
rules in .cursor/BUGBOT.md, and the .cursor/config/bugbot.yaml
repo config. These tests prove the pin fires for a real reason
on every load bearing claim the round 22 lanes named. A
symlinked skill copy, a drifted skill copy, an unknown
bugbot.yaml field, a bad autofix mode, an enabling autofix
mode, a variables schema
violation on the platform root, a dropped symlink pin, a
dropped neutral default, a dropped fail on unresolved, a
dropped effort split, a Bugbot rule without a derivation note,
a passing prose title mention, a version drift, an absolute
manifest path, and a decision record without a decision 4
statement each fail the Cursor gate.
"""

import importlib.util
import marshal
import json
import re
import shutil
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    path = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location("cursor_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_extractor_shadow(source):
    """Plant a weakened compiled shadow of the extractor beside it.

    The shadow is the Round 25 red team construction, the
    extractor compiled with its companion definition cap
    weakened, carried in the unchecked hash based form the
    import system accepts without consulting the source.
    """
    data = source.read_bytes()
    weakened = data.replace(
        b"MAX_DEFINITIONS_PER_NAME = 3",
        b"MAX_DEFINITIONS_PER_NAME = 3000",
    )
    if weakened == data:
        raise AssertionError("the shipped cap line stands moved")
    code = compile(
        weakened, str(source.resolve()), "exec", dont_inherit=True
    )
    header = (
        importlib.util.MAGIC_NUMBER
        + struct.pack("<I", 1)
        + importlib.util.source_hash(weakened)
    )
    cache = source.parent / "__pycache__"
    cache.mkdir(exist_ok=True)
    tag = "cpython-%d%d" % sys.version_info[:2]
    shadow = cache / ("extract.%s.pyc" % tag)
    shadow.write_bytes(header + marshal.dumps(code))
    return shadow


def write_faithful_cache(source):
    """Write the cache an interpreter writes from the source itself.

    The write suppression a gate under test switched on for
    its own process is lifted for the load and restored
    after it, and the cache must stand written, so this
    fixture can never pass in silence over no cache at all.
    """
    spec = importlib.util.spec_from_file_location(
        "faithful_extract", source
    )
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = False
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    cache = Path(
        importlib.util.cache_from_source(str(source))
    )
    if not cache.is_file():
        raise AssertionError("no cache stands written")
    return cache


class TestCheckCursor(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("check_cursor")

    def make_layout(self, tmp):
        """A scratch tree with the plugin, the brief, and the record."""
        root = Path(tmp) / "root"
        for rel in (
            "docs/cursor-plugin-brief.md",
            "docs/decisions.md",
            ".cursor-plugin/plugin.json",
            ".cursor-plugin/marketplace.json",
            ".cursor-plugin/rules/recognitio.mdc",
            "docs/brand/recognitio-icon.svg",
            ".cursor/BUGBOT.md",
            ".cursor/config/bugbot.yaml",
            ".claude-plugin/plugin.json",
            "README.md",
            ".cursor-plugin/README.md",
        ):
            source = ROOT / rel
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        shutil.copytree(
            ROOT / ".cursor-plugin" / "skills" / "recognitio",
            root / ".cursor-plugin" / "skills" / "recognitio",
        )
        shutil.copytree(
            ROOT / ".agents" / "skills" / "recognitio",
            root / ".agents" / "skills" / "recognitio",
        )
        return root

    def problems(self, root):
        return self.mod.cursor_problems(root)

    def read_brief(self, root):
        return (root / "docs" / "cursor-plugin-brief.md").read_text(
            encoding="utf-8"
        )

    def write_brief(self, root, text):
        (root / "docs" / "cursor-plugin-brief.md").write_text(
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

    def read_readme(self, root):
        return (root / "README.md").read_text(encoding="utf-8")

    def write_readme(self, root, text):
        (root / "README.md").write_text(text, encoding="utf-8")

    def read_plugin_readme(self, root):
        return (root / ".cursor-plugin" / "README.md").read_text(
            encoding="utf-8"
        )

    def write_plugin_readme(self, root, text):
        (root / ".cursor-plugin" / "README.md").write_text(
            text, encoding="utf-8"
        )

    def read_manifest(self, root):
        return json.loads(
            (root / ".cursor-plugin" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )

    def write_manifest(self, root, data):
        (root / ".cursor-plugin" / "plugin.json").write_text(
            json.dumps(data), encoding="utf-8"
        )

    def test_the_shipped_tree_holds(self):
        self.assertEqual(self.mod.cursor_problems(ROOT), [])

    def test_the_scratch_layout_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            self.assertEqual(self.problems(root), [])

    def _discover(self, base, values):
        """One reading of the plugin files, listing what it finds.

        Every value resolves from the one base the reading
        names, and a component counts as discovered only when
        the path it resolves to stands on disk, with a skill
        directory holding its SKILL.md beside the listing.
        """
        found = []
        for kind, value in values:
            shown = value[2:] if value.startswith("./") else value
            shown = shown.rstrip("/")
            target = base / value
            if kind == "skills":
                holds = (target / "SKILL.md").is_file()
            else:
                holds = target.is_file()
            found.append((kind, shown, holds))
        return sorted(found)

    def test_both_documented_readings_discover_the_same_components(self):
        # Round 39 priced a scripted two reading proof for the
        # Cursor mixed path bases fix, and the burn-down spec
        # review recorded the absence of that proof as a
        # verification gap. The marketplace reading takes the
        # entry source as the plugin root and reads the
        # manifest under it, resolving the manifest values and
        # the entry values from that one base. The local
        # reading copies the repository folder, as the
        # documented route does, and reads the manifest nested
        # inside the copy with the copy as the plugin root.
        # Both readings must discover the same components, and
        # every discovered component must stand on disk.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            market = json.loads(
                (root / ".cursor-plugin" / "marketplace.json")
                .read_text(encoding="utf-8"))
            entry = market["plugins"][0]
            base = root / entry["source"]
            manifest = json.loads(
                (base / ".cursor-plugin" / "plugin.json")
                .read_text(encoding="utf-8"))
            manifest_values = (
                [("skills", v) for v in manifest["skills"]]
                + [("rules", v) for v in manifest["rules"]]
                + [("logo", manifest["logo"])]
            )
            entry_values = (
                [("skills", v) for v in entry["skills"]]
                + [("logo", entry["logo"])]
            )
            marketplace = self._discover(base, manifest_values)
            entry_found = self._discover(base, entry_values)
            copied = Path(tmp) / "copied-repository"
            shutil.copytree(root, copied)
            local_manifest = json.loads(
                (copied / ".cursor-plugin" / "plugin.json")
                .read_text(encoding="utf-8"))
            local_values = (
                [("skills", v) for v in local_manifest["skills"]]
                + [("rules", v) for v in local_manifest["rules"]]
                + [("logo", local_manifest["logo"])]
            )
            local = self._discover(copied, local_values)
            self.assertEqual(marketplace, local)
            self.assertTrue(
                all(holds for _kind, _value, holds in local),
                local,
            )
            # The entry reading must agree with the other
            # two readings on the components it carries, not
            # merely stand on disk, so an entry skills or
            # logo drift to another standing target fails
            # this proof as well as the gate.
            self.assertEqual(
                entry_found,
                [
                    item for item in local
                    if item[0] in ("skills", "logo")
                ],
            )
            self.assertEqual(
                [value for _kind, value, _holds in local],
                [
                    "docs/brand/recognitio-icon.svg",
                    ".cursor-plugin/rules/recognitio.mdc",
                    ".cursor-plugin/skills/recognitio",
                ],
            )

    def test_a_manifest_inside_a_cache_folder_in_the_copy_fails(self):
        # Rounds 286 and 294. A manifest wearing a cache folder
        # name inside the skill copy must stand in the copy
        # census, so the gate names it as an extra file instead
        # of certifying the copy against the canonical skill.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            cache = (root / ".cursor-plugin/skills/recognitio"
                     / "__pycache__")
            cache.mkdir(parents=True)
            (cache / "manifest.json").write_text(
                "{}\n", encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("extra file" in p for p in problems),
                problems,
            )

    def test_a_compiled_shadow_of_the_extractor_in_the_copy_fails(self):
        # Round 25 red team Major 1. A weakened extractor
        # compiled into the cache shape the tree maps used to
        # skip on shape alone is measured now, so the gate
        # names it instead of certifying the copy over it.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            write_extractor_shadow(
                root / ".cursor-plugin" / "skills" / "recognitio" / "scripts" / "extract.py"
            )
            problems = self.problems(root)
            self.assertTrue(
                any("extract.cpython" in p for p in problems),
                problems,
            )

    def test_a_compiled_shadow_of_the_extractor_in_the_canonical_skill_fails(self):
        # The same shadow on the canonical side, the side an
        # honest run leaves its own faithful cache on, is
        # named in the other direction.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            write_extractor_shadow(
                root / ".agents" / "skills" / "recognitio" / "scripts" / "extract.py"
            )
            problems = self.problems(root)
            self.assertTrue(
                any("extract.cpython" in p for p in problems),
                problems,
            )

    def test_a_faithful_cache_of_the_extractor_passes(self):
        # Control. The cache an interpreter writes from the
        # shipped source itself is build state, so a run that
        # imported the extractor leaves the pin standing, in
        # the copy and on the canonical side alike.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            write_faithful_cache(root / ".agents" / "skills" / "recognitio" / "scripts" / "extract.py")
            write_faithful_cache(root / ".cursor-plugin" / "skills" / "recognitio" / "scripts" / "extract.py")
            self.assertEqual(self.problems(root), [])
    def test_a_bytecode_cache_file_in_a_cache_folder_passes(self):
        # Control. A genuine bytecode cache file, a .pyc file
        # inside a cache folder, stays excluded as build state
        # in both the fixed state and the state before the fix.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            cache = (root / ".cursor-plugin/skills/recognitio"
                     / "scripts" / "__pycache__")
            cache.mkdir(parents=True)
            (cache / "extract.cpython-311.pyc").write_bytes(
                b"\x42\x0d\x0d\x0a cache bytes")
            self.assertEqual(self.problems(root), [])

    def test_a_bytecode_file_nested_below_a_cache_folder_fails(self):
        # Red team re-review of the burndown stack. A bytecode
        # file nested one folder below a cache folder is not
        # the shape an interpreter writes, so it stands in the
        # census like any other file and the gate names it.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            nested = (root / ".cursor-plugin/skills/recognitio"
                      / "scripts" / "__pycache__" / "nested")
            nested.mkdir(parents=True)
            (nested / "payload.pyc").write_bytes(
                b"\x42\x0d\x0d\x0a payload bytes")
            problems = self.problems(root)
            self.assertTrue(
                any("extra file" in p for p in problems),
                problems,
            )

    def test_a_dropped_readme_package_position_fails(self):
        # Visual round 1. No Cursor Marketplace listing
        # exists or has been submitted, so a README that
        # drops the shipped package position fails the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_readme(root)
            broken = text.replace(
                "The plugin ships in this repo as a plugin "
                "package.",
                "The plugin ships somehow.",
                1,
            )
            self.assertNotEqual(broken, text)
            self.write_readme(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("plugin package position" in p for p in problems),
                problems,
            )

    def test_the_stale_readme_marketplace_claim_fails(self):
        # Visual round 1. The marketplace distribution
        # sentence the README once carried is refused
        # outright, so it cannot return beside the
        # corrected sentences.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_readme(root)
            plant = (
                "The plugin is distributed through the "
                "manually reviewed Cursor Marketplace, and "
                "reviewed updates auto deploy to clients "
                "pinned at the commit SHA."
            )
            self.write_readme(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "stale Cursor Marketplace distribution claim"
                    in p
                    for p in problems
                ),
                problems,
            )

    def test_a_dropped_plugin_readme_package_position_fails(self):
        # Visual round 1 addendum. No Cursor Marketplace
        # listing exists or has been submitted, so a plugin
        # README that drops the shipped package position
        # fails the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_plugin_readme(root)
            broken = text.replace(
                "The plugin ships in this repo as a plugin "
                "package.",
                "The plugin ships somehow.",
                1,
            )
            self.assertNotEqual(broken, text)
            self.write_plugin_readme(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    ".cursor-plugin/README.md" in p
                    and "plugin package position" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_dropped_plugin_readme_no_listing_position_fails(self):
        # Visual round 1 addendum. A plugin README that
        # drops the no listing position fails the gate, so
        # the correction cannot soften in silence.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_plugin_readme(root)
            broken = text.replace(
                "No Cursor\nMarketplace listing exists or "
                "has been submitted",
                "A Cursor\nMarketplace listing may exist",
                1,
            )
            self.assertNotEqual(broken, text)
            self.write_plugin_readme(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    ".cursor-plugin/README.md" in p
                    and "no listing position" in p
                    for p in problems
                ),
                problems,
            )

    def test_the_stale_plugin_readme_marketplace_claim_fails(self):
        # Visual round 1 addendum. The marketplace
        # distribution passage the plugin README once
        # carried is refused outright, so it cannot return
        # beside the corrected sentences.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_plugin_readme(root)
            plant = (
                "The plugin is distributed through the "
                "manually reviewed Cursor Marketplace. Every "
                "plugin is manually reviewed before it is "
                "listed, and all plugins must be open source. "
                "Reviewed updates auto deploy to clients "
                "pinned at the commit SHA, with no user "
                "version pinning. A running Cloud Agent keeps "
                "the plugin versions it started with, so "
                "start a new agent to pick up an update."
            )
            self.write_plugin_readme(
                root, text + "\n\n" + plant + "\n"
            )
            problems = self.problems(root)
            self.assertTrue(
                any(
                    ".cursor-plugin/README.md" in p
                    and "stale Cursor Marketplace distribution "
                    "claim" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_symlinked_skill_copy_fails(self):
        # R22-RT-01. The host skips a symlink that points at a
        # plugin repository elsewhere on disk, so the skill copy
        # must be real files.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            copy_dir = root / ".cursor-plugin" / "skills" / "recognitio"
            shutil.rmtree(copy_dir)
            copy_dir.symlink_to(
                root / ".agents" / "skills" / "recognitio",
                target_is_directory=True,
            )
            problems = self.problems(root)
            self.assertTrue(
                any("is a symlink" in p for p in problems), problems
            )

    def test_a_drifted_skill_copy_fails(self):
        # The standing guidance is never ship two separate copies
        # of the same skill. The plugin copy stays byte identical
        # to the canonical skill, and a drift fails the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            skill = (
                root
                / ".cursor-plugin"
                / "skills"
                / "recognitio"
                / "SKILL.md"
            )
            before = skill.read_bytes()
            skill.write_bytes(before + b"\nExtra line.\n")
            problems = self.problems(root)
            self.assertTrue(
                any("drifts from" in p for p in problems), problems
            )

    def test_an_unknown_bugbot_yaml_field_fails(self):
        # R22-RT-05. An unknown field falls back silently down the
        # precedence order, so the gate rejects it outright. The
        # effort field is the adversarial case, because a
        # secondary analysis claims it works while the primary
        # page documents no such field.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".cursor" / "config" / "bugbot.yaml"
            text = path.read_text(encoding="utf-8")
            broken = text + "effort: high\n"
            self.assertNotEqual(broken, text)
            path.write_text(broken, encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("unknown fields" in p for p in problems),
                problems,
            )

    def test_a_bad_autofix_mode_fails(self):
        # Only the autofix.mode values the primary page names are
        # allowed. An invented mode fails the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".cursor" / "config" / "bugbot.yaml"
            text = path.read_text(encoding="utf-8")
            broken = text.replace("mode: disabled", "mode: turbo", 1)
            self.assertNotEqual(broken, text)
            path.write_text(broken, encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("not a mode" in p for p in problems), problems
            )

    def test_the_enabling_autofix_mode_fails(self):
        # Round 278. The brief states the shipped file sets mode
        # to disabled and decision 4 keeps Autofix off in this
        # repo, so the gate pins that exact value. The enabling
        # value the primary page also names fails by name even
        # though the shipped comment beside it still states the
        # disabled position, because the gate reads the value and
        # not the comment.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".cursor" / "config" / "bugbot.yaml"
            text = path.read_text(encoding="utf-8")
            broken = text.replace(
                "mode: disabled", "mode: newBranch", 1
            )
            self.assertNotEqual(broken, text)
            path.write_text(broken, encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "pins the shipped mode" in p
                    and "newBranch" in p
                    for p in problems
                ),
                problems,
            )

    def test_the_enabling_mode_fails_without_the_shipped_comment(self):
        # The pin reads the parsed value alone, so a bare file
        # carrying only the enabling value and none of the
        # shipped comment text fails the same way.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".cursor" / "config" / "bugbot.yaml"
            path.write_text(
                "autofix:\n  mode: newBranch\n", encoding="utf-8"
            )
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "pins the shipped mode" in p
                    and "newBranch" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_reworded_comment_with_the_disabled_mode_holds(self):
        # Control. The pin holds the value and not the file
        # bytes, so a comment rewording that keeps the shipped
        # disabled value passes the bugbot.yaml reading in both
        # gate states.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".cursor" / "config" / "bugbot.yaml"
            text = path.read_text(encoding="utf-8")
            broken = text.replace(
                "# Repo settings for Cursor Bugbot, read from the "
                "PR base branch.",
                "# Repo settings for Cursor Bugbot.",
                1,
            )
            self.assertNotEqual(broken, text)
            path.write_text(broken, encoding="utf-8")
            problems = self.mod.bugbot_yaml_problems(root)
            self.assertEqual(problems, [])

    def test_a_dropped_symlink_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            broken = text.replace(
                "Cursor skips a\nsymlink that points to a plugin repository "
                "elsewhere on disk.",
                "Cursor handles symlinks however it likes.",
                1,
            )
            self.assertNotEqual(broken, text)
            self.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("symlink skip" in p for p in problems), problems
            )

    def test_a_dropped_neutral_pin_fails(self):
        # R22-RT-03. Without the neutral default sentence, a
        # later edit could read neutral as a pass.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            broken = text.replace(
                "this is\nthe default conclusion when Bugbot reports findings.",
                "this is one possible conclusion.",
                1,
            )
            self.assertNotEqual(broken, text)
            self.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("neutral default" in p for p in problems),
                problems,
            )

    def test_a_dropped_fail_on_unresolved_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            broken = text.replace(
                "enable it to\nmake unresolved findings produce a failing "
                "status.",
                "enable it to make findings nicer.",
                1,
            )
            self.assertNotEqual(broken, text)
            self.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("fail on unresolved" in p for p in problems),
                problems,
            )

    def test_a_dropped_effort_split_pin_fails(self):
        # R22-RT-02. Without the dashboard setting sentence, a
        # later edit could claim bugbot.yaml pins effort.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            broken = text.replace(
                "Bugbot Teams includes the ability to set the "
                "effort level Bugbot\nuses for reviews.",
                "Bugbot effort is configured wherever is handy.",
                1,
            )
            self.assertNotEqual(broken, text)
            self.write_brief(root, broken)
            problems = self.problems(root)
            self.assertTrue(
                any("effort dashboard setting" in p for p in problems),
                problems,
            )

    def test_a_variables_schema_violation_fails(self):
        # R22-RT-04. The platform provided root is exempt from
        # the variables schema checklist item, so declaring it
        # there fails the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["variables"] = {
                "CURSOR_PLUGIN_ROOT": {"type": "string"}
            }
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("exempt" in p for p in problems), problems
            )

    def test_a_bugbot_rule_without_a_derivation_note_fails(self):
        # The second packet guard, carried over from Build 9. A
        # Bugbot rule with no derivation note is a rival
        # instruction source.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".cursor" / "BUGBOT.md"
            text = path.read_text(encoding="utf-8")
            broken = text.replace(
                "Derives from canonical skill, The tier model, the T0 instruction\n"
                "file flag.",
                "No derivation is offered for this rule.",
                1,
            )
            self.assertNotEqual(broken, text)
            path.write_text(broken, encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("no derivation note" in p for p in problems),
                problems,
            )

    def test_a_passing_prose_title_mention_fails(self):
        # R21-ST-01, applied to the Bugbot rules. A note that
        # names a canonical section title in passing prose
        # without deriving from it must fail.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".cursor" / "BUGBOT.md"
            text = path.read_text(encoding="utf-8")
            broken = text.replace(
                "Derives from canonical skill, The tier model, the T0 instruction\n"
                "file flag.",
                "Derives from the primary blog post. It shapes the\n"
                "Workflow of the review and nothing else.",
                1,
            )
            self.assertNotEqual(broken, text)
            path.write_text(broken, encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "no canonical skill section" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_version_drift_fails(self):
        # Every surface that carries a version agrees, so a
        # Cursor manifest that drifted from the Claude manifest
        # fails the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["version"] = "9.9.9"
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("disagree" in p for p in problems), problems
            )

    def test_a_marketplace_only_version_drift_fails(self):
        # R23-ST-02. No committed test broke only the marketplace
        # listing. A marketplace entry that drifted from the
        # manifest must fail the gate through the marketplace
        # check alone, so deleting the marketplace version
        # comparison fails this test.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".cursor-plugin" / "marketplace.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["plugins"][0]["version"] = "9.9.9"
            path.write_text(json.dumps(data), encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "marketplace.json is at version" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_manifest_folder_relative_skills_path_fails(self):
        # Every manifest path resolves from the one plugin
        # root at the repository root. The skills value this
        # tree once shipped, written from the manifest folder,
        # resolves nowhere from that base, so restoring it
        # must fail by name.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["skills"] = ["./skills/recognitio/"]
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("not a real directory" in p for p in problems),
                problems,
            )

    def test_a_manifest_folder_relative_rules_path_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["rules"] = ["./rules/recognitio.mdc"]
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("not a real file" in p for p in problems),
                problems,
            )

    def test_a_logo_written_from_the_manifest_folder_fails(self):
        # The logo value resolves from the plugin root like
        # every other manifest path. A value that names a
        # file only inside the manifest folder resolves
        # nowhere from the root.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["logo"] = "plugin.json"
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "logo" in p and "plugin root" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_marketplace_entry_with_the_old_skills_value_fails(self):
        # The entry paths resolve from the entry source at
        # the plugin root, so the entry must carry the
        # manifest values themselves. The skills value the
        # entry once shipped, written from the manifest
        # folder, must fail by name.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".cursor-plugin" / "marketplace.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["plugins"][0]["skills"] = ["./skills/recognitio/"]
            path.write_text(json.dumps(data), encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("entry carries skills" in p for p in problems),
                problems,
            )

    def test_a_marketplace_entry_source_drift_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".cursor-plugin" / "marketplace.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["plugins"][0]["source"] = "./.cursor-plugin"
            path.write_text(json.dumps(data), encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("source" in p for p in problems),
                problems,
            )

    def test_a_marketplace_entry_logo_drift_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / ".cursor-plugin" / "marketplace.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["plugins"][0]["logo"] = "docs/brand/other.svg"
            path.write_text(json.dumps(data), encoding="utf-8")
            problems = self.problems(root)
            self.assertTrue(
                any("entry carries logo" in p for p in problems),
                problems,
            )

    def read_marketplace(self, root):
        return json.loads(
            (root / ".cursor-plugin" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )

    def write_marketplace(self, root, data):
        (root / ".cursor-plugin" / "marketplace.json").write_text(
            json.dumps(data), encoding="utf-8"
        )

    def test_a_joint_skills_repoint_fails(self):
        # Burn-down repair. The gate once pinned agreement
        # between the manifest and the entry plus resolution
        # from the root, so repointing both files together
        # at the canonical skill copy, which resolves from
        # the root and keeps the two files agreeing, passed
        # both readings while the shipped skills value
        # moved. The shipped value itself is now pinned.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["skills"] = ["./.agents/skills/recognitio/"]
            self.write_manifest(root, data)
            market = self.read_marketplace(root)
            market["plugins"][0]["skills"] = [
                "./.agents/skills/recognitio/"
            ]
            self.write_marketplace(root, market)
            problems = self.problems(root)
            self.assertTrue(
                any("shipped skills value" in p for p in problems),
                problems,
            )

    def test_a_rules_repoint_to_another_in_root_file_fails(self):
        # Burn-down repair. Repointing the manifest rules
        # value at another existing in root file with a
        # frontmatter block passed the resolution reading.
        # The shipped rules value itself is now pinned.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["rules"] = [
                "./.agents/skills/recognitio/SKILL.md"
            ]
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("shipped rules value" in p for p in problems),
                problems,
            )

    def test_a_joint_logo_repoint_fails(self):
        # Burn-down repair. The logo agreement pinned the
        # entry to the manifest, so moving both files
        # together to another real in root file passed. The
        # shipped logo value itself is now pinned.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["logo"] = ".cursor-plugin/rules/recognitio.mdc"
            self.write_manifest(root, data)
            market = self.read_marketplace(root)
            market["plugins"][0]["logo"] = (
                ".cursor-plugin/rules/recognitio.mdc"
            )
            self.write_marketplace(root, market)
            problems = self.problems(root)
            self.assertTrue(
                any("shipped logo value" in p for p in problems),
                problems,
            )

    def test_a_marketplace_entry_with_a_rules_key_fails(self):
        # Burn-down repair. The entry agreement once covered
        # only source, skills, and logo, so an entry rules
        # key written from the manifest folder base, which
        # resolves nowhere under the entry source, passed
        # unexamined. The widened agreement reads it.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            market = self.read_marketplace(root)
            market["plugins"][0]["rules"] = [
                "./rules/recognitio.mdc"
            ]
            self.write_marketplace(root, market)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "entry carries rules" in p for p in problems
                ),
                problems,
            )

    def test_a_marketplace_entry_with_a_bogus_agents_key_fails(
        self,
    ):
        # Burn-down repair. An entry agents key naming a
        # path that stands nowhere passed the old agreement
        # for the same reason. The manifest carries no
        # agents value for it to agree with.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            market = self.read_marketplace(root)
            market["plugins"][0]["agents"] = [
                "./.cursor-plugin/agents/bogus.md"
            ]
            self.write_marketplace(root, market)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "entry carries agents" in p for p in problems
                ),
                problems,
            )

    def test_a_marketplace_entry_with_an_unknown_key_fails(self):
        # Burn-down repair. The entry key set is closed by
        # the widened agreement, so an invented entry key
        # fails by name instead of riding unexamined.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            market = self.read_marketplace(root)
            market["plugins"][0]["invented"] = "docs/brand/x.svg"
            self.write_marketplace(root, market)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "'invented'" in p and "unexamined" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_manifest_agents_component_fails(self):
        # Burn-down re-review. The brief states the shipped
        # shape in plain words, it ships no agents, no
        # commands, no MCP servers, and the gate enforced
        # only the MCP limb. A manifest that gains an agents
        # component pointing at a real file certified a
        # plugin the brief says does not ship, so the
        # absence itself is now pinned.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["agents"] = ["./agents/reviewer.md"]
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "carries agents" in p
                    and "shipping no agents" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_manifest_commands_component_fails(self):
        # Burn-down re-review. The commands limb of the
        # same absence pin.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["commands"] = ["./docs"]
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "carries commands" in p
                    and "shipping no commands" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_joint_agents_component_fails(self):
        # Burn-down re-review. The joint plant, manifest
        # and entry gaining the same agents value together,
        # passed every gate before the absence pins, because
        # agreement and resolution were the only readings.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["agents"] = ["./agents/reviewer.md"]
            self.write_manifest(root, data)
            market = self.read_marketplace(root)
            market["plugins"][0]["agents"] = [
                "./agents/reviewer.md"
            ]
            self.write_marketplace(root, market)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "shipping no agents" in p for p in problems
                ),
                problems,
            )

    def test_a_marketplace_entry_with_a_commands_key_fails(
        self,
    ):
        # Burn-down re-review, second round. The entry
        # absence loop refuses agents and commands, and the
        # agents iteration carried a plant while the
        # commands iteration carried none, so narrowing the
        # loop to agents alone passed the whole suite. The
        # commands limb is planted here beside it.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            market = self.read_marketplace(root)
            market["plugins"][0]["commands"] = ["./docs"]
            self.write_marketplace(root, market)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "entry carries commands" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_marketplace_owner_with_an_extra_key_fails(self):
        # Burn-down re-review, second round. The owner
        # object was the marketplace file's remaining
        # unexamined corner, so an invented owner key rode
        # in silence. Its key set is closed the same way.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            market = self.read_marketplace(root)
            market["owner"]["agents"] = ["./agents/x.md"]
            self.write_marketplace(root, market)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "owner carries the 'agents' key" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_marketplace_owner_naming_another_person_fails(
        self,
    ):
        # Burn-down re-review, second round. The owner name
        # and email drifted to another person while every
        # gate passed, because no reading compared them with
        # the manifest author they restate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            market = self.read_marketplace(root)
            market["owner"]["name"] = "Someone Else"
            self.write_marketplace(root, market)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "owner carries name" in p
                    and "different owner" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_marketplace_metadata_description_drift_fails(
        self,
    ):
        # Burn-down re-review, second round. The metadata
        # description is the listing's second display text,
        # and its value was the one metadata field no
        # reading examined once the key set closed.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            market = self.read_marketplace(root)
            market["metadata"]["description"] = (
                "A completely different listing."
            )
            self.write_marketplace(root, market)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "metadata carries description" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_joint_non_string_description_fails(self):
        # Burn-down re-review, second round. The Cursor
        # manifest description was read for truthiness only,
        # the gap the Antigravity repair closed one surface
        # over, so a manifest and an entry jointly carrying
        # a non-string description agreed with each other
        # and certified. The value is typed now.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["description"] = 12345
            self.write_manifest(root, data)
            market = self.read_marketplace(root)
            market["plugins"][0]["description"] = 12345
            self.write_marketplace(root, market)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "not the string the primary manifest "
                    "schema names" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_joint_description_drift_fails(self):
        # Burn-down re-review, second round. The manifest,
        # entry, and metadata descriptions drifted together
        # to a different text while every agreement check
        # still passed, so the manifest description itself
        # is pinned as a value.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["description"] = "A completely different plugin."
            self.write_manifest(root, data)
            market = self.read_marketplace(root)
            market["plugins"][0]["description"] = (
                "A completely different plugin."
            )
            market["metadata"]["description"] = (
                "A completely different plugin."
            )
            self.write_marketplace(root, market)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "the shipped description is" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_marketplace_metadata_in_string_form_fails(self):
        # Burn-down re-review, third round. The metadata
        # block was guarded by an isinstance check with no
        # refusal behind it, so a metadata standing as a
        # string skipped its closed key set, its version
        # pin, and its description pin at once, where the
        # owner block beside it refuses a non-object owner
        # outright.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            market = self.read_marketplace(root)
            market["metadata"] = "recognitio"
            self.write_marketplace(root, market)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "carries metadata 'recognitio'" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_joint_author_and_owner_drift_fails(self):
        # Burn-down re-review, third round. The owner
        # values were pinned against the manifest author,
        # and the author itself was pinned nowhere as a
        # value, so the two drifted together to another
        # name and email while the agreement between them
        # held. The author now stands pinned as a value.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["author"] = {
                "name": "Someone Else",
                "email": "someone@example.invalid",
            }
            self.write_manifest(root, data)
            market = self.read_marketplace(root)
            market["owner"] = {
                "name": "Someone Else",
                "email": "someone@example.invalid",
            }
            self.write_marketplace(root, market)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "the shipped author is" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_marketplace_name_drift_fails(self):
        # Burn-down re-review, third round. The marketplace
        # file's top level key set was closed while the
        # value of the file's own name was read by no gate,
        # so the listing renamed itself in silence.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            market = self.read_marketplace(root)
            market["name"] = "another-marketplace"
            self.write_marketplace(root, market)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "the shipped marketplace name is" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_manifest_author_with_an_extra_key_fails(self):
        # Burn-down re-review, fourth round. The author
        # object was pinned as a value and left without a
        # key set, the one object in the pair of files with
        # none, so an invented author key rode in the very
        # object the anchor stands in.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["author"]["url"] = "https://example.invalid"
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "author carries the 'url' key" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_joint_plugin_rename_fails(self):
        # Burn-down re-review, fourth round. The manifest
        # name was read only for its kebab-case shape and
        # the entry name only against the manifest, so the
        # pair renamed the plugin together while their
        # agreement held. The manifest name now stands
        # pinned as a value.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["name"] = "another-plugin"
            self.write_manifest(root, data)
            market = self.read_marketplace(root)
            market["plugins"][0]["name"] = "another-plugin"
            self.write_marketplace(root, market)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "the shipped plugin name is" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_variables_entry_in_bare_value_form_fails(self):
        # Burn-down re-review, fifth round, with its
        # rationale corrected in the sixth. The variables
        # object was read for exactly one forbidden key,
        # so an entry standing as a bare value rode
        # unexamined in a schema the host reads as plugin
        # configuration. The gate pins each entry's shape
        # as a schema object. The plant carries the
        # correspondence the sixth round requires, an
        # mcp.json using the name, whose own presence the
        # gate separately refuses, so the shape limb is
        # the one this test prices.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["variables"] = {"RECOGNITIO_X": "x"}
            self.write_manifest(root, data)
            (root / ".cursor-plugin" / "mcp.json").write_text(
                '{"mcpServers": {"s": {"env": '
                '{"A": "${RECOGNITIO_X}"}}}}',
                encoding="utf-8",
            )
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "variable 'RECOGNITIO_X' standing as" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_variables_name_with_no_correspondence_fails(
        self,
    ):
        # Burn-down re-review, sixth round. The brief
        # ties every declared name to a variable the
        # plugin own mcp.json uses, and the user set
        # values it names are the values a user sets for
        # a variable the plugin declares, not a licence
        # to invent declaration names. An invented name
        # in schema object form rode through the shape
        # pin, so the gate now refuses a declared name
        # no mcp.json variable corresponds to.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["variables"] = {
                "RECOGNITIO_EXTRA": {"type": "string"}
            }
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "variable 'RECOGNITIO_EXTRA', which no "
                    "variable in the plugin mcp.json "
                    "corresponds to" in p
                    for p in problems
                ),
                problems,
            )

    def test_the_variables_correspondence_reads_uses(self):
        # Burn-down re-review, seventh round. The
        # correspondence extractor read the mcp.json as
        # raw text, so a mention inside a description
        # earned a correspondence no use stands behind,
        # a file that is not JSON at all earned one the
        # same way, and the default value, braceless,
        # and spaced brace spellings of a real use earned
        # none. The extractor now reads the file as the
        # structure it is, from its string values with
        # descriptions excepted, in the spellings the
        # hosts substitute.
        refused = (
            '{"mcpServers": {"s": {"description": '
            '"set ${RECOGNITIO_X} in your shell"}}}',
            "note ${RECOGNITIO_X} note",
        )
        for text in refused:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                data = self.read_manifest(root)
                data["variables"] = {
                    "RECOGNITIO_X": {"type": "string"}
                }
                self.write_manifest(root, data)
                (root / ".cursor-plugin" / "mcp.json").write_text(
                    text, encoding="utf-8"
                )
                problems = self.problems(root)
                self.assertTrue(
                    any(
                        "variable 'RECOGNITIO_X', which no "
                        "variable in the plugin mcp.json "
                        "corresponds to" in p
                        for p in problems
                    ),
                    (text, problems),
                )
        earned = (
            "${RECOGNITIO_X:-fallback}",
            "$RECOGNITIO_X",
            "${ RECOGNITIO_X }",
        )
        for spelling in earned:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                data = self.read_manifest(root)
                data["variables"] = {
                    "RECOGNITIO_X": {"type": "string"}
                }
                self.write_manifest(root, data)
                (root / ".cursor-plugin" / "mcp.json").write_text(
                    '{"mcpServers": {"s": {"env": '
                    '{"A": "%s"}}}}' % spelling,
                    encoding="utf-8",
                )
                problems = self.problems(root)
                self.assertFalse(
                    any(
                        "corresponds to" in p for p in problems
                    ),
                    (spelling, problems),
                )

    def test_the_variables_correspondence_operators(self):
        # Burn-down re-review, ninth round. The braced
        # default slot read the dash and equals
        # operators and stopped there, while the
        # substitution grammar the hosts mirror carries
        # the plus and question operators in the same
        # slot, and the percent and slash expansion
        # forms beside them. The slot now reads the
        # operator set of that grammar, and each
        # spelling below earns the correspondence.
        earned = (
            "${RECOGNITIO_X:+fallback}",
            "${RECOGNITIO_X+fallback}",
            "${RECOGNITIO_X:?fallback}",
            "${RECOGNITIO_X?fallback}",
            "${RECOGNITIO_X%fallback}",
            "${RECOGNITIO_X/fallback}",
        )
        for spelling in earned:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                data = self.read_manifest(root)
                data["variables"] = {
                    "RECOGNITIO_X": {"type": "string"}
                }
                self.write_manifest(root, data)
                (root / ".cursor-plugin" / "mcp.json").write_text(
                    '{"mcpServers": {"s": {"env": '
                    '{"A": "%s"}}}}' % spelling,
                    encoding="utf-8",
                )
                problems = self.problems(root)
                self.assertFalse(
                    any(
                        "corresponds to" in p for p in problems
                    ),
                    (spelling, problems),
                )

    def test_the_variables_correspondence_grammar(self):
        # Burn-down re-review, tenth round. The braced
        # operator slot read one operator family and
        # stopped short of the grammar its comment
        # names, while the shell style substitution the
        # hosts mirror carries the prefix removal and
        # case and substring operators in the same
        # slot, and the length and indirect prefix
        # forms at the name's other side. The slot now
        # reads the grammar whole, and each spelling
        # below earns the correspondence.
        earned = (
            "${RECOGNITIO_X#fallback}",
            "${RECOGNITIO_X##fallback}",
            "${RECOGNITIO_X@Q}",
            "${RECOGNITIO_X@a}",
            "${RECOGNITIO_X^fallback}",
            "${RECOGNITIO_X^^fallback}",
            "${RECOGNITIO_X,fallback}",
            "${RECOGNITIO_X,,fallback}",
            "${RECOGNITIO_X:1}",
            "${RECOGNITIO_X: -1}",
            "${RECOGNITIO_X:0:1}",
            "${#RECOGNITIO_X}",
            "${!RECOGNITIO_X}",
            "${RECOGNITIO_X:fallback}",
        )
        for spelling in earned:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                data = self.read_manifest(root)
                data["variables"] = {
                    "RECOGNITIO_X": {"type": "string"}
                }
                self.write_manifest(root, data)
                (root / ".cursor-plugin" / "mcp.json").write_text(
                    '{"mcpServers": {"s": {"env": '
                    '{"A": "%s"}}}}' % spelling,
                    encoding="utf-8",
                )
                problems = self.problems(root)
                self.assertFalse(
                    any(
                        "corresponds to" in p for p in problems
                    ),
                    (spelling, problems),
                )

    def test_the_variables_correspondence_at_depth(self):
        # Burn-down re-review, eighth round. The walk
        # excepted a description only at the leaf it
        # stood on, so a mention inside a description
        # standing as an object earned the correspondence
        # its exception was built to refuse, and the
        # braced default spellings past the colon dash
        # form earned none. The exception now follows the
        # description at any depth, and the default slot
        # reads the dash and equals forms beside it.
        refused = (
            '{"mcpServers": {"s": {"description": '
            '{"text": "set ${RECOGNITIO_X} in your '
            'shell"}}}}',
        )
        for text in refused:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                data = self.read_manifest(root)
                data["variables"] = {
                    "RECOGNITIO_X": {"type": "string"}
                }
                self.write_manifest(root, data)
                (root / ".cursor-plugin" / "mcp.json").write_text(
                    text, encoding="utf-8"
                )
                problems = self.problems(root)
                self.assertTrue(
                    any(
                        "variable 'RECOGNITIO_X', which no "
                        "variable in the plugin mcp.json "
                        "corresponds to" in p
                        for p in problems
                    ),
                    (text, problems),
                )
        earned = (
            "${RECOGNITIO_X-fallback}",
            "${RECOGNITIO_X:=fallback}",
        )
        for spelling in earned:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                data = self.read_manifest(root)
                data["variables"] = {
                    "RECOGNITIO_X": {"type": "string"}
                }
                self.write_manifest(root, data)
                (root / ".cursor-plugin" / "mcp.json").write_text(
                    '{"mcpServers": {"s": {"env": '
                    '{"A": "%s"}}}}' % spelling,
                    encoding="utf-8",
                )
                problems = self.problems(root)
                self.assertFalse(
                    any(
                        "corresponds to" in p for p in problems
                    ),
                    (spelling, problems),
                )

    def test_a_marketplace_top_level_key_fails(self):
        # Burn-down re-review. The repair closed the entry
        # key set and left the marketplace file's own key
        # set unexamined, so an extra top level key rode in
        # silence in a file the gate claims to pin.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            market = self.read_marketplace(root)
            market["hooks"] = {}
            self.write_marketplace(root, market)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "'hooks'" in p and "unexamined" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_marketplace_metadata_key_fails(self):
        # Burn-down re-review. The metadata object inside
        # the marketplace file carries the same closed set
        # discipline as the file itself.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            market = self.read_marketplace(root)
            market["metadata"]["extra"] = "x"
            self.write_marketplace(root, market)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "'extra'" in p and "unexamined" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_marketplace_entry_without_a_description_fails(
        self,
    ):
        # Burn-down re-review. The entry description was an
        # allowed entry key whose value no gate read, so
        # deleting it passed in silence where entry name,
        # version, skills, and logo are all pinned to the
        # manifest.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            market = self.read_marketplace(root)
            del market["plugins"][0]["description"]
            self.write_marketplace(root, market)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "entry carries description" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_marketplace_entry_with_a_drifted_description_fails(
        self,
    ):
        # Burn-down re-review. A drifted entry description
        # is the same unexamined value in its standing form.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            market = self.read_marketplace(root)
            market["plugins"][0]["description"] = (
                "A completely different plugin that does "
                "other things."
            )
            self.write_marketplace(root, market)
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "entry carries description" in p
                    for p in problems
                ),
                problems,
            )

    def test_a_marketplace_entry_with_agreeing_rules_passes(self):
        # Control. An entry rules key that carries the
        # manifest value itself agrees and resolves from
        # the plugin root, so the widened agreement keeps
        # passing it in the other direction.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            market = self.read_marketplace(root)
            market["plugins"][0]["rules"] = [
                "./.cursor-plugin/rules/recognitio.mdc"
            ]
            self.write_marketplace(root, market)
            self.assertEqual(self.problems(root), [])

    def test_an_absolute_manifest_path_fails(self):
        # All manifest paths must be relative with no parent
        # traversal and no absolute paths.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["skills"] = ["/etc/recognitio"]
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("not a relative path" in p for p in problems),
                problems,
            )

    def test_the_manifest_logo_key_is_accepted(self):
        # Visual round 8. The brand logo field joins the
        # closed manifest key list as its one planned repin
        # so a scratch layout carrying the shipped logo
        # value passes the Cursor gate whole.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            self.assertEqual(
                data.get("logo"), "docs/brand/recognitio-icon.svg"
            )
            self.assertEqual(self.problems(root), [])

    def test_an_unknown_manifest_key_still_fails(self):
        # The logo repin opens the list by one key only and
        # an invented key beside the logo still fails.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["invented"] = "docs/brand/recognitio-icon.svg"
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("unknown keys" in p for p in problems),
                problems,
            )

    def test_a_dropped_discovery_field_fails(self):
        # Top 20 item 16. The discovery fields the primary
        # manifest schema names join the manifest as pinned
        # values, so dropping any one of them fails.
        for field in (
            "displayName", "homepage", "repository", "keywords",
            "category", "tags",
        ):
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                data = self.read_manifest(root)
                del data[field]
                self.write_manifest(root, data)
                problems = self.problems(root)
                self.assertTrue(
                    any(field in p for p in problems),
                    (field, problems),
                )

    def test_a_changed_discovery_value_fails(self):
        # A drifted display name or a keyword set that lost
        # a term no longer matches the pinned values.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["displayName"] = "Recognitio Review"
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("displayName" in p for p in problems),
                problems,
            )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            data = self.read_manifest(root)
            data["keywords"] = data["keywords"][:-1]
            self.write_manifest(root, data)
            problems = self.problems(root)
            self.assertTrue(
                any("keywords" in p for p in problems),
                problems,
            )

    def test_a_dropped_discovery_brief_pin_fails(self):
        # The brief states the discovery contract, and the
        # gate pins the sentences so a later edit cannot
        # quietly drop them.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.assertIn(
                "The manifest also carries the discovery fields",
                text,
            )
            text = text.replace(
                "The manifest also carries the discovery fields",
                "The manifest also carries the listing fields",
            )
            self.write_brief(root, text)
            problems = self.problems(root)
            self.assertTrue(
                any("discovery fields" in p for p in problems),
                problems,
            )

    def test_a_dropped_security_review_pin_fails(self):
        # R31-EX-03. The Build 10 brief pins the Security
        # Review separation, scope, team rules, draft skip,
        # and plan gate, plus the Origin launch path beside
        # the Cursor plugin path.
        cases = (
            ("Security Review is a separate bot from Bugbot",
             "Security Review separation"),
            ("injection across SQL, command, and template surfaces",
             "Security Review scope"),
            ("enforces them on every pull request",
             "Security Review team rules"),
            ("Draft pull requests are skipped",
             "Security Review draft skip"),
            ("gated to Teams and Enterprise plans",
             "Security Review plan gate"),
            ("built in review-security skill",
             "review-security skill"),
            ("Origin App Marketplace launched October 13 2026",
             "Origin launch path"),
            ("not the only CodeRabbit in Cursor path",
             "Origin not only plugin path"),
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

    def test_a_decision_record_without_decision_4_fails(self):
        # Every landed build records a decision 4 statement. A
        # Build 10 record without one fails the pin.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            path = root / "docs" / "decisions.md"
            text = path.read_text(encoding="utf-8")
            start = text.find("## 19. Build 10")
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


    def test_cap_figure_and_bugbot_control_plants_fail(self):
        # R36-RT-03. A repository cap figure stated alone,
        # a bugbot.yaml effort pin, and a merge blocking
        # neutral conclusion each passed while the pins
        # stayed in place, because no check read a
        # contradicting brief sentence.
        cases = (
            ("A cloud agent environment supports up to 500 "
             "repositories.", "cap figure of 500"),
            ("A cloud agent environment supports up to 300 "
             "repositories.", "cap figure of 300"),
            ("Bugbot effort can be pinned at High in "
             "bugbot.yaml for this repository.",
             "pins Bugbot effort"),
            ("A neutral Bugbot conclusion blocks merges on "
             "findings.", "neutral Bugbot conclusion"),
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

    def test_a_cap_figure_with_the_conflict_note_passes(self):
        # R36-RT-03. A cap figure stated with the R35-C-01
        # conflict named beside it in the same sentence is
        # the one allowed form, so it passes.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root,
                text + "\n\nOne primary page supports up to "
                "500 repositories and another states 300, "
                "and the conflict stands unresolved.\n",
            )
            self.assertEqual(self.problems(root), [])

    def test_gate_review_cursor_restated_plants_fail(self):
        # Gate review repair. The first cap branch needed a
        # bounding verb and exempted a sentence naming both
        # figures, the effort branch read a 50 character
        # window and three pin verbs, and the neutral branch
        # read one verb form, so the review restated every
        # plant just outside those shapes and each passed.
        cases = (
            ("A cloud agent environment has 500 "
             "repositories.", "cap figure of 500"),
            ("Cloud agent environments get 500 repositories "
             "each.", "cap figure of 500"),
            ("A cloud agent environment supports up to five "
             "hundred repositories.",
             "cap figure of five hundred"),
            ("A cloud agent environment supports up to 500 "
             "repositories, while another page says 300 "
             "repositories.", "cap figure of 500"),
            ("The bugbot.yaml file controls Bugbot effort "
             "for this repository.", "pins Bugbot effort"),
            ("Bugbot effort for this repository, across all "
             "reviews and all teams in the organization, can "
             "be pinned in bugbot.yaml.",
             "pins Bugbot effort"),
            ("A neutral Bugbot conclusion stops merges on "
             "findings.", "neutral Bugbot conclusion"),
            ("A neutral Bugbot conclusion blocked merges on "
             "findings.", "neutral Bugbot conclusion"),
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

    def test_gate_review_cursor_cannot_control_passes(self):
        # Gate review repair. The effort guard read the
        # words not and never, so the same true sentence
        # with cannot in place of never failed the gate.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root,
                text + "\n\nEffort cannot be pinned in "
                "bugbot.yaml, because effort is a dashboard "
                "setting only.\n",
            )
            self.assertEqual(self.problems(root), [])

    def test_round37_neutral_conclusion_split_across_sentences_fails(self):
        # R37-RT-06. The pronoun carries the neutral
        # conclusion into a second sentence that holds the
        # blocking verb, and the pair reading must catch it.
        plant = (
            "Bugbot findings default to a neutral "
            "conclusion. That conclusion blocks merges in "
            "this repository."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "neutral Bugbot conclusion blocking" in p
                    for p in problems
                ),
                problems,
            )

    def test_round37_cap_figure_past_the_reach_fails(self):
        # R37-RT-06 and R35-C-01. Filler between the figure
        # and the word repositories no longer shelters a
        # cap figure stated without the conflict note.
        plant = (
            "A cloud agent environment supports up to 500 "
            "carefully counted and individually tracked "
            "repositories in this workspace."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "repository cap figure of 500" in p
                    for p in problems
                ),
                problems,
            )

    def test_round37_effort_pin_past_the_reach_fails(self):
        # R37-RT-06. The effort pin stated across a long
        # dashboard filler must fail at sentence scope.
        plant = (
            "Bugbot effort, as a dashboard value that the "
            "workspace admin reviews each quarter alongside "
            "the other review choices for this repository "
            "and its sibling projects in the same "
            "organisation and its partner teams abroad, is "
            "pinned in bugbot.yaml."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "pins Bugbot effort in bugbot.yaml" in p
                    for p in problems
                ),
                problems,
            )


    def test_round37_grouped_cap_figure_is_named_in_full(self):
        # Gate review repair. A comma grouped figure binds
        # as one figure, so the problem names 100,000 and
        # not the truncated 100 the digit run alone reads.
        plant = (
            "A cloud agent environment supports up to "
            "100,000 repositories in this workspace."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "repository cap figure of 100,000" in p
                    for p in problems
                ),
                problems,
            )

    def test_round37_fixreview_unit_word_in_parenthetical_fails(self):
        # R37F-RT-07. A unit word inside a parenthetical
        # after the figure does not rebind it, because the
        # figure's unit position stands empty, so the cap
        # figure still binds to repositories.
        plant = (
            "A cloud agent environment supports up to 500, "
            "counting files separately, repositories in "
            "this workspace."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "repository cap figure of 500" in p
                    for p in problems
                ),
                problems,
            )

    def test_round37_fixreview_idle_negation_does_not_guard(self):
        # R37F-RT-08. A negation joined to the blocking
        # verb by a coordinating and modifies the earlier
        # verb, so the neutral conclusion blocking merges
        # still fails.
        plant = (
            "Bugbot findings default to a neutral "
            "conclusion. That conclusion never sits idle "
            "and blocks merges in this repository."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "conclusion blocking merges" in p
                    for p in problems
                ),
                problems,
            )

    def test_round37_fixreview_effort_in_another_clause_passes(self):
        # R37F-RT-09. Effort in one coordinating unit and
        # a pin verb in the next state no pin, so the true
        # sentence must pass.
        sentence = (
            "Bugbot effort is a dashboard setting, and the "
            "autofix mode is pinned in bugbot.yaml."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root, text + "\n\n" + sentence + "\n"
            )
            self.assertEqual(self.problems(root), [])

    def test_round37_fixreview_count_of_another_noun_passes(self):
        # R37F-RT-09. A figure followed directly by its own
        # count noun binds to that noun, so a workspace
        # listing 500 issues across its repositories
        # states no repository cap figure and must pass.
        sentence = (
            "The workspace lists 500 issues across its "
            "repositories."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(
                root, text + "\n\n" + sentence + "\n"
            )
            self.assertEqual(self.problems(root), [])

    def test_round37_confirm2_neutral_comma_splice_fails(self):
        # R37C-RT-04. A comma splice joins the verbs the
        # same way a coordinating and does, so a negation
        # before the comma modifies the earlier verb and
        # does not guard the blocking verb.
        plant = (
            "Bugbot findings default to a neutral "
            "conclusion. That conclusion never sits idle, "
            "blocks merges in this repository."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any("neutral" in p for p in problems), problems
            )

    def test_round37_confirm2_effort_plain_and_units_pass(self):
        # R37C-RT-05. A comma free sentence joins its
        # units with the plain joint alone, so effort in
        # one unit and a pin verb in the next state no pin
        # and the true sentence passes.
        plant = (
            "Bugbot effort is a dashboard setting and the "
            "autofix mode is pinned in bugbot.yaml."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertFalse(
                any("effort" in p for p in problems), problems
            )

    def test_round37_confirm2_cap_parenthetical_behind_fails(self):
        # Unnumbered confirmation shape. A unit word in a
        # parenthetical between the target and its figure
        # is not in the figure unit position behind the
        # target either, so the cap figure still binds.
        plant = (
            "Repositories in this workspace, counting files "
            "separately, number 500 in this environment."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "repository cap figure of 500" in p
                    for p in problems
                ),
                problems,
            )


    def test_round38_neutral_split_across_three_sentences_fails(self):
        # R38-RT-05. The neutral claim split across three
        # sentences with a filler between the halves stands
        # in no pair, and the paragraph scope reading must
        # catch it.
        plant = (
            "Bugbot findings default to a neutral "
            "conclusion. The packet lists each finding "
            "beside its diff. That conclusion blocks "
            "merges in this repository."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "neutral Bugbot conclusion blocking" in p
                    for p in problems
                ),
                problems,
            )

    def test_round38_neutral_semicolon_negation_does_not_guard(self):
        # R38-RT-06. A negation before a semicolon modifies
        # the earlier verb alone, so the blocking claim
        # after the semicolon still fails.
        plant = (
            "Bugbot findings default to a neutral "
            "conclusion. That conclusion never sits idle; "
            "blocks merges in this repository."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "neutral Bugbot conclusion blocking" in p
                    for p in problems
                ),
                problems,
            )

    def test_gate_round38_cli_attempt_note_pins_hold(self):
        # Round 38 CLI attempt note. Dropping any of the
        # amended note sentences fails the gate, so the
        # CLI surface record cannot quietly soften back
        # into the blocked API attempt wording or grow a
        # desktop claim the attempt never observed.
        fragments = (
            "no session included a recognitio plugin manifest",
            "the entry pointed at the .claude/skills spelling "
            "of the canonical skill",
            "the plugin tree copy never appeared as a skill "
            "entry in any session",
            "no claim in this note rests on a skill count",
            "no session named the plugin rule file or "
            "BUGBOT.md as in effect on that surface",
        )
        for fragment in fragments:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                problems = self.break_brief(
                    root, fragment, "the record omits this"
                )
                label = {
                    frag: lab for lab, frag in self.mod.PINNED
                }[fragment]
                self.assertTrue(
                    any(label in p for p in problems),
                    (fragment, problems),
                )

    def test_desktop_verification_pins_hold(self):
        # Desktop verification of 2026-10-25. Dropping any
        # of the settled desktop sentences fails the gate,
        # so the brief cannot drift back to carrying the
        # desktop questions as open once the real client
        # run answered them. The precedence fragment that
        # stood here moved to the CLI precedence pins,
        # because the CLI run settled that question on its
        # surface later the same day.
        fragments = (
            "The duplicate skill residual is settled at the "
            "level of desktop registration",
            "the official Cursor desktop build 3.27.12 for "
            "Linux ran here under a virtual display",
            "recorded the recognitio plugin loaded with zero "
            "failures five times in the first launch",
            "every recorded load happened before any "
            "sign-in",
            "the Customize backing records, which list a "
            "skill entry and a rule entry pointing at the "
            "local plugin copies",
            "the Customize backing records held two "
            "recognitio skill entries side by side",
            "the desktop deduped neither entry",
            "Marketplace installation from a listing and "
            "Bugbot behaviour on a real pull request stay "
            "UNVERIFIED",
        )
        for fragment in fragments:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                problems = self.break_brief(
                    root, fragment, "the record omits this"
                )
                label = {
                    frag: lab for lab, frag in self.mod.PINNED
                }[fragment]
                self.assertTrue(
                    any(label in p for p in problems),
                    (fragment, problems),
                )

    def test_the_superseded_desktop_sentences_fail(self):
        # Desktop verification of 2026-10-25. Each pre run
        # sentence the desktop evidence falsified or
        # discharged fails the gate when planted back,
        # because the positive pins alone would let a
        # restored stale sentence ride beside them.
        plants = (
            "This box has no Cursor client, so the real "
            "client run is owed.",
            "The local simulation of the documented rule in "
            "this round's gate is the evidence that stands "
            "in until that run happens.",
            "Cursor plugin load behaviour in the desktop "
            "client stays UNVERIFIED.",
            "Duplicate skill behaviour on the Cursor agent "
            "CLI surface was observed in round 38 and stays "
            "UNVERIFIED for the desktop client.",
            "The duplicate skill residual stays UNVERIFIED "
            "at primary, and the standing guidance is "
            "unchanged.",
            "The real desktop client run remains owed under "
            "the protocol in this brief.",
        )
        for plant in plants:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                text = self.read_brief(root)
                self.write_brief(root, text + "\n\n" + plant + "\n")
                problems = self.problems(root)
                self.assertTrue(
                    any("stale" in p for p in problems),
                    (plant, problems),
                )

    def test_cli_precedence_pins_hold(self):
        # CLI precedence run of 2026-10-25. Dropping any
        # of the settled precedence sentences fails the
        # gate, so the brief cannot drift back to carrying
        # invocation precedence as open on every surface
        # once the live CLI sessions answered it.
        fragments = (
            "Invocation precedence is settled on the agent "
            "CLI surface",
            "stays open on the desktop client alone",
            "two in the shipped state and two in the "
            "duplicate state",
            "a distinct marker line appended to each copy "
            "of the skill",
            "installed at .cursor/plugins/local/recognitio "
            "in the session home",
            "each session invoked the workspace copy at "
            "the .claude/skills/recognitio/SKILL.md "
            "spelling",
            "registered as a second entry and was never "
            "invoked",
            "each session invoked the added copy at "
            ".cursor/skills/recognitio/SKILL.md",
            "took the workspace seat outright while the "
            ".claude spelling entry left the catalog",
            "The repo root plugin tree at .cursor-plugin "
            "appeared as an entry in no session",
            "no signed-in desktop session could be landed "
            "on this box",
            "login-session poll never received a completed "
            "sign-in across the original run and the "
            "repaired relaunch",
            "the evidence stands in the desktop "
            "precedence report and the sign-in repair "
            "report",
        )
        for fragment in fragments:
            with tempfile.TemporaryDirectory() as tmp:
                root = self.make_layout(tmp)
                problems = self.break_brief(
                    root, fragment, "the record omits this"
                )
                label = {
                    frag: lab for lab, frag in self.mod.PINNED
                }[fragment]
                self.assertTrue(
                    any(label in p for p in problems),
                    (fragment, problems),
                )

    def test_the_superseded_precedence_sentence_fails(self):
        # CLI precedence run of 2026-10-25. The open
        # precedence sentence the run superseded fails the
        # gate when planted back, because the positive
        # pins alone would let a restored stale sentence
        # ride beside them.
        plant = (
            "Invocation precedence stays open, because both "
            "copies register with no precedence field in "
            "the Customize data and a live agent session "
            "requires a sign-in the run did not perform."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any("stale" in p for p in problems),
                (plant, problems),
            )

    def test_gate_round38_neutral_split_across_paragraphs_fails(self):
        # R38G-RT-04. The neutral claim split across a
        # paragraph break inside one block stands in no
        # paragraph window, and the claim scope reading
        # must catch it.
        plant = (
            "Bugbot findings default to a neutral "
            "conclusion. The packet lists each finding "
            "beside its diff.\n\n"
            "That conclusion blocks merges in this "
            "repository."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "neutral Bugbot conclusion blocking" in p
                    for p in problems
                ),
                problems,
            )

    def test_gate_round38_cap_split_across_paragraphs_fails(self):
        # R38G-RT-04. The cap figure and the repositories
        # it counts split across a paragraph break inside
        # one block state one cap claim, and the claim
        # scope pair reading must catch it.
        plant = (
            "A cloud agent environment supports up to 500 "
            "in this workspace.\n\n"
            "Those are repositories counted across every "
            "team in the organisation."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "repository cap figure of 500" in p
                    for p in problems
                ),
                problems,
            )

    def test_round38_cap_split_across_two_sentences_fails(self):
        # R38-RT-07. The cap figure in one sentence and the
        # repositories it counts named in the next, carried
        # by a deictic opening, state one cap claim with no
        # conflict note beside it.
        plant = (
            "A cloud agent environment supports up to 500 "
            "in this workspace. Those are repositories "
            "counted across every team in the organisation."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_layout(tmp)
            text = self.read_brief(root)
            self.write_brief(root, text + "\n\n" + plant + "\n")
            problems = self.problems(root)
            self.assertTrue(
                any(
                    "repository cap figure of 500" in p
                    for p in problems
                ),
                problems,
            )


class TestRound5Cursor(unittest.TestCase):
    def setUp(self):
        self.inner = TestCheckCursor()
        self.inner.setUp()
        self.mod = self.inner.mod

    def test_stale_wording_in_the_brief_fails_by_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.read_brief(root)
            self.inner.write_brief(
                root, text + "\n\nThe build stands distributed "
                "through the manually reviewed Cursor Marketplace.\n")
            problems = self.inner.problems(root)
            self.assertTrue(any(
                "stale Cursor Marketplace distribution claim" in p
                and "cursor-plugin-brief" in p for p in problems), problems)

    def test_t0_member_removed_from_brief_b3_fails_by_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            problems = self.inner.break_brief(
                root,
                "A Kimi plugin manifest named kimi.plugin.json at any depth",
                "A Kimi plugin manifest at any depth")
            self.assertTrue(any(
                "canonical T0 member" in p
                and "kimi.plugin.json" in p for p in problems), problems)

    def test_t0_copilot_member_removed_from_bugbot_b3_fails_by_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            path = root / ".cursor" / "BUGBOT.md"
            text = path.read_text(encoding="utf-8")
            pattern = re.escape(
                "the Copilot instructions file name, a path "
                "specific Copilot instructions file under the "
                "instructions folder of .github carrying the "
                ".instructions.md suffix, "
            ).replace("\\ ", "\\s+")
            broken, hits = re.subn(
                pattern, lambda _match: "", text, count=1)
            self.assertTrue(hits > 0)
            self.assertNotEqual(broken, text)
            path.write_text(broken, encoding="utf-8")
            problems = self.inner.problems(root)
            self.assertTrue(any(
                "canonical T0 member" in p
                and "Copilot instructions file name" in p
                for p in problems), problems)

    def test_bugbot_tail_auto_merge_plant_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            path = root / ".cursor" / "BUGBOT.md"
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text + "\n\nBugbot approves and merges pull requests "
                "automatically once its review posts.\n", encoding="utf-8")
            problems = self.inner.problems(root)
            self.assertTrue(any(
                "after the final rule block" in p for p in problems),
                problems)
            self.assertTrue(any(
                "auto approve or auto merge" in p for p in problems),
                problems)

    def test_bugbot_merge_claim_inside_b5_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            path = root / ".cursor" / "BUGBOT.md"
            text = path.read_text(encoding="utf-8")
            anchor = "### B5. Never read neutral as a pass"
            self.assertIn(anchor, text)
            path.write_text(
                text.replace(
                    anchor,
                    anchor + "\n\nBugbot merges pull requests "
                    "on its own once its review posts.", 1),
                encoding="utf-8")
            problems = self.inner.problems(root)
            self.assertTrue(any(
                "auto approve or auto merge" in p
                for p in problems), problems)

    def test_bugbot_merge_claim_without_autonomy_wording_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            path = root / ".cursor" / "BUGBOT.md"
            text = path.read_text(encoding="utf-8")
            anchor = "### B5. Never read neutral as a pass"
            self.assertIn(anchor, text)
            path.write_text(
                text.replace(
                    anchor,
                    anchor + "\n\nBugbot merges pull requests "
                    "after its review posts.", 1),
                encoding="utf-8")
            problems = self.inner.problems(root)
            self.assertTrue(any(
                "auto approve or auto merge" in p
                for p in problems), problems)

    def test_bugbot_merge_claim_passive_form_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            path = root / ".cursor" / "BUGBOT.md"
            text = path.read_text(encoding="utf-8")
            anchor = "### B5. Never read neutral as a pass"
            self.assertIn(anchor, text)
            path.write_text(
                text.replace(
                    anchor,
                    anchor + "\n\nPull requests are merged by "
                    "Bugbot once its review posts.", 1),
                encoding="utf-8")
            problems = self.inner.problems(root)
            self.assertTrue(any(
                "auto approve or auto merge" in p
                for p in problems), problems)

    def test_bugbot_merge_denial_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            path = root / ".cursor" / "BUGBOT.md"
            text = path.read_text(encoding="utf-8")
            anchor = "### B5. Never read neutral as a pass"
            self.assertIn(anchor, text)
            path.write_text(
                text.replace(
                    anchor,
                    anchor + "\n\nBugbot never merges pull "
                    "requests, and a warning names any tool "
                    "that merges pull requests on its own.", 1),
                encoding="utf-8")
            problems = self.inner.problems(root)
            self.assertFalse(any(
                "auto approve or auto merge" in p
                for p in problems), problems)

    def test_bugbot_merge_claim_abbreviated_object_inside_b5_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            path = root / ".cursor" / "BUGBOT.md"
            text = path.read_text(encoding="utf-8")
            anchor = "### B5. Never read neutral as a pass"
            self.assertIn(anchor, text)
            path.write_text(
                text.replace(
                    anchor,
                    anchor + "\n\nBugbot merges PRs on its "
                    "own once its review posts.", 1),
                encoding="utf-8")
            problems = self.inner.problems(root)
            self.assertTrue(any(
                "auto approve or auto merge" in p
                for p in problems), problems)

    def test_bugbot_merge_denial_abbreviated_object_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            path = root / ".cursor" / "BUGBOT.md"
            text = path.read_text(encoding="utf-8")
            anchor = "### B5. Never read neutral as a pass"
            self.assertIn(anchor, text)
            path.write_text(
                text.replace(
                    anchor,
                    anchor + "\n\nBugbot never merges PRs, "
                    "and a warning names any tool that merges "
                    "PRs on its own.", 1),
                encoding="utf-8")
            problems = self.inner.problems(root)
            self.assertFalse(any(
                "auto approve or auto merge" in p
                for p in problems), problems)

    def test_bugbot_merge_claim_pronoun_autonomy_inside_b5_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            path = root / ".cursor" / "BUGBOT.md"
            text = path.read_text(encoding="utf-8")
            anchor = "### B5. Never read neutral as a pass"
            self.assertIn(anchor, text)
            path.write_text(
                text.replace(
                    anchor,
                    anchor + "\n\nBugbot reads each pull "
                    "request in full. It merges it on its own "
                    "once its review posts.", 1),
                encoding="utf-8")
            problems = self.inner.problems(root)
            self.assertTrue(any(
                "auto approve or auto merge" in p
                for p in problems), problems)

    def test_bugbot_merge_claim_description_autonomy_inside_b5_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            path = root / ".cursor" / "BUGBOT.md"
            text = path.read_text(encoding="utf-8")
            anchor = "### B5. Never read neutral as a pass"
            self.assertIn(anchor, text)
            path.write_text(
                text.replace(
                    anchor,
                    anchor + "\n\nBugbot merges the change "
                    "under review on its own once its review "
                    "posts.", 1),
                encoding="utf-8")
            problems = self.inner.problems(root)
            self.assertTrue(any(
                "auto approve or auto merge" in p
                for p in problems), problems)

    def test_bugbot_merge_denial_autonomy_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            path = root / ".cursor" / "BUGBOT.md"
            text = path.read_text(encoding="utf-8")
            anchor = "### B5. Never read neutral as a pass"
            self.assertIn(anchor, text)
            path.write_text(
                text.replace(
                    anchor,
                    anchor + "\n\nBugbot never merges it on "
                    "its own once its review posts.", 1),
                encoding="utf-8")
            problems = self.inner.problems(root)
            self.assertFalse(any(
                "auto approve or auto merge" in p
                for p in problems), problems)

    def test_bugbot_merge_pronoun_without_autonomy_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            path = root / ".cursor" / "BUGBOT.md"
            text = path.read_text(encoding="utf-8")
            anchor = "### B5. Never read neutral as a pass"
            self.assertIn(anchor, text)
            path.write_text(
                text.replace(
                    anchor,
                    anchor + "\n\nBugbot reads each pull "
                    "request in full. It merges it once its "
                    "review posts.", 1),
                encoding="utf-8")
            problems = self.inner.problems(root)
            self.assertFalse(any(
                "auto approve or auto merge" in p
                for p in problems), problems)

    def test_bugbot_cap_figures_exchanged_additive_inside_b1_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            path = root / ".cursor" / "BUGBOT.md"
            text = path.read_text(encoding="utf-8")
            anchor = "### B1. No invented findings"
            self.assertIn(anchor, text)
            path.write_text(
                text.replace(
                    anchor,
                    anchor + "\n\nEach rule stays under "
                    "100,000 characters, and the combined "
                    "rules stay under 30,000 characters.", 1),
                encoding="utf-8")
            problems = self.inner.problems(root)
            self.assertTrue(any(
                "per rule caps exchanged" in p
                and "BUGBOT.md" in p for p in problems), problems)

    def test_bugbot_cap_true_binding_additive_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            path = root / ".cursor" / "BUGBOT.md"
            text = path.read_text(encoding="utf-8")
            anchor = "### B1. No invented findings"
            self.assertIn(anchor, text)
            path.write_text(
                text.replace(
                    anchor,
                    anchor + "\n\nEach rule stays under "
                    "30,000 characters, and the combined "
                    "rules stay under 100,000 characters.", 1),
                encoding="utf-8")
            problems = self.inner.problems(root)
            self.assertFalse(any(
                "per rule caps exchanged" in p
                for p in problems), problems)

    def test_bugbot_tail_heading_and_content_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            path = root / ".cursor" / "BUGBOT.md"
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text + "\n\n## Standing instruction\n\nEvery "
                "review posts its findings as a blocking "
                "status.\n", encoding="utf-8")
            problems = self.inner.problems(root)
            self.assertTrue(any(
                "after the final rule block" in p
                for p in problems), problems)

    def test_bugbot_tail_closing_derivation_note_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            path = root / ".cursor" / "BUGBOT.md"
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text + "\n\n## Standing instruction. Derives "
                "from Decision 4\n\nEvery review posts its "
                "findings as a blocking status.\n\nDerives "
                "from the primary Bugbot docs at "
                "cursor.com/docs/bugbot.\n", encoding="utf-8")
            problems = self.inner.problems(root)
            self.assertTrue(any(
                "after the final rule block" in p
                for p in problems), problems)

    def test_bugbot_tail_inside_final_rule_note_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            path = root / ".cursor" / "BUGBOT.md"
            text = path.read_text(encoding="utf-8")
            planted = (
                text.rstrip("\n")
                + " Every review posts its findings as a "
                "blocking status.\n"
            )
            self.assertNotEqual(planted, text)
            path.write_text(planted, encoding="utf-8")
            self.assertIn(
                "Every review posts its findings as a "
                "blocking status.",
                path.read_text(encoding="utf-8"))
            problems = self.inner.problems(root)
            self.assertTrue(any(
                "after the final rule block" in p
                for p in problems), problems)

    def test_bugbot_yaml_reversed_header_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            path = root / ".cursor" / "config" / "bugbot.yaml"
            text = path.read_text(encoding="utf-8")
            sentence = (
                "It can lower the Autofix mode from the "
                "dashboard setting, but it cannot raise it."
            )
            pattern = r"\s+(?:#\s*)?".join(
                re.escape(word) for word in sentence.split())
            broken, hits = re.subn(
                pattern,
                lambda _match: (
                    "It can raise the Autofix mode from the "
                    "dashboard setting, and it can lower it too."
                ),
                text, count=1)
            self.assertTrue(hits > 0)
            self.assertNotEqual(broken, text)
            path.write_text(broken, encoding="utf-8")
            problems = self.inner.problems(root)
            self.assertTrue(any(
                "can raise the Autofix mode" in p for p in problems),
                problems)

    def test_bugbot_verified_glance_plant_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.read_brief(root)
            planted = (
                text + "\n\nBugbot behaviour on a real pull "
                "request is verified.\n"
            )
            self.assertNotEqual(planted, text)
            self.assertIn(
                "Bugbot behaviour on a real pull request "
                "is verified.", planted)
            self.inner.write_brief(root, planted)
            self.assertIn(
                "Bugbot behaviour on a real pull request "
                "is verified.", self.inner.read_brief(root))
            problems = self.inner.problems(root)
            self.assertTrue(any(
                "Bugbot" in p and "is verified" in p for p in problems),
                problems)

    def test_bugbot_verified_glance_claim_reworded_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.read_brief(root)
            self.inner.write_brief(
                root, text + "\n\nBugbot behaviour on a real "
                "pull request stands confirmed.\n")
            problems = self.inner.problems(root)
            self.assertTrue(any(
                "Bugbot" in p and "is verified" in p
                for p in problems), problems)

    def test_bugbot_verified_guard_in_given_that_clause_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.read_brief(root)
            self.inner.write_brief(
                root, text + "\n\nThe brief never claims a "
                "check given that Bugbot behaviour on a real "
                "pull request is verified.\n")
            problems = self.inner.problems(root)
            self.assertTrue(any(
                "Bugbot" in p and "is verified" in p
                for p in problems), problems)

    def test_bugbot_verified_guard_in_while_clause_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.read_brief(root)
            self.inner.write_brief(
                root, text + "\n\nThe brief never claims a "
                "check while Bugbot behaviour on a real pull "
                "request is verified.\n")
            problems = self.inner.problems(root)
            self.assertTrue(any(
                "Bugbot" in p and "is verified" in p
                for p in problems), problems)

    def test_readme_pinning_block_stale_form_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.read_readme(root)
            pattern = (
                r"cp -r[\s\\]+recognitio-pinned[\s\\]+"
                r"~/.cursor/plugins/local/[\s\\]+recognitio"
            )
            broken, hits = re.subn(
                pattern,
                lambda _match: (
                    "cp -r recognitio-pinned/.cursor-plugin "
                    "~/.cursor/plugins/local/recognitio"
                ),
                text, count=1)
            self.assertTrue(hits > 0)
            self.assertNotEqual(broken, text)
            self.inner.write_readme(root, broken)
            problems = self.inner.problems(root)
            self.assertTrue(any(
                "pinning block" in p for p in problems), problems)


class TestRound5SecondSeatCursor(unittest.TestCase):
    def setUp(self):
        self.inner = TestCheckCursor()
        self.inner.setUp()
        self.mod = self.inner.mod

    def test_b4_restatement_in_bugbot_moved_to_combined_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            path = root / ".cursor" / "BUGBOT.md"
            text = path.read_text(encoding="utf-8")
            b4 = text.find("### B4.")
            self.assertGreaterEqual(b4, 0)
            head, tail = text[:b4], text[b4:]
            tail = tail.replace(
                "Each rule stays under 30,000 characters",
                "Each rule stays under 100,000 characters", 1)
            path.write_text(head + tail, encoding="utf-8")
            problems = self.inner.problems(root)
            self.assertTrue(any(
                "rule B4 does not bind the per rule cap" in p
                and "BUGBOT" in p for p in problems), problems)

    def test_b4_restatement_in_brief_moved_to_combined_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.read_brief(root)
            b4 = text.find("### B4.")
            self.assertGreaterEqual(b4, 0)
            head, tail = text[:b4], text[b4:]
            tail = tail.replace(
                "Each rule stays under 30,000 characters",
                "Each rule stays under 100,000 characters", 1)
            self.inner.write_brief(root, head + tail)
            problems = self.inner.problems(root)
            self.assertTrue(any(
                "rule B4 does not bind the per rule cap" in p
                and "cursor-plugin-brief" in p
                for p in problems), problems)

    def test_caps_exchange_additive_sentence_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.inner.make_layout(tmp)
            text = self.inner.read_brief(root)
            self.inner.write_brief(
                root, text + "\n\nThe combined rules are capped "
                "at 30,000 characters and each rule is capped "
                "at 100,000 characters.\n")
            problems = self.inner.problems(root)
            self.assertTrue(any(
                "attaches a cap figure to the wrong scope" in p
                for p in problems), problems)


if __name__ == "__main__":
    unittest.main()


class TestRound15CursorTreeMap(unittest.TestCase):
    """Round 15. The tree map records a symlinked entry."""

    def setUp(self):
        self.base = TestCheckCursor()
        self.base.setUp()
        self.mod = self.base.mod

    def test_an_entry_level_symlink_inside_a_real_copy_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.base.make_layout(tmp)
            copy = root / ".cursor-plugin" / "skills" / "recognitio"
            (copy / "planted-link.md").symlink_to(copy / "SKILL.md")
            problems = self.base.problems(root)
            self.assertTrue(problems)
            self.assertTrue(
                any("planted-link" in p for p in problems), problems
            )

    def test_tree_bytes_records_the_symlink_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "tree"
            folder.mkdir()
            (folder / "real.md").write_text("real", encoding="utf-8")
            (folder / "link.md").symlink_to(folder / "real.md")
            found = self.mod.tree_bytes(folder)
            self.assertEqual(found["real.md"], b"real")
            self.assertIsNone(found["link.md"])


class TestRound24BriefDerivation(unittest.TestCase):
    """Round 24 spec Minor 1. The brief derivation judgement.

    The closure reading exempts the numbered rule blocks on
    the ground that each rule carries its derivation note.
    Ten brief gates enforce that ground over their briefs,
    and this gate enforced it only over BUGBOT.md, so the
    note of a brief rule could be stripped, or restated
    naming no source, and the gate exited green over both.
    The gate now runs the same judgement over the brief
    rules that it runs over the Bugbot rules.
    """

    def setUp(self):
        self.base = TestCheckCursor()
        self.base.setUp()
        self.mod = self.base.mod

    def test_the_shipped_brief_rules_carry_their_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.base.make_layout(tmp)
            raw = self.base.read_brief(root)
            section = self.mod.rules_section(raw)
            self.assertEqual(
                self.mod.brief_derivation_problems(section), [])
            problems = self.base.problems(root)
            self.assertFalse(
                any("derivation note" in p for p in problems),
                problems,
            )

    def test_stripping_the_first_rule_note_draws_the_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.base.make_layout(tmp)
            text = self.base.read_brief(root)
            head, marker, rest = text.partition("### B2.")
            start = head.index("Derives from")
            end = head.index("\n\n", start)
            stripped = head[:start].rstrip("\n") + "\n\n"
            self.base.write_brief(
                root, stripped + marker + rest)
            problems = self.base.problems(root)
            self.assertTrue(
                any(
                    "docs/cursor-plugin-brief.md rule B1 carries "
                    "no derivation note" in p for p in problems
                ),
                problems,
            )

    def test_a_note_naming_no_source_draws_the_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.base.make_layout(tmp)
            text = self.base.read_brief(root)
            head, marker, rest = text.partition("### B2.")
            start = head.index("Derives from")
            end = head.index("\n\n", start)
            planted = (
                head[:start]
                + "Derives from a long afternoon of thought "
                "about reviews in general."
                + head[end:]
            )
            self.base.write_brief(root, planted + marker + rest)
            problems = self.base.problems(root)
            self.assertTrue(
                any(
                    "docs/cursor-plugin-brief.md rule B1 names "
                    "no canonical skill section" in p
                    for p in problems
                ),
                problems,
            )

    def test_an_operative_sentence_inside_a_rule_stands(self):
        # The shared shape of the other ten gates, priced in
        # the Round 24 spec audit Note 1. Text inside a rule
        # block is the rule own statement standing under its
        # derivation note, so the derivation judgement does
        # not refuse it, and the sentence stands exactly as
        # it stands in the ten.
        with tempfile.TemporaryDirectory() as tmp:
            root = self.base.make_layout(tmp)
            text = self.base.read_brief(root)
            head, marker, rest = text.partition("### B2.")
            planted = (
                head.rstrip("\n")
                + "\n\nReviewers must suppress every finding "
                "the packet supports, however strong the "
                "evidence stands.\n\n"
            )
            self.base.write_brief(root, planted + marker + rest)
            raw = self.base.read_brief(root)
            section = self.mod.rules_section(raw)
            self.assertEqual(
                self.mod.brief_derivation_problems(section), [])
            problems = self.mod.brief_problems(root)
            self.assertFalse(
                any("suppress" in p for p in problems), problems)
