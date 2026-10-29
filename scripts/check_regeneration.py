#!/usr/bin/env python3
"""Regenerate every shipped artefact that claims a provenance.

Four artefact classes in this tree present themselves as the
output of a command a reader can run again. The example packet
prints its producing command in the examples index. The six
eval task packets rest on the sources files the eval gate
rebuilds. The proof run packet names a four file fixture. The
brand masters and exports rest on the shipped brand builder,
and every other builder under the docs tree writes outputs a
reader is told to trust. Before this gate no step in the check
reran any of those commands, so an extractor landing could
change the packet framing and every shipped packet rotted in
silence while the whole suite stayed green.

This gate regenerates each class into a temporary directory
and compares the regeneration against the shipped copy. The
comparison each class gets is the strongest one its provenance
honestly supports, and the docstring of each checker below
states the normalisation it applies and the reason for it.
Nothing in this gate writes into the tree it checks. The
gate sets sys.dont_write_bytecode for its own process before
it loads any sibling gate and passes
PYTHONDONTWRITEBYTECODE with a value of 1 in the environment
of every subprocess it spawns, so a run leaves no bytecode
in the checked tree either.

The first class runs the example command the examples index
prints, and only that one command. The printed block is read
out of the index rather than restated here, and the gate
verifies the block against one strict template built from
the block as printed. The template holds the extractor path
token as printed, the exact flag spellings in the printed
order, and one slot for each value the flags carry. The
commit value must be a hex string that resolves to a commit
in the tree. The out value must be the shipped example
folder path exactly. The repo value must be the printed
spelling that denotes the tree root. The line shape stands
checked first, because the block must stand as exactly one
command, with a continuation backslash on every line but
the last and no backslash on the last. The token stream
from the joined text must then match the template slot for
slot. Any extra token, any unknown or shortened flag, any
missing flag, and any token carrying a shell metacharacter
or an expansion character is a named refusal, and no
execution happens for a refused block. The gate verifies
the printed block is exactly the one command it then runs
token for token, and it does not interpret shell syntax,
so a block that uses shell syntax or departs from the
printed shape is refused rather than run.
A block that passes runs as an argument list the gate
builds itself, with no shell anywhere in the run, inside a
scratch checkout, a local clone of the checked tree at its
checked head in a temporary directory. The working folder
is the scratch checkout root, the repo argument is the
scratch checkout root, and the out argument is the
validated relative folder inside the scratch checkout, so
the packet the run produces in the scratch checkout is the
packet that compares against the shipped copy. Before the
pre run delete and before the run, the gate resolves the
example folder path inside the scratch checkout. A symlink
on any path component, or a resolved folder that is not
the literal folder inside the checkout, is a named
refusal, and nothing is deleted for a refused folder. The
same symlink check stands on the checked tree, where the
shipped example folder must stand as a real folder holding
a real packet file and a real manifest file, and the check
walks the packet file path and the manifest file path
themselves as well as the folder path, so a symlink
standing in place of either file is a named refusal in its
own right. The regenerated packet file and manifest file
in the scratch checkout stand under the same rule before
they compare, because a read follows a symlink standing
in their place in the same way. A stale printed command,
or a printed command that cannot reproduce the packet,
therefore fails this gate instead of drifting away from
the gate copy of it. The packet compares
byte for byte. The manifest compares field for field with
the creation time and the command array set aside, because
both record the machine and the moment of the run rather
than the change under review, and with nothing else set
aside, so the base and head and merge base hashes compare
exactly against the real history the extractor runs over.
The printed packet lengths in the examples index and in the
README compare against the shipped packet line count, so
regenerating the packet without restating its length fails
here as well.

The second class rebuilds each eval task through the fixture
builder the eval gate ships and runs the extractor over the
rebuilt range. The rebuilt diff compares byte for byte. The
packet and the manifest compare under a stated normalisation.
The fixture builder hardcodes the subjects base and head and
the author name Eval Fixture, so commit subject lines and
blame author lines rebuild exactly and compare exactly. Only
the commit dates stand unpinned, because the fixture builder
sets no date and each rebuild commits at the moment it runs,
and through the dates the commit hashes cannot be
reproduced. Hashes in full and in short form are set aside,
and token numbers are set aside, and the label of an eval
manifest is set aside whole, and everything else compares
exactly, framing included. A framing change the
normalisation cannot hide fails this class, and a token only
change inside the eval class is the consequential drift this
gate states it cannot see. The same symlink check stands on
the checked tree for this class as well, where each shipped
eval task folder must stand as a real folder holding a real
packet file and a real manifest file and a real diff file
and a real sources file, and the check walks each file path
itself as well as the folder path, so a symlink standing in
place of any of those files is a named refusal in its own
right. The diff file and the sources file stand under the
rule because this class certifies them in the same run, the
diff by a byte for byte comparison against the rebuild and
the sources as the provenance the rebuild runs from, and a
read follows a symlink standing in their place in the same
way it follows one standing in place of the packet.

The third class rebuilds the proof run fixture from the
sources file that stands beside the proof packet and runs the
extractor over the rebuilt range. That sources file pins both
revisions of all four files and the author and the subjects
and the dates of both commits, so its hashes are stable from
run to run and its token numbers are reproducible. Only the
hashes themselves and the manifest creation time and command
array are set aside in the comparison, because the packet
prints the hashes of the rebuilt history while the shipped
packet prints the hashes of the original authoring history.
Blob hashes in the diff index lines compare exactly, because
a blob hash rests on file content alone. The same symlink
check stands on the checked tree for this class as well,
where the shipped proof run folder must stand as a real
folder holding a real packet file and a real manifest file
and a real sources file, and the check walks each file path
itself as well as the folder path, so a symlink standing in
place of any of those files is a named refusal in its own
right. The sources file stands under the rule because this
class reads it as the provenance the fixture rebuilds from,
in the same way it reads the packet and the manifest it
compares against the rebuild.

The fourth class discovers every builder script under the
docs tree, at the top of the tree and at any depth below it,
and runs each one in a temporary copy of its own folder.
Every file a builder creates or changes is an output, and
every output name must stand in the shipped folder beside
the builder. An output that stands in the tree compares byte
for byte. A builder that writes a name the tree does not ship
fails here, which is the assertion that retires a builder in
the same landing that retires its assets. A builder that
deletes a shipped output names that output as a problem. The
run also records every file the builder process opens inside
its folder, and a shipped file standing in the folder subtree
of a builder that the run neither writes nor changes is
reported, because no regeneration will ever refresh it. A
read alone does not refresh a file, so a builder that only
reads a former output does not exempt it. A shipped file
counts as written when the traced run opens it for writing,
or creates it, or deletes it, or renames it, and a shipped
file counts as changed when its digest changes. A touch that
changes only the modification time counts as neither, and a
byte identical regeneration counts because the builder opens
the output for writing even though the digest stands still.
A file the traced run neither writes nor changes still gets
a marker run, in a scratch copy where its bytes stand
replaced by a marker, and it counts as refreshed when that
run restores the shipped bytes. A read or a touch leaves the
marker standing, so neither counts as a refresh, and a write
the trace cannot see, through a child process or through a
native library, restores the marker and so counts. The two
legs apply two different standards for the one word
refreshed, and the difference stands stated here rather than
hidden by the shared word. Under the traced leg a file
counts as refreshed when the traced run opens it for
writing, whatever the written bytes were derived from, so a
builder that copies a file from its own previous bytes in
process passes that leg. Under the marker leg a file counts
only when the run restores its shipped bytes from the
marker bytes standing in their place, so a read, a touch,
and an echo of the marked bytes all fail that leg. A
builder whose output is computed from its own previous
output, as a normaliser that sorts a file in place through
a child process does, is judged by the marker leg when its
writes escape the trace, and sorting marker bytes yields
marker bytes and never the shipped bytes, so such a builder
can never pass that leg. A seed-dependent builder cannot
be told from rot by regeneration and must not be gated by
this class. That shape is a limit of this class, and a
builder of that shape must not be read as rotten on this
evidence alone. The
named set DECLARED_BUILDER_INPUTS in this script declares
the genuine read only inputs, and it holds only the palette
record the brand builder reads and never writes. A Python
file in the subtree is exempt from that last check only when
the run reads it, because an import is a read and code the
run loads is an input, while a Python file the run neither
reads nor writes is reported like any other dropped output.
A subtree that holds another builder is the folder of that
other builder, so files under it are left to that builder
run. The check has one stated limit. It does not run for a
builder standing at the top of the docs tree, because that
builder shares its folder with the whole docs set, and a
file standing there cannot be told apart from the docs the
builder does not own. The same symlink check stands on the
checked tree for this class as well, over the folder subtree
of each builder, so a symlink standing at a component or at
a file inside that subtree is a named refusal before the
builder runs, and the rule covers the outputs a builder
writes and the inputs it reads in the same way, because a
read follows a symlink standing in place of either one. A
subtree that holds another builder is left to that builder
run, and the check does not run for a builder standing at
the top of the docs tree, under the same stated limit as
the dropped file check, so the shipped files of every
builder under that limit must stand as real files in a
real folder for the success line below to certify them.

Running this gate locally needs the builder class
prerequisites standing on the machine beside the Python
standard library this script itself uses. The brand builder
imports CairoSVG and fontTools and reads the Liberation
fonts from the system font paths, and the CI check job
installs all three before it runs the gate. A machine
missing one of them reports the brand builder as failed in
its scratch copy, and the fix is the install and not a
repair to the tree.

Exits nonzero and lists every problem when a class drifts.
"""

import difflib
import hashlib
import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# This gate writes no bytecode into the tree it checks. The
# flag is set before any sibling gate loads below, and the
# child environment carries the same rule to every process
# this gate spawns.
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
EXTRACT = ROOT / ".agents" / "skills" / "recognitio" / "scripts" / "extract.py"
EXAMPLE_EXTRACT_TOKEN = ".agents/skills/recognitio/scripts/extract.py"
EXAMPLE_COMMAND_LINES = 7
EXAMPLE_COMMAND_TOKENS = 8
EXAMPLE_FIXED_TOKENS = {
    0: "python3",
    1: EXAMPLE_EXTRACT_TOKEN,
    2: "--commit",
    4: "--out",
    6: "--repo",
}
SHELL_META_CHARS = frozenset("$`;&|<>*?[]{}\\()")

# The genuine read only builder inputs, named by the path of
# each file from the root of the tree. The brand builder reads
# the palette record beside it and never writes it, and no
# other shipped builder reads a file standing beside it as a
# pure input, so this set holds that one path and no other.
DECLARED_BUILDER_INPUTS = frozenset({"docs/brand/palette.json"})
HASH40 = re.compile(r"\b[0-9a-f]{40}\b")
GIT_SCRUB_VARS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_NAMESPACE",
    "GIT_NO_REPLACE_OBJECTS",
    "GIT_REPLACE_REF_BASE",
)
GIT_DRIVER_ENV_VARS = (
    "GIT_EXTERNAL_DIFF",
    "GIT_DIFF_OPTS",
    "GIT_PAGER",
    "GIT_EXEC_PATH",
)


class DuplicateKeyError(ValueError):
    """A JSON object holds the same key twice."""


def _reject_duplicate_keys(pairs):
    record = {}
    for key, value in pairs:
        if key in record:
            raise DuplicateKeyError("repeated key %r" % (key,))
        record[key] = value
    return record


def strict_json_loads(text):
    return json.loads(text, object_pairs_hook=_reject_duplicate_keys)


def guarded_read_text(path, *args, **kwargs):
    """Read a text file only when it stands as a regular file.

    A path that exists and is not a regular file raises the
    same OSError shape an unreadable file raises, so every
    caller keeps the problem wording it already carries and
    no caller can block opening a FIFO that stands at the
    path. A path that does not exist at all falls through to
    the read itself, so an absent path and a dangling link
    keep the behaviour they have always carried. The test
    follows links, so a link to a regular file still reads
    through and a link to a FIFO refuses.
    """
    if path.exists() and not path.is_file():
        raise OSError("%s is not a regular file" % path)
    return path.read_text(*args, **kwargs)


def guarded_read_bytes(path):
    """Read a file as bytes under the same guard as the text form."""
    if path.exists() and not path.is_file():
        raise OSError("%s is not a regular file" % path)
    return path.read_bytes()


def scrubbed_child_env(extra=None):
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in GIT_SCRUB_VARS
        and key not in GIT_DRIVER_ENV_VARS
        and not key.startswith("GIT_CONFIG")
    }
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if extra:
        env.update(extra)
    return env


def run(argv, cwd=None, env=None, timeout=600):
    child_env = dict(os.environ if env is None else env)
    child_env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        argv,
        cwd=str(cwd) if cwd else None,
        env=child_env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def run_extractor(args, out):
    result = run(
        [sys.executable, str(EXTRACT)] + args + ["--out", str(out)],
        env=scrubbed_child_env(),
        timeout=300,
    )
    return result


def diff_summary(label, shipped_text, rebuilt_text):
    """One problem naming a text drift and its first lines."""
    diff = list(
        difflib.unified_diff(
            shipped_text.splitlines(),
            rebuilt_text.splitlines(),
            lineterm="",
            n=0,
        )
    )
    changed = [
        line
        for line in diff
        if line[:1] in ("+", "-")
        and not line.startswith(("+++", "---"))
    ]
    first = " / ".join(line[:90] for line in changed[:3])
    return (
        "the regenerated %s differs from the shipped copy in "
        "%d lines and the first differences are %s"
        % (label, len(changed), first)
    )


def manifest_copy(data, keep_tokens, exact_hashes=False):
    """A manifest with the run record fields set aside.

    The creation time and the command array record the machine
    and the moment of a run rather than the change a packet
    covers, so both leave the comparison in every class. Hash
    fields become placeholders where a rebuilt history cannot
    carry the original hashes, and they compare exactly where
    the caller runs over real history and passes exact_hashes.
    Token fields become placeholders only where the caller
    states they rest on history the sources do not pin.
    """
    out = json.loads(json.dumps(data))
    out.pop("created_utc", None)
    out.pop("command", None)
    if not exact_hashes:
        for key in ("base", "head", "merge_base"):
            if key in out:
                out[key] = "@hash@"
        if isinstance(out.get("label"), str):
            out["label"] = HASH40.sub("@hash@", out["label"])
    if not keep_tokens and "label" in out:
        # The eval label names the rebuilt range in whatever
        # spelling the original run used, and one shipped task
        # carries a symbolic spelling, so the label of an eval
        # manifest stands outside the comparison entirely.
        out["label"] = "@label@"
    passage = out.get("prior_pull_requests_passage")
    if isinstance(passage, str) and not exact_hashes:
        out["prior_pull_requests_passage"] = HASH40.sub("@hash@", passage)
    if not keep_tokens:
        for tier in (out.get("tiers") or {}).values():
            if isinstance(tier, dict):
                for field in ("estimated_tokens", "emitted_tokens"):
                    if field in tier:
                        tier[field] = "@tokens@"
        budget = out.get("budget")
        if isinstance(budget, dict) and "estimated_tokens" in budget:
            budget["estimated_tokens"] = "@tokens@"
    return out


def manifest_problems(label, shipped, rebuilt, keep_tokens,
                      exact_hashes=False):
    if not isinstance(shipped, dict) or not isinstance(rebuilt, dict):
        return [
            "the manifest of %s does not hold a JSON object" % label
        ]
    left = manifest_copy(shipped, keep_tokens, exact_hashes)
    right = manifest_copy(rebuilt, keep_tokens, exact_hashes)
    if left == right:
        return []
    moved = sorted(
        key for key in set(left) | set(right) if left.get(key) != right.get(key)
    )
    return [
        "the regenerated manifest of %s differs from the shipped "
        "manifest in the fields %s" % (label, ", ".join(moved))
    ]


def load_sibling(name):
    path = ROOT / "scripts" / ("%s.py" % name)
    if path.exists() and not path.is_file():
        raise OSError("%s is not a regular file" % path)
    spec = importlib.util.spec_from_file_location("gate_%s" % name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def printed_example_block(root):
    """Read the producing command block out of the examples index.

    The block comes back exactly as the index prints it, line
    continuations and all, because the strict template check
    below is the judge of whether the block may run at all. A
    missing block is itself a problem, because the printed
    provenance is the claim under test.
    """
    text = guarded_read_text((root / "examples" / "README.md"), encoding="utf-8")
    match = re.search(r"```bash\n(.*?)```", text, re.DOTALL)
    if match is None:
        return None, ["the examples index prints no command block"]
    block = match.group(1)
    if not block.strip():
        return None, ["the examples index prints an empty command block"]
    return block, []


def printed_example_words(block):
    """Split a printed block into the tokens of its joined text.

    The continuation pairs leave the text first, in the same
    way the printed lines join into one command, and the
    split then gives the token stream the template check
    judges. A block the split cannot read gives back no
    words, and a block with no words gives back none either,
    and in both cases the block is not run.
    """
    try:
        words = shlex.split(block.replace("\\\n", ""))
    except ValueError:
        return None
    return words or None


def printed_line_problems(block):
    """Name a printed block that is not one continued command.

    Every line but the last must end with a continuation
    backslash and the last line must carry none. A removed
    backslash breaks the one command into pieces, and a line
    added after the last line is a second command rather
    than a continuation, and both shapes stand refused here
    before any token is read.
    """
    lines = block.splitlines()
    if not lines:
        return ["the printed example command prints no lines"]
    for index, line in enumerate(lines[:-1]):
        if not line.endswith("\\"):
            return [
                "the printed example command line %d carries "
                "no continuation backslash and the block is "
                "not the one printed command, so the block "
                "is not run" % (index + 1)
            ]
    if lines[-1].endswith("\\"):
        return [
            "the printed example command ends with a "
            "continuation backslash and the block is not "
            "the one printed command, so the block is not run"
        ]
    return []


def printed_template_problems(block, root):
    """Check a printed block against the one strict template.

    The template is the printed command itself, token for
    token, with the commit and the out and the repo values
    standing in their printed slots as the only parts that
    vary. Each varying value stands validated in place, the
    commit as a hex string that resolves in the tree, the
    out as the shipped example folder path exactly, and the
    repo as the printed spelling for the tree root. The
    return is the validated values beside the problems, and
    the values stand empty whenever a problem stands.
    """
    line_problems = printed_line_problems(block)
    if line_problems:
        return None, line_problems
    joined = block.replace("\\\n", "")
    for mark in ("'", '"', "\\"):
        if mark in joined:
            return None, [
                "the printed example command carries the "
                "shell character %s outside a continuation "
                "and the gate does not interpret shell "
                "syntax, so the block is not run" % mark
            ]
    words = printed_example_words(block)
    if words is None:
        return None, [
            "the printed example command cannot be split "
            "into words and its tokens cannot be checked "
            "against the printed command template, so the "
            "block is not run"
        ]
    for word in words:
        bad = sorted(set(word) & SHELL_META_CHARS)
        if bad:
            return None, [
                "the printed example command carries the "
                "token %s with the shell character %s and "
                "the gate does not interpret shell syntax, "
                "so the block is not run" % (word, bad[0])
            ]
    for index in sorted(EXAMPLE_FIXED_TOKENS):
        expected = EXAMPLE_FIXED_TOKENS[index]
        if index < len(words) and words[index] != expected:
            return None, [
                "the printed example command carries %s "
                "where the printed command template carries "
                "%s, so the block is not run"
                % (words[index], expected)
            ]
    if len(words) != EXAMPLE_COMMAND_TOKENS:
        return None, [
            "the printed example command carries %d tokens "
            "and not the %d tokens of the printed command "
            "template, so the block is not run"
            % (len(words), EXAMPLE_COMMAND_TOKENS)
        ]
    commit = words[3]
    if re.fullmatch(r"[0-9a-f]+", commit) is None:
        return None, [
            "the printed example command names the commit "
            "value %s and that value is not a hex commit "
            "name, so the block is not run" % commit
        ]
    resolved = run(
        [
            "git", "-C", str(root), "rev-parse", "--verify",
            "--quiet", "%s^{commit}" % commit,
        ],
        env=scrubbed_child_env(),
        timeout=120,
    )
    if resolved.returncode != 0:
        return None, [
            "the printed example command names commit %s "
            "and that commit does not stand in the checked "
            "tree, so the block is not run" % commit
        ]
    out_problems = printed_out_problems(
        [words[5]], "examples/example-packet-%s" % commit
    )
    if out_problems:
        return None, out_problems
    if words[7] != ".":
        return None, [
            "the printed example command carries the repo "
            "value %s and not the tree root spelling of "
            "the printed command template, so the block is "
            "not run" % words[7]
        ]
    lines = block.splitlines()
    if len(lines) != EXAMPLE_COMMAND_LINES:
        return None, [
            "the printed example command runs to %d lines "
            "and not the %d lines of the printed shape, so "
            "the block is not run"
            % (len(lines), EXAMPLE_COMMAND_LINES)
        ]
    values = {"commit": commit, "out": words[5], "repo": words[7]}
    return values, []


def symlink_component(base, rel_folder):
    """Return the first symlink component of a folder path.

    The walk steps through each part of the relative folder
    in turn, so a symlink standing in place of the parent
    folder is found in the same way as a symlink standing
    in place of the folder itself.
    The return is the component path relative to the base,
    or nothing when every component stands real.
    """
    current = Path(base)
    walked = []
    for part in Path(rel_folder).parts:
        current = current / part
        walked.append(part)
        if current.is_symlink():
            return "/".join(walked)
    return None


def checked_symlink_problems(
    root,
    rel_folder,
    label="example",
    file_names=("packet.md", "manifest.json"),
):
    """Name a shipped folder or file behind a link.

    The shipped files of a packet class must be real files
    in a real folder, so a symlink on any component of the
    folder path in the checked tree is a problem in its own
    right, before any regeneration runs. Every file the
    class certifies inside the folder stands under the same
    rule, so the walk runs over each file path as well as
    over the folder path, and a file that does not stand as
    a regular file in the checked tree is a problem in the
    same way. The class label names the class in each
    problem, so the wording states which class and which
    path stand behind the link.
    """
    folder_claim = (
        "the shipped builder files must stand as "
        "real files in a real folder"
        if label == "builder"
        else "the shipped %s packet must be a real "
        "file in a real folder" % label
    )
    component = symlink_component(root, rel_folder)
    if component is not None:
        return [
            "the shipped %s folder %s stands behind "
            "the symlink at %s in the checked tree and %s"
            % (label, rel_folder, component, folder_claim)
        ]
    resolved = (Path(root) / rel_folder).resolve()
    if resolved != Path(root).resolve() / rel_folder:
        return [
            "the shipped %s folder %s resolves "
            "outside its literal folder in the checked "
            "tree and %s" % (label, rel_folder, folder_claim)
        ]
    for name in file_names:
        rel_file = "%s/%s" % (rel_folder, name)
        component = symlink_component(root, rel_file)
        if component is not None:
            return [
                "the shipped %s file %s stands behind "
                "the symlink at %s in the checked tree and "
                "the shipped %s files must stand as "
                "real files in a real folder"
                % (label, rel_file, component, label)
            ]
        resolved_file = (Path(root) / rel_file).resolve()
        if resolved_file != Path(root).resolve() / rel_file:
            return [
                "the shipped %s file %s resolves "
                "outside its literal file in the checked "
                "tree and the shipped %s files must "
                "stand as real files in a real folder"
                % (label, rel_file, label)
            ]
        if not (Path(root) / rel_file).is_file():
            return [
                "the shipped %s file %s does not stand "
                "as a regular file in the checked tree and "
                "the shipped %s files must stand as "
                "real files in a real folder"
                % (label, rel_file, label)
            ]
    return []


def builder_symlink_problems(root, builder, other_folders=()):
    """Name a shipped builder file behind a link.

    The scope is the scope of the dropped file check, the
    folder subtree of the builder with any subtree that
    holds another builder left to that builder run, and a
    builder at the top of the docs tree stands outside the
    check under the same stated limit. Every file in that
    scope stands checked through the checked tree helper
    under the builder label, covering the outputs the
    builder writes and the inputs it reads alike, and a
    symlink standing in place of a folder inside the scope
    is named as well, because the walk does not descend
    through a linked folder to the files standing under it.
    """
    folder = builder.parent
    if folder == root / "docs":
        return []
    rel_folder = folder.relative_to(root).as_posix()
    file_names = []
    folder_names = []
    for dirpath, dirnames, filenames in os.walk(folder):
        rel_dir = Path(dirpath).relative_to(folder).as_posix()
        kept = []
        for name in sorted(dirnames):
            rel = (
                name
                if rel_dir == "."
                else "%s/%s" % (rel_dir, name)
            )
            if any(
                rel == other or rel.startswith(other + "/")
                for other in other_folders
            ):
                continue
            kept.append(name)
            folder_names.append(rel)
        dirnames[:] = kept
        for name in sorted(filenames):
            rel = (
                name
                if rel_dir == "."
                else "%s/%s" % (rel_dir, name)
            )
            file_names.append(rel)
    problems = checked_symlink_problems(
        root,
        rel_folder,
        label="builder",
        file_names=tuple(file_names),
    )
    if problems:
        return problems
    for rel in folder_names:
        if (folder / rel).is_symlink():
            rel_entry = "%s/%s" % (rel_folder, rel)
            return [
                "the shipped builder folder %s stands "
                "behind the symlink at %s in the checked "
                "tree and the shipped builder files must "
                "stand as real files in a real folder"
                % (rel_entry, rel_entry)
            ]
    return []


def scratch_symlink_problems(scratch, rel_folder):
    """Name an example folder path that leaves the scratch.

    The check runs before any delete and before any run, so
    a refused folder loses nothing. A symlink on any path
    component, or a resolved folder that is not the literal
    folder inside the checkout, refuses the run outright.
    The packet file and the manifest file inside the folder
    stand under the same walk, so a link standing in place
    of either file refuses the run in the same way, before
    anything is deleted.
    """
    component = symlink_component(scratch, rel_folder)
    if component is not None:
        return [
            "the example folder %s in the scratch "
            "checkout stands behind the symlink at %s, so "
            "nothing is deleted and the block is not run"
            % (rel_folder, component)
        ]
    resolved = (Path(scratch) / rel_folder).resolve()
    if resolved != Path(scratch).resolve() / rel_folder:
        return [
            "the example folder %s in the scratch "
            "checkout resolves outside its literal folder "
            "inside the checkout, so nothing is deleted "
            "and the block is not run" % rel_folder
        ]
    for name in ("packet.md", "manifest.json"):
        rel_file = "%s/%s" % (rel_folder, name)
        component = symlink_component(scratch, rel_file)
        if component is not None:
            return [
                "the example file %s in the scratch "
                "checkout stands behind the symlink at %s, "
                "so nothing is deleted and the block is "
                "not run" % (rel_file, component)
            ]
        resolved_file = (Path(scratch) / rel_file).resolve()
        if resolved_file != Path(scratch).resolve() / rel_file:
            return [
                "the example file %s in the scratch "
                "checkout resolves outside its literal "
                "file inside the checkout, so nothing is "
                "deleted and the block is not run" % rel_file
            ]
    return []


def printed_out_problems(values, expected):
    """Name every printed out value the run must refuse.

    A printed out value passes only when it is the shipped
    example folder path exactly, spelled relative, with a
    normalisation that does not escape. An absolute value
    lands outside the scratch checkout by construction, a
    value whose normalisation climbs out by dotdot lands
    outside it as well, and a value naming any other folder
    is not the target this class compares. Every failing
    value is a problem that refuses the run, because running
    the block first and reporting the target afterwards
    would let the run write wherever the value names.
    """
    problems = []
    for value in values:
        normalised = os.path.normpath(value)
        if Path(value).is_absolute():
            problems.append(
                "the printed example command writes to the "
                "absolute out target %s and not to the shipped "
                "example folder, so the block is not run" % value
            )
        elif normalised == ".." or normalised.startswith(
            ".." + os.sep
        ):
            problems.append(
                "the printed example command writes to the "
                "out target %s that escapes the scratch "
                "checkout and not to the shipped example "
                "folder, so the block is not run" % value
            )
        elif value != expected:
            problems.append(
                "the printed example command writes to %s and "
                "not to the shipped example folder, so the "
                "block is not run" % value
            )
    return problems


def printed_length_problems(root, packet_lines):
    problems = []
    index_text = guarded_read_text((root / "examples" / "README.md"),
        encoding="utf-8"
    )
    match = re.search(r"Packet length (\d+) lines", index_text)
    if match is None or int(match.group(1)) != packet_lines:
        problems.append(
            "the examples index prints a packet length that is "
            "not the %d lines the shipped packet runs" % packet_lines
        )
    readme = guarded_read_text((root / "README.md"), encoding="utf-8")
    match = re.search(
        r"full packet for this commit runs (\d+) lines", readme
    )
    if match is None or int(match.group(1)) != packet_lines:
        problems.append(
            "the README prints a packet length that is not the "
            "%d lines the shipped packet runs" % packet_lines
        )
    return problems


def example_problems(root):
    problems = []
    try:
        block, parse_problems = printed_example_block(root)
        if parse_problems:
            return parse_problems
        values, template_problems = printed_template_problems(
            block, root
        )
        if template_problems:
            return template_problems
        commit = values["commit"]
        rel_folder = "examples/example-packet-%s" % commit
        folder = root / "examples" / ("example-packet-%s" % commit)
        if not folder.is_dir():
            return [
                "the printed example command names commit %s and no "
                "example folder for that commit stands in the tree"
                % commit
            ]
        link_problems = checked_symlink_problems(root, rel_folder)
        if link_problems:
            return link_problems
        shipped_packet = guarded_read_text((folder / "packet.md"), encoding="utf-8")
        problems.extend(
            printed_length_problems(
                root, len(shipped_packet.splitlines())
            )
        )
        problems.extend(
            example_regeneration_problems(
                block, root, folder, shipped_packet
            )
        )
        return problems
    except DuplicateKeyError:
        return problems + [
            "the shipped manifest of the example packet holds "
            "a repeated key"
        ]
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        AssertionError,
        subprocess.SubprocessError,
    ) as exc:
        return problems + [
            "the shipped example packet or its manifest cannot "
            "be read with %s" % exc
        ]


def scratch_checkout(root, tmp):
    """Clone the checked tree at its checked head into a folder.

    The clone is a plain local clone of the tree this gate
    checks, checked out at the head that tree stands on, so
    the history the printed command runs over is the history
    of the checked tree and every write the run makes lands
    in the clone and never in the checked tree.
    """
    scratch = Path(tmp) / "scratch"
    head = run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        env=scrubbed_child_env(),
        timeout=120,
    )
    if head.returncode != 0:
        return None, [
            "the checked tree head cannot be read for a scratch "
            "checkout with %s" % head.stderr.strip()
        ]
    clone = run(
        ["git", "clone", "-q", str(root), str(scratch)],
        env=scrubbed_child_env(),
        timeout=300,
    )
    if clone.returncode != 0:
        return None, [
            "a scratch checkout of the checked tree cannot be "
            "cloned with %s" % clone.stderr.strip()
        ]
    checkout = run(
        ["git", "-C", str(scratch), "checkout", "-q", head.stdout.strip()],
        env=scrubbed_child_env(),
        timeout=120,
    )
    if checkout.returncode != 0:
        return None, [
            "a scratch checkout of the checked tree cannot be "
            "checked out at its head with %s" % checkout.stderr.strip()
        ]
    return scratch, []


def example_regeneration_problems(block, root, folder, shipped_packet):
    """Run the one validated command in a scratch checkout.

    The block stands checked against the strict template
    here as well as in the caller, before anything executes,
    so no route into this run can execute a block the
    template refuses. A passing block runs as an argument
    list built from its validated values, with the scratch
    checkout root as the working folder and as the repo
    argument and with the validated relative folder as the
    out argument. The shipped example folder in the scratch
    checkout is removed before the run, after its path
    stands resolved and verified as the literal folder
    inside the checkout, so the packet that compares is the
    packet the run itself produced there and never a copy
    the clone carried in. The regenerated packet file and
    manifest file stand checked as real files before they
    compare, because the reads that compare them follow a
    link standing in their place in the same way as the
    reads of the shipped copies.
    """
    problems = []
    rel_folder = folder.relative_to(root).as_posix()
    values, template_problems = printed_template_problems(block, root)
    if template_problems:
        return template_problems
    if values["out"] != rel_folder:
        return printed_out_problems([values["out"]], rel_folder)
    with tempfile.TemporaryDirectory() as tmp:
        scratch, checkout_problems = scratch_checkout(root, tmp)
        if checkout_problems:
            return checkout_problems
        link_problems = scratch_symlink_problems(scratch, rel_folder)
        if link_problems:
            return link_problems
        out = scratch / rel_folder
        try:
            if out.is_dir():
                shutil.rmtree(out)
            result = run(
                [
                    sys.executable,
                    str(scratch / EXAMPLE_EXTRACT_TOKEN),
                    "--commit", values["commit"],
                    "--out", rel_folder,
                    "--repo", str(scratch),
                ],
                cwd=scratch,
                env=scrubbed_child_env(),
                timeout=300,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return [
                "the printed example command cannot be run "
                "as printed with %s" % exc
            ]
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            return [
                "the printed example command failed in a "
                "scratch checkout with exit %d and %s"
                % (result.returncode, detail)
            ]
        if not (out / "packet.md").is_file() or not (
            out / "manifest.json"
        ).is_file():
            return [
                "the printed example command ran in a "
                "scratch checkout and produced no packet "
                "and manifest in the shipped example folder %s"
                % rel_folder
            ]
        for name in ("packet.md", "manifest.json"):
            if (out / name).is_symlink():
                return [
                    "the regenerated example file %s stands "
                    "as a symlink in the scratch checkout "
                    "and the regenerated example files must "
                    "stand as real files in a real folder"
                    % ("%s/%s" % (rel_folder, name))
                ]
        rebuilt_packet = guarded_read_text((out / "packet.md"), encoding="utf-8")
        if rebuilt_packet != shipped_packet:
            problems.append(
                diff_summary(
                    "example packet", shipped_packet, rebuilt_packet
                )
            )
        shipped_manifest = strict_json_loads(
            guarded_read_text((folder / "manifest.json"), encoding="utf-8")
        )
        rebuilt_manifest = strict_json_loads(
            guarded_read_text((out / "manifest.json"), encoding="utf-8")
        )
        problems.extend(
            manifest_problems(
                "example packet", shipped_manifest, rebuilt_manifest,
                keep_tokens=True, exact_hashes=True,
            )
        )
    return problems


def norm_eval_packet(text):
    """Set aside the history shapes a rebuild cannot reproduce.

    The fixture builder hardcodes the subjects and the author,
    so subject lines and blame author lines compare as written
    apart from the hash each one carries. Only the hashes move
    between rebuilds, because the builder sets no commit date,
    and the token numbers stay set aside as the module
    docstring states.
    """
    out = []
    for line in text.splitlines():
        line = HASH40.sub("@hash@", line)
        line = re.sub(
            r"^(# The pericope for range) .*$", r"\1 @range@", line
        )
        line = re.sub(
            r"^(commit) [0-9a-f]{7,40}( .*)$", r"\1 @hash@\2", line
        )
        line = re.sub(
            r"^(.+ )([0-9a-f]{7,8})( lines \d+)$", r"\1@hash@\3", line
        )
        line = re.sub(r"^([0-9a-f]{7})( .*)$", r"@hash@\2", line)
        line = re.sub(
            r"^(Packet estimate in tokens:) \d+$", r"\1 @tokens@", line
        )
        line = re.sub(
            r"^(T\d included at about) \d+ (tokens.*)$",
            r"\1 @tokens@ \2",
            line,
        )
        out.append(line)
    return "\n".join(out)


def eval_task_problems(root, eval_gate, task_dir):
    problems = []
    rel_folder = "evals/tasks/%s" % task_dir.name
    link_problems = checked_symlink_problems(
        root,
        rel_folder,
        label="eval task",
        file_names=(
            "packet.md",
            "manifest.json",
            "diff.patch",
            "sources.json",
        ),
    )
    if link_problems:
        return link_problems
    duplicate_errors = (
        DuplicateKeyError,
        getattr(eval_gate, "DuplicateKeyError", DuplicateKeyError),
    )
    try:
        sources = eval_gate.strict_json_loads(
            guarded_read_text((task_dir / "sources.json"), encoding="utf-8")
        )
        if not isinstance(sources, dict):
            return problems + [
                "the sources of %s do not hold a JSON object"
                % task_dir.name
            ]
        with tempfile.TemporaryDirectory() as tmp:
            repo, base, head, rebuilt_diff = (
                eval_gate.build_fixture_repo(tmp, sources)
            )
            saved_diff = guarded_read_bytes((task_dir / "diff.patch"))
            if rebuilt_diff != saved_diff:
                problems.append(
                    "the diff of %s does not rebuild byte for byte "
                    "from its sources" % task_dir.name
                )
            out = Path(tmp) / "out"
            result = run_extractor(
                ["--repo", str(repo), "--range", "%s..%s" % (base, head)],
                out,
            )
            if result.returncode != 0:
                return problems + [
                    "the extractor failed on the rebuilt history of "
                    "%s with %s" % (task_dir.name, result.stderr.strip())
                ]
            shipped_packet = guarded_read_text((task_dir / "packet.md"),
                encoding="utf-8"
            )
            rebuilt_packet = guarded_read_text((out / "packet.md"),
                encoding="utf-8"
            )
            if norm_eval_packet(rebuilt_packet) != norm_eval_packet(
                shipped_packet
            ):
                problems.append(
                    diff_summary(
                        "packet of %s" % task_dir.name,
                        norm_eval_packet(shipped_packet),
                        norm_eval_packet(rebuilt_packet),
                    )
                )
            shipped_manifest = strict_json_loads(
                guarded_read_text((task_dir / "manifest.json"), encoding="utf-8")
            )
            rebuilt_manifest = strict_json_loads(
                guarded_read_text((out / "manifest.json"), encoding="utf-8")
            )
            problems.extend(
                manifest_problems(
                    task_dir.name, shipped_manifest, rebuilt_manifest,
                    keep_tokens=False,
                )
            )
        return problems
    except duplicate_errors:
        return problems + [
            "the saved manifest or sources of %s holds a "
            "repeated key" % task_dir.name
        ]
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        AssertionError,
        subprocess.SubprocessError,
    ) as exc:
        return problems + [
            "the eval task %s cannot be rebuilt or read with "
            "%s" % (task_dir.name, exc)
        ]


def eval_problems(root):
    tasks = root / "evals" / "tasks"
    if not tasks.is_dir():
        return ["no eval tasks stand under evals/tasks"]
    try:
        eval_gate = load_sibling("check_evals")
    except (OSError, ValueError, ImportError) as exc:
        return ["the eval gate module cannot be loaded with %s" % exc]
    problems = []
    for task_dir in sorted(tasks.iterdir()):
        if task_dir.is_dir():
            problems.extend(eval_task_problems(root, eval_gate, task_dir))
    return problems


def git(repo, *args, env_extra=None):
    env = scrubbed_child_env(env_extra)
    argv = [
        "git", "--no-pager", "--no-replace-objects",
        "--literal-pathspecs", "-C", str(repo),
        "-c", "core.quotepath=false",
    ] + list(args)
    result = run(argv, env=env, timeout=120)
    if result.returncode != 0:
        raise AssertionError(
            "git %s failed with %s" % (" ".join(args), result.stderr)
        )
    return result.stdout.strip()


def write_mapping(repo, mapping):
    for child in list(repo.iterdir()):
        if child.name == ".git":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    for name, content in mapping.items():
        target = repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def build_proof_repo(tmp, sources):
    """Build the two commit proof fixture from its sources file.

    The author and the subjects and the dates come from the
    sources file and ride the environment of each commit, so
    two builds of the same sources file produce one history
    with one pair of hashes.
    """
    repo = Path(tmp) / "repo"
    repo.mkdir(parents=True)
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", sources["author_name"])
    git(repo, "config", "user.email", sources["author_email"])
    git(repo, "config", "core.autocrlf", "false")
    git(repo, "config", "commit.gpgsign", "false")
    write_mapping(repo, sources["base"])
    git(repo, "add", "-A")
    git(
        repo, "commit", "-m", sources["base_subject"],
        env_extra={
            "GIT_AUTHOR_DATE": sources["base_date"],
            "GIT_COMMITTER_DATE": sources["base_date"],
        },
    )
    base = git(repo, "rev-parse", "HEAD")
    write_mapping(repo, sources["head"])
    git(repo, "add", "-A")
    git(
        repo, "commit", "-m", sources["head_subject"],
        env_extra={
            "GIT_AUTHOR_DATE": sources["head_date"],
            "GIT_COMMITTER_DATE": sources["head_date"],
        },
    )
    head = git(repo, "rev-parse", "HEAD")
    return repo, base, head


def norm_proof_packet(text):
    """Set aside the commit hashes of the rebuilt history.

    Subjects stay in the comparison because the sources file
    pins them, and blob hashes stay because they rest on file
    content alone.
    """
    out = []
    for line in text.splitlines():
        line = HASH40.sub("@hash@", line)
        line = re.sub(r"^(commit) [0-9a-f]{7,40}( )", r"\1 @hash@\2", line)
        line = re.sub(r"^[0-9a-f]{7}( )", "@hash@ ", line)
        line = re.sub(
            r"^(.+ )([0-9a-f]{7,8})( lines \d+)$", r"\1@hash@\3", line
        )
        out.append(line)
    return "\n".join(out)


def proof_problems(root):
    folder = root / "workflows" / "proof-run"
    sources_path = folder / "sources.json"
    # The sources file stands guarded before it is loaded,
    # in the order the eval class uses, so a symlink at the
    # sources file or at a component above it is named as a
    # link and its bytes are never read through the link as
    # provenance. The full guard keeps its place after the
    # load below, so the packet and manifest diagnostics and
    # the sparse fixture and repeated key diagnostics keep
    # the texts and the precedence they already hold.
    if (
        symlink_component(root, "workflows/proof-run/sources.json")
        is not None
    ):
        return checked_symlink_problems(
            root,
            "workflows/proof-run",
            label="proof run",
            file_names=("sources.json",),
        )
    if not sources_path.is_file():
        return [
            "no sources file stands at workflows/proof-run/"
            "sources.json and the proof fixture cannot be "
            "rebuilt from the tree"
        ]
    problems = []
    try:
        sources = strict_json_loads(
            guarded_read_text(sources_path, encoding="utf-8")
        )
        if not isinstance(sources, dict):
            return problems + [
                "the proof run sources do not hold a JSON object"
            ]
        link_problems = checked_symlink_problems(
            root,
            "workflows/proof-run",
            label="proof run",
            file_names=(
                "packet.md",
                "manifest.json",
                "sources.json",
            ),
        )
        if link_problems:
            return link_problems
        with tempfile.TemporaryDirectory() as tmp:
            repo, base, head = build_proof_repo(tmp, sources)
            out = Path(tmp) / "out"
            result = run_extractor(
                ["--repo", str(repo), "--range", "%s..%s" % (base, head)],
                out,
            )
            if result.returncode != 0:
                return [
                    "the extractor failed on the rebuilt proof "
                    "fixture with %s" % result.stderr.strip()
                ]
            shipped_packet = guarded_read_text((folder / "packet.md"),
                encoding="utf-8"
            )
            rebuilt_packet = guarded_read_text((out / "packet.md"),
                encoding="utf-8"
            )
            if norm_proof_packet(rebuilt_packet) != norm_proof_packet(
                shipped_packet
            ):
                problems.append(
                    diff_summary(
                        "proof run packet",
                        norm_proof_packet(shipped_packet),
                        norm_proof_packet(rebuilt_packet),
                    )
                )
            shipped_manifest = strict_json_loads(
                guarded_read_text((folder / "manifest.json"), encoding="utf-8")
            )
            rebuilt_manifest = strict_json_loads(
                guarded_read_text((out / "manifest.json"), encoding="utf-8")
            )
            problems.extend(
                manifest_problems(
                    "proof run packet", shipped_manifest,
                    rebuilt_manifest, keep_tokens=True,
                )
            )
        return problems
    except DuplicateKeyError:
        return problems + [
            "the proof run sources or its shipped manifest "
            "holds a repeated key"
        ]
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        AssertionError,
        subprocess.SubprocessError,
    ) as exc:
        return problems + [
            "the proof run packet or its sources cannot be "
            "rebuilt or read with %s" % exc
        ]


def folder_snapshot(folder):
    """Map each file under a folder to its digest.

    The modification time does not stand in the snapshot,
    because a touch with no write and no content change is
    not a refresh. A builder that regenerates a shipped file
    byte for byte is still seen through the traced write the
    run made on that file, or through the marker run that
    judges the files the trace cannot see being written.
    """
    snap = {}
    for path in sorted(folder.rglob("*")):
        if path.is_file() and ".build-tmp" not in path.parts:
            snap[path.relative_to(folder).as_posix()] = hashlib.sha256(
                guarded_read_bytes(path)
            ).hexdigest()
    return snap


BUILDER_RUNNER = r"""
import os
import runpy
import sys

builder = sys.argv[1]
log_path = sys.argv[2]
folder = os.path.realpath(os.getcwd())
fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)


def record(raw, written):
    if isinstance(raw, bytes):
        raw = os.fsdecode(raw)
    if not isinstance(raw, str):
        return
    path = raw
    if not os.path.isabs(path):
        path = os.path.join(os.getcwd(), path)
    path = os.path.realpath(path)
    if not path.startswith(folder + os.sep):
        return
    rel = os.path.relpath(path, folder)
    line = ("W " if written else "R ") + rel + "\n"
    os.write(fd, line.encode("utf-8", "surrogateescape"))


def hook(event, args):
    if not args:
        return
    try:
        if event == "open":
            mode = args[1] if len(args) > 1 else None
            flags = args[2] if len(args) > 2 else 0
            written = False
            if isinstance(mode, str) and any(
                mark in mode for mark in "wax+"
            ):
                written = True
            if isinstance(flags, int) and flags & (
                os.O_WRONLY | os.O_RDWR | os.O_TRUNC | os.O_APPEND
            ):
                written = True
            record(args[0], written)
        elif event in ("os.remove", "os.unlink"):
            record(args[0], True)
        elif event in ("os.rename", "os.replace"):
            record(args[0], True)
            if len(args) > 1:
                record(args[1], True)
    except Exception:
        return


sys.dont_write_bytecode = True
sys.addaudithook(hook)
try:
    runpy.run_path(builder, run_name="__main__")
except SystemExit as exc:
    code = exc.code
    if isinstance(code, int):
        sys.exit(code)
    sys.exit(0 if code is None else 1)
"""


def traced_opens(trace_path):
    """Read the builder run record into read and written name sets."""
    reads = set()
    writes = set()
    if not trace_path.is_file():
        return reads, writes
    for line in guarded_read_text(trace_path,
        encoding="utf-8", errors="surrogateescape"
    ).splitlines():
        if line.startswith("W "):
            writes.add(line[2:])
        elif line.startswith("R "):
            reads.add(line[2:])
    return reads, writes


def builder_problems(root):
    """Run every builder under the docs tree in a scratch copy."""
    builders = sorted(root.glob("docs/**/build_*.py"))
    if not builders:
        return ["no builder script stands under the docs tree"]
    problems = []
    for builder in builders:
        other_folders = []
        for other in builders:
            if other == builder:
                continue
            try:
                rel = other.parent.relative_to(builder.parent)
            except ValueError:
                continue
            if rel.as_posix() != ".":
                other_folders.append(rel.as_posix())
        problems.extend(
            one_builder_problems(root, builder, other_folders)
        )
    return problems


def one_builder_problems(root, builder, other_folders=()):
    """Run one builder in a scratch copy of its own folder.

    A file the builder creates or changes in its copy is one
    of its outputs, and so is a shipped file the traced run
    opens for writing even when the regenerated bytes match
    the shipped bytes. Every output name must stand in the
    shipped folder and every output that stands there must
    match the shipped bytes. A name the run deletes is a
    deleted output. A shipped file standing in the folder
    subtree of the builder that the run neither writes nor
    changes is reported as a file no regeneration refreshes,
    after a marker run has had its chance to restore that
    file from marked bytes, under the limits the module
    docstring states. The checked tree symlink guard over
    the builder folder subtree runs before the builder
    itself, so a linked shipped file is named as a problem
    rather than read through in the copy the run compares.
    """
    problems = []
    folder = builder.parent
    rel_folder = folder.relative_to(root).as_posix()
    rel_builder = builder.relative_to(root).as_posix()
    link_problems = builder_symlink_problems(
        root, builder, other_folders
    )
    if link_problems:
        return link_problems
    try:
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "copy"
            shutil.copytree(folder, copy)
            before = folder_snapshot(copy)
            trace = Path(tmp) / "trace.log"
            result = run(
                [
                    sys.executable, "-c", BUILDER_RUNNER,
                    str(copy / builder.name), str(trace),
                ],
                cwd=copy,
                timeout=600,
            )
            if result.returncode != 0:
                problems.append(
                    "the builder at %s failed in a scratch copy "
                    "with %s"
                    % (rel_builder, result.stderr.strip()[-200:])
                )
                return problems
            after = folder_snapshot(copy)
            reads, writes = traced_opens(trace)
            changed = {
                name
                for name in set(before) | set(after)
                if before.get(name) != after.get(name)
            }
            outputs = sorted(
                changed
                | {
                    name
                    for name in writes
                    if name in before or name in after
                }
            )
            if not outputs:
                problems.append(
                    "the builder at %s writes no outputs" % rel_builder
                )
            for name in outputs:
                shipped = folder / name
                if name not in after:
                    problems.append(
                        "the builder at %s deletes the shipped "
                        "output %s that stands under %s"
                        % (rel_builder, name, rel_folder)
                    )
                elif name not in before or not shipped.is_file():
                    problems.append(
                        "the builder at %s writes %s and no file "
                        "of that name stands under %s"
                        % (rel_builder, name, rel_folder)
                    )
                elif after[name] != before[name]:
                    problems.append(
                        "the output %s of the builder at %s "
                        "differs from the shipped bytes"
                        % (name, rel_builder)
                    )
            if folder != root / "docs":
                candidates = dropped_output_candidates(
                    before, after, reads, writes, builder,
                    rel_folder, other_folders,
                )
                if candidates:
                    restored = marker_restored_names(
                        folder, builder, candidates, before, tmp
                    )
                    candidates = [
                        name
                        for name in candidates
                        if name not in restored
                    ]
                problems.extend(
                    dropped_problem(name, rel_builder)
                    for name in candidates
                )
    except (OSError, subprocess.SubprocessError) as exc:
        problems.append(
            "the builder at %s cannot be run in a scratch "
            "copy with %s" % (rel_builder, exc)
        )
    return problems


def dropped_output_candidates(before, after, reads, writes,
                              builder, rel_folder,
                              other_folders=()):
    """List shipped files in a builder subtree it never refreshes.

    A file is refreshed when the run writes it or its digest
    changes, and a read alone refreshes nothing. The declared
    inputs named in DECLARED_BUILDER_INPUTS stand outside the
    rule, and a Python file stands outside it only when the
    run reads that file. A file under the folder of another
    builder stands outside it as well, because that other
    builder run is the run that judges it.
    """
    changed = {
        name
        for name in set(before) | set(after)
        if before.get(name) != after.get(name)
    }
    refreshed = changed | set(writes)
    candidates = []
    for name in sorted(before):
        if name not in after:
            continue
        if name in refreshed:
            continue
        if name == builder.name:
            continue
        if any(
            name == other or name.startswith(other + "/")
            for other in other_folders
        ):
            continue
        if "%s/%s" % (rel_folder, name) in DECLARED_BUILDER_INPUTS:
            continue
        if name.endswith(".py") and name in reads:
            continue
        candidates.append(name)
    return candidates


def dropped_problem(name, rel_builder):
    """One problem naming a shipped file no run refreshes."""
    return (
        "the shipped file %s stands in the folder subtree "
        "of the builder at %s and the builder neither "
        "writes nor changes it, so no regeneration "
        "refreshes it" % (name, rel_builder)
    )


MARKER_BYTES = b"\x00recognitio dropped output marker\x00\n"


def marker_restored_names(folder, builder, candidates, digests, tmp):
    """Run one builder over marked copies of its candidate files.

    Each candidate file stands in the copy with the marker
    bytes in place of its shipped bytes. A candidate the run
    restores to its shipped digest counts as refreshed, which
    is how a write through a child process or a native library
    counts even though the trace of the builder process holds
    no write for it. A candidate the run only reads or only
    touches keeps the marker bytes and counts for nothing. The
    return code of this run is set aside, because a builder
    that reads a marked former output can fail on the marker
    itself, and the restored set is the evidence either way.
    """
    restored = set()
    marked = [
        name
        for name in candidates
        if digests.get(name)
        != hashlib.sha256(MARKER_BYTES).hexdigest()
    ]
    if not marked:
        return restored
    try:
        copy = Path(tmp) / "marker"
        shutil.copytree(folder, copy)
        for name in marked:
            (copy / name).write_bytes(MARKER_BYTES)
        trace = Path(tmp) / "marker-trace.log"
        run(
            [
                sys.executable, "-c", BUILDER_RUNNER,
                str(copy / builder.name), str(trace),
            ],
            cwd=copy,
            timeout=600,
        )
        after = folder_snapshot(copy)
        for name in marked:
            if after.get(name) == digests.get(name):
                restored.add(name)
    except (OSError, subprocess.SubprocessError):
        return restored
    return restored


def all_problems(root):
    problems = []
    problems.extend(example_problems(root))
    problems.extend(eval_problems(root))
    problems.extend(proof_problems(root))
    problems.extend(builder_problems(root))
    return problems


def main():
    problems = all_problems(ROOT)
    if problems:
        for problem in problems:
            print("check_regeneration: %s" % problem, file=sys.stderr)
        return 1
    print(
        "check_regeneration: the example packet and the six "
        "eval task packets and the proof run packet regenerate "
        "from their stated provenance and every builder under "
        "the docs tree writes only the outputs the tree ships "
        "and writes them byte for byte"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
