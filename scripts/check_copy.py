#!/usr/bin/env python3
"""Enforce the copy bar on the public prose files.

The bar bans four marks from prose sentences. Em dashes, en
dashes, semicolons and colons all push a writer toward
compressed clauses, and the house style is short plain
sentences instead. The em dash and the en dash are matched by
codepoint because a shell grep for the character once reported zero
hits on a tree full of them.

Code is exempt. Fenced code blocks and inline code spans are skipped,
as are YAML frontmatter keys, link reference definitions and lines
that hold nothing but a file path. A line that holds one HTML tag
and nothing else is markup and is skipped in the same way, because
an attribute value inside a tag is syntax and not a sentence, and
the tag lines of the README hero stand in that class, the wordmark
image pair and the recording picture alike. Text standing beside a
tag on the same line stays prose and is judged. A URL exempts only
its own span of a line, never the whole line, so a banned mark
hiding beside a link is still caught. The span ends at the link
boundary, so punctuation sitting right after a link stays in the
prose and is judged.

Four files are mostly code with prose living in their comments.
The workflow, the dependabot config, the Makefile and the
gitignore are scanned by comment span only, so their shell and
pattern lines are never judged as prose while every sentence a
contributor writes in them is.

The fence is discovered by rule inside a bounded frame rather
than listed by hand, so a new authored prose surface in a
format and a location the frame already covers joins it by
construction instead of waiting for someone to remember the
list. The frame is the four file patterns the discovery rule
walks and the allow list of hidden directories below, and a
surface in a new format or under a new hidden directory stands
outside the fence until the frame itself is extended to cover
it. Every Markdown file and every Cursor rule file the frame
covers is prose, apart from the generated packets saved as eval
fixtures, which are extractor output and not authored text,
regenerated on every check by `scripts/check_regeneration.py`,
and the plugin skill copy, which is pinned byte identical to
the canonical skill by its own gate script. The description
fields of the plugin manifests are prose a reader meets in a
listing, so they are scanned as values, and the scan collects
the longer listing description keys and the extension note
keys beside the plain description key, because a listing
reader meets that prose first. Every YAML file the frame
covers is discovered by the same rule as the Markdown files
and scanned as YAML, apart from the files in the comment span
class, whose values are code and whose prose lives in hash
comments, and those are scanned by comment span.

The fence also carries a floor. The root README is a required
prose surface, and a discovery that finds no prose file at all
is a violation by name, so the gate never prints its success
line over a tree whose prose has gone missing. Relative
Markdown link targets in the scanned Markdown files are
checked against the tree as well, so a link naming a file that
does not stand in the tree is a violation, while external
addresses are never fetched and stand outside this check.

Exits nonzero and lists every violation when the bar is broken.
"""

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]

# Hidden directories whose files are authored prose the bar
# reaches. Every other hidden directory holds tool or dependency
# state and stays outside the fence. The .cursor directory holds
# the authored Bugbot rules and repo config, and the
# .cursor-plugin directory holds the authored plugin README, the
# rule file, and the manifests, so both join the fence. The
# .antigravity directory holds the authored Antigravity plugin
# manifest and hook wiring, and the .zcode-plugin directory
# holds the authored ZCode plugin manifest, so both join the
# fence as well. The plugin's skill copy subtree stays out by
# the rule below, because its own gate script pins it byte
# identical to the canonical skill the fence already scans.
_PUBLIC_DOT_DIRS = (".github", ".agents", ".claude", ".claude-plugin",
                    ".cursor", ".cursor-plugin", ".antigravity",
                    ".zcode-plugin")


def is_fence_excluded(root, path):
    """Whether a path stands outside the fence by the shared rule.

    Local dependency and tool directories are not authored prose,
    so a file under a hidden directory other than the GitHub
    config directory, the skill directories, the plugin
    directories, or the Cursor config directory, or under a
    node_modules directory, stays outside the fence, and so does
    a symlink whose target leaves the tree. The skill directories
    .agents/skills and .claude/skills hold authored skill prose
    by design, so they stay inside the fence, and the
    output-styles directory at the plugin root holds the
    authored packet style for the same reason. The generated eval
    packets stay outside it for the reason the module docstring
    records, and so does the plugin skill copy under
    .cursor-plugin/skills, because scripts/check_cursor.py pins
    that copy byte identical to the canonical skill the fence
    already scans. Discovery and the fence completeness walk in the
    gate tests both call this one predicate, so the two can never
    encode opposite rules for the same locations again.
    """
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    parts = rel.parts
    if any(
        part == "node_modules"
        or (part.startswith(".") and part not in _PUBLIC_DOT_DIRS)
        for part in parts[:-1]
    ):
        return True
    if len(parts) == 4 and parts[:2] == ("evals", "tasks") \
            and parts[3] == "packet.md":
        return True
    if parts[0] == "examples" and parts[-1] == "packet.md":
        # A packet saved under examples is extractor output
        # shipped so a visitor can read one without installing,
        # so it stays out by the same rule as the eval packets.
        # The regeneration gate at scripts/check_regeneration.py
        # reruns the extractor over it on every check. Every
        # other file under examples is authored prose and
        # stays inside the fence.
        return True
    if parts == ("workflows", "proof-run", "packet.md"):
        # The proof run packet is extractor output shipped as
        # the record a fan out run stands on, regenerated by
        # the regeneration gate at scripts/check_regeneration.py
        # running the extractor itself, so it stays out by the
        # same rule as the example packet. The runbook and the
        # readme in the same folder are authored prose and stay
        # inside the fence.
        return True
    if len(parts) >= 2 and parts[:2] == (".cursor-plugin", "skills"):
        # The plugin skill copy is pinned byte identical to the
        # canonical skill by scripts/check_cursor.py, and the
        # canonical skill is already inside the fence, so the copy
        # stays out by rule the way the generated eval packets do.
        return True
    if path.is_symlink():
        try:
            path.resolve().relative_to(root.resolve())
        except ValueError:
            return True
    return False


def is_comment_span_file(root, path):
    """Whether a file is scanned by comment span rather than as prose.

    The dependabot config and the workflow files carry code in
    their values, so their prose lives in their hash comments and
    the comment span scan is the scan that reaches them. The
    Makefile and the gitignore stand in the same class.
    """
    try:
        rel = path.relative_to(root)
    except ValueError:
        return False
    if rel == Path(".github") / "dependabot.yml":
        return True
    if rel.parent == Path(".github") / "workflows" \
            and path.suffix in (".yml", ".yaml"):
        return True
    return rel in (Path("Makefile"), Path(".gitignore"))


def discover_prose_files(root=None):
    """Every authored prose file the bar reaches, found by rule.

    Markdown files, Cursor rule files, and YAML files are
    discovered the same way, by location and suffix under the
    shared exclusion rule, so a new YAML surface or a new rule
    file joins the fence by construction just as a new Markdown
    file does. YAML files in the comment span class stay out of
    this set because that scan already reaches them.
    """
    root = ROOT if root is None else root
    found = []
    candidates = []
    for pattern in ("*.md", "*.mdc", "*.yml", "*.yaml"):
        candidates.extend(root.rglob(pattern))
    for path in sorted(set(candidates)):
        if is_fence_excluded(root, path):
            continue
        if path.suffix in (".yml", ".yaml") \
                and is_comment_span_file(root, path):
            continue
        found.append(path)
    return sorted(found)


def discover_comment_files(root=None):
    """Files whose prose lives in hash comments, found by rule."""
    root = ROOT if root is None else root
    found = []
    for path in (
        root / ".github" / "dependabot.yml",
        root / "Makefile",
        root / ".gitignore",
    ):
        if path.is_file():
            found.append(path)
    workflows = root / ".github" / "workflows"
    if workflows.is_dir():
        for path in sorted(workflows.iterdir()):
            if path.suffix in (".yml", ".yaml") and path.is_file():
                found.append(path)
    return sorted(found)


def discover_manifest_files(root=None):
    """Plugin manifests whose description fields are public prose.

    Manifests are found by rule rather than listed by hand. Every
    plugin.json and every marketplace.json under the tree is a
    manifest surface, discovered through the shared exclusion
    rule, so a new manifest joins the fence by construction the
    way a new Markdown file does. The two Claude Code manifests
    are additionally returned when absent, so a deleted manifest
    is reported as missing by the caller instead of passing a
    scan that never ran.
    """
    root = ROOT if root is None else root
    found = []
    for pattern in ("plugin.json", "marketplace.json"):
        for path in sorted(root.rglob(pattern)):
            if is_fence_excluded(root, path):
                continue
            found.append(path)
    for path in (
        root / ".claude-plugin" / "plugin.json",
        root / ".claude-plugin" / "marketplace.json",
    ):
        if path not in found:
            found.append(path)
    return sorted(set(found))


PROSE_FILES = discover_prose_files()
COMMENT_FILES = discover_comment_files()
MANIFEST_FILES = discover_manifest_files()

EM_DASH = "\u2014"
EN_DASH = "\u2013"
FRONTMATTER_KEY = re.compile(r"^\s*[A-Za-z][A-Za-z0-9_-]*:(\s|$)")
LINK_REFERENCE = re.compile(r"^\s*\[[^\]]+\]:")
BARE_PATH = re.compile(r"^[\w.@~+-]+(/[\w.@~+-]+)+/?$")
HTML_TAG_LINE = re.compile(r"^<[^>]*>$")
INLINE_CODE = re.compile(r"`[^`]*`")
URL_SPAN = re.compile(r"https?://\S+")
YAML_BLOCK = re.compile(r":\s*[|>][+-]?\s*$")


def _quoted_end(text, start=0):
    """The index just past a quoted scalar, or None when it spans on.

    The text at start is the opening quote. A doubled single quote
    is an escaped quote inside a single quoted scalar, and a
    backslash escapes the next character inside a double quoted
    one, so neither ends the scalar.
    """
    quote = text[start]
    index = start + 1
    while index < len(text):
        char = text[index]
        if char == "\\" and quote == '"':
            index += 2
            continue
        if char == quote:
            if quote == "'" and text[index + 1:index + 2] == "'":
                index += 2
                continue
            return index + 1
        index += 1
    return None


def _opens_quote(text, index):
    """Whether the quote character at index opens a quoted scalar.

    A quote opens a scalar only where a scalar can start, at
    the start of the text or after a space or a flow delimiter
    or a key colon. An apostrophe standing inside a plain
    scalar, as in a word like don't, is text and not a quote,
    and treating it as one would leave the scanner waiting
    for a close that never comes and swallow the lines after
    it into the wrong span.
    """
    return index == 0 or text[index - 1] in " \t,[{:"


def _spanning_quote(text):
    """The quote character a text leaves open, or None.

    The scan asks after the first quote that opens a scalar,
    under the same opening rule the YAML reading uses, whether
    that scalar closes on the same text. A scalar that closes
    is read whole by its own line, so only a scalar still open
    at the end of the text carries state to the next line.
    """
    index = 0
    while index < len(text):
        char = text[index]
        if char in "\"'" and _opens_quote(text, index):
            if _quoted_end(text, index) is None:
                return char
            return None
        index += 1
    return None


def _split_key(candidate, flow=False):
    """Split one YAML line into its key and value, or return None.

    Key recognition is structural rather than a character pattern.
    Any scalar a YAML line can carry as a key is a key, quoted or
    plain, dotted or numeric or spaced or slashed or digit led,
    and only the value after its colon is prose. The colon that
    ends a key is the first colon standing outside quotes and
    outside any flow collection that is followed by a space or by
    the end of the line, or by anything at all inside a flow
    collection. A line with no such colon carries no key.
    """
    if not candidate:
        return None
    if candidate[0] in "\"'":
        end = _quoted_end(candidate)
        if end is None:
            return None
        rest = candidate[end:].lstrip()
        if rest.startswith(":") and (
            flow or len(rest) == 1 or rest[1] in " \t"
        ):
            return candidate[:end], rest[1:].strip()
        return None
    depth = 0
    quote = None
    index = 0
    while index < len(candidate):
        char = candidate[index]
        if quote is not None:
            if char == "\\" and quote == '"':
                index += 1
            elif char == quote:
                quote = None
        elif char in "\"'" and _opens_quote(candidate, index):
            quote = char
        elif char in "{[":
            depth += 1
        elif char in "}]":
            depth -= 1
        elif char == "#" and index > 0 and candidate[index - 1] in " \t":
            return None
        elif char == ":" and depth == 0:
            following = candidate[index + 1:index + 2]
            if flow and following != ":":
                key = candidate[:index].strip()
                return (key, candidate[index + 1:].strip()) if key else None
            if following == "" or following in " \t":
                key = candidate[:index].strip()
                if not key or key[0] in "{[&*!%@`":
                    return None
                return key, candidate[index + 1:].strip()
        index += 1
    return None


def _strip_value_prefix(value):
    """Drop the anchor and tag tokens standing before a YAML value.

    An anchor or a tag is structure that names or types the value
    after it, so the value a reader meets starts after those
    tokens, whether what follows is a flow collection, a quoted
    scalar or a plain one.
    """
    text = value.strip()
    while text:
        if text.startswith("&"):
            parts = text.split(None, 1)
            if len(parts) == 1:
                return ""
            text = parts[1].lstrip()
            continue
        if text.startswith("!<"):
            end = text.find(">")
            if end == -1:
                return text
            text = text[end + 1:].lstrip()
            continue
        if text.startswith("!"):
            parts = text.split(None, 1)
            if len(parts) == 1:
                return ""
            text = parts[1].lstrip()
            continue
        return text
    return text


def _flow_scan(text):
    """The flow depth and open quote a flow text ends in."""
    depth = 0
    quote = None
    index = 0
    while index < len(text):
        char = text[index]
        if quote is not None:
            if char == "\\" and quote == '"':
                index += 1
            elif char == quote:
                if quote == "'" and text[index + 1:index + 2] == "'":
                    index += 1
                else:
                    quote = None
        elif char in "\"'" and _opens_quote(text, index):
            quote = char
        elif char in "{[":
            depth += 1
        elif char in "}]":
            depth -= 1
        index += 1
    return depth, quote


def _flow_complete(text):
    depth, quote = _flow_scan(text)
    return depth <= 0 and quote is None


def _flow_close_index(text):
    """The index where the flow collection opening a text closes."""
    depth = 0
    quote = None
    index = 0
    while index < len(text):
        char = text[index]
        if quote is not None:
            if char == "\\" and quote == '"':
                index += 1
            elif char == quote:
                if quote == "'" and text[index + 1:index + 2] == "'":
                    index += 1
                else:
                    quote = None
        elif char in "\"'" and _opens_quote(text, index):
            quote = char
        elif char in "{[":
            depth += 1
        elif char in "}]":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return len(text)


def _url_replacement(match):
    """Blank a URL span but keep the punctuation that trails it.

    A Markdown link ends at its closing parenthesis, and a semicolon
    or a colon right after a link or a bare URL is prose punctuation,
    not part of the address. A port or path colon is never the last
    character of the span, so trimming these marks from the end of
    the span only ever exposes prose. Whatever trails the span stays
    in the line, so the bar still judges it.
    """
    span = match.group(0)
    core = span.rstrip(");:")
    return span[len(core):]


def clean(text):
    """Remove the spans of a line the bar does not reach."""
    text = URL_SPAN.sub(_url_replacement, text)
    text = INLINE_CODE.sub("", text)
    return text


def prose_lines(path):
    """Yield (number, text) pairs for the lines the bar applies to."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if path.suffix in (".yaml", ".yml"):
        yield from yaml_prose_lines(lines)
        return
    in_fence = False
    in_frontmatter = False
    fm_open_quote = None
    fm_block_indent = None
    for number, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if number == 1 and stripped == "---":
            in_frontmatter = True
            continue
        if in_frontmatter:
            if fm_open_quote is not None:
                # A line inside a spanning quoted scalar is
                # prose in full, whatever shape its first words
                # take, in the same reading the YAML prose
                # reader gives such a line. Judging the line by
                # its own shape would read a key shaped
                # continuation as a key and judge only the words
                # after its colon, so the colon itself and the
                # words before it would escape the bar.
                yield number, clean(raw)
                if _closes_quote(raw, fm_open_quote):
                    fm_open_quote = None
                continue
            indent = len(raw) - len(raw.lstrip())
            if fm_block_indent is not None:
                if stripped and indent <= fm_block_indent:
                    fm_block_indent = None
                else:
                    if stripped:
                        yield number, clean(raw)
                    continue
            if stripped == "---":
                in_frontmatter = False
            elif FRONTMATTER_KEY.match(raw):
                # The key is syntax. The value after it stays prose.
                value = raw.split(":", 1)[1]
                yield number, clean(value)
                fm_open_quote = _spanning_quote(value)
                if YAML_BLOCK.search(raw):
                    fm_block_indent = indent
            else:
                yield number, clean(raw)
                fm_open_quote = _spanning_quote(raw)
            continue
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if LINK_REFERENCE.match(raw):
            continue
        if BARE_PATH.match(stripped):
            continue
        if HTML_TAG_LINE.match(stripped):
            continue
        yield number, clean(raw)


def _flow_parts(text):
    """Split a flow body on its top level commas.

    Commas inside quotes or inside a nested flow collection do
    not split, so a quoted prose value keeps its shape whole.
    """
    parts = []
    depth = 0
    quote = None
    start = 0
    index = 0
    while index < len(text):
        char = text[index]
        if quote is not None:
            if char == "\\" and quote == '"':
                index += 1
            elif char == quote:
                quote = None
        elif char in "\"'" and _opens_quote(text, index):
            quote = char
        elif char in "{[":
            depth += 1
        elif char in "}]":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(text[start:index])
            start = index + 1
        index += 1
    parts.append(text[start:])
    return parts


def _flow_value_values(value):
    """Yield the prose inside one flow value."""
    value = _strip_value_prefix(value)
    if value.startswith("{") or value.startswith("["):
        yield from flow_prose_values(value)
    elif value:
        yield value


def flow_prose_values(text):
    """Yield the scalar values inside a flow collection.

    The brackets and the key marks of a flow collection are
    structure and stay exempt. A value standing inside one can
    still be a prose sentence a reader meets, quoted or plain, so
    each value is yielded for the scan in the same way a block
    value is. A nested flow collection yields the values inside
    it, whether it stands as a mapping value, as a list item, or
    inside another flow collection. A bare entry of a flow
    sequence is a value and is yielded, while a bare key of a
    flow mapping names a null value and stays exempt.
    """
    text = text.strip()
    if text.startswith("{"):
        close = _flow_close_index(text)
        for part in _flow_parts(text[1:close]):
            part = part.strip()
            if not part:
                continue
            split = _split_key(part, flow=True)
            if split:
                yield from _flow_value_values(split[1])
        trailing = text[close + 1:].strip()
        if trailing:
            # Text standing after the collection on its line,
            # a trailing comment above all, is prose the reader
            # meets and it is judged like any other comment.
            yield trailing
        return
    if text.startswith("["):
        close = _flow_close_index(text)
        for part in _flow_parts(text[1:close]):
            part = part.strip()
            if not part:
                continue
            if part.startswith("{") or part.startswith("["):
                yield from flow_prose_values(part)
                continue
            split = _split_key(part, flow=True)
            if split:
                yield from _flow_value_values(split[1])
            else:
                yield part
        trailing = text[close + 1:].strip()
        if trailing:
            yield trailing
        return
    yield text


def _closes_quote(text, quote):
    """Whether a line closes a quoted scalar opened earlier."""
    index = 0
    while index < len(text):
        char = text[index]
        if char == "\\" and quote == '"':
            index += 2
            continue
        if char == quote:
            if quote == "'" and text[index + 1:index + 2] == "'":
                index += 2
                continue
            return True
        index += 1
    return False


def _yaml_carried_state(raw, stripped, indent, number, state):
    """Run the carried state checks for one YAML line.

    Returns a pair of a carried flag and the spans the carried
    state yields for this line. A line inside a block scalar, a
    spanning quoted scalar or an unfinished flow collection is
    prose of that carried shape and never reaches the line
    reader below. The three carried shapes never stand active
    together, because each one is entered from the line reader
    only while the others are clear and each consumes every
    line until it closes.
    """
    if state["block_indent"] is not None:
        if stripped and indent <= state["block_indent"]:
            state["block_indent"] = None
        else:
            spans = [(number, clean(raw))] if stripped else []
            return True, spans
    if state["open_quote"] is not None:
        # A line inside a spanning quoted scalar is prose in
        # full, whatever shape its first words take.
        spans = [(number, clean(raw))]
        if _closes_quote(raw, state["open_quote"]):
            state["open_quote"] = None
        return True, spans
    if state["flow_buffer"] is not None:
        state["flow_buffer"].append(stripped)
        joined = "\n".join(state["flow_buffer"])
        if _flow_complete(joined):
            spans = [
                (state["flow_start"], clean(value))
                for value in flow_prose_values(joined)
            ]
            state["flow_buffer"] = None
            return True, spans
        return True, []
    return False, []


def _yaml_flow_yields(text, number, state):
    """The prose spans of one flow collection standing on a line.

    A complete collection is read by the flow reader at once. An
    incomplete one is buffered into the carried state and read
    whole when its closing line arrives.
    """
    if _flow_complete(text):
        return [
            (number, clean(value)) for value in flow_prose_values(text)
        ]
    state["flow_buffer"] = [text]
    state["flow_start"] = number
    return []


def _yaml_key_value(split, number, candidate_col, state):
    """The prose spans of the value on one key line.

    A flow value is read by the flow reader, a quoted value is
    yielded whole with its spanning state recorded when it does
    not close on its line, and a plain value is yielded with the
    key column recorded so a more indented line after it reads
    as its continuation.
    """
    _key, value = split
    state["plain_key_col"] = None
    if not value:
        return []
    value = _strip_value_prefix(value)
    if not value:
        return []
    if value.startswith("{") or value.startswith("["):
        # A flow collection standing as a key value, after any
        # anchor or tag tokens, is read by the flow reader.
        return _yaml_flow_yields(value, number, state)
    if value[0] in "\"'":
        if _quoted_end(value) is None:
            state["open_quote"] = value[0]
        return [(number, clean(value))]
    state["plain_key_col"] = candidate_col
    return [(number, clean(value))]


def yaml_prose_lines(lines):
    """Yield the prose of a YAML file.

    Comments are prose. So are block scalar bodies and the plain or
    quoted values on key lines and the scalar values inside flow
    collections. Keys and structure are syntax.

    The reader is stateful where YAML is. A scalar that spans
    lines carries its state with it, so a continuation line is
    yielded as prose in full even when it is shaped like a key,
    because inside a spanning scalar it is prose and not a key. A
    flow collection that spans lines is gathered until it closes
    and then read by the flow reader as one collection. A plain
    scalar opened by a key continues only on lines indented past
    the column its key stands in, so the next key of the same
    mapping, standing at the same column, is never swallowed as
    a continuation.
    """
    state = {
        "block_indent": None,
        "open_quote": None,
        "flow_buffer": None,
        "flow_start": 0,
        "plain_key_col": None,
    }
    for number, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        indent = len(raw) - len(raw.lstrip())
        carried, spans = _yaml_carried_state(
            raw, stripped, indent, number, state
        )
        yield from spans
        if carried:
            continue
        if not stripped:
            continue
        if stripped.startswith("#"):
            body = stripped.lstrip("#").strip()
            # Editor directives are machine syntax, not prose.
            if body.startswith("yaml-language-server"):
                continue
            yield number, clean(body)
            continue
        if YAML_BLOCK.search(raw):
            state["block_indent"] = indent
            state["plain_key_col"] = None
            continue
        plain_key_col = state["plain_key_col"]
        if plain_key_col is not None:
            if indent > plain_key_col:
                # A line inside a spanning plain scalar is prose
                # in full, whatever shape its first words take.
                yield number, clean(raw)
                continue
            state["plain_key_col"] = None
        candidate = stripped
        while candidate.startswith("- "):
            # Repeated list markers are structure too, so a nested
            # sequence of mappings is stripped to its inner key.
            candidate = candidate[2:].lstrip()
        candidate_col = len(raw.rstrip()) - len(candidate)
        flow_text = _strip_value_prefix(candidate)
        if flow_text.startswith("{") or flow_text.startswith("["):
            yield from _yaml_flow_yields(flow_text, number, state)
            state["plain_key_col"] = None
            continue
        split = _split_key(candidate)
        if split:
            yield from _yaml_key_value(
                split, number, candidate_col, state
            )
            continue
        if candidate and candidate[0] in "\"'" \
                and _quoted_end(candidate) is None:
            yield number, clean(candidate)
            state["open_quote"] = candidate[0]
            state["plain_key_col"] = None
            continue
        yield number, clean(candidate)
        if candidate and candidate[0] not in "{[\"'":
            state["plain_key_col"] = candidate_col
    if state["flow_buffer"] is not None:
        for value in flow_prose_values(
            "\n".join(state["flow_buffer"])
        ):
            yield state["flow_start"], clean(value)

def comment_spans(path):
    """Yield (number, text) pairs for the comment spans of a file."""
    lines = path.read_text(encoding="utf-8").splitlines()
    for number, raw in enumerate(lines, start=1):
        for index, char in enumerate(raw):
            if char == "#" and (index == 0 or raw[index - 1] in " \t"):
                body = raw[index + 1:].strip()
                # Editor directives are machine syntax, not prose.
                if body.startswith("yaml-language-server"):
                    break
                if body:
                    yield number, clean(body)
                break


def display_name(path):
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def scan(violations, path, spans):
    for number, text in spans:
        where = "%s line %d" % (display_name(path), number)
        if EM_DASH in text:
            violations.append("%s has an em dash" % where)
        if EN_DASH in text:
            violations.append("%s has an en dash" % where)
        if ";" in text:
            violations.append("%s has a semicolon" % where)
        if ":" in text:
            violations.append("%s has a colon in prose" % where)


PROSE_VALUE_KEYS = (
    "description",
    "longDescription",
    "shortDescription",
    "note",
    "defaultPrompt",
)


def collect_list_strings(key, items, values):
    """Collect the strings inside a list a prose key holds.

    A string item is collected under the key's name. A
    dictionary item is searched as a manifest in its own
    right. A list item is walked by this same reading, so
    the strings inside a list inside the list are collected
    under the key's name as well.
    """
    for item in items:
        if isinstance(item, str):
            values.append((key, item))
        elif isinstance(item, list):
            collect_list_strings(key, item, values)
        else:
            values.extend(description_values(item))


def description_values(data):
    """Every prose value in a parsed manifest, at any depth.

    The collected keys are the plain description key, the two
    longer listing description keys the portable manifest
    carries under its OpenAI extension, and the note key its
    extension objects carry, because all four are prose a
    listing reader meets and none may stand outside the bar
    the plain description already stands under. The default
    prompt key of the same OpenAI interface object joins
    them, holding a list of suggested prompt sentences a
    listing reader also meets, so the strings inside that
    list are collected under its name as well. Any of the
    collected keys may hold a list of strings rather than
    one string, and the strings inside such a list are
    collected under the key's name the same way, because a
    reader meets them as the same prose in list dress.
    A list inside such a list is walked the same way, so a
    string at any depth inside the list a collected key
    holds is collected under that key's name.
    Each value travels with the key it stood under, so a
    violation can name the field that carries it.
    """
    values = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key in PROSE_VALUE_KEYS and isinstance(value, str):
                values.append((key, value))
            elif key in PROSE_VALUE_KEYS and isinstance(
                value, list
            ):
                collect_list_strings(key, value, values)
            else:
                values.extend(description_values(value))
    elif isinstance(data, list):
        for item in data:
            values.extend(description_values(item))
    return values


def scan_manifest(violations, path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        violations.append(
            "%s does not parse for the copy scan: %s"
            % (display_name(path), exc)
        )
        return
    for key, value in description_values(data):
        text = clean(value)
        where = "%s %s field" % (display_name(path), key)
        if EM_DASH in text:
            violations.append("%s has an em dash" % where)
        if EN_DASH in text:
            violations.append("%s has an en dash" % where)
        if ";" in text:
            violations.append("%s has a semicolon" % where)
        if ":" in text:
            violations.append("%s has a colon in prose" % where)


MARKDOWN_LINK = re.compile(
    r"!?\[[^\]]*\]\((<[^>]+>|[^\s)]+)"
    r"(?:\s+[\"'][^\"']*[\"'])?\s*\)"
)
LINK_REFERENCE_TARGET = re.compile(r"^\s*\[[^\]]+\]:\s*(\S+)")
LINK_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
HTML_HREF = re.compile(
    r"<a\s[^>]*?href\s*=\s*[\"']([^\"']+)[\"']", re.IGNORECASE
)
SPLIT_DESTINATION = re.compile(r"^\s*(<[^>]+>|[^\s)]+)")
SPLIT_PAREN_DESTINATION = re.compile(
    r"^\s*\(\s*(<[^>]+>|[^\s)]+)"
)


def split_link_target(lines, index, text):
    """The target of a link split over two lines, or None.

    The Markdown grammar these pages render under reads an
    inline link as one link even when the destination
    stands on the line after the opening bracket, so the
    per line pattern never sees it. The destination line is
    the line after the opening line in either split shape,
    the bracket closing with an open parenthesis at the end
    of the opening line, or the parenthesis opening the
    following line.
    """
    if index + 1 >= len(lines):
        return None
    following = INLINE_CODE.sub("", lines[index + 1])
    if re.search(r"\]\(\s*$", text):
        match = SPLIT_DESTINATION.match(following)
        return match.group(1) if match else None
    if re.search(r"\]\s*$", text):
        match = SPLIT_PAREN_DESTINATION.match(following)
        return match.group(1) if match else None
    return None


def link_target_problems(path):
    """Problems with relative Markdown link targets in one file.

    A relative target names a file in the tree, so a target
    that resolves to nothing is a dead link a reader meets
    under a green gate. External addresses and anchors and
    absolute paths stand outside this check and no address
    is ever fetched. Links inside fenced blocks and inline
    code spans are examples and not references, so they are
    skipped in the same way the prose scan skips them. A
    link whose destination stands on the line after its
    opening bracket is read as one link and reported at the
    line where it opens, and an anchor element href naming
    a relative target is checked the same way, with
    external schemes and pure anchors still skipped.
    """
    problems = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        return [
            "%s cannot be read as UTF-8 text, %s"
            % (display_name(path), exc)
        ]
    in_fence = False
    for index, raw in enumerate(lines):
        number = index + 1
        stripped = raw.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        text = INLINE_CODE.sub("", raw)
        targets = [
            match.group(1) for match in MARKDOWN_LINK.finditer(text)
        ]
        ref = LINK_REFERENCE_TARGET.match(text)
        if ref:
            targets.append(ref.group(1))
        targets.extend(HTML_HREF.findall(text))
        split = split_link_target(lines, index, text)
        if split:
            targets.append(split)
        for target in targets:
            target = target.strip("<>")
            if not target or target.startswith(("#", "/")):
                continue
            if LINK_SCHEME.match(target):
                continue
            rel_target = target.split("#", 1)[0].split("?", 1)[0]
            if not rel_target:
                continue
            if not (path.parent / unquote(rel_target)).exists():
                problems.append(
                    "%s line %d links to %s, which does not "
                    "stand in the tree"
                    % (display_name(path), number, target)
                )
    return problems


def census_problems(root=None):
    """Problems with the prose census the fence stands on.

    The floor is read from a fresh discovery over the root
    rather than from the module level sets, so the reading
    names the tree as it stands when the gate runs. The
    root README is a required prose surface, and a census
    of zero prose files certifies nothing at all.
    """
    root = ROOT if root is None else root
    problems = []
    prose = discover_prose_files(root)
    if not prose:
        problems.append(
            "the copy fence discovered no prose files, so "
            "its census stands at zero and the bar certifies "
            "nothing"
        )
    readme = root / "README.md"
    if not readme.is_file():
        problems.append(
            "README.md is missing, and the copy fence "
            "requires it as a prose surface"
        )
    elif readme not in prose:
        problems.append(
            "README.md stands outside the copy fence "
            "discovery, so the bar never reads it"
        )
    return problems


def main():
    violations = []
    violations.extend(census_problems())
    for path in PROSE_FILES:
        if not path.is_file():
            violations.append("%s is missing" % display_name(path))
            continue
        try:
            scan(violations, path, prose_lines(path))
        except (OSError, UnicodeDecodeError) as exc:
            violations.append(
                "%s cannot be read as UTF-8 text, %s"
                % (display_name(path), exc)
            )
            continue
        if path.suffix in (".md", ".mdc"):
            violations.extend(link_target_problems(path))
    for path in COMMENT_FILES:
        if not path.is_file():
            violations.append("%s is missing" % display_name(path))
            continue
        try:
            scan(violations, path, comment_spans(path))
        except (OSError, UnicodeDecodeError) as exc:
            violations.append(
                "%s cannot be read as UTF-8 text, %s"
                % (display_name(path), exc)
            )
    for path in MANIFEST_FILES:
        if not path.is_file():
            violations.append("%s is missing" % display_name(path))
            continue
        scan_manifest(violations, path)
    if violations:
        for violation in violations:
            print("check_copy: %s" % violation, file=sys.stderr)
        return 1
    print(
        "check_copy: copy bar holds on %d prose files, the "
        "description fields of %d plugin manifests and the "
        "comment prose of %d config files"
        % (len(PROSE_FILES), len(MANIFEST_FILES), len(COMMENT_FILES))
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
