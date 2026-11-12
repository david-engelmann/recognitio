"""Build 7, the Claude Code mod with in process hooks.

The mod's agent.spawn hook gates the reviewer fan out on the review
packet manifest named by RECOGNITIO_PACKET_DIR. These tests execute
the real hooks module under node with stub arguments, the way the
host drives events through hooks, and prove the dispatch contract.
The hook denies an unverified packet, lets a verified packet
through, stays inert with no packet configured, and fails closed
through its .catch handler when the hook crashes. The host side
semantic for a crashed catch handler is pinned as a recorded
limit in the brief. The disabled mods degradation is proved by
running the shipped deterministic scripts with no mod loaded.
"""

import ast
import importlib.util
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOKS_DIR = ROOT / "hooks"
MODULE = HOOKS_DIR / "register.js"
BRIEF = ROOT / "docs" / "mod-build7.md"


def load_script(name):
    path = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location("mod_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_extractor():
    path = ROOT / ".agents" / "skills" / "recognitio" / "scripts" / "extract.py"
    spec = importlib.util.spec_from_file_location("mod_extract", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HARNESS = r"""
import { register } from "./register.js";

const mode = process.argv[2];
const manifestKind = process.env.MANIFEST_KIND || "verified";
const packetDir = process.env.RECOGNITIO_PACKET_DIR || "";

const manifests = {
  verified: JSON.stringify({ verified: true, files: [] }),
  unverified: JSON.stringify({ verified: false, files: [] }),
  truthy: JSON.stringify({ verified: "yes", files: [] }),
  duplicate: '{"verified": false, "verified": true}',
  duplicatefiles: '{"verified": true, "files": [], "files": []}',
  nesteddup: '{"verified": true, "inner": {"a": 1, "a": 2}}',
};

const $ = {
  env: {
    get: async (name) =>
      name === "RECOGNITIO_PACKET_DIR" ? packetDir || undefined : undefined,
  },
  fs: {
    read: async (path) => {
      if (typeof path !== "string" || path !== packetDir + "/manifest.json") {
        throw new Error("fs.read takes the manifest path as a string");
      }
      if (manifestKind === "unreadable") throw new Error("EACCES: no entry");
      if (manifestKind === "corrupt") return "not json{{{";
      return manifests[manifestKind] ?? manifests.verified;
    },
  },
};
const e = { agentId: "reviewer-1" };
const next = async (ev) => ({ passedThrough: true });

let hooked = null;
const fakeOn = (name, handler) => {
  hooked = { name, handler };
  return { catch: (h) => { hooked.catchHandler = h; } };
};
register(fakeOn, {});

const out = {};
if (mode === "describe") {
  out.event = hooked.name;
  out.hasCatch = typeof hooked.catchHandler === "function";
} else if (mode === "fire") {
  try {
    out.result = await hooked.handler($, e, next);
    out.crashed = false;
  } catch (err) {
    out.result = await hooked.catchHandler($, e, next);
    out.crashed = true;
  }
}
console.log(JSON.stringify(out));
"""


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
        raise AssertionError(
            "git %s failed: %s" % (" ".join(args), result.stderr)
        )
    return result.stdout.strip()


class ModDispatchTestCase(unittest.TestCase):
    """The dispatch contract, proved against the real hooks module."""

    def run_harness(self, mode, env=None, module_text=None):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "package.json").write_text('{"type": "module"}')
            (tmp / "register.js").write_text(
                module_text
                if module_text is not None
                else MODULE.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (tmp / "harness.mjs").write_text(HARNESS, encoding="utf-8")
            full_env = dict(os.environ)
            full_env.pop("RECOGNITIO_PACKET_DIR", None)
            full_env.update(env or {})
            result = subprocess.run(
                ["node", "harness.mjs", mode],
                cwd=str(tmp),
                env=full_env,
                capture_output=True,
                text=True,
                timeout=60,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def fire(self, env=None, module_text=None):
        return self.run_harness("fire", env, module_text)

    def test_the_hook_registers_agent_spawn_with_a_catch_handler(self):
        out = self.run_harness("describe")
        self.assertEqual(out["event"], "agent.spawn")
        self.assertTrue(out["hasCatch"])

    def test_a_verified_packet_lets_the_spawn_through(self):
        out = self.fire(
            {"RECOGNITIO_PACKET_DIR": "/packet", "MANIFEST_KIND": "verified"}
        )
        self.assertFalse(out["crashed"])
        self.assertEqual(out["result"], {"passedThrough": True})

    def test_an_unverified_packet_denies_the_spawn(self):
        out = self.fire(
            {"RECOGNITIO_PACKET_DIR": "/packet", "MANIFEST_KIND": "unverified"}
        )
        self.assertFalse(out["crashed"])
        self.assertIn("not verified", out["result"]["deny"])

    def test_a_truthy_verified_flag_denies_the_spawn(self):
        # The strictness regression. A flag that is merely
        # truthy is not the verified stamp, and a module that
        # let it through would pass every true and false test
        # while opening the gate.
        out = self.fire(
            {"RECOGNITIO_PACKET_DIR": "/packet", "MANIFEST_KIND": "truthy"}
        )
        self.assertFalse(out["crashed"])
        self.assertIn("not verified", out["result"]["deny"])

    def test_a_repeated_top_level_key_denies_the_spawn(self):
        # JSON.parse keeps the last value, so a manifest that
        # names verified false and then true would pass a plain
        # parse while the packet gate's strict reader refuses
        # the same bytes. The mod reads it as unverified.
        out = self.fire(
            {"RECOGNITIO_PACKET_DIR": "/packet", "MANIFEST_KIND": "duplicate"}
        )
        self.assertFalse(out["crashed"])
        self.assertIn("not verified", out["result"]["deny"])

    def test_a_repeated_non_stamp_key_denies_the_spawn(self):
        # The refusal is on the repeated top level key, not on
        # the verified name alone, so a repeated files key over
        # a verified stamp still reads as unverified.
        out = self.fire(
            {"RECOGNITIO_PACKET_DIR": "/packet",
             "MANIFEST_KIND": "duplicatefiles"}
        )
        self.assertFalse(out["crashed"])
        self.assertIn("not verified", out["result"]["deny"])

    def test_a_nested_repeated_key_denies_the_spawn(self):
        # The refusal reads every level, the way the packet
        # gate's strict reader does, so a key named twice
        # inside a nested object reads as unverified too.
        out = self.fire(
            {"RECOGNITIO_PACKET_DIR": "/packet",
             "MANIFEST_KIND": "nesteddup"}
        )
        self.assertFalse(out["crashed"])
        self.assertIn("not verified", out["result"]["deny"])

    def test_a_verified_packet_in_another_directory_passes(self):
        # The path comes from the configured directory, so a
        # module hardcoding the directory the other tests use
        # would read a path this harness refuses and fail here.
        out = self.fire(
            {"RECOGNITIO_PACKET_DIR": "/other-packet",
             "MANIFEST_KIND": "verified"}
        )
        self.assertFalse(out["crashed"])
        self.assertEqual(out["result"], {"passedThrough": True})

    def test_no_packet_configured_leaves_the_spawn_alone(self):
        out = self.fire({"MANIFEST_KIND": "verified"})
        self.assertFalse(out["crashed"])
        self.assertEqual(out["result"], {"passedThrough": True})

    def test_an_unreadable_manifest_fails_closed(self):
        out = self.fire(
            {"RECOGNITIO_PACKET_DIR": "/packet", "MANIFEST_KIND": "unreadable"}
        )
        self.assertTrue(out["crashed"])
        self.assertIn("denied rather than let through", out["result"]["deny"])

    def test_a_corrupt_manifest_fails_closed(self):
        out = self.fire(
            {"RECOGNITIO_PACKET_DIR": "/packet", "MANIFEST_KIND": "corrupt"}
        )
        self.assertTrue(out["crashed"])
        self.assertIn("denied rather than let through", out["result"]["deny"])

    def test_a_catch_handler_without_deny_breaks_fail_closed(self):
        # The revert that must fail. A catch handler that answers
        # anything but deny lets a crashed hook through.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'deny: "recognitio: the packet gate hook failed, '
            'so this review spawn is denied rather than let through"',
            'passed: true',
        )
        self.assertNotEqual(broken, text)
        out = self.fire(
            {"RECOGNITIO_PACKET_DIR": "/packet", "MANIFEST_KIND": "unreadable"},
            module_text=broken,
        )
        self.assertTrue(out["crashed"])
        self.assertNotIn("deny", out["result"])

    def test_the_second_layer_fail_open_is_a_recorded_limit(self):
        # The host skips the hook when the catch handler itself
        # throws or times out, and the spawn proceeds. That semantic
        # belongs to the host, so the deterministic proof is that
        # the shipped brief records it as a limit, pinned here and
        # by the gate script.
        mod = load_script("check_mod")
        text = re.sub(r"\s+", " ", BRIEF.read_text(encoding="utf-8"))
        self.assertIn(mod.LIMIT_SENTENCE, text)


class ModDegradationTestCase(unittest.TestCase):
    """Disabled mods degrade to the deterministic scripts."""

    def test_the_scripts_gate_with_no_mod_loaded(self):
        # No mod is loaded in this test at all. The packet scripts
        # must still gate the review, which is the degradation the
        # brief promises when mods are disabled or unavailable.
        extract = load_extractor()
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            repo = tmp / "repo"
            repo.mkdir()
            (repo / "main.py").write_text("print(1)\n", encoding="utf-8")
            git(repo, "init", "-q")
            git(repo, "config", "user.email", "t@t.t")
            git(repo, "config", "user.name", "t")
            git(repo, "add", "-A")
            git(repo, "commit", "-qm", "base")
            (repo / "main.py").write_text("print(2)\n", encoding="utf-8")
            git(repo, "add", "-A")
            git(repo, "commit", "-qm", "change")
            packet = tmp / "packet"
            code = extract.main(
                [
                    "--range",
                    "HEAD~1..HEAD",
                    "--repo",
                    str(repo),
                    "--out",
                    str(packet),
                ]
            )
            self.assertEqual(code, 0)
            good = subprocess.run(
                [os.environ.get("PYTHON", "python3"),
                 str(ROOT / "scripts" / "check_packet.py"),
                 "--repo", str(repo), str(packet)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(good.returncode, 0, good.stderr)
            manifest = json.loads(
                (packet / "manifest.json").read_text(encoding="utf-8")
            )
            manifest["verified"] = False
            (packet / "manifest.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            bad = subprocess.run(
                [os.environ.get("PYTHON", "python3"),
                 str(ROOT / "scripts" / "check_packet.py"),
                 "--repo", str(repo), str(packet)],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(bad.returncode, 0)


class ModContractTestCase(unittest.TestCase):
    """The structural contract, pinned by the gate script."""

    def setUp(self):
        self.mod = load_script("check_mod")

    def test_the_shipped_mod_holds_its_contract(self):
        self.assertEqual(self.mod.mod_problems(), [])

    def test_the_marketplace_entry_sentence_stands_in_the_brief(self):
        # The gate requires the brief to state the marketplace
        # entry, and this test holds the same sentence the way
        # the limit sentence is held, so a brief that drops the
        # entry fails here in words, not only in the gate.
        text = re.sub(r"\s+", " ", BRIEF.read_text(encoding="utf-8"))
        self.assertIn(
            "offers the mod as its own marketplace entry, named "
            "recognitio-mod",
            text,
        )

    def test_the_version_floor_sentence_stands_in_the_brief_and_the_readme(self):
        # The floor is the first build with mods, and it stands
        # stated in the brief and in the mod README. This test
        # holds the sentence in both files the way the limit
        # sentence is held, so a silent edit to either file
        # fails here in words, not only in the gate.
        floor = (
            "The mod needs Claude Code v2.1.287 or later, the "
            "first build with mods, and stands live tested "
            "on 2.1.314"
        )
        text = re.sub(r"\s+", " ", BRIEF.read_text(encoding="utf-8"))
        self.assertIn(floor, text)
        readme = re.sub(
            r"\s+", " ",
            (ROOT / "plugins" / "recognitio-mod" / "README.md")
            .read_text(encoding="utf-8"),
        )
        self.assertIn(floor, readme)

    def test_a_lowered_version_floor_fails_the_gate(self):
        # The gate plant for the floor pin. Lowering the floor
        # figure in the brief the gate reads must draw the
        # version floor problem, so a brief that restates the
        # floor at an earlier build fails the gate.
        text = re.sub(r"\s+", " ", BRIEF.read_text(encoding="utf-8"))
        planted = text.replace("v2.1.287", "v2.1.200")
        self.assertNotEqual(planted, text)
        with tempfile.TemporaryDirectory() as tmp:
            brief = Path(tmp) / "mod-build7.md"
            brief.write_text(planted, encoding="utf-8")
            self.mod.BRIEF = brief
            problems = self.mod.brief_problems()
        self.assertTrue(
            any("version floor" in p for p in problems), problems
        )

    # The seven named residuals of the contract, verbatim as
    # the brief states them, each with the label the gate
    # names it under. The list is the finality boundary of
    # the contract, so every sentence stands held here and
    # planted against the gate below.
    RESIDUAL_SENTENCES = (
        (
            "The gate reads a loop condition's shape, not its "
            "value, so a loop condition that is constant in "
            "fact but not in spelling, standing as a name the "
            "module bound to a literal, as a member of a "
            "literal, or against a bound no spelling can "
            "reach, reads as state under the census while the "
            "loop it heads never ends.",
            "the loop condition residual",
        ),
        (
            "A bare local call that never returns, standing "
            "before the registration, reads as the delegation "
            "the family tolerates while the registration it "
            "precedes never runs.",
            "the bare local call residual",
        ),
        (
            "A call that writes into an object, reached "
            "through a receiver whose identity the census "
            "does not judge, an alias holding the constructor "
            "or the constructor reached through the global "
            "object, reads as a call on a name the census "
            "leaves alone while the write lands the same way.",
            "the write call through an unjudged receiver "
            "residual",
        ),
        (
            "A write through a member standing as one clause "
            "of a comma sequence inside a returned value "
            "reads as the value it stands in, since the write "
            "readings judge statements and a sequence clause "
            "is a value position.",
            "the comma sequence write residual",
        ),
        (
            "A handler standing under an export alias, or "
            "under a differently cased export name beside the "
            "name the registration binds, reads as the export "
            "it stands under, since the readings judge the "
            "names the module's own text binds.",
            "the export alias residual",
        ),
        (
            "A call to eval reached through a member chain "
            "reads as a call on the receiver it stands "
            "behind.",
            "the member chain eval residual",
        ),
        (
            "A regex literal spelled inside a template "
            "literal's hole reads as the template it stands "
            "in, since the slash judgement stands over "
            "literal text and a hole is code.",
            "the template hole regex residual",
        ),
    )

    def test_the_named_residual_sentences_stand_in_the_brief(self):
        # The residual sentences stand held the way the limit
        # sentence is held, so a brief that drops or rewords
        # one of them fails here in words.
        text = re.sub(r"\s+", " ", BRIEF.read_text(encoding="utf-8"))
        for sentence, label in self.RESIDUAL_SENTENCES:
            self.assertIn(sentence, text, label)

    def test_a_deleted_named_residual_fails_the_gate(self):
        # The gate plant for the residual pins. Deleting any
        # one of the seven sentences from the brief the gate
        # reads must draw that residual's problem, so the
        # finality boundary cannot narrow in silence.
        text = re.sub(r"\s+", " ", BRIEF.read_text(encoding="utf-8"))
        for sentence, label in self.RESIDUAL_SENTENCES:
            planted = text.replace(sentence, "")
            self.assertNotEqual(planted, text, label)
            with tempfile.TemporaryDirectory() as tmp:
                brief = Path(tmp) / "mod-build7.md"
                brief.write_text(planted, encoding="utf-8")
                self.mod.BRIEF = brief
                problems = self.mod.brief_problems()
            self.assertTrue(
                any(label in p for p in problems),
                (label, problems),
            )

    def test_the_gate_problem_messages_carry_no_banned_mark(self):
        # The gate's problem messages follow the file's comma
        # form, and this census holds them to it. An abstract
        # syntax tree walk collects the string literals the
        # gate passes as problems, in append calls on a
        # problems list and in the returns of the problem
        # functions, and it also collects the literals the
        # gate delivers through the other shapes it uses, a
        # literal passed as the message itself to a helper
        # defined inside a problem function whose body
        # appends or returns its argument as a problem, and a
        # literal assigned to a variable a problem function
        # then appends or returns or hands to such a helper,
        # and refuses any carrying a colon, a semicolon, an
        # em dash or an en dash, so a leftover or a fresh
        # colon form fails the suite. The walk also reads the
        # parts a built message is made from, a literal
        # passed to a builder function whose return inserts
        # its argument into a template it returns, and each
        # module level constant that return inserts beside
        # the argument, and a literal standing as one
        # element of a container whose other element a
        # delivered format draws through a loop name, and a
        # literal fragment assigned to a name a delivered
        # format inserts, whether the name stands assigned
        # in the function itself or reaches its loop through
        # a collection the function builds by adding parts,
        # because each of those parts stands word for word
        # in a message the gate delivers. The census never
        # reads a docstring or any other string the gate
        # holds, and a literal the gate uses only to match,
        # to compare or to key a reading never stands in a
        # delivered message and stays outside the walk. The
        # walk proves itself live on the reader messages and
        # on a message or a part from each widened shape
        # first, so a walk that collected nothing or lost a
        # shape cannot pass in silence.
        source = (ROOT / "scripts" / "check_mod.py").read_text(
            encoding="utf-8")
        tree = ast.parse(source)
        messages = []

        def collect(node):
            for child in ast.walk(node):
                if isinstance(child, ast.Constant) and \
                        isinstance(child.value, str):
                    messages.append(child.value)

        def collect_literal(node):
            if isinstance(node, ast.Constant) and \
                    isinstance(node.value, str):
                messages.append(node.value)
            elif isinstance(node, ast.BinOp):
                collect_literal(node.left)
                collect_literal(node.right)
            elif isinstance(node, ast.JoinedStr):
                for value in node.values:
                    collect_literal(value)
            elif isinstance(node, (ast.Tuple, ast.List, ast.Set)):
                for element in node.elts:
                    collect_literal(element)
            elif isinstance(node, ast.IfExp):
                collect_literal(node.body)
                collect_literal(node.orelse)
            elif isinstance(node, ast.FormattedValue):
                collect_literal(node.value)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and \
                    isinstance(node.func, ast.Attribute) and \
                    node.func.attr == "append" and \
                    isinstance(node.func.value, ast.Name) and \
                    "problem" in node.func.value.id:
                for arg in node.args:
                    collect(arg)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and \
                    ("problem" in node.name
                     or node.name == "module_path"):
                for child in ast.walk(node):
                    if isinstance(child, ast.Return) and \
                            child.value is not None:
                        collect(child.value)
        for function in ast.walk(tree):
            if not isinstance(function, ast.FunctionDef) or \
                    ("problem" not in function.name
                     and function.name != "module_path"):
                continue
            helpers = {}
            for child in function.body:
                if not isinstance(child, ast.FunctionDef):
                    continue
                params = {arg.arg for arg in child.args.args}
                delivers = False
                for sub in ast.walk(child):
                    if isinstance(sub, ast.Call) and \
                            isinstance(sub.func, ast.Attribute) and \
                            sub.func.attr == "append" and \
                            isinstance(sub.func.value, ast.Name) and \
                            "problem" in sub.func.value.id and \
                            any(isinstance(arg, ast.Name)
                                and arg.id in params
                                for arg in sub.args):
                        delivers = True
                    if isinstance(sub, ast.Return) and \
                            isinstance(sub.value, ast.Name) and \
                            sub.value.id in params:
                        delivers = True
                if delivers:
                    helpers[child.name] = params
            for node in ast.walk(function):
                if isinstance(node, ast.Call) and \
                        isinstance(node.func, ast.Name) and \
                        node.func.id in helpers:
                    for arg in node.args:
                        collect_literal(arg)
            delivered = set()
            for node in ast.walk(function):
                if isinstance(node, ast.Call) and \
                        isinstance(node.func, ast.Attribute) and \
                        node.func.attr == "append" and \
                        isinstance(node.func.value, ast.Name) and \
                        "problem" in node.func.value.id:
                    for arg in node.args:
                        if isinstance(arg, ast.Name):
                            delivered.add(arg.id)
                if isinstance(node, ast.Return):
                    if isinstance(node.value, ast.Name):
                        delivered.add(node.value.id)
                    elif isinstance(node.value,
                                    (ast.List, ast.Tuple)):
                        for element in node.value.elts:
                            if isinstance(element, ast.Name):
                                delivered.add(element.id)
                if isinstance(node, ast.Call) and \
                        isinstance(node.func, ast.Name) and \
                        node.func.id in helpers:
                    for arg in node.args:
                        if isinstance(arg, ast.Name):
                            delivered.add(arg.id)
            for node in ast.walk(function):
                if isinstance(node, ast.Assign) and \
                        len(node.targets) == 1 and \
                        isinstance(node.targets[0], ast.Name) and \
                        node.targets[0].id in delivered:
                    collect_literal(node.value)
        module_constants = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and \
                    len(node.targets) == 1 and \
                    isinstance(node.targets[0], ast.Name):
                module_constants[node.targets[0].id] = node.value
        returned_builder_calls = set()
        for function in ast.walk(tree):
            if isinstance(function, ast.FunctionDef) and \
                    "problem" in function.name:
                for child in ast.walk(function):
                    if isinstance(child, ast.Return) and \
                            isinstance(child.value, ast.Call):
                        returned_builder_calls.add(id(child.value))
        builders = {}
        for function in ast.walk(tree):
            if not isinstance(function, ast.FunctionDef):
                continue
            params = [arg.arg for arg in function.args.args]
            for child in ast.walk(function):
                if not isinstance(child, ast.Return) or \
                        child.value is None:
                    continue
                interpolated = set()
                if isinstance(child.value, ast.BinOp) and \
                        isinstance(child.value.op, ast.Mod):
                    interpolated = {
                        name.id
                        for name in ast.walk(child.value.right)
                        if isinstance(name, ast.Name)}
                elif isinstance(child.value, ast.JoinedStr):
                    for value in child.value.values:
                        if isinstance(value, ast.FormattedValue):
                            interpolated.update(
                                name.id
                                for name in ast.walk(value.value)
                                if isinstance(name, ast.Name))
                inserted = [name for name in params
                            if name in interpolated]
                if inserted:
                    builders[function.name] = {
                        name: params.index(name)
                        for name in inserted}
                    for name in interpolated:
                        if name not in params and \
                                name in module_constants:
                            collect_literal(module_constants[name])
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and \
                    isinstance(node.func, ast.Name) and \
                    node.func.id in builders and \
                    id(node) not in returned_builder_calls:
                for position in builders[node.func.id].values():
                    if position < len(node.args):
                        collect_literal(node.args[position])
        for function in ast.walk(tree):
            if not isinstance(function, ast.FunctionDef) or \
                    ("problem" not in function.name
                     and function.name != "module_path"):
                continue
            helpers = {
                child.name for child in function.body
                if isinstance(child, ast.FunctionDef)}
            delivered = set()
            delivered_exprs = []
            for node in ast.walk(function):
                if isinstance(node, ast.Call) and \
                        isinstance(node.func, ast.Attribute) and \
                        node.func.attr == "append" and \
                        isinstance(node.func.value, ast.Name) and \
                        "problem" in node.func.value.id:
                    delivered_exprs.extend(node.args)
                    for arg in node.args:
                        if isinstance(arg, ast.Name):
                            delivered.add(arg.id)
                if isinstance(node, ast.Return) and \
                        node.value is not None:
                    delivered_exprs.append(node.value)
                    if isinstance(node.value, ast.Name):
                        delivered.add(node.value.id)
                    elif isinstance(node.value,
                                    (ast.List, ast.Tuple)):
                        for element in node.value.elts:
                            if isinstance(element, ast.Name):
                                delivered.add(element.id)
                if isinstance(node, ast.Call) and \
                        isinstance(node.func, ast.Name) and \
                        node.func.id in helpers:
                    delivered_exprs.extend(node.args)
                    for arg in node.args:
                        if isinstance(arg, ast.Name):
                            delivered.add(arg.id)
            for node in ast.walk(function):
                if isinstance(node, ast.Assign) and \
                        len(node.targets) == 1 and \
                        isinstance(node.targets[0], ast.Name) and \
                        node.targets[0].id in delivered:
                    delivered_exprs.append(node.value)
            interpolated = set()
            for expr in delivered_exprs:
                for sub in ast.walk(expr):
                    if isinstance(sub, ast.BinOp) and \
                            isinstance(sub.op, ast.Mod):
                        interpolated.update(
                            name.id for name in ast.walk(sub.right)
                            if isinstance(name, ast.Name))
                    elif isinstance(sub, ast.FormattedValue):
                        interpolated.update(
                            name.id for name in ast.walk(sub.value)
                            if isinstance(name, ast.Name))
            if not interpolated:
                continue
            for node in ast.walk(function):
                if isinstance(node, ast.Assign) and \
                        len(node.targets) == 1 and \
                        isinstance(node.targets[0], ast.Name) and \
                        node.targets[0].id in interpolated:
                    collect_literal(node.value)
            for node in ast.walk(function):
                if not isinstance(node, ast.For):
                    continue
                if isinstance(node.target, ast.Tuple):
                    targets = [
                        element.id
                        if isinstance(element, ast.Name) else None
                        for element in node.target.elts]
                elif isinstance(node.target, ast.Name):
                    targets = [node.target.id]
                else:
                    continue
                for index, target in enumerate(targets):
                    if target is None or \
                            target not in interpolated:
                        continue
                    if isinstance(node.iter, (ast.Tuple, ast.List)):
                        for inner in node.iter.elts:
                            if isinstance(inner,
                                           (ast.Tuple, ast.List)) and \
                                    index < len(inner.elts):
                                collect_literal(inner.elts[index])
                    collection = None
                    if isinstance(node.iter, ast.Name):
                        collection = node.iter.id
                    elif isinstance(node.iter, ast.Call) and \
                            isinstance(node.iter.func, ast.Name) and \
                            node.iter.func.id in (
                                "sorted", "list", "tuple", "set",
                                "reversed") and \
                            node.iter.args and \
                            isinstance(node.iter.args[0], ast.Name):
                        collection = node.iter.args[0].id
                    if collection is not None:
                        for sub in ast.walk(function):
                            if isinstance(sub, ast.Call) and \
                                    isinstance(sub.func,
                                               ast.Attribute) and \
                                    sub.func.attr in (
                                        "add", "append") and \
                                    isinstance(sub.func.value,
                                               ast.Name) and \
                                    sub.func.value.id == collection:
                                for arg in sub.args:
                                    collect_literal(arg)
        self.assertGreater(len(messages), 96)
        self.assertTrue(
            any(m.startswith("cannot read hooks/hooks.json")
                for m in messages),
            messages,
        )
        self.assertTrue(
            any(m.startswith(
                "the agent.spawn hook carries no .catch handler")
                for m in messages),
            messages,
        )
        self.assertTrue(
            any(m.startswith(
                "the hooks module calls $ itself through "
                "an optional call")
                for m in messages),
            messages,
        )
        self.assertTrue(
            any(m.startswith(
                "the hooks module reaches the mods API through "
                "a computed or optional")
                for m in messages),
            messages,
        )
        self.assertTrue(
            any(m.startswith(
                "the hooks module reaches the mods API through "
                "a receiver other than")
                for m in messages),
            messages,
        )
        self.assertTrue(
            any(m.startswith(
                "the hooks module binds $ itself to another name")
                for m in messages),
            messages,
        )
        self.assertTrue(
            any(m.startswith("a labelled")
                for m in messages),
            messages,
        )
        self.assertTrue(
            any(m.startswith(
                "a handler name %s standing alone")
                for m in messages),
            messages,
        )
        self.assertTrue(
            any(m.startswith("stands outside")
                for m in messages),
            messages,
        )
        self.assertTrue(
            any(m == "the version floor" for m in messages),
            messages,
        )
        self.assertTrue(
            any(m == "$.%s.%s" for m in messages),
            messages,
        )
        self.assertGreaterEqual(
            sum(1 for m in messages if m == "$."),
            2,
            messages,
        )
        for message in messages:
            for mark in (":", ";", "\u2014", "\u2013"):
                self.assertNotIn(mark, message)

    def test_no_gate_function_stands_defined_but_uncalled(self):
        # A helper nothing calls is dead code a reader must
        # carry, and this census refuses one. An abstract
        # syntax tree walk counts every call by name in the
        # gate against every function it defines, and the
        # only names allowed to stand uncalled are the two
        # the frameworks call, the strict JSON parser
        # callback, which the parser calls through the
        # object_pairs_hook argument and never by name in
        # this file, and the slash context constructor,
        # which runs when its class is instantiated and
        # never by its own name.
        source = (ROOT / "scripts" / "check_mod.py").read_text(
            encoding="utf-8")
        tree = ast.parse(source)
        defined = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef,
                                 ast.AsyncFunctionDef))
        ]
        calls = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = None
                if isinstance(func, ast.Name):
                    name = func.id
                elif isinstance(func, ast.Attribute):
                    name = func.attr
                if name is not None:
                    calls[name] = calls.get(name, 0) + 1
        allowlisted = {"reject", "__init__"}
        for name in allowlisted:
            self.assertIn(name, defined)
            self.assertEqual(calls.get(name, 0), 0, name)
        self.assertIn("_handler_outcome_items", defined)
        self.assertGreater(
            calls.get("_handler_outcome_items", 0), 0)
        uncalled = [
            name for name in defined
            if calls.get(name, 0) == 0 and name not in allowlisted
        ]
        self.assertEqual(uncalled, [])

    def test_the_module_exports_register_and_nothing_else(self):
        # The shipped module's named export surface is the
        # one name the contract pins, judged by the gate
        # reading on the stripped and decoded source the
        # gate itself reads.
        text = MODULE.read_text(encoding="utf-8")
        decoded = self.mod.decode_identifier_escapes(
            self.mod.strip_comments(text))
        self.assertEqual(self.mod.export_problems(decoded), [])

    def test_a_trailing_export_list_fails_the_export_pin(self):
        # Both trailing list shapes widen the surface, the
        # two handler list the module once shipped and a
        # single handler list, and each must draw the export
        # problem.
        text = MODULE.read_text(encoding="utf-8")
        for listing in (
            "export { gateSpawn, catchSpawnFailure };",
            "export { gateSpawn };",
        ):
            broken = text.rstrip("\n") + "\n\n" + listing + "\n"
            self.assertNotEqual(broken, text)
            problems = self.problems_for(broken)
            self.assertTrue(
                any("exports gateSpawn beside register" in p
                    for p in problems),
                problems,
            )

    def test_an_inline_export_on_a_handler_fails_the_export_pin(self):
        # The inline idiom widens the surface the same way,
        # on either handler, and each spelling must draw the
        # export problem.
        text = MODULE.read_text(encoding="utf-8")
        for plain, exported in (
            ("async function gateSpawn", "export async function gateSpawn"),
            ("function catchSpawnFailure", "export function catchSpawnFailure"),
        ):
            broken = text.replace(plain, exported)
            self.assertNotEqual(broken, text)
            problems = self.problems_for(broken)
            self.assertTrue(
                any("beside register" in p for p in problems),
                problems,
            )

    def test_the_brief_names_the_untraced_provenance_class(self):
        # The outside the promise statement in the brief names
        # the one class of values the walk does not trace, by
        # the productions that make them and both placements
        # they can stand in, so a brief that drops or narrows
        # the clause fails here in words.
        text = re.sub(r"\s+", " ", BRIEF.read_text(encoding="utf-8"))
        self.assertIn(
            "an options object the walk does not trace, one "
            "produced by a branch, a call, a constructor, a "
            "member walk, a container or an await step",
            text,
        )
        self.assertIn(
            "whether it stands at the call itself or behind "
            "a bound name",
            text,
        )
        changelog = re.sub(
            r"\s+", " ",
            (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))
        self.assertIn(
            "one produced by a branch, a call, a constructor, "
            "a member walk, a container or an await step, at "
            "the call itself or behind a bound name",
            changelog,
        )

    def test_a_hook_without_catch_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(".catch(catchSpawnFailure)", "")
        self.assertNotEqual(broken, text)
        with tempfile.TemporaryDirectory() as tmp:
            module = Path(tmp) / "register.js"
            module.write_text(broken, encoding="utf-8")
            problems = self.mod.module_problems(module)
        self.assertTrue(
            any("no .catch handler" in p for p in problems), problems
        )

    def test_a_model_call_in_the_hook_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.model.complete({ prompt: 'judge' });",
        )
        self.assertNotEqual(broken, text)
        with tempfile.TemporaryDirectory() as tmp:
            module = Path(tmp) / "register.js"
            module.write_text(broken, encoding="utf-8")
            problems = self.mod.module_problems(module)
        self.assertTrue(
            any("$.model.complete" in p for p in problems), problems
        )

    def test_an_options_object_read_fails_the_pin(self):
        # The live run regression. The host takes the path as the
        # read's one argument, so an options object read throws in
        # a session and no verified packet could ever pass.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read({ path: manifestPath });",
        )
        self.assertNotEqual(broken, text)
        with tempfile.TemporaryDirectory() as tmp:
            module = Path(tmp) / "register.js"
            module.write_text(broken, encoding="utf-8")
            problems = self.mod.module_problems(module)
        self.assertTrue(
            any("$.fs.read" in p and "options" in p for p in problems),
            problems,
        )

    def test_a_variable_env_name_fails_the_pin(self):
        # The live run regression. The host lists the variables a
        # module reads from the call site and refuses to load a
        # module that passes a variable instead of a literal.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            "const packetDir = await $.env.get(PACKET_ENV);",
        )
        self.assertNotEqual(broken, text)
        with tempfile.TemporaryDirectory() as tmp:
            module = Path(tmp) / "register.js"
            module.write_text(broken, encoding="utf-8")
            problems = self.mod.module_problems(module)
        self.assertTrue(
            any("not a string literal" in p for p in problems), problems
        )

    def problems_for(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            module = Path(tmp) / "register.js"
            module.write_text(text, encoding="utf-8")
            return self.mod.module_problems(module)

    def test_the_shipped_verified_comparison_passes_the_operator_pin(self):
        # Round 14 control. The shipped module compares the
        # verified flag against true with the strict operator.
        text = MODULE.read_text(encoding="utf-8")
        problems = self.problems_for(text)
        self.assertFalse(
            any("loose" in p or "strict" in p for p in problems),
            problems,
        )

    def test_a_loose_verified_comparison_fails_the_operator_pin(self):
        # Round 14. The one comparison the spawn gate turns
        # on, respelled with the loose operator, widened the
        # gate to any truthy value and passed every reading
        # the gate then carried.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "manifest.verified === true", "manifest.verified == true"
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("loose operator" in p for p in problems), problems
        )

    def test_a_reversed_loose_comparison_fails_the_operator_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "manifest.verified === true", "true == manifest.verified"
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("loose operator" in p for p in problems), problems
        )

    def test_an_aliased_verified_flag_fails_the_operator_pin(self):
        # The flag carried into a local name before the
        # comparison leaves the shipped strict form, so the
        # pin refuses it the same way.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "manifest.verified === true", "flag === true"
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("strict" in p and "verified" in p for p in problems),
            problems,
        )

    def test_a_numeric_disjunct_beside_the_verified_comparison_fails_the_operator_pin(self):
        # Round 18. A numeric stamp standing beside the
        # shipped comparison as a disjunct widens the gate
        # to that stamp while the strict spelling still
        # stands in the module, so the pin now reads the
        # comparison in the return that carries it.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "manifest.verified === true",
            "manifest.verified === true || manifest.verified === 1",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("strict" in p and "verified" in p for p in problems),
            problems,
        )

    def test_a_string_disjunct_beside_the_verified_comparison_fails_the_operator_pin(self):
        # Round 18. The string true stamp standing beside
        # the shipped comparison as a disjunct widens the
        # gate the same way, and the pin refuses it on the
        # same reading.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "manifest.verified === true",
            "manifest.verified === true || manifest.verified === \"true\"",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("strict" in p and "verified" in p for p in problems),
            problems,
        )

    def test_a_widened_return_before_a_clean_return_fails_the_operator_pin(self):
        # Round 18. A widened return carrying the
        # comparison draws the refusal even when a clean
        # return carrying it stands after it in the
        # deciding function, because the pin judges every
        # return that carries the comparison.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "  return (\n"
            "    manifest !== null &&\n"
            "    typeof manifest === \"object\" &&\n"
            "    manifest.verified === true\n"
            "  );",
            "  if (manifest !== null && typeof manifest === \"object\") {\n"
            "    return manifest.verified === true || manifest.verified === 1;\n"
            "  }\n"
            "  return manifest.verified === true;",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("strict" in p and "verified" in p for p in problems),
            problems,
        )

    def test_a_widened_return_after_a_clean_return_fails_the_operator_pin(self):
        # Round 18. The mirrored order draws the refusal
        # as well, a clean return carrying the comparison
        # standing first and the widened return standing
        # after it in the deciding function.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "  return (\n"
            "    manifest !== null &&\n"
            "    typeof manifest === \"object\" &&\n"
            "    manifest.verified === true\n"
            "  );",
            "  if (manifest === null || typeof manifest !== \"object\") {\n"
            "    return manifest.verified === true;\n"
            "  }\n"
            "  return manifest.verified === true || manifest.verified === 1;",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("strict" in p and "verified" in p for p in problems),
            problems,
        )

    def test_a_spaced_env_call_with_a_variable_fails_the_pin(self):
        # The red team regression. A space before the parenthesis
        # took the call outside the first pin's pattern entirely,
        # while the real host still refused the module at load.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const PACKET_ENV = "RECOGNITIO_PACKET_DIR";\n'
            "  const packetDir = await $.env.get (PACKET_ENV);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not a string literal" in p for p in problems), problems
        )

    def test_a_newline_before_an_env_variable_fails_the_pin(self):
        # Whitespace between the parenthesis and the argument
        # does not turn a variable into the literal the host lists.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const PACKET_ENV = "RECOGNITIO_PACKET_DIR";\n'
            "  const packetDir = await $.env.get(\n    PACKET_ENV);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not a string literal" in p for p in problems), problems
        )

    def test_bracket_access_to_an_env_variable_fails_the_gate(self):
        # A bracket member names the same member as the dot,
        # so the env pin itself judges the call, and the
        # variable name it passes is not the literal.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const PACKET_ENV = "RECOGNITIO_PACKET_DIR";\n'
            '  const packetDir = await $.env["get"](PACKET_ENV);',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not a string literal" in p for p in problems),
            problems,
        )

    def test_a_dot_spaced_env_variable_fails_the_gate(self):
        # A space before the member name still stands as the
        # env call, so the env pin itself judges it, and the
        # variable name it passes is not the literal.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const PACKET_ENV = "RECOGNITIO_PACKET_DIR";\n'
            "  const packetDir = await $.env .get(PACKET_ENV);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not a string literal" in p for p in problems),
            problems,
        )

    def test_a_concatenated_env_name_fails_the_pin(self):
        # The name at the call site is a join expression, which
        # the host refuses at load with the error the first
        # shipped module died of.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.env.get("RECOGNITIO_" + "PACKET_DIR");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("joins literals" in p for p in problems), problems
        )

    def test_a_wrong_env_literal_fails_the_pin(self):
        # A wrong literal passes the host and leaves the module
        # reading a variable nobody sets, inert and ungated.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.env.get("SOMETHING_ELSE");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not the exact name" in p for p in problems), problems
        )

    def test_an_empty_env_literal_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.env.get("");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not the exact name" in p for p in problems), problems
        )

    def test_a_comment_before_an_env_variable_fails_the_pin(self):
        # A comment between the parenthesis and the argument
        # does not make a variable into a literal.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const PACKET_ENV = "RECOGNITIO_PACKET_DIR";\n'
            "  const packetDir = await $.env.get(/*x*/PACKET_ENV);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not a string literal" in p for p in problems), problems
        )

    def test_an_env_reference_without_a_call_fails_the_pin(self):
        # Taking the method by reference leaves no call site
        # whose literal the host can list.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            "const getEnv = $.env.get;\n"
            '  const packetDir = await getEnv("RECOGNITIO_PACKET_DIR");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("without calling it" in p for p in problems), problems
        )

    def test_an_env_literal_in_a_comment_covers_no_variable_call(self):
        # The literal standing in a comment beside the real call
        # must not rescue a spaced variable call from the pin.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const PACKET_ENV = "RECOGNITIO_PACKET_DIR"; '
            '// $.env.get("RECOGNITIO_PACKET_DIR")\n'
            "  const packetDir = await $.env.get (PACKET_ENV);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not a string literal" in p for p in problems), problems
        )

    def test_a_spaced_options_object_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read ({ path: manifestPath });",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("$.fs.read" in p and "options object" in p
                for p in problems),
            problems,
        )

    def test_a_commented_options_object_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read(/*x*/{ path: manifestPath });",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("$.fs.read" in p and "options object" in p
                for p in problems),
            problems,
        )

    def test_a_parenthesised_options_object_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read(({ path: manifestPath }));",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("$.fs.read" in p and "options object" in p
                for p in problems),
            problems,
        )

    def test_a_newline_before_an_options_object_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read(\n  { path: manifestPath });",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("$.fs.read" in p and "options object" in p
                for p in problems),
            problems,
        )

    def test_bracket_access_to_an_options_object_read_fails_the_gate(self):
        # A bracket member names the same member as the dot,
        # so the file pin itself judges the call and refuses
        # the options object it carries.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            'const text = await $.fs["read"]({ path: manifestPath });',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("with an options object, where the host" in p
                for p in problems),
            problems,
        )

    def test_an_options_object_read_through_a_variable_fails_the_pin(self):
        # The object reaches the read behind a name, and the pin
        # follows the binding the module itself declares.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const opts = { path: manifestPath };\n"
            "  const text = await $.fs.read(opts);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("bound in the module to an options object"
                in p for p in problems),
            problems,
        )

    def test_a_read_with_a_second_argument_fails_the_pin(self):
        # The contract is the path as the read's one argument.
        # An options object riding as a second argument stands
        # outside that shape even though the first is a path.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            'const text = await $.fs.read(manifestPath, { encoding: "utf8" });',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("$.fs.read" in p and "one argument" in p
                for p in problems),
            problems,
        )

    def test_a_read_with_no_argument_fails_the_pin(self):
        # A read with no path at all is outside the one argument
        # shape the contract pins.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read();",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("$.fs.read" in p and "0 top" in p and "one argument" in p
                for p in problems),
            problems,
        )

    def test_an_env_get_with_a_second_argument_fails_the_pin(self):
        # The read side of the pair names its variable in the
        # literal standing alone. A second argument beside the
        # name is not that shape.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR", "x");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("second argument" in p for p in problems), problems
        )

    def test_an_interpolated_template_env_name_fails_the_pin(self):
        # The name is built at runtime, so no literal at the
        # call site names the variable the host must list.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            "const packetDir = await $.env.get(`RECOGNITIO_${\"PACKET\"}_DIR`);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("interpolated template" in p for p in problems),
            problems,
        )

    def test_a_comment_quoting_the_options_object_read_passes_the_pin(self):
        # The Minor 2 false positive. A comment quoting the
        # forbidden shape is not a call site, and the module's
        # own header prose may quote what it forbids.
        text = MODULE.read_text(encoding="utf-8")
        quoted = (
            "// $.fs.read({ path: x }) is the shape the host "
            "mishandles.\n" + text
        )
        self.assertEqual(self.problems_for(quoted), [])

    def test_a_comment_before_the_env_literal_passes_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        spaced = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.env.get(/*x*/"RECOGNITIO_PACKET_DIR");',
        )
        self.assertNotEqual(spaced, text)
        self.assertEqual(self.problems_for(spaced), [])

    def test_a_spaced_env_call_with_the_literal_passes_the_pin(self):
        # Whitespace before the parenthesis is not the defect.
        # The host refuses the variable, not the spacing.
        text = MODULE.read_text(encoding="utf-8")
        spaced = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.env.get ("RECOGNITIO_PACKET_DIR");',
        )
        self.assertNotEqual(spaced, text)
        self.assertEqual(self.problems_for(spaced), [])

    def test_a_quoting_comment_after_a_call_passes_the_pin(self):
        # A comment trailing a call on the same line is still a
        # comment. The stripping reads the two slashes as a
        # comment wherever they stand outside a string.
        text = MODULE.read_text(encoding="utf-8")
        quoted = text + "\nconst probe = f(1) // $.env.get(PACKET_ENV)\n"
        self.assertEqual(self.problems_for(quoted), [])

    def test_a_quoting_comment_after_a_string_passes_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        quoted = text + '\nconst note = "x" // $.fs.read({ path: x })\n'
        self.assertEqual(self.problems_for(quoted), [])

    def test_a_quoting_comment_after_a_brace_passes_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        quoted = text + "\nconst empty = {} // $.env.get(PACKET_ENV)\n"
        self.assertEqual(self.problems_for(quoted), [])

    def test_a_dollar_alias_env_call_fails_the_pin(self):
        # Binding $ itself to another name carries the call
        # past every pin that reads the $. spelling, and the
        # host refuses such a module at load.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const PACKET_ENV = "RECOGNITIO_PACKET_DIR";\n'
            "  const d = $;\n"
            "  const packetDir = await d.env.get(PACKET_ENV);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("binds $ itself" in p for p in problems), problems
        )

    def test_a_destructured_dollar_env_call_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const PACKET_ENV = "RECOGNITIO_PACKET_DIR";\n'
            "  const { env } = $;\n"
            "  const packetDir = await env.get(PACKET_ENV);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("binds $ itself" in p for p in problems), problems
        )

    def test_a_dollar_alias_options_object_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const d = $;\n"
            "  const text = await d.fs.read({ path: manifestPath });",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("binds $ itself" in p for p in problems), problems
        )

    def test_a_multi_declarator_options_object_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const dummy = 1, opts = { path: manifestPath };\n"
            "  const text = await $.fs.read(opts);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("bound in the module to an options object"
                in p for p in problems),
            problems,
        )

    def test_a_reassigned_options_object_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "let opts = manifestPath;\n"
            "  opts = { path: manifestPath };\n"
            "  const text = await $.fs.read(opts);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("bound in the module to an options object"
                in p for p in problems),
            problems,
        )

    def test_a_bare_assigned_options_object_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "async function packetIsVerified($, packetDir) {",
            "async function packetIsVerified($, packetDir) {\n"
            "  opts = { path: 1 };",
        ).replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read(opts);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("bound in the module to an options object"
                in p for p in problems),
            problems,
        )

    def test_an_object_assign_options_object_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const opts = Object.assign({}, { path: manifestPath });\n"
            "  const text = await $.fs.read(opts);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("bound in the module to an options object"
                in p for p in problems),
            problems,
        )

    def test_an_array_destructured_options_object_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const [opts] = [{ path: manifestPath }];\n"
            "  const text = await $.fs.read(opts);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("bound in the module to an options object"
                in p for p in problems),
            problems,
        )

    def test_a_spread_options_object_read_fails_the_pin(self):
        # The object stands in the call itself, handed over by
        # the array the spread opens.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read(...[{ path: manifestPath }]);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("$.fs.read" in p and "options object" in p
                for p in problems),
            problems,
        )

    def test_a_conditional_options_object_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read("
            "true ? { path: manifestPath } : manifestPath);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("$.fs.read" in p and "options object" in p
                for p in problems),
            problems,
        )

    def test_a_fallback_options_object_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read(null ?? { path: manifestPath });",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("$.fs.read" in p and "options object" in p
                for p in problems),
            problems,
        )

    def test_a_parameter_fed_options_object_read_fails_the_pin(self):
        # The object arrives through a parameter the module's
        # own call site feeds, which is the module binding it
        # by another route.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "async function packetIsVerified($, packetDir) {",
            "async function packetIsVerified($, packetDir, opts) {",
        ).replace(
            "packetIsVerified($, packetDir)",
            "packetIsVerified($, packetDir, { path: 1 })",
        ).replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read(opts);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("parameter its own call sites feed" in p
                for p in problems),
            problems,
        )

    def test_an_env_get_second_argument_behind_parens_fails_the_pin(self):
        # The parenthesis the pin reads through for the literal
        # does not hide a second argument standing after it.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.env.get(("RECOGNITIO_PACKET_DIR"), "x");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("second argument" in p for p in problems), problems
        )

    def test_a_name_reassigned_to_a_string_read_passes_the_pin(self):
        # The latest binding decides. A name that held an
        # object and then a string passes the string.
        text = MODULE.read_text(encoding="utf-8")
        spaced = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "let opts = { path: manifestPath };\n"
            "  opts = manifestPath;\n"
            "  const text = await $.fs.read(opts);",
        )
        self.assertNotEqual(spaced, text)
        self.assertEqual(self.problems_for(spaced), [])

    def test_a_binding_in_another_function_does_not_taint_a_read(self):
        # A binding inside a function that never shares its
        # scope with the read is not the read's binding.
        text = MODULE.read_text(encoding="utf-8")
        spaced = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read(opts);",
        ).replace(
            "export function register",
            "function dead() { const opts = { path: 1 }; return opts; }\n\n"
            "export function register",
        )
        self.assertNotEqual(spaced, text)
        self.assertEqual(self.problems_for(spaced), [])

    def test_a_shadowed_parameter_read_passes_the_pin(self):
        # A parameter shadows any outer binding of its name,
        # and a call site feeding it the path string feeds it
        # no object.
        text = MODULE.read_text(encoding="utf-8")
        spaced = text.replace(
            "async function packetIsVerified($, packetDir) {",
            "async function packetIsVerified($, packetDir, opts) {",
        ).replace(
            "packetIsVerified($, packetDir)",
            "packetIsVerified($, packetDir, manifestPath)",
        ).replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read(opts);",
        )
        self.assertNotEqual(spaced, text)
        self.assertEqual(self.problems_for(spaced), [])

    def test_a_parameter_with_an_object_default_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "async function packetIsVerified($, packetDir) {",
            "async function packetIsVerified($, packetDir, opts = { path: 1 }) {",
        ).replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read(opts);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("parameter whose default is an options object" in p
                for p in problems),
            problems,
        )

    def test_an_array_destructured_later_object_read_fails_the_pin(self):
        # The name's own place in the array decides, not the
        # first element.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            'const [label, opts] = ["x", { path: manifestPath }];\n'
            "  const text = await $.fs.read(opts);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("bound in the module to an options object"
                in p for p in problems),
            problems,
        )

    def test_an_array_destructured_string_sibling_read_passes_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        spaced = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const [opts, label] = [{ path: manifestPath }, manifestPath];\n"
            "  const text = await $.fs.read(label);",
        )
        self.assertNotEqual(spaced, text)
        self.assertEqual(self.problems_for(spaced), [])

    def test_an_object_destructured_options_object_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const { opts } = { opts: { path: manifestPath } };\n"
            "  const text = await $.fs.read(opts);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("bound in the module to an options object"
                in p for p in problems),
            problems,
        )

    def test_a_for_of_options_object_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "export function register",
            "function dead($) { for (const opts of [{ path: 1 }]) "
            "{ return $.fs.read(opts); } }\n\n"
            "export function register",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("bound in the module to an options object"
                in p for p in problems),
            problems,
        )

    def test_a_member_of_an_options_object_read_passes_the_pin(self):
        # The member is the path string itself, which is the
        # shape the contract pins, not the object.
        text = MODULE.read_text(encoding="utf-8")
        spaced = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const opts = { path: manifestPath };\n"
            "  const text = await $.fs.read(opts.path);",
        )
        self.assertNotEqual(spaced, text)
        self.assertEqual(self.problems_for(spaced), [])

    def test_an_object_literal_member_read_passes_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        spaced = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read({ path: manifestPath }.path);",
        )
        self.assertNotEqual(spaced, text)
        self.assertEqual(self.problems_for(spaced), [])

    def test_a_parenthesised_env_literal_passes_the_pin(self):
        # Parentheses around the literal change nothing the
        # host lists, and the pin reads through them.
        text = MODULE.read_text(encoding="utf-8")
        spaced = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.env.get(("RECOGNITIO_PACKET_DIR"));',
        )
        self.assertNotEqual(spaced, text)
        self.assertEqual(self.problems_for(spaced), [])

    def test_an_escaped_env_literal_fails_the_pin(self):
        # The pin wants the name spelled plainly, so the name
        # a reviewer reads is the name the host lists. An
        # escape spelling decodes to the name but does not
        # read as it.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DI\\u0052");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not the exact name" in p for p in problems), problems
        )

    def test_a_template_literal_env_name_passes_the_pin(self):
        # The host accepts a template literal carrying the exact
        # name with no interpolation and lists the variable.
        text = MODULE.read_text(encoding="utf-8")
        templated = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            "const packetDir = await $.env.get(`RECOGNITIO_PACKET_DIR`);",
        )
        self.assertNotEqual(templated, text)
        self.assertEqual(self.problems_for(templated), [])

    def test_a_dollar_spaced_wrong_env_name_fails_the_pin(self):
        # Whitespace between $ and its member still stands as
        # the env call, so the pin judges the name it carries.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $ .env.get("SOMETHING_ELSE");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not the exact name" in p for p in problems), problems
        )

    def test_a_newline_spaced_env_variable_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const PACKET_ENV = "RECOGNITIO_PACKET_DIR";\n'
            "  const packetDir = await $\n.env.get(PACKET_ENV);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not a string literal" in p for p in problems), problems
        )

    def test_a_dollar_spaced_fs_options_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $ .fs.read({ path: manifestPath });",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("with an options object, where the host" in p
                for p in problems),
            problems,
        )

    def test_a_renamed_hook_parameter_env_read_fails_the_pin(self):
        # The hooks take $ under whatever name the signature
        # gives it, and a renamed parameter still reaches the
        # mods API, so the pin refuses the foreign receiver.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "async function gateSpawn($, e, next) {",
            "async function gateSpawn(d, e, next) {",
        ).replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await d.env.get("SOMETHING_ELSE");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("receiver other than $" in p for p in problems),
            problems,
        )

    def test_a_pattern_hook_parameter_env_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "async function gateSpawn($, e, next) {",
            "async function gateSpawn({ env }, e, next) {",
        ).replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await env.get("SOMETHING_ELSE");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("receiver other than $" in p for p in problems),
            problems,
        )

    def test_a_nested_destructured_dollar_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "async function gateSpawn($, e, next) {",
            "async function gateSpawn($, e, next) {\n"
            "  const { env: { get } } = $;",
        ).replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await get("SOMETHING_ELSE");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("binds $ itself to another name" in p
                for p in problems),
            problems,
        )

    def test_a_parenthesised_options_binding_read_fails_the_pin(self):
        # The right hand side decides the binding, not its
        # first character, so parentheses around the object
        # literal still bind the object.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const opts = ({ path: manifestPath });\n"
            "  const text = await $.fs.read(opts);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("bound in the module to an options object" in p
                for p in problems),
            problems,
        )

    def test_a_branch_options_binding_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            'const opts = true ? { path: manifestPath } : "x";\n'
            "  const text = await $.fs.read(opts);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("bound in the module to an options object" in p
                for p in problems),
            problems,
        )

    def test_an_object_call_options_binding_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const opts = Object({ path: manifestPath });\n"
            "  const text = await $.fs.read(opts);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("bound in the module to an options object" in p
                for p in problems),
            problems,
        )

    def test_a_function_local_late_binding_read_passes_the_pin(self):
        # A binding inside the same function counts in its
        # written order, so a name bound after the read in
        # that function is not the object behind the read.
        # The read itself throws on the uninitialised name
        # in a session, which fails closed on its own.
        text = MODULE.read_text(encoding="utf-8")
        spaced = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read(opts);\n"
            "  const opts = { path: manifestPath };",
        )
        self.assertNotEqual(spaced, text)
        self.assertEqual(self.problems_for(spaced), [])

    def test_a_binding_after_the_read_still_fails_the_pin(self):
        # A module top level binding loads before any spawn
        # fires, so a binding written after the function that
        # reads through it still feeds the read.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read(opts);",
        ) + "\nconst opts = { path: manifestPath };\n"
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("bound in the module to an options object" in p
                for p in problems),
            problems,
        )

    def test_a_member_held_options_object_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const holder = {};\n"
            "  holder.opts = { path: manifestPath };\n"
            "  const text = await $.fs.read(holder.opts);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("options object held in a member" in p
                for p in problems),
            problems,
        )

    def test_an_array_indexed_options_object_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read([{ path: manifestPath }][0]);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("with an options object, where the host" in p
                for p in problems),
            problems,
        )

    def test_an_immediately_invoked_parameter_read_fails_the_pin(self):
        # The invocation at an unnamed function's own close
        # feeds its parameter, and the gate judges that feed
        # like any other call site.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await (async (opts) => $.fs.read(opts))"
            "({ path: manifestPath });",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("its own call sites feed an options object" in p
                for p in problems),
            problems,
        )

    def test_a_callback_parameter_read_fails_the_pin(self):
        # A callback's feeds are the host's, and no call site
        # in the module shows them, so the gate refuses the
        # read through its parameter outright.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            'const text = await on("agent.spawn", '
            "(opts) => $.fs.read(opts));",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("parameter of an unnamed function" in p
                for p in problems),
            problems,
        )

    def test_an_immediately_invoked_string_read_passes_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        spaced = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await (async (opts) => $.fs.read(opts))"
            "(manifestPath);",
        )
        self.assertNotEqual(spaced, text)
        self.assertEqual(self.problems_for(spaced), [])

    def test_a_nullish_assigned_options_object_read_fails_the_pin(self):
        # A logical assignment binds like any other, so the
        # object it carries reaches the read the same way.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "let opts;\n"
            "  opts ??= { path: manifestPath };\n"
            "  const text = await $.fs.read(opts);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("bound in the module to an options object" in p
                for p in problems),
            problems,
        )

    def test_a_fallback_assigned_options_object_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "let opts;\n"
            "  opts ||= { path: manifestPath };\n"
            "  const text = await $.fs.read(opts);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("bound in the module to an options object" in p
                for p in problems),
            problems,
        )

    def test_a_regex_default_parameter_keeps_the_read_index(self):
        # A comma inside a regex default is not a parameter
        # separator, so the read parameter keeps its own
        # index and the object fed at that index is judged.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "function readIt(sep = /,/, opts) { "
            "return $.fs.read(opts); }\n"
            "  const text = await readIt(undefined, "
            "{ path: manifestPath });",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("its own call sites feed an options object" in p
                for p in problems),
            problems,
        )

    def test_a_regex_default_parameter_string_feed_passes_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        spaced = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "function readIt(sep = /,/, opts) { "
            "return $.fs.read(opts); }\n"
            "  const text = await readIt({ path: manifestPath }, "
            "manifestPath);",
        )
        self.assertNotEqual(spaced, text)
        self.assertEqual(self.problems_for(spaced), [])

    def test_a_bracket_receiver_env_read_fails_the_pin(self):
        # The fixture isolates the receiver spelling. The
        # parameter keeps its shipped name, the literal is
        # the exact pinned name and the surrounding code is
        # the shipped line, so only the bracket spelling of
        # the receiver can fail the pin, and the host refuses
        # that spelling at load.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $["env"].get("RECOGNITIO_PACKET_DIR");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )
        self.assertFalse(
            any("not the exact name" in p for p in problems),
            problems,
        )
        self.assertFalse(
            any("receiver other than $" in p for p in problems),
            problems,
        )

    def test_an_optional_chain_env_read_fails_the_pin(self):
        # The fixture isolates the receiver spelling the
        # same way. The literal is the exact pinned name, so
        # only the optional chain step on $.env can fail the
        # pin, where an earlier fixture carried a wrong
        # literal and failed on the name instead.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.env?.get("RECOGNITIO_PACKET_DIR");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )
        self.assertFalse(
            any("not the exact name" in p for p in problems),
            problems,
        )

    def test_a_full_bracket_receiver_env_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $["env"]["get"]'
            '("RECOGNITIO_PACKET_DIR");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_a_bracket_method_env_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.env["get"]'
            '("RECOGNITIO_PACKET_DIR");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_a_single_quoted_bracket_env_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            "const packetDir = await $['env'].get"
            "(\"RECOGNITIO_PACKET_DIR\");",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_a_backtick_bracket_env_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.env[`get`]'
            '("RECOGNITIO_PACKET_DIR");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_a_dynamic_bracket_env_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $["e" + "nv"].get'
            '("RECOGNITIO_PACKET_DIR");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_optional_head_env_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $?.env.get'
            '("RECOGNITIO_PACKET_DIR");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_optional_both_env_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $?.env?.get'
            '("RECOGNITIO_PACKET_DIR");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_optional_bracket_env_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $?.["env"].get'
            '("RECOGNITIO_PACKET_DIR");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_optional_call_env_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.env.get?.'
            '("RECOGNITIO_PACKET_DIR");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_optional_chain_env_set_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.env?.set'
            '("RECOGNITIO_PACKET_DIR", "x");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_a_bracket_receiver_fs_read_fails_the_pin(self):
        # The file read fixture isolates the receiver
        # spelling the same way, with the shipped path
        # argument standing in plain surrounding code.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            'const text = await $["fs"].read(manifestPath);',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )
        self.assertFalse(
            any("options object" in p for p in problems),
            problems,
        )

    def test_a_full_bracket_receiver_fs_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            'const text = await $["fs"]["read"](manifestPath);',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_a_bracket_method_fs_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            'const text = await $.fs["read"](manifestPath);',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_optional_chain_fs_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs?.read(manifestPath);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )
        self.assertFalse(
            any("options object" in p for p in problems),
            problems,
        )

    def test_an_optional_head_fs_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $?.fs.read(manifestPath);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_a_backtick_bracket_fs_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs[`read`](manifestPath);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_optional_call_fs_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read?.(manifestPath);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_head_env_read_with_a_wrong_literal_fails(self):
        # The escape door regression. The host decodes the
        # escaped noun to env, so the env pin judges the
        # call, and the wrong literal fails it the way the
        # plain spelling does.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.\\u0065nv.get("SOMETHING_ELSE");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not the exact name" in p for p in problems), problems
        )

    def test_an_escaped_head_env_read_with_a_variable_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            "const packetDir = await $.\\u0065nv.get(PACKET_ENV);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not a string literal" in p for p in problems), problems
        )

    def test_an_escaped_head_env_read_with_a_joined_name_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.\\u0065nv.get('
            '"RECOGNITIO_" + "PACKET_DIR");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("joins literals" in p for p in problems), problems
        )

    def test_a_braced_escaped_head_env_read_with_a_wrong_literal_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.\\u{65}nv.get("SOMETHING_ELSE");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not the exact name" in p for p in problems), problems
        )

    def test_an_escaped_head_env_read_with_a_bracket_method_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.\\u0065nv["get"]'
            '("RECOGNITIO_PACKET_DIR");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_head_env_read_with_an_optional_method_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.\\u0065nv?.get'
            '("RECOGNITIO_PACKET_DIR");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_head_fs_read_with_an_options_object_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.\\u0066s.read({ path: manifestPath });",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("options object" in p for p in problems), problems
        )

    def test_a_braced_escaped_fs_read_with_an_options_object_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.\\u{66}s.read({ path: manifestPath });",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("options object" in p for p in problems), problems
        )

    def test_an_escaped_head_fs_read_with_a_bound_object_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const opts = { path: manifestPath };\n"
            "  const text = await $.\\u0066s.read(opts);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("bound in the module to an options object" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_head_fs_read_with_a_second_argument_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            'const text = await $.\\u0066s.read(manifestPath, "x");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("2 top level arguments" in p for p in problems),
            problems,
        )

    def test_an_escaped_head_env_read_with_the_exact_literal_passes(self):
        # The host decodes the escape and accepts the plain
        # call, so the pin passes the correct spelling too
        # and judges it as env rather than missing it.
        text = MODULE.read_text(encoding="utf-8")
        variant = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.\\u0065nv.get'
            '("RECOGNITIO_PACKET_DIR");',
        )
        self.assertNotEqual(variant, text)
        self.assertEqual(self.problems_for(variant), [])

    def test_a_braced_escaped_head_fs_read_with_the_path_passes(self):
        text = MODULE.read_text(encoding="utf-8")
        variant = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.\\u{66}s.read(manifestPath);",
        )
        self.assertNotEqual(variant, text)
        self.assertEqual(self.problems_for(variant), [])

    def test_a_partial_escape_in_the_env_noun_passes_the_pin(self):
        # A partial escape flags under a truncated name on
        # the old gate, while the host decodes it and
        # accepts the call, so the fixed pin passes it.
        text = MODULE.read_text(encoding="utf-8")
        variant = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.e\\u006ev.get'
            '("RECOGNITIO_PACKET_DIR");',
        )
        self.assertNotEqual(variant, text)
        self.assertEqual(self.problems_for(variant), [])

    def test_a_partial_escape_in_the_fs_method_passes_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        variant = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.r\\u0065ad(manifestPath);",
        )
        self.assertNotEqual(variant, text)
        self.assertEqual(self.problems_for(variant), [])

    def test_a_full_escape_of_the_env_method_passes_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        variant = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.env.\\u0067et'
            '("RECOGNITIO_PACKET_DIR");',
        )
        self.assertNotEqual(variant, text)
        self.assertEqual(self.problems_for(variant), [])

    def test_a_full_escape_of_the_fs_method_passes_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        variant = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.\\u0072ead(manifestPath);",
        )
        self.assertNotEqual(variant, text)
        self.assertEqual(self.problems_for(variant), [])

    def test_an_optional_call_on_dollar_itself_fails_the_pin(self):
        # The optional call on $ regression. Normalisation
        # rewrote the optional step to a dot, so the value
        # scan read a called $ as a chain head and passed
        # it, while the host refuses a called $ at load.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $?.("RECOGNITIO_PACKET_DIR");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("calls $ itself through an optional call" in p
                for p in problems),
            problems,
        )

    def test_an_optional_call_on_dollar_for_the_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $?.(manifestPath);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("calls $ itself through an optional call" in p
                for p in problems),
            problems,
        )

    def test_a_spaced_optional_call_on_dollar_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $?. ("RECOGNITIO_PACKET_DIR");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("calls $ itself through an optional call" in p
                for p in problems),
            problems,
        )

    def test_a_spaced_head_optional_call_on_dollar_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $ ?.("RECOGNITIO_PACKET_DIR");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("calls $ itself through an optional call" in p
                for p in problems),
            problems,
        )

    def test_a_commented_optional_call_on_dollar_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $/*c*/?./*c*/'
            '("RECOGNITIO_PACKET_DIR");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("calls $ itself through an optional call" in p
                for p in problems),
            problems,
        )

    def test_a_newline_optional_call_on_dollar_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $?.\n(manifestPath);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("calls $ itself through an optional call" in p
                for p in problems),
            problems,
        )

    def test_a_comment_quoting_receiver_spellings_passes_the_pin(self):
        # A comment quoting a refused receiver spelling is
        # not a call site, because the receiver scan reads
        # the comment stripped source like the other pins.
        text = MODULE.read_text(encoding="utf-8")
        quoted = text + (
            '\n// await $.env?.get("RECOGNITIO_PACKET_DIR")'
            ' and await $["fs"]["read"](manifestPath)\n'
        )
        self.assertNotEqual(quoted, text)
        self.assertEqual(self.problems_for(quoted), [])

    def test_a_member_dollar_receiver_fails_the_pin(self):
        # A $ reached as another object's member is not the
        # mods object, even when the call it carries names
        # the exact literal.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await e.$.env.get('
            '"RECOGNITIO_PACKET_DIR");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("receiver other than $" in p for p in problems),
            problems,
        )

    def test_a_function_expression_parameter_read_fails_the_pin(self):
        # A function expression binds its parameter like any
        # other function spelling, and a call through the
        # name it is assigned to feeds it.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const readIt = function(opts) { "
            "return $.fs.read(opts); };\n"
            "  const text = await readIt({ path: manifestPath });",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("its own call sites feed an options object" in p
                for p in problems),
            problems,
        )

    def test_a_function_expression_string_feed_passes_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        spaced = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await (function(opts) { "
            "return $.fs.read(opts); })(manifestPath);",
        )
        self.assertNotEqual(spaced, text)
        self.assertEqual(self.problems_for(spaced), [])

    def test_a_wrapped_dollar_argument_fails_the_pin(self):
        # Only the bare $ passed to a parameter named $ is
        # the pinned idiom. A $ wrapped in a container is a
        # value use the host refuses.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "await packetIsVerified($, packetDir)",
            "await packetIsVerified({ wrap: $ }, packetDir)",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("binds $ itself to another name" in p
                for p in problems),
            problems,
        )

    def test_a_spread_dollar_argument_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "await packetIsVerified($, packetDir)",
            "await packetIsVerified(...$, packetDir)",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("binds $ itself to another name" in p
                for p in problems),
            problems,
        )

    def test_a_template_interpolated_dollar_fails_the_pin(self):
        # Code inside a template interpolation runs as code,
        # so a $ standing there as a value is judged like
        # any other value use.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "async function gateSpawn($, e, next) {",
            "async function gateSpawn($, e, next) {\n"
            "  const label = `${$}`;",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("binds $ itself to another name" in p
                for p in problems),
            problems,
        )

    def test_a_catch_binding_named_dollar_passes_the_pin(self):
        # A catch clause binding named $ binds the error
        # under that name, a parameter in everything but
        # spelling, and no value use of the mods object.
        text = MODULE.read_text(encoding="utf-8")
        spaced = text.replace(
            "async function gateSpawn($, e, next) {",
            "async function gateSpawn($, e, next) {\n"
            "  try { await next(); } catch ($) { }",
        )
        self.assertNotEqual(spaced, text)
        self.assertEqual(self.problems_for(spaced), [])

    def test_a_paren_free_arrow_dollar_parameter_passes_the_pin(self):
        # A parenthesis free arrow binds its one parameter
        # with no list, and a parameter named $ in that
        # spelling is the same binding as in any other.
        text = MODULE.read_text(encoding="utf-8")
        spaced = text.replace(
            "async function gateSpawn($, e, next) {",
            "const helper = $ => $.env.get("
            '"RECOGNITIO_PACKET_DIR");\n\n'
            "async function gateSpawn($, e, next) {",
        )
        self.assertNotEqual(spaced, text)
        self.assertEqual(self.problems_for(spaced), [])

    def test_a_paren_free_arrow_parameter_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const readIt = opts => $.fs.read(opts);\n"
            "  const text = await readIt({ path: manifestPath });",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("its own call sites feed an options object" in p
                for p in problems),
            problems,
        )

    def test_a_helper_return_options_object_read_fails_the_pin(self):
        # A value produced by a module local helper carries
        # the provenance of the helper's returns, so an
        # options object returned there reaches the read
        # through the binding all the same.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "function makeOpts() { "
            "return { path: manifestPath }; }\n"
            "  const opts = makeOpts();\n"
            "  const text = await $.fs.read(opts);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("bound in the module to an options object" in p
                for p in problems),
            problems,
        )

    def test_a_member_fed_options_object_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const holder = { opts: { path: manifestPath } };\n"
            "  const text = await $.fs.read(holder.opts);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("options object held in a member" in p
                for p in problems),
            problems,
        )

    def test_a_call_result_member_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "function getHolder() { "
            "return { opts: { path: manifestPath } }; }\n"
            "  const text = await $.fs.read(getHolder().opts);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("options object held in a member" in p
                for p in problems),
            problems,
        )

    def test_a_getter_member_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const holder = { get opts() { "
            "return { path: manifestPath }; } };\n"
            "  const text = await $.fs.read(holder.opts);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("options object held in a member" in p
                for p in problems),
            problems,
        )

    def test_an_object_assign_string_target_read_fails_the_pin(self):
        # Object.assign returns an object whatever its
        # target holds, so the binding stands as one even
        # when the target names the path string.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const opts = Object.assign(manifestPath, "
            "{ path: manifestPath });\n"
            "  const text = await $.fs.read(opts);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("bound in the module to an options object" in p
                for p in problems),
            problems,
        )

    def test_a_for_of_destructured_options_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "let text;\n"
            "  for (const { opts } of "
            "[{ opts: { path: manifestPath } }]) {\n"
            "    text = await $.fs.read(opts);\n"
            "  }",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("bound in the module to an options object" in p
                for p in problems),
            problems,
        )

    def test_a_variable_index_member_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const holder = [{ path: manifestPath }];\n"
            "  const index = 0;\n"
            "  const text = await $.fs.read(holder[index]);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("options object held in a member" in p
                for p in problems),
            problems,
        )

    def test_an_at_index_member_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const holder = [{ path: manifestPath }];\n"
            "  const text = await $.fs.read(holder.at(0));",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("options object held in a member" in p
                for p in problems),
            problems,
        )

    def test_a_destructured_noun_read_fails_the_pin(self):
        # A noun of $ destructured into a binding hands the
        # method to calls no pin can read, where a chain
        # called in place stands at a judged call site. The
        # host refuses a noun of $ bound, passed or read.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const { read } = $.fs;\n"
            "  const text = await read({ path: manifestPath });",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("binds a noun of $ to another name" in p
                for p in problems),
            problems,
        )

    def test_a_member_call_dollar_argument_fails_the_pin(self):
        # A $ handed to a member call goes to a function the
        # module does not define at that receiver, whatever
        # the member is named, so no parameter named $ in
        # the module excuses it.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "await packetIsVerified($, packetDir)",
            "await other.packetIsVerified($, packetDir)",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("binds $ itself to another name" in p
                for p in problems),
            problems,
        )

    def test_a_helper_return_string_read_passes_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        spaced = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "function makePath() { return manifestPath; }\n"
            "  const opts = makePath();\n"
            "  const text = await $.fs.read(opts);",
        )
        self.assertNotEqual(spaced, text)
        self.assertEqual(self.problems_for(spaced), [])

    def test_a_method_fed_options_object_read_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const helper = { readIt(opts) { "
            "return $.fs.read(opts); } };\n"
            "  const text = await helper.readIt("
            "{ path: manifestPath });",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("its own call sites feed an options object" in p
                for p in problems),
            problems,
        )

    def test_an_env_trailing_comma_passes_the_pin(self):
        # A trailing comma adds no argument, so the exact
        # literal still stands alone, as the host reads it.
        text = MODULE.read_text(encoding="utf-8")
        spaced = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR",);',
        )
        self.assertNotEqual(spaced, text)
        self.assertEqual(self.problems_for(spaced), [])

    def test_an_env_parenthesised_trailing_comma_passes_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        spaced = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.env.get('
            '("RECOGNITIO_PACKET_DIR"),);',
        )
        self.assertNotEqual(spaced, text)
        self.assertEqual(self.problems_for(spaced), [])

    def test_an_fs_trailing_comma_passes_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        spaced = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read(manifestPath,);",
        )
        self.assertNotEqual(spaced, text)
        self.assertEqual(self.problems_for(spaced), [])

    def test_a_bracket_member_of_an_object_literal_passes_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        spaced = text.replace(
            "const text = await $.fs.read(manifestPath);",
            'const text = await $.fs.read('
            '{ path: manifestPath }["path"]);',
        )
        self.assertNotEqual(spaced, text)
        self.assertEqual(self.problems_for(spaced), [])

    def test_an_optional_chain_member_read_passes_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        spaced = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const opts = { path: manifestPath };\n"
            "  const text = await $.fs.read(opts?.path);",
        )
        self.assertNotEqual(spaced, text)
        self.assertEqual(self.problems_for(spaced), [])

    def test_a_computed_member_argument_read_passes_the_pin(self):
        # A bracket step on the argument object is not a
        # computed access on the $ receiver, so the receiver
        # refusal does not reach it and the member read of
        # the path passes as it did before.
        text = MODULE.read_text(encoding="utf-8")
        spaced = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const opts = { path: manifestPath };\n"
            "  const text = await $.fs.read(opts[\"path\"]);",
        )
        self.assertNotEqual(spaced, text)
        self.assertEqual(self.problems_for(spaced), [])

    def test_a_destructured_string_shadow_read_passes_the_pin(self):
        # A destructured declaration of the same name inside
        # the reading function shadows the top level object
        # binding, so the read takes the string.
        text = MODULE.read_text(encoding="utf-8")
        spaced = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const { opts } = { opts: manifestPath };\n"
            "  const text = await $.fs.read(opts);",
        ) + "\nconst opts = { path: manifestPath };\n"
        self.assertNotEqual(spaced, text)
        self.assertEqual(self.problems_for(spaced), [])

    def make_copy_layout(self, tmp):
        root = Path(tmp) / "root"
        hooks = root / "hooks"
        plugin_dir = root / "plugins" / "recognitio-mod"
        copy_hooks = plugin_dir / "hooks"
        hooks.mkdir(parents=True)
        copy_hooks.mkdir(parents=True)
        for name in ("hooks.json", "register.js", "register.test.ts"):
            text = (HOOKS_DIR / name).read_text(encoding="utf-8")
            (hooks / name).write_text(text, encoding="utf-8")
            (copy_hooks / name).write_text(text, encoding="utf-8")
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        (root / "LICENSE").write_text(license_text, encoding="utf-8")
        (plugin_dir / "LICENSE").write_text(
            license_text, encoding="utf-8")
        self.mod.ROOT = root
        self.mod.MOD_PLUGIN_DIR = plugin_dir
        self.mod.MOD_PLUGIN_HOOKS = copy_hooks
        return copy_hooks

    def test_the_marketplace_copy_holds_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.make_copy_layout(tmp)
            self.assertEqual(self.mod.plugin_copy_problems(), [])

    def test_a_drifted_marketplace_copy_fails_the_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy_hooks = self.make_copy_layout(tmp)
            target = copy_hooks / "register.js"
            target.write_text(
                target.read_text(encoding="utf-8") + "\n// drift\n",
                encoding="utf-8",
            )
            problems = self.mod.plugin_copy_problems()
        self.assertTrue(
            any("drifted" in p for p in problems), problems
        )

    def test_a_missing_marketplace_copy_fails_the_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy_hooks = self.make_copy_layout(tmp)
            (copy_hooks / "hooks.json").unlink()
            problems = self.mod.plugin_copy_problems()
        self.assertTrue(
            any("does not mirror" in p for p in problems), problems
        )

    def test_an_extra_file_in_the_copy_fails_the_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy_hooks = self.make_copy_layout(tmp)
            (copy_hooks / "extra.js").write_text(
                "// uncertified\n", encoding="utf-8")
            problems = self.mod.plugin_copy_problems()
        self.assertTrue(
            any("does not mirror" in p for p in problems), problems
        )

    def test_an_uncopied_hooks_file_fails_the_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy_hooks = self.make_copy_layout(tmp)
            originals = copy_hooks.parent.parent.parent / "hooks"
            (originals / "second.js").write_text(
                "// new module\n", encoding="utf-8")
            problems = self.mod.plugin_copy_problems()
        self.assertTrue(
            any("does not mirror" in p for p in problems), problems
        )

    def test_a_missing_mod_license_fails_the_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy_hooks = self.make_copy_layout(tmp)
            (copy_hooks.parent / "LICENSE").unlink()
            problems = self.mod.plugin_copy_problems()
        self.assertTrue(
            any("missing" in p for p in problems), problems
        )

    def test_a_drifted_mod_license_fails_the_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy_hooks = self.make_copy_layout(tmp)
            target = copy_hooks.parent / "LICENSE"
            target.write_text(
                target.read_text(encoding="utf-8") + "\nExtra.\n",
                encoding="utf-8",
            )
            problems = self.mod.plugin_copy_problems()
        self.assertTrue(
            any("different terms" in p for p in problems), problems
        )

    def test_the_struck_onfailure_language_fails_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "return {",
            "const onFailure = 'block'; return {",
            1,
        )
        self.assertNotEqual(broken, text)
        with tempfile.TemporaryDirectory() as tmp:
            module = Path(tmp) / "register.js"
            module.write_text(broken, encoding="utf-8")
            problems = self.mod.module_problems(module)
        self.assertTrue(
            any("onFailure" in p for p in problems), problems
        )

    # Lane 4, the shared slash judgement. A slash after a
    # postfix ++ or -- is division, and a regex literal after
    # a keyword that expects an expression is a regex, so the
    # walkers the pins share read both positions as the host
    # does and the call sites behind them stand judged.

    def test_an_escaped_env_variable_behind_a_postfix_division_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'let n = 0;\n'
            '  const packetDir = await (n++ / $.\\u0065nv.get(PACKET_ENV) / 1);',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not a string literal" in p for p in problems), problems
        )

    def test_an_escaped_env_wrong_literal_behind_a_postfix_division_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'let n = 0;\n'
            '  const packetDir = await (n++ / $.\\u0065nv.get("SOMETHING_ELSE") / 1);',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not the exact name" in p for p in problems), problems
        )

    def test_an_escaped_env_bracket_method_behind_a_postfix_division_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'let n = 0;\n'
            '  const packetDir = await (n++ / $.\\u0065nv["get"]'
            '("RECOGNITIO_PACKET_DIR") / 1);',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_fs_bracket_method_behind_a_postfix_division_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            'let n = 0;\n'
            '  const text = await (n++ / $.\\u0066s["read"](manifestPath) / 1);',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_fs_optional_method_behind_a_postfix_decrement_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            'let n = 0;\n'
            '  const text = await (n-- / $.\\u0066s?.read(manifestPath) / 1);',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_fs_second_argument_behind_a_postfix_decrement_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            'let n = 0;\n'
            '  const text = await (n-- / $.\\u0066s.read(manifestPath, "x") / 1);',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("2 top level arguments" in p for p in problems),
            problems,
        )

    def test_an_escaped_fs_options_object_behind_a_postfix_division_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            'let n = 0;\n'
            '  const text = await (n++ / $.\\u0066s.read({ path: manifestPath }) / 1);',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("options object" in p for p in problems), problems
        )

    def test_a_plain_optional_dollar_call_behind_a_postfix_division_fails(self):
        # The written source dollar judgement shares the span
        # walk, so the plain spelling stood behind the same
        # door as the escaped one.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'let n = 0;\n'
            '  const packetDir = await (n++ / $?.("RECOGNITIO_PACKET_DIR") / 1);',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("calls $ itself through an optional call" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_optional_dollar_call_behind_a_postfix_division_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'let n = 0;\n'
            '  const packetDir = await (n++ / \\u0024?.'
            '("RECOGNITIO_PACKET_DIR") / 1);',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("calls $ itself through an optional call" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_env_correct_literal_behind_a_postfix_division_passes(self):
        # The judged position cuts both ways, so the correct
        # escaped call in the same division chain passes as
        # the host accepts it.
        text = MODULE.read_text(encoding="utf-8")
        variant = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'let n = 0;\n'
            '  const packetDir = await (n++ / $.\\u0065nv.get'
            '("RECOGNITIO_PACKET_DIR") / 1);',
        )
        self.assertNotEqual(variant, text)
        self.assertEqual(self.problems_for(variant), [])

    def test_a_plain_env_correct_literal_behind_a_postfix_division_passes(self):
        text = MODULE.read_text(encoding="utf-8")
        variant = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'let n = 0;\n'
            '  const packetDir = await (n++ / $.env.get'
            '("RECOGNITIO_PACKET_DIR") / 1);',
        )
        self.assertNotEqual(variant, text)
        self.assertEqual(self.problems_for(variant), [])

    def test_division_in_ordinary_arithmetic_passes_the_pin(self):
        # Division after an identifier, a number, a closing
        # parenthesis, a closing bracket, a string and a
        # postfix step all stand as division, and none of the
        # divisions opens a literal that swallows the module.
        text = MODULE.read_text(encoding="utf-8")
        variant = text + (
            "\nlet counter = 8;\n"
            "const byName = counter / 2;\n"
            "const byNumber = 100 / 5 / 2;\n"
            "const byParen = (100) / 5;\n"
            "const byBracket = [100][0] / 5;\n"
            "const byString = \"abcd\".length / 2;\n"
            "const byPostfix = counter++ / 2;\n"
            "const byDecrement = counter-- / 2;\n"
        )
        self.assertEqual(self.problems_for(variant), [])

    def keyword_regex_variant(self, call):
        text = MODULE.read_text(encoding="utf-8")
        return text.replace(
            "async function gateSpawn($, e, next) {",
            "function probeKeywordRegex() { return /'/.test(\"x\"); }\n"
            "\nasync function gateSpawn($, e, next) {",
            1,
        ).replace(
            'await $.env.get("RECOGNITIO_PACKET_DIR")', call, 1
        )

    def test_an_escaped_env_variable_behind_a_keyword_regex_fails(self):
        broken = self.keyword_regex_variant(
            'await $.\\u0065nv.get(PACKET_ENV)')
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not a string literal" in p for p in problems), problems
        )

    def test_an_escaped_env_wrong_literal_behind_a_keyword_regex_fails(self):
        broken = self.keyword_regex_variant(
            'await $.\\u0065nv.get("SOMETHING_ELSE")')
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not the exact name" in p for p in problems), problems
        )

    def test_an_escaped_env_bracket_method_behind_a_keyword_regex_fails(self):
        broken = self.keyword_regex_variant(
            'await $.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR")')
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_env_correct_literal_behind_a_keyword_regex_passes(self):
        variant = self.keyword_regex_variant(
            'await $.\\u0065nv.get("RECOGNITIO_PACKET_DIR")')
        self.assertEqual(self.problems_for(variant), [])

    def test_regexes_after_operators_and_keywords_pass_the_pin(self):
        # Regex literals after an operator and after keywords
        # that expect an expression open as regexes, quotes
        # inside them open no string, and the module behind
        # them stands judged and clean.
        text = MODULE.read_text(encoding="utf-8")
        variant = text + (
            "\nfunction probeRegexes(v) {\n"
            "  if (/a/.test(\"x\")) { return /'/.test(\"x\"); }\n"
            "  const byTypeof = typeof /'/;\n"
            "  const byBang = !/'/.test(\"x\");\n"
            "  switch (v) { case /'/.test(\"x\") ? 1 : 1: break; }\n"
            "  return byTypeof;\n"
            "}\n"
        )
        self.assertEqual(self.problems_for(variant), [])

    def test_the_shared_slash_judgement_reads_tokens_not_characters(self):
        # The three walkers share the one judgement, so each
        # reads the postfix division and the keyword regex
        # positions as code.
        decode = self.mod.decode_identifier_escapes
        call = '$.\\u0065nv.get("X")'
        for head in (
            "function p() { return /'/.test(\"x\"); }\n",
            "const t = typeof /'/.test(\"x\");\n",
            "const t = (/'/.test(\"x\"), 1);\n",
            "switch (v) { case /'/.test(\"x\") ? 1 : 1: break; }\n",
        ):
            self.assertIn("$.env.get", decode(head + call), head)
        self.assertIn(
            "$.env.get",
            decode("(n++ / " + call + " / 1)"),
        )
        self.assertIn(
            "$.fs.read",
            decode("(n-- / $.\\u0066s.read(p) / 1)"),
        )
        chain = "(n++ / $.env.get(\"X\") / 1)"
        dollar = chain.index("$")
        for start, end in self.mod.literal_spans(chain):
            self.assertFalse(start <= dollar <= end, chain)
        regexed = "function p() { return /'/.test(\"x\"); }"
        slash = regexed.index("/'")
        self.assertTrue(
            any(start <= slash <= end
                for start, end in self.mod.literal_spans(regexed)),
            regexed,
        )
        stripped = self.mod.strip_comments(
            "(n++ / $.env.get(\"X\") /*c*/ / 1)")
        self.assertNotIn("/*c*/", stripped)
        self.assertIn("$.env.get", stripped)

    # Lane 4, invalid escapes. The decoder decodes only a
    # character that can stand in an identifier at the
    # position the escape stands in, so an invalid or
    # punctuation valued escape stays as written and is
    # judged as written, never fabricated into a chain.

    def test_the_decoder_leaves_invalid_escapes_undecoded(self):
        decode = self.mod.decode_identifier_escapes
        for snippet in (
            "$.\\u{110000}nv.get(\"X\")",
            "$.\\u{}nv.get(\"X\")",
            "$.\\u{zz}nv.get(\"X\")",
            "$.\\uD800nv.get(\"X\")",
            "$.\\u06 5nv.get(\"X\")",
            "$.env\\u002eget(\"X\")",
            "$\\u002env.get(\"X\")",
            "$.env.\\u0031et(\"X\")",
        ):
            self.assertEqual(decode(snippet), snippet, snippet)

    def test_the_decoder_decodes_valid_escapes_by_position(self):
        decode = self.mod.decode_identifier_escapes
        self.assertEqual(
            decode("$.env.g\\u0031t(\"X\")"), "$.env.g1t(\"X\")")
        self.assertEqual(
            decode("$.env.ge\\u0024(\"X\")"), "$.env.ge$(\"X\")")
        self.assertEqual(
            decode("\\u0024.env.get(\"X\")"), "$.env.get(\"X\")")
        self.assertEqual(
            decode("\\u{24}.env.get(\"X\")"), "$.env.get(\"X\")")
        self.assertEqual(
            decode("$.\\u0065nv.get(\"X\")"), "$.env.get(\"X\")")

    def test_an_escaped_dot_in_a_member_name_is_not_fabricated(self):
        # Before the fix the decoder rewrote this source to
        # the clean $.env.get chain it does not contain and
        # passed it, where the host refuses the module as an
        # invalid unicode escape. Judged as written, the
        # allowlist reads the $.env head the source does make.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.env\\u002eget'
            '("RECOGNITIO_PACKET_DIR");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("$.env, outside the allowlist" in p for p in problems),
            problems,
        )

    def test_a_digit_escaped_method_head_is_judged_as_written(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.env.\\u0031et'
            '("RECOGNITIO_PACKET_DIR");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("$.env, outside the allowlist" in p for p in problems),
            problems,
        )

    def test_the_allowlist_names_a_dollar_continue_member_in_full(self):
        # The member ge$ is a valid identifier the host leaves
        # alone, and the refusal names the call the source
        # makes, in full, not the call truncated at the $.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.env.ge\\u0024'
            '("RECOGNITIO_PACKET_DIR");',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("$.env.ge$," in p for p in problems), problems
        )

    # Lane 4, quoted call shapes. The env and fs pins skip a
    # match whose head stands inside a literal span, so a
    # call shape quoted as text is not a call site, the way
    # a comment quoting one already was not.

    def test_a_string_quoting_an_env_call_shape_passes_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        quoted = text + (
            '\nconst probeQuoted = "$.env.get(\\"SOMETHING_ELSE\\")";\n'
        )
        self.assertEqual(self.problems_for(quoted), [])

    def test_a_template_quoting_an_env_call_shape_passes_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        quoted = text + (
            '\nconst probeQuoted = `$.env.get("SOMETHING_ELSE")`;\n'
        )
        self.assertEqual(self.problems_for(quoted), [])

    def test_a_regex_quoting_an_env_call_shape_passes_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        quoted = text + (
            '\nconst probeQuoted = /$.env.get("SOMETHING_ELSE")/;\n'
        )
        self.assertEqual(self.problems_for(quoted), [])

    def test_a_string_quoting_an_fs_options_shape_passes_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        quoted = text + (
            '\nconst probeQuoted = "$.fs.read({ path: x })";\n'
        )
        self.assertEqual(self.problems_for(quoted), [])

    def test_a_regex_quoting_an_fs_options_shape_passes_the_pin(self):
        text = MODULE.read_text(encoding="utf-8")
        quoted = text + (
            '\nconst probeQuoted = /$.fs.read({ path: x })/;\n'
        )
        self.assertEqual(self.problems_for(quoted), [])

    def test_an_interpolated_template_env_call_still_fails_the_pin(self):
        # Code inside a template interpolation stands outside
        # the literal spans and is judged, so the exclusion
        # for quoted text opens no door for a real call site.
        text = MODULE.read_text(encoding="utf-8")
        broken = text + (
            '\nconst probeInterp = `${ $.env.get("SOMETHING_ELSE") }`;\n'
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not the exact name" in p for p in problems), problems
        )

    # Lane 5, the bracket kinds. A closing parenthesis is
    # judged by the parenthesis it closes and a closing brace
    # by the brace it closes, so a regex standing as the body
    # of a control head opens as a regex and a division slash
    # after an object literal reads as division, and the call
    # sites behind both stand judged.

    def control_head_variant(self, head, call):
        text = MODULE.read_text(encoding="utf-8")
        variant = text.replace(
            "async function gateSpawn($, e, next) {",
            head + "\nasync function gateSpawn($, e, next) {",
            1,
        ).replace(
            'await $.env.get("RECOGNITIO_PACKET_DIR")', call, 1
        )
        self.assertNotEqual(variant, text)
        self.assertIn("probe", variant)
        return variant

    def test_an_escaped_env_bracket_method_behind_an_if_head_regex_fails(self):
        broken = self.control_head_variant(
            "function probeIf(v) { if (v) /'/.test(\"x\"); }",
            'await $.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR")',
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_env_variable_behind_a_while_head_regex_fails(self):
        broken = self.control_head_variant(
            "function probeWhile(v) { while (v) /'/.test(\"x\"); }",
            'await $.\\u0065nv.get(PACKET_ENV)',
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not a string literal" in p for p in problems),
            problems,
        )

    def test_an_escaped_env_bracket_method_behind_a_for_head_regex_fails(self):
        broken = self.control_head_variant(
            "function probeFor() {"
            " for (let i = 0; i < 1; i++) /'/.test(\"x\"); }",
            'await $.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR")',
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_env_correct_literal_behind_an_if_head_regex_passes(self):
        variant = self.control_head_variant(
            "function probeIf(v) { if (v) /'/.test(\"x\"); }",
            'await $.\\u0065nv.get("RECOGNITIO_PACKET_DIR")',
        )
        self.assertEqual(self.problems_for(variant), [])

    def test_an_escaped_env_correct_literal_behind_a_while_head_regex_passes(self):
        variant = self.control_head_variant(
            "function probeWhile(v) { while (v) /'/.test(\"x\"); }",
            'await $.\\u0065nv.get("RECOGNITIO_PACKET_DIR")',
        )
        self.assertEqual(self.problems_for(variant), [])

    def test_an_object_inside_a_control_head_still_leaves_a_regex(self):
        # The object brace inside the head closes as an
        # operand and the head parenthesis still closes as a
        # control head, so the regex behind the head opens.
        broken = self.control_head_variant(
            "function probeNest(v) { if ({a: 2}.a) /'/.test(\"x\"); }",
            'await $.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR")',
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_a_control_head_inside_an_object_value_function_still_opens(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "async function gateSpawn($, e, next) {",
            "const probeHolder = { run: function (v) {"
            " if (v) /'/.test(\"x\"); return 1; } };\n"
            "async function gateSpawn($, e, next) {",
            1,
        ).replace(
            'await $.env.get("RECOGNITIO_PACKET_DIR")',
            'await $.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR")',
            1,
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_env_bracket_method_behind_a_block_close_regex_fails(self):
        # A brace closing a block leaves a statement to start,
        # so the regex standing after a function body opens
        # as a regex and the call behind it stands judged.
        broken = self.control_head_variant(
            "function probeBlock() { const q = 1; }\n/'/.test(\"x\");",
            'await $.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR")',
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_env_correct_literal_behind_a_block_close_regex_passes(self):
        variant = self.control_head_variant(
            "function probeBlock() { const q = 1; }\n/'/.test(\"x\");",
            'await $.\\u0065nv.get("RECOGNITIO_PACKET_DIR")',
        )
        self.assertEqual(self.problems_for(variant), [])

    def test_an_escaped_env_bracket_method_after_an_object_literal_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await ({a: 2} / $.\\u0065nv["get"]'
            '("RECOGNITIO_PACKET_DIR") / 1);',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_fs_bracket_method_after_an_object_literal_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            'const text = await ({a: 2} / $.\\u0066s["read"]'
            '(manifestPath) / 1);',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_env_correct_literal_after_an_object_literal_passes(self):
        text = MODULE.read_text(encoding="utf-8")
        variant = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await ({a: 2} / $.\\u0065nv.get'
            '("RECOGNITIO_PACKET_DIR") / 1);',
        )
        self.assertNotEqual(variant, text)
        self.assertEqual(self.problems_for(variant), [])

    def test_an_escaped_env_bracket_method_after_a_returned_object_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text + (
            '\nfunction probeReturn() { return {a: 2} / '
            '$.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR") / 1; }\n'
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_env_correct_literal_after_a_returned_object_passes(self):
        text = MODULE.read_text(encoding="utf-8")
        variant = text + (
            '\nfunction probeReturn() { return {a: 2} / '
            '$.\\u0065nv.get("RECOGNITIO_PACKET_DIR") / 1; }\n'
        )
        self.assertEqual(self.problems_for(variant), [])

    def test_an_escaped_env_bracket_method_after_an_object_in_call_arguments_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text + (
            '\nconst probeArgs = Math.max({a: 2} / '
            '$.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR") / 1, 0);\n'
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_env_correct_literal_after_an_object_in_call_arguments_passes(self):
        text = MODULE.read_text(encoding="utf-8")
        variant = text + (
            '\nconst probeArgs = Math.max({a: 2} / '
            '$.\\u0065nv.get("RECOGNITIO_PACKET_DIR") / 1, 0);\n'
        )
        self.assertEqual(self.problems_for(variant), [])

    def test_an_escaped_env_bracket_method_after_an_object_in_an_array_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text + (
            '\nconst probeArray = [{a: 2} / '
            '$.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR") / 1];\n'
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_env_bracket_method_after_an_object_behind_a_comma_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text + (
            '\nconst probeComma = (0, {a: 2} / '
            '$.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR") / 1);\n'
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_env_bracket_method_after_an_object_as_a_value_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text + (
            '\nconst probeValue = { held: {a: 2} / '
            '$.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR") / 1 };\n'
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_env_bracket_method_after_an_object_in_a_function_body_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text + (
            '\nfunction probeBody() { const held = {a: 2} / '
            '$.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR") / 1;'
            ' return held; }\n'
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_env_bracket_method_after_an_object_in_an_arrow_body_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text + (
            '\nconst probeArrow = () => { const held = {a: 2} / '
            '$.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR") / 1;'
            ' return held; };\n'
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_env_bracket_method_after_an_object_in_a_class_method_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text + (
            '\nclass ProbeClass { method() { return {a: 2} / '
            '$.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR") / 1; } }\n'
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_env_bracket_method_after_an_object_in_an_interpolation_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text + (
            '\nconst probeInterpObject = `${ {a: 2} / '
            '$.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR") / 1 }`;\n'
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_a_member_step_after_an_object_brace_still_divides(self):
        # The member word after the brace is the operand at
        # the slash, so the chain behind the member divides
        # and the escaped call in it stands judged, the
        # control the axes seat recorded for this family.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await ({a: 2}.a / $.\\u0065nv["get"]'
            '("RECOGNITIO_PACKET_DIR") / 1);',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )
        variant = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await ({a: 2}.a / $.\\u0065nv.get'
            '("RECOGNITIO_PACKET_DIR") / 1);',
        )
        self.assertNotEqual(variant, text)
        self.assertEqual(self.problems_for(variant), [])

    def test_the_shared_slash_judgement_reads_bracket_kinds(self):
        # The three walkers share the one judgement, so each
        # reads the control head and object literal positions
        # as code and the block positions as statements.
        decode = self.mod.decode_identifier_escapes
        call = '$.\\u0065nv.get("X")'
        for head in (
            "function p(v) { if (v) /'/.test(\"x\"); }\n",
            "function p(v) { while (v) /'/.test(\"x\"); }\n",
            "function p() { for (let i = 0; i < 1; i++)"
            " /'/.test(\"x\"); }\n",
            "function p(o) { with (o) /'/.test(\"x\"); }\n",
            "switch (v) /'/.test(\"x\");\n",
            "try { probe(); } catch (e) /'/.test(\"x\");\n",
            "function p() { const q = 1; } /'/.test(\"x\");\n",
            "const f = () => {}; /'/.test(\"x\");\n",
            "class Probe { m() { return 1; } } /'/.test(\"x\");\n",
        ):
            self.assertIn("$.env.get", decode(head + call), head)
        for chain in (
            "({a: 2} / " + call + " / 1)",
            "function p() { return {a: 2} / " + call + " / 1; }",
            "const t = probe({a: 2} / " + call + " / 1);",
            "const t = [{a: 2} / " + call + " / 1];",
            "const t = (0, {a: 2} / " + call + " / 1);",
            "const t = {b: {a: 2} / " + call + " / 1};",
            "const t = `${ {a: 2} / " + call + " / 1 }`;",
        ):
            self.assertIn("$.env.get", decode(chain), chain)
        headed = "function p(v) { if (v) /'/.test(\"x\"); }"
        slash = headed.index("/'")
        self.assertTrue(
            any(start <= slash <= end
                for start, end in self.mod.literal_spans(headed)),
            headed,
        )
        chained = "({a: 2} / $.env.get(\"X\") / 1)"
        dollar = chained.index("$")
        for start, end in self.mod.literal_spans(chained):
            self.assertFalse(start <= dollar <= end, chained)
        stripped = self.mod.strip_comments(
            "({a: 2} / $.env.get(\"X\") /*c*/ / 1)")
        self.assertNotIn("/*c*/", stripped)
        self.assertIn("$.env.get", stripped)
        stripped_head = self.mod.strip_comments(
            "function p(v) { if (v) /'/.test(\"x\"); } /*c*/")
        self.assertNotIn("/*c*/", stripped_head)

    # Lane 5 addendum, the red team lane 4 corpora. The word
    # default joins the keywords an expression can follow, the
    # auxiliary walks share the one slash judgement, and the
    # member walk counts a top level holder wherever it
    # stands, so the A, B, E and X payload families and their
    # controls judge in both directions.

    def export_default_variant(self, call):
        text = MODULE.read_text(encoding="utf-8")
        variant = text.replace(
            "async function gateSpawn($, e, next) {",
            "export default /'/.test(\"x\") ? 1 : 2;\n"
            "\nasync function gateSpawn($, e, next) {",
            1,
        ).replace(
            'await $.env.get("RECOGNITIO_PACKET_DIR")', call, 1
        ) + "\nconst tailExport = 'z';\n"
        self.assertNotEqual(variant, text)
        self.assertIn("export default", variant)
        return variant

    def test_an_escaped_env_bracket_method_behind_an_export_default_regex_fails(self):
        broken = self.export_default_variant(
            'await $.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR")')
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_env_variable_behind_an_export_default_regex_fails(self):
        broken = self.export_default_variant(
            'await $.\\u0065nv.get(PACKET_ENV)')
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not a string literal" in p for p in problems),
            problems,
        )

    def test_an_escaped_env_correct_literal_behind_an_export_default_regex_passes(self):
        variant = self.export_default_variant(
            'await $.\\u0065nv.get("RECOGNITIO_PACKET_DIR")')
        self.assertEqual(self.problems_for(variant), [])

    def test_the_shared_slash_judgement_reads_default_and_extends(self):
        decode = self.mod.decode_identifier_escapes
        call = '$.\\u0065nv.get("X")'
        self.assertIn(
            "$.env.get",
            decode("export default /'/.test(\"x\") ? 1 : 2;\n"
                   + call),
        )
        self.assertIn(
            "$.env.get",
            decode("class Probe extends /'/.test(\"x\") {}\n"
                   + call),
        )

    def test_an_escaped_env_variable_behind_a_helper_if_head_regex_fails(self):
        broken = self.control_head_variant(
            "function probeA1(x) {\n"
            "  if (x) /'/.test(\"x\");\n}",
            'await $.\\u0065nv.get(PACKET_ENV)',
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not a string literal" in p for p in problems),
            problems,
        )

    def test_a_plain_optional_dollar_call_behind_a_for_head_regex_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "async function gateSpawn($, e, next) {",
            "function probeA3() {\n"
            "  for (;;) /'/.test(\"x\");\n}\n"
            "\nasync function gateSpawn($, e, next) {",
            1,
        ).replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $?.("RECOGNITIO_PACKET_DIR");',
            1,
        ) + "\nconst tailA3 = 'z';\n"
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("calls $ itself through an optional call" in p
                for p in problems),
            problems,
        )

    def test_a_plain_wrong_literal_behind_an_if_head_regex_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "async function gateSpawn($, e, next) {",
            "function probeA4(x) {\n"
            "  if (x) /'/.test(\"x\");\n}\n"
            "\nasync function gateSpawn($, e, next) {",
            1,
        ).replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.env.get("SOMETHING_ELSE");',
            1,
        ) + "\nconst tailA4 = 'z';\n"
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not the exact name" in p for p in problems),
            problems,
        )

    def test_an_escaped_fs_bracket_method_behind_an_else_if_head_regex_fails(self):
        # The helper stands ahead of the function holding the
        # file read, so the fake string the head opens in the
        # mutant reading is the one that would swallow it.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "async function packetIsVerified($, packetDir) {",
            "function probeA5(x, y) {\n"
            "  if (x) { return 1; } else if (y) /'/.test(\"x\");\n}\n"
            "\nasync function packetIsVerified($, packetDir) {",
            1,
        ).replace(
            "const text = await $.fs.read(manifestPath);",
            'const text = await $.\\u0066s["read"](manifestPath);',
            1,
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_env_variable_after_an_object_literal_in_a_helper_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "async function gateSpawn($, e, next) {",
            "function probeB1() {\n"
            "  const w = {a: 1} / $.\\u0065nv.get(PACKET_ENV) / 1;\n"
            "  return w;\n}\n"
            "\nasync function gateSpawn($, e, next) {",
            1,
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not a string literal" in p for p in problems),
            problems,
        )

    def test_a_plain_wrong_literal_after_an_object_literal_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "async function gateSpawn($, e, next) {",
            "function probeB3() {\n"
            "  const w = {a: 1} / $.env.get(\"SOMETHING_ELSE\") / 1;\n"
            "  return w;\n}\n"
            "\nasync function gateSpawn($, e, next) {",
            1,
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not the exact name" in p for p in problems),
            problems,
        )

    def test_a_plain_optional_dollar_call_after_an_object_literal_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "async function gateSpawn($, e, next) {",
            "function probeB4() {\n"
            "  const w = {a: 1} / $?.(\"RECOGNITIO_PACKET_DIR\") / 1;\n"
            "  return w;\n}\n"
            "\nasync function gateSpawn($, e, next) {",
            1,
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("calls $ itself through an optional call" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_env_variable_after_an_object_literal_in_a_call_argument_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "async function gateSpawn($, e, next) {",
            "function sinkB5(x) { return x; }\n"
            "function probeB5() {\n"
            "  return sinkB5({a: 1} / $.\\u0065nv.get(PACKET_ENV) / 1);\n"
            "}\n"
            "\nasync function gateSpawn($, e, next) {",
            1,
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not a string literal" in p for p in problems),
            problems,
        )

    def test_an_escaped_fs_options_object_after_an_object_literal_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "async function gateSpawn($, e, next) {",
            "function probeB7(manifestPath) {\n"
            "  const w = {a: 1} / $.\\u0066s.read({ path: manifestPath }) / 1;\n"
            "  return w;\n}\n"
            "\nasync function gateSpawn($, e, next) {",
            1,
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("calls $.fs.read with an options object" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_env_variable_after_an_object_literal_at_the_shipped_call_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await (0, {a: 1} / $.\\u0065nv.get'
            '(PACKET_ENV) / 1);',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not a string literal" in p for p in problems),
            problems,
        )

    def test_an_escaped_env_variable_after_a_class_name_still_fails(self):
        # The brace door is the brace itself, so a division
        # headed by a class name, an operand in its own
        # right, judged the same way before and after.
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "async function gateSpawn($, e, next) {",
            "function probeB6() {\n"
            "  const C = class {};\n"
            "  const w = C / $.\\u0065nv.get(PACKET_ENV) / 1;\n"
            "  return w;\n}\n"
            "\nasync function gateSpawn($, e, next) {",
            1,
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not a string literal" in p for p in problems),
            problems,
        )

    def test_an_fs_branch_object_behind_a_typeof_regex_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read(typeof /'/.test(\"x\") "
            "? { path: manifestPath } : manifestPath);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("calls $.fs.read with an options object" in p
                for p in problems),
            problems,
        )
        self.assertFalse(
            any("cannot read" in p for p in problems), problems
        )

    def test_an_fs_branch_object_behind_a_bang_regex_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read(!/'/.test(\"x\") "
            "? { path: manifestPath } : manifestPath);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("calls $.fs.read with an options object" in p
                for p in problems),
            problems,
        )

    def test_a_benign_fs_branch_behind_a_typeof_regex_passes(self):
        text = MODULE.read_text(encoding="utf-8")
        variant = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read(typeof /'/.test(\"x\") "
            "? manifestPath : manifestPath);",
        )
        self.assertNotEqual(variant, text)
        self.assertEqual(self.problems_for(variant), [])

    def test_an_fs_member_object_behind_a_typeof_holder_value_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const holder = { probe: typeof /'/.test(\"x\") ? 1 : 2, "
            "inner: { path: manifestPath } };\n"
            "  const text = await $.fs.read(holder.inner);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("options object held in a member" in p
                for p in problems),
            problems,
        )

    def test_an_fs_member_object_behind_a_top_level_typeof_holder_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text + (
            '\nconst holderB = { probe: typeof /\'/.test("x") ? 1 : 2, '
            'inner: { path: "x" } };\n'
        )
        broken = broken.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read(holderB.inner);",
            1,
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("options object held in a member" in p
                for p in problems),
            problems,
        )

    def test_an_fs_member_object_behind_a_leading_typeof_holder_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = (
            "const holderF = { probe: typeof /'/.test(\"x\") ? 1 : 2, "
            "inner: { path: \"x\" } };\n"
        ) + text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read(holderF.inner);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("options object held in a member" in p
                for p in problems),
            problems,
        )

    def test_an_fs_member_object_behind_a_leading_plain_holder_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = (
            "const holderF = { probe: 1, inner: { path: \"x\" } };\n"
        ) + text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read(holderF.inner);",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("options object held in a member" in p
                for p in problems),
            problems,
        )

    def test_a_benign_fs_member_string_behind_a_typeof_holder_passes(self):
        text = MODULE.read_text(encoding="utf-8")
        variant = text + (
            '\nconst holderB = { probe: typeof /\'/.test("x") ? 1 : 2, '
            'inner: "x" };\n'
        )
        variant = variant.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read(holderB.inner);",
            1,
        )
        self.assertNotEqual(variant, text)
        self.assertEqual(self.problems_for(variant), [])

    def test_an_fs_member_object_behind_a_holder_defined_after_the_read_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text + '\nconst holderH = { inner: { path: "x" } };\n'
        broken = broken.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read(holderH.inner);",
            1,
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("options object held in a member" in p
                for p in problems),
            problems,
        )

    def test_an_fs_bound_object_behind_a_holder_defined_after_the_read_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text + '\nconst holderH = { path: "x" };\n'
        broken = broken.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read(holderH);",
            1,
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("bound in the module to an options object" in p
                for p in problems),
            problems,
        )

    def test_an_fs_helper_return_object_behind_a_keyword_regex_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read(optsHelper());",
        ) + (
            "\nfunction optsHelper() {\n"
            "  if (/'/.test(\"x\")) { return { path: manifestPath }; }\n"
            "  return { path: manifestPath };\n}\n"
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("calls $.fs.read with an options object" in p
                for p in problems),
            problems,
        )

    def test_an_fs_helper_return_object_behind_a_typeof_regex_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read(optsHelper());",
        ) + (
            "\nfunction optsHelper() {\n"
            "  const t = typeof /'/.test(\"x\");\n"
            "  if (t) { return { path: manifestPath }; }\n"
            "  return { path: manifestPath };\n}\n"
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("calls $.fs.read with an options object" in p
                for p in problems),
            problems,
        )

    def test_an_fs_fed_parameter_behind_a_typeof_default_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text + (
            "\nasync function readerX5(path = typeof /'/.test(\"x\")"
            " ? \"a\" : \"b\", $) {\n"
            "  return $.fs.read(path);\n}\n"
            "async function probeCallerX5($) {\n"
            "  return readerX5({ path: \"x\" });\n}\n"
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("feed an options object" in p for p in problems),
            problems,
        )

    def test_an_fs_fed_parameter_behind_a_typeof_call_argument_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text + (
            "\nasync function readerX5(path, $) {\n"
            "  return $.fs.read(path);\n}\n"
            "async function probeCallerX5() {\n"
            "  return readerX5({ path: \"x\" },"
            " typeof /'/.test(\"x\") ? 1 : 2);\n}\n"
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("parameter" in p and "options object" in p
                for p in problems),
            problems,
        )

    def test_an_fs_fed_parameter_behind_a_plain_call_argument_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text + (
            "\nasync function readerX5(path, $) {\n"
            "  return $.fs.read(path);\n}\n"
            "async function probeCallerX5() {\n"
            "  return readerX5({ path: \"x\" }, 1);\n}\n"
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("parameter" in p and "options object" in p
                for p in problems),
            problems,
        )

    def test_a_benign_dollar_feeding_call_behind_a_typeof_regex_passes(self):
        text = MODULE.read_text(encoding="utf-8")
        variant = text + (
            "\nfunction dollarSink2(a, $) { return a; }\n"
        )
        variant = variant.replace(
            "  if (await packetIsVerified($, packetDir)) {",
            "  const probeDS = dollarSink2("
            "typeof /'/.test(\"x\") ? 1 : 2, $);\n"
            "  if (await packetIsVerified($, packetDir)) {",
            1,
        )
        self.assertNotEqual(variant, text)
        self.assertEqual(self.problems_for(variant), [])

    def test_an_escaped_env_variable_behind_a_regex_class_fails(self):
        broken = self.control_head_variant(
            "function probeC2() {\n"
            "  const r = /[/']/.test(\"x\");\n"
            "  const w = $.\\u0065nv.get(PACKET_ENV);\n"
            "  return r ? w : null;\n}",
            'await $.env.get("RECOGNITIO_PACKET_DIR")',
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not a string literal" in p for p in problems),
            problems,
        )

    def test_an_escaped_env_variable_behind_keyword_spelled_keys_fails(self):
        broken = self.control_head_variant(
            "function probeC4(k) {\n"
            "  const o = {return: 8, in: 4};\n"
            "  const w = o[k] / $.\\u0065nv.get(PACKET_ENV) / 1;\n"
            "  return w;\n}",
            'await $.env.get("RECOGNITIO_PACKET_DIR")',
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not a string literal" in p for p in problems),
            problems,
        )

    def test_an_escaped_env_variable_inside_nested_templates_fails(self):
        broken = self.control_head_variant(
            "function probeC5() {\n"
            "  const s = `${ `${ /'/.test(\"x\") ? "
            "$.\\u0065nv.get(PACKET_ENV) : \"\" }` }`;\n"
            "  return s;\n}",
            'await $.env.get("RECOGNITIO_PACKET_DIR")',
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not a string literal" in p for p in problems),
            problems,
        )

    def test_an_escaped_env_variable_behind_a_file_head_regex_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = "/'/.test(\"x\");\n" + text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await $.\\u0065nv.get(PACKET_ENV);',
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not a string literal" in p for p in problems),
            problems,
        )

    def test_an_escaped_env_variable_behind_a_parenthesised_postfix_fails(self):
        broken = self.control_head_variant(
            "function probeC9() {\n"
            "  let n = 0;\n"
            "  const w = (n)++ / $.\\u0065nv.get(PACKET_ENV) / 1;\n"
            "  return w;\n}",
            'await $.env.get("RECOGNITIO_PACKET_DIR")',
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not a string literal" in p for p in problems),
            problems,
        )

    def test_an_escaped_env_variable_behind_a_plain_control_head_regex_fails(self):
        broken = self.control_head_variant(
            "function probeC10(x, y) {\n"
            "  if (x) /re/.test(y);\n"
            "  const w = $.\\u0065nv.get(PACKET_ENV);\n"
            "  return w;\n}",
            'await $.env.get("RECOGNITIO_PACKET_DIR")',
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not a string literal" in p for p in problems),
            problems,
        )

    # Lane 6, the final red team pass. The registration,
    # catch and deny pins are structural, the colon, number
    # dot, expression standing and return line terminator
    # positions stand judged in the shared reading, the
    # auxiliary walks read templates as the charged walks
    # do, and the allowlist and alien scans hold the literal
    # span exclusion their sibling scans already held.

    def door_variant(self, opener, call):
        text = MODULE.read_text(encoding="utf-8")
        variant = text.replace(
            "async function gateSpawn($, e, next) {",
            opener + "\n\nasync function gateSpawn($, e, next) {",
            1,
        ).replace(
            'await $.env.get("RECOGNITIO_PACKET_DIR")', call, 1
        )
        self.assertNotEqual(variant, text)
        return variant

    def chain_variant(self, stmt, call=None):
        text = MODULE.read_text(encoding="utf-8")
        variant = text.replace(
            "async function gateSpawn($, e, next) {",
            stmt + "\n\nasync function gateSpawn($, e, next) {",
            1,
        )
        if call is not None:
            variant = variant.replace(
                'await $.env.get("RECOGNITIO_PACKET_DIR")', call, 1
            )
        self.assertNotEqual(variant, text)
        return variant

    def gate_variant(self, gate_fn):
        text = MODULE.read_text(encoding="utf-8")
        shipped_gate = (
            "async function gateSpawn($, e, next) {\n"
            "  const packetDir = await $.env.get("
            "\"RECOGNITIO_PACKET_DIR\");\n"
            "  if (typeof packetDir !== \"string\""
            " || packetDir.length === 0) {\n"
            "    return next(e);\n"
            "  }\n"
            "  if (await packetIsVerified($, packetDir)) {\n"
            "    return next(e);\n"
            "  }\n"
            "  return {\n"
            "    deny: \"recognitio: the review packet manifest"
            " is not verified, so this review spawn is denied\",\n"
            "  };\n"
            "}"
        )
        self.assertIn(shipped_gate, text)
        return text.replace(shipped_gate, gate_fn)

    def catch_variant(self, catch_fn=None, register=None):
        text = MODULE.read_text(encoding="utf-8")
        shipped_catch = (
            "function catchSpawnFailure($, e, next) {\n"
            "  return {\n"
            "    deny: \"recognitio: the packet gate hook failed, "
            "so this review spawn is denied rather than let through\",\n"
            "  };\n"
            "}"
        )
        shipped_register = (
            "export function register(on, options) {\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}"
        )
        if catch_fn is not None:
            self.assertIn(shipped_catch, text)
            text = text.replace(shipped_catch, catch_fn)
        if register is not None:
            self.assertIn(shipped_register, text)
            text = text.replace(shipped_register, register)
        return text

    # Item 1, the structural registration, catch and deny pins.

    def test_a_comment_carrying_the_registration_fails_the_pin(self):
        broken = self.catch_variant(register=(
            "// on('agent.spawn', gateSpawn)"
            ".catch(catchSpawnFailure)\n"
            "export function register(on, options) {\n"
            "  on(\"prompt.change\", gateSpawn);\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("registers no agent.spawn hook" in p
                for p in problems),
            problems,
        )

    def test_a_string_carrying_the_registration_fails_the_pin(self):
        broken = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  const note = \"on('agent.spawn', gateSpawn)"
            ".catch(catchSpawnFailure)\";\n"
            "  on(\"prompt.change\", gateSpawn);\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("registers no agent.spawn hook" in p
                for p in problems),
            problems,
        )

    def test_a_wrong_event_registration_fails_the_pin(self):
        broken = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  on(\"prompt.change\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("registers no agent.spawn hook" in p
                for p in problems),
            problems,
        )

    def test_a_registration_whose_handler_never_catches_fails(self):
        broken = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  on(\"agent.spawn\", gateSpawn);\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("no .catch handler" in p for p in problems),
            problems,
        )

    def test_a_catch_handler_holding_deny_in_a_string_fails(self):
        broken = self.catch_variant(catch_fn=(
            "function catchSpawnFailure($, e, next) {\n"
            "  const note = \"deny\";\n"
            "  return {};\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("returns no deny shape" in p for p in problems),
            problems,
        )

    def test_a_catch_handler_with_a_brace_in_a_string_fails(self):
        # The brace in the string held the old naive brace
        # count open into the next function's deny return.
        # The structural body ends at the handler's own
        # closing brace, whose return carries no deny.
        broken = self.catch_variant(catch_fn=(
            "function catchSpawnFailure($, e, next) {\n"
            "  const open = \"{\";\n"
            "  return {};\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("returns no deny shape" in p for p in problems),
            problems,
        )

    def test_a_catch_handler_returning_an_empty_object_fails(self):
        broken = self.catch_variant(catch_fn=(
            "function catchSpawnFailure($, e, next) {\n"
            "  return {};\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("returns no deny shape" in p for p in problems),
            problems,
        )

    def test_a_catch_handler_that_passes_the_spawn_through_fails(self):
        broken = self.catch_variant(catch_fn=(
            "function catchSpawnFailure($, e, next) {\n"
            "  return next(e);\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("returns no deny shape" in p for p in problems),
            problems,
        )

    def test_a_catch_handler_denying_on_one_branch_only_fails(self):
        broken = self.catch_variant(catch_fn=(
            "function catchSpawnFailure($, e, next) {\n"
            "  return e ? { deny: \"recognitio: denied\" } : {};\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("returns no deny shape" in p for p in problems),
            problems,
        )

    def test_an_arrow_catch_handler_with_a_true_deny_passes(self):
        variant = self.catch_variant(catch_fn=(
            "const catchSpawnFailure = ($, e, next) => {\n"
            "  return {\n"
            "    deny: \"recognitio: the packet gate hook failed\",\n"
            "  };\n"
            "};"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_a_function_expression_catch_handler_passes(self):
        variant = self.catch_variant(catch_fn=(
            "const catchSpawnFailure = function ($, e, next) {\n"
            "  return { deny: \"recognitio: denied\" };\n"
            "};"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_an_arrow_catch_handler_with_an_expression_body_passes(self):
        variant = self.catch_variant(catch_fn=(
            "const catchSpawnFailure = ($, e, next) => "
            "({ deny: \"recognitio: denied\" });"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_an_inline_arrow_catch_handler_passes(self):
        variant = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  on(\"agent.spawn\", gateSpawn).catch(\n"
            "    ($, e, next) => ({ deny: \"recognitio: denied\" }));\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_a_catch_handler_returning_a_bound_deny_object_passes(self):
        variant = self.catch_variant(catch_fn=(
            "function catchSpawnFailure($, e, next) {\n"
            "  const shape = { deny: \"recognitio: denied\" };\n"
            "  return shape;\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_a_single_quoted_registration_passes_the_pin(self):
        variant = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  on('agent.spawn', gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_a_template_literal_registration_passes_the_pin(self):
        variant = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  on(`agent.spawn`, gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    # Lane 7, the deciding re-grade. Every registration is
    # judged for reachability in the register flow, for
    # the gating handler it registers and for singleness,
    # a named handler is judged by its binding as at the
    # registration call, and every exit of the catch
    # handler counts as an outcome.

    def test_a_registration_in_a_dead_branch_fails_the_pin(self):
        broken = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  if (false) {\n"
            "    on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "  }\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("conditional branch" in p for p in problems),
            problems,
        )

    def test_a_registration_after_a_return_fails_the_pin(self):
        broken = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  return;\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("after a return" in p for p in problems),
            problems,
        )

    def test_a_registration_in_an_uncalled_helper_fails(self):
        broken = self.catch_variant(register=(
            "function setup(on) {\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}\n"
            "\n"
            "export function register(on, options) {\n"
            "  on(\"prompt.change\", gateSpawn);\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("statement flow of the register function" in p
                for p in problems),
            problems,
        )

    def test_a_registration_of_an_approving_handler_fails(self):
        broken = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  on(\"agent.spawn\", async ($, e, next) => next(e))"
            ".catch(catchSpawnFailure);\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("does not gate on the packet manifest" in p
                for p in problems),
            problems,
        )

    def test_a_second_registration_fails_the_pin(self):
        broken = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "  on(\"agent.spawn\", gateSpawn);\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("more than once" in p for p in problems),
            problems,
        )

    def test_a_registration_in_a_try_block_passes_the_pin(self):
        variant = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  try {\n"
            "    on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "  } catch (e) {\n"
            "  }\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_a_registration_in_a_finally_block_passes(self):
        variant = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  try {\n"
            "  } finally {\n"
            "    on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "  }\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_a_registration_in_a_plain_block_passes(self):
        variant = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  {\n"
            "    on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "  }\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_a_registration_after_a_conditional_return_passes(self):
        variant = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  if (options) {\n"
            "    return;\n"
            "  }\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_a_registration_in_an_else_branch_fails(self):
        broken = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  if (false) {\n"
            "  } else {\n"
            "    on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "  }\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("conditional branch" in p for p in problems),
            problems,
        )

    def test_a_handler_rebound_before_the_call_fails(self):
        broken = self.catch_variant(register=(
            "catchSpawnFailure = ($, e, next) => ({});\n"
            "\n"
            "export function register(on, options) {\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("returns no deny shape" in p for p in problems),
            problems,
        )

    def test_a_handler_rebound_after_the_call_passes(self):
        variant = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "  catchSpawnFailure = ($, e, next) => ({});\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_a_handler_rebound_in_a_branch_before_the_call_fails(self):
        broken = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  if (options) {\n"
            "    catchSpawnFailure = ($, e, next) => ({});\n"
            "  }\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("returns no deny shape" in p for p in problems),
            problems,
        )

    def test_a_handler_rebound_to_a_denying_arrow_passes(self):
        variant = self.catch_variant(register=(
            "catchSpawnFailure = ($, e, next) => "
            "({ deny: \"recognitio: rebound deny\" });\n"
            "\n"
            "export function register(on, options) {\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_a_catch_handler_falling_off_the_end_fails(self):
        broken = self.catch_variant(catch_fn=(
            "function catchSpawnFailure($, e, next) {\n"
            "  if (e && e.retry) { return { deny: \"x\" }; }\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("returns no deny shape" in p for p in problems),
            problems,
        )

    def test_a_catch_handler_ending_in_a_bare_return_fails(self):
        broken = self.catch_variant(catch_fn=(
            "function catchSpawnFailure($, e, next) {\n"
            "  if (e && e.retry) { return { deny: \"x\" }; }\n"
            "  return;\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("returns no deny shape" in p for p in problems),
            problems,
        )

    def test_an_arrow_catch_handler_falling_off_the_end_fails(self):
        broken = self.catch_variant(catch_fn=(
            "const catchSpawnFailure = ($, e, next) => {\n"
            "  if (e && e.retry) { return { deny: \"x\" }; }\n"
            "};"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("returns no deny shape" in p for p in problems),
            problems,
        )

    def test_a_catch_handler_denying_on_both_branches_passes(self):
        variant = self.catch_variant(catch_fn=(
            "function catchSpawnFailure($, e, next) {\n"
            "  if (e) { return { deny: \"x\" }; }"
            " else { return { deny: \"y\" }; }\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_a_catch_handler_throwing_on_a_branch_fails(self):
        broken = self.catch_variant(catch_fn=(
            "function catchSpawnFailure($, e, next) {\n"
            "  if (e) { return { deny: \"x\" }; }\n"
            "  throw new Error(\"boom\");\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("returns no deny shape" in p for p in problems),
            problems,
        )

    def test_a_catch_handler_throwing_into_its_own_catch_passes(self):
        variant = self.catch_variant(catch_fn=(
            "function catchSpawnFailure($, e, next) {\n"
            "  try { throw new Error(\"boom\"); }"
            " catch (err) { return { deny: \"x\" }; }\n"
            "  return { deny: \"y\" };\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_a_catch_handler_denying_in_try_and_catch_passes(self):
        variant = self.catch_variant(catch_fn=(
            "function catchSpawnFailure($, e, next) {\n"
            "  try { return { deny: \"x\" }; }"
            " catch (err) { return { deny: \"y\" }; }\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    # Lane 7, the yield line terminator in the shared slash
    # judgement, judged through the charged receiver family
    # at the file read position as well as at the env call.

    def test_an_escaped_env_bracket_method_behind_a_yield_block_fails(self):
        broken = self.door_variant(
            "function* probeYield() {\n"
            "  yield\n"
            "  { }\n"
            "  /'/.test(\"x\");\n"
            "}",
            'await $.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR")',
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_fs_bracket_method_behind_a_yield_block_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "async function packetIsVerified($, packetDir) {",
            "function* probeYieldRead() {\n"
            "  yield\n"
            "  { }\n"
            "  /'/.test(\"x\");\n"
            "}\n"
            "\n"
            "async function packetIsVerified($, packetDir) {",
            1,
        ).replace(
            "const text = await $.fs.read(manifestPath);",
            'const text = await $.\\u0066s["read"](manifestPath);',
            1,
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_a_same_line_yield_object_still_divides(self):
        # A yield with no line terminator takes the object
        # as its operand, so the slash after it is division
        # and the payload behind it stands judged.
        broken = self.door_variant(
            "function* probeYieldLine() {\n"
            "  yield { };\n"
            "  /'/.test(\"x\");\n"
            "}",
            'await $.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR")',
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    # Lane 7, the tolerated registration and deny spellings
    # the host accepts, and the catch bound and rest
    # destructured reads the file read walk now traces.

    def test_a_catch_handler_returning_a_helper_result_passes(self):
        variant = self.catch_variant(catch_fn=(
            "function denyShape() {\n"
            "  return { deny: \"recognitio: helper shape\" };\n"
            "}\n"
            "\n"
            "function catchSpawnFailure($, e, next) {\n"
            "  return denyShape();\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_a_catch_handler_helper_denying_on_one_branch_fails(self):
        broken = self.catch_variant(catch_fn=(
            "function denyShape(e) {\n"
            "  if (e) { return { deny: \"x\" }; }\n"
            "  return {};\n"
            "}\n"
            "\n"
            "function catchSpawnFailure($, e, next) {\n"
            "  return denyShape(e);\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("returns no deny shape" in p for p in problems),
            problems,
        )

    def test_a_deny_under_a_computed_template_key_passes(self):
        variant = self.catch_variant(catch_fn=(
            "function catchSpawnFailure($, e, next) {\n"
            "  return { [`deny`]: \"recognitio: denied\" };\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_a_deny_produced_by_spreading_a_bound_object_passes(self):
        variant = self.catch_variant(catch_fn=(
            "const DENY_SHAPE = {\n"
            "  deny: \"recognitio: spread shape\",\n"
            "};\n"
            "\n"
            "function catchSpawnFailure($, e, next) {\n"
            "  return { ...DENY_SHAPE };\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_a_spaced_catch_chain_passes_the_pin(self):
        variant = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  on(\"agent.spawn\", gateSpawn)"
            " . catch (catchSpawnFailure);\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_an_escaped_event_literal_passes_the_pin(self):
        variant = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  on(\"agent.sp\\u0061wn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_an_options_object_bound_by_a_catch_clause_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "let text;\n"
            "  try { throw { path: manifestPath }; }"
            " catch (o) { text = await $.fs.read(o); }",
            1,
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("bound by a catch clause" in p for p in problems),
            problems,
        )

    def test_an_options_object_thrown_from_a_helper_into_a_catch_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "function throwerProbe() {"
            " throw { path: manifestPath }; }\n"
            "  let text;\n"
            "  try { throwerProbe(); }"
            " catch (o) { text = await $.fs.read(o); }",
            1,
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("bound by a catch clause" in p for p in problems),
            problems,
        )

    def test_an_options_object_from_a_rest_destructuring_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const { a, ...o } = { a: 1, path: manifestPath };\n"
            "  const text = await $.fs.read(o);",
            1,
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("$.fs.read" in p and "options" in p
                for p in problems),
            problems,
        )

    # Lane 8, the consolidation. One flow and completion
    # calculus for the reach machine and the outcome
    # walk, one binding reading extended to destructuring
    # for the handler name, the deny name and the gating
    # names, the gating calls judged in code position
    # through the call pins, and outcome expressions read
    # under the shared line terminator fact.

    def test_a_registration_after_a_throw_fails_the_pin(self):
        broken = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  throw new Error(\"closed\");\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("after a return" in p for p in problems),
            problems,
        )

    def test_a_registration_after_a_braced_if_else_that_both_return_fails(self):
        broken = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  if (options) { return; } else { return; }\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("after a return" in p for p in problems),
            problems,
        )

    def test_a_registration_after_an_unbraced_if_else_that_both_return_fails(self):
        broken = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  if (options) return; else return;\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("after a return" in p for p in problems),
            problems,
        )

    def test_a_registration_after_a_returning_catch_fails(self):
        broken = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  try { throw new Error(\"closed\"); }"
            " catch (e) { return; }\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("after a return" in p for p in problems),
            problems,
        )

    def test_a_registration_after_an_all_returning_switch_fails(self):
        broken = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  switch (options) { case 1: return;"
            " default: return; }\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("after a return" in p for p in problems),
            problems,
        )

    def test_a_registration_after_a_try_that_returns_through_an_empty_catch_fails(self):
        broken = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  try { return; } catch (e) { }\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("after a return" in p for p in problems),
            problems,
        )

    def test_a_registration_in_a_finally_after_a_returning_try_passes(self):
        variant = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  try { return; } finally {\n"
            "    on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "  }\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_a_registration_after_a_comma_ternary_statement_passes(self):
        variant = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  (options ? 1 : 2), on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_a_registration_after_an_unbracketed_comma_passes(self):
        variant = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  options ? 1 : 2, on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_a_catch_handler_rebound_by_destructuring_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "export function register(on, options) {",
            "({ catchSpawnFailure } = { catchSpawnFailure:"
            " ($, e, next) => ({}) });\n"
            "\n"
            "export function register(on, options) {",
            1,
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("returns no deny shape" in p for p in problems),
            problems,
        )

    def test_a_catch_handler_rebound_by_destructuring_to_a_denying_arrow_passes(self):
        text = MODULE.read_text(encoding="utf-8")
        variant = text.replace(
            "export function register(on, options) {",
            "({ catchSpawnFailure } = { catchSpawnFailure:"
            " ($, e, next) => ({ deny: \"recognitio: rebound\""
            " }) });\n"
            "\n"
            "export function register(on, options) {",
            1,
        )
        self.assertNotEqual(variant, text)
        self.assertEqual(self.problems_for(variant), [])

    def test_a_gating_handler_rebound_by_destructuring_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "export function register(on, options) {",
            "({ gateSpawn } = { gateSpawn:"
            " async ($, e, next) => next(e) });\n"
            "\n"
            "export function register(on, options) {",
            1,
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("does not gate on the packet manifest" in p
                for p in problems),
            problems,
        )

    def test_a_catch_handler_returning_a_branch_bound_deny_fails(self):
        broken = self.catch_variant(catch_fn=(
            "function catchSpawnFailure($, e, next) {\n"
            "  let shape = {};\n"
            "  if (e && e.retry) { shape = { deny: \"x\" }; }\n"
            "  return shape;\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("returns no deny shape" in p for p in problems),
            problems,
        )

    def test_a_catch_handler_returning_a_branch_emptied_deny_fails(self):
        broken = self.catch_variant(catch_fn=(
            "function catchSpawnFailure($, e, next) {\n"
            "  let shape = { deny: \"x\" };\n"
            "  if (e && e.retry) { shape = {}; }\n"
            "  return shape;\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("returns no deny shape" in p for p in problems),
            problems,
        )

    def test_a_catch_handler_returning_a_name_rebound_in_register_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        shipped_catch = (
            "function catchSpawnFailure($, e, next) {\n"
            "  return {\n"
            "    deny: \"recognitio: the packet gate hook failed, "
            "so this review spawn is denied rather than let through\",\n"
            "  };\n"
            "}"
        )
        self.assertIn(shipped_catch, text)
        broken = text.replace(shipped_catch, (
            "let shape = { deny: \"recognitio: denied\" };\n"
            "\n"
            "function catchSpawnFailure($, e, next) {\n"
            "  return shape;\n"
            "}"
        )).replace(
            "export function register(on, options) {\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}",
            "export function register(on, options) {\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "  shape = {};\n"
            "}\n"
            "\n"
            "function neverCalled() {\n"
            "  shape = { deny: \"recognitio: late\" };\n"
            "}",
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("returns no deny shape" in p for p in problems),
            problems,
        )

    def test_a_gating_handler_naming_the_calls_in_a_string_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = self.gate_variant((
            "async function gateSpawn($, e, next) {\n"
            "  const spellings = \"$.env.get( $.fs.read(\";\n"
            "  return { deny: \"recognitio: denied\" };\n"
            "}"
        ))
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("does not gate on the packet manifest" in p
                for p in problems),
            problems,
        )

    def test_a_gating_handler_naming_the_calls_in_a_template_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = self.gate_variant((
            "async function gateSpawn($, e, next) {\n"
            "  const spellings = `$.env.get( $.fs.read(`;\n"
            "  return { deny: \"recognitio: denied\" };\n"
            "}"
        ))
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("does not gate on the packet manifest" in p
                for p in problems),
            problems,
        )

    def test_a_gating_handler_with_calls_only_in_an_uncalled_nested_function_fails(self):
        broken = self.gate_variant((
            "async function gateSpawn($, e, next) {\n"
            "  function innerEnv() {\n"
            "    return $.env.get(\"RECOGNITIO_PACKET_DIR\");\n"
            "  }\n"
            "  function innerRead() {\n"
            "    return $.fs.read(\"manifest.json\");\n"
            "  }\n"
            "  return { deny: \"recognitio: denied\" };\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("does not gate on the packet manifest" in p
                for p in problems),
            problems,
        )

    def test_a_gating_handler_with_a_fake_declaration_before_a_group_fails(self):
        broken = self.gate_variant((
            "async function gateSpawn($, e, next) {\n"
            "  function innerEnv() {\n"
            "    return $.env.get(\"RECOGNITIO_PACKET_DIR\");\n"
            "  }\n"
            "  (0);\n"
            "  function innerRead() {\n"
            "    return $.fs.read(\"manifest.json\");\n"
            "  }\n"
            "  return { deny: \"recognitio: denied\" };\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("does not gate on the packet manifest" in p
                for p in problems),
            problems,
        )

    def test_a_gating_call_inside_an_immediately_invoked_function_passes(self):
        variant = self.gate_variant((
            "async function gateSpawn($, e, next) {\n"
            "  const packetDir = await (() => $.env.get("
            "\"RECOGNITIO_PACKET_DIR\"))();\n"
            "  if (typeof packetDir !== \"string\""
            " || packetDir.length === 0) {\n"
            "    return next(e);\n"
            "  }\n"
            "  if (await packetIsVerified($, packetDir)) {\n"
            "    return next(e);\n"
            "  }\n"
            "  return {\n"
            "    deny: \"recognitio: the review packet manifest"
            " is not verified, so this review spawn is denied\",\n"
            "  };\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_a_gating_read_standing_in_a_catch_block_passes(self):
        text = MODULE.read_text(encoding="utf-8")
        variant = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "let text;\n"
            "  try { throw new Error(\"x\"); }"
            " catch (o) { text = await $.fs.read(manifestPath); }",
        )
        self.assertNotEqual(variant, text)
        self.assertEqual(self.problems_for(variant), [])

    def test_a_registration_after_a_labelled_block_that_returns_fails(self):
        variant = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  out: { return; }\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}"
        ))
        problems = self.problems_for(variant)
        self.assertTrue(
            any("stands after a return" in p for p in problems),
            problems,
        )

    def test_a_registration_after_a_labelled_throw_fails(self):
        variant = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  out: throw new Error(\"x\");\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}"
        ))
        problems = self.problems_for(variant)
        self.assertTrue(
            any("stands after a return" in p for p in problems),
            problems,
        )

    def test_a_registration_after_a_labelled_if_that_returns_fails(self):
        variant = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  out: if (options) { return; }"
            " else { return; }\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}"
        ))
        problems = self.problems_for(variant)
        self.assertTrue(
            any("stands after a return" in p for p in problems),
            problems,
        )

    def test_a_registration_after_a_labelled_block_that_falls_is_refused_as_outside_the_family(self):
        # The narrowed contract of the lane 8 decision. This
        # shape stood priced as a pass while the gate claimed
        # to judge every module, and the lane 8 repair red
        # team proved the label reading certifies a catch
        # handler that returns nothing, so a labelled
        # statement now stands outside the structural family
        # and the gate refuses the module for carrying one.
        variant = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  out: { options.touched = true; }\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}"
        ))
        problems = self.problems_for(variant)
        self.assertTrue(
            any("labelled statement" in p
                and "structural family" in p for p in problems),
            problems,
        )

    def test_a_deny_bound_only_after_a_labelled_return_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        variant = text.replace(
            "export function register(on, options) {",
            "let shape = {};\n"
            "export function register(on, options) {\n"
            "  out: { return; }\n"
            "  shape = { deny: \"x\" };",
        ).replace(
            "function catchSpawnFailure($, e, next) {\n"
            "  return {\n"
            "    deny: \"recognitio: the packet gate hook"
            " failed, so this review spawn is denied rather"
            " than let through\",\n"
            "  };\n"
            "}",
            "function catchSpawnFailure($, e, next) {\n"
            "  return shape;\n"
            "}",
        )
        self.assertNotEqual(variant, text)
        problems = self.problems_for(variant)
        self.assertTrue(
            any("returns no deny shape" in p for p in problems),
            problems,
        )

    def test_a_catch_handler_rebound_before_its_declaration_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        variant = (
            "catchSpawnFailure = ($, e, next) => ({});\n"
            + text
        )
        problems = self.problems_for(variant)
        self.assertTrue(
            any("returns no deny shape" in p for p in problems),
            problems,
        )

    def test_a_catch_handler_rebound_by_destructuring_at_the_top_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        variant = (
            "({ catchSpawnFailure } = { catchSpawnFailure:"
            " ($, e, next) => ({}) });\n"
            + text
        )
        problems = self.problems_for(variant)
        self.assertTrue(
            any("returns no deny shape" in p for p in problems),
            problems,
        )

    def test_a_gating_handler_rebound_before_its_declaration_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        variant = (
            "gateSpawn = async ($, e, next) => next(e);\n"
            + text
        )
        problems = self.problems_for(variant)
        self.assertTrue(
            any("does not gate on the packet manifest" in p
                for p in problems),
            problems,
        )

    def test_a_gating_handler_shadowed_by_a_later_declarator_fails(self):
        variant = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  let dummy = 0, { gateSpawn } = { gateSpawn:"
            " ($, e, next) => next(e) };\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}"
        ))
        problems = self.problems_for(variant)
        self.assertTrue(
            any("does not gate on the packet manifest" in p
                for p in problems),
            problems,
        )

    def test_a_catch_handler_shadowed_by_a_later_declarator_fails(self):
        variant = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  let dummy = 0, { catchSpawnFailure } ="
            " { catchSpawnFailure: ($, e, next) => ({}) };\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}"
        ))
        problems = self.problems_for(variant)
        self.assertTrue(
            any("returns no deny shape" in p for p in problems),
            problems,
        )

    def test_a_deny_name_the_gating_handler_rebinds_fails(self):
        variant = self.catch_variant(catch_fn=(
            "function catchSpawnFailure($, e, next) {\n"
            "  return shape;\n"
            "}"
        ))
        variant = "let shape = { deny: \"x\" };\n" + variant
        variant = variant.replace(
            "async function gateSpawn($, e, next) {",
            "async function gateSpawn($, e, next) {\n"
            "  shape = {};",
        )
        problems = self.problems_for(variant)
        self.assertTrue(
            any("returns no deny shape" in p for p in problems),
            problems,
        )

    def test_a_deny_name_a_helper_of_the_catch_handler_rebinds_fails(self):
        variant = self.catch_variant(catch_fn=(
            "function catchSpawnFailure($, e, next) {\n"
            "  function inner() { shape = {}; }\n"
            "  inner();\n"
            "  return shape;\n"
            "}"
        ))
        variant = "let shape = { deny: \"x\" };\n" + variant
        problems = self.problems_for(variant)
        self.assertTrue(
            any("returns no deny shape" in p for p in problems),
            problems,
        )

    def test_a_gating_helper_called_only_on_a_branch_fails(self):
        variant = self.gate_variant((
            "async function gateSpawn($, e, next) {\n"
            "  if (e && e.special) {\n"
            "    return helperGate($, e, next);\n"
            "  }\n"
            "  return next(e);\n"
            "}"
        ))
        variant = variant.replace(
            "function catchSpawnFailure",
            "async function helperGate($, e, next) {\n"
            "  const packetDir = await $.env.get("
            "\"RECOGNITIO_PACKET_DIR\");\n"
            "  if (typeof packetDir !== \"string\""
            " || packetDir.length === 0) {\n"
            "    return next(e);\n"
            "  }\n"
            "  if (await packetIsVerified($, packetDir)) {\n"
            "    return next(e);\n"
            "  }\n"
            "  return {\n"
            "    deny: \"recognitio: the review packet manifest"
            " is not verified, so this review spawn is denied\",\n"
            "  };\n"
            "}\n"
            "\n"
            "function catchSpawnFailure",
            1,
        )
        problems = self.problems_for(variant)
        self.assertTrue(
            any("does not gate on the packet manifest" in p
                for p in problems),
            problems,
        )

    def test_a_gating_helper_whose_reads_stand_after_its_return_fails(self):
        variant = self.gate_variant((
            "async function gateSpawn($, e, next) {\n"
            "  return deadGate($, e, next);\n"
            "}"
        ))
        variant = variant.replace(
            "function catchSpawnFailure",
            "async function deadGate($, e, next) {\n"
            "  if (e && e.known) {\n"
            "    return { deny: \"recognitio: denied\" };\n"
            "  }\n"
            "  return next(e);\n"
            "  const packetDir = await $.env.get("
            "\"RECOGNITIO_PACKET_DIR\");\n"
            "  return $.fs.read(packetDir);\n"
            "}\n"
            "\n"
            "function catchSpawnFailure",
            1,
        )
        problems = self.problems_for(variant)
        self.assertTrue(
            any("does not gate on the packet manifest" in p
                for p in problems),
            problems,
        )

    def test_a_catch_handler_returning_a_nullish_fallback_passes(self):
        variant = self.catch_variant(catch_fn=(
            "function catchSpawnFailure($, e, next) {\n"
            "  return DENY_SHAPE ?? next(e);\n"
            "}\n"
            "const DENY_SHAPE = { deny: \"x\" };"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_a_catch_handler_returning_its_catch_binding_passes(self):
        variant = self.catch_variant(catch_fn=(
            "function catchSpawnFailure($, e, next) {\n"
            "  try {\n"
            "    throw { deny: \"x\" };\n"
            "  } catch (shape) {\n"
            "    return shape;\n"
            "  }\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_a_two_level_delegated_gating_handler_passes(self):
        text = MODULE.read_text(encoding="utf-8")
        variant = self.gate_variant((
            "async function gateSpawn($, e, next) {\n"
            "  return midGate($, e, next);\n"
            "}\n"
            "\n"
            "async function midGate($, e, next) {\n"
            "  return realGate($, e, next);\n"
            "}\n"
            "\n"
            "async function realGate($, e, next) {\n"
            "  const packetDir = await $.env.get("
            "\"RECOGNITIO_PACKET_DIR\");\n"
            "  if (typeof packetDir !== \"string\""
            " || packetDir.length === 0) {\n"
            "    return next(e);\n"
            "  }\n"
            "  if (await packetIsVerified($, packetDir)) {\n"
            "    return next(e);\n"
            "  }\n"
            "  return {\n"
            "    deny: \"recognitio: the review packet manifest"
            " is not verified, so this review spawn is denied\",\n"
            "  };\n"
            "}"
        ))
        self.assertNotEqual(variant, text)
        self.assertEqual(self.problems_for(variant), [])

    def test_a_catch_handler_returning_a_deny_on_the_next_line_fails(self):
        broken = self.catch_variant(catch_fn=(
            "function catchSpawnFailure($, e, next) {\n"
            "  return\n"
            "  { deny: \"recognitio: denied\" };\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("returns no deny shape" in p for p in problems),
            problems,
        )

    def test_a_catch_handler_returning_a_two_level_helper_result_passes(self):
        variant = self.catch_variant(catch_fn=(
            "function innerDeny() {\n"
            "  return { deny: \"recognitio: inner\" };\n"
            "}\n"
            "\n"
            "function outerDeny() {\n"
            "  return innerDeny();\n"
            "}\n"
            "\n"
            "function catchSpawnFailure($, e, next) {\n"
            "  return outerDeny();\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_a_deny_under_a_computed_key_spelled_by_interpolation_passes(self):
        variant = self.catch_variant(catch_fn=(
            "function catchSpawnFailure($, e, next) {\n"
            "  return { [`de${\"ny\"}`]: \"recognitio: denied\" };\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_a_deny_under_a_wholly_interpolated_computed_key_passes(self):
        variant = self.catch_variant(catch_fn=(
            "function catchSpawnFailure($, e, next) {\n"
            "  return { [`${\"deny\"}`]: \"recognitio: denied\" };\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_a_catch_handler_returning_a_deny_or_a_pass_through_passes(self):
        variant = self.catch_variant(catch_fn=(
            "const DENY_SHAPE = { deny: \"recognitio: denied\" };\n"
            "\n"
            "function catchSpawnFailure($, e, next) {\n"
            "  return DENY_SHAPE || next(e);\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_a_catch_handler_that_only_returns_in_an_endless_loop_is_refused_as_outside_the_family(self):
        # The narrowed contract of the lane 8 decision. A
        # loop whose condition reads no state stands outside
        # the family even where its body returns on the
        # first pass, because the same head standing over a
        # body that reaches no break is the second lane 8
        # hole, a certified module whose register function
        # never registers anything, and the census
        # classifies the head without judging the body.
        variant = self.catch_variant(catch_fn=(
            "function catchSpawnFailure($, e, next) {\n"
            "  for (;;) { return { deny: \"recognitio: denied\" }; }\n"
            "}"
        ))
        problems = self.problems_for(variant)
        self.assertTrue(
            any("loop whose condition reads no state" in p
                and "structural family" in p for p in problems),
            problems,
        )

    def test_a_catch_handler_whose_switch_always_returns_the_deny_passes(self):
        variant = self.catch_variant(catch_fn=(
            "function catchSpawnFailure($, e, next) {\n"
            "  switch (e) { case 1: return { deny: \"x\" };"
            " default: return { deny: \"y\" }; }\n"
            "}"
        ))
        self.assertEqual(self.problems_for(variant), [])

    def test_an_options_object_from_a_rest_destructuring_of_a_bound_name_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            "const opts = { path: manifestPath };\n"
            "  const { ...o } = opts;\n"
            "  const text = await $.fs.read(o);",
            1,
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("$.fs.read" in p and "options" in p
                for p in problems),
            problems,
        )

    def test_the_unreadable_catch_sentence_names_no_named_function(self):
        broken = self.catch_variant(register=(
            "export function register(on, options) {\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure.bind(null));\n"
            "}"
        ))
        problems = self.problems_for(broken)
        self.assertTrue(
            any("stands in a form the structural reading "
                "cannot read" in p for p in problems),
            problems,
        )
        self.assertFalse(
            any("cannot be found as a named function" in p
                for p in problems),
            problems,
        )

    # Item 2, colon headed blocks.

    def test_an_escaped_env_bracket_method_behind_a_label_block_fails(self):
        broken = self.door_variant(
            "lblLane6: { }\n/'/.test(\"x\");",
            'await $.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR")',
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_env_bracket_method_behind_a_case_block_fails(self):
        broken = self.door_variant(
            "switch (1) { case 1: { } /'/.test(\"x\"); break; }",
            'await $.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR")',
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_env_bracket_method_behind_a_default_block_fails(self):
        broken = self.door_variant(
            "switch (1) { default: { } /'/.test(\"x\"); break; }",
            'await $.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR")',
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_env_variable_behind_a_case_block_fails(self):
        broken = self.door_variant(
            "switch (1) { case 1: { } /'/.test(\"x\"); break; }",
            'await $.\\u0065nv.get(PACKET_ENV)',
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("not a string literal" in p for p in problems),
            problems,
        )

    def test_an_escaped_fs_bracket_method_behind_a_label_block_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "async function packetIsVerified($, packetDir) {",
            "lblLane6f: { }\n/'/.test(\"x\");\n\n"
            "async function packetIsVerified($, packetDir) {",
            1,
        ).replace(
            "const text = await $.fs.read(manifestPath);",
            'const text = await $.\\u0066s["read"](manifestPath);',
            1,
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_object_after_a_case_value_still_divides(self):
        # The colon of a case value is a value colon where
        # the value is an expression, so the object heading
        # the division chain stands as an operand.
        broken = self.chain_variant(
            "let qCase;\n"
            "switch (1) { case 1: qCase = {a: 1} / "
            '$.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR") / 1; }',
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_the_shared_judgement_reads_colon_constructs(self):
        decode = self.mod.decode_identifier_escapes
        call = '$.\\u0065nv.get("X")'
        for head in (
            "lbl: { } /'/.test(\"x\");\n",
            "switch (1) { case 1: { } /'/.test(\"x\"); break; }\n",
            "switch (1) { default: { } /'/.test(\"x\"); break; }\n",
        ):
            self.assertIn("$.env.get", decode(head + call), head)
        for chain in (
            "const t = {a: {b: 1} / " + call + " / 1};",
            "const t = c ? {a: 1} : {b: 2};\n" + call,
        ):
            self.assertIn("$.env.get", decode(chain), chain)

    # Item 3, the trailing dot number.

    def test_an_escaped_env_bracket_method_behind_a_number_dot_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await (1. / '
            '$.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR") / 1);',
            1,
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_fs_bracket_method_behind_a_number_dot_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            'const text = await (1. / '
            '$.\\u0066s["read"](manifestPath) / 1);',
            1,
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_a_plain_optional_dollar_call_behind_a_number_dot_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await (1. / '
            '$?.("RECOGNITIO_PACKET_DIR") / 1);',
            1,
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("calls $ itself through an optional call" in p
                for p in problems),
            problems,
        )

    def test_number_spellings_in_ordinary_code_pass_the_pin(self):
        variant = self.chain_variant(
            "const qNum1 = 1.5 / 2;\n"
            "const qNum2 = 1..toString();\n"
            "const qNum3 = 1.e3 / 2;\n"
            "const qNum4 = (1.5).toString();"
        )
        self.assertEqual(self.problems_for(variant), [])

    def test_the_shared_judgement_reads_a_trailing_dot_number(self):
        decode = self.mod.decode_identifier_escapes
        call = '$.\\u0065nv.get("X")'
        self.assertIn(
            "$.env.get",
            decode("const q = 1. / " + call + " / 1;"),
        )
        self.assertIn(
            "$.env.get",
            decode("const q = 10 / " + call + " / 1;"),
        )

    # Item 4, function and class expression division heads.

    def test_an_escaped_env_bracket_method_behind_a_function_expression_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await (function () { return 1; } / '
            '$.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR") / 1);',
            1,
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_env_bracket_method_behind_a_class_expression_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            'const packetDir = await $.env.get("RECOGNITIO_PACKET_DIR");',
            'const packetDir = await (class { } / '
            '$.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR") / 1);',
            1,
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_fs_bracket_method_behind_a_function_expression_fails(self):
        text = MODULE.read_text(encoding="utf-8")
        broken = text.replace(
            "const text = await $.fs.read(manifestPath);",
            'const text = await (function () { return 1; } / '
            '$.\\u0066s["read"](manifestPath) / 1);',
            1,
        )
        self.assertNotEqual(broken, text)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_env_bracket_method_behind_an_object_value_function_fails(self):
        broken = self.chain_variant(
            "const oVal = { f: function () { return 1; } / "
            '$.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR") / 1 };',
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_env_bracket_method_behind_an_async_function_expression_fails(self):
        broken = self.chain_variant(
            "const qAsync = (async function () { return 1; } / "
            '$.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR") / 1);',
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_a_correct_literal_behind_a_function_declaration_regex_passes(self):
        variant = self.door_variant(
            "function probeDecl() { return 1; }\n/'/.test(\"x\");",
            'await $.\\u0065nv.get("RECOGNITIO_PACKET_DIR")',
        )
        self.assertEqual(self.problems_for(variant), [])

    def test_a_correct_literal_behind_a_class_declaration_regex_passes(self):
        variant = self.door_variant(
            "class ProbeDecl { }\n/'/.test(\"x\");",
            'await $.\\u0065nv.get("RECOGNITIO_PACKET_DIR")',
        )
        self.assertEqual(self.problems_for(variant), [])

    # Item 5, the return line terminator.

    def test_an_escaped_env_bracket_method_behind_a_return_line_break_fails(self):
        broken = self.door_variant(
            "function probeASI() {\n"
            "  return\n"
            "  { }\n"
            "  /'/.test(\"x\");\n"
            "}",
            'await $.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR")',
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_an_escaped_env_bracket_method_behind_a_return_comment_break_fails(self):
        broken = self.door_variant(
            "function probeASIC() {\n"
            "  return /*\n*/ { }\n"
            "  /'/.test(\"x\");\n"
            "}",
            'await $.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR")',
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    def test_a_correct_literal_behind_a_same_line_return_object_passes(self):
        variant = self.door_variant(
            "function probeSame() { return { }; }\n/'/.test(\"x\");",
            'await $.\\u0065nv.get("RECOGNITIO_PACKET_DIR")',
        )
        self.assertEqual(self.problems_for(variant), [])

    def test_an_escaped_env_bracket_method_behind_a_same_line_return_object_fails(self):
        broken = self.door_variant(
            "function probeSameF() { return {a: 1} / "
            '$.\\u0065nv["get"]("RECOGNITIO_PACKET_DIR") / 1; }',
            'await $.env.get("RECOGNITIO_PACKET_DIR")',
        )
        problems = self.problems_for(broken)
        self.assertTrue(
            any("computed or optional member access" in p
                for p in problems),
            problems,
        )

    # Item 6, template accounting in the auxiliary walks.

    def template_helper_variant(self, name, inner_text, plain=False):
        text = MODULE.read_text(encoding="utf-8")
        if plain:
            template = "`${ {a: 1} }`"
        else:
            template = "`${ {a: `" + inner_text + "`} }`"
        broken = text.replace(
            "async function gateSpawn($, e, next) {",
            "function " + name + "() {\n"
            "  const s = " + template + ";\n"
            "  return { path: \"x\" };\n"
            "}\n\nasync function gateSpawn($, e, next) {",
            1,
        ).replace(
            "const text = await $.fs.read(manifestPath);",
            "const text = await $.fs.read(" + name + "());",
            1,
        )
        self.assertNotEqual(broken, text)
        return broken

    def test_a_helper_return_behind_a_nested_template_close_brace_fails(self):
        broken = self.template_helper_variant("helperTplClose", "}")
        problems = self.problems_for(broken)
        self.assertTrue(
            any("$.fs.read" in p and "options object" in p
                for p in problems),
            problems,
        )

    def test_a_helper_return_behind_a_nested_template_open_brace_fails(self):
        broken = self.template_helper_variant("helperTplOpen", "{")
        problems = self.problems_for(broken)
        self.assertTrue(
            any("$.fs.read" in p and "options object" in p
                for p in problems),
            problems,
        )

    def test_a_helper_return_behind_a_plain_template_still_fails(self):
        broken = self.template_helper_variant(
            "helperTplPlain", "", plain=True)
        problems = self.problems_for(broken)
        self.assertTrue(
            any("$.fs.read" in p and "options object" in p
                for p in problems),
            problems,
        )

    def test_the_auxiliary_walks_read_nested_templates(self):
        code = (
            "function h() { const s = `${ {a: `}`} }`;"
            " return 1; }"
        )
        close = self.mod.matching_close(code, code.index("{"))
        self.assertEqual(close, len(code) - 1)
        args = self.mod.call_arguments(
            "f(`a${`}`}b`, 2)", 1)
        self.assertEqual(len(args), 2)
        self.assertEqual(args[0].strip(), "`a${`}`}b`")

    # Item 7a, the quoted shapes against the allowlist and
    # alien receiver scans.

    def quoted_variant(self, line):
        text = MODULE.read_text(encoding="utf-8")
        variant = text.replace(
            "async function gateSpawn($, e, next) {",
            line + "\n\nasync function gateSpawn($, e, next) {",
            1,
        )
        self.assertNotEqual(variant, text)
        return variant

    def test_a_string_quoting_a_model_call_passes_the_pin(self):
        variant = self.quoted_variant(
            'const qQuote1 = "$.model.complete";')
        self.assertEqual(self.problems_for(variant), [])

    def test_a_string_quoting_an_alien_env_call_passes_the_pin(self):
        variant = self.quoted_variant(
            'const qQuote2 = "x.env.get(\\"RECOGNITIO_PACKET_DIR\\")";')
        self.assertEqual(self.problems_for(variant), [])

    def test_a_template_quoting_an_alien_fs_call_passes_the_pin(self):
        variant = self.quoted_variant(
            "const qQuote3 = `y.fs.read(manifestPath)`;")
        self.assertEqual(self.problems_for(variant), [])

    def test_a_regex_quoting_a_model_call_passes_the_pin(self):
        variant = self.quoted_variant(
            "const qQuote4 = /$.model.complete/;")
        self.assertEqual(self.problems_for(variant), [])

    def test_an_interpolated_model_call_still_fails_the_pin(self):
        broken = self.quoted_variant(
            "const qQuote5 = `${$.model.complete({})}`;")
        problems = self.problems_for(broken)
        self.assertTrue(
            any("$.model.complete" in p for p in problems),
            problems,
        )

    def test_an_interpolated_alien_call_still_fails_the_pin(self):
        broken = self.quoted_variant(
            "const qQuote6 = `${other.fs.read(manifestPath)}`;")
        problems = self.problems_for(broken)
        self.assertTrue(
            any("receiver other than $" in p for p in problems),
            problems,
        )

    # The six lane 8 holes, closed by scoping under the
    # decision that followed the hard stop. Each module
    # below certified with no problems on the lane 8 tree,
    # and node proved the harm the red team report records.
    # The narrowed contract refuses each one as outside the
    # structural family, and each test names the hole it
    # proves closed by that refusal. A gate that drops the
    # family census returns no problem for these modules
    # again, so every test here fails on that revert.

    def test_the_labelled_break_hole_is_refused_as_outside_the_family(self):
        # Lane 8 Major 1. An unlabelled break inside a
        # labelled block in the catch handler's loop leaves
        # the loop, not the label, so the handler returns
        # undefined on the plain drive and the crash drive
        # alike while the gate read it as never falling
        # through. Both members carry a labelled statement.
        for catch_fn in (
            "function catchSpawnFailure($, e, next) {\n"
            "  while (true) {\n"
            "    out: { break; }\n"
            "    return { deny: \"x\" };\n"
            "  }\n"
            "}",
            "function catchSpawnFailure($, e, next) {\n"
            "  while (true) {\n"
            "    out: try { break; } catch (err) { }\n"
            "    return { deny: \"x\" };\n"
            "  }\n"
            "}",
        ):
            variant = self.catch_variant(catch_fn=catch_fn)
            problems = self.problems_for(variant)
            self.assertTrue(
                any("labelled statement" in p
                    and "structural family" in p
                    for p in problems),
                problems,
            )

    def test_the_constant_loop_hole_is_refused_as_outside_the_family(self):
        # Lane 8 Major 2. A registration standing after a
        # loop whose condition reads no state and whose
        # body reaches no break never runs, so the module
        # certified while registering nothing.
        call = (
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
        )
        for body in (
            "  for (;;) { }\n",
            "  while (true) { continue; }\n",
            "  lbl: for (;;) { continue lbl; }\n",
        ):
            variant = self.catch_variant(register=(
                "export function register(on, options) {\n"
                + body + call +
                "}"
            ))
            problems = self.problems_for(variant)
            self.assertTrue(
                any("loop whose condition reads no state" in p
                    and "structural family" in p
                    for p in problems),
                problems,
            )

    def test_the_unterminated_statement_hole_is_refused_as_outside_the_family(self):
        # Lane 8 Major 3. A rebind at the top of the module
        # is the binding in force where a later declaration
        # of the same name is read as a declaration, and a
        # declaration standing after a statement no
        # semicolon ends was not read as one, so the rebind
        # was lost and the shipped handler was judged.
        text = MODULE.read_text(encoding="utf-8")
        for rebind, head in (
            (
                "catchSpawnFailure = ($, e, next) => ({});\n",
                "\nfunction catchSpawnFailure",
            ),
            (
                "gateSpawn = async ($, e, next) => next(e);\n",
                "\nasync function gateSpawn",
            ),
        ):
            broken = rebind + text
            broken = broken.replace(
                head, "\nconst dummyNote = 1" + head)
            self.assertNotEqual(broken, rebind + text)
            problems = self.problems_for(broken)
            self.assertTrue(
                any("no semicolon ends" in p
                    and "structural family" in p
                    for p in problems),
                problems,
            )

    def test_the_block_scoped_handler_hole_is_refused_as_outside_the_family(self):
        # Lane 8 Major 4. A const declaration of a handler
        # name inside a block in the register function
        # hides nothing outside its block, so the call
        # after the block registers the top level binding,
        # while the binding reading judged the block
        # declaration as the register scope binding.
        text = MODULE.read_text(encoding="utf-8")
        gate = text[
            text.index("async function gateSpawn"):
            text.index("function catchSpawnFailure")]
        real_gate = gate.replace(
            "async function gateSpawn",
            "async function gateSpawnReal", 1)
        approving_gate = (
            "async function gateSpawn($, e, next) {\n"
            "  return next(e);\n"
            "}\n\n")
        variant = text.replace(gate, approving_gate + real_gate)
        variant = variant.replace(
            "export function register(on, options) {\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}",
            "export function register(on, options) {\n"
            "  if (options) { const gateSpawn = gateSpawnReal; }\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}",
        )
        self.assertNotEqual(variant, text)
        problems = self.problems_for(variant)
        self.assertTrue(
            any("handler name gateSpawn" in p
                and "structural family" in p for p in problems),
            problems,
        )
        shipped_catch = (
            "function catchSpawnFailure($, e, next) {\n"
            "  return {\n"
            "    deny: \"recognitio: the packet gate hook failed, "
            "so this review spawn is denied rather than let through\",\n"
            "  };\n"
            "}"
        )
        self.assertIn(shipped_catch, text)
        real_catch = shipped_catch.replace(
            "function catchSpawnFailure",
            "function catchSpawnReal", 1)
        empty_catch = (
            "function catchSpawnFailure($, e, next) {\n"
            "  return {};\n"
            "}\n\n")
        variant = text.replace(
            shipped_catch, empty_catch + real_catch)
        variant = variant.replace(
            "export function register(on, options) {\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}",
            "export function register(on, options) {\n"
            "  if (options) {"
            " const catchSpawnFailure = catchSpawnReal; }\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}",
        )
        self.assertNotEqual(variant, text)
        problems = self.problems_for(variant)
        self.assertTrue(
            any("handler name catchSpawnFailure" in p
                and "structural family" in p for p in problems),
            problems,
        )

    def test_the_destructuring_declarator_hole_is_refused_as_outside_the_family(self):
        # Lane 8 Major 5. The destructuring collection
        # stopped its walk at a member named of or in in an
        # earlier declarator, so a destructuring declarator
        # standing after one was never collected and the
        # rebind it carries was never judged.
        call = (
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
        )
        for line in (
            "  let dummy = options.of,"
            " { gateSpawn } = { gateSpawn:"
            " async ($, e, next) => next(e) };\n",
            "  let dummy = options.in,"
            " { gateSpawn } = { gateSpawn:"
            " async ($, e, next) => next(e) };\n",
            "  let dummy = options.of,"
            " { catchSpawnFailure } = { catchSpawnFailure:"
            " ($, e, next) => ({}) };\n",
        ):
            variant = self.catch_variant(register=(
                "export function register(on, options) {\n"
                + line + call +
                "}"
            ))
            problems = self.problems_for(variant)
            self.assertTrue(
                any("destructuring pattern standing after "
                    "the first declarator" in p
                    and "structural family" in p
                    for p in problems),
                problems,
            )

    def test_the_emptied_deny_object_hole_is_refused_as_outside_the_family(self):
        # Lane 8 Major 6. The crash path counted the
        # bindings of the deny name but not the writes
        # through the object it holds, so a gating handler
        # that emptied the deny object left the catch
        # handler answering an empty object on the crash
        # drive. One member deletes the key and the other
        # assigns through an alias of the same object.
        text = MODULE.read_text(encoding="utf-8")
        shipped_catch = (
            "function catchSpawnFailure($, e, next) {\n"
            "  return {\n"
            "    deny: \"recognitio: the packet gate hook failed, "
            "so this review spawn is denied rather than let through\",\n"
            "  };\n"
            "}"
        )
        self.assertIn(shipped_catch, text)
        shape_catch = (
            "let shape = { deny: \"x\" };\n\n"
            "function catchSpawnFailure($, e, next) {\n"
            "  return shape;\n"
            "}"
        )
        env_line = (
            "const packetDir = await "
            "$.env.get(\"RECOGNITIO_PACKET_DIR\");")
        self.assertIn(env_line, text)
        for opening, fragment in (
            ("delete shape.deny;\n  ", "delete operator"),
            (
                "const alias = shape;\n"
                "  alias.deny = undefined;\n  ",
                "assignment through a member",
            ),
        ):
            variant = text.replace(
                env_line, opening + env_line).replace(
                shipped_catch, shape_catch)
            self.assertNotEqual(variant, text)
            problems = self.problems_for(variant)
            self.assertTrue(
                any(fragment in p
                    and "structural family" in p
                    for p in problems),
                problems,
            )

    def test_the_regex_and_member_call_head_holes_are_refused_as_outside_the_family(self):
        # The Option B red team Major 2. A declaration
        # standing after a statement no semicolon ends
        # drew the refusal only for the predecessors the
        # census read, and a regex literal ending the
        # statement, and a member call whose name spells
        # a control word heading its parenthesis, slipped
        # both readings, so the rebind at the top of the
        # module was lost the way the priced hole lost it.
        text = MODULE.read_text(encoding="utf-8")
        for rebind, head, insertion in (
            (
                "catchSpawnFailure = ($, e, next) => ({});\n",
                "\nfunction catchSpawnFailure",
                "\nconst dummyNote = /x/",
            ),
            (
                "gateSpawn = async ($, e, next) => next(e);\n",
                "\nasync function gateSpawn",
                "\nconst dummyNote = /x/",
            ),
            (
                "catchSpawnFailure = ($, e, next) => ({});\n",
                "\nfunction catchSpawnFailure",
                "\nconst dummyObj = { while: (x) => x };\n"
                "dummyObj.while(1)",
            ),
            (
                "gateSpawn = async ($, e, next) => next(e);\n",
                "\nasync function gateSpawn",
                "\nconst dummyObj = { catch: (x) => x };\n"
                "dummyObj.catch(1)",
            ),
        ):
            broken = rebind + text
            broken = broken.replace(head, insertion + head)
            self.assertNotEqual(broken, rebind + text)
            problems = self.problems_for(broken)
            self.assertTrue(
                any("no semicolon ends" in p
                    and "structural family" in p
                    for p in problems),
                problems,
            )

    def test_the_static_block_handler_hole_is_refused_as_outside_the_family(self):
        # The Option B red team Major 3. A class body
        # brace and the static block brace inside it read
        # as object braces to the census, so a const of a
        # handler name inside a static block in the
        # register function stood in no frame the nested
        # reading counts and was judged as the register
        # scope binding, the block scoped hole in a scope
        # the frame kinds could not see.
        text = MODULE.read_text(encoding="utf-8")
        gate = text[
            text.index("async function gateSpawn"):
            text.index("function catchSpawnFailure")]
        real_gate = gate.replace(
            "async function gateSpawn",
            "async function gateSpawnReal", 1)
        approving_gate = (
            "async function gateSpawn($, e, next) {\n"
            "  return next(e);\n"
            "}\n\n")
        shipped_register = (
            "export function register(on, options) {\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}")
        variant = text.replace(gate, approving_gate + real_gate)
        variant = variant.replace(
            shipped_register,
            "export function register(on, options) {\n"
            "  class Dummy { static {"
            " const gateSpawn = gateSpawnReal; } }\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}",
        )
        self.assertNotEqual(variant, text)
        problems = self.problems_for(variant)
        self.assertTrue(
            any("handler name gateSpawn" in p
                and "structural family" in p for p in problems),
            problems,
        )
        shipped_catch = (
            "function catchSpawnFailure($, e, next) {\n"
            "  return {\n"
            "    deny: \"recognitio: the packet gate hook failed, "
            "so this review spawn is denied rather than let through\",\n"
            "  };\n"
            "}"
        )
        self.assertIn(shipped_catch, text)
        real_catch = shipped_catch.replace(
            "function catchSpawnFailure",
            "function catchSpawnReal", 1)
        empty_catch = (
            "function catchSpawnFailure($, e, next) {\n"
            "  return {};\n"
            "}\n\n")
        variant = text.replace(
            shipped_catch, empty_catch + real_catch)
        variant = variant.replace(
            shipped_register,
            "export function register(on, options) {\n"
            "  class Dummy { static {"
            " const catchSpawnFailure = catchSpawnReal; } }\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}",
        )
        self.assertNotEqual(variant, text)
        problems = self.problems_for(variant)
        self.assertTrue(
            any("handler name catchSpawnFailure" in p
                and "structural family" in p for p in problems),
            problems,
        )

    def test_the_in_operator_declarator_hole_is_refused_as_outside_the_family(self):
        # The Option B red team Major 4. The declarator
        # walk stopped at a depth nothing in word in an
        # earlier declarator, and in is an operator there
        # as readily as the for head word the stop was
        # written for, so the destructuring declarator
        # behind it was collected by neither the census
        # nor the gate.
        call = (
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
        )
        line = (
            "  let dummy = \"x\" in options,"
            " { gateSpawn } = { gateSpawn:"
            " async ($, e, next) => next(e) };\n"
        )
        variant = self.catch_variant(register=(
            "export function register(on, options) {\n"
            + line + call +
            "}"
        ))
        problems = self.problems_for(variant)
        self.assertTrue(
            any("destructuring pattern standing after "
                "the first declarator" in p
                and "structural family" in p
                for p in problems),
            problems,
        )

    def test_the_bracket_and_indirect_write_holes_are_refused_as_outside_the_family(self):
        # The Option B red team Major 5. The census named
        # the write channels in their dot spellings, so a
        # deny object emptied through a bracket member, a
        # bracket spelling of a writing call, a member
        # target in a destructuring assignment or a for
        # head, or a call to eval certified while the catch
        # handler answered an empty deny on the crash
        # drive. The Function constructor member stands in
        # the same channel by the closing ruling's own
        # enumeration, a function built from text writing
        # the same way the eval call writes.
        text = MODULE.read_text(encoding="utf-8")
        shipped_catch = (
            "function catchSpawnFailure($, e, next) {\n"
            "  return {\n"
            "    deny: \"recognitio: the packet gate hook failed, "
            "so this review spawn is denied rather than let through\",\n"
            "  };\n"
            "}"
        )
        self.assertIn(shipped_catch, text)
        shape_catch = (
            "let shape = { deny: \"x\" };\n\n"
            "function catchSpawnFailure($, e, next) {\n"
            "  return shape;\n"
            "}"
        )
        env_line = (
            "const packetDir = await "
            "$.env.get(\"RECOGNITIO_PACKET_DIR\");")
        self.assertIn(env_line, text)
        for opening, fragment in (
            ("shape[\"deny\"] = undefined;\n  ",
             "assignment through a member"),
            ("shape[[\"den\"] + \"y\"] = undefined;\n  ",
             "assignment through a member"),
            ("shape[\"deny\"]++;\n  ",
             "step through a member"),
            ("Object[\"assign\"](shape, { deny: undefined });\n  ",
             "call to Object.assign"),
            ("Object[`assign`](shape, { deny: undefined });\n  ",
             "call to Object.assign"),
            ("Reflect[\"set\"](shape, \"deny\", undefined);\n  ",
             "call to Reflect.set"),
            ("({ v: shape.deny } = { v: undefined });\n  ",
             "assignment through a member"),
            ("const [ , shape.deny ] = [undefined, undefined];\n  ",
             "assignment through a member"),
            ("for (shape.deny of [undefined]) { }\n  ",
             "assignment through a member"),
            ("eval(\"shape.deny = undefined\");\n  ",
             "call to eval"),
            ("Function(\"shape.deny = undefined\");\n  ",
             "Function constructor"),
        ):
            variant = text.replace(
                env_line, opening + env_line).replace(
                shipped_catch, shape_catch)
            self.assertNotEqual(variant, text)
            problems = self.problems_for(variant)
            self.assertTrue(
                any(fragment in p
                    and "structural family" in p
                    for p in problems),
                problems,
            )

    def test_the_block_after_a_bare_statement_hole_is_refused_as_outside_the_family(self):
        # The finisher red team Major 1. A standalone
        # block standing after a bare name, a number or
        # an array literal, where the grammar ends the
        # statement before it by insertion, read as an
        # object to the census, so a handler name declared
        # under const inside the block was judged as no
        # block declaration and the binding at the call
        # outside it was misread the way the block scoped
        # hole misread it.
        text = MODULE.read_text(encoding="utf-8")
        gate = text[
            text.index("async function gateSpawn"):
            text.index("function catchSpawnFailure")]
        real_gate = gate.replace(
            "async function gateSpawn",
            "async function gateSpawnReal", 1)
        approving_gate = (
            "async function gateSpawn($, e, next) {\n"
            "  return next(e);\n"
            "}\n\n")
        shipped_register = (
            "export function register(on, options) {\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}")
        for bare in ("options", "42", "[1, 2]"):
            variant = text.replace(
                gate, approving_gate + real_gate)
            variant = variant.replace(
                shipped_register,
                "export function register(on, options) {\n"
                "  " + bare + "\n"
                "  { const gateSpawn = gateSpawnReal; }\n"
                "  on(\"agent.spawn\", gateSpawn)"
                ".catch(catchSpawnFailure);\n"
                "}",
            )
            self.assertNotEqual(variant, text)
            problems = self.problems_for(variant)
            self.assertTrue(
                any("handler name gateSpawn" in p
                    and "structural family" in p
                    for p in problems),
                problems,
            )
        # The priced E5 member of the same hole, an eval
        # call standing inside the block the bare
        # statement leaves behind, refused for the eval
        # it carries once the block reads as a block.
        variant = text.replace(
            gate, approving_gate + real_gate)
        variant = variant.replace(
            shipped_register,
            "export function register(on, options) {\n"
            "  options\n"
            "  { eval(\"gateSpawn = gateSpawnReal\"); }\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}",
        )
        self.assertNotEqual(variant, text)
        problems = self.problems_for(variant)
        self.assertTrue(
            any("call to eval" in p
                and "structural family" in p
                for p in problems),
            problems,
        )

    def test_the_second_write_channel_holes_are_refused_as_outside_the_family(self):
        # The finisher red team Major 2. The write
        # channels stood named in their plain spellings,
        # and one step past each stood open, a member
        # target in a for head pattern, the optional
        # member step on a writing call, a parenthesised
        # receiver, a bracket name spelled as a join of
        # literals or through a template hole or a unicode
        # escape, and a grouped eval callee.
        text = MODULE.read_text(encoding="utf-8")
        shipped_catch = (
            "function catchSpawnFailure($, e, next) {\n"
            "  return {\n"
            "    deny: \"recognitio: the packet gate hook failed, "
            "so this review spawn is denied rather than let through\",\n"
            "  };\n"
            "}"
        )
        self.assertIn(shipped_catch, text)
        shape_catch = (
            "let shape = { deny: \"x\" };\n\n"
            "function catchSpawnFailure($, e, next) {\n"
            "  return shape;\n"
            "}"
        )
        env_line = (
            "const packetDir = await "
            "$.env.get(\"RECOGNITIO_PACKET_DIR\");")
        self.assertIn(env_line, text)
        for opening, fragment in (
            ("for ({ v: shape.deny } of [{ v: undefined }]) { }\n  ",
             "assignment through a member"),
            ("for ({ v: shape.deny } in { v: undefined }) { }\n  ",
             "assignment through a member"),
            ("Object?.assign(shape, { deny: undefined });\n  ",
             "call to Object.assign"),
            ("(Object).assign(shape, { deny: undefined });\n  ",
             "call to Object.assign"),
            ("Object[\"ass\" + \"ign\"](shape, { deny: undefined });\n  ",
             "call to Object.assign"),
            ("Object[`ass${\"ign\"}`](shape, { deny: undefined });\n  ",
             "call to Object.assign"),
            ("Object[`\\u0061ssign`](shape, { deny: undefined });\n  ",
             "call to Object.assign"),
            ("Object['\\u0061ssign'](shape, { deny: undefined });\n  ",
             "call to Object.assign"),
            ("Reflect?.set(shape, \"deny\", undefined);\n  ",
             "call to Reflect.set"),
            ("(eval)(\"shape.deny = undefined\");\n  ",
             "call to eval"),
        ):
            variant = text.replace(
                env_line, opening + env_line).replace(
                shipped_catch, shape_catch)
            self.assertNotEqual(variant, text)
            problems = self.problems_for(variant)
            self.assertTrue(
                any(fragment in p
                    and "structural family" in p
                    for p in problems),
                problems,
            )

    def test_the_pattern_discriminator_holes_are_refused_as_outside_the_family(self):
        # The finisher red team Major 2, the members the
        # pattern aware repair itself opened. A pattern
        # target standing in parentheses was read as no
        # target, and a bracket write on an operand whose
        # name the chain reading filed as no operand, the
        # names of, get and async among them, was routed
        # to the pattern reading and never judged.
        text = MODULE.read_text(encoding="utf-8")
        shipped_catch = (
            "function catchSpawnFailure($, e, next) {\n"
            "  return {\n"
            "    deny: \"recognitio: the packet gate hook failed, "
            "so this review spawn is denied rather than let through\",\n"
            "  };\n"
            "}"
        )
        self.assertIn(shipped_catch, text)
        shape_catch = (
            "let shape = { deny: \"x\" };\n\n"
            "function catchSpawnFailure($, e, next) {\n"
            "  return shape;\n"
            "}"
        )
        env_line = (
            "const packetDir = await "
            "$.env.get(\"RECOGNITIO_PACKET_DIR\");")
        self.assertIn(env_line, text)
        for opening in (
            "({ v: (shape.deny) } = { v: undefined });\n  ",
            "([(shape.deny)] = [undefined]);\n  ",
        ):
            variant = text.replace(
                env_line, opening + env_line).replace(
                shipped_catch, shape_catch)
            self.assertNotEqual(variant, text)
            problems = self.problems_for(variant)
            self.assertTrue(
                any("assignment through a member" in p
                    and "structural family" in p
                    for p in problems),
                problems,
            )
        for name in ("of", "get", "async"):
            named_shape = (
                "let %s = { deny: \"x\" };\n\n"
                "function catchSpawnFailure($, e, next) {\n"
                "  return %s;\n"
                "}" % (name, name))
            variant = text.replace(
                env_line,
                "%s[\"deny\"] = undefined;\n  " % name
                + env_line).replace(shipped_catch, named_shape)
            self.assertNotEqual(variant, text)
            problems = self.problems_for(variant)
            self.assertTrue(
                any("assignment through a member" in p
                    and "structural family" in p
                    for p in problems),
                problems,
            )

    def test_a_member_name_after_a_class_field_certifies(self):
        # The finisher red team Minors 2 and 3. A class
        # field need not end with a semicolon, so a method
        # standing after one stands after a token no
        # position list holds, and a field carrying one of
        # the names has no method shape at all, and both
        # were read as the constructs the names spell. A
        # method named Function stood with no exemption
        # where its sibling names carried one.
        text = MODULE.read_text(encoding="utf-8")
        for helper in (
            "\nclass Toolbox {\n"
            "  size = 1\n"
            "  delete() { return 2; }\n"
            "}\n",
            "\nclass Toolbox {\n"
            "  size = other\n"
            "  Proxy() { return 2; }\n"
            "}\n",
            "\nclass Toolbox {\n"
            "  size = other\n"
            "  delete() { return 2; }\n"
            "}\n",
            "\nclass Toolbox {\n"
            "  size = 1\n"
            "  eval() { return 2; }\n"
            "}\n",
            "\nclass Toolcase { delete = 1; }\n",
            "\nclass Toolcase { Proxy = 1; }\n",
            "\nconst toolbox = { Function() { return 1; } };\n",
            "\nclass Toolbox { Function() { return 1; } }\n",
        ):
            variant = text + helper
            self.assertEqual(self.problems_for(variant), [])

    def test_a_pattern_with_a_hole_and_a_plain_for_pattern_certify(self):
        # The finisher red team Minor 4 and the Minor 1
        # remainder. An array pattern carrying an elision
        # made the gate raise out of its pattern reading
        # instead of returning a verdict, and a plain
        # array pattern standing as a for head target was
        # refused by its own closing bracket. Both shapes
        # stand inside the family and certify.
        text = MODULE.read_text(encoding="utf-8")
        for helper in (
            "\nfunction helper(pair) {\n"
            "  [, b] = pair;\n"
            "  return b;\n"
            "}\n",
            "\nfunction total(pairs) {\n"
            "  let sum = 0;\n"
            "  for ([a, b] of pairs) { sum += a + b; }\n"
            "  return sum;\n"
            "}\n",
        ):
            variant = text + helper
            self.assertEqual(self.problems_for(variant), [])

    def test_the_block_after_a_literal_or_step_hole_is_refused_as_outside_the_family(self):
        # The second finisher red team Major 1. A block
        # standing after a statement ending in a literal
        # or a postfix step read as an object, because
        # the token the walk sees before its brace is the
        # assignment sign the literal hides behind or the
        # step itself, so a handler name declared inside
        # the block escaped the nested reading the way
        # the bare statement members did.
        text = MODULE.read_text(encoding="utf-8")
        gate = text[
            text.index("async function gateSpawn"):
            text.index("function catchSpawnFailure")]
        real_gate = gate.replace(
            "async function gateSpawn",
            "async function gateSpawnReal", 1)
        approving_gate = (
            "async function gateSpawn($, e, next) {\n"
            "  return next(e);\n"
            "}\n\n")
        shipped_register = (
            "export function register(on, options) {\n"
            "  on(\"agent.spawn\", gateSpawn)"
            ".catch(catchSpawnFailure);\n"
            "}")
        for bare in (
            "const dummyNote = \"x\"",
            "const dummyNote = /x/",
            "const dummyNote = `x`",
            "options++",
        ):
            variant = text.replace(
                gate, approving_gate + real_gate)
            variant = variant.replace(
                shipped_register,
                "export function register(on, options) {\n"
                "  " + bare + "\n"
                "  { const gateSpawn = gateSpawnReal; }\n"
                "  on(\"agent.spawn\", gateSpawn)"
                ".catch(catchSpawnFailure);\n"
                "}",
            )
            self.assertNotEqual(variant, text)
            problems = self.problems_for(variant)
            self.assertTrue(
                any("handler name gateSpawn" in p
                    and "structural family" in p
                    for p in problems),
                problems,
            )

    def test_the_parenthesised_member_write_holes_are_refused_as_outside_the_family(self):
        # The second finisher red team Major 2. A member
        # target standing in parentheses was invisible to
        # every write reading, because each judges a
        # target by the token behind the assignment or
        # the step and that token was the closing
        # parenthesis of the group.
        text = MODULE.read_text(encoding="utf-8")
        shipped_catch = (
            "function catchSpawnFailure($, e, next) {\n"
            "  return {\n"
            "    deny: \"recognitio: the packet gate hook failed, "
            "so this review spawn is denied rather than let through\",\n"
            "  };\n"
            "}"
        )
        self.assertIn(shipped_catch, text)
        shape_catch = (
            "let shape = { deny: \"x\" };\n\n"
            "function catchSpawnFailure($, e, next) {\n"
            "  return shape;\n"
            "}"
        )
        env_line = (
            "const packetDir = await "
            "$.env.get(\"RECOGNITIO_PACKET_DIR\");")
        self.assertIn(env_line, text)
        for opening, fragment in (
            ("(shape.deny) = undefined;\n  ",
             "assignment through a member"),
            ("((shape.deny)) = undefined;\n  ",
             "assignment through a member"),
            ("(shape[\"deny\"]) = undefined;\n  ",
             "assignment through a member"),
            ("(shape.deny)++;\n  ",
             "step through a member"),
            ("++(shape.deny);\n  ",
             "step through a member"),
            ("for ((shape.deny) of [undefined]) { }\n  ",
             "assignment through a member"),
        ):
            variant = text.replace(
                env_line, opening + env_line).replace(
                shipped_catch, shape_catch)
            self.assertNotEqual(variant, text)
            problems = self.problems_for(variant)
            self.assertTrue(
                any(fragment in p
                    and "structural family" in p
                    for p in problems),
                problems,
            )

    def test_the_grouped_receiver_and_callee_holes_are_refused_as_outside_the_family(self):
        # The second finisher red team Majors 3 and 4.
        # The write calls and the eval call stood named
        # behind one pair of parentheses, and each
        # reading unwrapped exactly one pair or none, and
        # an eval call followed by a block matched the
        # method definition shape in a frame no method
        # can stand in.
        text = MODULE.read_text(encoding="utf-8")
        shipped_catch = (
            "function catchSpawnFailure($, e, next) {\n"
            "  return {\n"
            "    deny: \"recognitio: the packet gate hook failed, "
            "so this review spawn is denied rather than let through\",\n"
            "  };\n"
            "}"
        )
        self.assertIn(shipped_catch, text)
        shape_catch = (
            "let shape = { deny: \"x\" };\n\n"
            "function catchSpawnFailure($, e, next) {\n"
            "  return shape;\n"
            "}"
        )
        env_line = (
            "const packetDir = await "
            "$.env.get(\"RECOGNITIO_PACKET_DIR\");")
        self.assertIn(env_line, text)
        for opening, fragment in (
            ("((Object)).assign(shape, { deny: undefined });\n  ",
             "call to Object.assign"),
            ("((Object))[\"assign\"](shape, { deny: undefined });\n  ",
             "call to Object.assign"),
            ("Object?.[\"assign\"](shape, { deny: undefined });\n  ",
             "call to Object.assign"),
            ("Reflect?.[\"set\"](shape, \"deny\", undefined);\n  ",
             "call to Reflect.set"),
            ("Object.assign?.(shape, { deny: undefined });\n  ",
             "call to Object.assign"),
            ("Object[\"assign\"]?.(shape, { deny: undefined });\n  ",
             "call to Object.assign"),
            ("Object[(\"ass\") + \"ign\"](shape, { deny: undefined });\n  ",
             "call to Object.assign"),
            ("Object[`ass${(\"ign\")}`](shape, { deny: undefined });\n  ",
             "call to Object.assign"),
            ("((eval))(\"shape.deny = undefined\");\n  ",
             "call to eval"),
            ("eval(\"shape.deny = undefined\"); { }\n  ",
             "call to eval"),
        ):
            variant = text.replace(
                env_line, opening + env_line).replace(
                shipped_catch, shape_catch)
            self.assertNotEqual(variant, text)
            problems = self.problems_for(variant)
            self.assertTrue(
                any(fragment in p
                    and "structural family" in p
                    for p in problems),
                problems,
            )

    def test_a_member_name_at_a_class_boundary_certifies(self):
        # The second finisher red team Minors 1 and 2. A
        # method named while standing after a class field
        # was read as a loop head, because the loop guard
        # read the previous token the way its sibling
        # names once did, and a bare class field named
        # delete or Proxy standing before another class
        # element was read as the construct, because the
        # field exemption named only the endings.
        text = MODULE.read_text(encoding="utf-8")
        for helper in (
            "\nclass Toolbox {\n"
            "  size = 1\n"
            "  while() { return 2; }\n"
            "}\n",
            "\nclass Toolbox {\n"
            "  size = \"x\"\n"
            "  while() { return 2; }\n"
            "}\n",
            "\nclass Toolbox {\n"
            "  size = 1\n"
            "  Function() { return 2; }\n"
            "}\n",
            "\nclass Toolbox {\n"
            "  delete\n"
            "  fine() { return 1; }\n"
            "}\n",
            "\nclass Toolbox {\n"
            "  Proxy\n"
            "  other = 1;\n"
            "}\n",
        ):
            variant = text + helper
            self.assertEqual(self.problems_for(variant), [])

    def test_the_handler_name_inside_brackets_hole_is_refused_as_outside_the_family(self):
        # The third finisher red team Major 1, the part
        # of it five reconstructions could verify. A
        # handler name standing alone inside brackets, as
        # the key of a computed member step or an element
        # of an array, was judged by no reading, where the
        # shipped module names its handlers only as
        # declarations and as the plain arguments of its
        # calls. The reconstructions of the wider claim
        # stood refused by the registration and census
        # readings as they stand, and the record of that
        # stands in the lane 8 report's decision section.
        text = MODULE.read_text(encoding="utf-8")
        for helper in (
            "\nfunction pickHandler(table) {\n"
            "  return table[gateSpawn];\n"
            "}\n",
            "\nfunction pickHandlers() {\n"
            "  return [catchSpawnFailure];\n"
            "}\n",
        ):
            variant = text + helper
            problems = self.problems_for(variant)
            self.assertTrue(
                any("standing alone inside brackets" in p
                    and "structural family" in p
                    for p in problems),
                problems,
            )

    def test_a_method_named_delete_or_proxy_certifies(self):
        # The Option B red team Minor. A method named
        # delete is not the delete operator, and a method
        # named Proxy is not the Proxy constructor, and
        # the census refused both spellings for the names
        # alone, in member positions its position reading
        # did not cover.
        text = MODULE.read_text(encoding="utf-8")
        for helper in (
            "\nclass Toolbox {\n"
            "  fine() { return 1; }\n"
            "  delete() { return 2; }\n"
            "}\n",
            "\nconst toolbox = { get delete() { return 1; } };\n",
            "\nconst toolcase = { Proxy() { return 1; } };\n",
        ):
            variant = text + helper
            self.assertEqual(self.problems_for(variant), [])


if __name__ == "__main__":
    unittest.main()
