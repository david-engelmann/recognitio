#!/usr/bin/env python3
"""Pin the Build 20 Comate adaptation.

Build 20 carries recognitio into Baidu Comate, which
consumes the community skill folder format. The canonical
skill already stands at .agents/skills/recognitio, one of
the two project paths the implementer record names for
Comate, so the build adds a byte identical copy of the
whole canonical folder at .comate/skills/recognitio for the
native project path and ships no manifest, package file,
or registration artifact, because none is evidenced at
either scope. This script pins that arrangement without a
Comate host. The .comate tree must hold the skill copy and
no manifest, package, registration artifact, or stray file
beside it, with bytecode caches excluded as build state
the way every copy gate in this repo excludes them, so no
manifest or plugin file can grow beside the copy and read
as a Comate registration the record never evidenced. The
copy must stay byte identical to the canonical skill as a
real directory of files, so the two project seats can never
drift into two instruction sources. The brief at
docs/comate-brief.md must state the format, the two project
paths, the user scope path as guidance, the absent listing,
and the client run with its sign in wall. Every rule in it
must carry a derivation note naming a canonical skill
section or a checkable citation from that rule's own
expected set, and the contradiction reader below refuses
the claim families the build's honesty negates, a live
session result, extractor execution under Comate, a
marketplace or store listing, a settled form of any open
question, an accepted submission, and any sentence that
withdraws a pinned claim, on every surface that carries
the claims. The families are phrasing classes, and a
meaning based paraphrase outside them stays a human review
surface, the limit recorded for every stem gate in this
repo. Decision 32 must record the build with its decision
4 statement.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CANONICAL_TREE = ".agents/skills/recognitio"
COMATE_TREE = ".comate/skills/recognitio"

BRIEF_SENTENCES = (
    (
        "the skill format",
        "A Comate skill is a folder named for the skill "
        "holding a SKILL.md file",
    ),
    (
        "the no manifest position",
        "No manifest file, package file, or registration step "
        "is evidenced for the folder itself at either scope",
    ),
    (
        "the user scope path",
        "The user scope path is `~/.comate/skills/recognitio/`",
    ),
    (
        "the two project paths",
        "The project scope record names two paths together, "
        "the canonical `.agents/skills/recognitio/` and the "
        "native `.comate/skills/recognitio/`",
    ),
    (
        "the auto discovery record",
        "with project skills auto discovered on the same record",
    ),
    (
        "the byte identical copy",
        "stands byte identical to the canonical skill, pinned "
        "by the gate at `scripts/check_comate.py`",
    ),
    (
        "the no listing honesty sentence",
        "No Comate skill marketplace, skill store, or "
        "submission route is evidenced, and this build ships "
        "no submission pack",
    ),
    (
        "the unverified remainder",
        "Invocation inside a live Comate session stays "
        "unverified",
    ),
    (
        "the frontmatter open question",
        "Whether Comate ignores the canonical frontmatter "
        "fields beyond name and description, rejects the file, "
        "or misreads them stays unverified",
    ),
    (
        "the script execution open question",
        "Whether a skill invoked in Comate gets shell access "
        "to run a bundled script stays unverified",
    ),
    (
        "the size open question",
        "Any Comate side limit on the length of a SKILL.md "
        "file stays unverified",
    ),
    (
        "the precedence open question",
        "Which copy a client reads when the skill stands at "
        "both project paths and at the user path stays "
        "unverified",
    ),
    (
        "the installer version",
        "The official Linux installer record names Comate AI "
        "IDE 3.11.5 for linux x64",
    ),
    (
        "the download hash match",
        "The downloaded tarball matched the SHA-256 hash the "
        "installer record publishes",
    ),
    (
        "the client launch",
        "The desktop client opened under a virtual display on "
        "this box with a scratch home",
    ),
    (
        "the unopened project",
        "the project never stood open as a workspace",
    ),
    (
        "the sign in wall",
        "The agent surface presents a log in button and no "
        "task surface before a sign in",
    ),
    (
        "the blocker",
        "The one missing piece is a sign in, by Baidu account "
        "or by license, that only the owner can complete",
    ),
    (
        "the trust posture rule",
        "The trust posture stands unchanged on Comate",
    ),
    (
        "the announcement tier",
        "The 4.0 announcement was read by the parent seat in "
        "a live browser, and this lane's own read of its text "
        "is still owed",
    ),
    (
        "the directed placement",
        "The scoping record held placement guidance to the "
        "brief until a live client proved more",
    ),
)

RULES_HEADING = "## The Comate rules"

# The contradiction reader works sentence by sentence over
# every surface that carries the build's claims. A sentence
# is refused when it asserts one of the claim families the
# honesty sentences negate, in the phrasings the families
# cover. The honest forms never assert these families,
# because each honest sentence negates or scopes the claim
# it makes. Matching is case folded, because a claim that
# opens a sentence capitalises its first word and the
# refusal has to hold there too.
SESSION_VERB = re.compile(
    r"\b(invoked|exercised|verified|ran|runs|executed|"
    r"loaded|discovered)\b"
)
SESSION_PLACE = re.compile(
    r"(live|signed in|signed-in) comate session|"
    r"session with comate|session inside the client"
)
SESSION_NEGATED = re.compile(
    r"\b(has|have|had|was|were|is|are) not\b|\bnot been\b|"
    r"\bnever\b"
)
SESSION_STATUS = (
    "stays unverified",
    "stands unverified",
    "stand unverified",
    "is unverified",
    "remains unverified",
)
EXTRACTOR_STEMS = (
    "comate executed",
    "comate executes",
    "comate ran the",
    "comate runs the",
    "executed by comate",
    "executed under comate",
    "runs under comate",
    "ran under comate",
)
MARKET_STEMS = (
    "listed in the comate",
    "listed on the comate",
    "comate skill store",
    "comate marketplace listing",
    "submitted to a comate",
    "submitted to the comate",
    "submission to comate",
    "stands in the comate",
    "available in the comate",
    "available on the comate",
)
SETTLED_STEMS = (
    "frontmatter is settled",
    "frontmatter are settled",
    "precedence is settled",
    "comate ignores the fields",
    "comate ignores unknown fields",
    "ignores the fields beyond name and description",
    "takes precedence over the canonical",
    "takes precedence over the .agents",
    "the native copy takes precedence",
    "the size limit is settled",
)
SUBMISSION_STEMS = (
    "submission pack was accepted",
    "submission was accepted",
    "pack was accepted",
    "was submitted to a comate",
    "stands submitted",
)
WITHDRAWAL_STEMS = (
    "it is false that",
    "it is no longer true that",
    "no longer true that",
    "opens without any sign in",
    "without any sign in",
    "replaced by a hand edited",
    "hand edited comate",
    "contrary to the withdrawn claim",
)

README_LINK = "[the Comate brief](docs/comate-brief.md)"
README_COPY_SENTENCE = (
    "a byte identical copy at `.comate/skills/recognitio/`"
)
README_MARKETPLACE_SENTENCE = (
    "no Comate skill marketplace or submission route is "
    "evidenced"
)

# Canonical skill sections a derivation note may name. These are
# the section titles of .agents/skills/recognitio/SKILL.md, and
# a note that names one says which canonical section the rule
# restates.
CANONICAL_SECTIONS = {
    "Purpose",
    "Input modes",
    "Workflow",
    "Choosing tiers",
    "Fanning out",
    "Escalation",
    "Stamping the gate report",
    "The tier model",
    "Completeness discipline",
    "Re-review",
    "Trust and limits",
    "The boundary",
}

# Citations a derivation note may name, written as stems so the
# note pins the surface the claim was read from. The first tier
# is the Baidu primary material the build lane read itself, the
# second is the implementer record on the Visual Studio
# Marketplace, and the last two are repo records whose
# precedents the rules rest on.
PRIMARY_CITATIONS = (
    "comate.baidu.com/zh/news/news/36",
    "Rebekah.personal-kb",
    "Microi.v8-engine",
    "docs/qwen-code-brief.md",
    "docs/cursor-plugin-brief.md",
)

# The citation set each rule's own derivation note must draw
# from, so a note swapped in from another rule fails even
# though it names a real source. A canonical section title
# counts where the rule restates the canonical skill beside
# its citation.
EXPECTED_CITATIONS = {
    1: (
        "Rebekah.personal-kb",
        "Microi.v8-engine",
        "comate.baidu.com/zh/news/news/36",
    ),
    2: ("Microi.v8-engine",),
    3: ("Microi.v8-engine",),
    4: ("Rebekah.personal-kb",),
    5: (
        "comate.baidu.com/zh/news/news/36",
        "docs/qwen-code-brief.md",
    ),
    6: ("Rebekah.personal-kb", "Microi.v8-engine"),
    7: ("docs/cursor-plugin-brief.md", "Trust and limits"),
    8: ("Trust and limits", "The boundary", "Decision 4"),
}

# A derivation note that negates the citation it names derives
# nothing from it, so the negated forms are refused in the
# note itself.
NEGATED_CITATIONS = (
    "not microi.v8-engine",
    "not rebekah.personal-kb",
    "rejected decision 4",
    "not decision 4",
)


def is_bytecode_cache(path):
    """Whether a path is a compiled bytecode cache file.

    Only a bytecode file standing inside a cache directory is
    build state. A cache name alone excludes nothing, so a
    manifest or plugin file wearing a cache folder name or a
    cache suffix is counted like any other file, which is the
    census blindness rounds 286 and 294 filed. The bytecode
    file must stand directly in the cache directory, the one
    shape an interpreter writes, so a payload nested below a
    cache directory is counted like any other file.
    """
    return (
        len(path.parts) >= 2
        and path.parts[-2] == "__pycache__"
        and path.suffix == ".pyc"
    )


def tree_bytes(directory):
    """Map every file under a directory to its bytes.

    Compiled bytecode caches are build state, not skill content,
    so bytecode cache files are excluded the way the other copy
    gates exclude them. The exclusion is keyed on the bytecode
    shape alone, so a file that merely wears a cache name is
    read and compared like any other file.
    """
    found = {}
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        if is_bytecode_cache(path):
            continue
        rel = str(path.relative_to(directory))
        found[rel] = path.read_bytes()
    return found


def symlink_problems(root, rel, problems):
    """Problems with a symlink on any component of a pinned path.

    A byte pin certifies content, not containment, and a leaf
    check alone lets a linked parent directory carry the whole
    surface outside the tree, so every component of the path
    is refused in turn.
    """
    current = root
    prefix = []
    for part in Path(rel).parts:
        current = current / part
        prefix.append(part)
        if current.is_symlink():
            problems.append(
                "%s passes through the symlink %s, so the pinned "
                "surface stands outside the tree it names"
                % (rel, "/".join(prefix))
            )
            return


def read_text(root, rel, problems, label):
    """Read one pinned text file, recording any problem."""
    path = root / rel
    if path.exists() and not path.is_file():
        problems.append(
            "%s cannot be read, it is not a regular file" % label
        )
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        problems.append("%s is missing" % label)
        return None


def placement_problems(root, problems):
    """Problems with the .comate tree and its skill copy."""
    comate = root / ".comate"
    if comate.is_symlink():
        problems.append(
            ".comate is a symlink, so the native seat stands "
            "outside the tree it names"
        )
        return
    if not comate.is_dir():
        problems.append(
            ".comate is missing, so the native Comate project "
            "path carries no skill copy"
        )
        return
    # A cache directory is excluded only when everything under
    # it is a bytecode cache file. A cache directory holding
    # anything else stands in the census whole, so a manifest
    # or plugin file inside it is named as the stray it is.
    pure_cache_dirs = set()
    for path in comate.rglob("__pycache__"):
        if path.is_dir() and all(
            is_bytecode_cache(item)
            for item in path.rglob("*")
            if item.is_file()
        ):
            pure_cache_dirs.add(path)
    census = sorted(
        str(path.relative_to(comate))
        for path in comate.rglob("*")
        if not any(
            cache in path.parents or cache == path
            for cache in pure_cache_dirs
        )
    )
    copy_dir = comate / "skills" / "recognitio"
    canonical = root / CANONICAL_TREE
    if not canonical.is_dir():
        problems.append("the canonical skill directory is missing")
        return
    canonical_files = tree_bytes(canonical)
    expected = sorted(
        set(
            ["skills", "skills/recognitio"]
            + [
                "skills/recognitio/" + str(Path(name).parent)
                for name in canonical_files
                if str(Path(name).parent) != "."
            ]
            + ["skills/recognitio/" + name for name in canonical_files]
        )
    )
    if census != expected:
        if copy_dir.is_symlink():
            # The census is short because the walk does not
            # descend into the linked seat, so only entries
            # outside the expectation are a beside the copy
            # problem here. The symlink itself is refused
            # below, and naming it as a stray file would
            # misdiagnose the failure.
            extras = sorted(set(census) - set(expected))
            if extras:
                problems.append(
                    ".comate holds %r beside the linked seat, "
                    "so a manifest, package, or stray file "
                    "stands as a registration the record never "
                    "evidenced" % (extras,)
                )
        else:
            problems.append(
                ".comate holds %r, not the skill copy alone, so a "
                "manifest, package, or stray file stands beside the "
                "copy as a registration the record never evidenced"
                % (census,)
            )
    if copy_dir.is_symlink():
        problems.append(
            ".comate/skills/recognitio is a symlink, so the "
            "native seat is not the real directory of files the "
            "copy discipline ships"
        )
        return
    if not copy_dir.is_dir():
        problems.append(".comate/skills/recognitio is not a directory")
        return
    copy_files = tree_bytes(copy_dir)
    for name in sorted(set(copy_files) | set(canonical_files)):
        if name not in canonical_files:
            problems.append(
                ".comate/skills/recognitio carries an extra file "
                "%s the canonical skill does not hold" % name
            )
        elif name not in copy_files:
            problems.append(
                ".comate/skills/recognitio is missing the file "
                "%s the canonical skill holds" % name
            )
        elif copy_files[name] != canonical_files[name]:
            problems.append(
                ".comate/skills/recognitio/%s drifts from the "
                "canonical skill" % name
            )


def rules_section(raw):
    """The text of the rules section, or None when it is missing."""
    start = raw.find(RULES_HEADING)
    if start < 0:
        return None
    rest = raw[start + len(RULES_HEADING):]
    match = re.search(r"(?m)^## ", rest)
    if match:
        rest = rest[:match.start()]
    return rest


def deliberate_source(note):
    """Whether the derivation note names a source on purpose.

    A bare substring match lets a note mention a canonical
    section title in passing prose without deriving from it, so
    a section title counts only when it is named as the source,
    right after the canonical skill attribution marker. Primary
    and implementer citation stems and Decision 4 are rare
    enough to match as substrings.
    """
    for title in CANONICAL_SECTIONS:
        if re.search(
            r"canonical skill[^.;]{0,200}" + re.escape(title), note
        ):
            return True
    if any(stem in note for stem in PRIMARY_CITATIONS):
        return True
    return "Decision 4" in note


def derivation_problems(section):
    """Problems with the rules derivation discipline."""
    problems = []
    parts = re.split(r"(?m)^### C(\d+)\.", section)
    numbers = parts[1::2]
    blocks = parts[2::2]
    if not blocks:
        return ["the rules section carries no C numbered rules"]
    if numbers != [str(n) for n in range(1, 9)]:
        problems.append(
            "the rules section carries rules %s, not C1 to C8 "
            "in order, so a dropped or renumbered rule would "
            "stand unpinned" % (", ".join("C" + n for n in numbers),)
        )
    for number, block in zip(numbers, blocks):
        index = int(number)
        flat = " ".join(block.split())
        if "Derives from" not in flat:
            problems.append(
                "rule C%d carries no derivation note, so it would "
                "be a rival instruction source" % index
            )
            continue
        note = flat.split("Derives from", 1)[1]
        if not deliberate_source(note):
            problems.append(
                "rule C%d names no canonical skill section or "
                "checkable citation in its derivation note" % index
            )
            continue
        folded_note = note.lower()
        if any(stem in folded_note for stem in NEGATED_CITATIONS):
            problems.append(
                "rule C%d negates the citation its derivation "
                "note names, so the note derives nothing from "
                "it" % index
            )
            continue
        expected = EXPECTED_CITATIONS.get(index, ())
        if expected and not any(stem in note for stem in expected):
            problems.append(
                "rule C%d names none of its own expected "
                "citations in its derivation note, so the note "
                "could stand under another rule unchanged"
                % index
            )
    return problems


def sentences_of(text):
    """The sentences of a text, flattened the way the pins read."""
    flat = " ".join(text.split())
    return [
        piece.strip()
        for piece in re.split(r"(?<=[.!?])\s+", flat)
        if piece.strip()
    ]


def sentence_families(sentence):
    """The claim families one folded sentence asserts.

    Each family returns the refusal phrase the problem
    message carries. The session family needs an assertive
    verb at a Comate session place with no negation on the
    verb and no unverified status word, so the honest
    negated and scoped forms pass. The marketplace family
    yields to a sentence that scopes itself to the
    evidenced record.
    """
    families = []
    if any(stem in sentence for stem in WITHDRAWAL_STEMS):
        families.append("withdraws a pinned claim")
    if (
        SESSION_VERB.search(sentence)
        and SESSION_PLACE.search(sentence)
        and not SESSION_NEGATED.search(sentence)
        and not any(status in sentence for status in SESSION_STATUS)
    ):
        families.append(
            "the skill was invoked in a live Comate session"
        )
    if any(stem in sentence for stem in EXTRACTOR_STEMS):
        families.append("Comate runs the bundled extractor")
    evidenced = "evidenced" in sentence and (
        "no " in sentence or "not " in sentence or "never" in sentence
    )
    if not evidenced and any(
        stem in sentence for stem in MARKET_STEMS
    ):
        families.append("submitted to a Comate marketplace")
    if any(stem in sentence for stem in SETTLED_STEMS):
        families.append("an open Comate question stands settled")
    if any(stem in sentence for stem in SUBMISSION_STEMS):
        families.append("a Comate submission stands accepted")
    return families


def contradiction_problems(text, surface, beside=None):
    """Problems with claims that contradict the honesty pins.

    The build's honesty rests on the negatives its sentences
    pin, that invocation in a live session stays unverified,
    that the bundled extractor is not stated to run under
    Comate, that no marketplace or submission route is
    evidenced, and that the open questions stand open. A
    presence pin cannot stop an appended sentence from
    claiming the opposite, so the claim families are refused
    on every surface that carries the claims, read over the
    whole file so a claim cannot hide outside the section a
    slice would read.
    """
    beside = beside or "the pinned honesty sentences"
    problems = []
    for sentence in sentences_of(text):
        for family in sentence_families(sentence.lower()):
            problems.append(
                "%s claims %s beside %s"
                % (surface, family, beside)
            )
    return problems


COMATE_HEADING_RE = re.compile(
    r"^###[ \t]+Comate(?:[ \t]+#+)?[ \t]*$")
FENCE_OPEN_RE = re.compile(r"(```+|~~~+)(.*)$")
FENCE_CLOSE_RE = re.compile(r"(```+|~~~+)[ \t]*$")

# Raw text elements whose content a reader never renders as
# markdown, so a heading line inside one is literal text
# until the closing tag stands.
RAW_TEXT_TAGS = {"pre", "script", "style", "textarea"}

# The block level tags of the rendered HTML block family.
# A block opened by one of them runs until a blank line, and
# its content lines are HTML rather than markdown, so no
# heading inside one renders as a heading.
HTML_BLOCK_TAGS = {
    "address", "article", "aside", "base", "basefont",
    "blockquote", "body", "caption", "center", "col",
    "colgroup", "dd", "details", "dialog", "dir", "div",
    "dl", "dt", "fieldset", "figcaption", "figure", "footer",
    "form", "frame", "frameset", "h1", "h2", "h3", "h4",
    "h5", "h6", "head", "header", "hr", "html", "iframe",
    "search",
    "legend", "li", "link", "main", "menu", "menuitem",
    "nav", "noframes", "ol", "optgroup", "option", "p",
    "param", "section", "source", "summary", "table",
    "tbody", "td", "tfoot", "th", "thead", "title", "tr",
    "track", "ul",
}
HTML_TAG_RE = re.compile(r"<(/?)([A-Za-z][A-Za-z0-9]*)\b[^>]*>")
LIST_MARKER_RE = re.compile(
    r"(?:[-+*]|[0-9]{1,9}[.)])[ \t]+(.*)$")
BARE_LIST_MARKER_RE = re.compile(
    r"([-+*]|[0-9]{1,9}[.)])[ \t]*$")
LONE_TAG_LINE_RE = re.compile(
    r"(?:</?[A-Za-z][A-Za-z0-9]*\b[^>]*>\s*)+$")


def indent_columns(line):
    """The rendered indent of a line in columns.

    A space counts one column and a tab counts to the next
    multiple of four, the reading a renderer gives them, so
    a space and a tab together carry a line to the fourth
    column just as four spaces do.
    """
    columns = 0
    for char in line:
        if char == " ":
            columns += 1
        elif char == "\t":
            columns += 4 - (columns % 4)
        else:
            break
    return columns


def comate_subsection_stands(readme):
    """Whether the Comate heading stands in the rendered document.

    The heading is read in the structure a reader renders.
    Lines inside a fenced code block and text inside an HTML
    comment are not headings of the document, so neither can
    stand in for the subsection, and the closed ATX form,
    where a run of hash marks closes the heading after a
    space, names the same subsection as the open form. The
    separator after the hash marks is any run of spaces or
    tabs, because a rendered heading allows more than one.
    A line carried to the fourth column by its indent, by
    spaces or by a tab or by both together, is an indented
    code block, because an ATX heading allows at most three
    columns of indent, and a closing fence indented that far
    does not close its fence either. A fence line carrying an
    info string cannot close a fenced block, and a backtick
    fence line whose info string carries a backtick is no
    fence at all, so a heading after one stands in the open.
    The content of an HTML block is not markdown, whether the
    block is a raw text element running to its closing tag or
    a block level element running to a blank line, so a
    heading line inside a div, a details element or a script
    block stands in no rendered subsection either. The rest
    of the rendered block family stands beside them. A line
    holding one complete tag of any other element opens a
    block running to a blank line in the rendering, as an
    anchor line placed above a heading does, and a
    processing instruction block, a declaration block and a
    CDATA block each run to their own closing marks. A
    comment block runs to its closing marks across as
    many lines as it takes and can interrupt a paragraph,
    and a paragraph line standing after a blockquote line
    without the quote marker is the blockquote its own
    paragraph continuing, its lazy continuation, so no
    paragraph of the outer document stands open after it
    either. A list stands open across a blank line, and a
    paragraph line standing in its item at the item its
    content indent after the blank line is the item its
    paragraph, closing with the item. A line standing
    at the fourth column or past it inside an open
    item, short of four columns past the item its
    content indent, is the item its content in the
    rendering and not an indented code block, so a
    paragraph line there arms the item its paragraph
    fact in the same way, while a line at that deeper
    indent inside the item is an indented code block
    of the item and arms no paragraph fact. The item
    its content indent is counted in columns in the
    same way, a tab in the gap after a marker counting
    to the next multiple of four columns and not as
    one character, and a gap of five columns or more
    after a marker counting as one space with the
    content indent standing one column past the end
    of the marker, so the window short of four
    columns past the content indent stands where the
    rendering puts it. A list item
    opened by a bare marker standing alone on its line
    holds the item its content at the marker its content
    indent in the same way, and a marker carrying a
    trailing space and no content opens an empty item
    in the same way, and a block standing outside
    an item, a comment block or a fenced block among
    them, closes the item its lazy continuation, so a
    paragraph line standing after one is a paragraph of
    the outer document. The
    start conditions are the rendered ones. The instruction,
    declaration and CDATA blocks and a block level tag,
    opening or closing, can interrupt a paragraph and open
    after any line at all, and a block level tag split
    across two lines opens on its first line. A lone tag
    block cannot interrupt a paragraph, so it opens only
    where no paragraph stands open, at the start of the
    document, after a blank line, a heading, a setext
    heading underline, a thematic break, a fence close, a
    comment only line or a comment block, a blockquote
    line or its lazy continuation line, a list item line
    or its lazy continuation line or another block,
    after the last item of a list on a line that stands
    outside the item its indent, after a paragraph
    standing in a list item across a blank line on a line
    outside the item its indent, or as the first content
    of a list item. The reader tracks whether a
    paragraph stands open, the content indent of a
    preceding list item line and of an open list item
    across a blank line, whether a blockquote
    paragraph stands open for a lazy continuation, and
    whether a list item paragraph stands open for a lazy
    continuation, the facts the lone tag condition
    reads. A structure standing inside a list
    item is read after its list marker, because the marker
    is list syntax and the
    fence or block after it is the item its content, while a
    heading standing as a list item its own content renders
    as a heading and stands.
    """
    visible = []
    in_fence = False
    fence_char = ""
    fence_len = 0
    fence_item_indent = None
    raw_tag = None
    in_html_block = False
    markup_end = None
    in_comment = False
    quote_open = False
    item_lazy_open = False
    open_item_indent = None
    prev_paragraph = False
    prev_item_indent = None
    for line in readme.splitlines():
        if markup_end is not None:
            quote_open = False
            item_lazy_open = False
            if markup_end in line:
                markup_end = None
                prev_paragraph = False
            continue
        if in_comment:
            # A comment block runs to its closing marks
            # across as many lines as it takes, and every
            # line of it is the block, the closing line
            # with any text after the marks included, so
            # no paragraph stands open after it.
            quote_open = False
            item_lazy_open = False
            if "-->" in line:
                in_comment = False
                prev_paragraph = False
                prev_item_indent = None
            continue
        if in_fence:
            quote_open = False
            item_lazy_open = False
            if fence_item_indent is not None and \
                    line.strip() and \
                    indent_columns(line) < fence_item_indent:
                # A line standing outside the item its
                # indent ends the item and its fence in the
                # rendering, the line standing as a line of
                # the outer document, so the fence reading
                # stands down and the line is read on its
                # own below. A fence line standing at that
                # place then opens a fence of the outer
                # document in the same reading.
                in_fence = False
                fence_item_indent = None
                open_item_indent = None
            else:
                close = None
                if indent_columns(line) <= 3:
                    close = FENCE_CLOSE_RE.match(
                        line.lstrip(" "))
                if close:
                    marker = close.group(1)
                    if marker[0] == fence_char and \
                            len(marker) >= fence_len:
                        in_fence = False
                        fence_item_indent = None
                        prev_paragraph = False
                continue
        if raw_tag is not None:
            quote_open = False
            item_lazy_open = False
            if re.search(
                    r"</%s\s*>" % raw_tag, line, re.IGNORECASE):
                raw_tag = None
                prev_paragraph = False
            continue
        if in_html_block:
            quote_open = False
            item_lazy_open = False
            if not line.strip():
                in_html_block = False
                prev_paragraph = False
                prev_item_indent = None
                visible.append(line)
            continue
        if not line.strip():
            visible.append(line)
            prev_paragraph = False
            prev_item_indent = open_item_indent
            quote_open = False
            item_lazy_open = False
            continue
        if indent_columns(line) >= 4 and not (
                open_item_indent is not None
                and open_item_indent <= indent_columns(line)
                < open_item_indent + 4):
            # A line at the fourth column or past it is
            # an indented code block, except where it
            # stands inside an open list item short of
            # four columns past the item its content
            # indent, where it is the item its content
            # in the rendering and is read on its own
            # below in the same way as any item line.
            continue
        content = line.lstrip(" ")
        if open_item_indent is not None and \
                indent_columns(line) < open_item_indent:
            # A line standing outside the open item its
            # indent is no part of the item, so the open
            # item standing ends at this line. The blank
            # line before it kept the standing only for a
            # line that stands inside the indent.
            open_item_indent = None
        in_open_item = open_item_indent is not None and \
            indent_columns(line) >= open_item_indent
        if content.strip().startswith("<!--"):
            # A comment block is a closed block in the
            # rendering, not paragraph text, so no
            # paragraph stands open after it. The block
            # runs to its closing marks, on this line or on
            # a later one, and it can interrupt a paragraph.
            if "-->" not in content.strip()[4:]:
                in_comment = True
            prev_paragraph = False
            prev_item_indent = None
            quote_open = False
            item_lazy_open = False
            continue
        before_paragraph = prev_paragraph
        before_item_indent = prev_item_indent
        prev_item_indent = None
        line_item_indent = None
        marker = LIST_MARKER_RE.match(content)
        bare = None
        if not marker and not before_paragraph:
            # A marker standing alone on its line opens an
            # empty item in the rendering, where a paragraph
            # stands open no empty item can interrupt it, so
            # the bare form is read only where no paragraph
            # stands open before it.
            bare = BARE_LIST_MARKER_RE.match(content)
        if marker or bare:
            # A structure standing inside a list item stands
            # after the list marker, and the marker is list
            # syntax rather than content, so the reading
            # starts where the item its content starts. The
            # item its first content stands where no paragraph
            # stands open, whatever line came before the item.
            if marker:
                # The item its content indent is counted
                # in columns in the same way as every
                # other indent in this reading, a tab in
                # the gap after the marker counting to
                # the next multiple of four columns and
                # not as one character, so the window
                # short of four columns past the content
                # indent stands where the rendering puts
                # it. A gap of five columns or more after
                # the marker counts as one space in the
                # rendering, so the content indent then
                # stands one column past the end of the
                # marker however wide the gap counts.
                prefix = content[
                    :len(content) - len(marker.group(1))]
                token = re.match(
                    r"[-+*]|[0-9]{1,9}[.)]", prefix)
                columns = len(line) - len(content)
                for char in prefix[:token.end()]:
                    columns += 1
                marker_end = columns
                gap = 0
                for char in prefix[token.end():]:
                    if char == "\t":
                        step = 4 - (columns % 4)
                        columns += step
                        gap += step
                    else:
                        columns += 1
                        gap += 1
                if gap >= 5:
                    line_item_indent = marker_end + 1
                else:
                    line_item_indent = columns
                content = marker.group(1)
            else:
                line_item_indent = indent_columns(line) + \
                    len(bare.group(1)) + 1
                content = ""
            open_item_indent = line_item_indent
            before_paragraph = False
            quote_open = False
            if bare or not content.strip():
                # The empty item carries no paragraph yet,
                # so no paragraph stands open after it and
                # its paragraph does not stand open for a
                # lazy continuation until a content line
                # stands in the item. A marker carrying a
                # trailing space and no content opens an
                # empty item in the rendering in the same
                # way as a bare marker, so it takes this
                # reading and not the paragraph reading.
                prev_paragraph = False
                item_lazy_open = False
                prev_item_indent = line_item_indent
                continue
        fence = FENCE_OPEN_RE.match(content)
        if fence:
            marker = fence.group(1)
            if marker[0] == "`" and "`" in fence.group(2):
                # A backtick fence line whose info string
                # carries a backtick is no fence at all, so
                # the line is the paragraph text of the
                # place it stands in, a list item included,
                # and the item its paragraph stands open
                # for a lazy continuation after it in the
                # same way as after an ordinary paragraph
                # line of the item.
                visible.append(line)
                prev_paragraph = True
                quote_open = False
                item_lazy_open = bool(
                    (line_item_indent is not None
                     or in_open_item) and prev_paragraph)
                if line_item_indent is not None:
                    prev_item_indent = line_item_indent
                elif in_open_item:
                    prev_item_indent = open_item_indent
                continue
            in_fence = True
            fence_char = marker[0]
            fence_len = len(marker)
            fence_item_indent = line_item_indent \
                if line_item_indent is not None else (
                    open_item_indent if in_open_item else None)
            prev_paragraph = False
            quote_open = False
            item_lazy_open = False
            continue
        if content.startswith("<?"):
            if "?>" not in content[2:]:
                markup_end = "?>"
            prev_paragraph = False
            quote_open = False
            item_lazy_open = False
            continue
        if content.startswith("<![CDATA["):
            if "]]>" not in content[9:]:
                markup_end = "]]>"
            prev_paragraph = False
            quote_open = False
            item_lazy_open = False
            continue
        if content.startswith("<!") and \
                len(content) > 2 and content[2].isupper():
            if ">" not in content[2:]:
                markup_end = ">"
            prev_paragraph = False
            quote_open = False
            item_lazy_open = False
            continue
        tag = HTML_TAG_RE.match(content)
        if tag and not tag.group(1):
            name = tag.group(2).lower()
            if name in RAW_TEXT_TAGS:
                rest = content[tag.end():]
                if not re.search(
                        r"</%s\s*>" % name, rest, re.IGNORECASE):
                    raw_tag = name
                prev_paragraph = False
                quote_open = False
                item_lazy_open = False
                continue
        if tag:
            name = tag.group(2).lower()
            if name in HTML_BLOCK_TAGS:
                in_html_block = True
                prev_paragraph = False
                quote_open = False
                item_lazy_open = False
                continue
        if not tag:
            split = re.match(
                r"</?([A-Za-z][A-Za-z0-9]*)\b[^>]*$", content)
            if split and \
                    split.group(1).lower() in HTML_BLOCK_TAGS:
                # A block level tag split across two lines
                # opens its block on the first line in the
                # rendering, where the tag name stands
                # followed by the line break.
                in_html_block = True
                prev_paragraph = False
                quote_open = False
                item_lazy_open = False
                continue
        lone_opens = not before_paragraph or (
            before_item_indent is not None
            and indent_columns(line) < before_item_indent)
        if tag and lone_opens and \
                LONE_TAG_LINE_RE.match(content):
            # A line holding one complete tag of an element
            # outside the block list opens the same kind of
            # block in the rendering, running to a blank
            # line, so a heading after it stands inside the
            # block and not in the document. The block cannot
            # interrupt a paragraph, so a lone tag standing
            # after a paragraph line opens nothing.
            in_html_block = True
            prev_paragraph = False
            quote_open = False
            item_lazy_open = False
            continue
        if quote_open and line_item_indent is None and \
                not re.match(r"#{1,6}[ \t]", content) and \
                not content.startswith(">"):
            # A paragraph line standing after a blockquote
            # line without the quote marker is the
            # blockquote its lazy continuation, the quote
            # its own paragraph continuing, so it is no
            # paragraph of the outer document and no
            # paragraph stands open after it.
            prev_paragraph = False
            prev_item_indent = None
            continue
        if item_lazy_open and line_item_indent is None \
                and not tag and not \
                re.match(r"#{1,6}[ \t]", content) and not \
                content.startswith(">") and not re.fullmatch(
                    r"([-*_])([ \t]*\1){2,}[ \t]*$", content):
            # A paragraph line standing after a list item
            # line without the marker is the item its own
            # paragraph continuing, its lazy continuation,
            # so it is no paragraph of the outer document
            # and no paragraph stands open after it, while
            # the item paragraph stands open for a further
            # lazy line in the same way.
            prev_paragraph = False
            prev_item_indent = None
            quote_open = False
            continue
        visible.append(content)
        if re.match(r"#{1,6}[ \t]", content):
            prev_paragraph = False
            quote_open = False
        elif before_paragraph and re.fullmatch(
                r"(=+|-+)[ \t]*", content):
            # A setext heading underline under a paragraph
            # line closes that paragraph as a heading, so no
            # paragraph stands open after it.
            prev_paragraph = False
            quote_open = False
        elif re.match(
                r"([-*_])([ \t]*\1){2,}[ \t]*$", content):
            prev_paragraph = False
            quote_open = False
        elif content.startswith(">"):
            # A blockquote line is a closed block in the
            # rendering once a line without the quote marker
            # follows it, so no paragraph of the outer
            # document stands open after it, and its
            # paragraph stands open inside the quote for a
            # lazy continuation line.
            prev_paragraph = False
            quote_open = True
        else:
            prev_paragraph = True
            quote_open = False
        item_lazy_open = bool(
            (line_item_indent is not None or in_open_item)
            and prev_paragraph)
        if line_item_indent is not None:
            prev_item_indent = line_item_indent
        elif in_open_item:
            # A line standing in the open item at its
            # content indent is the item its content, so
            # the item standing carries to the next line
            # across this one as it does across a blank
            # line, and a lone tag standing outside the
            # indent after it opens its block.
            prev_item_indent = open_item_indent
        else:
            prev_item_indent = None
    text = "\n".join(visible)
    text = re.sub(
        r"<!--.*?(?:-->|\Z)", "", text, flags=re.DOTALL)
    return any(
        COMATE_HEADING_RE.match(line.strip())
        for line in text.splitlines()
    )


def brief_problems(root, problems):
    """Problems with the Build 20 brief and its records."""
    raw = read_text(
        root, "docs/comate-brief.md", problems,
        "docs/comate-brief.md",
    )
    if raw is None:
        return
    text = " ".join(raw.split())
    section = rules_section(raw)
    if section is None:
        problems.append(
            "docs/comate-brief.md carries no %r section"
            % RULES_HEADING
        )
    else:
        problems.extend(derivation_problems(section))
    problems.extend(
        contradiction_problems(text, "docs/comate-brief.md")
    )
    for label, sentence in BRIEF_SENTENCES:
        if sentence not in text:
            problems.append(
                "docs/comate-brief.md does not state %s, so the "
                "brief could drift from the record it rests on"
                % label
            )
    record = read_text(
        root, "docs/decisions.md", problems, "docs/decisions.md"
    )
    if record is not None:
        start = record.find("## 32. Build 20")
        if start == -1:
            problems.append(
                "docs/decisions.md carries no decision 32 for "
                "Build 20"
            )
        else:
            section = record[start:]
            next_head = section.find("\n## ", 1)
            if next_head != -1:
                section = section[:next_head]
            if "Decision 4 binds" not in section:
                problems.append(
                    "decision 32 carries no decision 4 statement"
                )
        problems.extend(
            contradiction_problems(
                record, "docs/decisions.md",
                beside="decision 32's pinned honesty sentences",
            )
        )
    changelog = read_text(
        root, "CHANGELOG.md", problems, "CHANGELOG.md"
    )
    if changelog is not None:
        if "\n- The Comate adaptation." not in changelog:
            problems.append(
                "CHANGELOG.md carries no Comate adaptation entry"
            )
        else:
            # Round 288. The bullet narrates an addition, so it
            # stands under the Added heading. Standing under a
            # later heading, the Removed subsection at the
            # finding, reads the whole platform adaptation as
            # a removal to anyone scanning by headings.
            bullet = changelog.find("\n- The Comate adaptation.")
            added = changelog.find("### Added")
            fixed = changelog.find("### Fixed")
            if not (
                added != -1 and fixed != -1
                and added < bullet < fixed
            ):
                problems.append(
                    "the Comate adaptation entry stands outside "
                    "the Added subsection of CHANGELOG.md, so "
                    "the addition it narrates reads under the "
                    "wrong heading"
                )
        problems.extend(
            contradiction_problems(changelog, "CHANGELOG.md")
        )
    index = read_text(
        root, "docs/README.md", problems, "docs/README.md"
    )
    if index is not None:
        if "(comate-brief.md)" not in index:
            problems.append(
                "docs/README.md does not list the Comate brief"
            )
        problems.extend(
            contradiction_problems(index, "docs/README.md")
        )
    readme = read_text(root, "README.md", problems, "README.md")
    if readme is not None:
        if README_LINK not in readme:
            problems.append(
                "README.md does not link the Comate brief from "
                "the adaptations table"
            )
        flat_readme = " ".join(readme.split())
        if README_COPY_SENTENCE not in flat_readme:
            problems.append(
                "README.md does not state the byte identical "
                "copy on the native Comate project path"
            )
        if README_MARKETPLACE_SENTENCE not in flat_readme:
            problems.append(
                "README.md does not scope the Comate marketplace "
                "position to the evidenced record, so the "
                "unverified negative could harden into an "
                "existence claim"
            )
        if not comate_subsection_stands(readme):
            # The heading must stand as its own line in the
            # rendered document structure. A bare substring
            # search is satisfied by a renamed heading that
            # only begins with the same words, and a bare line
            # search is satisfied by a heading shaped line
            # inside a fenced code block or an HTML comment,
            # so the subsection could be retitled away while
            # the gate still certified that it stands.
            problems.append(
                "README.md carries no Comate install subsection"
            )
        problems.extend(contradiction_problems(flat_readme, "README.md"))
    agents = read_text(root, "AGENTS.md", problems, "AGENTS.md")
    if agents is not None:
        problems.extend(
            contradiction_problems(
                " ".join(agents.split()), "AGENTS.md"
            )
        )


def comate_problems(root=None):
    """Every Build 20 Comate adaptation problem."""
    root = ROOT if root is None else root
    problems = []
    symlink_problems(root, COMATE_TREE, problems)
    placement_problems(root, problems)
    brief_problems(root, problems)
    return problems


def main(root=None):
    problems = comate_problems(root)
    if problems:
        for problem in problems:
            print("check_comate: %s" % problem, file=sys.stderr)
        return 1
    print("check_comate: the Build 20 Comate adaptation holds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
