#!/usr/bin/env python3
"""Pin the Build 7 mod contract deterministically.

The mod lives under hooks/ beside the portable core. This script
checks the mod's structural contract without a Claude Code host.
The hooks/hooks.json module list must name exactly the shipped
hooks module. The module must register its agent.spawn hook with
a string literal event name, must carry a .catch handler that
returns the deny shape, must never use the struck onFailure
language or the withdrawn --mod flag, and must call no mods API
beyond the allowlist, so no model judgment can replace the
deterministic manifest check. The mod brief at docs/mod-build7.md
must state the second layer fail open as a limit, the in session
gating boundary, the deployment gate check, and the unset
disable-model-invocation. At least one *.test.ts file must exist
for the host side test story.

The mod also ships as its own entry in the Claude marketplace
listing, sourced from the plugin folder at
plugins/recognitio-mod. That folder carries byte identical
copies of every file under hooks/ and of the root LICENSE,
and this gate pins the copies to the originals by directory
listing and by bytes, so the installed mod can never drift
from the module this gate certifies.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOKS_JSON = ROOT / "hooks" / "hooks.json"
BRIEF = ROOT / "docs" / "mod-build7.md"
MOD_PLUGIN_DIR = ROOT / "plugins" / "recognitio-mod"
MOD_PLUGIN_HOOKS = MOD_PLUGIN_DIR / "hooks"

ALLOWED_API_CALLS = {"$.fs.read", "$.env.get"}

LIMIT_SENTENCE = (
    "If the catch handler itself throws or times out, the host "
    "skips the hook as if it had no handler and the spawn proceeds"
)
BOUNDARY_SENTENCE = "The hook sees only in session agent spawns"
GATE_CHECK = "claude plugin validate --json"
FLAG_RECONCILIATION = "leaves `disable-model-invocation` at its default"


class DuplicateKeyError(ValueError):
    """A JSON object names one key twice."""


def strict_json_loads(text):
    """Parse JSON refusing a repeated key, like the other gates."""
    def reject(pairs):
        seen = {}
        for key, value in pairs:
            if key in seen:
                raise DuplicateKeyError("repeated key %r" % key)
            seen[key] = value
        return seen
    return json.loads(text, object_pairs_hook=reject)


def module_path():
    """The hooks module hooks/hooks.json names, or a problem."""
    try:
        data = strict_json_loads(HOOKS_JSON.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, "cannot read hooks/hooks.json: %s" % exc
    except (json.JSONDecodeError, DuplicateKeyError) as exc:
        return None, "hooks/hooks.json does not parse: %s" % exc
    modules = data.get("modules")
    if not isinstance(modules, list) or len(modules) != 1 \
            or not isinstance(modules[0], str):
        return None, "hooks/hooks.json names no single hooks module"
    path = (HOOKS_JSON.parent / modules[0]).resolve()
    try:
        path.relative_to((ROOT / "hooks").resolve())
    except ValueError:
        return None, "the hooks module %r is outside hooks/" % modules[0]
    if not path.is_file():
        return None, "the hooks module %r does not exist" % modules[0]
    return path, None


def catch_body(source):
    """The body of the .catch handler, found by brace matching."""
    match = re.search(r"\.catch\(\s*([A-Za-z_][\w]*)", source)
    if not match:
        return None
    name = match.group(1)
    decl = re.search(
        r"function\s+" + re.escape(name) + r"\s*\([^)]*\)\s*\{", source
    )
    if not decl:
        return None
    depth = 0
    for index in range(decl.end() - 1, len(source)):
        char = source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[decl.end():index]
    return None


def module_problems(path):
    """Problems with the hooks module source."""
    problems = []
    source = path.read_text(encoding="utf-8")
    if "on('agent.spawn'" not in source \
            and 'on("agent.spawn"' not in source:
        problems.append(
            "the hooks module registers no agent.spawn hook with a "
            "string literal event name"
        )
    if ".catch(" not in source:
        problems.append(
            "the agent.spawn hook carries no .catch handler, so a "
            "hook crash would fail open"
        )
    else:
        body = catch_body(source)
        if body is None:
            problems.append(
                "the .catch handler cannot be found as a named function"
            )
        elif "deny" not in body:
            problems.append(
                "the .catch handler returns no deny shape, so a hook "
                "crash would not fail closed"
            )
    if "onFailure" in source:
        problems.append(
            "the hooks module uses the struck onFailure language, a "
            "category error on the Mods surface"
        )
    if "--mod" in source:
        problems.append(
            "the hooks module uses the withdrawn --mod flag"
        )
    if "disable-model-invocation" in source:
        problems.append(
            "the hooks module touches disable-model-invocation, which "
            "stays at its default false"
        )
    calls = re.findall(r"\$\.[A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)?", source)
    for call in sorted(set(calls)):
        if call not in ALLOWED_API_CALLS:
            problems.append(
                "the hooks module calls %s, outside the allowlist, so "
                "a model judgment could replace the deterministic check"
                % call
            )
    return problems


def brief_problems():
    """Problems with the mod brief's stated contract."""
    problems = []
    try:
        raw = BRIEF.read_text(encoding="utf-8")
    except OSError as exc:
        return ["cannot read docs/mod-build7.md: %s" % exc]
    text = re.sub(r"\s+", " ", raw)
    for sentence, label in (
        (LIMIT_SENTENCE, "the second layer fail open limit"),
        (BOUNDARY_SENTENCE, "the in session gating boundary"),
        (GATE_CHECK, "the deployment gate check"),
        (FLAG_RECONCILIATION, "the disable-model-invocation reconciliation"),
        (
            "offers the mod as its own marketplace entry, "
            "named recognitio-mod",
            "the marketplace entry",
        ),
    ):
        if sentence not in text:
            problems.append(
                "docs/mod-build7.md does not state %s" % label
            )
    if "is struck from this brief as a category error" not in text:
        problems.append(
            "docs/mod-build7.md does not strike the onFailure language"
        )
    if "onFailure block mode" in text or "onFailure: " in text:
        problems.append(
            "docs/mod-build7.md presents onFailure as a mod mechanism"
        )
    return problems


def test_story_problems():
    """Problems with the host side test story."""
    tests = sorted((ROOT / "hooks").glob("*.test.ts"))
    if not tests:
        return ["hooks/ holds no *.test.ts file for claude plugin test"]
    return []


def plugin_copy_problems():
    """Problems with the marketplace entry copy of the mod.

    The recognitio-mod plugin folder ships the mod on its own.
    Its hooks folder must hold exactly the files the hooks
    folder at the root holds, each a byte identical copy of
    the original, and its LICENSE must be a byte identical
    copy of the root LICENSE, so the entry can never install
    a module this gate has not certified or stand in a
    folder under different terms.
    """
    problems = []
    hooks_dir = ROOT / "hooks"
    if not hooks_dir.is_dir():
        return ["hooks/ is missing, so the mod has no original"]
    originals = sorted(
        path.name for path in hooks_dir.iterdir() if path.is_file())
    copies = []
    if MOD_PLUGIN_HOOKS.is_dir():
        copies = sorted(
            path.name for path in MOD_PLUGIN_HOOKS.iterdir()
            if path.is_file())
    if copies != originals:
        problems.append(
            "plugins/recognitio-mod/hooks holds %s and hooks "
            "holds %s, so the marketplace copy of the mod does "
            "not mirror the certified module"
            % (copies, originals))
    for name in sorted(set(originals) & set(copies)):
        if (MOD_PLUGIN_HOOKS / name).read_bytes() != \
                (hooks_dir / name).read_bytes():
            problems.append(
                "plugins/recognitio-mod/hooks/%s differs from "
                "hooks/%s, so the marketplace copy of the mod "
                "has drifted from the certified module"
                % (name, name))
    license_copy = MOD_PLUGIN_DIR / "LICENSE"
    if not license_copy.is_file():
        problems.append(
            "plugins/recognitio-mod/LICENSE is missing, so "
            "the mod plugin folder carries no licence of its "
            "own")
    elif license_copy.read_bytes() != (ROOT / "LICENSE").read_bytes():
        problems.append(
            "plugins/recognitio-mod/LICENSE differs from the "
            "root LICENSE, so the mod plugin folder stands "
            "under different terms")
    return problems


def mod_problems(root=None):
    """Every Build 7 mod problem."""
    problems = []
    path, problem = module_path()
    if problem:
        return [problem]
    problems.extend(module_problems(path))
    problems.extend(brief_problems())
    problems.extend(test_story_problems())
    problems.extend(plugin_copy_problems())
    return problems


def main(argv=None):
    problems = mod_problems()
    if problems:
        for problem in problems:
            print("check_mod: %s" % problem, file=sys.stderr)
        return 1
    print("check_mod: the Build 7 mod contract holds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
